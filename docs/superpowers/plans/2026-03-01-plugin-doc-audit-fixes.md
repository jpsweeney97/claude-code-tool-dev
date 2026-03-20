# Plugin Documentation Audit Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all discrepancies found by the 5-agent plugin documentation audit — one critical (broken skill), one significant (stale version), two minor (wrong line count, undocumented hook).

**Architecture:** Single feature branch. Merge the `feature/analytics-stats` branch to resolve the broken `/consultation-stats` skill (its `compute_stats.py` dependency lives there), then fix docs. The `origin/feature/p0-system-polish` branch (8 merge conflicts) is OUT OF SCOPE — it needs separate conflict resolution work.

**Tech Stack:** Git, markdown edits. No new code written — this plan merges existing code and fixes documentation.

---

## Context

An audit compared README.md, CHANGELOG.md, and plugin.json for three plugins (handoff, cross-model, context-metrics) against their actual contents, git history, and handoff archives.

**Findings to address:**

| ID | Priority | Plugin | Issue |
|----|----------|--------|-------|
| P0 | Critical | cross-model | `/consultation-stats` skill references `compute_stats.py` which doesn't exist on `main` — it's on unmerged `feature/analytics-stats` branch |
| P1 | Significant | cross-model | plugin.json is v1.0.0 but Unreleased CHANGELOG section has massive feature additions that ARE present in the plugin |
| P2 | Minor | handoff | README context reduction table says `/save` loads ~570 lines; actual is 750 (231 SKILL.md + 519 synthesis-guide.md) |
| P3 | Minor | handoff | PostToolUse quality_check.py hook exists in hooks.json but is not documented in README Hooks section |

**Out of scope:**
- `origin/feature/p0-system-polish` merge (8 conflicts, separate effort)
- context-metrics plugin (zero discrepancies found)
- Handoff CHANGELOG Unreleased version bump (fixes are accurate, version decision is separate)

---

### Task 1: Create feature branch

**Files:** None

**Step 1: Create branch from main**

```bash
git checkout main
git checkout -b fix/plugin-doc-audit-fixes
```

**Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `fix/plugin-doc-audit-fixes`

---

### Task 2: Merge feature/analytics-stats (resolves P0)

This branch adds `compute_stats.py` (517 lines), `stats_common.py` (251 lines), and tests (1154 lines) that the `/consultation-stats` skill depends on. The merge is clean — all additions, no conflicts.

**Files:**
- Added by merge: `packages/plugins/cross-model/scripts/compute_stats.py`
- Added by merge: `packages/plugins/cross-model/scripts/stats_common.py`
- Added by merge: `tests/test_compute_stats.py`
- Added by merge: `tests/test_stats_common.py`

**Step 1: Merge the branch**

```bash
git merge feature/analytics-stats --no-edit
```

Expected: Clean merge, no conflicts. 4 files changed, 1922 insertions.

**Step 2: Verify the critical file exists**

```bash
ls -la packages/plugins/cross-model/scripts/compute_stats.py
```

Expected: File exists, ~517 lines.

**Step 3: Run the merged tests**

```bash
cd packages/plugins/cross-model && uv run pytest ../../tests/test_compute_stats.py ../../tests/test_stats_common.py -v --tb=short 2>&1 | tail -20
```

Expected: All tests pass (48 tests in test_compute_stats, additional in test_stats_common).

**Step 4: Commit is already created by the merge — verify**

```bash
git log --oneline -1
```

Expected: Merge commit message referencing `feature/analytics-stats`.

---

### Task 3: Update cross-model CHANGELOG (resolves P1, partially)

Move the Unreleased section to a new version and add entries for the merged `feature/analytics-stats` content.

**Files:**
- Modify: `packages/plugins/cross-model/CHANGELOG.md`

**Step 1: Read the current CHANGELOG**

```bash
# Already read during audit — verify it hasn't changed
head -45 packages/plugins/cross-model/CHANGELOG.md
```

**Step 2: Edit CHANGELOG.md**

Changes:
1. Replace `## [Unreleased]` with `## [Unreleased]` (empty) + `## [2.0.0] — 2026-03-01`
2. Under the new Added section, add entries for the modules from the merged branch:
   - `compute_stats.py` — 4-section analytics computation (usage, dialogue quality, context quality, security)
   - `stats_common.py` — shared analytics primitives (time windowing, rate computation, formatting)
3. Under a new Fixed section entry, add: hardened analytics pipeline against malformed data

The full edit transforms:

```markdown
## [Unreleased]

### Added

- `/dialogue` skill — orchestrated multi-turn consultation...
```

Into:

```markdown
## [Unreleased]

## [2.0.0] — 2026-03-01

### Added

- `/dialogue` skill — orchestrated multi-turn consultation...
[...existing entries stay...]
- `compute_stats.py` — 4-section analytics computation (usage overview, dialogue quality, context quality, security)
- `stats_common.py` — shared analytics primitives for time windowing, rate computation, and formatting

### Changed

[...existing entries stay...]

### Fixed

[...existing entries stay...]
- Analytics pipeline hardened against malformed data and edge cases
```

**Step 3: Verify the edit**

Read the CHANGELOG and confirm:
- `[Unreleased]` section is empty
- `[2.0.0] — 2026-03-01` contains all previous Unreleased entries plus new module entries
- `[1.0.0]` and `[0.1.0]` sections are unchanged

---

### Task 4: Update cross-model plugin.json version (resolves P1)

**Files:**
- Modify: `packages/plugins/cross-model/.claude-plugin/plugin.json`

**Step 1: Read current plugin.json**

Verify current version is `1.0.0`.

**Step 2: Edit version to 2.0.0**

Change `"version": "1.0.0"` to `"version": "2.0.0"`.

**Step 3: Verify the edit**

Read `plugin.json` and confirm version is `2.0.0`.

---

### Task 5: Fix handoff README line count (resolves P2)

**Files:**
- Modify: `packages/plugins/handoff/README.md`

**Step 1: Read the context reduction table**

Lines 89-97 of `packages/plugins/handoff/README.md`.

**Step 2: Edit the /save line count**

Change:
```
| `/save` | ~570 (skill + synthesis guide) |
```

To:
```
| `/save` | ~750 (skill + synthesis guide) |
```

Rationale: SKILL.md is 231 lines, synthesis-guide.md is 519 lines, total 750.

**Step 3: Verify the edit**

Read the table and confirm the number is ~750.

---

### Task 6: Add PostToolUse hook to handoff README (resolves P3)

**Files:**
- Modify: `packages/plugins/handoff/README.md`

**Step 1: Read the Hooks section**

Lines 81-83 of `packages/plugins/handoff/README.md`:
```markdown
## Hooks

- **SessionStart**: Prunes old handoffs silently (no prompts, no auto-inject)
```

**Step 2: Add the PostToolUse hook**

Change to:
```markdown
## Hooks

- **SessionStart**: Prunes old handoffs silently (no prompts, no auto-inject)
- **PostToolUse** (Write): Quality validation on handoff file writes
```

**Step 3: Verify the edit**

Read the Hooks section and confirm both hooks are listed.

---

### Task 7: Commit documentation fixes

**Files:** All files modified in Tasks 3-6.

**Step 1: Stage changed files**

```bash
git add packages/plugins/cross-model/CHANGELOG.md
git add packages/plugins/cross-model/.claude-plugin/plugin.json
git add packages/plugins/handoff/README.md
```

**Step 2: Commit**

```bash
git commit -m "docs: fix plugin documentation audit findings

- cross-model: cut v2.0.0 release (Unreleased → versioned)
- cross-model: bump plugin.json version 1.0.0 → 2.0.0
- cross-model: add compute_stats.py/stats_common.py to CHANGELOG
- handoff: fix /save line count in context reduction table (570 → 750)
- handoff: add PostToolUse quality hook to README Hooks section

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

**Step 3: Verify**

```bash
git log --oneline -3
```

Expected: Doc fix commit + merge commit + previous main HEAD.

---

### Task 8: Final verification

**Step 1: Verify cross-model /consultation-stats works**

```bash
ls packages/plugins/cross-model/scripts/compute_stats.py && echo "PASS: script exists"
```

**Step 2: Verify cross-model version consistency**

```bash
grep '"version"' packages/plugins/cross-model/.claude-plugin/plugin.json
head -10 packages/plugins/cross-model/CHANGELOG.md
```

Expected: Both show `2.0.0`.

**Step 3: Verify handoff README accuracy**

```bash
grep "save" packages/plugins/handoff/README.md | grep -i "750"
grep "PostToolUse" packages/plugins/handoff/README.md
```

Expected: Both grep commands return matches.

**Step 4: Run full test suite for cross-model**

```bash
cd packages/plugins/cross-model && uv run pytest ../../tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All tests pass.

---

## Summary of Changes

| File | Change | Finding |
|------|--------|---------|
| `packages/plugins/cross-model/scripts/compute_stats.py` | Added (via merge) | P0 |
| `packages/plugins/cross-model/scripts/stats_common.py` | Added (via merge) | P0 |
| `tests/test_compute_stats.py` | Added (via merge) | P0 |
| `tests/test_stats_common.py` | Added (via merge) | P0 |
| `packages/plugins/cross-model/CHANGELOG.md` | Version cut + entries | P1 |
| `packages/plugins/cross-model/.claude-plugin/plugin.json` | Version bump | P1 |
| `packages/plugins/handoff/README.md` | Line count + hook entry | P2, P3 |

## Deferred Work

- **`origin/feature/p0-system-polish` merge** — 8 merge conflicts across 9 files (codex-dialogue.md, consultation-contract.md, emit_analytics.py, codex/SKILL.md, dialogue/SKILL.md, validate script, 3 test files). Needs dedicated conflict resolution session. When merged, CHANGELOG needs entries for: `read_events.py` typed event reader, `parse_truncated` event field, §17 learning retrieval, mode propagation fix, replay-based conformance tests.
- **Handoff CHANGELOG Unreleased version bump** — Unreleased section has fixes (ticket subdirs, triage bug, defer error handling). Accurate but unversioned. Separate release decision.
