import datetime as dt

import pytest
from django.contrib.auth.models import Group

from nile_quran_community_api.apps.v1.users.models import Activity, Category, User
from nile_quran_community_api.apps.v1.users.services import top_performers

WINDOW_START = dt.datetime(2026, 1, 20, tzinfo=dt.UTC)
WINDOW_END = dt.datetime(2026, 2, 18, tzinfo=dt.UTC)
INSIDE = dt.datetime(2026, 2, 1, 12, 0, tzinfo=dt.UTC)


@pytest.fixture
def make_student(db):
    category = Category.objects.create(name="Reciting Quran", value=1)
    students = Group.objects.get(name="Student")

    def _make(username, points, date=INSIDE, is_active=True):
        student = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass",
            is_active=is_active,
        )
        student.groups.add(students)
        if points:
            Activity.objects.create(
                user=student, category=category, multiplier=points, date=date
            )
        return student

    return _make


@pytest.mark.django_db
class TestTopPerformers:
    def test_ranks_by_points_descending(self, make_student):
        make_student("third", 3)
        make_student("first", 10)
        make_student("second", 5)

        performers = top_performers(WINDOW_START, WINDOW_END)

        assert [p.username for p in performers] == ["first", "second", "third"]
        assert [p.rank for p in performers] == [1, 2, 3]

    def test_ties_share_a_rank_and_both_are_returned(self, make_student):
        make_student("tied_a", 10)
        make_student("tied_b", 10)
        make_student("next", 5)

        performers = top_performers(WINDOW_START, WINDOW_END)

        assert {p.username for p in performers[:2]} == {"tied_a", "tied_b"}
        assert [p.rank for p in performers] == [1, 1, 2]

    def test_a_tie_at_the_cutoff_returns_more_than_three_students(self, make_student):
        make_student("first", 10)
        make_student("second", 8)
        for name in ("third_a", "third_b", "third_c"):
            make_student(name, 5)

        performers = top_performers(WINDOW_START, WINDOW_END)

        assert len(performers) == 5
        assert [p.rank for p in performers] == [1, 2, 3, 3, 3]

    def test_students_below_the_third_rank_are_dropped(self, make_student):
        for points in (10, 8, 5, 3, 1):
            make_student(f"student_{points}", points)

        performers = top_performers(WINDOW_START, WINDOW_END)

        assert [p.points for p in performers] == [10, 8, 5]

    def test_students_without_points_are_excluded(self, make_student):
        make_student("active", 4)
        make_student("idle", 0)

        assert [p.username for p in top_performers(WINDOW_START, WINDOW_END)] == [
            "active"
        ]

    def test_activity_outside_the_window_does_not_count(self, make_student):
        make_student("inside", 4)
        make_student("before", 99, date=WINDOW_START - dt.timedelta(days=1))
        make_student("after", 99, date=WINDOW_END)

        assert [p.username for p in top_performers(WINDOW_START, WINDOW_END)] == [
            "inside"
        ]

    def test_inactive_students_are_excluded(self, make_student):
        make_student("active", 4)
        make_student("deactivated", 99, is_active=False)

        assert [p.username for p in top_performers(WINDOW_START, WINDOW_END)] == [
            "active"
        ]

    def test_non_students_are_excluded(self, make_student, admin_user):
        make_student("student", 4)
        Activity.objects.create(
            user=admin_user,
            category=Category.objects.first(),
            multiplier=99,
            date=INSIDE,
        )

        assert [p.username for p in top_performers(WINDOW_START, WINDOW_END)] == [
            "student"
        ]

    def test_points_sum_category_value_times_multiplier(self, make_student):
        student = make_student("student", 0)
        category = Category.objects.create(name="Preparing a thought", value=2)
        Activity.objects.create(
            user=student, category=category, multiplier=3, date=INSIDE
        )

        assert top_performers(WINDOW_START, WINDOW_END)[0].points == 6

    def test_no_qualifying_students_returns_empty(self, make_student):
        make_student("idle", 0)

        assert top_performers(WINDOW_START, WINDOW_END) == []
