"""Smoke tests for ajack's contributed engines."""

import chess

from engines.ajack.engine import AjackBerserker, AjackCounter, AjackLongbow
from grokchess.discovery import load_engines


def test_ajack_engines_return_legal_moves():
    board = chess.Board()
    for engine_cls in (AjackBerserker, AjackLongbow, AjackCounter):
        move = engine_cls().choose_move(board.copy())
        assert move in board.legal_moves


def test_discovery_finds_ajack_engines():
    names = {engine.name for engine in load_engines("engines")}
    assert {"ajack-berserker", "ajack-longbow", "ajack-counter"} <= names
