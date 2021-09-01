import asyncio

import discord
from discord.ext import tasks, commands
from cogs.dbutils import query, check_table_exists
from cogs.log import log
import math
import time
from datetime import datetime


def ordinal(x):
    return "%d%s" % (x, "tsnrhtdd"[(math.floor(x / 10) % 10 != 1) * (x % 10 < 4) * x % 10::4])


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.monthly_reset.start(bot)

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

    @tasks.loop(reconnect=True)
    async def monthly_reset(self, ctx):
        announce = self.bot.get_channel(865253224135393294)
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            now = datetime.now()
            if now.day == 1 and now.hour == 0 and now.minute == 1:
                log("It's a new month! Getting leaderboards..")
                result = await query(returntype="one", sql="SELECT member_id, month_lvl, month_exp, coins WHERE "
                                                           "guild_id = %s ORDER BY month_lvl DESC, month_exp "
                                                           "DESC LIMIT 0,1", params=ctx.guild.id)
                member = discord.utils.get(ctx.guild.members, id=result[0])
                admin_role = discord.utils.get(ctx.guild.roles, name="Admins")
                krypt_role = discord.utils.get(ctx.guild.roles, name="Kryptonite")

                if int(result[0]) == 152229351168016384 or admin_role in member.roles:
                    await announce.send(f"Nobody has earned the Kryptonite role this month. Better luck next month!")
                elif krypt_role in member.roles:
                    val = (int(result[3]) + 1500, ctx.guild.id, member.id)
                    await query(returntype="commit",
                                sql="UPDATE members SET coins = %s WHERE guild_id = %s and member_id = %s", params=val)
                    await announce.send(f"{member.mention} is the top poster this month, beating Kryptix.\n"
                                        f"They already have the {krypt_role.display_name} role, so they have been "
                                        f"awarded 1500 coins instead!")
                else:
                    await member.add_roles(krypt_role)
                    await announce.send(f"{member.mention} is the top poster this month, beating Kryptix.\nThey "
                                        f"have been awarded the {krypt_role.display_name} role!")

                month_result = await query(returntype="ten", sql="SELECT member_id, month_lvl, month_exp FROM "
                                                                 "members WHERE guild_id = %s ORDER BY month_lvl DESC,"
                                                                 " month_exp DESC", params=ctx.guild.id)

                description = "Another month is behind us. Here are last month's top posters!\r\n\r\n"
                r = 0
                for row in month_result:
                    member = discord.utils.get(ctx.guild.members, id=row[0])
                    if r == 0:
                        message = f":first_place:    **{member.mention}**\n"
                    elif r == 1:
                        message = f":second_place:    **{member.mention}**\n"
                    elif r == 3:
                        message = f":third_place:    **{member.mention}**\n"
                    else:
                        message = f"{ordinal(r)}:    {member.display_name}\n"
                    mlvl = f"Lvl {row[1]}"
                    description += message + " - " + mlvl + "\n"
                    r += 1
                await announce.send(description)
                await query(returntype="commit", sql="UPDATE members SET month_lvl = 0, month_exp = 0")
                await announce.send(f":date:  |  A new month has begun and the monthly leaderboards have been reset.")
                await asyncio.sleep(60)


def setup(bot: commands.Bot):
    bot.add_cog(Levels(bot))

