---
id: mcp-scopes
topic: MCP Server Scopes
category: mcp
tags: [scopes, local, project, user, visibility]
requires: [mcp-overview]
related_to: [mcp-transports]
official_docs: https://code.claude.com/en/mcp
---

# MCP Server Scopes

MCP servers can be configured at three scope levels.

## Scope Reference

| Scope | Storage | Visibility |
|-------|---------|------------|
| **local** (default) | `~/.claude.json` (per-project) | You, this project only |
| **project** | `.mcp.json` | Team (committed to git) |
| **user** | `~/.claude.json` | You, all projects |

## Setting Scope

```bash
# Explicit scope
claude mcp add --transport http --scope user hubspot https://mcp.hubspot.com/anthropic

# Implicit local scope (default)
claude mcp add --transport http api https://api.example.com/mcp
```

## Environment Variable Expansion

In `.mcp.json`:

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

Supported syntax:
- `${VAR}` — Value of VAR
- `${VAR:-default}` — Value of VAR or default

## Key Points

- Local scope is default (project-specific, not committed)
- Project scope for team sharing (committed to git)
- User scope for personal tools across projects
- Environment variables expand in .mcp.json
