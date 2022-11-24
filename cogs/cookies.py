import random
import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, Cooldown, CommandOnCooldown, MissingRole
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from typing import Union

cookie_types = ['chocolate', 'choc-chip', 'M&M encrusted', 'gingerbread', 'slightly broken',
                'half-eaten', 'pre-licked', 'golden', 'homemade', 'dark chocolate pistachio sea salt',
                'cinnamon roll sugar', 'brown butter oatmeal', 'kitsilano', 'brown butter bourbon spice',
                'peanut butter & jelly', 'caramel pecan', 'apricot pistachio oatmeal', 'pie crust',
                'nutella lava', 'almond & raspberry jam', 'million dollar', 'vanilla bean',
                'blueberry shortbread', 'red velvet', 'giant', 'tiny', 'small', 'double dark chocolate',
                'white chocolate macadamia', 'white chocolate coconut pecan']
selected_cookie = random.choice(cookie_types)

cookie_cooldown = Cooldown(1, 79200)  # 79200 seconds is 22 hours.


def cookie_cd_checker(interaction: Interaction):
    return cookie_cooldown


class Cookies(commands.GroupCog, name="cookie"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name="Send Cookie", callback=self.send_cookie_context)
        self.bot.tree.add_command(self.ctx_menu)

    @app_commands.command(name="send", description="Send a cookie to an OG member, once per day.")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(cookie_cd_checker)
    async def send(self, interaction: Interaction, member: discord.Member) -> None:
        cookiespin = await get_emoji(1045406030215000175, self.bot)
        if cookiespin is None:
            cookiespin = ":cookie:"

        if member.bot:
            await interaction.response.send_message(
                f":robot:  Sorry, robots can't eat cookies made from organic material."
                f" _sad beep boop_.", ephemeral=True, delete_after=10)
            Cooldown.reset(cookie_cooldown)
        elif member.id is interaction.user.id:
            await interaction.response.send_message(
                f"{cookiespin}  Sorry, you can't send a cookie to yourself. Use the /cookie greed command "
                f"instead!", ephemeral=True, delete_after=20)
            Cooldown.reset(cookie_cooldown)
        else:
            val = (interaction.guild_id, member.id)
            val2 = (interaction.guild_id, interaction.user.id)
            result = await query(returntype="one", sql="SELECT cookie_s, cookie_r FROM members WHERE"
                                                       " guild_id = %s AND member_id = %s", params=val)
            if result is None:
                await interaction.response.send_message(f":question:  |  "
                                                        f"Hmm, I can't find a record for {member.display_name}. "
                                                        f"Have they spoken in this server before?", ephemeral=True,
                                                        delete_after=10)
                return
            else:

                cookie_s = result[0]
                cookie_r = result[1]
                await query(returntype="commit", sql="UPDATE members SET cookie_r = '" + str(cookie_r + 1) +
                                                     "' WHERE guild_id = %s  AND member_id = %s", params=val)
                await query(returntype="commit", sql="UPDATE members SET cookie_s = '" + str(cookie_s + 1) +
                                                     "' WHERE guild_id = %s  AND member_id = %s", params=val2)
                await interaction.response.send_message(f"{cookiespin}  {interaction.user.display_name} has sent "
                                                        f"{member.display_name} a {selected_cookie} cookie!")

    @app_commands.command(name="greed", description="Keep your cookie to yourself! OMNOMNOM!!")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(cookie_cd_checker)  # 79200 seconds is 22 hours
    async def greed(self, interaction: Interaction) -> None:
        cookiemonster = await get_emoji("cookiemonster", self.bot)
        if cookiemonster is None:
            cookiemonster = ":cookie:"

        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT cookie_k FROM members WHERE "
                                                   "guild_id = %s AND member_id = %s", params=val)
        cookie_k = result[0]
        await query(returntype="commit", sql="UPDATE members SET cookie_k = '" + str(cookie_k + 1) +
                                             "' WHERE guild_id = %s  AND member_id = %s", params=val)
        await interaction.response.send_message(
            f"{cookiemonster}  {interaction.user.display_name} is being a greedy cookie monster today and eats "
            f"the cookie themself! OMNOMNOMNOMNOM! ")

    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(cookie_cd_checker)
    async def send_cookie_context(self, interaction: Interaction,
                                  member: Union[discord.Member, discord.User]) -> None:
        cookiespin = await get_emoji("cookiespin", self.bot)
        if cookiespin is None:
            cookiespin = ":cookie:"

        if member.bot:
            await interaction.response.send_message(
                f":robot:  Sorry, robots can't eat cookies made from organic material."
                f" _sad beep boop_.", ephemeral=True, delete_after=10)
            Cooldown.reset(cookie_cooldown)
        elif member.id is interaction.user.id:
            await interaction.response.send_message(
                f"{cookiespin}  Sorry, you can't send a cookie to yourself. Use the /cookie greed command "
                f"instead!", ephemeral=True, delete_after=20)
            Cooldown.reset(cookie_cooldown)
        else:
            val = (interaction.guild_id, member.id)
            val2 = (interaction.guild_id, interaction.user.id)
            result = await query(returntype="one", sql="SELECT cookie_s, cookie_r FROM members WHERE"
                                                       " guild_id = %s AND member_id = %s", params=val)
            if result is None:
                await interaction.response.send_message(f":question:  |  "
                                                        f"Hmm, I can't find a record for {member.display_name}. "
                                                        f"Have they spoken in this server before?", ephemeral=True)
                return
            else:

                cookie_s = result[0]
                cookie_r = result[1]
                await query(returntype="commit", sql="UPDATE members SET cookie_r = '" + str(cookie_r + 1) +
                                                     "' WHERE guild_id = %s  AND member_id = %s", params=val)
                await query(returntype="commit", sql="UPDATE members SET cookie_s = '" + str(cookie_s + 1) +
                                                     "' WHERE guild_id = %s  AND member_id = %s", params=val2)
                await interaction.response.send_message(f"{cookiespin}  {interaction.user.display_name} has sent "
                                                        f"{member.display_name} a {selected_cookie} cookie!")

    async def cog_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, MissingRole):
            await interaction.response.send_message(":warning:  Sorry, you don't have the role required to use this "
                                                    "command ", ephemeral=True, delete_after=10)
            Cooldown.reset(cookie_cooldown)
        elif isinstance(error, CommandOnCooldown):
            if error.retry_after > 3600:
                await interaction.response.send_message(
                    f":hourglass:  You've run out of cookies for today, a fresh batch will finish baking in "
                    f"{round(error.retry_after / 60 / 60)} hours.", ephemeral=True, delete_after=10)
            elif 3600 > error.retry_after > 60:
                await interaction.response.send_message(
                    f":hourglass:  You've run out of cookies for today, a fresh batch will finish baking in "
                    f"{round(error.retry_after / 60)} minutes.", ephemeral=True, delete_after=10)
            else:
                await interaction.response.send_message(
                    f":hourglass:  You've run out of cookies for today, a fresh batch will finish baking in "
                    f"{round(error.retry_after)} seconds.", ephemeral=True, delete_after=error.retry_after)
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
