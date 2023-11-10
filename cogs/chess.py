# external imports
from chess import Board, SQUARES, square_file, square_rank
from discord import app_commands, Embed, Color, Interaction, File as discord_file, utils
from discord.ext import commands
from PIL import Image, ImageDraw

# builtin imports
from functools import cached_property
from traceback import print_exc
from io import BytesIO
import random

class Game:
    def __init__(self) -> None:
        # constants
        self.SQUARE_SIZE = 100
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
        self.playing = False
    
    """ ----- Properties ------ """
    @property
    def turn(self) -> str:
        return "White to play" if self.board.turn else "Black to play"

    @cached_property
    def empty_board_image(self) -> Image:
        """ Returns the raw .png data of the board without pieces """
        # create a blank image
        image = Image.new("RGBA", (self.BOARD_SIZE, self.BOARD_SIZE), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # loop 64 times
        for row in range(8):
            for col in range(8):
                # get the coordinates and color of each square
                x1, y1 = col * self.SQUARE_SIZE, row * self.SQUARE_SIZE
                x2, y2 = x1 + self.SQUARE_SIZE, y1 + self.SQUARE_SIZE
                color = self.TILE_LIGHT if (row + col) % 2 == 0 else self.TILE_DARK
                
                # draw a square at the specified coordinates
                draw.rectangle([x1, y1, x2, y2], fill = tuple(color))
        
        return image

    @property
    def board_image(self) -> Image:
        """ Returns the raw png data of the current board state"""
        # get the empty board image
        image = self.empty_board_image
        
        # loop through every square
        for square in SQUARES:
            # get the piece from the chessboard, skip if there is no piece at that square
            piece = self.board.piece_at(square)
            if piece is None:
                continue

            # get the coordinates of the piece
            x = square_file(square) * self.SQUARE_SIZE
            y = (7 - square_rank(square)) * self.SQUARE_SIZE

            # access the image and resize it
            piece_image = self.PIECE_IMAGES[piece.symbol()]
            piece_image = piece_image.resize((self.SQUARE_SIZE, self.SQUARE_SIZE))

            # draw the piece at the given coordinates onto the empty board
            image.paste(piece_image, (x, y), piece_image)

        # create a BytesIO stream
        image_stream = BytesIO()
        image.save(image_stream, format="PNG")
        image_stream.seek(0) # move the stream cursor to the beginning

        # return the image stream
        return image_stream

    """ ----- General Methods ----- """
    def start_game(self) -> None:
        self.playing = True
        self.reset_board()
        self.reset_votes()

    def end_game(self) -> None:
        self.playing = False

    def reset_votes(self) -> dict:
        self.votes = {self.board.san(move) for move in self.board.legal_moves}

    def reset_board(self) -> None:
        self.board = Board()
    
    def add_vote(self, move) -> bool:
        """
        Adds a vote to the vote list and returns true if the vote was added successfully.
        Otherwise returns False.
        """

        # check if the move is in san format
        try:
            parsed_move = self.board.uci(move)
            self.votes[parsed_move] += 1
        except:
            # check if the move is in uci format (standard format)
            try:
                parsed_move = self.board.san(move)
                self.votes[move] += 1
            except:
                return False
        return True

    def play_popular_move(self) -> None:
        pass

class Chess(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        # aliases
        self.bot = bot

        # constants
        self.TEAMS = ["white", "black"]
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
        self.game = Game()

    @app_commands.command(name="start_game")
    async def start_game(self, interaction: Interaction) -> None:
        try:
            # check user permissions
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            # check if there is already a game in session
            if self.game.playing:
                await interaction.response.send_message("The game is already in session!", ephemeral=True)
                return
            
            # start the game
            await interaction.response.send_message("Starting game...")
            self.game.start_game()

            # loop through every member and give them a role
            self.bot.logger.info("Building teams...")
            guild = interaction.guild
            for member in guild.members:
                team = random.choice(self.TEAMS)
                existing_role = utils.get(guild.roles, name=team)
                if not existing_role:
                    existing_role = await guild.create_role(name=team)

                await member.add_roles(existing_role)

                self.bot.logger.info(f"Added role '{team}' to {member.name}")

            # create discord embed
            self.bot.logger.info(f"Building embed")
            embed = Embed(
                title = self.game.turn,
                color = Color.gold()
            )
            embed.set_image(url='attachment://board_image.png')
            embed.set_author(name = f'Requested by {interaction.user.name}', icon_url = interaction.user.avatar)

            self.bot.logger.info(f"Generating board state")
            board_image = discord_file(self.game.board_image, filename="board_image.png")

            await interaction.followup.send(embed=embed, file=board_image)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()
    
    @app_commands.command(name="end_game")
    async def end_game(self, interaction: Interaction) -> None:
        try:
            # check user permissions
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return
            
            # end the game
            await interaction.response.send_message(f"Ending game...")
            self.game.end_game()

            # remove roles from each user
            self.bot.logger.info(f"Removing roles")
            guild = interaction.guild
            for member in guild.members:
                for team in self.TEAMS:
                    role = utils.get(guild.roles, name=team)
                    await member.remove_roles(role)

                    self.bot.logger.info(f"Removing role '{team}' from {member.name}'")

            await interaction.followup.send(f"Game ended.")

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()

    @app_commands.command(name="vote")
    async def vote(self, interaction: Interaction) -> None:
        try:
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return
            
            await interaction.response.send_message("This command hasn't been implemented yet, maybe try again later? :/", ephemeral=True)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()

# add the extension to the bot
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chess(bot))