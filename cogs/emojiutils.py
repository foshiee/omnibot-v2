import discord
from discord.ext import commands


def get_emoji(emote, ctx: commands.Bot.emojis):
    try:
        for emoji in ctx.emojis:
            if type(emote) == str:
                if emote == emoji.name:
                    e_id = int(emoji.id)
                    e_object = ctx.get_emoji(e_id)
                    return e_object
            else:
                if emote == emoji.id:
                    e_id = int(emoji.id)
                    e_object = ctx.get_emoji(e_id)
                    return e_object
        return None

    except Exception as e:
        print("Unable to get emoji")
        print(e)

