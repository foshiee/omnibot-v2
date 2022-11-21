import discord
from discord.ext import commands


async def get_emoji(emote, ctx: commands.Bot.emojis):
    try:
        for emoji in ctx.emojis:
            if emote is str:
                if emoji.name == str(emote):
                    e_id = int(emoji.id)
                    e_object = ctx.get_emoji(e_id)
                    return e_object
            else:
                if emoji.id == int(emote):
                    e_id = int(emoji.id)
                    e_object = ctx.get_emoji(e_id)
                    return e_object
        return None

    except Exception as e:
        print("Unable to get emoji")
        print(e)

