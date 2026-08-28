import datetime

import pytest
from django.core.management import call_command

from nile_quran_community_api.apps.v1.goals.models import Goal


@pytest.fixture
def test_goal(db) -> Goal:
    goal = Goal.objects.create(
        title="goal 1",
        description="goal 1 description",
        target=10,
        current=5,
    )
    return goal


@pytest.fixture
def goal_data() -> dict:
    return {
        "scope": "monthly",
        "title": "goal 1",
        "description": "goal 1 description",
        "target": 10,
        "current": 5,
        "created_at": datetime.datetime.now(tz=datetime.UTC).date(),
    }


@pytest.fixture(autouse=True, scope="function")
def load_data(db, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("setuproles")


@pytest.fixture
def updated_goal() -> dict:
    return {
        "scope": "yearly",
        "title": "new title",
        "description": "new description",
        "target": 5,
        "current": 1,
    }


@pytest.fixture
def goals_for_filtering(db):
    from nile_quran_community_api.apps.v1.goals.models import Goal

    goals = [
        Goal.objects.create(
            scope="monthly",
            title="Quran Reading",
            description="Read 5 pages daily",
            target=30,
            current=10,
            created_at=datetime.date(2025, 3, 2),
        ),
        Goal.objects.create(
            scope="yearly",
            title="Memorization",
            description="Memorize 2 surahs",
            target=2,
            current=1,
            created_at=datetime.date(2025, 2, 24),
        ),
        Goal.objects.create(
            scope="monthly",
            title="Revision",
            description="Revise Juz Amma",
            target=5,
            current=5,
            created_at=datetime.date(2025, 7, 25),
        ),
    ]
    return goals
