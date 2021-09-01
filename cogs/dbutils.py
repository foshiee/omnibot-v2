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
        dbconnect.close()
        return result
    except:
        print("MySQL connection failed.")
        log(str(sys.exc_info()[0]))
        log(str(sys.exc_info()[1]))
        log(str(sys.exc_info()[2]))
        traceback.print_exc()
        return 0


async def check_table_exists(tablename):
    result = await query(returntype="one", sql="SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '" + tablename + "'")
    if result[0] == 1:
        return True
    return False
