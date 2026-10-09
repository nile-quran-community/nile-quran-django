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

# Discord's code for "Unknown Message". A 404 on its own is not enough to go on: a
# missing channel answers 404 too, and that one leaves the message itself intact.
_UNKNOWN_MESSAGE = 10008


class MessageNotFound(Exception):
    """The message we hold an ID for is no longer in the channel."""


type Member = dict[str, str]


class Embed(t.TypedDict):
    title: str
    description: str


class Message(t.TypedDict):
    """A ping in `content` and the body in `embed`: embeds alone notify nobody."""

    content: str
    embed: Embed


def _embed(payload: Embed) -> discord.Embed:
    return discord.Embed(title=payload["title"], description=payload["description"])


async def _session[T](
    action: t.Callable[[discord.Client], t.Awaitable[T]],
    intents: discord.Intents | None = None,
) -> T:
    """Log in over REST, hand `action` the client, and close cleanly afterwards."""

    client = discord.Client(intents=intents or discord.Intents.none())
    await client.login(settings.DISCORD_BOT_TOKEN)
    try:
        return await action(client)
    finally:
        await client.close()


def _with_channel[T](
    channel_id: str,
    action: t.Callable[[t.Any], t.Awaitable[T]],
) -> T:
    """Run `action` against the channel, which Discord types loosely on the way back."""

    async def resolve(client: discord.Client) -> T:
        return await action(await client.fetch_channel(int(channel_id)))

    return asyncio.run(_session(resolve))


def post_message(channel_id: str, payload: Message) -> str:
    """Post a message to a channel and return the new message's ID."""

    async def send(channel: discord.abc.Messageable) -> str:
        message = await channel.send(
            content=payload["content"], embed=_embed(payload["embed"])
        )
        return str(message.id)

    return _with_channel(channel_id, send)


def edit_message(channel_id: str, message_id: str, payload: Message) -> None:
    """Replace the content and embed on a message this bot previously posted."""

    async def edit(channel: discord.TextChannel) -> None:
        try:
            await channel.get_partial_message(int(message_id)).edit(
                content=payload["content"], embed=_embed(payload["embed"])
            )
        except discord.NotFound as error:
            if error.code != _UNKNOWN_MESSAGE:
                raise
            raise MessageNotFound(message_id) from error

    _with_channel(channel_id, edit)


def list_members(guild_id: str) -> list[Member]:
    """Every human member of the server, by the name the server shows for them.

    `display_name` is their nickname on this server when they have set one, and their
    Discord display name otherwise — the name other members actually see.

    `fetch_members` is the HTTP route, so this still needs no gateway, but it does
    require the Server Members intent to be enabled for the bot.
    """

    intents = discord.Intents.none()
    intents.members = True

    async def fetch(client: discord.Client) -> list[Member]:
        guild = await client.fetch_guild(int(guild_id))
        return [
            {"id": str(member.id), "name": member.display_name}
            async for member in guild.fetch_members(limit=None)
            if not member.bot
        ]

    return asyncio.run(_session(fetch, intents=intents))


def mention(discord_id: str, fallback: str) -> str:
    """Render a user as a Discord mention, or as plain text when we have no ID."""

    return f"<@{discord_id}>" if discord_id else fallback
