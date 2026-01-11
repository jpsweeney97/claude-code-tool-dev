---
id: security-managed
topic: Managed Settings Deployment
category: security
tags: [managed, enterprise, deployment, it]
related_to: [security-mcp-restrictions, security-marketplace-restrictions, security-hooks-restrictions, settings-scopes]
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

## MCP Server Restrictions

Control which MCP servers users can enable:

| Setting | Purpose |
|---------|---------|
| `allowedMcpServers` | Allowlist of permitted servers |
| `blockedMcpServers` | Denylist of prohibited servers |

### Allowlist Configuration

```json
{
  "allowedMcpServers": ["filesystem", "github", "custom-server"]
}
```

When set, only listed servers can be enabled. Empty array blocks all MCP servers.

### Denylist Configuration

```json
{
  "blockedMcpServers": ["dangerous-server"]
}
```

Blocked servers cannot be enabled regardless of other settings.

### Interaction

| Scenario | Result |
|----------|--------|
| Server in allowlist | Can be enabled |
| Server in blocklist | Cannot be enabled |
| Server in both | Cannot be enabled (blocklist wins) |
| No allowlist set | All non-blocked servers allowed |

## Hook Restrictions

Control hook execution in managed environments:

| Setting | Effect |
|---------|--------|
| `allowManagedHooksOnly` | Only run hooks from managed config |
| `disableHooks` | Disable all hook execution |
| `allowedHookEvents` | Limit which events can trigger hooks |
| `hookTimeout` | Maximum hook execution time (ms) |

### Disable All Hooks

```json
{
  "disableHooks": true
}
```

### Managed Hooks Only

```json
{
  "allowManagedHooksOnly": true,
  "hooks": {
    "PreToolUse": [
      { "command": "/usr/local/bin/audit-hook", "matcher": "Bash" }
    ]
  }
}
```

User-defined hooks are ignored; only managed hooks execute.

### Restrict Hook Events

```json
{
  "allowedHookEvents": ["SessionStart", "SessionEnd"]
}
```

Only specified events can trigger hooks.

## Marketplace Restrictions

See [marketplaces-restrictions](../marketplaces/marketplaces-restrictions.md) for detailed allowlist configuration using `strictKnownMarketplaces`.

### Quick Reference

| Setting | Effect |
|---------|--------|
| Not set | All marketplaces allowed |
| Empty array `[]` | All marketplace additions blocked |
| List of sources | Only listed marketplaces allowed |

## Deployment

Deploy managed settings via configuration management:

| Tool | Example |
|------|---------|
| macOS MDM | Jamf, Kandji, Mosyle |
| Windows | Group Policy, Intune |
| Linux | Ansible, Chef, Puppet |

## Key Points

- Managed settings deployed by IT
- Highest precedence, cannot be overridden
- Platform-specific locations
- Controls MCP, hooks, marketplaces, permissions
