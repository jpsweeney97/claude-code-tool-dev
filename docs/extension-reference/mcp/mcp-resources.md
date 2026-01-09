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

## MCP Prompts as Commands

MCP servers expose prompts as slash commands:

```
/mcp__github__list_prs
/mcp__github__pr_review 456
/mcp__jira__create_issue "Bug in login" high
```

Format: `/mcp__<server>__<prompt-name> [args]`

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

## Dynamic Tool Updates

MCP servers can send `list_changed` notifications to dynamically update available tools without reconnecting.

## Key Points

- @ mentions for resources
- /mcp__server__prompt for commands
- Default 25,000 token output limit
- Servers can update tools dynamically
