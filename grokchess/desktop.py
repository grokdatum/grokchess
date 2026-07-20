"""Launch grokchess in a browser app window.

This keeps the project cross-platform: Windows and Linux can run the same
module, and browsers that support app windows open without normal tabs/toolbars.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn


def _serve(host: str, port: int) -> None:
    uvicorn.run("grokchess.web.app:app", host=host, port=port, log_level="warning")


def _wait_until_ready(url: str, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.4):
                return
        except URLError:
            time.sleep(0.15)
    raise RuntimeError(f"server did not start at {url}")


def _browser_candidates() -> list[str]:
    if sys.platform.startswith("win"):
        return ["msedge", "chrome"]
    return ["google-chrome", "chromium", "chromium-browser", "microsoft-edge"]


def _open_window(url: str) -> None:
    for name in _browser_candidates():
        browser = shutil.which(name)
        if browser:
            subprocess.Popen([browser, f"--app={url}"])
            return
    webbrowser.open(url)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="grokchess-desktop",
        description="Serve grokchess and open it in its own browser window.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    args = parser.parse_args(argv)

    url = f"http://{args.host}:{args.port}/"
    server = threading.Thread(target=_serve, args=(args.host, args.port), daemon=True)
    server.start()
    _wait_until_ready(url)
    _open_window(url)
    print(f"grokchess.desktop: running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
