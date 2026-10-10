import django_filters

from .models import Announcement, AnnouncementDelivery


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
    type = django_filters.ChoiceFilter(
        field_name="type",
        choices=Announcement.Type.choices,
    )
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


class AnnouncementDeliveryFilterSet(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            "created_at",
            "updated_at",
            "delivered_at",
            "attempts",
        )
    )

    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    updated = django_filters.DateFromToRangeFilter(field_name="updated_at")
    delivered = django_filters.DateFromToRangeFilter(field_name="delivered_at")
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=AnnouncementDelivery.Status.choices,
    )
    channel = django_filters.ChoiceFilter(
        field_name="channel",
        choices=AnnouncementDelivery.Channel.choices,
    )
    announcement = django_filters.NumberFilter(
        field_name="announcement__id",
        lookup_expr="exact",
    )
    announcement_type = django_filters.ChoiceFilter(
        field_name="announcement__type",
        choices=Announcement.Type.choices,
    )

    class Meta:
        model = AnnouncementDelivery
        fields: list[str] = []
