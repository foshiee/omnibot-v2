import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import cogs.dbutils as dbutils  # noqa: E402  (needs the path set up first)


# Remembered for the whole session: without this every db test pays the full
# connection timeout again when there's no database to talk to.
_db_unavailable = None


@pytest.fixture
async def db_pool():
    """Give a test a freshly initialised connection pool, and tear it down after.

    Skips the test if the database is unreachable, so the non-db tests still run
    on a machine with no MySQL access or no credentials in .env.
    """
    global _db_unavailable
    if _db_unavailable is not None:
        pytest.skip(_db_unavailable)

    try:
        await dbutils.init_pool()
    except Exception as e:
        await dbutils.close_pool()
        _db_unavailable = f"database unreachable: {type(e).__name__}: {e}"
        pytest.skip(_db_unavailable)

    try:
        yield dbutils._pool
    finally:
        await dbutils.close_pool()


@pytest.fixture
async def scratch_table(db_pool):
    """Create a throwaway table for write tests and drop it afterwards.

    Deliberately not the real 'members' table - these tests must never write to
    live member data.
    """
    name = "pytest_scratch"
    await dbutils.query(returntype="commit", sql=f"DROP TABLE IF EXISTS {name}")
    await dbutils.query(returntype="commit", sql=f"CREATE TABLE {name} (id INT, label VARCHAR(32))")
    try:
        yield name
    finally:
        await dbutils.query(returntype="commit", sql=f"DROP TABLE IF EXISTS {name}")


class FakeEmoji:
    """Stand-in for discord.Emoji - only needs .name and .url for these tests."""

    def __init__(self, name, url=None):
        self.name = name
        self.url = url or f"https://cdn.example/{name}.png"


class FakeBot:
    """Stand-in for commands.Bot exposing just fetch_application_emojis."""

    def __init__(self, emojis=None, error=None):
        self._emojis = emojis if emojis is not None else []
        self._error = error
        self.fetch_count = 0

    async def fetch_application_emojis(self):
        self.fetch_count += 1
        if self._error is not None:
            raise self._error
        return list(self._emojis)


@pytest.fixture(autouse=True)
def reset_emoji_cache():
    """emojiutils keeps a module level cache; clear it between tests."""
    import cogs.emojiutils as emojiutils

    emojiutils._emoji_cache.clear()
    emojiutils._fetch_attempted = False
    yield
    emojiutils._emoji_cache.clear()
    emojiutils._fetch_attempted = False
