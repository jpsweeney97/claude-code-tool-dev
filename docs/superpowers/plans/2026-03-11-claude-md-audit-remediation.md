# CLAUDE.md Audit Remediation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all findings from the 2026-03-11 CLAUDE.md audit — 1 factual error, 2 stale claims, 6 missing items, and 2 quality issues across 2 files.

**Architecture:** Pure documentation edits to `.claude/CLAUDE.md` (root) and `packages/mcp-servers/claude-code-docs/CLAUDE.md`. No code changes. No tests. Verification is path/command checking.

**Tech Stack:** Git, shell commands for verification

**Source audit:** This conversation (2026-03-11 CLAUDE.md audit with 5-teammate exploration team)

---

## File Map

| File | Action | Findings Addressed |
|------|--------|-------------------|
| `.claude/CLAUDE.md` | Major rewrite of Directory Structure, Systems, Scripts sections | I1, S1, M1–M6, Q1, Q2 |
| `packages/mcp-servers/claude-code-docs/CLAUDE.md` | Single line edit (test count) | I2 |

No new files created. No tests. No code changes.

---

## Chunk 1: Root CLAUDE.md — Directory Structure

Addresses: **I1** (wrong context-injection path), **M1** (missing plugins), **M3** (incomplete docs/), **M4** (incomplete .claude/), **M6** (missing .claude-plugin/), **Q2** (packages/ children not shown)

### Task 1: Fix Directory Structure tree

**Files:**
- Modify: `.claude/CLAUDE.md:13-35`

The current directory tree (lines 15-35) has these problems:
1. `context-injection/` shown as direct child of `packages/` — wrong (it's at `packages/plugins/cross-model/context-injection/`)
2. `packages/plugins/` doesn't show its children (`cross-model/`, `handoff/`, `ticket/`, `context-metrics/`)
3. `.claude/` missing `handoffs/`, `sessions/`, `worktrees/`
4. `docs/` missing major subdirectories (`decisions/`, `learnings/`, `adrs/`)
5. No mention of `.claude-plugin/`

- [ ] **Step 1: Replace the directory tree block**

Replace lines 13-35 (from `## Directory Structure` through the closing ` ``` `) with:

~~~markdown
## Directory Structure

```
.claude/
├── skills/       # Skills (SKILL.md required)
├── hooks/        # Hooks (Python scripts, synced to settings.json)
├── commands/     # Slash commands
├── agents/       # Subagents
├── rules/        # Auto-loaded session rules (keep minimal)
├── handoffs/     # Session handoff documents (gitignored)
├── sessions/     # Session notes (gitignored)
└── worktrees/    # Git worktree state (gitignored)

packages/
├── plugins/
│   ├── cross-model/          # Codex MCP + context injection + dialogue agent
│   │   └── context-injection/  # Mid-conversation evidence gathering MCP server
│   ├── handoff/              # Session state persistence
│   ├── ticket/               # Repo-local ticket management
│   └── context-metrics/      # Context window usage tracking
└── mcp-servers/
    └── claude-code-docs/     # BM25-indexed doc search (TypeScript)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Cross-model consultation insights
├── tickets/      # Work tickets
└── audits/       # Quality audits

.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
```
~~~

- [ ] **Step 2: Verify all paths in the new tree exist**

Run:
```bash
# Every directory referenced in the tree must exist
for dir in \
  .claude/skills .claude/hooks .claude/commands .claude/agents .claude/rules \
  .claude/handoffs .claude/sessions .claude/worktrees \
  packages/plugins/cross-model packages/plugins/cross-model/context-injection \
  packages/plugins/handoff packages/plugins/ticket packages/plugins/context-metrics \
  packages/mcp-servers/claude-code-docs \
  scripts docs/frameworks docs/references docs/plans docs/decisions \
  docs/learnings docs/tickets docs/audits .claude-plugin; do
  [ -d "$dir" ] && echo "OK: $dir" || echo "MISSING: $dir"
done
```

Expected: All OK. If any MISSING, fix the tree before proceeding.

**Note on omitted docs/ subdirectories:** The tree intentionally excludes `adrs/`, `post-mortems/`, `spikes/`, `discussions/`, `benchmarks/`, `assessments/`, `codex-mcp/`, `prompts/`, `superpowers/` (this plan lives here), `handoffs/`, `notes/`. These are either archival, specialized, or low-traffic. Including them would bloat the tree for minimal navigational value. The 7 shown are the ones Claude regularly needs to find.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "fix(claude-md): correct directory structure tree

Fix context-injection path (was packages/context-injection/, actually
packages/plugins/cross-model/context-injection/). Add missing plugin
packages, .claude/ operational dirs, docs/ subdirectories, and
.claude-plugin/ marketplace config."
```

---

## Chunk 2: Root CLAUDE.md — Package Inventory + Systems Compression

Addresses: **M5** (no package inventory), **Q1** (verbose Systems section), **S1** (stale learning status)

### Task 2: Add package inventory table and compress Systems section

**Files:**
- Modify: `.claude/CLAUDE.md` (the `## Systems` section — line numbers will have shifted after Chunk 1; match on content `## Systems`, not line numbers)

The current "Systems" section uses 40 lines of narrative prose to describe 3 systems. For a CLAUDE.md, this should be denser. Replace it with:
1. A package inventory table (M5) — gives Claude the full monorepo map
2. A compressed systems overview — same info, half the lines

- [ ] **Step 1: Replace the Systems section**

Replace from `## Systems` through `**Status:** Design complete. Implementation not started.` with:

```markdown
## Packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| cross-model | `packages/plugins/cross-model/` | Python | Codex MCP server + enforcement hooks + dialogue agent |
| context-injection | `packages/plugins/cross-model/context-injection/` | Python | Mid-conversation evidence gathering with redaction (991 tests) |
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search (397 tests) |

Plugins deploy via `turbo-mode` marketplace. MCP servers and extensions deploy via `uv run scripts/promote`.

## Systems

Three systems form the cross-model collaboration stack:

| System | Status | Key Resources |
|--------|--------|---------------|
| **Codex Integration** — Cross-model dialogue with OpenAI Codex | Deployed | MCP tools: `mcp__plugin_cross-model_codex__codex`, `codex-reply`. Agent: `agents/codex-dialogue.md` |
| **Context Injection** — Mid-conversation evidence gathering for Codex dialogues | Complete | MCP tools: `mcp__plugin_cross-model_context-injection__process_turn`, `execute_scout`. Server: `packages/plugins/cross-model/context-injection/`. Contract: `packages/plugins/cross-model/references/context-injection-contract.md` |
| **Cross-Model Learning** — Persistent knowledge capture from Codex conversations | Phase 0 in progress | Spec: `docs/plans/2026-02-10-cross-model-learning-system.md`. Skill: `.claude/skills/learn/` |

**Context Injection security:** Over-redaction is always preferable to under-redaction. Footgun tests (`test_footgun_*`) verify which pipeline layer catches secrets.

**Codex hook delivery:** `PostToolUseFailure` `additionalContext` confirmed working (verified 2026-02-17).
```

- [ ] **Step 2: Verify all paths in the new tables exist**

Run:
```bash
for path in \
  packages/plugins/cross-model \
  packages/plugins/cross-model/context-injection \
  packages/plugins/handoff \
  packages/plugins/ticket \
  packages/plugins/context-metrics \
  packages/mcp-servers/claude-code-docs \
  .claude/skills/learn; do
  [ -e "$path" ] && echo "OK: $path" || echo "MISSING: $path"
done
# Check files too
for file in \
  docs/plans/2026-02-11-conversation-aware-context-injection.md \
  docs/plans/2026-02-10-cross-model-learning-system.md; do
  [ -f "$file" ] && echo "OK: $file" || echo "MISSING: $file"
done
```

Expected: All OK.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "refactor(claude-md): add package inventory, compress Systems

Add Packages table with all 6 packages. Compress Systems from 40 lines
of prose to a summary table. Update Cross-Model Learning status from
'not started' to 'Phase 0 in progress'."
```

---

## Chunk 3: Root CLAUDE.md — Workflow + Scripts

Addresses: **M2** (incomplete scripts inventory)

### Task 3: Expand scripts reference and clean up Workflow section

**Files:**
- Modify: `.claude/CLAUDE.md:79-121` (post-Chunk-2 line numbers will shift — use content matching, not line numbers)

The current "Workflow" section has two subsections (Promoting, Plugin Development) that will partially overlap with the new Packages table from Task 2. The "Scripts" line (line 121) lists only 4 of 12+ scripts.

- [ ] **Step 1: Replace the Workflow and Scripts sections**

Find the current Workflow section (starts with `## Workflow`) and replace through the Scripts line (`Run with...`) with:

~~~markdown
## Workflow

### Promoting Extensions

```bash
uv run scripts/promote <type> <name>   # Validate and deploy to ~/.claude/
```

Types: `skill`, `command`, `agent`, `hook`. Plugins use the marketplace instead (see Packages table).

### Scripts

Run with `uv run scripts/<name>`:

| Script | Purpose |
|--------|---------|
| `promote` | Validate and deploy extensions to `~/.claude/` |
| `sync-settings` | Sync hook config to `settings.json` (run after hook changes) |
| `inventory` | List all extensions and packages |
| `migrate` | Extension schema migrations |
| `validate_consultation_contract.py` | Validate Codex contract + governance rules |
| `validate_episode.py` | Validate learning episode format |

Additional scripts in `scripts/` for benchmarking and analysis (`benchmark_v0_resume.py`, `blinded_eval_packet.py`, `skill_impact_stats.py`, `migrate-extension-docs.py`). See directory listing for full inventory.
~~~

**Script selection rationale:** The 6 listed scripts are either referenced elsewhere in CLAUDE.md (`promote`, `sync-settings`) or run as part of standard development workflows (`inventory`, `migrate`, `validate_*`). The remaining scripts are specialized analysis/benchmarking tools used infrequently.

- [ ] **Step 2: Verify key scripts exist**

Run:
```bash
for script in promote sync-settings inventory migrate \
  validate_consultation_contract.py validate_episode.py; do
  [ -f "scripts/$script" ] && echo "OK: $script" || echo "MISSING: $script"
done
```

Expected: All OK.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs(claude-md): expand scripts inventory

List 6 key scripts in a table instead of 4 inline. Add note pointing
to scripts/ for full inventory. Simplify Promoting section since
Packages table now covers plugin deployment."
```

---

## Chunk 4: claude-code-docs CLAUDE.md — Test Count Fix

Addresses: **I2** (test count 386 → 397)

### Task 4: Update test count in claude-code-docs CLAUDE.md

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/CLAUDE.md:16`

- [ ] **Step 1: Update the test count**

Replace `386 tests` with `397 tests` on line 16:

```
npm test              # vitest run (397 tests)
```

- [ ] **Step 2: Verify**

Run:
```bash
cd packages/mcp-servers/claude-code-docs && npx vitest run --reporter=verbose 2>&1 | tail -3
```

Expected: `Tests  39x passed` (exact number may vary by ±1 from skips).

- [ ] **Step 3: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/CLAUDE.md
git commit -m "fix(claude-code-docs): update test count 386 → 397"
```

---

## Chunk 5: Final Verification

### Task 5: End-to-end verification of all CLAUDE.md files

- [ ] **Step 1: Verify root CLAUDE.md line count**

Run:
```bash
wc -l .claude/CLAUDE.md
```

Expected: 140-180 lines (should stay within the 50-200 recommended range). If over 200, identify lines to cut.

- [ ] **Step 2: Verify no broken paths in root CLAUDE.md**

Run:
```bash
# Extract all backtick-quoted paths and check they exist (uses rg, not grep -oP which is unsupported on macOS)
rg -o '`[^`]*`' .claude/CLAUDE.md | \
  rg '`(\.claude|packages|docs|scripts)' | \
  sed 's/.*`\(.*\)`/\1/' | \
  while read -r p; do
    [ -e "$p" ] && echo "OK: $p" || echo "BROKEN: $p"
  done
```

Expected: All OK or known-relative paths (like `packages/plugins/cross-model/references/context-injection-contract.md`).

- [ ] **Step 3: Verify no broken paths in claude-code-docs CLAUDE.md**

Run:
```bash
cd packages/mcp-servers/claude-code-docs
rg -o '`[^`]*\.ts`' CLAUDE.md | sed 's/.*`\(.*\)`/\1/' | \
  while read -r f; do
    [ -f "src/$f" ] && echo "OK: $f" || echo "BROKEN: $f"
  done
```

Expected: All OK.

- [ ] **Step 4: Read final CLAUDE.md and sanity check**

Read `.claude/CLAUDE.md` in full. Check:
- [ ] No internal contradictions (commands in Gotchas match Scripts table)
- [ ] No duplicate information (Packages table doesn't repeat what Directory Structure shows)
- [ ] Imperative voice throughout
- [ ] Every line earns its context window cost

---

## Pre-Execution Checklist

Before starting:
- [ ] Create branch: `git checkout -b chore/claude-md-audit-remediation`
- [ ] Verify clean working tree: `git status`

After all tasks complete:
- [ ] All 4 commits on the branch
- [ ] No broken paths in any CLAUDE.md
- [ ] Root CLAUDE.md under 200 lines
- [ ] Offer to merge or create PR
