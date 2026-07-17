# engines/

One folder per person. Put your engine(s) in `engines/<your-name>/` — that way
nobody's changes collide.

## Add your engine

```bash
cp -r engines/_template engines/<your-name>
$EDITOR engines/<your-name>/engine.py     # rename the class, set name/author/league
python -m grokchess.tournament -v         # watch it play
```

An engine is just a subclass of `grokchess.engine_base.Engine` with a
`choose_move(board) -> chess.Move` method. The referee gives you a **copy** of
the board, so push/pop moves on it freely while you think.

## Rules (short version — see `../RULES.md` for the full text)

- Import only the Python **standard library** and **`chess`**. CI enforces this.
- **No borrowed brains:** no external engines (Stockfish etc.), no cloud APIs,
  no opening books, no endgame tablebases.
- Return a **legal move** within the **time limit** (1s default). Illegal move,
  crash, or timeout = you lose that game.
- Declare your **league** on the class: `L0` (no lookahead), `L1` (search ≤
  depth 3), or `L2` (open).

## What's here

- `_template/` — copy-me starter (skipped by the tournament; the leading `_`).
- `eric/` — reference engines: `random-mover` (L0), `greedy-material` (L1),
  `minimax-ab` (L1). Beat these first.
