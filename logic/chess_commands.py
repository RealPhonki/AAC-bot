# external imports
from discord import File, Embed, app_commands, Color, Interaction
from discord.ext import commands

# builtin imports
from io import BytesIO

# local imports
from logic.chess_handler import ChessHandler

class ChessCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.chess_handler = ChessHandler()
    
    def board_image(self) -> File:
        """ Returns an image of the board """
        # gets raw png data from the chess_handler class
        image = self.chess_handler.get_board_png()

        # save the image to BytesIO stream
        image_stream = BytesIO()
        image.save(image_stream, format = "PNG")
        image_stream.seek(0) # move the stream cursor to the beginning

        # generate discord file instance for formatting
        return File(image_stream, filename="board_img.png")
    
    @app_commands.command(name="display_board", description="Display a chess board.")
    async def display_board(self, interaction: Interaction) -> None:
        try:
            board_image = self.board_image()

            # create embed
            embed = Embed(
                title = self.chess_handler.turn,
                color = Color.gold()
            )
            embed.set_image(url='attachment://board_img.png')
            embed.set_author(name = f'Requested by {interaction.user.name}', icon_url = interaction.user.avatar)

            await interaction.response.send_message(embed=embed, file=board_image)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")

# add cog extension to "client" (the bot)
# NOTE: THIS CODE RUNS FROM THE DIRECTORY THAT "main.py" IS IN
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChessCommands(bot))