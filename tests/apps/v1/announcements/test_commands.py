import datetime as dt

import discord as discord_py
import pytest
from django.core.management import call_command

from nile_quran_community_api.apps.v1.announcements.integrations import discord
from nile_quran_community_api.apps.v1.announcements.models import (
    Announcement,
    AnnouncementDelivery,
)

RAMADAN_START = "2026-02-18"  # 1 Ramadan 1447; the month that just ended is Sha'ban.
IN_SHAABAN = dt.date(2026, 2, 1)
SHAABAN_KEY = f"{Announcement.Type.MONTH_TOP_PERFORMERS.value}:1447-08"


MESSAGE_ID = "discord-message-1"


@pytest.fixture
def discord_api(monkeypatch, settings):
    """Record calls instead of reaching Discord."""
    settings.DISCORD_BOT_TOKEN = "test-token"
    settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID = "channel-1"
    calls: list[dict] = []

    def post_message(channel_id, payload):
        calls.append({"action": "post", "channel": channel_id, "payload": payload})
        return MESSAGE_ID

    def edit_message(channel_id, message_id, payload):
        calls.append(
            {
                "action": "edit",
                "channel": channel_id,
                "message": message_id,
                "payload": payload,
            }
        )

    monkeypatch.setattr(discord, "post_message", post_message)
    monkeypatch.setattr(discord, "edit_message", edit_message)
    return calls


def break_discord(monkeypatch):
    """Make sending fail the way a Discord outage would; returns a repair callable."""
    recording = discord.post_message

    def fail(*args, **kwargs):
        raise discord_py.DiscordException("discord is down")

    monkeypatch.setattr(discord, "post_message", fail)
    return lambda: monkeypatch.setattr(discord, "post_message", recording)


def due_announcement(**overrides) -> Announcement:
    return Announcement.objects.create(
        **{
            "type": Announcement.Type.GENERAL,
            "title": "إعلان",
            "content": "نص الإعلان",
            "publish_at": dt.datetime(2020, 1, 1, tzinfo=dt.UTC),
            **overrides,
        }
    )


@pytest.mark.django_db
class TestGenerateTopPerformers:
    def test_queues_an_announcement_for_the_previous_month(self, make_student):
        make_student("winner", 10, IN_SHAABAN)

        call_command("generate_top_performers", f"--date={RAMADAN_START}")

        announcement = Announcement.objects.get(idempotency_key=SHAABAN_KEY)
        assert announcement.type == Announcement.Type.MONTH_TOP_PERFORMERS
        assert announcement.status == Announcement.Status.PENDING
        assert announcement.publish_at is not None
        assert "رمضان" not in announcement.title
        assert "شعبان" in announcement.title
        assert "10" in announcement.content

    def test_does_nothing_outside_a_hijri_month_start(self, make_student):
        make_student("winner", 10, IN_SHAABAN)

        call_command("generate_top_performers", "--date=2026-02-10")

        assert not Announcement.objects.exists()

    def test_force_overrides_the_month_start_check(self, make_student):
        make_student("winner", 10, IN_SHAABAN)

        # Mid-Ramadan, so the month that just ended is still Sha'ban.
        call_command("generate_top_performers", "--date=2026-02-20", "--force")

        assert Announcement.objects.filter(idempotency_key=SHAABAN_KEY).exists()

    def test_skips_when_no_student_earned_points(self, make_student):
        make_student("idle", 0, IN_SHAABAN)

        call_command("generate_top_performers", f"--date={RAMADAN_START}")

        assert not Announcement.objects.exists()

    def test_rerun_updates_instead_of_creating_a_second_announcement(
        self, make_student
    ):
        make_student("winner", 10, IN_SHAABAN)
        call_command("generate_top_performers", f"--date={RAMADAN_START}")
        make_student("latecomer", 20, IN_SHAABAN)

        call_command("generate_top_performers", f"--date={RAMADAN_START}")

        announcement = Announcement.objects.get(idempotency_key=SHAABAN_KEY)
        assert Announcement.objects.count() == 1
        assert "20" in announcement.content

    def test_rerun_edits_a_message_already_in_discord(self, make_student, discord_api):
        make_student("winner", 10, IN_SHAABAN)
        call_command("generate_top_performers", f"--date={RAMADAN_START}")
        call_command("publish_announcements")
        discord_api.clear()
        make_student("latecomer", 20, IN_SHAABAN)

        call_command("generate_top_performers", f"--date={RAMADAN_START}")

        assert [call["action"] for call in discord_api] == ["edit"]
        assert discord_api[0]["message"] == MESSAGE_ID
        assert "20" in discord_api[0]["payload"]["embed"]["description"]


@pytest.mark.django_db
class TestPublishAnnouncements:
    def test_sends_a_due_announcement(self, discord_api):
        announcement = due_announcement()

        call_command("publish_announcements")

        delivery = announcement.deliveries.get()
        announcement.refresh_from_db()
        assert [call["action"] for call in discord_api] == ["post"]
        assert discord_api[0]["channel"] == "channel-1"
        assert discord_api[0]["payload"] == {
            "content": "@everyone",
            "embed": {"title": "إعلان", "description": "نص الإعلان"},
        }
        assert delivery.status == AnnouncementDelivery.Status.SENT
        assert delivery.external_id == MESSAGE_ID
        assert delivery.delivered_at is not None
        assert announcement.status == Announcement.Status.PUBLISHED

    def test_does_not_resend_an_already_delivered_announcement(self, discord_api):
        due_announcement()
        call_command("publish_announcements")
        discord_api.clear()

        call_command("publish_announcements")

        assert discord_api == []

    def test_skips_announcements_not_yet_due(self, discord_api):
        due_announcement(publish_at=dt.datetime(2099, 1, 1, tzinfo=dt.UTC))

        call_command("publish_announcements")

        assert discord_api == []

    def test_skips_drafts_which_are_announcements_without_a_publish_time(
        self, discord_api
    ):
        due_announcement(publish_at=None)

        call_command("publish_announcements")

        assert discord_api == []

    def test_records_a_failure_and_retries_on_the_next_run(
        self, discord_api, monkeypatch
    ):
        announcement = due_announcement()
        repair = break_discord(monkeypatch)

        call_command("publish_announcements")

        delivery = announcement.deliveries.get()
        assert delivery.status == AnnouncementDelivery.Status.FAILED
        assert delivery.attempts == 1
        assert "discord is down" in delivery.last_error

        repair()
        call_command("publish_announcements")

        delivery.refresh_from_db()
        assert delivery.status == AnnouncementDelivery.Status.SENT
        assert delivery.attempts == 2
        assert delivery.last_error == ""

    def test_sends_nothing_when_discord_is_not_configured(self, settings, monkeypatch):
        settings.DISCORD_BOT_TOKEN = ""
        settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID = ""
        due_announcement()
        monkeypatch.setattr(
            discord,
            "post_message",
            lambda *a, **kw: pytest.fail("Discord should not be called"),
        )

        call_command("publish_announcements")

        assert not AnnouncementDelivery.objects.exists()
