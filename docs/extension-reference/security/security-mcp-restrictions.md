---
id: security-mcp-restrictions
topic: MCP Server Restrictions
category: security
tags: [mcp, restrictions, allowlist, denylist]
requires: [security-managed]
related_to: [mcp-managed, mcp-overview]
official_docs: https://code.claude.com/en/iam
---

# MCP Server Restrictions

Control which MCP servers users can access.

## Option 1: Exclusive Control

`managed-mcp.json` provides complete control:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "company-internal": {
      "type": "stdio",
      "command": "/usr/local/bin/company-mcp-server"
    }
  }
}
```

Users cannot add other MCP servers.

## Option 2: Allowlist/Denylist

In `managed-settings.json`:

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverCommand": ["npx", "-y", "approved-package"] },
    { "serverUrl": "https://mcp.company.com/*" }
  ],
  "deniedMcpServers": [
    { "serverName": "dangerous-server" },
    { "serverUrl": "https://*.untrusted.com/*" }
  ]
}
```

## Allowlist Behavior

| `allowedMcpServers` Value | Behavior |
|---------------------------|----------|
| `undefined` | No restrictions |
| `[]` | All additions blocked |
| `[entries...]` | Only matching servers allowed |

## Key Points

- managed-mcp.json for exclusive control
- allowedMcpServers for allowlist
- deniedMcpServers for denylist
- Deny always wins over allow
- Glob patterns supported in URLs
