---
id: memory-rules-organization
topic: Rules Organization
category: memory
tags: [memory, rules, subdirectories, symlinks]
requires: [memory-rules-overview]
related_to: [memory-rules-paths]
official_docs: https://code.claude.com/en/memory
---

# Rules Organization

Strategies for organizing rules in larger projects.

## Subdirectories

Rules can be organized into subdirectories:

```
.claude/rules/
├── frontend/
│   ├── react.md
│   └── styles.md
├── backend/
│   ├── api.md
│   └── database.md
└── general.md
```

All `.md` files are discovered recursively.

## Symlinks

Share common rules across projects using symlinks:

```bash
# Symlink a shared rules directory
ln -s ~/shared-claude-rules .claude/rules/shared

# Symlink individual rule files
ln -s ~/company-standards/security.md .claude/rules/security.md
```

Symlinks are resolved and contents loaded normally. Circular symlinks are detected and handled gracefully.

## User-Level Rules

Personal rules that apply to all projects:

```
~/.claude/rules/
├── preferences.md    # Personal coding preferences
└── workflows.md      # Preferred workflows
```

User-level rules load before project rules, giving project rules higher priority.

## Best Practices

| Practice | Reason |
|----------|--------|
| Keep rules focused | One topic per file |
| Use descriptive filenames | Indicates coverage |
| Use conditional rules sparingly | Only when truly needed |
| Organize with subdirectories | Group related concerns |

## Key Points

- Subdirectories supported with recursive discovery
- Symlinks enable shared rules across projects
- User rules in `~/.claude/rules/` apply globally
- Project rules override user rules
