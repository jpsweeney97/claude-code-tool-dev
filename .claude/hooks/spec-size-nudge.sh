#!/bin/bash
# /// hook
# event: PostToolUse
# matcher: Write
# ///
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# Only check markdown files in docs/ or specs/ directories
case "$FILE_PATH" in
  */docs/*|*/specs/*) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.md) ;;
  *) exit 0 ;;
esac

LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')

if [ "$LINE_COUNT" -gt 500 ]; then
  cat <<EOF
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "This file ($FILE_PATH) is $LINE_COUNT lines. Files over 500 lines are difficult to reference in future conversations. Consider invoking the spec-writer skill to create a modular spec structure."}}
EOF
fi

exit 0
