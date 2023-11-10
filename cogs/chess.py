# external imports
from discord import app_commands, Interaction
from discord.ext import commands
from PIL import Image
from chess import Board

class Chess(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        # aliases
        self.bot = bot

        # constants
        self.SQUARE_SIZE = 100 # square size in pixels
        self.BOARD_SIZE = self.SQUARE_SIZE * 8
        self.TILE_LIGHT = [238,238,210]
        self.TILE_DARK = [118,150,86]
        self.PIECE_IMAGES = {
            'r': Image.open("assets/pieces/black_rook.png"),
            'n': Image.open("assets/pieces/black_knight.png"),
            'b': Image.open("assets/pieces/black_bishop.png"),
            'q': Image.open("assets/pieces/black_queen.png"),
            'k': Image.open("assets/pieces/black_king.png"),
            'p': Image.open("assets/pieces/black_pawn.png"),
            'R': Image.open("assets/pieces/white_rook.png"),
            'N': Image.open("assets/pieces/white_knight.png"),
            'B': Image.open("assets/pieces/white_bishop.png"),
            'Q': Image.open("assets/pieces/white_queen.png"),
            'K': Image.open("assets/pieces/white_king.png"),
            'P': Image.open("assets/pieces/white_pawn.png"),
        }

        # attributes
        self.board = Board()

    @app_commands.command(name="start_game")
    async def start_game(self, interaction: Interaction) -> None:
        try:
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            await interaction.response.send_message("Command not implemented")
            
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
    
    @app_commands.command(name="end_game")
    async def end_game(self, interaction: Interaction) -> None:
        try:
            print(5 / 0)
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            await interaction.response.send_message("Command not implemented")

        except Exception as e:
            print(f"{type(e).__name__}: {e}")

    @app_commands.command(name="vote")
    async def vote(self, interaction: Interaction) -> None:
        try:
            await interaction.response.send_message("Command not implemented", ephemeral=True)

        except Exception as e:
            print(f"{type(e).__name__}: {e}")

# add the extension to the bot
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chess(bot))