---
id: mcp-examples
topic: MCP Examples
category: mcp
tags: [examples, templates, patterns]
requires: [mcp-overview, mcp-transports, mcp-scopes]
official_docs: https://code.claude.com/en/mcp
---

# MCP Examples

Complete working MCP configurations.

## GitHub Integration

```bash
# Register GitHub MCP
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# Authenticate
/mcp
# Select "Authenticate" for github

# Use
@github:issue://123
/mcp__github__list_prs
```

## Local Database Server

```bash
# Register local Postgres MCP
claude mcp add --transport stdio postgres \
  --env DATABASE_URL=$DATABASE_URL \
  -- npx -y @anthropic/mcp-server-postgres
```

## Team Project Configuration

`.mcp.json` (committed to git):

```json
{
  "mcpServers": {
    "internal-api": {
      "type": "http",
      "url": "${API_URL:-https://api.internal.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    },
    "docs": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-docs", "./docs"]
    }
  }
}
```

## Claude Code as MCP Server

Expose Claude Code's tools to other applications:

```bash
claude mcp serve
```

Add to Claude Desktop:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"]
    }
  }
}
```

## Key Points

- GitHub MCP for repository operations
- stdio for local database servers
- Project .mcp.json for team configuration
- Claude Code can serve as MCP server
