"""Writes the monthly top-performers announcement.

Scheduled daily rather than monthly: it exits immediately unless today is the first of a
Hijri month, which means a day the cluster was unavailable is picked up on the next run.
Reruns are safe — `idempotency_key` identifies the month, so a second run updates the
existing announcement and edits the message already in Discord instead of posting again.
"""

import datetime as dt

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from ....users.services import top_performers
from ... import hijri, renderers
from ...integrations import discord
from ...models import Announcement, AnnouncementDelivery


class Command(BaseCommand):
    help = "Create or refresh the previous Hijri month's top-performers announcement."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            type=dt.date.fromisoformat,
            help="Run as if today were this Gregorian date (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Run even when today is not the first of a Hijri month.",
        )

    def handle(self, *args, **options) -> None:
        today = options["date"] or hijri.today()
        if not options["force"] and not hijri.is_month_start(today):
            self.stdout.write(
                f"{today} is not the start of a Hijri month; nothing to do."
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

        idempotency_key = (
            f"{Announcement.Type.MONTH_TOP_PERFORMERS.value}:{year}-{month:02d}"
        )
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

        discord.edit_message(
            settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID,
            delivery.external_id,
            renderers.announcement_message(announcement),
        )
