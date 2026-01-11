---
id: memory-overview
topic: Memory System Overview
category: memory
tags: [memory, claude.md, hierarchy, precedence]
related_to: [memory-imports, memory-rules-overview, precedence]
official_docs: https://code.claude.com/en/memory
---

# Memory System Overview

Claude Code offers five memory locations in a hierarchical structure.

## Memory Types

| Memory Type | Location | Purpose | Shared With |
|-------------|----------|---------|-------------|
| Enterprise policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Organization-wide instructions | All org users |
| Project memory | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project instructions | Team via VCS |
| Project rules | `./.claude/rules/*.md` | Modular, topic-specific rules | Team via VCS |
| User memory | `~/.claude/CLAUDE.md` | Personal preferences | Just you |
| Project local | `./CLAUDE.local.md` | Personal project-specific | Just you |

## Precedence

Files higher in the hierarchy take precedence and load first. Project rules have same priority as `.claude/CLAUDE.md`.

## Loading Behavior

All memory files are automatically loaded into context when Claude Code launches. CLAUDE.local.md files are automatically added to .gitignore.

## Key Points

- Five memory locations with hierarchical precedence
- Enterprise > Project > User > Local
- All loaded automatically at launch
- Rules have same priority as CLAUDE.md
