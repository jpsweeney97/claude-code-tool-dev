---
date: 2026-04-01
time: "12:25"
created_at: "2026-04-01T16:25:55Z"
session_id: 18b4b4c3-2b90-4754-be7d-d5d4476a3a72
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md
project: claude-code-tool-dev
branch: fix/persistence-replay-hardening
commit: 2266ccab
title: "persistence hardening Task 4 — Journal migration and controller tests"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/tests/test_journal.py
  - packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
---

# persistence hardening Task 4 — Journal migration and controller tests

## Goal

Execute Task 4 of the persistence hardening implementation plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` — the Journal store migration and controller-level corruption tests.

**Trigger:** Session 5 completed Tasks 0-3 (shared replay helper, TurnStore migration, LineageStore migration). The user's review of Task 3 passed with no findings. Task 4 was the next item in the execution sequence.

**Stakes:** Journal is the most complex store — per-operation+phase conditional requirements mean the callback has branching validation logic. The recovery coordinator at `dialogue.py:446-592` depends on specific fields being present for specific operation+phase combinations. Without enforcement, type-valid but incomplete records survive to recovery and crash with `RuntimeError`. This was the Round 1 P1 finding that drove the most plan complexity.

**Success criteria:** (1) Journal migrated to `replay_jsonl` with `_journal_callback`. (2) Per-operation+phase conditional requirements enforced. (3) `check_health()` available on Journal. (4) Controller-level corruption tests proving store hardening composes correctly with `DialogueController`. (5) All existing tests pass. (6) Ruff clean.

**Connection to project arc:** Sixth session in the persistence hardening chain: design (1) → plan (2) → review rounds 1-3 (3) → review round 4 + merge (4) → execute Tasks 0-3 (5) → **execute Task 4** (6) → merge Branch 1 + Tasks 5-6 (7). Branch 1 (`fix/persistence-replay-hardening`) is now complete pending merge. Branch 2 (`chore/type-narrowing`, Tasks 5-6) follows after Branch 1 merges.

## Session Narrative

Session began by loading the prior handoff (`2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md`), which described the Tasks 0-3 execution session and set Task 4 as the next step. The user provided their review of Task 3 — no findings, pass — and requested proceeding to Task 4 using `/subagent-driven-development`.

**Subagent-driven development setup:** The skill dispatches fresh subagents per task with two-stage review (spec compliance then code quality) after each. Task 4 was split into two sequential sub-tasks: Task 4A (Journal migration, plan steps 1-6) and Task 4B (controller-level corruption tests, plan steps 7-10).

**Task 4A execution (implementer subagent):** The implementer subagent was dispatched with the full plan text for steps 1-6 plus context about prior learnings from Tasks 1-3 (ruff format before check, `type(x) is not int` for bool rejection, expect mechanical fixes). The subagent reported DONE with a significant plan deviation:

The plan's `_journal_callback` required `codex_thread_id` on ALL `turn_dispatch` phases (intent, dispatched, completed), and `turn_sequence` on `dispatched` and `completed`. But production code (`dialogue.py:291-301`, `:588-595`, `:688-695`) writes `completed` phase entries as minimal resolution markers WITHOUT either field. The implementer correctly relaxed the conditional to only enforce at `intent` and `dispatched` phases. Without this fix, the callback would have rejected every `completed` record written by production code — catastrophic for the system.

The implementer also modified `test_dialogue.py:test_recover_thread_creation_dispatched_phase_requires_thread_id` — previously expected `RuntimeError` on missing `codex_thread_id`, now expects silent filtering at replay. This is the correct behavioral change: with replay-level validation, the record is a `schema_violation` and never reaches recovery.

**Verification of plan deviation:** I independently verified by reading `dialogue.py` at three call sites (lines 300-309, 588-595, 688-695). All three write `completed` entries with only the 6 required string fields — no `codex_thread_id`, no `turn_sequence`. The plan had a genuine bug: it was written assuming all phases carry the same fields, but `completed` is semantically different — it's a resolution marker, not a data-carrying record.

**Task 4B execution (implementer subagent):** Dispatched with plan steps 7-10. The subagent reported DONE_WITH_CONCERNS — the plan asserted `handle.status == "unknown"` for the journal fallback test, but the actual behavior is `"active"` due to the two-phase recovery design: Phase 1 quarantines to `unknown` (unconfirmed turn_dispatch intent), then Phase 2 picks up the unknown handle with zero completed turns and reattaches it to `active`. This matches the existing test `test_journal_reconciled_before_reattach` at `test_recovery_coordinator.py:70-117`. The implementer corrected the assertion.

**Spec compliance review (sonnet subagent):** Found one issue — `turn_sequence` not enforced on `turn_dispatch` at `completed` phase, even though the plan required it. I verified this is the same production evidence: `completed` entries never include `turn_sequence`. The test docstring incorrectly said "dispatched/completed" — fixed to "dispatched" with an explanatory note about resolution markers.

**Code quality review (sonnet subagent):** Found two issues: (1) Missing inline comment explaining why `completed` phase is excluded from conditional requirements — the `runtime_id` relaxation had a 4-line comment but the `completed` relaxation didn't. Fixed by adding a comment block. (2) E402 lint violations — `import pytest` and `from server.models import OperationJournalEntry` were mid-file in `test_journal.py`. Moved to top.

**User review (P2 and P3 findings):** The user's review identified two additional issues:

1. **P2: Non-discriminating fallback test.** The controller journal fallback test asserted only `handle.status == "active"` after `recover_startup()`, but that's the same end state whether the malformed row was skipped or accepted (because Phase 2 reattach promotes unknown handles with zero completed turns back to active regardless). Fix: added intermediate assertions before `recover_startup()` — `check_health()` must report `schema_violation` and `list_unresolved()` must show `intent` as terminal phase. These assertions would fail if the callback regressed and accepted the malformed row.

2. **P3: Unused `pytest` import.** Pre-existing in `test_recovery_coordinator.py` but the file was touched by Task 4B, and the plan's lint gate requires `ruff check .` to pass. Removed.

Both fixes committed as the final commit on the branch.

## Decisions

### Relax completed-phase conditional requirements

**Choice:** `turn_dispatch` at `completed` phase does NOT require `codex_thread_id` or `turn_sequence`. Only `intent` and `dispatched` phases enforce these fields.

**Driver:** Production code writes `completed` as minimal resolution markers. Three call sites in `dialogue.py` (lines 300-309, 588-595, 688-695) write only the 6 required string fields. Enforcing `codex_thread_id` at `completed` would reject every `completed` record ever written.

**Alternatives considered:**
- **Follow the plan exactly** — would break all existing `completed` records, making operations unresolvable. Rejected as catastrophic.
- **Update production writers to include all fields on `completed`** — would require changing `dialogue.py` in 3 places plus all existing JSONL files. Rejected as out of scope for the persistence hardening effort (which is about resilience, not schema changes).

**Trade-offs accepted:** `completed` records are less validated than `intent`/`dispatched`. A corrupted `completed` record could falsely resolve an operation. Mitigated by: `completed` is only written after successful execution, so corruption would require a write failure that produces valid JSON with correct required fields but wrong operation semantics — unlikely.

**Confidence:** High (E2) — verified against 3 production call sites and confirmed by the full test suite passing.

**Reversibility:** High — adding `completed` validation later is additive (tighten the conditional).

**Change trigger:** If `dialogue.py` is updated to include `codex_thread_id`/`turn_sequence` in `completed` entries, the validation should be tightened to match.

### Correct controller test assertion from "unknown" to "active"

**Choice:** The journal fallback controller test asserts `handle.status == "active"`, not `"unknown"` as the plan specified.

**Driver:** The recovery coordinator's two-phase design: Phase 1 (`recover_pending_operations`) quarantines the handle to `unknown` (unconfirmed turn_dispatch intent with zero completed turns). Phase 2 (`_reattach_eligible_handles`) picks up the unknown handle, verifies zero completed turns (no metadata completeness check needed), and reattaches it to `active`. This flow is documented by the existing test `test_journal_reconciled_before_reattach` at `test_recovery_coordinator.py:70-117`.

**Alternatives considered:**
- **Split the test into two stages** — call `recover_pending_operations()` first and assert `unknown`, then call the full `recover_startup()` and assert `active`. Rejected as over-testing implementation details — the test's purpose is to verify the end-to-end behavior with a malformed record.
- **Follow the plan's assertion** — would fail because the plan's author didn't model the Phase 2 reattach flow when writing the test stub.

**Trade-offs accepted:** The test no longer asserts the intermediate `unknown` state. Mitigated by adding intermediate assertions (`check_health` and `list_unresolved`) before `recover_startup()` to prove the malformed row was actually skipped.

**Confidence:** High (E2) — verified against the existing `test_journal_reconciled_before_reattach` test which demonstrates the same Phase 1 → Phase 2 flow.

**Reversibility:** High — assertion change only.

**Change trigger:** None — the plan's assertion was incorrect.

### Strengthen controller test with discriminating intermediate assertions

**Choice:** Added `check_health()` and `list_unresolved()` assertions before `recover_startup()` in the journal fallback test.

**Driver:** User's P2 review finding: "After the assertion change to `active`, this test no longer proves the malformed `completed` row was skipped. If `_journal_callback` regressed and accepted that bad terminal row, phase 1 would do nothing and phase 2 would still resume the already-active handle, so the test would still pass."

**Alternatives considered:**
- **Assert `journal.check_health()` only** — proves the malformed row was diagnosed but doesn't prove it affected the terminal-phase computation.
- **Split into `recover_pending_operations()` + state check** — tests Phase 1 in isolation. Rejected as testing implementation details rather than behavioral contract.

**Trade-offs accepted:** More assertions make the test longer and more coupled to `check_health`/`list_unresolved` API. Accepted because the alternative is a non-discriminating test that passes even if the core property (malformed row skipped) is violated.

**Confidence:** High (E2) — if the callback regressed, `check_health()` would return no diagnostics and `list_unresolved()` would return 0 entries (the `completed` row would resolve the operation), failing both assertions.

**Reversibility:** High — assertion-only change.

**Change trigger:** None — this closes a genuine coverage gap.

## Changes

### Modified files

| File | Purpose |
|------|---------|
| `server/journal.py` | Replaced inline `_terminal_phases()` with `replay_jsonl()` + `_journal_callback()`, added `check_health()`, added completed-phase relaxation comment |
| `tests/test_journal.py` | Added `TestReplayHardening` (10 tests), moved imports to top (E402 fix) |
| `tests/test_recovery_coordinator.py` | Added 2 controller-level corruption tests, strengthened journal fallback test with intermediate assertions, removed unused `pytest` import |
| `tests/test_dialogue.py` | Updated `test_recover_thread_creation_dispatched_phase_requires_thread_id` from crash-expected to filter-expected, ruff formatting |

### Commit log (Task 4)

| Commit | Message | Tests |
|--------|---------|-------|
| `a33e98d0` | fix: migrate Journal to shared replay helper (I5) | 411 |
| `7bba1da4` | fix: correct test docstring for turn_sequence enforcement scope | 411 |
| `16394b8e` | test: controller-level corruption tests for journal and TurnStore | 413 |
| `d3de26eb` | style: document completed-phase relaxation, fix E402 import order | 413 |
| `2266ccab` | fix: strengthen controller fallback test, remove unused import | 413 |

### Full branch commit log

| Commit | Message | Tests |
|--------|---------|-------|
| `bf2641af` | docs: update design spec with review findings | — |
| `311fea3f` | feat: shared JSONL replay helper with corruption classification | 382 |
| `5f7edbde` | test: cover UnknownOperation trailing-classification and partial final line | 384 |
| `7cb2685f` | fix: migrate TurnStore to shared replay helper (I2) | 389 |
| `538c726a` | fix: migrate LineageStore to shared replay helper (I4) | 401 |
| `a33e98d0` | fix: migrate Journal to shared replay helper (I5) | 411 |
| `7bba1da4` | fix: correct test docstring for turn_sequence enforcement scope | 411 |
| `16394b8e` | test: controller-level corruption tests for journal and TurnStore | 413 |
| `d3de26eb` | style: document completed-phase relaxation, fix E402 import order | 413 |
| `2266ccab` | fix: strengthen controller fallback test, remove unused import | 413 |

## Codebase Knowledge

### _journal_callback Architecture

`_journal_callback` at `server/journal.py:44-102` — validates all fields and constructs `OperationJournalEntry` explicitly. The callback is a module-level function (not a method or closure), unlike LineageStore's closure factory pattern. This is because Journal doesn't need to mutate external state — it returns `(idempotency_key, entry)` tuples that `replay_jsonl` collects.

Validation layers:
1. **Required strings** (lines 48-50): 6 fields (`idempotency_key`, `operation`, `phase`, `collaboration_id`, `created_at`, `repo_root`) via `isinstance(record.get(name), str)`.
2. **Literal validation** (lines 51-53): `operation` against `_VALID_OPERATIONS` frozenset, `phase` against `_VALID_PHASES` frozenset. Unlike LineageStore which derives frozensets from `get_args(Literal[...])`, Journal uses hardcoded frozensets because the operation/phase values aren't defined as `Literal` type aliases in `models.py`.
3. **Optional strings** (lines 55-58): `codex_thread_id`, `runtime_id` — `isinstance(val, str)`.
4. **Optional ints** (lines 59-62): `turn_sequence`, `context_size` — `type(val) is not int` (rejects bools).
5. **Per-operation+phase conditionals** (lines 69-84):
   - `turn_dispatch` at `intent`/`dispatched`: requires `codex_thread_id` (string)
   - `turn_dispatch` at `dispatched`: additionally requires `turn_sequence` (int)
   - `thread_creation` at `dispatched`: requires `codex_thread_id` (string)
   - `completed` phase: NO conditional requirements (resolution marker)
6. **Explicit construction** (lines 90-101): builds `OperationJournalEntry` from known fields only — extra fields silently ignored (forward-compat).

### Production completed-phase writer pattern

All three `completed` phase writers in `dialogue.py` follow the same minimal pattern:

```python
self._journal.write_phase(
    OperationJournalEntry(
        idempotency_key=...,
        operation=entry.operation,
        phase="completed",
        collaboration_id=...,
        created_at=...,
        repo_root=...,
    ),
    session_id=self._session_id,
)
```

Call sites: `dialogue.py:300-309` (normal turn completion), `dialogue.py:588-595` (recovery turn_dispatch resolution), `dialogue.py:688-695` (best-effort repair resolution). None include `codex_thread_id`, `turn_sequence`, `runtime_id`, or `context_size`.

### Two-phase recovery flow

`DialogueController.recover_startup()` at `dialogue.py:369` runs two phases sequentially:
1. **Phase 1:** `recover_pending_operations()` — processes unresolved journal entries. For `turn_dispatch` intent with zero confirmed turns, quarantines handle to `unknown`.
2. **Phase 2:** `_reattach_eligible_handles()` — iterates all `active` and `unknown` handles. For unknown handles with zero completed turns, reattaches to `active` (eligible for reattach without metadata completeness check). For unknown handles with completed turns, checks TurnStore metadata completeness before reattaching.

This means a `turn_dispatch` intent entry → Phase 1 quarantines to `unknown` → Phase 2 reattaches to `active` (zero completed turns). The end state is `active` regardless of whether Phase 1 found journal entries or not — which is why the controller fallback test needs intermediate assertions to prove the malformed row was actually skipped.

### Non-discriminating test pattern

When recovery has multiple paths that converge to the same end state, asserting only the end state creates a non-discriminating test — it passes regardless of which path was taken. Fix: assert an intermediate state that distinguishes the path being tested.

In this case: `check_health()` reports `schema_violation` (proves malformed row was diagnosed) and `list_unresolved()` shows `intent` as terminal phase (proves fallback to earlier valid row occurred). If the callback regressed and accepted the malformed `completed` row: `check_health()` would report no diagnostics, and `list_unresolved()` would return 0 entries (completed = resolved).

### Dependency Graph (Complete — All Stores Migrated)

```
replay.py (shared helper — no dependencies)
  ↑ imported by:
  ├── turn_store.py (uses replay_jsonl, SchemaViolation)
  ├── lineage_store.py (uses replay_jsonl, SchemaViolation, UnknownOperation)
  └── journal.py (uses replay_jsonl, SchemaViolation, ReplayDiagnostics)

models.py (HandleStatus, CapabilityProfile Literal types; OperationJournalEntry dataclass)
  ↑ imported by:
  ├── lineage_store.py (get_args for literal validation frozensets)
  ├── journal.py (OperationJournalEntry for explicit construction)
  ├── dialogue.py (controller logic, filtering, recovery)
  └── [profiles.py — Task 5 target for type narrowing]
```

### Pre-Migration vs Post-Migration Journal Comparison

| Aspect | Pre-migration | Post-migration |
|--------|--------------|----------------|
| Construction | `OperationJournalEntry(**record)` — crashes on extra fields | Explicit field-by-field construction — extra fields ignored |
| Malformed JSON | `json.JSONDecodeError` caught, line skipped silently | Classified as `trailing_truncation` or `mid_file_corruption` |
| Wrong field types | Silently accepted (e.g., `turn_sequence="not-an-int"`) | `SchemaViolation` diagnosed, record skipped |
| Unknown operations | Silently accepted (e.g., `operation="future_op"`) | `SchemaViolation` diagnosed, record skipped |
| Unknown phases | Silently accepted | `SchemaViolation` diagnosed, record skipped |
| Missing conditional fields | Silently accepted → crashes in recovery | `SchemaViolation` diagnosed, record skipped at replay |
| Diagnostics | None | `check_health()` returns `ReplayDiagnostics` |

## Context

### Mental Model

This is a **defense-in-depth migration** — replacing crash-on-malformed with diagnose-and-continue at the persistence layer. The shared `replay_jsonl` helper is the single chokepoint: every JSONL store routes through it, and it guarantees that no store can crash on bad data. Each store's callback defines what "valid" means for that store's schema, but the corruption classification (trailing vs. mid-file) and exception handling are centralized.

The Journal migration revealed that "valid" is phase-dependent. Unlike TurnStore (fixed schema) and LineageStore (operation-dependent schema), Journal has operation+phase conditional requirements where the same field can be required or optional depending on the combination of two other fields. The `completed` phase is semantically different from `intent`/`dispatched` — it's a resolution marker, not a data-carrying record.

### Project State

- **Branch:** `fix/persistence-replay-hardening` at `2266ccab`
- **Tests:** 413 passing (359 baseline + 54 new)
- **Plan progress:** Tasks 0-4 complete, Tasks 5-6 remain (on Branch 2)
- **Branch 1 status:** Complete, review-clean, ready to merge to main
- **All 3 JSONL stores migrated:** TurnStore, LineageStore, Journal

### Test Count Summary

| Task | New Tests | Running Total |
|------|-----------|---------------|
| Task 1 (replay helper) | 25 | 384 |
| Task 2 (TurnStore) | 5 | 389 |
| Task 3 (LineageStore) | 12 | 401 |
| Task 4 (Journal + controller) | 12 | 413 |
| **Total new** | **54** | |

### Review Statistics

| Task | Review Result | Findings | Tests Added |
|------|--------------|----------|-------------|
| Task 4A (Journal) | Pass with deviation | Completed-phase relaxation (plan bug) | +10 |
| Task 4A spec review | 1 issue (docstring accuracy) | Fixed | — |
| Task 4A quality review | 2 issues (comment, E402) | Fixed | — |
| Task 4B (controller) | Pass with deviation | Assertion corrected (plan bug) | +2 |
| User review | 2 findings (P2, P3) | Both fixed | — |

## Learnings

### Plan bugs concentrate in the most complex task

**Mechanism:** The plan contained ~1800 lines of code written from reading, not execution. Tasks 1-3 had 6 mechanical fixes (unused imports, variables, assertion typo). Task 4 had 2 genuine bugs (completed-phase over-restriction, controller test assertion) plus 3 mechanical fixes (docstring, comment, E402). The plan's complexity directly correlates with bug density.

**Evidence:** Task 4's `_journal_callback` has branching logic (operation+phase conditional requirements) that the plan author modeled incorrectly — they assumed all phases carry the same fields. Tasks 1-3 had fixed schemas (TurnStore) or operation-only discrimination (LineageStore), which the plan modeled correctly.

**Implication:** For future plans with branching validation logic, verify the plan's assumptions against production writers BEFORE execution. The TDD cycle catches the bugs, but discovering them during execution adds review cycles and commits.

**Watch for:** Any plan that specifies different validation rules for different phases/states of the same record type.

### Non-discriminating tests hide regressions in convergent systems

**Mechanism:** When a system has multiple paths that converge to the same end state, an end-state-only assertion passes regardless of which path was taken. A regression in one path (e.g., callback stops rejecting malformed rows) is invisible because the other path still produces the correct end state.

**Evidence:** The controller journal fallback test asserted `handle.status == "active"` after `recover_startup()`. This is the end state for both: (a) malformed row skipped → Phase 1 quarantine → Phase 2 reattach, and (b) malformed row accepted → no quarantine → handle stays active. The test couldn't distinguish (a) from (b).

**Implication:** In convergent systems (recovery, fallback, retry patterns), always assert an intermediate state or side-effect that distinguishes the path being tested. `check_health()` diagnostics, log output, intermediate state snapshots are all viable discriminators.

**Watch for:** Any test of fallback/recovery behavior where the fallback path and the normal path produce the same observable end state.

### Subagent-driven development needs plan deviation tracking

**Mechanism:** The subagent-driven development skill dispatches fresh subagents per task. When a subagent discovers a plan deviation, the deviation is reported in the subagent's result, but the controller (me) must verify it independently. The two-stage review (spec compliance + code quality) catches most issues, but the user's review still found a P2 issue that both automated reviews missed (non-discriminating test).

**Evidence:** The spec reviewer correctly identified the `turn_sequence` at `completed` gap. The code quality reviewer correctly identified the missing comment and E402 violations. Neither identified the non-discriminating test pattern — the user's adversarial review did.

**Implication:** The automated review pipeline (spec + quality) catches structural issues but not semantic test quality issues. The user's review remains essential for catching non-discriminating assertions and other "does this test actually prove what it claims?" questions.

## Next Steps

### 1. Merge Branch 1 to main

**Dependencies:** All Task 0-4 work complete, reviewed, and committed. Branch is review-clean.

**What to read first:** The branch has 10 commits ahead of main (plus 2 handoff archive commits). Consider squash vs. merge commit based on project convention.

**Approach:** Merge `fix/persistence-replay-hardening` to main. The branch has no conflicts (checked implicitly — all work is additive to the codex-collaboration plugin).

**Acceptance criteria:** Main at the merged commit passes full suite (413 tests). No regressions in other packages.

### 2. Create Branch 2 for Tasks 5-6

**Dependencies:** Branch 1 merged to main.

**What to read first:** Plan lines 1691-2062 (Tasks 5-6 — type narrowing).

**Approach:** Create `chore/type-narrowing` from main after merge. Task 5 (profiles, 14 tests) and Task 6 (models, 1 test). These are on a separate branch because they're maintenance/cleanup work, not bug fixes.

**Key complexity:** Task 5 introduces `Literal` types for `ResolvedProfile` fields. Task 6 adds a single test. Both are simpler than Tasks 1-4.

### 3. AC6 analytics emission (deferred)

Still deferred from prior sessions. Actual roadmap work in packet 2b (`delivery.md:255`). Ticket T-20260330-03 tracks it.

## In Progress

Clean stopping point. Tasks 0-4 are committed on `fix/persistence-replay-hardening`. No work in flight. No uncommitted files. The branch has 10 implementation commits ahead of main (plus 2 handoff archive commits).

Next task is merging Branch 1 to main, then creating `chore/type-narrowing` for Tasks 5-6.

## Open Questions

### Plan test count discrepancies (cumulative)

The plan's test counts across all tasks don't match actual:
- Plan says 22 replay tests → actual 25 (plan miscounted + 2 review-driven additions)
- Plan says 13 LineageStore tests → actual 12 in TestReplayHardening
- Plan says 10 Journal tests → actual 10 (matches)
- Plan says 2 controller tests → actual 2 (matches)
- Plan cumulative: 67 → actual: 54 new tests total (but some tests existed before)

The discrepancies are plan counting errors, not implementation deviations.

### Journal per-operation+phase validation completeness

The callback validates conditional requirements for `turn_dispatch` (intent, dispatched) and `thread_creation` (dispatched). It does NOT validate `thread_creation` at `intent` or `completed`, or `turn_dispatch` at `completed`. The rationale: (1) `intent` phase records have no conditional requirements because dispatch hasn't happened yet, and (2) `completed` phase records are minimal resolution markers. This is correct per production code, but future operation types or phases could need conditional requirements added to the callback.

## Risks

### Branch 1 merge may need conflict resolution

Branch 1 has 10 commits touching 7 files in the codex-collaboration plugin. If main has received changes to any of these files since the branch was created, merge conflicts are possible. Mitigated by: the branch only touches store files and test files, which are unlikely to change in parallel.

### Full-file replacement steps remain brittle

Round 4 finding #5 (deferred from prior sessions). Task 4 replaced `_terminal_phases()` entirely. The method was small (18 lines), so this was low-risk. But the pattern of replacing entire methods from plan code is fragile if the file has changed since the plan was written.

### Subagent review pipeline misses semantic test quality

The two-stage automated review (spec compliance + code quality) caught structural issues (missing comment, lint violations, docstring accuracy) but missed the non-discriminating test pattern — a semantic test quality issue. The user's adversarial review was needed to catch it. For Tasks 5-6, expect similar: automated reviews catch "is the code correct?" but not "does this test actually prove what it claims?"

## References

| What | Where |
|------|-------|
| Implementation plan (final) | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| Shared replay helper | `packages/plugins/codex-collaboration/server/replay.py` |
| TurnStore (migrated) | `packages/plugins/codex-collaboration/server/turn_store.py` |
| LineageStore (migrated) | `packages/plugins/codex-collaboration/server/lineage_store.py` |
| Journal (migrated) | `packages/plugins/codex-collaboration/server/journal.py` |
| Recovery coordinator | `packages/plugins/codex-collaboration/server/dialogue.py:369-601` |
| Controller tests | `packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py` |
| HandleStatus/CapabilityProfile types | `packages/plugins/codex-collaboration/server/models.py:10-12` |
| Prior handoff (Tasks 0-3) | `docs/handoffs/archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |

## Gotchas

### Completed phase is a resolution marker with minimal fields

Production code writes `completed` entries with only the 6 required string fields. The plan's callback code required `codex_thread_id` and `turn_sequence` on `completed` — this would reject all production `completed` records. The fix: only enforce conditional requirements at `intent` and `dispatched` phases.

### Two-phase recovery makes end-state assertions non-discriminating

The recovery coordinator runs Phase 1 (journal reconciliation) then Phase 2 (handle reattach). A `turn_dispatch` intent with zero completed turns goes: Phase 1 quarantine → `unknown` → Phase 2 reattach → `active`. This is the same end state as "no journal entries" → Phase 2 reattach → `active`. Always add intermediate assertions when testing fallback behavior in convergent systems.

### Plan bugs correlate with task complexity

Tasks 1-3 had 6 mechanical fixes (imports, variables, typos). Task 4 had 2 genuine bugs (completed-phase over-restriction, controller test assertion) plus 3 mechanical fixes. The plan's code for Task 4 was the most complex (per-operation+phase branching), and that's where the genuine bugs concentrated.

### Ruff format diverges from plan code style

Same as Tasks 1-3: ruff reformats the plan's inline formatting to multi-line with trailing commas. Cosmetic only.

### Parallel Bash calls cancel on failure

Same learning from Tasks 1-3: run ruff format (which may fail) before pytest (which takes longer), not in parallel.

## User Preferences

**Execute-then-review workflow:** Consistent across all sessions. User explicitly requested in session 5: "Follow this pattern for the rest of the execution — execute task → pause and wait for review." This session followed the same pattern — Task 4 was executed, then user provided a structured review.

**Review format:** User provides structured reviews with: Findings (correctness issues with `::code-comment` annotations including priority, confidence, file, line range), Verification (commands run and results), Verdict (ship/ship-with-fixes/block).

**Adversarial review quality:** User's review caught a P2 non-discriminating test that both automated reviews (spec compliance + code quality) missed. The user's review is the highest-quality gate in the pipeline.

**Phase-boundary handoffs:** Consistent across all 6 sessions. User separates design → plan → review → execute into distinct sessions with handoff saves at each boundary.

## Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| 5 | 2026-04-01 | Execute Tasks 0-3 | `archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| **6** | **2026-04-01** | **Execute Task 4** | **This handoff** |
| 7 | Next | Merge Branch 1 + Tasks 5-6 | Not started |
