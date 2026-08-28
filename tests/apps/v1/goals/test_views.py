import datetime
from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from nile_quran_community_api.apps.v1.users.models import User


@pytest.mark.django_db
class TestGoalView:
    def test_list_goals_returns_200(self, client: APIClient, existing_user: User):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_goal_returns_200(
        self, client: APIClient, existing_user: User, test_goal
    ):
        client.force_authenticate(user=existing_user)
        response = client.get(f"/goals/{test_goal.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_target_gt_current_returns_201(
        self, client: APIClient, goal_data, admin_user: User, jwt_admin_token: str
    ):
        client.force_authenticate(user=admin_user)
        response = client.post("/goals/", data=goal_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_target_gt_current_returns_correct_data(
        self, client: APIClient, goal_data, jwt_admin_token: str
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.post("/goals/", data=goal_data, format="json")
        assert response.data["scope"] == goal_data["scope"]
        assert response.data["title"] == goal_data["title"]
        assert response.data["description"] == goal_data["description"]
        assert response.data["current"] == goal_data["current"]
        assert response.data["target"] == goal_data["target"]

    @pytest.mark.parametrize("current, target", [(10, 5), (-1, -1), (0, -5), (-6, 0)])
    def test_invalid_target_and_current_returns_400(
        self,
        client: APIClient,
        goal_data,
        current: int,
        target: int,
        jwt_admin_token: str,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        goal_data["target"] = target
        goal_data["current"] = current
        response = client.post("/goals/", data=goal_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_target_lt_current_returns_correct_message(
        self, client: APIClient, goal_data, jwt_admin_token: str
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        goal_data["target"] = 5
        goal_data["current"] = 10
        response = client.post("/goals/", data=goal_data, format="json")
        assert "Current is greater than target" in response.data["non_field_errors"]

    def test_target_lt_current_arabic_translation(
        self, client: APIClient, goal_data, jwt_admin_token: str
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        goal_data["target"] = 5
        goal_data["current"] = 10
        response = client.post(
            "/goals/", data=goal_data, format="json", HTTP_ACCEPT_LANGUAGE="ar"
        )
        assert "القيمة الحالية أكبر من المستهدفة" in response.data["non_field_errors"]


@pytest.mark.django_db
class TestGoalPermissions:
    def test_admin_can_create_goal(
        self, client: APIClient, jwt_admin_token: str, goal_data: dict
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.post("/goals/", data=goal_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_can_partially_modify_goal(
        self,
        client: APIClient,
        jwt_admin_token: str,
        test_goal,
        updated_goal,
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.patch(
            f"/goals/{test_goal.id}/", data=updated_goal, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_fully_modify_goal(
        self, client: APIClient, jwt_admin_token: str, test_goal, updated_goal
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.put(
            f"/goals/{test_goal.id}/", data=updated_goal, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_delete_goal(
        self, client: APIClient, jwt_admin_token: str, test_goal
    ):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_admin_token}")
        response = client.delete(f"/goals/{test_goal.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.parametrize(
        "jwt_token_fixture, expected_status",
        [
            ("jwt_supervisor_token", status.HTTP_403_FORBIDDEN),  # Supervisor user
            (
                "jwt_user_token",
                status.HTTP_403_FORBIDDEN,
            ),  # Non-admin authenticated user
            (None, status.HTTP_401_UNAUTHORIZED),  # Unauthenticated user
        ],
    )
    def test_non_admin_cannot_create_goal(
        self,
        client: APIClient,
        goal_data: dict,
        request,
        jwt_token_fixture,
        expected_status,
    ):
        if jwt_token_fixture:
            jwt_token = request.getfixturevalue(jwt_token_fixture)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
        response = client.post("/goals/", data=goal_data, format="json")
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "jwt_token_fixture, expected_status",
        [
            ("jwt_supervisor_token", status.HTTP_403_FORBIDDEN),
            ("jwt_user_token", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ],
    )
    def test_non_admin_cannot_partially_modify_goal(
        self,
        client: APIClient,
        test_goal,
        updated_goal,
        request,
        jwt_token_fixture,
        expected_status,
    ):
        if jwt_token_fixture:
            jwt_token = request.getfixturevalue(jwt_token_fixture)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
        response = client.patch(
            f"/goals/{test_goal.id}/", data=updated_goal, format="json"
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "jwt_token_fixture, expected_status",
        [
            ("jwt_supervisor_token", status.HTTP_403_FORBIDDEN),
            ("jwt_user_token", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ],
    )
    def test_non_admin_cannot_fully_modify_goal(
        self,
        client: APIClient,
        test_goal,
        updated_goal,
        request,
        jwt_token_fixture,
        expected_status,
    ):
        if jwt_token_fixture:
            jwt_token = request.getfixturevalue(jwt_token_fixture)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
        response = client.put(
            f"/goals/{test_goal.id}/", data=updated_goal, format="json"
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "jwt_token_fixture, expected_status",
        [
            ("jwt_supervisor_token", status.HTTP_403_FORBIDDEN),
            ("jwt_user_token", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ],
    )
    def test_non_admin_cannot_delete_goal(
        self, client: APIClient, test_goal, request, jwt_token_fixture, expected_status
    ):
        if jwt_token_fixture:
            jwt_token = request.getfixturevalue(jwt_token_fixture)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_token}")
        response = client.delete(f"/goals/{test_goal.id}/")
        assert response.status_code == expected_status


@pytest.mark.django_db
class TestGoalFilters:
    def test_filter_by_scope(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?scope=monthly")
        assert response.status_code == status.HTTP_200_OK
        assert all(goal["scope"] == "monthly" for goal in response.data["results"])

    def test_filter_by_title(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?title=Memorization")
        assert response.status_code == status.HTTP_200_OK
        assert all("Memorization" in goal["title"] for goal in response.data["results"])

    def test_filter_by_description(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?description=Revise")
        assert response.status_code == status.HTTP_200_OK
        assert all("Revise" in goal["description"] for goal in response.data["results"])

    def test_filter_by_target_exact(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?target_exact=2")
        assert response.status_code == status.HTTP_200_OK
        assert all(goal["target"] == 2 for goal in response.data["results"])

    def test_filter_by_target_range(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?target_range_min=2&target_range_max=30")
        assert response.status_code == status.HTTP_200_OK
        for goal in response.data["results"]:
            assert 2 <= goal["target"] <= 30

    def test_filter_by_current_exact(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?current_exact=5")
        assert response.status_code == status.HTTP_200_OK
        assert all(goal["current"] == 5 for goal in response.data["results"])

    def test_filter_by_current_range(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?current_range_min=1&current_range_max=10")
        assert response.status_code == status.HTTP_200_OK
        for goal in response.data["results"]:
            assert 1 <= goal["current"] <= 10

    def test_filter_by_created_at_range(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        start_date = date(2025, 5, 4)
        end_date = datetime.datetime.now(tz=datetime.UTC).date()
        response = client.get(
            f"/goals/?created_at_after={start_date}&created_at_before={end_date}"
        )
        assert response.status_code == status.HTTP_200_OK
        for goal in response.data["results"]:
            created_at = date.fromisoformat(goal["created_at"])
            assert start_date <= created_at <= end_date

    def test_multiple_filters(
        self, client: APIClient, goals_for_filtering, existing_user
    ):
        client.force_authenticate(user=existing_user)
        response = client.get("/goals/?scope=monthly&current_exact=5")
        assert response.status_code == status.HTTP_200_OK
        for goal in response.data["results"]:
            assert goal["scope"] == "monthly"
            assert goal["current"] == 5
