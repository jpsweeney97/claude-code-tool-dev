"""Shared safety primitives for cross-model consultation.

Extracted from codex_guard.py to serve both the PreToolUse hook and the
codex_consult.py adapter. This module owns:
- ToolScanPolicy: controls which tool_input fields are scanned
- extract_strings: policy-driven traversal of tool_input dicts
- Policy constants: START_POLICY, REPLY_POLICY

This module does NOT own:
- Hook dispatch logic (stays in codex_guard.py)
- Credential pattern matching (stays in credential_scan.py)
- Event logging (stays in event_log.py)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

if __package__:
    from scripts.credential_scan import scan_text
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from credential_scan import scan_text  # type: ignore[import-not-found,no-redef]

_NODE_CAP = 10_000
_CHAR_CAP = 256 * 1024


@dataclass(frozen=True)
class ToolScanPolicy:
    """Controls which tool_input fields are scanned for egress secrets."""

    expected_fields: set[str]
    content_fields: set[str]
    scan_unknown_fields: bool = True


class ToolInputLimitExceeded(RuntimeError):
    """Raised when tool_input traversal exceeds configured safety caps."""


START_POLICY = ToolScanPolicy(
    expected_fields={"sandbox", "approval-policy", "model", "profile"},
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)

REPLY_POLICY = ToolScanPolicy(
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


def policy_for_tool(tool_name: str) -> ToolScanPolicy:
    """Return the scan policy for a given MCP tool name."""
    if tool_name == "mcp__plugin_cross-model_codex__codex-reply":
        return REPLY_POLICY
    return START_POLICY


def extract_strings(tool_input: object, policy: ToolScanPolicy) -> tuple[list[str], list[str]]:
    """Extract string-bearing values selected by the scan policy.

    Returns (texts_to_scan, unexpected_fields).

    Traverses the tool_input dict. For root-level keys:
    - content_fields: scan all nested strings
    - expected_fields: skip (known safe structural fields)
    - unknown fields: scan if policy.scan_unknown_fields is True

    Raises TypeError if tool_input is not a dict.
    Raises ToolInputLimitExceeded if traversal exceeds node or char caps.
    """
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


_ACTION_RANK = {"block": 0, "shadow": 1, "allow": 2}
_TIER_RANK = {"strict": 0, "contextual": 1}


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of running credential scan on tool_input."""

    action: Literal["allow", "block", "shadow"]
    reason: str | None = None
    tier: str | None = None
    unexpected_fields: list[str] = field(default_factory=list)


def check_tool_input(tool_input: object, policy: ToolScanPolicy) -> SafetyVerdict:
    """Run credential scan on tool_input per policy. Returns worst verdict."""
    texts, unexpected = extract_strings(tool_input, policy)

    worst_action = "allow"
    worst_reason: str | None = None
    worst_tier: str | None = None

    for text in texts:
        result = scan_text(text)

        result_rank = _ACTION_RANK.get(result.action, 2)
        current_rank = _ACTION_RANK.get(worst_action, 2)

        if result_rank < current_rank:
            worst_action = result.action
            worst_reason = result.reason
            worst_tier = result.tier
        elif result_rank == current_rank and result.action == "block":
            if _TIER_RANK.get(result.tier or "", 99) < _TIER_RANK.get(worst_tier or "", 99):
                worst_reason = result.reason
                worst_tier = result.tier

    return SafetyVerdict(
        action=worst_action,
        reason=worst_reason,
        tier=worst_tier,
        unexpected_fields=unexpected,
    )
