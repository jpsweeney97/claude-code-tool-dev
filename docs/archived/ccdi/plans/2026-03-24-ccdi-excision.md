# CCDI Excision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surgically remove all CCDI (Claude Code Documentation Intelligence) code, tests, hooks, agents, data files, and embedded skill sections from the cross-model plugin. Archive documentation to `docs/archived/ccdi/`.

**Architecture:** Single-pass removal in dependency order across 8 commits. Each commit removes one layer — skill sections first (highest risk), then standalone components, then tests, then library code, then data, then docs. Full test suite runs after each commit for bisectability.

**Tech Stack:** Markdown (skill/agent files), Python (library, tests, hooks), JSON (data files)

**Context:** CCDI was designed to inject Claude Code documentation into Codex dialogues. Empirical testing (2026-03-24) confirmed Codex has native access to `mcp__claude_code_docs__search_docs` and reliably searches it without prompting in both `/codex` and `/dialogue` modes. CCDI's content delivery role is fully obviated.

---

## Pre-flight Checks

Before starting, verify the baseline is green:

- [ ] **Step 1: Run the full cross-model test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All tests pass (including the 616 CCDI tests — this is the baseline).

- [ ] **Step 2: Record baseline test count**

Run: `cd packages/plugins/cross-model && uv run pytest --co -q 2>/dev/null | tail -1`
Expected: Note the total count (should be ~991+ tests). After excision, this drops by 616.

---

## Task 1: Edit skill sections (remove CCDI entry points)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md`
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md`
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md`
- Modify: `packages/plugins/cross-model/references/dialogue-synthesis-format.md`

This is the highest-risk task — semantic edits in large instruction documents. Each edit must preserve surrounding context.

### 1a: Edit dialogue SKILL.md

- [ ] **Step 1: Read the file and identify all CCDI sections**

The following sections contain CCDI content that must be removed or simplified:

| Lines | Section | Action |
|-------|---------|--------|
| 161 | Step 2 intro sentence | Remove "plus (conditionally) the CCDI gatherer" clause |
| 163-176 | CCDI Pre-Dispatch Gate subsection | Remove entire subsection |
| 200-210 | Gatherer C block + launch instruction | Remove entirely |
| 212 | Timeout handling | Remove CCDI-specific clause ("For Gatherer C...") |
| 321-322 | Briefing template `### Claude Code Extension Reference` | Remove subsection line |
| 363-398 | Step 4c: CCDI Sentinel Extraction + Initial Commit | Remove entire step |
| 416-418 | Delegation envelope: ccdi_seed, ccdi_inventory_snapshot, ccdi_debug | Remove these 3 lines from the code block |
| 425-434 | CCDI delegation envelope fields table + atomic pair invariant | Remove entirely |

- [ ] **Step 2: Edit line 161 — simplify Step 2 intro**

Replace:
```
Launch agents **in parallel** via the Task tool with a 120-second timeout each. This includes the existing code/falsifier gatherers plus (conditionally) the CCDI gatherer.
```
With:
```
Launch agents **in parallel** via the Task tool with a 120-second timeout each.
```

- [ ] **Step 3: Remove lines 163-176 — CCDI Pre-Dispatch Gate**

Remove the entire `#### CCDI Pre-Dispatch Gate` subsection (from `#### CCDI Pre-Dispatch Gate` through `If threshold met, include **Gatherer C (ccdi-gatherer)** in the parallel launch below.`).

- [ ] **Step 4: Remove lines 200-210 — Gatherer C block**

Remove from `**Gatherer C (ccdi-gatherer) — only if CCDI threshold met:**` through `Launch Gatherer C in parallel with A and B. If threshold was not met, omit Gatherer C.`

- [ ] **Step 5: Simplify line 212 — timeout handling**

Replace:
```
**Timeout handling:** If a gatherer times out (120s), treat as 0 parseable lines. Proceed to the low-output retry in Step 3. For Gatherer C (ccdi-gatherer), timeout means no CCDI content — proceed without `ccdi_seed`.
```
With:
```
**Timeout handling:** If a gatherer times out (120s), treat as 0 parseable lines. Proceed to the low-output retry in Step 3.
```

- [ ] **Step 6: Remove lines 321-322 — briefing template CCDI subsection**

Remove these two lines from the briefing template:
```
### Claude Code Extension Reference
{ccdi-gatherer rendered markdown output, if non-empty — omit subsection if empty}
```

- [ ] **Step 7: Remove lines 363-398 — entire Step 4c**

Remove from `### Step 4c: CCDI Sentinel Extraction + Initial Commit` through `**If no sentinel extracted:** No \`ccdi_seed\` in delegation envelope — mid-dialogue CCDI disabled.`

- [ ] **Step 8: Remove CCDI lines from Step 5 delegation envelope**

Remove these 3 lines from the Task code block:
```
    ccdi_seed: {path to seed temp file, if sentinel extracted — omit if absent}
    ccdi_inventory_snapshot: {inventory_snapshot_path from sentinel, if seed present — omit if absent}
    ccdi_debug: {true if debug mode, omit otherwise}
```

Remove the entire CCDI delegation envelope fields section:
```
**CCDI delegation envelope fields:**

| Field | When present | Value |
|-------|-------------|-------|
| `ccdi_seed` | Sentinel extracted AND initial commit completed | File path to the registry temp file |
| `ccdi_inventory_snapshot` | Same as `ccdi_seed` — atomic pair | File path to pinned inventory snapshot |
| `ccdi_debug` | Testing/debug mode | `true` — controls trace emission in Phase B |

**Atomic pair invariant:** `ccdi_seed` and `ccdi_inventory_snapshot` MUST both be present or both absent. If one is missing (e.g., inventory_snapshot_path absent from sentinel), log warning and omit BOTH.
```

- [ ] **Step 9: Verify the file is well-formed**

Read the edited file. Check that:
- Step numbering is still sequential (Step 4b flows to Step 5 — no gap from removing 4c)
- The briefing template in Step 3h still has `## Material` followed by `{CLAIM items}`
- The delegation code block in Step 5 is still valid
- No orphaned references to `ccdi_seed`, `ccdi_gatherer`, or `topic_inventory` remain

Run: `grep -n "ccdi\|topic_inventory" packages/plugins/cross-model/skills/dialogue/SKILL.md`
Expected: 0 matches

### 1b: Edit codex SKILL.md

- [ ] **Step 10: Remove lines 109-161 — entire Step 1b: CCDI-Lite**

Remove from `## Step 1b: CCDI-Lite (Extension Documentation Injection)` through `If \`build-packet\` stdout is empty (no results met quality threshold), proceed without CCDI content. Do not log or report the absence.`

Ensure `## Step 2: Choose Invocation Strategy` follows directly after Step 1's closing content.

- [ ] **Step 11: Verify no orphaned CCDI references**

Run: `grep -n "ccdi\|CCDI\|topic_inventory" packages/plugins/cross-model/skills/codex/SKILL.md`
Expected: 0 matches

### 1c: Edit codex-dialogue.md agent

- [ ] **Step 12: Remove ccdi_mode from state table (line 138)**

Remove the row:
```
| `ccdi_mode` | `"unavailable"` | CCDI mode — see [ccdi-dialogue-protocol.md](../references/ccdi-dialogue-protocol.md) for additional CCDI state variables and full protocol. |
```

- [ ] **Step 13: Remove CCDI mid-dialogue protocol section (lines 149-153)**

Remove from `### CCDI mid-dialogue protocol (conditional)` through the paragraph ending `...emit minimal CCDI diagnostics in the pipeline data epilogue: \`"ccdi": {"status": "unavailable", "phase": "initial_only"}\`.`

- [ ] **Step 14: Remove Step 6.5: CCDI PREPARE (lines 454-456)**

Remove:
```
#### Step 6.5: CCDI PREPARE (conditional)

IF `ccdi_mode` is not `"unavailable"`: execute Step 6.5 per [ccdi-dialogue-protocol.md](../references/ccdi-dialogue-protocol.md). OTHERWISE: skip.
```

- [ ] **Step 15: Simplify Step 7 (line 460)**

Remove the CCDI prepend condition:
```
IF `ccdi_mode` is `"active"` AND a CCDI packet was staged in Step 6.5: prepend the packet to the follow-up text before sending (see [ccdi-dialogue-protocol.md](../references/ccdi-dialogue-protocol.md) Step 7 integration).
```

Leave the remaining Step 7 content (Send via codex-reply, increment turn, etc.) intact.

- [ ] **Step 16: Remove Step 7.5: CCDI COMMIT (lines 466-468)**

Remove:
```
#### Step 7.5: CCDI COMMIT (conditional)

IF `ccdi_mode` is not `"unavailable"`: execute Step 7.5 per [ccdi-dialogue-protocol.md](../references/ccdi-dialogue-protocol.md). OTHERWISE: skip.
```

- [ ] **Step 17: Simplify Phase 3 CCDI emission (line 520)**

Replace:
```
IF `ccdi_mode` is not `"unavailable"`: also emit CCDI trace and diagnostics per [ccdi-dialogue-protocol.md](../references/ccdi-dialogue-protocol.md). OTHERWISE: emit `"ccdi": {"status": "unavailable", "phase": "initial_only"}` in the pipeline data epilogue.
```
With:
```
Emit `"ccdi": {"status": "removed"}` in the pipeline data epilogue.
```

Note: We keep a minimal `ccdi` field in the epilogue for backwards compatibility with the analytics emitter. The value changes from `"unavailable"` to `"removed"` to signal the excision.

- [ ] **Step 18: Verify no orphaned CCDI references**

Run: `grep -n "ccdi\|CCDI\|topic_inventory" packages/plugins/cross-model/agents/codex-dialogue.md`
Expected: Only the `"ccdi": {"status": "removed"}` line remains.

### 1d: Edit dialogue-synthesis-format.md

- [ ] **Step 19: Remove CCDI fields from pipeline data schema**

Remove these rows from the pipeline data table (lines 155-156):
```
| `ccdi` | object | CCDI diagnostics. Schema varies by `ccdi.status` — see [ccdi-dialogue-protocol.md](ccdi-dialogue-protocol.md) or emit `{"status": "unavailable", "phase": "initial_only"}` when CCDI is unavailable. |
| `ccdi_trace` | list or null | Per-turn CCDI trace entries. Present only when `ccdi_debug` is `true`. `null` otherwise. |
```

Remove from the example JSON (lines 172-173):
```
  "ccdi": {"status": "unavailable", "phase": "initial_only"},
  "ccdi_trace": null
```

### 1e: Commit and verify

- [ ] **Step 20: Run full test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: ALL tests pass (including CCDI tests — they haven't been removed yet, and the library code they test is still present).

- [ ] **Step 21: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md \
       packages/plugins/cross-model/skills/codex/SKILL.md \
       packages/plugins/cross-model/agents/codex-dialogue.md \
       packages/plugins/cross-model/references/dialogue-synthesis-format.md
git commit -m "refactor(cross-model): remove CCDI entry points from skills and agents

Remove all CCDI sections from /dialogue SKILL.md (pre-dispatch gate,
Gatherer C, Step 4c sentinel extraction, delegation envelope fields),
/codex SKILL.md (Step 1b CCDI-Lite), codex-dialogue agent (mid-dialogue
protocol, Steps 6.5/7.5, Phase 3 trace emission), and dialogue-synthesis
format reference.

CCDI content delivery is obviated by Codex's native access to
mcp__claude_code_docs__search_docs (verified 2026-03-24)."
```

---

## Task 2: Remove standalone agent and reference

**Files:**
- Delete: `packages/plugins/cross-model/agents/ccdi-gatherer.md`
- Delete: `packages/plugins/cross-model/references/ccdi-dialogue-protocol.md`

- [ ] **Step 1: Verify no remaining references to these files**

Run: `grep -rn "ccdi-gatherer\|ccdi-dialogue-protocol" packages/plugins/cross-model/ --include="*.md" --include="*.py" --include="*.json"`
Expected: 0 matches (all references were removed in Task 1).

- [ ] **Step 2: Delete files**

```bash
trash packages/plugins/cross-model/agents/ccdi-gatherer.md
trash packages/plugins/cross-model/references/ccdi-dialogue-protocol.md
```

- [ ] **Step 3: Run test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add -A packages/plugins/cross-model/agents/ccdi-gatherer.md \
           packages/plugins/cross-model/references/ccdi-dialogue-protocol.md
git commit -m "refactor(cross-model): remove ccdi-gatherer agent and dialogue protocol reference"
```

---

## Task 3: Remove hook

**Files:**
- Delete: `packages/plugins/cross-model/hooks/ccdi_inventory_refresh.py`

- [ ] **Step 1: Verify the hook is not registered in hooks.json**

Run: `grep "ccdi\|inventory_refresh" packages/plugins/cross-model/hooks/hooks.json`
Expected: 0 matches (already verified — hook was never wired up).

- [ ] **Step 2: Delete file**

```bash
trash packages/plugins/cross-model/hooks/ccdi_inventory_refresh.py
```

- [ ] **Step 3: Run non-CCDI tests only**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q --ignore=tests/test_ccdi_hooks.py`
Expected: All non-CCDI tests pass. `test_ccdi_hooks.py` would fail (imports the deleted hook) — we exclude it here and remove it in Task 5.

- [ ] **Step 4: Commit**

```bash
git add -A packages/plugins/cross-model/hooks/ccdi_inventory_refresh.py
git commit -m "refactor(cross-model): remove ccdi_inventory_refresh hook

Hook was never registered in hooks.json — dormant code with tests but
no live wiring."
```

---

## Task 4: Remove all CCDI tests and fixtures

**Files:**
- Delete: `packages/plugins/cross-model/tests/test_ccdi_agent_sequence.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_cache.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_classifier.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_cli.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_config.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_contracts.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_diagnostics.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_dialogue_turn.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_hooks.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_integration.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_packets.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_registry.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_replay.py`
- Delete: `packages/plugins/cross-model/tests/test_ccdi_types.py`
- Delete: `packages/plugins/cross-model/tests/test_build_inventory.py`
- Delete: `packages/plugins/cross-model/tests/fixtures/ccdi/` (directory)

- [ ] **Step 1: Delete all CCDI test files and fixtures**

```bash
trash packages/plugins/cross-model/tests/test_ccdi_*.py
trash packages/plugins/cross-model/tests/test_build_inventory.py
trash packages/plugins/cross-model/tests/fixtures/ccdi
```

- [ ] **Step 2: Run remaining test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All remaining tests pass. Test count should drop by ~616.

- [ ] **Step 3: Verify test count**

Run: `cd packages/plugins/cross-model && uv run pytest --co -q 2>/dev/null | tail -1`
Expected: ~375 tests (991 - 616). The remaining tests cover context-injection, codex integration, analytics, and other non-CCDI functionality.

- [ ] **Step 4: Commit**

```bash
git add -A packages/plugins/cross-model/tests/test_ccdi_*.py \
           packages/plugins/cross-model/tests/test_build_inventory.py \
           packages/plugins/cross-model/tests/fixtures/ccdi
git commit -m "refactor(cross-model): remove 616 CCDI tests and fixtures

Remove 15 test files (~15,312 lines) and fixtures directory (~55 files).
Remaining ~375 tests cover context-injection, codex integration,
analytics, and other non-CCDI functionality."
```

---

## Task 5: Remove CCDI library and CLI

**Files:**
- Delete: `packages/plugins/cross-model/scripts/ccdi/` (entire directory)
- Delete: `packages/plugins/cross-model/scripts/topic_inventory.py`

- [ ] **Step 1: Verify no non-CCDI code imports from these modules**

Run: `grep -rn "from.*scripts\.ccdi\|import.*scripts\.ccdi\|from.*topic_inventory\|import.*topic_inventory" packages/plugins/cross-model/ --include="*.py" | grep -v "test_ccdi\|test_build_inventory\|scripts/ccdi/\|scripts/topic_inventory"`
Expected: 0 matches (already verified — no non-CCDI production code imports from CCDI).

- [ ] **Step 2: Delete library and CLI**

```bash
trash packages/plugins/cross-model/scripts/ccdi
trash packages/plugins/cross-model/scripts/topic_inventory.py
```

- [ ] **Step 3: Run remaining test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All remaining tests pass (no test imports from deleted modules).

- [ ] **Step 4: Commit**

```bash
git add -A packages/plugins/cross-model/scripts/ccdi \
           packages/plugins/cross-model/scripts/topic_inventory.py
git commit -m "refactor(cross-model): remove CCDI library and CLI entry point

Remove scripts/ccdi/ (12 Python files, ~5,435 lines: classifier,
registry, packets, cache, dialogue_turn, config, types, etc.) and
scripts/topic_inventory.py CLI (~300 lines)."
```

---

## Task 6: Remove data files

**Files:**
- Delete: `packages/plugins/cross-model/data/ccdi_config.json`
- Delete: `packages/plugins/cross-model/data/topic_overlay.json`

- [ ] **Step 1: Check if any remaining files reference these data files**

Run: `grep -rn "ccdi_config\|topic_overlay" packages/plugins/cross-model/ --include="*.py" --include="*.md" --include="*.json"`
Expected: 0 matches.

- [ ] **Step 2: Delete data files**

```bash
trash packages/plugins/cross-model/data/ccdi_config.json
trash packages/plugins/cross-model/data/topic_overlay.json
```

- [ ] **Step 3: Check if `data/` directory is now empty**

Run: `ls packages/plugins/cross-model/data/`
Expected: Directory may be empty. If so, remove it too:
```bash
trash packages/plugins/cross-model/data/ 2>/dev/null || true
```

- [ ] **Step 4: Run remaining test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All remaining tests pass.

- [ ] **Step 5: Commit**

```bash
git add -A packages/plugins/cross-model/data/
git commit -m "refactor(cross-model): remove CCDI data files (config, overlay)"
```

---

## Task 7: Archive documentation

**Files:**
- Move: `docs/superpowers/specs/ccdi/` → `docs/archived/ccdi/specs/`
- Move: `docs/superpowers/specs/2026-03-20-ccdi-design.md` → `docs/archived/ccdi/`
- Move: `docs/superpowers/specs/2026-03-24-ccdi-inventory-build-design.md` → `docs/archived/ccdi/`
- Move: All `docs/superpowers/plans/*ccdi*` → `docs/archived/ccdi/plans/`
- Move: All `docs/plans/*ccdi*` → `docs/archived/ccdi/plans/`
- Create: `docs/archived/ccdi/README.md` (archive notice)

Expected file counts: ~10 files in `docs/superpowers/specs/ccdi/`, 2 standalone specs, ~10 plan files in `docs/superpowers/plans/`, ~7 plan files in `docs/plans/`. Total: ~29 files moved.

- [ ] **Step 1: Create archive directory structure**

```bash
mkdir -p docs/archived/ccdi/specs docs/archived/ccdi/plans
```

- [ ] **Step 2: Move spec files**

```bash
mv docs/superpowers/specs/ccdi/* docs/archived/ccdi/specs/
rmdir docs/superpowers/specs/ccdi
mv docs/superpowers/specs/2026-03-20-ccdi-design.md docs/archived/ccdi/
mv docs/superpowers/specs/2026-03-24-ccdi-inventory-build-design.md docs/archived/ccdi/
```

- [ ] **Step 3: Move all plan files using globs**

**Note:** The `*ccdi*` glob will also catch THIS excision plan (`2026-03-24-ccdi-excision.md`). This is intentional — after execution, the excision plan is a historical document that belongs in the archive alongside the system it removed. All code changes are complete before Task 7 runs.

```bash
mv docs/superpowers/plans/*ccdi* docs/archived/ccdi/plans/ 2>/dev/null || true
mv docs/plans/*ccdi* docs/archived/ccdi/plans/ 2>/dev/null || true
```

Verify nothing was missed:
```bash
find docs/superpowers docs/plans -name '*ccdi*' -o -name '*CCDI*' 2>/dev/null
```
Expected: 0 results (the excision plan itself was moved to the archive).

- [ ] **Step 4: Create archive README**

Create `docs/archived/ccdi/README.md`:
```markdown
# CCDI — Archived

**Status:** Removed (2026-03-24)

CCDI (Claude Code Documentation Intelligence) was a system for injecting Claude Code
documentation into Codex dialogues during cross-model collaboration.

**Why removed:** Empirical testing confirmed that Codex has native access to the
`claude-code-docs` MCP server (`mcp__claude_code_docs__search_docs`) and reliably
searches it without prompting in both `/codex` and `/dialogue` modes. CCDI's content
delivery role was fully obviated.

**Evidence:** Three independent tests (2026-03-24) — two `/codex` consultations and
one `/dialogue` consultation on Claude Code topics — confirmed Codex detects the
domain and searches docs autonomously. See the dialogue consultation thread
`019d2183-2f57-76d3-ae1f-1dd9fb532d9b` for the architectural discussion.

**What's here:**
- `specs/` — CCDI modular spec (10 files, ~1350 lines)
- `2026-03-20-ccdi-design.md` — Original design document
- `2026-03-24-ccdi-inventory-build-design.md` — Build pipeline design (never implemented)
- `plans/` — Remediation and implementation plans
```

- [ ] **Step 5: Commit**

```bash
git add docs/archived/ccdi/ docs/superpowers/specs/ docs/superpowers/plans/ docs/plans/
git commit -m "docs: archive CCDI documentation to docs/archived/ccdi/

Move specs, design docs, and remediation plans to archive.
Add README explaining removal rationale and evidence."
```

---

## Task 8: Update project references

**Files:**
- Modify: `.claude/CLAUDE.md` (remove CCDI references)
- Modify: Memory file (update current focus)

- [ ] **Step 1: Update .claude/CLAUDE.md**

Remove or update any CCDI-specific references in the Gotchas, Packages, or Systems sections. Specifically:

- In the Gotchas section, remove the bullet about "Hook failure polarity" if it only applies to CCDI (verify first — it may be general advice that should stay).
- If there's a CCDI entry in any tables, remove it.
- Check for references to `ccdi-gatherer`, `topic_inventory`, or `ccdi_config`.

Run: `grep -n "ccdi\|CCDI\|topic_inventory" .claude/CLAUDE.md`
Expected: Identify any references. Edit as needed.

- [ ] **Step 2: Update memory**

Update the memory MEMORY.md to reflect that CCDI has been excised and the `feature/ccdi-inventory-build` branch work is complete (the branch should be closed/merged with the excision, not the original build pipeline).

- [ ] **Step 3: Run final full test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -x -q`
Expected: All remaining tests pass.

- [ ] **Step 4: Verify no CCDI references remain in production code**

Run: `grep -rn "ccdi\|CCDI\|topic_inventory\|ccdi_config\|ccdi_gatherer" packages/plugins/cross-model/ --include="*.py" --include="*.md" --include="*.json" | grep -v __pycache__`
Expected: Only the `"ccdi": {"status": "removed"}` line in `codex-dialogue.md` remains.

- [ ] **Step 5: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "chore: update project references after CCDI removal"
```

---

## Post-Excision Verification

- [ ] **Step 1: Run full test suite one final time**

Run: `cd packages/plugins/cross-model && uv run pytest -v`
Expected: ~375 tests pass, 0 failures.

- [ ] **Step 2: Verify git status is clean**

Run: `git status`
Expected: Clean working tree with 8 new commits on the branch.

- [ ] **Step 3: Review the commit log**

Run: `git log --oneline -8`
Expected: 8 commits in dependency order, each with a clear description of what was removed.

---

## Summary

| Commit | What | Files Affected | Risk |
|--------|------|---------------|------|
| 1 | Edit skill sections (remove CCDI entry points) | 4 modified | **High** — semantic edits in instruction docs |
| 2 | Remove ccdi-gatherer agent + protocol reference | 2 deleted | Low — standalone files |
| 3 | Remove ccdi_inventory_refresh hook | 1 deleted | Low — never wired up |
| 4 | Remove 616 CCDI tests + fixtures | 15 tests + ~55 fixtures deleted | Low — mechanical deletion |
| 5 | Remove CCDI library + CLI | 13 deleted | Low — no remaining consumers |
| 6 | Remove data files | 2-3 deleted | Low — no remaining consumers |
| 7 | Archive documentation | ~29 moved, 1 created | Low — file moves |
| 8 | Update project references | 1-2 modified | Low — documentation |

**Net change:** ~21,000 lines removed, 616 tests removed, ~33 docs archived. Remaining ~375 cross-model tests unaffected.
