import discord
from discord.ext import tasks, commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import typing
import asyncio
import traceback
import sys
from cogs.log import log


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="stats")
    @commands.cooldown(rate=2, per=10, type=commands.BucketType.member)
    async def stats(self, ctx: commands.Context, option=None, member: typing.Optional[discord.Member] = None):
        try:
            if option is None and member is None:
                member = ctx.author
                await ctx.send(f"Hey {member.display_name}! You can use this command to get wealth, cookie and level "
                               f"statistics for yourself or another OG member. Syntax: +stats option member")
                ctx.command.reset_cooldown(ctx)

            elif member is None or member is ctx.author:
                member = ctx.author
                val = (member.id, ctx.guild.id)
                if option == "wealth":
                    omnicoin = await get_emoji("omnicoin", self.bot)
                    result = await query(returntype="one", sql="SELECT coins FROM members WHERE member_id = %s "
                                                               "AND guild_id = %s", params=val)
                    msg = await ctx.send(f"{omnicoin}  Fetching your personal wealth...")
                    await asyncio.sleep(1.5)
                    await msg.edit(content=f"{omnicoin}  You have {result[0]} omnicoins in your wallet")
                elif option == "cookie":
                    cookiespin = await get_emoji(880509570978553856, self.bot)
                    result = await query(returntype="one", sql="SELECT cookie_s, cookie_k, cookie_r FROM members WHERE "
                                                               "member_id = %s AND guild_id = %s", params=val)
                    cookie_s = result[0]
                    cookie_r = result[1]
                    cookie_k = result[2]

                    msg = await ctx.send(f"{cookiespin}  Gathering ingredients and baking your cookie stats...")
                    await asyncio.sleep(2)
                    await msg.edit(content=f"{cookiespin}  **{member.display_name}'s Cookie Statistics**\n\n"
                                           f"Sent: {cookie_s}       Received: {cookie_r}        Kept: {cookie_k}")

                elif option == "level":
                    plus1 = await get_emoji(950031480803964758, self.bot)
                    result = await query(returntype="one", sql="SELECT exp, month_exp, lvl, month_lvl FROM members "
                                                               "WHERE member_id = %s AND guild_id = %s", params=val)
                    exp = result[0]
                    m_exp = result[1]
                    lvl = result[2]
                    m_lvl = result[3]

                    msg = await ctx.send(f"{plus1}  Calculating your personal experiences and representing "
                                         f"as numerical data...")
                    await asyncio.sleep(2)
                    await msg.edit(content=f"{plus1}  **{member.display_name}'s Level Statistics**\n\n"
                                           f"Month Lvl: {m_lvl}    Month XP: {m_exp}       Total Lvl: {lvl}    "
                                           f"Total XP: {exp}")
            else:
                val = (member.id, ctx.guild.id)
                if option == "wealth":
                    omnicoin = await get_emoji("omnicoin", self.bot)
                    result = await query(returntype="one", sql="SELECT coins FROM members WHERE member_id = %s "
                                                               "AND guild_id = %s", params=val)
                    msg = await ctx.send(f"{omnicoin}  Fetching {member.display_name}'s wealth...")
                    await asyncio.sleep(1.5)
                    await msg.edit(content=f"{omnicoin}  {member.display_name} has {result[0]} omnicoins in their "
                                           f"wallet.")
                elif option == "cookie":
                    cookiespin = await get_emoji(880509570978553856, self.bot)
                    result = await query(returntype="one", sql="SELECT cookie_s, cookie_k, cookie_r FROM members WHERE "
                                                               "member_id = %s AND guild_id = %s", params=val)
                    cookie_s = result[0]
                    cookie_r = result[1]
                    cookie_k = result[2]

                    msg = await ctx.send(f"{cookiespin}  Gathering ingredients and baking {member.display_name}'s "
                                         f"cookie stats...")
                    await asyncio.sleep(2)
                    await msg.edit(content=f"{cookiespin}  **{member.display_name}'s Cookie Statistics**\n\n"
                                           f"Sent: {cookie_s}       Received: {cookie_r}        Kept: {cookie_k}")

                elif option == "level":
                    plus1 = await get_emoji(950031480803964758, self.bot)
                    result = await query(returntype="one", sql="SELECT exp, month_exp, lvl, month_lvl FROM members "
                                                               "WHERE member_id = %s AND guild_id = %s", params=val)
                    exp = result[0]
                    m_exp = result[1]
                    lvl = result[2]
                    m_lvl = result[3]

                    msg = await ctx.send(f"{plus1}  Calculating {member.display_name}'s experiences and representing "
                                         f"as numerical data...")
                    await asyncio.sleep(2)
                    await msg.edit(content=f"{plus1}  **{member.display_name}'s Level Statistics**\n\n"
                                           f"Month Lvl: {m_lvl}    Month XP: {m_exp}       Total Lvl: {lvl}    "
                                           f"Total XP: {exp}")

        except:
            print("Something went wrong with stats cog:", file=sys.stderr)
            log(str(sys.exc_info()[0]))
            log(str(sys.exc_info()[1]))
            log(str(sys.exc_info()[2]))
            traceback.print_exc()

    @stats.error
    async def stats_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f":hourglass:  |  Woah there! Please wait {round(error.retry_after)} seconds before "
                           f"requesting more stats.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
