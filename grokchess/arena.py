"""The referee.

The arena holds the single authoritative board and shuttles moves between two
players. Engines never talk to each other directly — they only ever see a copy
of the board and hand back a move. The arena:

* asks each player for a move in turn,
* enforces a per-move wall-clock time limit,
* validates that the move is legal (via python-chess),
* records the game as PGN,

and decides the result. A player that returns an illegal move, raises an
exception, or blows the time limit forfeits the game.

A "player" is anything with a ``name`` attribute and a
``choose_move(board) -> chess.Move`` method — that's an :class:`~grokchess.engine_base.Engine`,
but the web UI also wraps a human as a player, so the same code runs an
engine-vs-engine tournament and a human-vs-engine web game.
"""

from __future__ import annotations

import signal
import threading
import time
from dataclasses import dataclass, field

import chess
import chess.pgn

DEFAULT_TIME_LIMIT = 1.0   # seconds a player gets to choose one move
DEFAULT_MAX_PLIES = 400    # hard cap on game length (a ply = one side's move)


class MoveTimeout(Exception):
    """Raised when a player exceeds its per-move time budget."""


def call_with_time_limit(fn, seconds):
    """Call ``fn()`` under a wall-clock limit, returning ``(result, elapsed)``.

    On Unix, when we're on the main thread, we use ``SIGALRM`` so a genuinely
    stuck engine is actually interrupted (not just scored as late). Otherwise we
    fall back to measuring elapsed time and raising :class:`MoveTimeout` after
    the fact — cooperative, but it can't cut off an infinite loop.
    """
    use_alarm = hasattr(signal, "SIGALRM") and (
        threading.current_thread() is threading.main_thread()
    )
    if use_alarm:
        def _handler(signum, frame):  # noqa: ANN001 - signal handler signature
            raise MoveTimeout(f"exceeded {seconds:.3f}s")

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        start = time.perf_counter()
        try:
            result = fn()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
        return result, time.perf_counter() - start

    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    if elapsed > seconds:
        raise MoveTimeout(f"exceeded {seconds:.3f}s (soft limit)")
    return result, elapsed


@dataclass
class GameResult:
    """The outcome of one game."""

    white: str
    black: str
    result: str          # "1-0", "0-1", or "1/2-1/2"
    reason: str          # why it ended (see _natural_reason + forfeit reasons)
    moves: list = field(default_factory=list)   # UCI strings, in order
    pgn: str = ""
    detail: str = ""     # extra context for forfeits (the bad move / error)

    @property
    def winner(self):
        if self.result == "1-0":
            return self.white
        if self.result == "0-1":
            return self.black
        return None


def _natural_reason(board: chess.Board) -> str:
    """Why did a game that reached a terminal position end?"""
    if board.is_checkmate():
        return "checkmate"
    if board.is_stalemate():
        return "stalemate"
    if board.is_insufficient_material():
        return "insufficient_material"
    if board.is_seventyfive_moves():
        return "seventyfive_moves"
    if board.is_fivefold_repetition():
        return "fivefold_repetition"
    if board.can_claim_fifty_moves():
        return "fifty_moves"
    if board.can_claim_threefold_repetition():
        return "threefold_repetition"
    return "draw"


def play_game(
    white,
    black,
    *,
    time_limit: float = DEFAULT_TIME_LIMIT,
    max_plies: int = DEFAULT_MAX_PLIES,
    start_fen: str | None = None,
    on_move=None,
    event: str = "grokchess",
) -> GameResult:
    """Play one full game between two players and return the :class:`GameResult`.

    ``on_move(board, move)`` is an optional callback fired after each accepted
    move (handy for live displays).
    """
    board = chess.Board(start_fen) if start_fen else chess.Board()
    players = {chess.WHITE: white, chess.BLACK: black}
    names = {
        chess.WHITE: getattr(white, "name", "white"),
        chess.BLACK: getattr(black, "name", "black"),
    }

    game = chess.pgn.Game()
    game.headers["Event"] = event
    game.headers["White"] = names[chess.WHITE]
    game.headers["Black"] = names[chess.BLACK]
    if start_fen:
        game.setup(chess.Board(start_fen))
    node = game
    uci_moves: list[str] = []

    def finish(result: str, reason: str, detail: str = "") -> GameResult:
        game.headers["Result"] = result
        return GameResult(
            white=names[chess.WHITE],
            black=names[chess.BLACK],
            result=result,
            reason=reason,
            moves=uci_moves,
            pgn=str(game),
            detail=detail,
        )

    while not board.is_game_over(claim_draw=True):
        if board.ply() >= max_plies:
            return finish("1/2-1/2", "max_plies")

        color = board.turn
        mover = players[color]
        # If this mover forfeits, the *other* side wins.
        forfeit_result = "0-1" if color == chess.WHITE else "1-0"

        try:
            move, _elapsed = call_with_time_limit(
                lambda: mover.choose_move(board.copy()), time_limit
            )
        except MoveTimeout as exc:
            return finish(forfeit_result, "timeout", f"{names[color]}: {exc}")
        except Exception as exc:  # noqa: BLE001 - any engine bug forfeits the game
            return finish(forfeit_result, "engine_error", f"{names[color]}: {exc!r}")

        if not isinstance(move, chess.Move) or move not in board.legal_moves:
            return finish(forfeit_result, "illegal_move", f"{names[color]}: {move}")

        board.push(move)
        uci_moves.append(move.uci())
        node = node.add_variation(move)
        if on_move is not None:
            on_move(board, move)

    return finish(board.result(claim_draw=True), _natural_reason(board))
