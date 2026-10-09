import dataclasses
import datetime as dt
import re
import unicodedata
from collections import Counter

from django.db.models import F, Prefetch, QuerySet, Sum

from .models import Activity, User

# Harakat, tatweel and the like: present or absent depending on who typed the name.
_ARABIC_NOISE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u0640]")
# Spelling variants that carry no distinction for matching purposes.
_ARABIC_VARIANTS = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
)


def students_with_points(activities: QuerySet[Activity]) -> list[User]:
    """Active students, each annotated with the points they earned in `activities`.

    `points` is the sum of each activity's category value times its multiplier, and
    `scored_activities` holds that student's slice of `activities`. Runs in a fixed
    number of queries regardless of how many students there are.
    """
    points: dict[int, int] = {
        row["user"]: row["points"]
        for row in activities.values("user").annotate(
            points=Sum(F("category__value") * F("multiplier"))
        )
    }

    students = list(
        User.objects.filter(groups__name="Student", is_active=True).prefetch_related(
            Prefetch("activities", queryset=activities, to_attr="scored_activities")
        )
    )
    for student in students:
        student.points = points.get(student.pk, 0)

    return students


def top_performers(
    start: dt.datetime,
    end: dt.datetime,
    ranks: int = 3,
) -> list[User]:
    """Students holding the top `ranks` point totals for activities in [start, end).

    Ranking is dense: students on equal points share a rank, so asking for 3 ranks can
    return more than 3 students. Students with no points are left out entirely. Each
    returned user carries `points` and `rank`.
    """

    students = students_with_points(
        Activity.objects.filter(date__gte=start, date__lt=end)
    )
    scored = sorted(
        (student for student in students if student.points > 0),
        key=lambda student: student.points,
        reverse=True,
    )

    performers: list[User] = []
    rank, previous_points = 0, None
    for student in scored:
        if student.points != previous_points:
            rank, previous_points = rank + 1, student.points
            if rank > ranks:
                break
        student.rank = rank
        performers.append(student)

    return performers


def normalize_name(name: str) -> str:
    """Fold a name so that spelling variants of it compare equal."""
    folded = unicodedata.normalize("NFKC", name)
    folded = _ARABIC_NOISE.sub("", folded).translate(_ARABIC_VARIANTS)
    return " ".join(folded.split()).casefold()


@dataclasses.dataclass
class DiscordMatches:
    """The outcome of matching community members against a Discord server."""

    linked: dict[int, str] = dataclasses.field(default_factory=dict)
    unmatched: list[User] = dataclasses.field(default_factory=list)
    ambiguous: list[User] = dataclasses.field(default_factory=list)


def match_discord_members(members: list[dict]) -> DiscordMatches:
    """Pair users who have no Discord ID yet with the server members who share a name.

    Deliberately strict: a user is linked only when their name matches exactly one
    member and that member matches exactly one user. A wrong link would mention, and
    later message, the wrong person, so anything uncertain is reported rather than
    guessed at.
    """
    by_name: dict[str, set[str]] = {}
    for member in members:
        for name in member["names"]:
            by_name.setdefault(normalize_name(name), set()).add(member["id"])

    candidates: dict[str, list[User]] = {}
    for user in User.objects.filter(is_active=True, discord_id=""):
        name = normalize_name(f"{user.first_name} {user.last_name}")
        if name:
            candidates.setdefault(name, []).append(user)

    matches = DiscordMatches()
    users = {}
    for name, found in candidates.items():
        discord_ids = by_name.get(name, set())
        users.update({user.pk: user for user in found})
        if len(found) == 1 and len(discord_ids) == 1:
            matches.linked[found[0].pk] = next(iter(discord_ids))
        elif discord_ids:
            matches.ambiguous.extend(found)
        else:
            matches.unmatched.extend(found)

    # One Discord account cannot belong to two people, even if both names fit it.
    contested = Counter(matches.linked.values())
    for pk, discord_id in list(matches.linked.items()):
        if contested[discord_id] > 1:
            del matches.linked[pk]
            matches.ambiguous.append(users[pk])

    return matches
