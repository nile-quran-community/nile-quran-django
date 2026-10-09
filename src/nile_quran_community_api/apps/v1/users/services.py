import datetime as dt

from django.db.models import F, Prefetch, QuerySet, Sum

from .models import Activity, User


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
