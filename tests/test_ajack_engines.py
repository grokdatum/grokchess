"""Smoke tests for ajack's contributed engines."""

import chess
import pytest

from grokchess.discovery import load_engines

AJACK_ENGINES = {"ajack-berserker", "ajack-longbow", "ajack-counter"}


# `engines/` is deliberately not a Python package — discovery loads each engine
# from its file path (see grokchess/discovery.py), so `import engines.ajack...`
# would not resolve. Go through discovery, the same way the arena does.
@pytest.fixture(scope="module")
def ajack_engine_classes():
    by_name = {engine.name: engine for engine in load_engines("engines")}
    return [by_name[name] for name in sorted(AJACK_ENGINES & by_name.keys())]


def test_ajack_engines_return_legal_moves(ajack_engine_classes):
    board = chess.Board()
    for engine_cls in ajack_engine_classes:
        move = engine_cls().choose_move(board.copy())
        assert move in board.legal_moves


def test_discovery_finds_ajack_engines():
    names = {engine.name for engine in load_engines("engines")}
    assert AJACK_ENGINES <= names
