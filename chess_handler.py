# external imports
from PIL import Image, ImageDraw
import chess

# builtin imports
from collections import deque
from functools import cached_property
from datetime import datetime
from io import BytesIO

class ChessHandler:
    def __init__(self) -> None:
        """
        Creates a chess handler object.
        """
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
        self.board = chess.Board()
        self.game_number = 1
        self.legal_moves = []
        self.votes = {}
        self.playing = False

    """ ------ Properties ----- """
    @property
    def vote_pool(self) -> dict:
        """
        Returns a dictionary mapping the vote pool.
        {"Nf3": 4, "e4": 7, ... }
        """
        return {move: sum(1 for vote in self.votes.values() if vote == move) for move in self.legal_moves}
    
    @ property
    def turn(self) -> bool:
        """ Returns True if it is white to play and False if it is black to play. """
        return self.board.turn
    
    @cached_property
    def empty_board_image(self) -> Image:
        """
        Returns the raw .png data of the board without pieces
        """
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

    """ ----- Private methods ----- """
    def reset_legal_moves(self) -> None:
        """ Resets the legal moves"""
        self.legal_moves = [self.board.san(move) for move in self.board.legal_moves]

    def reset_voting(self) -> None:
        """ Resets the saved votes and the users who voted """
        self.votes = {}

    """ ----- Public methods ------ """
    def generate_board_image(self) -> Image:
        """ Returns the raw png data of the current board state. """
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
    
    def get_pgn(self) -> str:
        """ Returns the pgn of the board """
        # create chess game instance
        game = chess.pgn.Game()

        # set metadata attributes
        game.headers["Event"] = "Alliance Academy Experimental Chess Event"
        game.headers["Site"] = "https://discord.com"
        game.headers["Date"] = datetime.now().strftime("%Y-%m-%d")
        game.headers["Round"] = str(self.game_number)
        game.headers["White"] = "White team"
        game.headers["Black"] = "Black team"

        # undo all moves
        switchyard = deque()
        while self.board.move_stack:
            switchyard.append(self.board.pop())

        # setup the board
        game.setup(self.board)
        node = game

        # replay all moves
        while switchyard:
            move = switchyard.pop()
            node = node.add_variation(move)
            self.board.push(move)
        
        # set the game result
        if self.board.result() == "*":
            game.headers["Result"] = "GAME CANCELED"
        else:
            game.headers["Result"] = self.board.result()

        # return the pgn
        return game.accept(chess.pgn.StringExporter())

    def start_game(self, game_number, fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") -> None:
        """ Starts a game of chess. """
        self.game_number = game_number
        self.board = chess.Board(fen)
        self.reset_legal_moves()
        self.reset_voting()
        self.playing = True
    
    def end_game(self) -> None:
        """ Ends the game and returns the pgn of the board. """
        self.playing = False
        return self.get_pgn()
    
    def try_add_vote(self, user_id: int, move: str) -> bool:
        """
        Adds a vote to the voting pool if the move is legal.
        """
        if move not in self.legal_moves:
            return False
        
        self.votes[user_id] = move
        return True

    def play_popular_move(self) -> None:
        """
        Plays the move with the most amount of votes.
        """
        self.board.push_san(max(self.vote_pool, key=self.vote_pool.get))
        self.reset_voting()
        self.reset_legal_moves()
    
    def check_vote_tie(self) -> bool:
        """
        Checks if there is a tie in the voting pool.
        """
        most_votes = max(self.vote_sum.values())
        return sum(1 for votes in self.vote_sum.values() if votes == most_votes) != 1