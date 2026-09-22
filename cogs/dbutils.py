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


async def query(returntype, sql, params=None):
    dbconnect = None
    try:
        dbconnect = await aiomysql.connect(host=dbhost, port=dbport, user=dbuser, password=dbpasswd, db=dbname,
                                           charset="utf8mb4")
        dbcursor = await dbconnect.cursor()

        if params is None:
            result = await dbcursor.execute(sql)
        else:
            result = await dbcursor.execute(sql, params)

        if returntype == "one":
            result = await dbcursor.fetchone()
        elif returntype == "many":
            result = await dbcursor.fetchmany()
        elif returntype == "ten":
            result = await dbcursor.fetchmany(10)
        elif returntype == "all":
            result = await dbcursor.fetchall()
        elif returntype == "commit":
            await dbconnect.commit()

        await dbcursor.close()
        return result
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
    finally:
        if dbconnect is not None:
            dbconnect.close()


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
