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
            val = (member.id, member.name, member.guild.id, 2, 2, 2, 1, 1, 0, 0, coin_time, 0, 0, rep_time, 0, 0, 0,
                   cookie_time, 1, nt)
            if not await check_table_exists("members"):
                await create_members_table()
                await insert_member(val)
            else:
                result = await query(returntype="one", sql="SELECT COUNT(*) FROM members WHERE member_id = '" +
                                                           str(member.id) + "'")
                if result[0] >= 1:
                    pass
                else:
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
