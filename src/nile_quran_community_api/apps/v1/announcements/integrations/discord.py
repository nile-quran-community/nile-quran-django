"""Discord access, via discord.py.

Logs in as a bot but never opens a gateway connection: `Client.login` performs only the
REST handshake, so each call is a short-lived request and these commands stay ordinary
one-shot cron jobs. `Client.connect` is what would start a long-running event loop.

discord.py is async and management commands are not, so each entry point here wraps its
work in `asyncio.run`.
"""

import asyncio
import typing as t

import discord
from django.conf import settings

# Raised for anything the caller should treat as a delivery failure rather than a bug.
DeliveryError = (discord.DiscordException, OSError)


def _embed(payload: dict) -> discord.Embed:
    return discord.Embed(title=payload["title"], description=payload["description"])


async def _with_channel(channel_id: str, action: t.Callable) -> t.Any:
    """Log in over REST, hand `action` the channel, and close cleanly afterwards."""
    client = discord.Client(intents=discord.Intents.none())
    await client.login(settings.DISCORD_BOT_TOKEN)
    try:
        channel = await client.fetch_channel(int(channel_id))
        return await action(channel)
    finally:
        await client.close()


def post_message(channel_id: str, embed: dict) -> str:
    """Post an embed to a channel and return the new message's ID."""

    async def send(channel):
        message = await channel.send(embed=_embed(embed))
        return str(message.id)

    return asyncio.run(_with_channel(channel_id, send))


def edit_message(channel_id: str, message_id: str, embed: dict) -> None:
    """Replace the embed on a message this bot previously posted."""

    async def edit(channel):
        # Partial: we already know the ID, so there is nothing to fetch first.
        await channel.get_partial_message(int(message_id)).edit(embed=_embed(embed))

    asyncio.run(_with_channel(channel_id, edit))


def mention(discord_id: str, fallback: str) -> str:
    """Render a user as a Discord mention, or as plain text when we have no ID."""
    return f"<@{discord_id}>" if discord_id else fallback
