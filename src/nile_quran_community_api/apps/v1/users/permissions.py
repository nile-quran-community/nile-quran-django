from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from . import models


def is_admin_user(request: Request) -> bool:
    return request.user.groups.filter(name="Admin").exists()


class CanCreateUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return not any(field in request.data for field in ("groups", "supervisor"))

        return request.user.has_perm("users.add_user")


class CanModifyUser(BasePermission):
    def __init__(self) -> None:
        # WARN: only admins can edit the following fields of a user
        self._ADMIN_ONLY_FIELDS: tuple[str, ...] = (
            "referrer",
            "supervisor",
            "groups",
            "is_active",
        )

    def _admin_only_change(self, request: Request) -> bool:
        return any(field in request.data for field in self._ADMIN_ONLY_FIELDS)

    def has_object_permission(
        self, request: Request, view: APIView, obj: models.User
    ) -> bool:
        if self._admin_only_change(request):
            return is_admin_user(request)

        return obj == request.user or request.user.has_perm("users.change_user")


class CanModifyActivity(BasePermission):
    def _supervisor(self, view: APIView) -> models.User | None:
        student_id: int | None = view.kwargs.get("uid")
        if not student_id:
            return None

        return models.User.objects.get(id=student_id).supervisor

    def has_permission(self, request: Request, view: APIView):
        supervisor: models.User | None = self._supervisor(view)
        if supervisor:
            return request.user == supervisor

        return is_admin_user(request)

    def has_object_permission(
        self, request: Request, view: APIView, obj: models.Activity
    ) -> bool:
        return is_admin_user(request) or request.user == obj.user.supervisor
