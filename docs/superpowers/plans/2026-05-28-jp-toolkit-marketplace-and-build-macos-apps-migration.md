# jp-toolkit Marketplace and build-macos-apps Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a second, local-only marketplace (`jp-toolkit`) alongside the existing `turbo-mode` marketplace; restructure `packages/plugins/` symmetrically into `turbo-mode/` and `jp-toolkit/` subdirectories; migrate the OpenAI `build-macos-apps` Codex plugin into `jp-toolkit` as a Claude-native skills-only plugin (3 upstream slash commands convert to skills).

**Architecture:** Symmetric marketplace layout — `marketplaces/{turbo-mode,jp-toolkit}/.claude-plugin/marketplace.json` + matching plugin subdirectories `packages/plugins/{turbo-mode,jp-toolkit}/<plugin>/`. The migrated build-macos-apps plugin reauthored as JP-owned with OpenAI's MIT notice preserved in LICENSE. Codex-specific contracts (`.codex/environments/environment.toml` Run-button wiring, `agents/openai.yaml` surface-presentation files, `assets/`, `interface` manifest block) stripped. `script/build_and_run.sh` retained as host-agnostic.

**Tech Stack:** Bash + `git mv` for file motion, JSON (plugin and marketplace manifests), Markdown + YAML frontmatter (skills, README, docs), TOML (`pyproject.toml` uv workspace), uv (workspace resolution check).

---

## File Structure

### Created

| Path | Responsibility |
|------|---------------|
| `marketplaces/turbo-mode/.claude-plugin/marketplace.json` | Distributed marketplace manifest (relocated, source paths updated) |
| `marketplaces/jp-toolkit/.claude-plugin/marketplace.json` | New local-only marketplace manifest |
| `packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json` | Lean JP-authored manifest replacing OpenAI Codex manifest |
| `packages/plugins/jp-toolkit/build-macos-apps/README.md` | Plugin overview with upstream credit |
| `packages/plugins/jp-toolkit/build-macos-apps/LICENSE` | OpenAI MIT notice preserved verbatim |
| `packages/plugins/jp-toolkit/build-macos-apps/skills/<11 existing skills>/SKILL.md` + references | Existing skills copied without per-skill `agents/` subdirs |
| `packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/build-script-bootstrap.md` | Renamed from `run-button-bootstrap.md`; `.codex/.toml` schema section deleted |
| `packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app/SKILL.md` | Converted from `commands/build-and-run-macos-app.md` |
| `packages/plugins/jp-toolkit/build-macos-apps/skills/fix-codesign-error/SKILL.md` | Converted from `commands/fix-codesign-error.md` |
| `packages/plugins/jp-toolkit/build-macos-apps/skills/test-macos-app/SKILL.md` | Converted from `commands/test-macos-app.md` |
| `docs/archived/2026-codex-collaboration-extracted/MIGRATED.md` | Tombstone relocated out of active package tree |

### Moved (via `git mv`)

| Source | Destination |
|--------|-------------|
| `.claude-plugin/marketplace.json` | `marketplaces/turbo-mode/.claude-plugin/marketplace.json` |
| `packages/plugins/handoff/` | `packages/plugins/turbo-mode/handoff/` |
| `packages/plugins/context-metrics/` | `packages/plugins/turbo-mode/context-metrics/` |
| `packages/plugins/ticket/` | `packages/plugins/turbo-mode/ticket/` |
| `packages/plugins/superspec/` | `packages/plugins/turbo-mode/superspec/` |
| `packages/plugins/codex-collaboration/MIGRATED.md` | `docs/archived/2026-codex-collaboration-extracted/MIGRATED.md` |

### Modified

| Path | What changes |
|------|-------------|
| `.claude/CLAUDE.md` | Rewrite "How This Repo Works", "Directory Structure", "Packages" sections |
| `.codex/AGENTS.md` | Update Packages table paths for existing plugins; update `.claude-plugin/` directory-tree line. Leave unrelated stale entries (cross-model, context-injection) alone per narrow-scope rule |
| `pyproject.toml` | Update `[tool.uv.workspace]` members to `packages/plugins/turbo-mode/<plugin>`; update codex-collab comment to new tombstone location |

### Deleted

| Path | Why |
|------|-----|
| `.claude-plugin/` directory (after marketplace.json moved out) | Replaced by `marketplaces/turbo-mode/.claude-plugin/` |
| `packages/plugins/codex-collaboration/` directory (after MIGRATED.md moved out) | Tombstone relocated to `docs/archived/` |
| `packages/plugins/build-macos-apps/` directory entirely (after migration complete) | Replaced by `packages/plugins/jp-toolkit/build-macos-apps/` |

### NOT carried over to the migrated tree

- `.codex-plugin/` directory (Codex-only manifest location)
- `agents/openai.yaml` at plugin root + the plugin-level `agents/` directory
- 11 × `skills/<name>/agents/openai.yaml` + each per-skill `agents/` directory
- `assets/app-icon.png`, `assets/build-macos-apps-small.svg`, `assets/` directory
- `commands/` directory entirely (content converted to skills)
- All `.DS_Store` files

---

## Task 1: Create branch and directory skeleton

**Files:**
- Create: `marketplaces/turbo-mode/.claude-plugin/.gitkeep`
- Create: `marketplaces/jp-toolkit/.claude-plugin/.gitkeep`
- Create: `packages/plugins/turbo-mode/.gitkeep`
- Create: `packages/plugins/jp-toolkit/.gitkeep`
- Create: `docs/archived/2026-codex-collaboration-extracted/.gitkeep`

- [ ] **Step 1: Verify clean working tree**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev && git status --short
```

Expected: no output (clean working tree). If anything is uncommitted, stop and address before proceeding.

- [ ] **Step 2: Create the working branch**

```bash
git checkout -b chore/jp-toolkit-marketplace-and-build-macos-apps
```

Expected: `Switched to a new branch 'chore/jp-toolkit-marketplace-and-build-macos-apps'`.

- [ ] **Step 3: Create directory skeleton**

```bash
mkdir -p marketplaces/turbo-mode/.claude-plugin
mkdir -p marketplaces/jp-toolkit/.claude-plugin
mkdir -p packages/plugins/turbo-mode
mkdir -p packages/plugins/jp-toolkit
mkdir -p docs/archived/2026-codex-collaboration-extracted
touch marketplaces/turbo-mode/.claude-plugin/.gitkeep
touch marketplaces/jp-toolkit/.claude-plugin/.gitkeep
touch packages/plugins/turbo-mode/.gitkeep
touch packages/plugins/jp-toolkit/.gitkeep
touch docs/archived/2026-codex-collaboration-extracted/.gitkeep
```

- [ ] **Step 4: Verify all directories exist**

```bash
ls -d marketplaces/turbo-mode/.claude-plugin marketplaces/jp-toolkit/.claude-plugin packages/plugins/turbo-mode packages/plugins/jp-toolkit docs/archived/2026-codex-collaboration-extracted
```

Expected: all 5 paths listed, no `ls` errors.

- [ ] **Step 5: Commit skeleton**

```bash
git add marketplaces/ packages/plugins/turbo-mode/.gitkeep packages/plugins/jp-toolkit/.gitkeep docs/archived/2026-codex-collaboration-extracted/
git commit -m "chore: scaffold marketplaces/ + jp-toolkit/turbo-mode subdirs + archive dir"
```

---

## Task 2: Rewrite CLAUDE.md "How This Repo Works" section

**Files:**
- Modify: `.claude/CLAUDE.md` (lines ~7–14)

- [ ] **Step 1: Edit "How This Repo Works" section**

Replace the existing section. Find:

```markdown
## How This Repo Works

- Develop skills, commands, and agents in `extensions/` (NOT auto-loaded into Claude's context)
- Develop hooks and packages in `.claude/hooks/` and `packages/`
- Promote to `~/.claude/` when ready

`extensions/` lives outside `.claude/` deliberately. Anything under `.claude/skills/`, `.claude/agents/`, or `.claude/commands/` would auto-load into every session in this repo, duplicating the user-level versions and crowding the skill-listing budget. Keeping dev-staged extensions at `extensions/` makes them ordinary editable files until `scripts/promote` deploys them to `~/.claude/`.
```

Replace with:

```markdown
## How This Repo Works

- Develop skills, commands, and agents in `extensions/` (NOT auto-loaded into Claude's context)
- Develop hooks and packages in `.claude/hooks/` and `packages/`
- Develop plugins in `packages/plugins/<marketplace>/<plugin>/` under one of two marketplaces:
  - `turbo-mode` — distributed marketplace (intended for public release)
  - `jp-toolkit` — local-only marketplace (personal plugins, not distributed)
- Promote individual extensions to `~/.claude/` via `scripts/promote`; install plugins via their marketplace

`extensions/` lives outside `.claude/` deliberately. Anything under `.claude/skills/`, `.claude/agents/`, or `.claude/commands/` would auto-load into every session in this repo, duplicating the user-level versions and crowding the skill-listing budget. Keeping dev-staged extensions at `extensions/` makes them ordinary editable files until `scripts/promote` deploys them to `~/.claude/`.

Plugins are distinct from per-extension dev: each plugin lives in `packages/plugins/<marketplace>/<plugin>/` and is registered through its marketplace's `marketplace.json`. The two marketplaces are co-equal in structure; their difference is intent — `turbo-mode` is meant for public distribution, `jp-toolkit` is not.
```

- [ ] **Step 2: Verify edit applied**

```bash
grep -A 5 'Develop plugins in' .claude/CLAUDE.md
```

Expected: shows the new bullet about `turbo-mode` and `jp-toolkit`.

---

## Task 3: Rewrite CLAUDE.md "Directory Structure" section

**Files:**
- Modify: `.claude/CLAUDE.md` (lines ~138–165)

- [ ] **Step 1: Edit Directory Structure code-fence**

Find:

```markdown
## Directory Structure

\`\`\`
extensions/       # Dev-staging for skills/commands/agents (NOT auto-loaded)
├── skills/       # Skills under development (SKILL.md required)
├── commands/     # Slash commands under development
└── agents/       # Subagents under development

.claude/
├── hooks/        # Hooks (Python scripts, synced to settings.json) — auto-loaded
├── rules/        # Auto-loaded session rules (keep minimal)
├── handoffs/     # Session handoff documents (gitignored)
├── sessions/     # Session notes (gitignored)
└── worktrees/    # Git worktree state (gitignored)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Codex consultation insights
├── tickets/      # Work tickets
└── audits/       # Quality audits

.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
\`\`\`
```

Replace with:

```markdown
## Directory Structure

\`\`\`
extensions/       # Dev-staging for skills/commands/agents (NOT auto-loaded)
├── skills/       # Skills under development (SKILL.md required)
├── commands/     # Slash commands under development
└── agents/       # Subagents under development

.claude/
├── hooks/        # Hooks (Python scripts, synced to settings.json) — auto-loaded
├── rules/        # Auto-loaded session rules (keep minimal)
├── handoffs/     # Session handoff documents (gitignored)
├── sessions/     # Session notes (gitignored)
└── worktrees/    # Git worktree state (gitignored)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Codex consultation insights
├── tickets/      # Work tickets
├── audits/       # Quality audits
└── archived/     # Archived docs (e.g., extracted-plugin tombstones)

marketplaces/     # Plugin marketplace manifests
├── turbo-mode/   # Distributed marketplace
│   └── .claude-plugin/marketplace.json
└── jp-toolkit/   # Local-only marketplace for personal plugins
    └── .claude-plugin/marketplace.json

packages/plugins/ # Plugin sources, grouped by marketplace
├── turbo-mode/   # Sources for distributed plugins
└── jp-toolkit/   # Sources for local-only plugins
\`\`\`
```

- [ ] **Step 2: Verify Directory Structure section reflects new layout**

```bash
grep -A 3 '^marketplaces/' .claude/CLAUDE.md
```

Expected: shows `marketplaces/` followed by `turbo-mode/` and `jp-toolkit/` subdirs.

---

## Task 4: Rewrite CLAUDE.md "Packages" section

**Files:**
- Modify: `.claude/CLAUDE.md` (lines ~167–179)

- [ ] **Step 1: Edit Packages section**

Find:

```markdown
## Packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
| superspec | `packages/plugins/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search |

> **codex-collaboration** was extracted to its own repo at `/Users/jp/Projects/active/codex-collaboration/` on 2026-05-11. The standalone repo is the sole authority. See `packages/plugins/codex-collaboration/MIGRATED.md` for the redirect.

Plugins deploy via `turbo-mode` marketplace. MCP servers and extensions deploy via `uv run scripts/promote`.
```

Replace with:

```markdown
## Packages

### turbo-mode marketplace (distributed)

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| handoff | `packages/plugins/turbo-mode/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/turbo-mode/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/turbo-mode/context-metrics/` | Python | Context window usage analysis |
| superspec | `packages/plugins/turbo-mode/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |

### jp-toolkit marketplace (local-only, not distributed)

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| build-macos-apps | `packages/plugins/jp-toolkit/build-macos-apps/` | Markdown (skills) | Build, run, test, debug, instrument macOS apps with Xcode, SwiftUI, AppKit; forked from OpenAI's Codex plugin under MIT |

### Other packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search |

> **codex-collaboration** was extracted to its own repo at `/Users/jp/Projects/active/codex-collaboration/` on 2026-05-11. The standalone repo is the sole authority. See `docs/archived/2026-codex-collaboration-extracted/MIGRATED.md` for the redirect.

Plugins deploy via their marketplace: `turbo-mode` is intended for public distribution; `jp-toolkit` is local-only and not registered beyond this laptop. MCP servers and extensions deploy via `uv run scripts/promote`.
```

- [ ] **Step 2: Verify Packages section has two marketplace tables**

```bash
grep -c '^### turbo-mode marketplace' .claude/CLAUDE.md
grep -c '^### jp-toolkit marketplace' .claude/CLAUDE.md
```

Expected: each command outputs `1`.

- [ ] **Step 3: Verify the codex-collab redirect points to new location**

```bash
grep 'docs/archived/2026-codex-collaboration-extracted' .claude/CLAUDE.md
```

Expected: line matches showing the new tombstone path.

- [ ] **Step 4: Commit CLAUDE.md updates**

```bash
git add .claude/CLAUDE.md
git commit -m "docs(claude-md): document two-marketplace layout and split Packages table"
```

---

## Task 5: Update .codex/AGENTS.md (narrow scope)

**Files:**
- Modify: `.codex/AGENTS.md`

Per the design decision: only update paths for plugins that are part of the marketplace restructure. Leave unrelated stale entries (cross-model, context-injection) alone — they are a separate cleanup concern.

- [ ] **Step 1: Update Directory Structure `.claude-plugin/` line**

Find:

```
.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
```

Replace with:

```
marketplaces/     # Plugin marketplace manifests
├── turbo-mode/   # Distributed marketplace
└── jp-toolkit/   # Local-only marketplace
```

- [ ] **Step 2: Update Packages table — handoff row**

Find:

```
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
```

Replace with:

```
| handoff | `packages/plugins/turbo-mode/handoff/` | Python | Session state persistence (save/load/search) |
```

- [ ] **Step 3: Update Packages table — ticket row**

Find:

```
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
```

Replace with:

```
| ticket | `packages/plugins/turbo-mode/ticket/` | Python | Repo-local ticket lifecycle management |
```

- [ ] **Step 4: Update Packages table — context-metrics row**

Find:

```
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
```

Replace with:

```
| context-metrics | `packages/plugins/turbo-mode/context-metrics/` | Python | Context window usage analysis |
```

- [ ] **Step 5: Update Packages table — superspec row**

Find:

```
| superspec | `packages/plugins/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
```

Replace with:

```
| superspec | `packages/plugins/turbo-mode/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
```

- [ ] **Step 6: Append jp-toolkit table after the existing Packages table**

After the line that reads `Plugins deploy via `turbo-mode` marketplace. ...`, append:

```markdown

### jp-toolkit marketplace (local-only)

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| build-macos-apps | `packages/plugins/jp-toolkit/build-macos-apps/` | Markdown (skills) | Build, run, test, debug, instrument macOS apps; forked from OpenAI's Codex plugin |
```

- [ ] **Step 7: Verify path updates**

```bash
grep 'packages/plugins/turbo-mode/' .codex/AGENTS.md | wc -l
```

Expected: at least 4 (one row per turbo-mode plugin).

- [ ] **Step 8: Commit AGENTS.md update**

```bash
git add .codex/AGENTS.md
git commit -m "docs(agents-md): update package paths for marketplace split"
```

---

## Task 6: Move existing turbo-mode plugins to subdirectory

**Files:**
- Move (via `git mv`): `packages/plugins/{handoff,context-metrics,ticket,superspec}/` → `packages/plugins/turbo-mode/<same>/`

- [ ] **Step 1: Move handoff**

```bash
git mv packages/plugins/handoff packages/plugins/turbo-mode/handoff
```

- [ ] **Step 2: Move context-metrics**

```bash
git mv packages/plugins/context-metrics packages/plugins/turbo-mode/context-metrics
```

- [ ] **Step 3: Move ticket**

```bash
git mv packages/plugins/ticket packages/plugins/turbo-mode/ticket
```

- [ ] **Step 4: Move superspec**

```bash
git mv packages/plugins/superspec packages/plugins/turbo-mode/superspec
```

- [ ] **Step 5: Verify the 4 plugins now live under turbo-mode/**

```bash
ls packages/plugins/turbo-mode/
```

Expected output:
```
context-metrics
handoff
superspec
ticket
```

- [ ] **Step 6: Verify the old paths are gone**

```bash
ls packages/plugins/ 2>&1 | grep -E '^(handoff|context-metrics|ticket|superspec)$' | wc -l
```

Expected: `0` (none of the four exist at the old top-level location).

---

## Task 7: Move and update turbo-mode marketplace.json

**Files:**
- Move (via `git mv`): `.claude-plugin/marketplace.json` → `marketplaces/turbo-mode/.claude-plugin/marketplace.json`
- Modify: the moved `marketplace.json` source paths

- [ ] **Step 1: Move the marketplace.json file**

```bash
git mv .claude-plugin/marketplace.json marketplaces/turbo-mode/.claude-plugin/marketplace.json
```

- [ ] **Step 2: Update source paths inside the moved file**

Edit `marketplaces/turbo-mode/.claude-plugin/marketplace.json`. Replace the entire file contents with:

```json
{
  "name": "turbo-mode",
  "owner": { "name": "JP" },
  "plugins": [
    { "name": "handoff", "source": "../../../packages/plugins/turbo-mode/handoff" },
    { "name": "context-metrics", "source": "../../../packages/plugins/turbo-mode/context-metrics" },
    { "name": "ticket", "source": "../../../packages/plugins/turbo-mode/ticket" },
    { "name": "superspec", "source": "../../../packages/plugins/turbo-mode/superspec" }
  ]
}
```

Note: the source paths use `../../../` because the marketplace.json lives at `marketplaces/turbo-mode/.claude-plugin/marketplace.json` — three directory levels deep relative to repo root.

- [ ] **Step 3: Verify the moved file's content**

```bash
cat marketplaces/turbo-mode/.claude-plugin/marketplace.json
```

Expected: the JSON content above, with all 4 plugin source paths starting with `../../../packages/plugins/turbo-mode/`.

- [ ] **Step 4: Remove the .gitkeep that's no longer needed**

```bash
git rm marketplaces/turbo-mode/.claude-plugin/.gitkeep
```

- [ ] **Step 5: Remove the now-empty repo-root .claude-plugin/ directory**

```bash
rmdir .claude-plugin
```

Expected: command succeeds (directory was empty after `git mv`).

- [ ] **Step 6: Verify repo-root .claude-plugin/ is gone**

```bash
ls .claude-plugin 2>&1
```

Expected: `ls: .claude-plugin: No such file or directory`.

---

## Task 8: Update pyproject.toml workspace members

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace `[tool.uv.workspace]` section**

Find:

```toml
[tool.uv.workspace]
members = [
    "packages/plugins/context-metrics",
    "packages/plugins/handoff",
    "packages/plugins/ticket",
    "packages/plugins/superspec",
]
# codex-collaboration extracted to /Users/jp/Projects/active/codex-collaboration on 2026-05-11.
# See packages/plugins/codex-collaboration/MIGRATED.md.
```

Replace with:

```toml
[tool.uv.workspace]
members = [
    "packages/plugins/turbo-mode/context-metrics",
    "packages/plugins/turbo-mode/handoff",
    "packages/plugins/turbo-mode/ticket",
    "packages/plugins/turbo-mode/superspec",
]
# codex-collaboration extracted to /Users/jp/Projects/active/codex-collaboration on 2026-05-11.
# See docs/archived/2026-codex-collaboration-extracted/MIGRATED.md.
```

- [ ] **Step 2: Verify uv workspace resolves**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev && uv sync
```

Expected: succeeds with no "missing workspace member" errors. If any error mentions a missing path, double-check Task 6 (plugin moves) and Step 1 above.

- [ ] **Step 3: Commit Phase B (turbo-mode relocation + workspace update)**

```bash
git add pyproject.toml marketplaces/turbo-mode/.claude-plugin/marketplace.json packages/plugins/turbo-mode/
git commit -m "refactor(plugins): move turbo-mode plugins + marketplace.json to symmetric layout"
```

---

## Task 9: Move codex-collaboration tombstone to archive

**Files:**
- Move (via `git mv`): `packages/plugins/codex-collaboration/MIGRATED.md` → `docs/archived/2026-codex-collaboration-extracted/MIGRATED.md`

- [ ] **Step 1: Move the tombstone**

```bash
git mv packages/plugins/codex-collaboration/MIGRATED.md docs/archived/2026-codex-collaboration-extracted/MIGRATED.md
```

- [ ] **Step 2: Remove the now-empty legacy directory**

```bash
rmdir packages/plugins/codex-collaboration
```

Expected: command succeeds.

- [ ] **Step 3: Remove the .gitkeep in the new archive directory**

```bash
git rm docs/archived/2026-codex-collaboration-extracted/.gitkeep
```

- [ ] **Step 4: Verify**

```bash
cat docs/archived/2026-codex-collaboration-extracted/MIGRATED.md | head -5
ls packages/plugins/codex-collaboration 2>&1
```

Expected: `cat` shows the MIGRATED.md content starting with `# MIGRATED`. `ls` errors with "No such file or directory".

- [ ] **Step 5: Commit tombstone move**

```bash
git add docs/archived/2026-codex-collaboration-extracted/ packages/plugins/codex-collaboration
git commit -m "chore: move codex-collaboration tombstone to docs/archived/"
```

---

## Task 10: Scaffold the migrated build-macos-apps tree

**Files:**
- Create: `packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json`
- Create: `packages/plugins/jp-toolkit/build-macos-apps/LICENSE`
- Create: `packages/plugins/jp-toolkit/build-macos-apps/README.md`

- [ ] **Step 1: Create the plugin directory and `.claude-plugin/` subdirectory**

```bash
mkdir -p packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin
mkdir -p packages/plugins/jp-toolkit/build-macos-apps/skills
```

- [ ] **Step 2: Remove the placeholder .gitkeep in jp-toolkit**

```bash
git rm packages/plugins/jp-toolkit/.gitkeep
```

- [ ] **Step 3: Write the lean plugin manifest**

Create `packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json` with this exact content:

```json
{
  "name": "build-macos-apps",
  "version": "0.1.0",
  "description": "Build, run, test, debug, instrument, and implement local macOS apps using Xcode, SwiftUI, AppKit interop, unified logging, and shell-first desktop workflows.",
  "author": { "name": "JP" },
  "license": "MIT",
  "keywords": ["macos", "swift", "swiftui", "appkit", "xcode", "swiftpm", "debugging", "codesign", "logging", "telemetry", "oslog"]
}
```

- [ ] **Step 4: Write the LICENSE file with OpenAI's MIT notice**

Create `packages/plugins/jp-toolkit/build-macos-apps/LICENSE` with this exact content:

```
MIT License

Copyright (c) OpenAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

If the upstream `openai/plugins` repository has a more specific LICENSE text for `build-macos-apps`, prefer that verbatim. Note in the README's attribution line if the LICENSE source is uncertain.

- [ ] **Step 5: Write the migrated README.md**

Create `packages/plugins/jp-toolkit/build-macos-apps/README.md` with this content:

```markdown
# Build macOS Apps Plugin

> Forked from OpenAI's `build-macos-apps` Codex plugin under the MIT License. Adapted for Claude Code by JP. See `LICENSE` for the original copyright notice.

This plugin packages macOS-first development workflows as Claude Code skills.

## Skills

- `appkit-interop` — bridge SwiftUI into AppKit for representables, panels, and responder chain
- `build-run-debug` — build, run, and debug macOS apps with shell-first Xcode/Swift workflows
- `build-and-run-macos-app` — set up a project-local `build_and_run.sh` script as the default build/run entrypoint
- `fix-codesign-error` — diagnose and repair macOS codesign/entitlement failures
- `liquid-glass` — implement modern macOS Liquid Glass UI patterns
- `packaging-notarization` — prepare distribution archives and notarization workflows
- `signing-entitlements` — inspect signing, entitlements, hardened runtime, Gatekeeper issues
- `swiftpm-macos` — build/run/test SwiftPM macOS packages
- `swiftui-patterns` — build macOS SwiftUI scenes with desktop patterns
- `telemetry` — add and verify Logger / os.Logger instrumentation
- `test-macos-app` — execute the macOS test suite (Xcode or SwiftPM) and report results
- `test-triage` — triage failing macOS tests and classify failure categories
- `view-refactor` — refactor large SwiftUI views into stable scene/selection/command structure
- `window-management` — customize SwiftUI window chrome, placement, restoration

## What It Covers

- discovering local Xcode workspaces, projects, and Swift packages
- building and running macOS apps with shell-first desktop workflows via a project-local `script/build_and_run.sh` entrypoint
- implementing native macOS SwiftUI scenes, menus, settings, toolbars, and multiwindow flows
- adopting modern macOS Liquid Glass and design-system guidance
- bridging into AppKit for representables, responder-chain behavior, panels, and other desktop-only needs
- refactoring large macOS view files toward stable scene, selection, and command structure
- adding lightweight `Logger` / `os.Logger` instrumentation
- reading and verifying runtime events with Console, `log stream`, and process logs
- triaging failing unit, integration, and UI-hosted macOS tests
- debugging launch failures, crashes, linker problems, and runtime regressions
- inspecting signing identities, entitlements, hardened runtime, and Gatekeeper issues
- preparing packaging and notarization workflows for distribution

## What It Does Not Cover

- iOS, watchOS, or tvOS simulator control
- desktop UI automation
- App Store Connect release management
- pixel-perfect visual design or design-system generation

## Plugin Structure

- `.claude-plugin/plugin.json` — plugin manifest
- `skills/` — skill payload, each with `SKILL.md`, optional `references/`, `assets/`, `scripts/`
- `README.md` — this file
- `LICENSE` — original MIT copyright preserved

## Notes

This plugin does not ship a plugin-local `.mcp.json` or any hooks.

The default posture is shell-first: `xcodebuild`, `swift`, `open`, `lldb`, `codesign`, `spctl`, `plutil`, and `log stream`, with native SwiftUI scene design and AppKit interop layered on top. No simulator tooling, no touch-driven UI inspection.
```

- [ ] **Step 6: Verify scaffolding**

```bash
ls packages/plugins/jp-toolkit/build-macos-apps/
cat packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json
```

Expected `ls`: shows `.claude-plugin`, `LICENSE`, `README.md`, `skills`.
Expected `cat`: shows the lean 6-field manifest.

---

## Task 11: Copy existing 11 skills into the migrated tree (without per-skill agents/)

**Files:**
- Create: `packages/plugins/jp-toolkit/build-macos-apps/skills/<each of 11 skill dirs>/...`

- [ ] **Step 1: Copy each skill directory, excluding `agents/`**

```bash
SRC=/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/build-macos-apps/skills
DST=/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/jp-toolkit/build-macos-apps/skills

for skill in appkit-interop build-run-debug liquid-glass packaging-notarization signing-entitlements swiftpm-macos swiftui-patterns telemetry test-triage view-refactor window-management; do
  mkdir -p "$DST/$skill"
  rsync -a --exclude='agents' --exclude='.DS_Store' "$SRC/$skill/" "$DST/$skill/"
done
```

- [ ] **Step 2: Verify all 11 skills landed**

```bash
ls packages/plugins/jp-toolkit/build-macos-apps/skills/ | wc -l
```

Expected: `11`.

- [ ] **Step 3: Verify no per-skill agents/ directory snuck through**

```bash
find packages/plugins/jp-toolkit/build-macos-apps/skills -type d -name agents
```

Expected: no output (zero agents/ directories anywhere under skills).

- [ ] **Step 4: Verify no .DS_Store files**

```bash
find packages/plugins/jp-toolkit/build-macos-apps -name '.DS_Store'
```

Expected: no output.

---

## Task 12: Apply content surgery to README.md (already created in Task 10)

The README was written from scratch in Task 10 with Codex references already absent. This task verifies that and adds nothing new.

- [ ] **Step 1: Verify no Codex references in the new README**

```bash
grep -iE '(\.codex|codex app|run button)' packages/plugins/jp-toolkit/build-macos-apps/README.md
```

Expected: no matches.

- [ ] **Step 2: Verify upstream credit is present**

```bash
grep -i 'forked from openai' packages/plugins/jp-toolkit/build-macos-apps/README.md
```

Expected: matches the attribution line at the top of README.

---

## Task 13: Strip Codex references from skills/build-run-debug/SKILL.md

**Files:**
- Modify: `packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/SKILL.md`

- [ ] **Step 1: Replace the "Quick Start" intro paragraph**

Find:

```markdown
## Quick Start

Use this skill to set up one project-local `script/build_and_run.sh` entrypoint,
wire `.codex/environments/environment.toml` so the Codex app shows a Run button,
then use that script as the default build/run path.
```

Replace with:

```markdown
## Quick Start

Use this skill to set up one project-local `script/build_and_run.sh` entrypoint,
then use that script as the default build/run path.
```

- [ ] **Step 2: Strip the Codex git-features line in Workflow Step 1**

Find:

```markdown
   - If no git repo is present, run `git init` at the project/workspace root before building so Codex app git-backed features are available. Never run `git init` inside a nested subdirectory when the current workspace already belongs to a parent repo.
```

Replace with:

```markdown
   - If no git repo is present, run `git init` at the project/workspace root before building. Never run `git init` inside a nested subdirectory when the current workspace already belongs to a parent repo.
```

- [ ] **Step 3: Update the reference doc filename in Workflow Step 3**

Find:

```markdown
   - Use `references/run-button-bootstrap.md` as the canonical source for the
     script shape and exact environment file format. Do not fork a second
     authoritative snippet in another skill or command.
```

Replace with:

```markdown
   - Use `references/build-script-bootstrap.md` as the canonical source for the
     script shape. Do not fork a second authoritative snippet in another skill or command.
```

- [ ] **Step 4: Delete Workflow Step 4 entirely (the Codex environment writing step)**

Find:

```markdown
4. Write `.codex/environments/environment.toml` at the project root once the script exists.
   - Use this exact placement: `.codex/environments/environment.toml`.
   - Use the exact action shape in `references/run-button-bootstrap.md`.
   - This file is what gives the user a Codex app Run button wired to the script.
   - If the project already has this file, update the `Run` action command to point at `./script/build_and_run.sh` instead of creating a duplicate action.
   - Keep this Codex environment config separate from Swift app source files.

5. Build and run through the script.
```

Replace with:

```markdown
4. Build and run through the script.
```

(Note: this collapses old Step 5 into Step 4 because Step 4 was removed. Subsequent Workflow steps renumber from 5 onward but since they were 5–8 they become 5–7.)

After Step 4, the workflow has step `4. Build and run through the script.` (renumbered from old step 5) followed by old-numbered steps `6.`, `7.`, `8.`. The next three steps renumber those to `5.`, `6.`, `7.` respectively. Each find/replace touches only the header line — the indented bullet body below each header remains in place.

- [ ] **Step 5: Renumber step 6 → 5**

Find:

```markdown
6. Summarize failures correctly.
```

Replace with:

```markdown
5. Summarize failures correctly.
```

- [ ] **Step 6: Renumber step 7 → 6**

Find:

```markdown
7. Debug the right way.
```

Replace with:

```markdown
6. Debug the right way.
```

- [ ] **Step 7: Renumber step 8 → 7**

Find:

```markdown
8. Use Xcode-aware MCP tooling only when it helps.
```

Replace with:

```markdown
7. Use Xcode-aware MCP tooling only when it helps.
```

- [ ] **Step 8: Update the References section**

Find:

```markdown
## References

- `references/run-button-bootstrap.md`: canonical `build_and_run.sh` and `.codex/environments/environment.toml` contract.
```

Replace with:

```markdown
## References

- `references/build-script-bootstrap.md`: canonical `build_and_run.sh` script contract.
```

- [ ] **Step 9: Update Guardrails — remove Codex environment guardrail**

Find:

```markdown
- Do not write `.codex/environments/environment.toml` before the run script exists, and do not point the Run action at a stale script path.
```

Replace with nothing (delete the entire line including the trailing newline).

- [ ] **Step 10: Update Output Expectations**

Find:

```markdown
- the script path and Codex environment action you configured, if applicable
```

Replace with:

```markdown
- the script path you configured, if applicable
```

- [ ] **Step 11: Verify no Codex references remain in build-run-debug/SKILL.md**

```bash
grep -iE '(\.codex|codex app|run button|run-button-bootstrap)' packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/SKILL.md
```

Expected: no matches.

---

## Task 14: Strip Codex references from skills/swiftui-patterns/SKILL.md

**Files:**
- Modify: `packages/plugins/jp-toolkit/build-macos-apps/skills/swiftui-patterns/SKILL.md`

- [ ] **Step 1: Strip the Codex git-features line in "New app scaffolding"**

Find:

```markdown
- Before creating the scaffold, check whether the workspace is already inside a git repo with `git rev-parse --is-inside-work-tree`. If not, run `git init` at the project root so Codex app git-backed features are available from the start. Do not initialize a nested repo inside an existing parent checkout.
- For a new app scaffold, also create one project-local `script/build_and_run.sh` and `.codex/environments/environment.toml` so the Codex app Run button works immediately. Use the exact bootstrap contract from `build-run-debug` and its `references/run-button-bootstrap.md` file rather than inventing a second variant here.
```

Replace with:

```markdown
- Before creating the scaffold, check whether the workspace is already inside a git repo with `git rev-parse --is-inside-work-tree`. If not, run `git init` at the project root. Do not initialize a nested repo inside an existing parent checkout.
- For a new app scaffold, also create one project-local `script/build_and_run.sh` as the build/run entrypoint. Use the exact bootstrap contract from `build-run-debug` and its `references/build-script-bootstrap.md` file rather than inventing a second variant here.
```

- [ ] **Step 2: Strip the Codex environment line in "Pre-Edit Checklist"**

Find:

```markdown
5. Keep `script/build_and_run.sh` and `.codex/environments/environment.toml` separate from app source.
```

Replace with:

```markdown
5. Keep `script/build_and_run.sh` separate from app source.
```

- [ ] **Step 3: Verify no Codex references remain in swiftui-patterns/SKILL.md**

```bash
grep -iE '(\.codex|codex app|run button|run-button-bootstrap)' packages/plugins/jp-toolkit/build-macos-apps/skills/swiftui-patterns/SKILL.md
```

Expected: no matches.

---

## Task 15: Rename and rewrite the bootstrap reference doc

**Files:**
- Rename: `packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/run-button-bootstrap.md` → `packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/build-script-bootstrap.md`
- Modify: the renamed file's intro and remove the `.codex/.toml` schema section

- [ ] **Step 1: Rename the file**

```bash
git mv packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/run-button-bootstrap.md \
       packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/build-script-bootstrap.md
```

Note: this file was created by the `rsync` in Task 11, so `git mv` operates on an unstaged new file — equivalent to `mv` + add new + remove old. Use the `mv` form if `git mv` complains about an untracked source:

```bash
mv packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/run-button-bootstrap.md \
   packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/build-script-bootstrap.md
```

- [ ] **Step 2: Replace the file header**

Find:

```markdown
# Run Button Bootstrap

This is the canonical bootstrap contract for the macOS Build plugin's local run
loop.

When a project does not already have an established macOS run entrypoint:

1. Create one project-local `script/build_and_run.sh`.
2. Make it executable.
3. Use it as the single kill + build + run entrypoint.
4. Support optional `--debug`, `--logs`, `--telemetry`, and `--verify` flags.
5. Write `.codex/environments/environment.toml` so the Codex app exposes a
   `Run` action wired to that script.
```

Replace with:

```markdown
# Build Script Bootstrap

This is the canonical bootstrap contract for the macOS Build plugin's local run
loop.

When a project does not already have an established macOS run entrypoint:

1. Create one project-local `script/build_and_run.sh`.
2. Make it executable.
3. Use it as the single kill + build + run entrypoint.
4. Support optional `--debug`, `--logs`, `--telemetry`, and `--verify` flags.
```

- [ ] **Step 3: Delete the `.codex/environments/environment.toml` section entirely**

Find (the entire section from line ~160 to end of file):

````markdown
## `.codex/environments/environment.toml`

Write the environment file at this exact path:

`.codex/environments/environment.toml`

with this action shape:

```toml
# THIS IS AUTOGENERATED. DO NOT EDIT MANUALLY
version = 1
name = "<project-name>"

[setup]
script = ""

[[actions]]
name = "Run"
icon = "run"
command = "./script/build_and_run.sh"
```

If the project already has an environment file, update the existing `Run`
action to point at `./script/build_and_run.sh` instead of adding a duplicate.
````

Replace with nothing (delete the entire section). The file should end after the "Adapt the build step for Xcode projects..." paragraph.

- [ ] **Step 4: Verify no Codex references in build-script-bootstrap.md**

```bash
grep -iE '(\.codex|codex app|run button|environment\.toml)' packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/build-script-bootstrap.md
```

Expected: no matches.

- [ ] **Step 5: Confirm the renamed file exists and the old name doesn't**

```bash
ls packages/plugins/jp-toolkit/build-macos-apps/skills/build-run-debug/references/
```

Expected: shows `build-script-bootstrap.md`, does NOT show `run-button-bootstrap.md`.

---

## Task 16: Convert command → skill: build-and-run-macos-app

**Files:**
- Create: `packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app
```

- [ ] **Step 2: Write the SKILL.md**

Create `packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app/SKILL.md` with this content:

```markdown
---
name: build-and-run-macos-app
description: Create or update a project-local `script/build_and_run.sh` build/run entrypoint for a macOS Xcode workspace, Xcode project, or SwiftPM package. Use when a project needs its build/run workflow scripted, or when the existing script needs new modes (debug, logs, telemetry, verify).
---

# Build and Run macOS App

Create or update the project-local macOS `build_and_run.sh` script, then use
that script as the default build/run entrypoint.

## Inputs to determine

- Xcode scheme name (if Xcode workspace/project)
- Path to `.xcworkspace` or `.xcodeproj` (if Xcode)
- SwiftPM executable product name (if SwiftPM)
- Mode: `run`, `debug`, `logs`, `telemetry`, or `verify` (default: `run`)
- Process/app name to stop before relaunching

## Workflow

1. Detect whether the repo uses an Xcode workspace, Xcode project, or SwiftPM package.
2. If the workspace is not inside a git repo, run `git init` at the project root.
3. Create or update `script/build_and_run.sh` so it always stops the current app, builds the macOS target, and launches the fresh result.
4. For SwiftPM, keep raw executable launch only for true CLI tools; for AppKit/SwiftUI GUI apps, create a project-local `.app` bundle and launch it with `/usr/bin/open -n`.
5. Support optional script flags for `--debug`, `--logs`, `--telemetry`, and `--verify`.
6. Follow the canonical bootstrap contract in `../build-run-debug/references/build-script-bootstrap.md` for the exact script shape.
7. Run the script in the requested mode and summarize any build, script, or launch failure.

## Guardrails

- Do not initialize a nested git repo inside an existing parent checkout.
- Do not leave stale `Run` actions pointing at old script paths.
- Keep the no-flag script path simple: kill, build, run.
- Use `--debug`, `--logs`, `--telemetry`, or `--verify` only when the user asks for those modes.
```

- [ ] **Step 3: Verify**

```bash
cat packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app/SKILL.md | head -5
grep -iE '(\.codex|codex app|run button)' packages/plugins/jp-toolkit/build-macos-apps/skills/build-and-run-macos-app/SKILL.md
```

Expected `cat`: shows the YAML frontmatter starting with `---\nname: build-and-run-macos-app`.
Expected `grep`: no matches.

---

## Task 17: Convert command → skill: fix-codesign-error

**Files:**
- Create: `packages/plugins/jp-toolkit/build-macos-apps/skills/fix-codesign-error/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p packages/plugins/jp-toolkit/build-macos-apps/skills/fix-codesign-error
```

- [ ] **Step 2: Write the SKILL.md**

Create `packages/plugins/jp-toolkit/build-macos-apps/skills/fix-codesign-error/SKILL.md` with this content:

```markdown
---
name: fix-codesign-error
description: Walk through a guided diagnosis-and-fix procedure for a specific macOS codesign or entitlement failure. Use when a concrete codesign error needs step-by-step remediation (distinct from the broader inspection workflow in `signing-entitlements`).
---

# Fix Codesign Error

Inspect a macOS signing or entitlement failure and explain the minimum fix path.

## Inputs to determine

- Path to `.app` bundle or binary
- Signing identity hint, if available
- Mode: `inspect` (diagnose only) or `repair-plan` (diagnose + recommend fix sequence). Default: `inspect`.

## Workflow

1. Inspect the app bundle, executable, signing info, and entitlements.
2. Determine whether the problem is identity, provisioning, hardened runtime, sandboxing, or trust policy.
3. Summarize the exact failure class in plain language.
4. Provide the minimal repair sequence or validation command.

## Guardrails

- Never invent entitlements; read them from the binary or source files.
- Distinguish local development signing problems from distribution or notarization failures.
- Prefer verifiable commands like `codesign -d`, `spctl`, and `plutil` over guesswork.
```

- [ ] **Step 3: Verify**

```bash
cat packages/plugins/jp-toolkit/build-macos-apps/skills/fix-codesign-error/SKILL.md | head -5
```

Expected: shows the YAML frontmatter starting with `---\nname: fix-codesign-error`.

---

## Task 18: Convert command → skill: test-macos-app

**Files:**
- Create: `packages/plugins/jp-toolkit/build-macos-apps/skills/test-macos-app/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p packages/plugins/jp-toolkit/build-macos-apps/skills/test-macos-app
```

- [ ] **Step 2: Write the SKILL.md**

Create `packages/plugins/jp-toolkit/build-macos-apps/skills/test-macos-app/SKILL.md` with this content:

```markdown
---
name: test-macos-app
description: Execute the macOS test suite for an Xcode or SwiftPM project and report results categorized by failure class. Use when the action requested is running tests (vs. triaging an already-failing test, which `test-triage` handles).
---

# Test macOS App

Run the smallest meaningful macOS test scope first and explain failures by category.

## Inputs to determine

- Xcode scheme name, if applicable
- Test target or product name, if focusing on a subset
- Test filter expression, if focusing further
- Configuration: `Debug` or `Release` (default: `Debug`)

## Workflow

1. Detect whether the repo uses `xcodebuild test` or `swift test`.
2. Prefer focused test execution when a target or filter is provided.
3. Classify failures as compile, assertion, crash, env/setup, or flake.
4. Summarize the top blocker and the narrowest sensible next step.

## Guardrails

- Avoid rerunning the full suite if a focused rerun is possible.
- Distinguish build failures from actual failing tests.
- Note when host app setup or simulator-only test assumptions leak into a macOS run.
```

- [ ] **Step 3: Verify**

```bash
cat packages/plugins/jp-toolkit/build-macos-apps/skills/test-macos-app/SKILL.md | head -5
```

Expected: shows the YAML frontmatter starting with `---\nname: test-macos-app`.

---

## Task 19: Delete the legacy build-macos-apps source

**Files:**
- Delete: `packages/plugins/build-macos-apps/` (entire directory)

- [ ] **Step 1: Verify the new tree has everything**

```bash
ls packages/plugins/jp-toolkit/build-macos-apps/
ls packages/plugins/jp-toolkit/build-macos-apps/skills/ | wc -l
```

Expected `ls` (plugin dir): `.claude-plugin`, `LICENSE`, `README.md`, `skills`.
Expected count: `14` (11 original skills + 3 converted from commands).

- [ ] **Step 2: Cross-check no `.codex`, `agents/openai.yaml`, or `assets/` content survived**

```bash
find packages/plugins/jp-toolkit/build-macos-apps -type d -name agents -o -name assets -o -name '.codex-plugin'
grep -riE '(\.codex/environments|codex app|run button|run-button-bootstrap)' packages/plugins/jp-toolkit/build-macos-apps/ | grep -v LICENSE
```

Expected `find`: no output.
Expected `grep`: no output (or only matches in `LICENSE` if any false positive; the `grep -v LICENSE` filter handles that).

- [ ] **Step 3: Delete the legacy source**

```bash
git rm -r packages/plugins/build-macos-apps
```

Note: this uses `git rm -r` because the source was tracked in git. If for some reason the legacy tree is untracked (unlikely, since you copied it in via a commit earlier), use `rm -rf` instead — but verify with `git status` first.

- [ ] **Step 4: Verify legacy path is gone**

```bash
ls packages/plugins/build-macos-apps 2>&1
```

Expected: `ls: packages/plugins/build-macos-apps: No such file or directory`.

---

## Task 20: Create jp-toolkit marketplace.json

**Files:**
- Create: `marketplaces/jp-toolkit/.claude-plugin/marketplace.json`

- [ ] **Step 1: Write the marketplace manifest**

Create `marketplaces/jp-toolkit/.claude-plugin/marketplace.json` with this exact content:

```json
{
  "name": "jp-toolkit",
  "owner": { "name": "JP" },
  "plugins": [
    { "name": "build-macos-apps", "source": "../../../packages/plugins/jp-toolkit/build-macos-apps" }
  ]
}
```

- [ ] **Step 2: Remove the placeholder .gitkeep**

```bash
git rm marketplaces/jp-toolkit/.claude-plugin/.gitkeep
```

- [ ] **Step 3: Verify content**

```bash
cat marketplaces/jp-toolkit/.claude-plugin/marketplace.json
```

Expected: the JSON content above.

- [ ] **Step 4: Commit build-macos-apps migration + jp-toolkit marketplace**

```bash
git add packages/plugins/jp-toolkit/ marketplaces/jp-toolkit/ packages/plugins/build-macos-apps
git commit -m "feat(jp-toolkit): migrate build-macos-apps to Claude-native, register in jp-toolkit"
```

---

## Task 21: Final pre-merge verification

- [ ] **Step 1: Run uv sync to confirm workspace is consistent**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev && uv sync
```

Expected: succeeds.

- [ ] **Step 2: Verify all expected file paths exist**

```bash
ls marketplaces/turbo-mode/.claude-plugin/marketplace.json
ls marketplaces/jp-toolkit/.claude-plugin/marketplace.json
ls packages/plugins/turbo-mode/handoff packages/plugins/turbo-mode/context-metrics packages/plugins/turbo-mode/ticket packages/plugins/turbo-mode/superspec
ls packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json
ls packages/plugins/jp-toolkit/build-macos-apps/skills | wc -l
ls docs/archived/2026-codex-collaboration-extracted/MIGRATED.md
```

Expected: every path resolves; skill count is `14`.

- [ ] **Step 3: Verify nothing references the old `packages/plugins/{handoff,context-metrics,ticket,superspec,codex-collaboration,build-macos-apps}` paths**

```bash
rg -l '"packages/plugins/(handoff|context-metrics|ticket|superspec|codex-collaboration|build-macos-apps)' --hidden -g '!docs/archived/**' -g '!docs/handoffs/**' -g '!docs/tickets/closed-tickets/**' -g '!docs/superpowers/specs/**' -g '!docs/superpowers/plans/**' -g '!docs/reviews/**' -g '!docs/benchmarks/**'
```

Expected: no matches outside known historical-document directories. Historical references are intentionally preserved as 404s per the design.

- [ ] **Step 4: Verify no Codex references anywhere in the migrated plugin**

```bash
grep -riE '(\.codex/environments|codex app|run button|run-button-bootstrap|\.codex-plugin)' packages/plugins/jp-toolkit/build-macos-apps/ | grep -v LICENSE
```

Expected: no output.

- [ ] **Step 5: Verify lean manifest**

```bash
cat packages/plugins/jp-toolkit/build-macos-apps/.claude-plugin/plugin.json
```

Expected: 6 top-level fields (name, version, description, author, license, keywords). No `interface`, `homepage`, `repository`, or OpenAI URLs.

- [ ] **Step 6: Verify LICENSE has the OpenAI MIT notice**

```bash
grep -i 'Copyright (c) OpenAI' packages/plugins/jp-toolkit/build-macos-apps/LICENSE
```

Expected: matches.

- [ ] **Step 7: Inspect the commit history on the branch**

```bash
git log --oneline main..HEAD
```

Expected: a series of granular commits covering the moves, doc updates, and migration. Each commit message should describe one logical change.

---

## Task 22: Merge to main and re-register marketplaces

This task involves manual steps in Claude Code's interactive `/plugin marketplace` commands. It cannot be automated by a worker — the user runs these in a Claude Code session.

- [ ] **Step 1: Merge the branch to main**

```bash
git checkout main
git merge chore/jp-toolkit-marketplace-and-build-macos-apps
```

Expected: fast-forward merge succeeds.

- [ ] **Step 2: Delete the working branch**

```bash
git branch -d chore/jp-toolkit-marketplace-and-build-macos-apps
```

- [ ] **Step 3: Re-register the turbo-mode marketplace at its new path (manual, in Claude Code)**

In a Claude Code session, run:

```
/plugin marketplace remove turbo-mode
/plugin marketplace add /Users/jp/Projects/active/claude-code-tool-dev/marketplaces/turbo-mode
```

Expected: turbo-mode marketplace removed then re-added; `/plugin list` shows the same 4 turbo-mode plugins as before.

- [ ] **Step 4: Add the jp-toolkit marketplace (manual, in Claude Code)**

```
/plugin marketplace add /Users/jp/Projects/active/claude-code-tool-dev/marketplaces/jp-toolkit
```

Expected: jp-toolkit marketplace registered; `/plugin list` shows `build-macos-apps` under jp-toolkit.

- [ ] **Step 5: Install build-macos-apps (manual, in Claude Code)**

```
/plugin install build-macos-apps@jp-toolkit
```

Expected: installation succeeds; the plugin's 14 skills become available.

---

## Task 23: Post-install smoke tests

- [ ] **Step 1: Verify turbo-mode plugins still load**

In a Claude Code session, run `/plugin list` and confirm all 4 turbo-mode plugins (`handoff`, `context-metrics`, `ticket`, `superspec`) appear and are enabled.

- [ ] **Step 2: Invoke at least one skill per turbo-mode plugin**

Trigger each plugin's primary skill to confirm load:
- `handoff:save` — by asking Claude to checkpoint state
- `ticket:ticket-triage` — by asking Claude to review tickets
- (`context-metrics` and `superspec` are passive in the session — verify via `/plugin list` only)

Expected: each invocation loads the skill content without error.

- [ ] **Step 3: Verify build-macos-apps skills load**

In a Claude Code session, ask Claude: "Use the swiftui-patterns skill to outline a macOS settings scene." Confirm Claude loads the skill content and no error references a missing file.

- [ ] **Step 4: Verify the renamed reference doc resolves**

In a Claude Code session, ask Claude: "Use build-run-debug to set up a build_and_run.sh script for a SwiftPM macOS GUI app." Confirm Claude references `references/build-script-bootstrap.md` (not the old `run-button-bootstrap.md`) and that the loaded content has no `.codex/environments/environment.toml` references.

- [ ] **Step 5: Verify the 3 converted skills trigger correctly**

Test each converted skill's `description:` trigger:
- Prompt: "I need to set up a build_and_run script for this Xcode project." → expect `build-and-run-macos-app` to load
- Prompt: "This macOS app is failing to codesign with error X." → expect `fix-codesign-error` to load
- Prompt: "Run the macOS test suite and tell me what's failing." → expect `test-macos-app` to load

If Claude reaches for the topically-adjacent existing skill instead (e.g., `build-run-debug` instead of `build-and-run-macos-app`), tune the converted skill's `description:` to be more specific and re-test.

- [ ] **Step 6: Verify tombstone is reachable at archive path**

```bash
cat docs/archived/2026-codex-collaboration-extracted/MIGRATED.md | head -5
```

Expected: shows the MIGRATED.md content.

---

## Out of scope (deferred)

The following are deliberately NOT addressed in this plan and may be candidates for follow-up cleanup PRs:

- **Unrelated stale drift in `.codex/AGENTS.md`** — the file lists `cross-model` and `context-injection` as plugins, both retired weeks ago. User explicitly chose narrow scope for this PR; address separately.
- **Historical references to old `packages/plugins/<plugin>/` paths** in closed tickets, archived specs, plans, benchmark transcripts, and reviews (40+ files). These are intentionally frozen-in-time records and become 404s in the new layout by design.
- **Claude Code subagents in the migrated plugin** — the upstream `agents/openai.yaml` files were Codex surface-presentation manifests, not subagents. Adding real subagents would be scope creep under the narrowly-scoped rule.
- **Translating `.codex/environments/environment.toml` to a `.claude/environments/...` equivalent** — Claude Code has no such file. The contract is removed, not translated.
- **Deduplicating topically-overlapping skills** (`build-and-run-macos-app` ↔ `build-run-debug`; `fix-codesign-error` ↔ `signing-entitlements`; `test-macos-app` ↔ `test-triage`) — left as separate skills. If overlap causes Claude's skill-selection to misfire in practice, consider merging in a follow-up.
