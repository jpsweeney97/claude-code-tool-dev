#!/usr/bin/env python3
"""Context summary injection hook.

Hook events: UserPromptSubmit, SessionStart(compact).
Queries sidecar -> prints summary to stdout -> exit 0.
Fail-open: sidecar unreachable -> exit 0 (no output).

Stdout is the injection channel: Claude Code captures hook stdout as
system-reminder content. Only event-specific logic is notifying sidecar
of compaction on SessionStart(compact).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_PORT = 7432


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Fail-open

    event = hook_input.get("hook_event_name", "")
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    # Handle compaction: mark compaction pending on sidecar
    if event == "SessionStart" and hook_input.get("subtype") == "compact":
        _notify_compaction(args.port, session_id)

    # Query sidecar for injection decision
    payload = json.dumps({
        "hook_event_name": event,
        "session_id": session_id,
        "transcript_path": transcript_path,
    }).encode()

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{args.port}/hooks/context-metrics",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        return 0  # Fail-open: sidecar unreachable

    if result.get("inject") and result.get("summary"):
        print(result["summary"])

    return 0


def _notify_compaction(port: int, session_id: str) -> None:
    """Tell sidecar that a compaction occurred for this session."""
    try:
        qs = urllib.parse.urlencode({"session_id": session_id})
        url = f"http://127.0.0.1:{port}/sessions/compaction?{qs}"
        urllib.request.urlopen(url, timeout=2)
    except (urllib.error.URLError, OSError, TimeoutError):
        pass  # Fail-open


if __name__ == "__main__":
    sys.exit(main())
