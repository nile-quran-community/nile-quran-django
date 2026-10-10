import asyncio

import discord as discord_py
import pytest

from nile_quran_community_api.apps.v1.announcements.integrations import discord

PAYLOAD = discord.Message(
    content="@everyone",
    embed=discord.Embed(title="عنوان", description="محتوى"),
)


class FakeResponse:
    status = 404
    reason = "Not Found"


class FakePartialMessage:
    def __init__(self, code: int | None):
        self.code = code

    async def edit(self, **kwargs) -> None:
        if self.code is not None:
            raise discord_py.NotFound(FakeResponse(), {"code": self.code})


class FakeChannel:
    def __init__(self, code: int | None):
        self.code = code
        self.edited: list[dict] = []

    def get_partial_message(self, message_id: int) -> FakePartialMessage:
        return FakePartialMessage(self.code)


@pytest.fixture
def channel_answering(monkeypatch):
    def _install(code: int | None) -> FakeChannel:
        channel = FakeChannel(code)
        monkeypatch.setattr(
            discord,
            "_with_channel",
            lambda channel_id, action: asyncio.run(action(channel)),
        )
        return channel

    return _install


class TestEditMessage:
    def test_unknown_message_becomes_a_domain_error(self, channel_answering):
        channel_answering(discord.DiscordErrorCode.UNKNOWN_MESSAGE)

        with pytest.raises(discord.MessageNotFound):
            discord.edit_message("channel-1", "123456789", PAYLOAD)

    def test_unknown_channel_is_left_alone(self, channel_answering):
        channel_answering(discord.DiscordErrorCode.UNKNOWN_CHANNEL)

        with pytest.raises(discord_py.NotFound):
            discord.edit_message("channel-1", "123456789", PAYLOAD)

    def test_a_successful_edit_raises_nothing(self, channel_answering):
        channel_answering(None)

        assert discord.edit_message("channel-1", "123456789", PAYLOAD) is None
