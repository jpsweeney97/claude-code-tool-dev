---
id: mcp-overview
topic: MCP Servers Overview
category: mcp
tags: [mcp, servers, external, tools, apis]
related_to: [mcp-transports, mcp-scopes, mcp-authentication]
official_docs: https://code.claude.com/en/mcp
---

# MCP Servers Overview

MCP (Model Context Protocol) servers connect Claude Code to external tools, databases, and APIs. They enable Claude to interact with services like GitHub, databases, monitoring systems, and custom tools.

## Purpose

- Connect to external services and APIs
- Access databases and data stores
- Integrate with development tools
- Use custom tool implementations

## Registration Commands

```bash
claude mcp add --transport http <name> <url>     # HTTP server
claude mcp add --transport stdio <name> -- <cmd> # Local process
claude mcp add-json <name> '<config>'            # From JSON
claude mcp add-from-claude-desktop               # Import from Desktop
```

## Management Commands

```bash
claude mcp list              # List all servers
claude mcp get <name>        # Details for specific server
claude mcp remove <name>     # Remove server
/mcp                         # Status and authentication
```

## Key Points

- Three transport types: HTTP, SSE (deprecated), stdio
- Three scopes: local, project, user
- OAuth authentication supported
- MCP resources via @ mentions
- MCP prompts as slash commands
