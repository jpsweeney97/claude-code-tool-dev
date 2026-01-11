---
id: memory-imports
topic: CLAUDE.md Imports
category: memory
tags: [memory, imports, syntax]
requires: [memory-overview]
related_to: [memory-lookup]
official_docs: https://code.claude.com/en/memory
---

# CLAUDE.md Imports

CLAUDE.md files can import additional files using `@path/to/import` syntax.

## Import Syntax

```markdown
See @README for project overview and @package.json for available npm commands.

# Additional Instructions
- git workflow @docs/git-instructions.md
```

## Path Types

| Type | Example | Use Case |
|------|---------|----------|
| Relative | `@README` | Same directory |
| Relative nested | `@docs/guide.md` | Subdirectory |
| Absolute | `@~/.claude/my-project.md` | Personal instructions across worktrees |

## Recursive Imports

Imported files can recursively import additional files with max-depth of 5 hops. View loaded files with `/memory` command.

## Code Block Protection

Imports are not evaluated inside markdown code spans and code blocks:

```markdown
This will not be treated as an import: `@anthropic-ai/claude-code`
```

## Key Points

- Use `@path` syntax to import files
- Relative and absolute paths supported
- Max import depth: 5 hops
- Code blocks protect against unintended imports
