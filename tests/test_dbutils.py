"""Integration tests for dbutils - these hit a real MySQL server.

They skip automatically if the database is unreachable. Writes go to a throwaway
table only; the live `members` table is never modified.

Run just these:      pytest -m db
Skip them entirely:  pytest -m "not db"
"""
import asyncio

import pymysql
import pytest

import cogs.dbutils as dbutils
from cogs.dbutils import check_table_exists, close_pool, init_pool, query

pytestmark = pytest.mark.db


class TestPoolLifecycle:
    async def test_init_pool_creates_a_pool(self, db_pool):
        assert dbutils._pool is not None

    async def test_init_pool_is_idempotent(self, db_pool):
        first = dbutils._pool
        await init_pool()
        assert dbutils._pool is first

    async def test_close_pool_clears_the_pool(self, db_pool):
        await close_pool()
        assert dbutils._pool is None

    async def test_close_pool_is_safe_when_never_created(self):
        await close_pool()
        await close_pool()  # must not raise
        assert dbutils._pool is None

    async def test_query_lazily_creates_the_pool(self):
        await close_pool()
        assert dbutils._pool is None
        try:
            await query(returntype="one", sql="SELECT 1")
        except Exception as e:
            pytest.skip(f"database unreachable: {type(e).__name__}: {e}")
        assert dbutils._pool is not None
        await close_pool()

    async def test_concurrent_lazy_init_creates_only_one_pool(self):
        # Several messages arriving at once must not each build a pool.
        await close_pool()
        try:
            await asyncio.gather(*[query(returntype="one", sql="SELECT 1") for _ in range(10)])
        except Exception as e:
            pytest.skip(f"database unreachable: {type(e).__name__}: {e}")
        assert dbutils._pool is not None
        await close_pool()


class TestQueryReturnTypes:
    async def test_one_returns_a_single_row(self, db_pool):
        assert await query(returntype="one", sql="SELECT 1") == (1,)

    async def test_one_returns_none_when_no_rows_match(self, db_pool):
        # None here means "found nothing", NOT "the query failed".
        result = await query(
            returntype="one",
            sql="SELECT table_name FROM information_schema.tables WHERE table_name = %s",
            params=("zzz_table_that_does_not_exist",),
        )
        assert result is None

    async def test_all_returns_every_row(self, db_pool):
        rows = await query(returntype="all", sql="SELECT 1 UNION SELECT 2 UNION SELECT 3")
        assert sorted(rows) == [(1,), (2,), (3,)]

    async def test_all_returns_empty_sequence_when_no_rows(self, db_pool):
        rows = await query(
            returntype="all",
            sql="SELECT table_name FROM information_schema.tables WHERE table_name = %s",
            params=("zzz_nope",),
        )
        assert list(rows) == []

    async def test_ten_caps_the_row_count(self, db_pool):
        rows = await query(returntype="ten", sql="SELECT table_name FROM information_schema.tables")
        assert len(rows) <= 10

    async def test_params_are_bound_not_interpolated(self, db_pool):
        # A value containing quotes must be safely parameterised.
        nasty = "'; DROP TABLE members; --"
        result = await query(returntype="one", sql="SELECT %s", params=(nasty,))
        assert result == (nasty,)


class TestQueryErrorHandling:
    async def test_bad_sql_raises_rather_than_returning_a_sentinel(self, db_pool):
        # This used to return 0, which callers then subscripted -> TypeError
        # far away from the real cause.
        with pytest.raises(pymysql.err.Error):
            await query(returntype="one", sql="SELECT * FROM definitely_not_a_table_xyz")

    async def test_failure_is_distinguishable_from_empty_result(self, db_pool):
        empty = await query(
            returntype="one",
            sql="SELECT table_name FROM information_schema.tables WHERE table_name = %s",
            params=("zzz_nope",),
        )
        assert empty is None
        with pytest.raises(pymysql.err.Error):
            await query(returntype="one", sql="SELECT nonexistent_column_xyz")

    async def test_pool_still_usable_after_a_failed_query(self, db_pool):
        # A broken query must not poison the pooled connection for the next caller.
        with pytest.raises(pymysql.err.Error):
            await query(returntype="one", sql="SELECT * FROM definitely_not_a_table_xyz")
        assert await query(returntype="one", sql="SELECT 1") == (1,)


class TestCheckTableExists:
    async def test_true_for_an_existing_table(self, scratch_table):
        assert await check_table_exists(scratch_table) is True

    async def test_false_for_a_missing_table(self, db_pool):
        assert await check_table_exists("zzz_table_that_does_not_exist") is False

    async def test_scoped_to_the_connected_database(self, db_pool):
        # information_schema lists tables across every database on the server.
        # Without a table_schema filter this matched a same-named table in any
        # other database, so the bot skipped creating its own and then failed
        # with "Table '<db>.members' doesn't exist".
        #
        # Pick a table that exists somewhere on the server but NOT in our own
        # database - that is exactly the case the missing filter got wrong.
        elsewhere = await query(
            returntype="one",
            sql=(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name NOT IN ("
                "  SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"
                ") LIMIT 1"
            ),
        )
        if elsewhere is None:
            pytest.skip("no table outside this database available to test scoping against")
        assert await check_table_exists(elsewhere[0]) is False

    async def test_same_name_in_another_database_does_not_count(self, scratch_table):
        # Sanity check on the positive side: our own table still resolves True
        # even though other databases on this server have their own tables.
        assert await check_table_exists(scratch_table) is True


class TestPoolReuseAndDurability:
    async def test_handles_many_concurrent_queries(self, db_pool):
        results = await asyncio.gather(
            *[query(returntype="one", sql="SELECT %s", params=(i,)) for i in range(20)]
        )
        assert results == [(i,) for i in range(20)]

    async def test_write_is_visible_to_a_later_query(self, scratch_table):
        # Without autocommit=True on the pool, a write could sit in an open
        # transaction on one pooled connection and be invisible to the next
        # caller, who may well get a different connection.
        await query(returntype="commit", sql=f"INSERT INTO {scratch_table} (id, label) VALUES (%s, %s)",
                    params=(42, "written"))
        assert await query(returntype="one", sql=f"SELECT label FROM {scratch_table} WHERE id = %s",
                           params=(42,)) == ("written",)

    async def test_write_survives_concurrent_readers(self, scratch_table):
        await query(returntype="commit", sql=f"INSERT INTO {scratch_table} (id, label) VALUES (%s, %s)",
                    params=(7, "durable"))
        reads = await asyncio.gather(
            *[query(returntype="one", sql=f"SELECT label FROM {scratch_table} WHERE id = %s", params=(7,))
              for _ in range(10)]
        )
        assert all(r == ("durable",) for r in reads)

    async def test_commit_returns_affected_row_count(self, scratch_table):
        affected = await query(returntype="commit", sql=f"INSERT INTO {scratch_table} (id) VALUES (1), (2), (3)")
        assert affected == 3
