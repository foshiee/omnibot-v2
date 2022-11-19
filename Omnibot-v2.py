from typing import Optional, Literal
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Greedy, Context
from dotenv import load_dotenv
from os import getenv
import sys
import traceback
from cogs.log import log
import asyncio

load_dotenv()
token = getenv("TOKEN")
botname = getenv("BOTNAME")
guild_id = getenv("GUILD_ID")

intents = discord.Intents.default()
intents.members = True
intents.messages = True
prefix = commands.when_mentioned
description = botname + "by the OmniDevs."

cogs = ['cogs.welcome', 'cogs.ping', 'cogs.setstatus', 'cogs.snipe', 'cogs.omnicoins', 'cogs.rep',
        'cogs.cookies', 'cogs.levels', 'cogs.monthly_reset', 'cogs.stats']


print(discord.__version__)


class OmniBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=prefix, intents=intents, description=description)

    async def setup_hook(self) -> None:
        if __name__ == '__main__':
            for cog in cogs:
                try:
                    await bot.load_extension(cog)
                    log("Loaded extension " + cog)
                except Exception as e:
                    print(f'Failed to load extension {cog}', file=sys.stderr)
                    log(str(sys.exc_info()[0]))
                    log(str(sys.exc_info()[1]))
                    log(str(sys.exc_info()[2]))
                    traceback.print_exc()
                    print(e)


bot = OmniBot()


@bot.command()
@commands.guild_only()
@commands.check(commands.is_owner())  # Members of the Development Team "omnidevs" are considered owners
async def cogutils(ctx: Context,
                   action: Optional[Literal["load", "unload", "reload", "list"]] = None, cog=None) -> None:
    if action is None and cog is None:
        await ctx.send(
            "Use this command to manage cogs.\nSyntax: @bot cogutils {list/load/unload/reload} {cogname}")
    elif action is None:
        await ctx.send("Invalid input. You must input an action to perform on the cog.")
    elif action == "list":
        for c in cogs:
            print(c)
    if cog is None:
        await ctx.send("You must input a cog.")
    elif "cogs." + cog not in cogs:
        await ctx.send(f"The {cog} cog does not exist.")
    elif action == "load":
        message = await ctx.send(content=f"Loading the {cog} cog, please wait..")
        await bot.load_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f"Finished loading the {cog} cog.")
        print(f"Finished loading the {cog} cog.")
    elif action == "unload":
        message = await ctx.send(content=f"Unloading the {cog} cog, please wait..")
        await bot.unload_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f"Finished unloading the {cog} cog.")
        print(f"Finished unloading the {cog} cog.")
    elif action == "reload":
        await ctx.send(f"The {cog} cog does not exist.")
        message = await ctx.send(content=f"Reloading the {cog} cog, please wait..")
        await bot.reload_extension("cogs." + cog)
        await asyncio.sleep(1.5)
        await message.edit(content=f"Finished reloading the {cog} cog.")
        print(f"Finished reloading the {cog} cog.")


@cogutils.error
async def on_cogutils_error(ctx: commands.Context, error: commands.CommandInvokeError):
    if isinstance(error, commands.NotOwner):
        await ctx.send("Oops! You do not have permission to use that command.")
    elif isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Oops! That cog is not loaded.")
    elif isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send("Oops! That cog is already loaded.")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("Oops! That cog does not exist.")
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send(f"Oops! The cog failed to load.")
    else:
        raise error


@bot.command()
@commands.guild_only()
@commands.check(commands.is_owner())  # Members of the Development Team "omnidevs" are considered owners
async def sync(
  ctx: Context, guilds: Greedy[discord.Object],
        spec: Optional[Literal["current", "copy", "clear", "clearall"]] = None) -> None:
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
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
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

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
    print(f"Synced the tree to {ret}/{len(guilds)}.")


@sync.error
async def on_sync_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.NotOwner):
        await ctx.send("Oops! You do not have permission to use that command.")
    else:
        raise error


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"{botname} online and logged in as {bot.user}")

    activity = discord.Activity(name="Streaming data to the OmniVerse.", type=discord.ActivityType.streaming)
    await bot.change_presence(status=discord.Status.online, activity=activity)


bot.run(token, reconnect=True)
