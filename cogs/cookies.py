import random
import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, MissingRole
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from cogs.cooldown_utils import on_cooldown
from typing import Union
from datetime import timedelta

cookie_types = ['chocolate', 'choc-chip', 'M&M encrusted', 'gingerbread', 'golden', 'dark chocolate pistachio sea salt',
                'cinnamon roll sugar', 'brown butter oatmeal', 'kitsilano', 'brown butter bourbon spice',
                'peanut butter & jelly', 'caramel pecan', 'apricot pistachio oatmeal', 'pie crust',
                'nutella lava', 'almond & raspberry jam', 'million dollar', 'vanilla bean',
                'blueberry shortbread', 'red velvet', 'double dark chocolate',
                'white chocolate macadamia', 'white chocolate coconut pecan']

cookie_mods = ['homemade', 'giant', 'tiny', 'small', 'slightly broken',
                'half-eaten', 'pre-licked']

cooking_gif = discord.File("images/cooking.gif", filename="cooking.gif")

class Cookies(commands.GroupCog, name="cookie"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name="Send Cookie", callback=self.send_cookie_context)
        self.bot.tree.add_command(self.ctx_menu)
    
    def cd_embed(self, interaction: Interaction):
        cd_embed_desc = "You've run out of cookies for today. The next batch is in the oven.."
        cd_embed = discord.Embed(title="Baking more cookies..", description=cd_embed_desc, 
                                        colour=discord.Colour.orange())
        cd_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        cd_embed.set_image(url="attachment://cooking.gif")
        cd_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        return cd_embed

    async def send_cookie(self, interaction: Interaction, member: discord.Member) -> None:
        cookiespin = await get_emoji("cookieSpin", self.bot)
        if cookiespin is None:
            cookiespin = ":cookie:"

        try:
            if member.bot:
                await interaction.response.send_message(
                    f":robot:  Sorry, robots can't eat cookies made from organic material."
                    f" _sad beep boop_.", ephemeral=True, delete_after=20)
            elif member.id is interaction.user.id:
                await interaction.response.send_message(
                    f"{cookiespin}  Sorry, you can't send a cookie to yourself. Try the /cookie greed command "
                    f"instead!", ephemeral=True, delete_after=20)
            else:
                member_val = (interaction.guild_id, member.id)
                user_val = (interaction.guild_id, interaction.user.id)
                member_result = await query(returntype="one", sql="SELECT cookie_r FROM members WHERE"
                                                                " guild_id = %s AND member_id = %s", params=member_val)
                if member_result is None:
                    await interaction.response.send_message(f":question:  "
                                                            f"Hmm, I can't find a record for {member.display_name}. "
                                                            f"Have they spoken in this server before?", ephemeral=True)
                else:
                    user_result = await query(returntype="one", sql="SELECT cookie_s, cookie_time FROM members WHERE "
                                                                    "guild_id = %s AND member_id = %s", params=user_val)

                    cookie_r = member_result[0]
                    cookie_s = user_result[0]
                    cookie_time = user_result[1]
                    new_time = interaction.created_at.replace(tzinfo=None)
                    delta = timedelta(hours=22)

                    if on_cooldown(cookie_time, new_time, delta):
                        cd_sum = cookie_time + delta
                        time_diff = cd_sum.timestamp() - new_time.timestamp()
                        send_cd_embed = self.cd_embed(interaction)
                        send_cd_embed.set_thumbnail(url=cookiespin.url)
                        if time_diff > 3600:
                            send_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60 / 60)} hours")
                            await interaction.response.send_message(file=cooking_gif, embed=send_cd_embed, ephemeral=True, 
                                                                    delete_after=30)
                        elif 3600 > time_diff > 60:
                            send_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60)} minutes")
                            await interaction.response.send_message(file=cooking_gif, embed=send_cd_embed, ephemeral=True, 
                                                                    delete_after=30)
                        else:
                            send_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff)} seconds")
                            await interaction.response.send_message(file=cooking_gif, embed=send_cd_embed, ephemeral=True, 
                                                                    delete_after=time_diff)
                    else:
                        selected_cookie = random.choice(cookie_types)
                        cookie_mod = random.choice(cookie_mods)
                        cookie_r += 1
                        cookie_s += 1
                        r_val = (cookie_r, interaction.guild_id, member.id)
                        s_val = (cookie_s, new_time, interaction.guild_id, interaction.user.id)

                        send_embed = discord.Embed(title=f"{cookie_mod.capitalize()} {selected_cookie} cookie sent!", 
                                                   colour=discord.Colour.dark_gold())
                        send_embed.set_author(name=interaction.user.display_name,icon_url=interaction.user.display_avatar)
                        send_embed.set_thumbnail(url=cookiespin.url)
                        send_embed.add_field(name="Delivered to", value=member.mention)
                        send_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

                        await query(returntype="commit", sql="UPDATE members SET cookie_r = %s WHERE guild_id = %s  "
                                                            "AND member_id = %s", params=r_val)
                        await query(returntype="commit", sql="UPDATE members SET cookie_s = %s, cookie_time = %s WHERE "
                                                            "guild_id = %s  AND member_id = %s", params=s_val)
                        await interaction.response.send_message(embed=send_embed)
        except Exception as e:
            print(e)

    @app_commands.command(name="send", description="Send a cookie to an OG member, once per day.")
    async def send(self, interaction: Interaction, member: discord.Member) -> None:
        await self.send_cookie(interaction, member)

    @app_commands.command(name="greed", description="Keep your cookie to yourself! OMNOMNOM!!")
    async def greed(self, interaction: Interaction) -> None:
        cookiemonster = await get_emoji("cookiemonster", self.bot)
        if cookiemonster is None:
            cookiemonster = ":cookie:"

        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT cookie_k, cookie_time FROM members WHERE "
                                                   "guild_id = %s AND member_id = %s", params=val)
        cookie_k = result[0]
        cookie_time = result[1]
        new_time = interaction.created_at.replace(tzinfo=None)
        delta = timedelta(hours=22)

        if on_cooldown(cookie_time, new_time, delta):
            cd_sum = cookie_time + delta
            time_diff = cd_sum.timestamp() - new_time.timestamp()
            greed_cd_embed = self.cd_embed(interaction)
            greed_cd_embed.set_thumbnail(url=cookiemonster.url)
            if time_diff > 3600:
                greed_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60 / 60)} hours")
                await interaction.response.send_message(file=cooking_gif, embed=greed_cd_embed, ephemeral=True, 
                                                        delete_after=30)
            elif 3600 > time_diff > 60:
                greed_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60)} minutes")
                await interaction.response.send_message(file=cooking_gif, embed=greed_cd_embed, ephemeral=True, 
                                                        delete_after=30)
            else:
                greed_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff)} seconds")
                await interaction.response.send_message(file=cooking_gif, embed=greed_cd_embed, ephemeral=True, 
                                                        delete_after=time_diff)

        else:
            selected_cookie = random.choice(cookie_types)
            cookie_mod = random.choice(cookie_mods)
            cookie_k += 1
            val = (cookie_k, new_time, interaction.guild_id, interaction.user.id)

            greed_embed_desc = f"You eat your {cookie_mod} {selected_cookie} cookie like a greedy cookie monster."
            greed_embed = discord.Embed(title="OMNOMNOMNOMNOM!", description=greed_embed_desc, 
                                        colour=discord.Colour.dark_blue())
            greed_embed.set_author(name=interaction.user.display_name,icon_url=interaction.user.display_avatar)
            greed_embed.set_thumbnail(url=cookiemonster.url)
            greed_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

            await query(returntype="commit", sql="UPDATE members SET cookie_k = %s, cookie_time = %s "
                                                 "WHERE guild_id = %s  AND member_id = %s", params=val)
            await interaction.response.send_message(embed=greed_embed)

    async def send_cookie_context(self, interaction: Interaction,
                                  member: Union[discord.Member, discord.User]) -> None:
        await self.send_cookie(interaction, member)

    async def cog_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, MissingRole):
            await interaction.response.send_message(":warning:  Sorry, you don't have the role required to use this "
                                                    "command ", ephemeral=True, delete_after=10)
        else:
            raise error

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)


async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot))
    print("Cookies extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Cookies")
    print("Cookies extension unloaded.")
