from typing import Optional, Literal
import discord
from discord import Interaction
from discord import app_commands
from discord.app_commands import AppCommandError, CommandOnCooldown, MissingRole
from discord.ext import commands
from discord.ext.commands import Greedy, Context
from dotenv import load_dotenv
from os import getenv
import asyncio
import logging

load_dotenv()
token = getenv("TOKEN")
botname = getenv("BOTNAME")
guild_id = getenv("GUILD_ID")

intents = discord.Intents.default()
intents.members = True
intents.messages = True
prefix = commands.when_mentioned
description = botname + "by the OmniDevs."

cog_list = ['cogs.welcome', 'cogs.ping', 'cogs.status', 'cogs.snipe', 'cogs.omnicoins', 'cogs.rep',
            'cogs.levels', 'cogs.monthly_reset',  'cogs.cookies', 'cogs.stats', 'cogs.coinflip']

logging.basicConfig(level=logging.INFO)

logging.info("Running discord.py version " + discord.__version__)


class OmniBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=prefix, intents=intents, description=description)

    async def setup_hook(self) -> None:
        if __name__ == '__main__':
            for cog in cog_list:
                try:
                    await bot.load_extension(cog)
                except Exception as e:
                    logging.warning(f'Failed to load extension {cog}')
                    print(e)


bot = OmniBot()
tree = bot.tree


@bot.group()
@commands.guild_only()
@commands.is_owner()
async def cogs(ctx: Context):
    """Admin utility to manage Omnibot's cogs."""
    if ctx.invoked_subcommand is None:
        await ctx.send(f":warning:  Oops! {ctx.subcommand_passed} does not belong to cogs.", delete_after=10)


@cogs.command()
async def load(ctx: Context, cog=None):
    """Load one of Omnibot's cogs"""
    if cog is None:
        await ctx.send(":warning:  You must input a cog.", delete_after=10)
    elif "cogs." + cog not in cog_list:
        await ctx.send(f":warning:  The {cog} cog does not exist.", delete_after=10)
    else:
        message = await ctx.send(content=f":small_red_triangle:  Loading the {cog} cog, please wait..")
        await bot.load_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f":white_check_mark:  The {cog} cog is now loaded.")


@cogs.command()
async def unload(ctx: Context, cog=None):
    """Unload one of Omnibot's cogs"""
    if cog is None:
        await ctx.send(":warning:  You must input a cog.", delete_after=10)
    elif "cogs." + cog not in cog_list:
        await ctx.send(f":warning:  The {cog} cog does not exist.", delete_after=10)
    else:
        message = await ctx.send(content=f":small_red_triangle_down:  Unloading the {cog} cog, please wait..")
        await bot.unload_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f":white_check_mark:  Finished unloading the {cog} cog.")


@cogs.command()
async def reload(ctx: Context, cog=None):
    """Reload one of Omnibot's cogs"""
    if cog is None:
        await ctx.send(":warning:  You must input a cog.")
    elif "cogs." + cog not in cog_list:
        await ctx.send(f":warning:  The {cog} cog does not exist.", delete_after=10)
    else:
        message = await ctx.send(content=f":recycle:  Reloading the {cog} cog, please wait..")
        await bot.reload_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f":white_check_mark:  Finished reloading the {cog} cog.")


@cogs.error
async def on_cogs_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.NotOwner):
        await ctx.send(":closed_lock_with_key:  Oops! You do not have permission to use that command.", delete_after=10)


@load.error
async def on_load_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send(":warning:  Oops! That cog is already loaded.", delete_after=10)
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send(":warning:  Oops! That cog does not exist.", delete_after=10)
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send(f":warning:  Oops! The cog failed to load.", delete_after=10)
    else:
        raise error


@unload.error
async def on_unload_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send(":warning:  Oops! That cog is not loaded.", delete_after=10)
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send(":warning:  Oops! That cog does not exist.", delete_after=10)
    else:
        raise error


@reload.error
async def on_load_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.ExtensionNotFound):
        await ctx.send(":warning:  Oops! That cog does not exist.", delete_after=10)
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send(f":warning:  Oops! The cog failed to load.", delete_after=10)
    else:
        raise error


@bot.command()
@commands.guild_only()
@commands.is_owner()  # Members of the Development Team "omnidevs" are considered owners
async def sync(
        ctx: Context, guilds: Greedy[discord.Object],
        spec: Optional[Literal["current", "copy", "clear", "clearall"]] = None) -> None:
    """Admin utility to sync slash commands"""
    if not guilds:
        if spec == "current":  # sync current guild
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "copy":  # copies all global app commands to current guild and syncs
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "clear":  # clears all commands from current guild and syncs (removes guild commands)
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        elif spec == "clearall":  # clears all commands from guild and global and syncs
            ctx.bot.tree.clear_commands(guild=None)
            await ctx.bot.tree.sync()
            synced = []
        else:
            synced = await ctx.bot.tree.sync()  # global sync

        if spec == "clearall":
            await ctx.send("Cleared all commands globally")
        else:
            await ctx.send(
                f":cyclone:  Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            print(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
            return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f":cyclone:  Synced the tree to {ret}/{len(guilds)}.")
    print(f"Synced the tree to {ret}/{len(guilds)}.")


@sync.error
async def on_sync_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.NotOwner):
        await ctx.send(":closed_lock_with_key:  Oops! You do not have permission to use that command.", delete_after=10)
    else:
        raise error


@tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError):
    if isinstance(error, CommandOnCooldown):
        if error.retry_after > 3600:
            await interaction.response.send_message(f":hourglass:  That command is on cooldown. "
                                                    f"Try again in {round(error.retry_after / 60 / 60)} hours.",
                                                    ephemeral=True, delete_after=10)
        elif 3600 > error.retry_after > 60:
            await interaction.response.send_message(f":hourglass:  That command is on cooldown. "
                                                    f"Try again in {round(error.retry_after / 60)} minutes.",
                                                    ephemeral=True, delete_after=10)
        else:
            await interaction.response.send_message(f":hourglass:  That command is on cooldown. "
                                                    f"Try again in {round(error.retry_after)} seconds.",
                                                    ephemeral=True, delete_after=error.retry_after)
    elif isinstance(error, MissingRole):
        await interaction.response.send_message(":closed_lock_with_key:  Oops! You do not have the required role "
                                                "to use that command.", ephemeral=True, delete_after=10)
    else:
        raise error


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"{botname} online and logged in as {bot.user}")

    activity = discord.Activity(name="and streaming data from the OmniVerse.", type=discord.ActivityType.listening)
    await bot.change_presence(status=discord.Status.idle, activity=activity)


bot.run(token, reconnect=True)
