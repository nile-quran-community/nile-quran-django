import dataclasses
import datetime as dt

from django.db.models import F, Prefetch, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from .models import Activity, User


@dataclasses.dataclass(frozen=True)
class Performer:
    """A student's standing in one ranking.

    `rank` belongs here rather than on the user: the same student ranks differently
    from one month to the next, so it is a fact about this result set, not about them.
    """

    user: User
    points: int
    rank: int


def students_with_points(activities: QuerySet[Activity]) -> QuerySet[User]:
    """Active students, annotated with the points they earned in `activities`.

    `points` is the sum of each activity's category value times its multiplier, counted
    in the database so callers can order and filter on it. `scored_activities` holds
    that student's slice of `activities`.
    """

    return (
        User.objects.filter(groups__name="Student", is_active=True)
        .annotate(
            points=Coalesce(
                Sum(
                    F("activities__category__value") * F("activities__multiplier"),
                    filter=Q(activities__in=activities),
                ),
                Value(0),
            )
        )
        .prefetch_related(
            Prefetch("activities", queryset=activities, to_attr="scored_activities")
        )
    )


def top_performers(
    start: dt.datetime,
    end: dt.datetime,
    ranks: int = 3,
) -> list[Performer]:
    """Students holding the top `ranks` point totals for activities in [start, end).

    Ranking is dense: students on equal points share a rank, so asking for 3 ranks can
    return more than 3 students. Students with no points are left out entirely.
    """

    scored = (
        students_with_points(Activity.objects.filter(date__gte=start, date__lt=end))
        .filter(points__gt=0)
        .order_by("-points")
    )

    performers: list[Performer] = []
    rank, previous_points = 0, None
    for student in scored:
        if student.points != previous_points:
            rank, previous_points = rank + 1, student.points
            if rank > ranks:
                break
        performers.append(Performer(user=student, points=student.points, rank=rank))

    return performers
