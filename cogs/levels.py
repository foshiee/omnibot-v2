import asyncio
import discord
from discord.ext import tasks, commands
from cogs.dbutils import query, check_table_exists
from cogs.log import log
import math
import time


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        nt = int(time.time())
        val = (message.author.id, message.author.name, message.author.guild.id, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, nt)
        if not message.author.bot:
            if not await check_table_exists("members"):
                await query(returntype="commit", sql="""CREATE TABLE IF NOT EXISTS members (diwor INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(diwor), member_id bigint, 
                                                    member_name varchar(40), guild_id bigint, exp bigint, month_exp bigint, lvl int, 
                                                    month_lvl int, prestige int, coins int, rep int, cookie_s int, cookie_r int, cookie_k int, can_mention int, rank_posttime bigint)""")

                await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, guild_id, exp, 
                                                    month_exp, lvl, month_lvl, prestige, coins, rep, cookie_s, cookie_r, cookie_k, can_mention, 
                                                    rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            params=val)
            else:
                result = await query(returntype="one", sql="SELECT member_id, guild_id, exp, month_exp, lvl, month_lvl,"
                                                           " prestige, rank_posttime FROM members WHERE guild_id = '"
                                                           + str(message.author.guild.id) + "' ""AND ""member_id = '"
                                                           + str(message.author.id) + "'")

                if result is None:
                    await query(returntype="commit", sql="INSERT INTO members (member_id, member_name, guild_id, exp, "
                                                         "month_exp, lvl, month_lvl, prestige, coins, rep, cookie_r, cookie_s, cookie_k, can_mention,"
                                                         " rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                params=val)

                else:
                    current_exp = int(result[2])
                    current_mexp = int(result[3])
                    current_lvl = int(result[4])
                    current_mlvl = int(result[5])
                    current_prestige = int(result[6])
                    lastranked_posttime = int(result[7])
                    lvl_xpend = math.floor(5 * (current_lvl ^ 2) + 30 * current_lvl + 100)
                    mlvl_xpend = math.floor(5 * (current_mlvl ^ 2) + 30 * current_mlvl + 100)

                    # hidden_channels = []
                    # if ctx.message.channel not in hidden_channels:

                    if lastranked_posttime + 30 < int(time.time()):
                        i = 2
                        current_exp += i
                        current_mexp += i
                        lastranked_posttime = int((time.time()))

                        if current_exp >= lvl_xpend:
                            current_lvl += 1
                            current_exp -= lvl_xpend
                            await message.channel.send(f":chart_with_upwards_trend: | {message.author.mention} just "
                                                       f"leveled up to Lvl.{str(current_lvl)}")

                        if current_mexp >= mlvl_xpend:
                            current_mlvl += 1
                            current_mexp -= mlvl_xpend
                            await message.channel.send(f":chart_with_upwards_trend: | {message.author.display_name} "
                                                       f"just month leveled up "f"to mLvl.{str(current_lvl)}")

                        if current_lvl > 99:
                            current_prestige += 1
                            current_lvl = 1

                    await query(returntype="commit",
                                sql="UPDATE members SET exp = " + str(current_exp) + ", month_exp = " +
                                    str(current_mexp) + ", lvl = " + str(current_lvl) +
                                    ", month_lvl = " + str(current_mlvl) + ", prestige = " +
                                    str(current_prestige) + ", rank_posttime = " + str(
                                    lastranked_posttime) + " WHERE guild_id = " +
                                str(message.author.guild.id) + " AND member_id = " + str(message.author.id))


def setup(bot: commands.Bot):
    bot.add_cog(Levels(bot))
