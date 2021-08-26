import discord
from discord.ext import commands
from cogs.dbutils import query
from cogs.log import log
from cogs.emojiutils import get_emoji
import traceback
import sys


class Rep(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="rep")
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.member)
    async def rep(self, ctx, member: discord.Member = None):
        clippy = await get_emoji(695331750372573214, self.bot)
        try:
            if member is None:
                await ctx.send(f"Use the rep command with a @username to big them up, giving them a rep point.")
            elif member.bot:
                await ctx.send(f":robot:  |  Sorry, you cannot big up a robot. _sad beep boop_.")
            elif ctx.author.id == member.id:
                await ctx.send(f"{clippy}  |  Woah there! We know you're cool, but you can't big up yourself.")
            else:
                val = (ctx.guild.id, member.id)
                result = await query(returntype="one", sql="SELECT rep FROM members WHERE guild_id = %s AND member_id ="
                                                           " %s", params=val)
                if result is None:
                    await ctx.send(f":question:  |  Hmm, I can't find a record for {member.display_name}. "
                                   f"Have they spoken in this server before?")
                else:
                    current_rep = result[0]
                    current_rep += 1
                    await query(returntype="commit", sql="UPDATE members SET rep = " + str(current_rep) +
                                                         " WHERE guild_id = %s AND member_id = %s", params=val)
                    await ctx.send(f"{ctx.message.author.display_name} biggs up {member.mention} and adds 1 to their "
                                   f"rep counter. {member.display_name} now has {current_rep} rep.")
        except:
            print("Something went wrong with rep cog:", file=sys.stderr)
            log(str(sys.exc_info()[0]))
            log(str(sys.exc_info()[1]))
            log(str(sys.exc_info()[2]))
            traceback.print_exc()

    @rep.error
    async def rep_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete(delay=5)
            await ctx.send(f":hourglass:  |  You have already given rep today! "
                           f"Try again in {round(error.retry_after)/60/60} hours.")


def setup(bot: commands.Bot):
    bot.add_cog(Rep(bot))


