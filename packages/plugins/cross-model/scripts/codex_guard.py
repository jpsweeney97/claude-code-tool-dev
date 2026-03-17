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

import json
import sys
from dataclasses import dataclass

try:
    from credential_scan import scan_text
except ModuleNotFoundError:
    from scripts.credential_scan import scan_text

try:
    from event_log import ts as _ts, append_log as _raw_append_log
except ModuleNotFoundError:
    from scripts.event_log import ts as _ts, append_log as _raw_append_log


def _append_log(entry: dict) -> None:
    """Delegate to event_log.append_log, discarding the bool return.

    codex_guard callers expect None return (fire-and-forget).
    event_log.append_log returns bool. This wrapper preserves the
    original call-site semantics while gaining POSIX atomicity and
    0o600 permission enforcement.
    """
    _raw_append_log(entry)


_NODE_CAP = 10_000
_CHAR_CAP = 256 * 1024


@dataclass(frozen=True)
class ToolScanPolicy:
    """Controls which tool_input fields are scanned for egress secrets."""

    expected_fields: set[str]
    content_fields: set[str]
    scan_unknown_fields: bool = True


CODEX_POLICY = ToolScanPolicy(
    expected_fields={"sandbox", "approval-policy", "model", "profile"},
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)

CODEX_REPLY_POLICY = ToolScanPolicy(
    expected_fields={
        "sandbox",
        "approval-policy",
        "model",
        "profile",
        "threadId",
        "conversationId",
    },
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)


class ToolInputLimitExceeded(RuntimeError):
    """Raised when tool_input traversal exceeds configured safety caps."""


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


def _policy_for_tool(tool_name: str) -> ToolScanPolicy:
    if tool_name == "mcp__plugin_cross-model_codex__codex-reply":
        return CODEX_REPLY_POLICY
    return CODEX_POLICY


def _extract_strings(tool_input: dict, policy: ToolScanPolicy) -> tuple[list[str], list[str]]:
    """Extract string-bearing values selected by the scan policy."""

    if not isinstance(tool_input, dict):
        raise TypeError(f"tool_input must be dict. Got: {tool_input!r:.100}")

    texts_to_scan: list[str] = []
    unexpected_fields: list[str] = []
    seen_unexpected: set[str] = set()
    node_count = 0
    char_count = 0
    stack: list[tuple[object, bool, bool]] = [(tool_input, False, True)]

    while stack:
        value, scan_strings, is_root = stack.pop()
        node_count += 1
        if node_count > _NODE_CAP:
            raise ToolInputLimitExceeded("tool_input traversal failed: node cap exceeded")

        if isinstance(value, str):
            char_count += len(value)
            if char_count > _CHAR_CAP:
                raise ToolInputLimitExceeded("tool_input traversal failed: char cap exceeded")
            if scan_strings:
                texts_to_scan.append(value)
            continue

        if value is None or isinstance(value, (bool, int, float)):
            continue

        if isinstance(value, dict):
            for key, child in reversed(list(value.items())):
                child_scan = scan_strings
                if is_root:
                    if key in policy.content_fields:
                        child_scan = True
                    elif key in policy.expected_fields:
                        child_scan = False
                    else:
                        key_name = str(key)
                        if key_name not in seen_unexpected:
                            unexpected_fields.append(key_name)
                            seen_unexpected.add(key_name)
                        child_scan = policy.scan_unknown_fields
                stack.append((child, child_scan, False))
            continue

        if isinstance(value, (list, tuple)):
            for child in reversed(value):
                stack.append((child, scan_strings, False))
            continue

        if isinstance(value, (set, frozenset)):
            for child in value:
                stack.append((child, scan_strings, False))
            continue

        raise TypeError(f"tool_input traversal failed: unsupported value. Got: {value!r:.100}")

    return texts_to_scan, unexpected_fields


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

    for text in texts_to_scan:
        result = scan_text(text)
        if result.action == "block":
            return _log_block(tool, session_id, str(result.reason), scanned_chars)

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
