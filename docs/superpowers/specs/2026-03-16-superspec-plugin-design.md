# Superspec Plugin Design

Bundle the spec system (spec-writer, spec-review-team, spec-modulator) + shared contract + spec-size-nudge hook into a single plugin for the turbo-mode marketplace.

## Motivation

The shared contract (`docs/references/shared-contract.md`) is consumed by all three spec skills but lives in a separate directory tree. Skills embed inline copies of contract tables (claims enum, derivation table, etc.) guarded by `SYNC` comment markers, with a validation script to detect drift. This is fragile and creates maintenance overhead.

A plugin co-locates the contract with the skills via `${CLAUDE_PLUGIN_ROOT}`, eliminating duplication and the sync system entirely.

## Plugin Structure

```
packages/plugins/superspec/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── spec-writer/
│   │   └── SKILL.md
│   ├── spec-review-team/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── agent-teams-platform.md
│   │       ├── failure-patterns.md
│   │       ├── preflight-taxonomy.md
│   │       ├── role-rubrics.md
│   │       └── synthesis-guidance.md
│   └── spec-modulator/
│       └── SKILL.md
├── references/
│   └── shared-contract.md
├── hooks/
│   └── hooks.json
├── scripts/
│   └── spec-size-nudge.sh
└── pyproject.toml
```

## Components

### plugin.json

```json
{
  "name": "superspec",
  "description": "Modular specification system — write, review, and modularize specs with shared contract enforcement",
  "version": "1.0.0",
  "author": { "name": "JP" },
  "license": "MIT",
  "keywords": ["spec", "specification", "modular", "review"]
}
```

### pyproject.toml

Follows the project convention — all plugins include a `pyproject.toml` for uv workspace integration:

```toml
[project]
name = "superspec-plugin"
version = "1.0.0"
description = "Modular specification system plugin for Claude Code"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

No Python dependencies currently — the hook is a shell script. The `pyproject.toml` exists for workspace consistency and to support future Python components.

### Skills

Three skills migrate from `.claude/skills/`:

| Skill | Purpose | Supporting Files |
|-------|---------|-----------------|
| spec-writer | Compile approved designs into modular, review-ready specs | None |
| spec-review-team | Parallel agent review of multi-file specs | 5 reference files in `references/` |
| spec-modulator | Design modular spec structures (greenfield or from-monolith) | None |

Skills become namespaced: `/superspec:spec-writer`, `/superspec:spec-review-team`, `/superspec:spec-modulator`.

### Skill Modifications

Each skill receives two changes:

1. **Strip embedded contract tables** — remove all `<!-- SYNC: ... -->` marked sections containing inline copies of claims enum, derivation table, spec.yaml schema, and failure model.
2. **Update contract references** — replace `docs/references/shared-contract.md` with `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md`. Add an explicit instruction to read the contract at the appropriate workflow point:

```markdown
Read the shared contract at `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` before proceeding with spec generation.
```

Core workflow logic, frontmatter (aside from path references), and supporting files transfer unchanged.

### Shared Contract

The authoritative shared contract moves from `docs/references/shared-contract.md` to `packages/plugins/superspec/references/shared-contract.md`. The original is deleted — the plugin copy is the single source of truth.

Contents unchanged. Defines:
- `spec.yaml` schema (shared_contract_version, authorities, precedence rules, boundary_rules)
- Claims Enum (8 fixed values)
- Claim-to-Role Derivation Table
- File Frontmatter requirements
- Precedence Resolution rules
- Failure Model (producer hard-stop, consumer degraded/hard-stop)

### Hook

The PostToolUse spec-size-nudge hook migrates from `.claude/hooks/spec-size-nudge.sh`.

**hooks/hooks.json:**

```json
{
  "description": "Spec size nudge — suggests modular structure for large files",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/spec-size-nudge.sh"
          }
        ]
      }
    ]
  }
}
```

Matcher is `Write`-only (not `Write|Edit`) because the script reads `.tool_input.content`, which only the Write tool provides. Edit uses `old_string`/`new_string` fields.

The shell script moves to `scripts/spec-size-nudge.sh` with one change: the `additionalContext` message references the namespaced skill name `/superspec:spec-writer` instead of `spec-writer`. No other path changes are needed — the script reads all input from stdin JSON and uses no absolute paths.

### Marketplace Entry

Add to `.claude-plugin/marketplace.json`:

```json
{ "name": "superspec", "source": "./packages/plugins/superspec" }
```

Follows the existing pattern — minimal entry, plugin.json handles metadata. Default `strict: true` means plugin.json is the authority.

## Files Removed

| Path | Reason |
|------|--------|
| `.claude/skills/spec-writer/` | Moved to plugin |
| `.claude/skills/spec-review-team/` | Moved to plugin |
| `.claude/skills/spec-modulator/` | Moved to plugin |
| `.claude/hooks/spec-size-nudge.sh` | Moved to plugin |
| `docs/references/shared-contract.md` | Moved to plugin (single source of truth) |
| `scripts/validate_spec_writing_contract.py` | Sync system retired |
| `tests/test_spec_writing_contract_sync.py` | Sync system retired |
| Hook entry in `.claude/settings.json` | Plugin hooks merge automatically |

## Files Added

| Path | Purpose |
|------|--------|
| `packages/plugins/superspec/` | Entire plugin tree (see structure above) |
| Entry in `.claude-plugin/marketplace.json` | Marketplace registration |

## Post-Migration Updates

- **CLAUDE.md**: Add superspec to the Packages table. Remove references to sync validation system. Update shared-contract reference in Key References.
- **settings.json**: Remove spec-size-nudge hook entry. Run `uv run scripts/sync-settings` to verify consistency.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Contract at plugin root `references/`, not inside a skill | Consumed equally by all three skills — shared resource, not skill-owned |
| Strip embedded tables, reference-only | Eliminates duplication. One Read call per workflow is trivial cost |
| Delete sync validation system | No duplication = no drift to validate |
| Delete `docs/references/shared-contract.md` | Single source of truth in plugin. Avoids stale copy confusion |
| Shell script unchanged | Hook logic is independent of its location. Only path references need updating |
| Develop directly in plugin dir | Avoids two-copies problem. Plugin dir is the source of truth |

## Future Considerations

The plugin structure accommodates future additions:
- New skills: add to `skills/`
- New hooks: add entries to `hooks/hooks.json` or additional hook JSON files
- Agents: add `agents/` directory at plugin root
- MCP servers: add `.mcp.json` at plugin root
