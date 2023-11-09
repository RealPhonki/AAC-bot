# external imports
from discord import Embed, app_commands, Interaction
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check if the bot is alive!")
    async def ping(self, interaction: Interaction) -> None:
        try:
            # get bot latency from discord api
            bot_latency = round(self.bot.latency * 1000)

            # create embed instance
            embed_message = Embed(title = f"pong : {bot_latency} ms")
            embed_message.set_author( # set author of embed to the user who requested the command
                name = f'Requested by {interaction.user.name}',
                icon_url = interaction.user.avatar
            )

            await interaction.response.send_message(embed = embed_message)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")

# add cog extension to "client" (the bot)
# NOTE: THIS CODE RUNS FROM THE DIRECTORY THAT "main.py" IS IN
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))