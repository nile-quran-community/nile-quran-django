import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

from nile_quran_community_api.apps.v1.announcements.integrations import discord
from nile_quran_community_api.apps.v1.users.models import User


@pytest.fixture
def make_user(db):
    students = Group.objects.get(name="Student")

    def _make(username, first, last, discord_id=""):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass",
            first_name=first,
            last_name=last,
            discord_id=discord_id,
        )
        user.groups.add(students)
        return user

    return _make


@pytest.fixture
def server_members(monkeypatch, settings):
    """Stand in for the Discord server's member list."""
    settings.DISCORD_BOT_TOKEN = "test-token"
    settings.DISCORD_GUILD_ID = "guild-1"
    members: list[dict] = []
    monkeypatch.setattr(discord, "list_members", lambda guild_id: members)
    return members


@pytest.mark.django_db
class TestLinkDiscordAccounts:
    def test_saves_the_id_of_an_unambiguous_match(self, make_user, server_members):
        user = make_user("ahmed", "أحمد", "علي")
        server_members.append({"id": "111", "names": ["احمد علي"]})

        call_command("link_discord_accounts")

        user.refresh_from_db()
        assert user.discord_id == "111"

    def test_dry_run_saves_nothing(self, make_user, server_members):
        user = make_user("ahmed", "أحمد", "علي")
        server_members.append({"id": "111", "names": ["أحمد علي"]})

        call_command("link_discord_accounts", "--dry-run")

        user.refresh_from_db()
        assert user.discord_id == ""

    def test_leaves_an_existing_id_untouched(self, make_user, server_members):
        user = make_user("ahmed", "أحمد", "علي", discord_id="999")
        server_members.append({"id": "111", "names": ["أحمد علي"]})

        call_command("link_discord_accounts")

        user.refresh_from_db()
        assert user.discord_id == "999"

    def test_does_not_link_an_ambiguous_name(self, make_user, server_members):
        first = make_user("ahmed1", "أحمد", "علي")
        second = make_user("ahmed2", "أحمد", "علي")
        server_members.append({"id": "111", "names": ["أحمد علي"]})

        call_command("link_discord_accounts")

        first.refresh_from_db()
        second.refresh_from_db()
        assert (first.discord_id, second.discord_id) == ("", "")

    def test_links_only_the_users_it_can_place(self, make_user, server_members):
        matched = make_user("ahmed", "أحمد", "علي")
        missing = make_user("omar", "عمر", "حسن")
        server_members.append({"id": "111", "names": ["أحمد علي"]})

        call_command("link_discord_accounts")

        matched.refresh_from_db()
        missing.refresh_from_db()
        assert matched.discord_id == "111"
        assert missing.discord_id == ""

    def test_rerunning_is_harmless(self, make_user, server_members):
        user = make_user("ahmed", "أحمد", "علي")
        server_members.append({"id": "111", "names": ["أحمد علي"]})

        call_command("link_discord_accounts")
        call_command("link_discord_accounts")

        user.refresh_from_db()
        assert user.discord_id == "111"

    def test_requires_discord_configuration(self, settings):
        settings.DISCORD_BOT_TOKEN = ""
        settings.DISCORD_GUILD_ID = ""

        with pytest.raises(CommandError):
            call_command("link_discord_accounts")
