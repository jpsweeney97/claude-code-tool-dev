---
paths: .claude/agents/**
---

# Agent Development

## Structure

Agents are markdown files:
```
.claude/agents/<name>.md
```

## Format

```markdown
---
description: Agent description for selection
allowed-tools: ["Tool1", "Tool2"]  # Tools this agent can use
---

Agent system prompt and instructions...
```

## Workflow

1. Create `.claude/agents/<name>.md`
2. Test via Task tool with `subagent_type: <name>`
3. Promote: `uv run scripts/promote agent <name>`
