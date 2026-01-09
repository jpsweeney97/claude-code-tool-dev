---
id: hooks-overview
topic: Hooks Overview
category: hooks
tags: [hooks, events, automation, validation]
related_to: [hooks-events, hooks-types, hooks-exit-codes]
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

## Key Points

- 10 event types (some can block, some can't)
- 3 hook types: command, prompt, agent
- Exit code 2 blocks, exit code 1 does NOT block
- Hooks fail open by default
