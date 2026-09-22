import discord
from discord.ext import commands
from typing import Optional

# Application emojis are fetched over HTTP, not cached by the library, so they are
# held here for the process lifetime. get_emoji is called on every message by the
# levels cog, which would otherwise be one API request per message.
_emoji_cache: dict[str, discord.Emoji] = {}
_fetch_attempted = False


async def load_emojis(bot: commands.Bot) -> Optional[int]:
    """Fetch the application's emojis and repopulate the cache.

    Returns the number of emojis loaded, or None if the fetch failed.
    """
    global _fetch_attempted
    # Set even when the fetch fails, so get_emoji does not retry once per message.
    # Use the "cogs emojis" command to retry after a failure.
    _fetch_attempted = True

    try:
        emojis = await bot.fetch_application_emojis()
    except discord.HTTPException as e:
        print(f"Unable to fetch application emojis: {e}")
        return None

    _emoji_cache.clear()
    _emoji_cache.update({emoji.name: emoji for emoji in emojis})
    print(f"Loaded {len(_emoji_cache)} application emojis.")
    return len(_emoji_cache)


async def get_emoji(name: str, bot: commands.Bot) -> Optional[discord.Emoji]:
    """Get an application emoji by name, or None if it does not exist."""
    if not _fetch_attempted:
        await load_emojis(bot)
    return _emoji_cache.get(name)


def emoji_url(emoji) -> Optional[str]:
    """Get an emoji's image URL. Returns None when a unicode fallback is in use."""
    return emoji.url if isinstance(emoji, discord.Emoji) else None
