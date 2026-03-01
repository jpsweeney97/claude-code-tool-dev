#!/usr/bin/env python3
"""Deregister session and optionally stop sidecar.

Hook event: SessionEnd, command hook (stdlib only).
Deregisters session. If no active sessions remain, sends SIGTERM to sidecar.

Only stops sidecar when no sessions remain — avoids killing a shared
sidecar serving other concurrent sessions.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    if not session_id:
        session_id = Path(transcript_path).stem if transcript_path else ""

    if not session_id:
        return 0

    # Deregister session
    active_sessions = _deregister_session(session_id)

    # If no sessions remain, stop sidecar
    if active_sessions == 0:
        _stop_sidecar()

    return 0


def _deregister_session(session_id: str) -> int:
    """Deregister and return remaining active session count."""
    try:
        qs = urllib.parse.urlencode({"session_id": session_id})
        url = f"http://127.0.0.1:{DEFAULT_PORT}/sessions/deregister?{qs}"
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read())
            return data.get("active_sessions", 0)
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        return -1  # Unknown — don't kill sidecar


def _stop_sidecar() -> None:
    """Send SIGTERM to sidecar process."""
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
    except (FileNotFoundError, ValueError, ProcessLookupError, OSError):
        pass


if __name__ == "__main__":
    sys.exit(main())
