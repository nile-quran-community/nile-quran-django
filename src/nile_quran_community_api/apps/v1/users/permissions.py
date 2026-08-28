from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from . import models


class CanCreateUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return not any(field in request.data for field in ("groups", "supervisor"))

        return request.user.groups.filter(name="Admin").exists()


class CanModifyUser(BasePermission):
    def __init__(self) -> None:
        # WARN: only admins can edit the following fields of a user
        self._ADMIN_ONLY_FIELDS: tuple[str, ...] = (
            "referrer",
            "supervisor",
            "groups",
            "is_active",
        )

    def has_object_permission(
        self, request: Request, view: APIView, obj: models.User
    ) -> bool:
        if not request.user:
            return False
        if any(field in request.data for field in self._ADMIN_ONLY_FIELDS):
            return request.user.groups.filter(name="Admin").exists()
        return obj == request.user or request.user.has_perm("users.change_user")


class CanDeleteUser(BasePermission):
    def has_object_permission(
        self, request: Request, view: APIView, obj: models.User
    ) -> bool:
        if request.user and request.user.has_perm("users.delete_user"):
            return True
        return obj == request.user


class CanModifyActivity(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user is not None
            and request.user.is_authenticated
            and (
                request.user.groups.filter(name="Admin").exists()
                or request.user
                == models.User.objects.get(id=view.kwargs.get("uid")).supervisor
            )
        )

    def has_object_permission(
        self, request: Request, view: APIView, obj: models.Activity
    ) -> bool:
        return (
            request.user is not None
            and request.user.is_authenticated
            and (
                request.user.groups.filter(name="Admin").exists()
                or request.user
                == models.User.objects.get(id=view.kwargs.get("uid")).supervisor
            )
        )
