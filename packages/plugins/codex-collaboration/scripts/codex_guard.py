#!/usr/bin/env python3
"""PreToolUse hook: fail-closed credential scanning on codex-collaboration tool args.

Reads JSON from stdin with {tool_name, tool_input}.
Exit 0 = allow, exit 2 = block (reason on stderr).

Claude Code ignores stdout on exit 2. All feedback goes to stderr,
which Claude Code feeds back to Claude as an error message.

Only scans tools with the codex-collaboration MCP prefix. Other tools pass through.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add package root to sys.path for server imports
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

_TOOL_PREFIX = "mcp__plugin_codex-collaboration_codex-collaboration__"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError, UnicodeDecodeError) as e:
        # Cannot parse input — fail closed.
        print(f"codex-guard: failed to parse stdin ({e})", file=sys.stderr)
        return 2

    tool_name = data.get("tool_name", "")
    if not isinstance(tool_name, str) or not tool_name.startswith(_TOOL_PREFIX):
        return 0  # Not our tool — pass through

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        # Plugin tool with missing/malformed input — fail closed.
        print("codex-guard: missing or invalid tool_input", file=sys.stderr)
        return 2

    # Status tool has no user content — always allow
    if tool_name == f"{_TOOL_PREFIX}codex.status":
        return 0

    from server.consultation_safety import check_tool_input, policy_for_tool

    try:
        policy = policy_for_tool(tool_name)
        verdict = check_tool_input(tool_input, policy)
    except Exception as e:
        # Safety module error — fail closed.
        print(f"codex-guard: internal error ({e})", file=sys.stderr)
        return 2

    if verdict.action == "block":
        print(
            f"codex-guard: credential detected ({verdict.reason}). "
            "Remove the secret before retrying.",
            file=sys.stderr,
        )
        return 2

    return 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("codex-guard: interrupted", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    run()
