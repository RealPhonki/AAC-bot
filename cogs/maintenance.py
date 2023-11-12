# external imports
import discord
from discord import app_commands
from discord.ext import commands

# builtin imports
import os

class Maintenance(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = bot.logger
        self.cursor = os.getcwd()
    
    @app_commands.command(name = "ls", description = "(Admins only) \nLists all of the files in the cursor directory.")
    async def list_directory(self, interaction: discord.Interaction):
        try:
            # check if the user has admin
            is_admin = await self.bot.check_admin(interaction)
            if not is_admin:
                return
            
            # create embed object
            embed_message = discord.Embed(title = "/ls", color = discord.Color.gold())
            embed_message.set_author(name = f"Requested by {interaction.user.name}", icon_url = interaction.user.avatar)
            
            embed_message.add_field(name = self.cursor, value = "")

            # get string containing all directories
            directories_str = "```\n"
            for f in os.listdir(self.cursor):
                directories_str += f + "\n"
            directories_str += "```"
            embed_message.add_field(name = "", value = directories_str, inline = False)

            await interaction.response.send_message(embed = embed_message, ephemeral = True)

        except Exception as error:
            self.logger.error(f"{type(error)}: {error}")

# when the bot.load_extension method is called, this function will be called
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Maintenance(bot))