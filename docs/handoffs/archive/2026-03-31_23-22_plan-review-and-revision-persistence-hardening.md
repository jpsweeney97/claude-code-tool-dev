---
date: 2026-03-31
time: "23:22"
created_at: "2026-04-01T03:22:12Z"
session_id: a30d2bb4-4e01-4e55-8667-d4caefd30301
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md
project: claude-code-tool-dev
branch: chore/plan-revision-persistence-hardening
commit: 8f009615
title: "plan review and revision — persistence hardening"
type: handoff
files:
  - docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md
  - docs/learnings/learnings.md
---

# plan review and revision — persistence hardening

## Goal

Review and revise the persistence hardening implementation plan (`docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`) to close gaps identified during the user's manual review, before execution begins.

**Trigger:** The prior session wrote a 1491-line implementation plan with 6 TDD tasks and 50 new tests. The user chose to review the plan before execution — consistent with the phase-boundary workflow observed across the handoff chain (design → plan → **review** → execute).

**Stakes:** The plan is the direct input for subagent-driven implementation. Gaps in validation logic, missing test coverage, or drifts from the design spec would propagate into code. The review caught 7 findings in Round 1 and 3 in Round 2 — without this session, 5 of those would have become implementation bugs or undocumented behavior choices.

**Success criteria:** (1) All accepted findings incorporated into the plan. (2) Test matrix expanded to cover identified gaps. (3) Design spec update formalized as blocking Task 0. (4) Compatibility decisions documented inline, not left as accidental omissions.

**Connection to project arc:** Third session in the persistence hardening chain: design (session 1) → plan (session 2) → **review** (session 3) → execute (session 4). The plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` is the artifact that bridges sessions 3→4.

## Session Narrative

Session began by loading the prior handoff (`2026-03-31_21-22_persistence-hardening-implementation-plan.md`), which described the plan-writing session. The handoff's first next step was "Execute the implementation plan." The user overrode this — they wanted to review the plan first and would share feedback.

The user asked for three specific artifacts to facilitate review: the exact planned file touch list, helper API sketch, and proposed test matrix. This required reading the full 1491-line plan in chunks (3 reads of ~500 lines each) and extracting structured summaries. The user's intent was clear: they wanted to review the plan at the API contract and test coverage level, not at the line-by-line code level.

The user then provided a structured review with 7 findings prioritized P1-P3, each citing specific line numbers in the design spec and codebase. The review format was consistent with patterns observed in prior sessions — precise, evidence-backed, with line references.

**Round 1 review — 7 findings:**

| ID | Severity | Finding | Verdict |
|----|----------|---------|---------|
| 1 | P1 | Journal validates wrong layer — flat type checks miss per-operation+phase requirements that recovery depends on | Accepted |
| 2 | P1 | No controller-level corruption tests — store unit tests don't verify composition with recovery/read paths | Accepted |
| 3 | P2 | Lineage validation under-tested for `update_runtime` wrong types and missing literal validation | Partially accepted |
| 4 | P2 | `check_health` API drift — journal outlier not documented in spec | Accepted |
| 5 | P2 | F4 tests only exercise explicit args, not YAML ingress path | Accepted |
| 6 | P3 | F6 test assertion mechanism should be documented (raw annotation-token, not resolved type) | Accepted |
| 7 | P3 | Extra-field forward-compat only tested for journal, not lineage | Accepted |

The verification phase for each finding involved reading the specific codebase locations cited. Key reads:

- `dialogue.py:446-592` — recovery coordinator. Confirmed `_recover_thread_creation` at `dispatched` phase unconditionally accesses `entry.codex_thread_id` (line 469) and raises `RuntimeError` if `None`. Similarly, `_recover_turn_dispatch` requires `entry.codex_thread_id` (line 534). The plan's journal callback treated `codex_thread_id` as unconditionally optional (`_JOURNAL_OPTIONAL_STR`), so a type-valid but semantically incomplete record would survive to recovery and crash. This was the highest-value finding.

- `dialogue.py:592,689` — audit event emission guarded by `if turn_id is not None and entry.runtime_id is not None`. Missing `runtime_id` doesn't crash but suppresses audit. The user's third constraint in Round 2 required an explicit tolerance decision for this.

- `dialogue.py:703-753` — `dialogue.read()` with TurnStore left-join. `context_size = metadata.get(seq)` raises `RuntimeError` if `None`. A malformed TurnStore overwrite that gets skipped by replay would leave the valid entry intact — the controller should still work.

- `test_recovery_coordinator.py:18-48` — `_recovery_stack` helper wires the full `DialogueController → ControlPlane → LineageStore → OperationJournal → TurnStore` stack. Used by all existing recovery tests. The controller-level corruption tests were added using this existing infrastructure.

- `models.py:10-12` — `HandleStatus = Literal["active", "completed", "crashed", "unknown"]` and `CapabilityProfile = Literal["advisory", "execution"]`. These are the enum types that the lineage callback should validate against.

- `profiles.py:40-64` and `profiles.py:96-116` — YAML load path. Key discovery: the YAML key is `reasoning_effort` (line 107: `profile.get("reasoning_effort")`), not `effort`. The plan's F4 tests only used `explicit_effort=`, which bypasses this mapping entirely.

For the partial acceptance of Finding 3: the plan's callback code already validates `runtime_id` and `codex_thread_id` types on `update_runtime` — the reviewer's claim about "wrong-typed `runtime_id`/`codex_thread_id`" was a test matrix gap, not a code gap. On "invalid `status` literals" — this was escalated by the user's Round 2 constraint into a full compatibility decision (see Decisions section).

After incorporating Round 1, the user provided Round 2 — 3 additional constraints before freezing the plan:

**Round 2 — 3 constraints:**

1. Lineage literal validation needs its own compatibility decision, not just tests. Unknown `status` or `capability_class` from a newer writer would be skipped on replay — this is tighter than the extra-field policy and must be documented explicitly.

2. Controller-level tests must be concrete, not generic. Two specific scenarios: (a) malformed journal terminal row with last-write-wins fallback, (b) malformed TurnStore overwrite with `dialogue.read()` using last valid metadata.

3. For journal conditional rules, decide explicitly whether missing `runtime_id` on `turn_dispatch` is acceptable. It doesn't crash recovery but suppresses audit repair at `dialogue.py:592,689`.

All three constraints were incorporated. A third round produced 3 more findings (1 P2, 2 P3) — classified as cleanup, not blockers. These were also incorporated.

**Round 3 — 3 cleanup findings:**

1. [P2] Lineage literal validation tests should verify the diagnostic label via `check_health`, not just assert the handle is skipped.
2. [P3] YAML ingress tests should use `_REFERENCES_DIR` patch with real YAML files, not `load_profiles()` monkeypatch.
3. [P3] Spec update should be a blocking Task 0, not a pre-implementation checklist.

The plan went through 3 review rounds total. Final state: 2017 lines (up from 1491), 66 new tests (up from 50), 7 tasks (Task 0-6, up from 6).

## Decisions

### Per-operation+phase conditional requirements in journal callback

**Choice:** Add conditional field requirements beyond flat type checks: `turn_dispatch` at any phase requires `codex_thread_id` (str); `turn_dispatch` at `dispatched`/`completed` requires `turn_sequence` (int); `thread_creation` at `dispatched` requires `codex_thread_id` (str).

**Driver:** `dialogue.py:534-538` raises `RuntimeError("Recovery integrity failure: no codex_thread_id in turn_dispatch entry")` if `entry.codex_thread_id is None`. The flat type checks in the original plan treated `codex_thread_id` as unconditionally optional, so a type-valid record without it would survive to recovery and crash. User's P1 finding: "The journal plan is still validating the wrong layer of invariants."

**Alternatives considered:**
- **Push defense up to recovery code** — make recovery handle `None` gracefully. Rejected because recovery already has explicit integrity checks that raise `RuntimeError` — the contract expects these fields to exist. Changing recovery to tolerate missing fields would weaken the recovery contract.
- **Require all optional fields on all operations** — tighter but rejects legitimate records (e.g., `thread_creation` at `intent` phase genuinely doesn't have `codex_thread_id`).

**Trade-offs accepted:** The conditional rules add complexity to `_journal_callback` (~20 lines). The rules are derived from reading the recovery code, not from a formal protocol spec — if recovery logic changes, the callback rules may need updating.

**Confidence:** High (E2) — verified by reading both the recovery code (`dialogue.py:446-592`) and tracing which fields are accessed unconditionally vs. guarded.

**Reversibility:** Medium — removing a conditional requirement means records without the field would start surviving to recovery, potentially causing `RuntimeError`.

**Change trigger:** If the recovery code adds `None` guards for currently-required fields, the conditional requirements can be relaxed.

### runtime_id tolerance on turn_dispatch — compatibility decision

**Choice:** `runtime_id` on `turn_dispatch` is NOT required. Tolerate `None`.

**Driver:** Missing `runtime_id` suppresses audit event emission at `dialogue.py:592` and `dialogue.py:689` (`if turn_id is not None and entry.runtime_id is not None`) but does not crash recovery. Requiring it would reject records from older writers that may not persist `runtime_id` on all `turn_dispatch` entries.

**Alternatives considered:**
- **Require `runtime_id`** — would close the audit gap but break forward compatibility. Rejected because recovery handles it gracefully (the `and` guard).
- **Emit a warning diagnostic** — softer signal. Deferred as over-engineering for a test/support-only surface.

**Trade-offs accepted:** Audit trail has a data-quality gap for entries without `runtime_id`. A `turn_dispatch` that is confirmed (turn completed) but has no `runtime_id` produces no audit event for that turn.

**Confidence:** High (E2) — verified by reading both access sites (`dialogue.py:592,689`). The `and` guard is explicit.

**Reversibility:** Low — tightening this later would reject previously-tolerated records.

**Change trigger:** If audit completeness becomes a hard requirement (e.g., compliance), `runtime_id` should become required and older records without it should be backfilled or flagged.

### Lineage literal validation — tighter than extra-field policy

**Choice:** Validate `status` against `HandleStatus` and `capability_class` against `CapabilityProfile` on lineage replay. Unknown literal values are `SchemaViolation`.

**Driver:** User's Round 2 constraint: "Do not leave lineage literal validation as an accidental omission... `status` drives controller behavior and filtering." A handle with `status="banana"` or `capability_class="delegation"` from a newer writer would be semantically misinterpreted by the controller.

**Alternatives considered:**
- **Tolerate unknown literals (forward-compatible)** — would allow newer writers to introduce new enum values without breaking older readers. Rejected because `status` drives `LineageStore.list()` filtering and controller lifecycle decisions. A handle the reader can't classify is worse than a handle the reader skips.
- **Log warning but keep the handle** — softer failure. Rejected because a handle with unknown `status` would appear in `list()` results with unpredictable behavior.

**Trade-offs accepted:** New enum values require coordinated rollout: update the `Literal` type first, then start writing the new value. This is tighter than the extra-field policy (which silently ignores additive keys). The tighter contract is justified because enum values are semantic, not additive.

**Confidence:** High (E2) — `HandleStatus` at `models.py:12` lists exactly 4 values. `CapabilityProfile` at `models.py:10` lists 2. Both are `Literal` types that can be validated via `get_args()`.

**Reversibility:** Medium — loosening would allow previously-rejected records to survive, potentially creating handles the controller can't handle.

**Change trigger:** If enum expansion becomes frequent, consider a "known + unknown-tolerated" two-tier model instead of strict rejection.

### YAML ingress tests via _REFERENCES_DIR patch

**Choice:** Test F4 YAML ingress by patching `_REFERENCES_DIR` to a temp directory with a real `consultation-profiles.yaml`, not by monkeypatching `load_profiles()`.

**Driver:** User's Round 3 constraint: "Monkeypatching `load_profiles()` is still weaker than true ingress coverage. It does not pin YAML parsing, local-override merge behavior, or the file-key contract around `reasoning_effort`."

**Alternatives considered:**
- **Monkeypatch `load_profiles()`** — simpler but skips YAML parsing, file I/O, and the `reasoning_effort` → `effort` key mapping at `profiles.py:107`. Rejected per user feedback.
- **Widen `resolve_profile()` to accept a path parameter** — rejected because user said "do not widen `resolve_profile()` just to inject a temp YAML path for tests."

**Trade-offs accepted:** Tests are slightly more complex (write YAML, patch module-level `_REFERENCES_DIR`). `import yaml` is added to the test class. The YAML fixture is minimal (3-5 fields) so it doesn't become a maintenance burden.

**Confidence:** High (E1) — standard monkeypatch pattern. `_REFERENCES_DIR` is a module-level `Path` at `profiles.py:37`.

**Reversibility:** High — test-only change. Swapping between patch targets requires no production code changes.

**Change trigger:** If `_REFERENCES_DIR` is refactored or removed, tests need to patch the new resolution mechanism.

### Task 0 as blocking first task

**Choice:** Promote design spec updates from a pre-implementation checklist to a numbered `## Task 0: Update Design Spec` before Branch 1.

**Driver:** User's Round 3 constraint: "If those remain 'to-do before coding' instead of explicit step 0, the implementation can drift from the canonical design again."

**Alternatives considered:**
- **Pre-implementation checklist** — weaker signal. Rejected because the user explicitly said the spec updates should block coding.

**Trade-offs accepted:** Adds a commit to the implementation sequence that contains no code — only spec changes. Minor overhead.

**Confidence:** High (E1) — structural choice about plan organization.

**Reversibility:** High — Task 0 can be demoted back to a checklist if the overhead isn't worth it.

**Change trigger:** If the team adopts a workflow where specs are updated during implementation rather than before.

## Changes

### Modified files

| File | Lines | Purpose |
|------|-------|---------|
| `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` | 1491 → 2017 | Implementation plan revised with all review findings |
| `docs/learnings/learnings.md` | +8 | Learning captured: protocol-layer validation in design specs |

### Plan revision details

The plan was modified through ~20 targeted edits. Key structural changes:

**Task 0 added (new):** Blocking design spec update with 3 contract changes (journal check_health outlier, conditional requirements table, lineage literal validation). Positioned before Branch 1.

**Task 3 (lineage) expanded:**
- Imports: added `CapabilityProfile` and `get_args`
- Added `_VALID_STATUSES` and `_VALID_CAPABILITIES` frozensets
- Added literal validation in `create` and `update_status` branches with inline compatibility decision comment
- Added 7 new tests: `test_create_invalid_status_diagnosed_and_skipped`, `test_create_invalid_capability_class_diagnosed_and_skipped`, `test_update_status_invalid_literal_diagnosed_and_skipped`, `test_update_runtime_wrong_type_runtime_id_skipped`, `test_update_runtime_wrong_type_codex_thread_id_skipped`, `test_create_extra_field_ignored`
- Tests verify both skip behavior AND diagnostic label via `check_health`

**Task 4 (journal) expanded:**
- Added per-operation+phase conditional requirements block after flat type checks, before entry construction
- Added `runtime_id` tolerance compatibility decision comment inline
- Added 4 new tests: `test_turn_dispatch_without_codex_thread_id_skipped`, `test_thread_creation_dispatched_without_codex_thread_id_skipped`, `test_thread_creation_intent_without_codex_thread_id_accepted`, `test_turn_dispatch_dispatched_without_turn_sequence_skipped`

**Controller-level tests added (Steps 7-10 after Task 4):**
- `test_malformed_journal_terminal_row_falls_back_to_earlier` — injects malformed `completed` row for same idempotency key, verifies intent row becomes terminal phase, recovery marks handle "unknown"
- `test_malformed_turn_metadata_overwrite_survives_in_read` — injects malformed TurnStore overwrite, verifies `dialogue.read()` returns original `context_size=4096`

**Task 5 (F4) expanded:**
- Added `TestYamlIngressValidation` class with `_write_profile_yaml` helper
- 3 tests: bad posture, bad reasoning_effort (pins YAML key mapping), non-int turn_budget
- Tests patch `_REFERENCES_DIR` to temp dir with real YAML, not `load_profiles()` monkeypatch

**Task 6 (F6) enhanced:**
- Added annotation-token assertion docstring to test

**Verification checklist expanded:** 9 → 15 items, covering new validation, controller tests, YAML ingress, and compatibility decisions.

## Codebase Knowledge

### Recovery Coordinator Field Dependencies

The recovery coordinator at `dialogue.py:435-601` has per-operation+phase field dependencies that are not expressed in the data model:

| Recovery method | Line | Field accessed | Guard | Consequence if None |
|----------------|------|---------------|-------|-------------------|
| `_recover_thread_creation` | 469 | `entry.codex_thread_id` | None → `RuntimeError` | Crash |
| `_recover_turn_dispatch` | 534 | `entry.codex_thread_id` | None → `RuntimeError` | Crash |
| `_recover_turn_dispatch` | 550-551 | `entry.turn_sequence` | None → `and` short-circuits | Turn never confirmed, handle marked "unknown" |
| `_recover_turn_dispatch` | 592 | `entry.runtime_id` | None → `and` short-circuits | Audit event suppressed |

The first two are hard failures (RuntimeError). The third is a graceful degradation. The fourth is a data-quality gap. The journal callback's conditional requirements enforce the first two and tolerate the last two.

### dialogue.read() TurnStore Left-Join

`dialogue.py:703-753` reads completed turns from the thread API and enriches each with `context_size` from TurnStore. The left-join at line 744-753:

```python
context_size = metadata.get(seq)
if context_size is None:
    raise RuntimeError(
        f"Turn metadata integrity failure: no context_size for ..."
    )
```

This means a malformed TurnStore row that gets skipped by replay causes `metadata.get(seq)` to return the last valid value for that `(cid, turn_sequence)` pair (if one exists). The controller test verifies this end-to-end.

### HandleStatus and CapabilityProfile as Literal Types

`models.py:10-12`:
```python
CapabilityProfile = Literal["advisory", "execution"]
AuthStatus = Literal["authenticated", "expired", "missing"]
HandleStatus = Literal["active", "completed", "crashed", "unknown"]
```

These are `typing.Literal` types, which means `get_args(HandleStatus)` returns `("active", "completed", "crashed", "unknown")`. The lineage callback uses `frozenset(get_args(...))` for O(1) validation.

### FakeRuntimeSession Test Infrastructure

`test_control_plane.py:21-129` defines `FakeRuntimeSession` with configurable behaviors:
- `read_thread_response: dict | None` — when set, `read_thread()` returns this instead of auto-generating turns from `completed_turn_count`
- `resumed_threads: list[str]` — tracks `resume_thread()` calls
- `started_threads: list[str]` — tracks `start_thread()` calls

`test_recovery_coordinator.py:18-48` defines `_recovery_stack(tmp_path, session=None)` which wires the full component stack and returns all components. This is the infrastructure used for the new controller-level corruption tests.

### YAML Profiles Key Mapping

`profiles.py:107`: `effort = explicit_effort or profile.get("reasoning_effort")`. The YAML key is `reasoning_effort`, the resolved field is `effort`. The F4 YAML ingress tests pin this mapping by writing a YAML file with `reasoning_effort: "turbo"` and asserting the error message contains "unknown effort" (not "unknown reasoning_effort").

### Module Dependency for Lineage Literal Validation

The lineage callback now imports `CapabilityProfile` in addition to the existing `CollaborationHandle` and `HandleStatus`:

```
from .models import CapabilityProfile, CollaborationHandle, HandleStatus
```

And `get_args` from typing:

```
from typing import Any, Callable, get_args
```

The `_VALID_STATUSES` and `_VALID_CAPABILITIES` frozensets are module-level constants derived from the Literal types at import time.

## Context

### Mental Model

This session was a **plan-level code review** — reviewing code that hasn't been written yet. The review operated at three layers:

1. **Schema layer** — field presence and type correctness (the original plan covered this)
2. **Protocol layer** — per-operation+phase conditional requirements (P1 finding — the plan missed this)
3. **Integration layer** — controller-level composition of store behavior (P1 finding — the plan only had unit tests)

The highest-value findings came from tracing data flow *through* the stores into the consumer (recovery coordinator), not from examining the stores in isolation. The design spec described schema-layer validation; the review revealed protocol-layer invariants that were only visible in the consumer code.

### Project State

- **Branch:** `chore/plan-revision-persistence-hardening` at `8f009615`
- **Plan:** Revised and verified — ready for execution
- **Design spec:** Needs updating (Task 0 in the plan)
- **Tests:** 359/359 passing (unchanged — this session only modified the plan, not code)
- **No implementation branches exist yet**

### Review Statistics

| Metric | Value |
|--------|-------|
| Review rounds | 3 |
| Total findings | 10 (2 P1, 4 P2, 4 P3) |
| Accepted | 9 (1 partially) |
| Rejected | 0 |
| New tests added to plan | +16 (50 → 66) |
| Plan line growth | +526 (1491 → 2017) |
| New decisions documented | 5 |
| Compatibility decisions | 2 (runtime_id tolerance, literal validation tightening) |

## Learnings

### Protocol-layer invariants must be captured in design specs proactively

**Mechanism:** Design specs that describe data validation often stop at the schema layer (field presence, type correctness) and miss the protocol layer — invariants that a consumer depends on but that the data model doesn't express. The `OperationJournalEntry` dataclass has `codex_thread_id: str | None` (structurally valid), but `turn_dispatch` at any phase requires it non-None or recovery crashes.

**Evidence:** `dialogue.py:534-538` unconditionally accesses `entry.codex_thread_id` for `turn_dispatch` entries. The design spec at line 153-166 only described flat type checks. The gap was only discoverable by reading the consumer code.

**Implication:** When a design spec defines validation for a persistence format, enumerate consumer-side field requirements as a separate table. Review checkpoint: "does the consumer access any optional field unconditionally?"

**Watch for:** Any dataclass with optional fields that is consumed by code with unconditional field access. The mismatch between structural optionality and semantic requirement is the bug pattern.

### Compatibility decisions must be explicit, not incidental

**Mechanism:** When validation rejects values that the current data model accepts, that's a tighter contract — even if the validation is correct. The lineage literal validation rejects unknown `status` values, which is tighter than the extra-field policy that silently ignores additive keys. Without an explicit compatibility decision, the tightening looks like an oversight.

**Evidence:** User's Round 2 feedback: "If you do neither, that gap will survive as an undocumented behavior choice."

**Implication:** Any time validation rejects data that was previously accepted (or could be written by a newer version), document: (1) what's rejected, (2) why rejection is safer than tolerance, (3) what the upgrade path is for new values.

**Watch for:** Forward-compatibility asymmetry — extra fields are additive, but enum expansion is semantic. Different policies are appropriate for each.

### Controller-level corruption tests catch composition bugs that unit tests miss

**Mechanism:** Store unit tests verify that `replay_jsonl` correctly skips malformed records. But the interesting behavior is one layer up: what happens when a skipped record changes the terminal phase in last-write-wins? The journal test verifies that a skipped `completed` record causes fallback to the earlier `intent` record, and recovery processes the fallback deterministically (marks handle "unknown").

**Evidence:** The two controller-level tests exercise paths that no store-level test covers: journal fallback + recovery behavior, and TurnStore skip + `dialogue.read()` left-join.

**Implication:** When hardening a persistence layer, add at least one test at the consumer layer that injects malformed data and verifies end-to-end behavior.

## Next Steps

### 1. Commit and merge the plan revision

**Dependencies:** None — plan is ready.

**What to do:** Commit the plan on `chore/plan-revision-persistence-hardening`, merge to main, delete the branch.

**Approach suggestion:** Since the plan is the only changed file (plus the learning), a direct merge to main is appropriate — no PR needed for a documentation-only change.

### 2. Execute the implementation plan

**Dependencies:** Plan revision merged to main.

**What to read first:** The plan itself at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`. It contains all code, test cases, and commands. No other files need to be read before starting.

**Approach suggestion:** Invoke `superpowers:subagent-driven-development` skill. The plan has 7 tasks (Task 0 → Task 6). Task 0 updates the design spec (no code). Tasks 1-4 execute on `fix/persistence-replay-hardening` branch. After merging Branch 1, Tasks 5-6 execute on `chore/type-narrowing` branch.

**Acceptance criteria:** All 359 existing tests pass. 66 new tests added and passing. `check_health()` available on all three stores. Malformed records diagnosed (not crashed). Type narrowing catches typo postures/efforts. Per-operation+phase conditional requirements enforced. Compatibility decisions documented inline.

### 3. (After Branch 1 merged) AC6 analytics emission

**Dependencies:** Branch 1 merged. Ticket T-20260330-03. Delivery roadmap at `delivery.md:255` (packet 2b).

**What to read first:** `delivery.md` for packet 2b acceptance criteria. `contracts.md` §Analytics for the event schema.

**Approach suggestion:** This is actual roadmap work (not debt/cleanup). Scope and plan separately.

## In Progress

Clean stopping point. The implementation plan is revised and verified at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`. The learning is appended to `docs/learnings/learnings.md`. Both files are uncommitted on `chore/plan-revision-persistence-hardening` branch. No code changes in flight.

## Open Questions

### AC6 analytics emission

Deferred from T-03. Actual roadmap work in packet 2b (`delivery.md:255`). Not addressed in this session or the prior two. Ticket T-20260330-03 tracks it.

### Diagnostics consumer architecture

The design spec defers wiring `check_health()` to a production surface. The store ownership split (control plane owns journal; dialogue owns lineage/turn stores) means no single component can call all three without refactoring. The journal `check_health` outlier (takes `session_id`) adds complexity to a uniform consumer.

### Deferred review suggestions (S1-S16)

16 suggestions from the T-03 second review agents were not independently validated. Unchanged from prior handoffs. May contain false positives.

## Risks

### Plan code may need adjustment during implementation

The plan contains 2017 lines including ~1800 lines of code written from reading, not execution. The TDD structure mitigates this — each step verifies before proceeding. The review added 16 more tests, reducing the risk of unverified assumptions.

### Conditional requirements derived from consumer reading, not spec

The per-operation+phase conditional requirements were derived by reading `dialogue.py:446-592`, not from a formal protocol specification. If the recovery code changes (new operations, different field access patterns), the callback rules may need updating. Task 0 mitigates this by encoding the rules in the design spec.

### Branch merge ordering matters

Branch 2 (`chore/type-narrowing`) must be created after Branch 1 is merged. If created in parallel, the type narrowing tests may interact with the replay migration in unexpected ways.

## References

| What | Where |
|------|-------|
| Implementation plan (revised) | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| Recovery coordinator | `packages/plugins/codex-collaboration/server/dialogue.py:435-601` |
| dialogue.read() | `packages/plugins/codex-collaboration/server/dialogue.py:703-753` |
| HandleStatus/CapabilityProfile | `packages/plugins/codex-collaboration/server/models.py:10-12` |
| FakeRuntimeSession | `packages/plugins/codex-collaboration/tests/test_control_plane.py:21-129` |
| _recovery_stack | `packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py:18-48` |
| YAML profile loading | `packages/plugins/codex-collaboration/server/profiles.py:40-64` |
| Prior handoff | `docs/handoffs/archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |

## Gotchas

### Journal callback ordering: flat checks → conditional checks → construction

The conditional requirements block must come AFTER the flat type checks (which validate `codex_thread_id` as optional string if present) and BEFORE the entry construction. The flat checks ensure type correctness; the conditional checks ensure semantic completeness for specific operation+phase combinations. If reordered, the conditional check for `codex_thread_id` would fire before the type check has verified it's a string.

### YAML key is reasoning_effort, resolved field is effort

`profiles.py:107`: `effort = explicit_effort or profile.get("reasoning_effort")`. The YAML file uses `reasoning_effort` as the key, but the `ResolvedProfile` field is `effort`. The F4 YAML ingress tests pin this mapping, but it's a gotcha for anyone adding new YAML profile fields — the YAML key and the resolved field name may differ.

### Literal validation uses get_args, not hardcoded values

The lineage callback uses `frozenset(get_args(HandleStatus))` to derive the valid set. If someone adds a new value to the `Literal` type in `models.py`, the validation set updates automatically. This is intentional — the callback doesn't hardcode status values. But it means the callback's behavior changes when the type alias changes, which is the intended coordinated rollout pattern.

### check_health diagnostic assertions require fresh store instance

The lineage literal validation tests call `store2.check_health()` on a freshly constructed store (not the original `store` that wrote the handle). This is because `check_health()` replays the JSONL file — it needs a new store instance to exercise the full replay path including the injected malformed records.

## User Preferences

**Review style:** Structured findings with priority levels (P1-P3) and specific line references. Expects responses that verify each finding against the codebase before accepting or rejecting.

**Compatibility decisions must be explicit:** User said (Round 2): "Either validate `status` against `HandleStatus` now, or explicitly record that unknown status strings are tolerated on replay and why. If you do neither, that gap will survive as an undocumented behavior choice."

**Controller tests must be concrete:** User said (Round 2): "Make the new controller-level tests concrete, not generic." Specified two exact scenarios with expected behaviors.

**Monkeypatch at the right level:** User said (Round 2): "Do not widen `resolve_profile()` just to inject a temp YAML path for tests. Keep the public API stable and test the YAML ingress by monkeypatching `load_profiles()` or the module reference path instead." Then in Round 3, upgraded this to `_REFERENCES_DIR` patch for full ingress coverage.

**Phase-boundary workflow:** User consistently separates design → plan → review → execution into distinct sessions, running `/save` at each boundary. Three sessions in this chain so far, all following this pattern.

**Spec authority over plan:** User said (Round 3): "The spec updates should be a blocking first task, not just a pre-implementation checklist." The design spec is the canonical authority; the plan must match it before implementation begins.
