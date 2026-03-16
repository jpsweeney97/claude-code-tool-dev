---
module: hook
status: active
normative: true
authority: hook
---

# PostToolUse Hook

A lightweight passive safety net. Not the primary trigger for the spec-writing skill — the primary trigger is explicit user invocation or the brainstorming skill's handoff.

## Behavior

A `PostToolUse` hook on `Write` that checks if the written file is a markdown document in `docs/` or `specs/` directories exceeding 500 lines. If so, it injects a soft nudge into Claude's context suggesting the spec-writing skill.

## Hook Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/spec-size-nudge.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Script

```bash
#!/bin/bash
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
```

## Design Decisions

- **`additionalContext`, not `decision: "block"`:** The nudge is informational, not corrective. It doesn't block the write — the file is already written successfully. It suggests an action Claude may or may not take.
- **Only `docs/` and `specs/` directories:** Avoids false positives on generated files, changelogs, or other legitimately large markdown files.
- **Only `.md` files:** The skill operates on markdown specs, not code or data files.
- **500-line threshold:** Matches the brainstorming skill's observation that specs above this size benefit from modularization. Conservative enough to avoid noise.
- **No state tracking:** The hook fires every time a large file is written. Repeated nudges for the same file are acceptable — the user can ignore them.
