# Skill Composability Spec Remediation Plan — Round 10

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 39 canonical findings from spec review round 10, resolving authority misplacement, abort-path asymmetry, CI enforcement scope gaps, and verification spec inconsistencies.

**Architecture:** Seven tasks in three phases. Phase 1 (T1–T4) touches non-overlapping spec sections — safe to parallelize. Phase 2 (T5–T6) adds CI enforcement and verification consistency that depend on Phase 1 normative text being stable. Phase 3 (T7) is a P2 editorial batch. A new `governance.md` authority file is introduced per Codex dialogue consensus (thread `019d1820-c537-7700-963f-ed0138277544`).

**Tech Stack:** Markdown spec files at `docs/superpowers/specs/skill-composability/`, YAML manifest at `spec.yaml`

---

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 39 canonical findings (2 P0, 22 P1, 15 P2) across 8 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/skill-composability/` (9 files, 8 normative + 1 supporting + spec.yaml)
**Dominant patterns:** Authority misplacement of enforcement claims in delivery.md (SY-1/AA-2/AA-4 cluster), abort-path asymmetry between Step 0 case (c) and partial correction failure (SY-3/SY-4/CC-3/SY-9), CI grep check scope gaps (SY-5/IE-1/IE-6 cluster)

## Strategy

Seven tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Four tasks, all parallel (touch different sections of shared files):
   - **T1:** P0 interim verification + count fix (VR-1, VR-2, CC-1) — verification.md, delivery.md
   - **T2:** Authority reorganization (SY-1, AA-2, AA-4) — NEW governance.md, spec.yaml, delivery.md, foundations.md, verification.md, routing-and-materiality.md
   - **T3:** Abort-path symmetry (SY-3, SY-4, CC-3, SY-9, CC-7) — routing-and-materiality.md, verification.md, pipeline-integration.md
   - **T4:** Behavioral contract gaps (SY-2, SY-6, CE-2, CE-3, IE-11) — capsule-contracts.md, routing-and-materiality.md

2. **Phase 2** — After Phase 1 (normative text and authority placement must be stable):
   - **T5:** CI enforcement scope (SY-5, IE-1, IE-3, IE-6, IE-7) — verification.md, routing-and-materiality.md
   - **T6:** Verification spec consistency (SY-8, SY-10, VR-5, VR-6, VR-7) — verification.md

3. **Phase 3** — After Phase 1:
   - **T7:** P2 batch (SY-7, CC-4, CC-5, AA-3, AA-5, AA-8, CE-6, CE-7, IE-5, IE-8, VR-8, VR-9, VR-10, VR-11) — all files

**Dependency chains:**
1. SY-1 (T2) → SY-5 (T5): COMPOSITION_HELPERS.md enforcement claims need authority placement before verification rows
2. SY-1 (T2) → IE-1, IE-6 (T5): grep scope entries reference clause IDs assigned in T2
3. VR-1/VR-2 (T1) → SY-10, VR-5 (T6): deferred table updates must align with interim verification decisions
4. SY-3/SY-4 (T3) → SY-9 (already in T3): abort-path parity table depends on assertion (vii) resolution and flag teardown rule
5. T2–T4 → T7: P1 normative text changes may shift line numbers and cross-references affecting P2 edits

**Commit strategy:**
1. `fix(spec): add P0 interim verification paths and fix delivery.md count (3 findings)` (T1)
2. `fix(spec): reorganize enforcement authority — new governance.md, break circular delegation (3 findings)` (T2)
3. `fix(spec): resolve abort-path asymmetry — flag teardown, assertion (vii), parity (5 findings)` (T3)
4. `fix(spec): close behavioral contract gaps — provenance, hold_reason, processing order (5 findings)` (T4)
5. `fix(spec): harden CI enforcement scope — COMPOSITION_HELPERS.md, grep file scope, tautology gate (5 findings)` (T5)
6. `fix(spec): fix verification spec consistency — tracking pointers, deferred table, test feasibility (5 findings)` (T6)
7. `fix(spec): remediate 14 P2 findings from spec review round 10` (T7)

**Design decisions from Codex dialogue (thread `019d1820-c537-7700-963f-ed0138277544`):**
- Introduce `governance.md` authority with `review_gate` as sole default claim (NOT `enforcement_mechanism`)
- Governance ranks after lineage, before delivery-plan in `fallback_authority_order`
- Split item #8 into scheduling (stays in delivery.md) and enforcement clauses (relocate)
- 4-way placement rule: semantic owner / governance / verification / delivery-plan
- Verification checks become derivative — cite upstream clause IDs with `Validates: <clause-id>` prefix
- One-directional delegation edges only (breaks AA-4 circular delegation)

---

## Task 1 — P0 Interim Verification Paths + Count Fix (3 findings)

**Finding count:** 2 P0 + 1 P1
**Files:** verification.md, delivery.md
**Depends on:** nothing — start immediately

### [VR-1] Add interim verification paths for materiality harness-dependent claims

**Source:** VR-1 (P0, singleton)
**File:** verification.md §Routing and Materiality Verification table (lines 73–101)

Every verification table row whose path begins "Materiality harness —" has zero interim verification. Add an explicit interim path or acknowledged-gap annotation for each.

- [ ] **Step 1:** Read verification.md lines 73–101 (Routing and Materiality Verification table).

- [ ] **Step 2:** For each row whose verification path contains only "Materiality harness", add an interim annotation. Pattern per row:

  For rows with feasible interim checks (correction rule ordering, consequence prohibitions, novelty veto, cross-tier guard):
  > `Materiality harness — 24-case validity matrix. **Interim:** Manual walk-through per §Interim Materiality Verification Protocol above (active P0 gate).`

  For rows where only the harness can verify (budget enforcement, ambiguous placement, indeterminate state):
  > `Materiality harness — [description]. **Interim:** No interim verification path — gap acknowledged. Covered by promotion gate (delivery.md item #7).`

- [ ] **Step 3:** Verify every "Materiality harness" row now has either "**Interim:**" or "**Interim:** No interim verification path" appended.

- [ ] **Step 4:** Add a note after the Routing and Materiality Verification table heading:
  > **Interim verification status:** Rows marked "Interim: Manual walk-through" are covered by the §Interim Materiality Verification Protocol. Rows marked "Interim: No interim verification path" are acknowledged gaps tracked by delivery.md item #7 (P0 blocker). Both are blocked by the promotion gate.

---

### [VR-2] Add interim verification paths for validator-dependent acceptance criteria

**Source:** VR-2 (P0, singleton)
**File:** verification.md §Validator Acceptance Criteria table (lines 128–146)

7 of 9 validator checks terminate at non-existent `validate_composition_contract.py`.

- [ ] **Step 5:** Read verification.md lines 128–146 (validator acceptance criteria table).

- [ ] **Step 6:** Add an "Interim Path" column to the validator acceptance criteria table. Populate per check:

  | # | Interim Path |
  |---|---|
  | 1 | `grep -l` file-level check (active) — boundary-scoped gap acknowledged |
  | 2 | `grep -n` sentinel check (active) |
  | 3 | Structural code review: verify feedback capsule schema requires `record_path` non-null — add to deferred verification checklist |
  | 4 | Behavioral: multi-hop chain test asserts `lineage_root_id` string equality (active — see Lineage Verification table) |
  | 5 | Structural code review: verify each stub's composition section references only owned sentinels/fields |
  | 6 | Manual: semantic spot-check in PR description (active — delivery.md item #8 protocol) |
  | 7 | Code review responsibility (active — deferred verification table entry exists) |
  | 8 | Structural: verify comparison code uses parsed numeric timestamps — add to PR checklist |
  | 9 | Manual: reverse parity check in PR description (active — delivery.md item #8 protocol) |

- [ ] **Step 7:** Verify all 9 checks now have a non-empty "Interim Path" cell.

---

### [CC-1] Fix delivery.md retirement condition count: 6 → 9

**Source:** CC-1 (P1, singleton)
**File:** delivery.md §Open Items, items #6 and #8

delivery.md says "6 acceptance criteria" but verification.md has 9 checks.

- [ ] **Step 8:** In delivery.md item #6, change `passes all 6 acceptance criteria` to `passes all 9 acceptance criteria`.

- [ ] **Step 9:** In delivery.md item #8, change `covering all 6 acceptance criteria` to `covering all 9 acceptance criteria`.

- [ ] **Step 10:** Commit T1.

```bash
git add docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): add P0 interim verification paths and fix delivery.md count (3 findings)"
```

---

## Task 2 — Authority Reorganization (3 findings)

**Finding count:** 3 P1 (all corroborated)
**Files:** NEW governance.md, spec.yaml, delivery.md, foundations.md, verification.md, routing-and-materiality.md
**Depends on:** nothing — start immediately
**Design source:** Codex dialogue thread `019d1820-c537-7700-963f-ed0138277544`

This is the highest-risk task (structurally invasive, widest blast radius). Uses the split-then-relocate execution strategy from the Codex dialogue.

### [SY-1] Create governance.md and relocate enforcement MUST clauses from delivery.md item #8

**Sources:** AA-1 + CE-9 (cross-lens confirmation)

Item #8 is a monolithic paragraph containing ~20 MUST clauses under `delivery-plan` authority (ranked 7th). Enforcement claims can't win precedence conflicts. The 4-way placement rule from the dialogue determines each clause's destination:

| Clause Category | Destination | Claims |
|---|---|---|
| **Runtime/behavioral invariants** (no-auto-chaining co-review basis, literal-assignment convention, `tautology_filter_applied` key presence) | routing-and-materiality.md (semantic owner — already has §No Auto-Chaining and §Dimension Independence) | Augment existing clauses |
| **Drift detection invariants** (contract marker verification, stub co-review checklist) | foundations.md §Versioning and Drift Detection (semantic owner) | Augment existing section |
| **PR review gate procedures** (co-review gate, COMPOSITION_HELPERS.md deliverable, helper function tracking, topic_key scope guard, literal-assignment assertion, `record_path` ordering check, thread freshness check) | NEW governance.md | `review_gate` claim |
| **Scheduling and protocol description** (bidirectional review protocol, retirement conditions) | delivery.md (stays — appropriate for `implementation_plan`) | Slim down |

- [ ] **Step 1:** Create `docs/superpowers/specs/skill-composability/governance.md` with frontmatter and relocated PR-gate review procedures:

```markdown
---
module: governance
status: active
normative: true
authority: governance
---

# Governance

PR review gate procedures for composition system changes. Each gate cites the normative clause it enforces — gates are derivative, not independently normative.

## Stub Composition Co-Review Gate

Validates: routing-and-materiality.md §No Auto-Chaining (enforcement basis)

Reviewer confirms no helper-mediated indirect skill delegation via static code inspection. PR checklist item: "Confirmed: stub does not programmatically invoke any skill via model output or helper delegation chains. Helper functions in the feedback capsule assembly path: [explicitly name each function]. Composition paths verified by static inspection of the named functions."

Reviewer (not author) MUST independently verify the helper function list is complete and that no named function delegates to another skill. For each named helper function: confirm no assignment of `classifier_source` or `materiality_source` outside the literal set `{rule, model}`.

The co-review gate MUST also verify the NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags (key presence, not just value correctness) — absence is a gate failure requiring remediation before merge.

## Helper Function Tracking

Validates: routing-and-materiality.md §No Auto-Chaining (enforcement basis)

Any function called from the feedback capsule assembly path MUST be tracked in a checked-in list (`COMPOSITION_HELPERS.md` or equivalent) and diffed on each PR — this makes new helpers visible without requiring deep static analysis.

`COMPOSITION_HELPERS.md` (or equivalent) is a required deliverable for any PR that introduces helper functions called from the feedback capsule assembly path. The file MUST exist before the co-review gate can pass — absence of the file when helper functions exist is a gate failure, not a deferral.

## Constrained Field Literal-Assignment Assertion

Validates: routing-and-materiality.md §Dimension Independence (literal-assignment convention)

PRs introducing helper functions that assign `classifier_source`, `materiality_source`, or `hold_reason` MUST use literal values only (e.g., `classifier_source = "rule"`, not `classifier_source = src`). PR checklist item: "Confirmed: all assignments to `classifier_source`, `materiality_source`, and `hold_reason` in the feedback capsule assembly path use literal string values from the permitted set — no variable-mediated assignments."

This gate closes the grep-evasion gap for the interim enforcement period. Retirement: when `validate_composition_contract.py` includes static analysis for variable-assigned constrained fields.

## Contract Marker Verification

Validates: foundations.md §Versioning and Drift Detection (drift detection invariant)

During stub authoring, reviewer MUST verify that `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). PR checklist item: "Confirmed: `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). Verified by inspecting the marker's location in the stub file — `grep -l` file-level presence is insufficient for this gate (it matches markers in comments)."

## `topic_key` Scope Guard

Validates: lineage.md §Three Identity Keys (`topic_key` is non-authoritative metadata)

During composition contract authoring (delivery.md item #6 delivery window), manually scan the contract draft for `topic_key` appearances in any control path (conditional branches, budget counter expressions, staleness predicates). `topic_key` is non-authoritative metadata — if it appears in a control path, flag as a spec violation.

## `record_path` Pre-Computation Ordering Check

Validates: routing-and-materiality.md §Selective Durable Persistence (path construction rule)

PR checklist item: "Confirmed: `record_path` (absolute filesystem path) is assigned to a local variable before the correction pipeline gate runs. The error handler reads from this pre-computed variable, not from re-derived path logic. Verified by tracing the error handler code path from write-failure branch to `record_path` reference."

## Thread Freshness Numeric Comparison Check

Validates: routing-and-materiality.md §Thread Continuation vs Fresh Start (timestamp comparison rule)

PR checklist item: "Confirmed: thread continuation vs. fresh start comparison uses parsed numeric timestamps (millisecond precision), not string comparison. Verified by reviewing the comparison code path for `created_at` vs `thread_created_at`."
```

- [ ] **Step 2:** Update spec.yaml — add governance authority, update fallback_authority_order, add boundary rules:

  In the `authorities:` block, after `lineage:` and before `delivery-plan:`, add:
  ```yaml
  governance:
    description: PR review gate procedures — derivative enforcement that cites normative clauses from semantic owner files.
    default_claims: [review_gate]
  ```

  In `fallback_authority_order`, insert `governance` after `lineage` and before `delivery-plan`:
  ```yaml
  fallback_authority_order: [foundation, decisions, capsule-contract, routing, pipeline, lineage, governance, delivery-plan, delivery-verification, supporting]
  ```

  Add `review_gate` to `claim_precedence` (governance is the only authority with this claim, so no ordering conflict — but declaring it makes the claim type discoverable):
  ```yaml
  review_gate: [governance]
  ```

  Add bidirectional boundary rules for governance:
  ```yaml
  - on_change_to: [governance]
    review_authorities: [routing, foundation, lineage]
    reason: Governance gates cite normative clauses from semantic owners — changes must be reviewed to prevent governance from re-specifying runtime behavior.
  - on_change_to: [routing, foundation, lineage]
    review_authorities: [governance]
    reason: Changes to normative clauses may invalidate or require updates to governance gate procedures that cite them.
  ```

- [ ] **Step 3:** Slim delivery.md item #8. Replace the monolithic paragraph with scheduling-only content:

  Replace item #8's content (everything after "Active (interim, retired when...") with:
  > Bidirectional manual review protocol (until item #6 CI enforcement exists). **Contract → stub:** Any modification to the composition contract's routing, materiality, lineage, or capsule schema sections MUST be accompanied by a manual review of all three participating skill stubs (adversarial-review, next-steps, dialogue) against the updated contract text. The PR description MUST include a stub-impact checklist confirming which stubs were reviewed and whether updates are needed. **Stub → contract:** Any modification to a participating skill stub's composition section MUST be accompanied by verification that the change conforms to the current contract. The PR description MUST confirm the stub change does not diverge from contract intent. See [foundations.md](foundations.md#versioning-and-drift-detection) for the architectural invariant this protocol protects. PR review gate procedures are defined in [governance.md](governance.md).

- [ ] **Step 4:** Update the enforcement coverage note at end of delivery.md (line 55) to point to governance.md instead of item #8:
  > **Note on enforcement coverage gap:** The helper-mediated indirect delegation detection gap (see [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) enforcement coverage note) has no closure timeline in v1. The gap is documented and mitigated by the co-review gate in [governance.md](governance.md#stub-composition-co-review-gate); deeper static analysis is deferred to `validate_composition_contract.py` (item #6).

### [AA-4] Break circular delegation between foundations.md and delivery.md

**Sources:** AA-4 (P1, singleton)

foundations.md line 115 delegates to delivery.md item #8 with "contains MUST clauses that implement this architectural invariant." Item #8 points back: "Governance authority derives from foundations.md." This creates a circular dependency.

- [ ] **Step 5:** In foundations.md, replace lines 113–115 (the delegation + MUST clause sentence) with a one-directional informational note:

  Replace:
  > **Interim drift mitigation protocol:** see [delivery.md](delivery.md#open-items) item #8. Contract→stub drift is bidirectional and is a P0 prerequisite check.
  >
  > The interim drift mitigation protocol ([delivery.md](delivery.md#open-items) item #8) contains MUST clauses that implement this architectural invariant as delivery guidance.

  With:
  > **Interim drift mitigation protocol:** The bidirectional review protocol for contract→stub drift is described in [delivery.md](delivery.md#open-items) item #8 (scheduling) with PR review gates defined in [governance.md](governance.md) (review procedures). Contract→stub drift is bidirectional and is a P0 prerequisite check.

### [AA-2] Make verification.md checks derivative — cite clause IDs

**Sources:** AA-2 (P1, singleton)

verification.md contains behavioral specs that exceed delivery-verification authority (shadow authority).

- [ ] **Step 6:** In verification.md, for each row in the Capsule Contract Verification and Routing and Materiality Verification tables that defines behavioral expectations, add a `Validates:` prefix to the verification path cell pointing to the normative source. Examples:

  - Row "Emission-time enforcement: correction pipeline is a required gate" → prepend `Validates: routing-and-materiality.md §Affected-Surface Validity.`
  - Row "`classifier_source` MUST be `rule` or `model`" → prepend `Validates: routing-and-materiality.md §Dimension Independence + capsule-contracts.md §Schema Constraints.`

  Apply consistently to all verification table rows. The `Source` column already cites the normative file — the `Validates:` prefix in the verification path makes the derivative relationship explicit in the test specification text.

- [ ] **Step 7:** In verification.md, update the Verification Instruments table (line 18) — change the interim manual review protocol entry:

  Replace reference to "delivery.md item #8 (PR MUST clauses)" with "[governance.md](governance.md) (PR review gates)".

- [ ] **Step 8:** Update routing-and-materiality.md line 194 — reverse the forward reference direction. Change:
  > Helper-mediated indirect delegation chains are a known coverage gap in the interim grep-based enforcement. See [delivery.md](delivery.md#open-items) item #8 for the co-review gate that addresses this gap.

  To:
  > Helper-mediated indirect delegation chains are a known coverage gap in the interim grep-based enforcement. See [governance.md](governance.md#stub-composition-co-review-gate) for the co-review gate that addresses this gap.

- [ ] **Step 9:** Update routing-and-materiality.md §Dimension Independence (line 35) — change the delivery.md reference:

  Replace "See [delivery.md](delivery.md#open-items) item #8 auto-chaining co-review gate" with "See [governance.md](governance.md#stub-composition-co-review-gate)".

- [ ] **Step 10:** Update README.md — add governance to authority table (after lineage, before delivery-plan), reading order table (as item 6.5 or renumber), and boundary rules table.

- [ ] **Step 11:** Commit T2.

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/spec.yaml docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/foundations.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): reorganize enforcement authority — new governance.md, break circular delegation (3 findings)"
```

---

## Task 3 — Abort-Path Symmetry (5 findings)

**Finding count:** 5 P1 (3 corroborated, 1 singleton, 1 P2 related)
**Files:** routing-and-materiality.md, verification.md, pipeline-integration.md
**Depends on:** nothing — start immediately

### [SY-3] Fix Step 0 case (c) assertion count and add assertion (vii) to normative source

**Sources:** CC-2 + VR-3 (independent convergence)

verification.md labels "all 6 assertions" but enumerates 7 (i–vii). Assertion (vii) — capability flags remain absent after rejection — has no normative basis in routing-and-materiality.md.

**Decision:** Assertion (vii) IS a real normative requirement. The behavior it describes (capability flags physically absent after Stage A rejection) is already implied by pipeline-integration.md Stage A: "`upstream_handoff` MUST NOT be initialized — it remains absent." Add it to routing-and-materiality.md to make it explicit.

- [ ] **Step 1:** In routing-and-materiality.md §Material-Delta Gating, Step 0 case (c) post-abort behavior list (line 122), add a 7th behavior after item (6):
  > (7) All `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) MUST remain absent from pipeline state after rejection — no partial initialization. (Cross-reference: [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage A rejection behavior.)

- [ ] **Step 2:** In verification.md line 38, fix the label from "all 6 assertions" to "all 7 assertions".

### [SY-4] Add capability flag teardown rule to partial correction failure post-abort

**Sources:** CE-5 + IE-12 (cross-lens confirmation)

Step 0 case (c) specifies flag teardown; partial correction failure does not. Flags set at Stage B persist into undefined state.

- [ ] **Step 3:** In routing-and-materiality.md §Affected-Surface Validity, partial correction failure post-abort behavior (line 105), add after item (6) about `dialogue-orchestrated-briefing`:
  > (7) All `upstream_handoff` capability flags set during Stage B (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) MUST be torn down after capsule assembly abort — flags MUST NOT persist into post-abort pipeline state. This is symmetric with Step 0 case (c) post-abort behavior item (7).

### [CC-3] Add assertion (vii) to abort-path parity table

**Source:** CC-3 (P2, followup from CC-2)

The parity table maps 5 shared assertions but omits assertion (vii).

- [ ] **Step 4:** In verification.md, the abort-path parity section (line 59), add a row:
  > Capability flags torn down: (vii) / (7) — Step 0 requires physical absence (never initialized); partial correction failure requires teardown (flags set at Stage B are removed). Both achieve the same end state: no capability flags in post-abort pipeline state.

  Update the parity summary: "Both abort paths MUST produce identical behavior for **six** shared assertions" (was five).

### [SY-9] Add independent test fixture language to abort-path parity

**Sources:** VR-4 + IE-4 (independent convergence)

The parity table is a documentation cross-check, not an executable test.

- [ ] **Step 5:** In verification.md, after the parity table, add:
  > **Independent test mandate:** Each abort path MUST have an independent test fixture. The parity table is a structural cross-reference — it is NOT a substitute for behavioral testing. A single shared fixture that exercises both paths and masks regressions in one path is prohibited. Verification: two separate test fixtures (one per abort path) MUST produce independently passing results.

### [CC-7] Resolve physical vs. logical absence ambiguity in pipeline-integration.md

**Source:** CC-7 (P2, followup)
**File:** pipeline-integration.md §Two-Stage Admission, Stage A rejection paragraph

- [ ] **Step 6:** In pipeline-integration.md, Stage A rejection behavior, replace:
  > All capability flags are treated as absent (equivalent to `false`).

  With:
  > All capability flags are physically absent — `upstream_handoff` is not initialized, so no capability flag key exists in any state object. The "equivalent to `false`" characterization applies to downstream boolean checks (which evaluate absent keys as false), not to the storage representation.

- [ ] **Step 7:** Commit T3.

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/pipeline-integration.md
git commit -m "fix(spec): resolve abort-path asymmetry — flag teardown, assertion (vii), parity (5 findings)"
```

---

## Task 4 — Behavioral Contract Gaps (5 findings)

**Finding count:** 5 P1 (1 corroborated, 4 singleton)
**Files:** capsule-contracts.md, routing-and-materiality.md
**Depends on:** nothing — start immediately

### [SY-2] Fix Contract 3 provenance rule — make emitter-subject explicit

**Sources:** AA-9 + CE-4 (cross-lens confirmation)
**File:** capsule-contracts.md line 212

The provenance rule says "do not reference an NS `artifact_id` that was not validated via two-stage admission" — but two-stage admission is a pipeline-authority procedure that only the dialogue skill (emitter) performs. AR and NS (advisory/tolerant consumers of feedback) have no admission path.

- [ ] **Step 1:** In capsule-contracts.md line 212, replace:
  > The feedback capsule MUST omit `source_artifacts` entries for any upstream capsule (NS handoff) that was not structurally consumed — do not reference an NS `artifact_id` that was not validated via two-stage admission (sentinel detected in conversation context, schema validated against expected format, normalized to `upstream_handoff` pipeline state).

  With:
  > The `/dialogue` skill (emitter) MUST omit `source_artifacts` entries for any upstream NS handoff that was not structurally consumed during that invocation — do not reference an NS `artifact_id` that was not validated via two-stage admission ([pipeline-integration.md](pipeline-integration.md#two-stage-admission)). Two-stage admission is a pipeline-authority procedure executed by dialogue; AR and NS consumers of the feedback capsule do not perform admission and are not constrained by this rule.

### [SY-6] Add hold_reason precedence rule for routing-stage vs. capsule-assembly conflict

**Sources:** CE-10 + IE-2 (cross-lens confirmation)
**File:** routing-and-materiality.md §Ambiguous Item Behavior (line 50)

`hold_reason` can be assigned at routing stage (`routing_pending`) and at capsule assembly time. No precedence rule exists for valid-to-valid overwrites.

- [ ] **Step 2:** In routing-and-materiality.md, after the "Non-response behavior" paragraph (line 50), add:
  > **`hold_reason` assignment precedence:** Routing-stage assignment is authoritative. If `hold_reason` is set to `routing_pending` during the routing stage, capsule assembly MUST NOT overwrite it with a different valid value. Capsule assembly MAY set `hold_reason` to `routing_pending` for items that were not routed (implementation timing flexibility), but MUST NOT clear or replace an existing `routing_pending` value. The emission-time gate validates the final value but does not resolve valid-to-valid conflicts — those are prevented by this precedence rule.

### [CE-2] Add hold_reason validation to per-entry processing order

**Source:** CE-2 (P1, singleton)
**File:** routing-and-materiality.md §Affected-Surface Validity, processing order (line 95)

Processing order lists 3 steps but omits `hold_reason` validation.

- [ ] **Step 3:** In routing-and-materiality.md line 95, after step (3) "`materiality_source` validation", add step (4):
  > (4) Apply `hold_reason` validation — correct invalid values to `null` with structured warning (always recoverable). `hold_reason` validation runs after the correction pipeline and `classifier_source`/`materiality_source` validation — it operates on `unresolved[]` entries only (not `feedback_candidates[]`).

### [CE-3] Clarify consumer-side durable store check ordering for record_status absent + file exists

**Source:** CE-3 (P1, singleton)
**File:** routing-and-materiality.md §Selective Durable Persistence (line 274)

The consumer-side contract for the double-fault case (record_status absent + file exists) is specified but the ordering between checks is ambiguous.

- [ ] **Step 4:** In routing-and-materiality.md line 274, in the consumer-side contract, after the `record_status` absent paragraph, add:
  > **Check ordering:** The consumer MUST check fields in this order: (1) `record_path` nullity, (2) file existence at `record_path`, (3) `record_status` field presence, (4) `record_status` value, (5) file content integrity. Each check short-circuits to the appropriate fallback — later checks are unreached if an earlier check triggers fallback. This ordering ensures the `record_status`-absent guard (step 3) fires before any file I/O (step 5).

### [IE-11] Define corrupt content re-encounter behavior at precedence level 3

**Source:** IE-11 (P1, singleton)
**File:** routing-and-materiality.md §Selective Durable Persistence (line 274)

When durable store lookup (level 2) finds corrupt content, falls through to conversation-local scan (level 3). If conversation-local scan finds the same corrupt capsule, re-encounter is undefined.

- [ ] **Step 5:** In routing-and-materiality.md, after the consumer-side contract's case (6) (corrupt/unparseable), add:
  > **Re-encounter at level 3:** If the conversation-local sentinel scan (precedence level 3) discovers a capsule with the same `artifact_id` as the corrupt durable file, the consumer MUST still reject it if it fails the same validity checks (same content in both locations). Do NOT retry parsing — if the content was corrupt at level 2, it is corrupt at level 3. The consumer proceeds as if no feedback capsule exists and applies advisory/tolerant fallback behavior.

- [ ] **Step 6:** Commit T4.

```bash
git add docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/routing-and-materiality.md
git commit -m "fix(spec): close behavioral contract gaps — provenance, hold_reason, processing order (5 findings)"
```

---

## Task 5 — CI Enforcement Scope (5 findings)

**Finding count:** 5 P1 (1 corroborated, 4 singleton)
**Files:** verification.md, routing-and-materiality.md
**Depends on:** T2 (enforcement claims must be in correct authority files before adding verification rows and CI scope entries — governance.md clause IDs are referenced)

### [SY-5] Add verification.md entry for COMPOSITION_HELPERS.md existence check

**Sources:** CE-8 + IE-13 (cross-lens confirmation)

A MUST gate with no enforcement mechanism.

- [ ] **Step 1:** In verification.md §Capsule Contract Verification table, add a new row:
  > | `COMPOSITION_HELPERS.md` exists when helper functions exist | [governance.md](governance.md#helper-function-tracking) | Validates: governance.md §Helper Function Tracking. Automated (interim): CI check — when any PR modifies files in the feedback capsule assembly path, verify `COMPOSITION_HELPERS.md` exists in the repository root. Fail if helper functions are referenced from the capsule path but the file is absent. Structural: verify the file lists every function called from the feedback capsule assembly path (diff-based on each PR) |

### [IE-1] Enumerate file scope for no-auto-chaining grep check

**Source:** IE-1 (P1, singleton)
**File:** verification.md line 89

The auto-chaining grep check has no enumerated file scope.

- [ ] **Step 2:** In verification.md line 89 (no auto-chaining verification row), add explicit file scope after the structural check description:
  > **File scope for grep-based CI checks:** `adversarial-review/SKILL.md`, `next-steps/SKILL.md`, `dialogue/SKILL.md` (composition stub blocks), `packages/plugins/cross-model/references/composition-contract.md` (when authored), and `COMPOSITION_HELPERS.md` (when present). Do NOT apply to spec files, test fixtures, or documentation.

### [IE-3] Add CI enforcement gate for tautology_filter_applied absent-key warning

**Source:** IE-3 (P1, singleton)
**File:** verification.md line 91

The warning for absent `tautology_filter_applied` key has no CI enforcement.

- [ ] **Step 3:** In verification.md line 91, after test case (5), add:
  > **CI enforcement (interim):** Add to the grep-based CI check suite: verify the dialogue stub contains a code path that checks for `tautology_filter_applied` key presence (not just value) and emits a structured warning when the key is absent. Pattern: fail if the stub's Stage A/B admission code does not contain a key-presence check for `tautology_filter_applied`.

### [IE-6] Extend grep scope to include COMPOSITION_HELPERS.md

**Source:** IE-6 (P1, singleton)
**File:** verification.md lines 60–62

Grep checks for `classifier_source`, `materiality_source`, and `hold_reason` exclude `COMPOSITION_HELPERS.md`.

- [ ] **Step 4:** In verification.md lines 60–62, for each grep-based CI check row (`classifier_source`, `materiality_source`, `hold_reason`), update the file scope to include `COMPOSITION_HELPERS.md`:
  > File scope: skill stub files, composition contract, **and `COMPOSITION_HELPERS.md` (when present)**.

### [IE-7] Include contract file in sentinel consumption check during authoring window

**Source:** IE-7 (P1, singleton)
**File:** verification.md line 65

The consumption-side check for `dialogue-orchestrated-briefing` excludes the contract file during the authoring window.

- [ ] **Step 5:** In verification.md line 65, consumption-side interim CI check, update scope:
  > `grep -rn 'dialogue-orchestrated-briefing' <stub-files-excluding-dialogue> <composition-contract-when-authored>` — fail if any non-dialogue skill stub **or the composition contract** references this sentinel in a consumption pattern. Scope includes: AR stub, NS stub, and `packages/plugins/cross-model/references/composition-contract.md` (when authored).

- [ ] **Step 6:** Commit T5.

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): harden CI enforcement scope — COMPOSITION_HELPERS.md, grep file scope, tautology gate (5 findings)"
```

---

## Task 6 — Verification Spec Consistency (5 findings)

**Finding count:** 5 P1 (1 corroborated, 4 singleton)
**Files:** verification.md
**Depends on:** T1 (deferred table updates align with interim verification decisions), T3 (abort-path parity resolved)

### [SY-8] Fix dialogue-orchestrated-briefing tracking pointer

**Sources:** AA-10 + IE-10 (cross-lens confirmation)
**File:** verification.md §Deferred Verification (line 161)

The tracking pointer to delivery.md item #8 for sentinel suppression check activation is broken — item #8 doesn't enumerate the suppression as a tracked gate.

- [ ] **Step 1:** In verification.md line 161 (deferred entry for `dialogue-orchestrated-briefing`), update the activation responsibility reference:
  > Activation responsibility: tracked by [governance.md](governance.md#stub-composition-co-review-gate) (PR review gate scope). The co-review gate MUST include sentinel suppression verification as an explicit checklist item when the dialogue skill text is authored.

  Add to the cascade note:
  > **Activation checklist:** When dialogue stub is authored, activate simultaneously: (1) standalone coherence assertion (4), (2) partial correction failure assertion (6), (3) Step 0 case (c) sub-assertion (vi). All three assertions depend on the `dialogue-orchestrated-briefing` sentinel being present in the stub's internal pipeline — verify each assertion independently, not as a single shared test.

### [SY-10] Add deferred table entry for budget override context-compression

**Sources:** VR-5 + IE-9 (independent convergence)
**File:** verification.md §Deferred Verification (line 160)

The reclassified structural check has no deferred table entry.

- [ ] **Step 2:** In verification.md, replace the budget override deferred entry (line 160) with a properly specified entry:
  > | Budget override context-compression recovery | [routing-and-materiality.md](routing-and-materiality.md#budget-enforcement-mechanics) | **Structural check** (not behavioral — context compression cannot be simulated). **Acceptance criteria:** (1) Stub code contains a branch that checks whether a prior "continue" message is absent from visible context after budget exhaustion, (2) that branch emits re-confirmation text containing "context compression". **Pass criterion:** Both conditions met in stub code review. **Activation trigger:** When budget override code is authored in the dialogue skill stub. |

### [VR-5] Add acceptance criteria for budget override structural check

**Source:** VR-5 (P1, singleton) — addressed by SY-10 above (same fix).

### [VR-6] Address NS adapter partial-tier test infeasibility

**Source:** VR-6 (P1, singleton)
**File:** verification.md line 91

Test cases (1), (4), (6) require a configuration mechanism that doesn't exist.

- [ ] **Step 3:** In verification.md line 91, add a note after test cases (1), (4), (6):
  > **Fault injection mechanism (required for test cases 1, 4, 6):** These tests require a tier-level configuration point in the NS adapter (ability to suppress specific tiers or fail model calls). Either: (a) specify a test-mode flag or mock model call wrapper in the dialogue skill's composition stub that enables partial-tier execution for testing, or (b) reclassify test cases (1), (4), and (6) as structural checks — verify the stub code contains explicit tier-completion tracking logic with conditions for setting `tautology_filter_applied` to `false` when any tier is incomplete. **Decision: Reclassify as structural checks** — the NS adapter's tautology filter implementation in a skill context does not support external fault injection. Acceptance criteria: stub code contains a branch per tier that sets the flag to false when that tier does not complete.

### [VR-7] Convert cascade tracking to concrete deliverable

**Source:** VR-7 (P1, singleton)
**File:** verification.md line 161

"Track activation as a single milestone" is an informal process note.

- [ ] **Step 4:** In verification.md line 161 (cascade note in the dialogue-orchestrated-briefing deferred entry), replace:
  > Track activation as a single milestone.

  With:
  > **Concrete deliverable:** A single test file (or test block) that covers all three cascade assertions, activated by the same PR that authors the dialogue skill stub. The test file MUST be created in the same PR — the three assertions are not independently tracked. The interim PR description check is the active gate during authoring; the test file retires it.

- [ ] **Step 5:** Commit T6.

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): fix verification spec consistency — tracking pointers, deferred table, test feasibility (5 findings)"
```

---

## Task 7 — P2 Batch (14 findings)

**Finding count:** 14 P2
**Files:** routing-and-materiality.md, foundations.md, capsule-contracts.md, verification.md, README.md, decisions.md, pipeline-integration.md
**Depends on:** T2–T4 (P1 normative text changes may shift cross-references)

### [SY-7] Enumerate the 3-arc subset in completeness proof

**Sources:** CE-1 + CC-6 (independent convergence, P1 corroborated)
**File:** routing-and-materiality.md line 87
**Priority placement note:** Classified P1 in the report but placed in T7 (P2 batch) because the fix is a single-line enumeration addition with no normative behavior change — purely editorial clarity.

- [ ] **Step 1:** In routing-and-materiality.md line 87, change:
  > Rule 1 covers all 9 invalid tuples where `material: false` AND `suggested_arc ≠ dialogue_continue` (3 `affected_surface` values × 3 invalid `suggested_arc` values).

  To:
  > Rule 1 covers all 9 invalid tuples where `material: false` AND `suggested_arc ≠ dialogue_continue` (3 `affected_surface` values × 3 non-`dialogue_continue` `suggested_arc` values: `{adversarial-review, next-steps, ambiguous}`).

### [CC-4] Fix "inline stub" → "composition stub" term drift in foundations.md

**Source:** CC-4 (P2, independent)
**File:** foundations.md §Three-Layer Delivery Authority

- [ ] **Step 2:** In foundations.md Three-Layer Delivery Authority table (line 68), change Layer 3 entry from "Inline stubs (per skill)" to "Composition stubs (per skill)".

- [ ] **Step 3:** In foundations.md, replace all remaining "inline stub" occurrences in the Three-Layer Delivery Authority section with "composition stub". Retain one parenthetical clarification in the first occurrence: "(also called 'inline stub' in earlier drafts)".

### [CC-5] Add gate_id to upstream source boundary definition

**Source:** CC-5 (P2, independent)
**File:** routing-and-materiality.md §Routing Classification, upstream source boundary (line 23)

- [ ] **Step 4:** In routing-and-materiality.md line 23, extend the upstream source boundary:

  Replace:
  > MUST read upstream IDs exclusively from `upstream_handoff.source_findings[]` and `upstream_handoff.source_assumptions[]`.

  With:
  > MUST read upstream IDs exclusively from `upstream_handoff.source_findings[]`, `upstream_handoff.source_assumptions[]`, and `upstream_handoff.decision_gates[]` (for `gate_id` references). `task_id` references use `upstream_handoff.selected_tasks[]`.

### [AA-3] Add decisions authority ranking to README precedence section

**Source:** AA-3 (P2, singleton)
**File:** README.md §Precedence

- [ ] **Step 5:** In README.md §Precedence (line 33), after the fallback line, add:
  > - `decision_record`: decisions (sole holder)
  > - `review_gate`: governance (sole holder)

### [AA-5] Note Stage B enforcement preconditions in pipeline-integration.md

**Source:** AA-5 (P2, singleton)
**File:** pipeline-integration.md §Two-Stage Admission, Stage B

- [ ] **Step 6:** In pipeline-integration.md Stage B section, add a note:
  > **Authority note:** Stage B sets enforcement preconditions (capability flags) under pipeline authority. The enforcement actions that depend on these preconditions are defined in routing-and-materiality.md (routing authority) and governance.md (governance authority).

### [AA-8] Fix decisions.md D2 forward-reference standalone coherence

**Source:** AA-8 (P2, singleton)
**File:** decisions.md, D2 entry

- [ ] **Step 7:** In decisions.md, D2's description, add a brief inline explanation of the advisory/tolerant concept rather than relying solely on the forward reference to foundations.md. After the existing cross-reference, add:
  > (Advisory/tolerant: validate if present, fall back to alternative source if absent or invalid.)

### [CE-6] Add "optional fields do not invalidate" statement to Contracts 1 and 3

**Source:** CE-6 (P2, singleton)
**File:** capsule-contracts.md §Validity Criteria for Contracts 1 and 3

- [ ] **Step 8:** In capsule-contracts.md, after each validity criteria section (Contract 1 and Contract 3), add:
  > **Optional field absence:** Optional fields that are absent or null do NOT make the capsule invalid. Only required field absence or type violations trigger invalidity.

### [CE-7] Define post-abort prose synthesis ordering

**Source:** CE-7 (P2, singleton)
**File:** routing-and-materiality.md §Affected-Surface Validity, partial correction failure post-abort

- [ ] **Step 9:** In routing-and-materiality.md, partial correction failure post-abort section, add:
  > **Ordering:** Prose synthesis output MUST complete before the structured warning about the correction failure is emitted. The warning is appended after the synthesis, not interleaved with it.

### [IE-5] Define combined indeterminate state prose output

**Source:** IE-5 (P2, singleton)
**File:** routing-and-materiality.md §Budget Enforcement Mechanics, combined indeterminate state (line 230)

- [ ] **Step 10:** In routing-and-materiality.md line 230, after the combined indeterminate state paragraph, add:
  > **Prose output for combined indeterminate:** When both counter and override are indeterminate, the prose warning MUST include both conditions: "Budget counter and override confirmation are both unavailable due to context compression. Proceeding as if budget is available; override requires re-confirmation. Say `continue` to allow one more hop."

### [IE-8] Confirm record_path pre-computation is correctly classified as deferred

**Source:** IE-8 (P2, singleton)

No edit needed — IE-8 confirms the existing deferred classification is correct. Already addressed by the deferred verification entry.

### [VR-8] Cross-reference classifier_source grep gap interim mitigation

**Source:** VR-8 (P2, singleton)
**File:** verification.md line 60

- [ ] **Step 11:** In verification.md line 60, `classifier_source` grep check row, add cross-reference:
  > See also [governance.md](governance.md#constrained-field-literal-assignment-assertion) for the PR checklist gate that closes the variable-assignment gap during the interim period.

### [VR-9] Mark thread freshness scenarios 7+8 as regression tests

**Source:** VR-9 (P2, singleton)
**File:** verification.md line 100

- [ ] **Step 12:** In verification.md line 100, after the description of scenarios (7) and (8), add:
  > **Regression classification:** Scenarios (7) and (8) are required permanent regression tests, not one-time validation steps. They MUST be included in the standing test suite and re-run on any PR touching thread-continuation comparison logic.

### [VR-10] Specify mock-level write-failure injection

**Source:** VR-10 (P2, singleton)
**File:** verification.md line 56

- [ ] **Step 13:** In verification.md line 56, after the accepted risk statement, add:
  > **Alternative injection:** If a stub-level write-failure test double is feasible (intercept the file-write call with a double that raises a permission error), use it to verify the prose warning content includes the pre-computed path. If infeasible, add the prose warning content assertion to the structural review checklist: "verify the error handler's prose warning template includes a reference to the pre-computed `record_path` variable."

### [VR-11] Specify standalone coherence test fixture for dialogue

**Source:** VR-11 (P2, singleton)
**File:** verification.md line 69

- [ ] **Step 14:** In verification.md line 69, after "no additional context injection", add:
  > For the dialogue standalone coherence test: "without any upstream capsule present" means a clean conversation context with no prior skill output and no injected sentinels — only the user's question as input. The fixture MUST NOT contain any sentinel strings (`<!-- ar-capsule:`, `<!-- next-steps-dialogue-handoff:`, `<!-- dialogue-feedback-capsule:`, `<!-- dialogue-orchestrated-briefing -->`) in the conversation history.

- [ ] **Step 15:** Commit T7.

```bash
git add docs/superpowers/specs/skill-composability/
git commit -m "fix(spec): remediate 14 P2 findings from spec review round 10"
```

---

## Verification

After all 7 commits, verify:

- [ ] **Cross-reference integrity:** All relative markdown links in all spec files resolve to existing files and anchors. Run: `grep -rn '\[.*\](.*\.md' docs/superpowers/specs/skill-composability/ | grep -v '#'` to find unanchored links; manually verify anchored links.
- [ ] **Frontmatter consistency:** governance.md frontmatter matches spec.yaml authority entry.
- [ ] **Count consistency:** delivery.md retirement conditions say "9", verification.md validator table has 9 rows.
- [ ] **Assertion count consistency:** verification.md Step 0 case (c) says "all 7 assertions" and lists 7 (i–vii). Parity table has 6 shared assertions.
- [ ] **README accuracy:** README.md authority table, reading order, and boundary rules reflect governance.md addition.
- [ ] **spec.yaml validity:** `fallback_authority_order` has 10 entries (was 9), `boundary_rules` has 6 rules (was 4), `claim_precedence` has 3 entries (was 2).
