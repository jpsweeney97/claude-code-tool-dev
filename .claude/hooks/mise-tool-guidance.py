#!/usr/bin/env python3
"""
PreToolUse hook: Provides guidance when Claude attempts tool installations.
Reminds Claude to check mise config before installing tools.

Exit codes:
  0 - Allow (stdout guidance shown in verbose mode)
  2 - Block (tool is managed by mise, use mise install instead)
"""
import json
import re
import sys
import tomllib
from pathlib import Path

MISE_CONFIG = Path.home() / ".config/mise/config.toml"

# Exceptions - tools managed outside mise
EXCEPTIONS = {"pgcli"}  # Needs pipx inject for psycopg-binary


def load_mise_tools() -> set[str]:
    """Load tool names from mise config. Returns empty set on error (fail open)."""
    try:
        with open(MISE_CONFIG, "rb") as f:
            config = tomllib.load(f)

        tools = set()
        for key in config.get("tools", {}):
            # Strip backend prefix: "pipx:ruff" -> "ruff", "cargo:just" -> "just"
            tool_name = key.split(":")[-1]
            tools.add(tool_name)
        return tools
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return set()  # Fail open — don't block if config is missing/malformed


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        # Patterns that suggest tool installation
        install_patterns = [
            (r"pipx\s+install\s+(\S+)", "pipx"),
            (r"cargo\s+install\s+(\S+)", "cargo"),
            (r"go\s+install\s+(\S+)", "go"),
        ]

        mise_managed = load_mise_tools()

        for pattern, installer in install_patterns:
            match = re.search(pattern, command)
            if match:
                tool_name = match.group(1).split("/")[-1].split("@")[0]

                if tool_name in EXCEPTIONS:
                    continue

                if tool_name in mise_managed:
                    print(
                        f"'{tool_name}' is managed by mise. "
                        f"Run `mise install` instead of `{installer} install`.",
                        file=sys.stderr
                    )
                    sys.exit(2)
                else:
                    # Not in mise - provide guidance but allow
                    # stdout with exit 0 = shown in verbose mode (ctrl+o)
                    print(
                        f"Note: Consider adding '{tool_name}' to "
                        f"~/.config/mise/config.toml if this is a dev tool "
                        f"you'll use across projects."
                    )
                    sys.exit(0)

        # No installation detected
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
