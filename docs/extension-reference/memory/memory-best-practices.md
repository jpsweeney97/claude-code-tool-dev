---
id: memory-best-practices
topic: Memory Best Practices
category: memory
tags: [memory, best-practices, guidelines]
requires: [memory-overview]
related_to: [memory-rules-overview, memory-imports]
official_docs: https://code.claude.com/en/memory
---

# Memory Best Practices

Guidelines for effective memory management.

## Writing Effective Instructions

| Practice | Example |
|----------|---------|
| Be specific | "Use 2-space indentation" not "Format code properly" |
| Use structure | Bullet points under descriptive headings |
| Include commands | Document build, test, lint commands |
| Avoid duplication | Use imports for shared content |

## Organization Guidelines

| Guideline | Rationale |
|-----------|-----------|
| One topic per file | Easier to maintain and find |
| Descriptive filenames | Self-documenting structure |
| Group with subdirectories | Logical organization |
| Conditional rules sparingly | Only when truly file-specific |

## Maintenance

| Practice | Frequency |
|----------|-----------|
| Review accuracy | When project evolves |
| Remove obsolete content | After major changes |
| Update commands | When tooling changes |
| Verify imports | When moving files |

## Anti-Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| Giant CLAUDE.md | Hard to navigate | Split into rules/ |
| Vague instructions | Claude can't follow | Be specific |
| Stale content | Misleads Claude | Regular review |
| Duplicate content | Inconsistency risk | Use imports |

## Key Points

- Be specific in instructions
- Use structure (bullets, headings)
- Review and update regularly
- Split large files into modular rules
