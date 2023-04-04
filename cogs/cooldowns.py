import discord
from discord.ext import commands
from discord import app_commands, Interaction
from cogs.cooldown_utils import on_cooldown
from cogs.dbutils import query


class CoolDowns(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="cooldowns")
    async def cooldowns(self, interaction: Interaction):
        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT coin_time, cookie_time, rep_time FROM members"
                                                   "WHERE guild_id = %s AND member_id = %s", params=val)

