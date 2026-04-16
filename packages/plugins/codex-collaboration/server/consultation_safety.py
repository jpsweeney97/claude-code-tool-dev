"""Tool-input safety policy for codex-collaboration advisory flows.

Policy-driven traversal and credential scanning of MCP tool arguments.
The hook guard (codex_guard.py) calls this module to validate raw tool
input before the MCP server processes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .credential_scan import scan_text
from .secret_taxonomy import Tier

_NODE_CAP = 10_000
_CHAR_CAP = 256 * 1024


@dataclass(frozen=True)
class ToolScanPolicy:
    """Controls which tool_input fields are scanned for egress secrets."""

    expected_fields: frozenset[str]
    content_fields: frozenset[str]
    scan_unknown_fields: bool = True


class ToolInputLimitExceeded(RuntimeError):
    """Raised when tool_input traversal exceeds configured safety caps."""


CONSULT_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"repo_root", "explicit_paths"}),
    content_fields=frozenset({"objective", "profile"}),
)

DIALOGUE_START_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"repo_root", "posture", "turn_budget"}),
    content_fields=frozenset({"profile"}),
)

DIALOGUE_REPLY_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"collaboration_id", "explicit_paths"}),
    content_fields=frozenset({"objective"}),
    # Reply schema: collaboration_id, objective, explicit_paths.
    # No profile (stored on handle), no repo_root.
)

_TOOL_POLICY_MAP: dict[str, ToolScanPolicy] = {
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult": CONSULT_POLICY,
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.start": DIALOGUE_START_POLICY,
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply": DIALOGUE_REPLY_POLICY,
}


def policy_for_tool(tool_name: str) -> ToolScanPolicy:
    """Return the scan policy for a given MCP tool name."""
    return _TOOL_POLICY_MAP[tool_name]


def extract_strings(
    tool_input: object, policy: ToolScanPolicy
) -> tuple[list[str], tuple[str, ...]]:
    """Extract string-bearing values selected by the scan policy.

    Returns (texts_to_scan, unexpected_fields).
    Raises ToolInputLimitExceeded if traversal exceeds caps.
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
            raise ToolInputLimitExceeded(
                "tool_input traversal failed: node cap exceeded"
            )

        if isinstance(value, str):
            char_count += len(value)
            if char_count > _CHAR_CAP:
                raise ToolInputLimitExceeded(
                    "tool_input traversal failed: char cap exceeded"
                )
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

        raise TypeError(
            f"tool_input traversal failed: unsupported value. Got: {value!r:.100}"
        )

    return texts_to_scan, tuple(unexpected_fields)


_ACTION_RANK = {"block": 0, "shadow": 1, "allow": 2}
TIER_RANK = {"strict": 0, "contextual": 1}


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of running credential scan on tool_input."""

    action: Literal["allow", "block", "shadow"]
    reason: str | None = None
    tier: Tier | None = None
    unexpected_fields: tuple[str, ...] = ()


def check_tool_input(tool_input: object, policy: ToolScanPolicy) -> SafetyVerdict:
    """Run credential scan on tool_input per policy. Returns worst verdict."""
    texts, unexpected = extract_strings(tool_input, policy)

    worst_action = "allow"
    worst_reason: str | None = None
    worst_tier: Tier | None = None

    for text in texts:
        result = scan_text(text)
        result_rank = _ACTION_RANK.get(result.action, 2)
        current_rank = _ACTION_RANK.get(worst_action, 2)

        if result_rank < current_rank:
            worst_action = result.action
            worst_reason = result.reason
            worst_tier = result.tier
        elif result_rank == current_rank and result.action == "block":
            if TIER_RANK.get(result.tier or "", 99) < TIER_RANK.get(
                worst_tier or "", 99
            ):
                worst_reason = result.reason
                worst_tier = result.tier

    return SafetyVerdict(
        action=worst_action,
        reason=worst_reason,
        tier=worst_tier,
        unexpected_fields=unexpected,
    )
