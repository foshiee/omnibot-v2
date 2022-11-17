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

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents, description=botname + "by the OmniDevs.")

extensions = ['cogs.welcome', 'cogs.ping', 'cogs.setstatus', 'cogs.snipe', 'cogs.coins', 'cogs.rep',
              'cogs.cookies', 'cogs.levels', 'cogs.monthly_reset', 'cogs.stats']


@bot.event
async def on_ready():
    print(f"{botname} online and logged in as {bot.user}")
    if __name__ == '__main__':
        for extension in extensions:
            try:
                await bot.load_extension(extension)
                log("Loaded extension " + extension)
            except Exception as e:
                print(f'Failed to load extension {extension}', file=sys.stderr)
                log(str(sys.exc_info()[0]))
                log(str(sys.exc_info()[1]))
                log(str(sys.exc_info()[2]))
                traceback.print_exc()

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
    except Exception as e:
        print(e)

    activity = discord.Activity(name="Streaming data to the OmniVerse.", type=discord.ActivityType.streaming)
    await bot.change_presence(status=discord.Status.online, activity=activity)

bot.run(token, reconnect=True)
