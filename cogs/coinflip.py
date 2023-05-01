import random
import discord
from discord import app_commands, Interaction, Embed, Colour
from discord.app_commands import AppCommandError, CommandOnCooldown, Choice
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji


def flip_coin():
    outcome = random.choice(["heads","tails"])
    return outcome


class CoinFlip(commands.Cog, name="coinflip"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.checks.cooldown(1, 5)
    @app_commands.describe(guess="Guess the outcome of the coin flip")
    @app_commands.describe(bet="Number of omnicoins to bet")
    @app_commands.choices(guess=[
        Choice(name="Heads", value="heads"),
        Choice(name="Tails", value="tails")
    ])
    @app_commands.command(name="coinflip")
    async def coin_flip(self, interaction: Interaction, guess: Choice[str], bet: int = None) -> None:
        omnicoin = await get_emoji("omnicoin", self.bot)
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = %s AND member_id = %s", 
                             params=(interaction.guild_id, interaction.user.id))
        wallet = result[0]
        try:
            if bet is None or 0:
                await interaction.response.send_message(f"You must bet at least 1 {omnicoin}")
            elif bet > wallet:
                poor_man_embed = Embed(title="You can't afford that!", colour=Colour.brand_red())
                poor_man_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                poor_man_embed.set_thumbnail(url=omnicoin.url)
                poor_man_embed.add_field(name="Your Wallet", value=f"{wallet}{omnicoin}")
                poor_man_embed.set_footer(text=self.bot.user.display_name,icon_url=self.bot.user.display_avatar)
                await interaction.response.send_message(embed=poor_man_embed)
            else:
                outcome = flip_coin()
                if outcome is not guess:
                    wallet-=bet
                    loser_embed = Embed(title=outcome, description=f"You lost {bet}{omnicoin}", 
                                                colour=Colour.brand_red())
                    loser_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                    loser_embed.set_thumbnail(url=omnicoin.url)
                    loser_embed.add_field(name=f"New {omnicoin} balance", value=f"{wallet}{omnicoin}")
                    loser_embed.set_footer(text=self.bot.user.display_name,icon_url=self.bot.user.display_avatar)
                    await interaction.response.send_message(embed=loser_embed)
                else:
                    wallet+=bet
                    win_embed = Embed(title=outcome, description=f"You won {bet}{omnicoin}", 
                                                colour=Colour.brand_green())
                    win_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                    win_embed.set_thumbnail(url=omnicoin.url)
                    win_embed.add_field(name=f"New {omnicoin} balance", value=f"{wallet}{omnicoin}")
                    win_embed.set_footer(text=self.bot.user.display_name,icon_url=self.bot.user.display_avatar)
                    await interaction.response.send_message(embed=win_embed)
                await query(returntype="commit", sql="UPDATE members SET coins = %s WHERE guild_id = %s AND member_id = %s", 
                                params=(wallet, interaction.guild_id, interaction.user.id))
        except Exception as e:
            print(e)

    @coin_flip.error
    async def coin_flip_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, CommandOnCooldown):
            await interaction.response.send_message(f":hourglass: Woah! Not so fast. "
                                                    "Try again in {error.retry_after} seconds.", ephemeral=True)
        else:
            raise error
            
async def setup(bot: commands.Bot):
    await bot.add_cog(CoinFlip(bot))
    print("CoinFlip extension loaded.")


async def teardown(bot: commands.Bot):
    await bot.remove_cog("CoinFlip")
    print("CoinFlip extension unloaded.")
