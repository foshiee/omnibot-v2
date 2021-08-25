import discord
from discord.ext import commands
from cogs.dbutils import query
import random
import asyncio


class Coins(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="daily")
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)  # 86400 seconds is 24 hours
    async def daily(self, ctx: commands.Context):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(ctx.author.guild.id) + " AND member_id = " + str(ctx.author.id)
                             )

        current_coins = result[0]
        rand_coins = random.randrange(30, 501, step=10)
        current_coins += rand_coins

        await query(returntype="commit", sql="UPDATE members SET coins = " + str(current_coins) + " WHERE guild_id = "
                                             + str(ctx.author.guild.id) + " AND member_id = " + str(ctx.author.id))

        await ctx.send(f" :coin:  |  You've been granted {rand_coins} omnicoins today! "
                       f"Your total is now {current_coins}!")

    @daily.error
    async def daily_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete(delay=3)
            await ctx.send(f":hourglass:  |  You've already claimed your omnicoins for today, try again in "
                           f"{round(error.retry_after/60/60)} hours.")

    @commands.command(name="wallet")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def wallet(self, ctx: commands.Context):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(ctx.author.guild.id) + " AND member_id = " + str(ctx.author.id))

        current_coins = result[0]
        if current_coins == 0:
            await ctx.send(f"You open your wallet to a puff of dust... you are flat broke.")
        elif current_coins >= 10000:
            await ctx.send(f"You open your wallet and count your coins...", delete_after=3)
            await asyncio.sleep(3)
            await ctx.send(content=f":moneybag:  |  You've saved up a king's ransom! You have {current_coins} omnicoins in the coffers.")
        else:
            await ctx.send(f"You open your wallet and count your coins...", delete_after=3)
            await asyncio.sleep(3)
            await ctx.send(content=f":coin:  |  You have {current_coins} omnicoins.")


def setup(bot: commands.Bot):
    bot.add_cog(Coins(bot))
