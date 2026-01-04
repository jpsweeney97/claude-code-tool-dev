---
paths: .claude/commands/**
---

# Command Development

## Structure

Commands are markdown files:
```
.claude/commands/<name>.md
```

## Format

```markdown
---
description: Shown in command list
allowed-tools: ["Tool1"]  # Optional
---

Command template or instructions...

$ARGUMENTS will be replaced with user input after the command.
```

## Workflow

1. Create `.claude/commands/<name>.md`
2. Test with `/<name>` in this project
3. Promote: `uv run scripts/promote command <name>`
