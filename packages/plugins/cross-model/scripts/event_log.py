"""Shared event log helpers for cross-model plugin analytics.

Used by all analytics-emitting cross-model scripts, including codex_guard.py
(migrated from local implementations — see commit history for D26 context).

Audit durability: Best-effort JSONL append is proportionate for a single-developer
tool where security enforcement (credential blocking) does not depend on log
availability — enforcement happens fail-closed in codex_guard.py PreToolUse.
If the user base grows or audit trail is needed for governance compliance,
upgrade to a separate audit log with fail-closed write semantics.

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
