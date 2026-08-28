import django_filters

from .models import Goal


class GoalFilterSet(django_filters.FilterSet):
    scope: django_filters.ChoiceFilter = django_filters.ChoiceFilter(
        choices=Goal.Scope.choices
    )
    title: django_filters.CharFilter = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains"
    )
    description: django_filters.CharFilter = django_filters.CharFilter(
        field_name="description", lookup_expr="icontains"
    )
    target_exact: django_filters.NumberFilter = django_filters.NumberFilter(
        field_name="target", lookup_expr="exact"
    )
    target_range: django_filters.RangeFilter = django_filters.RangeFilter(
        field_name="target"
    )
    current_exact: django_filters.NumberFilter = django_filters.NumberFilter(
        field_name="current", lookup_expr="exact"
    )
    current_range: django_filters.RangeFilter = django_filters.RangeFilter(
        field_name="current"
    )
    created_at: django_filters.DateFromToRangeFilter = (
        django_filters.DateFromToRangeFilter(field_name="created_at")
    )

    class Meta:
        model = Goal
        fields: list[str] = []
