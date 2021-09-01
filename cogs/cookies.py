import asyncio
import discord
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji


class Cookie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cookie")
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.member)
    async def cookie(self, ctx, member: discord.Member = None, option=None):
        cookiespin = await get_emoji(880509570978553856, self.bot)
        if cookiespin is None:
            cookiespin = ":cookie:"

        cookiemonster = await get_emoji(596349000056307742, self.bot)
        if cookiemonster is None:
            cookiemonster = ":cookie:"

        if option is None:
            if member is None:
                await ctx.send(f"Use +cookie @username to give a user a cookie once per day, or keep it to yourself.")
            elif member.bot:
                await ctx.send(f":robot:  |  Sorry, robots can't eat cookies made from organic material."
                               f" _sad beep boop_.")
            else:
                val = (ctx.guild.id, member.id)
                val2 = (ctx.guild.id, ctx.message.author.id)
                result = await query(returntype="one", sql="SELECT cookie_s, cookie_k, cookie_r FROM members WHERE"
                                                           " guild_id = %s AND member_id = %s", params=val)
                if result is None:
                    await ctx.send(f":question:  |  Hmm, I can't find a record for {member.display_name}. "
                                   f"Have they spoken in this server before?")
                else:
                    cookie_s = result[0]
                    cookie_k = result[1]
                    cookie_r = result[2]

                    if member.id == ctx.message.author.id:
                        await query(returntype="commit", sql="UPDATE members SET cookie_k = '" + str(cookie_k+1) +
                                                             "' WHERE guild_id = %s  AND member_id = %s", params=val)
                        await ctx.send(f"{cookiemonster}  |  {ctx.message.author.display_name} decided to keep their "
                                       f"cookie today. Om Nom Nom!")
                    else:
                        await query(returntype="commit", sql="UPDATE members SET cookie_r = '" + str(cookie_r+1) +
                                                             "' WHERE guild_id = %s  AND member_id = %s", params=val)
                        await query(returntype="commit", sql="UPDATE members SET cookie_s = '" + str(cookie_s + 1) +
                                                             "' WHERE guild_id = %s  AND member_id = %s", params=val2)
                        await ctx.send(f"{cookiespin}  |  {ctx.message.author.display_name} has sent "
                                       f"{member.display_name} a cookie!")
        elif option == "stats":
            val = (ctx.guild.id, member.id)
            result = await query(returntype="one", sql="SELECT cookie_s, cookie_k, cookie_r FROM members WHERE"
                                                       " guild_id = %s AND member_id = %s", params=val)
            cookie_s = result[0]
            cookie_k = result[1]
            cookie_r = result[2]

            message = await ctx.send(f"Gathering ingredients and baking cookie statistics for {member.display_name}...")
            await asyncio.sleep(2)
            await message.edit(content=f"{cookiespin}  **{member.display_name}'s Cookie Statistics**\n\n"
                                       f"Sent: {cookie_s}       Received: {cookie_r}        Kept: {cookie_k}")


def setup(bot: commands.Bot):
    bot.add_cog(Cookie(bot))
