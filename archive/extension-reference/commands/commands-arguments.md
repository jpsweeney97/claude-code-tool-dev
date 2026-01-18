---
id: commands-arguments
topic: Command Arguments and Dynamic Content
category: commands
tags: [arguments, substitution, bash, files]
requires: [commands-overview]
related_to: [commands-frontmatter, commands-examples]
official_docs: https://code.claude.com/en/slash-commands
---

# Command Arguments and Dynamic Content

Commands support argument substitution and dynamic content injection.

## Argument Substitution

| Pattern | Description | Example |
|---------|-------------|---------|
| `$ARGUMENTS` | All arguments as string | `Review $ARGUMENTS` |
| `$1` | First argument | `Compare $1` |
| `$2` | Second argument | `with $2` |
| `$N` | Nth argument | Positional access |

### When to Use Positional Arguments

Use `$1`, `$2`, etc. instead of `$ARGUMENTS` when you need to:

- Access arguments individually in different parts of your command
- Provide defaults for missing arguments
- Build more structured commands with specific parameter roles

## Bash Execution

Execute commands before prompt injection with backticks and `!`:

```markdown
Current branch: !`git branch --show-current`
Recent commits: !`git log --oneline -5`
Status: !`git status --short`
```

Output is inserted where the backticks appear.

**Requirement:** You must include `allowed-tools` with the `Bash` tool in frontmatter for bash execution to work. You can restrict to specific commands:

```yaml
---
allowed-tools: Bash(git status:*), Bash(git log:*)
---
```

## File References

Include file contents with `@` to [reference files and directories](https://code.claude.com/en/common-workflows#reference-files-and-directories):

```markdown
Review this file: @src/main.ts
Consider these patterns: @src/patterns/
```

## Combined Example

```markdown
---
description: Review changes on current branch
allowed-tools: Bash(git branch:*), Bash(git diff:*)
---

Branch: !`git branch --show-current`
Diff from main: !`git diff main --stat`

Review these changes for:
- Bugs and edge cases
- Security issues
- Code style

User focus: $ARGUMENTS
```

## Key Points

- `$ARGUMENTS` for full argument string
- `$1`, `$2` for positional arguments
- `!`command`` executes bash, injects output
- `@path` includes file contents
