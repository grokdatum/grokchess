"""Referee behavior: legal play terminates, and every way to misbehave forfeits."""

import random
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


def test_timeout_forfeits():
    res = play_game(SleepyEngine(), RandomEngine(), time_limit=0.2)
    assert res.result == "0-1"
    assert res.reason == "timeout"


def test_winner_property():
    res = play_game(IllegalEngine(), RandomEngine())
    assert res.winner == "rand"
