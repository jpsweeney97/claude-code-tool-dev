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

## Option Ordering

All options must come **before** the server name:

```bash
claude mcp add [options] <name> -- <command> [args...]
```

| Position | Content |
|----------|---------|
| Options | `--transport`, `--env`, `--scope`, `--header` |
| Server name | Unique identifier |
| `--` | Separator (for stdio) |
| Command + args | Passed to MCP server |

Example:
```bash
claude mcp add --transport stdio --env KEY=value myserver -- python server.py --port 8080
```

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

**Migration**: If you have existing SSE servers, check if the provider offers an HTTP endpoint. Most modern MCP servers support HTTP, which provides better reliability and wider compatibility.

## Windows Users

On native Windows (not WSL), `npx` requires the `cmd /c` wrapper:

```bash
# Correct — Windows can execute cmd
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package

# Wrong — "Connection closed" error
claude mcp add --transport stdio my-server -- npx -y @some/package
```

Without `cmd /c`, Windows cannot directly execute `npx`.

## Key Points

- HTTP is recommended for remote servers
- stdio for local processes
- SSE is deprecated, migrate to HTTP
- Options must come before server name
- `--` separates server name from command/args
- Windows requires `cmd /c` wrapper for npx
