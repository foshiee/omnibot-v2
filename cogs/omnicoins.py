import datetime

import discord
from discord import app_commands, Embed, Colour
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
import random
import asyncio
from datetime import timedelta


class OmniCoins(commands.GroupCog, name="omnicoins"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.cooldown(1, 79200)  # 79200 seconds is 22 hours
    @app_commands.command(name="daily", description="Claim your daily omnicoin allowance.")
    async def daily(self, interaction: discord.Interaction):
        result = await query(returntype="one", sql="SELECT coins, coin_time, coin_streak FROM members WHERE guild_id = "
                                                   + str(interaction.guild_id) + " AND member_id = "
                                                   + str(interaction.user.id))

        current_coins = result[0]
        coin_time = result[1]
        coin_streak = result[2]
        new_time = interaction.created_at.replace(tzinfo=None)
        streak_delta = timedelta(days=1)

        if coin_time is None:
            coin_streak = 0
        else:
            time_sum = coin_time + streak_delta
            if time_sum > new_time:
                coin_streak += 1
            else:
                coin_streak = 0

        rand_coins = random.randrange(5, 250, step=5)
        if coin_streak > 0:
            current_coins += (rand_coins + (50 * coin_streak))
        else:
            current_coins += rand_coins

        coin_val = (current_coins, interaction.guild_id, interaction.user.id)
        time_val = (new_time, interaction.guild_id, interaction.user.id)
        streak_val = (coin_streak, interaction.guild_id, interaction.user.id)

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        await query(returntype="commit", sql="UPDATE members SET coins = %s WHERE guild_id = %s AND member_id = %s",
                    params=coin_val)
        await query(returntype="commit", sql="UPDATE members SET coin_time = %s WHERE guild_id = %s AND member_id = %s",
                    params=time_val)
        await query(returntype="commit", sql="UPDATE members SET coin_streak = %s WHERE guild_id = %s AND "
                                             "member_id = %s", params=streak_val)
        
        omnicoin_daily_embed = Embed(title="Daily omnicoins claimed!",description="",colour=Colour.gold())
        omnicoin_daily_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        omnicoin_daily_embed.set_thumbnail(url=omnicoin.url)
        omnicoin_daily_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        omnicoin_daily_embed.add_field(name="coinpurse", value=f"{current_coins} {omnicoin}")

        if coin_streak > 0:
            omnicoin_daily_embed.insert_field_at(index=0, name="Omnicoins claimed", value=f"{rand_coins} + {50 * coin_streak} {omnicoin}",
                                                 inline=True)
            omnicoin_daily_embed.insert_field_at(index=1, name="Streak", value=coin_streak + 1, inline=True)
            await interaction.response.send_message(embed=omnicoin_daily_embed)
        else:
            omnicoin_daily_embed.insert_field_at(index=0,name="Omnicoins claimed", value=f"{rand_coins} {omnicoin}",inline=True)
            await interaction.response.send_message(embed=omnicoin_daily_embed)

    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        omnicoin = await get_emoji("omnicoin", self.bot)
        daily_cd_embed_desc = "You've already received your daily omnicoin allowance. Try again tomorrow."
        daily_cd_embed = discord.Embed(title="Omnicoins already claimed", description=daily_cd_embed_desc, 
                                       colour=discord.Colour.orange())
        daily_cd_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)    
        daily_cd_embed.set_thumbnail(url=omnicoin.url)
        daily_cd_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        if isinstance(error, app_commands.CommandOnCooldown):
            if error.retry_after > 3600:
                daily_cd_embed.add_field(name=":hourglass:", value=f"{round(error.retry_after / 60 / 60)} hours")
                await interaction.response.send_message(embed=daily_cd_embed, ephemeral=True, delete_after=30)
            elif 3600 > error.retry_after > 60:
                daily_cd_embed.add_field(name=":hourglass:", value=f"{round(error.retry_after / 60)} minutes")
                await interaction.response.send_message(embed=daily_cd_embed, ephemeral=True, delete_after=30)
            else:
                daily_cd_embed.add_field(name=":hourglass:", value=f"{round(error.retry_after)} seconds")
                await interaction.response.send_message(embed=daily_cd_embed, ephemeral=True, 
                                                        delete_after=error.retry_after)
        else:
            raise error

    @app_commands.checks.cooldown(rate=1, per=10)
    @app_commands.command(name="coinpurse", description="See how wealthy you are.")
    async def coinpurse(self, interaction: discord.Interaction):
        val = (interaction.guild_id, interaction.user.id)
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = %s AND member_id = %s",
                             params=val)

        omnicoin = await get_emoji("omnicoin", self.bot)
        if omnicoin is None:
            omnicoin = ":coin:"

        current_coins = result[0]
        await interaction.response.send_message(f"You open your coinpurse and count your coins...")
        await asyncio.sleep(1.5)
        coinpurse_embed = discord.Embed(title="coinpurse", colour=Colour.dark_gold())
        coinpurse_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        coinpurse_embed.set_thumbnail(url='https://discord.com/assets/80046b0579dcdc6aa402.svg')
        coinpurse_embed.set_footer(text=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        if current_coins <= 1000:
            coinpurse_embed.add_field(name="", value=f"You have {current_coins} {omnicoin} and 4 dust bunnies.")
            await interaction.edit_original_response(embed=coinpurse_embed)
        elif current_coins >= 20000:
            coinpurse_embed.add_field(name=":moneybag:", value=f"You've saved up a king's ransom! You have "
                                                             f"{current_coins} {omnicoin} in the coffers.")
            await interaction.edit_original_response(embed=coinpurse_embed)
        else:
            coinpurse_embed.add_field(name="", value=f"You have {current_coins} {omnicoin}")
            await interaction.edit_original_response(embed=coinpurse_embed)

    @coinpurse.error
    async def coinpurse_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f":hourglass:  You are on cooldown! Try again after "
                                                    f"{round(error.retry_after)} seconds.", ephemeral=True,
                                                    delete_after=error.retry_after)


async def setup(bot: commands.Bot):
    await bot.add_cog(OmniCoins(bot))
    print("OmniCoins extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("OmniCoins")
    print("OmniCoins extension unloaded.")
