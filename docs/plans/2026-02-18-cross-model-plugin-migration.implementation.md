# Cross-Model Plugin Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from the `codex` plugin to a single self-contained `cross-model` plugin that bundles Codex integration, context injection MCP server, and all supporting artifacts.

**Architecture:** Create `packages/plugins/cross-model/` by scaffolding from the existing `codex` plugin, vendoring the context injection Python MCP server, migrating project-level agents and hooks, transforming all tool names for the plugin rename + context injection bundling, and updating metadata. The plugin becomes the canonical source for all cross-model reference files. Development source for context injection code stays at `packages/context-injection/` (where tests run); a build script syncs to the plugin for distribution.

**Tech Stack:** Python 3.11+ (context injection), `uv` (package management), Claude Code plugin system, MCP protocol

**Reference:** `docs/plans/2026-02-18-cross-model-plugin-migration.md` (design doc with 6 resolved design questions)

**Amended:** 2026-02-18 — pre-execution review found 7 issues (3 blocking, 2 important, 2 minor). Fixes: Task 2 adds vendored copy warning + build script `--exclude` to preserve it; Task 6 adds broader file-type verification; Task 7 expands CLAUDE.md updates to cover tool names and agent paths; Task 8 updates all three validation paths (contract, skill, agent) not just contract; Task 9 scopes stale-name grep to exclude soon-to-be-deleted project agents; Task 10 replaces `git add -A` with explicit staging, adds repo-level `.mcp.json` removal, adds `mcp__context-injection__` dangling reference check.

**Branch:** Create `feature/cross-model-plugin` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest` (969 tests) + `uv run pytest tests/test_codex_guard.py` (24 tests) + `uv run pytest tests/test_consultation_contract_sync.py` (13 tests)

**Dependencies between tasks:**
- Task 1: independent (scaffolding)
- Task 2: depends on Task 1 (plugin directory must exist)
- Task 3: depends on Task 1 (plugin directory must exist)
- Task 4: depends on Task 1 (plugin directory must exist)
- Task 5: depends on Task 1 (plugin directory must exist)
- Task 6: depends on Tasks 1-5 (all files must be in place before renaming)
- Task 7: depends on Task 6 (tool names must be finalized)
- Task 8: depends on Task 6 (tool names must be finalized)
- Task 9: depends on Tasks 7-8 (metadata and validation must be updated)
- Task 10: depends on Task 9 (verification before cleanup)

---

## Task 1: Scaffold new plugin from existing codex plugin

**Files:**
- Create: `packages/plugins/cross-model/` (full tree copied from codex)
- Modify: `packages/plugins/cross-model/.claude-plugin/plugin.json`

**Step 1: Create the feature branch**

```bash
git checkout -b feature/cross-model-plugin main
```

**Step 2: Copy the existing codex plugin**

```bash
cp -r packages/plugins/codex packages/plugins/cross-model
```

**Step 3: Remove codex-specific build artifacts from the copy**

```bash
trash packages/plugins/cross-model/.pytest_cache
trash packages/plugins/cross-model/scripts/__pycache__
```

**Step 4: Update plugin.json name field**

Edit `packages/plugins/cross-model/.claude-plugin/plugin.json`:

```json
{
  "name": "cross-model",
  "version": "0.1.0",
  "description": "Codex consultation skill, agent, and enforcement hooks for cross-model second opinions",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["codex", "consultation", "second-opinion", "cross-model"]
}
```

Only change: `"name": "codex"` → `"name": "cross-model"`. Leave version at `0.1.0` — Task 7 bumps it.

**Step 5: Verify directory structure**

```bash
find packages/plugins/cross-model -type f | sort
```

Expected: same structure as codex plugin (skill, agent, hooks, scripts, references, .mcp.json, README, CHANGELOG).

**Step 6: Commit**

```bash
git add packages/plugins/cross-model
git commit -m "feat: scaffold cross-model plugin from codex plugin"
```

---

## Task 2: Vendor context injection MCP server and create build script

**Files:**
- Create: `packages/plugins/cross-model/context-injection/` (vendored Python package)
- Create: `scripts/build-cross-model-plugin`
- Modify: `packages/plugins/cross-model/.mcp.json`

**Step 1: Create the build script**

Create `scripts/build-cross-model-plugin`:

```bash
#!/usr/bin/env bash
# Syncs vendored context injection source into the cross-model plugin.
# Run before marketplace update when context injection code changes.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="$REPO_ROOT/packages/context-injection"
DEST="$REPO_ROOT/packages/plugins/cross-model/context-injection"

if [ ! -d "$SRC" ]; then
    echo "error: source not found at $SRC" >&2
    exit 1
fi

rsync -a --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='tests/' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='README.vendored.md' \
    "$SRC/" "$DEST/"

echo "Synced context-injection → cross-model plugin ($(find "$DEST/context_injection" -name '*.py' | wc -l | tr -d ' ') Python files)"
```

```bash
chmod +x scripts/build-cross-model-plugin
```

**Step 2: Run the build script to vendor context injection**

```bash
scripts/build-cross-model-plugin
```

Expected output: `Synced context-injection → cross-model plugin (N Python files)`

**Step 3: Add vendored copy warning**

The build script created `packages/plugins/cross-model/context-injection/`. Add a marker file (preserved across future syncs by the `--exclude='README.vendored.md'` in the build script):

Create `packages/plugins/cross-model/context-injection/README.vendored.md`:

```markdown
# Vendored Copy — Do Not Edit

This directory is a vendored copy of `packages/context-injection/`.
Edits here will be overwritten by `scripts/build-cross-model-plugin`.

To make changes:
1. Edit the source at `packages/context-injection/`
2. Run tests: `cd packages/context-injection && uv run pytest`
3. Sync: `scripts/build-cross-model-plugin`
```

**Step 4: Verify the vendored copy excludes build artifacts**

```bash
ls packages/plugins/cross-model/context-injection/
```

Expected: `CLAUDE.md`, `context_injection/`, `pyproject.toml`, `uv.lock` — NO `.venv/`, `tests/`, `__pycache__/`.

**Step 5: Add context injection MCP server to `.mcp.json`**

Edit `packages/plugins/cross-model/.mcp.json`:

```json
{
  "mcpServers": {
    "codex": {
      "type": "stdio",
      "command": "codex",
      "args": ["mcp-server"],
      "env": {
        "CODEX_SANDBOX": "seatbelt"
      }
    },
    "context-injection": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}/context-injection", "python", "-m", "context_injection"],
      "env": {}
    }
  }
}
```

**Step 6: Commit**

```bash
git add scripts/build-cross-model-plugin packages/plugins/cross-model/context-injection packages/plugins/cross-model/.mcp.json
git commit -m "feat: vendor context injection MCP server into cross-model plugin

Adds build script (scripts/build-cross-model-plugin) that syncs
source from packages/context-injection/ excluding .venv, tests,
and build artifacts. Adds context-injection MCP server config
using \${CLAUDE_PLUGIN_ROOT}/context-injection."
```

---

## Task 3: Migrate reference files (plugin-canonical)

**Files:**
- Create: `packages/plugins/cross-model/references/context-injection-contract.md`
- Replace: `docs/references/consultation-contract.md` → symlink
- Replace: `docs/references/consultation-profiles.yaml` → symlink
- Replace: `docs/references/context-injection-contract.md` → symlink

**Step 1: Copy context injection contract to plugin**

```bash
cp docs/references/context-injection-contract.md packages/plugins/cross-model/references/context-injection-contract.md
```

**Step 2: Verify all three reference files exist in plugin**

```bash
ls packages/plugins/cross-model/references/
```

Expected: `consultation-contract.md`, `consultation-profiles.yaml`, `context-injection-contract.md`

**Step 3: Replace originals with symlinks**

```bash
# Remove originals
trash docs/references/consultation-contract.md
trash docs/references/consultation-profiles.yaml
trash docs/references/context-injection-contract.md

# Create symlinks (relative paths from docs/references/ to plugin)
ln -s ../../packages/plugins/cross-model/references/consultation-contract.md docs/references/consultation-contract.md
ln -s ../../packages/plugins/cross-model/references/consultation-profiles.yaml docs/references/consultation-profiles.yaml
ln -s ../../packages/plugins/cross-model/references/context-injection-contract.md docs/references/context-injection-contract.md
```

**Step 4: Verify symlinks resolve correctly**

```bash
head -1 docs/references/consultation-contract.md
head -1 docs/references/context-injection-contract.md
```

Expected: first line of each file (not a broken symlink error).

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/references/context-injection-contract.md docs/references/consultation-contract.md docs/references/consultation-profiles.yaml docs/references/context-injection-contract.md
git commit -m "feat: make cross-model plugin canonical for reference files

Moves context-injection-contract.md into plugin references/.
Replaces docs/references/ originals with symlinks to plugin.
Plugin is now the single source of truth for:
- consultation-contract.md
- consultation-profiles.yaml
- context-injection-contract.md"
```

---

## Task 4: Migrate codex-reviewer agent

**Files:**
- Create: `packages/plugins/cross-model/agents/codex-reviewer.md`

**Step 1: Copy codex-reviewer to plugin**

```bash
cp .claude/agents/codex-reviewer.md packages/plugins/cross-model/agents/codex-reviewer.md
```

**Step 2: Verify the agent has no repo-relative path references that need transformation**

```bash
grep -n 'docs/references\|packages/\|\.\./\.\.' packages/plugins/cross-model/agents/codex-reviewer.md
```

Expected: no matches (codex-reviewer is self-contained — it doesn't reference contract files).

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-reviewer.md
git commit -m "feat: add codex-reviewer agent to cross-model plugin"
```

---

## Task 5: Migrate nudge hook with guardrails

**Files:**
- Create: `packages/plugins/cross-model/scripts/nudge_codex.py`
- Modify: `packages/plugins/cross-model/hooks/hooks.json`

**Step 1: Create the guarded nudge hook script**

Create `packages/plugins/cross-model/scripts/nudge_codex.py`:

```python
#!/usr/bin/env python3
# /// hook
# event: PostToolUseFailure
# matcher: Bash
# timeout: 5
# ///
"""
Suggest /codex consultation after repeated Bash failures.

Opt-in only: set CROSS_MODEL_NUDGE=1 to enable. User-scope plugins
affect all projects — nudging should be explicit.

Exit codes:
  0 - Success (with optional additionalContext JSON)
  1 - Hook error (non-blocking)
"""
import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path

THRESHOLD = 3


def state_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"claude-nudge-{session_id}"


def main() -> None:
    # Guardrail: opt-in gate
    if os.environ.get("CROSS_MODEL_NUDGE") != "1":
        sys.exit(0)

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"nudge-codex: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    try:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
        with os.fdopen(fd, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read().strip()
            count = (int(content) if content else 0) + 1

            if count >= THRESHOLD:
                f.seek(0)
                f.truncate()
                f.write("0")
            else:
                f.seek(0)
                f.truncate()
                f.write(str(count))
    except (ValueError, OSError):
        count = 1

    if count >= THRESHOLD:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
```

Key difference from original: `CROSS_MODEL_NUDGE=1` env var gate at the top of `main()`.

**Step 2: Add PostToolUseFailure matcher to hooks.json**

Edit `packages/plugins/cross-model/hooks/hooks.json` — add after the existing PostToolUse entry:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_codex_codex__codex|mcp__plugin_codex_codex__codex-reply",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_guard.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__plugin_codex_codex__codex|mcp__plugin_codex_codex__codex-reply",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_guard.py"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/nudge_codex.py"
          }
        ]
      }
    ]
  }
}
```

Note: tool names in PreToolUse/PostToolUse matchers are still `mcp__plugin_codex_codex__` — Task 6 renames them.

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/scripts/nudge_codex.py packages/plugins/cross-model/hooks/hooks.json
git commit -m "feat: add opt-in nudge hook to cross-model plugin

PostToolUseFailure hook suggests /codex after 3+ Bash failures.
Gated by CROSS_MODEL_NUDGE=1 env var — user-scope plugins affect
all projects, so nudging requires explicit opt-in."
```

---

## Task 6: Tool name cascade (two-pass rename)

**Files:**
- Modify: all files in `packages/plugins/cross-model/` containing tool name references

**Step 1: Count occurrences before transformation**

```bash
grep -r "mcp__plugin_codex_codex__" packages/plugins/cross-model/ | wc -l
grep -r "mcp__context-injection__" packages/plugins/cross-model/ | wc -l
```

Expected: ~21 for codex tool names, ~8 for context-injection tool names.

**Step 2: Pass 1 — Plugin rename (codex → cross-model)**

Transform `mcp__plugin_codex_codex__` → `mcp__plugin_cross-model_codex__` across all files in the plugin:

```bash
find packages/plugins/cross-model -type f \( -name '*.md' -o -name '*.json' -o -name '*.py' -o -name '*.yaml' \) \
  -exec sed -i '' 's/mcp__plugin_codex_codex__/mcp__plugin_cross-model_codex__/g' {} +
```

**Step 3: Verify Pass 1 — no stale codex tool names remain**

```bash
grep -r "mcp__plugin_codex_codex__" packages/plugins/cross-model/
```

Expected: no matches.

**Step 4: Pass 2 — Context injection bundling**

Transform `mcp__context-injection__` → `mcp__plugin_cross-model_context-injection__` across all files in the plugin:

```bash
find packages/plugins/cross-model -type f \( -name '*.md' -o -name '*.json' -o -name '*.py' -o -name '*.yaml' \) \
  -exec sed -i '' 's/mcp__context-injection__/mcp__plugin_cross-model_context-injection__/g' {} +
```

**Step 5: Verify Pass 2 — no stale context-injection tool names remain**

```bash
grep -r "mcp__context-injection__" packages/plugins/cross-model/
```

Expected: no matches.

**Step 6: Verify new tool names are correct**

```bash
grep -r "mcp__plugin_cross-model_" packages/plugins/cross-model/ | head -20
```

Expected: all references use `mcp__plugin_cross-model_codex__codex`, `mcp__plugin_cross-model_codex__codex-reply`, `mcp__plugin_cross-model_context-injection__process_turn`, `mcp__plugin_cross-model_context-injection__execute_scout`.

**Step 7: Spot-check critical files**

Verify the agent `tools` frontmatter (hard allowlist — wrong names = broken agent):

```bash
head -5 packages/plugins/cross-model/agents/codex-dialogue.md
```

Expected line 4: `tools: Bash, Read, Glob, Grep, mcp__plugin_cross-model_codex__codex, mcp__plugin_cross-model_codex__codex-reply, mcp__plugin_cross-model_context-injection__process_turn, mcp__plugin_cross-model_context-injection__execute_scout`

Verify hook matchers:

```bash
cat packages/plugins/cross-model/hooks/hooks.json | grep matcher
```

Expected: `mcp__plugin_cross-model_codex__codex|mcp__plugin_cross-model_codex__codex-reply` for PreToolUse/PostToolUse, `Bash` for PostToolUseFailure.

**Step 8: Broader verification — check for missed file types**

The `find` in Steps 2 and 4 filters for `.md`, `.json`, `.py`, `.yaml`. Verify no stale tool names exist in other file types (`.toml`, extensionless files, etc.):

```bash
grep -r "mcp__plugin_codex_codex__\|mcp__context-injection__" packages/plugins/cross-model/
```

Expected: no matches. If any found in files not covered by the extension filter, fix manually.

**Step 9: Commit**

```bash
git add packages/plugins/cross-model
git commit -m "feat: transform all tool names for cross-model plugin rename

Pass 1: mcp__plugin_codex_codex__ → mcp__plugin_cross-model_codex__
Pass 2: mcp__context-injection__ → mcp__plugin_cross-model_context-injection__

Affects: skill allowed-tools, agent tools frontmatter, agent body
text, hook matchers, consultation contract, codex_guard.py."
```

---

## Task 7: Update metadata and marketplace

**Files:**
- Modify: `packages/plugins/cross-model/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `packages/plugins/cross-model/CHANGELOG.md`
- Modify: `packages/plugins/cross-model/README.md`
- Modify: `.claude/CLAUDE.md`

**Step 1: Update plugin.json**

Edit `packages/plugins/cross-model/.claude-plugin/plugin.json`:

```json
{
  "name": "cross-model",
  "version": "1.0.0",
  "description": "Cross-model consultation: Codex integration, context injection, and enforcement hooks",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["codex", "consultation", "second-opinion", "cross-model", "context-injection"]
}
```

Changes: version `0.1.0` → `1.0.0`, description updated, keywords expanded.

**Step 2: Update marketplace.json**

Edit `.claude-plugin/marketplace.json`:

```json
{
  "name": "cross-model",
  "owner": { "name": "JP" },
  "plugins": [
    { "name": "cross-model", "source": "./packages/plugins/cross-model" }
  ]
}
```

Changes: plugin name `codex` → `cross-model`, source path updated. Old `codex` entry removed.

**Step 3: Write CHANGELOG.md**

Replace `packages/plugins/cross-model/CHANGELOG.md` with:

```markdown
# Changelog

## [1.0.0] — 2026-02-18

### Added

- Context injection MCP server bundled (vendored from `packages/context-injection/`)
- `codex-reviewer` agent for single-turn code review
- Opt-in nudge hook: suggests `/codex` after repeated Bash failures (`CROSS_MODEL_NUDGE=1`)
- `context-injection-contract.md` in plugin references (canonical)

### Changed

- Renamed from `codex` to `cross-model`
- Plugin is now canonical source for consultation contract, profiles, and context injection contract
- All tool names updated for plugin rename (`mcp__plugin_cross-model_codex__*`, `mcp__plugin_cross-model_context-injection__*`)
- Context injection tools no longer require separate repo-level MCP configuration

### Migration

Uninstall old plugin and install new:
```bash
claude plugin uninstall codex@cross-model
claude plugin marketplace update cross-model
claude plugin install cross-model@cross-model
```

## [0.1.0] — 2026-02-18

### Added

- `/codex` skill (237 lines, 7 governance rules)
- `codex-dialogue` subagent for extended multi-turn consultations
- Consultation contract (16 sections, normative) and 5 named profiles
- PreToolUse enforcement hook: tiered credential detection (strict/contextual/shadow)
- PostToolUse consultation event logging to `~/.claude/.codex-events.jsonl`
- Auto-configured `codex mcp-server` MCP connection
```

**Step 4: Update README.md**

Replace the first paragraph and installation section of `packages/plugins/cross-model/README.md` to reflect the cross-model scope. Include:
- Description covering all three systems (Codex, context injection, future learning)
- Updated install command: `claude plugin install cross-model@cross-model`
- Note that `CROSS_MODEL_NUDGE=1` enables the opt-in failure nudge
- Prerequisites: Codex CLI + `uv` (for context injection server)

**Step 5: Update .claude/CLAUDE.md — marketplace, tool names, and paths**

Search `.claude/CLAUDE.md` for all stale references. Three categories of updates:

**5a: Marketplace references**
- Install command: `claude plugin install cross-model@cross-model`
- Any references to "codex plugin" → "cross-model plugin"

**5b: Tool name references (4 occurrences)**

In the "Codex Integration" table:
- `mcp__plugin_codex_codex__codex`, `mcp__plugin_codex_codex__codex-reply` → `mcp__plugin_cross-model_codex__codex`, `mcp__plugin_cross-model_codex__codex-reply`

In the "Context Injection" table:
- `mcp__context-injection__process_turn`, `mcp__context-injection__execute_scout` → `mcp__plugin_cross-model_context-injection__process_turn`, `mcp__plugin_cross-model_context-injection__execute_scout`

**5c: Agent path reference**

In the "Codex Integration" table:
- `| Agent | .claude/agents/codex-dialogue.md |` → update to reference the plugin location or the plugin itself (e.g., `| Agent | cross-model plugin: agents/codex-dialogue.md |`)

Verify no stale references remain:

```bash
grep -n "mcp__plugin_codex_codex__\|mcp__context-injection__\|\.claude/agents/codex-" .claude/CLAUDE.md
```

Expected: no matches.

**Step 6: Commit**

```bash
git add packages/plugins/cross-model/.claude-plugin/plugin.json .claude-plugin/marketplace.json packages/plugins/cross-model/CHANGELOG.md packages/plugins/cross-model/README.md .claude/CLAUDE.md
git commit -m "feat: update metadata for cross-model plugin v1.0.0

Bumps version to 1.0.0, updates marketplace entry, CHANGELOG,
README, and CLAUDE.md references (tool names, agent paths,
install command). Install command is now:
claude plugin install cross-model@cross-model"
```

---

## Task 8: Update validation scripts

**Files:**
- Modify: `scripts/validate_consultation_contract.py`
- Modify: `tests/test_consultation_contract_sync.py`

**Context:** The validation script references three paths (lines 130-132):
- `contract_path` → `docs/references/consultation-contract.md`
- `skill_path` → `.claude/skills/codex/SKILL.md`
- `agent_path` → `.claude/agents/codex-dialogue.md`

The skill path has been broken since PR #13 (project-level skill removed). All three paths must be updated to plugin-canonical locations.

**Step 1: Find all path constants in validate_consultation_contract.py**

```bash
grep -n 'docs/references\|\.claude/skills\|\.claude/agents\|contract_path\|skill_path\|agent_path' scripts/validate_consultation_contract.py
```

**Step 2: Update all three path constants**

Change line 130: `docs/references/consultation-contract.md` → `packages/plugins/cross-model/references/consultation-contract.md`
Change line 131: `.claude/skills/codex/SKILL.md` → `packages/plugins/cross-model/skills/codex/SKILL.md`
Change line 132: `.claude/agents/codex-dialogue.md` → `packages/plugins/cross-model/agents/codex-dialogue.md`

The symlinks at `docs/references/` would work for the contract, but pointing directly at canonical locations is clearer.

**Step 3: Find the path constant in test_consultation_contract_sync.py**

```bash
grep -n 'docs/references\|CONTRACT_PATH\|CANONICAL' tests/test_consultation_contract_sync.py
```

**Step 4: Update the test path constant**

Change the `CONTRACT_PATH` from `docs/references/consultation-contract.md` to `packages/plugins/cross-model/references/consultation-contract.md`.

**Step 5: Run validation script directly**

```bash
uv run scripts/validate_consultation_contract.py
```

Expected: 16-section check passes (previously failing due to missing skill path).

**Step 6: Run validation tests**

```bash
uv run pytest tests/test_consultation_contract_sync.py -v
```

Expected: All 13 tests pass (previously 1 failing due to missing skill path).

**Step 7: Commit**

```bash
git add scripts/validate_consultation_contract.py tests/test_consultation_contract_sync.py
git commit -m "fix: update validation scripts for plugin-canonical paths

Updates contract, skill, and agent paths to point at
packages/plugins/cross-model/ instead of docs/references/
and .claude/ (project-level skill removed in PR #13,
project-level agent removed in Task 10)."
```

---

## Task 9: Smoke test and verification

**Files:** No file changes — verification only.

**Step 1: Run context injection tests (from development source)**

```bash
cd packages/context-injection && uv run pytest
```

Expected: 969 tests pass. These tests run against the development source, not the vendored copy. They verify the code that the build script vendors.

**Step 2: Run codex guard tests**

```bash
uv run pytest tests/test_codex_guard.py -v
```

Expected: 24 tests pass.

**Step 3: Run consultation contract tests**

```bash
uv run pytest tests/test_consultation_contract_sync.py -v
```

Expected: 13 tests pass with updated paths.

**Step 4: Lint the plugin scripts**

```bash
uv run ruff check packages/plugins/cross-model/scripts/
```

Expected: no errors.

**Step 5: Validate plugin structure**

This requires running outside the current Claude session:

```bash
claude plugin validate packages/plugins/cross-model
```

Or test by loading the plugin directly:

```bash
claude --plugin-dir packages/plugins/cross-model
```

Verify:
- Plugin loads without errors
- `/cross-model:codex` appears as a skill
- `cross-model:codex-dialogue` and `cross-model:codex-reviewer` appear as agents
- Both MCP servers initialize (check `claude --debug` output)

**Step 6: Verify symlinks resolve**

```bash
file docs/references/consultation-contract.md
file docs/references/consultation-profiles.yaml
file docs/references/context-injection-contract.md
```

Expected: all three show as symbolic links pointing to `../../packages/plugins/cross-model/references/...`

**Step 7: Verify no stale tool names in plugin and CLAUDE.md**

```bash
grep -r "mcp__plugin_codex_codex__" packages/plugins/cross-model/ .claude/CLAUDE.md
grep -r "mcp__context-injection__" packages/plugins/cross-model/ .claude/CLAUDE.md
```

Expected: no matches. Note: `.claude/agents/` is excluded from this check — those files still contain old tool names but are deleted in Task 10.

---

## Task 10: Clean up project-level files

**Files:**
- Remove: `packages/plugins/codex/` (old plugin)
- Remove: `.claude/agents/codex-dialogue.md` (plugin is canonical)
- Remove: `.claude/agents/codex-reviewer.md` (plugin is canonical)
- Remove: `.claude/hooks/nudge-codex-consultation.py` (plugin is canonical)
- Remove: `.mcp.json` (repo-level context-injection server — now bundled in plugin)

**Step 1: Remove old codex plugin**

```bash
trash packages/plugins/codex
```

**Step 2: Remove project-level agents**

```bash
trash .claude/agents/codex-dialogue.md
trash .claude/agents/codex-reviewer.md
```

**Step 3: Remove project-level nudge hook**

```bash
trash .claude/hooks/nudge-codex-consultation.py
```

**Step 4: Remove repo-level .mcp.json**

The repo-level `.mcp.json` starts a context-injection MCP server with `mcp__context-injection__*` tool names. After migration, nothing references those tools — the plugin provides `mcp__plugin_cross-model_context-injection__*` instead. Remove to avoid confusion.

```bash
trash .mcp.json
```

Note: for development testing of context injection code, run tests directly (`cd packages/context-injection && uv run pytest`). The MCP server is only needed at runtime via the plugin.

**Step 5: Verify no dangling references to removed files**

```bash
grep -r "\.claude/agents/codex-" .claude/ docs/ --include='*.md'
grep -r "nudge-codex-consultation" .claude/ docs/ --include='*.md' --include='*.json'
grep -r "mcp__context-injection__" .claude/ docs/ scripts/ tests/ --include='*.md' --include='*.py' --include='*.json'
```

Fix any references found (update or remove).

**Step 6: Commit**

```bash
git add packages/plugins/codex .claude/agents/codex-dialogue.md .claude/agents/codex-reviewer.md .claude/hooks/nudge-codex-consultation.py .mcp.json
git commit -m "chore: remove project-level files replaced by cross-model plugin

Removes:
- packages/plugins/codex/ (replaced by cross-model)
- .claude/agents/codex-dialogue.md (plugin canonical)
- .claude/agents/codex-reviewer.md (plugin canonical)
- .claude/hooks/nudge-codex-consultation.py (plugin canonical)
- .mcp.json (context-injection now bundled in plugin)"
```

**Step 7: Uninstall old plugin (separate session)**

After merging and restarting Claude Code:

```bash
claude plugin uninstall codex@cross-model
claude plugin marketplace update cross-model
claude plugin install cross-model@cross-model
```

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest`
Expected: All 969 tests pass

Run: `uv run pytest tests/test_codex_guard.py`
Expected: All 24 tests pass

Run: `uv run pytest tests/test_consultation_contract_sync.py`
Expected: All 13 tests pass (using new plugin-canonical paths)

Run: `uv run ruff check packages/plugins/cross-model/scripts/`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Delivers |
|--------|-------------|------------------------|
| `packages/plugins/cross-model/` | New | Self-contained cross-model plugin (replaces `codex` plugin) |
| `packages/plugins/cross-model/context-injection/` | New | Vendored Python MCP server |
| `packages/plugins/cross-model/references/context-injection-contract.md` | New | Canonical MCP protocol spec (moved from docs/) |
| `packages/plugins/cross-model/agents/codex-reviewer.md` | New | Code review agent (migrated from project) |
| `packages/plugins/cross-model/scripts/nudge_codex.py` | New | Failure nudge hook with opt-in guardrails |
| `scripts/build-cross-model-plugin` | New | Build script to sync vendored context injection |
| `packages/plugins/cross-model/hooks/hooks.json` | Modified | Added nudge hook + updated tool name matchers |
| `.claude-plugin/marketplace.json` | Modified | Updated plugin name and source path |
| `scripts/validate_consultation_contract.py` | Modified | Updated canonical path to plugin |
| `tests/test_consultation_contract_sync.py` | Modified | Updated canonical path to plugin |
| `docs/references/{3 files}` | Modified | Replaced with symlinks to plugin |
| `.claude/CLAUDE.md` | Modified | Updated marketplace/install references, tool names, agent paths |
| `packages/plugins/cross-model/context-injection/README.vendored.md` | New | Warning marker for vendored copy |
| `packages/plugins/codex/` | Removed | Replaced by cross-model plugin |
| `.claude/agents/codex-{dialogue,reviewer}.md` | Removed | Replaced by plugin agents |
| `.claude/hooks/nudge-codex-consultation.py` | Removed | Replaced by plugin hook |
| `.mcp.json` | Removed | Context-injection now bundled in plugin |
