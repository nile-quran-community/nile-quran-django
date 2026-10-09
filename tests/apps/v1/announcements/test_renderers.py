import datetime as dt

import pytest

from nile_quran_community_api.apps.v1.announcements import poetry, renderers
from nile_quran_community_api.apps.v1.announcements.integrations import discord
from nile_quran_community_api.apps.v1.announcements.models import Announcement

IN_SHAABAN = dt.date(2026, 2, 1)
SHAABAN = (1447, 8)


def ranked(student, points, rank):
    student.points, student.rank = points, rank
    return student


@pytest.fixture
def performer(make_student):
    def _make(username, points, rank, discord_id=""):
        student = make_student(username, points, IN_SHAABAN, discord_id=discord_id)
        return ranked(student, points, rank)

    return _make


@pytest.mark.django_db
class TestTopPerformersContent:
    def test_opens_with_a_banner_and_a_verse(self, performer):
        content = renderers.top_performers_content([performer("a", 5, 1)], *SHAABAN)

        assert content.startswith(renderers.BANNER)
        assert poetry.for_month(*SHAABAN) in content

    def test_greets_the_month_that_ended(self, performer):
        content = renderers.top_performers_content([performer("a", 5, 1)], *SHAABAN)

        assert "انتهينا من شهر شعبان" in content

    def test_lists_winners_from_first_place_down(self, performer):
        performers = [
            performer("first", 12, 1),
            performer("second", 10, 2),
            performer("third", 9, 3),
        ]

        content = renderers.top_performers_content(performers, *SHAABAN)

        places = [line for line in content.splitlines() if line.startswith("- المركز")]
        assert [p.split(":")[0] for p in places] == [
            "- المركز الأول",
            "- المركز الثاني",
            "- المركز الثالث",
        ]

    def test_lists_ranks_beyond_the_third_as_honourable_mentions(self, performer):
        performers = [
            performer("first", 12, 1),
            performer("second", 10, 2),
            performer("third", 9, 3),
            performer("fourth", 7, 4),
            performer("fifth", 6, 5),
        ]

        content = renderers.top_performers_content(performers, *SHAABAN)

        assert renderers.HONOURABLE_HEADING in content
        honourable = content.split(renderers.HONOURABLE_HEADING)[1]
        assert "ب7 نقاط" in honourable
        assert "ب6 نقاط" in honourable
        assert "المركز" not in honourable

    def test_winning_rank_count_comes_from_settings(self, performer, settings):
        settings.ANNOUNCEMENTS_WINNING_RANKS = 1
        performers = [performer("first", 12, 1), performer("second", 10, 2)]

        content = renderers.top_performers_content(performers, *SHAABAN)

        winners, honourable = content.split(renderers.HONOURABLE_HEADING)
        assert "المركز الأول" in winners
        assert "المركز الثاني" not in winners
        assert "ب10 نقاط" in honourable

    def test_omits_the_honourable_section_when_nobody_qualifies(self, performer):
        content = renderers.top_performers_content([performer("a", 5, 1)], *SHAABAN)

        assert renderers.HONOURABLE_HEADING not in content

    def test_students_sharing_a_rank_share_a_line(self, performer):
        performers = [performer("one", 12, 1), performer("two", 12, 1)]

        content = renderers.top_performers_content(performers, *SHAABAN)

        first = [li for li in content.splitlines() if li.startswith("- المركز الأول")]
        assert len(first) == 1
        assert " و " in first[0]
        assert first[0].count("ب12 نقطة") == 1

    def test_mentions_students_who_have_a_discord_id(self, performer):
        content = renderers.top_performers_content(
            [performer("linked", 5, 1, discord_id="99")], *SHAABAN
        )

        assert "<@99>" in content

    def test_falls_back_to_the_name_without_a_discord_id(self, performer):
        content = renderers.top_performers_content(
            [performer("unlinked", 5, 1)], *SHAABAN
        )

        assert "<@" not in content
        assert "طالب unlinked" in content

    def test_title_carries_the_hijri_month_and_year(self):
        assert renderers.top_performers_title(*SHAABAN) == "المتصدرون لشهر شعبان 1447"


class TestArabicPointAgreement:
    @pytest.mark.parametrize(
        ("points", "expected"),
        [
            (1, "بنقطة واحدة"),
            (2, "بنقطتين"),
            (3, "ب3 نقاط"),
            (9, "ب9 نقاط"),
            (10, "ب10 نقاط"),
            (11, "ب11 نقطة"),
            (12, "ب12 نقطة"),
        ],
    )
    def test_unit_agrees_with_the_number(self, points, expected):
        assert renderers._points(points) == expected


class TestPoetry:
    def test_the_same_month_always_gets_the_same_verse(self):
        """A rerun edits the posted message, so the verse must not drift."""
        assert poetry.for_month(*SHAABAN) == poetry.for_month(*SHAABAN)

    def test_consecutive_months_differ(self):
        assert poetry.for_month(1447, 8) != poetry.for_month(1447, 9)


@pytest.mark.django_db
class TestAnnouncementMessage:
    def test_pings_in_content_and_body_in_the_embed(self):
        announcement = Announcement(title="عنوان", content="محتوى")

        assert renderers.announcement_message(announcement) == {
            "content": "@everyone",
            "embed": {"title": "عنوان", "description": "محتوى"},
        }

    def test_embed_payload_converts_for_discord(self):
        embed = discord._embed({"title": "عنوان", "description": "محتوى"})

        assert (embed.title, embed.description) == ("عنوان", "محتوى")
