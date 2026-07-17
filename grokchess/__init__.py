"""grokchess — a friendly arena for home-grown chess engines."""

from __future__ import annotations

from .arena import (
    DEFAULT_MAX_PLIES,
    DEFAULT_TIME_LIMIT,
    GameResult,
    MoveTimeout,
    play_game,
)
from .discovery import load_engines
from .engine_base import Engine

# NOTE: tournament is intentionally NOT imported here. Importing it eagerly
# makes `python -m grokchess.tournament` emit a runpy double-import warning.
# Get the runner via `from grokchess.tournament import round_robin`.

__version__ = "0.1.0"

__all__ = [
    "Engine",
    "play_game",
    "GameResult",
    "MoveTimeout",
    "DEFAULT_TIME_LIMIT",
    "DEFAULT_MAX_PLIES",
    "load_engines",
    "__version__",
]
