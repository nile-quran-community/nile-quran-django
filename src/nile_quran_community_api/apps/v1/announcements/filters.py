import django_filters

from .models import Announcement


class AnnouncementFilterSet(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            "created_at",
            "updated_at",
            "publish_at",
        )
    )

    publish = django_filters.DateFromToRangeFilter(field_name="publish_at")
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    updated = django_filters.DateFromToRangeFilter(field_name="updated_at")
    type = django_filters.ChoiceFilter(field_name="type")
    status = django_filters.ChoiceFilter(field_name="status")
    in_title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
    )
    created_by = django_filters.CharFilter(
        field_name="created_by__username",
        lookup_expr="iexact",
    )

    class Meta:
        model = Announcement
        fields: list[str] = []
