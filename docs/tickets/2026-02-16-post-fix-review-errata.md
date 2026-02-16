# T-002: Post-Fix Review Errata — Context Injection Agent Integration

```yaml
id: T-002
date: 2026-02-16
status: closed
priority: high
branch: docs/post-fix-review-errata
blocked_by: []
blocks: [implementation of D1-D5]
related: [T-001]
```

## Summary

Post-fix Codex review of the 9 corrected plan documents found **45 unique issues** (16 blocking, 17 should-fix, 12 advisory). The plan architecture remains sound — no structural redesign needed. Findings are concentrated in three categories: (1) contract regressions in the CC-1 base_types extraction, (2) missing parameters at cross-document boundaries, and (3) under-specified test code in D4a/D4b.

Four findings are **genuinely new** — not caught in T-001's 3 prior review rounds (12 individual/transition reviews + 4 DD verifications + 8 CC verifications):
1. D5 clarifier-skip bug (B15)
2. Budget.budget_status scope contradiction (B10/CC-PF-1)
3. test_canonical.py gap (B12)
4. Dual claims channel divergence (S17/CC-PF-3)

**Scope:** Fix plan documents only. No code changes.

**Work estimate:** ~100-150 targeted edits across 8 files.

## Context

Twelve independent Codex dialogue reviews were conducted on the errata-corrected documents (post-T-001 fix pass, merged at `984ddba`):
- 7 individual document reviews (manifest, D1, D2, D3, D4a, D4b, D5)
- 5 transition reviews (D1->D3, D3->D2, D2->D4a, D4a->D4b, D4b->D5)

This mirrors the T-001 Round 1 review structure. All 12 dialogues converged (most by turn 5-6 of 6 budget). Issues found by multiple independent reviews carry highest confidence.

**Source session:** Handoff `2026-02-16_01-14_errata-applied-plan-merged-to-main.md` (archived).

## Prerequisites

Before starting fixes:
1. Read the manifest: `docs/plans/2026-02-15-context-injection-agent-integration-manifest.md`
2. No design decisions to resolve (all findings have clear fixes)
3. Create branch from `main` for fix application

## 1. Cross-Cutting Issues

Issues affecting multiple documents. Fix all instances when addressing each.

### CC-PF-1: Budget.budget_status scope contradiction [BLOCKING]

**Found by:** D2->D4a transition, D4a->D4b transition

D4a adds a required `budget_status: Literal["under_budget", "at_budget", "over_budget"]` field to `Budget`. But `compute_budget()` in `templates.py:108` and `execute.py:182` construct `Budget()` without this field. D4a's scope explicitly forbids modifying `pipeline.py`, `execute.py`, or `server.py`. D4b's plan doesn't mention updating the producers either. The `Budget()` construction failures are Category 1 per D4a's own triage rules (shape failures — fix immediately, not xfail).

**Resolution:** Expand D4a scope minimally. Add `templates.py` and `execute.py` to D4a "Modify" scope, limited to Budget compatibility. Update done criteria from "No changes to pipeline.py, execute.py, or server.py" to "No changes to pipeline.py or server.py; execute.py and templates.py changes limited to Budget compatibility."

**Alternative considered:** Derived-default approach (`mode="before"` validator backfills `budget_status` from `evidence_remaining`). Cleaner but adds Pydantic validator complexity. Either approach works — choose during implementation.

**5 edits across 1 file (D4a):**
1. Files in Scope: add `context_injection/templates.py` and `context_injection/execute.py` to Modify list
2. Done criteria: update scope exclusion text
3. Task 11 or 12: add substep to update both `compute_budget()` return values with `budget_status`
4. Commit step: add `templates.py` and `execute.py` to `git add`
5. D4a scope text line 53: update "out of scope" declaration

**Test file impact:** `test_types.py:223` and `test_canonical.py:151` construct `Budget()` directly — must also add `budget_status`. Covered by D4a-PF-4 and D4a-PF-5.

### CC-PF-2: Scout-option shape mismatch in test snippets [BLOCKING]

**Found by:** D4b review, D4b->D5 transition

D4b test snippets at lines 728, 951 construct `ScoutRequest` using `candidate.scout_option_id` / `.scout_token` / `.turn_request_ref`. The actual type `TemplateCandidate` (types.py:243) has nested `scout_options: list[ReadOption | GrepOption]`, not flat fields. `turn_request_ref` is agent-derived from `"{conversation_id}:{turn_number}"`, not a TemplateCandidate field. D5's Step 3 response table also lists `turn_request_ref` as a field of `template_candidates`.

**Edits across 2 files (D4b + D5):**

D4b (4 edits):
1. Lines 728-730: change `candidate.scout_option_id` to `candidate.scout_options[0].id`
2. Same: change `candidate.scout_token` to `candidate.scout_options[0].scout_token`
3. Same: derive `turn_request_ref` from `f"{request.conversation_id}:{request.turn_number}"`
4. Lines 949-954: same fixes for Task 14 integration test snippet

D5 (1 edit):
5. Step 3 "Fields agent reads from template_candidates": remove `turn_request_ref`, add note that it is agent-derived in Step 4

### CC-PF-3: Dual claims channel divergence risk [SHOULD-FIX]

**Found by:** D4b->D5 transition (NEW — not in T-001)

D4b pipeline extracts entities from `request.focus.claims` (line 448) but validates ledger from top-level `request.claims` (line 525). D5 instructs the agent to "set focus.claims and top-level claims to the same list" but provides no enforcement. If these diverge, entity extraction and ledger validation operate on different data — silent wrong results.

**Edits across 2 files (D4b + D5):**

D4b (1 edit):
1. Add equality guard early in `_process_turn_inner`: if `request.focus.claims != request.claims` or `request.focus.unresolved != request.unresolved`, return `TurnPacketError(code="ledger_hard_reject")`

D5 (1 edit):
2. Strengthen instruction at line 232: replace "Set focus.claims and top-level claims to the same list" with explicit build-once-assign-twice pattern

## 2. Per-Document Fixes

### Manifest

File: `docs/plans/2026-02-15-context-injection-agent-integration-manifest.md`

- [x] **M-PF-1** [Should-fix] Lines 57-62: Add explicit gate checks for errata-fixed items. D1 gate: add "base_types extraction complete, re-export identity verified." D2 gate: add "checkpoint restore guards pass (4 validation checks)." D4b gate: add "no `D4b:` xfail markers remain in tests."
- [x] **M-PF-2** [Should-fix] Line 33-34: Annotate D4b dependency — "D4b also directly imports D1/D2/D3 runtime modules; D4a provides schema integration but not full encapsulation"
- [x] **M-PF-3** [Advisory] Lines 103-104: Reconcile test estimate — "~400-580 new" doesn't match per-delivery estimates. Either sum actuals or remove global estimate
- [x] **M-PF-4** [Advisory] Lines 66-71: Contingency section stale — line counts (~971/~241) are pre-errata; trigger framing ("context budget exceeded") doesn't match actual trigger mechanics (test-failure thresholds)
- [x] **M-PF-5** [Advisory] Line 122: Remove server.py from deliverables (no task covers it; Resolved Question #2 confirms stable signature) or add verification step
- [x] **M-PF-6** [Should-fix] Line 129: pyproject.toml assigned to D4b but absent from D4b scope/tasks/commits (see D4b-PF-6)

### D1: Ledger Validation

File: `docs/plans/2026-02-15-context-injection-agent-integration-d1-ledger-validation.md`

- [x] **D1-PF-1** [Blocking] Line 298: Add `strict=True` to `ProtocolModel` ConfigDict — existing `types.py` uses `ConfigDict(extra="forbid", strict=True, frozen=True)`. Omission allows type coercion that protocol types reject, affecting D2's checkpoint deserialization path
- [x] **D1-PF-2** [Blocking] Line 305: Change `Claim.status: str` to `status: Literal["new", "reinforced", "revised", "conceded"]` — matches existing `types.py` Claim. Widening to `str` is a contract regression that cascades through D3's `compute_counters` (silent miscount -> wrong effective_delta -> premature plateau detection)
- [x] **D1-PF-3** [Blocking] Lines 331-334: Add `from typing import Any` to ledger.py imports — `ValidationWarning.details: dict[str, Any] | None` at line 366 uses `Any` without importing it. Causes `NameError` at import time
- [x] **D1-PF-4** [Blocking] base_types.py imports: Add `from typing import Literal` — required by D1-PF-2 fix. Current spec only imports from pydantic
- [x] **D1-PF-5** [Should-fix] Line 24: Change "new error codes" to "three new enum classes" — D1 adds `EffectiveDelta`, `QualityLabel`, `ValidationTier`. Error code expansion belongs to D4a/D4b
- [x] **D1-PF-6** [Should-fix] `LedgerEntryCounters` and `CumulativeState` count fields: Add `Field(ge=0)` annotations. Add guard in `compute_counters` for negative `unresolved_closed`
- [x] **D1-PF-7** [Should-fix] Task 3 `validate_ledger_entry`: Add structural chronology checks — reject if any `claim.turn < 1` or `claim.turn > turn_number`. Status-conditioned checks deferred to D4a
- [x] **D1-PF-8** [Should-fix] Task 3 prose: Add note documenting intentional tolerance of unknown delta values: "Unknown delta values are tolerated in D1. Stricter validation (Literal constraint) deferred to D4a when schema 0.2.0 introduces a constrained delta field."
- [x] **D1-PF-9** [Should-fix] Add 6 missing test specifications: (1) strictness preservation (re-exported Claim rejects type coercion), (2) invalid claim status rejection, (3) `_delta_disagrees` truth table (all 9 canonical combinations + unknown), (4) LedgerEntry/CumulativeState immutability, (5) negative counter rejection, (6) quality=SUBSTANTIVE + effective_delta=STATIC documentation test

### D2: Conversation State

File: `docs/plans/2026-02-15-context-injection-agent-integration-d2-conversation-state.md`

- [x] **D2-PF-1** [Blocking] Line 1108: Change `from context_injection.action import compute_action` to `from context_injection.control import compute_action`. Lines 1121-1126: Change `compute_action(cumulative=full_cumulative, ...)` to `compute_action(entries=list(full.entries), budget_remaining=..., closing_probe_fired=...)` — matches D3's actual signature. (See CC-PF-2 in T-001 — this was found by 3 reviews)
- [x] **D2-PF-2** [Blocking] Task 8 `get_or_create_conversation` (lines 1390-1401): Add `CONVERSATION_GUARD_LIMIT = 50` constant and overflow check before creating new entries. Add 3 tests (below-limit create, overflow on new ID, existing ID returns at limit). DD-3 resolution was in T-001 errata ticket but never propagated to Task 8
- [x] **D2-PF-3** [Should-fix] `test_corrupt_payload_raises`: payload `"not valid json"` has byte length 14 but `size=15` — size mismatch check fires first, payload-parse branch never reached. Either split into two tests or set `size=14`
- [x] **D2-PF-4** [Should-fix] (a) Prerequisite contract lines 14-17: add `LedgerEntryCounters` to imports. (b) Task 5 intro line 67: `ConfigDict(frozen=True)` should be `ConfigDict(frozen=True, extra="forbid", strict=True)`
- [x] **D2-PF-5** [Should-fix] `TestCompactionEquivalence`: expand from single ADVANCING-only case to parameterized cases covering all `compute_action` branches (plateau+probe, plateau+no_probe, plateau+unresolved, budget exhausted). Add explicit invariant assertion: `KEEP_RECENT_ENTRIES >= MIN_ENTRIES_FOR_PLATEAU`

### D3: Conversation Control

File: `docs/plans/2026-02-15-context-injection-agent-integration-d3-conversation-control.md`

- [x] **D3-PF-1** [Should-fix] Lines 383, 391, 399, 817: Change `list[LedgerEntry]` to `Sequence[LedgerEntry]` — D2 stores entries as `tuple[LedgerEntry, ...]`. `Sequence` matches D3's pure/read-only contract. Update `_is_plateau` and `_has_open_unresolved` similarly
- [x] **D3-PF-2** [Should-fix] Add 4 missing precedence/interaction tests: (1) `compute_action([], budget_remaining=0)` returns CONCLUDE, (2) budget=0 + plateau + unresolved returns CONCLUDE, (3) closing probe at budget=1 then budget=0 forces CONCLUDE, (4) unresolved-latest-only behavior lock-in test

### D4a: Schema 0.2.0

File: `docs/plans/2026-02-15-context-injection-agent-integration-d4a-schema-020.md`

- [x] **D4a-PF-1** [Blocking] Lines 173-188: `test_invalid_delta_rejected` uses `delta="static"` which is a valid Literal value — test passes vacuously. Change to `delta="high"` or `delta="medium"` to test that pre-canonical values are rejected
- [x] **D4a-PF-2** [Blocking] Line 725: git add omits `packages/context-injection/tests/xfail_inventory_d4a.md`. Line 38: "Create: None" contradicts done criteria requiring xfail inventory. Fix: add file to git add, change "Create: None" to "Create: `tests/xfail_inventory_d4a.md`"
- [x] **D4a-PF-3** [Blocking] Budget.budget_status scope contradiction — see CC-PF-1. Expand D4a scope to include `templates.py` and `execute.py` for Budget compatibility
- [x] **D4a-PF-4** [Blocking] Task 11 Step 5 / Task 12: test_types.py migration under-specified. Only mentions version string changes but actual file has 6+ locations needing migration: old TurnRequest fixtures using `context_claims`/`evidence_history` (lines 109, 116, 129, 145-156), Budget construction without `budget_status` (line 223), hardcoded `"0.1.0"` in packet/result payloads (lines 360, 378, 394, 427, 447)
- [x] **D4a-PF-5** [Blocking] `tests/test_canonical.py` not in D4a scope. Line 151 constructs `Budget(evidence_count=1, evidence_remaining=4, scout_available=True)` without `budget_status`. Line 153 asserts exact dumped keys. Both break after D4a adds `budget_status`. Add to D4a Files in Scope, Task 12 file list, and commit staging
- [x] **D4a-PF-6** [Should-fix] Line 21: Change "ConversationState from context_injection/conversation.py -- embedded in TurnPacketSuccess" to "-- transported as opaque checkpoint string in TurnPacketSuccess.state_checkpoint (not embedded directly)"
- [x] **D4a-PF-7** [Should-fix] Task 12: Add note that `SchemaVersionLiteral` change cascades to Scout type constructors in test files. Checklist should include: update all hardcoded `"0.1.0"` strings in tests to `SCHEMA_VERSION` or `"0.2.0"`
- [x] **D4a-PF-8** [Advisory] Line 452: `action` field uses duplicated `Literal["continue_dialogue", "closing_probe", "conclude"]` instead of `ConversationAction` enum from `control.py`. Either use enum or add parity test
- [x] **D4a-PF-9** [Should-fix] Lines 693-710 (Task 12 Step 7): Add one clarifying rule to xfail triage — "shape failures in runtime producers within D4a's expanded scope (Budget in templates.py, execute.py) are Category 1: fix immediately"

### D4b: Pipeline + Execute + Test Migration

File: `docs/plans/2026-02-15-context-injection-agent-integration-d4b-pipeline-execute-test-migration.md`

- [x] **D4b-PF-1** [Blocking] Line ~420: Add `target_conversation_id=request.conversation_id` to `validate_checkpoint_intake` call. Without this, D2's guard #4 (cross-conversation checkpoint swap detection) is a no-op. Add pipeline-level test for cross-conversation checkpoint rejection. (Found by D2, D3->D2, D4a->D4b — 3 reviews)
- [x] **D4b-PF-2** [Blocking] Lines 728-731, 949-954: Fix scout-option shape — see CC-PF-2. Change `candidate.scout_option_id` to `candidate.scout_options[0].id`, etc.
- [x] **D4b-PF-3** [Blocking] Add CC-3 test matrix (4 tests: consistent triplet, two-turn chain, restart chain, cross-conversation reject) and CC-5 test matrix (6 tests: constant invariant, below-cap success, at-cap rejection, no-mutation-on-reject, repeated-turn bound, checkpoint-restore-at-cap). Manifest review gate requires "guard tested"
- [x] **D4b-PF-4** [Blocking] Snippet syntax: (a) Line 697: `(tmp_path / "src" / "app.py").mkdir(parents=True, exist_ok=True)` creates directory named `app.py` — should be `(tmp_path / "src").mkdir(...)` then `.write_text(...)`. (b) Line 768: `assert len(evidence) >= 1` over-indented — `IndentationError` if copied verbatim
- [x] **D4b-PF-5** [Should-fix] Line 1067: Protocol contract update checklist omits `turn_cap_exceeded`. Add to error codes list. Also add `Budget.budget_status` to TurnPacketSuccess changes
- [x] **D4b-PF-6** [Should-fix] Line 42: Add `pyproject.toml` to Files in Scope. Add version-bump step to Task 14 (manifest line 129 assigns it to D4b but D4b has no task step)
- [x] **D4b-PF-7** [Should-fix] Add xfail removal verification step: `grep -r 'reason="D4b:' tests/ && echo "FAIL: D4b xfails remain" && exit 1` — done criteria require no D4b xfails but no verification step enforces it
- [x] **D4b-PF-8** [Advisory] Checkpoint atomicity gap: evidence recorded by `execute_scout` updates in-memory state but not the checkpoint returned to client. On server restart, restored state loses execute-recorded evidence. Low-probability under "short-lived MCP server process" assumption. Document as known limitation

### D5: Agent Rewrite

File: `docs/plans/2026-02-15-context-injection-agent-integration-d5-agent-rewrite.md`

- [x] **D5-PF-1** [Blocking] Line 272: Clarifier-skip bug — Step 4 gates entirely on `budget.scout_available`, but clarifiers don't consume evidence budget. When scout budget is exhausted but clarifier `template_candidates` exist, they're silently skipped. Fix: skip Step 4 only when `template_candidates` is empty. When `budget.scout_available` is false, still perform clarifier check (step 4.2) but skip scout execution (steps 4.3-4.6). **(NEW — not in T-001)**
- [x] **D5-PF-2** [Blocking] Line 368: codex-reply failure path not implementable — `process_turn` cannot be called again after codex-reply failure (no new Codex response to extract from). Fix: replace with "proceed directly to Phase 3 synthesis using turn_history"
- [x] **D5-PF-3** [Should-fix] Lines 257-267: Server crash after successful `process_turn` underspecified. Add error recovery table row: "Transport/tool failure (after prior success) | Do not switch to manual_legacy. Proceed to Phase 3 (Synthesis) using turn_history."
- [x] **D5-PF-4** [Should-fix] Lines 261, 451: Checkpoint retry wording mismatch — spec says "different checkpoint pair" while test checklist says "null checkpoint." Align both to: "Retry once with state_checkpoint=null and checkpoint_id=null."
- [x] **D5-PF-5** [Should-fix] Step 5 additions to Phase 3 (line 371): Phase 3 intro says "walk the ledger entries" but after D5 the agent walks `turn_history`. Update: "walk the turn_history (server-validated validated_entry records and cumulative snapshots)"
- [x] **D5-PF-6** [Should-fix] Lines 148-156: manual_legacy mode framing ambiguous — described as both "original 3-step loop" and "skip Steps 2-4 of the 7-step loop." Rewrite: "The 7-step per-turn loop is bypassed entirely in manual_legacy mode. Instead, use the original 3-step conversation loop."
- [x] **D5-PF-7** [Should-fix] Lines 412-460: Manual test checklist missing critical branches — add: unknown action fallback, `ledger_hard_reject` retry cap, `turn_cap_exceeded` handling, budget-precedence override, clarifier handling when `budget.scout_available=false`, transport/tool failure after initial success, `checkpoint_missing`/`checkpoint_invalid` error recovery, `turn_history` append semantics
- [x] **D5-PF-8** [Should-fix] D5 Step 3 response table: remove `turn_request_ref` from "Fields agent reads from template_candidates" (see CC-PF-2). Add note that `turn_request_ref` is agent-derived in Step 4
- [x] **D5-PF-9** [Should-fix] Dual claims channel divergence — see CC-PF-3. Strengthen agent instruction with explicit build-once-assign-twice pattern
- [x] **D5-PF-10** [Advisory] Line 87: "Tool listing fails" not operationally precise. Change to "first call to mcp__context-injection__process_turn returns an error or times out"
- [x] **D5-PF-11** [Advisory] Lines 86-87: Precondition contradiction — "must be available" then defines unavailability fallback. Change to "should be available (see mode gating below)"
- [x] **D5-PF-12** [Advisory] Line 21: "preserving Phase 1 (setup) and Phase 3 (synthesis)" should be "preserving Phase 1 (setup) and Phase 3 (synthesis) with targeted additions"
- [x] **D5-PF-13** [Advisory] Line 59: Stale line count (324 vs actual 323). Update or remove

### Decisions Document

File: `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md`

- [x] **DEC-PF-1** [Should-fix] Line 199: Stale action value `"continue"` — should be `"continue_dialogue"` per D3's `ConversationAction` enum

## 3. Post-Fix Follow-Up Items

Not blockers for plan fix pass, but should be tracked:

- [ ] **FU-PF-1** D4a: Consider shared `derive_budget_status()` helper for the two `compute_budget()` implementations in `templates.py` and `execute.py` to prevent drift
- [ ] **FU-PF-2** D4a: `ErrorCode` enum at `enums.py:109` has 4 values; D4a adds 5 new codes to `ErrorDetail`'s Literal but doesn't update the enum. Update or document Literal as source of truth
- [ ] **FU-PF-3** D4b: Turn-number monotonicity — neither D1 validation nor D2's `with_turn()` enforces `entry.turn_number` is monotonically increasing. Add `request.turn_number == len(base.entries) + 1` guard at D4b protocol boundary
- [ ] **FU-PF-4** D4b: Checkpoint atomicity — execute_recorded evidence lost on server restart. Document as known limitation with revisit trigger (cross-session process reuse)
- [ ] **FU-PF-5** D5: `posture` field is unused server-side (template matching uses only `conversation_id` and `turn_number`). Document as reserved/no-op in protocol contract
- [ ] **FU-PF-6** D5: Tags are free-form server-side but D5 instructs constrained set. Either add server-side whitelist or document as convention-only
- [ ] **FU-PF-7** D5: Hardcoded `MAX_CONVERSATION_TURNS=15` in agent could drift from server value. Long-term: expose server turn cap in TurnPacketSuccess or shared config

## 4. Acceptance Criteria

All items in Sections 1-2 checked off:

- [x] All cross-cutting issues (CC-PF-1 through CC-PF-3) addressed
- [x] All per-document fixes applied (M-PF, D1-PF, D2-PF, D3-PF, D4a-PF, D4b-PF, D5-PF, DEC-PF items)
- [x] Documents internally consistent — no cross-document contradictions
- [x] Grep for known error patterns:
  - `from context_injection.action` should not appear in any plan document (D2-PF-1)
  - `cumulative=` as keyword arg to `compute_action` should not appear (D2-PF-1)
  - `candidate.scout_option_id` should not appear (CC-PF-2 — use `candidate.scout_options[0].id`)
  - `candidate.scout_token` should not appear (CC-PF-2 — use `candidate.scout_options[0].scout_token`)
  - `candidate.turn_request_ref` should not appear (CC-PF-2 — agent-derived)
  - `Claim.status: str` should not appear in base_types.py spec (D1-PF-2 — use Literal)
  - `"Create: None"` should not appear in D4a scope (D4a-PF-2)
  - `delta="static"` should not appear in `test_invalid_delta_rejected` (D4a-PF-1)
  - `"continue"` (bare, not `"continue_dialogue"`) should not appear as an action value in decisions doc (DEC-PF-1)
- [x] Commit on fix branch
- [ ] Merge to `main`

## 5. References

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
| Planning Brief | `docs/plans/2026-02-15-context-injection-agent-integration-planning-brief.md` |

### Codex Dialogue Thread IDs

**Round 4: Post-fix individual + transition reviews (this session)**

| Review | Thread ID |
|--------|-----------|
| Manifest | `019c651d-357e-7983-af08-177470946cd5` |
| D1 | `019c651c-8407-7740-83fd-2cc6519206c3` |
| D2 | `019c651c-a466-7e00-9f45-5401d5e23aa8` |
| D3 | `019c651c-f92f-7291-94a6-5306fbd230c0` |
| D4a | `019c651d-1288-7bc2-a8a3-b9bae05d18c8` |
| D4b | `019c651d-09cb-7311-a430-027e79c30485` |
| D5 | `019c651d-5e41-7460-91a3-febd92628152` |
| D1->D3 | `019c651c-fdf6-71d3-9df1-098b177a3c63` |
| D3->D2 | `019c651d-a622-73c3-9a94-ffc153191e7a` |
| D4b->D5 | `019c651d-b4fa-7353-8daa-617e5ce52cf9` |

### Related Tickets

| Ticket | Relationship |
|--------|-------------|
| T-001 | Predecessor — T-001's ~60 fixes were applied before this review. T-002 catches residual and newly-visible issues |
