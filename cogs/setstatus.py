import discord
from discord.ext import commands


class SetStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setstatus")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.default)  # type determines scope, default = global
    async def setstatus(self, ctx: commands.Context, *, text: str):
        #  Set the bot's status.
        await self.bot.change_presence(activity=discord.Game(name=text))

    @setstatus.error
    async def setstatus_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown, try again after {round(error.retry_after)} seconds",
                           delete_after=5)
        print(error)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetStatus(bot))
