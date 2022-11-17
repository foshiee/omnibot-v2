import discord
from discord.ext import commands


class Snipe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_msg = None

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        self.last_msg = message

    @commands.command(name="snipe")
    async def snipe(self, ctx: commands.Context):
        """A command to snipe deleted messages"""
        if not self.last_msg:  # on_message_delete hasn't been triggered since the bot started
            await ctx.send("There is no message to snipe!")
        else:
            author = self.last_msg.author
            content = self.last_msg.content

            embed = discord.Embed(title=f"Message from {author}", description=content)
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Snipe(bot))

