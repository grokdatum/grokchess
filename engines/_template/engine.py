"""COPY-ME TEMPLATE — this folder is skipped by the tournament.

To enter the arena:

  1. Copy this folder to  engines/<your-name>/
  2. Rename the class and set name / author / league below.
  3. Make choose_move() smarter than "pick something random".
  4. Try it:   python -m grokchess.tournament -v

Rules of the road (see RULES.md):
  * Import only the Python standard library and `chess`.
  * No external engines, cloud APIs, opening books, or tablebases.
  * Return a legal move within the time limit (default 1 second).
"""

import random

import chess

from grokchess.engine_base import Engine


class MyEngine(Engine):
    name = "my-engine"      # short, unique-ish
    author = "your-name"
    league = "L0"           # L0 = no lookahead, L1 = search <= depth 3, L2 = open

    def choose_move(self, board: chess.Board) -> chess.Move:
        # The simplest legal engine there is. Replace with your own idea:
        # material counting, piece-square tables, a minimax search, ...
        return random.choice(list(board.legal_moves))
