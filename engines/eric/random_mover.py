"""random-mover — the baseline everyone should be able to beat.

Picks a uniformly random legal move. No lookahead, so it enters League L0.
Useful as a punching bag and as a sanity check that the arena works.
"""

import random

import chess

from grokchess.engine_base import Engine


class RandomMover(Engine):
    name = "random-mover"
    author = "eric"
    league = "L0"

    def choose_move(self, board: chess.Board) -> chess.Move:
        return random.choice(list(board.legal_moves))
