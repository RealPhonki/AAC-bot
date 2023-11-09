# external imports
from discord.ext import commands, tasks
from discord import Intents, Embed, Game, __version__
from asyncio import run

# builtin imports
from platform import python_version, system, release
from itertools import cycle
import json
import os

# local imports
from bot_logger import logger

# load config
with open("config.json") as file:
    config = json.load(file)

# create bot
client = commands.Bot(command_prefix=commands.when_mentioned_or(config["prefix"]), intents=Intents.all())
client.logger = logger()

@tasks.loop(seconds=60)
async def change_status() -> None:
    bot_status = cycle(["Bullet", "Rapid", "Classic", "Atomic", "Duck", "Fog of war"])
    await client.change_presence(activity=Game(next(bot_status)))

@client.command(name="sync") 
async def sync(ctx: commands.Context):
    synced = await client.tree.sync()

    # create embed instance
    embed_message = Embed(title = f"Synced {len(synced)} command(s)")
    embed_message.set_author( # set author of embed to the user who requested the command
        name = f'Requested by {ctx.author.name}',
        icon_url = ctx.author.avatar
    )

    await ctx.send(embed=embed_message)

@client.event
async def on_ready() -> None:
    # initialize
    change_status.start()

    # debug
    client.logger.info(f"Logged in as {client.user.name}")
    client.logger.info(f"discord.py API version: {__version__}")
    client.logger.info(f"Python version: {python_version()}")
    client.logger.info(f"Running on: {system()} {release()} ({os.name})")
    client.logger.info("-------------------")

async def load() -> None:
    # for every python file in the cogs folder
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            extension = filename[:-3]
            try:
                # load the python extension and print a cool message
                await client.load_extension(f"cogs.{extension}")
                client.logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                # print the exception if there is one
                exception = f"{type(e).__name__}: {e}"
                client.logger.error(f"Failed to load extension {extension}\n{exception}")

async def main() -> None:
    async with client:
        await load()
        await client.start(config["token"])

run(main())
