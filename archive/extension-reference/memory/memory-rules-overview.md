---
id: memory-rules-overview
topic: Rules Directory Overview
category: memory
tags: [memory, rules, modular]
requires: [memory-overview]
related_to: [memory-rules-paths, memory-rules-organization]
official_docs: https://code.claude.com/en/memory
---

# Rules Directory Overview

The `.claude/rules/` directory provides modular, topic-focused instructions as an alternative to a single large CLAUDE.md.

## Basic Structure

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

## Loading Behavior

All `.md` files in `.claude/rules/` are automatically loaded as project memory with the same priority as `.claude/CLAUDE.md`.

## When to Use Rules

| Scenario | Approach |
|----------|----------|
| Small project | Single CLAUDE.md |
| Large project | CLAUDE.md + rules/ |
| Team collaboration | Rules for shared standards |
| Personal preferences | User rules in `~/.claude/rules/` |

## Key Points

- Rules provide modular alternative to single CLAUDE.md
- All `.md` files in `.claude/rules/` auto-loaded
- Same priority as `.claude/CLAUDE.md`
- Use for larger projects with distinct concerns
