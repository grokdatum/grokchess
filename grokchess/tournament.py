"""Round-robin tournament runner + leaderboard.

Every engine plays every other engine twice — once as White, once as Black.
Win = 1 point, draw = 0.5, loss = 0. Run it with::

    python -m grokchess.tournament

Data (the standings table) goes to stdout so it stays greppable; progress and
diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from dataclasses import dataclass
from pathlib import Path

from .arena import DEFAULT_MAX_PLIES, DEFAULT_TIME_LIMIT, GameResult, play_game
from .discovery import load_engines


@dataclass
class Standing:
    name: str
    author: str = ""
    league: str = ""
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def points(self) -> float:
        return self.wins + 0.5 * self.draws


def _tally(white_s: Standing, black_s: Standing, res: GameResult) -> None:
    white_s.played += 1
    black_s.played += 1
    if res.result == "1-0":
        white_s.wins += 1
        black_s.losses += 1
    elif res.result == "0-1":
        black_s.wins += 1
        white_s.losses += 1
    else:
        white_s.draws += 1
        black_s.draws += 1


def round_robin(
    engine_classes,
    *,
    time_limit: float = DEFAULT_TIME_LIMIT,
    max_plies: int = DEFAULT_MAX_PLIES,
    rounds: int = 1,
    start_fen: str | None = None,
    on_game=None,
):
    """Play a full round-robin. Returns ``(standings_table, results)``.

    ``standings_table`` is sorted best-first. ``on_game(res)`` is called after
    each game (used by the CLI to print progress to stderr).
    """
    standings = {
        cls: Standing(cls.name, getattr(cls, "author", ""), getattr(cls, "league", ""))
        for cls in engine_classes
    }
    results: list[GameResult] = []

    for _ in range(rounds):
        for white_cls, black_cls in itertools.permutations(engine_classes, 2):
            res = play_game(
                white_cls(),
                black_cls(),
                time_limit=time_limit,
                max_plies=max_plies,
                start_fen=start_fen,
            )
            results.append(res)
            _tally(standings[white_cls], standings[black_cls], res)
            if on_game is not None:
                on_game(res)

    table = sorted(
        standings.values(), key=lambda s: (s.points, s.wins), reverse=True
    )
    return table, results


def _print_standings(table) -> None:
    """Standings table to stdout — one engine per line, no decoration."""
    header = ("rank", "name", "author", "league", "played", "W", "D", "L", "points")
    rows = [header]
    for i, s in enumerate(table, start=1):
        rows.append(
            (
                str(i),
                s.name,
                s.author,
                s.league,
                str(s.played),
                str(s.wins),
                str(s.draws),
                str(s.losses),
                f"{s.points:g}",
            )
        )
    widths = [max(len(r[c]) for r in rows) for c in range(len(header))]
    for r in rows:
        print("  ".join(cell.ljust(widths[c]) for c, cell in enumerate(r)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="grokchess-tournament",
        description="Run a round-robin tournament across all discovered engines.",
    )
    parser.add_argument(
        "--engines-dir", default="engines", help="where to look for engines (default: engines)"
    )
    parser.add_argument(
        "--time-limit", type=float, default=DEFAULT_TIME_LIMIT,
        help=f"seconds per move (default: {DEFAULT_TIME_LIMIT})",
    )
    parser.add_argument(
        "--rounds", type=int, default=1, help="how many full round-robins to play (default: 1)"
    )
    parser.add_argument(
        "--max-plies", type=int, default=DEFAULT_MAX_PLIES,
        help=f"cap on game length in plies (default: {DEFAULT_MAX_PLIES})",
    )
    parser.add_argument(
        "--save-dir", default=None,
        help="if set, write each game's PGN into this directory",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="print each game's result to stderr as it finishes",
    )
    args = parser.parse_args(argv)

    engine_classes = load_engines(args.engines_dir)
    if len(engine_classes) < 2:
        print(
            f"grokchess-tournament: error: need at least 2 engines, found "
            f"{len(engine_classes)} in {args.engines_dir}",
            file=sys.stderr,
        )
        return 1

    print(
        f"grokchess-tournament: {len(engine_classes)} engines, "
        f"{args.rounds} round(s), {args.time_limit}s/move",
        file=sys.stderr,
    )

    save_dir = Path(args.save_dir) if args.save_dir else None
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
    counter = {"n": 0}

    def on_game(res: GameResult) -> None:
        counter["n"] += 1
        if args.verbose:
            print(
                f"  game {counter['n']:>4}: {res.white} vs {res.black} -> "
                f"{res.result} ({res.reason})"
                + (f" [{res.detail}]" if res.detail else ""),
                file=sys.stderr,
            )
        if save_dir is not None:
            out = save_dir / f"game-{counter['n']:04d}.pgn"
            out.write_text(res.pgn + "\n", encoding="utf-8")

    table, _results = round_robin(
        engine_classes,
        time_limit=args.time_limit,
        max_plies=args.max_plies,
        rounds=args.rounds,
        on_game=on_game,
    )

    _print_standings(table)

    launcher = f'"{sys.executable}" -m grokchess.desktop'
    if sys.platform.startswith("win"):
        launcher = "& " + launcher
    print(
        "grokchess-tournament: done. "
        + (f"PGNs in {save_dir}/. " if save_dir else "")
        + "Next: open the board with "
        + f"`{launcher}` (see README).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
