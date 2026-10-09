from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Announcement(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("reference_key",),
                condition=~models.Q(reference_key=""),
                name="unique_announcement_reference_key",
            ),
        ]

    class Type(models.TextChoices):
        GENERAL = "general", _("General")
        WEEKLY_REFLECTION = "weekly_reflection", _("Weekly Reflection")
        GATHERING = "gathering", _("Gathering")
        ILM_LESSON = "ilm_lesson", _("Ilm Lesson")
        MONTH_TOP_PERFORMERS = "month_top_performers", _("Month Top Performers")

    class Status(models.TextChoices):
        """Derived, never stored — see `Announcement.status`."""

        DRAFT = "draft", _("Draft")
        SCHEDULED = "scheduled", _("Scheduled")
        PENDING = "pending", _("Pending")
        PUBLISHED = "published", _("Published")
        FAILED = "failed", _("Failed")

    type = models.CharField(max_length=32, choices=Type)
    title = models.CharField(max_length=255)
    content = models.TextField()
    publish_at = models.DateTimeField(blank=True, null=True)
    reference_key = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="announcements",
        null=True,
        on_delete=models.SET_NULL,
    )

    @property
    def status(self) -> "Announcement.Status":
        """Where this announcement stands, worked out from when it is due and whether
        Discord has it.

        Not a stored column: a stored one can disagree with the delivery records, and
        an admin setting it to published by hand would silently stop the post going
        out. Reads `deliveries.all()` so a prefetch covers a whole list.
        """
        deliveries = self.deliveries.all()
        if any(d.status == AnnouncementDelivery.Status.SENT for d in deliveries):
            return self.Status.PUBLISHED
        if self.publish_at is None:
            return self.Status.DRAFT
        if self.publish_at > timezone.now():
            return self.Status.SCHEDULED
        if any(d.status == AnnouncementDelivery.Status.FAILED for d in deliveries):
            return self.Status.FAILED
        return self.Status.PENDING


class AnnouncementDelivery(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("announcement", "channel"),
                name="unique_announcement_delivery_channel",
            ),
        ]

    class Channel(models.TextChoices):
        DISCORD = "discord", _("Discord")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    channel = models.CharField(max_length=32, choices=Channel)
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    external_id = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    announcement = models.ForeignKey(
        Announcement,
        related_name="deliveries",
        on_delete=models.CASCADE,
    )
