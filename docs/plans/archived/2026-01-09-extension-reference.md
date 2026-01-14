# Machine-Parsable Extension Reference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create ~45 focused markdown files optimized for Claude Code's context retrieval system.

**Architecture:** Multiple small files with YAML frontmatter for metadata. Each file = one concept = one retrieval chunk. Cross-references via explicit `requires`/`related_to` fields plus inline mentions.

**Tech Stack:** Markdown with YAML frontmatter. Source: `docs/claude-code-extension-system.md` and `docs/documentation/*.md`

---

## Frontmatter Schema (Reference)

Every file uses this schema:

```yaml
---
id: unique-identifier           # kebab-case, matches filename without .md
topic: Human Readable Title     # Display name
category: parent-category       # commands|skills|agents|hooks|mcp|lsp|plugins|marketplaces|settings|security
tags: [searchable, terms]       # For retrieval
requires: [prerequisite-ids]    # Must read first (optional)
related_to: [sibling-ids]       # Related concepts (optional)
see_also: [other-ids]           # Further reading (optional)
official_docs: https://...      # Anthropic docs URL
---
```

---

## Task 1: Directory Structure + Index

**Files:**
- Create: `docs/extension-reference/_index.md`
- Create: directories for each category

**Step 1: Create directory structure**

```bash
mkdir -p docs/extension-reference/{overview,commands,skills,agents,hooks,mcp,lsp,plugins,marketplaces,settings,security}
```

**Step 2: Create _index.md**

Create `docs/extension-reference/_index.md`:

```markdown
---
id: index
topic: Claude Code Extension System Reference
category: index
tags: [extensions, reference, navigation]
official_docs: https://code.claude.com/docs/llms.txt
---

# Extension System Reference

Machine-optimized reference for Claude Code extensions. Each file covers one concept.

## Categories

| Category | Files | Description |
|----------|-------|-------------|
| [overview/](./overview/) | 3 | Extension types, decision guidance, precedence |
| [commands/](./commands/) | 4 | Slash command creation |
| [skills/](./skills/) | 6 | Complex workflow skills |
| [agents/](./agents/) | 7 | Autonomous subagents |
| [hooks/](./hooks/) | 8 | Event-driven automation |
| [mcp/](./mcp/) | 7 | Model Context Protocol servers |
| [lsp/](./lsp/) | 3 | Language Server Protocol |
| [plugins/](./plugins/) | 6 | Bundled distribution |
| [marketplaces/](./marketplaces/) | 4 | Plugin distribution |
| [settings/](./settings/) | 6 | Configuration |
| [security/](./security/) | 4 | Managed deployment |

## Frontmatter Schema

All files use:
- `id`: Unique identifier (matches filename)
- `topic`: Display title
- `category`: Parent category
- `tags`: Searchable terms
- `requires`: Prerequisites
- `related_to`: Sibling concepts
- `official_docs`: Anthropic documentation URL

## Source Documents

- Human-readable: `docs/claude-code-extension-system.md`
- Official: `docs/documentation/*.md`
```

**Step 3: Commit**

```bash
git add docs/extension-reference/
git commit -m "docs: create extension-reference directory structure"
```

---

## Task 2: Overview Files (3 files)

**Files:**
- Create: `docs/extension-reference/overview/extension-types.md`
- Create: `docs/extension-reference/overview/when-to-use.md`
- Create: `docs/extension-reference/overview/precedence.md`

**Step 1: Create extension-types.md**

```markdown
---
id: extension-types
topic: Extension Types Overview
category: overview
tags: [commands, skills, agents, hooks, mcp, lsp, plugins, comparison]
related_to: [when-to-use, precedence]
official_docs: https://code.claude.com/docs/llms.txt
---

# Extension Types

Claude Code supports 6 extension types plus plugins for bundling.

## Comparison Matrix

| Type | Complexity | Isolation | Invocation | Event-Driven |
|------|------------|-----------|------------|--------------|
| Commands | Lowest | None | `/command` | No |
| Skills | Medium | Optional fork | `/skill` or auto | No |
| Agents | Medium-High | Full context | Task tool | No |
| Hooks | Medium | Process-level | Automatic | Yes |
| MCP Servers | High | Separate process | Tool calls | No |
| LSP Servers | High | Separate process | Automatic | No |

## Extension Purposes

- **Commands**: Simple prompt templates, no logic
- **Skills**: Complex workflows with verification and decision points
- **Agents**: Autonomous background tasks in separate context
- **Hooks**: React to events (validate, log, transform, block)
- **MCP Servers**: Integrate external tools, databases, APIs
- **LSP Servers**: Code intelligence (diagnostics, go-to-definition)
- **Plugins**: Bundle any of the above for distribution

## Key Points

- Start simple (commands), grow as needed (skills → plugins)
- Extensions are composable: plugins bundle skills, skills define hooks
- User scope overrides project scope for same-named extensions
```

**Step 2: Create when-to-use.md**

```markdown
---
id: when-to-use
topic: Choosing the Right Extension Type
category: overview
tags: [decision, selection, guidance]
requires: [extension-types]
related_to: [precedence]
official_docs: https://code.claude.com/docs/llms.txt
---

# Choosing the Right Extension Type

Decision guide for selecting the appropriate extension.

## Decision Tree

| Need | Extension |
|------|-----------|
| Simple prompt injection, no logic | Command |
| Complex workflow with verification | Skill |
| Autonomous background task | Agent |
| React to events automatically | Hook |
| Integrate external tools/APIs | MCP Server |
| Code intelligence (types, diagnostics) | LSP Server |
| Distribute to others | Plugin |

## When to Use Commands

- One-shot prompt templates
- Team standardization of prompts
- No conditional logic needed
- Quick setup, immediate use

## When to Use Skills

- Multi-step procedures
- "If X then Y otherwise Z" logic
- Quality gates and verification
- Reusable across projects

## When to Use Agents

- Long-running analysis
- Parallel work streams
- Tasks needing separate context
- Specialized autonomous workers

## When to Use Hooks

- Validate before tool execution
- Log or audit operations
- Transform inputs/outputs
- Block dangerous operations

## Key Points

- Commands → Skills: When you need conditional logic
- Skills → Plugins: When you need distribution
- If event-driven: Always hooks
- If external integration: Always MCP
```

**Step 3: Create precedence.md**

```markdown
---
id: precedence
topic: Configuration Precedence
category: overview
tags: [scope, priority, settings, override]
requires: [extension-types]
related_to: [settings-scopes]
official_docs: https://code.claude.com/en/settings
---

# Configuration Precedence

How configurations override each other across scopes.

## Precedence Order (Highest to Lowest)

1. **Managed** — `managed-settings.json` (cannot be overridden)
2. **Command line** — Flags passed to `claude`
3. **Local** — `.claude/settings.local.json`
4. **Project** — `.claude/settings.json`
5. **User** — `~/.claude/settings.json`

## File Locations

| Scope | Path | Shared |
|-------|------|--------|
| Managed | `/Library/Application Support/ClaudeCode/` | By IT |
| User | `~/.claude/` | No |
| Project | `.claude/` | Yes (git) |
| Local | `.claude/*.local.*` | No |

## Override Rules

- Higher scope always wins
- **Deny always wins**: Any deny blocks regardless of allows elsewhere
- Same-scope conflicts: More specific wins
- User extensions override project with same name

## Key Points

- Managed settings enforce organizational policy
- Local settings for personal project overrides
- Project settings for team-shared configuration
- Test in local before promoting to project
```

**Step 4: Commit**

```bash
git add docs/extension-reference/overview/
git commit -m "docs: add extension-reference overview files"
```

---

## Task 3: Commands Files (4 files)

**Files:**
- Create: `docs/extension-reference/commands/commands-overview.md`
- Create: `docs/extension-reference/commands/commands-frontmatter.md`
- Create: `docs/extension-reference/commands/commands-arguments.md`
- Create: `docs/extension-reference/commands/commands-examples.md`

**Step 1: Create commands-overview.md**

```markdown
---
id: commands-overview
topic: Commands Overview
category: commands
tags: [commands, slash, prompt, template]
related_to: [commands-frontmatter, commands-arguments, skills-overview]
official_docs: https://code.claude.com/en/slash-commands
---

# Commands Overview

Commands are markdown files that inject prompts into conversations. Simplest extension type.

## Purpose

- Repetitive prompt templates
- Team standardization
- Quick workflow shortcuts
- No logic, just injection

## Locations

| Scope | Path |
|-------|------|
| Project | `.claude/commands/<name>.md` |
| User | `~/.claude/commands/<name>.md` |

User commands override project commands with the same name.

## Invocation

```
/<command-name>
/<command-name> arguments here
```

## When to Use

Use commands when:
- Simple prompt injection
- No conditional logic
- One-shot execution
- Quick team standardization

Use skills instead when:
- Complex multi-step workflow
- "If X then Y" logic needed
- Verification steps required

## Key Points

- Markdown file = slash command
- User scope overrides project scope
- No logic, just prompt templates
- Arguments via `$ARGUMENTS` or `$1`, `$2`
```

**Step 2: Create commands-frontmatter.md**

```markdown
---
id: commands-frontmatter
topic: Command Frontmatter Schema
category: commands
tags: [frontmatter, yaml, schema, configuration]
requires: [commands-overview]
related_to: [commands-arguments]
official_docs: https://code.claude.com/en/slash-commands
---

# Command Frontmatter Schema

YAML frontmatter configures command behavior.

## Full Schema

```yaml
---
description: Brief description shown in slash menu (required)
argument-hint: <file> [options]     # Hint for expected arguments
model: claude-sonnet-4-20250514     # Model override
allowed-tools: Read, Glob, Grep     # Restrict available tools
hooks:                               # Component-scoped hooks
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
---
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Shown in slash menu and Skill tool |
| `argument-hint` | string | No | Hint shown for expected arguments |
| `model` | string | No | Override model for this command |
| `allowed-tools` | string | No | Comma-separated tool whitelist |
| `hooks` | object | No | Component-scoped hook definitions |

## Key Points

- Only `description` is required
- `allowed-tools` restricts what tools command can use
- Component-scoped hooks run only during command execution
- Model override useful for complex prompts needing Opus
```

**Step 3: Create commands-arguments.md**

```markdown
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

## Bash Execution

Execute commands before prompt injection with backticks and `!`:

```markdown
Current branch: `!git branch --show-current`
Recent commits: `!git log --oneline -5`
Status: `!git status --short`
```

Output is inserted where the backticks appear.

## File References

Include file contents with `@`:

```markdown
Review this file: @src/main.ts
Consider these patterns: @src/patterns/
```

## Combined Example

```markdown
---
description: Review changes on current branch
---

Branch: `!git branch --show-current`
Diff from main: `!git diff main --stat`

Review these changes for:
- Bugs and edge cases
- Security issues
- Code style

User focus: $ARGUMENTS
```

## Key Points

- `$ARGUMENTS` for full argument string
- `$1`, `$2` for positional arguments
- `` `!command` `` executes bash, injects output
- `@path` includes file contents
```

**Step 4: Create commands-examples.md**

```markdown
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

## Key Points

- Keep commands focused on one task
- Use `allowed-tools` to limit scope
- Combine bash execution with file references
- Provide clear `argument-hint` for complex commands
```

**Step 5: Commit**

```bash
git add docs/extension-reference/commands/
git commit -m "docs: add extension-reference commands files"
```

---

## Task 4: Skills Files (6 files)

**Files:**
- Create: `docs/extension-reference/skills/skills-overview.md`
- Create: `docs/extension-reference/skills/skills-frontmatter.md`
- Create: `docs/extension-reference/skills/skills-invocation.md`
- Create: `docs/extension-reference/skills/skills-context-fork.md`
- Create: `docs/extension-reference/skills/skills-content-sections.md`
- Create: `docs/extension-reference/skills/skills-examples.md`

**Step 1: Create all 6 skills files**

See source: `docs/claude-code-extension-system.md` Skills section (lines ~200-400)

Each file follows the frontmatter schema with:
- `id`: skills-overview, skills-frontmatter, etc.
- `category`: skills
- `requires`: skills-overview for non-overview files
- `related_to`: sibling skills files
- `official_docs`: https://code.claude.com/en/skills

Content extracted from source, split by topic:
- overview: purpose, location, when to use
- frontmatter: full schema with all fields
- invocation: three paths (manual, Skill tool, auto-discovery)
- context-fork: isolation with `context: fork`
- content-sections: 8 mandatory sections, risk tiering
- examples: complete working skill

**Step 2: Commit**

```bash
git add docs/extension-reference/skills/
git commit -m "docs: add extension-reference skills files"
```

---

## Task 5: Agents Files (7 files)

**Files:**
- Create: `docs/extension-reference/agents/agents-overview.md`
- Create: `docs/extension-reference/agents/agents-frontmatter.md`
- Create: `docs/extension-reference/agents/agents-builtin.md`
- Create: `docs/extension-reference/agents/agents-task-tool.md`
- Create: `docs/extension-reference/agents/agents-resumable.md`
- Create: `docs/extension-reference/agents/agents-permissions.md`
- Create: `docs/extension-reference/agents/agents-examples.md`

**Step 1: Create all 7 agents files**

See source: `docs/claude-code-extension-system.md` Subagents section

Content split by topic:
- overview: purpose, location, when to use
- frontmatter: full schema (description, prompt, tools, model, skills, permissionMode, hooks)
- builtin: general-purpose, Plan, Explore types
- task-tool: Task tool invocation syntax
- resumable: agentId, resume parameter, transcript storage
- permissions: 6 permission modes table
- examples: complete working agent

**Step 2: Commit**

```bash
git add docs/extension-reference/agents/
git commit -m "docs: add extension-reference agents files"
```

---

## Task 6: Hooks Files (8 files)

**Files:**
- Create: `docs/extension-reference/hooks/hooks-overview.md`
- Create: `docs/extension-reference/hooks/hooks-events.md`
- Create: `docs/extension-reference/hooks/hooks-types.md`
- Create: `docs/extension-reference/hooks/hooks-configuration.md`
- Create: `docs/extension-reference/hooks/hooks-matchers.md`
- Create: `docs/extension-reference/hooks/hooks-exit-codes.md`
- Create: `docs/extension-reference/hooks/hooks-environment.md`
- Create: `docs/extension-reference/hooks/hooks-examples.md`

**Step 1: Create all 8 hooks files**

See source: `docs/claude-code-extension-system.md` Hooks section

Critical content:
- events: all 10 event types with can-block column
- types: command, prompt, agent (plugins only)
- configuration: JSON schema structure
- matchers: patterns (Bash, Bash(cmd), Bash(prefix:*), *)
- exit-codes: 0=allow, 1=error-proceed, 2=block
- environment: CLAUDE_PROJECT_DIR, TOOL_INPUT, TOOL_OUTPUT, CLAUDE_ENV_FILE

**Step 2: Commit**

```bash
git add docs/extension-reference/hooks/
git commit -m "docs: add extension-reference hooks files"
```

---

## Task 7: MCP Files (7 files)

**Files:**
- Create: `docs/extension-reference/mcp/mcp-overview.md`
- Create: `docs/extension-reference/mcp/mcp-transports.md`
- Create: `docs/extension-reference/mcp/mcp-scopes.md`
- Create: `docs/extension-reference/mcp/mcp-authentication.md`
- Create: `docs/extension-reference/mcp/mcp-resources.md`
- Create: `docs/extension-reference/mcp/mcp-managed.md`
- Create: `docs/extension-reference/mcp/mcp-examples.md`

**Step 1: Create all 7 MCP files**

See source: `docs/claude-code-extension-system.md` MCP Servers section

Content split:
- overview: purpose, registration commands
- transports: HTTP, SSE (deprecated), stdio
- scopes: local, project, user
- authentication: OAuth flow, /mcp command
- resources: @ mentions, prompts as commands
- managed: managed-mcp.json, allowedMcpServers, deniedMcpServers

**Step 2: Commit**

```bash
git add docs/extension-reference/mcp/
git commit -m "docs: add extension-reference mcp files"
```

---

## Task 8: LSP Files (3 files)

**Files:**
- Create: `docs/extension-reference/lsp/lsp-overview.md`
- Create: `docs/extension-reference/lsp/lsp-configuration.md`
- Create: `docs/extension-reference/lsp/lsp-examples.md`

**Step 1: Create all 3 LSP files**

See source: `docs/claude-code-extension-system.md` LSP Servers section

Key points:
- Plugin-only component
- Configuration in `.lsp.json`
- extensionToLanguage mapping
- Available plugins: pyright-lsp, typescript-lsp, rust-lsp

**Step 2: Commit**

```bash
git add docs/extension-reference/lsp/
git commit -m "docs: add extension-reference lsp files"
```

---

## Task 9: Plugins Files (6 files)

**Files:**
- Create: `docs/extension-reference/plugins/plugins-overview.md`
- Create: `docs/extension-reference/plugins/plugins-manifest.md`
- Create: `docs/extension-reference/plugins/plugins-components.md`
- Create: `docs/extension-reference/plugins/plugins-paths.md`
- Create: `docs/extension-reference/plugins/plugins-caching.md`
- Create: `docs/extension-reference/plugins/plugins-examples.md`

**Step 1: Create all 6 plugins files**

See source: `docs/claude-code-extension-system.md` Plugins section

Content split:
- overview: purpose, directory structure
- manifest: plugin.json schema (all fields)
- components: 6 types (commands, skills, agents, hooks, mcp, lsp)
- paths: `./` prefix, `${CLAUDE_PLUGIN_ROOT}`
- caching: cache location, two-step installation
- examples: complete plugin manifest

**Step 2: Commit**

```bash
git add docs/extension-reference/plugins/
git commit -m "docs: add extension-reference plugins files"
```

---

## Task 10: Marketplaces Files (4 files)

**Files:**
- Create: `docs/extension-reference/marketplaces/marketplaces-overview.md`
- Create: `docs/extension-reference/marketplaces/marketplaces-schema.md`
- Create: `docs/extension-reference/marketplaces/marketplaces-sources.md`
- Create: `docs/extension-reference/marketplaces/marketplaces-examples.md`

**Step 1: Create all 4 marketplaces files**

See source: `docs/claude-code-extension-system.md` Marketplaces section

Content split:
- overview: purpose, commands
- schema: marketplace.json fields
- sources: relative, github, git, url, npm, file, directory
- examples: complete marketplace.json

**Step 2: Commit**

```bash
git add docs/extension-reference/marketplaces/
git commit -m "docs: add extension-reference marketplaces files"
```

---

## Task 11: Settings Files (6 files)

**Files:**
- Create: `docs/extension-reference/settings/settings-overview.md`
- Create: `docs/extension-reference/settings/settings-scopes.md`
- Create: `docs/extension-reference/settings/settings-permissions.md`
- Create: `docs/extension-reference/settings/settings-sandbox.md`
- Create: `docs/extension-reference/settings/settings-schema.md`
- Create: `docs/extension-reference/settings/settings-examples.md`

**Step 1: Create all 6 settings files**

See source: `docs/claude-code-extension-system.md` Settings section

Content split:
- overview: purpose, file locations
- scopes: managed, user, project, local
- permissions: allow/ask/deny syntax, patterns
- sandbox: enabled, excludedCommands, network settings
- schema: all settings.json fields
- examples: complete settings.json

**Step 2: Commit**

```bash
git add docs/extension-reference/settings/
git commit -m "docs: add extension-reference settings files"
```

---

## Task 12: Security Files (4 files)

**Files:**
- Create: `docs/extension-reference/security/security-managed.md`
- Create: `docs/extension-reference/security/security-mcp-restrictions.md`
- Create: `docs/extension-reference/security/security-marketplace-restrictions.md`
- Create: `docs/extension-reference/security/security-hooks-restrictions.md`

**Step 1: Create all 4 security files**

See source: `docs/claude-code-extension-system.md` Security section

Content split:
- managed: managed-settings.json locations, precedence
- mcp-restrictions: allowedMcpServers, deniedMcpServers, managed-mcp.json
- marketplace-restrictions: strictKnownMarketplaces
- hooks-restrictions: allowManagedHooksOnly, disableAllHooks

**Step 2: Commit**

```bash
git add docs/extension-reference/security/
git commit -m "docs: add extension-reference security files"
```

---

## Task 13: Validation

**Step 1: Verify all files exist**

```bash
find docs/extension-reference -name "*.md" | wc -l
```

Expected: 59 (1 index + 58 content files)

**Step 2: Verify frontmatter validity**

```bash
for f in docs/extension-reference/**/*.md; do
  head -1 "$f" | grep -q "^---$" || echo "Missing frontmatter: $f"
done
```

Expected: No output (all files have frontmatter)

**Step 3: Check cross-references**

Verify all `requires` and `related_to` IDs exist as files:
- Extract all referenced IDs
- Check each has corresponding `.md` file

**Step 4: Final commit**

```bash
git add docs/extension-reference/
git commit -m "docs: complete extension-reference with validation"
```

---

## Verification Checklist

- [ ] 59 total markdown files created
- [ ] All files have valid YAML frontmatter
- [ ] All `requires` references point to existing files
- [ ] All `related_to` references point to existing files
- [ ] Tags are consistent within categories
- [ ] Each file is self-contained
- [ ] Content matches source documentation
