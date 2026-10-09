"""Fills in Discord IDs by matching community members against the server's member list.

Saves an admin typing an ID per student, but only where the pairing is unambiguous:
a user is linked when their name matches exactly one server member and that member
matches exactly one user. Everything else is reported for a human to resolve, because
a wrong link mentions — and later messages — the wrong person.

Users who already have an ID are never touched, so this is safe to re-run as the
community grows.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from ....users.models import User
from ....users.services import match_discord_members
from ...integrations import discord


class Command(BaseCommand):
    help = "Link users to their Discord accounts by matching names against the server."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be linked without saving anything.",
        )

    def handle(self, *args, **options) -> None:
        if not settings.DISCORD_BOT_TOKEN or not settings.DISCORD_GUILD_ID:
            raise CommandError("DISCORD_BOT_TOKEN and DISCORD_GUILD_ID are required.")

        matches = match_discord_members(discord.list_members(settings.DISCORD_GUILD_ID))

        if matches.linked and not options["dry_run"]:
            users = User.objects.filter(pk__in=matches.linked)
            for user in users:
                user.discord_id = matches.linked[user.pk]
            User.objects.bulk_update(users, ["discord_id"])

        self.report(matches, options["dry_run"])

    def report(self, matches, dry_run: bool) -> None:
        verb = "Would link" if dry_run else "Linked"
        self.stdout.write(f"{verb} {len(matches.linked)} user(s).")

        for label, users in (
            ("No Discord member found for", matches.unmatched),
            ("Several possible matches for", matches.ambiguous),
        ):
            for user in users:
                self.stdout.write(f"  {label} {user.username}.")
