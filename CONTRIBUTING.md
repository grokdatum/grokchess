# Contributing your engine

New to the GitHub pull-request flow? This is the whole dance. (A **pull
request**, or PR, is how you propose changes: you push your work to a *branch*
— a parallel line of history — and ask for it to be merged into `main`.)

## One-time setup

```bash
git clone https://github.com/grokdatum/grokchess
cd grokchess
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Every time you add or change an engine

```bash
# 1. Start a branch named after what you're doing
git checkout main && git pull
git checkout -b add-<your-name>-engine

# 2. Copy the template and make it yours
cp -r engines/_template engines/<your-name>
$EDITOR engines/<your-name>/engine.py   # rename the class; set name/author/league

# 3. Check your work locally (this is exactly what CI will run)
python tools/check_imports.py engines   # imports: stdlib + chess only
pytest -q                               # referee tests still pass
python -m grokchess.tournament -v       # your engine actually plays

# 4. Push your branch and open the PR
git add engines/<your-name>
git commit -m "feat: add <engine-name> (league L0)"
git push -u origin add-<your-name>-engine
```

Then open the link git prints (or go to the repo page — GitHub shows a
"Compare & pull request" button). CI must be green before it can merge —
`main` is protected, so nobody (including you) can land a broken engine.

## Ground rules

Read [`RULES.md`](RULES.md) — short version: your own folder, stdlib + `chess`
imports only, no borrowed brains, legal move within 1 second, declare a league.

Touching the referee, web UI, or tools is welcome too — same flow, just keep
the engine contract stable (see [`CLAUDE.md`](CLAUDE.md) "Conventions").

## Stuck?

Open an issue, or just push the branch and open a draft PR — broken is fine,
that's what review is for. This is a learning repo; questions are the point.
