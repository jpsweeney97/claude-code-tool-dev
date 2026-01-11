---
id: memory-lookup
topic: Memory Lookup Behavior
category: memory
tags: [memory, discovery, recursive]
requires: [memory-overview]
related_to: [memory-imports]
official_docs: https://code.claude.com/en/memory
---

# Memory Lookup Behavior

Claude Code discovers memory files through recursive directory traversal.

## Upward Discovery

Starting from the current working directory, Claude Code recurses up to (but not including) the root directory `/`, reading any CLAUDE.md or CLAUDE.local.md files found.

**Example:** Running Claude Code in `foo/bar/` loads both `foo/CLAUDE.md` and `foo/bar/CLAUDE.md`.

## Downward Discovery

CLAUDE.md files nested in subtrees under your current working directory are discovered but only included when Claude reads files in those subtrees.

## Discovery Behavior Summary

| Direction | When Loaded | Scope |
|-----------|-------------|-------|
| Upward (ancestors) | At launch | Always in context |
| Downward (descendants) | On file access | Contextual |

## Key Points

- Upward: All ancestor CLAUDE.md files loaded at launch
- Downward: Descendant files loaded on demand
- Root directory `/` is excluded from search
