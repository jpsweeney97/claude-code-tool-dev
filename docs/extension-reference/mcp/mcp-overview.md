---
id: mcp-overview
topic: MCP Servers Overview
category: mcp
tags: [mcp, servers, external, tools, apis]
related_to: [mcp-transports, mcp-scopes, mcp-authentication, mcp-resources, mcp-plugins]
official_docs: https://code.claude.com/en/mcp
---

# MCP Servers Overview

MCP (Model Context Protocol) servers connect Claude Code to external tools, databases, and APIs. They enable Claude to interact with services like GitHub, databases, monitoring systems, and custom tools.

## Use Cases

- **Issue trackers** — "Add the feature from JIRA issue ENG-4521 and create a PR on GitHub"
- **Monitoring** — "Check Sentry and Statsig for usage of feature ENG-4521"
- **Databases** — "Find emails of 10 users who used feature ENG-4521 from PostgreSQL"
- **Design tools** — "Update our email template based on new Figma designs"
- **Workflow automation** — "Create Gmail drafts inviting users to a feedback session"

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

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `MCP_TIMEOUT` | Server startup timeout in ms (e.g., `MCP_TIMEOUT=10000 claude`) |
| `MAX_MCP_OUTPUT_TOKENS` | Maximum output tokens (default: 25000) |

## Key Points

- Three transport types: HTTP, SSE (deprecated), stdio
- Three scopes: local, project, user
- OAuth authentication supported
- MCP resources via @ mentions
- MCP prompts as slash commands
- Plugins can bundle MCP servers (see mcp-plugins)
