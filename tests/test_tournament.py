"""Tournament tallying and engine discovery."""

import random

import pytest

from grokchess.discovery import load_engines
from grokchess.engine_base import Engine
from grokchess.tournament import round_robin


class AlphaEngine(Engine):
    name = "alpha"
    author = "test"
    league = "L0"

    def choose_move(self, board):
        return random.choice(list(board.legal_moves))


class BetaEngine(Engine):
    name = "beta"
    author = "test"
    league = "L0"

    def choose_move(self, board):
        return next(iter(board.legal_moves))


def test_round_robin_plays_both_colors():
    table, results = round_robin([AlphaEngine, BetaEngine], rounds=1, max_plies=60)
    # 2 engines -> each ordered pair once -> 2 games; each engine plays twice.
    assert len(results) == 2
    assert len(table) == 2
    for standing in table:
        assert standing.played == 2
        assert standing.wins + standing.draws + standing.losses == 2
    # Points are internally consistent (win=1, draw=0.5).
    total_points = sum(s.points for s in table)
    assert abs(total_points - len(results)) < 1e-9


def test_discovery_skips_template_and_finds_reference_engines():
    classes = load_engines("engines")
    names = {c.name for c in classes}
    assert "random-mover" in names
    assert "greedy-material" in names
    assert "minimax-ab" in names
    # The copy-me template must never be picked up.
    assert "my-engine" not in names


ENGINE_SRC = """
import random
import chess
from grokchess.engine_base import Engine

class E(Engine):
    name = {name!r}
    author = {author!r}
    def choose_move(self, board):
        return random.choice(list(board.legal_moves))
"""


def test_discovery_rejects_duplicate_names(tmp_path):
    # Two friends copy the template and both forget to rename their engine —
    # discovery must refuse loudly instead of silently shadowing one of them.
    (tmp_path / "alice").mkdir()
    (tmp_path / "bob").mkdir()
    (tmp_path / "alice" / "engine.py").write_text(
        ENGINE_SRC.format(name="my-engine", author="alice"), encoding="utf-8"
    )
    (tmp_path / "bob" / "engine.py").write_text(
        ENGINE_SRC.format(name="my-engine", author="bob"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate engine name"):
        load_engines(tmp_path)
