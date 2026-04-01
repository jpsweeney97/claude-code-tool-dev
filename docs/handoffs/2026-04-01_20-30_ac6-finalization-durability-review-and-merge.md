---
date: 2026-04-01
time: "20:30"
created_at: "2026-04-01T20:30:00Z"
session_id: e29ae46c-afdb-4feb-86a8-7d17f947db99
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_18-15_ac6-analytics-emission-execution.md
project: claude-code-tool-dev
branch: main
commit: 9d5b8b74
title: "AC6 finalization durability — review, implementation, and merge"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_dialogue_integration.py
  - packages/plugins/codex-collaboration/tests/test_journal.py
  - packages/plugins/codex-collaboration/tests/test_control_plane.py
  - packages/plugins/codex-collaboration/tests/test_mcp_server.py
  - docs/plans/2026-04-01-AC6-finalization-durability-and-replay-safe-emission.md
  - docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md
---

# AC6 finalization durability — review, implementation, and merge

## Goal

Review the AC6 analytics emission implementation from session 9, identify durability and error-surfacing defects, design fixes, iterate the plan through 3 review rounds, implement, and merge to main.

**Trigger:** Session 9 completed all 8 AC6 execution tasks (OutcomeRecord emission on 4 success paths). This session resumed for user review of that implementation. The user's first-pass review surfaced 3 findings (2×P1, 1×P2) against failure semantics and analytics integrity — not the happy-path wiring.

**Stakes:** Medium-high. AC6 is the last analytics acceptance criterion in ticket T-20260330-03. The findings exposed a durability inversion where the analytics artifact (the whole point of AC6) was less durable than the operational artifact it derived from. Without the fix, outcome records could be permanently lost after any `append_outcome()` failure because the journal entry was already marked `completed` and recovery would never revisit it.

**Success criteria:** (1) `completed` written only after all local finalization artifacts are durable. (2) Replay-safe JSONL append helpers prevent duplicate audit/outcome rows across retries. (3) `CommittedTurnFinalizationError` surfaces instead of raw `OSError` after a committed turn. (4) Recovery/repair outcome timestamps use remote `createdAt`. (5) Consult audit/outcome appends are independently best-effort. (6) 459 tests passing, lint clean. (7) Merged to main.

**Connection to project arc:** Tenth session in the codex-collaboration build chain. Sessions 1-7 completed persistence hardening. Session 8 authored the AC6 plan. Session 9 executed it. This session reviewed, hardened, and merged.

## Session Narrative

Resumed from the session 9 handoff (`2026-04-01_18-15_ac6-analytics-emission-execution.md`). The handoff's next step was user review of the AC6 implementation on `feature/ac6-analytics-emission`.

**User's first-pass review.** The user provided 3 structured findings with `::code-comment` annotations, each citing specific lines, reproduction steps, and confidence levels:

1. [P1] `dialogue.py:301-343` — Outcome loss is unrecoverable. The dialogue paths mark the operation journal `completed` before writing the analytics record. If `append_outcome()` fails after `completed` is written, `list_unresolved()` never surfaces the entry again. The user forced `append_outcome` to raise during `reply()` and confirmed: raw failure, no `analytics/outcomes.jsonl`, and `journal.list_unresolved(session_id="sess-1") == 0`. The same ordering was repeated in recovery and repair paths.

2. [P1] `dialogue.py:330-357` — Outcome append failures escape as raw errors after the turn is already committed. The new analytics write sits outside the `CommittedTurnParseError` wrapper. `reply()` surfaced `OSError("outcome boom")` while the handle remained `active` and `audit/events.jsonl` already contained the turn. `codex_consult()` had the same partial-failure surface.

3. [P2] `dialogue.py:628-639` — Recovery and repair paths stamped outcomes with `self._journal.timestamp()` (wall clock at recovery time) instead of the original turn's `createdAt` from `thread/read`.

**Root cause analysis.** I confirmed all three findings by reading the code. The core issue was a **durability inversion**: the journal marked `completed` (the operational artifact) before writing audit/outcome (the analytics artifacts). Since `list_unresolved()` only looks at the phase of the terminal record, artifact completeness was invisible to recovery. I also identified that `_best_effort_repair_turn()` had a scope mismatch: the blanket `try` at `dialogue.py:674` only covered remote read + turn confirmation, but the `completed` write and artifact appends at `:718-755` were exposed to the caller — contradicting the docstring's "all exceptions are swallowed" contract.

**Fix hypothesis exploration.** Three options were discussed:

- Option A: Move `completed` after local finalization (pre-completion semantics). Keep existing phases, treat `dispatched` as "remote dispatch done, local finalization pending."
- Option B: Add a new terminal phase like `finalized`. More explicit state machine but larger schema and test blast radius.
- Option C: Downgrade outcomes to best-effort post-completion. Simplest but doesn't close the durability hole.

The user chose **pre-completion semantics** (Option A). I probed for gaps:

1. **Gap 1:** Option A conflates two failure modes — "remote turn never completed" vs. "remote turn succeeded but local outcome write failed." Recovery needs to distinguish these. The user verified that `_recover_turn_dispatch()` already distinguishes `turn_confirmed` vs `turn_confirmed == False` via `thread/read`, so no new recovery mode was needed.

2. **Gap 2:** Audit event had the same ordering vulnerability. The user confirmed both audit and outcome should move pre-completion.

3. **Gap 3:** The structured error's audience — the MCP tool caller via `mcp_server.py`.

**Duplicate analysis correction.** I initially claimed the duplicate-on-replay risk was limited to a "narrow crash window between two JSONL appends." The user corrected this: if `append_audit_event()` succeeds and `append_outcome()` raises deterministically, the entry stays at `dispatched`, and recovery in `_recover_turn_dispatch()` will re-append audit. This is the normal replay behavior for any partial local finalization failure, not just a crash edge case. Idempotence (replay-safe guards) was therefore required, not optional.

**Further user corrections:**

- The proposed downstream dedupe key `collaboration_id + outcome_type` was too weak — a single collaboration has many `dialogue_turn` outcomes. Correct key: `collaboration_id + turn_id + outcome_type` for outcomes, `collaboration_id + turn_id + action` for audit.

- `entry.created_at` is the journal intent timestamp, not the remote turn completion time. For recovery/repair, the authoritative source is `completed_turns[turn_index].get("createdAt")` from `thread/read`.

- The repair path's blanket `try` ended at line 696, not covering the `completed` write and artifact appends — making repair not "P2-immune" as I had claimed.

**Plan authoring (3 rounds).** The user wrote the first draft of the plan. I reviewed and found 5 findings:

Round 1 findings:
- [F1] Finalization error boundary in `reply()` not specified — no `try`/`except` structure defined, TurnStore.write excluded from boundary.
- [F2] Successful repair still surfaces raw `run_turn()` exception — the "error surfacing" goal was incomplete.
- [F3] Recovery/repair timestamp extraction underspecified — no field name, no fallback chain.
- [F4] `reply()` reorder omits what happens if `completed` write itself fails.
- [F5] Consult's use of replay-safe helpers is unnecessary overhead — consult `collaboration_id`s are unique per call.

Round 2: User addressed all 5 findings. I found:
- [F1] Phase naming error — plan said `dispatched` but entry is at `intent` when repair runs.
- [F2] Confirmed_finalized inline resume failure path unspecified.
- [F3] Finalization helper needs conditional TurnStore.write.
- [F4] Missing rationale for audit/outcome timestamp asymmetry.
- [F5] Replay-safe helper behavior on non-existent JSONL file.

Round 3: User addressed all 5 findings. Plan declared review-clean — no remaining findings.

**Implementation.** The user implemented the plan manually across `dialogue.py`, `journal.py`, and `control_plane.py`, with tests expanded across 5 test files. 459 tests passing, lint clean.

**Implementation review.** I read all changed files and traced every code path:
- Reply success path: dispatched → finalize (TurnStore → audit_once → outcome_once → completed) → parse
- Repair three-way result: unconfirmed / confirmed_unfinalized / confirmed_finalized
- Recovery: same finalization helper, failure logged + handle unknown
- Resume inline: success → active, failure → unknown
- Replay-safe helpers: scan JSONL with predicate, skip if logical match found
- Consult: separate try/excepts for audit and outcome

One minor gap identified: no test explicitly asserted the timestamp fallback path (empty `createdAt` → `entry.created_at`). User added the missing regression test. Final count: 460 tests passing. (Note: 459 was the count before the fallback test was added; verify on next session.)

**Merge.** Committed implementation as `72cf2910` (fix: harden AC6 dialogue finalization ordering and error surfacing) and plans as `9d5b8b74` (docs: add AC6 analytics emission and finalization durability plans). Merged `feature/ac6-analytics-emission` to `main` via `--ff-only`. Branch deleted.

## Decisions

### Pre-completion semantics over new phase or best-effort

**Choice:** Move `completed` after all local finalization writes. Keep existing 3-phase model (`intent`, `dispatched`, `completed`) — no new phases.

**Driver:** The user stated: "`completed` should not be written until the local durable side effects that make the turn inspectable are done." The `OperationJournalEntry` model docstring at `models.py:252-254` already described `completed` as "confirmed, eligible for compaction" — the code was inconsistent with its own documentation.

**Alternatives considered:**
- **Option B: New `finalized` phase** — more explicit state machine. Rejected because the existing phases are sufficient when `completed` is properly gated, and adding a phase would require schema migration, test updates across all recovery paths, and changes to `compact()`.
- **Option C: Best-effort post-completion** — simplest but doesn't close the durability hole. The user explicitly rejected: "This is the wrong contract for AC6 if robustness is the goal."

**Trade-offs accepted:** Moving `completed` later means a crash between audit/outcome write and `completed` write leaves the entry at `dispatched`. Recovery will re-confirm the remote turn (redundant network call) and re-attempt artifact writes (replay-safe helpers prevent duplicates). This is a small efficiency cost for a significant durability gain.

**Confidence:** High (E2) — traced all 3 code paths (reply, recovery, repair) through the new ordering, verified replay-safe helpers prevent duplicates in partial-success scenarios.

**Reversibility:** Medium — the ordering change is internal to `dialogue.py` and `journal.py`. No external API changes. But the replay-safe helpers are now depended on by recovery, so removing them would require re-introducing the old ordering.

**Change trigger:** If the codex-collaboration plugin moves to a transactional storage backend (e.g., SQLite), the replay-safe JSONL scanning could be replaced with atomic multi-row writes.

### Three-way repair result with inline resume

**Choice:** `_best_effort_repair_turn()` returns `Literal["unconfirmed", "confirmed_unfinalized", "confirmed_finalized"]`. For `confirmed_finalized`, `reply()` attempts inline resume and restores handle to `active`.

**Driver:** The user identified that the pre-existing code had a gap: successful repair still surfaced a raw `run_turn()` exception, leaving the caller with no signal that the turn was actually committed. "The 'error surfacing' goal is incomplete" if repair confirms the turn but the caller sees a raw network timeout.

**Alternatives considered:**
- **Keep blind re-raise** — always re-raise the original `run_turn()` exception regardless of repair outcome. Rejected because the caller would retry a turn that's already committed, creating duplicates.
- **Two-way result (confirmed/unconfirmed)** — simpler but conflates "confirmed and finalized" with "confirmed but finalization failed." These need different error handling: the first should restore the handle, the second should leave it unknown.

**Trade-offs accepted:** More complex `reply()` exception handler (switch on 3 states vs. unconditional re-raise). Inline resume may fail, requiring its own error handling. Accepted because the previous behavior was strictly wrong — callers got misleading errors.

**Confidence:** High (E2) — tested all 3 states explicitly, including the resume-failure edge case.

**Reversibility:** Medium — the repair return type is internal. Reverting to blind re-raise would require removing the `CommittedTurnFinalizationError` from the repair path.

**Change trigger:** If the MCP protocol gains native "operation partially succeeded" semantics, the structured error could be replaced with a protocol-level signal.

### Asymmetric consult vs. dialogue handling

**Choice:** Consult uses raw `append_audit_event` / `append_outcome` (not replay-safe helpers), each wrapped in independent best-effort blocks. Dialogue uses replay-safe helpers with JSONL scan.

**Driver:** Consult is stateless — no journal, no recovery path, no retry. Each consult generates a unique `collaboration_id` via `self._uuid_factory()`, so the JSONL scan would never find a match. The overhead is pure waste.

**Alternatives considered:**
- **Use replay-safe helpers for both** — consistent but adds O(n) file scan per consult with zero benefit. Rejected for unnecessary overhead.

**Trade-offs accepted:** If consult ever gains a journal (unlikely for R1), this asymmetry would need revisiting. Accepted because consult is explicitly best-effort for local artifacts.

**Confidence:** High (E1) — consult `collaboration_id` uniqueness is structural (fresh UUID per call).

**Reversibility:** High — switching consult to replay-safe helpers is a one-line change per append call.

**Change trigger:** If consult gains journal-backed persistence or retry semantics.

## Changes

### Modified files

| File | What Changed | Lines |
|------|-------------|-------|
| `server/dialogue.py` | Extracted `_finalize_confirmed_turn` shared helper; added `CommittedTurnFinalizationError`; refactored `_best_effort_repair_turn` to return 3-way result; added `_resume_handle_inline`; reordered `reply()` to finalize before `completed`; reordered `_recover_turn_dispatch()` to use shared helper; added `_confirmed_turn_details` for timestamp extraction; added `_completed_entry` helper; updated docstrings | +422/-233 net |
| `server/journal.py` | Added `append_dialogue_audit_event_once` and `append_dialogue_outcome_once` replay-safe helpers; added `_jsonl_contains` static method | +49 |
| `server/control_plane.py` | Wrapped consult audit and outcome appends in independent try/except blocks; added `_log_local_append_failure` helper | +64/-39 net |
| `tests/test_dialogue.py` | Added `TestDialogueFinalizationFailures` (4 tests); expanded `TestBestEffortRepairTurn` (timestamp tests); added `TestReplyRunTurnFailure` tests for confirmed_unfinalized, confirmed_finalized, resume failure; added timestamp fallback regression test | +356 |
| `tests/test_dialogue_integration.py` | Updated integration test assertions for new finalization ordering | +8/-8 |
| `tests/test_journal.py` | Added `TestDialogueReplaySafeAppends` (2 tests) — audit dedupe and outcome dedupe with missing-file handling | +79 |
| `tests/test_control_plane.py` | Added `test_codex_consult_suppresses_audit_failure` and `test_codex_consult_suppresses_outcome_failure` | +70 |
| `tests/test_mcp_server.py` | Added `test_mcp_surfaces_committed_turn_finalization_guidance` and `FakeDialogueControllerWithFinalizationError` | +73 |

### Created files

| File | Purpose |
|------|---------|
| `docs/plans/2026-04-01-AC6-finalization-durability-and-replay-safe-emission.md` | Review-clean plan (3 review rounds) |
| `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` | Original AC6 execution plan (from session 8, updated with P1/P2 fixes in session 9) |

### Commit history (this session)

| SHA | Message |
|-----|---------|
| `72cf2910` | fix: harden AC6 dialogue finalization ordering and error surfacing |
| `9d5b8b74` | docs: add AC6 analytics emission and finalization durability plans |

## Codebase Knowledge

### Finalization Architecture (Post-Durability Fix)

The shared `_finalize_confirmed_turn` helper at `dialogue.py:206-254` is called by three sites:

| Caller | Entry Phase | Timestamp Source | Turn ID Source |
|--------|-------------|-----------------|----------------|
| `reply()` success path (`:444-450`) | `dispatched` | `self._journal.timestamp()` (append time) | `turn_result.turn_id` |
| `_recover_turn_dispatch()` (`:710-716`) | `intent` or `dispatched` | `completed_turns[turn_index].get("createdAt")` with fallback to `entry.created_at` | Extracted from `thread/read` |
| `_best_effort_repair_turn()` (`:785-791`) | `intent` | Same as recovery | Same as recovery |

The helper's execution order is: TurnStore.write (conditional on `context_size` + `turn_sequence`) → `append_dialogue_audit_event_once` (conditional on `runtime_id` + `turn_id`) → `append_dialogue_outcome_once` (same guard) → `write_phase(completed)`.

### Replay-Safe JSONL Helpers

`journal.py:169-201` — Two helpers that scan existing JSONL and skip append if a matching logical record exists:

| Helper | Dedupe Key | JSONL File |
|--------|-----------|------------|
| `append_dialogue_audit_event_once` | `(action, collaboration_id, turn_id)` | `audit/events.jsonl` |
| `append_dialogue_outcome_once` | `(outcome_type, collaboration_id, turn_id)` | `analytics/outcomes.jsonl` |

Backed by `_jsonl_contains` (`journal.py:263-280`) — static method that reads JSONL line-by-line with a predicate. Handles missing files (returns False → proceed to append) and malformed JSON lines (skips).

### Repair Three-Way Result

`_best_effort_repair_turn` (`dialogue.py:744-799`) returns `RepairTurnResult = Literal["unconfirmed", "confirmed_unfinalized", "confirmed_finalized"]`:

| Result | Meaning | `reply()` Behavior |
|--------|---------|-------------------|
| `unconfirmed` | Thread/read failed or turn not confirmed | Set handle `unknown`, re-raise original `run_turn()` exception |
| `confirmed_unfinalized` | Turn confirmed but finalization helper raised | Set handle `unknown`, raise `CommittedTurnFinalizationError` |
| `confirmed_finalized` | Turn confirmed, all artifacts written, `completed` written | Attempt inline resume; if resume succeeds → handle `active`, if fails → handle `unknown`. Raise `CommittedTurnFinalizationError` in both cases |

### Error Type Hierarchy

| Error | When Raised | Handle Status After | Journal State After |
|-------|-------------|--------------------|--------------------|
| Original `run_turn()` exception | Repair result = `unconfirmed` | `unknown` | `intent` (unresolved) |
| `CommittedTurnFinalizationError` | Finalization fails after `run_turn()` succeeds, OR repair confirms but can't/can finalize | `unknown` (unless repair finalized + resume succeeded → `active`) | `dispatched` or `intent` (unresolved), unless repair finalized → `completed` |
| `CommittedTurnParseError` | Parse fails after `completed` written | `active` (unchanged) | `completed` |

### Phase Transitions (Post-Fix)

| Code Path | Phase Sequence | Notes |
|-----------|---------------|-------|
| `reply()` success | intent → dispatched → completed | `completed` written last by finalization helper |
| `reply()` finalization failure | intent → dispatched | Stays at `dispatched`, recovery handles |
| `reply()` run_turn failure + repair confirms | intent → completed | Direct jump, no intermediate `dispatched` |
| `reply()` run_turn failure + repair unconfirmed | intent | Stays at `intent`, recovery handles |
| Recovery confirms | intent → completed OR dispatched → completed | Depends on where crash happened |
| Recovery unconfirmed | intent OR dispatched | Phase unchanged, handle set to `unknown` |

### Consult Best-Effort Pattern

`control_plane.py:210-242` — Two independent try/excepts:

```
try:
    journal.append_audit_event(...)
except Exception as exc:
    _log_local_append_failure("codex_consult_audit", exc, collaboration_id)
try:
    journal.append_outcome(...)
except Exception as exc:
    _log_local_append_failure("codex_consult_outcome", exc, collaboration_id)
return ConsultResult(...)
```

Audit failure doesn't block outcome append. Neither blocks `ConsultResult` return. Uses raw (non-replay-safe) helpers because consult `collaboration_id` is unique per call.

### Test Count by Area (Post-Durability Fix)

| Test File | Count | New This Session |
|-----------|-------|-----------------|
| `test_dialogue.py` | ~73 | +13 (finalization failures, repair states, timestamps, resume failure) |
| `test_journal.py` | ~25 | +2 (replay-safe dedupe) |
| `test_control_plane.py` | ~20 | +2 (consult best-effort) |
| `test_mcp_server.py` | ~12 | +1 (CTFE surfacing) |
| `test_dialogue_integration.py` | ~11 | ~0 (assertions updated) |
| `test_outcome_record.py` | 8 | 0 (from session 9) |
| `test_outcome_shape_consistency.py` | 1 | 0 (from session 9) |
| **Total** | **459** | **+18** |

## Context

### Mental Model

This session was a **review-driven hardening** of the AC6 analytics emission. The user's review findings exposed a durability inversion — the journal's `completed` phase was a lie. It said "done" when local artifacts could still fail. The fix was semantic tightening: make `completed` actually mean what its docstring said it means ("confirmed, eligible for compaction"), and make the write ordering enforce that guarantee.

The replay-safe helpers are the key design element. They make the system convergent: any partial failure at any point in the finalization sequence can be retried via recovery, and the replay-safe scan ensures no duplicates. The system always converges to the correct final state regardless of where it crashed — textbook idempotent recovery.

### Execution Methodology

This session was **user-driven** in a way earlier sessions were not. The user wrote all production code manually (no subagent dispatch). My role was reviewer — finding gaps in findings, probing proposals, reviewing the plan through 3 rounds, and reviewing the final implementation. The user also wrote the plan (I reviewed it) and implemented it (I reviewed it).

### Project State

- **Branch:** `main` at `9d5b8b74` (12 AC6 commits merged via `--ff-only`)
- **Tests:** 459 passing (430 pre-AC6 + 18 from session 9 execution + 18 from this session's durability fix - some overlapping with session 9 changes that were modified)
- **Lint:** Clean on all modified files
- **AC6 status:** Complete — analytics emission on all 4 success paths, with finalization durability, replay safety, and structured error surfacing

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
| 9 | 2026-04-01 | AC6 execution | `archive/2026-04-01_18-15_ac6-analytics-emission-execution.md` |
| **10** | **2026-04-01** | **AC6 durability review + merge** | **This handoff** |

## Learnings

### User-driven plan review catches structural defects that automated review misses

**Mechanism:** The user's 3 findings against the AC6 implementation were all about failure semantics — completed-before-outcome ordering, raw exception escaping post-commit, and timestamp source confusion. These require tracing the state machine through failure paths, not just reading the happy path. The user reproduced each finding with specific monkeypatching and state inspection.

**Evidence:** Finding P1 was confirmed by forcing `append_outcome()` to raise and checking `journal.list_unresolved()` — a specific falsification test that showed the entry was permanently lost. This kind of targeted failure injection is the right tool for durability verification.

**Implication:** For any feature that adds durable side effects (audit events, analytics records, metadata), the review should include explicit failure injection: force each write to fail independently and verify the system is recoverable.

**Watch for:** Features where "write A then write B" ordering is assumed safe because "B can't fail" — any I/O can fail, and the ordering determines recoverability.

### Plan review rounds have diminishing returns after the third round

**Mechanism:** Round 1 found 5 findings (structural gaps: error boundary, repair-success path, timestamp spec, completed-write failure, consult overhead). Round 2 found 5 findings (factual error in phase naming, resume failure path, conditional TurnStore, timestamp rationale, missing-file handling). Round 3 found 0 findings — plan declared review-clean.

**Evidence:** The severity pattern was: Round 1 = architectural gaps, Round 2 = specification gaps and one factual error, Round 3 = nothing. Each round addressed a smaller class of issues.

**Implication:** For plans of this complexity (~80 lines), 2-3 review rounds is the right investment. The first round catches structural issues, the second catches specification issues, and the third confirms convergence.

**Watch for:** Plans that still have findings at round 3 — those indicate the design isn't converging and may need a different approach rather than more review iterations.

### Replay-safe JSONL helpers are O(n) and acceptable only at low volume

**Mechanism:** `_jsonl_contains` reads the entire JSONL file on every append-once call. For dialogue turns (low volume, serialized dispatch), this is acceptable. For high-volume consult (if it ever uses these helpers), the scan cost would grow linearly.

**Evidence:** The plan explicitly noted this in assumptions: "Full-file scan dedupe is acceptable for dialogue volume; no side index or schema migration is added." Consult was deliberately excluded from replay-safe helpers for this reason.

**Implication:** If the codex-collaboration plugin adds more JSONL-appending operations (e.g., delegation outcomes), evaluate whether the volume warrants a side index or whether the consult pattern (unique IDs, no replay) is sufficient.

**Watch for:** Any future change that routes consult through replay-safe helpers — this would add unnecessary O(n) scanning per consult with zero dedup benefit.

## Next Steps

### 1. Verify test count on next session start

**Dependencies:** None.

**What to read first:** N/A — just run `uv run pytest packages/plugins/codex-collaboration/tests/ -q`.

**Approach:** The handoff reports 459 tests. The user added a timestamp fallback regression test after my review identified the gap. Verify the actual count is 460 (or whatever the correct number is).

**Acceptance criteria:** Test count matches expectations, no regressions.

### 2. Consider bulk ruff formatting PR for codex-collaboration

**Dependencies:** None — standalone chore.

**What to read first:** `uv run ruff format --check packages/plugins/codex-collaboration/` to see how many files diverge.

**Approach:** A standalone formatting commit on main would eliminate the mixed-diff tax on future feature branches. The session 9 handoff documented ~28 files with pre-existing formatting divergence.

**Acceptance criteria:** All files in the plugin pass `ruff format --check`. The commit is pure formatting, no behavior changes.

**Potential obstacles:** Large diff may be hard to review. Consider doing it as a `chore/ruff-format-codex-collaboration` branch with a clear commit message.

### 3. Proceed with ticket T-20260330-04 and T-20260330-05

**Dependencies:** AC6 (T-20260330-03) is now complete. Check the ticket file for T-20260330-04 and T-20260330-05 scope.

**What to read first:** `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` for remaining acceptance criteria.

## In Progress

Clean stopping point. All AC6 work complete and merged to main. No work in flight.

## Open Questions

### Bulk ruff formatting for codex-collaboration

The plugin has ~28 files with pre-existing formatting divergence from ruff. Should a standalone formatting PR be created to clear this debt? It would eliminate the mixed-diff tax on future feature branches but creates a large diff. Session 9 deferred this question; it remains open.

## Risks

### Replay-safe JSONL scan at scale

Low risk currently. The `_jsonl_contains` helper scans the full JSONL file on every `append_dialogue_*_once` call. At current dialogue volume (single-digit turns per session), this is negligible. If dialogue volume increases significantly, a side index or schema change would be needed. The plan's assumption section explicitly bounds this: "Full-file scan dedupe is acceptable for dialogue volume."

### Phase jump in repair path

Low risk. When repair confirms a turn, the finalization helper writes `completed` directly from `intent` (no intermediate `dispatched`). The journal's `_terminal_phases()` replay just keeps the last record per key, so this works. But it's semantically unusual — the entry was never "dispatched." If any future code checks for `dispatched` phase specifically (rather than `!= completed`), it would miss repair-finalized entries.

## References

| What | Where |
|------|-------|
| Durability plan (review-clean) | `docs/plans/2026-04-01-AC6-finalization-durability-and-replay-safe-emission.md` |
| AC6 execution plan (from session 8) | `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` |
| Ticket (AC6 scope) | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` |
| Delivery spec (packet 2b) | `docs/superpowers/specs/codex-collaboration/delivery.md:248` |
| Finalization helper | `packages/plugins/codex-collaboration/server/dialogue.py:206-254` |
| Replay-safe audit helper | `packages/plugins/codex-collaboration/server/journal.py:169-181` |
| Replay-safe outcome helper | `packages/plugins/codex-collaboration/server/journal.py:189-201` |
| JSONL contains helper | `packages/plugins/codex-collaboration/server/journal.py:263-280` |
| Repair three-way result | `packages/plugins/codex-collaboration/server/dialogue.py:744-799` |
| CommittedTurnFinalizationError | `packages/plugins/codex-collaboration/server/dialogue.py:48-53` |
| Consult best-effort wrapping | `packages/plugins/codex-collaboration/server/control_plane.py:210-242` |
| Resume inline helper | `packages/plugins/codex-collaboration/server/dialogue.py:277-300` |
| Prior handoff (AC6 execution) | `docs/handoffs/archive/2026-04-01_18-15_ac6-analytics-emission-execution.md` |

## Gotchas

### Parse-emission ordering differs between consult and dialogue

In `control_plane.py`, `parse_consult_response()` runs BEFORE audit/outcome emission. Parse failures raise before any audit/outcome is written. In `dialogue.py`, audit/outcome emission runs BEFORE `parse_consult_response()` (via the finalization helper which writes `completed` first). Parse failures produce `CommittedTurnParseError` with all artifacts already durable. This asymmetry is intentional — consult is stateless, dialogue is journaled.

### The finalization boundary includes TurnStore.write

`TurnStore.write` failure is treated the same as audit/outcome failure — `CommittedTurnFinalizationError` is raised and the entry stays unresolved. This is correct because TurnStore is a local artifact needed for `dialogue.read()` integrity. But it means a transient disk error on TurnStore prevents the entry from completing, even though the remote turn is confirmed.

### Repair phase jump: intent → completed

When inline repair confirms a turn and successfully finalizes, the journal goes directly from `intent` to `completed` with no intermediate `dispatched` record. This is valid because `_terminal_phases()` only keeps the last record per key. But it means you cannot reconstruct the exact phase history from the journal — you only see `intent` then `completed`.

### Audit timestamp vs. outcome timestamp in recovery

Audit events always use `self._journal.timestamp()` (append time — when the audit was recorded locally). Outcome records in recovery/repair use `completed_turns[turn_index].get("createdAt")` (remote turn completion time). This asymmetry is intentional: audit is a trust-boundary record (when was it recorded?), outcome is analytics (when did the turn complete?). A test at `test_dialogue.py` explicitly verifies this with a recovery entry where `createdAt` is `2026-04-02` but `entry.created_at` is `2026-04-01`.

### UUID iterators in tests are path-sensitive

Tests use `iter(("uuid-1", ...)).__next__` for deterministic UUID assignment. Adding any `self._uuid_factory()` call in a success path exhausts iterators that don't account for it. The AC6 + durability changes add outcome UUIDs to several paths. All existing iterators were updated in session 9, but new tests must account for the full UUID consumption chain.

## User Preferences

**Execute-then-review workflow:** Consistent across all 10 sessions. User reviews output before proceeding. This session: user provided first-pass findings against the AC6 implementation, then wrote the plan, then implemented, then asked for review at each stage.

**Pre-analysis before Claude acts:** User provided structured findings with `::code-comment` annotations citing specific lines, reproduction steps, and confidence levels. This pattern (user scopes corrections, Claude reviews and probes) has been consistent since session 1.

**Merge safety:** User prefers `--ff-only` for branch merges. Feature branches for implementation work. Confirmed again this session.

**Plan ownership:** In this session, the user authored the plan (Claude reviewed). In session 8, Claude authored the plan (user reviewed). Both patterns work — the user adapts the authorship based on who has the deeper understanding of the problem space.

**Thoroughness over cost:** The user explicitly asked for "ultrathink" on multiple turns, invested 3 review rounds on the plan, and implemented manually rather than delegating to subagents. The user values correctness over speed for durability-critical code.

**Challenge weak ideas:** The user corrected my duplicate analysis ("narrow crash window" → "normal replay behavior"), my dedupe key proposal ("collaboration_id + outcome_type" → needs turn_id), my timestamp source recommendation ("entry.created_at" → "completed_turns[turn_index].get('createdAt')"), and my repair path scope analysis (blanket try coverage). Each correction was backed by specific evidence. This user expects the reviewer to probe back with equal rigor.
