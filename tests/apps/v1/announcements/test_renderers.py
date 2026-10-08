import datetime as dt

import pytest

from nile_quran_community_api.apps.v1.announcements import renderers
from nile_quran_community_api.apps.v1.announcements.integrations import discord
from nile_quran_community_api.apps.v1.announcements.models import Announcement

IN_SHAABAN = dt.date(2026, 2, 1)


def ranked(student, points, rank):
    student.points, student.rank = points, rank
    return student


@pytest.mark.django_db
class TestTopPerformersContent:
    def test_mentions_students_who_have_a_discord_id(self, make_student):
        student = make_student("linked", 5, IN_SHAABAN, discord_id="99")

        assert "<@99>" in renderers.top_performers_content([ranked(student, 5, 1)])

    def test_falls_back_to_the_name_without_a_discord_id(self, make_student):
        student = make_student("unlinked", 5, IN_SHAABAN)

        content = renderers.top_performers_content([ranked(student, 5, 1)])

        assert "<@" not in content
        assert "طالب unlinked" in content

    def test_tied_students_each_get_their_shared_medal(self, make_student):
        students = [
            ranked(make_student(name, 5, IN_SHAABAN), 5, 1) for name in ("one", "two")
        ]

        assert renderers.top_performers_content(students).count("🥇") == 2

    def test_rank_beyond_the_medals_falls_back_to_a_number(self, make_student):
        student = make_student("fourth", 1, IN_SHAABAN)

        assert "4." in renderers.top_performers_content([ranked(student, 1, 4)])

    def test_points_appear_next_to_each_student(self, make_student):
        student = make_student("winner", 7, IN_SHAABAN)

        assert "7 نقطة" in renderers.top_performers_content([ranked(student, 7, 1)])

    def test_title_carries_the_hijri_month_and_year(self):
        assert (
            renderers.top_performers_title("شعبان", 1447) == "المتصدرون لشهر شعبان 1447"
        )


@pytest.mark.django_db
class TestAnnouncementEmbed:
    def test_maps_title_and_content(self):
        announcement = Announcement(title="عنوان", content="محتوى")

        assert renderers.announcement_embed(announcement) == {
            "title": "عنوان",
            "description": "محتوى",
        }

    def test_embed_payload_converts_for_discord(self):
        """The dict the renderer produces has to satisfy discord.py's Embed."""
        embed = discord._embed({"title": "عنوان", "description": "محتوى"})

        assert (embed.title, embed.description) == ("عنوان", "محتوى")
