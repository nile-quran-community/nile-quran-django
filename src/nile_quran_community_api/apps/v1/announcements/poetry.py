"""The verse that opens the monthly leaderboard.

Chosen from the Hijri month rather than at random: the announcement can be
regenerated, and a rerun edits the message already in Discord, so the same month has
to keep producing the same verse.

NOTE: Seed list. Verify the attributions and replace these with the community's own
choices — the comments record where each is believed to come from.
"""

# Each entry is one or two أبيات, hemistichs on their own lines.
VERSES: tuple[str, ...] = (
    # الطغرائي — لامية العجم
    """حُبُّ السَلامَةِ يُثني هَمَّ صاحِبِهِ
عَنِ المَعالي وَيُغري المَرءَ بِالكَسَلِ

فَإِن جَنَحتَ إِلَيهِ فَاِتَّخِذ نَفَقاً
في الأَرضِ أَو سُلَّماً في الجَوِّ فَاِعتَزِلِ""",
    # المتنبي
    """عَلى قَدرِ أَهلِ العَزمِ تَأتي العَزائِمُ
وَتَأتي عَلى قَدرِ الكِرامِ المَكارِمُ""",
    # الإمام الشافعي
    """بِقَدرِ الكَدِّ تُكتَسَبُ المَعالي
وَمَن طَلَبَ العُلا سَهِرَ اللَيالي""",
    # أحمد شوقي
    """وَما نَيلُ المَطالِبِ بِالتَمَنّي
وَلَكِن تُؤخَذُ الدُنيا غِلابا""",
    # المتنبي
    """وَلَم أَرَ في عُيوبِ النّاسِ شَيئاً
كَنَقصِ القادِرينَ عَلى التَمامِ""",
)


def for_month(hijri_year: int, hijri_month: int) -> str:
    """The verse for a given Hijri month. Same month, same verse, every time."""

    return VERSES[(hijri_year * 12 + hijri_month) % len(VERSES)]
