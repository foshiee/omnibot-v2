import discord
from discord import app_commands
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import random
import asyncio

coin_cooldown = app_commands.Cooldown(1, 79200)  # 79200 seconds is 22 hours.


def coin_cd_checker(interaction: discord.Interaction):
    return coin_cooldown


class OmniCoins(commands.GroupCog, name="omnicoins"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="daily", description="Claim your daily omnicoin allowance.")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(coin_cd_checker)  # 79200 seconds is 22 hours
    async def daily(self, interaction: discord.Interaction):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(interaction.guild_id) + " AND member_id = "
                                                   + str(interaction.user.id))

        current_coins = result[0]
        rand_coins = random.randrange(1, 350, step=5)
        current_coins += rand_coins

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        await query(returntype="commit", sql="UPDATE members SET coins = " + str(current_coins) + " WHERE guild_id = "
                                             + str(interaction.guild_id) + " AND member_id = " + str(
            interaction.user.id))

        await interaction.response.send_message(f" {omnicoin}  You've been granted {rand_coins} omnicoins today! "
                                                f"Your total is now {current_coins}!")

    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            if error.retry_after > 3600:
                return await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {round(error.retry_after / 60 / 60)} hours.", ephemeral=True)
            elif 3600 > error.retry_after > 60:
                return await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {round(error.retry_after / 60)} minutes.", ephemeral=True)
            else:
                return await interaction.response.send_message(
                    f":hourglass:  You've already claimed your omnicoins for "
                    f"today, try again in {error.retry_after} seconds.", ephemeral=True)
        elif isinstance(error, app_commands.MissingRole):
            discord.app_commands.Cooldown.reset(coin_cooldown)
            return await interaction.response.send_message("Sorry, you don't have the role required to use this command"
                                                           , ephemeral=True)
        else:
            discord.app_commands.Cooldown.reset(coin_cooldown)
            raise error

    @app_commands.command(name="wallet", description="See how wealthy you are.")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.cooldown(rate=1, per=10)
    async def wallet(self, interaction: discord.Interaction):
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = "
                                                   + str(interaction.guild_id) + " AND member_id = " +
                                                   str(interaction.user.id))

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        current_coins = result[0]
        if current_coins <= 100:
            await interaction.response.send_message(f" {omnicoin}  You open your wallet to a puff of dust and "
                                                    f"{current_coins} omnicoins.")
        elif current_coins >= 10000:
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
