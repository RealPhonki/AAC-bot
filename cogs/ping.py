# external imports
import discord
from discord import app_commands
from discord.ext import commands

# builtin imports
from traceback import print_exc

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is alive!")
    async def ping(self, interaction: discord.Interaction) -> None:
        """
        Checks the latency of the bot.
        """
        try:
            bot_latency = round(self.bot.latency * 1000)

            # create embed instance
            embed_message = discord.Embed(title = f"pong : {bot_latency} ms")
            embed_message.set_author(
                name = f'Requested by {interaction.user.name}',
                icon_url = interaction.user.avatar
            )

            await interaction.response.send_message(embed = embed_message)
            
        except Exception:
            print_exc()

# add the extension to the bot
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))