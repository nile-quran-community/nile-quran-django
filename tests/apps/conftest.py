import pytest
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import AccessToken

from nile_quran_community_api.apps.v1.users.models import User


@pytest.fixture
def existing_user(db) -> User:
    group, _ = Group.objects.get_or_create(name="Student")
    user = User.objects.create_user(
        email="existinguser@example.com",
        username="existinguser",
        password="testpass",
        first_name="Existing",
        last_name="User",
    )
    user.groups.add(group)
    return user


@pytest.fixture
def admin_user(db) -> User:
    group = Group.objects.get(name="Admin")
    admin = User.objects.create_user(
        email="admin@example.com",
        username="adminuser",
        password="adminpass",
        first_name="Admin",
        last_name="User",
    )
    admin.groups.add(group)
    return admin


@pytest.fixture
def supervisor_user(db):
    group, _ = Group.objects.get_or_create(name="Supervisor")
    supervisor = User.objects.create_user(
        email="supervisor@example.com",
        username="supervisoruser",
        password="supervisorpass",
        first_name="Supervisor",
        last_name="User",
    )
    supervisor.groups.add(group)
    return supervisor


@pytest.fixture
def media_user(db) -> User:
    group = Group.objects.get(name="Media")
    media = User.objects.create_user(
        email="media@example.com",
        username="mediauser",
        password="mediapass",
        first_name="Media",
        last_name="User",
    )
    media.groups.add(group)
    return media


@pytest.fixture
def jwt_user_token(existing_user) -> str:
    token = AccessToken.for_user(existing_user)
    return str(token)


@pytest.fixture
def jwt_admin_token(admin_user) -> str:
    token = AccessToken.for_user(admin_user)
    return str(token)


@pytest.fixture
def jwt_supervisor_token(supervisor_user) -> str:
    token = AccessToken.for_user(supervisor_user)
    return str(token)


@pytest.fixture
def jwt_media_token(media_user) -> str:
    token = AccessToken.for_user(media_user)
    return str(token)
