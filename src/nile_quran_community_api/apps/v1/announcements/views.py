import logging

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import AnnouncementDeliveryFilterSet, AnnouncementFilterSet
from .integrations import discord
from .models import Announcement, AnnouncementDelivery
from .serializers import (
    AnnouncementDeliverySerializer,
    AnnouncementPreviewSerializer,
    AnnouncementSerializer,
)

logger = logging.getLogger(__name__)


class DiscordUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = _("Could not remove the Discord message; nothing was deleted.")
    default_code = "discord_unavailable"


def visible_to(queryset: QuerySet, user, prefix: str = "") -> QuerySet:
    """Narrow `queryset` to the announcements this user is allowed to see.

    Editors (anyone who can change announcements) see everything that has a publish time,
    plus their own drafts. Everyone else, including a logged-out visitor on the preview
    endpoint, sees only announcements whose publish time has already passed.

    Edits and deletes look the announcement up through this same filter, so one you can't
    see can't be found: the request is a 404. That is what keeps a draft private to its
    author, with no separate permission check.

    `prefix` reaches the announcement from a related model, e.g. `"announcement__"` when
    filtering deliveries."""

    if user.has_perm("announcements.change_announcement"):
        return queryset.filter(
            Q(**{f"{prefix}publish_at__isnull": False})
            | Q(**{f"{prefix}created_by": user})
        )
    return queryset.filter(**{f"{prefix}publish_at__lte": timezone.now()})


@extend_schema(tags=["announcements"])
class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_class = AnnouncementFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = Announcement.objects.select_related(
        "created_by", "updated_by"
    ).prefetch_related("deliveries")

    def get_queryset(self) -> QuerySet[Announcement]:
        return visible_to(super().get_queryset(), self.request.user)

    def perform_create(self, serializer: AnnouncementSerializer) -> None:
        user = self.request.user
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer: AnnouncementSerializer) -> None:
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance: Announcement) -> None:
        """Take the Discord post down first: deleting the row would lose the message ID
        and leave the post orphaned."""

        sent = instance.deliveries.filter(
            channel=AnnouncementDelivery.Channel.DISCORD,
            status=AnnouncementDelivery.Status.SENT,
        ).first()
        if sent and (
            settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID and settings.DISCORD_BOT_TOKEN
        ):
            try:
                discord.delete_message(
                    settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID, sent.external_id
                )
            except discord.MessageNotFound:
                pass  # already gone, which is what we wanted
            except discord.DeliveryError as error:
                raise DiscordUnavailable() from error
        elif sent:
            # Deleting still goes ahead, so a local or half-configured environment isn't
            # stuck with a post it can never remove; the message is left behind in Discord.
            logger.warning(
                "Announcement %s deleted but Discord is not configured; message %s "
                "was left in the channel.",
                instance.pk,
                sent.external_id,
            )
        instance.delete()

    @extend_schema(responses=AnnouncementPreviewSerializer)
    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def preview(self, request: Request, pk: str | None = None) -> Response:
        """Title and summary only, so a link can unfurl for someone not logged in."""

        return Response(AnnouncementPreviewSerializer(self.get_object()).data)


@extend_schema(tags=["announcements"])
class AnnouncementDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnnouncementDeliverySerializer
    filterset_class = AnnouncementDeliveryFilterSet
    permission_classes = [DjangoModelPermissions]
    queryset = AnnouncementDelivery.objects.select_related("announcement")

    def get_queryset(self) -> QuerySet[AnnouncementDelivery]:
        queryset = super().get_queryset()
        # Discord message IDs and error text are for the people who run announcements
        if not self.request.user.has_perm("announcements.change_announcement"):
            return queryset.none()
        return visible_to(queryset, self.request.user, prefix="announcement__")
