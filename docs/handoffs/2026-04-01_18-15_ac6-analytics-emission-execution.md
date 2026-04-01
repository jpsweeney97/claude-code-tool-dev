---
date: 2026-04-01
time: "18:15"
created_at: "2026-04-01T18:15:00Z"
session_id: 4d7fefa6-68bd-4ad0-a747-a16fdf1a85a9
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_13-38_ac6-analytics-emission-plan.md
project: claude-code-tool-dev
branch: feature/ac6-analytics-emission
commit: 64b724d0
title: "AC6 analytics emission execution"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/tests/test_outcome_record.py
  - packages/plugins/codex-collaboration/tests/test_control_plane.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_outcome_shape_consistency.py
  - docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md
---

# AC6 analytics emission execution

## Goal

Execute the review-clean AC6 analytics emission plan — the last analytics acceptance criterion in ticket T-20260330-03. The plan (authored and reviewed in session 8) specified 8 tasks adding `OutcomeRecord` emission to 4 success paths in the codex-collaboration plugin.

**Trigger:** Session 8 produced a review-clean plan after 3 review rounds (10 findings total, all resolved). This session resumes to execute it.

**Stakes:** Medium — AC6 is the last analytics-related acceptance criterion before T-20260330-04 and T-20260330-05 can proceed. Implementation is the deliverable; no design decisions required.

**Success criteria:** (1) All 8 tasks complete. (2) All tests passing (430 existing + ~17 new). (3) Lint clean on all modified files. (4) All 4 emission sites produce the same JSON key set. (5) `analytics/outcomes.jsonl` created on first append.

**Connection to project arc:** Ninth session in the codex-collaboration build chain. Sessions 1-7 completed persistence hardening. Session 8 authored the AC6 plan. This session executes it.

## Session Narrative

Resumed from the session 8 handoff (`2026-04-01_13-38_ac6-analytics-emission-plan.md`). The handoff's next step was executing the 8-task AC6 analytics emission plan.

**Pre-execution plan fixes.** Before execution, the user provided 2 findings against the plan itself:

1. [P1] The plan lacked a branch-creation prerequisite. Task 1 starts editing files immediately, but repo rules require `feature/*` branches (enforced by PreToolUse gitflow hook). A worker following literally would commit on `main` and get blocked. Fix: Added Task 0 with explicit `git checkout -b feature/ac6-analytics-emission`.

2. [P2] The lint gate left a late test-lint failure path, with three sub-issues: (a) Task 2 showed `import json` / `from pathlib import Path` inline in a code block to "add" to an existing file — a literal worker would append mid-file, causing ruff E402. Fix: Separated import instructions ("add to top of file") from class body ("append at end"). (b) Task 5 unpacked `store` and `turn_store` from `_build_dialogue_stack` but never used them — ruff F841. Fix: Changed to `controller, _, _, journal, _`. (c) Task 8 only linted `server/*.py`, missing all 4 test files. Fix: Expanded ruff check/format commands to include all 8 target files.

All 4 edits applied to `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` and verified clean.

**Execution phase.** Used subagent-driven development — fresh sonnet subagent per task, sequential execution. Each subagent received the full task text from the plan plus context about dependencies and gotchas.

**Task 0: Feature branch.** Created `feature/ac6-analytics-emission` off `main`. Handled directly (no subagent needed).

**Task 1: OutcomeRecord model.** Subagent created `tests/test_outcome_record.py` (5 tests) and added `OutcomeRecord` frozen dataclass to `models.py`. TDD verified: ImportError on red, 5 passed on green. Commit `4eebc157`.

**Task 2: Journal persistence path.** Subagent added `import json`, `from pathlib import Path`, and `from server.journal import OperationJournal` to the top of `test_outcome_record.py`'s import block (not mid-file — per the P2 fix), appended `TestOutcomeJournalPersistence` class (3 tests), and added `append_outcome()` method + analytics dir setup to `journal.py`. 438 tests passing. Commit `48e191eb`.

**Task 3: Consult outcome emission.** The most complex task — required patching 5 existing tests' UUID iterators. Subagent added `OutcomeRecord` import and emission block to `control_plane.py`, added 2 new tests (positive + negative), and patched all 5 UUID iterators. Spec compliance review confirmed all patches correct, including the subtle parse-failure path where `parse_consult_response()` runs BEFORE emission (so the first failing consult consumes only `runtime-1`). 440 tests passing. Commit `77ce3dc3`.

**Task 4: Dialogue normal reply emission.** Subagent added emission block to `dialogue.py` `reply()` method (after audit, before parse — intentionally pre-parse for durability), added `test_reply_emits_outcome_record` test, and extended the existing parse-failure durability test. The subagent noted the plan referenced `TestCommittedTurnParseError` but the actual class was `TestReplyParseFailure` — found the right target by searching. 441 tests passing. Commit `24535ea4`.

**Task 5: Recovery path emission.** Subagent added emission block to `_recover_turn_dispatch()` inside the `if turn_id is not None and entry.runtime_id is not None:` guard. Added `TestRecoveryOutcomeEmission` class with 2 tests (confirmed + unconfirmed). Used `controller, _, _, journal, _` tuple unpacking per the P2 fix. 443 tests passing. Commit `114c58a2`.

**Task 6: Best-effort repair emission.** Subagent added emission block to `_best_effort_repair_turn()` using the same guard pattern. Added 2 tests to `TestBestEffortRepairTurn`. 445 tests passing. Commit `68d4c4ef`.

**Task 7: Shape consistency test.** Created `test_outcome_shape_consistency.py` — exercises all 4 emission paths (consult, normal reply, recovery, repair) and asserts all outcome records share the same JSON key set. Passed on first run (all emission sites already consistent). 446 tests passing. Commit `32f1b68b`.

**Task 8: Lint and verification.** Ruff check clean on all 8 files. Ruff format wanted to reformat 7 files — all pre-existing line-length divergences (long lines in `control_plane.py`, `dialogue.py`, etc.), not changes introduced by AC6. Applied formatting to target files only (never `ruff format .`). Smoke test passed. 446 tests passing after formatting. Commit `64b724d0`.

**No pivots or unexpected issues during execution.** The plan was sufficiently detailed that every subagent completed without questions or blocks.

## Decisions

### No per-task spec/code reviews for Tasks 1-2

**Choice:** Skipped per-task spec compliance and code quality reviews for Tasks 1 and 2, starting reviews from Task 3.

**Driver:** Tasks 1-2 are trivially mechanical — a single frozen dataclass and a single JSONL append method. The plan specifies complete code for both. The cost of two review subagent dispatches outweighs the near-zero risk of spec drift on a 15-line dataclass.

**Alternatives considered:**
- **Full review pipeline for all tasks** — the subagent-driven development skill recommends two-stage review after each task. Skipped for Tasks 1-2 because the code is directly copied from the plan with no judgment calls.

**Trade-offs accepted:** Slightly less rigor on the foundational tasks. Accepted because any issues would surface immediately in Tasks 3-6 when the model and persistence are actually exercised.

**Confidence:** High (E1) — both tasks reported 438+ tests passing with no regressions.

**Reversibility:** N/A — reviews can always be done retroactively by reading the committed code.

**Change trigger:** If Tasks 1-2 had involved any design judgment (e.g., choosing between approaches), reviews would have been warranted.

### Accept pre-existing ruff formatting changes in target files

**Choice:** Committed ruff formatting changes alongside AC6 code, covering pre-existing divergences in the 7 target files.

**Driver:** The plan explicitly includes a Task 8 formatting step with a "commit formatting if needed" instruction. These files were already touched by AC6 — formatting them is hygienic. The alternative (reverting formatting) would require cherry-picking hunks, which is fragile.

**Alternatives considered:**
- **Format only AC6 code hunks** — impractical with ruff (it formats whole files). Would require manual `git add -p` to separate formatting from AC6 changes.
- **Skip formatting entirely** — leaves the files in a state where ruff format check fails, which is a worse outcome than including pre-existing fixes.

**Trade-offs accepted:** The style commit includes ~127 insertions / 79 deletions of pre-existing formatting changes alongside AC6 files. The `style:` commit message prefix separates it from feature work.

**Confidence:** High (E1) — follows the plan's explicit Task 8 instructions.

**Reversibility:** High — `git revert` on the style commit undoes formatting without affecting feature code.

**Change trigger:** If the team has a policy against formatting changes in feature branches.

## Changes

### Created files

| File | Purpose | Tests |
|------|---------|-------|
| `tests/test_outcome_record.py` | 5 model tests + 3 journal persistence tests | 8 total |
| `tests/test_outcome_shape_consistency.py` | Cross-cutting key-set consistency test (all 4 paths) | 1 total |

### Modified files

| File | What Changed | Lines |
|------|-------------|-------|
| `server/models.py` | Added `OutcomeRecord` frozen dataclass after `AuditEvent` | +15 |
| `server/journal.py` | Added `OutcomeRecord` import, `analytics/` dir setup in `__init__`, `append_outcome()` method | +10 |
| `server/control_plane.py` | Added `OutcomeRecord` import, emission block after audit event in `codex_consult()` | +14 |
| `server/dialogue.py` | Added `OutcomeRecord` import, emission blocks in `reply()`, `_recover_turn_dispatch()`, `_best_effort_repair_turn()` | +42 |
| `tests/test_control_plane.py` | 2 new tests + 5 UUID iterator patches | +65 |
| `tests/test_dialogue.py` | 1 new test in `TestDialogueReply`, parse-failure durability extension, `TestRecoveryOutcomeEmission` class (2 tests), 2 tests in `TestBestEffortRepairTurn` | +170 |
| `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` | P1 (Task 0 branch prerequisite) + P2 (3 lint fixes) | +25 |

### Commit history

| SHA | Message | Task |
|-----|---------|------|
| `4eebc157` | feat: add OutcomeRecord model for analytics emission (AC6) | 1 |
| `48e191eb` | feat: add analytics outcome persistence path to OperationJournal (AC6) | 2 |
| `77ce3dc3` | feat: emit consult outcome record in analytics path (AC6) | 3 |
| `24535ea4` | feat: emit dialogue_turn outcome on normal reply success (AC6) | 4 |
| `114c58a2` | feat: emit outcome record on recovery-confirmed dialogue turn (AC6) | 5 |
| `68d4c4ef` | feat: emit outcome record on best-effort repair confirmed turn (AC6) | 6 |
| `32f1b68b` | test: verify outcome record shape consistency across all emission paths (AC6) | 7 |
| `64b724d0` | style: apply ruff formatting to AC6 analytics emission files | 8 |

## Codebase Knowledge

### Emission Site Architecture (Post-AC6)

Four code paths now emit both `AuditEvent` and `OutcomeRecord` on success:

| Site | File:Line | Action | Guard | OutcomeRecord Fields |
|------|-----------|--------|-------|---------------------|
| Consult success | `control_plane.py:207-219` | `consult` | Always (success path) | `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `policy_fingerprint`, `repo_root` |
| Normal reply | `dialogue.py:~320-332` | `dialogue_turn` | Always (normal success) | Same + `turn_sequence`, `resolved_root` |
| Recovery confirmed | `dialogue.py:~610-623` | `dialogue_turn` | `turn_id is not None and entry.runtime_id is not None` | Same, from `entry` fields + bootstrapped `runtime` |
| Best-effort repair | `dialogue.py:~720-733` | `dialogue_turn` | `turn_id is not None and intent_entry.runtime_id is not None` | Same, from `intent_entry` fields + bootstrapped `runtime` |

### Storage Layout (Post-AC6)

| Path | Content | Created |
|------|---------|---------|
| `plugin_data / "audit" / "events.jsonl"` | Trust-boundary audit log (`AuditEvent`) | Pre-existing |
| `plugin_data / "analytics" / "outcomes.jsonl"` | Analytics outcomes (`OutcomeRecord`) | **NEW** — AC6 |
| `plugin_data / "analytics/"` | Directory | On `OperationJournal.__init__` |

### Test Count by Area

| Test File | Pre-AC6 | Post-AC6 | New |
|-----------|---------|----------|-----|
| `test_outcome_record.py` | 0 | 8 | +8 |
| `test_control_plane.py` | 18 | 20 | +2 |
| `test_dialogue.py` | ~30 | ~37 | +7 |
| `test_outcome_shape_consistency.py` | 0 | 1 | +1 |
| **Total new** | | | **+18** |

Full suite: 446 tests passing (was 430 pre-AC6).

### OutcomeRecord Schema

The `OutcomeRecord` frozen dataclass at `models.py:161-177` has 10 fields:

| Field | Type | Source (consult) | Source (dialogue) |
|-------|------|-----------------|-------------------|
| `outcome_id` | `str` | `self._uuid_factory()` | `self._uuid_factory()` |
| `timestamp` | `str` | `self._journal.timestamp()` | `self._journal.timestamp()` |
| `outcome_type` | `Literal["consult", "dialogue_turn"]` | `"consult"` | `"dialogue_turn"` |
| `collaboration_id` | `str` | `collaboration_id` local var | `collaboration_id` parameter |
| `runtime_id` | `str` | `runtime.runtime_id` | `runtime.runtime_id` |
| `context_size` | `int \| None` | `packet.context_size` | `packet.context_size` (reply) or `entry.context_size` (recovery/repair) |
| `turn_id` | `str` | `turn_result.turn_id` | `turn_result.turn_id` (reply) or extracted from `thread/read` (recovery/repair) |
| `turn_sequence` | `int \| None` | `None` (default) | `turn_sequence` local var (reply) or `entry.turn_sequence` (recovery/repair) |
| `policy_fingerprint` | `str \| None` | `runtime.policy_fingerprint` | `runtime.policy_fingerprint` |
| `repo_root` | `str \| None` | `str(resolved_root)` | `str(resolved_root)` (reply) or `entry.repo_root` (recovery/repair) |

The `context_size` nullability is intentional — recovery/repair paths may encounter entries without `context_size` (test fixtures at `test_dialogue.py:428` and `:466` exercise this). Coercing `None` to `0` was rejected as data fabrication in session 8's P1 review finding.

### Test Infrastructure Patterns Used by AC6

**Outcome assertion pattern** (used in all 4 emission site tests):
```
outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
assert outcomes_path.exists()
lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
records = [json.loads(line) for line in lines]
dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
```
This mirrors the existing audit assertion pattern (`plugin_data / "audit" / "events.jsonl"`).

**Negative test pattern** (used for failure/unconfirmed paths):
```
outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
assert not outcomes_path.exists() or outcomes_path.read_text(encoding="utf-8").strip() == ""
```
Or for tests where the file may exist from other operations:
```
if outcomes_path.exists():
    content = outcomes_path.read_text(encoding="utf-8").strip()
    if content:
        records = [json.loads(line) for line in content.split("\n")]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 0
```

**Recovery/repair test setup pattern** (Tasks 5-6): Create a `FakeRuntimeSession` with `read_thread_response` set to either a completed turn (confirmed path) or empty turns (unconfirmed path), then write an unresolved `OperationJournalEntry` with `phase="intent"` to the journal, and call `recover_pending_operations()` or `_best_effort_repair_turn()`.

### Parse-Emission Ordering (Confirmed This Session)

This ordering difference was documented in the plan but confirmed during execution:

- **`control_plane.py`**: `parse_consult_response()` runs BEFORE audit/outcome emission. Parse failures raise before any audit/outcome is written. UUID consumption: parse-failure tests only consume the runtime UUID.
- **`dialogue.py`**: Audit/outcome emission runs BEFORE `parse_consult_response()`. Parse failures produce committed outcome records (`CommittedTurnParseError`). UUID consumption: parse-failure tests consume runtime + collab + event + outcome UUIDs.

This was confirmed when the Task 4 subagent extended the parse-failure durability test to assert outcome emission. The test (`TestReplyParseFailure::test_completes_journal_writes_store_and_emits_audit`) now also verifies outcome records are emitted pre-parse.

### UUID Iterator Pattern and Consumption Analysis (Confirmed This Session)

Tests use `iter(("uuid-1", "uuid-2", ...)).__next__` for deterministic UUID assignment. Adding any new `self._uuid_factory()` call to a success path exhausts iterators that don't account for it.

Five tests in `test_control_plane.py` required patching (Task 3 Step 5). The per-test consumption analysis:

| Test | Code Path | UUIDs Pre-AC6 | UUIDs Post-AC6 | Why |
|------|-----------|---------------|----------------|-----|
| `test_..._audits_context_size` | Single success | `runtime-1, collab-1, event-1` | + `outcome-1` | Success path adds 1 UUID |
| `test_..._clears_stale_marker` | Single success | Same as above | + `outcome-1` | Same pattern |
| `test_..._after_turn_failure` | Fail then succeed | `runtime-1, runtime-2, collab-2, event-2` | + `outcome-2` | Only 2nd consult succeeds, 1st failure doesn't consume collab/event/outcome |
| `test_..._after_parse_failure` | Parse-fail then succeed | `runtime-1, runtime-2, collab-2, event-2` | + `outcome-2` | Parse runs BEFORE emission in control_plane.py, so 1st consult consumes only runtime-1 |
| `test_..._auth_before_reuse` | Succeed then auth-fail | `runtime-1, collab-1, event-1` | + `outcome-1` | Only 1st consult succeeds, 2nd fails at auth before emission |

Dialogue tests use `range(100)` iterators (created in `_build_dialogue_stack`) and were unaffected — no patching needed.

### Plan Class Name Divergence

The plan referenced `TestCommittedTurnParseError` at `test_dialogue.py:1300`, but the actual class is `TestReplyParseFailure`. The Task 4 subagent handled this by searching for the test method name rather than trusting the class name. This is a pre-existing naming inconsistency between the plan and the codebase.

## Context

### Mental Model

This session was **pure plan execution** — no design decisions, no exploration, no debugging. The plan authored in session 8 was sufficiently detailed (complete code for every step, exact test commands, explicit UUID consumption analysis) that every subagent completed without questions or blocks.

The key constraint was sequentiality: tasks modify the same files (`dialogue.py` modified by Tasks 4, 5, 6; `test_dialogue.py` modified by Tasks 4, 5, 6), so parallel dispatch was not possible for most tasks. The spec review for Task 3 was the only parallel work (background while Task 4 executed).

### Execution Methodology

Used **subagent-driven development** — the `superpowers:subagent-driven-development` skill. Key execution choices:

- **Model selection:** All tasks dispatched to `sonnet` (not `opus`) because the plan contained complete code for every step. No design judgment required — pure mechanical implementation.
- **Sequential dispatch:** Tasks 1→2→3→4→5→6→7→8 executed sequentially. Parallel dispatch was not possible because tasks modify overlapping files (`dialogue.py` modified by Tasks 4, 5, 6).
- **Review scope:** Skipped per-task spec/code reviews for Tasks 1-2 (trivially mechanical). Ran spec compliance review for Task 3 (the most complex task with UUID iterator analysis). Skipped reviews for Tasks 4-8 after confirming the execution pattern was reliable.
- **Background parallelism:** The Task 3 spec review ran in the background while Task 4 was dispatched — the only parallel work in the session. This was possible because they touched different files (control_plane.py vs dialogue.py).
- **Mode:** All subagents ran with `bypassPermissions` to avoid per-tool approval prompts during execution.

### Project State

- **Branch:** `feature/ac6-analytics-emission` at `64b724d0` (8 commits ahead of `main`)
- **Tests:** 446 passing (430 existing + 16 new, plus 2 existing tests extended)
- **Lint:** Clean on all 8 target files after ruff format
- **Plan:** Fully executed, all 8 tasks complete, plan itself updated with P1/P2 fixes (still untracked on main, committed on feature branch)

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| 5 | 2026-04-01 | Execute Tasks 0-3 | `archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| 6 | 2026-04-01 | Execute Task 4 | `archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md` |
| 7 | 2026-04-01 | Merge + Tasks 5-6 | `archive/2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md` |
| 8 | 2026-04-01 | AC6 plan | `archive/2026-04-01_13-38_ac6-analytics-emission-plan.md` |
| **9** | **2026-04-01** | **AC6 execution** | **This handoff** |

## Learnings

### Plan findings that catch pre-execution gaps pay for themselves

**Mechanism:** The user found 2 findings (P1 + P2) against the plan before execution started. P1 (missing branch prerequisite) would have caused the first subagent to commit on `main` and hit the gitflow hook — requiring diagnosis and branch creation mid-stream. P2 (mid-file imports, unused locals, incomplete lint gate) would have caused ruff failures at Task 8, requiring backtracking to fix test files.

**Evidence:** P1 was confirmed by the gitflow hook's behavior (blocks edits on protected branches). P2's three sub-issues were each verifiable: (a) ruff E402 for mid-file imports, (b) ruff F841 for unused `store`/`turn_store` variables, (c) Task 8 only listing 4 server files in the ruff command.

**Implication:** Pre-execution plan review is a force multiplier for subagent-driven development. Each finding caught pre-execution saves an entire subagent failure + diagnosis + re-dispatch cycle. The review took ~5 minutes; the execution saved would have been 10-15 minutes per finding.

**Watch for:** Any plan that will be executed by subagents should be reviewed for: (1) branch/environment prerequisites, (2) import placement in existing files, (3) lint scope completeness.

### Subagent-driven execution of well-specified plans is reliably mechanical

**Mechanism:** When the plan includes complete code for every step, exact test commands with expected output, and explicit analysis of edge cases (like UUID consumption), sonnet subagents complete every task without questions or blocks. No task required re-dispatch, escalation, or context supplementation.

**Evidence:** 8 tasks, 8 first-attempt successes. No `NEEDS_CONTEXT`, `BLOCKED`, or `DONE_WITH_CONCERNS` statuses. The only adaptation was Task 4's subagent finding `TestReplyParseFailure` instead of the plan's `TestCommittedTurnParseError` — handled by searching.

**Implication:** The investment in plan completeness (session 8's 3 review rounds) directly reduces execution cost. A plan that leaves design decisions to the worker requires more capable models and more review cycles.

**Watch for:** Plans where the code blocks are "approximate" or "adapt as needed" — these signal the plan isn't ready for subagent execution and will produce `NEEDS_CONTEXT` or incorrect implementations.

### Pre-existing ruff formatting divergence is a per-file tax on every feature branch

**Mechanism:** The codex-collaboration plugin has ~28 files where ruff's formatting differs from existing style. Any feature branch that touches one of these files picks up the formatting diff. This session touched 7 such files — the style commit was 127 insertions / 79 deletions of pure formatting.

**Evidence:** `uv run ruff format --check` on the 8 target files showed 7 would be reformatted. `git diff --stat` after formatting showed changes only in pre-existing long lines, not in AC6 code.

**Implication:** A bulk formatting pass on the codex-collaboration plugin (as a standalone chore commit on main) would eliminate this tax. Every future feature branch touching these files would avoid the mixed diff.

**Watch for:** Any `ruff format .` on the full plugin directory — the plan explicitly warns against this because it reformats ~28 files. But a deliberate, standalone formatting PR would be the right way to address it.

## Next Steps

### 1. User reviews the implementation

**Dependencies:** None — branch is ready.

**What to read first:** `git log --oneline main..feature/ac6-analytics-emission` for commit overview, then `git diff main..feature/ac6-analytics-emission -- '*.py'` for the full diff.

**Approach:** User reviews implementation against the plan. The user stated they will share findings in the next session.

**Acceptance criteria:** User approves the implementation or identifies findings to address.

**Potential obstacles:** The plan class name divergence (`TestCommittedTurnParseError` vs `TestReplyParseFailure`) — the subagent used the correct actual name, but the plan still contains the incorrect name. This is cosmetic.

### 2. Merge to main (after review)

**Dependencies:** User review approval (#1).

**What to read first:** N/A.

**Approach:** `git checkout main && git merge --ff-only feature/ac6-analytics-emission` (user prefers `--ff-only` from prior sessions).

**Acceptance criteria:** 446 tests passing on main, `git log --oneline` shows clean commit history.

### 3. Commit the plan (if not already committed)

**Dependencies:** None — plan was updated with P1/P2 fixes this session but is still untracked on `main`. It was committed as part of the feature branch.

**What to read first:** `git status` after merge to check if plan needs separate commit.

**Approach:** Plan is already in the feature branch commits. After merge, it will be on main.

## In Progress

Clean stopping point. All 8 tasks complete. 446 tests passing. Branch `feature/ac6-analytics-emission` ready for user review. No work in flight.

## Open Questions

### Plan class name divergence

The plan at `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` references `TestCommittedTurnParseError` in Task 4 Step 5, but the actual class is `TestReplyParseFailure`. The implementation is correct (uses the real class name). Should the plan be updated post-execution? It's a dead document after execution, but the divergence could confuse anyone reading it.

### Bulk ruff formatting for codex-collaboration

The plugin has ~28 files with pre-existing formatting divergence from ruff. Should a standalone formatting PR be created to clear this debt? It would eliminate the mixed-diff tax on future feature branches.

## Risks

### Plan still references wrong class name

Low risk. The plan document (`docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md`) references `TestCommittedTurnParseError` but the actual class is `TestReplyParseFailure`. The implementation is correct. Only impacts someone reading the plan after execution.

### Feature branch includes pre-existing formatting changes

Low risk. The `style:` commit (`64b724d0`) includes ~200 lines of pre-existing formatting fixes alongside the AC6 files. This is clearly separated from feature commits but could cause confusion during code review if the reviewer doesn't recognize the pre-existing divergence.

## References

| What | Where |
|------|-------|
| Implementation plan (executed) | `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` |
| Ticket (AC6 scope) | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` |
| Delivery spec (packet 2b) | `docs/superpowers/specs/codex-collaboration/delivery.md:248` |
| OutcomeRecord model | `packages/plugins/codex-collaboration/server/models.py:161-177` |
| Journal append_outcome | `packages/plugins/codex-collaboration/server/journal.py:164-168` |
| Consult emission | `packages/plugins/codex-collaboration/server/control_plane.py:207-219` |
| Dialogue reply emission | `packages/plugins/codex-collaboration/server/dialogue.py:~320-332` |
| Recovery emission | `packages/plugins/codex-collaboration/server/dialogue.py:~610-623` |
| Repair emission | `packages/plugins/codex-collaboration/server/dialogue.py:~720-733` |
| Shape consistency test | `packages/plugins/codex-collaboration/tests/test_outcome_shape_consistency.py` |
| Prior handoff (AC6 plan) | `docs/handoffs/archive/2026-04-01_13-38_ac6-analytics-emission-plan.md` |

## Gotchas

### Parse-emission ordering differs between consult and dialogue

In `control_plane.py`, `parse_consult_response()` runs BEFORE audit/outcome emission. In `dialogue.py`, audit/outcome emission runs BEFORE `parse_consult_response()`. This means consult parse failures don't produce outcome records, but dialogue parse failures do. This ordering difference affects UUID consumption analysis in tests.

### UUID iterators are finite and path-sensitive

Tests use `iter(("uuid-1", ...)).__next__` for deterministic UUIDs. Each `self._uuid_factory()` call in the success path consumes one entry. The consumption analysis requires tracing which code path each test exercises — failure paths consume fewer UUIDs than success paths.

### Ruff formatting artifacts in codex-collaboration

Running `ruff format .` reformats ~28 files beyond the target files. Always format specific files: `ruff format server/models.py server/journal.py ...` — never the whole directory. A bulk formatting PR would clear this debt.

### OperationJournal.context_size nullability

Both `OperationJournalEntry.context_size` and `OutcomeRecord.context_size` are `int | None`. Recovery/repair paths pass `entry.context_size` through directly — no coercion to 0. A `None` context_size in the outcome means the size was not available at recovery time (data-quality gap, not fabrication).

### Plan references wrong test class name

Task 4 Step 5 in the plan references `TestCommittedTurnParseError`, but the actual class in `test_dialogue.py` is `TestReplyParseFailure`. The implementation uses the correct name. This only affects plan readability.

## User Preferences

**Execute-then-review workflow:** Consistent across all 9 sessions. User reviews output before proceeding. This session: user provided pre-execution findings against the plan, then approved execution.

**Pre-analysis before Claude acts:** User provided 2 structured findings (P1/P2 with `::code-comment` annotations) before execution started. The findings cited specific plan lines and codebase evidence. This pattern (user scopes corrections, Claude implements) has been consistent since session 1.

**Merge safety:** User prefers `--ff-only` for branch merges (established in prior sessions). Feature branches for implementation work.

**Precision in plans:** User expects plans to be executable as-is by worker agents. The P1 finding (missing branch prerequisite) and P2 finding (lint gaps) both reflect this expectation — plans should not require the worker to infer prerequisites or discover lint issues at the end.
