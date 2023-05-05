import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, MissingRole, ContextMenu
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from cogs.cooldown_utils import on_cooldown
from datetime import timedelta


class Rep(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = ContextMenu(name='Rep', callback=self.rep_context)
        self.bot.tree.add_command(self.ctx_menu)

    async def send_rep(self, interaction: discord.Interaction, member: discord.Member):
        clippy = await get_emoji("clippy", self.bot)
        if clippy is None:
            clippy = ":warning:"
        epic = await get_emoji("epic", self.bot)
        if epic is None:
            epic = ":flower_playing_cards:"
        try:
            if member.bot:
                await interaction.response.send_message(f":robot:  Sorry, you cannot big up a robot."
                                                        f" _sad beep boop_.", ephemeral=True, delete_after=10)
            elif interaction.user.id is member.id:
                await interaction.response.send_message(f"{clippy}  Woah there! We know you're cool, "
                                                        f"but you can't big up yourself.", ephemeral=True,
                                                        delete_after=10)
            else:
                val = (interaction.guild.id, member.id)
                result = await query(returntype="one", sql="SELECT rep, rep_time FROM members WHERE guild_id = %s AND "
                                                        "member_id = %s", params=val)

                if result is None:
                    await interaction.response.send_message(f":question:  "
                                                            f"Hmm, I can't find a record for {member.display_name}. "
                                                            f"Have they spoken in this server before?",
                                                            ephemeral=True, delete_after=10)
                else:
                    time_val = (interaction.guild_id, interaction.user.id)
                    time_result = await query(returntype="one", sql="SELECT rep_time FROM members WHERE guild_id = %s "
                                                                    "AND member_id = %s", params=time_val)
                    current_rep = result[0]
                    rep_time = time_result[0]
                    current_rep += 1
                    new_time = interaction.created_at.replace(tzinfo=None)
                    delta = timedelta(hours=22)

                    if on_cooldown(rep_time, new_time, delta):
                        cd_sum = rep_time + delta
                        time_diff = cd_sum.timestamp() - new_time.timestamp()
                        
                        rep_cd_embed = discord.Embed(title="Rep cooldown", description="You have already given rep today.", 
                                                     colour=discord.Colour.orange())
                        rep_cd_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                        rep_cd_embed.set_thumbnail(url=epic.url)
                        rep_cd_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

                        if time_diff > 3600:
                            rep_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60 / 60)} hours")
                            await interaction.response.send_message(embed=rep_cd_embed, ephemeral=True, 
                                                                    delete_after=20)
                        elif 3600 > time_diff > 60:
                            rep_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff / 60)} minutes")
                            await interaction.response.send_message(embed=rep_cd_embed, ephemeral=True, 
                                                                    delete_after=20)
                        else:
                            rep_cd_embed.add_field(name=":hourglass:", value=f"{round(time_diff)} seconds")
                            await interaction.response.send_message(embed=rep_cd_embed, ephemeral=True, 
                                                                    delete_after=time_diff)
                    else:
                        cr_val = (current_rep, interaction.guild_id, member.id)
                        nt_val = (new_time, interaction.guild_id, interaction.user.id)

                        reb_embed_desc = (f"{interaction.user.display_name} bigs up {member.mention} "
                                          f"and adds 1 to their rep counter.")
                        rep_embed = discord.Embed(title="Rep up!",description=reb_embed_desc, 
                                                  colour=discord.Colour.dark_magenta())
                        rep_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                        rep_embed.set_thumbnail(url=epic.url)
                        rep_embed.add_field(name=f"{member.display_name}'s rep", value=current_rep)
                        rep_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

                        await query(returntype="commit", sql="UPDATE members SET rep = %s "
                                                            "WHERE guild_id = %s AND member_id = %s", params=cr_val)
                        await query(returntype="commit", sql="UPDATE members SET rep_time = %s WHERE guild_id = %s AND "
                                                            "member_id = %s", params=nt_val)
                        await interaction.response.send_message(embed=rep_embed)
        except Exception as e:
            print(e)


    @app_commands.command(name="rep", description="Give recognition to a fellow OG. Send them rep and big them up.")
    async def rep(self, interaction: Interaction, member: discord.Member):
        await self.send_rep(interaction, member)

    async def rep_context(self, interaction: Interaction, member: discord.Member):
        await self.send_rep(interaction, member)

    async def cog_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, MissingRole):
            await interaction.response.send_message(":closed_lock_with_key:  Oops! You do not have the required role"
                                                    "to use that command", ephemeral=True, delete_after=10)
        else:
            raise error

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rep(bot))
    print("Rep extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("Rep")
    print("Rep extension unloaded.")
