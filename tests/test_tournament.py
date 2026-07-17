"""Tournament tallying and engine discovery."""

import random

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
