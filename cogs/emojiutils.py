import discord
from discord.ext import commands
from cogs.log import log
import traceback
import sys


async def get_emoji(emote, ctx: commands.Bot):
    try:
        for emoji in ctx.emojis:
            if emoji.name == str(emote) or emoji.id == int(emote):
                e_id = int(emoji.id)
                e_object = ctx.get_emoji(e_id)
                return e_object

        return None

    except:
        print("Unable to get emoji")
        log(str(sys.exc_info()[0]))
        log(str(sys.exc_info()[1]))
        log(str(sys.exc_info()[2]))
        traceback.print_exc()
        return None
