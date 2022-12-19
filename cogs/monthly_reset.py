import discord
from discord.ext import tasks, commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from cogs.log import log
import math
import asyncio


def ordinal(x):
    return "%d%s" % (x, "tsnrhtdd"[(math.floor(x / 10) % 10 != 1) * (x % 10 < 4) * x % 10::4])


class MonthlyReset(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.monthly_reset.start(bot)

    @tasks.loop(seconds=30, reconnect=True)
    async def monthly_reset(self, ctx):
        announce = self.bot.get_channel(349221525028732929)
        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"
        now = discord.utils.utcnow()

        if now.day == 1 and now.hour == 0 and now.minute == 1:
            log("It's a new month! Getting leaderboards..")
            result = await query(returntype="one", sql="SELECT member_id, month_lvl, month_exp, coins FROM members "
                                                       "WHERE guild_id = %s ORDER BY month_lvl DESC, month_exp "
                                                       "DESC LIMIT 0,1", params=announce.guild.id)

            member = discord.utils.get(announce.guild.members, id=result[0])
            admin_role = discord.utils.get(announce.guild.roles, name="Admins")
            krypt_role = discord.utils.get(announce.guild.roles, name="Kryptonite")
            month_result = await query(returntype="ten", sql="""SELECT member_id, month_lvl, month_exp FROM
                                                                       members WHERE guild_id = %s ORDER BY month_lvl 
                                                                       DESC, month_exp DESC""",
                                       params=announce.guild.id)

            description = "**Another month is behind us. Here are last month's top posters!**\r\n\r\n"
            r = 0
            for row in month_result:
                member = discord.utils.get(announce.guild.members, id=row[0])
                if r == 0:
                    message = f":first_place:    **{member.mention}**"
                elif r == 1:
                    message = f":second_place:    **{member.mention}**"
                elif r == 3:
                    message = f":third_place:    **{member.mention}**"
                else:
                    message = f"{ordinal(r)}:    {member.display_name}"
                mlvl = f"**Lvl {row[1]}**"
                description += message + " - " + mlvl + "\n"
                r += 1
            await announce.send(description)

            if int(result[0]) == krypt_role or admin_role in member.roles:
                await announce.send(f"**Nobody has earned the Kryptonite role this month. Better luck next month!**")
            elif krypt_role in member.roles:
                val = (int(result[3]) + 1500, announce.guild.id, member.id)
                await query(returntype="commit",
                            sql="UPDATE members SET coins = %s WHERE guild_id = %s and member_id = %s", params=val)
                await announce.send(f"**{member.mention} is the top poster this month, beating Kryptix.**\r\n"
                                    f"They already have the {krypt_role.name} role, so they have been "
                                    f"awarded 1500 {omnicoin} instead!")
            else:
                await member.add_roles(krypt_role)
                await announce.send(f"{member.mention} is the top poster this month, beating Kryptix.\r\nThey "
                                    f"have been awarded the {krypt_role.name} role!")

            await query(returntype="commit", sql="UPDATE members SET month_lvl = 0, month_exp = 0")
            await announce.send(f":date:  |  A new month has begun and the monthly leaderboards have been reset.")
            await asyncio.sleep(60)

    @monthly_reset.before_loop
    async def monthly_reset_before(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(MonthlyReset(bot))
    print("MonthlyReset extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("MonthlyReset")
    print("MonthlyReset extension unloaded.")
