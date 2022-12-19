import discord
from discord.ext import commands
from cogs.dbutils import query, check_table_exists
import time


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            nt = int(time.time())
            coin_time = None
            welcome_channel = 349229012331003905
            channel = self.bot.get_channel(welcome_channel)
            val = (member.id, member.name, member.guild.id, 0, 0, 1, 1, 0, 0, coin_time, 0, 0, 0, 0, 0, 1, nt)
            if not await check_table_exists("members"):
                await query(returntype="commit", sql="""CREATE TABLE IF NOT EXISTS members 
                                                    (diwor INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(diwor), 
                                                    member_id bigint, member_name varchar(40), guild_id bigint, 
                                                    exp bigint, month_exp bigint, lvl int, month_lvl int, prestige int, 
                                                    coins int, coin_time datetime, coin_streak int, rep int, 
                                                    cookie_s int, cookie_r int, cookie_k int, can_mention int, 
                                                    rank_posttime bigint)""")

                await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, guild_id, exp, 
                                                    month_exp, lvl, month_lvl, prestige, coins, coin_time, coin_streak, 
                                                    rep, cookie_s, cookie_r, cookie_k, can_mention, rank_posttime) 
                                                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            params=val)
            else:
                result = await query(returntype="one", sql="SELECT COUNT(*) FROM members WHERE member_id = '" +
                                                           str(member.id) + "'")
                if result[0] >= 1:
                    pass
                else:
                    await query(returntype="commit", sql="""INSERT INTO members (member_id, member_name, guild_id, exp,
                                                        month_exp, lvl, month_lvl, prestige, coins, coin_time, 
                                                        coin_streak, rep, cookie_s, cookie_r, cookie_k, can_mention, 
                                                        rank_posttime) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                        %s,%s)""", params=val)

            if not channel:
                return
            else:
                await channel.send(f":alien:  Beaming up {member.display_name}. Welcome to OmniGamers Community.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
    print("Welcome extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Welcome")
    print("Welcome extension unloaded.")
