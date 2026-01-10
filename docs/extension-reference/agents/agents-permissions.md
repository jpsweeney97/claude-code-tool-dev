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

Agents support 5 permission modes that control tool access prompting.

## Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Prompt user on first use of each tool |
| `acceptEdits` | Auto-accept file edits (Read, Write, Edit) |
| `plan` | Analyze only, no modifications |
| `dontAsk` | Auto-deny unless pre-approved in settings |
| `bypassPermissions` | Skip all permission prompts |

**Warning:** `bypassPermissions` skips all permission checks. Use only for trusted automation.

If the parent conversation uses `bypassPermissions`, agents inherit this and cannot override it.

## Mode Selection Guide

| Use Case | Recommended Mode |
|----------|------------------|
| General development | `default` |
| Code generation tasks | `acceptEdits` |
| Analysis and review | `plan` |
| Restricted agents | `dontAsk` |
| Trusted automation | `bypassPermissions` |

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

- 5 modes from most to least restrictive
- `plan` is safest for analysis agents
- `bypassPermissions` skips all checks — use with caution
- Parent's `bypassPermissions` cannot be overridden
- Mode can be set per-agent or globally

See [IAM documentation](/en/iam#tool-specific-permission-rules) for advanced permission rules.
