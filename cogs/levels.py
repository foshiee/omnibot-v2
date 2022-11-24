import discord
from discord.ext import commands
from cogs.dbutils import query, check_table_exists
import math
import time


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        no_exp_channels = []
        nt = int(time.time())
        author = message.author
        guild = message.guild
        channel = message.channel
        if guild is not None:  # catches ephemeral messages
            if channel.id not in no_exp_channels:
                if not author.bot:
                    val = (author.id, author.name, guild.id, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, nt)
                    if not await check_table_exists("members"):
                        await query(returntype="commit", sql="""CREATE TABLE IF NOT EXISTS members (diwor INT NOT 
                        NULL AUTO_INCREMENT, PRIMARY KEY(diwor), member_id bigint, member_name varchar(40), 
                        guild_id bigint, exp bigint, month_exp bigint, lvl int, month_lvl int, prestige int, 
                        coins int, rep int, cookie_s int, cookie_r int, cookie_k int, can_mention int, rank_posttime 
                        bigint)""")

                        await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, 
                        guild_id, exp, month_exp, lvl, month_lvl, prestige, coins, rep, cookie_s, cookie_r, cookie_k, 
                        can_mention, rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                    params=val)
                    else:
                        result = await query(returntype="one", sql="SELECT member_id, guild_id, exp, month_exp, lvl, "
                                                                   "month_lvl, prestige, rank_posttime FROM members "
                                                                   "WHERE guild_id = ' "
                                                                   + str(guild.id) + "' ""AND ""member_id = '"
                                                                   + str(author.id) + "'")

                        if result is None:
                            await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, "
                                                                 guild_id, exp, 
                                                                 month_exp, lvl, month_lvl, prestige, coins, rep, 
                                                                 cookie_r, cookie_s, cookie_k, can_mention, 
                                                                 rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                                 %s,%s,%s,%s,%s,%s)""",
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
                                    await message.channel.send(f":chart_with_upwards_trend:  {author.mention} just "
                                                               f"leveled up to Lvl.{str(current_lvl)}")

                                if current_mexp >= mlvl_xpend:
                                    current_mlvl += 1
                                    current_mexp -= mlvl_xpend
                                    await message.channel.send(f":chart_with_upwards_trend:  {author.display_name} "
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
                                        str(guild.id) + " AND member_id = " + str(author.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
    print("Levels extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Levels")
    print("Levels extension unloaded.")
