import typing as t

from django.db.models import F, QuerySet, Sum
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from . import filters, models, serializers
from . import permissions as userperms


@extend_schema_view(
    create=extend_schema(
        auth=[],
        examples=[
            OpenApiExample(
                name="User Signup",
                value={
                    "username": "ahmed",
                    "email": "user@example.com",
                    "password": "password",
                    "first_name": "أحمد",
                    "last_name": "محمد",
                    "referrer": "username",
                },
            )
        ],
    )
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    filterset_class = filters.UserFilter

    def get_permissions(self) -> t.Sequence[permissions.BasePermission]:
        permission_classes: t.Sequence[type[permissions.BasePermission]] = []
        if self.action == "create":
            permission_classes = [userperms.CanCreateUser]
        elif self.action in ("list", "retrieve", "current_user"):
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ("update", "partial_update"):
            permission_classes = [permissions.IsAuthenticated, userperms.CanModifyUser]
        elif self.action == "destroy":
            permission_classes = [permissions.IsAuthenticated, userperms.CanDeleteUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["GET"], url_path="me")
    def current_user(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserActivitiesViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActivitySerializer
    filterset_class = filters.UserActivitiesFilter

    def get_permissions(self) -> t.Sequence[permissions.BasePermission]:
        permission_classes: t.Sequence[type[permissions.BasePermission]] = []
        if self.action in ("list", "retrieve"):
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [
                permissions.IsAuthenticated,
                userperms.CanModifyActivity,
            ]

        return [permission() for permission in permission_classes]

    def get_user(self) -> models.User:
        uid: int | None = self.kwargs.get("uid")
        user = models.User.objects.filter(id=uid).first()
        if not user:
            raise NotFound(detail=_("No user was found with the given ID."))
        return user

    def get_queryset(self) -> QuerySet[models.Activity]:
        if getattr(self, "swagger_fake_view", False):
            return models.Activity.objects.none()

        return models.Activity.objects.filter(user=self.get_user())

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.get_user())

    def perform_update(self, serializer) -> None:
        serializer.save(user=self.get_user())


class UserPointsListView(generics.ListAPIView):
    queryset = models.Activity.objects.all()
    serializer_class = serializers.UserPointsSerializer
    filterset_class = filters.ActivitiesFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="ordering",
                description="Ordering",
                many=True,
                type=str,
                enum=("points", "-points"),
                required=False,
            )
        ]
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        response_data: list[dict] = []
        activities: QuerySet[models.Activity] = self.filter_queryset(
            self.get_queryset()
        )
        students: QuerySet[models.User] = models.User.objects.filter(
            groups__name="Student", is_active=True
        )

        for student in students:
            acts: QuerySet[models.Activity] = activities.filter(user=student)
            points: int = (
                acts.aggregate(points=Sum(F("category__value") * F("multiplier")))[
                    "points"
                ]
                or 0
            )
            response_data.append(
                {
                    "user": student.pk,
                    "points": points,
                    "activities": acts,
                }
            )

        # NOTE: sort response data based on the defined ordering fields
        ordering: list[str] = request.GET.get("ordering", "").split(",")
        sorted_data: list[dict] = response_data
        for field in ("points",):
            if field in ordering or f"-{field}" in ordering:
                sorted_data = sorted(
                    sorted_data,
                    key=lambda x: x[field],
                    reverse=(f"-{field}" in ordering),
                )

        page: t.Sequence[t.Any] | None = self.paginate_queryset(sorted_data)
        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sorted_data, many=True)
        return Response(serializer.data)


class UserPointsView(generics.RetrieveAPIView):
    serializer_class = serializers.UserPointsSerializer
    filterset_class = filters.ActivitiesFilter

    def get_user(self) -> models.User:
        uid: int | None = self.kwargs.get("id")
        user = models.User.objects.filter(id=uid).first()
        if not user:
            raise NotFound(detail=_("No user was found with the given ID."))
        return user

    def get_queryset(self):
        user = self.get_user()
        return models.Activity.objects.filter(user=user)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="category", type=int, required=False),
            OpenApiParameter(
                name="date_after",
                type=str,
                required=False,
            ),
            OpenApiParameter(
                name="date_before",
                type=str,
                required=False,
            ),
        ]
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        activities: QuerySet[models.Activity] = self.filter_queryset(
            self.get_queryset()
        )
        points: int = (
            activities.aggregate(points=Sum(F("category__value") * F("multiplier")))[
                "points"
            ]
            or 0
        )

        user: models.User = self.get_user()
        response_data: dict = {
            "user": user.pk,
            "points": points,
            "activities": activities,
        }

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)


class CategoryPointsListView(generics.ListAPIView):
    serializer_class = serializers.CategorySerializer
    filterset_class = filters.CategoryFilter

    def get_queryset(self) -> QuerySet[models.Category]:
        queryset = models.Category.objects.all()
        return queryset

    def get(self, request: Request, *args, **kwargs) -> Response:
        categories: QuerySet[models.Category] = self.filter_queryset(
            self.get_queryset()
        )

        page: t.Sequence[dict] | None = self.paginate_queryset(categories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
