import django_filters
from django.utils.translation import gettext_lazy as _

from . import models


class UserFilter(django_filters.FilterSet):
    """Filter set for UserViewSet with ordering and search functionality."""

    ordering = django_filters.OrderingFilter(
        fields=(
            ("username", "username"),
            ("email", "email"),
            ("first_name", "first_name"),
            ("last_name", "last_name"),
        ),
        field_labels={
            "username": _("Username"),
            "email": _("Email"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
        },
    )

    email: django_filters.CharFilter = django_filters.CharFilter(
        field_name="email", lookup_expr="icontains"
    )
    username: django_filters.CharFilter = django_filters.CharFilter(
        field_name="username", lookup_expr="icontains"
    )
    username_exact: django_filters.CharFilter = django_filters.CharFilter(
        field_name="username", lookup_expr="iexact"
    )
    first_name: django_filters.CharFilter = django_filters.CharFilter(
        field_name="first_name", lookup_expr="icontains"
    )
    last_name: django_filters.CharFilter = django_filters.CharFilter(
        field_name="last_name", lookup_expr="icontains"
    )
    referrer: django_filters.CharFilter = django_filters.CharFilter(
        field_name="referrer__username", lookup_expr="exact"
    )
    supervisor: django_filters.CharFilter = django_filters.CharFilter(
        field_name="supervisor__username", lookup_expr="exact"
    )
    group: django_filters.CharFilter = django_filters.CharFilter(
        field_name="groups__name", lookup_expr="iexact"
    )
    faculty: django_filters.CharFilter = django_filters.CharFilter(
        field_name="faculty", lookup_expr="exact"
    )
    academic_year: django_filters.CharFilter = django_filters.CharFilter(
        field_name="academic_year", lookup_expr="exact"
    )
    tajweed_level: django_filters.CharFilter = django_filters.CharFilter(
        field_name="tajweed_level", lookup_expr="exact"
    )

    class Meta:
        model = models.User
        fields: list[str] = []


class UserActivitiesFilter(django_filters.FilterSet):
    """Filter set for UserActivitiesViewSet with category and date filtering."""

    ordering = django_filters.OrderingFilter(
        fields=(
            ("date", "date"),
            ("category__id", "category"),
        ),
        field_labels={
            "date": _("Activity Date"),
            "category__id": _("Category"),
        },
    )

    category = django_filters.NumberFilter(field_name="category", lookup_expr="exact")
    date = django_filters.DateFromToRangeFilter(field_name="date")

    class Meta:
        model = models.Activity
        fields: list[str] = []


class ActivitiesFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(field_name="date")
    category = django_filters.NumberFilter(field_name="category", lookup_expr="exact")
    email: django_filters.CharFilter = django_filters.CharFilter(
        field_name="user__email", lookup_expr="icontains"
    )
    username: django_filters.CharFilter = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )
    first_name: django_filters.CharFilter = django_filters.CharFilter(
        field_name="user__first_name", lookup_expr="icontains"
    )
    last_name: django_filters.CharFilter = django_filters.CharFilter(
        field_name="user__last_name", lookup_expr="icontains"
    )
    referrer = django_filters.CharFilter(
        field_name="user__referrer__username", lookup_expr="exact"
    )
    supervisor = django_filters.CharFilter(
        field_name="user__supervisor__username", lookup_expr="exact"
    )

    class Meta:
        model = models.Activity
        fields: list[str] = []


class CategoryFilter(django_filters.FilterSet):
    """Filter set for filtering categories."""

    ordering = django_filters.OrderingFilter(
        fields=(("value", "value"),),
        field_labels={
            "value": _("value"),
        },
    )

    id: django_filters.NumberFilter = django_filters.NumberFilter(
        field_name="id",
        lookup_expr="exact",
        help_text=_("Filter categories by ID"),
    )
    name: django_filters.CharFilter = django_filters.CharFilter(
        field_name="name", lookup_expr="exact", help_text=_("Filter categories by name")
    )
    value: django_filters.NumberFilter = django_filters.NumberFilter(
        field_name="value",
        lookup_expr="exact",
        help_text=_("Filter categories by value"),
    )

    class Meta:
        model = models.Category
        fields: list[str] = []
