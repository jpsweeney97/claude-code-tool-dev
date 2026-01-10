---
id: hooks-mcp
topic: Hooks with MCP Tools
category: hooks
tags: [mcp, tools, servers, patterns]
requires: [hooks-overview, hooks-matchers]
related_to: [hooks-configuration, hooks-events]
official_docs: https://code.claude.com/en/hooks
---

# Hooks with MCP Tools

Claude Code hooks work with Model Context Protocol (MCP) tools. MCP servers provide tools with a special naming pattern.

## MCP Tool Naming Pattern

MCP tools follow the pattern `mcp__<server>__<tool>`:

| Example | Server | Tool |
|---------|--------|------|
| `mcp__memory__create_entities` | memory | create_entities |
| `mcp__filesystem__read_file` | filesystem | read_file |
| `mcp__github__search_repositories` | github | search_repositories |

## Matching MCP Tools

### Match Specific Tool

```json
{
  "matcher": "mcp__memory__create_entities"
}
```

### Match All Tools from Server

```json
{
  "matcher": "mcp__memory__.*"
}
```

### Match Pattern Across Servers

```json
{
  "matcher": "mcp__.*__write.*"
}
```

## Configuration Examples

### Log Memory Operations

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "mcp__memory__.*",
      "hooks": [{
        "type": "command",
        "command": "echo 'Memory operation initiated' >> ~/mcp-operations.log"
      }]
    }]
  }
}
```

### Validate MCP Writes

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "mcp__.*__write.*",
      "hooks": [{
        "type": "command",
        "command": "/home/user/scripts/validate-mcp-write.py"
      }]
    }]
  }
}
```

### Multiple MCP Matchers

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [{"type": "command", "command": "./log-memory.sh"}]
      },
      {
        "matcher": "mcp__filesystem__delete.*",
        "hooks": [{"type": "command", "command": "./confirm-delete.sh"}]
      }
    ]
  }
}
```

## Key Points

- MCP tools use `mcp__<server>__<tool>` naming
- Use `.*` regex for partial matching
- Same matcher syntax as built-in tools
- Can match by server, tool, or pattern
