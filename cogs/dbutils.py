import asyncio
from dotenv import load_dotenv
from os import getenv
import aiomysql
import sys
import traceback
from cogs.log import log

load_dotenv()
dbname = getenv('DBNAME')
dbhost = str(getenv('DBHOST'))
dbport = int(getenv('DBPORT'))
dbuser = getenv('DBUSER')
dbpasswd = getenv('DBPASSWD')

_pool: aiomysql.Pool = None
_pool_lock = asyncio.Lock()


async def init_pool() -> None:
    """Create the connection pool. Safe to call more than once; call this from
    setup_hook so the pool is ready before the first message arrives. query()
    also lazily creates it on first use as a fallback."""
    global _pool
    async with _pool_lock:
        if _pool is not None:
            return
        # autocommit=True: every query here is a single standalone statement, never
        # part of a multi-statement transaction. Without it, a pooled connection left
        # mid-transaction by one caller (e.g. a SELECT with no explicit commit) would
        # carry that open transaction over to whichever caller acquires it next.
        _pool = await aiomysql.create_pool(host=dbhost, port=dbport, user=dbuser, password=dbpasswd, db=dbname,
                                           charset="utf8mb4", autocommit=True, minsize=1, maxsize=5)


async def close_pool() -> None:
    """Close the connection pool. Safe to call even if it was never created."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def query(returntype, sql, params=None):
    if _pool is None:
        await init_pool()

    try:
        async with _pool.acquire() as dbconnect:
            async with dbconnect.cursor() as dbcursor:
                if params is None:
                    affected = await dbcursor.execute(sql)
                else:
                    affected = await dbcursor.execute(sql, params)

                if returntype == "one":
                    return await dbcursor.fetchone()
                elif returntype == "many":
                    return await dbcursor.fetchmany()
                elif returntype == "ten":
                    return await dbcursor.fetchmany(10)
                elif returntype == "all":
                    return await dbcursor.fetchall()
                elif returntype == "commit":
                    return affected
    except Exception:
        # Logged here for immediate visibility, then re-raised: a failed query must
        # not look like "no rows found" to callers (None is also fetchone()'s normal
        # result when a row genuinely doesn't exist, so swallowing errors into None
        # here made real failures indistinguishable from legitimate empty results).
        print("MySQL connection failed.")
        log(str(sys.exc_info()[0]))
        log(str(sys.exc_info()[1]))
        log(str(sys.exc_info()[2]))
        traceback.print_exc()
        raise


async def check_table_exists(tablename):
    # table_schema scopes the check to the connected database, otherwise a table
    # of the same name in any other database on the server counts as a match.
    result = await query(returntype="one",
                         sql="SELECT COUNT(*) FROM information_schema.tables "
                             "WHERE table_schema = DATABASE() AND table_name = %s",
                         params=(tablename,))
    return result[0] > 0


async def create_members_table():
    await query(returntype="commit", sql="""CREATE TABLE IF NOT EXISTS members (diwor INT NOT NULL AUTO_INCREMENT, 
    PRIMARY KEY(diwor), member_id bigint, member_name varchar(40), guild_id bigint, exp bigint, month_exp bigint, 
    total_exp bigint, lvl int, month_lvl int, prestige int, coins int, coin_time datetime, coin_streak int, rep int, 
    rep_time datetime, cookie_s int, cookie_r int, cookie_k int, cookie_time datetime, can_mention int, rank_posttime 
    bigint)""")


async def insert_member(val):
    await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, guild_id, exp, month_exp, 
    total_exp, lvl, month_lvl, prestige, coins, coin_time, coin_streak, rep, rep_time, cookie_s, cookie_r, cookie_k, 
    cookie_time, can_mention, rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                params=val)
