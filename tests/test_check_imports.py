"""The import gate: stdlib+chess allowed, third-party and escape hatches not."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from check_imports import main  # noqa: E402


def _write(tmp_path, body: str) -> Path:
    f = tmp_path / "engine.py"
    f.write_text(body, encoding="utf-8")
    return f


def test_clean_engine_passes(tmp_path):
    _write(tmp_path, "import random\nimport chess\nfrom grokchess.engine_base import Engine\n")
    assert main([str(tmp_path)]) == 0


def test_third_party_rejected(tmp_path):
    _write(tmp_path, "import chess\nimport requests\n")
    assert main([str(tmp_path)]) == 1


def test_escape_hatches_rejected(tmp_path):
    # subprocess is stdlib, but it's how you'd shell out to Stockfish —
    # the denylist must catch it even though the stdlib allowlist would not.
    _write(tmp_path, "import subprocess\n")
    assert main([str(tmp_path)]) == 1


def test_relative_import_ok(tmp_path):
    _write(tmp_path, "from . import helpers\nimport chess\n")
    assert main([str(tmp_path)]) == 0
