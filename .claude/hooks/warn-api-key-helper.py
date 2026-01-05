#!/usr/bin/env python3
"""
Require user confirmation for apiKeyHelper modifications in settings.json.

This is a security control tied to a previous credential exposure incident.
When detected, the user must explicitly approve the operation.

Exit codes:
  0 - Either not a settings.json edit, or outputs JSON to prompt user confirmation
"""
import json
import re
import sys

WARNING_MESSAGE = """⚠️ apiKeyHelper modification detected

This exact pattern caused a credential exposure incident.

Before approving, verify:
• Did you explicitly request this change?
• Is `claude /login` insufficient for this use case?
• apiKeyHelper expects API keys (sk-ant-api03-...), not OAuth tokens

If uncertain: Deny and discuss the approach first."""


def get_file_path(tool_input: dict) -> str:
    """Extract file path from various tool input shapes."""
    path = tool_input.get("file_path", "")
    if path:
        return path
    edits = tool_input.get("edits", [])
    if edits:
        return edits[0].get("file_path", "")
    return ""


def get_content(tool_input: dict) -> str:
    """Extract content from various tool input shapes."""
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
        tool_input = data.get("tool_input", {})
        
        file_path = get_file_path(tool_input)
        content = get_content(tool_input)
        
        # Only check settings.json files
        if not re.search(r'settings\.json$', file_path):
            sys.exit(0)
        
        # Check for apiKeyHelper
        if 'apiKeyHelper' not in content:
            sys.exit(0)
        
        # Require user confirmation via permission prompt
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": WARNING_MESSAGE
            }
        }
        print(json.dumps(output))
        sys.exit(0)
    
    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
