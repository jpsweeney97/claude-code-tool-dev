#!/bin/bash
# Example PreToolUse hook for validating Bash commands
# This script demonstrates bash command validation patterns

set -euo pipefail

# Read input from stdin
input=$(cat)

# Validate JSON input
if ! echo "$input" | jq empty 2>/dev/null; then
  echo '{"continue": true, "systemMessage": "Hook received malformed JSON input, skipping validation"}' >&2
  exit 0
fi

# Extract command
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")

# Validate command exists
if [ -z "$command" ]; then
  echo '{"continue": true}' # No command to validate
  exit 0
fi

# Check for obviously safe commands (quick approval)
if [[ "$command" =~ ^(ls|pwd|echo|date|whoami)(\s|$) ]]; then
  exit 0
fi

# Check for destructive operations
if [[ "$command" == *"rm -rf"* ]] || [[ "$command" == *"rm -fr"* ]]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "deny"}, "systemMessage": "Dangerous command detected: rm -rf"}' >&2
  exit 2
fi

# Check for other dangerous commands
if [[ "$command" == *"dd if="* ]] || [[ "$command" == *"mkfs"* ]] || [[ "$command" == *"> /dev/"* ]]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "deny"}, "systemMessage": "Dangerous system operation detected"}' >&2
  exit 2
fi

# Check for privilege escalation
if [[ "$command" == sudo* ]] || [[ "$command" == su* ]]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "ask"}, "systemMessage": "Command requires elevated privileges"}' >&2
  exit 2
fi

# Approve the operation
exit 0
