#!/usr/bin/env python3
"""Start sidecar and register session.

Hook event: SessionStart(startup), async command hook.
If sidecar already running: register session, exit.
If not running: start sidecar in background, register session, exit.

Design reference: Amendment 3 F3 (no kill-restart).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"
PLUGIN_ROOT = Path(__file__).parent.parent


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Fail-open

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    if not session_id:
        session_id = Path(transcript_path).stem if transcript_path else ""

    if not session_id:
        return 0  # No session info

    # Check if sidecar is running
    if not _sidecar_healthy():
        _start_sidecar()
        # Wait for startup (up to 2 seconds)
        for _ in range(20):
            time.sleep(0.1)
            if _sidecar_healthy():
                break

    # Register session
    _register_session(session_id, transcript_path)
    return 0


def _sidecar_healthy() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{DEFAULT_PORT}/health", timeout=1
        ) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


LOG_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.log"


def _start_sidecar() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fd = open(LOG_FILE, "a")  # noqa: SIM115 — intentionally leaked to subprocess
    subprocess.Popen(
        [sys.executable, "-m", "scripts.server", "--port", str(DEFAULT_PORT)],
        cwd=str(PLUGIN_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=log_fd,
        start_new_session=True,
    )
    log_fd.close()


def _register_session(session_id: str, transcript_path: str) -> None:
    try:
        qs = urllib.parse.urlencode({"session_id": session_id, "transcript_path": transcript_path})
        url = f"http://127.0.0.1:{DEFAULT_PORT}/sessions/register?{qs}"
        urllib.request.urlopen(url, timeout=2)
    except (urllib.error.URLError, OSError, TimeoutError):
        pass  # Fail-open


if __name__ == "__main__":
    sys.exit(main())
