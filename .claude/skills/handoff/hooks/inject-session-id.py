#!/usr/bin/env python3
"""
PreToolUse hook for Skill tool - injects session ID for handoff skill.

When the handoff or resume skill is invoked, this hook adds the session ID
to Claude's context via additionalContext, making it available for use in
handoff frontmatter and state file paths.
"""

import json
import sys


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 1

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "")

    # Only process Skill tool calls
    if tool_name != "Skill":
        return 0

    # Only inject for handoff-related skills
    skill_name = tool_input.get("skill", "")
    if skill_name not in ("handoff", "resume"):
        return 0

    # Inject session ID as additional context
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"Session ID: {session_id}",
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
