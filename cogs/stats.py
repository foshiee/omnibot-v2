import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, Cooldown, CommandOnCooldown, MissingRole
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from typing import Optional
import asyncio


stats_cooldown = Cooldown(2, 10)


def stats_cd_checker(interaction: discord.Interaction):
    return stats_cooldown


class Stats(commands.GroupCog, name="stats", description="Fetch various stats for OGs."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cookies", description="Get cookie stats for yourself or other OGs.")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(stats_cd_checker)
    async def cookies(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        try:
            cookiespin = await get_emoji("cookieSpin", self.bot)
            if cookiespin is None:
                cookiespin = ":cookie"
            if member is None or member is interaction.user:
                member = interaction.user
            elif member.bot:
                await interaction.response.send_message(":robot: Sorry, robots can't eat cookies made from organic "
                                                        "material. _sad beep boop_.")
                Cooldown.reset(stats_cooldown)

            val = (member.id, interaction.guild_id)
            result = await query(returntype="one", sql="SELECT cookie_s, cookie_k, cookie_r FROM members WHERE "
                                                       "member_id = %s AND guild_id = %s", params=val)

            if result is None:
                await interaction.response.send_message(f":question:  "
                                                        f"Hmm, I can't find a record for {member.display_name}. "
                                                        f"Have they spoken in this server before?", ephemeral=True)
                Cooldown.reset(stats_cooldown)
                return
            else:
                cookie_s = result[0]
                cookie_r = result[1]
                cookie_k = result[2]

                if member is interaction.user:
                    await interaction.response.send_message(f"{cookiespin}  "
                                                            f"Gathering ingredients and baking your cookie stats..."
                                                            )
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{cookiespin}  "
                                                                     f"**{member.display_name}'s Cookie "
                                                                     f"Statistics**"
                                                                     f"\n\nSent: {cookie_s}       "
                                                                     f"Received: {cookie_r}        "
                                                                     f"Kept: {cookie_k}")
                else:
                    await interaction.response.send_message(f"{cookiespin}  "
                                                            f"Gathering ingredients and {member.display_name}'s "
                                                            f"cookie stats...")
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{cookiespin}  "
                                                                     f"**{member.display_name}'s Cookie "
                                                                     f"Statistics**"
                                                                     f"\n\nSent: {cookie_s}       "
                                                                     f"Received: {cookie_r}        "
                                                                     f"Kept: {cookie_k}")
        except Exception as e:
            print(e)

    @app_commands.command(name="exp", description="Get exp stats for yourself or other OGs.")
    @app_commands.checks.has_role("Gamers")
    @app_commands.checks.dynamic_cooldown(stats_cd_checker)
    async def exp(self, interaction: Interaction, member: Optional[discord.Member] = None) -> None:
        try:
            plus1 = await get_emoji("plus1", self.bot)
            if plus1 is None:
                plus1 = ":chart_with_upwards_trend:"

            if member is None or member is interaction.user:
                member = interaction.user
            elif member.bot:
                await interaction.response.send_message(":robot:  Sorry, robots do not have human experiences."
                                                        " _sad beep boop_.", ephemeral=True)
                Cooldown.reset(stats_cooldown)

            val = (member.id, interaction.guild_id)
            result = await query(returntype="one", sql="SELECT exp, month_exp, lvl, month_lvl FROM members "
                                                       "WHERE member_id = %s AND guild_id = %s", params=val)
            if result is None:
                await interaction.response.send_message(f":question:  "
                                                        f"Hmm, I can't find a record for {member.display_name}. "
                                                        f"Have they spoken in this server before?", ephemeral=True)
                Cooldown.reset(stats_cooldown)
                return
            else:
                exp = result[0]
                m_exp = result[1]
                lvl = result[2]
                m_lvl = result[3]

                if member is interaction.user:
                    await interaction.response.send_message(f"{plus1}  "
                                                            f"Calculating your personal experiences and "
                                                            f"representing as numerical data...")
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{plus1}  **{member.display_name}'s Level "
                                                                     f"Statistics**\n\nMonth Lvl: {m_lvl}    "
                                                                     f"Month XP: {m_exp}       Total Lvl: {lvl}    "
                                                                     f"Total XP: {exp}")
                else:
                    await interaction.response.send_message(f"{plus1}  "
                                                            f"Calculating {member.display_name}'s experiences and "
                                                            f"representing as numerical data...")
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{plus1}  **{member.display_name}'s Level "
                                                                     f"Statistics**\n\nMonth Lvl: {m_lvl}    "
                                                                     f"Month XP: {m_exp}       Total Lvl: {lvl}    "
                                                                     f"Total XP: {exp}")
        except Exception as e:
            print(e)

    @app_commands.command(name="rep", description="Get rep stats for yourself or other OGs.")
    @app_commands.checks.has_role("Gamer")
    @app_commands.checks.dynamic_cooldown(stats_cd_checker)
    async def rep(self, interaction: Interaction, member: Optional[discord.Member]) -> None:
        try:
            epic = await get_emoji("epic", self.bot)
            if epic is None:
                epic = ":flower_playing_cards:"
            if member is None or member is interaction.user:
                member = interaction.user
            elif member.bot:
                await interaction.response.send_message(":robot:  Sorry, robots don't understand human praise "
                                                        "mechanisms _sad beep boop_.", ephemeral=True)
                Cooldown.reset(stats_cooldown)

            val = (member.id, interaction.guild_id)
            result = await query(returntype="one", sql="SELECT rep FROM members "
                                                       "WHERE member_id = %s AND guild_id = %s", params=val)

            if result is None:
                await interaction.response.send_message(f":question:  "
                                                        f"Hmm, I can't find a record for {member.display_name}. "
                                                        f"Have they spoken in this server before?", ephemeral=True)
                Cooldown.reset(stats_cooldown)
                return
            else:
                rep = int(result[0])

                if member is interaction.user:
                    await interaction.response.send_message(f"{epic}  Counting number of times you have been "
                                                            f"bigged up...")
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{epic}  OGs have bigged you up {rep} times.")
                else:
                    await interaction.response.send_message(f"{epic}  Counting number of times "
                                                            f"{member.display_name} has been bigged up...")
                    await asyncio.sleep(2)
                    await interaction.edit_original_response(content=f"{epic}  {member.display_name} has been "
                                                                     f"bigged up {rep} times.")
        except Exception as e:
            print(e)

    async def cog_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, CommandOnCooldown):
            await interaction.response.send_message(f":hourglass:  Woah there, not so fast."
                                                    f"Try again in {round(error.retry_after)} seconds.",
                                                    ephemeral=True, delete_after=error.retry_after)
        elif isinstance(error, MissingRole):
            await interaction.response.send_message(":closed_lock_with_key:  Oops! You do not have the required role"
                                                    "to use that command", ephemeral=True, delete_after=10)
            Cooldown.reset(stats_cooldown)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
    print("Stats extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Stats")
    print("Stats extension unloaded.")
