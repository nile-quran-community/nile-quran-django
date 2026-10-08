import pytest
from django.db import IntegrityError, transaction

from nile_quran_community_api.apps.v1.announcements.models import Announcement


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
