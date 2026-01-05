# Claude Code Extension Development Monorepo

**Status:** Approved
**Date:** 2026-01-04

## Problem

Two repos (`superserum`, `claude-skill-dev`) plus orphaned extensions in `~/.claude/` created fragmentation:

| Location | Contents | Deployment |
|----------|----------|------------|
| superserum | 6 plugins | Symlinked to ~/.claude/plugins/ |
| claude-skill-dev | 8 skills, 3 frameworks | Symlinked to ~/.claude/skills/ |
| ~/.claude/skills/ only | 6 skills | No git backup |

**Root cause:** The repos organized existing mess but didn't establish a proactive workflow. New work continued in `~/.claude/` because it was the path of least resistance.

## Solution

A monorepo that makes the sandbox the natural place to work, with explicit promotion to production.

### Core Workflow

```
1. CREATE           2. TEST              3. PROMOTE
───────────         ──────               ─────────
Write extension     Run Claude Code      uv run scripts/promote
in .claude/         inside monorepo      ├─ validates
                    (auto-discovers)     ├─ shows diff
                                         └─ copies to ~/.claude
```

**Why this works:**
- Creating in `.claude/` is natural — Claude Code discovers it automatically
- Testing requires no setup — project-local takes precedence
- Promotion is explicit — you decide when something is ready
- Production stays clean — only validated extensions land in `~/.claude/`

## Directory Structure

```
claude-code-tool-dev/
├── CLAUDE.md                    # Lean, imports from rules/
├── CLAUDE.local.md              # Personal overrides (gitignored)
├── README.md
├── package.json                 # npm workspace root
├── tsconfig.base.json
├── migration-inventory.yaml     # Migration tracking
│
├── .claude/
│   ├── commands/                # Slash commands (markdown)
│   ├── agents/                  # Subagents (markdown)
│   ├── skills/                  # Skills (markdown)
│   ├── hooks/                   # Hook scripts (shell/python)
│   ├── settings.json            # Hook wiring + project config
│   ├── settings.local.json      # Local experiments (gitignored)
│   └── rules/                   # Modular Claude context (auto-discovered)
│       ├── skills.md            # paths: .claude/skills/**
│       ├── hooks.md             # paths: .claude/hooks/**
│       ├── commands.md          # paths: .claude/commands/**
│       ├── agents.md            # paths: .claude/agents/**
│       └── mcp-servers.md       # paths: packages/mcp-servers/**
│
├── packages/                    # npm workspaces
│   ├── mcp-servers/             # TypeScript MCP servers
│   │   └── <server-name>/
│   │       ├── package.json
│   │       ├── tsconfig.json
│   │       ├── src/
│   │       └── dist/            # gitignored
│   └── plugins/                 # Plugin packages
│
├── scripts/
│   ├── promote                  # Promotion script (Python)
│   ├── inventory                # Generate migration inventory (Python)
│   └── migrate                  # Process inventory decisions (Python)
│
├── references/                  # Source material (copy into skills)
│
├── docs/
│   └── plans/                   # Design documents
│
└── tmp/                         # Ephemeral (gitignored)
```

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `promote` | Validate and deploy extensions (copy to ~/.claude/ or register MCP) |
| `sync-settings` | Rebuild settings.json hooks section from hook frontmatter |
| `inventory` | Scan sources, generate migration YAML |
| `migrate` | Process inventory decisions |

**Promote supports all extension types:**

```bash
uv run scripts/promote <type> <name>

# Copy to ~/.claude/<type>/
uv run scripts/promote skill deep-exploration
uv run scripts/promote command deploy
uv run scripts/promote agent code-reviewer
uv run scripts/promote hook block-credentials

# Build + register via claude mcp add
uv run scripts/promote mcp-server my-server
```

---

## Promote Script

**Purpose:** Controlled gate between sandbox and production.

**Usage:**
```bash
uv run scripts/promote <type> <name>
# Examples:
uv run scripts/promote skill my-skill
uv run scripts/promote command deploy
uv run scripts/promote hook pre-commit
uv run scripts/promote agent code-reviewer
```

**Validation pipeline:**

| Step | Check |
|------|-------|
| 1. EXISTS | File exists and is non-empty |
| 2. SYNTAX | Valid YAML/JSON frontmatter (skills) |
| 3. PERMISSIONS | Hook scripts are executable |
| 4. CONFLICT | Warn if name exists in ~/.claude/ |
| 5. DRY-RUN | Show diff of changes |
| 6. CONFIRM | Prompt for approval |
| 7. COPY | Copy to ~/.claude/<type>/ |

**Flags:**
- `--dry-run` — Stop after diff, don't copy
- `--force` — Skip confirmation (for scripting)
- `--all` — Promote all extensions of a type

**Implementation:** Python with PEP 723 inline metadata, run via `uv run`.

**Hook promotion integration:** After copying a hook, promote asks "Also sync settings.json?" and calls sync-settings if confirmed.

---

## Sync-Settings Script

**Purpose:** Rebuild `~/.claude/settings.json` hooks section from hook file frontmatter.

**Important:** Hook frontmatter is a **project convention**, not native Claude Code behavior. Claude Code stores all hook configuration in `settings.json`. This script bridges the gap by parsing our frontmatter and generating the config.

**Scope:**
- Reads hook scripts from `~/.claude/hooks/`
- Parses frontmatter, rebuilds `hooks` section
- Preserves all other settings.json sections (permissions, sandbox, enabledPlugins)
- Does NOT handle MCP servers (use `promote mcp-server`) or plugins (marketplace-managed)

**Hook frontmatter format (PEP 723 style):**
```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60
# ///
```

**Valid events:** `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `Notification`, `PermissionRequest`, `PreCompact`, `SessionStart`, `SessionEnd`

Maps to settings.json:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "~/.claude/hooks/script.py", "timeout": 60}]
    }]
  }
}
```

**Algorithm:**
1. Discover — Glob `~/.claude/hooks/*.{py,sh}`
2. Parse — Extract frontmatter; warn on files without valid frontmatter
3. Validate — Check required fields (`hook-event`, `matcher`)
4. Group — Organize by event type
5. Read — Load current settings.json
6. Diff — Compare current vs generated hooks section
7. Show — Display diff
8. Confirm — Prompt for approval (unless `--force`)
9. Write — Update hooks section, preserve everything else

**Usage:**
```bash
uv run scripts/sync-settings [OPTIONS]
```

**Flags:**
- `--dry-run` — Show diff, don't write
- `--force` — Skip confirmation
- `--quiet` — Only output errors

**Key property:** Deleting a hook file → next sync removes it from settings.json. The hooks section is derived, not hand-edited.

---

## Migration Inventory

**File:** `migration-inventory.yaml`

**Structure:**
```yaml
sources:
  superserum:
    path: /Users/jp/Projects/active/superserum
    status: pending

  claude-skill-dev:
    path: /Users/jp/Projects/active/claude-skill-dev
    status: pending

  orphaned:
    path: ~/.claude/skills
    status: pending

extensions:
  skills:
    # Simple case: single source
    - name: deep-exploration
      source: claude-skill-dev
      decision: migrate    # migrate | archive | delete
      status: pending      # pending | migrated | archived | deleted
      notes: "Core skill, actively used"

    # Conflict case: same name in multiple sources
    - name: foo
      conflict: true
      sources:
        - location: claude-skill-dev
          path: /Users/jp/Projects/active/claude-skill-dev/skills/foo
          modified: 2026-01-02T14:30:00
          files: 3
        - location: orphaned
          path: ~/.claude/skills/foo
          modified: 2026-01-03T09:15:00
          files: 2
      decision: null        # REQUIRED before migrate
      selected_source: null # REQUIRED if decision=migrate
      status: pending
      notes: ""

  plugins:
    - name: doc-auditor
      source: superserum
      decision: migrate
      status: pending
```

**Conflict handling:**
- Inventory detects same-named extensions across sources
- Marks with `conflict: true` and lists all sources with metadata
- Migrate refuses to proceed until conflicts are resolved
- Resolution requires both `decision` and `selected_source`
- Non-selected sources remain in place (manual cleanup after verification)

**Migration workflow:**
1. `uv run scripts/inventory` — Scan all sources, generate YAML
2. Review conflicts — Compare versions, set `selected_source`
3. Edit YAML — Set `decision` for each extension
4. `uv run scripts/migrate` — Process decisions, update status
5. Remove symlinks from `~/.claude/`
6. Clean up non-selected conflict sources (manual)
7. Archive old repos (update READMEs, mark as archived)

## MCP Server Workspaces

**Node/npm:** Provided by mise (globally managed).

**Root package.json:**
```json
{
  "name": "claude-code-tool-dev",
  "private": true,
  "workspaces": [
    "packages/mcp-servers/*",
    "packages/plugins/*"
  ]
}
```

**Creating a new server:**
```bash
mkdir -p packages/mcp-servers/my-server
cd packages/mcp-servers/my-server
npm init -y
# Add src/, tsconfig.json extending ../../tsconfig.base.json
```

**Server package.json with Claude Code metadata:**
```json
{
  "name": "@claude-tools/my-server",
  "version": "1.0.0",
  "scripts": {
    "build": "tsc"
  },
  "claudeCode": {
    "mcp": {
      "transport": "stdio",
      "command": "node dist/index.js",
      "env": ["API_KEY"]
    }
  }
}
```

**Building:**
```bash
npm install                                    # Install all workspace deps
npm run build -w packages/mcp-servers/my-server  # Build specific server
```

**Promotion workflow:**
```bash
uv run scripts/promote mcp-server my-server
```

This runs:
1. **VALIDATE** — Dir exists, `claudeCode.mcp` in package.json
2. **BUILD** — `npm run build -w packages/mcp-servers/<name>`
3. **CHECK** — `claude mcp get <name>` (already registered?)
4. **REGISTER** — `claude mcp add --transport <type> <name> --scope project -- <command>`
5. **VERIFY** — `claude mcp get <name>` confirms registration
6. **UPDATE** — `.mcp.json` auto-updated by `claude mcp add`
7. **PROMPT** — "Commit updated .mcp.json? [y/N]"

**Team workflow:** Commit `.mcp.json` after promotion. Team members pull and get servers—first use triggers per-user approval prompt (Claude Code security feature).

**Flags:**
- `--dry-run` — Build and show what would be registered
- `--force` — Skip confirmation prompts
- `--rebuild` — Force rebuild even if dist/ exists

## Python Scripts

All Python scripts use PEP 723 inline metadata:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
```

**Rationale:**
- No global pip installs (aligns with mise-tool-management.md)
- No project .venv needed for utility scripts
- Dependencies resolved automatically by `uv run`

## Path-Specific Rules

The `.claude/rules/` directory is **natively supported** by Claude Code with auto-discovery. We use path-scoped rules so context stays focused on the current task.

**Example rule file:**
```markdown
<!-- .claude/rules/skills.md -->
---
paths: .claude/skills/**
---

# Skill Development

- Skills require `name` and `description` in YAML frontmatter
- Use `allowed-tools` to grant tool permissions without prompting
- Test with /<skill-name> before promoting
- Directory structure: `.claude/skills/<name>/SKILL.md`
```

**Rule files in this project:**

| File | Scope | Purpose |
|------|-------|---------|
| `rules/skills.md` | `.claude/skills/**` | Skill development guidelines |
| `rules/hooks.md` | `.claude/hooks/**` | Hook development + frontmatter convention |
| `rules/commands.md` | `.claude/commands/**` | Command development guidelines |
| `rules/agents.md` | `.claude/agents/**` | Agent development guidelines |
| `rules/mcp-servers.md` | `packages/mcp-servers/**` | MCP server development + promote workflow |

**How it works:** When Claude edits a file matching a rule's `paths` glob, only that rule loads. Editing a skill loads skill rules; editing an MCP server loads MCP rules. This keeps context lean.

**Rules without paths:** If a rule file omits the `paths` frontmatter, it applies unconditionally to all files.

## Preventing Backsliding

**The problem:** Old habit of creating extensions directly in `~/.claude/`.

**Countermeasures:**

1. **Workflow friction** — Creating in `~/.claude/` means no git backup, no testing isolation
2. **CLAUDE.md reminder** — Workflow documented where Claude sees it every session
3. **Pre-commit hook** — Warn if `~/.claude/` has untracked changes not in monorepo

**CLAUDE.md section:**
```markdown
## Extension Development

### Skill Precedence
Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

| Scenario | Workflow |
|----------|----------|
| **New skill** | Create in `.claude/skills/` → test → promote |
| **Modify existing** | Copy to `.claude/skills/<name>-dev/` → test with dev name → verify by moving production aside → promote |

### New Skill
1. Create `.claude/skills/<name>/SKILL.md`
2. Test in this directory (project-local loads)
3. Promote: `uv run scripts/promote skill <name>`

### Existing Skill Iteration
Personal skills shadow project skills. To test changes:

1. Copy to `.claude/skills/<name>-dev/`
2. Test with `/<name>-dev` (avoids shadow)
3. Final verify: move `~/.claude/skills/<name>` aside temporarily
4. Promote, restore original references

### MCP Server Dependencies
Extensions using MCP tools require project config:

\`\`\`json
// .mcp.json
{ "mcpServers": { "server-name": { "command": "...", "args": [...] } } }
\`\`\`

Plugins (greptile, context7) work without setup—enabled at user level.
```

## Post-Migration State

**Old repos:** Archived in place, READMEs updated, symlinks removed.

**~/.claude/:** Contains only promoted (copied) extensions, no symlinks.

**This repo:** Single source of truth for all Claude Code extensions.

## Implementation Sequence

1. Initialize git repo, create directory structure
2. Create package.json, tsconfig.base.json
3. Write inventory script, generate migration-inventory.yaml
4. Annotate decisions in inventory
5. Write migrate script, execute migration
6. Write promote script
7. Remove symlinks from ~/.claude/
8. Archive old repos
9. Set up pre-commit hook
10. Create CLAUDE.md with workflow documentation
