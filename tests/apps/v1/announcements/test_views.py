import datetime as dt

import pytest
from rest_framework import status as http
from rest_framework.test import APIClient

from nile_quran_community_api.apps.v1.announcements.models import (
    Announcement,
    AnnouncementDelivery,
)

DUE = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)


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
