---
date: 2026-04-01
time: "13:38"
created_at: "2026-04-01T17:38:31Z"
session_id: 6fd5a131-12f7-4103-bb13-96533e9e42b0
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md
project: claude-code-tool-dev
branch: main
commit: 7e0d866e
title: "AC6 analytics emission plan"
type: handoff
files:
  - docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/tests/test_control_plane.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
---

# AC6 analytics emission plan

## Goal

Produce a review-clean implementation plan for AC6 analytics emission (ticket T-20260330-03) that a worker agent can execute task-by-task without design decisions or re-exploration.

**Trigger:** Session 7 of the persistence hardening chain landed all 6 tasks on main. AC6 analytics emission was identified as the next work item — the only outstanding acceptance criterion in T-20260330-03's analytics scope.

**Stakes:** Medium — AC6 is the last analytics-related acceptance criterion before T-20260330-04 and T-20260330-05 can proceed. The plan itself is the deliverable; no implementation code was written this session.

**Success criteria:** (1) Plan covers all emission sites. (2) Plan passes user review with no P1/P2 findings. (3) Plan uses correct API names, field types, and test patterns. (4) Plan is ready for subagent-driven or inline execution.

**Connection to project arc:** Eighth session in the codex-collaboration build chain. Sessions 1-7 completed persistence hardening. This session transitions to the safety substrate layer (packet 2b of the delivery spec at `docs/superpowers/specs/codex-collaboration/delivery.md:248`).

## Session Narrative

Session began by loading the persistence hardening handoff (`2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md`). The handoff's next step was AC6 analytics emission (ticket T-20260330-03). The user confirmed readiness to proceed.

**Scoping phase — user pre-analysis.** The user provided a detailed readout before I began, citing specific file:line locations across the ticket, delivery spec, and codebase. Key insight from the user's readout: AC6 is almost certainly not "port `emit_analytics.py`" — cross-model's 800-line script exists because it parses free-form outputs, while codex-collaboration already has structured consult and dialogue results. The semantic carryover is deterministic append-only emission, not parser reuse.

The user presented three hypotheses ranked by likelihood: (A) separate analytics path with shared journal helper, (B) separate path with direct controller emission, (C) expand the existing AuditEvent. The user recommended A and asked me to validate.

**Validation phase.** I read six files to confirm the user's analysis: `models.py` (AuditEvent shape), `journal.py` (append_audit_event pattern), `control_plane.py` (consult emission site), `dialogue.py` (three dialogue emission sites), and both test files (existing audit assertions and test patterns). I also read the first 50 lines of `emit_analytics.py` to confirm the parsing vs. structured contrast.

Key validation findings:
- Four emission sites confirmed: consult success (`control_plane.py:192`), normal reply (`dialogue.py:307`), startup recovery (`dialogue.py:592`), best-effort repair (`dialogue.py:689`)
- All sites share the same data: `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, action type
- Dialogue sites additionally have `turn_sequence`, `resolved_root`, `runtime.policy_fingerprint`
- Recovery/repair sites guard with `if turn_id is not None and entry.runtime_id is not None`
- The ticket explicitly says "Analytics must be rebuilt on codex-collaboration's audit vocabulary" and excludes "Porting cross-model JSONL analytics payloads as-is"

Hypothesis A validated. The user confirmed scope: success-only, with the `OutcomeRecord` shape designed to accommodate a future `status` field.

**Plan writing phase.** Wrote the initial 8-task plan to `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md`. Tasks: (1) OutcomeRecord model, (2) journal persistence path, (3) consult emission, (4) dialogue normal reply, (5) recovery path, (6) best-effort repair, (7) shape consistency test, (8) lint and verification.

**Review round 1 — user found 5 findings (2 P1, 2 P2, 1 P3):**

1. [P1] `OutcomeRecord.context_size` defined as `int` but recovery entries have `int | None` — plan coerced missing values to `0` via `if x is not None else 0`, fabricating data. The user cited existing test fixtures at `test_dialogue.py:428` and `:466` that exercise dispatched entries without `context_size`, proving the `None` case is real, not theoretical. Fix: made `context_size: int | None` on `OutcomeRecord` and passed through directly without coercion.

2. [P1] Plan called `controller.recover_unresolved()` which doesn't exist — I inferred the name from `journal.list_unresolved()` but the actual method is `recover_pending_operations()` at `dialogue.py:424`. The user cited the real entry point and the existing test patterns at `test_dialogue.py:320` that use the correct name. Fix: replaced all four occurrences with `recover_pending_operations()`.

3. [P2] UUID iterator exhaustion — plan only patched one of five affected tests in `test_control_plane.py`. The user identified four more tests at lines 337, 365, 402, and 438 with finite iterators that reach the consult success path. Fix: added detailed per-test consumption analysis (5a-5e) accounting for which tests trigger success paths (consuming outcome UUIDs) vs. failure paths (not consuming). The parse-failure test (`test_codex_consult_invalidates_cached_runtime_after_parse_failure`) required careful analysis because `parse_consult_response()` runs before emission in `control_plane.py` — so the first (failing) consult consumes only `runtime-1`, not collab/event/outcome UUIDs.

4. [P2] Dialogue outcomes omitted `repo_root` and `policy_fingerprint` even though both are available at all three dialogue emission sites. The user cited `dialogue.py:212` (reply has `resolved_root` and `runtime.policy_fingerprint`), `dialogue.py:540` (recovery bootstraps runtime), and `dialogue.py:639` (repair bootstraps runtime). Fix: added both fields to all three dialogue emission code blocks, updated test assertions from `is None` to `== str(tmp_path.resolve())` and `is not None`.

5. [P3] Shape consistency test (Task 7) claimed to cover 4 paths (consult, normal reply, recovery, repair) but only constructed 3 — best-effort repair was never invoked. The `len(outcomes) >= 3` assertion would pass even with repair missing. Fix: added a fourth test section that creates a dialogue stack, marks the handle as unknown, writes an unresolved intent entry, calls `_best_effort_repair_turn()`, and asserts `len(outcomes) >= 4`.

**Review round 2 — user found 2 findings (1 P2, 1 P3):**

1. [P2] Task 4 lacked parse-failure durability coverage. The existing test `TestCommittedTurnParseError.test_completes_journal_writes_store_and_emits_audit` at `test_dialogue.py:1300` locks the pre-parse invariant: it verifies that journal completion, TurnStore writes, and audit emission all happen before `parse_consult_response()`. Since `append_outcome()` is placed in the same pre-parse block, the plan should extend this test to assert outcome emission too — otherwise, a future refactor that moves outcome emission below parsing would silently break the durability guarantee without failing any AC6 test. Fix: added steps 5-6 to Task 4, appending outcome assertions to the existing parse-failure test.

2. [P3] Task 8 verification step was a false green. The proposed command `uv run python -c "from server.journal import OperationJournal; j = OperationJournal(); print(j._analytics_dir, j._outcomes_path)"` only instantiates the journal and prints attributes. But `__init__` creates directories, not files — `outcomes.jsonl` only appears after `append_outcome()` is called. This check would pass even if `append_outcome()` was completely broken. Fix: replaced with an actual smoke test that calls `append_outcome()`, writes to a temp dir, and reads the record back.

**Review round 3 — user found 3 findings (all P3, plan hygiene):**

1. [P3] Verification checklist at plan line 1299 still said "`analytics/outcomes.jsonl` created on journal init" — directly contradicting the architecture where init creates only the directory and the file appears on first append. This was the same false-green assumption the user caught in round 2, now lingering in the checklist. Fix: changed to "`analytics/` directory created on journal init; `outcomes.jsonl` created on first append."

2. [P3] UUID guidance section 5d contained draft reasoning: it first claimed parse failure happens AFTER emission, then immediately corrected itself. The final conclusion was right, but leaving the wrong intermediate in a published plan makes it harder to trust and easier to follow incorrectly. Fix: collapsed to the correct analysis only.

3. [P3] Task 1 Step 4 still said "4 passed" but the test class now has 5 tests (the `test_context_size_nullable` test was added during the P1 fix for nullable `context_size`). Fix: updated to "5 passed."

**Session ended** with the plan review-clean and ready for execution. No implementation code was written — the plan is the deliverable.

## Decisions

### Separate OutcomeRecord from AuditEvent

**Choice:** Create a new `OutcomeRecord` frozen dataclass for analytics, persisted to `analytics/outcomes.jsonl`, rather than expanding the existing `AuditEvent` or reusing `audit/events.jsonl`.

**Driver:** The ticket explicitly states "Analytics must be rebuilt on codex-collaboration's audit vocabulary rather than copying cross-model event shapes" at `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md:74`. The `AuditEvent` comment at `models.py:154` says "R1 only emits consult events" and marks it as intentionally minimal. The ticket verification criterion at line 105 says "Emit and inspect a consult outcome artifact in the new analytics path" — the word "new" implies a separate path.

**Alternatives considered:**
- **Expand AuditEvent** — would couple trust-boundary audit records with analytics metrics. Rejected because the ticket's "new analytics path" wording argues against it, and `AuditEvent` has an intentional-minimality comment that warns against adding fields. The user confirmed: "I would reject this path unless the docs clearly force it."
- **Direct emission from controllers without shared helper** — would work but dialogue has three distinct success sites, creating shape divergence risk. Rejected because the user identified this as "plausible but weaker" in their initial hypothesis ranking.

**Trade-offs accepted:** Two JSONL files instead of one. Slight code duplication between `append_audit_event()` and `append_outcome()`. Accepted because the separation preserves clean trust-boundary semantics for audit and clean analytics semantics for outcomes.

**Confidence:** High (E2) — validated against ticket wording, codebase comments, and user analysis.

**Reversibility:** High — `OutcomeRecord` is a new type with no dependents. Can be merged into `AuditEvent` later if needed.

**Change trigger:** If downstream analytics consumers require audit+outcome correlation in a single file, merging would be reconsidered. Currently no consumers exist.

### Success-only outcome emission

**Choice:** Emit outcome records only on successful consult/dialogue completion, not on failures.

**Driver:** The ticket verification at line 105 says "Emit and inspect a consult outcome artifact" — implies a positive outcome artifact. The current code paths only produce durable success-state data at the three dialogue emission sites and the consult emission site. Failure paths raise exceptions before reaching emission.

**Alternatives considered:**
- **Include failure outcomes** — would require defining what a "failure outcome" looks like for each emission site. Rejected because the ticket doesn't require it, the current code doesn't emit audit events on failure either, and adding failure semantics would expand scope.

**Trade-offs accepted:** Analytics can only measure success rates indirectly (via absence). Accepted because the `OutcomeRecord` shape includes an `outcome_type` field that could later accommodate a `status` discriminator without schema changes.

**Confidence:** High (E1) — based on ticket wording. No counter-evidence found in spec or codebase.

**Reversibility:** High — adding failure emission later requires only new emission sites, not schema changes.

**Change trigger:** If the ticket owner or downstream analytics work explicitly requires failure tracking.

### Nullable context_size on OutcomeRecord

**Choice:** Define `OutcomeRecord.context_size` as `int | None` rather than `int`.

**Driver:** User's P1 review finding. The source data (`OperationJournalEntry.context_size` at `models.py:249`) is `int | None`. Recovery/repair paths may encounter entries without `context_size`. The initial plan coerced `None` to `0` via `if x is not None else 0`, which fabricates data — a `0` context_size is indistinguishable from "unknown" in the analytics output.

**Alternatives considered:**
- **Coerce to 0** — original plan approach. Rejected because it fabricates analytics data: "AC6 will silently write false analytics instead of preserving 'unknown' or surfacing an integrity gap" (user's review).
- **Skip outcome emission when context_size is None** — would lose the outcome record entirely for recovered turns. Rejected because the outcome (turn confirmed) is still analytically valuable even without context_size.

**Trade-offs accepted:** Downstream consumers must handle `null` context_size. Accepted because preserving "unknown" is more honest than fabricating a metric.

**Confidence:** High (E2) — user identified the coercion as a P1 finding with evidence from existing test fixtures (`test_dialogue.py:428`, `:466`) that exercise entries without `context_size`.

**Reversibility:** N/A — this is a type design decision baked into the schema.

**Change trigger:** None — nullable is strictly more expressive than non-nullable.

### Carry repo_root and policy_fingerprint through all dialogue outcomes

**Choice:** Include `repo_root` and `policy_fingerprint` in dialogue outcome records, not just consult outcomes.

**Driver:** User's P2 review finding. Both values are structurally available at all three dialogue emission sites: `resolved_root` and `runtime.policy_fingerprint` in `reply()` at `dialogue.py:212`, `entry.repo_root` and bootstrapped `runtime.policy_fingerprint` in recovery at `dialogue.py:541`, `intent_entry.repo_root` and bootstrapped `runtime.policy_fingerprint` in repair at `dialogue.py:639`.

**Alternatives considered:**
- **Omit for dialogue, include only for consult** — original plan approach. Rejected because the user identified this as "throwing away available analytics dimensions for no technical reason" — both values are in scope at every emission site.

**Trade-offs accepted:** None — this is strictly additive data capture with no cost.

**Confidence:** High (E2) — verified data availability at all three dialogue emission sites in the source code.

**Reversibility:** N/A — can always stop populating these fields; downstream sees them as optional.

**Change trigger:** None.

## Changes

### Created files

| File | Purpose |
|------|---------|
| `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` | 8-task TDD implementation plan for AC6 analytics emission |

**Plan structure summary:**

| Task | What | Source Files | Test Files |
|------|------|-------------|------------|
| 1 | `OutcomeRecord` frozen dataclass | `models.py` | `test_outcome_record.py` (5 tests) |
| 2 | `append_outcome()` + `analytics/` dir | `journal.py` | `test_outcome_record.py` (+3 tests) |
| 3 | Consult emission + negative test | `control_plane.py` | `test_control_plane.py` (+2 tests, 5 iterator patches) |
| 4 | Normal reply + parse-failure durability | `dialogue.py` | `test_dialogue.py` (+2 tests) |
| 5 | Recovery confirmed + negative | `dialogue.py` | `test_dialogue.py` (+2 tests) |
| 6 | Best-effort repair + negative | `dialogue.py` | `test_dialogue.py` (+2 tests) |
| 7 | Shape consistency (all 4 paths) | — | `test_outcome_shape_consistency.py` (1 test) |
| 8 | Lint, format, smoke verification | All 4 source files | — |

### No modified files

No implementation code was written this session. The plan is the sole artifact.

## Codebase Knowledge

### Emission Site Architecture

Four code paths emit `AuditEvent` on success. Each will also emit `OutcomeRecord` in the plan:

| Site | File:Line | Action | Guard | Data Available |
|------|-----------|--------|-------|----------------|
| Consult success | `control_plane.py:192` | `"consult"` | Always (success path) | `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `policy_fingerprint`, `repo_root` |
| Normal reply | `dialogue.py:307` | `"dialogue_turn"` | Always (normal success) | `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `turn_sequence`, `resolved_root`, `runtime.policy_fingerprint` |
| Recovery confirmed | `dialogue.py:592` | `"dialogue_turn"` | `turn_id is not None and entry.runtime_id is not None` | Same as above via `entry` fields + bootstrapped runtime |
| Best-effort repair | `dialogue.py:689` | `"dialogue_turn"` | `turn_id is not None and intent_entry.runtime_id is not None` | Same as above via `intent_entry` fields + bootstrapped runtime |

### AuditEvent Shape (Intentionally Minimal)

`models.py:141-157` — frozen dataclass with 9 fields. Comment at line 154: "R1 only emits consult events. The spec's delegation-oriented audit fields such as job_id, request_id, artifact_hash, decision, and causal_parent are deferred until those flows exist in code." The `extra` dict serves as an escape hatch but is used sparingly (only `repo_root` for consult).

### Journal Persistence Pattern

`journal.py:155-159` — `append_audit_event()` is a simple JSONL append: `json.dumps(asdict(event), sort_keys=True) + "\n"`. No fsync (unlike `write_phase` which fsyncs for crash recovery). The `append_outcome()` method follows the same pattern.

Storage layout:
- `self._plugin_data_path / "audit" / "events.jsonl"` — existing audit log
- `self._plugin_data_path / "analytics" / "outcomes.jsonl"` — new outcomes log (plan Task 2)
- `self._journal_dir / "operations" / f"{session_id}.jsonl"` — phased journal (per-session)

### Test Infrastructure

- `FakeRuntimeSession` at `test_control_plane.py:22-56` — shared test double for all runtime operations
- `_build_dialogue_stack()` at `test_dialogue.py:22-56` — wires up full dialogue stack with test doubles
- UUID iterators: tests use finite `iter(("uuid-1", "uuid-2", ...)).__next__` for deterministic UUID assignment. Adding emission sites that call `self._uuid_factory()` exhausts these iterators — five tests in `test_control_plane.py` needed patching.
- Audit assertions: read `plugin_data / "audit" / "events.jsonl"`, parse lines, filter by `action`

### Dialogue Controller Recovery Architecture

The dialogue controller has two independent recovery paths that both reach audit/outcome emission:

**Startup recovery** (`recover_pending_operations()` at `dialogue.py:424`): Called at session start. Replays the operations journal (`list_unresolved()`), finds entries whose terminal phase is not `completed`, and processes each. For `turn_dispatch` entries, calls `_recover_turn_dispatch()` at `dialogue.py:517`. Recovery verifies via `thread/read` whether the turn actually completed on Codex's side. If confirmed (`completed_count >= entry.turn_sequence`), it repairs metadata, resolves the journal entry, and emits audit + outcome. If unconfirmed, marks the handle as `unknown` — no audit or outcome emitted.

**Best-effort repair** (`_best_effort_repair_turn()` at `dialogue.py:624`): Called inline from `reply()`'s exception path (line 264). When `run_turn()` raises, reply marks the handle as `unknown` and calls this method. It bootstraps a fresh runtime, inspects the thread via `thread/read`, and if the turn actually completed (transport failure after Codex committed), repairs metadata and emits audit + outcome. All exceptions are swallowed — this is cleanup, not a retry.

Both paths share the same confirmation logic: extract `turn_id` from `completed_turns[turn_index].get("id")`, guard emission with `if turn_id is not None and entry.runtime_id is not None`. The guard prevents emission when the turn can't be confirmed or when the entry lacks a runtime_id (data-quality gap from older writers).

### Parse-Emission Ordering in control_plane.py

`control_plane.py:182-206` — `parse_consult_response()` runs BEFORE audit/outcome emission. This means parse failures (malformed agent response) raise before any audit/outcome is written. Contrast with `dialogue.py:284-330` where audit/outcome emission runs BEFORE `parse_consult_response()` — parse failures there produce `CommittedTurnParseError` because durable state (journal + store + audit + outcome) is already committed.

This ordering difference matters for UUID consumption analysis in tests: consult parse-failure tests consume fewer UUIDs than dialogue parse-failure tests.

### Cross-Model emit_analytics.py Contrast

`packages/plugins/cross-model/scripts/emit_analytics.py` (800 lines) is a **parser** — it takes free-form synthesis text, regex-extracts convergence codes, seed confidence, mode sources, etc. It imports from `event_log.py` (shared append), `event_schema.py` (schema version, valid value sets), and uses TypeGuard patterns for validation. None of this complexity applies to codex-collaboration, which has structured results from the start.

### OperationJournalEntry Field Nullability

`models.py:228-250` — `context_size` is `int | None` on `OperationJournalEntry`. It is set at the intent phase for `turn_dispatch` operations (pre-dispatch), but the type allows `None` for other operation types. Recovery fixtures in `test_dialogue.py:428` and `:466` exercise entries without `context_size`. This nullability is why `OutcomeRecord.context_size` must also be `int | None`.

### Ruff Formatting Divergence

The codex-collaboration plugin has ~28 files where ruff's formatting differs from existing style. Running `ruff format .` reformats all of them. The plan's Task 8 explicitly warns: "Format only target files. Never `ruff format .` in this plugin directory." This is documented in prior handoffs and remains a pre-existing condition.

## Context

### Mental Model

This session was **plan authoring with adversarial review** — no implementation code was written. The user provided pre-analysis with hypotheses, I validated against the codebase, wrote the plan, and the user reviewed it through three rounds. The review rounds progressively shifted from design-level findings (P1: data fabrication, wrong API names) to plan-hygiene (P3: stale pass counts, draft reasoning left in).

The key insight from the user's initial readout: AC6 analytics is a **structured append** problem, not a **parsing** problem. Cross-model's `emit_analytics.py` exists because Codex returns free-form text that must be parsed into structured analytics events. Codex-collaboration already has structured results (`ConsultResult`, `DialogueReplyResult`, `TurnExecutionResult`) at every emission site — the outcome record is a deterministic projection of data that's already in scope.

### Project State

- **Branch:** `main` at `7e0d866e`
- **Tests:** 430 passing (from persistence hardening chain)
- **Untracked files:** `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` (the plan)
- **Plan status:** Review-clean after 3 rounds (5 findings → 2 findings → 3 findings, all resolved)
- **Plan scope:** 8 tasks, ~16 new tests, 4 modified source files, 3 new test files

### Test Count Summary (Planned)

| Task | New Tests | Purpose |
|------|-----------|---------|
| Task 1 | 5 | OutcomeRecord model (fields, frozen, nullable, roundtrip) |
| Task 2 | 3 | Journal persistence (create, append multiple, directory init) |
| Task 3 | 2 | Consult emission (success + failure negative) |
| Task 4 | 2 | Dialogue reply (success + parse-failure durability) |
| Task 5 | 2 | Recovery (confirmed + unconfirmed negative) |
| Task 6 | 2 | Best-effort repair (confirmed + unconfirmed negative) |
| Task 7 | 1 | Shape consistency (all 4 paths same keys) |
| **Total** | **~17** | |

## Learnings

### `or` semantics coercion creates data fabrication in analytics

**Mechanism:** When a plan uses `x if x is not None else 0` to coerce a nullable integer to a non-nullable type, the resulting `0` is indistinguishable from a genuine zero value in the output. For analytics, this is data fabrication — a consumer cannot tell whether `context_size: 0` means "zero bytes of context" or "context size unknown."

**Evidence:** User's P1 review finding. The source field `OperationJournalEntry.context_size` is `int | None` (`models.py:249`). Existing recovery test fixtures at `test_dialogue.py:428` and `:466` exercise entries without `context_size`. If the plan had been executed as written, outcome records from recovered turns would silently report `context_size: 0`.

**Implication:** When projecting fields from a source type with broader nullability to an output type, preserve the nullability rather than coercing. The output type should mirror the source type's precision. This applies to any analytics or metrics system where "unknown" and "zero" have different semantic meanings.

**Watch for:** Any `x or default` or `x if x is not None else sentinel` pattern in analytics emission code. Ask: would a consumer interpret the sentinel differently from a genuine value?

### Plan review catches API name drift between plan and codebase

**Mechanism:** The plan called `controller.recover_unresolved()` based on method-name inference from the journal's `list_unresolved()` method. The actual method is `recover_pending_operations()` at `dialogue.py:424`. A worker agent following the plan literally would fail at test execution time.

**Evidence:** User's P1 review finding. Verified by grepping: `def recover_` in `dialogue.py` returns `recover_startup` (line 345) and `recover_pending_operations` (line 424).

**Implication:** Plans that reference API names should verify them against the actual codebase, not infer from related method names. The cost of a `grep` during planning is trivial; the cost of a worker agent failing and needing diagnosis is high.

**Watch for:** Any plan that references a method, function, or class by name — verify it exists in the codebase before publishing.

### UUID iterator exhaustion is a hidden regression class in this codebase

**Mechanism:** Tests use finite `iter((...,)).__next__` for deterministic UUID assignment. Adding a new `self._uuid_factory()` call to a success path (like outcome emission) exhausts these iterators in tests that don't account for the new call. The result is `StopIteration` at runtime, which may surface as an opaque failure unrelated to the feature being implemented.

**Evidence:** User's P2 review finding. Five tests in `test_control_plane.py` (lines 256, 337, 366, 402, 438) used finite iterators that would exhaust after adding outcome emission. The plan initially only patched one of them.

**Implication:** When adding any new `uuid_factory()` call to a code path exercised by tests, audit ALL tests that reach that path for finite UUID iterators. The analysis requires understanding which tests trigger the success path (consuming UUIDs) vs. failure paths (not consuming).

**Watch for:** Any change that adds a new `self._uuid_factory()` call in `control_plane.py` or `dialogue.py`. Grep for `uuid_factory=iter(` in the test files.

## Next Steps

### 1. Execute the AC6 analytics emission plan

**Dependencies:** None — plan is review-clean and ready.

**What to read first:** `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` — the complete 8-task plan.

**Approach:** Use subagent-driven development (recommended) or inline execution. The plan includes complete code for every step, exact test commands with expected output, and commit messages.

**Acceptance criteria:** All 8 tasks complete, all tests passing (430 existing + ~17 new), lint clean on target files, `analytics/outcomes.jsonl` created on first append, all 4 emission sites covered with same JSON key set.

**Potential obstacles:** UUID iterator exhaustion (plan patches all 5 known tests, but new tests added between plan creation and execution could introduce more). Ruff formatting artifacts (plan warns to format only target files).

### 2. Commit the plan (pre-execution)

**Dependencies:** None.

**What to read first:** N/A — plan is already written.

**Approach:** Create a feature branch, commit the plan, then execute tasks on that branch. Or commit on main if the plan is considered documentation.

**Acceptance criteria:** Plan committed and visible in git history.

## In Progress

Clean stopping point. The plan is written and review-clean. No implementation code was written. No work in flight. The only untracked file is the plan itself.

## Open Questions

### Should the plan be committed before or during execution?

The plan is untracked (`docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md`). It could be committed to main as documentation before creating a feature branch for execution, or committed as part of the first task's feature branch. Prior sessions committed plans separately, but this is a convention question, not a technical one.

### Static type checker configuration

Carried forward from session 7: the codex-collaboration package has no pyright/mypy config checked in. The new `OutcomeRecord` with `Literal["consult", "dialogue_turn"]` would benefit from static type checking at import sites. Not blocking for AC6, but relevant for ongoing type safety.

## Risks

### UUID iterator exhaustion in tests not yet written

If new tests are added to `test_control_plane.py` between plan creation and plan execution that use finite UUID iterators on consult success paths, they will fail when outcome emission is added. Mitigated by: the plan's Task 3 step 5 explains the consumption analysis pattern so the worker can apply it to new tests.

### Ruff formatting artifacts may cause accidental commits

Pre-existing risk from the persistence hardening chain. The plan's Task 8 explicitly warns to format only target files. But a worker unfamiliar with this gotcha might run `ruff format .` and stage 28 formatting changes alongside the feature.

## References

| What | Where |
|------|-------|
| Implementation plan (review-clean) | `docs/superpowers/plans/2026-04-01-ac6-analytics-emission.md` |
| Ticket (AC6 scope) | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` |
| Delivery spec (packet 2b) | `docs/superpowers/specs/codex-collaboration/delivery.md:248` |
| AuditEvent (trust-boundary record) | `packages/plugins/codex-collaboration/server/models.py:141-157` |
| OperationJournal (persistence) | `packages/plugins/codex-collaboration/server/journal.py:110-250` |
| Consult emission site | `packages/plugins/codex-collaboration/server/control_plane.py:188-205` |
| Dialogue emission sites | `packages/plugins/codex-collaboration/server/dialogue.py:304-318`, `:592-604`, `:689-701` |
| Cross-model emit_analytics.py (contrast) | `packages/plugins/cross-model/scripts/emit_analytics.py` |
| Prior handoff (persistence hardening) | `docs/handoffs/archive/2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md` |

## Gotchas

### Parse-emission ordering differs between consult and dialogue

In `control_plane.py`, `parse_consult_response()` (line 182) runs BEFORE audit/outcome emission (lines 192+). In `dialogue.py`, audit/outcome emission (lines 307+) runs BEFORE `parse_consult_response()` (line 323). This means consult parse failures don't produce audit/outcome records, but dialogue parse failures do (the turn is "committed but unparseable," raising `CommittedTurnParseError`). This ordering difference affects UUID consumption analysis in tests.

### UUID iterators are finite and path-sensitive

Tests use `iter(("uuid-1", ...)).__next__` for deterministic UUIDs. Each `self._uuid_factory()` call in the success path consumes one entry. Adding outcome emission adds one call per success path. A test that exercises two consults (one failing, one succeeding) only consumes outcome UUIDs for the succeeding one — the analysis requires tracing which code path each test exercises.

### Ruff formatting artifacts in codex-collaboration

Running `ruff format .` reformats ~28 files beyond the target files. Always format specific files: `ruff format server/models.py server/journal.py ...` — never the whole directory.

### OperationJournal.context_size nullability

`OperationJournalEntry.context_size` is `int | None`. It's set at the intent phase for turn_dispatch operations but the type allows None. Recovery/repair paths may encounter entries without it. The `OutcomeRecord.context_size` mirrors this nullability to avoid data fabrication.

## User Preferences

**Execute-then-review workflow:** Consistent across all 8 sessions. User reviews output before proceeding. This session: three review rounds on the plan, progressively shifting from design-level (P1) to hygiene (P3).

**Review format:** Structured `::code-comment` annotations with priority, confidence, file, and line range. Each finding links to specific plan lines and codebase evidence. Findings section provides a prose summary. The user expects findings to be addressed completely — partial fixes are re-flagged.

**Pre-analysis before Claude acts:** User provided detailed readout with hypotheses before asking Claude to validate. This pattern (user scopes, Claude validates) is more efficient than open-ended exploration.

**Precision in plans:** User expects plans to use correct API names, field types, and test patterns. Draft reasoning (wrong intermediate claims followed by corrections) should be collapsed to the final analysis in the published plan.

**Data integrity over convenience:** User flagged `context_size` coercion to `0` as P1 — fabricating analytics data is unacceptable even when the coercion "works" mechanically.

**Merge safety:** User prefers `--ff-only` for branch merges (from prior sessions). Creates feature branches for implementation work.

## Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| 5 | 2026-04-01 | Execute Tasks 0-3 | `archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| 6 | 2026-04-01 | Execute Task 4 | `archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md` |
| 7 | 2026-04-01 | Merge + Tasks 5-6 | `archive/2026-04-01_12-58_persistence-hardening-tasks-5-6-and-merge.md` |
| **8** | **2026-04-01** | **AC6 plan** | **This handoff** |
