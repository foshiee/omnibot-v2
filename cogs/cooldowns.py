import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, CommandOnCooldown
from cogs.cooldown_utils import on_cooldown, format_remaining
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from cogs.member_utils import send_no_record
from datetime import timedelta

DAILY_DELTA = timedelta(hours=22)


class CoolDowns(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.cooldown(1, 10)
    @app_commands.command(name="cooldowns", description="See which of your daily commands are ready to use.")
    async def cooldowns(self, interaction: Interaction):
        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT coin_time, cookie_time, rep_time FROM members "
                                                   "WHERE guild_id = %s AND member_id = %s", params=val)
        if result is None:
            await send_no_record(interaction)
            return

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"
        cookiespin = await get_emoji("cookieSpin", self.bot)
        if cookiespin is None:
            cookiespin = ":cookie:"
        epic = await get_emoji("epic", self.bot)
        if epic is None:
            epic = ":flower_playing_cards:"

        now = interaction.created_at.replace(tzinfo=None)
        # coin_time is the record of the last daily claim. The gate on
        # /omnicoins daily is the app_commands cooldown decorator, which keeps
        # its buckets in memory, so a restart can make the claim available again
        # before this says it is.
        rows = ((f"{omnicoin}  Daily omnicoins", result[0]),
                (f"{cookiespin}  Cookie", result[1]),
                (f"{epic}  Rep", result[2]))

        embed = discord.Embed(title="Your cooldowns", colour=discord.Colour.blurple())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

        for label, last_used in rows:
            if on_cooldown(last_used, now, DAILY_DELTA):
                remaining = (last_used + DAILY_DELTA).timestamp() - now.timestamp()
                value = f":hourglass:  {format_remaining(remaining)}"
            else:
                value = ":white_check_mark:  Ready"
            embed.add_field(name=label, value=value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, CommandOnCooldown):
            await interaction.response.send_message(f":hourglass:  Woah there, not so fast. Try again in "
                                                    f"{round(error.retry_after)} seconds.",
                                                    ephemeral=True, delete_after=error.retry_after)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(CoolDowns(bot))
    print("CoolDowns extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("CoolDowns")
    print("CoolDowns extension unloaded.")
