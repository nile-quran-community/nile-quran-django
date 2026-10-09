import datetime as dt

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from nile_quran_community_api.apps.v1.announcements.models import (
    Announcement,
    AnnouncementDelivery,
)


def announcement(**overrides) -> Announcement:
    return Announcement.objects.create(
        **{
            "type": Announcement.Type.MONTH_TOP_PERFORMERS,
            "title": "عنوان",
            "content": "محتوى",
            **overrides,
        }
    )


@pytest.mark.django_db
class TestAnnouncementReferenceKey:
    def test_the_same_reference_key_cannot_be_used_twice(self):
        announcement(reference_key="top_performers:1447-08")

        with pytest.raises(IntegrityError), transaction.atomic():
            announcement(reference_key="top_performers:1447-08")

    def test_announcements_without_a_reference_key_are_unconstrained(self):
        announcement(type=Announcement.Type.GENERAL)
        announcement(type=Announcement.Type.GENERAL)

        assert Announcement.objects.filter(reference_key="").count() == 2


def delivery(announcement: Announcement, status: str) -> AnnouncementDelivery:
    return AnnouncementDelivery.objects.create(
        announcement=announcement,
        channel=AnnouncementDelivery.Channel.DISCORD,
        status=status,
    )


@pytest.mark.django_db
class TestAnnouncementStatus:
    """status is derived, so it can never disagree with the delivery records."""

    def test_no_publish_time_is_a_draft(self):
        assert announcement().status == Announcement.Status.DRAFT

    def test_a_future_publish_time_is_scheduled(self):
        future = timezone.now() + dt.timedelta(days=1)

        assert announcement(publish_at=future).status == Announcement.Status.SCHEDULED

    def test_due_but_undelivered_is_pending(self):
        past = timezone.now() - dt.timedelta(days=1)

        assert announcement(publish_at=past).status == Announcement.Status.PENDING

    def test_a_sent_delivery_makes_it_published(self):
        due = announcement(publish_at=timezone.now() - dt.timedelta(days=1))
        delivery(due, AnnouncementDelivery.Status.SENT)

        assert due.status == Announcement.Status.PUBLISHED

    def test_a_failed_delivery_shows_as_failed(self):
        due = announcement(publish_at=timezone.now() - dt.timedelta(days=1))
        delivery(due, AnnouncementDelivery.Status.FAILED)

        assert due.status == Announcement.Status.FAILED

    def test_delivery_wins_over_the_publish_time(self):
        """Backdating publish_at cannot un-send something Discord already has."""
        future = announcement(publish_at=timezone.now() + dt.timedelta(days=1))
        delivery(future, AnnouncementDelivery.Status.SENT)

        assert future.status == Announcement.Status.PUBLISHED

    def test_reads_prefetched_deliveries_without_extra_queries(
        self, django_assert_num_queries
    ):
        for _ in range(3):
            due = announcement(publish_at=timezone.now() - dt.timedelta(days=1))
            delivery(due, AnnouncementDelivery.Status.SENT)

        queryset = Announcement.objects.prefetch_related("deliveries")
        with django_assert_num_queries(2):
            assert [a.status for a in queryset] == [Announcement.Status.PUBLISHED] * 3
