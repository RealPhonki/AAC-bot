# external imports
import discord
from discord.ext import commands, tasks
from asyncio import run

# builtin imports
from platform import python_version, system, release
from os import name as os_name, listdir
from json import load as json_load
from itertools import cycle

# local imports
from bot_logger import logger

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        """
        Creates some custom attributes before calling the super initializer.
        """
        
        # constants
        self.CONFIG = self.load_config()

        # attributes
        self.logger = logger()

        # initialization
        super().__init__(self.CONFIG["prefix"], intents=discord.Intents.all())
        self.add_builtin_commands()

    async def check_perms(self, interaction: discord.Interaction, warning = True) -> bool:
        """
        Check if a user in an interaction is an admin.
        """
        if self.CONFIG["admin_role"] in [role.id for role in interaction.user.roles]:
            return True
        
        elif warning:
            await interaction.response.send_message("You need to be an admin to run this command!", ephemeral=True)
        return False

    def load_config(self) -> dict:
        """
        Loads config.json as a json file and returns the contents as a dictionary.
        """
        try:
            with open("config.json") as file:
                return json_load(file)
            
        except Exception as error:
            raise FileNotFoundError(f"{type(error).__name__}: {error}")

    async def on_ready(self) -> None:
        """
        Debug information to confirm that the bot has connected.
        """
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {python_version()}")
        self.logger.info(f"Running on: {system()} {release()} ({os_name})")
        self.logger.info("-------------------")

        self.change_status.start()

    async def load_cogs(self) -> None:
        """
        Loops through every python file in the cogs folder and loads it as a cog extension.
        """
        for filename in listdir("./cogs"):
            if not filename.endswith(".py"):
                continue

            extension = filename[:-3] # remove the '.py' from the name
            try:
                await self.load_extension(f"cogs.{extension}")
                self.logger.info(f"Loaded extension '{extension}'")

            except Exception as error:
                self.logger.error(f"Failed to load extension {extension}\n{type(error).__name__}: {error}")

    @tasks.loop(seconds=60)
    async def change_status(self) -> None:
        """
        Changes the bot status every 60 seconds.
        """
        bot_status = cycle(self.CONFIG["statuses"])
        await self.change_presence(activity=discord.Game(next(bot_status)))

    def add_builtin_commands(self) -> None:
        """
        Adds commands and events that are required for bot development.
        """
        try:
            @self.command(name="sync") 
            async def sync(ctx: commands.Context):
                try:
                    synced = await self.tree.sync()

                    # create embed instance
                    embed_message = discord.Embed(title = f"Synced {len(synced)} command(s)", color=discord.Color.gold())
                    embed_message.set_author( # set author of embed to the user who requested the command
                        name = f'Requested by {ctx.author.name}',
                        icon_url = ctx.author.avatar
                    )

                    await ctx.send(embed=embed_message)

                except Exception as e:
                    await ctx.send(f"{type(e).__name__}: {e}")
            
            self.logger.info(f"Loaded command 'sync'")

        except Exception as error:
            self.logger.error(f"Failed to load command 'sync'\n{type(error).__name__}: {error}")

    async def main(self) -> None:
        """
        Loads the bot and logs into the discord server.
        """
        await self.load_cogs()
        await self.start(self.CONFIG["token"])

if __name__ == '__main__':
    discord_bot = DiscordBot()
    run(discord_bot.main())
