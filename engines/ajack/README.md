# ajack engines

This folder contains three League L1 engines that share one evaluator and choose
moves differently.

| Engine | Idea |
|--------|------|
| `ajack-berserker` | Plays for checks, captures, king pressure, and fast piece activity. |
| `ajack-longbow` | Builds long-range pressure with bishops, rooks, queens, open files, and pins. |
| `ajack-counter` | Finds the opponent's strongest expected reply, then chooses the move that leaves the best counter. |

All three follow the project rules: they import only the standard library,
`chess`, and `grokchess`; use no external engines, books, APIs, or tablebases;
and return legal moves inside the tournament time limit.
