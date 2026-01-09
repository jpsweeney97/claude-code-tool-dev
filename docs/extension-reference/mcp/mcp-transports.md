---
id: mcp-transports
topic: MCP Transport Types
category: mcp
tags: [transports, http, sse, stdio]
requires: [mcp-overview]
related_to: [mcp-scopes]
official_docs: https://code.claude.com/en/mcp
---

# MCP Transport Types

MCP servers communicate via three transport types.

## Transport Comparison

| Transport | Command | Notes |
|-----------|---------|-------|
| **HTTP** | `claude mcp add --transport http <name> <url>` | Recommended for remote servers |
| **SSE** | `claude mcp add --transport sse <name> <url>` | Deprecated, use HTTP |
| **stdio** | `claude mcp add --transport stdio <name> -- <cmd>` | Local processes |

## HTTP Transport (Recommended)

```bash
# Basic HTTP server
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# HTTP with authentication headers
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer $TOKEN"
```

## stdio Transport

For local MCP server processes:

```bash
claude mcp add --transport stdio airtable \
  --env AIRTABLE_API_KEY=$KEY \
  -- npx -y airtable-mcp-server
```

## SSE Transport (Deprecated)

Server-Sent Events. Use HTTP instead for new servers.

```bash
claude mcp add --transport sse legacy-api https://api.legacy.com/mcp
```

## Key Points

- HTTP is recommended for remote servers
- stdio for local processes
- SSE is deprecated, migrate to HTTP
- Use --header for authentication
- Use --env for environment variables
