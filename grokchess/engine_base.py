"""The engine contract.

Every grokchess engine subclasses :class:`Engine` and implements
``choose_move``. That's the whole interface — everything else (holding the real
board, enforcing the time limit, rejecting illegal moves, recording the game)
is the referee's job, not yours. See ``grokchess/arena.py``.
"""

from __future__ import annotations

import chess


class Engine:
    """Base class for all grokchess engines.

    Subclass this and implement :meth:`choose_move`. The referee calls it with
    a *copy* of the current board, so you can ``push``/``pop`` moves on it while
    thinking without disturbing the real game.

    Class attributes (override these on your subclass):

    * ``name``   — short, unique-ish display name.
    * ``author`` — who wrote it.
    * ``league`` — the division you're entering (see ``RULES.md``):

        - ``"L0"`` — no lookahead: decide from the current position only.
        - ``"L1"`` — shallow search: look ahead at most depth 3.
        - ``"L2"`` — open: anything, as long as you stay inside the time limit.
    """

    name: str = "unnamed"
    author: str = "anonymous"
    league: str = "L2"

    def choose_move(self, board: chess.Board) -> chess.Move:
        """Return a legal move for the side to move (``board.turn``).

        Must return a ``chess.Move``. Returning an illegal move, raising an
        exception, or taking longer than the per-move time limit all count as
        losing the game — so when in doubt, return *some* legal move.
        """
        raise NotImplementedError(
            f"{type(self).__name__}.choose_move() is not implemented"
        )

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} name={self.name!r} author={self.author!r} league={self.league!r}>"
