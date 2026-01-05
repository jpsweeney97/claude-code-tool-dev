#!/usr/bin/env python3
"""
Block creation of credential-related JSON files in .claude directory.

Catches files like:
  - .claude/credentials.json
  - .claude/oauth-tokens.json
  - .claude/auth.json
  - .claude/secrets.json

Allows:
  - .claude/settings.json
  - .claude/settings.local.json

Exit codes:
  0 - File path allowed
  2 - Credential-adjacent file blocked with feedback to Claude
"""
import json
import os
import re
import sys

# Match .claude/ directory (relative or absolute) with credential-related JSON files
CREDENTIAL_FILE_PATTERN = re.compile(
    r'(^|/)\.claude/[^/]*(credential|token|auth|secret|oauth|key)[^/]*\.json$',
    re.IGNORECASE
)

ALLOWED_BASENAMES = {
    'settings.json',
    'settings.local.json',
}

BLOCK_MESSAGE = """BLOCKED: Writing credential-adjacent JSON file

You attempted to create a JSON file in `.claude/` with a credential-related name.

Why this is blocked:
- Writing credentials to JSON files defeats secure storage
- Previous incident involved writing OAuth tokens to `.credentials.json`
- Credential files should never exist in plaintext

Allowed: settings.json, settings.local.json (but NOT adding apiKeyHelper without explicit user confirmation)

For auth issues: Run `claude /login` — don't create credential files."""


def get_file_path(tool_input: dict) -> str:
    """Extract file path from various tool input shapes."""
    # Write/Edit tool
    path = tool_input.get("file_path", "")
    if path:
        return path
    
    # MultiEdit: return first file path (all should be same file)
    edits = tool_input.get("edits", [])
    if edits:
        return edits[0].get("file_path", "")
    
    return ""


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        file_path = get_file_path(tool_input)
        
        if not file_path:
            sys.exit(0)
        
        # Normalize path for matching
        normalized = os.path.normpath(file_path)
        basename = os.path.basename(normalized)
        
        # Allow known-safe files
        if basename in ALLOWED_BASENAMES:
            sys.exit(0)
        
        # Block credential-adjacent files
        if CREDENTIAL_FILE_PATTERN.search(normalized):
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
