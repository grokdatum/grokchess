"""Run the web board:  python -m grokchess.web  (from the repo root)."""

from __future__ import annotations

import argparse

import uvicorn


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m grokchess.web",
        description="Serve the grokchess web board (human vs. engine).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    args = parser.parse_args(argv)

    print(f"grokchess.web: open http://{args.host}:{args.port}/ in your browser")
    uvicorn.run("grokchess.web.app:app", host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
