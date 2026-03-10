# CLAUDE.md Section Templates

## Section Selection Guide

Include a section when exploration findings reveal project-specific knowledge that isn't obvious from reading the code. Skip sections where the project follows standard conventions for its language/framework.

| Section | Include When | Skip When | Primary Source |
|---------|-------------|-----------|----------------|
| Project Overview | Always | Never | Cartographer |
| Commands | Build/test/lint commands exist | No build step | Toolchain Scout |
| Architecture | Structure isn't self-evident | Single-file or trivial layout | Cartographer |
| Code Style | Non-obvious conventions found | Conventions are framework-standard | Convention Miner |
| Environment | Env vars or setup steps required | No env config needed | Toolchain Scout |
| Testing | Test patterns aren't obvious | Standard test runner, no quirks | Toolchain Scout + Convention Miner |
| Key Files | Important files aren't discoverable from structure | Conventional file layout | Cartographer |
| Gotchas | Non-obvious pitfalls exist | No quirks found | Gotcha Hunter |
| Workflow | Dev workflow has specific patterns | Standard git flow | Multiple |
| Dependencies | Inter-package or service deps exist | Single package, no services | Cartographer + Toolchain Scout |

## Templates

### Project Overview

Always included. Orients Claude to the project type so it applies the right mental model.

```markdown
## Project Overview

<One line: what it does and what kind of codebase it is (library, CLI, web app, API, monorepo, plugin).>
```

Keep to 1-3 lines. Don't repeat the README.

### Commands

The most immediately actionable section. Every command must be verified against the build system.

```markdown
## Commands

| Command | Purpose |
|---------|---------|
| `<full command>` | <what it does> |
```

**Rules:**
- Only include commands that exist and work
- Include the full invocation (e.g., `uv run pytest tests/` not just `pytest`)
- Group by purpose if more than 6 commands (Build, Test, Lint, Deploy)
- Note required working directory if not project root

### Architecture

Structure overview for codebase navigation.

```markdown
## Architecture

```
<directory tree, depth 2-3>
```

<brief annotation only for directories whose names don't self-document>
```

**Rules:**
- Exclude standard ignores: node_modules, .git, __pycache__, dist, build, .venv, .tox, target, out
- For monorepos, include a package table:

```markdown
| Package | Path | Purpose |
|---------|------|---------|
| `<name>` | `<path>` | <one-line purpose> |
```

### Code Style

Only include conventions that deviate from the language/framework default. If a Python project uses snake_case, that's standard — skip it. If it uses camelCase, that's unusual — document it.

```markdown
## Code Style

| Convention | Pattern |
|------------|---------|
| <aspect> | <what this project does> |
```

**Rules:**
- Document deviations from defaults, not the defaults themselves
- Include import ordering if it matters
- Include error handling patterns if non-obvious
- Reference linter/formatter configs rather than repeating their rules

### Environment

Setup Claude needs to know before working.

```markdown
## Environment

### Required
- `<VAR_NAME>` — <purpose>

### Setup
1. <step>
```

**Rules:**
- Only development-relevant env vars, not every production var
- Include setup steps not already in the README
- Note tools required beyond the package manager

### Testing

Patterns for writing and running tests.

```markdown
## Testing

- Run: `<test command>`
- File pattern: `<naming convention>`
- <pattern>: <description>
```

**Rules:**
- Include test file naming convention
- Include fixture/factory patterns if established
- Note test-specific env vars or setup
- Note if tests require sequential execution or have ordering constraints

### Key Files

Files Claude should know about that aren't discoverable from the architecture section.

```markdown
## Key Files

- `<path>` — <why it matters>
```

**Rules:**
- Only files that aren't obvious from directory structure
- Focus on files Claude will reference frequently
- Include config files with non-obvious effects

### Gotchas

Non-obvious patterns that will waste time if not documented.

```markdown
## Gotchas

- **<title>**: <what happens, why, and what to do about it>
```

**Rules:**
- Each gotcha includes: the problem, why it happens, the fix or workaround
- Prioritize by time wasted if not known
- Skip gotchas common to all projects ("run install first")

### Workflow

Development workflow patterns specific to this project.

```markdown
## Workflow

- <pattern>: <when and how>
```

**Rules:**
- Include branch naming conventions if enforced
- Include PR/review patterns if specific
- Include deployment workflow if Claude might trigger it
- Reference CI/CD config rather than restating it

### Dependencies

Inter-package or service dependencies that affect development.

```markdown
## Dependencies

- `<package/service>` depends on `<other>` — <why it matters>
```

**Rules:**
- Only for monorepos or multi-service projects
- Focus on dependencies that affect build/test order
- Include service dependencies (databases, caches) needed for development

## Content Guidelines

### What Belongs in CLAUDE.md

- Commands that Claude will need to run
- Architecture that helps Claude navigate the codebase
- Conventions that Claude should follow when writing code
- Gotchas that will waste time if not documented
- Environment setup needed before Claude can work

### What Does NOT Belong

| Don't Include | Why | Bad Example |
|---------------|-----|-------------|
| Obvious code info | Names already self-document | "UserService handles users" |
| Generic best practices | Claude already knows them | "Write tests for new features" |
| One-off fixes | Won't recur | "Fixed login bug in abc123" |
| Verbose explanations | Wastes context window | Full JWT explanation |
| Duplicated README content | Reference the README instead | Repeating installation steps |
| Standard conventions | Expected for the language | "Python uses snake_case" |

### Voice

CLAUDE.md speaks to Claude in imperative mood:

| Don't | Do |
|-------|-----|
| "Tests should be run with pytest" | "Run tests: `pytest tests/`" |
| "The project uses a monorepo structure" | "Monorepo. Packages in `packages/`." |
| "It is important to note that..." | (delete — just state the thing) |

Every line pays rent in the context window. If removing a line would not cause Claude to make a mistake, remove it.

### Target Size

A well-crafted CLAUDE.md is typically 50-200 lines. Over 300 lines suggests content that doesn't earn its context window cost — look for generic advice, verbose explanations, or duplicated README content to cut. CLAUDE.md is loaded into every conversation, so bloat has a compounding cost that README and handbook don't share.

### Sections to Never Include

- **Table of contents** — if the file needs a TOC, it's too long
- **Version history** — that's the changelog's job
- **User-facing documentation** — that's the README's job
- **Operational runbooks** — that's the handbook's job
- **Personal preferences** — those belong in `~/.claude/CLAUDE.md` (global), not project-level CLAUDE.md (shared)

## Project Type Patterns

Different project types emphasize different sections:

| Project Type | Priority Sections | Often Skipped |
|-------------|-------------------|---------------|
| Library | Commands, Code Style, Testing, Key Files | Workflow, Environment |
| CLI Tool | Commands, Architecture, Gotchas | Code Style, Dependencies |
| Web App | Commands, Architecture, Environment, Gotchas | Key Files |
| API Service | Commands, Environment, Testing, Architecture | Key Files |
| Monorepo | Architecture, Commands, Dependencies, Workflow | Code Style (varies by package) |
| Plugin | Commands, Architecture, Gotchas, Workflow | Environment, Dependencies |

When a project fits multiple types (e.g., a monorepo containing CLI tools), use the dominant type's sections for the root CLAUDE.md and write nested CLAUDE.md files for sub-packages using their own type's priorities.
