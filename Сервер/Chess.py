import chess

LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8']


class Board(chess.Board):
    def __init__(self):
        super().__init__()

    def pos_to_lett(self, y, x):
        return LETTERS[x] + NUMBERS[y]

    def move_piece(self, x1, y1, x2, y2):
        letter_move1 = self.pos_to_lett(x1, y1)
        letter_move2 = self.pos_to_lett(x2, y2)
        move_str = letter_move1 + letter_move2

        move = chess.Move.from_uci(move_str)
        if move in self.legal_moves:
            self.push(move)
            return True, move_str
        move = chess.Move.from_uci(move_str + 'q')
        if move in self.legal_moves:
            self.push(move)
            return True, move_str
        return False, ''

    def cell(self, i, j):
        square = chess.square(j, i)
        piece = self.piece_at(square)
        if piece is None:
            return '  '
        piece = piece.symbol()
        if piece == piece.upper():
            piece = 'w' + piece
        else:
            piece = 'b' + piece.upper()
        return piece
