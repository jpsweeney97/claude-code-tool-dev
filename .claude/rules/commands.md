---
paths:
  - ".claude/commands/**"
  - "~/.claude/commands/**"
---

# Command Development

Commands are slash-invoked templates that provide reusable prompts or instructions. They're the simplest Claude Code extension—just markdown files.

## When to Use Commands

- **Reusable prompts**: Standard questions, review templates, report formats
- **Quick actions**: `/$ARGUMENTS` substitution for parameterized tasks
- **Project shortcuts**: Team-specific workflows invoked by name
- **Simple templates**: No complex logic, just prompt injection

## When NOT to Use Commands

- **Complex workflows with decision trees**: Use skills instead (commands are static)
- **Multi-step procedures with verification**: Use skills instead (commands can't enforce steps)
- **Autonomous multi-turn work**: Use agents instead (commands are single-turn prompts)
- **Event-driven automation**: Use hooks instead (commands require explicit invocation)

## Structure

Commands are single markdown files:

```
.claude/commands/
├── <name>.md           # Command file
└── ...
```

## Locations

| Scope   | Path                           | Precedence     |
| ------- | ------------------------------ | -------------- |
| Project | `.claude/commands/<name>.md`   | Wins over user |
| User    | `~/.claude/commands/<name>.md` | Fallback       |

Project commands override user commands with the same name. The user command is silently ignored.

### Subdirectory Organization

Subdirectories organize commands and appear in the description:

| File                                | Command | Description        |
| ----------------------------------- | ------- | ------------------ |
| `.claude/commands/test.md`          | `/test` | (project)          |
| `.claude/commands/frontend/test.md` | `/test` | (project:frontend) |
| `~/.claude/commands/test.md`        | `/test` | (user)             |

Commands in different subdirectories can share names—the subdirectory distinguishes them.

## Command Format

```markdown
---
description: Shown in slash command menu
argument-hint: <placeholder text for arguments>
allowed-tools: ['Tool1', 'Tool2'] # Optional: restrict tool access
---

Your prompt template here.

The user wants: $ARGUMENTS
```

## Frontmatter Fields

| Field                      | Required | Type    | Notes                                                       |
| -------------------------- | -------- | ------- | ----------------------------------------------------------- |
| `description`              | No       | string  | Shown in command list (strongly recommended)                |
| `argument-hint`            | No       | string  | Placeholder shown in argument input                         |
| `allowed-tools`            | No       | string  | Space/comma-separated list of tools                         |
| `model`                    | No       | string  | Specific model (e.g., `claude-3-5-haiku-20241022`)          |
| `disable-model-invocation` | No       | boolean | Prevent Skill tool from calling this command                |
| `hooks`                    | No       | object  | PreToolUse, PostToolUse, or Stop handlers scoped to command |
| `hooks.*.once`             | No       | boolean | Run hook only once per session, then remove                 |

Hooks defined in commands are **automatically cleaned up** when the command finishes executing.

## Argument Substitution

### All arguments: `$ARGUMENTS`

`$ARGUMENTS` is replaced with everything the user types after the command name:

| User types                                | `$ARGUMENTS` becomes              |
| ----------------------------------------- | --------------------------------- |
| `/review`                                 | _(empty string)_                  |
| `/review src/main.py`                     | `src/main.py`                     |
| `/review src/main.py for security issues` | `src/main.py for security issues` |

### Positional arguments: `$1`, `$2`, etc.

Access individual arguments by position:

```markdown
Review PR #$1 with priority $2 and assign to $3
```

| User types                  | Result                                |
| --------------------------- | ------------------------------------- |
| `/review-pr 456 high alice` | `$1`="456", `$2`="high", `$3`="alice" |

Use positional args when you need arguments in different parts of the command or want to provide defaults for missing arguments.

## Special Syntax

### Bash execution: `!` prefix

Execute bash commands before the slash command runs. Output is included in context.

```markdown
---
allowed-tools: Bash(git diff:*), Bash(git status:*)
---

Review these changes:
!`git diff HEAD`

Current status:
!`git status`
```

**Requires**: `allowed-tools` must include the Bash tool for the specific commands.

### File references: `@` prefix

Include file contents in the command:

```markdown
Compare @src/old-version.js with @src/new-version.js and explain the differences.
```

## Design Principles

### Commands are prompts, not programs

A command injects text into the conversation. It can't enforce steps, make decisions, or verify outcomes. For those, use skills.

### Keep descriptions actionable

The description appears in the slash menu. Make it clear what the command does.

### Use argument-hint for clarity

If the command expects arguments, hint at what's needed: `<file path>`, `<branch name>`, `<description>`.

### Don't duplicate skills

If a workflow needs verification, decision points, or multi-step procedures, it should be a skill. Commands are for simple prompt templates.

## Common Patterns

### Review template

```markdown
---
description: Review code for common issues
argument-hint: <file or directory>
---

Review the following code for:

1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style violations

Focus on: $ARGUMENTS
```

### Explain template

```markdown
---
description: Explain how something works
argument-hint: <file, function, or concept>
---

Explain how this works in detail:

$ARGUMENTS

Include:

- High-level overview
- Key components and their interactions
- Important implementation details
- Common gotchas or edge cases
```

### Commit message generator

```markdown
---
description: Generate a commit message for staged changes
---

Look at the staged changes (git diff --cached) and generate a conventional commit message.

Format: <type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, test, chore
```

### Quick question template

```markdown
---
description: Ask a quick question about the codebase
argument-hint: <your question>
---

Answer this question about the codebase concisely:

$ARGUMENTS
```

## Anti-patterns

| Anti-pattern                                    | Problem                                    | Fix             |
| ----------------------------------------------- | ------------------------------------------ | --------------- |
| Complex multi-step procedures                   | Commands can't enforce or verify           | Use a skill     |
| Decision trees                                  | Commands are static text                   | Use a skill     |
| Expecting tool restrictions to enforce workflow | `allowed-tools` only limits, doesn't guide | Use a skill     |
| No description                                  | Command hidden in menu or unclear          | Add description |
| Vague description                               | Users don't know when to use it            | Be specific     |

## Testing

1. Create the command file
2. Invoke with `/<name>` in Claude Code
3. Test with various argument patterns
4. Verify `$ARGUMENTS` substitution works correctly

### Test cases to cover

- No arguments: `/<name>`
- Single argument: `/<name> foo`
- Multiple words: `/<name> foo bar baz`
- Paths with spaces: `/<name> "path with spaces"`

## Workflow

1. Create `.claude/commands/<name>.md`
2. Add frontmatter with description
3. Test with `/<name>` in this project
4. Promote: `uv run scripts/promote command <name>`

## Compliance Checklist

Before promoting a command, verify:

- [ ] Description is present and actionable
- [ ] `argument-hint` is set if command expects arguments
- [ ] `$ARGUMENTS` is used correctly (or intentionally omitted)
- [ ] Command is simple enough to not need a skill
- [ ] Tested with various argument patterns
- [ ] No complex logic that should be a skill

## Commands vs Skills Decision

| Characteristic  | Command              | Skill                        |
| --------------- | -------------------- | ---------------------------- |
| Structure       | Single prompt        | Multi-section with procedure |
| Verification    | None                 | Required quick checks        |
| Decision points | None                 | ≥2 explicit branches         |
| Complexity      | Static template      | Dynamic workflow             |
| Enforcement     | Cannot enforce steps | Can enforce via procedure    |
| Typical length  | 5-50 lines           | 50-500+ lines                |

**Rule of thumb**: If you need "If X then Y otherwise Z" logic, use a skill.

## See Also

- **skills.md** — Complex workflows with verification (use when commands aren't enough)
- **agents.md** — Autonomous multi-turn work (use for isolated execution)
- **plugins.md** — Bundle commands for distribution via marketplaces (use `/plugin-name:command-name` format)
- **settings.md** — Configure permissions and hooks in settings.json

## Skill Tool Integration

The Skill tool allows Claude to programmatically invoke commands. Key points:

- Commands need `description` frontmatter for Skill tool access
- Use `disable-model-invocation: true` to block programmatic invocation
- **Character budget**: 15,000 chars default; override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var
- Built-in commands (like `/compact`) are not available via Skill tool

## References

Authoritative specification (imported for full context):

- @.claude/skills/auditing-tool-designs/references/fallback-specs.md — Command structure and placeholder rules
