# Contributing your engine

You have **write access to this repo** — no fork needed. (A *fork* is your own
copy of a repo; you'd normally need one to contribute to someone else's
project. Here you don't: you push straight to the real thing.)

## One-time setup

```bash
git clone https://github.com/grokdatum/grokchess
cd grokchess
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Every time you add or change an engine

```bash
# 1. Copy the template and make it yours
cp -r engines/_template engines/<your-name>
$EDITOR engines/<your-name>/engine.py   # rename the class; set name/author/league

# 2. Watch it play
python -m grokchess.tournament -v

# 3. Ship it
tools/submit.sh -m "feat: add <engine-name> (league L0)"
```

That's it. `submit.sh` makes a branch, commits, pushes, opens a pull request
(a **PR** — a proposal to merge your work into `main`), and turns on
**auto-merge**. The PR merges itself the moment CI goes green. Nobody has to
review it or click anything, including Eric.

If you'd rather drive git yourself, the long way still works — branch, commit,
push, then `gh pr create --fill && gh pr merge --auto --squash`. `submit.sh` is
just those steps in one command; run it with `--dry-run` to see what it would do
without doing it.

## What CI checks

The only gate is [`.github/workflows/ci.yml`](.github/workflows/ci.yml), run on
every PR against Python 3.10 and 3.12:

```bash
python tools/check_imports.py engines   # imports: stdlib + chess only
pytest -q                               # referee tests still pass
python -m grokchess.tournament          # every engine loads and plays
```

`submit.sh` runs the first two locally before pushing, so you usually find out
in seconds rather than minutes. A red PR simply doesn't merge — push fixes to
the same branch and it merges itself once green.

## Ground rules

Read [`RULES.md`](RULES.md) — short version: your own folder, stdlib + `chess`
imports only, no borrowed brains, legal move within 1 second, declare a league.

**You can change anything**, not just your own engine — the referee, the web UI,
the tools, this file. Two asks when you touch shared code:

- **Keep the engine contract stable.** `Engine.choose_move(board) -> chess.Move`
  and the arena's forfeit behavior are what everyone else builds on. If you
  change them, update every engine and the docs in the same PR.
- **Say so in the PR body.** There's no review gate, so the PR description is
  how the rest of us find out that something shared moved. See
  [`AGENTS.md`](AGENTS.md) "Conventions for changes".

Since nothing blocks a merge but CI, the honour system is doing real work here.
That's deliberate — this is a learning repo among friends, and waiting on
reviews is how side projects die.

## Using an AI agent

Several of us work on this with coding agents (Claude Code, Codex, …). The house
rules for them live in **[`AGENTS.md`](AGENTS.md)** — one vendor-neutral file
that every agent reads. `CLAUDE.md` is just a pointer to it.

If your agent writes guidance about this repo, it goes in `AGENTS.md`, not a new
per-tool file. Two copies drift, and then which rules apply depends on which
tool you happened to open.

Agents are fine here — but auto-merge means nothing but CI stands between an
agent's output and `main`. Read the diff before you run `submit.sh`.

## Stuck?

Open an issue, or push a **draft** PR — `gh pr create --draft` won't auto-merge,
so it's a safe place to show broken code and ask what's wrong. That's exactly
what it's for. Questions are the point.
