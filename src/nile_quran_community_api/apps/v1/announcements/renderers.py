"""Turns announcements into the payload Discord receives.

Every announcement type renders through the same embed; only the monthly leaderboard
has its body generated, and it is generated once and stored on the announcement so the
row stays a faithful record of what was posted.
"""

from ..users.models import User
from .integrations.discord import mention
from .models import Announcement

# NOTE: Placeholder Arabic copy, pending the community's own wording.
TOP_PERFORMERS_TITLE = "المتصدرون لشهر {month} {year}"
TOP_PERFORMERS_INTRO = "بارك الله في جهود إخواننا المتصدرين هذا الشهر:"
TOP_PERFORMERS_LINE = "{rank} {name} — {points} نقطة"
RANKS = ("🥇", "🥈", "🥉")


def top_performers_title(month_name: str, hijri_year: int) -> str:
    return TOP_PERFORMERS_TITLE.format(month=month_name, year=hijri_year)


def _rank_label(rank: int) -> str:
    """A medal for the top three ranks, a plain number for anything below."""
    return RANKS[rank - 1] if rank <= len(RANKS) else f"{rank}."


def top_performers_content(performers: list[User]) -> str:
    """Render the leaderboard body. Students sharing a rank share a medal."""
    lines = [
        TOP_PERFORMERS_LINE.format(
            rank=_rank_label(student.rank),
            name=mention(
                student.discord_id, f"{student.first_name} {student.last_name}"
            ),
            points=student.points,
        )
        for student in performers
    ]
    return "\n".join([TOP_PERFORMERS_INTRO, "", *lines])


def announcement_embed(announcement: Announcement) -> dict:
    return {"title": announcement.title, "description": announcement.content}
