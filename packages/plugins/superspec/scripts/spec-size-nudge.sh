#!/bin/bash

# Require jq — emit diagnostic to stderr (visible with --debug)
if ! command -v jq &>/dev/null; then
  echo "spec-size-nudge: jq not found, skipping" >&2
  exit 0
fi

INPUT=$(cat)

FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check markdown files in docs/ or specs/ directories
case "$FILE_PATH" in
  */docs/*|*/specs/*) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.md) ;;
  *) exit 0 ;;
esac

CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.content // empty')
if [ -z "$CONTENT" ]; then
  exit 0
fi

# printf '%s' avoids echo's trailing newline inflating the count
LINE_COUNT=$(printf '%s' "$CONTENT" | wc -l | tr -d ' ')

if [ "$LINE_COUNT" -gt 3000 ]; then
  # Use jq to construct JSON safely (handles special chars in FILE_PATH)
  jq -n --arg path "$FILE_PATH" --arg count "$LINE_COUNT" \
    '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": ("This file (" + $path + ") is " + $count + " lines. Files over 3000 lines are difficult to reference in future conversations. Consider invoking /superspec:spec-writer to create a modular spec structure.")}}'
fi

exit 0
