"""Writes the monthly top-performers announcement.

Scheduled daily rather than monthly, and works on the Hijri month before today's during
the first RETRY_DAYS days of a month, so a run missed on the first is picked up by a later
one. After that the previous month is left alone: a leaderboard that late is stale, so it
is abandoned rather than posted. Reruns are safe —
`idempotency_key` identifies the month, so a later run updates the existing announcement
and edits the message already in Discord instead of posting again, and does nothing at
all when the leaderboard has not changed.
"""

import datetime as dt

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from ....users.services import top_performers
from ... import hijri, renderers
from ...integrations import discord
from ...models import Announcement, AnnouncementDelivery

RETRY_DAYS = 7


class Command(BaseCommand):
    help = "Create or refresh the previous Hijri month's top-performers announcement."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            type=dt.date.fromisoformat,
            help="Run as if today were this Gregorian date (YYYY-MM-DD).",
        )

    def handle(self, *args, **options) -> None:
        today = options["date"] or hijri.today()
        if hijri.to_hijri(today).day > RETRY_DAYS:
            self.stdout.write(
                f"{today} is past day {RETRY_DAYS} of the Hijri month; nothing to do."
            )
            return

        year, month = hijri.previous_month(today)
        start, end = hijri.month_window(year, month)
        performers = top_performers(
            start, end, ranks=settings.ANNOUNCEMENTS_TOTAL_RANKS
        )
        if not performers:
            self.stdout.write(
                f"No student earned points in {year}-{month:02d}; skipping."
            )
            return

        idempotency_key = f"{Announcement.Type.MONTH_TOP_PERFORMERS}:{year}-{month:02d}"
        title = renderers.top_performers_title(year, month)
        content = renderers.top_performers_content(performers, year, month)

        existing = Announcement.objects.filter(idempotency_key=idempotency_key).first()
        if existing is None:
            Announcement.objects.create(
                type=Announcement.Type.MONTH_TOP_PERFORMERS,
                title=title,
                content=content,
                publish_at=timezone.now(),
                idempotency_key=idempotency_key,
            )
            self.stdout.write(f"Queued {idempotency_key} for delivery.")
            return

        if (existing.title, existing.content) == (title, content):
            self.stdout.write(f"{idempotency_key} is up to date.")
            return

        existing.title, existing.content = title, content
        existing.save(update_fields=["title", "content", "updated_at"])
        self._refresh_delivered_message(existing)
        self.stdout.write(f"Updated {idempotency_key}.")

    def _refresh_delivered_message(self, announcement: Announcement) -> None:
        """Bring an already-posted Discord message back in line with the announcement."""
        delivery = announcement.deliveries.filter(
            channel=AnnouncementDelivery.Channel.DISCORD,
            status=AnnouncementDelivery.Status.SENT,
        ).first()
        if delivery is None:
            return

        if not settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID:
            raise CommandError("DISCORD_ANNOUNCEMENTS_CHANNEL_ID is not configured.")

        try:
            discord.edit_message(
                settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID,
                delivery.external_id,
                renderers.announcement_message(announcement),
            )
        except discord.MessageNotFound:
            # Someone removed the post. Dropping the delivery leaves the announcement
            # with nothing sent, so publish_announcements posts a replacement.
            delivery.delete()
            self.stdout.write("Discord message is gone; queued a replacement.")
