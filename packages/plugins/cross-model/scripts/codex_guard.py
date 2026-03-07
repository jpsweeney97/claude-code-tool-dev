#!/usr/bin/env python3
"""
codex_guard.py — PreToolUse/PostToolUse enforcement hook for mcp__plugin_cross-model_codex__codex.

PreToolUse: Tiered credential detection on outbound Codex prompts.
  Blocks on strict/contextual tier matches.
  Logs shadow telemetry for broad-tier matches.
PostToolUse: Logs consultation event to ~/.claude/.codex-events.jsonl.

Fail-closed (PreToolUse only): any unhandled exception during hook execution
blocks the Codex call. PostToolUse errors are always silent.

Tiered detection:
  Strict:      Hard-block. High-confidence, tightly constrained patterns.
  Contextual:  Block unless placeholder/example meta-language detected nearby.
  Broad:       Shadow telemetry only. No blocking.

Design: docs/plans/2026-02-18-codex-plugin-design.md

Note: registered for both PreToolUse and PostToolUse in hooks.json with
identical entries. This script dispatches on hook_event_name at runtime
(see main()). Both registrations must be updated together.

Exit codes:
  0  Allow (or all PostToolUse events)
  2  Block (PreToolUse only — credential detected or hook internal error)
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

try:
    from credential_scan import scan_text
except ModuleNotFoundError:
    from scripts.credential_scan import scan_text

# ---------------------------------------------------------------------------
# Log path
# ---------------------------------------------------------------------------

_LOG_PATH = Path.home() / ".claude" / ".codex-events.jsonl"


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _append_log(entry: dict) -> None:
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        print(f"codex-guard: log write failed: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


def handle_pre(data: dict) -> int:
    """PreToolUse handler: detect credentials and block if found."""
    tool_input = data.get("tool_input", {})
    prompt = tool_input.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = str(prompt)
    session_id = data.get("session_id", "unknown")
    tool = data.get("tool_name", "unknown")

    result = scan_text(prompt)
    if result.action == "block":
        _append_log({
            "ts": _ts(),
            "event": "block",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt),
            "reason": result.reason,
        })
        print(f"codex-guard: dispatch blocked ({result.reason})", file=sys.stderr)
        return 2

    if result.action == "shadow":
        _append_log({
            "ts": _ts(),
            "event": "shadow",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt),
            "reason": result.reason,
        })

    return 0


def handle_post(data: dict) -> int:
    """PostToolUse handler: log consultation event. Never blocks."""
    tool = data.get("tool_name", "unknown")
    session_id = data.get("session_id", "unknown")
    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response", {})

    prompt = tool_input.get("prompt", "") if isinstance(tool_input, dict) else ""
    result_text = ""
    if isinstance(tool_response, dict):
        result_text = str(tool_response.get("content", ""))
    elif isinstance(tool_response, str):
        result_text = tool_response

    thread_id_present = bool(
        (isinstance(tool_input, dict) and tool_input.get("threadId"))
        or (isinstance(tool_response, dict) and tool_response.get("threadId"))
        or (
            isinstance(tool_response, dict)
            and isinstance(tool_response.get("structuredContent"), dict)
            and tool_response["structuredContent"].get("threadId")
        )
    )

    _append_log(
        {
            "ts": _ts(),
            "event": "consultation",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt) if isinstance(prompt, str) else 0,
            "result_length": len(result_text),
            "thread_id_present": thread_id_present,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        # Cannot parse input — cannot determine event type.
        # Fail-closed: blocking is safer than silently allowing
        # a potentially dangerous PreToolUse through. PostToolUse
        # callers would also get exit 2, but Claude Code is unlikely
        # to send malformed JSON.
        print(f"codex-guard: failed to parse stdin ({e})", file=sys.stderr)
        return 2

    event = data.get("hook_event_name", "PreToolUse")

    try:
        if event == "PostToolUse":
            return handle_post(data)
        return handle_pre(data)
    except Exception as e:
        if event == "PostToolUse":
            return 0  # PostToolUse errors are always silent
        print(f"codex-guard: internal error (fail-closed): {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
