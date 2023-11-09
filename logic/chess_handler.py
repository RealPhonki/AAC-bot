from PIL import Image, ImageDraw
from functools import cached_property
import chess
import json

class ChessHandler():
    piece_images = {
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
    
    """ ----- Constructors -----"""
    def __init__(self) -> None:
        """ This class does not have parameters """
        self.config = self.get_config()
        self.board = chess.Board()
        self.square_size = self.config["square_size"]
        self.board_size = self.square_size * 8
        self.board_color = self.config["board_themes"]["theme_1"]

    def get_config(self) -> dict:
        """ Load json data and return it"""
        with open("logic/chess_config.json") as file:
            return json.load(file)

    """ ----- Properties ----- """
    @cached_property
    def checker_board(self) -> Image:
        """ Returns the raw .png data of the board without pieces """
        image = Image.new("RGBA", (self.board_size, self.board_size), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        for row in range(8):
            for col in range(8):
                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                color = self.board_color[0] if (row + col) % 2 == 0 else self.board_color[1]
                draw.rectangle([x1, y1, x2, y2], fill = tuple(color))
        
        return image

    @property
    def turn(self) -> str:
        return "White to play" if self.board.turn else "Black to play"

    """ ----- General Methods ----- """
    def get_board_png(self) -> Image:
        """ Returns the raw png data of the current board state"""
        # Returns the raw .png data of the board
        image = self.checker_board
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)

            if piece is None:
                continue

            x = chess.square_file(square) * self.square_size
            y = (7 - chess.square_rank(square)) * self.square_size

            position = (x, y)
            piece_image = self.piece_images[piece.symbol()]
            piece_image = piece_image.resize((self.square_size, self.square_size))
            image.paste(piece_image, position, piece_image)
        
        return image
    
    