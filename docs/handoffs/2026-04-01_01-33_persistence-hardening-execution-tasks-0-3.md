---
date: 2026-04-01
time: "01:33"
created_at: "2026-04-01T05:33:33Z"
session_id: c6671b6a-a35e-4a4b-bba4-f10dded644db
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md
project: claude-code-tool-dev
branch: fix/persistence-replay-hardening
commit: 538c726a
title: "persistence hardening execution — Tasks 0-3"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/replay.py
  - packages/plugins/codex-collaboration/tests/test_replay.py
  - packages/plugins/codex-collaboration/server/turn_store.py
  - packages/plugins/codex-collaboration/tests/test_turn_store.py
  - packages/plugins/codex-collaboration/server/lineage_store.py
  - packages/plugins/codex-collaboration/tests/test_lineage_store.py
  - docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md
---

# persistence hardening execution — Tasks 0-3

## Goal

Execute the first 4 tasks (Task 0–Task 3) of the persistence hardening implementation plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`.

**Trigger:** Plan was merged to main at `80ae21f5` after 4 rounds of adversarial review (15 findings, 12 accepted, 1 partially accepted, 1 deferred). The user's prior handoff (session 4) marked the plan as ready for execution.

**Stakes:** The codex-collaboration plugin has three JSONL stores (TurnStore, LineageStore, Journal) with inline replay logic that crashes on malformed records. A single corrupted line takes down the entire replay for all records in a file. The plan introduces a shared replay helper (`replay_jsonl`) that diagnoses corruption instead of crashing, then migrates each store to use it.

**Success criteria:** (1) Shared replay helper with full corruption classification. (2) TurnStore migrated — malformed records diagnosed, not crashed (I2 fix). (3) LineageStore migrated — unknown ops diagnosed, schema validation for all ops (I4 fix). (4) All existing tests continue to pass. (5) `check_health()` available on migrated stores.

**Connection to project arc:** Fifth session in the persistence hardening chain: design (1) → plan (2) → review rounds 1-3 (3) → review round 4 + merge (4) → **execute Tasks 0-3** (5) → execute Tasks 4-6 (6). Branch 1 (`fix/persistence-replay-hardening`) is partially complete. Tasks 4 (Journal) remains, plus controller tests. Branch 2 (`chore/type-narrowing`, Tasks 5-6) follows after Branch 1 merges.

## Session Narrative

Session began by loading the prior handoff (`2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md`), which described the plan review session and set next steps as "execute the implementation plan." The user confirmed they wanted to start by reading the plan and checking the existing untracked files.

The prior session's agent had attempted Task 1 execution but hit an API `ConnectionRefused` error after 13 minutes, producing two untracked files (`replay.py` and `test_replay.py`). The first task was assessing the damage: comparing the agent's output against the plan's specification.

**Task 0 (design spec update):** Already committed at `bf2641af` by the prior session's agent before the API error. Verified by reading the git log — the commit exists on the `fix/persistence-replay-hardening` branch.

**Task 1 (shared replay module):** The agent's `replay.py` (141 lines) and `test_replay.py` (248 lines) were character-for-character identical to the plan's code blocks. No modifications needed. Ran tests — 23 passed (plan said 22; the plan miscounted — `test_unknown_operation_with_none_op` exists in the plan's code but wasn't included in the test count). Ruff flagged two issues: unused imports `ReplayDiagnostic` and `ReplayDiagnostics` (F401) — the plan's test code imported them but never referenced them directly. Removed the imports, formatted with `ruff format`, ran full suite (382 passed), committed at `311fea3f`.

**User review of Task 1** identified two residual gaps:
1. No test pinning that `UnknownOperation` counts as valid JSON for trailing-classification purposes (only `SchemaViolation` had this test at `test_replay.py:139`).
2. No test of a partial final line without a trailing newline — `_write_lines()` always writes `\n`, so the actual crash-tail scenario wasn't covered.

Added both tests: `test_unknown_operation_counts_as_valid_json_for_classification` and `test_partial_final_line_without_newline`. Both passed. Committed at `5f7edbde`. Suite at 384.

**Task 2 (TurnStore migration):** Wrote 5 failing tests in `TestReplayHardening`. Verified 3 failed against old code: `test_malformed_record_does_not_crash` confirmed the I2 bug (`KeyError: 'collaboration_id'` at `turn_store.py:70`), plus 2 `check_health` tests failed with `AttributeError`. Notably, `test_wrong_type_does_not_crash` and `test_bool_as_int_rejected` passed against old code because the old replay doesn't type-check — it just uses dict key access, which works as long as the key exists regardless of value type.

Replaced `turn_store.py` with plan's implementation: extracted `_turn_callback` function with per-field type validation using `type(x) is not int` (rejects bools — `type(True) is bool`, not `int`), replaced inline `_replay()` with `replay_jsonl()`, added `check_health()`. All 16 tests passed (11 existing + 5 new). Ruff required formatting fix on test file. Full suite: 389. Committed at `7cb2685f`.

**Task 3 (LineageStore migration):** The most complex migration — 3 operation types (`create`, `update_status`, `update_runtime`), each needing per-field schema validation plus literal validation for `status` and `capability_class`.

Wrote 12 failing tests. Spotted a plan bug during test writing: `test_update_runtime_wrong_type_codex_thread_id_skipped` asserted `== "thread-1"` but `_make_handle()` defaults `codex_thread_id` to `"thr-1"` (via `thread_id="thr-1"` parameter). Fixed the assertion to `"thr-1"`.

Verified 9 failed against old code, 3 passed (consistent with plan expectations — old code already silently drops unknown/missing ops and ignores extra fields). The failing tests confirmed: `TypeError` on missing create fields, wrong types accepted into handles without validation, no `check_health()` method, no literal validation.

Replaced `lineage_store.py` with plan's implementation: closure-captured callback factory `_make_lineage_callback`, per-field validation for all 3 ops, literal validation via `frozenset(get_args(HandleStatus))` and `frozenset(get_args(CapabilityProfile))`, `UnknownOperation` for unknown ops. Ruff flagged 4 unused `store` variables (F841) in tests that created `LineageStore` only for the `mkdir` side-effect — fixed by removing them and adding explicit `mkdir` where needed. All 28 tests passed. Full suite: 401. Committed at `538c726a`.

The user's reviews after Tasks 1, 2, and 3 all passed with no correctness findings.

## Decisions

### Fix plan's assertion bug in test_update_runtime_wrong_type_codex_thread_id_skipped

**Choice:** Changed assertion from `== "thread-1"` to `== "thr-1"` to match `_make_handle()` default.

**Driver:** The plan's `_make_handle` helper at `tests/test_lineage_store.py:18` uses `thread_id="thr-1"` which maps to `codex_thread_id="thr-1"`. The plan's test at line 921 asserted `"thread-1"` — a typo that would have caused a false test failure.

**Alternatives considered:**
- **Change `_make_handle()` default** — would fix the mismatch but changes a test helper used by 12+ existing tests, risking unintended side effects. Rejected as disproportionate.

**Trade-offs accepted:** Deviates from plan text. Documented in commit message.

**Confidence:** High (E2) — verified `_make_handle()` parameter mapping and existing test assertions that depend on `"thr-1"`.

**Reversibility:** High — single assertion change.

**Change trigger:** None — this corrects a plan bug, not a design choice.

### Remove unused imports and variables flagged by ruff

**Choice:** Fixed ruff F401 (unused imports in `test_replay.py`) and F841 (unused variables in `test_lineage_store.py`) rather than suppressing them.

**Driver:** The plan includes `uv run ruff check .` as a gate before each commit. The plan's code triggered ruff violations that would block the commit step.

**Alternatives considered:**
- **Add `# noqa` suppressions** — would preserve plan's code exactly but violates the plan's own intent of clean ruff gates. Rejected.
- **Skip ruff gate** — would violate plan's Round 4 addition (finding #4). Rejected.

**Trade-offs accepted:** Tests no longer import `ReplayDiagnostic`/`ReplayDiagnostics` (Task 1) and 4 test methods no longer create unused `LineageStore` instances (Task 3). No behavioral change.

**Confidence:** High (E1) — ruff violations are clear and fixes are mechanical.

**Reversibility:** High — imports/variables can be restored if needed.

**Change trigger:** If future tests need to reference `ReplayDiagnostic` or `ReplayDiagnostics` directly, re-add the imports.

### Add review-driven tests for replay helper coverage gaps

**Choice:** Added `test_unknown_operation_counts_as_valid_json_for_classification` and `test_partial_final_line_without_newline` to `test_replay.py` after user review identified gaps.

**Driver:** User's Task 1 review identified: (1) `UnknownOperation` lacked a combined trailing-classification test (only `SchemaViolation` had one), making it "the least-protected part of the lineage-facing contract"; (2) `_write_lines()` always writes `\n`, so the crash-tail scenario of a partial final line wasn't tested.

**Alternatives considered:**
- **Defer to Task 3/4 integration tests** — rejected because the gaps are in the shared helper's contract, not in store-specific behavior. The helper is the foundation for all subsequent migrations.

**Trade-offs accepted:** 2 extra tests (25 → 25 in the replay module, but these bring total from 23 to 25 with the plan counting discrepancy). Minimal overhead.

**Confidence:** High (E1) — both tests exercise documented behavior paths in `replay_jsonl`.

**Reversibility:** High — test-only changes.

**Change trigger:** None — these close genuine coverage gaps.

## Changes

### New files

| File | Lines | Purpose |
|------|-------|---------|
| `server/replay.py` | 141 | Shared JSONL replay helper with corruption classification |
| `tests/test_replay.py` | 246 | 25 tests covering basic replay, corruption classification, exception handling, diagnostics model |

### Modified files

| File | Purpose |
|------|---------|
| `server/turn_store.py` | Replaced inline `_replay()` with `replay_jsonl()` + `_turn_callback()`, added `check_health()` |
| `tests/test_turn_store.py` | Added `TestReplayHardening` (5 tests) |
| `server/lineage_store.py` | Replaced inline `_replay()`/`_apply_record()` with `replay_jsonl()` + closure callback factory, added literal validation, `check_health()` |
| `tests/test_lineage_store.py` | Added `TestReplayHardening` (12 tests) |
| `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` | Task 0: design spec update with review findings |

### Commit log (Branch 1 so far)

| Commit | Message | Tests |
|--------|---------|-------|
| `bf2641af` | docs: update design spec with review findings | — |
| `311fea3f` | feat: shared JSONL replay helper with corruption classification | 382 |
| `5f7edbde` | test: cover UnknownOperation trailing-classification and partial final line | 384 |
| `7cb2685f` | fix: migrate TurnStore to shared replay helper (I2) | 389 |
| `538c726a` | fix: migrate LineageStore to shared replay helper (I4) | 401 |

## Codebase Knowledge

### replay.py Architecture

`replay_jsonl(path, apply)` at `server/replay.py:58` — single-pass JSONL replay with deferred trailing-truncation classification:

1. Lines where `json.loads` fails → added to `pending_parse_failures` list
2. Non-dict JSON (arrays, strings, etc.) → immediate `schema_violation` diagnostic, but counts as valid JSON parse for trailing classification (updates `last_valid_json_line`)
3. Dict JSON → passed to `apply` callback. `SchemaViolation` and `UnknownOperation` are caught and diagnosed. Other exceptions propagate (programmer bugs).
4. After loop: pending parse failures classified based on `last_valid_json_line` — failures after it are `trailing_truncation`, before it are `mid_file_corruption`. If no valid JSON existed at all (`last_valid_json_line == 0`), all failures are `mid_file_corruption`.

Return type: `tuple[tuple[T, ...], ReplayDiagnostics]` — results from callback + diagnostics.

Key design: the callback signature is `Callable[[dict[str, Any]], T | None]`. Returning `None` means "valid record, no result to collect" — used by LineageStore's closure pattern where the callback mutates an external dict instead of returning values.

### Store Migration Pattern

All three stores follow the same migration pattern:

1. Extract a `_callback(record)` function that validates fields and returns structured data (or mutates captured state)
2. Replace inline replay loop with `replay_jsonl(path, callback)`
3. Add `check_health()` that replays with the same callback and returns `ReplayDiagnostics`
4. The callback raises `SchemaViolation` for wrong/missing fields, `UnknownOperation` for unknown ops

**TurnStore callback** (`_turn_callback` at `server/turn_store.py:17`): Validates 3 fields (`collaboration_id`: str, `turn_sequence`: int, `context_size`: int). Returns `tuple[str, int]` — `(key, context_size)`. Uses `type(x) is not int` to reject bools.

**LineageStore callback** (`_make_lineage_callback` at `server/lineage_store.py:41`): Closure factory — returns a callback that mutates a captured `dict[str, CollaborationHandle]`. Validates per-operation:
- `create`: 7 required string fields + 4 optional strings + 1 optional int (`resolved_turn_budget`) + literal validation for `status` (via `_VALID_STATUSES` frozenset) and `capability_class` (via `_VALID_CAPABILITIES` frozenset). Builds `CollaborationHandle` from known fields only (extra fields silently ignored per §Extra-Field Policy).
- `update_status`: validates `status` is string + literal validation
- `update_runtime`: validates `runtime_id` is string, optionally `codex_thread_id` is string
- Unknown ops: raises `UnknownOperation(op)`

### Literal Validation Strategy

`lineage_store.py:19-20`:
```python
_VALID_STATUSES: frozenset[str] = frozenset(get_args(HandleStatus))
_VALID_CAPABILITIES: frozenset[str] = frozenset(get_args(CapabilityProfile))
```

These derive valid values from the `Literal` type aliases in `models.py:10-12`. The frozensets update automatically when the type alias changes (via `get_args()`). Unknown literal values are `SchemaViolation`, not forward-compatible — this is intentionally tighter than the extra-field policy. Rationale at `lineage_store.py:64-73`: status drives controller behavior, capability_class determines execution model. A handle with an unknown status/capability would be semantically misinterpreted.

### _replace_handle Helper

`lineage_store.py:217` — `_replace_handle(handle, **changes)` works around frozen dataclass immutability by destructuring to dict, merging changes, and reconstructing. Used by `update_status` and `update_runtime` ops.

### Test Fixture: _make_handle

`tests/test_lineage_store.py:15-32` — factory with defaults:
- `collaboration_id="collab-1"`, `capability_class="advisory"`, `runtime_id="rt-1"`, `codex_thread_id="thr-1"` (note: parameter is `thread_id`, maps to `codex_thread_id`), `claude_session_id="sess-1"`, `repo_root="/repo"`, `status="active"`, `created_at="2026-03-28T00:00:00Z"`

### Type Checking Pattern: `type(x) is not int` vs `isinstance`

Both `_turn_callback` and `_make_lineage_callback` use `type(x) is not int` instead of `isinstance(x, int)`. This is deliberate: `isinstance(True, int)` returns `True` because `bool` is a subclass of `int` in Python. Using `type(x) is not int` correctly rejects booleans. Test: `test_bool_as_int_rejected` at `tests/test_turn_store.py:123`.

For strings, `isinstance(x, str)` is used because there's no analogous subclass issue.

### Pre-Migration vs Post-Migration Store Comparison

| Aspect | Pre-migration | Post-migration |
|--------|--------------|----------------|
| Replay loop | Inline in each store's `_replay()` | Shared `replay_jsonl()` in `replay.py` |
| Malformed JSON | `json.JSONDecodeError` caught, line skipped silently | Classified as `trailing_truncation` or `mid_file_corruption` |
| Missing fields | `KeyError` crashes entire replay (I2 bug) | `SchemaViolation` diagnosed, record skipped |
| Wrong field types | Silently accepted (e.g., `runtime_id=123`) | `SchemaViolation` diagnosed, record skipped |
| Unknown ops | Silently dropped (LineageStore) | `UnknownOperation` diagnosed, record skipped |
| Unknown literals | Silently accepted (e.g., `status="banana"`) | `SchemaViolation` diagnosed, record skipped |
| Diagnostics | None — no way to inspect file health | `check_health()` returns `ReplayDiagnostics` |
| Valid records | Lost if any record crashes replay | Always preserved — bad records skipped individually |

### TurnStore File Layout

`<plugin_data_path>/turns/<session_id>/turn_metadata.jsonl` — one JSON object per line, each with `collaboration_id` (str), `turn_sequence` (int), `context_size` (int). Key is `f"{collaboration_id}:{turn_sequence}"`. Last write wins on replay. Used by `dialogue.read()` to enrich turn responses with context window size.

### LineageStore File Layout

`<plugin_data_path>/lineage/<session_id>/handles.jsonl` — operation log with `op` field discriminating record type:
- `create`: full `CollaborationHandle` fields + `"op": "create"`
- `update_status`: `op`, `collaboration_id`, `status`
- `update_runtime`: `op`, `collaboration_id`, `runtime_id`, optionally `codex_thread_id`

Replayed into `dict[str, CollaborationHandle]` — last state per `collaboration_id` wins. `CollaborationHandle` is a frozen dataclass at `models.py` with 13 fields (8 required, 5 optional). The `cleanup()` method at `lineage_store.py:193` uses `shutil.rmtree` — the only store with session directory cleanup.

### Dependency Graph (Area Touched)

```
replay.py (shared helper — no dependencies)
  ↑ imported by:
  ├── turn_store.py (uses replay_jsonl, SchemaViolation)
  ├── lineage_store.py (uses replay_jsonl, SchemaViolation, UnknownOperation)
  └── [journal.py — Task 4, not yet migrated]
       ↑ imported by:
       └── dialogue.py (recovery coordinator at :435-601)

models.py (HandleStatus, CapabilityProfile Literal types)
  ↑ imported by:
  ├── lineage_store.py (get_args for literal validation frozensets)
  ├── dialogue.py (controller logic, filtering)
  └── [profiles.py — Task 5 target for type narrowing]
```

## Context

### Mental Model

This is a **defense-in-depth migration** — replacing crash-on-malformed with diagnose-and-continue at the persistence layer. The shared `replay_jsonl` helper is the single chokepoint: every JSONL store routes through it, and it guarantees that no store can crash on bad data. Each store's callback defines what "valid" means for that store's schema, but the corruption classification (trailing vs. mid-file) and exception handling are centralized.

The TDD structure (write failing tests → verify failure → implement → verify pass) provides evidence at each step that the migration is correct. The failing tests confirm the bug exists; the passing tests confirm the fix works; the full suite confirms no regressions.

### Project State

- **Branch:** `fix/persistence-replay-hardening` at `538c726a`
- **Tests:** 401 passing (359 baseline + 42 new)
- **Plan progress:** Tasks 0-3 complete, Tasks 4-6 remain
- **Plan counts vs actual:**
  - Plan says 22 replay tests → actual 25 (plan miscount + 2 review-driven additions)
  - Plan says 5 TurnStore tests → actual 5
  - Plan says 13 LineageStore tests → actual 12 (plan counted the existing test `_make_handle` lines; actual new tests in `TestReplayHardening` = 12)
  - Running total: 42 new tests added so far

### Review Statistics (This Session)

| Task | Review Result | Findings | Tests Added |
|------|--------------|----------|-------------|
| Task 0 + Task 1 | Pass | 2 residual gaps (fixed) | +25 (23 plan + 2 review) |
| Task 2 | Pass | 0 findings | +5 |
| Task 3 | Pass | 0 findings | +12 |

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| **5** | **2026-04-01** | **Execute Tasks 0-3** | **This handoff** |
| 6 | Next | Execute Tasks 4-6 | Not started |

## Learnings

### Plan code needs mechanical adjustment during execution

**Mechanism:** The plan contains ~1800 lines of code written from reading, not execution. Four review rounds (15 findings) reduced conceptual errors, but mechanical issues surfaced during execution: unused imports (ruff F401), unused variables (ruff F841), a test assertion typo (`"thread-1"` vs `"thr-1"`), and a test count miscount (22 vs 23).

**Evidence:** Task 1 — ruff flagged `ReplayDiagnostic` and `ReplayDiagnostics` as unused imports. Task 3 — ruff flagged 4 unused `store` variables, and the `"thread-1"` assertion didn't match `_make_handle()` default `"thr-1"`.

**Implication:** Plan execution should expect mechanical fixes. The TDD structure catches correctness issues (test failures), but linting and test assertion accuracy require manual attention. The plan's ruff gates (Round 4 addition) were valuable — without them, these issues would have been committed.

**Watch for:** Similar mechanical issues in Tasks 4-6. The Journal migration (Task 4) is the most complex — 10 tests + 2 controller tests with per-operation+phase conditional requirements.

### Review-driven test additions improve contract coverage

**Mechanism:** The user's post-task review identified gaps not in the plan's test suite: `UnknownOperation` trailing-classification behavior and partial-line-without-newline crash-tail scenario. Both are contract-level behaviors of the shared helper that downstream stores depend on.

**Evidence:** The plan had `test_schema_violation_counts_as_valid_json_for_classification` but no equivalent for `UnknownOperation`. The plan's `_write_lines()` helper always writes `\n`, masking the partial-line scenario.

**Implication:** The execute-then-review pattern (implemented as "execute task → pause and wait for review") catches gaps that the plan's author didn't anticipate. Future plan executions should maintain this pattern.

**Watch for:** Task 4 (Journal) has the most complex callback — per-operation+phase conditional requirements. The review there will likely surface additional coverage gaps.

### Parallel tool calls with failure risk should be sequential

**Mechanism:** When two Bash calls run in parallel and one fails (exit code != 0), the other is automatically cancelled (`Cancelled: parallel tool call ... errored`). This happened twice: ruff format check failed, cancelling the concurrent pytest run.

**Evidence:** `uv run ruff format --check` returned exit code 1 ("Would reformat"), cancelling the parallel `uv run pytest -q`.

**Implication:** Run ruff format (which may fail) before pytest (which takes longer), not in parallel. Or run ruff format (auto-fix) first, then verify + test together.

**Watch for:** Any pair of parallel commands where one might fail.

## Next Steps

### 1. Execute Task 4: Migrate Journal

**Dependencies:** Tasks 0-3 complete. Journal is the most complex store — 10 new tests + 2 controller tests.

**What to read first:** The plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`, lines 1192-1690 (Task 4 section). Also read current `server/journal.py` and `tests/test_journal.py`.

**Approach:** Same TDD pattern: write failing tests → verify failure → implement → verify pass → lint → commit. Then write the 2 controller-level tests (separate commit per plan).

**Key complexity:** Journal has per-operation+phase conditional requirements (the Round 1 P1 finding). The callback must validate not just field presence/type but also operation-specific required fields that depend on the journal phase. The recovery coordinator at `dialogue.py:435-601` depends on these fields being present and correctly typed.

**Acceptance criteria:** All existing + new tests pass. `check_health()` available on Journal. Per-operation+phase validation catches the conditional requirement violations that Round 1 identified. Full suite regression-free.

### 2. After Task 4: Controller-level corruption tests

**Dependencies:** Task 4 implementation complete.

**What to read first:** Plan lines 1600-1690 (controller test section within Task 4).

**Approach:** These test that `dialogue.read()` works correctly when stores contain corrupted records — the integration layer.

### 3. After Branch 1: Tasks 5-6 on chore/type-narrowing

**Dependencies:** Branch 1 merged to main.

**What to read first:** Plan lines 1691-2062 (Tasks 5-6).

**Approach:** Create `chore/type-narrowing` from main after merging `fix/persistence-replay-hardening`. Task 5 (profiles, 14 tests) and Task 6 (models, 1 test).

## In Progress

Clean stopping point. Tasks 0-3 are committed on `fix/persistence-replay-hardening`. No work in flight. No uncommitted files. The branch has 5 commits ahead of main.

Next task is Task 4 (Journal migration), which is the most complex single task in the plan.

## Open Questions

### Plan test count discrepancies

The plan's test counts don't match actual:
- Plan says 22 replay tests → actual 25 (plan miscounted, plus 2 review-driven additions)
- Plan says 13 LineageStore tests → actual 12 in TestReplayHardening

These are plan counting errors, not implementation deviations. The plan's cumulative count of 67 new tests across all tasks will need adjustment at completion.

### Journal per-operation+phase validation complexity

Task 4's callback must enforce conditional requirements that depend on both the operation type and the journal phase. This is the Round 1 P1 finding that drove the most plan complexity. The actual implementation hasn't been tested yet.

### AC6 analytics emission (deferred)

Still deferred from prior sessions. Actual roadmap work in packet 2b (`delivery.md:255`). Not addressed in this session. Ticket T-20260330-03 tracks it.

## Risks

### Journal migration is the highest-complexity task

Task 4 has 10 tests + 2 controller tests, per-operation+phase conditional requirements, and the recovery coordinator (`dialogue.py:435-601`) depends on correct field presence/types. The plan's code for Task 4 hasn't been tested — it's the most likely place for plan-vs-reality divergence.

### Full-file replacement steps remain brittle

Round 4 finding #5 (deferred). Task 4 replaces `journal.py` entirely. If the file has changed since the plan was written, the replacement could clobber changes. Mitigated by: we're on a feature branch, TDD catches correctness issues.

### Plan code may need more mechanical fixes

Tasks 1-3 required 6 mechanical fixes (2 unused imports, 4 unused variables, 1 assertion typo). Task 4 is larger — expect similar or more adjustments.

## References

| What | Where |
|------|-------|
| Implementation plan (final) | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| Round 4 adversarial review | `docs/reviews/2026-03-31-persistence-hardening-and-type-narrowing-adversarial-review.md` |
| Shared replay helper | `packages/plugins/codex-collaboration/server/replay.py` |
| TurnStore (migrated) | `packages/plugins/codex-collaboration/server/turn_store.py` |
| LineageStore (migrated) | `packages/plugins/codex-collaboration/server/lineage_store.py` |
| Journal (not yet migrated) | `packages/plugins/codex-collaboration/server/journal.py` |
| Recovery coordinator | `packages/plugins/codex-collaboration/server/dialogue.py:435-601` |
| HandleStatus/CapabilityProfile types | `packages/plugins/codex-collaboration/server/models.py:10-12` |
| Profile resolver | `packages/plugins/codex-collaboration/server/profiles.py` |
| Prior handoff (round 4) | `docs/handoffs/archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |

## Gotchas

### Plan test counts are approximate

The plan says 22 replay tests, 5 TurnStore tests, 13 LineageStore tests, but actual counts are 25, 5, 12. The discrepancies are: plan miscounted replay tests (23 in plan code, counted as 22), 2 review-driven additions brought it to 25, and plan counted 13 for LineageStore but actual `TestReplayHardening` has 12 test methods. Cumulative plan count of 67 needs recalculation at end.

### Ruff format diverges from plan code style

The plan's Python code uses inline list formatting (e.g., `_write_lines(path, ["corrupt1", json.dumps({"a": 1}), "corrupt2"])`) but ruff reformats to multi-line with trailing commas. This is cosmetic — no behavioral difference — but means the committed code won't match the plan's code blocks character-for-character after Task 1.

### _make_handle parameter name mismatch

`_make_handle(thread_id="thr-1")` maps to `codex_thread_id="thr-1"` in the dataclass. The plan's Task 3 test had an assertion using `"thread-1"` instead of `"thr-1"` — likely confusing the parameter name (`thread_id`) with a default value. Fixed in this session.

### Parallel Bash calls cancel on failure

When two Bash tool calls run in parallel and one returns non-zero exit code, the other is automatically cancelled. This bit us twice with `ruff format --check` (exit 1) cancelling concurrent `pytest`. Pattern: run ruff format (fix), then verify + test.

## User Preferences

**Execute-then-review workflow:** User explicitly requested: "Follow this pattern for the rest of the execution — execute task → pause and wait for review." Each task was executed, then the user provided a structured review (findings, residual gaps/risk, verification) before proceeding.

**Review format:** User provides structured reviews with: Findings (correctness issues), Residual Gaps/Risk (known but non-blocking), Verification (commands run and results). No findings means "proceed."

**Plan deviation documentation:** User did not object to mechanical fixes (ruff, assertion typo) but these were documented in commit messages. The pattern suggests: fix mechanical issues, document them, proceed.

**Phase-boundary handoffs:** Consistent across all 5 sessions. User separates design → plan → review → execute into distinct sessions with handoff saves at each boundary. This session was the first execution session in the chain.
