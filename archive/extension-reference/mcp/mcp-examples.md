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

## Notion Integration

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

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

## Playwright Browser Testing

```bash
# Add Playwright MCP server
claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest

# Use
> "Test if the login flow works with test@example.com"
> "Take a screenshot of the checkout page on mobile"
> "Verify that the search feature returns results"
```

## Asana (SSE Transport - Deprecated)

```bash
# SSE transport is deprecated; use HTTP where available
claude mcp add --transport sse asana https://mcp.asana.com/sse
```

## Sentry Error Monitoring

```bash
# Add Sentry MCP server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# Authenticate
/mcp

# Use
> "What are the most common errors in the last 24 hours?"
> "Show me the stack trace for error ID abc123"
> "Which deployment introduced these new errors?"
```

## PostgreSQL Database

```bash
# Add database server with connection string
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
  --dsn "postgresql://readonly:pass@prod.db.com:5432/analytics"

# Use
> "What's our total revenue this month?"
> "Show me the schema for the orders table"
> "Find customers who haven't purchased in 90 days"
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

## Import from Claude Desktop

```bash
# Import servers from Claude Desktop
claude mcp add-from-claude-desktop

# Follow interactive prompts to select servers
claude mcp list
```

Notes:
- Works on macOS and WSL only
- Servers keep their original names
- Duplicate names get numerical suffix (e.g., `server_1`)
- Use `--scope user` for cross-project availability

## Add from JSON Configuration

```bash
# Basic syntax
claude mcp add-json <name> '<json>'

# HTTP server with headers
claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp","headers":{"Authorization":"Bearer token"}}'

# stdio server with args and env
claude mcp add-json local-weather '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"],"env":{"CACHE_DIR":"/tmp"}}'

# Verify
claude mcp get weather-api
```

Notes:
- Ensure JSON is properly escaped in your shell
- JSON must conform to MCP server configuration schema
- Use `--scope user` for cross-project availability

## Claude Code as MCP Server

Expose Claude Code's tools to other applications:

```bash
claude mcp serve
```

Add to Claude Desktop (`claude_desktop_config.json`):

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

**Important:** If `claude` is not in PATH, use full path:

```bash
# Find path
which claude

# Use in config
"command": "/full/path/to/claude"
```

Without correct path, you'll see `spawn claude ENOENT` error.

### Available Tools

The server provides access to Claude Code's tools: View, Edit, LS, and more.

In Claude Desktop, try asking Claude to read files in a directory, make edits, and more.

### Client Responsibility

This MCP server only exposes Claude Code's tools to your MCP client. Your own client is responsible for implementing user confirmation for individual tool calls.

## Key Points

- Notion, GitHub MCP for SaaS integrations
- Playwright for browser testing
- Sentry for error monitoring
- stdio for local database servers
- Project `.mcp.json` for team configuration
- `add-json` for direct JSON configuration
- Claude Code can serve as MCP server
- Import from Claude Desktop on macOS/WSL
