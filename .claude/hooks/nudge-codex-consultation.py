#!/usr/bin/env python3
# /// hook
# event: PostToolUseFailure
# matcher: Bash
# timeout: 5
# ///
"""
Suggest /codex consultation after repeated Bash failures.

Verified 2026-02-17: PostToolUseFailure additionalContext delivery confirmed working.
The additionalContext field is injected as a system-reminder visible to Claude.

Tracks failure count per session in a temp file. After THRESHOLD failures,
injects an additionalContext nudge suggesting /codex for a second opinion.
Counter resets after each nudge so the suggestion recurs only after another
THRESHOLD failures.

Exit codes:
  0 - Success (with optional additionalContext JSON)
  1 - Hook error (non-blocking, logged in verbose mode)
"""
import json
import sys
import tempfile
from pathlib import Path

THRESHOLD = 3


def state_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"claude-nudge-{session_id}"


def read_count(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_count(path: Path, count: int) -> None:
    path.write_text(str(count))


def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"nudge-codex-consultation: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    count = read_count(path) + 1

    if count >= THRESHOLD:
        write_count(path, 0)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several consecutive failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }
        print(json.dumps(output))
    else:
        write_count(path, count)

    sys.exit(0)


if __name__ == "__main__":
    main()
