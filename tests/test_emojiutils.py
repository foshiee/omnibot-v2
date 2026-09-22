import discord
import pytest

import cogs.emojiutils as emojiutils
from cogs.emojiutils import emoji_url, get_emoji, load_emojis
from conftest import FakeBot, FakeEmoji


def http_error(status=500):
    return discord.HTTPException(type("R", (), {"status": status, "reason": "boom"})(), "boom")


class TestLoadEmojis:
    async def test_returns_count_and_populates_cache(self):
        bot = FakeBot([FakeEmoji("omnicoin"), FakeEmoji("plus1")])
        assert await load_emojis(bot) == 2
        assert set(emojiutils._emoji_cache) == {"omnicoin", "plus1"}

    async def test_returns_none_on_http_failure(self):
        bot = FakeBot(error=http_error())
        assert await load_emojis(bot) is None

    async def test_repopulates_rather_than_appends(self):
        await load_emojis(FakeBot([FakeEmoji("old_one"), FakeEmoji("shared")]))
        await load_emojis(FakeBot([FakeEmoji("shared"), FakeEmoji("new_one")]))
        # A renamed or deleted emoji must not linger in the cache.
        assert set(emojiutils._emoji_cache) == {"shared", "new_one"}

    async def test_failed_reload_leaves_previous_cache_intact(self):
        await load_emojis(FakeBot([FakeEmoji("omnicoin")]))
        await load_emojis(FakeBot(error=http_error()))
        # Better to keep serving stale emojis than to blank them on a blip.
        assert "omnicoin" in emojiutils._emoji_cache


class TestGetEmoji:
    async def test_returns_matching_emoji(self):
        bot = FakeBot([FakeEmoji("omnicoin")])
        assert (await get_emoji("omnicoin", bot)).name == "omnicoin"

    async def test_returns_none_for_unknown_name(self):
        bot = FakeBot([FakeEmoji("omnicoin")])
        assert await get_emoji("not_a_real_emoji", bot) is None

    async def test_is_case_sensitive(self):
        # cookieSpin is referenced with that exact casing across the cogs.
        bot = FakeBot([FakeEmoji("cookieSpin")])
        assert await get_emoji("cookieSpin", bot) is not None
        assert await get_emoji("cookiespin", bot) is None

    async def test_fetches_only_once_across_many_lookups(self):
        # levels.py calls this on every message - it must not hit the API each time.
        bot = FakeBot([FakeEmoji("plus1")])
        for _ in range(50):
            await get_emoji("plus1", bot)
        assert bot.fetch_count == 1

    async def test_does_not_retry_after_a_failed_fetch(self):
        # A failed fetch used to leave the cache empty, causing one HTTP request
        # per message forever. It should give up until explicitly reloaded.
        bot = FakeBot(error=http_error())
        for _ in range(50):
            assert await get_emoji("plus1", bot) is None
        assert bot.fetch_count == 1

    async def test_explicit_reload_recovers_after_failure(self):
        bad = FakeBot(error=http_error())
        await get_emoji("plus1", bad)
        good = FakeBot([FakeEmoji("plus1")])
        assert await load_emojis(good) == 1
        assert (await get_emoji("plus1", good)).name == "plus1"


class TestEmojiUrl:
    def test_returns_none_for_unicode_fallback(self):
        # Cogs fall back to a plain string like ":coin:" when an emoji is missing.
        # Calling .url on that string used to raise AttributeError.
        assert emoji_url(":coin:") is None

    def test_returns_none_for_none(self):
        assert emoji_url(None) is None

    def test_returns_url_for_real_emoji(self):
        emoji = discord.Object(id=1)  # not an Emoji, so still treated as a fallback
        assert emoji_url(emoji) is None

    async def test_real_emoji_instance_returns_its_url(self, monkeypatch):
        # Build a genuine discord.Emoji so the isinstance check is exercised.
        emoji = discord.Emoji.__new__(discord.Emoji)
        monkeypatch.setattr(type(emoji), "url", property(lambda self: "https://cdn.example/x.png"))
        assert emoji_url(emoji) == "https://cdn.example/x.png"

    @pytest.mark.parametrize("fallback", [":cookie:", ":coin:", ":warning:", ":chart_with_upwards_trend:"])
    def test_all_cog_fallback_strings_are_safe(self, fallback):
        assert emoji_url(fallback) is None
