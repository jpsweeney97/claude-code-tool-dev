---
id: security-managed
topic: Managed Settings Deployment
category: security
tags: [managed, enterprise, deployment, it]
related_to: [security-mcp-restrictions, security-marketplace-restrictions, settings-scopes]
official_docs: https://code.claude.com/en/iam
---

# Managed Settings Deployment

Managed settings enable IT/enterprise control over Claude Code configuration.

## Purpose

- Enforce organizational security policies
- Control available MCP servers
- Restrict marketplaces
- Disable dangerous features

## Managed Settings Locations

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Linux/WSL | `/etc/claude-code/managed-settings.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-settings.json` |

## Precedence

Managed settings:
- Cannot be overridden by users
- Take highest precedence
- Override all other configuration levels

## Common Restrictions

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  },
  "allowManagedHooksOnly": true,
  "strictKnownMarketplaces": []
}
```

## Key Points

- Managed settings deployed by IT
- Highest precedence, cannot be overridden
- Platform-specific locations
- Controls MCP, hooks, marketplaces, permissions
