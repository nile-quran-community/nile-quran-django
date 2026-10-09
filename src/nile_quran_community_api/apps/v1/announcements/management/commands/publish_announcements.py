"""Delivers every announcement that is due and not yet in Discord.

Selection is driven by delivery records rather than `Announcement.status`, which stays
editable by admins: whatever status someone types, an announcement is sent exactly once
and a failed send is simply retried on the next run.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from django.utils import timezone

from ... import renderers
from ...integrations import discord
from ...models import Announcement, AnnouncementDelivery


class Command(BaseCommand):
    help = "Post due announcements to Discord."

    def due(self) -> QuerySet[Announcement]:
        """Announcements past their publish time that Discord has not received."""
        return (
            Announcement.objects.filter(publish_at__lte=timezone.now())
            .exclude(status=Announcement.Status.DRAFT)
            .exclude(
                deliveries__channel=AnnouncementDelivery.Channel.DISCORD,
                deliveries__status=AnnouncementDelivery.Status.SENT,
            )
        )

    def deliver(self, announcement: Announcement, channel_id: str) -> None:
        delivery, _ = AnnouncementDelivery.objects.get_or_create(
            announcement=announcement,
            channel=AnnouncementDelivery.Channel.DISCORD,
        )
        delivery.attempts += 1

        try:
            delivery.external_id = discord.post_message(
                channel_id,
                renderers.announcement_message(announcement),
            )
        except discord.DeliveryError as error:
            delivery.status = AnnouncementDelivery.Status.FAILED
            delivery.last_error = str(error)
            delivery.save()
            self.stderr.write(f"Announcement {announcement.pk} failed: {error}")
            return

        delivery.status = AnnouncementDelivery.Status.SENT
        delivery.delivered_at = timezone.now()
        delivery.last_error = ""
        delivery.save()

        announcement.status = Announcement.Status.PUBLISHED
        announcement.save(update_fields=["status", "updated_at"])
        self.stdout.write(f"Announcement {announcement.pk} sent.")

    def handle(self, *args, **options) -> None:
        channel_id = settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID
        if not channel_id or not settings.DISCORD_BOT_TOKEN:
            self.stderr.write("Discord is not configured; nothing was sent.")
            return

        for announcement in self.due():
            self.deliver(announcement, channel_id)
