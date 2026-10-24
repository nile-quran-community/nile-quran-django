import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status as http
from rest_framework.test import APIClient

from nile_quran_community_api.apps.v1.announcements.integrations import discord
from nile_quran_community_api.apps.v1.announcements.models import (
    Announcement,
    AnnouncementDelivery,
)

DUE = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)
LATER = dt.datetime(2099, 1, 1, tzinfo=dt.UTC)


def announcement(**overrides) -> Announcement:
    return Announcement.objects.create(
        **{
            "type": Announcement.Type.GENERAL,
            "title": "إعلان",
            "content": "نص",
            "publish_at": DUE,
            **overrides,
        }
    )


def delivery(announcement: Announcement, **overrides) -> AnnouncementDelivery:
    return AnnouncementDelivery.objects.create(
        **{
            "announcement": announcement,
            "channel": AnnouncementDelivery.Channel.DISCORD,
            "status": AnnouncementDelivery.Status.SENT,
            "external_id": "msg-1",
            "delivered_at": DUE,
            **overrides,
        }
    )


@pytest.fixture
def admin_client(client: APIClient, jwt_admin_token) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
    return client


@pytest.fixture
def media_client(client: APIClient, jwt_media_token) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_media_token}")
    return client


@pytest.fixture
def student_client(client: APIClient, jwt_user_token) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
    return client


def ids(response) -> set[int]:
    return {row["id"] for row in response.data["results"]}


@pytest.mark.django_db
class TestAnnouncementDeliveryViewSet:
    def test_lists_deliveries(self, admin_client):
        delivery(announcement())

        response = admin_client.get("/announcements/deliveries/")

        assert response.status_code == http.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["external_id"] == "msg-1"

    def test_deliveries_route_is_not_swallowed_by_the_announcement_detail_route(
        self, admin_client
    ):
        announcement()

        response = admin_client.get("/announcements/deliveries/")

        assert response.status_code == http.HTTP_200_OK
        assert "results" in response.data

    def test_retrieves_one_delivery(self, admin_client):
        record = delivery(announcement())

        response = admin_client.get(f"/announcements/deliveries/{record.pk}/")

        assert response.status_code == http.HTTP_200_OK
        assert response.data["id"] == record.pk

    def test_filters_by_status(self, admin_client):
        delivery(announcement(), status=AnnouncementDelivery.Status.SENT)
        delivery(announcement(), status=AnnouncementDelivery.Status.FAILED)

        response = admin_client.get("/announcements/deliveries/?status=failed")

        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "failed"

    def test_filters_by_announcement(self, admin_client):
        wanted = announcement()
        delivery(wanted)
        delivery(announcement())

        response = admin_client.get(
            f"/announcements/deliveries/?announcement={wanted.pk}"
        )

        assert response.data["count"] == 1
        assert response.data["results"][0]["announcement"] == wanted.pk

    def test_filters_by_announcement_type(self, admin_client):
        delivery(announcement(type=Announcement.Type.MONTH_TOP_PERFORMERS))
        delivery(announcement(type=Announcement.Type.GENERAL))

        response = admin_client.get(
            "/announcements/deliveries/?announcement_type=month_top_performers"
        )

        assert response.data["count"] == 1

    def test_is_read_only(self, admin_client):
        record = delivery(announcement())
        refused = {http.HTTP_403_FORBIDDEN, http.HTTP_405_METHOD_NOT_ALLOWED}

        assert (
            admin_client.post("/announcements/deliveries/", {}).status_code in refused
        )
        assert (
            admin_client.patch(
                f"/announcements/deliveries/{record.pk}/", {"status": "sent"}
            ).status_code
            in refused
        )
        assert (
            admin_client.delete(f"/announcements/deliveries/{record.pk}/").status_code
            in refused
        )
        assert AnnouncementDelivery.objects.count() == 1


@pytest.mark.django_db
class TestAnnouncementViewSet:
    def test_exposes_status_and_deliveries_inline(self, admin_client):
        delivery(announcement())

        response = admin_client.get("/announcements/")

        result = response.data["results"][0]
        assert result["status"] == Announcement.Status.PUBLISHED
        assert len(result["deliveries"]) == 1
        assert result["deliveries"][0]["external_id"] == "msg-1"

    def test_filters_by_type(self, admin_client):
        announcement(type=Announcement.Type.MONTH_TOP_PERFORMERS)
        announcement(type=Announcement.Type.GENERAL)

        response = admin_client.get("/announcements/?type=general")

        assert response.status_code == http.HTTP_200_OK
        assert response.data["count"] == 1

    def test_listing_does_not_scale_queries_with_rows(
        self, admin_client, django_assert_max_num_queries
    ):
        for _ in range(5):
            delivery(announcement())

        with django_assert_max_num_queries(8):
            response = admin_client.get("/announcements/")

        assert response.data["count"] == 5

    def test_create_attributes_the_announcement_to_the_requester(
        self, admin_client, admin_user, supervisor_user
    ):
        response = admin_client.post(
            "/announcements/",
            {
                "type": Announcement.Type.GENERAL,
                "title": "إعلان",
                "content": "نص",
                "created_by": supervisor_user.username,
            },
            format="json",
        )

        assert response.status_code == http.HTTP_201_CREATED
        assert Announcement.objects.get().created_by == admin_user

    def test_a_generated_announcement_can_be_edited(self, admin_client):
        record = announcement(created_by=None)

        response = admin_client.put(
            f"/announcements/{record.pk}/",
            {"type": Announcement.Type.GENERAL, "title": "جديد", "content": "نص"},
            format="json",
        )

        assert response.status_code == http.HTTP_200_OK

    def test_rejects_content_discord_cannot_carry(self, admin_client):
        response = admin_client.post(
            "/announcements/",
            {
                "type": Announcement.Type.GENERAL,
                "title": "إعلان",
                "content": "ا" * 4097,
            },
            format="json",
        )

        assert response.status_code == http.HTTP_400_BAD_REQUEST
        assert "content" in response.data


@pytest.mark.django_db
class TestVisibility:
    def test_a_student_sees_only_what_is_due(self, student_client):
        live = announcement()
        announcement(publish_at=None)
        announcement(publish_at=LATER)

        assert ids(student_client.get("/announcements/")) == {live.pk}

    def test_an_editor_sees_their_own_drafts_and_others_scheduled_posts(
        self, media_client, media_user, admin_user
    ):
        mine = announcement(publish_at=None, created_by=media_user)
        scheduled = announcement(publish_at=LATER, created_by=admin_user)

        assert ids(media_client.get("/announcements/")) == {mine.pk, scheduled.pk}

    def test_an_editor_does_not_see_another_editors_draft(
        self, media_client, admin_user
    ):
        announcement(publish_at=None, created_by=admin_user)

        assert media_client.get("/announcements/").data["count"] == 0

    def test_editing_someone_elses_draft_is_a_404(self, media_client, admin_user):
        draft = announcement(publish_at=None, created_by=admin_user)

        response = media_client.patch(
            f"/announcements/{draft.pk}/", {"title": "x"}, format="json"
        )

        assert response.status_code == http.HTTP_404_NOT_FOUND

    def test_deliveries_follow_the_same_rule(self, student_client):
        delivery(announcement(publish_at=LATER))

        assert student_client.get("/announcements/deliveries/").data["count"] == 0

    def test_a_student_cannot_read_delivery_records_even_of_a_live_announcement(
        self, student_client
    ):
        record = delivery(
            announcement(),
            status=AnnouncementDelivery.Status.FAILED,
            last_error="boom",
        )

        assert student_client.get("/announcements/deliveries/").data["count"] == 0
        assert (
            student_client.get(f"/announcements/deliveries/{record.pk}/").status_code
            == http.HTTP_404_NOT_FOUND
        )

    def test_an_editor_still_reads_delivery_records(self, media_client):
        delivery(announcement())

        assert media_client.get("/announcements/deliveries/").data["count"] == 1

    def test_the_list_needs_a_login(self, client):
        assert client.get("/announcements/").status_code in {
            http.HTTP_401_UNAUTHORIZED,
            http.HTTP_403_FORBIDDEN,
        }


@pytest.mark.django_db
class TestPreview:
    def test_works_without_a_login_and_hides_the_body(self, client):
        record = announcement(summary="ملخص")

        response = client.get(f"/announcements/{record.pk}/preview/")

        assert response.status_code == http.HTTP_200_OK
        assert response.data["summary"] == "ملخص"
        assert response.data["type_display"]
        assert "content" not in response.data

    def test_a_draft_is_a_404(self, client):
        record = announcement(publish_at=None)

        response = client.get(f"/announcements/{record.pk}/preview/")

        assert response.status_code == http.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAuthorship:
    def test_update_records_who_edited(self, admin_client, admin_user, media_user):
        record = announcement(created_by=media_user)

        response = admin_client.patch(
            f"/announcements/{record.pk}/", {"title": "جديد"}, format="json"
        )

        assert response.status_code == http.HTTP_200_OK
        assert response.data["updated_by"]["username"] == admin_user.username
        assert response.data["created_by"]["username"] == media_user.username

    def test_create_records_the_author_as_the_editor_too(
        self, admin_client, admin_user
    ):
        admin_client.post(
            "/announcements/",
            {"type": "general", "title": "إعلان", "content": "نص"},
            format="json",
        )

        record = Announcement.objects.get()
        assert record.created_by == record.updated_by == admin_user


@pytest.mark.django_db
class TestMentions:
    def test_maps_discord_ids_to_name_and_username_for_a_profile_link(
        self, admin_client
    ):
        get_user_model().objects.create_user(
            username="ali",
            email="ali@example.com",
            password="x",
            first_name="علي",
            last_name="أحمد",
            discord_id="123",
        )
        announcement(content="مبروك <@123> و <@999>")

        response = admin_client.get("/announcements/")

        # an ID nobody owns (999) is left out: the site shows a neutral word for it, no link
        assert response.data["results"][0]["mentions"] == {
            "123": {"name": "علي أحمد", "username": "ali"}
        }

    def test_plain_content_costs_no_extra_query(
        self, admin_client, django_assert_max_num_queries
    ):
        announcement()

        with django_assert_max_num_queries(8):
            response = admin_client.get("/announcements/")

        assert response.data["results"][0]["mentions"] == {}


@pytest.mark.django_db
class TestFilters:
    def test_live_hides_scheduled_posts_from_editors(self, media_client, media_user):
        live = announcement()
        announcement(publish_at=LATER)
        announcement(publish_at=None, created_by=media_user)

        response = media_client.get("/announcements/?live=true")

        assert ids(response) == {live.pk}

    def test_status_matches_the_derived_status(self, admin_client, admin_user):
        published = delivery(announcement()).announcement
        draft = announcement(publish_at=None, created_by=admin_user)
        scheduled = announcement(publish_at=LATER)
        failed = delivery(
            announcement(), status=AnnouncementDelivery.Status.FAILED
        ).announcement
        pending = announcement()

        expected = {
            "published": published,
            "draft": draft,
            "scheduled": scheduled,
            "failed": failed,
            "pending": pending,
        }
        for name, record in expected.items():
            response = admin_client.get(f"/announcements/?status={name}")
            assert ids(response) == {record.pk}, name
            assert response.data["results"][0]["status"] == name


@pytest.mark.django_db
class TestDelete:
    @pytest.fixture
    def configured(self, settings):
        settings.DISCORD_BOT_TOKEN = "token"
        settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID = "channel-1"

    def test_removes_the_discord_message_first(
        self, admin_client, configured, monkeypatch
    ):
        calls = []
        monkeypatch.setattr(
            discord, "delete_message", lambda channel, message: calls.append(message)
        )
        record = announcement()
        delivery(record)

        response = admin_client.delete(f"/announcements/{record.pk}/")

        assert response.status_code == http.HTTP_204_NO_CONTENT
        assert calls == ["msg-1"]
        assert not Announcement.objects.exists()

    def test_a_message_already_gone_does_not_block_deletion(
        self, admin_client, configured, monkeypatch
    ):
        def gone(*args):
            raise discord.MessageNotFound("msg-1")

        monkeypatch.setattr(discord, "delete_message", gone)
        record = announcement()
        delivery(record)

        response = admin_client.delete(f"/announcements/{record.pk}/")

        assert response.status_code == http.HTTP_204_NO_CONTENT

    def test_a_discord_failure_returns_502_and_keeps_the_row(
        self, admin_client, configured, monkeypatch
    ):
        def down(*args):
            raise OSError("discord is down")

        monkeypatch.setattr(discord, "delete_message", down)
        record = announcement()
        delivery(record)

        response = admin_client.delete(f"/announcements/{record.pk}/")

        assert response.status_code == http.HTTP_502_BAD_GATEWAY
        assert Announcement.objects.filter(pk=record.pk).exists()

    def test_without_discord_configured_the_row_is_just_deleted(
        self, admin_client, settings, monkeypatch
    ):
        settings.DISCORD_BOT_TOKEN = ""
        settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID = ""
        monkeypatch.setattr(
            discord, "delete_message", lambda *a: pytest.fail("Discord was called")
        )
        record = announcement()
        delivery(record)

        response = admin_client.delete(f"/announcements/{record.pk}/")

        assert response.status_code == http.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestDeliveryDetailsAreEditorOnly:
    def test_a_student_gets_no_deliveries_in_the_list(self, student_client):
        delivery(announcement())

        result = student_client.get("/announcements/").data["results"][0]

        assert "deliveries" not in result

    def test_a_student_gets_no_deliveries_on_one_announcement(self, student_client):
        record = announcement()
        delivery(record)

        response = student_client.get(f"/announcements/{record.pk}/")

        assert response.status_code == http.HTTP_200_OK
        assert "deliveries" not in response.data

    def test_a_student_still_sees_the_derived_status(self, student_client):
        delivery(announcement())

        result = student_client.get("/announcements/").data["results"][0]

        assert result["status"] == Announcement.Status.PUBLISHED

    @pytest.mark.parametrize("who", ["admin_client", "media_client"])
    def test_editors_get_deliveries(self, who, request):
        delivery(announcement())

        result = request.getfixturevalue(who).get("/announcements/").data["results"][0]

        assert result["deliveries"][0]["external_id"] == "msg-1"


@pytest.mark.django_db
class TestErrorTextIsAdminOnly:
    """`last_error` is raw exception text (hosts, Discord error codes): what whoever fixes
    the bot needs, and noise, or worse, for the rest of the media team."""

    @staticmethod
    def failed() -> AnnouncementDelivery:
        return delivery(
            announcement(),
            status=AnnouncementDelivery.Status.FAILED,
            attempts=3,
            last_error="403 Forbidden (error code: 50013)",
        )

    def test_an_admin_gets_it_inline(self, admin_client):
        self.failed()

        result = admin_client.get("/announcements/").data["results"][0]

        assert result["deliveries"][0]["last_error"].startswith("403")

    def test_another_editor_does_not_get_it_inline_but_still_sees_the_failure(
        self, media_client
    ):
        self.failed()

        record = media_client.get("/announcements/").data["results"][0]["deliveries"][0]

        assert "last_error" not in record
        assert (record["status"], record["attempts"]) == ("failed", 3)

    def test_an_admin_gets_it_on_the_deliveries_endpoint(self, admin_client):
        self.failed()

        result = admin_client.get("/announcements/deliveries/").data["results"][0]

        assert result["last_error"].startswith("403")

    def test_another_editor_does_not_get_it_on_the_deliveries_endpoint(
        self, media_client
    ):
        record = self.failed()

        listed = media_client.get("/announcements/deliveries/").data["results"][0]
        single = media_client.get(f"/announcements/deliveries/{record.pk}/").data

        assert "last_error" not in listed
        assert "last_error" not in single
