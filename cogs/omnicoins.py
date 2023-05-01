import datetime

import discord
from discord import app_commands
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import random
import asyncio
from datetime import timedelta


class OmniCoins(commands.GroupCog, name="omnicoins"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.cooldown(1, 79200)  # 79200 seconds is 22 hours
    @app_commands.command(name="daily", description="Claim your daily omnicoin allowance.")
    async def daily(self, interaction: discord.Interaction):
        result = await query(returntype="one", sql="SELECT coins, coin_time, coin_streak FROM members WHERE guild_id = "
                                                   + str(interaction.guild_id) + " AND member_id = "
                                                   + str(interaction.user.id))

        current_coins = result[0]
        coin_time = result[1]
        coin_streak = result[2]
        new_time = interaction.created_at.replace(tzinfo=None)
        streak_delta = timedelta(days=1)

        if coin_time is None:
            coin_streak = 0
        else:
            time_sum = coin_time + streak_delta
            if time_sum > new_time:
                coin_streak += 1
            else:
                coin_streak = 0

        rand_coins = random.randrange(5, 250, step=5)
        if coin_streak > 0:
            current_coins += (rand_coins + (50 * coin_streak))
        else:
            current_coins += rand_coins

        coin_val = (current_coins, interaction.guild_id, interaction.user.id)
        time_val = (new_time, interaction.guild_id, interaction.user.id)
        streak_val = (coin_streak, interaction.guild_id, interaction.user.id)

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        await query(returntype="commit", sql="UPDATE members SET coins = %s WHERE guild_id = %s AND member_id = %s",
                    params=coin_val)
        await query(returntype="commit", sql="UPDATE members SET coin_time = %s WHERE guild_id = %s AND member_id = %s",
                    params=time_val)
        await query(returntype="commit", sql="UPDATE members SET coin_streak = %s WHERE guild_id = %s AND "
                                             "member_id = %s", params=streak_val)

        if coin_streak > 0:
            await interaction.response.send_message(f"{omnicoin}  You're on a {coin_streak} day streak! You've claimed "
                                                    f"{rand_coins + (50 * coin_streak)} "
                                                    f"({rand_coins} + {50 * coin_streak}) coins today.")
        else:
            await interaction.response.send_message(f"{omnicoin}  You've claimed {rand_coins} omnicoins today.")

    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            if error.retry_after > 3600:
                await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {round(error.retry_after / 60 / 60)} hours.", ephemeral=True)
            elif 3600 > error.retry_after > 60:
                await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {round(error.retry_after / 60)} minutes.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {error.retry_after} seconds.", ephemeral=True)
        else:
            raise error

    @app_commands.checks.cooldown(rate=1, per=10)
    @app_commands.command(name="wallet", description="See how wealthy you are.")
    async def wallet(self, interaction: discord.Interaction):
        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = %s AND member_id = %s",
                             params=val)

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        current_coins = result[0]
        if current_coins <= 1000:
            await interaction.response.send_message(f" {omnicoin}  You open your wallet to a puff of dust and "
                                                    f"{current_coins} omnicoins.")
        elif current_coins >= 20000:
            await interaction.response.send_message(f"You open your wallet and count your coins...")
            await asyncio.sleep(1.5)
            await interaction.edit_original_response(content=f":moneybag:  You've saved up a king's ransom! You have "
                                                             f"{current_coins} omnicoins in the coffers.")
        else:
            await interaction.response.send_message(f"You open your wallet and count your coins...")
            await asyncio.sleep(1.5)
            await interaction.edit_original_response(content=f" {omnicoin}  You have {current_coins} omnicoins.")

    @wallet.error
    async def wallet_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f":hourglass:  You are on cooldown! Try again after "
                                                    f"{round(error.retry_after)} seconds.", ephemeral=True,
                                                    delete_after=error.retry_after)


async def setup(bot: commands.Bot):
    await bot.add_cog(OmniCoins(bot))
    print("OmniCoins extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("OmniCoins")
    print("OmniCoins extension unloaded.")
