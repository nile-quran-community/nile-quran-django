import django_filters
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone

from .models import Announcement, AnnouncementDelivery


def _delivery(status: str) -> Exists:
    return Exists(
        AnnouncementDelivery.objects.filter(announcement=OuterRef("pk"), status=status)
    )


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

    live = django_filters.BooleanFilter(method="filter_live")
    status = django_filters.ChoiceFilter(
        choices=Announcement.Status.choices, method="filter_status"
    )

    def filter_live(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Only what is already public, so editors can leave their scheduled posts out.
        `live=false` is not the opposite: it filters nothing, the same as omitting it."""

        return queryset.filter(publish_at__lte=timezone.now()) if value else queryset

    def filter_status(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Mirrors `Announcement.status`, which cannot be filtered on directly."""

        Status = Announcement.Status
        now = timezone.now()
        sent = _delivery(AnnouncementDelivery.Status.SENT)
        failed = _delivery(AnnouncementDelivery.Status.FAILED)
        due = Q(publish_at__lte=now)
        match value:
            case Status.PUBLISHED:
                return queryset.filter(sent)
            case Status.DRAFT:
                return queryset.filter(~sent, publish_at__isnull=True)
            case Status.SCHEDULED:
                return queryset.filter(~sent, publish_at__gt=now)
            case Status.FAILED:
                return queryset.filter(~sent, due, failed)
            case Status.PENDING:
                return queryset.filter(~sent, ~failed, due)
            case _:
                return queryset.none()

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
