#!/usr/bin/env python3
"""check-imports: verify engine files import only stdlib + chess + grokchess.

This is the "no borrowed brains" gate. An engine that imports ``requests``,
``torch``, ``stockfish``, etc. is rejected. Relative imports (within your own
engine folder) are always fine.

Usage:
    python tools/check_imports.py [PATH ...]      # default: engines

Exits 0 if clean, 1 if any disallowed import is found. Data goes nowhere on
stdout; violations and the summary go to stderr.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ALLOWED_EXTRA = {"chess", "grokchess"}


def _stdlib_names() -> set[str]:
    names = getattr(sys, "stdlib_module_names", None)
    if names:
        return set(names)
    # Python < 3.10 fallback: a small, conservative allowlist.
    return {
        "abc", "argparse", "collections", "copy", "dataclasses", "enum",
        "functools", "itertools", "json", "math", "os", "random", "re",
        "signal", "sys", "time", "typing",
    }


def _top_level_imports(tree: ast.AST) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import within the engine's own folder
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-imports",
        description="Verify engine files import only stdlib + chess + grokchess.",
    )
    parser.add_argument("paths", nargs="*", help="files or dirs to scan (default: engines)")
    args = parser.parse_args(argv)

    paths = [Path(p) for p in (args.paths or ["engines"])]
    allowed = _stdlib_names() | ALLOWED_EXTRA

    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)

    violations = 0
    for f in files:
        if "__pycache__" in f.parts:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError as exc:
            print(f"check-imports: error: {f}: syntax error: {exc}", file=sys.stderr)
            violations += 1
            continue
        for module in sorted(_top_level_imports(tree)):
            if module not in allowed:
                print(
                    f"check-imports: error: {f}: imports '{module}' (not allowed; "
                    f"stdlib + chess only)",
                    file=sys.stderr,
                )
                violations += 1

    if violations:
        print(f"check-imports: {violations} violation(s) across {len(files)} file(s)", file=sys.stderr)
        return 1
    print(f"check-imports: ok, {len(files)} file(s) scanned", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
