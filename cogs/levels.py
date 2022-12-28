import discord
from discord.ext import commands
from cogs.dbutils import *
from cogs.emojiutils import get_emoji
from cogs.lvl_utils import get_total_exp
import math
import time


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        no_exp_channels = [548164597472034826, 349221525028732929, 391370585571065859, 807425366925770762]
        nt = int(time.time())
        coin_time = None
        rep_time = None
        cookie_time = None
        author = message.author
        guild = message.guild
        channel = message.channel
        plus1 = await get_emoji("plus1", self.bot)
        if plus1 is None:
            plus1 = ":chart_with_upwards_trend:"
        if guild is not None:  # catches ephemeral messages
            if channel.id not in no_exp_channels:
                if not author.bot:
                    # (member_id, member_name, guild_id, exp, month_exp, total_exp, lvl, month_lvl, prestige, coins,
                    # coin_time, coin_streak, rep,rep_time, cookie_s, cookie_r, cookie_k, cookie_time, can_mention,
                    # rank_posttime)
                    val = (author.id, author.name, guild.id, 2, 2, 2, 1, 1, 0, 0, coin_time, 0, 0, rep_time, 0, 0, 0,
                           cookie_time, 1, nt)
                    if not await check_table_exists("members"):
                        await create_members_table()
                        await insert_member(val)
                    else:
                        result = await query(returntype="one", sql="SELECT member_id, guild_id, exp, month_exp, lvl, "
                                                                   "month_lvl, prestige, rank_posttime FROM "
                                                                   "members WHERE guild_id = ' "
                                                                   + str(guild.id) + "' ""AND ""member_id = '"
                                                                   + str(author.id) + "'")

                        if result is None:
                            await insert_member(val)
                        else:
                            current_exp = int(result[2])
                            current_mexp = int(result[3])
                            current_lvl = int(result[4])
                            current_mlvl = int(result[5])
                            total_exp = get_total_exp(current_lvl, current_exp)
                            current_prestige = int(result[6])
                            lastranked_posttime = int(result[7])
                            lvl_xpend = math.floor(5 * (current_lvl ^ 2) + 30 * current_lvl + 100)
                            mlvl_xpend = math.floor(5 * (current_mlvl ^ 2) + 30 * current_mlvl + 100)

                            if lastranked_posttime + 30 < int(time.time()):
                                i = 2
                                current_exp += i
                                current_mexp += i
                                total_exp += i
                                lastranked_posttime = int((time.time()))

                                if current_exp >= lvl_xpend:
                                    current_lvl += 1
                                    current_exp -= lvl_xpend
                                    await message.channel.send(f"{plus1}  {author.mention} just "
                                                               f"leveled up to Lvl. {str(current_lvl)}")

                                if current_mexp >= mlvl_xpend:
                                    current_mlvl += 1
                                    current_mexp -= mlvl_xpend
                                    await message.channel.send(f"{plus1}  {author.display_name} "
                                                               f"just month leveled up "f"to mLvl. {str(current_mlvl)}")

                                if current_lvl > 99:
                                    current_prestige += 1
                                    current_lvl = 1

                            await query(returntype="commit",
                                        sql="UPDATE members SET exp = " + str(current_exp) + ", month_exp = " +
                                            str(current_mexp) + ", total_exp = " + str(total_exp) + ", lvl = "
                                            + str(current_lvl) + ", month_lvl = " + str(current_mlvl) + ", prestige = "
                                            + str(current_prestige) + ", rank_posttime = " + str(lastranked_posttime) +
                                            " WHERE guild_id = " + str(guild.id) + " AND member_id = " + str(author.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
    print("Levels extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Levels")
    print("Levels extension unloaded.")
