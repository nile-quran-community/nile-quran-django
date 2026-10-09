"""Turns announcements into the payload Discord receives.

The body goes in an embed, but mentions in an embed render without notifying anyone,
so the `@everyone` that actually reaches the community lives in the message content.
Because that notifies everybody, the mentions inside the embed need only read well.

Only the monthly leaderboard has its body generated, and it is generated once and
stored on the announcement so the row stays a record of what was posted.
"""

from django.conf import settings

from ..users.services import Performer
from . import hijri, poetry
from .integrations.discord import Embed, Message, mention
from .models import Announcement

MENTION_EVERYONE = "@everyone"

# NOTE: Placeholder Arabic copy, pending the community's own wording.
TITLE = "المتصدرون لشهر {month} {year}"
BANNER = "🎊 🎊 🎊 🎊 🎊 🎊 🎊"
INTRO = """الحمد لله مُتِمِّ نعمته، والصلاة والسلام على من سار على هديه، انتهينا من شهر {month}."""
WINNERS_HEADING = "## **إعلان الفائزين**"
WINNERS_LINE = "- المركز {place}: {names} {points} {medal}"
HONOURABLE_HEADING = "**ذكر شرفي**"
HONOURABLE_LINE = "- {names} {points} ✨"

PLACES = {1: "الأول", 2: "الثاني", 3: "الثالث"}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def top_performers_title(hijri_year: int, hijri_month: int) -> str:
    return TITLE.format(
        month=hijri.month_name(hijri_year, hijri_month), year=hijri_year
    )


def _points(points: int) -> str:
    """Arabic number agreement: نقطتان for two, نقاط for three to ten, نقطة beyond."""

    if points == 1:
        return "بنقطة واحدة"
    if points == 2:
        return "بنقطتين"
    return f"ب{points} {'نقاط' if points <= 10 else 'نقطة'}"


def _names(performers: list[Performer]) -> str:
    """Students sharing a rank are listed together on one line."""

    return " و ".join(
        mention(
            performer.user.discord_id,
            f"{performer.user.first_name} {performer.user.last_name}",
        )
        for performer in performers
    )


def _ranked(performers: list[Performer]) -> dict[int, list[Performer]]:
    groups: dict[int, list[Performer]] = {}
    for performer in performers:
        groups.setdefault(performer.rank, []).append(performer)
    return groups


def top_performers_content(
    performers: list[Performer],
    hijri_year: int,
    hijri_month: int,
) -> str:
    """Render the leaderboard body: a verse, the month's greeting, then the ranking."""

    groups = _ranked(performers)
    winning = settings.ANNOUNCEMENTS_WINNING_RANKS
    winners = {rank: students for rank, students in groups.items() if rank <= winning}
    honourable = {rank: students for rank, students in groups.items() if rank > winning}

    blocks = [
        BANNER,
        poetry.for_month(hijri_year, hijri_month),
        BANNER,
        INTRO.format(month=hijri.month_name(hijri_year, hijri_month)),
    ]

    if winners:
        blocks.append(
            "\n".join(
                [WINNERS_HEADING]
                + [
                    WINNERS_LINE.format(
                        place=PLACES[rank],
                        names=_names(winners[rank]),
                        points=_points(winners[rank][0].points),
                        medal=MEDALS[rank],
                    )
                    for rank in sorted(winners)
                ]
            )
        )

    if honourable:
        blocks.append(
            "\n".join(
                [HONOURABLE_HEADING]
                + [
                    HONOURABLE_LINE.format(
                        names=_names(honourable[rank]),
                        points=_points(honourable[rank][0].points),
                    )
                    for rank in sorted(honourable)
                ]
            )
        )

    return "\n\n".join(blocks)


def announcement_embed(announcement: Announcement) -> Embed:
    return {"title": announcement.title, "description": announcement.content}


def announcement_message(announcement: Announcement) -> Message:
    """Ping in the content, body in the embed — an embed on its own notifies nobody."""

    return {
        "content": MENTION_EVERYONE,
        "embed": announcement_embed(announcement),
    }
