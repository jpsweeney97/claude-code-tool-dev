# Extension Reference Documentation Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 6 documentation fixes: 2 critical (broken cross-ref, PostToolUseFailure), 2 important (CLAUDE.md chunking, expand thin files), 2 nice-to-have (agents-getting-started, cross-ref standardization).

**Architecture:** Atomic documentation updates with verification after each phase. Memory/ chunking splits source into 9 focused files. Expansions pull from official docs.

**Tech Stack:** Markdown, YAML frontmatter, bash verification commands

---

## Task 1: Fix Broken Cross-Reference

**Files:**
- Modify: `docs/extension-reference/marketplaces/marketplaces-restrictions.md:7`

**Step 1: Read file to confirm current state**

Run: `sed -n '7p' docs/extension-reference/marketplaces/marketplaces-restrictions.md`
Expected: `related_to: [marketplaces-sources, settings-managed, security-managed]`

**Step 2: Remove invalid reference**

Edit line 7 from:
```yaml
related_to: [marketplaces-sources, settings-managed, security-managed]
```
To:
```yaml
related_to: [marketplaces-sources, security-managed]
```

**Step 3: Verify fix**

Run: `grep -r "settings-managed" docs/extension-reference/`
Expected: No output (reference removed)

**Step 4: Commit**

```bash
git add docs/extension-reference/marketplaces/marketplaces-restrictions.md
git commit -m "fix(extension-reference): remove broken settings-managed cross-ref"
```

---

## Task 2: Add PostToolUseFailure Event

**Files:**
- Modify: `docs/extension-reference/hooks/hooks-events.md:13,20,33,91,99`

**Step 1: Update event count (line 13)**

Edit from:
```markdown
Claude Code supports 11 hook event types.
```
To:
```markdown
Claude Code supports 12 hook event types.
```

**Step 2: Add event to reference table (after line 20)**

Insert after the PostToolUse row:
```markdown
| `PostToolUseFailure` | After tool execution fails | No | Error handling, retry logic |
```

**Step 3: Update matcher section header (line 33)**

Edit from:
```markdown
### PreToolUse / PostToolUse / PermissionRequest
```
To:
```markdown
### PreToolUse / PostToolUse / PostToolUseFailure / PermissionRequest
```

**Step 4: Add to Non-Blocking Events section (after line 91)**

Edit from:
```markdown
- `PostToolUse` - Exit code ignored
```
To:
```markdown
- `PostToolUse` - Exit code ignored
- `PostToolUseFailure` - Exit code ignored
```

**Step 5: Update Key Points event count (line 99)**

Edit from:
```markdown
- 11 events, 6 can block operations
```
To:
```markdown
- 12 events, 6 can block operations
```

**Step 6: Verify changes**

Run: `grep -c "PostToolUseFailure" docs/extension-reference/hooks/hooks-events.md`
Expected: `3` (table row, matcher section, non-blocking list)

Run: `grep "12" docs/extension-reference/hooks/hooks-events.md`
Expected: Two lines (intro and key points)

**Step 7: Commit**

```bash
git add docs/extension-reference/hooks/hooks-events.md
git commit -m "feat(extension-reference): add PostToolUseFailure hook event"
```

---

## Task 3: Create Memory Directory Structure

**Files:**
- Create: `docs/extension-reference/memory/` directory
- Modify: `docs/extension-reference/_index.md:27`

**Step 1: Create directory**

```bash
mkdir -p docs/extension-reference/memory
```

**Step 2: Update index with memory category**

After line 27 (`| [security/](./security/) | 4 | Managed deployment |`), insert:
```markdown
| [memory/](./memory/) | 9 | CLAUDE.md, rules, imports |
```

**Step 3: Verify directory exists**

Run: `test -d docs/extension-reference/memory && echo "exists"`
Expected: `exists`

**Step 4: Commit**

```bash
git add docs/extension-reference/_index.md docs/extension-reference/memory
git commit -m "feat(extension-reference): add memory category to index"
```

---

## Task 4: Create memory-overview.md

**Files:**
- Create: `docs/extension-reference/memory/memory-overview.md`
- Source: `docs/documentation/claude.md-reference.md:1-23`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-overview.md`:
```markdown
---
id: memory-overview
topic: Memory System Overview
category: memory
tags: [memory, claude.md, hierarchy, precedence]
related_to: [memory-imports, memory-rules-overview, precedence]
official_docs: https://code.claude.com/en/memory
---

# Memory System Overview

Claude Code offers five memory locations in a hierarchical structure.

## Memory Types

| Memory Type | Location | Purpose | Shared With |
|-------------|----------|---------|-------------|
| Enterprise policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Organization-wide instructions | All org users |
| Project memory | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project instructions | Team via VCS |
| Project rules | `./.claude/rules/*.md` | Modular, topic-specific rules | Team via VCS |
| User memory | `~/.claude/CLAUDE.md` | Personal preferences | Just you |
| Project local | `./CLAUDE.local.md` | Personal project-specific | Just you |

## Precedence

Files higher in the hierarchy take precedence and load first. Project rules have same priority as `.claude/CLAUDE.md`.

## Loading Behavior

All memory files are automatically loaded into context when Claude Code launches. CLAUDE.local.md files are automatically added to .gitignore.

## Key Points

- Five memory locations with hierarchical precedence
- Enterprise > Project > User > Local
- All loaded automatically at launch
- Rules have same priority as CLAUDE.md
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-overview.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-overview.md
git commit -m "docs(extension-reference): add memory-overview.md"
```

---

## Task 5: Create memory-imports.md

**Files:**
- Create: `docs/extension-reference/memory/memory-imports.md`
- Source: `docs/documentation/claude.md-reference.md:25-49`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-imports.md`:
```markdown
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
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-imports.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-imports.md
git commit -m "docs(extension-reference): add memory-imports.md"
```

---

## Task 6: Create memory-lookup.md

**Files:**
- Create: `docs/extension-reference/memory/memory-lookup.md`
- Source: `docs/documentation/claude.md-reference.md:51-56`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-lookup.md`:
```markdown
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
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-lookup.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-lookup.md
git commit -m "docs(extension-reference): add memory-lookup.md"
```

---

## Task 7: Create memory-commands.md

**Files:**
- Create: `docs/extension-reference/memory/memory-commands.md`
- Source: `docs/documentation/claude.md-reference.md:57-78`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-commands.md`:
```markdown
---
id: memory-commands
topic: Memory Commands
category: memory
tags: [memory, commands, init]
requires: [memory-overview]
related_to: [memory-rules-overview]
official_docs: https://code.claude.com/en/memory
---

# Memory Commands

Two slash commands manage memory files.

## /memory

Opens any memory file in your system editor for extensive additions or organization.

```
/memory
```

Shows loaded memory files and allows editing.

## /init

Bootstraps a CLAUDE.md file for your codebase.

```
/init
```

Creates project memory in `./CLAUDE.md` or `./.claude/CLAUDE.md`.

## Recommended Content

| Category | Examples |
|----------|----------|
| Frequently used commands | Build, test, lint commands |
| Code style preferences | Naming conventions, formatting |
| Architectural patterns | Project-specific patterns |
| Team workflows | PR process, deployment |

## Key Points

- `/memory` — View and edit loaded memory files
- `/init` — Bootstrap new project memory
- Project memory stored in `./CLAUDE.md` or `./.claude/CLAUDE.md`
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-commands.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-commands.md
git commit -m "docs(extension-reference): add memory-commands.md"
```

---

## Task 8: Create memory-rules-overview.md

**Files:**
- Create: `docs/extension-reference/memory/memory-rules-overview.md`
- Source: `docs/documentation/claude.md-reference.md:80-98`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-rules-overview.md`:
```markdown
---
id: memory-rules-overview
topic: Rules Directory Overview
category: memory
tags: [memory, rules, modular]
requires: [memory-overview]
related_to: [memory-rules-paths, memory-rules-organization]
official_docs: https://code.claude.com/en/memory
---

# Rules Directory Overview

The `.claude/rules/` directory provides modular, topic-focused instructions as an alternative to a single large CLAUDE.md.

## Basic Structure

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

## Loading Behavior

All `.md` files in `.claude/rules/` are automatically loaded as project memory with the same priority as `.claude/CLAUDE.md`.

## When to Use Rules

| Scenario | Approach |
|----------|----------|
| Small project | Single CLAUDE.md |
| Large project | CLAUDE.md + rules/ |
| Team collaboration | Rules for shared standards |
| Personal preferences | User rules in `~/.claude/rules/` |

## Key Points

- Rules provide modular alternative to single CLAUDE.md
- All `.md` files in `.claude/rules/` auto-loaded
- Same priority as `.claude/CLAUDE.md`
- Use for larger projects with distinct concerns
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-rules-overview.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-rules-overview.md
git commit -m "docs(extension-reference): add memory-rules-overview.md"
```

---

## Task 9: Create memory-rules-paths.md

**Files:**
- Create: `docs/extension-reference/memory/memory-rules-paths.md`
- Source: `docs/documentation/claude.md-reference.md:100-145`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-rules-paths.md`:
```markdown
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
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-rules-paths.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-rules-paths.md
git commit -m "docs(extension-reference): add memory-rules-paths.md"
```

---

## Task 10: Create memory-rules-organization.md

**Files:**
- Create: `docs/extension-reference/memory/memory-rules-organization.md`
- Source: `docs/documentation/claude.md-reference.md:147-176`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-rules-organization.md`:
```markdown
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
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-rules-organization.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-rules-organization.md
git commit -m "docs(extension-reference): add memory-rules-organization.md"
```

---

## Task 11: Create memory-managed.md

**Files:**
- Create: `docs/extension-reference/memory/memory-managed.md`
- Source: `docs/documentation/claude.md-reference.md:178-208`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-managed.md`:
```markdown
---
id: memory-managed
topic: Managed Memory Deployment
category: memory
tags: [memory, enterprise, managed, deployment]
requires: [memory-overview]
related_to: [security-managed]
official_docs: https://code.claude.com/en/memory
---

# Managed Memory Deployment

Organizations can deploy centrally managed CLAUDE.md files that apply to all users.

## Enterprise Policy Locations

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

## Deployment Process

1. Create the managed memory file at the enterprise policy location
2. Deploy via configuration management (MDM, Group Policy, Ansible, etc.)
3. File applies to all users on the machine

## Use Cases

| Use Case | Example Content |
|----------|-----------------|
| Coding standards | Language-specific conventions |
| Security policies | Credential handling, approved libraries |
| Compliance requirements | Regulatory documentation, audit trails |
| Tool configurations | Build commands, deployment targets |

## Precedence

Enterprise policy has highest precedence, loading first and overriding all other memory sources.

| Priority | Source |
|----------|--------|
| 1 (highest) | Enterprise policy |
| 2 | Project memory |
| 3 | User memory |
| 4 (lowest) | Project local |

## Key Points

- Deploy to platform-specific enterprise location
- Use configuration management for distribution
- Highest precedence in memory hierarchy
- Cannot be overridden by users or projects
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-managed.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-managed.md
git commit -m "docs(extension-reference): add memory-managed.md"
```

---

## Task 12: Create memory-best-practices.md

**Files:**
- Create: `docs/extension-reference/memory/memory-best-practices.md`
- Source: `docs/documentation/claude.md-reference.md:209-215`

**Step 1: Create file**

Create `docs/extension-reference/memory/memory-best-practices.md`:
```markdown
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
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/memory/memory-best-practices.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/memory/memory-best-practices.md
git commit -m "docs(extension-reference): add memory-best-practices.md"
```

---

## Task 13: Verify Memory Directory Complete

**Step 1: Count files**

Run: `ls docs/extension-reference/memory/ | wc -l`
Expected: `9`

**Step 2: List all files**

Run: `ls -la docs/extension-reference/memory/`
Expected: 9 markdown files

**Step 3: Verify index updated**

Run: `grep "memory/" docs/extension-reference/_index.md`
Expected: `| [memory/](./memory/) | 9 | CLAUDE.md, rules, imports |`

---

## Task 14: Expand lsp-overview.md

**Files:**
- Modify: `docs/extension-reference/lsp/lsp-overview.md`
- Source: `docs/documentation/plugins-reference.md:175-280`

**Step 1: Read current file**

Read `docs/extension-reference/lsp/lsp-overview.md` to understand current content.

**Step 2: Read source content**

Read `docs/documentation/plugins-reference.md` lines 175-280 for expansion content.

**Step 3: Add config schema section after "How LSP Works"**

Add new section:
```markdown
## Configuration Schema

LSP configuration in `manifest.json`:

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Command to start server |
| `args` | string[] | Command arguments |
| `env` | object | Environment variables |
| `initializationOptions` | object | LSP init options |
| `languages` | string[] | Language IDs to activate |
| `filePatterns` | string[] | Glob patterns for activation |

## Transport Options

| Transport | Use Case |
|-----------|----------|
| stdio | Default, most common |
| tcp | Network-based servers |
| pipe | Named pipe communication |
```

**Step 4: Add debug logging section**

Add before "Key Points":
```markdown
## Debug Logging

Enable LSP debug output:

```json
{
  "lsp": {
    "debug": true,
    "logFile": "/tmp/lsp-debug.log"
  }
}
```

| Setting | Purpose |
|---------|---------|
| `debug` | Enable verbose logging |
| `logFile` | Write logs to file |
| `traceServer` | Log server communication |
```

**Step 5: Verify line count**

Run: `wc -l docs/extension-reference/lsp/lsp-overview.md`
Expected: >= 100 lines

**Step 6: Commit**

```bash
git add docs/extension-reference/lsp/lsp-overview.md
git commit -m "docs(extension-reference): expand lsp-overview with config and debug"
```

---

## Task 15: Expand security-managed.md

**Files:**
- Modify: `docs/extension-reference/security/security-managed.md`
- Source: `docs/documentation/settings-reference.md:82-98,315-336,466-644`

**Step 1: Read current file**

Read `docs/extension-reference/security/security-managed.md` to understand current content.

**Step 2: Read source sections**

Read relevant sections from `docs/documentation/settings-reference.md`.

**Step 3: Add MCP restriction details after "Configuration Enforcement"**

Add new section:
```markdown
## MCP Server Restrictions

Control which MCP servers users can enable:

| Setting | Purpose |
|---------|---------|
| `allowedMcpServers` | Allowlist of permitted servers |
| `blockedMcpServers` | Denylist of prohibited servers |

### Allowlist Configuration

```json
{
  "allowedMcpServers": ["filesystem", "github", "custom-server"]
}
```

When set, only listed servers can be enabled. Empty array blocks all.

### Denylist Configuration

```json
{
  "blockedMcpServers": ["dangerous-server"]
}
```

Blocked servers cannot be enabled regardless of other settings.
```

**Step 4: Add hook restrictions section**

```markdown
## Hook Restrictions

Control hook execution in managed environments:

| Setting | Effect |
|---------|--------|
| `disableHooks` | Disable all hook execution |
| `allowedHookEvents` | Limit which events can trigger hooks |
| `hookTimeout` | Maximum hook execution time |

### Disable All Hooks

```json
{
  "disableHooks": true
}
```

### Restrict Hook Events

```json
{
  "allowedHookEvents": ["SessionStart", "SessionEnd"]
}
```
```

**Step 5: Add marketplace restrictions section**

```markdown
## Marketplace Restrictions

See [marketplaces-restrictions](../marketplaces/marketplaces-restrictions.md) for detailed allowlist configuration using `strictKnownMarketplaces`.
```

**Step 6: Verify line count**

Run: `wc -l docs/extension-reference/security/security-managed.md`
Expected: >= 120 lines

**Step 7: Commit**

```bash
git add docs/extension-reference/security/security-managed.md
git commit -m "docs(extension-reference): expand security-managed with restriction details"
```

---

## Task 16: Expand precedence.md

**Files:**
- Modify: `docs/extension-reference/overview/precedence.md`
- Source: `docs/documentation/settings-reference.md:46-69,311-346`

**Step 1: Read current file**

Read `docs/extension-reference/overview/precedence.md` to understand current content.

**Step 2: Add scope interactions section after "Resolution Order"**

```markdown
## Scope Interactions

When settings exist at multiple scopes, they interact based on type:

| Setting Type | Behavior |
|--------------|----------|
| Scalar (string, number, boolean) | Higher scope wins |
| Array | Merged (higher scope first) |
| Object | Deep merged (higher scope wins conflicts) |

### Scalar Example

```
Managed: { "theme": "dark" }
User:    { "theme": "light" }
Result:  { "theme": "dark" }  # Managed wins
```

### Array Merge Example

```
Managed: { "blockedTools": ["dangerous"] }
User:    { "blockedTools": ["risky"] }
Result:  { "blockedTools": ["dangerous", "risky"] }  # Merged
```
```

**Step 3: Add examples section**

```markdown
## Common Scenarios

### Organization Lockdown

Managed settings enforce security, project customizes for workflow:

```
Managed: { "disableWebSearch": true }
Project: { "defaultModel": "sonnet" }
User:    { "theme": "dark" }
Result:  All three apply (no conflicts)
```

### Setting Override Attempts

User cannot override managed settings:

```
Managed: { "maxTokens": 1000 }
User:    { "maxTokens": 5000 }
Result:  { "maxTokens": 1000 }  # Managed wins
```
```

**Step 4: Verify line count**

Run: `wc -l docs/extension-reference/overview/precedence.md`
Expected: >= 80 lines

**Step 5: Commit**

```bash
git add docs/extension-reference/overview/precedence.md
git commit -m "docs(extension-reference): expand precedence with scope interactions"
```

---

## Task 17: Expand extension-types.md

**Files:**
- Modify: `docs/extension-reference/overview/extension-types.md`
- Source: `docs/claude-code-extension-system.md:27-106`

**Step 1: Read current file**

Read `docs/extension-reference/overview/extension-types.md` to understand current content.

**Step 2: Add design philosophy section after capability comparison**

```markdown
## Design Philosophy

### Composition Over Inheritance

Extensions compose rather than inherit. A plugin bundles commands, skills, and hooks but doesn't create a new extension type.

### Single Responsibility

Each extension type serves one purpose:
- Commands: User-invoked actions
- Skills: Domain knowledge for Claude
- Hooks: Event-driven automation
- Agents: Autonomous task execution

### Progressive Disclosure

Start simple, add complexity as needed:
1. Command for single action
2. Skill for domain expertise
3. Hook for automation
4. Agent for autonomy
5. Plugin for distribution
```

**Step 3: Add decision guide section**

```markdown
## Decision Guide

### "I want Claude to..."

| Goal | Extension |
|------|-----------|
| Run a specific action when I type `/foo` | Command |
| Know how to do X better | Skill |
| React automatically when Y happens | Hook |
| Work independently on complex tasks | Agent |
| Share my extensions with others | Plugin |

### Complexity Indicators

| Signal | Suggests |
|--------|----------|
| User explicitly triggers | Command |
| Claude needs domain knowledge | Skill |
| "Whenever X, do Y" | Hook |
| Multiple steps, decisions | Agent |
| Bundle for distribution | Plugin |
```

**Step 4: Verify line count**

Run: `wc -l docs/extension-reference/overview/extension-types.md`
Expected: >= 80 lines

**Step 5: Commit**

```bash
git add docs/extension-reference/overview/extension-types.md
git commit -m "docs(extension-reference): expand extension-types with philosophy and guide"
```

---

## Task 18: Create agents-getting-started.md

**Files:**
- Create: `docs/extension-reference/agents/agents-getting-started.md`
- Pattern: `docs/extension-reference/skills/skills-getting-started.md`

**Step 1: Create file following skills-getting-started pattern**

Create `docs/extension-reference/agents/agents-getting-started.md`:
```markdown
---
id: agents-getting-started
topic: Creating Your First Agent
category: agents
tags: [tutorial, getting-started, example]
related_to: [agents-overview, agents-task-tool, agents-examples]
official_docs: https://code.claude.com/en/agents
---

# Creating Your First Agent

This tutorial creates a project agent that explores codebases to answer architectural questions.

## Prerequisites

- Claude Code installed and configured
- A codebase to explore

## Step 1: Check Available Agents

Before creating an agent, see what agents Claude already has access to:

```
What agents are available?
```

Claude lists any currently loaded agents from plugins or your organization.

## Step 2: Create the Agent Directory

Create a directory for the agent in your project:

```bash
mkdir -p .claude/agents
```

For personal agents available across projects, use `~/.claude/agents/` instead.

## Step 3: Write the Agent Definition

Create `.claude/agents/architecture-explorer.md`:

```markdown
---
name: architecture-explorer
description: Explores codebase architecture. Use for questions about structure, patterns, dependencies, or "how is this organized?"
tools: [Read, Glob, Grep, LS]
---

When exploring architecture:

1. **Map the structure**: Use Glob to find key directories and file patterns
2. **Identify entry points**: Find main files, index files, configuration
3. **Trace dependencies**: Use Grep to follow imports and references
4. **Summarize patterns**: Note naming conventions, file organization, layering

Report findings as:
- Directory structure overview
- Key architectural decisions observed
- Notable patterns or conventions
- Potential areas of concern
```

## Step 4: Verify the Agent Loads

Agents load automatically. Verify:

```
What agents are available?
```

You should see `architecture-explorer` with its description.

## Step 5: Test the Agent

Ask a question that matches the agent's description:

```
How is this codebase organized?
```

Claude should invoke the architecture-explorer agent via the Task tool.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not listed | Check path: `.claude/agents/architecture-explorer.md` |
| Agent doesn't trigger | Make description more specific |
| Permission errors | Verify `tools` list includes needed tools |

See [agents-troubleshooting](agents-troubleshooting.md) for detailed diagnostics.

## Next Steps

- [agents-task-tool](agents-task-tool.md) — How Claude invokes agents
- [agents-examples](agents-examples.md) — More agent patterns
- [agents-tools](agents-tools.md) — Available tools for agents

## Key Points

- Agents live in `.claude/agents/<name>.md` (project) or `~/.claude/agents/` (personal)
- `name`, `description`, and `tools` are key frontmatter fields
- Description quality determines when Claude delegates to the agent
- Changes take effect immediately
```

**Step 2: Verify file created**

Run: `test -f docs/extension-reference/agents/agents-getting-started.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add docs/extension-reference/agents/agents-getting-started.md
git commit -m "docs(extension-reference): add agents-getting-started tutorial"
```

---

## Task 19: Standardize agents-overview.md Cross-References

**Files:**
- Modify: `docs/extension-reference/agents/agents-overview.md`

**Step 1: Read current file**

Read `docs/extension-reference/agents/agents-overview.md` to find the "See Also" section.

**Step 2: Rename section**

Change:
```markdown
## See Also
```
To:
```markdown
## Related Topics
```

**Step 3: Verify change**

Run: `grep "## See Also" docs/extension-reference/agents/agents-overview.md`
Expected: No output

Run: `grep "## Related Topics" docs/extension-reference/agents/agents-overview.md`
Expected: `## Related Topics`

**Step 4: Commit**

```bash
git add docs/extension-reference/agents/agents-overview.md
git commit -m "docs(extension-reference): standardize agents-overview cross-refs"
```

---

## Task 20: Standardize marketplaces-walkthrough.md Cross-References

**Files:**
- Modify: `docs/extension-reference/marketplaces/marketplaces-walkthrough.md`

**Step 1: Read current file**

Read `docs/extension-reference/marketplaces/marketplaces-walkthrough.md` to find "Next Steps" and "Learn More" sections.

**Step 2: Merge sections into "Related Topics"**

Replace both sections with single:
```markdown
## Related Topics

- [marketplaces-publishing](marketplaces-publishing.md) — Publish plugins to marketplaces
- [marketplaces-sources](marketplaces-sources.md) — Configure marketplace sources
- [plugins-manifest](../plugins/plugins-manifest.md) — Plugin manifest reference
```

**Step 3: Verify changes**

Run: `grep -E "## (See Also|Learn More|Next Steps)" docs/extension-reference/marketplaces/marketplaces-walkthrough.md`
Expected: No output

Run: `grep "## Related Topics" docs/extension-reference/marketplaces/marketplaces-walkthrough.md`
Expected: `## Related Topics`

**Step 4: Commit**

```bash
git add docs/extension-reference/marketplaces/marketplaces-walkthrough.md
git commit -m "docs(extension-reference): standardize marketplaces-walkthrough cross-refs"
```

---

## Task 21: Final Verification

**Step 1: Verify all cross-reference sections standardized**

Run: `grep -rE "## (See Also|Learn More)" docs/extension-reference/`
Expected: No output (except skills-getting-started which keeps "Next Steps" for tutorials)

**Step 2: Verify memory directory complete**

Run: `ls docs/extension-reference/memory/ | wc -l`
Expected: `9`

**Step 3: Verify PostToolUseFailure added**

Run: `grep -c "PostToolUseFailure" docs/extension-reference/hooks/hooks-events.md`
Expected: `3`

**Step 4: Verify broken cross-ref removed**

Run: `grep "settings-managed" docs/extension-reference/marketplaces/marketplaces-restrictions.md`
Expected: No output

**Step 5: Count total files modified/created**

Run: `git diff --name-only HEAD~20 | wc -l`
Expected: ~19

**Step 6: Final commit for any remaining changes**

```bash
git status
# If clean, done. If changes remain:
git add -A
git commit -m "docs(extension-reference): complete 6-fix implementation"
```

---

## Summary

| Phase | Tasks | Files |
|-------|-------|-------|
| 1 | 1-2 | 2 modified |
| 2 | 3-13 | 9 created, 1 modified |
| 3 | 14-17 | 4 modified |
| 4 | 18 | 1 created |
| 5 | 19-20 | 2 modified |
| Final | 21 | Verification only |

**Total: 21 tasks, 10 new files, 9 modified files**
