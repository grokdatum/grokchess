"""Find engines on disk.

Each contributor drops a folder under ``engines/<name>/`` containing one or
more ``.py`` files that define :class:`~grokchess.engine_base.Engine`
subclasses. :func:`load_engines` imports them and returns the classes.

Files or folders whose names start with ``_`` (e.g. ``engines/_template/``) are
skipped, so the copy-me template never sneaks into a real tournament.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .engine_base import Engine


def _is_skipped(rel: Path) -> bool:
    return any(part.startswith("_") or part.startswith(".") for part in rel.parts)


def _load_module(path: Path, modname: str):
    spec = importlib.util.spec_from_file_location(modname, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"grokchess: could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    return module


def load_engines(engines_dir: str | Path = "engines") -> list[type[Engine]]:
    """Import every engine under ``engines_dir`` and return the classes.

    The list is sorted by ``(author, name)`` for stable ordering.
    """
    root = Path(engines_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"grokchess: engines dir not found: {root}")

    classes: list[type[Engine]] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if _is_skipped(rel):
            continue
        modname = "grokchess_engines_" + rel.with_suffix("").as_posix().replace("/", "_")
        module = _load_module(path, modname)
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, Engine)
                and obj is not Engine
                and obj.__module__ == module.__name__
            ):
                classes.append(obj)

    classes.sort(key=lambda c: (getattr(c, "author", ""), getattr(c, "name", "")))
    return classes
