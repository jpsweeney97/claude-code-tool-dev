"""Shared event log helpers for cross-model plugin analytics.

Used by analytics-emitting cross-model scripts. codex_guard.py is NOT
migrated (D26 — keeps its own _ts and _append_log with different semantics).

Exports:
    LOG_PATH: Path to ~/.claude/.codex-events.jsonl
    ts() -> str: ISO 8601 UTC with Z suffix (second precision)
    append_log(entry) -> bool: Atomic append, returns success
    session_id() -> str | None: From CLAUDE_SESSION_ID, nullable
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH: Path = Path.home() / ".claude" / ".codex-events.jsonl"


def ts() -> str:
    """ISO 8601 UTC timestamp with Z suffix. Second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_log(entry: dict) -> bool:
    """Append a JSON line to the event log. Returns True on success.

    Append-mode write — POSIX atomic for single-line writes under PIPE_BUF (4KB).
    """
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOG_PATH, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as f:
                fd = -1
                f.write(json.dumps(entry) + "\n")
        finally:
            if fd >= 0:
                os.close(fd)
        return True
    except OSError as exc:
        print(f"log write failed: {exc}", file=sys.stderr)
        return False


def session_id() -> str | None:
    """Read session ID from environment. Never fabricated.

    Returns None if CLAUDE_SESSION_ID is absent, empty, or whitespace-only.
    """
    value = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    return value or None
