#!/usr/bin/env python3
"""
Block file writes and bash commands containing Anthropic credential patterns.

Handles:
  - Write tool: tool_input.content
  - Edit tool: tool_input.new_string
  - MultiEdit tool: tool_input.edits[].new_string
  - Bash tool: tool_input.command

Exit codes:
  0 - Allow (no credentials detected)
  2 - Block (credentials detected, message in stderr)
"""
import json
import re
import sys

CREDENTIAL_PATTERN = re.compile(r'sk-ant-(api|oat|sid)\d{2}-[A-Za-z0-9_-]+')

BLOCK_MESSAGE = """BLOCKED: Credential content detected

You attempted to write content containing an Anthropic credential token pattern (sk-ant-*).

Why this is blocked:
- OAuth tokens (sk-ant-oat*) should never be written to files
- API keys (sk-ant-api*) should be in environment variables or secure storage
- Session IDs (sk-ant-sid*) are ephemeral and shouldn't be persisted

Correct approach: Use environment variables or Claude Code's native authentication.
Run `claude /login` for authentication — don't store credentials in files."""


def get_content(tool_input: dict, tool_name: str) -> str:
    """Extract content to check based on tool type."""
    if tool_name == "Bash":
        return tool_input.get("command", "")

    # Write tool
    content = tool_input.get("content", "")
    if content:
        return content

    # Edit tool
    content = tool_input.get("new_string", "")
    if content:
        return content

    # MultiEdit tool
    edits = tool_input.get("edits", [])
    if edits:
        return " ".join(e.get("new_string", "") for e in edits)

    return ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        content = get_content(tool_input, tool_name)

        if CREDENTIAL_PATTERN.search(content):
            print(BLOCK_MESSAGE, file=sys.stderr)
            sys.exit(2)

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
