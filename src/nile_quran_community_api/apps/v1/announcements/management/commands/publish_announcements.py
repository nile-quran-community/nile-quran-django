"""Delivers every announcement that is due and not yet in Discord.

An announcement is due once `publish_at` has passed; a null `publish_at` is a draft and
never matches. Delivery records decide what has already gone out, so an announcement is
sent exactly once and a failed send is retried on the next run.

A second pass edits the Discord message of any sent announcement that was changed since
it was last synced, so saving an announcement is all an editor has to do.

This command is the Discord boundary: announcement content mentions students with
site-native `@{username}` handles so the frontend can render them, and the renderers
adapt those to Discord mentions only on the way out.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, QuerySet
from django.utils import timezone

from ... import renderers
from ...integrations import discord
from ...models import Announcement, AnnouncementDelivery


class Command(BaseCommand):
    help = "Post due announcements to Discord."

    def due(self) -> QuerySet[Announcement]:
        """Announcements past their publish time that Discord has not received."""

        return Announcement.objects.filter(publish_at__lte=timezone.now()).exclude(
            deliveries__channel=AnnouncementDelivery.Channel.DISCORD,
            deliveries__status=AnnouncementDelivery.Status.SENT,
        )

    def stale(self) -> QuerySet[AnnouncementDelivery]:
        """Sent messages whose announcement was edited after they last matched it."""

        return AnnouncementDelivery.objects.filter(
            channel=AnnouncementDelivery.Channel.DISCORD,
            status=AnnouncementDelivery.Status.SENT,
            announcement__updated_at__gt=F("synced_at"),
        ).select_related("announcement")

    def resync(self, delivery: AnnouncementDelivery, channel_id: str) -> None:
        announcement = delivery.announcement
        try:
            discord.edit_message(
                channel_id,
                delivery.external_id,
                renderers.discord_announcement_message(announcement),
            )
        except discord.MessageNotFound:
            # Someone removed the post. Dropping the delivery leaves the announcement
            # due again, so the loop in `handle` posts a replacement in this same run.
            delivery.delete()
            self.stdout.write(f"Announcement {announcement.pk} is gone; reposting.")
            return
        except discord.DeliveryError as error:
            self.stderr.write(f"Announcement {announcement.pk} edit failed: {error}")
            return

        # The version we rendered, not the clock: an edit saved since we loaded the row has
        # a later `updated_at`, so it still reads as stale and goes out on the next run.
        delivery.synced_at = announcement.updated_at
        delivery.save(update_fields=["synced_at", "updated_at"])
        self.stdout.write(f"Announcement {announcement.pk} updated.")

    def deliver(self, announcement: Announcement, channel_id: str) -> None:
        delivery, _ = AnnouncementDelivery.objects.get_or_create(
            announcement=announcement,
            channel=AnnouncementDelivery.Channel.DISCORD,
        )
        delivery.attempts += 1

        try:
            delivery.external_id = discord.post_message(
                channel_id,
                renderers.discord_announcement_message(announcement),
            )
        except discord.DeliveryError as error:
            delivery.status = AnnouncementDelivery.Status.FAILED
            delivery.last_error = str(error)
            delivery.save()
            self.stderr.write(f"Announcement {announcement.pk} failed: {error}")
            return

        delivery.status = AnnouncementDelivery.Status.SENT
        delivery.delivered_at = timezone.now()
        delivery.synced_at = announcement.updated_at  # see `resync`
        delivery.last_error = ""
        delivery.save()
        self.stdout.write(f"Announcement {announcement.pk} sent.")

    def handle(self, *args, **options) -> None:
        channel_id = settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID
        if not channel_id or not settings.DISCORD_BOT_TOKEN:
            self.stderr.write("Discord is not configured; nothing was sent.")
            return

        for delivery in self.stale():
            self.resync(delivery, channel_id)

        for announcement in self.due():
            self.deliver(announcement, channel_id)
