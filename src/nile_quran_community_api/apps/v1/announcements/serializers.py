import re

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    ReadOnlyField,
    SerializerMethodField,
    ValidationError,
)

from ..users.permissions import is_admin_user
from .models import Announcement, AnnouncementDelivery

MENTION = re.compile(r"<@(\d+)>")


class AnnouncementDeliverySerializer(ModelSerializer):
    class Meta:
        model = AnnouncementDelivery
        fields = "__all__"

    def to_representation(self, instance: AnnouncementDelivery) -> dict:
        """`last_error` is raw exception text (hosts, Discord error codes): for the admins
        who fix the bot, not for the rest of the media team. Everyone who can see a delivery
        still sees that it failed, and how many times."""

        data = super().to_representation(instance)
        if not self._is_admin():
            data.pop("last_error")
        return data

    def _is_admin(self) -> bool:
        # Worked out once per request rather than once per row: a list serializes many.
        context = self.context
        if "is_admin" not in context:
            request = context.get("request")
            context["is_admin"] = bool(request and is_admin_user(request))
        return context["is_admin"]


class AuthorSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name")


class AnnouncementSerializer(ModelSerializer):
    status = ReadOnlyField()
    type_display = CharField(source="get_type_display", read_only=True)
    deliveries = AnnouncementDeliverySerializer(many=True, read_only=True)
    created_by = AuthorSerializer(read_only=True)
    updated_by = AuthorSerializer(read_only=True)
    mentions = SerializerMethodField()

    class Meta:
        model = Announcement
        fields = "__all__"
        # The leaderboard command upserts on this key; an editor must not be able to move it.
        read_only_fields = ("idempotency_key",)

    def validate_publish_at(self, value):
        """A post already in Discord can be rescheduled but not turned back into a draft:
        drafts are visible to their author alone, so it would vanish from the API (and be
        undeletable, for a post nobody authored) while staying up in Discord."""

        if value is None and self.instance is not None:
            sent = any(
                d.status == AnnouncementDelivery.Status.SENT
                for d in self.instance.deliveries.all()
            )
            if sent:
                raise ValidationError(
                    _("A post already on Discord cannot go back to a draft.")
                )
        return value

    def to_representation(self, instance: Announcement) -> dict:
        """Delivery records (Discord message IDs, errors, attempts) are for editors;
        everyone else gets the derived `status` only."""

        data = super().to_representation(instance)
        request = self.context.get("request")
        if not (request and request.user.has_perm("announcements.change_announcement")):
            data.pop("deliveries")
        return data

    def get_mentions(self, announcement: Announcement) -> dict[str, dict[str, str]]:
        """Who each `<@id>` ping in the content is, so the site can show a name that links
        to their profile instead of a Discord ID. Best effort: only people whose Discord ID
        we hold appear here; anyone else is simply not in the map."""

        ids = set(MENTION.findall(announcement.content))
        if not ids:
            return {}
        # ponytail: one query per leaderboard row on a list page; batch in the view if lists grow
        users = get_user_model().objects.filter(discord_id__in=ids)
        return {
            u.discord_id: {
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "username": u.username,
            }
            for u in users
        }


class AnnouncementPreviewSerializer(ModelSerializer):
    """What a logged-out visitor may see: enough for a link card, never the body."""

    type_display = CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Announcement
        fields = ("id", "type", "type_display", "title", "summary", "publish_at")
