import discord
from discord.ext import commands


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.default)  # type determines scope, default = global
    async def status(self, ctx: commands.Context):
        """Set Omnibot's status message."""
        if ctx.invoked_subcommand is None:
            await ctx.send(f":warning:  Oops! {ctx.subcommand_passed} does not belong to status.", delete_after=10)

    @status.command()
    async def playing(self, game: str):
        """Set playing status message"""
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.Game(str(game)))

    @status.command()
    async def listening(self, text: str):
        """Set listening status message"""
        activity = discord.ActivityType.listening(text)
        await self.bot.change_presence(status=discord.Status.idle, activity=activity)

    @status.error
    async def status_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f":hourglass:  This command is on cooldown, try again after {round(error.retry_after)} "
                           f"seconds", delete_after=error.retry_after)
        elif isinstance(error, commands.NotOwner):
            await ctx.send(f":closed_lock_with_key:  Oops! You do not have permission to use that command.",
                           delete_after=10)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Status(bot))
    print("Status extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Status")
    print("Status extension unloaded.")
