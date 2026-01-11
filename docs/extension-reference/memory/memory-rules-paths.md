---
id: memory-rules-paths
topic: Path-Specific Rules
category: memory
tags: [memory, rules, paths, glob]
requires: [memory-rules-overview]
related_to: [memory-rules-organization]
official_docs: https://code.claude.com/en/memory
---

# Path-Specific Rules

Rules can be scoped to specific files using YAML frontmatter with the `paths` field.

## Basic Path Scoping

```markdown
---
paths: src/api/**/*.ts
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
```

Rules without a `paths` field load unconditionally.

## Glob Patterns

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` directory |
| `*.md` | Markdown files in project root |
| `src/components/*.tsx` | React components in specific directory |

## Brace Expansion

Match multiple patterns efficiently:

```markdown
---
paths: src/**/*.{ts,tsx}
---

# TypeScript/React Rules
```

Expands to match both `src/**/*.ts` and `src/**/*.tsx`.

## Multiple Patterns

Combine patterns with commas:

```markdown
---
paths: {src,lib}/**/*.ts, tests/**/*.test.ts
---
```

## Key Points

- Use `paths` frontmatter for conditional rules
- Standard glob patterns supported
- Brace expansion for efficient multi-pattern matching
- Rules without `paths` apply unconditionally
