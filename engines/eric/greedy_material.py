"""greedy-material — looks exactly one move ahead and grabs the best thing.

For every legal move it makes the move, scores the resulting position, then
un-makes it, and plays whichever move scored best (ties broken randomly).

Because it tries each move, that's a one-ply search -> League L1.

The score is material (how much wood each side has) plus a small bonus for
putting pieces near the center. Positive numbers favor White; the engine flips
the sign when it's playing Black.
"""

import random

import chess

from grokchess.engine_base import Engine

# Centipawns: a pawn is worth 100. Kings are priceless, so leave them at 0 for
# counting purposes (you can't win one by capture anyway).
PIECE_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# A tiny "piece-square table": a small nudge toward the center of the board,
# indexed by square (a1 = 0 ... h8 = 63). Center squares score higher.
CENTER = [0] * 64
for _sq in range(64):
    _file, _rank = chess.square_file(_sq), chess.square_rank(_sq)
    _dist = abs(_file - 3.5) + abs(_rank - 3.5)   # 1.0 (center) .. 7.0 (corner)
    CENTER[_sq] = int((6 - _dist) * 2)


def evaluate(board: chess.Board) -> int:
    """Score the position from White's point of view (positive = good for White)."""
    if board.is_checkmate():
        # Side to move is checkmated -> terrible for them.
        return -1_000_000 if board.turn == chess.WHITE else 1_000_000
    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUE[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value + CENTER[square]
        else:
            score -= value + CENTER[chess.square_mirror(square)]
    return score


class GreedyMaterial(Engine):
    name = "greedy-material"
    author = "eric"
    league = "L1"

    def choose_move(self, board: chess.Board) -> chess.Move:
        white_to_move = board.turn == chess.WHITE
        best_key = None
        best_moves: list[chess.Move] = []
        for move in board.legal_moves:
            board.push(move)
            score = evaluate(board)
            board.pop()
            # From the mover's perspective, higher is better.
            key = score if white_to_move else -score
            if best_key is None or key > best_key:
                best_key = key
                best_moves = [move]
            elif key == best_key:
                best_moves.append(move)
        return random.choice(best_moves)
