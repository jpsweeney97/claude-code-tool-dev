---
id: commands-overview
topic: Commands Overview
category: commands
tags: [commands, slash, prompt, template]
related_to: [commands-frontmatter, commands-arguments, commands-builtin, commands-namespacing, commands-plugin, commands-mcp, commands-skill-tool, skills-overview]
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

Project commands take precedence over user commands with the same name.

## Invocation

```
/<command-name>
/<command-name> arguments here
```

> **Tip:** Slash command autocomplete works anywhere in your input, not just at the beginning. Type `/` at any position to see available commands.

## Extended Thinking

Commands can trigger extended thinking by including [extended thinking keywords](https://code.claude.com/en/common-workflows#use-extended-thinking) in the prompt content.

## Commands vs Skills

| Aspect | Commands | Skills |
|--------|----------|--------|
| Complexity | Simple prompts | Complex capabilities |
| Structure | Single `.md` file | Directory with `SKILL.md` + resources |
| Discovery | Explicit invocation (`/command`) | Automatic (based on context) |
| Files | One file only | Multiple files, scripts, templates |
| Scope | Project or personal | Project or personal |
| Sharing | Via git | Via git |

### When to Use Commands

**Quick, frequently used prompts:**
- Simple prompt snippets you use often
- Quick reminders or templates
- Frequently used instructions that fit in one file

**Examples:**
- `/review` → "Review this code for bugs and suggest improvements"
- `/explain` → "Explain this code in simple terms"
- `/optimize` → "Analyze this code for performance issues"

### When to Use Skills

**Comprehensive capabilities with structure:**
- Complex workflows with multiple steps
- Capabilities requiring scripts or utilities
- Knowledge organized across multiple files
- Team workflows you want to standardize

**Examples:**
- PDF processing skill with form-filling scripts and validation
- Data analysis skill with reference docs for different data types
- Documentation skill with style guides and templates

### Example Comparison

**As a command** (single file):

```markdown
# .claude/commands/review.md

Review this code for:
- Security vulnerabilities
- Performance issues
- Code style violations
```

Usage: `/review` (manual invocation)

**As a skill** (directory with resources):

```
.claude/skills/code-review/
├── SKILL.md (overview and workflows)
├── SECURITY.md (security checklist)
├── PERFORMANCE.md (performance patterns)
├── STYLE.md (style guide reference)
└── scripts/
    └── run-linters.sh
```

Usage: "Can you review this code?" (automatic discovery)

The skill provides richer context, validation scripts, and organized reference material.

## Key Points

- Markdown file = slash command
- User scope overrides project scope
- No logic, just prompt templates
- Arguments via `$ARGUMENTS` or `$1`, `$2`
