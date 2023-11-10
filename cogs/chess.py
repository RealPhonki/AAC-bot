# external imports
from chess import Board, SQUARES, square_file, square_rank, WHITE, BLACK
from discord import app_commands, Embed, Color, Interaction, File as discord_file, utils, User
from discord.ext import commands
from PIL import Image, ImageDraw

# builtin imports
from functools import cached_property
from traceback import print_exc
from typing import Tuple
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
        self.legal_moves = []
        self.playing = False
    
    """ ----- Properties ------ """
    @property
    def vote_sum(self) -> dict:
        vote_sum = dict.fromkeys(self.legal_moves, 0)
        for move in self.votes.values():
            vote_sum[move] += 1
        return vote_sum

    @property
    def legal_moves_str(self) -> str:
        return ", ".join(self.legal_moves)

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

    def generate_board_image(self) -> Image:
        """ Returns the raw png data of the current board state"""
        # get the empty board image
        image = self.empty_board_image.copy()
        
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
    def get_legal_moves(self):
        self.legal_moves = [self.board.san(move) for move in self.board.legal_moves]

    def start_game(self) -> None:
        self.playing = True
        self.reset_board()
        self.reset_votes()
        self.get_legal_moves()

    def end_game(self) -> None:
        self.playing = False

    def reset_votes(self) -> None:
        self.votes = {}

    def reset_board(self) -> None:
        self.board = Board()
    
    def vote(self, user: User, move: str) -> bool:
        """
        Adds a vote to the vote list and returns true if the vote was added successfully.
        Otherwise returns False.
        """

        if move not in self.legal_moves:
            return False

        self.votes[user] = move
        return True

    def play_popular_move(self) -> None:
        self.board.push_san(max(self.vote_sum, key=self.vote_sum.get))
        self.reset_votes()
        self.get_legal_moves()

class Chess(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        # aliases
        self.bot = bot

        # constants
        self.CHANNEL = 1172622450702434348
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
        self.vote_minimum = 0

    def get_board_embed(self) -> Tuple[Embed, discord_file]:
        embed = Embed(
            title = self.game.turn,
            color = Color.gold()
        )

        embed.add_field(name = f"{self.vote_minimum} vote(s) required to play move", value="")
        embed.add_field(name = "Legal moves:", value=self.game.legal_moves_str, inline=False)
        embed.set_image(url='attachment://board_image.png')

        board_image = discord_file(self.game.generate_board_image(), filename="board_image.png")

        return embed, board_image

    @app_commands.command(name="start_game")
    @app_commands.describe(grant_roles="Grant roles to all users")
    @app_commands.choices(grant_roles=[
        app_commands.Choice(name="True", value=True),
        app_commands.Choice(name="False", value=False)
    ])
    async def start_game(self, interaction: Interaction, grant_roles: app_commands.Choice[int], vote_minimum: str) -> None:
        try:
            # check user permissions
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            # check if this command has been run in the correct server
            if interaction.channel_id != self.CHANNEL:
                await interaction.response.send_message(f"Games can only be started in the https://discord.com/channels/1135023767798698117/{self.CHANNEL}", ephemeral=True)
                return

            # check if there is already a game in session
            if self.game.playing:
                await interaction.response.send_message("The game is already in session!", ephemeral=True)
                return
            
            if not vote_minimum.isnumeric():
                await interaction.response.send_message("vote_minimum needs to be a number!", ephemeral=True)
                return
            self.vote_minimum = int(vote_minimum)

            # start the game
            await interaction.response.send_message("Starting game...")
            self.game.start_game()

            # loop through every member and give them a role
            if grant_roles.value:
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
            embed, board_image = self.get_board_embed()

            await interaction.followup.send(embed=embed, file=board_image)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()
    
    @app_commands.command(name="end_game")
    @app_commands.describe(clear_roles="Clear roles from all users")
    @app_commands.choices(clear_roles=[
        app_commands.Choice(name="True", value=True),
        app_commands.Choice(name="False", value=False)
    ])
    async def end_game(self, interaction: Interaction, clear_roles: app_commands.Choice[int]) -> None:
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
            if clear_roles.value:
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
    async def vote(self, interaction: Interaction, move: str) -> None:
        try:
            # check if this command has been run in the correct server
            if interaction.channel_id != self.CHANNEL:
                await interaction.response.send_message(f"Votes can only be made in https://discord.com/channels/1135023767798698117/{self.CHANNEL}", ephemeral=True)
                return
            
            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return

            # check if they have perms

            if self.game.board.turn == WHITE:
                if "white" not in [role.name for role in interaction.user.roles]:
                    await interaction.response.send_message(f"Its not your turn to play!", ephemeral=True)
                    return
            else:
                if "black" not in [role.name for role in interaction.user.roles]:
                    await interaction.response.send_message(f"Its not your turn to play!", ephemeral=True)
                    return
                

            # check if the vote was successful
            if not self.game.vote(interaction.user.id, move):
                await interaction.response.send_message(f"\"{move}\" is not a legal move!", ephemeral=True)
                return
            
            await interaction.response.send_message(f"You voted for \"{move}\"!", ephemeral=True)

            # if vote minimum has been reached then play the move
            if len(self.game.votes) == self.vote_minimum:
                self.game.play_popular_move()
                embed, board_image = self.get_board_embed()

                await interaction.followup.send(embed=embed, file=board_image)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()
    
    @app_commands.command(name="show_votes")
    async def show_votes(self, interaction: Interaction) -> None:
        try:
            # check if there is a game in session
            if not self.game.playing:
                await interaction.response.send_message("There is no game in session!", ephemeral=True)
                return
            
            votes = ", ".join([f"{move}: {votes}" for move, votes in self.game.vote_sum.items() if votes != 0])
            if votes:
                await interaction.response.send_message(votes, ephemeral=True)
            else:
                await interaction.response.send_message("Nobody has voted yet!", ephemeral=True)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()

# add the extension to the bot
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chess(bot))