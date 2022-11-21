import discord
from discord import app_commands
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji


rep_cooldown = app_commands.Cooldown(1, 79200)  # 79200 seconds is 22 hours.


def rep_cd_checker(interaction: discord.Interaction):
    return rep_cooldown


class Rep(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rep", description="Give recognition to a fellow OG. Send them rep and big them up.")
    @app_commands.checks.dynamic_cooldown(rep_cd_checker)
    @app_commands.checks.has_role("Gamers")
    async def rep(self, interaction: discord.Interaction, member: discord.Member = None):
        clippy = await get_emoji(695331750372573214, self.bot)
        if clippy is None:
            clippy = ":warning:"
        epic = await get_emoji(350833993245261824, self.bot)
        if epic is None:
            epic = ":flower_playing_cards:"
        try:
            if member.bot:
                await interaction.response.send_message(f":robot:  |  Sorry, you cannot big up a robot."
                                                        f" _sad beep boop_.", ephemeral=True, delete_after=10)
                app_commands.Cooldown.reset(rep_cooldown)
            elif interaction.user.id is member.id:
                await interaction.response.send_message(f"{clippy}  |  Woah there! We know you're cool, "
                                                        f"but you can't big up yourself.", ephemeral=True,
                                                        delete_after=10)
                app_commands.Cooldown.reset(rep_cooldown)
            else:
                val = (interaction.guild.id, member.id)
                result = await query(returntype="one", sql="SELECT rep FROM members WHERE guild_id = %s AND member_id ="
                                                           " %s", params=val)

                if result is None:
                    await interaction.response.send_message(f":question:  |  "
                                                            f"Hmm, I can't find a record for {member.display_name}. "
                                                            f"Have they spoken in this server before?",
                                                            ephemeral=True, delete_after=10)
                    app_commands.Cooldown.reset(rep_cooldown)
                else:
                    current_rep = result[0]
                    current_rep += 1
                    await query(returntype="commit", sql="UPDATE members SET rep = " + str(current_rep) +
                                                         " WHERE guild_id = %s AND member_id = %s", params=val)
                    await interaction.response.send_message(f"{epic}  |  {interaction.user.display_name} bigs up "
                                                            f"{member.mention} and adds 1 to their rep counter. "
                                                            f"{member.display_name} now has {current_rep} rep.")
        except Exception as e:
            print(e)

    @rep.error
    async def on_rep_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.CommandOnCooldown):
            if error.retry_after > 3600:
                await interaction.response.send_message(f":hourglass:  |  You have already given rep today! "
                                                        f"Try again in {round(error.retry_after / 60 / 60)} hours.",
                                                        ephemeral=True)
            elif 3600 > error.retry_after > 60:
                await interaction.response.send_message(f":hourglass:  |  You have already given rep today! "
                                                        f"Try again in {round(error.retry_after / 60)} minutes.",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(f":hourglass:  |  You have already given rep today! "
                                                        f"Try again in {round(error.retry_after)} seconds.",
                                                        ephemeral=True)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Rep(bot))
