"""Referee behavior: legal play terminates, and every way to misbehave forfeits."""

import random
import threading
import time

import chess

from grokchess.arena import GameResult, play_game
from grokchess.engine_base import Engine


class RandomEngine(Engine):
    name = "rand"
    author = "test"
    league = "L0"

    def choose_move(self, board):
        return random.choice(list(board.legal_moves))


class FirstMoveEngine(Engine):
    name = "first"
    author = "test"
    league = "L0"

    def choose_move(self, board):
        return next(iter(board.legal_moves))


class IllegalEngine(Engine):
    name = "cheater"
    author = "test"

    def choose_move(self, board):
        # a1->a3 is blocked by the a2 pawn at the start: not a legal move
        return chess.Move(chess.A1, chess.A3)


class BoomEngine(Engine):
    name = "boom"
    author = "test"

    def choose_move(self, board):
        raise ValueError("kaboom")


class SleepyEngine(Engine):
    name = "sleepy"
    author = "test"

    def choose_move(self, board):
        time.sleep(5)
        return next(iter(board.legal_moves))


def test_random_game_terminates():
    res = play_game(RandomEngine(), RandomEngine(), max_plies=80)
    assert isinstance(res, GameResult)
    assert res.result in {"1-0", "0-1", "1/2-1/2"}
    assert res.pgn


def test_illegal_move_forfeits():
    # White (illegal) loses immediately on move 1.
    res = play_game(IllegalEngine(), RandomEngine())
    assert res.result == "0-1"
    assert res.reason == "illegal_move"


def test_engine_error_forfeits():
    # White plays fine, Black crashes -> Black loses.
    res = play_game(RandomEngine(), BoomEngine())
    assert res.result == "1-0"
    assert res.reason == "engine_error"


class DefensiveLateEngine(Engine):
    """Wraps everything in try/except and returns a legal move — late.

    Regression for the "timeout swallower" hole: with the old signal-based
    timer, catching Exception ate the timeout and the late move was accepted.
    The watcher-thread design raises the timeout in the referee instead, so
    this engine must forfeit no matter what it catches.
    """

    name = "defensive-late"
    author = "test"

    def choose_move(self, board):
        deadline = time.time() + 0.6  # 3x the 0.2s limit used below
        while True:
            try:
                while time.time() < deadline:
                    pass
                return next(iter(board.legal_moves))
            except Exception:
                pass


def test_timeout_forfeits():
    res = play_game(SleepyEngine(), RandomEngine(), time_limit=0.2)
    assert res.result == "0-1"
    assert res.reason == "timeout"


def test_timeout_cannot_be_swallowed():
    res = play_game(DefensiveLateEngine(), RandomEngine(), time_limit=0.2)
    assert res.result == "0-1"
    assert res.reason == "timeout"


def test_timeout_enforced_off_main_thread():
    """The web server calls the referee from a worker thread — the limit must
    hold there too (regression: the old SIGALRM path only worked on the main
    thread and silently degraded to a soft check that can't stop a stuck engine).
    """
    results = []
    t = threading.Thread(
        target=lambda: results.append(
            play_game(SleepyEngine(), RandomEngine(), time_limit=0.2)
        )
    )
    t.start()
    t.join(10)
    assert not t.is_alive(), "game hung when run off the main thread"
    assert results[0].result == "0-1"
    assert results[0].reason == "timeout"


def test_winner_property():
    res = play_game(IllegalEngine(), RandomEngine())
    assert res.winner == "rand"
