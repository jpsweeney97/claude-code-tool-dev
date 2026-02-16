# T-001: Plan Review Errata — Context Injection Agent Integration

```yaml
id: T-001
date: 2026-02-15
status: open
priority: critical
branch: fix/reconstruct-plan
blocked_by: []
blocks: [implementation of D1-D5]
```

## Summary

Codex cross-model review of the 7 plan documents (manifest + 6 deliveries) found **48 unique issues** including 3 critical bugs, 6 blocking contradictions, and 4 design decisions that must be resolved before implementation begins. The plan architecture is sound — no replanning needed — but the documents contain specific errors that would cause implementation failures.

**Scope:** Fix plan documents only. No code changes.

**Work estimate:** ~90-110 targeted edits across 9 files (expanded from original ~40-60 after CC verification dialogues found additional scope in every cross-cutting issue).

## Context

Twelve independent Codex dialogue reviews were conducted:
- 7 individual document reviews (manifest, D1, D2, D3, D4a, D4b, D5)
- 5 transition reviews (D1→D3, D3→D2, D2→D4a, D4a→D4b, D4b→D5)

Issues found by multiple independent reviews carry highest confidence. Six cross-cutting themes were found by 3+ reviews each.

**Source session:** Handoff `2026-02-15_22-30_plan-committed-and-split-into-deliveries.md` (archived).

## Prerequisites

Before starting fixes:
1. Read the manifest: `docs/plans/2026-02-15-context-injection-agent-integration-manifest.md`
2. ~~Resolve the 4 design decisions in Section 4~~ — **Done.** DD-1: Option A (base_types). DD-2: C-lite. DD-3: Hybrid B + guard. DD-4: B + guardrail.
3. Work on branch `fix/reconstruct-plan` — apply all fixes before merging to `main`

## 1. Cross-Cutting Issues

Issues affecting multiple documents. Fix all instances when addressing each.

### CC-1: Import cycle types.py ↔ ledger.py [CRITICAL]

**Found by:** D4a review, D2→D4a transition

D4a adds `from context_injection.ledger import CumulativeState, LedgerEntry, ValidationWarning` to `types.py`. D1's `ledger.py` already imports `from context_injection.types import Claim, ProtocolModel, Unresolved`. This creates a circular import that crashes at runtime. `from __future__ import annotations` does not resolve this. `TYPE_CHECKING` guards are fragile with Pydantic v2 nested model fields.

**Resolved via DD-1 + Codex dialogue** (thread `019c64e1-797e-7990-bd53-6da70d57090f`). High confidence.

**13 edits across 3 files.** D1 creates `base_types.py` (not D4a) — avoids carrying a known cycle through D2/D3. Canonical rule: all code imports from `types`, only `ledger.py` uses `base_types`.

D1 plan edits (8):
1. Files in Scope: add `base_types.py` to Create, add `types.py` and `test_types.py` to Modify
2. Scope statement: "pure additive" → "mostly additive (one extraction edit to `types.py`)"
3. Task 1 file list: add `base_types.py` create, `types.py` modify, `test_types.py` modify
4. New step 4a: re-export identity test `TestBaseTypeReexports.test_reexport_identity`
5. Step 7: insert `base_types.py` creation, modify `types.py` to remove 3 class defs and add re-export, remove unused `BaseModel`/`ConfigDict` pydantic imports
6. `ledger.py` import: `from context_injection.types` → `from context_injection.base_types`
7. Step 8 run command: include `tests/test_types.py::TestBaseTypeReexports`
8. Commit: add `base_types.py`, `types.py`, `test_types.py` to `git add`

D4a plan edits (2):
9. Prerequisites: expand D1 prereqs to note DD-1 base type extraction, list `base_types.py`
10. Before import block: add note that `types.py → ledger.py` import is cycle-safe because `ledger.py` imports from `base_types.py`

Manifest edits (2):
11. D1 description: "independent (pure new module)" → "independent (new modules + one extraction in `types.py`)"
12. Deliverables table: insert `base_types.py` row, update `types.py` and test rows

### CC-2: D4a review gate contradicts D4a document [MAJOR]

**Found by:** Manifest review, D4a review, D4a→D4b transition

Three contradictory statements:
- Manifest line 60: "all 739 existing tests pass with new schema"
- D4a line 48 (done criteria): "All 739 existing tests pass with new schema"
- D4a Task 12 Step 7 (line 619): "Some tests FAIL — these are semantic failures"

D4a's scope explicitly forbids pipeline changes needed to fix semantic failures.

**Verified via Codex dialogue** (thread `019c64e1-32be-79e1-84f2-84e3e14ab896`). High confidence.

**6 edits needed (not 3).** Dialogue found 3 additional locations.

Edit 1 — Manifest D4a gate (line 60):
> D4a | 0.2.0 types defined; all new type tests pass; all 739 existing tests collect and execute (no import/construction errors); remaining semantic failures marked `xfail(strict=True)` with D4b task mapping; xfail inventory committed; no pipeline/execute/server changes

Edit 2 — D4a done criteria (lines 45-49):
> - All new 0.2.0 type tests pass
> - All 739 existing tests collect and execute (no import errors, no construction errors)
> - Semantic failures marked with `pytest.mark.xfail(strict=True, reason="D4b: <cause> (Task 13a|13b|14)")`
> - Xfail inventory committed at `packages/context-injection/tests/xfail_inventory_d4a.md`
> - No changes to `pipeline.py`, `execute.py`, or `server.py`

Edit 3 — D4b prerequisite (lines 14-17): update to reference xfail inventory, add "xfail inventory matches in-code markers."

Edit 4 — **D4b done criteria** [NEW]: Add "No temporary D4a semantic markers remain: no pytest xfail with reason prefix `D4b:` exists in tests." Without this, xfails survive silently past D4b (pytest treats XFAIL as non-failing).

Edit 5 — **D4a Task 12 Step 7** [NEW] (lines 617-624): Replace "Some tests FAIL — these are semantic failures" with xfail-marking workflow: categorize as shape failures (fix immediately) vs semantic failures (mark xfail), re-run expecting no FAIL/ERROR, commit inventory.

Edit 6 — **D4a stale pre-split text** [NEW] (line 57, overlaps D4a-2): "Five tasks: 11, 12, 13a, 13b, 14" → "Two tasks: 11 (0.2.0 types) and 12 (test shape migration). Tasks 13a/13b/14 are in D4b."

### CC-3: Checkpoint serialization bug — stale last_checkpoint_id [CRITICAL]

**Found by:** D2 review, D2→D4a transition, D4b review

`serialize_checkpoint` in D2 generates a new `checkpoint_id`, serializes the state into the payload, then wraps in a `StateCheckpoint` envelope. But the state's `last_checkpoint_id` in the payload is the PREVIOUS checkpoint's ID. On restore, `validate_checkpoint_intake` trusts the payload, causing stale lineage that breaks chain validation.

**Verified via Codex dialogue** (thread `019c64e1-d1ce-7ec1-b0b1-3be430a0e3c1`). High confidence. Fix scope significantly expanded — signature redesign, security gap found.

**`serialize_checkpoint` redesign** (D2 lines 697-722):
- Return type: `SerializedCheckpoint` NamedTuple `(state, checkpoint_id, checkpoint_string)` — not bare tuple
- `parent_id` parameter eliminated — derived inside function from `state.last_checkpoint_id` (encapsulates ordering invariant, prevents caller/callee mismatch)
- Embed new `checkpoint_id` into state BEFORE serializing payload: `state_for_payload = state.with_checkpoint_id(checkpoint_id)`
- Returns updated state so caller commits the projected state directly

**Pipeline 18-step → 17-step** (D4b lines 520-534):
- Step 15 (dual-write `projected.with_checkpoint_id`) removed — `serialize_checkpoint` now returns updated state
- Downstream steps renumber: 16→15, 17→16, 18→17
- All "18-step" references in D4b (lines 278, 374, 632) updated to "17-step"

**4 restore-path guards** in `validate_checkpoint_intake` (D2 lines 984-1026):
1. `checkpoint_id` not None when payload present → `checkpoint_missing`
2. Request `checkpoint_id` matches envelope ID → `checkpoint_stale`
3. Payload `last_checkpoint_id` matches envelope ID → `checkpoint_invalid` (corruption guard)
4. **Payload `conversation_id` matches target conversation** → `checkpoint_invalid` [NEW — security gap: cross-conversation checkpoint swapping was not in original ticket]

**4 correctness invariants** (must hold after every turn):
1. `TurnPacketSuccess.checkpoint_id == StateCheckpoint.checkpoint_id`
2. `ConversationState(payload).last_checkpoint_id == StateCheckpoint.checkpoint_id`
3. `ctx.conversations[cid].last_checkpoint_id == TurnPacketSuccess.checkpoint_id`
4. Next `StateCheckpoint.parent_checkpoint_id == previous TurnPacketSuccess.checkpoint_id`

**15 tests:** 8 D2 unit (serialize round-trip, parent chain, first checkpoint, state update, 4 restore guard tests) + 4 D4b pipeline (consistent triplet, two-turn chain, restart chain, cross-conversation reject) + 3 integration. Existing restore test gives false confidence — hardcodes `"cp-1"` instead of asserting against actual serialized ID.

### CC-4: Budget semantic mismatch — evidence budget vs turn budget [CRITICAL]

**Found by:** D3 review, D4b review, D4b→D5 transition

D4b step 11 passes `budget.evidence_remaining` (max ~3) to `compute_action(budget_remaining=...)`, but D3 defines `budget_remaining` as **turn** budget (typically 8-15). Conversations would conclude after ~3 evidence items.

**Verified via Codex dialogue** (thread CC-4). High confidence. Fix expanded with precise placement and D5 agent override.

**D3** (line ~386): Add docstring: `"budget_remaining: Turns remaining in the conversation budget (NOT evidence budget). 0 or negative means budget is exhausted."`

**D4b** — `MAX_CONVERSATION_TURNS = 15` in `pipeline.py` (same constant serves CC-4 and DD-2):
- Import-time invariant: `if MAX_CONVERSATION_TURNS >= MAX_ENTRIES_BEFORE_COMPACT: raise RuntimeError(...)` (not `assert` — Python `-O` disables asserts)
- Pre-append guard at **step 4.5** (after checkpoint intake, before entity extraction — avoids unnecessary work on over-cap turns): `if len(base.entries) >= MAX_CONVERSATION_TURNS: return TurnPacketError(code="turn_cap_exceeded")`
- Step 11 fix: `turn_budget_remaining = max(0, MAX_CONVERSATION_TURNS - cumulative.turns_completed)` — off-by-one verified (turn 15 gets budget=0 → conclude, turn 16 rejected by guard)

**D5** — Agent-side budget override (interim, defense-in-depth):
- `effective_budget = min(max(1, user_budget), MAX_CONVERSATION_TURNS)`
- Step 5: if `turn_count >= effective_budget`, treat any server action as `conclude`
- Documented as interim measure; long-term: pass user budget through TurnRequest (separate ticket)

**DD-2 interaction verified:** No gap between "conclude" (turn 15, budget=0) and "hard reject" (turn 16, guard). CC-3 dependency noted: pre-append guard assumes checkpoint restore produces trustworthy state.

### CC-5: Compaction-cumulative contract [MAJOR]

**Found by:** Manifest review, D2 review, D3→D2 transition

`compute_cumulative_state()` iterates only `self.entries`. After compaction truncates to last 8, totals are undercounted. Decisions doc promises "running totals across all turns."

**Resolved via DD-2 (C-lite) + Codex dialogue** (thread `019c64e2-637d-76f1-a622-6f38b4bf9ffc`). High confidence.

**5 documents need edits:**

**D2** (lines ~439, ~1029): Two docstring annotations — `compute_cumulative_state`: "Correct only when compaction has not triggered. See DD-2 invariant." `compact_ledger`: "Unreachable under DD-2 invariant (MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT)."

**D4a**: Add `turn_cap_exceeded` to `ErrorDetail.code` literal type (line ~341) and test parametrize list (line ~235). 0.2.0 schema only — 0.1.0 has no turn caps.

**D4b**: Pre-append guard at **Step 3b** (after checkpoint intake, before entity extraction). `TurnPacketError` can't carry partial success fields, so early rejection is correct. Also: `MAX_CONVERSATION_TURNS` constant + `RuntimeError` invariant at module level.

**D5**: Error recovery table row: `turn_cap_exceeded | Do not retry. Proceed to Phase 3 (Synthesis).`

**Manifest**: Update D2 gate (compaction contract documented) and D4b gate (turn-cap invariant enforced, guard tested).

**Tests:** 6 required (constant invariant, below-cap success, at-cap rejection, no-mutation-on-reject, repeated-turn bound, checkpoint-restore-at-cap) + 3 optional hardening (D4a schema literal, guard precedence, turn_number secondary guard).

### CC-6: Naming/import path drift across documents

**Found by:** D1 review, D3 review, D4a review, D4b review, D1→D3 transition

**Verified via Codex dialogue** (thread `019c64e2-5b87-7c12-9e91-e8b1e4a1dc4c`). High confidence.

**4 fixes needed (not 3).** D2 was missing from original ticket.

All fixes are prose-only — code snippets in the plans are already correct. DD-1 (base_types) does NOT require additional CC-6 fixes (re-exports preserve paths).

1. **D3** prereq (line 15): split into per-module lines — `From context_injection/ledger.py: LedgerEntry, LedgerEntryCounters, CumulativeState` + `From context_injection/enums.py: EffectiveDelta, QualityLabel`
2. **D2** prereq (line 15) [NEW — missing from original ticket]: same pattern — `From context_injection/ledger.py: LedgerEntry, CumulativeState, validation functions` + `From context_injection/enums.py: EffectiveDelta, QualityLabel`
3. **D4a** prereq D1 block: fix enum module path + add `LedgerEntryCounters`. D3 block: replace `LedgerSummary` type with `generate_ledger_summary(entries, cumulative) -> str` function
4. **D4b** prereq (line 30): `generate_summary()` → `generate_ledger_summary()`

### CC-7: parent_checkpoint_id spec drift

**Found by:** D2 review, D4a→D4b transition

Decisions doc (line 179) specifies `parent_checkpoint_id` in TurnRequest. D4a removes it. It's redundant — stale detection uses head-pointer model (`checkpoint_id` vs `last_checkpoint_id`), not parent-chain comparison.

**Verified via Codex dialogue** (thread `019c64e2-2b50-7863-84f2-56bf103b4058`). High confidence.

**4 edits across 2 files (not 1).** Removing the field without fixing related descriptions leaves internal inconsistencies.

Decisions doc (`docs/plans/...-decisions.md`):
1. Line 31 (chain validation bullet): `"enables stale/replay/fork detection"` → `"reserved for future parent-chain validation (not used in 0.2.0 stale detection)"`
2. Line 38 (recovery error code): `"parent_checkpoint_id doesn't match server's expected chain"` → `"request checkpoint_id doesn't match server last_checkpoint_id (head-pointer model)"`
3. Lines 178-179 (TurnRequest shape): remove `parent_checkpoint_id` field, add comment: `# parent_checkpoint_id is inside state_checkpoint envelope only; not a TurnRequest field in 0.2.0`

Planning brief (`docs/plans/...-planning-brief.md`):
4. Line 266: remove `parent_checkpoint_id` from TurnRequest field list

Cross-reference: D2-3 handles remaining chain-model language updates.

### CC-8: Delta semantic drift

**Found by:** D4b review, D4b→D5 transition

D4b test code uses "high"/"medium"/"low" for delta. D5 instructs "advancing"/"shifting"/"static". Field is `str`, both pass validation. Drift extends beyond D4a/D4b — D1, D2, D3 also have inconsistent values.

**Verified via Codex dialogue** (thread CC-8). High confidence.

**28 line changes across 5 documents + 1 function simplification + 1 new test.** Scope significantly expanded from original 2-file fix.

**Type annotation:** `Literal["advancing", "shifting", "static"]` on `TurnRequest.delta` in D4a (not StrEnum — consistent with existing protocol model patterns). `LedgerEntry.delta` stays `str` — "strictness at the boundary, tolerance internally."

**Bug found in D1:** `_delta_disagrees` has no handling for `delta="shifting"` — falls through silently even when `effective_delta=STATIC`. Function needs simplification to canonical semantic logic (3-way: static vs non-static contradiction, not direct equality).

**Value corrections by document:**
- D4a: 14 lines (test fixtures and helpers using "high"/"medium" → "advancing"/"shifting"/"static")
- D4b: 8 lines (pipeline tests and integration fixtures)
- D3: 2 lines (`_make_entry` helper and summary test)
- D2: 2 lines (`_make_entry` helper and checkpoint test)
- D1: simplify `_delta_disagrees` function, add `delta="shifting"` test

**Context-sensitive mapping:** `claims=[]` → `delta="static"`, `claims=[new]` → `delta="advancing"`. Not a blanket find-replace.

**D1 unchanged:** `LedgerEntry.delta: str` stays str. `validate_ledger_entry(delta: str)` stays str. D1 test values ("new_information", "none", "stable", etc.) stay as-is — they exercise validation with intentionally diverse inputs.

**Ordering dependency:** D4b lines 983, 1005 have `claims=[]` (D4b-9 erratum). If D4b-9 adds claims first, delta mapping for those lines changes.

## 2. Per-Document Fixes

### Manifest

File: `docs/plans/2026-02-15-context-injection-agent-integration-manifest.md`

- [x] **M-1** [Major] Replace D4c contingency triggers (line 69-71) with actionable criteria: (a) after Tasks 13a+13b, first full test run has >25 failures across 4+ modules, (b) two consecutive fix passes still miss items from a fixed checklist (checkpoint ingestion, prospective-state commit, evidence auto-recording, contract doc, integration assertions)
- [x] **M-2** [Minor] Add "Operational Assumptions" section: single-agent, single-flight, short-lived MCP server process
- [x] **M-3** [Minor] Add `pyproject.toml` metadata update (package version, Python floor) to D4a or D4b scope

### D1: Ledger Validation

File: `docs/plans/2026-02-15-context-injection-agent-integration-d1-ledger-validation.md`

- [x] **D1-1** [Minor] Line ~298: Change `ValidationWarning.details: dict | None` to `dict[str, Any] | None`
- [x] **D1-2** [Minor] Line ~42: Clarify test estimate — "200-300" is for all deliveries, D1 specifically yields ~50-70 tests
- [x] **D1-3** [Major] DD-1 resolved: apply 8 D1 edits for base_types extraction (see CC-1). Create `base_types.py` with `ProtocolModel`, `Claim`, `Unresolved`. Update scope statement, file list, step 7, ledger.py import, step 8 run command, commit. Add re-export identity test in `test_types.py`
- [x] **D1-4** [Major] Simplify `_delta_disagrees` function (line ~778) to canonical semantic logic: `"static"` contradicts non-STATIC, `"advancing"`/`"shifting"` contradicts STATIC, unknown falls through. Bug: current function has no handling for `delta="shifting"` — falls through silently. Add test for `delta="shifting"` vs `effective_delta=STATIC` (see CC-8)

### D2: Conversation State

File: `docs/plans/2026-02-15-context-injection-agent-integration-d2-conversation-state.md`

- [x] **D2-1** [Critical] Lines 697-722: Fix `serialize_checkpoint` — embed new `checkpoint_id` into state BEFORE serialization (see CC-3)
- [x] **D2-2** [Critical] Lines 984-1026: Add restore integrity checks to `validate_checkpoint_intake` — validate envelope self-consistency (`state.last_checkpoint_id == envelope.checkpoint_id`), validate request-context binding (request `checkpoint_id` vs envelope id, conversation_id match)
- [x] **D2-3** [Major] Lines 780-781 (Task 7 intro): Update checkpoint chain model language — explicitly state "head-pointer validation model." Mark `parent_checkpoint_id` in `StateCheckpoint` as informational/deferred
- [x] **D2-4** [Major] Lines 398-408: Change collection fields to tuples (`tuple[LedgerEntry, ...] = ()`) and add `extra="forbid"`, `strict=True` to model config. Projection methods use tuple concatenation
- [x] **D2-5** [Major] DD-2 resolved (C-lite): Add docstring to `compute_cumulative_state` (line ~439): "Correct only when compaction has not triggered. See DD-2 invariant." Add docstring to `compact_ledger` (line ~1029): "Unreachable under DD-2 invariant (MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT)."
- [x] **D2-6** [Minor] Lines 720, 725-753: Add `len(checkpoint.payload.encode("utf-8")) == checkpoint.size` check in `deserialize_checkpoint`
- [x] **D2-7** [Minor] Add compaction-equivalence test: prove `compute_action()` on full-history state matches `compute_action()` on compacted state
- [x] **D2-8** [Minor] Add compaction round-trip test: build conversation with >16 entries, compact, restore, recompute cumulative, assert documented contract
- [x] **D2-9** [Minor] Fix prerequisite naming drift (line 15): split into per-module lines — `From context_injection/ledger.py: LedgerEntry, CumulativeState, validation functions` + `From context_injection/enums.py: EffectiveDelta, QualityLabel` (see CC-6 — missing from original ticket)
- [x] **D2-10** [Minor] Normalize delta test values: line 589 `delta="new"` → `"advancing"`, line 906 `delta="new_information"` → `"advancing"` (see CC-8)

### D3: Conversation Control

File: `docs/plans/2026-02-15-context-injection-agent-integration-d3-conversation-control.md`

- [x] **D3-1** [Major] Task 9 Step 3, `compute_action` docstring (line ~373): Document one-shot closing probe policy as explicit design decision
- [x] **D3-2** [Major] Task 9 Step 3, `compute_action` docstring (line ~386): Add "budget_remaining: Turn budget remaining (NOT evidence budget)"
- [x] **D3-3** [Major] Task 10 Step 2, docstring (line ~777): Add precondition: "entries and cumulative must come from same conversation snapshot"
- [x] **D3-4** [Major] Lines 130 and 569: Fix StrEnum literals — `_make_entry` passes `quality="substantive"` (string). With `strict=True`, must use `QualityLabel.SUBSTANTIVE`
- [x] **D3-5** [Major] Line 15: Update prerequisite contract — add `CumulativeState` and `LedgerEntryCounters` to imports from D1. Fix import source to `context_injection.enums`
- [x] **D3-6** [Minor] Task 9 Step 2, `TestComputeActionClosingProbe` (line ~198): Add test for full-cycle re-plateau `[STATIC, STATIC, ADVANCING, STATIC, STATIC]` with `closing_probe_fired=True`
- [x] **D3-7** [Minor] Same location: Add test for same scenario but with unresolved items on latest entry, asserting `CONTINUE_DIALOGUE`
- [x] **D3-8** [Advisory] Line 476: Note that D3 tests hand-build CumulativeState with values inconsistent with entries. Consider builder helper during implementation
- [x] **D3-9** [Minor] Normalize delta test values: line 121 `delta="high"` → `"advancing"`, line 563 `delta="high"` → `"advancing"` (see CC-8)

### D4a: Schema 0.2.0

File: `docs/plans/2026-02-15-context-injection-agent-integration-d4a-schema-020.md`

- [x] **D4a-1** [Critical] Line 357: Fix import cycle per DD-1 decision (see CC-1)
- [x] **D4a-2** [Major] Lines 57-63: Remove stale pre-split text — replace "Five tasks: 11, 12, 13a, 13b, 14" with "Two tasks: 11 (0.2.0 types) and 12 (test shape migration). Tasks 13a/13b/14 are in D4b."
- [x] **D4a-3** [Major] Line 30: Reword backward-compatibility language — "No wire-level backward compatibility: only 0.2.0 is accepted. Compatibility goal is test infrastructure migration (existing helpers compile with new fields), not dual-schema runtime support."
- [x] **D4a-4** [Major] Line 213: Fix `budget_status` phantom field — either add `budget_status: Literal["under_budget", "at_budget", "over_budget"]` to Budget type definition in Step 3, or remove from test example
- [x] **D4a-5** [Major] Line 380: Change `action: str` to `action: Literal["continue_dialogue", "closing_probe", "conclude"]`
- [x] **D4a-6** [Minor] Lines 19-22: Reword D2 prerequisite as runtime/semantic dependency, not direct schema import
- [x] **D4a-7** [Minor] Add explicit test for turn-1 checkpoint generation (TurnPacketSuccess requires `state_checkpoint` and `checkpoint_id` with no defaults)
- [x] **D4a-8** [Major] Add `turn_cap_exceeded` to `ErrorDetail.code` literal type (line ~341) and test parametrize list (line ~235). 0.2.0 schema only (see CC-5/DD-2)
- [x] **D4a-9** [Major] Change `delta: str` to `delta: Literal["advancing", "shifting", "static"]` (line 325). Add validation test: `delta="high"` raises `ValidationError` (see CC-8)

### D4b: Pipeline + Execute + Test Migration

File: `docs/plans/2026-02-15-context-injection-agent-integration-d4b-pipeline-execute-test-migration.md`

- [x] **D4b-1** [Critical] Line 510: Fix budget parameter — add `MAX_CONVERSATION_TURNS` constant, compute `turn_budget_remaining`, pass to `compute_action` (see CC-4)
- [x] **D4b-2** [Critical] Lines 479-488: Fix `validate_ledger_entry` call — change `prior_cumulative=prior_cumulative` to `prior_claims=prior_claims, unresolved_closed=unresolved_closed`. Compute `prior_claims` from `base.get_cumulative_claims()` (available at line 402)
- [x] **D4b-3** [Critical] Lines 490-501: Replace warning-filter logic with `try/except LedgerValidationError` handler that returns `TurnPacketError(code="ledger_hard_reject", ...)`
- [x] **D4b-4** [Critical] Lines 351-367: Add `except LedgerValidationError as exc` to error handler (currently only catches `CheckpointError` and generic `Exception`)
- [x] **D4b-5** [Major] Lines 146-152: Fix hard-reject test trigger — change from empty position (soft warn in D1) to empty claims list or `turn_number=0` (actual hard reject per D1)
- [x] **D4b-6** [Major] Line 480: Add `unresolved_closed` computation and pass to `validate_ledger_entry`
- [x] **D4b-7** [Major] Lines 698, 727, 917: Fix `execute_scout` argument order — change `execute_scout(scout_req, ctx)` to `execute_scout(ctx, scout_req)` (matches actual signature at `execute.py:497`)
- [x] **D4b-8** [Major] Lines 909, 691, 720: Fix vacuous integration tests — add `assert len(template_candidates) > 0` before Call 2 block. Use deterministic fixtures guaranteeing template matching
- [x] **D4b-9** [Major] Line 1004: Fix test that passes `claims=[]` expecting `status == "success"` — D1 hard-rejects empty claims
- [x] **D4b-10** [Minor] Line 16: Update prerequisite text to reference xfail inventory from D4a (per CC-2)
- [x] **D4b-11** [Minor] Line 253: Verify dedupe test entity_key shape against canonical format in `canonical.py`
- [x] **D4b-12** [Major] Update 8 delta test values from "high"/"medium"/"low" to "advancing"/"shifting"/"static" with context-sensitive mapping: `claims=[]` → `"static"`, `claims=[new]` → `"advancing"` (see CC-8). Lines: 137, 590, 849, 900, 940, 959, 983, 1005. D4b-9 ordering dependency for lines 983, 1005
- [x] **D4b-13** [Major] Pipeline 18-step → 17-step: remove step 15 (dual-write — eliminated by CC-3 serialize_checkpoint redesign), renumber steps 16-18 to 15-17. Update all "18-step" references (lines 278, 374, 632)
- [x] **D4b-14** [Major] Add pre-append turn cap guard at step 4.5 (after checkpoint intake, before entity extraction): `if len(base.entries) >= MAX_CONVERSATION_TURNS: return TurnPacketError(code="turn_cap_exceeded")` (see CC-4/CC-5/DD-2)
- [x] **D4b-15** [Major] Add D4b done criteria: "No temporary D4a semantic markers remain: no pytest xfail with reason prefix `D4b:` exists in tests" (see CC-2)

### D5: Agent Rewrite

File: `docs/plans/2026-02-15-context-injection-agent-integration-d5-agent-rewrite.md`

- [x] **D5-1** [Critical] Lines 87-88, 131: Fix dangling fallback — preserve old 3-step manual loop as "Fallback Mode: Legacy Manual Loop" subsection. Include mode gating: start in `server_assisted`, switch to `manual_legacy` if context injection tools unavailable
- [x] **D5-2** [Critical] Line 292: Fix "weakest claim" — agent must retain per-turn `validated_entry` objects. "Weakest claim" derived from accumulated claim history, not aggregate counters
- [x] **D5-3** [Critical] Lines 131-138, 331-342: Add explicit per-turn state retention for Phase 3 — after each `process_turn` response, store `validated_entry`, `cumulative` snapshot, and scout outcomes in a per-turn list
- [x] **D5-4** [Critical] Lines 239-245: Add `checkpoint_invalid` to error recovery table. Fix checkpoint retry: max 1 per turn regardless of error code. For `checkpoint_stale`, retry only with different checkpoint pair. For `checkpoint_missing`, retry only if non-null checkpoint available. Otherwise synthesize
- [x] **D5-5** [Major] Line 270: Fix field name — change `file_result` to `read_result` (matches protocol contract and execute module)
- [x] **D5-6** [Major] Lines 252-255: Add clarifier handling — if top candidate has `scout_options: []`, skip scouting, use clarifier question in follow-up composition instead
- [x] **D5-7** [Major] Line 273: Fix codex-reply failure path — if final `process_turn` also errors, synthesize from whatever data was collected in earlier turns (don't dead-end)
- [x] **D5-8** [Major] Add unknown-action fallback: unknown action → treat as `conclude` and log warning
- [x] **D5-9** [Major] Add closing_probe fallback when `validated_entry.unresolved` is empty: target unresolved item → highest-impact claim → core thesis summary question
- [x] **D5-10** [Major] Add `ledger_hard_reject` retry cap: maximum one retry per turn
- [x] **D5-11** [Major] Document server action vs agent turn budget precedence: agent cap takes priority, exhausted budget → `conclude`
- [x] **D5-12** [Minor] Add clarifying note for focus.claims: "On subsequent turns, focus.claims contains claims relevant to current focus scope"
- [x] **D5-13** [Major] DD-4 resolved: de-scope reframe model. Add explicit rationale (design spec flags detection as unsolved, Section 12). Add target-lock guardrail to Step 6: "When scout evidence is available, the follow-up question MUST target the claim or unresolved item that triggered the scout. Other observations MAY be noted in disposition but MUST NOT change the question's target." Document known tradeoff (one-turn delay on side findings) and future path (server-side `reframe_outcome` field)
- [x] **D5-14** [Major] Add `turn_cap_exceeded` to error recovery table: no retry, proceed to Phase 3 synthesis (see CC-5/DD-2)
- [x] **D5-15** [Major] Add agent-side budget override (defense-in-depth): `effective_budget = min(max(1, user_budget), MAX_CONVERSATION_TURNS)`. Step 5: if `turn_count >= effective_budget`, treat any server action as `conclude`. Document as interim measure (see CC-4)

### Decisions Document

File: `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md`

- [x] **DEC-1** [Major] 4 edits for `parent_checkpoint_id` removal (see CC-7): (1) line 31 chain validation bullet: "enables" → "reserved for future (not used in 0.2.0)"; (2) line 38 stale error: reference head-pointer model, not parent-chain; (3) lines 178-179 TurnRequest shape: remove field, add comment; (4) cross-ref to D2-3 for remaining chain-model language

### Planning Brief

File: `docs/plans/2026-02-15-context-injection-agent-integration-planning-brief.md`

- [x] **PB-1** [Minor] Line 266: Remove `parent_checkpoint_id` from TurnRequest field list (see CC-7)

## 3. Post-Fix Follow-Up Items

Not blockers for plan fix pass, but should be tracked:

- [ ] **FU-1** Add `tests/test_codex_dialogue_protocol_gate.py` as a follow-up task after D5 ships — static protocol conformance linting of agent markdown against server schema
- [ ] **FU-2** Verify `scout_option` shape consistency between D4b plan snippets and protocol contract during D4b implementation
- [ ] **FU-3** During D2 implementation, verify concurrent `process_turn` on same conversation_id is documented as relying on single-flight assumption

## 4. Design Decisions Required

These must be resolved before certain fixes can be applied.

### DD-1: Import Cycle Resolution Strategy

**Blocks:** CC-1, D4a-1, D1-3

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A: base_types extraction | Extract `ProtocolModel`, `Claim`, `Unresolved`, `EvidenceRecord` to `context_injection/base_types.py`. Both `types.py` and `ledger.py` import from it | Permanent fix, clean import graph | Touches D1's scope retroactively, adds a new module |
| B: TYPE_CHECKING tactical | Use `TYPE_CHECKING` guard in `types.py` with `from __future__ import annotations`, add `model_rebuild()` bootstrap in D4b | Contained to D4a, no D1 changes | Fragile with Pydantic v2 nested models, requires careful bootstrap |

**Recommendation:** Option A. The cycle is structural and will persist; a tactical workaround just defers the problem.

**Resolved: Option A (base_types extraction).** Confirmed via adversarial Codex dialogue (thread `019c64ca-fe7f-70c2-a26a-e8e667997e7f`). High confidence — both sides converged independently.

Specifics:
- `base_types.py` contains exactly 3 types: `ProtocolModel`, `Claim`, `Unresolved`
- `EvidenceRecord` stays in `types.py` (not needed to break the cycle; may be removed in 0.2.0)
- `types.py` re-exports all 3 types — preserves existing import paths, zero churn for D2/D3/D5
- Import DAG: `base_types.py` → `ledger.py` + `types.py` (no cycles)
- D1 plan edit: `ledger.py` imports `ProtocolModel`, `Claim`, `Unresolved` from `base_types` instead of `types`
- "Scope concern" dismissed: D1 is an unimplemented plan, not shipped code — this is a markdown edit

### DD-2: Compaction Cumulative Semantics

**Blocks:** CC-5, D2-5

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A: Windowed semantics | Accept that cumulative is "last N entries" after compaction. Document this. Possibly rename field | Zero implementation cost, honest contract | Violates decisions doc promise of "running totals" |
| B: Prefix counters | Add 6-7 carry-forward fields to ConversationState that accumulate pre-compaction totals | Correct lifetime totals | ~20-40 extra tests, moderate scope increase |
| C: Defer entirely | Note as known limitation. With 15-turn hard cap and 16-entry compaction threshold, compaction never triggers in practice | Zero cost, pragmatically correct | Latent bug if turn cap changes |

**Recommendation:** Option C for this implementation pass. The 15-turn cap (D3 `compute_action`) means `MAX_ENTRIES_BEFORE_COMPACT=16` never triggers. Document the constraint explicitly and add a compaction-equivalence test that asserts the current invariant. Revisit if turn cap changes.

**Resolved: Option C-lite (enforced non-trigger contract).** Confirmed via adversarial Codex dialogue (thread `019c64cb-7b5a-71a3-93dd-9f1cd70360ca`). High confidence. Bare Option C is insufficient — the 15-turn cap was agent-only, not server-enforced. C-lite piggybacks on the already-planned CC-4 fix (D4b-1 adds `MAX_CONVERSATION_TURNS`).

Three additions beyond bare Option C:
1. Static invariant: `MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT` (strict `<`, not `<=`)
2. Pre-append guard in pipeline: reject turn when `len(base.entries) >= MAX_CONVERSATION_TURNS` → `TurnPacketError(code="turn_cap_exceeded")`
3. `turn_cap_exceeded` error code propagated through D4a schema, D4b pipeline, D5 agent handling

Cross-cutting plan changes required:
- **D2**: Document that `compute_cumulative_state` is correct only when compaction has not triggered
- **D4a**: Add `turn_cap_exceeded` to `ErrorDetail.code` literal type
- **D4b**: Add pre-append guard before `with_turn()`; add static invariant assertion
- **D5**: Add agent handling for `turn_cap_exceeded` — no retry, proceed to synthesis/conclude

Tests (6-8): constant invariant, below-cap success, at-cap rejection, no-mutation-on-reject, repeated-turn bound, checkpoint-restore-at-cap.

B-lite (~35 LOC, ~8 tests) tracked as planned technical debt. Triggers: (1) any change to turn cap or compaction threshold, (2) alternate clients, (3) config-independent "running totals" requirement.

### DD-3: Conversations Dict Eviction

**Blocks:** Manifest review finding #3

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A: Add cap in D2 | Add `MAX_CONVERSATIONS` limit with oldest-eviction to `AppContext.conversations` | Bounded memory | 1-3 conversations per MCP session makes this mostly dead code |
| B: Explicit defer | Document as deferred to v0.3 with rationale (short-lived process, 1-3 conversations) | Honest, zero implementation | Becomes real if process lifetime assumptions change |

**Recommendation:** Option B. MCP server is short-lived (single session). Document the assumption.

**Resolved: Hybrid — Option B (defer eviction) + fail-fast guard.** Confirmed via adversarial Codex dialogue (thread `019c64cb-0bc1-7383-81a1-8dc362990cfc`). High confidence.

Eviction rejected: evicting a `ConversationState` silently destroys ledger history and checkpoint chain integrity — categorically worse than store record eviction. The "consistency" argument does not apply.

Warning-only logging rejected: MCP servers run as subprocesses with no stderr monitoring path. Fail-fast or nothing.

Resolution:
- No eviction policy
- Add `CONVERSATION_GUARD_LIMIT = 50` with `RuntimeError` on new-conversation creation exceeding limit
- 3 tests: below-limit create, overflow on new ID, existing ID returns at limit
- Document operational assumptions (session-scoped process, 1-3 conversations expected)
- Revisit triggers: cross-session process reuse, observed high cardinality, transport architecture changes

### DD-4: D5 Reframe Model Scope

**Blocks:** D5-13

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A: Add reframe logic | Add 3-way branch on evidence impact (focus answered / premise falsified / enrichment) | Matches design spec Step 6 | Increases 7-step loop complexity |
| B: Document de-scope | Collapse reframe into "frame question around evidence" with explicit rationale | Simpler agent instructions | Loses some design spec fidelity |

**Recommendation:** Option B. The evidence shape in Step 6 already forces evidence-first question composition. Server can add `reframe_outcome` field in a future version for more explicit control.

**Resolved: Option B (de-scope) + target-lock guardrail.** Confirmed via adversarial Codex dialogue (thread `019c64cb-94f4-7983-9ef9-a22568a3b27f`). High confidence.

De-scope rationale: The design spec itself flags reframe outcome detection as an unsolved problem (Section 12, Medium Priority). Unreliable classification in dense agent instructions creates more harm than benefit.

Add one guardrail line to D5 Step 6:
> "When scout evidence is available, the follow-up question MUST target the claim or unresolved item that triggered the scout. Other observations from the evidence MAY be noted in the disposition field but MUST NOT change the question's target."

This closes the enrichment hijack risk (tangential evidence drifting the conversation) without reintroducing classification.

Known tradeoff: occasional one-turn delay on important side findings from scout evidence. Acceptable because side findings are captured in the disposition field and become new unresolved items for later prioritization.

Future path: server-side `reframe_outcome` field (deterministic classification with cross-turn state) if explicit outcome routing proves necessary.

## 5. Acceptance Criteria

All items in Sections 1-2 checked off:

- [x] All cross-cutting issues (CC-1 through CC-8) addressed
- [x] All per-document fixes applied (M, D1, D2, D3, D4a, D4b, D5, DEC items)
- [x] All 4 design decisions resolved (DD-1 through DD-4)
- [x] Documents internally consistent — no file references another file's content contradictorily
- [x] Grep for known error patterns:
  - `prior_cumulative` should not appear in D4b (replaced by `prior_claims`)
  - `generate_summary` should be `generate_ledger_summary` everywhere
  - `file_result` should be `read_result` in D5
  - `execute_scout(scout_req, ctx)` should be `execute_scout(ctx, scout_req)` in D4b
  - `delta="high"`, `delta="medium"`, `delta="low"` should not appear in D4a/D4b (replaced by canonical vocabulary)
  - `parent_checkpoint_id` should not appear in TurnRequest shape in decisions doc
  - `"18-step"` should not appear in D4b (replaced by "17-step" after CC-3)
  - `from context_injection/ledger.py` for enums should be `from context_injection/enums.py` in D2/D3/D4a prereqs
- [ ] Commit on `fix/reconstruct-plan` branch
- [ ] Then merge `fix/reconstruct-plan` → `main`

## 6. References

### Plan Documents

| Document | Path |
|----------|------|
| Manifest | `docs/plans/2026-02-15-context-injection-agent-integration-manifest.md` |
| D1 | `docs/plans/2026-02-15-context-injection-agent-integration-d1-ledger-validation.md` |
| D2 | `docs/plans/2026-02-15-context-injection-agent-integration-d2-conversation-state.md` |
| D3 | `docs/plans/2026-02-15-context-injection-agent-integration-d3-conversation-control.md` |
| D4a | `docs/plans/2026-02-15-context-injection-agent-integration-d4a-schema-020.md` |
| D4b | `docs/plans/2026-02-15-context-injection-agent-integration-d4b-pipeline-execute-test-migration.md` |
| D5 | `docs/plans/2026-02-15-context-injection-agent-integration-d5-agent-rewrite.md` |
| Decisions | `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md` |

### Codex Dialogue Thread IDs

**Round 1: Individual + transition reviews (session 12)**

| Review | Thread ID |
|--------|-----------|
| Manifest | `019c6488-1442-7201-98fb-864869a41c78` |
| D1 | `019c6488-1124-72c3-a5e3-46e86cd0ae6b` |
| D3 | `019c6488-333b-7350-ac2b-f18cd77dd120` |
| D2 | `019c6488-5658-7a53-8b0e-6b0ad5825e5d` |
| D4a | `019c6494-7d92-7d02-87dc-f7bf9e2cceb9` |
| D4b | `019c6495-3ad3-7f43-9d1a-1362020e1c2a` |
| D5 | `019c6494-de0d-75c0-9a2f-3768011c867a` |
| D1→D3 | `019c64a3-2d9e-7962-8389-0d64d1138439` |
| D3→D2 | `019c64a3-3904-7233-9569-84fa8e5ecb73` |
| D2→D4a | `019c64a3-d33c-7270-a87d-7a380e3d1f73` |
| D4a→D4b | `019c64a3-f668-7ac3-87fa-86339f748a20` |
| D4b→D5 | `019c64a4-63f5-7b02-ad89-a69f87bba30c` |

**Round 2: Design decision verification (session 13)**

| Decision | Thread ID |
|----------|-----------|
| DD-1: Import cycle | `019c64ca-fe7f-70c2-a26a-e8e667997e7f` |
| DD-2: Compaction | `019c64cb-7b5a-71a3-93dd-9f1cd70360ca` |
| DD-3: Eviction | `019c64cb-0bc1-7383-81a1-8dc362990cfc` |
| DD-4: Reframe | `019c64cb-94f4-7983-9ef9-a22568a3b27f` |

**Round 3: Cross-cutting issue verification (session 13)**

| Issue | Thread ID |
|-------|-----------|
| CC-1: Import cycle fix | `019c64e1-797e-7990-bd53-6da70d57090f` |
| CC-2: Gate contradiction | `019c64e1-32be-79e1-84f2-84e3e14ab896` |
| CC-3: Checkpoint bug | `019c64e1-d1ce-7ec1-b0b1-3be430a0e3c1` |
| CC-5: Compaction contract | `019c64e2-637d-76f1-a622-6f38b4bf9ffc` |
| CC-6: Naming drift | `019c64e2-5b87-7c12-9e91-e8b1e4a1dc4c` |
| CC-7: Checkpoint ID drift | `019c64e2-2b50-7863-84f2-56bf103b4058` |
