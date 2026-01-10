---
id: hooks-overview
topic: Hooks Overview
category: hooks
tags: [hooks, events, automation, validation]
related_to: [hooks-events, hooks-types, hooks-exit-codes, hooks-input-schema, hooks-mcp, hooks-security, hooks-debugging, hooks-plugins]
official_docs: https://code.claude.com/en/hooks
---

# Hooks Overview

Hooks are event-driven automations that execute before or after specific actions. They can validate, log, transform, or block operations.

## Purpose

- Validate tool inputs before execution
- Log and audit operations
- Transform inputs or outputs
- Block dangerous operations
- Initialize session state

## Configuration Location

Hooks are configured in `settings.json`:

| Scope | Path |
|-------|------|
| Project | `.claude/settings.json` |
| User | `~/.claude/settings.json` |

Or scoped to components (skills, commands, agents) via frontmatter.

## When to Use

Use hooks when:
- Need to validate before tool execution
- Want automatic logging/auditing
- Need to transform inputs/outputs
- Want to block dangerous operations

Don't use hooks when:
- Logic belongs in skill/command content
- Manual verification is preferred
- One-time operation

## Execution Details

- **Timeout**: 60 seconds default, configurable per hook
- **Parallelization**: All matching hooks run in parallel
- **Deduplication**: Identical hook commands deduplicated
- **Input**: JSON via stdin

## Output Behavior by Event

| Events | Output Destination |
|--------|-------------------|
| PreToolUse, PermissionRequest, PostToolUse, Stop, SubagentStop | Verbose mode (Ctrl+O) |
| Notification, SessionEnd | Debug only (`--debug`) |
| UserPromptSubmit, SessionStart | stdout added as context |

## Key Points

- 10 event types (some can block, some can't)
- 3 hook types: command, prompt, agent
- Exit code 2 blocks, exit code 1 does NOT block
- Hooks fail open by default

## Related Topics

- [hooks-events](hooks-events.md) - Event types and matchers
- [hooks-types](hooks-types.md) - Hook type details
- [hooks-input-schema](hooks-input-schema.md) - JSON input per event
- [hooks-exit-codes](hooks-exit-codes.md) - Exit codes and JSON output
- [hooks-mcp](hooks-mcp.md) - MCP tool integration
- [hooks-security](hooks-security.md) - Security considerations
- [hooks-debugging](hooks-debugging.md) - Troubleshooting
- [hooks-plugins](hooks-plugins.md) - Plugin hook integration
