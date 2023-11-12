# external imports
import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(name="help", description = "Shows all of the available bot commands.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        try:
            # debug
            self.bot.logger.info(f"{interaction.user.name} used command '/help'")

            is_admin = await self.bot.check_admin(interaction, warning = False)

            embed_message = discord.Embed(title = "Bot commands", color = discord.Color.green())

            # loop through all bot cogs and their commands
            for cog in self.bot.cogs.values():
                for command in cog.get_commands() + cog.get_app_commands():
                    # only display admin commands to admins
                    if "(Admins only)" in command.description and not is_admin:
                        continue

                    # add field containing parsed command and arguments
                    arguments = " ".join([f"<{param.name}>" for param in command.parameters])
                    command_name = f"/{command.name} {arguments}"
                    embed_message.add_field(name = command_name, value = command.description, inline=False)

            # send the embed
            await interaction.response.send_message(embed = embed_message, ephemeral = True)

        except Exception as error:
            self.logger.error(f"Internal command failure:\n{type(error).__name__}: {error}")
    
# when the bot.load_extension method is called, this function will be called
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))