"""FastAPI backend for playing a human against an engine.

The human is just another player: the referee logic (validate the move, let the
engine reply, decide the result) is the same one the tournament uses. python-chess
is the source of truth for legality, so a tampered browser can't cheat.

Games are held in memory, so this is a single-process, single-user-ish server —
perfect for "clone it and play on your laptop", not a public multi-user site.

Run it with:  python -m grokchess.web   (from the repo root)
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import chess
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..arena import DEFAULT_TIME_LIMIT, MoveTimeout, _natural_reason, call_with_time_limit
from ..discovery import load_engines

TIME_LIMIT = float(os.environ.get("GROKCHESS_TIME_LIMIT", DEFAULT_TIME_LIMIT))
ENGINES_DIR = os.environ.get("GROKCHESS_ENGINES_DIR", "engines")
MAX_GAMES = 50  # in-memory game cap; oldest games are evicted past this

app = FastAPI(title="grokchess")

# Serve the vendored piece art (and any future assets) locally — no CDN, so the
# board works fully offline.
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

_INDEX_HTML = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

# name -> engine class
_REGISTRY: dict[str, type] = {}
# game_id -> game state
_GAMES: dict[str, dict] = {}


def _registry() -> dict[str, type]:
    if not _REGISTRY:
        for cls in load_engines(ENGINES_DIR):
            _REGISTRY[cls.name] = cls
    return _REGISTRY


class NewGame(BaseModel):
    engine: str
    human_color: str = "white"


class MoveReq(BaseModel):
    game_id: str
    from_sq: str = Field(alias="from")
    to_sq: str = Field(alias="to")
    promotion: str | None = None

    model_config = {"populate_by_name": True}


def _human_wins_status(game: dict) -> str:
    return "white_wins" if game["human_color"] == chess.WHITE else "black_wins"


def _status(game: dict):
    """Return (status, reason, detail)."""
    if game.get("forfeit"):
        return game["forfeit"]
    board = game["board"]
    if board.is_game_over(claim_draw=True):
        mapping = {"1-0": "white_wins", "0-1": "black_wins", "1/2-1/2": "draw"}
        return mapping[board.result(claim_draw=True)], _natural_reason(board), ""
    return "playing", "", ""


def _resolve_move(board: chess.Board, frm: str, to: str, promotion: str | None):
    frm, to = frm.lower(), to.lower()
    candidates = [
        m
        for m in board.legal_moves
        if chess.square_name(m.from_square) == frm
        and chess.square_name(m.to_square) == to
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if promotion:
        for m in candidates:
            if m.promotion and chess.piece_symbol(m.promotion) == promotion.lower():
                return m
    for m in candidates:  # default to a queen
        if m.promotion == chess.QUEEN:
            return m
    return candidates[0]


def _engine_reply(game: dict) -> None:
    """If it's the engine's turn, let it move (or forfeit on error/timeout)."""
    board = game["board"]
    if game.get("forfeit") or board.is_game_over(claim_draw=True):
        return
    if board.turn == game["human_color"]:
        return
    engine = game["engine"]
    try:
        move, _ = call_with_time_limit(
            lambda: engine.choose_move(board.copy()), TIME_LIMIT
        )
    except MoveTimeout as exc:
        game["forfeit"] = (_human_wins_status(game), "timeout", str(exc))
        return
    except Exception as exc:  # noqa: BLE001 - engine bug forfeits
        game["forfeit"] = (_human_wins_status(game), "engine_error", repr(exc))
        return
    if not isinstance(move, chess.Move) or move not in board.legal_moves:
        game["forfeit"] = (_human_wins_status(game), "illegal_move", str(move))
        return
    board.push(move)
    game["last_move"] = move.uci()


def _state(game_id: str) -> dict:
    game = _GAMES[game_id]
    board = game["board"]
    status, reason, detail = _status(game)
    legal = [
        {
            "from": chess.square_name(m.from_square),
            "to": chess.square_name(m.to_square),
            "uci": m.uci(),
            "promotion": chess.piece_symbol(m.promotion) if m.promotion else None,
        }
        for m in board.legal_moves
    ]
    return {
        "game_id": game_id,
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "human_color": "white" if game["human_color"] == chess.WHITE else "black",
        "engine": game["engine_name"],
        "legal_moves": legal,
        "last_move": game.get("last_move"),
        "check": board.is_check(),
        "status": status,
        "reason": reason,
        "detail": detail,
        "move_number": board.fullmove_number,
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@app.get("/api/engines")
def engines():
    return [
        {"name": cls.name, "author": getattr(cls, "author", ""), "league": getattr(cls, "league", "")}
        for cls in _registry().values()
    ]


@app.post("/api/new")
def new_game(req: NewGame):
    registry = _registry()
    if req.engine not in registry:
        raise HTTPException(status_code=404, detail=f"unknown engine: {req.engine}")
    if req.human_color not in ("white", "black"):
        raise HTTPException(status_code=400, detail="human_color must be 'white' or 'black'")
    # Bound the store: dicts iterate in insertion order, so the first key is
    # the oldest game. Without this, every "New game" click leaks memory.
    while len(_GAMES) >= MAX_GAMES:
        _GAMES.pop(next(iter(_GAMES)))
    game_id = uuid.uuid4().hex[:12]
    game = {
        "board": chess.Board(),
        "engine": registry[req.engine](),
        "engine_name": req.engine,
        "human_color": chess.WHITE if req.human_color == "white" else chess.BLACK,
        "last_move": None,
    }
    _GAMES[game_id] = game
    _engine_reply(game)  # engine moves first if the human chose Black
    return _state(game_id)


@app.post("/api/move")
def move(req: MoveReq):
    if req.game_id not in _GAMES:
        raise HTTPException(status_code=404, detail="unknown game_id")
    game = _GAMES[req.game_id]
    status, _, _ = _status(game)
    if status != "playing":
        return _state(req.game_id)
    board = game["board"]
    if board.turn != game["human_color"]:
        raise HTTPException(status_code=400, detail="not your turn")
    chosen = _resolve_move(board, req.from_sq, req.to_sq, req.promotion)
    if chosen is None:
        raise HTTPException(status_code=400, detail=f"illegal move: {req.from_sq}{req.to_sq}")
    board.push(chosen)
    game["last_move"] = chosen.uci()
    _engine_reply(game)
    return _state(req.game_id)


@app.get("/api/state/{game_id}")
def state(game_id: str):
    if game_id not in _GAMES:
        raise HTTPException(status_code=404, detail="unknown game_id")
    return _state(game_id)
