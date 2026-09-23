import discord
from discord.ext import commands
from cogs.dbutils import *
import time


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            nt = int(time.time())
            coin_time = None
            rep_time = None
            cookie_time = None
            welcome_channel = 349229012331003905
            channel = self.bot.get_channel(welcome_channel)
            # (member_id, member_name, guild_id, exp, month_exp, total_exp, lvl, month_lvl, prestige, coins,
            # coin_time, coin_streak, rep,rep_time, cookie_s, cookie_r, cookie_k, cookie_time, can_mention,
            # rank_posttime)
            val = (member.id, member.name, member.guild.id, 5, 5, 5, 1, 1, 0, 0, coin_time, 0, 0, rep_time, 0, 0, 0,
                   cookie_time, 1, nt)
            if not await check_table_exists("members"):
                await create_members_table()
                await insert_member(val)
            else:
                # Rows are per member per guild, and every command reads them
                # with both keys. Counting on member_id alone meant that someone
                # already known from another guild was treated as present here
                # and never got a row, so their commands found nothing.
                result = await query(returntype="one",
                                     sql="SELECT COUNT(*) FROM members WHERE member_id = %s AND guild_id = %s",
                                     params=(member.id, member.guild.id))
                if result[0] < 1:
                    await insert_member(val)
            if not channel:
                return
            else:
                await channel.send(f":alien:  Beaming up {member.display_name}. Welcome to OmniGamers Community.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
    print("Welcome extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Welcome")
    print("Welcome extension unloaded.")
