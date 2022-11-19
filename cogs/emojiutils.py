import discord
from discord.ext import commands
from cogs.log import log
import traceback
import sys


async def get_emoji(emote, ctx: commands.Bot.emojis):
    try:
        for emoji in ctx.emojis:
            if emoji.name == str(emote):
                e_id = int(emoji.id)
                e_object = ctx.get_emoji(e_id)
                return e_object
            elif emoji.id == int(emote):
                e_id = int(emoji.id)
                e_object = ctx.get_emoji(e_id)
                return e_object
        return None

    except Exception as e:
        print("Unable to get emoji")
        log(str(sys.exc_info()[0]))
        print(e)
        log(str(sys.exc_info()[2]))
        traceback.print_exc()
