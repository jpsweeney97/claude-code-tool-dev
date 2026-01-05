#!/usr/bin/env python3
"""
Block macOS Keychain credential extraction commands.

Catches:
  - security find-generic-password
  - security find-internet-password
  - security dump-keychain
  - security export
  - Subshell evasion attempts (bash -c "security ...")

Exit codes:
  0 - Allow (no keychain extraction detected)
  2 - Block (keychain extraction blocked, message in stderr)
"""
import json
import re
import sys

# Patterns that access/export keychain credentials
KEYCHAIN_PATTERNS = [
    # Direct security command usage
    r'security\s+(find-generic-password|find-internet-password|dump-keychain|export)',
    # Subshell evasion attempts
    r'(bash|sh|zsh)\s+(-c\s+["\'].*)?security\s+(find-|dump-|export)',
]

COMBINED_PATTERN = re.compile('|'.join(KEYCHAIN_PATTERNS))

BLOCK_MESSAGE = """BLOCKED: Keychain credential extraction

You attempted to extract credentials from macOS Keychain. This is blocked because:

1. Credential exposure risk — Output would appear in conversation transcript
2. Wrong approach — Credentials in Keychain should stay there
3. Previous incident — This exact pattern caused a credential exposure

If authenticating in a container:
- Run `claude /login` inside the container
- Linux Claude Code has its own file-based auth
- Browser OAuth works via VS Code port forwarding
- Credentials persist if `~/.claude` is bind-mounted

Never bridge macOS Keychain to container environments."""


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        if COMBINED_PATTERN.search(command):
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
