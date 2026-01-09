---
id: mcp-managed
topic: Managed MCP Configuration
category: mcp
tags: [managed, enterprise, restrictions, security]
requires: [mcp-overview]
related_to: [security-mcp-restrictions, settings-scopes]
official_docs: https://code.claude.com/en/mcp
---

# Managed MCP Configuration

Enterprise deployments can control MCP server access via managed settings.

## Managed MCP File

`/Library/Application Support/ClaudeCode/managed-mcp.json`:

```json
{
  "required-server": {
    "type": "http",
    "url": "https://internal.company.com/mcp"
  }
}
```

Servers defined here:
- Automatically available to all users
- Cannot be removed by users
- Pre-authenticated if configured

## Allowlist Restrictions

In `managed-settings.json`:

```json
{
  "allowedMcpServers": ["internal-api", "approved-server"]
}
```

Only listed servers can be added.

## Denylist Restrictions

```json
{
  "deniedMcpServers": ["external-api", "untrusted-*"]
}
```

Listed servers are blocked. Supports glob patterns.

## Combined Restrictions

```json
{
  "allowedMcpServers": ["internal-*"],
  "deniedMcpServers": ["internal-legacy"]
}
```

Deny always takes precedence over allow.

## Key Points

- managed-mcp.json for required servers
- allowedMcpServers for whitelist
- deniedMcpServers for blacklist
- Deny overrides allow
- Glob patterns supported
