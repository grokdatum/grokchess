"""minimax-ab — a small alpha-beta search over material + center control.

"Minimax" = assume your opponent always replies with their best move, and plan
against that. "Alpha-beta" is the standard trick to skip branches that can't
change the decision, so you search the same depth much faster.

Depth 2 means: my move, then the opponent's best reply. That's plenty to stop
hanging pieces and to spot simple 1-move tactics, and it stays well under the
1-second budget. Bump ``depth`` up if you want it stronger (League L1 caps at 3).
"""

import random

import chess

from grokchess.engine_base import Engine

PIECE_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

CENTER = [0] * 64
for _sq in range(64):
    _file, _rank = chess.square_file(_sq), chess.square_rank(_sq)
    _dist = abs(_file - 3.5) + abs(_rank - 3.5)
    CENTER[_sq] = int((6 - _dist) * 2)

INF = 10**9


def evaluate(board: chess.Board) -> int:
    """Static score from White's point of view (positive = good for White)."""
    if board.is_checkmate():
        return -INF if board.turn == chess.WHITE else INF
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUE[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value + CENTER[square]
        else:
            score -= value + CENTER[chess.square_mirror(square)]
    return score


def _search(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    if depth == 0 or board.is_game_over():
        return evaluate(board)
    if board.turn == chess.WHITE:  # White maximizes
        value = -INF
        for move in board.legal_moves:
            board.push(move)
            value = max(value, _search(board, depth - 1, alpha, beta))
            board.pop()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:  # Black minimizes
        value = INF
        for move in board.legal_moves:
            board.push(move)
            value = min(value, _search(board, depth - 1, alpha, beta))
            board.pop()
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


class MinimaxAB(Engine):
    name = "minimax-ab"
    author = "eric"
    league = "L1"
    depth = 2

    def choose_move(self, board: chess.Board) -> chess.Move:
        white_to_move = board.turn == chess.WHITE
        best_val = -INF if white_to_move else INF
        best_moves: list[chess.Move] = []
        for move in board.legal_moves:
            board.push(move)
            val = _search(board, self.depth - 1, -INF, INF)
            board.pop()
            better = val > best_val if white_to_move else val < best_val
            if better:
                best_val = val
                best_moves = [move]
            elif val == best_val:
                best_moves.append(move)
        return random.choice(best_moves)
