---
id: commands-examples
topic: Command Examples
category: commands
tags: [examples, templates, patterns]
requires: [commands-overview, commands-frontmatter, commands-arguments]
official_docs: https://code.claude.com/en/slash-commands
---

# Command Examples

Complete working command examples.

## Simple Review Command

`.claude/commands/review.md`:

```markdown
---
description: Quick code review
argument-hint: <file-or-directory>
---

Review the following for bugs, security issues, and style:

$ARGUMENTS
```

## Git Status Command

`.claude/commands/status.md`:

```markdown
---
description: Show git status with context
---

Current branch: `!git branch --show-current`
Status: `!git status --short`
Recent commits: `!git log --oneline -5`

Summarize the current state and suggest next steps.
```

## PR Description Command

`.claude/commands/pr-desc.md`:

```markdown
---
description: Generate PR description from changes
allowed-tools: Read, Glob, Grep
---

Changes: `!git diff main --stat`

Generate a PR description with:
- Summary of changes
- Testing done
- Breaking changes (if any)
```

## Multi-file Review Command

`.claude/commands/compare.md`:

```markdown
---
description: Compare two files
argument-hint: <file1> <file2>
---

Compare these files:
- File 1: @$1
- File 2: @$2

Identify differences and suggest which approach is better.
```

## Git Commit Command (Full Example)

Shows the relationship between `allowed-tools` frontmatter and bash execution.

`.claude/commands/commit.md`:

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit.
```

**Note:** The `allowed-tools` frontmatter is required for bash execution to work. Without it, the `!` backtick commands won't execute.

## Key Points

- Keep commands focused on one task
- Use `allowed-tools` to limit scope
- Combine bash execution with file references
- Provide clear `argument-hint` for complex commands
