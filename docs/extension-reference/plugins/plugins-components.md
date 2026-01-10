---
id: plugins-components
topic: Plugin Component Types
category: plugins
tags: [components, commands, skills, agents, hooks, mcp, lsp]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-paths]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Component Types

Plugins can bundle 6 types of components.

## Component Reference

| Component | Manifest Key | Location | Notes |
|-----------|--------------|----------|-------|
| Commands | `commands` | `commands/` | Markdown files |
| Skills | `skills` | `skills/` | Directories with SKILL.md |
| Agents | `agents` | `agents/` | Markdown files |
| Hooks | `hooks` | `hooks/` or inline | JSON configuration |
| MCP Servers | `mcpServers` | `.mcp.json` or inline | Server definitions |
| LSP Servers | `lspServers` | `.lsp.json` or inline | Language servers |

## Commands

Standard command markdown files:

```json
{
  "commands": "./commands/"
}
```

Or explicit list:

```json
{
  "commands": ["./commands/review.md", "./commands/test.md"]
}
```

For complete command structure, invocation patterns, and features, see `commands-overview`.

## Skills

Skill directories containing SKILL.md:

```json
{
  "skills": "./skills/"
}
```

**Skill structure:**

```
skills/
├── pdf-processor/
│   ├── SKILL.md
│   ├── reference.md (optional)
│   └── scripts/ (optional)
└── code-reviewer/
    └── SKILL.md
```

**Integration behavior:**

- Plugin Skills auto-discovered when plugin is installed
- Claude autonomously invokes Skills based on matching task context
- Skills can include supporting files alongside SKILL.md

For SKILL.md format and authoring guidance, see `skills-overview` and `skills-frontmatter`.

## Agents

Agent definition files:

```json
{
  "agents": ["./agents/reviewer.md", "./agents/analyzer.md"]
}
```

**Agent structure:**

```markdown
---
description: What this agent specializes in
capabilities: ['task1', 'task2', 'task3']
---

# Agent Name

Detailed description of the agent's role, expertise, and when Claude should invoke it.

## Capabilities

- Specific task the agent excels at
- Another specialized capability
- When to use this agent vs others

## Context and examples

Examples of when this agent should be used and what problems it solves.
```

**Integration points:**

- Agents appear in the `/agents` interface
- Claude can invoke agents automatically based on task context
- Agents can be invoked manually by users
- Plugin agents work alongside built-in Claude agents

## Hooks

File reference or inline:

```json
{
  "hooks": "./hooks/hooks.json"
}
```

Or inline:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "./validate.sh"}]
    }]
  }
}
```

**Available events:**

| Event | When Fired |
|-------|------------|
| `PreToolUse` | Before Claude uses any tool |
| `PostToolUse` | After Claude successfully uses any tool |
| `PostToolUseFailure` | After Claude tool execution fails |
| `PermissionRequest` | When a permission dialog is shown |
| `UserPromptSubmit` | When user submits a prompt |
| `Notification` | When Claude Code sends notifications |
| `Stop` | When Claude attempts to stop |
| `SubagentStart` | When a subagent is started |
| `SubagentStop` | When a subagent attempts to stop |
| `SessionStart` | At the beginning of sessions |
| `SessionEnd` | At the end of sessions |
| `PreCompact` | Before conversation history is compacted |

**Hook types:**

| Type | Description |
|------|-------------|
| `command` | Execute shell commands or scripts |
| `prompt` | Evaluate a prompt with an LLM (uses `$ARGUMENTS` placeholder) |
| `agent` | Run an agentic verifier with tools (plugin-only) |

## MCP Servers

```json
{
  "mcpServers": {
    "database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    },
    "api-client": {
      "command": "npx",
      "args": ["@company/mcp-server", "--plugin-mode"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}"
    }
  }
}
```

**Configuration fields:**

| Field | Description |
|-------|-------------|
| `command` | Executable to run |
| `args` | Command-line arguments |
| `env` | Environment variables for the server process |
| `cwd` | Working directory for the server |

**Integration behavior:**

- Plugin MCP servers start automatically when plugin is enabled
- Servers appear as standard MCP tools in Claude's toolkit
- Server capabilities integrate seamlessly with Claude's existing tools
- Plugin servers can be configured independently of user MCP servers

## LSP Servers

```json
{
  "lspServers": "./.lsp.json"
}
```

## Key Points

- All 6 component types are optional
- Use directory paths for auto-discovery
- Use array for explicit file lists
- Hooks, MCP, LSP support inline definitions
