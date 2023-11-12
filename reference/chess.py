# external imports
from discord import app_commands, Embed, Color, Interaction, File as discord_file, utils, User
from discord.ext import commands
from PIL import Image, ImageDraw
import reference.chess as chess
import chess.pgn

# builtin imports
from functools import cached_property
from traceback import print_exc
from datetime import datetime
from typing import Tuple
from io import BytesIO
import collections
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
        for square in chess.SQUARES:
            # get the piece from the chessboard, skip if there is no piece at that square
            piece = self.board.piece_at(square)
            if piece is None:
                continue

            # get the coordinates of the piece
            x = chess.square_file(square) * self.SQUARE_SIZE
            y = (7 - chess.square_rank(square)) * self.SQUARE_SIZE

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
    def get_pgn(self) -> str:
        # create chess game instance
        game = chess.pgn.Game()

        # set metadata attributes
        game.headers["Event"] = "Alliance Academy Experimental Chess Event"
        game.headers["Site"] = "https://discord.com"
        game.headers["Date"] = datetime.now().strftime("%Y-%m-%d")
        game.headers["Round"] = "1"
        game.headers["White"] = "White team"
        game.headers["Black"] = "Black team"

        # undo all moves
        switchyard = collections.deque()
        while self.board.move_stack:
            switchyard.append(self.board.pop())

        game.setup(self.board)
        node = game

        # replay all moves
        while switchyard:
            move = switchyard.pop()
            node = node.add_variation(move)
            self.board.push(move)
        
        if self.board.result() == "*":
            game.headers["Result"] = "GAME CANCELED"
        else:
            game.headers["Result"] = self.board.result()

        return game.accept(chess.pgn.StringExporter())

    def get_legal_moves(self) -> None:
        self.legal_moves = [self.board.san(move) for move in self.board.legal_moves]

    def start_game(self, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") -> None:
        self.board = chess.Board(fen)
        self.playing = True
        self.votes = {}
        self.get_legal_moves()

    def end_game(self) -> None:
        self.playing = False
        return self.get_pgn()
    
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
        # do not play moves if there are multiple moves with high vote counts
        most_votes = max(self.vote_sum.values())
        popular_moves = [move for move, votes in self.vote_sum.items() if votes == most_votes]
        if len(popular_moves) > 1:
            return False

        # play move and return True
        self.board.push_san(max(self.vote_sum, key=self.vote_sum.get))
        self.votes = {}
        self.get_legal_moves()
        return True

class Chess(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        # aliases
        self.bot = bot

        # constants
        self.CHANNEL = 1172622450702434348
        self.TEAMS = ["white", "black"]
        self.SQUARE_SIZE = 100 # square size in pixels
        self.BOARD_SIZE = self.SQUARE_SIZE * 8

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
    @app_commands.describe(mix_teams="Grant roles to all users")
    @app_commands.choices(mix_teams=[
        app_commands.Choice(name="True", value=True),
        app_commands.Choice(name="False", value=False)
    ])
    async def start_game(
        self,
        interaction: Interaction,
        mix_teams: app_commands.Choice[int],
        vote_minimum: str,
        fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    ) -> None:
        try:
            # check user permissions
            user_has_perms = await self.bot.check_perms(interaction)
            if not user_has_perms:
                return
            
            # check if this command has been run in the correct channel
            if interaction.channel_id != self.CHANNEL:
                await interaction.response.send_message(f"Games can only be started in the https://discord.com/channels/1135023767798698117/{self.CHANNEL}", ephemeral=True)
                return

            # check if there is already a game in session
            if self.game.playing:
                await interaction.response.send_message("The game is already in session!", ephemeral=True)
                return
            
            # check if the vote_minimum parameter is a number before saving it
            if not vote_minimum.isnumeric():
                await interaction.response.send_message("vote_minimum needs to be a number!", ephemeral=True)
                return
            self.vote_minimum = int(vote_minimum)

            # start the game
            await interaction.response.send_message("Starting game...")
            self.game.start_game(fen)

            # if the 'mix_teams' parameter is set to True
            if mix_teams.value:
                for member in interaction.guild.members:
                    # remove them from their old team
                    for team in self.TEAMS:
                        await member.remove_roles(utils.get(interaction.guild.roles, name=team))
                    self.bot.logger.info(f"Removed roles {self.TEAMS} from {member.name}")

                    # grant them a new team
                    new_team = utils.get(interaction.guild.roles, name=random.choice(self.TEAMS))
                    await member.add_roles(new_team)
                    self.bot.logger.info(f"Granted role '{team}' to {member.name}")

            # create discord embed
            embed, board_image = self.get_board_embed()

            await interaction.followup.send(embed=embed, file=board_image)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()
    
    @app_commands.command(name="end_game")
    async def end_game(self, interaction: Interaction) -> None:
        try:
            # check if this command has been run in the correct channel
            if interaction.channel_id != self.CHANNEL:
                await interaction.response.send_message(f"Game related commands can only be done in https://discord.com/channels/1135023767798698117/{self.CHANNEL}", ephemeral=True)
                return

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

            result = self.game.end_game()

            embed = Embed(
                title = "GAME OVER",
                color = Color.gold()
            )
            embed.add_field(name="Game result:", value=result)

            await interaction.followup.send(embed=embed)

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

            if self.game.board.turn == chess.WHITE:
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
            if len(self.game.votes) >= self.vote_minimum:
                if self.game.play_popular_move():
                    embed, board_image = self.get_board_embed()
                    await interaction.followup.send(embed=embed, file=board_image)

                    if self.game.board.is_checkmate():
                        result = self.game.end_game()

                        embed = Embed(
                            title = "GAME OVER",
                            color = Color.gold()
                        )
                        embed.add_field(name="Game result:", value=result)

                        await interaction.followup.send(embed=embed)
                else:
                    embed = Embed(
                        title = f"There is a tie in votes!",
                        color = Color.gold()
                    )
                    most_votes = max(self.game.vote_sum.values())
                    for move, votes in self.game.vote_sum.items():
                        if votes != most_votes:
                            continue
                        embed.add_field(name=move, value=votes, inline=True)

                    await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.channel.send(f"Internal command failure {type(e).__name__}: {e}")
            print_exc()
    
    @app_commands.command(name="show_votes")
    async def show_votes(self, interaction: Interaction) -> None:
        try:
            # check if this command has been run in the correct channel
            if interaction.channel_id != self.CHANNEL:
                await interaction.response.send_message(f"Game related commands can only be done in https://discord.com/channels/1135023767798698117/{self.CHANNEL}", ephemeral=True)
                return
            
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