import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, MissingAnyRole
import time
import asyncio


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Get Omnibot's current websocket and API latency")
    @app_commands.checks.has_any_role("Admins", "Developers")
    async def ping(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        start_time = time.time()
        await interaction.edit_original_response(content=":ping_pong:  Testing Ping...")
        end_time = time.time()
        await asyncio.sleep(1)
        await interaction.edit_original_response(content=f":ping_pong:  Pong! {round(self.bot.latency * 1000)}ms\n"
                                                         f"API: {round((end_time - start_time) * 1000)}ms")

    @ping.error
    async def on_ping_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, MissingAnyRole):
            await interaction.response.send_message(":closed_lock_with_key:  Oops! You do not have the required role "
                                                    "to run this command.",
                                                    ephemeral=True)
        else:
            raise error


# Now, we need to set up this cog somehow, and we do that by making a setup function:
async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
    print("Ping extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Ping")
    print("Ping extension unloaded.")