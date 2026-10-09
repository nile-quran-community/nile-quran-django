"""Turns announcements into the payload Discord receives.

The body goes in an embed, but mentions in an embed render without notifying anyone,
so the `@everyone` that actually reaches the community lives in the message content.
Because that notifies everybody, the mentions inside the embed need only read well.

Only the monthly leaderboard has its body generated, and it is generated once and
stored on the announcement so the row stays a record of what was posted.
"""

from django.conf import settings

from ..users.services import Performer
from . import hijri
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
VERSES: tuple[str, ...] = (
    # الطغرائي — لامية العجم
    """حُبُّ السَلامَةِ يُثني هَمَّ صاحِبِهِ
عَنِ المَعالي وَيُغري المَرءَ بِالكَسَلِ

فَإِن جَنَحتَ إِلَيهِ فَاِتَّخِذ نَفَقاً
في الأَرضِ أَو سُلَّماً في الجَوِّ فَاِعتَزِلِ""",
    # المتنبي
    """عَلى قَدرِ أَهلِ العَزمِ تَأتي العَزائِمُ
وَتَأتي عَلى قَدرِ الكِرامِ المَكارِمُ

وَتَعظُمُ في عَينِ الصَغيرِ صِغارُها
وَتَصغُرُ في عَينِ العَظيمِ العَظائِمُ""",
    # الإمام الشافعي
    """بِقَدرِ الكَدِّ تُكتَسَبُ المَعالي
وَمَن طَلَبَ العُلا سَهِرَ اللَيالي""",
    # أحمد شوقي
    """وَما نَيلُ المَطالِبِ بِالتَمَنّي
وَلَكِن تُؤخَذُ الدُنيا غِلابا""",
    # المتنبي
    """وَلَم أَرَ في عُيوبِ النّاسِ شَيئاً
كَنَقصِ القادِرينَ عَلى التَمامِ""",
    # المتنبي
    """إِذا غامَرتَ في شَرَفٍ مَرومِ
فَلا تَقنَع بِما دونَ النُجومِ

فَطَعمُ المَوتِ في أَمرٍ حَقيرٍ
كَطَعمِ المَوتِ في أَمرٍ عَظيمِ""",
    # المتنبي
    """وَإِذا كانَتِ النُفوسُ كِباراً
تَعِبَت في مُرادِها الأَجسامُ""",
    # المتنبي
    """ذَريني أَنَل ما لا يُنالُ مِنَ العُلا
فَصَعبُ العُلا في الصَعبِ وَالسَهلُ في السَهلِ

تُريدينَ لُقيانَ المَعالي رَخيصَةً
وَلا بُدَّ دونَ الشَهدِ مِن إِبَرِ النَحلِ""",
    # الإمام الشافعي
    """أَخي لَن تَنالَ العِلمَ إِلّا بِسِتَّةٍ
سَأُنبيكَ عَن تَفصيلِها بِبَيانِ

ذَكاءٌ وَحِرصٌ وَاِجتِهادٌ وَبُلغَةٌ
وَصُحبَةُ أُستاذٍ وَطولُ زَمانِ""",
    # الإمام الشافعي
    """شَكَوتُ إِلى وَكيعٍ سوءَ حِفظي
فَأَرشَدَني إِلى تَركِ المَعاصي

وَأَخبَرَني بِأَنَّ العِلمَ نورٌ
وَنورُ اللَهِ لا يُهدى لِعاصي""",
    # الإمام الشافعي
    """تَعَلَّم فَلَيسَ المَرءُ يولَدُ عالِماً
وَلَيسَ أَخو عِلمٍ كَمَن هُوَ جاهِلُ""",
    # الإمام الشافعي
    """وَمَن لَم يَذُق مُرَّ التَعَلُّمِ ساعَةً
تَجَرَّعَ ذُلَّ الجَهلِ طولَ حَياتِهِ""",
    # الإمام الشافعي
    """سَأَضرِبُ في طولِ البِلادِ وَعَرضِها
أَنالُ مُرادي أَو أَموتُ غَريبا""",
    # الإمام الشاطبي — حرز الأماني
    """وَإِنَّ كِتابَ اللَهِ أَوثَقُ شافِعٍ
وَأَغنى غَناءٍ واهِباً مُتَفَضِّلا

وَخَيرُ جَليسٍ لا يُمَلُّ حَديثُهُ
وَتَردادُهُ يَزدادُ فيهِ تَجَمُّلا""",
    # ابن الوردي — اللامية
    """اُطلُبِ العِلمَ وَلا تَكسَل فَما
أَبعَدَ الخَيرَ عَلى أَهلِ الكَسَل""",
    # أبو فراس الحمداني
    """تَهونُ عَلَينا في المَعالي نُفوسُنا
وَمَن خَطَبَ الحَسناءَ لَم يُغلِها المَهرُ""",
    # أبو العلاء المعري
    """وَإِنّي وَإِن كُنتُ الأَخيرَ زَمانُهُ
لَآتٍ بِما لَم تَستَطِعهُ الأَوائِلُ""",
)


def verse_for_month(hijri_year: int, hijri_month: int) -> str:
    """The verse that opens a month's leaderboard.

    Picked from the month rather than at random: the announcement can be regenerated
    and a rerun edits the message already in Discord, so the same month has to keep
    producing the same verse.
    """

    return VERSES[(hijri_year * 12 + hijri_month) % len(VERSES)]


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
        verse_for_month(hijri_year, hijri_month),
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
