---
id: settings-attribution
topic: Attribution Settings
category: settings
tags: [attribution, git, commits, pull-requests, co-authored-by]
requires: [settings-overview]
related_to: [settings-schema, settings-examples]
official_docs: https://code.claude.com/en/settings#attribution-settings
---

# Attribution Settings

Customize attribution for git commits and pull requests.

## Configuration

```json
{
  "attribution": {
    "commit": "Generated with AI\n\nCo-Authored-By: AI <ai@example.com>",
    "pr": "Created with Claude Code"
  }
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `commit` | string | Attribution for git commits (including trailers) |
| `pr` | string | Attribution for pull request descriptions |

## Default Values

**Default commit attribution:**

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Default PR attribution:**

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Hiding Attribution

Set fields to empty strings to hide attribution:

```json
{
  "attribution": {
    "commit": "",
    "pr": ""
  }
}
```

## Custom Attribution Example

```json
{
  "attribution": {
    "commit": "AI-assisted development\n\nCo-Authored-By: Claude <claude@anthropic.com>",
    "pr": ""
  }
}
```

This shows custom commit attribution while hiding PR attribution.

## Deprecated: includeCoAuthoredBy

The `includeCoAuthoredBy` setting is deprecated. Use `attribution` instead.

```json
// Old (deprecated):
{ "includeCoAuthoredBy": false }

// New:
{ "attribution": { "commit": "", "pr": "" } }
```

The `attribution` setting takes precedence over `includeCoAuthoredBy`.

## Key Points

- Commits use git trailers (like `Co-Authored-By`) by default
- PR descriptions are plain text
- Empty string hides attribution for that type
- `attribution` replaces deprecated `includeCoAuthoredBy`
