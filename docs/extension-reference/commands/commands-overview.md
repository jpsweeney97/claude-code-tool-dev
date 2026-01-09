---
id: commands-overview
topic: Commands Overview
category: commands
tags: [commands, slash, prompt, template]
related_to: [commands-frontmatter, commands-arguments, skills-overview]
official_docs: https://code.claude.com/en/slash-commands
---

# Commands Overview

Commands are markdown files that inject prompts into conversations. Simplest extension type.

## Purpose

- Repetitive prompt templates
- Team standardization
- Quick workflow shortcuts
- No logic, just injection

## Locations

| Scope | Path |
|-------|------|
| Project | `.claude/commands/<name>.md` |
| User | `~/.claude/commands/<name>.md` |

User commands override project commands with the same name.

## Invocation

```
/<command-name>
/<command-name> arguments here
```

## When to Use

Use commands when:
- Simple prompt injection
- No conditional logic
- One-shot execution
- Quick team standardization

Use skills instead when:
- Complex multi-step workflow
- "If X then Y" logic needed
- Verification steps required

## Key Points

- Markdown file = slash command
- User scope overrides project scope
- No logic, just prompt templates
- Arguments via `$ARGUMENTS` or `$1`, `$2`
