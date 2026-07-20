# CLAUDE.md — grokchess

Guidance for AI assistants (and humans) working in this repo. grokchess is a
self-contained, public, MIT-licensed learning project: friends writing chess
engines that play each other and their authors.

## What this repo is

- A **referee** (`grokchess/arena.py`) that plays one game between two players,
  enforcing legality and a per-move time limit.
- A **tournament runner** (`grokchess/tournament.py`) — round-robin + leaderboard.
- A **web board** (`grokchess/web/`) — FastAPI backend + a self-contained
  click-to-move UI, so a human can play any engine.
- **Engines** under `engines/<name>/` — one folder per contributor.

python-chess is the single source of truth for the rules. Engines only pick moves.

## The engine contract

An engine subclasses `grokchess.engine_base.Engine` and implements
`choose_move(board) -> chess.Move`. It gets a **copy** of the board. Returning an
illegal move, crashing, or exceeding the time limit forfeits the game — the
referee handles all of that; engines should just try to return a legal move.

## Rules of the exercise

See [`RULES.md`](RULES.md). The load-bearing constraints:

- Engines import **only the standard library and `chess`** (enforced by
  `tools/check_imports.py` in CI).
- **No borrowed brains:** no external engines, cloud APIs, opening books, or
  tablebases.
- Legal move within the time limit; declare a **league** (L0/L1/L2).

## Conventions for changes

- **Don't break the contract.** `Engine.choose_move(board) -> chess.Move` and the
  arena's forfeit behavior are the stable API everyone builds on. Changing them
  means updating every engine and the docs in the same PR.
- **CLI tools:** support `--help`, send data to stdout and diagnostics to stderr,
  and never require a flag to do something read-only.
- **Keep engines standalone.** An engine folder should be copy-pasteable; don't
  make one contributor's engine import another's.
- **Tests + CI stay green.** `pytest -q`, `python tools/check_imports.py engines`,
  and a smoke tournament all run on every PR (`.github/workflows/ci.yml`).
  **CI is the only gate** — contributors have write access and PRs auto-merge on
  green with no human review (`tools/submit.sh` is the one-command flow). So a
  passing test suite is the entire safety net: when you change shared code, add
  the test that would have caught you.
- **Explain chess/programming jargon** the first time it appears in docs or
  comments — this is a learning repo (e.g. FEN = one-line board snapshot; minimax
  = assume the opponent replies best).

## Handy commands

```bash
pip install -e ".[dev]"                 # install with test + web deps
pytest -q                               # run tests
python tools/check_imports.py engines   # enforce the import allowlist
python -m grokchess.tournament -v       # run a round-robin
python -m grokchess.web                 # serve the web board on :8000
```
