"""
Capability tools for the build reviewer - run the project's tests and take
Playwright screenshots of the running app.

Both are driven by .review/config.json, written when the project is scaffolded:

    {
      "test_cmd": ".venv/bin/pytest -q",
      "app_start_cmd": "PORT={port} .venv/bin/python app.py",
      "review_port": 5599,
      "app_ready_seconds": 30,
      "screenshot_paths": ["/", "/dashboard"]
    }

The app is started on review_port (never the dev port, so it can't collide
with a build session running the app), screenshotted, then stopped. If the
config file is missing, both tools degrade to a clear "not configured" reply
and the reviewer works read-only.
"""

import datetime
import json
import os
import re
import signal
import socket
import subprocess
import time
import urllib.request

from strands import tool

from .repo_tools import REPO_ROOT, REVIEW_DIR, SCREENSHOT_DIR

CONFIG_FILE = REVIEW_DIR / "config.json"
APP_LOG = REVIEW_DIR / "app.log"


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait_ready(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


@tool
def run_tests() -> str:
    """Run the project's test suite (test_cmd from .review/config.json).

    Returns:
        Exit code and the tail of the test output
    """
    cmd = _load_config().get("test_cmd")
    if not cmd:
        return "No test_cmd configured in .review/config.json - skip testing, review the code instead."
    try:
        p = subprocess.run(cmd, shell=True, cwd=REPO_ROOT,
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return f"ERROR: tests timed out after 600s: {cmd}"
    output = (p.stdout + "\n" + p.stderr).strip()
    return f"$ {cmd}\nexit code: {p.returncode}\n\n{output[-8000:]}"


@tool
def screenshot_page(path: str = "/") -> str:
    """Start the app on the review port, screenshot the given path, and save a PNG.

    The saved image is attached to your next Discord post automatically, so
    call this once per page worth showing (see screenshot_paths in
    .review/config.json for the suggested pages).

    Args:
        path: URL path to screenshot (default: "/")

    Returns:
        The saved PNG path, or an error
    """
    cfg = _load_config()
    start_cmd = cfg.get("app_start_cmd")
    port = int(cfg.get("review_port", 5601))  # 5599 is the app's own reserved-port guard
    if not start_cmd:
        return "No app_start_cmd configured in .review/config.json - cannot screenshot."

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "ERROR: playwright is not installed (pip install playwright && playwright install chromium)"

    url = f"http://127.0.0.1:{port}{path if path.startswith('/') else '/' + path}"
    proc = None
    already_running = _port_open(port)
    try:
        if not already_running:
            with APP_LOG.open("a") as log:
                proc = subprocess.Popen(
                    start_cmd.format(port=port), shell=True, cwd=REPO_ROOT,
                    env={**os.environ, "PORT": str(port)},
                    stdout=log, stderr=log, start_new_session=True,
                )
            if not _wait_ready(f"http://127.0.0.1:{port}/", int(cfg.get("app_ready_seconds", 30))):
                return f"ERROR: app did not become ready on port {port} - check .review/app.log"

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "root"
        out = SCREENSHOT_DIR / f"{datetime.datetime.now():%Y%m%d_%H%M%S}_{slug}.png"

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, wait_until="networkidle", timeout=20000)
            page.screenshot(path=str(out), full_page=True)
            browser.close()
        return f"Saved screenshot of {url} to {out}"
    except Exception as e:
        return f"ERROR: screenshot of {url} failed: {e}"
    finally:
        if proc is not None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except OSError:
                pass
