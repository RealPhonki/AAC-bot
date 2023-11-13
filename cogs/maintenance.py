# external imports
import discord
from discord import app_commands
from discord.ext import commands

# builtin imports
from traceback import print_exc
import os

# local imports
from helper import format_text_left

class Maintenance(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = bot.logger
        self.directory = os.getcwd()
    
    @app_commands.command(name = "ls", description = "(Admins only) \nLists all of the files in the current directory.")
    async def list_directory(self, interaction: discord.Interaction):
        try:
            # debug
            self.logger.info(f"{interaction.user.name} used command '/ls'")

            # check if the user has admin
            is_admin = await self.bot.check_admin(interaction)
            if not is_admin:
                return
            
            # create embed object
            embed_message = discord.Embed(title = "/ls", color = discord.Color.red())
            embed_message.set_author(name = f"Requested by {interaction.user.name}", icon_url = interaction.user.avatar)

            # get string containing all directories
            directories_str = "```\n"
            for f in os.listdir(self.directory):
                directories_str += f + "\n"
            directories_str += "```"
            embed_message.add_field(name = "", value = directories_str, inline = False)

            await interaction.response.send_message(embed = embed_message, ephemeral = True)

        except Exception as error:
            self.logger.error(f"{type(error)}: {error}")

    @app_commands.command(name = "cd", description = "(Admins only) \nChanges the current directory.")
    async def change_directory(self, interaction: discord.Interaction, directory: str):
        try:
            # debug
            self.logger.info(f"{interaction.user.name} used command '/ls {directory}'")

            # check if the user has admin
            is_admin = await self.bot.check_admin(interaction)
            if not is_admin:
                return
            
            # command to move backwards
            if directory == "..":
                self.directory = "/".join(self.directory.split("/")[:-1])
                await self.bot.send_command_embed(interaction, f"/cd ..", "Success", discord.Color.red())
                return

            # check if the path is valid
            if os.path.isdir(os.path.join(self.directory, directory)):
                self.directory = directory if self.directory == "" else os.path.join(self.directory, directory)
                await self.bot.send_command_embed(interaction, f"/cd {directory}", f"Success", discord.Color.red())
        
            else:
                # send a different message depending on what kind of invalid path they inputted
                if os.path.exists(os.path.join(self.directory, directory)):
                    await self.bot.send_command_embed(interaction, f"/cd {directory}", f"cd: not a directory: {directory}", discord.Color.red())
                else:
                    await self.bot.send_command_embed(interaction, f"/cd {directory}", f"cd: no such file or directory: {directory}", discord.Color.red())
            
        except Exception as error:
            self.logger.error(f"{type(error)}: {error}")
    
    @app_commands.command(name = "view_file", description = "(Admins only) \nViews a file in the current directory. (THIS GETS AFFECTED BY CHARACTER LIMIT)")
    async def view_file(self, interaction: discord.Interaction, file_name: str, start: str = None, stop: str = None) -> None:
        try:
            # debug
            self.logger.warn(f"{interaction.user.name} used command '/view_file {file_name} {start} {stop}'")

            # check if the user has admin
            is_admin = await self.bot.check_admin(interaction)
            if not is_admin:
                return
            
            # check if the user is not me..
            if interaction.user.id != self.bot.CONFIG["owner"]:
                ping_owner = "<@" + str(self.bot.CONFIG["owner"]) + ">"
                await self.bot.send_command_embed(interaction, f"/view_file {file_name} {start} {stop}", f"Nah why tf u trying to look through my files u monkey", discord.Color.red())
                await interaction.followup.send(f"{ping_owner} {interaction.user.name} tried to look at your files..")
                return
            
            file_path = os.path.join(self.directory, file_name)

            # check if the file is valid
            if not os.path.exists(file_path):
                await self.bot.send_command_embed(interaction, f"/view_file {file_name} {start} {stop}", f"view_file: {file_name}: No such file or directory", discord.Color.red())
                return
            
            elif os.path.isdir(file_path):
                await self.bot.send_command_embed(interaction, f"/view_file {file_name} {start} {stop}", f"view_file: {file_name}: Is a directory", discord.Color.red())
                return

            # open the file
            with open(file_path, "r") as f:
                # open the file
                file_contents = f.readlines()

            # get the file length
            file_length = len(file_contents)

            # check if the range is valid
            try:
                # convert the text into integers
                start = int(start) if start else 0
                stop = int(stop) if stop else file_length

            except:
                await self.bot.send_command_embed(interaction, f"/view_file {file_name} {start} {stop}", f'Invalid range "({start}, {stop})"', discord.Color.red())
                return

            # extract the lines
            file_contents = file_contents[start : stop]

            # select the formatting type
            if file_name.endswith(".py"):
                output = "```python\n"
            elif file_name.endswith(".json"):
                output = "```json\n"
            else:
                output = "```\n"

            for line_number, line_contents in enumerate(file_contents):
                # format the output
                formatted_line_number = start + line_number + 1 if start > 0 else (file_length + start) + (line_number + 1)
                format_width = len(str(stop + 1)) if stop > 0 else len(str(file_length + stop + 1))
                line_header = format_text_left(text = str(formatted_line_number), width = format_width)
                content = line_contents.replace("    ", "  ")

                new_content = f"{line_header} | {content}"

                # truncate if the text is too long
                if len(output + new_content + "```") > 2000:
                    break

                # append the newly formatted content
                output += new_content
            output += "```"

            # send the file
            await interaction.response.send_message(output, ephemeral = True)

        except Exception as error:
            self.logger.error(f"{type(error)}: {error}")
            print_exc()

# when the bot.load_extension method is called, this function will be called
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Maintenance(bot))