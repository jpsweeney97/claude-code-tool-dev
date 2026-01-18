---
id: commands-skill-tool
topic: Skill Tool Integration
category: commands
tags: [commands, skill-tool, programmatic, invocation]
requires: [commands-overview, commands-frontmatter]
related_to: [skills-overview, skills-invocation]
official_docs: https://code.claude.com/en/slash-commands
---

# Skill Tool Integration

The Skill tool allows Claude to programmatically invoke custom slash commands and Agent Skills during a conversation.

## Migration Note

In earlier versions of Claude Code, slash command invocation was provided by a separate `SlashCommand` tool. This has been merged into the `Skill` tool. Update any existing permission rules using `SlashCommand` to use `Skill`.

## What Skill Tool Can Invoke

| Type | Location | Requirements |
|------|----------|--------------|
| Custom slash commands | `.claude/commands/` or `~/.claude/commands/` | Must have `description` frontmatter |
| Agent Skills | `.claude/skills/` or `~/.claude/skills/` | Must not have `disable-model-invocation: true` |

Built-in commands like `/compact` and `/init` are **not** available through this tool.

## Encouraging Usage

To encourage Claude to use the Skill tool, reference the command by name (including the slash) in your prompts or CLAUDE.md:

```
Run /write-unit-test when you are about to start writing tests.
```

## Disable the Skill Tool

To prevent Claude from programmatically invoking any commands or Skills:

```bash
/permissions
# Add to deny rules: Skill
```

This removes the Skill tool and all command/Skill descriptions from context.

## Disable Specific Commands

To prevent a specific command from being invoked via the Skill tool, add to its frontmatter:

```yaml
---
description: My command
disable-model-invocation: true
---
```

This also removes the command's metadata from context.

**Note:** The `user-invocable` field in Skills only controls menu visibility, not Skill tool access. Use `disable-model-invocation: true` to block programmatic invocation. See [skills-invocation](../skills/skills-invocation.md) for details on Skill visibility control.

## Permission Rules

The permission rules support:

| Pattern | Effect |
|---------|--------|
| `Skill(/commit)` | Exact match - allows only `/commit` with no arguments |
| `Skill(/review-pr:*)` | Prefix match - allows `/review-pr` with any arguments |

## Character Budget

The Skill tool includes a character budget to limit context usage when many commands are available.

The budget includes each item's name, arguments, and description.

| Setting | Value |
|---------|-------|
| Default limit | 15,000 characters |
| Override | `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable |

When the budget is exceeded, Claude sees only a subset of available items.

**Monitoring:** Use `/context` to monitor token usage and see how many commands/Skills are included in context. A warning shows when items are excluded due to budget limits.

## Debugging

To see which commands and Skills are available to the Skill tool:

```bash
claude --debug
# Then trigger a query
```

## Key Points

- `SlashCommand` tool merged into `Skill` tool
- Commands need `description` frontmatter for Skill tool access
- Use `disable-model-invocation: true` to block programmatic invocation
- Built-in commands not available via Skill tool
- 15,000 character budget default for context management
