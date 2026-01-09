---
id: agents-permissions
topic: Agent Permission Modes
category: agents
tags: [permissions, security, modes]
requires: [agents-overview, agents-frontmatter]
related_to: [settings-permissions]
official_docs: https://code.claude.com/en/sub-agents
---

# Agent Permission Modes

Agents support 6 permission modes that control tool access prompting.

## Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Prompt user on first use of each tool |
| `acceptEdits` | Auto-accept file edits (Read, Write, Edit) |
| `plan` | Analyze only, no modifications |
| `dontAsk` | Auto-deny unless pre-approved in settings |
| `bypassPermissions` | Skip all permission prompts |
| `ignore` | No permissions enforced |

## Mode Selection Guide

| Use Case | Recommended Mode |
|----------|------------------|
| General development | `default` |
| Code generation tasks | `acceptEdits` |
| Analysis and review | `plan` |
| Restricted agents | `dontAsk` |
| Trusted automation | `bypassPermissions` |
| Testing only | `ignore` |

## Configuration

Set in agent frontmatter:

```yaml
---
description: Security analyzer
permissionMode: plan
---
```

Or in settings.json for all agents:

```json
{
  "agentPermissionMode": "default"
}
```

## Key Points

- 6 modes from most to least restrictive
- `plan` is safest for analysis agents
- `bypassPermissions` for trusted automation
- Mode can be set per-agent or globally
