---
id: mcp-resources
topic: MCP Resources and Prompts
category: mcp
tags: [resources, prompts, mentions, commands]
requires: [mcp-overview]
related_to: [mcp-authentication]
official_docs: https://code.claude.com/en/mcp
---

# MCP Resources and Prompts

MCP servers expose resources for @ mentions and prompts as slash commands.

## MCP Resources

Reference MCP resources with @ mentions:

```
@github:issue://123
@postgres:schema://users
@docs:file://api/authentication
```

Format: `@<server>:<resource-type>://<identifier>`

Multiple resources in a single prompt:
```
> Compare @postgres:schema://users with @docs:file://database/user-model
```

### Resource Features

| Feature | Behavior |
|---------|----------|
| Autocomplete | Type `@` to see available resources |
| Fuzzy search | Resource paths are fuzzy-searchable |
| Auto-fetch | Resources automatically fetched and included as attachments when referenced |
| Content types | Text, JSON, structured data (varies by server) |
| List/read tools | Claude Code automatically provides tools to list and read MCP resources when servers support them |

## MCP Prompts as Commands

MCP servers expose prompts as slash commands:

```
/mcp__github__list_prs
/mcp__github__pr_review 456
/mcp__jira__create_issue "Bug in login" high
```

Format: `/mcp__<server>__<prompt-name> [args]`

### Prompt Features

| Feature | Behavior |
|---------|----------|
| Dynamic discovery | Prompts discovered from connected servers |
| Argument parsing | Based on prompt's defined parameters |
| Name normalization | Spaces become underscores |
| Direct injection | Results injected into conversation |

## Output Limits

| Threshold | Behavior |
|-----------|----------|
| 10,000 tokens | Warning displayed |
| 25,000 tokens | Default maximum |

Configure via environment:

```bash
export MAX_MCP_OUTPUT_TOKENS=50000
claude
```

Higher limits useful for MCP servers that:
- Query large datasets or databases
- Generate detailed reports or documentation
- Process extensive log files or debugging information

If you frequently encounter output warnings with specific MCP servers, consider increasing the limit or configuring the server to paginate/filter responses.

## Dynamic Tool Updates

MCP servers can send `list_changed` notifications, allowing them to dynamically update their available tools, prompts, and resources without requiring you to disconnect and reconnect. When an MCP server sends a `list_changed` notification, Claude Code automatically refreshes the available capabilities from that server.

## Key Points

- @ mentions for resources (fuzzy-searchable, auto-fetched)
- /mcp__server__prompt for commands
- Prompts dynamically discovered, names normalized
- Default 25,000 token output limit (configurable)
- Servers can update tools dynamically via `list_changed`
