import random
import discord
from discord import app_commands, Interaction, Embed, Colour
from discord.app_commands import AppCommandError, CommandOnCooldown, Choice
from discord.ext import commands
from cogs.dbutils import query
from cogs.emojiutils import get_emoji
from typing import Optional


def flip_coin():
    outcome = random.choice(["heads","tails"])
    return outcome


class CoinFlip(commands.Cog, name="coinflip"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.omnicoin = get_emoji("omnicoin", self.bot)

    def create_embed(self, interaction: Interaction, title: Optional[str], description: Optional[str], 
                           colour: Colour, wallet, guess: Optional[Choice[str]]):
        embed = Embed(title=title, description=description, colour=colour)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url=self.omnicoin.url)
        embed.add_field(name="Wallet", value=f"{wallet} {self.omnicoin}", inline=True)
        if guess:
            embed.add_field(name="Your guess", value=guess.name)
        embed.set_footer(text=self.bot.user.display_name,icon_url=self.bot.user.display_avatar)
        return embed


    @app_commands.checks.cooldown(1, 5)
    @app_commands.describe(guess="Guess the outcome of the coin flip")
    @app_commands.describe(bet="Number of omnicoins to bet")
    @app_commands.choices(guess=[
        Choice(name="Heads", value="heads"),
        Choice(name="Tails", value="tails")
    ])
    @app_commands.command(name="coinflip")
    async def coin_flip(self, interaction: Interaction, guess: Choice[str], bet: int = None) -> None:
        result = await query(returntype="one", sql="SELECT coins FROM members WHERE guild_id = %s AND member_id = %s", 
                             params=(interaction.guild_id, interaction.user.id))
        wallet = result[0]
        try:
            if bet is None or 0:
                await interaction.response.send_message(f"You must bet at least 1 {self.omnicoin}")
            elif bet > wallet:
                await interaction.response.send_message(embed=self.create_embed(interaction, title="You can't afford that.",
                                                                                colour= Colour.brand_red(), wallet=wallet))
            else:
                outcome = flip_coin()
                if outcome is not guess.value:
                    wallet-=bet
                    description = f"You lost {bet} {self.omnicoin}"
                    await interaction.response.send_message(embed=self.create_embed(interaction, title=outcome.capitalize(),
                                                                                    description=description, colour=Colour.brand_red(), 
                                                                                    wallet=wallet, guess=guess))
                else:
                    wallet+=bet
                    description = f"You won {bet*2} {self.omnicoin}"
                    await interaction.response.send_message(embed=self.create_embed(interaction, title=outcome.capitalize(),
                                                                                    description=description, colour=Colour.brand_green(), 
                                                                                    wallet=wallet, guess=guess))      
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
