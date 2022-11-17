import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
import sys
import traceback
from cogs.log import log

load_dotenv()
token = getenv("TOKEN")
botname = getenv("BOTNAME")
guild_id = getenv("GUILD_ID")

intents = discord.Intents.default()
intents.members = True
prefix = "+"
description = botname + "by the OmniDevs."

cogs = ['cogs.welcome', 'cogs.ping', 'cogs.setstatus', 'cogs.snipe', 'cogs.coins', 'cogs.rep',
        'cogs.cookies', 'cogs.levels', 'cogs.monthly_reset', 'cogs.stats']

print(discord.__version__)


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=prefix, intents=intents, description=description)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=discord.Object(id=guild_id))
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
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands(s)")
        except Exception as e:
            print(e)


bot = Bot()


@bot.event
async def on_ready():
    print(f"{botname} online and logged in as {bot.user}")

    activity = discord.Activity(name="Streaming data to the OmniVerse.", type=discord.ActivityType.streaming)
    await bot.change_presence(status=discord.Status.online, activity=activity)


bot.run(token, reconnect=True)
