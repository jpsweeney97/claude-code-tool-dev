---
id: commands-mcp
topic: MCP Slash Commands
category: commands
tags: [commands, mcp, servers, prompts]
requires: [commands-overview]
related_to: [mcp-overview]
official_docs: https://code.claude.com/en/slash-commands
---

# MCP Slash Commands

MCP servers can expose prompts as slash commands dynamically discovered by Claude Code.

## Command Format

```
/mcp__<server-name>__<prompt-name> [arguments]
```

Examples:

```bash
# Without arguments
/mcp__github__list_prs

# With arguments
/mcp__github__pr_review 456
/mcp__jira__create_issue "Bug title" high
```

## Dynamic Discovery

MCP commands are automatically available when:

1. An MCP server is connected and active
2. The server exposes prompts through the MCP protocol
3. The prompts are successfully retrieved during connection

## Naming Conventions

Server and prompt names are normalized:

- Spaces and special characters become underscores
- Names are lowercase for consistency

## Managing MCP Connections

Use the `/mcp` command to:

- View all configured MCP servers
- Check connection status
- Authenticate with OAuth-enabled servers
- Clear authentication tokens
- View available tools and prompts from each server

## MCP Permissions and Wildcards

To approve all tools from an MCP server:

```bash
# Server name alone (approves all tools)
mcp__github

# Wildcard syntax (also approves all tools)
mcp__github__*
```

To approve specific tools:

```bash
mcp__github__get_issue
mcp__github__list_issues
```

See [MCP permission rules](https://code.claude.com/en/iam#tool-specific-permission-rules) for more details.

## Key Points

- Format: `/mcp__<server>__<prompt>`
- Dynamically discovered from connected servers
- Arguments defined by the MCP server
- Server/prompt names normalized to lowercase with underscores
- Use `/mcp` to manage connections and view available prompts
