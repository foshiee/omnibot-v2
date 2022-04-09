import discord
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import random
import asyncio


class Coins(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="daily")
    @commands.cooldown(rate=1, per=79200, type=commands.BucketType.member)  # 79200 seconds is 22 hours
    async def daily(self, ctx: commands.Context):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(ctx.author.guild.id) + " AND member_id = " + str(ctx.author.id)
                             )

        current_coins = result[0]
        rand_coins = random.randrange(1, 350, step=5)
        current_coins += rand_coins

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        await query(returntype="commit", sql="UPDATE members SET coins = " + str(current_coins) + " WHERE guild_id = "
                                             + str(ctx.author.guild.id) + " AND member_id = " + str(ctx.author.id))

        await ctx.send(f" {omnicoin}  You've been granted {rand_coins} omnicoins today! "
                       f"Your total is now {current_coins}!")

    @daily.error
    async def daily_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete(delay=3)
            if error.retry_after > 3600:
                await ctx.send(f":hourglass:  You've already claimed your omnicoins for today, try again in "
                               f"{round(error.retry_after / 60 / 60)} hours.")
            elif 3600 > error.retry_after > 60:
                await ctx.send(f":hourglass:  You've already claimed your omnicoins for today, try again in "
                               f"{round(error.retry_after / 60)} minutes.")
            else:
                await ctx.send(f":hourglass:  You've already claimed your omnicoins for today, try again in "
                               f"{error.retry_after} seconds.")

    @commands.command(name="wallet")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.member)
    async def wallet(self, ctx: commands.Context):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(ctx.author.guild.id) + " AND member_id = " +
                                                   str(ctx.author.id))

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        current_coins = result[0]
        if current_coins <= 100:
            await ctx.send(f" {omnicoin}  You open your wallet to a puff of dust and {current_coins} omnicoins.")
        elif current_coins >= 10000:
            message = await ctx.send(f"You open your wallet and count your coins...")
            await asyncio.sleep(1.5)
            await message.edit(content=f":moneybag:  You've saved up a king's ransom! You have {current_coins} "
                                       f"omnicoins in the coffers.")
        else:
            message = await ctx.send(f"You open your wallet and count your coins...")
            await asyncio.sleep(1.5)
            await message.edit(content=f" {omnicoin}  You have {current_coins} omnicoins.")

    @wallet.error
    async def wallet_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete(delay=3)
            await ctx.send(f":hourglass:  You are on cooldown! Try again after {round(error.retry_after)} seconds.")


def setup(bot: commands.Bot):
    bot.add_cog(Coins(bot))
