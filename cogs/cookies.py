import asyncio
import random

import discord
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import traceback
import sys
from cogs.log import log


class Cookie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cookie")
    @commands.cooldown(rate=1, per=79200, type=commands.BucketType.member)
    async def cookie(self, ctx, member: discord.Member = None):
        try:
            cookiespin = await get_emoji(880509570978553856, self.bot)
            if cookiespin is None:
                cookiespin = ":cookie:"

            cookiemonster = await get_emoji(596349000056307742, self.bot)
            if cookiemonster is None:
                cookiemonster = ":cookie:"

            cookie_types = ['chocolate', 'choc-chip', 'M&M encrusted', 'gingerbread', 'slightly broken',
                            'half-eaten', 'pre-licked', 'golden', 'homemade', 'dark chocolate pistachio sea salt',
                            'cinnamon roll sugar', 'brown butter oatmeal', 'kitsilano', 'brown butter bourbon spice',
                            'peanut butter & jelly', 'caramel pecan', 'apricot pistachio oatmeal', 'pie crust',
                            'nutella lava', 'almond & raspberry jam', 'million dollar', 'vanilla bean',
                            'blueberry shortbread', 'red velvet', 'giant', 'tiny', 'small', 'double dark chocolate',
                            'white chocolate macadamia', 'white chocolate coconut pecan']
            selected_cookie = random.choice(cookie_types)

            if member is None:
                await ctx.send(f"Use +cookie <username> to give a user a cookie once per day, or keep it to yourself.")
                ctx.command.reset_cooldown(ctx)
            elif member.bot:
                await ctx.send(f":robot:  Sorry, robots can't eat cookies made from organic material."
                               f" _sad beep boop_.")
                ctx.command.reset_cooldown(ctx)
            elif member is ctx.message.author:
                val = (ctx.guild.id, member.id)
                result = await query(returntype="one", sql="SELECT cookie_k FROM members WHERE"
                                                           " guild_id = %s AND member_id = %s", params=val)

                cookie_k = result[0]

                await query(returntype="commit", sql="UPDATE members SET cookie_k = '" + str(cookie_k + 1) +
                                                     "' WHERE guild_id = %s  AND member_id = %s", params=val)
                await ctx.send(f"{cookiemonster}  {ctx.message.author.display_name} decided to keep their "
                               f"{selected_cookie} cookie today. Om Nom Nom!")
            else:
                val = (ctx.guild.id, member.id)
                val2 = (ctx.guild.id, ctx.message.author.id)
                result = await query(returntype="one", sql="SELECT cookie_s, cookie_r FROM members WHERE"
                                                           " guild_id = %s AND member_id = %s", params=val)

                if result is None:
                    await ctx.send(f":question:  Hmm, I can't find a record for {member}. "
                                   f"Have they spoken in this server before?")
                    ctx.command.reset_cooldown(ctx)

                else:
                    cookie_s = result[0]
                    cookie_r = result[1]
                    await query(returntype="commit", sql="UPDATE members SET cookie_r = '" + str(cookie_r + 1) +
                                                         "' WHERE guild_id = %s  AND member_id = %s", params=val)
                    await query(returntype="commit", sql="UPDATE members SET cookie_s = '" + str(cookie_s + 1) +
                                                         "' WHERE guild_id = %s  AND member_id = %s", params=val2)
                    await ctx.send(f"{cookiespin}  {ctx.message.author.display_name} has sent "
                                   f"{member.display_name} a {selected_cookie} cookie!")

        except:
            print("Something went wrong with cookies cog:", file=sys.stderr)
            log(str(sys.exc_info()[0]))
            log(str(sys.exc_info()[1]))
            log(str(sys.exc_info()[2]))
            traceback.print_exc()

    @cookie.error
    async def cookie_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            if error.retry_after > 3600:
                await ctx.send(f":hourglass:  You have already used your cookie for today, "
                               f"{ctx.message.author.display_name}! "
                               f"The next batch will finish baking in {round(error.retry_after / 60 / 60)} hours.")
            elif 3600 > error.retry_after > 60:
                await ctx.send(f":hourglass:  You have already used your cookie for today, "
                               f"{ctx.message.author.display_name}! "
                               f"The next batch will finish baking in {round(error.retry_after / 60)} minutes.")
            else:
                await ctx.send(f":hourglass:  You have already used your cookie for today, "
                               f"{ctx.message.author.display_name}! "
                               f"The next batch will finish baking in {round(error.retry_after)} seconds.")


def setup(bot: commands.Bot):
    bot.add_cog(Cookie(bot))
