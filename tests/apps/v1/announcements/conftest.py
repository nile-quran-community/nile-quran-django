import datetime as dt

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from nile_quran_community_api.apps.v1.users.models import Activity, Category, User

# A date that falls on 1 Ramadan 1447 in the Umm al-Qura calendar, so the generate
# command treats it as a month start without needing to mock the clock.
RAMADAN_1447_START = dt.date(2026, 2, 18)


@pytest.fixture(autouse=True, scope="function")
def load_data(db, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("flush", "--no-input")
        call_command("setuproles")


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Reciting Quran", value=1)


@pytest.fixture
def make_student(db, category: Category):
    """Build an active student holding `points` points inside the given month."""
    students = Group.objects.get(name="Student")

    def _make(username: str, points: int, date: dt.date, discord_id: str = "") -> User:
        student = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass",
            first_name="طالب",
            last_name=username,
            discord_id=discord_id,
        )
        student.groups.add(students)
        if points:
            Activity.objects.create(
                user=student,
                category=category,
                multiplier=points,
                date=dt.datetime.combine(date, dt.time(12, 0), tzinfo=dt.UTC),
            )
        return student

    return _make
