# grokchess rules

This is a **draft** — it's meant to be argued over and edited by the group. Open
an issue or a PR to change a rule. The goal is a fun, fair learning exercise, not
an airtight anti-cheat system: we can all read each other's code, so most of this
runs on the honor system plus a couple of hard checks.

## 1. Your engine

- Lives in its own folder: `engines/<your-name>/`.
- Is a subclass of `grokchess.engine_base.Engine` with a
  `choose_move(board) -> chess.Move` method.
- Declares three things on the class: `name`, `author`, and `league`.

## 2. The move

- Return a **legal move** for the side to move.
- You get the board as a **copy** — do whatever you like to it while thinking.
- **1 second per move** (wall-clock, default). Over the limit = you lose the game.
- Returning an illegal move, returning a non-move, or crashing = you lose the game.

## 3. Leagues

Pick the division that matches how your engine thinks. Declare it in `league`.

| League | Rule | Typical approach |
|--------|------|------------------|
| **L0** | No lookahead — decide from the *current* position only. | random, or a positional score of the board as it stands |
| **L1** | Shallow search — look ahead at most **depth 3**. | greedy capture, minimax / alpha-beta depth ≤ 3 |
| **L2** | Open — anything, as long as you obey the time limit. | deeper search, quiescence, your own eval, etc. |

Leagues are self-declared and enforced socially (we read the code). Play up a
league if you like; don't play down.

## 4. No borrowed brains

The point is to write *your own* engine, so at least to start:

- ❌ No external chess engines (Stockfish, Leela, etc.) — no subprocesses, no bindings.
- ❌ No cloud APIs / network calls of any kind during a game.
- ❌ No opening books and no endgame tablebases (precomputed move databases).
- ✅ Your own hand-written heuristics, search, and evaluation are the whole game.

## 5. Imports

- Import **only the Python standard library and `chess`**.
- No `requests`, `numpy`, `torch`, `stockfish`, … (this keeps engines simple and
  the "no borrowed brains" rule enforceable).
- CI runs `tools/check_imports.py` on every pull request. It also blocks the
  stdlib escape hatches (`subprocess`, `socket`, `ctypes`, `importlib`, `os`, …)
  that would let an engine shell out to Stockfish or reach the network.
- **Honesty note:** the checker is a tripwire, not a fortress — a determined
  cheater can get around static analysis. PR review by the group is the real
  enforcement; the checker just catches accidents and the obvious routes.

## 6. Fair play

- It's a learning exercise. Share tricks and post-mortems **after** a tournament,
  not sabotage during one.
- Don't try to break the referee, crash other engines, or exploit the arena. If
  you find a hole, report it (that's a great PR).
- **Known accepted risk:** all engines run in one Python process, so a hostile
  engine *could* tamper with shared code at runtime. We accept this because we
  read each other's PRs; per-engine process isolation is on the roadmap
  (alongside the UCI bridge) if we ever need it.

## 7. Changing the rules

Everything here is negotiable except "have fun and learn". Propose changes via
issue or PR; if the group agrees, edit this file. Suggested future tweaks:
per-league time limits, a rating system, a "gauntlet vs. Stockfish (limited)"
exhibition league.
