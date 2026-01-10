---
id: mcp-scopes
topic: MCP Server Scopes
category: mcp
tags: [scopes, local, project, user, visibility, precedence]
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

## Legacy Scope Names

| Current | Previous (older versions) |
|---------|---------------------------|
| `local` | `project` |
| `user` | `global` |

## Choosing the Right Scope

| Scope | Best For |
|-------|----------|
| **local** | Personal servers, experimental configs, sensitive credentials specific to one project |
| **project** | Team-shared servers, project-specific tools, services required for collaboration |
| **user** | Personal utilities across projects, dev tools, frequently used services |

## Scope Precedence

When servers with the same name exist at multiple scopes:

```
local > project > user
```

Local-scoped servers override project-scoped, which override user-scoped.

## Setting Scope

```bash
# Explicit scope
claude mcp add --transport http --scope user hubspot https://mcp.hubspot.com/anthropic

# Implicit local scope (default)
claude mcp add --transport http api https://api.example.com/mcp
```

## Project Scope Security

Claude Code prompts for approval before using project-scoped servers from `.mcp.json` files.

To reset approval choices:
```bash
claude mcp reset-project-choices
```

## Environment Variable Expansion

In `.mcp.json`:

### HTTP Server Example

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

### stdio Server Example

```json
{
  "mcpServers": {
    "shared-server": {
      "command": "/path/to/server",
      "args": ["--config", "${CONFIG_PATH}"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### Syntax

| Pattern | Behavior |
|---------|----------|
| `${VAR}` | Value of VAR (fails if unset) |
| `${VAR:-default}` | Value of VAR or default |

**Important:** If a required environment variable is not set and has no default value, Claude Code will fail to parse the config.

### Expansion Locations

Variables expand in these fields:
- `command` — Server executable path
- `args` — Command-line arguments
- `env` — Environment variables passed to server
- `url` — For HTTP server types
- `headers` — For HTTP server authentication

## Storage Locations

| Scope | Storage |
|-------|---------|
| User and local | `~/.claude.json` (in `mcpServers` field or under project paths) |
| Project | `.mcp.json` in project root (checked into source control) |
| Managed | `managed-mcp.json` in system directories (see mcp-managed) |

## Key Points

- Local scope is default (project-specific, not committed)
- Project scope for team sharing (committed to git)
- User scope for personal tools across projects
- Precedence: local > project > user
- Project scope requires approval (security)
- Environment variables expand in command, args, env, url, headers
