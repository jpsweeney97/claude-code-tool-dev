#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Edit|Write
# timeout: 5
# ///
"""
Block Edit/Write operations to ~/.claude/ while working in the dev repo.

This prevents accidental modification of production Claude Code configuration
while developing extensions in the tool-dev repo.

Exit codes:
  0 - Allow (not targeting ~/.claude/)
  2 - Block (file is in ~/.claude/)
"""
import json
import os
import sys
from pathlib import Path


def get_production_claude_dir() -> Path:
    """Get the expanded path to ~/.claude/."""
    return Path.home() / ".claude"


def is_production_path(file_path: str) -> bool:
    """Check if file_path is within ~/.claude/.

    Handles both:
    - Literal tilde: ~/.claude/settings.json
    - Expanded path: /Users/name/.claude/settings.json
    """
    if not file_path:
        return False

    # Expand tilde if present
    expanded = os.path.expanduser(file_path)
    path = Path(expanded).resolve()
    production_dir = get_production_claude_dir().resolve()

    try:
        path.relative_to(production_dir)
        return True
    except ValueError:
        return False


BLOCK_MESSAGE = """Cannot edit production Claude configuration from dev repo.

You're trying to edit a file in ~/.claude/ while working in the tool-dev repo.
This is blocked to prevent accidental modification of your production config.

Options:
  1. Work on the file in .claude/ (this repo's dev copy)
  2. Use 'uv run scripts/promote' to deploy tested changes
  3. Open a separate session in ~/.claude/ if you need direct edits

Target: {file_path}"""


def main() -> None:
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only check Edit and Write tools
        if tool_name not in ("Edit", "Write"):
            sys.exit(0)

        file_path = tool_input.get("file_path", "")

        if is_production_path(file_path):
            print(BLOCK_MESSAGE.format(file_path=file_path), file=sys.stderr)
            sys.exit(2)

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
