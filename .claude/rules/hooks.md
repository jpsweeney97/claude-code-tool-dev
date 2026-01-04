---
paths: .claude/hooks/**
---

# Hook Development

## Frontmatter Convention

Hooks use PEP 723-style frontmatter (our convention, not native Claude Code):

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60000
# ///
```

## Valid Events

- `PreToolUse` - Before tool execution (can block)
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - Before processing user input
- `Stop` - When session ends
- `SubagentStop` - When subagent completes
- `Notification` - On notifications
- `PermissionRequest` - On permission prompts
- `PreCompact` - Before context compaction
- `SessionStart` - When session begins
- `SessionEnd` - When session ends

## Workflow

1. Create `.claude/hooks/<name>.py` with frontmatter
2. Make executable: `chmod +x .claude/hooks/<name>.py`
3. Promote: `uv run scripts/promote hook <name>`
4. Sync: `uv run scripts/sync-settings`

## Important

Claude Code reads hooks from `settings.json`, not from files directly.
The `sync-settings` script generates the config from frontmatter.
