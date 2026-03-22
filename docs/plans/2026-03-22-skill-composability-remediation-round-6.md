# Skill Composability Spec Remediation Plan — Round 6

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 36 canonical findings (1 P0, 20 P1, 15 P2) across 9 spec files
**Spec:** `docs/superpowers/specs/skill-composability/` (10 files, ~1208 lines)
**Dominant pattern:** Enforcement gaps without corresponding verification paths (10+ findings across 3 reviewers)

## Strategy

Four commits, ordered by dependency and priority:

1. **P0 + authority model** — validator acceptance criteria, authority delegation fix, broken cross-refs
2. **Behavioral contracts** — four inconsistencies in routing-and-materiality.md
3. **Enforcement + verification coverage** — 13 P1 findings adding enforcement mechanisms, test cases, and deferred entries
4. **P2 findings** — terminology, fixture details, minor asymmetries

Rationale: Commit 1 must land first (P0 blocking, authority model affects how all other claims are interpreted). Commit 2 is independent of 1 (different files) but should precede 3 because several Commit 3 verification additions reference the behavioral contracts fixed in 2. Commit 4 depends on 3 because some P2 findings extend P1 test surfaces added in 3.

---

## Commit 1 — P0: Validator Acceptance Criteria + Authority Model

**Finding count:** 1 P0 + 3 P1 + 1 P2 = 5 findings
**Files:** verification.md, foundations.md, delivery.md

### [SY-3] P0 — `validate_composition_contract.py` has no acceptance criteria

**Source:** VR-14, CE-9 (cross-lens confirmation)
**File:** verification.md

7+ normative claims defer enforcement to this unspecified tool. delivery.md item #6 provides a one-line sketch insufficient for implementation.

**Fix:** Add a "Validator Acceptance Criteria" section to verification.md after the Contract Drift Verification table, specifying:

```markdown
### Validator Acceptance Criteria (`validate_composition_contract.py`)

The validator (delivery.md item #6) MUST check the following. Each check maps to one or more normative claims whose enforcement terminates at this tool.

| # | Check | Normative Source | Pass Criteria |
|---|-------|-----------------|---------------|
| 1 | Boundary-scoped marker | foundations.md §Versioning | `implements_composition_contract: v1` appears within the active composition stub block (not in comments, examples, or disabled sections) — satisfies the boundary-scoped MUST that `grep -l` cannot enforce |
| 2 | Sentinel registry consistency | capsule-contracts.md §Sentinel Registry | All 3 sentinels present in each participating stub's consume/emit declarations |
| 3 | `record_path` non-null schema | routing-and-materiality.md §Selective Durable Persistence | Emitted feedback capsule schema enforces `record_path` as required (non-null) field |
| 4 | `lineage_root_id` immutability | lineage.md §Key Propagation | Downstream stubs inherit `lineage_root_id` from upstream capsule — no re-mint |
| 5 | Ownership mismatch detection | foundations.md §Three-Layer Delivery Authority | Each stub's composition section references only sentinels and fields owned by that skill's role |
| 6 | Semantic parity (contract→stub) | verification.md §Contract Drift | Routing classification rules, materiality tier definitions, and consumer class assignments in stubs match contract definitions |

**Unit test requirements:** The validator itself MUST have tests for each check above — at minimum one pass case and one fail case per check.

**Minimum fixture set:** One well-formed stub (passes all 6), one stub with marker in a comment (fails check 1), one stub missing a sentinel (fails check 2).
```

### [SY-13] P1 — foundations.md invents authority delegation mechanism

**Source:** AA-1 (singleton)
**File:** foundations.md (line 113)

The claim that delivery.md MUST clauses "carry `architecture_rule` authority by reference" uses a delegation mechanism that doesn't exist in spec.yaml. The `fallback_authority_order` already resolves correctly without it.

**Fix:** Replace foundations.md line 113:

```
OLD: The interim drift mitigation protocol ([delivery.md](delivery.md#open-items) item #8)
contains load-bearing MUST clauses that enforce this architectural invariant. These MUST
clauses carry `architecture_rule` authority by reference — they are enforcement mechanisms
for the contract→stub drift detection invariant defined in this section, not independent
`implementation_plan` claims. Contradictions between item #8 and this section are spec
defects (the architectural invariant governs).

NEW: The interim drift mitigation protocol ([delivery.md](delivery.md#open-items) item #8)
contains MUST clauses that implement this architectural invariant as delivery guidance.
Contradictions between item #8 and this section are resolved in favor of this section —
the architectural invariant (foundation authority) takes precedence over the interim
protocol (delivery-plan authority) per the `fallback_authority_order` in spec.yaml.
```

### [SY-14] P1 — delivery.md item #8 MUST clauses exceed authority scope

**Source:** AA-3 (singleton)
**File:** delivery.md (item #8, line 51)

Item #8 contains process enforcement MUST clauses whose binding force is ambiguous without the delegation mechanism removed in SY-13.

**Fix:** Append governance note to delivery.md item #8 text:

```
ADD (after the final sentence of item #8):
**Governance:** These process requirements implement the architectural invariant at
[foundations.md §Versioning and Drift Detection](foundations.md#versioning-and-drift-detection).
They are implementation guidance, not independent architectural constraints. Contradictions
are resolved in favor of foundations.md per `fallback_authority_order`.
```

### [SY-12] P1 — Broken cross-reference anchors to Contract 2

**Source:** CC-1, CC-2 (related pattern)
**Files:** foundations.md (line 57), verification.md (line 102)

Double-hyphen `--` in anchor should be single hyphen `-`. The `→` character generates no hyphen, not a double hyphen.

**Fix:** Two search-and-replace operations:

```
foundations.md:57 — change:
  capsule-contracts.md#contract-2-ns--dialogue-ns-handoff-block
to:
  capsule-contracts.md#contract-2-ns-dialogue-ns-handoff-block

verification.md:102 — change:
  capsule-contracts.md#contract-2-ns--dialogue-ns-handoff-block
to:
  capsule-contracts.md#contract-2-ns-dialogue-ns-handoff-block
```

### [SY-11] P2 — Stale spec.yaml line reference

**Source:** AA-2, CC-3 (independent convergence)
**File:** foundations.md (line 69)

Lines 63-67 point to the wrong comment block. The external authority comment starts at line 66.

**Fix:** Change `spec.yaml lines 63-67` to `spec.yaml lines 66-70` in foundations.md line 69. Alternatively, use a semantic reference: "the `# External authorities` comment in spec.yaml" to prevent future drift.

---

## Commit 2 — Behavioral Contract Consistency (routing-and-materiality.md)

**Finding count:** 4 P1
**Files:** routing-and-materiality.md

### [SY-1] P1 — Budget override tracking mechanism unspecified

**Source:** CE-3, VR-20, VR-21, IE-12 (3-way cross-lens confirmation)
**File:** routing-and-materiality.md §Budget Enforcement Mechanics

No state variable tracks the override lifecycle. "Exactly one more hop" is unenforceable without a defined mechanism.

**Fix:** Add after the override mechanism paragraph:

```markdown
**Override tracking:** The override is tracked as a conversation-local boolean flag
`budget_override_pending` per `lineage_root_id`. When the user confirms "continue": set
`budget_override_pending: true` for the current `lineage_root_id`. When the next hop
suggestion would be suppressed by budget enforcement: if `budget_override_pending` is
`true`, allow the hop suggestion and set `budget_override_pending: false`. On subsequent
budget checks with `budget_override_pending: false`, re-suppress as normal. Each override
requires an explicit user "continue" — the flag is single-use.
```

### [SY-2] P1 — `materiality_source` preservation contradicts emission-time gate

**Source:** CE-2, VR-22 (cross-lens confirmation)
**File:** routing-and-materiality.md §Affected Surface Validity (lines 71-73)

"Preserved unchanged" is literally false when `materiality_source` is invalid. The gate corrects it. Implementers may skip the gate believing the preservation claim is absolute.

**Fix:** Replace the preservation sentence at line 71:

```
OLD: Correction rules do NOT alter `materiality_source` — corrections affect routing
classification (`suggested_arc`) only, not the materiality evaluation result. The
`materiality_source` value reflects the tier that determined the `material` field and is
preserved unchanged through the correction pipeline.

NEW: Correction rules do NOT alter `materiality_source` when it holds a valid value (`rule`
or `model`) — corrections affect routing classification (`suggested_arc`) only, not the
materiality evaluation result. When `materiality_source` is outside `{rule, model}`, the
emission-time gate corrects it to `rule` as an unexpected-state recovery (see emission-time
enforcement below). This is an error-recovery action, not a normal correction pipeline
operation.
```

### [SY-4] P1 — `unresolved[]` placement exclusion has no enforcement gate

**Source:** CE-1, IE-11 (cross-lens confirmation)
**File:** routing-and-materiality.md §Affected Surface Validity (emission-time enforcement)

The gate governs `feedback_candidates[]` but not `unresolved[]`. The gate's own "capsule assembly MUST NOT begin" language implies `unresolved[]` should be in scope.

**Fix:** Expand the gate definition:

```
OLD: The correction pipeline is a required gate before `feedback_candidates[]` is written.

NEW: The correction pipeline is a required gate before `feedback_candidates[]` OR
`unresolved[]` is written. Both lists MUST reflect post-correction, post-placement state.
```

### [SY-6] P1 — `record_path` "regardless of abort" claim unsatisfied

**Source:** CE-4 (singleton)
**File:** routing-and-materiality.md §Selective Durable Persistence (lines 240-241)

The "regardless of whether the correction pipeline succeeds or aborts" claim is unsatisfied — the partial-correction-failure post-abort handler never references the path.

**Fix:** Qualify the MUST clause:

```
OLD: the fully-resolved path is needed by the error handler regardless of whether the
correction pipeline succeeds or aborts.

NEW: the fully-resolved path is needed by the error handler when the correction pipeline
succeeds but the file write fails. The path is pre-computed regardless of correction
outcome to simplify control flow, but is only consumed in the write-failure recovery path.
```

---

## Commit 3 — Enforcement Gaps + Verification Coverage

**Finding count:** 13 P1
**Files:** verification.md (11 changes), foundations.md (1 change), delivery.md (1 change)

### [SY-5] P1 — `record_path` ordering invariant absent from Deferred Verification

**Source:** VR-5, VR-17, IE-1 (independent convergence)
**File:** verification.md (Deferred Verification table)

The ordering MUST (compute path → run correction → write file) has no verification path, violating the spec's own integrity clause.

**Fix:** Add row to the Deferred Verification table:

```markdown
| `record_path` pre-computation ordering | routing-and-materiality.md §Selective Durable Persistence | Code review responsibility — verify path variable assigned before correction pipeline entry. Structural analysis of error handler code path is the verification mechanism. Same approach as `record_path` non-null enforcement. |
```

### [SY-7] P1 — Boundary-scoped grep MUST unenforceable by interim check

**Source:** VR-1, CE-8, IE-8 (3-lens convergence)
**File:** foundations.md §Versioning and Drift Detection (line 105)

`grep -l` is file-level only. The foundations.md MUST requires boundary-scoped verification. The MUST cannot be relaxed by verification.md's authority.

**Fix:** Add temporal qualifier to foundations.md line 105:

```
OLD: The grep-based CI check ([verification.md](verification.md)) MUST verify the marker
appears within the active composition stub boundaries.

NEW: The grep-based CI check ([verification.md](verification.md)) MUST verify the marker
appears within the active composition stub boundaries. During the interim period before
`validate_composition_contract.py` is implemented (delivery.md item #6), the check is
file-level only — boundary-scoped verification is an acknowledged gap closed by the
validator.
```

### [SY-8] P1 — Budget scan fixture ordering unspecified

**Source:** VR-6, VR-24, IE-5 (independent convergence)
**File:** verification.md (Soft iteration budget test, fixture 3)

Fixture 3 does not specify whether the malformed sentinel is newer or older than the valid artifact. Coverage of the full-scan property is accidental.

**Fix:** Add ordering constraint to fixture 3:

```
ADD: The malformed sentinel MUST have a more recent `created_at` than the valid NS artifact
(encountered first in a newest-first scan). This forces the scan to continue past the
invalid entry to find the valid artifact — a no-backtrack implementation would incorrectly
return 0.
```

### [SY-9] P1 — Thread continuation "never inject" has no API-layer enforcement

**Source:** VR-8, IE-9 (independent convergence)
**File:** verification.md (Thread continuation test)

The 8 behavioral scenarios test the continuation decision but none test the API call parameters.

**Fix:** Add 9th behavioral test scenario:

```markdown
| 9 | Fresh start required (new artifact detected) — verify Codex API call does NOT include prior `thread_id` | Configure dialogue with a `material: true` NS artifact newer than `thread_created_at`. Verify the Codex API call uses a new thread (no prior `thread_id` parameter). |
```

### [SY-15] P1 — `materiality_source` enforcement asymmetric with `classifier_source`

**Source:** IE-3, VR-23 (cross-lens confirmation)
**File:** verification.md (Routing and Materiality Verification table)

`classifier_source` has a grep-based CI check and standalone test. `materiality_source` has neither — only a piggybacked 7th test case.

**Fix:** Add parallel verification entries:

```markdown
1. Structural (interim) grep check: "Fail if `materiality_source` is assigned any value
   outside `{rule, model}` in skill stub files or composition contract."
2. Standalone behavioral test: "Inject `materiality_source: ambiguous` into a
   feedback_candidates[] entry at the emission-time gate → verify correction to `rule`
   and structured warning."
```

### [SY-16] P1 — `dialogue-orchestrated-briefing` sentinel depends on non-existent stubs

**Source:** VR-3 (singleton)
**File:** verification.md (Deferred Verification table)

The MUST NOT emit check depends on stub files that don't exist. Not in Deferred Verification table.

**Fix:** Add row:

```markdown
| `dialogue-orchestrated-briefing` sentinel suppression | capsule-contracts.md §Sentinel Registry | Structural check depends on dialogue stub text. Deferred until dialogue skill text is authored (delivery.md §Dialogue Skill Text Addition). |
```

### [SY-17] P1 — Briefing sentinel suppression unverified for abort paths

**Source:** IE-4 (singleton)
**File:** verification.md (abort-path test cases)

Abort paths verify feedback capsule sentinel suppression but not briefing sentinel.

**Fix:** Add assertion to both abort-path test cases (partial correction failure and Step 0 case c):

```
ADD: "Verify `<!-- dialogue-orchestrated-briefing -->` also does not appear in any
user-visible output."
```

### [SY-18] P1 — `tautology_filter_applied` Tier 1+2 partial implementation untested

**Source:** IE-6 (singleton)
**File:** verification.md (tautology filter test cases)

Only "Tier 1 only" partial is tested. "Tier 1+2, skip Tier 3" is the most likely production omission.

**Fix:** Add 4th test case:

```markdown
| 4 | Tiers 1+2 executed, Tier 3 skipped | Configure NS adapter to execute Tiers 1 and 2 but NOT Tier 3 (Tier 3 prompt not called) → verify `tautology_filter_applied` is `false`. |
```

### [SY-19] P1 — No-auto-chaining helper co-review is non-binding prose

**Source:** IE-2 (singleton)
**File:** delivery.md (item #8)

The co-review requirement for helper functions has no PR checklist entry.

**Fix:** Append to delivery.md item #8:

```
ADD: The PR checklist for dialogue skill text changes MUST include explicit confirmation
that all helper functions referenced from the feedback capsule assembly path have been
co-reviewed for auto-chaining patterns.
```

### [SY-20] P1 — `topic_key` non-use verification excludes composition contract

**Source:** VR-2 (singleton)
**File:** verification.md (topic_key check)

Grep check scopes to "skill stub files only" — the composition contract is excluded.

**Fix:** Add note:

```
ADD: "When the composition contract is authored, extend the grep check scope to include
`packages/plugins/cross-model/references/composition-contract.md` — the contract is the
primary propagation vector for `topic_key` misuse."
```

### [SY-21] P1 — Staleness detection no-backtrack on schema failure has no test

**Source:** VR-7 (singleton)
**File:** verification.md (staleness detection test cases)

The "if newest valid artifact has schema failure, treat as `unknown`" branch is untested.

**Fix:** Add 5th test scenario:

```markdown
| 5 | Newest valid artifact has schema failure (e.g., missing required field) | Pre-seed artifact with valid sentinel but invalid schema → verify staleness status is `unknown` and no backtrack to older artifacts. |
```

### [SY-22] P1 — AR re-review feedback capsule inheritance untested

**Source:** VR-10 (singleton)
**File:** verification.md (inheritance test)

The 4-hop chain (AR → NS → Dialogue → AR-re-review) is the most likely re-mint error vector.

**Fix:** Extend inheritance test:

```
ADD: "Extend to include 4-hop chain with AR re-review: AR₁ → NS → Dialogue → AR₂.
Verify AR₂ inherits `lineage_root_id` from the feedback capsule (same as AR₁'s original
`lineage_root_id`), not a freshly generated ID."
```

### [SY-23] P1 — Consumption discovery Step 0 has no negative `subject_key` test

**Source:** VR-15 (singleton)
**File:** verification.md (consumption discovery test cases)

Only matching `subject_key` is tested. No test verifies fall-through on mismatch.

**Fix:** Add 5th test scenario:

```markdown
| 5 | Durable file exists with non-matching `subject_key` | Pre-seed durable file with `subject_key` that does not match current context → verify consumer falls through to conversation-local scan (durable file not consumed). |
```

---

## Commit 4 — P2 Findings

**Finding count:** 14 P2
**Files:** verification.md (9), routing-and-materiality.md (2), delivery.md (2), foundations.md (1)

### [SY-10] Abort paths behavioral overlap unverified

**File:** verification.md
**Fix:** Add structural verification note: "Both abort paths (Step 0 case c and partial correction failure) MUST produce identical behavior for three shared assertions: (a) no feedback capsule sentinel, (b) no durable file, (c) no hop suggestion. Verify by table comparison of both test case assertion lists."

### [SY-24] Term drift: stub terminology

**File:** foundations.md §Versioning and Drift Detection
**Fix:** Add equivalence note: "'Inline stub' and 'composition stub' both refer to the composition-specific block within a skill's SKILL.md. 'Skill stub file' or 'skill file' refers to the entire SKILL.md. This spec uses 'composition stub' as the primary term."

### [SY-25] Bare "Tier 3" without qualifier

**File:** delivery.md (items 1, 5, 7)
**Fix:** Qualify item 1: "Examples added to [Tier 3](pipeline-integration.md#three-tier-tautology-filter) (tautology filter) (2026-03-19)." Qualify item 5: "Tier 2 (materiality) reopens/contradicts resolved."

### [SY-26] `hold_reason` no validation gate

**File:** routing-and-materiality.md §Emission-time enforcement
**Fix:** Add note: "The `hold_reason` field has a restricted enum (`routing_pending | null`) but no emission-time validation gate parallel to `classifier_source` and `materiality_source`. This is an accepted asymmetry — the enum is small enough that schema validation (when `validate_composition_contract.py` is implemented) provides sufficient enforcement."

### [SY-27] `#emission-contract-1/2` anchors renderer-dependent

**File:** verification.md (Capsule Contract Verification table)
**Fix:** Verify anchors resolve under GFM (they do — parentheses are stripped). Add note: "Anchors `#emission-contract-1` and `#emission-contract-2` resolve correctly under GFM. Non-GFM renderers may require explicit anchor IDs."

### [SY-28] No MUST for omit-hop precedence over `continuation_warranted`

**File:** routing-and-materiality.md §Budget Enforcement Mechanics
**Fix:** Add clarifying note after the enforcement action: "When budget is exhausted: `continuation_warranted` MAY be `true` (reflects synthesis outcome) but the hop suggestion block MUST be omitted regardless. The omit-hop-suggestion rule takes precedence over `continuation_warranted` value."

### [SY-29] `materiality_source` test covers only `ambiguous` value

**File:** verification.md (materiality_source correction test)
**Fix:** Extend the test note: "Test SHOULD also cover `materiality_source: null` and `materiality_source: <typo>` to verify the gate handles all invalid value classes, not just the `ambiguous` case."

### [SY-30] `record_status` absent fixture under-specified

**File:** verification.md (consumer-side test case 3)
**Fix:** Add fixture setup: "Pre-seed a durable file at a known `record_path` with valid feedback capsule content. Emit a capsule with `record_path` set to this path but `record_status` absent (field not present in YAML). Verify consumer does NOT read the file."

### [SY-31] "No budget consumed" for held items has no mechanism

**File:** verification.md (held ambiguous item test)
**Fix:** Add verification mechanism: "Verify budget count by scanning for qualifying artifacts — held items have no emitted capsule (no sentinel), so the budget counter naturally excludes them. Verify by assertion: budget count before hold equals budget count after hold."

### [SY-32] D5 grep exclusion paths missing

**File:** verification.md (D5 capsule externalization check)
**Fix:** Add authorized exclusion paths: "Exclude from grep check: `docs/superpowers/specs/skill-composability/` (spec files reference schemas), `packages/plugins/cross-model/references/` (contract file defines schemas), test fixtures."

### [SY-33] Correction rule ordering test covers only rule 1+2

**File:** verification.md (correction rule ordering test)
**Fix:** Add note: "Extend ordering test to cover additional overlapping rule pairs — at minimum rule 2+3 (both can apply to the same `material: true` item with different `suggested_arc` corrections). Verify earlier rule's correction is authoritative."

### [SY-34] Contract drift CI unidirectional

**File:** verification.md §Contract Drift Verification
**Fix:** Add directionality note: "The CI check (`validate_composition_contract.py`) covers contract→stub drift. Stub→contract drift detection is manual-only (delivery.md item #8 protocol). This asymmetry is accepted for v1 — bidirectional automated detection is deferred."

### [SY-35] Manual protocol retirement plan

**File:** delivery.md (item #8)
**Fix:** Add retirement clause: "This interim protocol is retired when `validate_composition_contract.py` (item #6) passes CI and covers all 6 acceptance criteria in verification.md."

### [SY-36] `record_status` absent consumer "do not read" verification

**File:** verification.md (consumer-side test case 3)
**Fix:** Add verification mechanism note: "The 'does not attempt to read' assertion is verified structurally: confirm the consumer code path checks for `record_status` field presence before any file I/O, and the absent-field branch leads directly to conversation-local scan. Code-path inspection is the verification mechanism."

---

## File Change Summary

| File | Commit 1 | Commit 2 | Commit 3 | Commit 4 | Total Changes |
|------|----------|----------|----------|----------|---------------|
| **verification.md** | SY-3, SY-12 | — | SY-5, SY-8, SY-9, SY-15, SY-16, SY-17, SY-18, SY-20, SY-21, SY-22, SY-23 | SY-10, SY-27, SY-29, SY-30, SY-31, SY-32, SY-33, SY-34, SY-36 | 22 |
| **foundations.md** | SY-13, SY-12, SY-11 | — | SY-7 | SY-24 | 5 |
| **routing-and-materiality.md** | — | SY-1, SY-2, SY-4, SY-6 | — | SY-26, SY-28 | 6 |
| **delivery.md** | SY-14 | — | SY-19 | SY-25, SY-35 | 4 |

## Dependency Map

```
Commit 1 (P0 + authority)
    ↓  (SY-13 authority fix informs SY-7's temporal qualifier in C3)
Commit 2 (behavioral contracts)
    ↓  (SY-1 budget flag referenced by SY-8 fixture; SY-4 gate scope referenced by SY-17)
Commit 3 (enforcement + verification)
    ↓  (SY-15 materiality_source check extended by SY-29; SY-5 deferred entry extended by SY-36)
Commit 4 (P2 findings)
```

Commits 1 and 2 are independent (no shared files), but sequential ordering is safer for cross-file consistency review. Commits 3 and 4 have genuine dependencies (P2 findings extend P1 surfaces).

## Findings Not Addressed

None. All 36 canonical findings are covered:
- P0: 1 (SY-3)
- P1: 20 (SY-1, SY-2, SY-4, SY-5, SY-6, SY-7, SY-8, SY-9, SY-12, SY-13, SY-14, SY-15, SY-16, SY-17, SY-18, SY-19, SY-20, SY-21, SY-22, SY-23)
- P2: 15 (SY-10, SY-11, SY-24, SY-25, SY-26, SY-27, SY-28, SY-29, SY-30, SY-31, SY-32, SY-33, SY-34, SY-35, SY-36)
