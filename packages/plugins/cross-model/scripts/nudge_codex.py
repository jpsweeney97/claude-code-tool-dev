#!/usr/bin/env python3
# /// hook (documentation only — registration is in hooks.json)
# event: PostToolUseFailure
# matcher: Bash
# timeout: 5
# ///
"""
Suggest /codex consultation after repeated Bash failures.

Opt-in only: set CROSS_MODEL_NUDGE=1 to enable. User-scope plugins
affect all projects — nudging should be explicit.

Verified 2026-02-17: PostToolUseFailure additionalContext delivery confirmed working.
The additionalContext field is injected as a system-reminder visible to Claude.

Tracks failure count per session in a temp file. After THRESHOLD failures,
injects an additionalContext nudge suggesting /codex for a second opinion.
Counter resets after each nudge so the suggestion recurs only after another
THRESHOLD failures.

Exit codes:
  0 - Success (with optional additionalContext JSON)
  1 - Hook error (non-blocking)
"""
import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path

THRESHOLD = 3


def state_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"claude-nudge-{session_id}"


def main() -> None:
    # Guardrail: opt-in gate
    if os.environ.get("CROSS_MODEL_NUDGE") != "1":
        sys.exit(0)

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"nudge-codex: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # B12: Defensive tool_name filtering — PostToolUseFailure matcher support
    # is undocumented, so filter in code to ensure only Bash failures count.
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    # B13: Atomic read-increment-write with file locking
    try:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
        with os.fdopen(fd, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read().strip()
            count = (int(content) if content else 0) + 1

            if count >= THRESHOLD:
                f.seek(0)
                f.truncate()
                f.write("0")
            else:
                f.seek(0)
                f.truncate()
                f.write(str(count))
    except (ValueError, OSError) as e:
        print(f"nudge-codex: state file error, resetting count: {e}", file=sys.stderr)
        count = 1

    if count >= THRESHOLD:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
