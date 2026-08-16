from datetime import timedelta

import pytest
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from nile_quran_community_api.apps.v1.users.models import Activity, Category, User
from nile_quran_community_api.apps.v1.users.serializers import UserSerializer


@pytest.mark.django_db
class TestUserAPI:
    def test_get_user_details(
        self, client: APIClient, existing_user: User, jwt_admin_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get(f"/users/{existing_user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == existing_user.username

    def test_get_nonexistent_user(self, client: APIClient, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get("/users/999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_current_user(
        self, client: APIClient, existing_user: User, jwt_user_token: str
    ) -> None:
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
        response: Response = client.get("/users/me/")
        serialized_user: dict = UserSerializer(existing_user).data
        assert response.json() == serialized_user


@pytest.mark.django_db
class TestUserPermissions:
    def test_admin_can_list_users(self, client, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get("/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_update_user(
        self, client, existing_user: User, jwt_admin_token, admin_user
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        data = {"username": "updated_username", "user": existing_user.id}
        response = client.patch(f"/users/{existing_user.id}/", data, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_delete_user(self, client, jwt_admin_token, existing_user: User):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.delete(f"/users/{existing_user.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_cannot_update_other_users(
        self, client, existing_user: User, jwt_user_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
        data = {"groups": ["Admin"]}
        response = client.patch(f"/users/{existing_user.id}/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_delete_other_users(
        self, client, existing_user: User, jwt_supervisor_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")
        data = {"username": "deleted_user"}
        response = client.delete(f"/users/{existing_user.id}/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_user_cannot_update_other_users(
        self, client, existing_user: User, jwt_supervisor_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")
        data = {"username": "updated_user"}
        response = client.patch(f"/users/{existing_user.id}/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_user_cannot_delete_other_users(
        self, client, existing_user: User, jwt_supervisor_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")
        data = {"username": "delete_user"}
        response = client.delete(f"/users/{existing_user.id}/", data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUserActivityPermissions:
    def test_user_can_list_activities(
        self, client, existing_user: User, jwt_user_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
        response = client.get(f"/users/{existing_user.id}/activities/")
        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_modify_activity(
        self, client, jwt_user_token, activity: Activity
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
        data = {"category": activity.category.id, "user": activity.user.id}
        response = client.patch(
            f"/users/{activity.user.id}/activities/{activity.id}/", data, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_delete_activity(
        self, client, existing_user: User, jwt_user_token, activity: Activity
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_user_token}")
        response = client.delete(f"/users/{activity.user.id}/activities/{activity.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSupervisorActivityPermissions:
    def test_supervisor_can_list_activities(
        self, client, existing_user: User, jwt_supervisor_token
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")
        response = client.get(f"/users/{existing_user.id}/activities/")
        assert response.status_code == status.HTTP_200_OK

    def test_supervisor_can_modify_activity(
        self, client, supervisor_user, jwt_supervisor_token, activity: Activity
    ):
        activity.user.supervisor = supervisor_user
        activity.user.save()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")

        data = {"category": activity.category.id, "user": activity.user.id}
        response = client.patch(
            f"/users/{activity.user.id}/activities/{activity.id}/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_supervisor_can_delete_activity(
        self, client, supervisor_user, jwt_supervisor_token, activity: Activity
    ):
        activity.user.supervisor = supervisor_user
        activity.user.save()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_supervisor_token}")

        response = client.delete(f"/users/{activity.user.id}/activities/{activity.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestAdminActivityPermissions:
    def test_admin_can_list_activities(
        self, client, jwt_admin_token, existing_user: User
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get(f"/users/{existing_user.id}/activities/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_modify_activity(
        self, client, jwt_admin_token, activity: Activity
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        data = {"category": activity.category.id, "user": activity.user.id}
        response = client.patch(
            f"/users/{activity.user.id}/activities/{activity.id}/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_delete_activity(
        self, client, jwt_admin_token, activity: Activity
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.delete(f"/users/{activity.user.id}/activities/{activity.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestUserPointsAPI:
    def test_get_all_users_points(
        self,
        client: APIClient,
        existing_user: User,
        admin_user,
        activity: Activity,
        jwt_admin_token,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get("/users/points/")
        expected_data = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "user": existing_user.id,
                    "points": 1,
                    "activities": [
                        {
                            "id": activity.id,
                            "category": activity.category.id,
                            "date": activity.date,
                            "multiplier": activity.multiplier,
                        }
                    ],
                },
            ],
        }
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        assert response.data == expected_data

    def test_get_user_points_by_id(
        self,
        client: APIClient,
        jwt_admin_token,
        existing_user: User,
        activity: Activity,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get(f"/users/{existing_user.id}/points/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == existing_user.id
        assert User.objects.filter(id=existing_user.id).exists(), (
            "User does not exist in test DB"
        )
        assert "points" in response.data
        assert "activities" in response.data

    def test_get_user_points_no_activities(
        self, client: APIClient, jwt_admin_token, existing_user: User
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get(f"/users/{existing_user.id}/points/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == existing_user.id
        assert response.data["points"] == 0
        assert list(response.data["activities"]) == []

    def test_get_nonexistent_user_points(self, client: APIClient, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get("/users/999999/points/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_user_points_by_category(
        self,
        client,
        jwt_admin_token,
        existing_user: User,
        category: Category,
        activity: Activity,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get(
            f"/users/{existing_user.id}/points/?category={category.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == existing_user.id
        assert "points" in response.data
        assert "activities" in response.data

    def test_filter_user_points_by_date_range(
        self,
        client,
        jwt_admin_token,
        existing_user: User,
        category: Category,
        activity: Activity,
    ):
        past_activity = Activity.objects.create(
            user=existing_user,
            category=category,
            date=(now() - timedelta(days=10)).strftime("%Y-%m-%dT00:00:00Z"),
        )
        future_activity = Activity.objects.create(
            user=existing_user,
            category=category,
            date=(now() + timedelta(days=10)).strftime("%Y-%m-%dT00:00:00Z"),
        )

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response: Response = client.get(
            f"/users/{existing_user.id}/points/?date_after={(now() - timedelta(days=5)).strftime('%Y-%m-%d')}&date_before={(now() + timedelta(days=5)).strftime('%Y-%m-%d')}"
        )
        activites_ids: list[int] = map(
            lambda act: act["id"], response.data["activities"]
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == existing_user.id
        assert past_activity.id not in activites_ids
        assert future_activity.id not in activites_ids

    def test_filter_user_points_by_category_and_date(
        self,
        client,
        jwt_admin_token,
        existing_user: User,
        activity: Activity,
        category: Category,
    ):
        today = now().date()
        category2 = Category.objects.create(name="Test 2", value=5)
        valid_activity = Activity.objects.create(
            user=existing_user,
            category=category,
            date=today.strftime("%Y-%m-%dT00:00:00Z"),
        )
        invalid_activity = Activity.objects.create(
            user=existing_user,
            category=category2,
            date=today.strftime("%Y-%m-%dT00:00:00Z"),
        )

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get(
            f"/users/{existing_user.id}/points/?category={category.id}&date_after={(today - timedelta(days=5)).strftime('%Y-%m-%d')}&date_before={today.strftime('%Y-%m-%d')}"
        )
        activites_ids: list[int] = map(
            lambda act: act["id"], response.data["activities"]
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == existing_user.id
        assert valid_activity.id in activites_ids
        assert invalid_activity.id not in activites_ids


@pytest.mark.django_db
class TestCategoryPointsAPI:
    def test_get_all_categories(
        self, client: APIClient, jwt_admin_token, category: Category
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get("/users/points/categories/")

        assert response.status_code == status.HTTP_200_OK

    def test_filter_categories_by_id(
        self, client: APIClient, jwt_admin_token, category: Category
    ):
        """Test filtering categories by a valid category ID."""
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get(f"/users/points/categories/?id={category.id}")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == category.id

    def test_filter_categories_by_name(
        self, client: APIClient, jwt_admin_token, category: Category
    ):
        """Test filtering categories by a valid category name."""
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get(f"/users/points/categories/?name={category.name}")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == category.name

    def test_filter_with_invalid_category_id(self, client: APIClient, jwt_admin_token):
        """Test filtering with a category ID that does not exist."""
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get("/users/points/categories/?id=999999")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_filter_categories_by_value(
        self, client: APIClient, jwt_admin_token, category: Category
    ):
        """Test filtering categories by a valid category value."""
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get(f"/users/points/categories/?value={category.value}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["value"] == category.value

    def test_empty_category_list(self, client: APIClient, jwt_admin_token):
        """Ensure API returns an empty list when no categories exist."""
        Category.objects.all().delete()

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.get("/users/points/categories/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []


@pytest.mark.django_db
class TestUserActivitiesMultiplier:
    def test_create_activity_with_multiplier(
        self,
        jwt_admin_token,
        client: APIClient,
        existing_user: User,
        category: Category,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        payload = {
            "category": category.id,
            "multiplier": 5,
            "date": "2025-12-07T05:55:07Z",
        }

        response = client.post(
            f"/users/{existing_user.id}/activities/",
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {"id": 1, **payload}

    def test_create_activity_without_multiplier_defaults_to_one(
        self,
        jwt_admin_token,
        client: APIClient,
        existing_user: User,
        category: Category,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        payload = {
            "category": category.id,
            "date": "2025-12-07T05:55:07Z",
        }

        response = client.post(
            f"/users/{existing_user.id}/activities/",
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert (
            Activity.objects.filter(
                user=existing_user,
                category=category,
            ).count()
            == 1
        )

    def test_create_activity_with_invalid_multiplier(
        self,
        jwt_admin_token,
        client: APIClient,
        existing_user: User,
        category: Category,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        payload = {
            "category": category.id,
            "multiplier": 0,
            "date": "2025-12-07T05:55:07Z",
        }

        response = client.post(
            f"/users/{existing_user.id}/activities/",
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "multiplier" in response.data


@pytest.mark.django_db
class TestI18nAPI:
    def test_categories_translation_arabic(self, client, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        Category.objects.create(name="Attending thought session", value=1)

        # English
        response = client.get("/users/points/categories/", HTTP_ACCEPT_LANGUAGE="en")
        assert response.status_code == status.HTTP_200_OK
        assert any(
            "Attending thought session" in item.get("name", "")
            for item in response.data["results"]
        )

        # Arabic
        response = client.get("/users/points/categories/", HTTP_ACCEPT_LANGUAGE="ar")
        assert response.status_code == status.HTTP_200_OK
        assert any(
            "حضور جلسة الخاطرة" in item.get("name", "")
            for item in response.data["results"]
        )

    def test_404_translation(self, client, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")

        # English
        response = client.get("/users/999999/activities/", HTTP_ACCEPT_LANGUAGE="en")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No user was found with the given ID." in response.data["detail"]

        # Arabic
        response = client.get("/users/999999/activities/", HTTP_ACCEPT_LANGUAGE="ar")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "لم يتم العثور على مستخدم بالمعرف المحدد." in response.data["detail"]

    def test_user_not_found_translation(self, client, jwt_admin_token):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")

        # English
        response = client.get("/users/99999/", HTTP_ACCEPT_LANGUAGE="en")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No User matches the given query." in response.data["detail"]

        # Arabic
        response = client.get("/users/99999/", HTTP_ACCEPT_LANGUAGE="ar")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            "لم يتم العثور على مستخدم يطابق الاستعلام المحدد."
            in response.data["detail"]
        )
