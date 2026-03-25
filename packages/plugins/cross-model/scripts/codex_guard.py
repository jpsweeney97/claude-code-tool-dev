#!/usr/bin/env python3
"""
codex_guard.py — PreToolUse/PostToolUse enforcement hook for mcp__plugin_cross-model_codex__codex.

PreToolUse: Tiered credential detection on outbound Codex prompts.
  Blocks on strict/contextual tier matches.
  Logs shadow telemetry for broad-tier matches.
PostToolUse: Logs consultation event to ~/.claude/.codex-events.jsonl.

Fail-closed (PreToolUse only): any unhandled exception during hook execution
blocks the Codex call. PostToolUse errors log to stderr but never block.

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

import json
import sys

if __package__:
    from scripts.credential_scan import scan_text
    from scripts.event_log import ts as _ts, append_log as _raw_append_log
else:
    from credential_scan import scan_text  # type: ignore[import-not-found,no-redef]
    from event_log import ts as _ts, append_log as _raw_append_log  # type: ignore[import-not-found,no-redef]


def _append_log(entry: dict) -> None:
    """Delegate to event_log.append_log, discarding the bool return.

    codex_guard callers expect None return (fire-and-forget).
    event_log.append_log returns bool. This wrapper preserves the
    original call-site semantics while gaining POSIX atomicity and
    0o600 permission enforcement.

    Logs to stderr when a write fails, since block/shadow events on
    a security-enforcement path should surface audit trail failures.
    """
    if not _raw_append_log(entry):
        event_type = entry.get("event", "unknown")
        print(f"codex-guard: audit log write failed for {event_type}", file=sys.stderr)


if __package__:
    from scripts.consultation_safety import (
        ToolScanPolicy,
        ToolInputLimitExceeded,
        extract_strings as _extract_strings,
        START_POLICY as CODEX_POLICY,
        REPLY_POLICY as CODEX_REPLY_POLICY,
        policy_for_tool as _policy_for_tool,
        TIER_RANK,
    )
else:
    from consultation_safety import (  # type: ignore[import-not-found,no-redef]
        ToolScanPolicy,
        ToolInputLimitExceeded,
        extract_strings as _extract_strings,
        START_POLICY as CODEX_POLICY,
        REPLY_POLICY as CODEX_REPLY_POLICY,
        policy_for_tool as _policy_for_tool,
        TIER_RANK,
    )


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


def _log_block(tool: object, session_id: object, reason: str, prompt_length: int) -> int:
    _append_log({
        "ts": _ts(),
        "event": "block",
        "tool": tool,
        "session_id": session_id,
        "prompt_length": prompt_length,
        "reason": reason,
    })
    print(f"codex-guard: dispatch blocked ({reason})", file=sys.stderr)
    return 2


def handle_pre(data: dict) -> int:
    """PreToolUse handler: detect credentials and block if found."""
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "unknown")
    tool = data.get("tool_name", "unknown")
    policy = _policy_for_tool(str(tool))

    try:
        texts_to_scan, unexpected_fields = _extract_strings(tool_input, policy)
    except (ToolInputLimitExceeded, TypeError) as exc:
        return _log_block(tool, session_id, str(exc), 0)

    scanned_chars = sum(len(text) for text in texts_to_scan)

    if unexpected_fields:
        _append_log({
            "ts": _ts(),
            "event": "shadow",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": scanned_chars,
            "reason": "unexpected_fields",
            "unexpected_fields": unexpected_fields,
        })

    results = [scan_text(text) for text in texts_to_scan]

    blocks = [r for r in results if r.action == "block"]
    if blocks:
        best = min(blocks, key=lambda r: TIER_RANK.get(r.tier or "", 99))
        return _log_block(tool, session_id, str(best.reason), scanned_chars)

    for result in results:
        if result.action == "shadow":
            _append_log({
                "ts": _ts(),
                "event": "shadow",
                "tool": tool,
                "session_id": session_id,
                "prompt_length": scanned_chars,
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

    thread_id: str | None = None
    if isinstance(tool_input, dict) and tool_input.get("threadId"):
        thread_id = tool_input["threadId"]
    elif isinstance(tool_response, dict) and tool_response.get("threadId"):
        thread_id = tool_response["threadId"]
    elif (
        isinstance(tool_response, dict)
        and isinstance(tool_response.get("structuredContent"), dict)
        and tool_response["structuredContent"].get("threadId")
    ):
        thread_id = tool_response["structuredContent"]["threadId"]

    _append_log(
        {
            "ts": _ts(),
            "event": "consultation",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt) if isinstance(prompt, str) else 0,
            "result_length": len(result_text),
            "thread_id": thread_id,
        }
    )
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError, UnicodeDecodeError) as e:
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
            print(f"codex-guard: PostToolUse error (non-blocking): {e}", file=sys.stderr)
            return 0
        print(f"codex-guard: internal error (fail-closed): {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
