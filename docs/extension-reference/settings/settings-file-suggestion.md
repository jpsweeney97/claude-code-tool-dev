---
id: settings-file-suggestion
topic: File Suggestion Settings
category: settings
tags: [file-suggestion, autocomplete, file-picker, gitignore]
requires: [settings-overview]
related_to: [settings-schema, hooks-overview]
official_docs: https://code.claude.com/en/settings#file-suggestion-settings
---

# File Suggestion Settings

Configure custom file path autocomplete for `@` mentions.

## fileSuggestion

Replace built-in file suggestion with a custom command.

```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  }
}
```

**When to use:** Large monorepos may benefit from project-specific indexing.

### Input Format

The command receives JSON via stdin:

```json
{ "query": "src/comp" }
```

### Output Format

Return newline-separated file paths to stdout (limit: 15):

```
src/components/Button.tsx
src/components/Modal.tsx
src/components/Form.tsx
```

### Environment Variables

The command runs with the same environment as hooks, including:
- `CLAUDE_PROJECT_DIR` — Project root directory

### Example Script

```bash
#!/bin/bash
query=$(cat | jq -r '.query')
your-repo-file-index --query "$query" | head -20
```

## respectGitignore

Control whether file picker respects `.gitignore` patterns.

```json
{
  "respectGitignore": false
}
```

| Value | Behavior |
|-------|----------|
| `true` (default) | Files matching `.gitignore` excluded from suggestions |
| `false` | All files shown in suggestions |

## Complete Example

```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  },
  "respectGitignore": true
}
```

## Key Points

- Built-in uses fast filesystem traversal
- Custom commands useful for pre-built indexes
- Input via stdin, output via stdout
- Max 15 suggestions displayed
- `respectGitignore` controls `.gitignore` filtering
