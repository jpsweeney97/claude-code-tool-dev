# Superspec Plugin Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bundle the spec-writing system (spec-writer, spec-review-team, spec-modulator skills + shared contract + spec-size-nudge hook) into a single plugin for the turbo-mode marketplace, eliminating the fragile SYNC marker content duplication system.

**Architecture:** Three skills, one hook, and the shared contract co-locate under `packages/plugins/superspec/`. Skills reference the contract via `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` instead of embedding inline copies. The sync validation system (script + tests) is deleted — no duplication means no drift to validate.

**Tech Stack:** Shell (hook script), Markdown (skills, contract), JSON (plugin.json, hooks.json), TOML (pyproject.toml)

---

## File Structure

### Files Created

| File | Responsibility |
|------|---------------|
| `packages/plugins/superspec/.claude-plugin/plugin.json` | Plugin manifest — name, version, description, author, license |
| `packages/plugins/superspec/pyproject.toml` | UV workspace integration — package name, Python version, dev deps |
| `packages/plugins/superspec/references/shared-contract.md` | Authoritative shared contract (moved from `docs/references/`) |
| `packages/plugins/superspec/hooks/hooks.json` | PostToolUse Write matcher for spec-size-nudge |
| `packages/plugins/superspec/scripts/spec-size-nudge.sh` | Spec size nudge — line counting and modularization suggestion |
| `packages/plugins/superspec/skills/spec-writer/SKILL.md` | Compile designs into modular specs (SYNC sections stripped) |
| `packages/plugins/superspec/skills/spec-review-team/SKILL.md` | Parallel agent review of multi-file specs |
| `packages/plugins/superspec/skills/spec-review-team/references/agent-teams-platform.md` | Agent teams API reference |
| `packages/plugins/superspec/skills/spec-review-team/references/failure-patterns.md` | Failure mode troubleshooting |
| `packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md` | Review cluster classification |
| `packages/plugins/superspec/skills/spec-review-team/references/role-rubrics.md` | Reviewer role definitions |
| `packages/plugins/superspec/skills/spec-review-team/references/synthesis-guidance.md` | Synthesis ledger format and examples |
| `packages/plugins/superspec/skills/spec-modulator/SKILL.md` | Design modular spec structures |

### Files Modified

| File | Change |
|------|--------|
| `.claude-plugin/marketplace.json` | Add `superspec` plugin entry |
| `pyproject.toml` (root) | Add `packages/plugins/superspec` to workspace members |
| `.claude/settings.json` | Remove spec-size-nudge PostToolUse hook entry |
| `.claude/CLAUDE.md` | Add superspec to Packages table, remove sync validation references |

### Files Removed

| File | Reason |
|------|--------|
| `.claude/skills/spec-writer/SKILL.md` | Moved to plugin |
| `.claude/skills/spec-review-team/SKILL.md` | Moved to plugin |
| `.claude/skills/spec-review-team/references/*.md` (5 files) | Moved to plugin |
| `.claude/skills/spec-modulator/SKILL.md` | Moved to plugin |
| `.claude/hooks/spec-size-nudge.sh` | Moved to plugin |
| `docs/references/shared-contract.md` | Moved to plugin (single source of truth) |
| `scripts/validate_spec_writing_contract.py` | Sync system retired |
| `tests/test_spec_writing_contract_sync.py` | Sync system retired |

---

## Chunk 1: Plugin Infrastructure

### Task 1: Create Plugin Scaffold

**Files:**
- Create: `packages/plugins/superspec/.claude-plugin/plugin.json`
- Create: `packages/plugins/superspec/pyproject.toml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p packages/plugins/superspec/.claude-plugin
mkdir -p packages/plugins/superspec/references
mkdir -p packages/plugins/superspec/hooks
mkdir -p packages/plugins/superspec/scripts
mkdir -p packages/plugins/superspec/skills/spec-writer
mkdir -p packages/plugins/superspec/skills/spec-review-team/references
mkdir -p packages/plugins/superspec/skills/spec-modulator
```

- [ ] **Step 2: Write plugin.json**

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

Write to: `packages/plugins/superspec/.claude-plugin/plugin.json`

- [ ] **Step 3: Write pyproject.toml**

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

Write to: `packages/plugins/superspec/pyproject.toml`

- [ ] **Step 4: Verify scaffold**

```bash
# Verify both files exist and are parseable
python3 -c "import json; json.load(open('packages/plugins/superspec/.claude-plugin/plugin.json'))" && echo "plugin.json OK"
python3 -c "import tomllib; tomllib.load(open('packages/plugins/superspec/pyproject.toml', 'rb'))" && echo "pyproject.toml OK"
```

Expected: both print "OK"

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/superspec/.claude-plugin/plugin.json packages/plugins/superspec/pyproject.toml
git commit -m "feat(superspec): scaffold plugin directory structure"
```

### Task 2: Move Shared Contract to Plugin

**Files:**
- Create: `packages/plugins/superspec/references/shared-contract.md` (copy from `docs/references/shared-contract.md`)

The shared contract content is unchanged — this is a pure file copy. The original remains until Task 7 (cleanup).

- [ ] **Step 1: Copy shared contract**

```bash
cp docs/references/shared-contract.md packages/plugins/superspec/references/shared-contract.md
```

- [ ] **Step 2: Verify content matches**

```bash
diff docs/references/shared-contract.md packages/plugins/superspec/references/shared-contract.md
```

Expected: no diff output (files identical)

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/superspec/references/shared-contract.md
git commit -m "feat(superspec): copy shared contract to plugin"
```

### Task 3: Migrate Hook to Plugin

**Files:**
- Create: `packages/plugins/superspec/hooks/hooks.json`
- Create: `packages/plugins/superspec/scripts/spec-size-nudge.sh` (modified from `.claude/hooks/spec-size-nudge.sh`)

Two changes from the original hook script:
1. The `additionalContext` message references `/superspec:spec-writer` (namespaced) instead of `spec-writer`
2. The hook frontmatter comment block (`# /// hook` ... `# ///`) is removed — hook config lives in `hooks.json` for plugins

- [ ] **Step 1: Write hooks.json**

```json
{
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

Write to: `packages/plugins/superspec/hooks/hooks.json`

Note: the spec design includes a top-level `"description"` field, but the existing `handoff` plugin's `hooks.json` does not use this pattern. Omit it to match established plugin conventions.

- [ ] **Step 2: Write spec-size-nudge.sh**

Copy from `.claude/hooks/spec-size-nudge.sh` with two modifications:

1. **Remove hook frontmatter** — delete lines 2-5 (the `# /// hook` ... `# ///` block; keep the `#!/bin/bash` shebang on line 1 since hook config now lives in `hooks.json`)
2. **Update skill reference** — change `"the spec-writer skill"` to `"/superspec:spec-writer"` in the `additionalContext` JSON output

The resulting script:

```bash
#!/bin/bash

# Require jq — emit diagnostic to stderr (visible with --debug)
if ! command -v jq &>/dev/null; then
  echo "spec-size-nudge: jq not found, skipping" >&2
  exit 0
fi

INPUT=$(cat)

FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check markdown files in docs/ or specs/ directories
case "$FILE_PATH" in
  */docs/*|*/specs/*) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.md) ;;
  *) exit 0 ;;
esac

CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.content // empty')
if [ -z "$CONTENT" ]; then
  exit 0
fi

# printf '%s' avoids echo's trailing newline inflating the count
LINE_COUNT=$(printf '%s' "$CONTENT" | wc -l | tr -d ' ')

if [ "$LINE_COUNT" -gt 500 ]; then
  # Use jq to construct JSON safely (handles special chars in FILE_PATH)
  jq -n --arg path "$FILE_PATH" --arg count "$LINE_COUNT" \
    '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": ("This file (" + $path + ") is " + $count + " lines. Files over 500 lines are difficult to reference in future conversations. Consider invoking /superspec:spec-writer to create a modular spec structure.")}}'
fi

exit 0
```

Write to: `packages/plugins/superspec/scripts/spec-size-nudge.sh`

- [ ] **Step 3: Make script executable**

```bash
chmod +x packages/plugins/superspec/scripts/spec-size-nudge.sh
```

- [ ] **Step 4: Verify hook changes**

```bash
# Verify hooks.json is valid JSON
python3 -c "import json; json.load(open('packages/plugins/superspec/hooks/hooks.json'))" && echo "hooks.json OK"

# Verify script has no hook frontmatter comment
grep -c '# /// hook' packages/plugins/superspec/scripts/spec-size-nudge.sh
# Expected: 0

# Verify namespaced skill reference
grep '/superspec:spec-writer' packages/plugins/superspec/scripts/spec-size-nudge.sh
# Expected: 1 match containing "/superspec:spec-writer"

# Verify old reference is gone
grep -c 'the spec-writer skill' packages/plugins/superspec/scripts/spec-size-nudge.sh
# Expected: 0
```

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/superspec/hooks/hooks.json packages/plugins/superspec/scripts/spec-size-nudge.sh
git commit -m "feat(superspec): migrate spec-size-nudge hook to plugin"
```

---

## Chunk 2: Skill Migration

### Task 4: Migrate spec-writer Skill

**Files:**
- Create: `packages/plugins/superspec/skills/spec-writer/SKILL.md` (modified from `.claude/skills/spec-writer/SKILL.md`)

Three changes from the source file:

1. **Strip all 4 SYNC-marked sections** — remove the Claims Enum table, Claim-to-Role Derivation Table, spec.yaml Schema block, and Failure Model table (lines 198-269 in the source). These are inline copies of content that now lives in the shared contract at `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md`.

2. **Add contract Read instruction** — insert between Phase 1 and Phase 2 instructions. The contract contains the Claims Enum, Derivation Table, spec.yaml schema, and Failure Model that the skill previously had inline.

3. **Update References table** — change `docs/references/shared-contract.md` to `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md`.

- [ ] **Step 1: Copy source skill to plugin**

```bash
cp .claude/skills/spec-writer/SKILL.md packages/plugins/superspec/skills/spec-writer/SKILL.md
```

- [ ] **Step 2: Strip the 4 SYNC-marked sections**

Remove the following content block from the copied SKILL.md (everything from the first `<!-- SYNC:` comment through the last table row of the Failure Model, inclusive):

```markdown
<!-- SYNC: docs/references/shared-contract.md#claims-enum -->
## Claims Enum
...through...
| `spec.yaml` top-level key has wrong type (e.g., `boundary_rules: {}` instead of list, `authorities: []` instead of mapping) | Hard failure |
```

This removes:
- `<!-- SYNC: docs/references/shared-contract.md#claims-enum -->` + Claims Enum section (table with 8 rows)
- `<!-- SYNC: docs/references/shared-contract.md#derivation-table -->` + Derivation Table section (table with 6 rows + explanatory paragraph)
- `<!-- SYNC: docs/references/shared-contract.md#spec-yaml-schema -->` + spec.yaml Schema section (fenced YAML block)
- `<!-- SYNC: docs/references/shared-contract.md#failure-model -->` + Failure Model section (table with 9 producer failure rows)

- [ ] **Step 3: Add contract Read instruction**

Insert after the Phase 1 section (after `### Phase 1: ENTRY GATE` and its content, before `### Phase 2: ANALYSIS`):

```markdown
### Contract Reference

Read the shared contract at `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` before proceeding to Phase 2. The contract defines:
- Claims Enum (8 fixed values)
- Claim-to-Role Derivation Table
- spec.yaml schema
- Producer Failure Model (hard failures)

These were previously embedded inline — they now live exclusively in the shared contract.
```

- [ ] **Step 4: Update References table**

In the `## References` section at the end of the file, change:

```markdown
| `docs/references/shared-contract.md` | Full shared contract — authoritative for spec.yaml schema, claims, derivation, precedence, boundaries, failure model |
```

to:

```markdown
| `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` | Full shared contract — authoritative for spec.yaml schema, claims, derivation, precedence, boundaries, failure model |
```

- [ ] **Step 5: Verify modifications**

```bash
# Verify no SYNC markers remain
grep -c 'SYNC' packages/plugins/superspec/skills/spec-writer/SKILL.md
# Expected: 0

# Verify no old contract path remains
grep -c 'docs/references/shared-contract.md' packages/plugins/superspec/skills/spec-writer/SKILL.md
# Expected: 0

# Verify new contract path exists
grep -c 'CLAUDE_PLUGIN_ROOT.*shared-contract' packages/plugins/superspec/skills/spec-writer/SKILL.md
# Expected: 2 (one in Contract Reference section, one in References table)

# Verify Contract Reference section exists
grep -c 'Contract Reference' packages/plugins/superspec/skills/spec-writer/SKILL.md
# Expected: 1

# Verify frontmatter is intact (name, description, allowed-tools)
head -20 packages/plugins/superspec/skills/spec-writer/SKILL.md
# Expected: YAML frontmatter with name: spec-writer, description, allowed-tools list
```

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/superspec/skills/spec-writer/SKILL.md
git commit -m "feat(superspec): migrate spec-writer skill to plugin"
```

### Task 5: Migrate spec-review-team Skill

**Files:**
- Create: `packages/plugins/superspec/skills/spec-review-team/SKILL.md` (modified from `.claude/skills/spec-review-team/SKILL.md`)
- Create: `packages/plugins/superspec/skills/spec-review-team/references/agent-teams-platform.md` (copy)
- Create: `packages/plugins/superspec/skills/spec-review-team/references/failure-patterns.md` (copy)
- Create: `packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md` (copy)
- Create: `packages/plugins/superspec/skills/spec-review-team/references/role-rubrics.md` (copy)
- Create: `packages/plugins/superspec/skills/spec-review-team/references/synthesis-guidance.md` (copy)

Two changes to SKILL.md:

1. **Update contract reference paths** — replace all 5 occurrences of `docs/references/shared-contract.md` with `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md`
2. **Add contract Read instruction** — insert at the start of the Procedure section

4 of the 5 reference files copy unchanged. `preflight-taxonomy.md` contains one stale contract path that must be updated after copying.

- [ ] **Step 1: Copy reference files**

```bash
cp .claude/skills/spec-review-team/references/agent-teams-platform.md packages/plugins/superspec/skills/spec-review-team/references/
cp .claude/skills/spec-review-team/references/failure-patterns.md packages/plugins/superspec/skills/spec-review-team/references/
cp .claude/skills/spec-review-team/references/preflight-taxonomy.md packages/plugins/superspec/skills/spec-review-team/references/
cp .claude/skills/spec-review-team/references/role-rubrics.md packages/plugins/superspec/skills/spec-review-team/references/
cp .claude/skills/spec-review-team/references/synthesis-guidance.md packages/plugins/superspec/skills/spec-review-team/references/
```

- [ ] **Step 2: Verify reference files match**

```bash
for f in agent-teams-platform.md failure-patterns.md preflight-taxonomy.md role-rubrics.md synthesis-guidance.md; do
  diff ".claude/skills/spec-review-team/references/$f" "packages/plugins/superspec/skills/spec-review-team/references/$f" && echo "$f OK"
done
```

Expected: all 5 print "OK"

- [ ] **Step 3: Update stale contract path in preflight-taxonomy.md**

`preflight-taxonomy.md` line 36 contains `docs/references/shared-contract.md#claim-to-role-derivation-table`. Update to `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md#claim-to-role-derivation-table`.

```bash
# Verify the stale reference exists
grep 'docs/references/shared-contract.md' packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md
# Expected: 1 match
```

Replace `docs/references/shared-contract.md` with `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` in that file.

```bash
# Verify update
grep 'CLAUDE_PLUGIN_ROOT.*shared-contract' packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md
# Expected: 1 match
grep -c 'docs/references/shared-contract.md' packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md
# Expected: 0
```

- [ ] **Step 4: Copy SKILL.md to plugin**

```bash
cp .claude/skills/spec-review-team/SKILL.md packages/plugins/superspec/skills/spec-review-team/SKILL.md
```

- [ ] **Step 5: Update contract reference paths**

Replace all 5 occurrences of `docs/references/shared-contract.md` with `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md` in the copied SKILL.md.

The 5 occurrences and their contexts:

1. Phase 1, step 4 (effective claims): `See \`docs/references/shared-contract.md\` for claims rules.`
2. Phase 1, step 4 (derived roles): `mapped from effective claims via the derivation table in \`docs/references/shared-contract.md\``
3. Phase 3A (semantic validation): `Consumer failure rules from \`docs/references/shared-contract.md\` apply`
4. Phase 5 (contradiction resolution): `See \`docs/references/shared-contract.md\` for full precedence rules.`
5. References table: `| \`docs/references/shared-contract.md\` | Shared contract — ...`

Use `replace_all` to replace all occurrences at once.

- [ ] **Step 6: Add contract Read instruction**

Insert at the start of the `## Procedure` section, before `### Phase 1: DISCOVERY`:

```markdown
**Before starting:** Read the shared contract at `${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md`. The contract defines the claims enum, derivation table, precedence rules, and failure model used throughout this procedure.

```

- [ ] **Step 7: Verify modifications**

```bash
# Verify no old contract path remains in SKILL.md or reference files
grep -rc 'docs/references/shared-contract.md' packages/plugins/superspec/skills/spec-review-team/
# Expected: 0 (all occurrences updated)
# Expected: 0

# Verify new contract path appears 6 times (5 original + 1 new Read instruction)
grep -c 'CLAUDE_PLUGIN_ROOT.*shared-contract' packages/plugins/superspec/skills/spec-review-team/SKILL.md
# Expected: 6

# Verify frontmatter is intact
head -20 packages/plugins/superspec/skills/spec-review-team/SKILL.md
# Expected: YAML frontmatter with name: spec-review-team, description, allowed-tools list
```

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/superspec/skills/spec-review-team/
git commit -m "feat(superspec): migrate spec-review-team skill to plugin"
```

### Task 6: Migrate spec-modulator Skill

**Files:**
- Create: `packages/plugins/superspec/skills/spec-modulator/SKILL.md` (copy from `.claude/skills/spec-modulator/SKILL.md`)

No content changes needed — spec-modulator does not reference the shared contract.

- [ ] **Step 1: Copy SKILL.md**

```bash
cp .claude/skills/spec-modulator/SKILL.md packages/plugins/superspec/skills/spec-modulator/SKILL.md
```

- [ ] **Step 2: Verify content matches**

```bash
diff .claude/skills/spec-modulator/SKILL.md packages/plugins/superspec/skills/spec-modulator/SKILL.md
```

Expected: no diff output

- [ ] **Step 3: Verify no stale references**

```bash
# Verify no references to docs/references/shared-contract.md
grep -c 'docs/references/shared-contract.md' packages/plugins/superspec/skills/spec-modulator/SKILL.md
# Expected: 0

# Verify frontmatter is intact
head -5 packages/plugins/superspec/skills/spec-modulator/SKILL.md
# Expected: YAML frontmatter with name: spec-modulator
```

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/superspec/skills/spec-modulator/SKILL.md
git commit -m "feat(superspec): migrate spec-modulator skill to plugin"
```

---

## Chunk 3: Cleanup and Configuration

### Task 7: Remove Old Files

**Files removed:**
- `.claude/skills/spec-writer/SKILL.md` (and directory)
- `.claude/skills/spec-review-team/SKILL.md` + `references/*.md` (and directories)
- `.claude/skills/spec-modulator/SKILL.md` (and directory)
- `.claude/hooks/spec-size-nudge.sh`
- `docs/references/shared-contract.md`
- `scripts/validate_spec_writing_contract.py`
- `tests/test_spec_writing_contract_sync.py`

**Important:** Verify plugin copies exist before removing originals. This is the destructive step — validate first.

- [ ] **Step 1: Verify plugin copies exist**

```bash
# All 13 plugin files must exist before removing originals
for f in \
  packages/plugins/superspec/.claude-plugin/plugin.json \
  packages/plugins/superspec/pyproject.toml \
  packages/plugins/superspec/references/shared-contract.md \
  packages/plugins/superspec/hooks/hooks.json \
  packages/plugins/superspec/scripts/spec-size-nudge.sh \
  packages/plugins/superspec/skills/spec-writer/SKILL.md \
  packages/plugins/superspec/skills/spec-review-team/SKILL.md \
  packages/plugins/superspec/skills/spec-review-team/references/agent-teams-platform.md \
  packages/plugins/superspec/skills/spec-review-team/references/failure-patterns.md \
  packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md \
  packages/plugins/superspec/skills/spec-review-team/references/role-rubrics.md \
  packages/plugins/superspec/skills/spec-review-team/references/synthesis-guidance.md \
  packages/plugins/superspec/skills/spec-modulator/SKILL.md; do
  [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: all 13 print "OK". If any print "MISSING", stop and fix before proceeding.

- [ ] **Step 2: Remove old skill directories**

```bash
trash .claude/skills/spec-writer
trash .claude/skills/spec-review-team
trash .claude/skills/spec-modulator
```

- [ ] **Step 3: Remove old hook script**

```bash
trash .claude/hooks/spec-size-nudge.sh
```

- [ ] **Step 4: Remove old shared contract**

```bash
trash docs/references/shared-contract.md
```

- [ ] **Step 5: Remove sync validation system**

```bash
trash scripts/validate_spec_writing_contract.py
trash tests/test_spec_writing_contract_sync.py
```

- [ ] **Step 6: Verify removals**

```bash
# All old paths should be gone
for f in \
  .claude/skills/spec-writer \
  .claude/skills/spec-review-team \
  .claude/skills/spec-modulator \
  .claude/hooks/spec-size-nudge.sh \
  docs/references/shared-contract.md \
  scripts/validate_spec_writing_contract.py \
  tests/test_spec_writing_contract_sync.py; do
  [ -e "$f" ] && echo "STILL EXISTS: $f" || echo "REMOVED: $f"
done
```

Expected: all 7 print "REMOVED"

- [ ] **Step 7: Stage deletions and commit**

After `trash`, git sees the files as deleted in the working tree but unstaged. Use `git add -u` to stage all tracked-file deletions:

```bash
git add -u .claude/skills/spec-writer .claude/skills/spec-review-team .claude/skills/spec-modulator .claude/hooks/spec-size-nudge.sh docs/references/shared-contract.md scripts/validate_spec_writing_contract.py tests/test_spec_writing_contract_sync.py
git commit -m "chore(superspec): remove migrated source files and sync system"
```

Note: `-u` (not `-A`) is required here because `trash` removes files from the filesystem without `git rm`. `-u` tells git to update the index for tracked files that have been modified or deleted in the working tree.

### Task 8: Update Configuration Files

**Files modified:**
- `.claude-plugin/marketplace.json` — add superspec entry
- `pyproject.toml` (root) — add workspace member
- `.claude/settings.json` — remove hook entry

- [ ] **Step 1: Add superspec to marketplace.json**

In `.claude-plugin/marketplace.json`, add the superspec entry to the `plugins` array:

```json
{ "name": "superspec", "source": "./packages/plugins/superspec" }
```

The full file after edit:

```json
{
  "name": "turbo-mode",
  "owner": { "name": "JP" },
  "plugins": [
    { "name": "cross-model", "source": "./packages/plugins/cross-model" },
    { "name": "handoff", "source": "./packages/plugins/handoff" },
    { "name": "context-metrics", "source": "./packages/plugins/context-metrics" },
    { "name": "ticket", "source": "./packages/plugins/ticket" },
    { "name": "superspec", "source": "./packages/plugins/superspec" }
  ]
}
```

- [ ] **Step 2: Add workspace member to root pyproject.toml**

Add `"packages/plugins/superspec"` to the `[tool.uv.workspace] members` list:

```toml
[tool.uv.workspace]
members = [
    "packages/plugins/cross-model/context-injection",
    "packages/plugins/context-metrics",
    "packages/plugins/cross-model",
    "packages/plugins/handoff",
    "packages/plugins/ticket",
    "packages/plugins/superspec",
]
```

- [ ] **Step 3: Update settings.json — remove hook entry**

The current `.claude/settings.json` contains a `PostToolUse` hook entry for `spec-size-nudge.sh`. Remove the entire `hooks` block since the hook now lives in the plugin's `hooks.json`.

The file after edit (hook entry removed, `env` block preserved):

```json
{
  "env": {
    "GITFLOW_ALLOW_FILES": "**/docs/**,**/.review-workspace/**,CHANGELOG.md,README.md,HANDBOOK.md,settings.json,plugin.json,**/.claude/handoffs/**,**/.claude/notes/**,**/.claude/skills/**,**/tickets/**,**/CLAUDE.md,**/rules/**"
  }
}
```

- [ ] **Step 4: Verify configuration changes**

```bash
# Verify marketplace.json is valid JSON with superspec entry
python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); assert any(p['name']=='superspec' for p in d['plugins']), 'superspec not found'" && echo "marketplace OK"

# Verify pyproject.toml has superspec workspace member
grep 'packages/plugins/superspec' pyproject.toml && echo "workspace OK"

# Verify settings.json has no hooks block
python3 -c "import json; d=json.load(open('.claude/settings.json')); assert 'hooks' not in d, 'hooks still present'" && echo "settings OK"

# Verify settings.json is valid JSON
python3 -c "import json; json.load(open('.claude/settings.json'))" && echo "settings JSON OK"
```

Expected: all 4 print "OK"

- [ ] **Step 5: Run sync-settings to verify consistency**

```bash
uv run scripts/sync-settings
```

Expected: clean run, no errors. After running, verify `settings.json` still has no `hooks` block (sync-settings reads `.claude/hooks/` — since `spec-size-nudge.sh` was removed in Task 7 and no other hook scripts exist in that directory, no hooks should be re-added):

```bash
python3 -c "import json; d=json.load(open('.claude/settings.json')); assert 'hooks' not in d, 'sync-settings re-added hooks'" && echo "post-sync OK"
```

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/marketplace.json pyproject.toml .claude/settings.json
git commit -m "chore(superspec): register plugin in marketplace and workspace"
```

### Task 9: Update CLAUDE.md

**Files modified:**
- `.claude/CLAUDE.md` — add superspec to Packages table, remove sync validation references

Three changes:

1. **Add to Packages table** — add a row for superspec
2. **Remove sync validation from Scripts table** — `validate_spec_writing_contract.py` no longer exists
3. **Update shared-contract reference in Gotchas or elsewhere** — if any references to `docs/references/shared-contract.md` exist, remove or update them

- [ ] **Step 1: Add superspec to Packages table**

Add this row to the Packages table in `.claude/CLAUDE.md`:

```markdown
| superspec | `packages/plugins/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
```

Insert after the `context-metrics` row and before the `claude-code-docs` row.

- [ ] **Step 2: Verify no stale references remain**

```bash
# Check for references to removed files
grep -n 'validate_spec_writing_contract' .claude/CLAUDE.md
grep -n 'test_spec_writing_contract_sync' .claude/CLAUDE.md
grep -n 'docs/references/shared-contract.md' .claude/CLAUDE.md
```

Expected: no matches. If any match, update or remove the stale reference.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: add superspec plugin to CLAUDE.md Packages table"
```

### Task 10: Final Validation

No files modified — this is a verification-only task.

- [ ] **Step 1: Verify complete plugin structure**

```bash
find packages/plugins/superspec -type f | sort
```

Expected output (13 files):

```
packages/plugins/superspec/.claude-plugin/plugin.json
packages/plugins/superspec/hooks/hooks.json
packages/plugins/superspec/pyproject.toml
packages/plugins/superspec/references/shared-contract.md
packages/plugins/superspec/scripts/spec-size-nudge.sh
packages/plugins/superspec/skills/spec-modulator/SKILL.md
packages/plugins/superspec/skills/spec-review-team/SKILL.md
packages/plugins/superspec/skills/spec-review-team/references/agent-teams-platform.md
packages/plugins/superspec/skills/spec-review-team/references/failure-patterns.md
packages/plugins/superspec/skills/spec-review-team/references/preflight-taxonomy.md
packages/plugins/superspec/skills/spec-review-team/references/role-rubrics.md
packages/plugins/superspec/skills/spec-review-team/references/synthesis-guidance.md
packages/plugins/superspec/skills/spec-writer/SKILL.md
```

- [ ] **Step 2: Verify no stale references in plugin skills**

```bash
# No SYNC markers anywhere in plugin
grep -r 'SYNC' packages/plugins/superspec/skills/
# Expected: no output

# No old contract path in plugin
grep -r 'docs/references/shared-contract.md' packages/plugins/superspec/
# Expected: no output

# All contract references use CLAUDE_PLUGIN_ROOT
grep -r 'CLAUDE_PLUGIN_ROOT.*shared-contract' packages/plugins/superspec/skills/
# Expected: matches in spec-writer and spec-review-team only
```

- [ ] **Step 3: Verify old files are gone**

```bash
# Skills removed
[ -d .claude/skills/spec-writer ] && echo "FAIL: spec-writer still exists" || echo "OK"
[ -d .claude/skills/spec-review-team ] && echo "FAIL: spec-review-team still exists" || echo "OK"
[ -d .claude/skills/spec-modulator ] && echo "FAIL: spec-modulator still exists" || echo "OK"

# Hook removed
[ -f .claude/hooks/spec-size-nudge.sh ] && echo "FAIL: hook still exists" || echo "OK"

# Contract removed from old location
[ -f docs/references/shared-contract.md ] && echo "FAIL: old contract still exists" || echo "OK"

# Sync system removed
[ -f scripts/validate_spec_writing_contract.py ] && echo "FAIL: sync script still exists" || echo "OK"
[ -f tests/test_spec_writing_contract_sync.py ] && echo "FAIL: sync tests still exist" || echo "OK"
```

Expected: all print "OK"

- [ ] **Step 4: Verify git status is clean**

```bash
git status
```

Expected: working tree clean, all changes committed.

- [ ] **Step 5: Verify uv workspace lockfile**

```bash
uv lock --check
```

Expected: lockfile is up to date. If not, run `uv lock` and commit the updated lockfile.

- [ ] **Step 6: Verify existing tests still pass**

```bash
# Run any existing tests — check exit code explicitly
uv run pytest tests/ -v --tb=short; echo "EXIT: $?"
```

Expected: `EXIT: 0`. If `test_spec_writing_contract_sync.py` was properly removed in Task 7, it won't run. Any failures indicate stale test dependencies on removed files.
