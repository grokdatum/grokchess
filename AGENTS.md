# AGENTS.md — grokchess

Guidance for AI coding agents (and humans) working in this repo.

**This file is canonical for every agent** — Claude Code, Codex, Cursor, Aider,
or whatever comes next. [`CLAUDE.md`](CLAUDE.md) is a pointer to this file, not a
second copy. If you're an agent that auto-loads a vendor-specific filename, you
have already been redirected here; read on.

**When you change how this repo works, update this file — not a per-vendor
copy.** Two divergent guidance files is worse than none, because whichever one
an agent happens to load becomes the truth.

grokchess is a self-contained, public, MIT-licensed learning project: friends
writing chess engines that play each other and their authors.

## What this repo is

- A **referee** (`grokchess/arena.py`) that plays one game between two players,
  enforcing legality and a per-move time limit.
- A **tournament runner** (`grokchess/tournament.py`) — round-robin + leaderboard.
- A **web board** (`grokchess/web/`) — FastAPI backend + a self-contained
  click-to-move UI, so a human can play any engine.
- A **desktop wrapper** (`grokchess/desktop.py`) — the same web board in a
  standalone browser app window.
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

## How changes land

Contributors have **write access** and PRs **auto-merge on green CI with no
human review** — `tools/submit.sh` is the one-command flow. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

This has a direct consequence for you as an agent: **CI is the entire safety
net.** Nobody is reading the diff before it hits `main`. So when you change
shared code, add the test that would have caught you breaking it — and never
leave `main` red, because a red `main` blocks *everyone's* auto-merge, not just
the change that broke it.

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
- **Explain chess/programming jargon** the first time it appears in docs or
  comments — this is a learning repo (e.g. FEN = one-line board snapshot; minimax
  = assume the opponent replies best).
- **Contributors are on mixed platforms** — at least one is on Windows. Don't add
  symlinks, POSIX-only shell in required paths, or `/`-only path assumptions to
  anything CI or contributors depend on.

## Gotchas that have already bitten someone

- **`engines/` is not a Python package.** There is no `__init__.py`, by design —
  `grokchess/discovery.py` loads each engine from its *file path*. So
  `from engines.foo.engine import Foo` raises `ModuleNotFoundError` and, in a
  test, breaks collection for the entire suite. Use
  `load_engines("engines")` and look the class up by its `name`. This took
  `main` red on 2026-07-20.
- **A crashing engine forfeits; a crashing *import* breaks everyone.** The arena
  catches exceptions from `choose_move`, so a buggy engine just loses. But an
  engine that raises at import time or in its constructor breaks discovery, and
  therefore the CI smoke tournament, for every contributor.

## Handy commands

```bash
pip install -e ".[dev]"                 # install with test + web deps
pytest -q                               # run tests
python tools/check_imports.py engines   # enforce the import allowlist
python -m grokchess.tournament -v       # run a round-robin
python -m grokchess.web                 # serve the web board on :8000
python -m grokchess.desktop             # same board, standalone app window
tools/submit.sh -m "feat: ..."          # branch, push, open a self-merging PR
```

Everything CI runs, in one line:

```bash
python tools/check_imports.py engines && pytest -q \
  && python -m grokchess.tournament --rounds 1 --time-limit 1 --max-plies 60
```
