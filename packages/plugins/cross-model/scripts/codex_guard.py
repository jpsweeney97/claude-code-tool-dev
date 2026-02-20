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

Exit codes:
  0  Allow (or all PostToolUse events)
  2  Block (PreToolUse only — credential detected or hook internal error)
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------
# Tightened from packages/context-injection/context_injection/redact.py:
# - Word boundaries added to prevent substring matches
# - Minimum lengths raised (e.g., sk- now requires 40+ not 10+)
# - Ambiguous high-FP patterns moved to broad tier

# STRICT tier — hard-block. Near-zero false positive rate.
_STRICT: list[re.Pattern[str]] = [
    # AWS access key: exactly AKIA + 16 uppercase alphanumeric chars
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    # PEM private key block (any key type)
    re.compile(
        r"-----BEGIN\s+(?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
    ),
    # JWT token: 3 base64url segments each 10+ chars
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
]

# CONTEXTUAL tier — block unless placeholder suppression applies.
_CONTEXTUAL: list[re.Pattern[str]] = [
    # GitHub token prefixes + 36+ chars (raised from 10+ in redact.py)
    re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    # GitLab PAT
    re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
    # Stripe keys
    re.compile(r"\b(?:pk_live|pk_test)_[A-Za-z0-9]{24,}\b"),
    # OpenAI sk- key: 40+ chars (raised from 10+ to reduce discussion-text FPs)
    re.compile(r"\bsk-[A-Za-z0-9]{40,}\b"),
    # Bearer token in text (20+ char token value)
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    # URL userinfo: username:password@host
    re.compile(r"://[^@\s]+:[^@\s]{6,}@"),
]

# Words that indicate the match is in a discussion/example context, not a real credential.
_PLACEHOLDER_WORDS: frozenset[str] = frozenset(
    [
        "format",
        "example",
        "looks",
        "placeholder",
        "dummy",
        "sample",
        "suppose",
        "hypothetical",
        "redact",
        "redacted",
        "your-",
        "my-",
        "[redacted",
    ]
)

# BROAD tier — shadow telemetry only. No blocking. High FP rate.
_BROAD: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|"
        r"auth_token|private_key|client_secret)\s*[=:]\s*.{6,}"
    ),
]

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
# Detection helpers
# ---------------------------------------------------------------------------


def _has_placeholder_context(
    text: str, match_start: int, match_end: int, window: int = 100
) -> bool:
    """Return True if a placeholder/example word appears within `window` chars of the match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    context = text[start:end].lower()
    return any(word in context for word in _PLACEHOLDER_WORDS)


def _check_strict(prompt: str) -> str | None:
    """Return a reason string if a strict-tier pattern matches, else None."""
    for pat in _STRICT:
        if pat.search(prompt):
            return f"strict:{pat.pattern[:60]}"
    return None


def _check_contextual(prompt: str) -> str | None:
    """Return a reason string if any contextual-tier match lacks placeholder context."""
    for pat in _CONTEXTUAL:
        for m in pat.finditer(prompt):
            if not _has_placeholder_context(prompt, m.start(), m.end()):
                return f"contextual:{pat.pattern[:60]}"
    return None


def _broad_tag(prompt: str) -> str | None:
    """Return a tag if a broad-tier pattern matches (for shadow telemetry only)."""
    for pat in _BROAD:
        if pat.search(prompt):
            return f"broad:{pat.pattern[:60]}"
    return None


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

    reason = _check_strict(prompt) or _check_contextual(prompt)
    if reason:
        _append_log(
            {
                "ts": _ts(),
                "event": "block",
                "tool": tool,
                "session_id": session_id,
                "prompt_length": len(prompt),
                "reason": reason,
            }
        )
        print(f"codex-guard: dispatch blocked ({reason})", file=sys.stderr)
        return 2

    tag = _broad_tag(prompt)
    if tag:
        _append_log(
            {
                "ts": _ts(),
                "event": "shadow",
                "tool": tool,
                "session_id": session_id,
                "prompt_length": len(prompt),
                "reason": tag,
            }
        )

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
