# Skill Composability Spec Remediation — Round 13

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 43 findings (25 P1, 18 P2) from the round 13 spec review — zero P0s, all findings are governance gate accuracy and enforcement surface completeness issues.

**Architecture:** All changes are spec text edits to markdown files in `docs/superpowers/specs/skill-composability/`. No code changes, no test changes. Each task targets one spec file, applying all findings for that file in a single pass to avoid re-reading.

**Tech Stack:** Markdown spec files with YAML frontmatter. Cross-reference validation via grep.

**Source:** Review report at `.review-workspace/synthesis/report.md`, ledger at `.review-workspace/synthesis/ledger.md`.

---

## File Change Map

| File | Findings | Priority |
|------|----------|----------|
| `governance.md` | SY-1, SY-2, SY-3, SY-5, SY-6, SY-9, SY-22, SY-27, SY-31, SY-34, SY-35, SY-36, SY-37, SY-42 | 10 P1, 4 P2 |
| `verification.md` | SY-4, SY-7, SY-8, SY-18, SY-19, SY-23, SY-24, SY-25, SY-28, SY-29, SY-30, SY-38, SY-41 | 8 P1, 5 P2 |
| `capsule-contracts.md` | SY-10, SY-11, SY-13, SY-16, SY-17 | 3 P1, 2 P2 |
| `delivery.md` | SY-9 (xref fix), SY-24, SY-32, SY-33, SY-40 | 2 P1, 3 P2 |
| `routing-and-materiality.md` | SY-12, SY-14, SY-39, SY-43 | 1 P1, 3 P2 |
| `foundations.md` | SY-15, SY-21 | 0 P1, 2 P2 |
| `README.md` | SY-20 | 0 P1, 1 P2 |

---

### Task 1: Fix governance.md — Gate Accuracy and Missing Gates

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/governance.md`

This is the most heavily affected file (14 findings). Edits are grouped by section within the file.

- [ ] **Step 1: Read the full file**

Read `governance.md` to have current content in context.

- [ ] **Step 2: SY-1 — Fix Constrained Field Literal-Assignment Assertion citation**

In §Constrained Field Literal-Assignment Assertion, replace:

```
Validates: routing-and-materiality.md §Dimension Independence (literal-assignment convention)
```

with:

```
Validates: routing-and-materiality.md §Dimension Independence (literal-assignment convention for `classifier_source` and `materiality_source`) + routing-and-materiality.md §Ambiguous Item Behavior + §Affected-Surface Validity (literal-assignment convention for `hold_reason`)
```

- [ ] **Step 3: SY-2 — Fix `supersedes` citation in Stub Composition Co-Review Gate**

In §Stub Composition Co-Review Gate, replace:

```
per the emitter-side MUST in lineage.md §DAG Structure
```

with:

```
per the emitter-side MUST in [capsule-contracts.md §Validity Criteria (Contract 3)](capsule-contracts.md#validity-criteria-contract-3) (field-presence obligation) and the minting rule in [lineage.md §DAG Structure](lineage.md#dag-structure) (value-assignment rule)
```

- [ ] **Step 4: SY-3 — Rewrite `hold_reason` Assignment and Placement Review item 1**

Replace item 1:

```
1. "Confirmed: exactly one authoritative write point for `hold_reason` exists — the routing stage sets `hold_reason: routing_pending` for held ambiguous items. No other code path assigns a non-null `hold_reason` value."
```

with:

```
1. "Confirmed: `hold_reason: routing_pending` is set for all held ambiguous items before capsule emission — verified that no held ambiguous item reaches `unresolved[]` without `hold_reason: routing_pending`, regardless of which stage (routing or capsule assembly) set it. If set at the routing stage, capsule assembly MUST NOT overwrite it. No code path sets `hold_reason` to any value other than `routing_pending` or `null`."
```

Also replace item 2:

```
2. "Confirmed: later stages (capsule assembly, emission-time gate) can only propagate or omit `hold_reason` — they MUST NOT clear, replace, or default over an existing `routing_pending` value."
```

with:

```
2. "Confirmed: if `hold_reason: routing_pending` is set at the routing stage, capsule assembly and emission-time gate MUST NOT clear, replace, or default over the existing value. If `hold_reason` is set only at capsule assembly time, no routing-stage write exists for that item. Verified by tracing all write sites for `hold_reason`."
```

- [ ] **Step 5: SY-5 — Expand `decomposition_seed` gate scope to all paths**

In §Stub Composition Co-Review Gate, replace:

```
PR checklist item: "Confirmed: NS adapter's `decomposition_seed` assignment is conditional on `--plan` being active. Verified by tracing the adapter code path."
```

with:

```
PR checklist item: "Confirmed: `decomposition_seed: true` is only reachable when `--plan` was active AND decomposition seeding actually ran. Verified by enumerating ALL code paths that assign or initialize `decomposition_seed` (not only the adapter's primary path — include default initializers, copy-construction, merge operations, and conditional branches), and confirming none set it to `true` outside the conditional gate."
```

- [ ] **Step 6: SY-37 — Add per-flag enumeration for Stage A rejection paths**

In §Stub Composition Co-Review Gate, replace:

```
PR checklist item: "Confirmed: adapter exit paths are exhaustively enumerated — including schema-validation-failure paths where `upstream_handoff` is never initialized. For rejection paths: verified no capability flags leak into pipeline state."
```

with:

```
PR checklist item: "Confirmed: adapter exit paths are exhaustively enumerated — including schema-validation-failure paths where `upstream_handoff` is never initialized. For rejection paths: verified `decomposition_seed`, `gatherer_seed`, `briefing_context`, and `tautology_filter_applied` are all absent from pipeline state — `upstream_handoff` is never initialized, so no capability flag key exists in any state object. Verified by tracing the Stage A rejection branch to confirm it exits before any capability flag assignment."
```

- [ ] **Step 7: SY-31 — Add test existence mandate to co-review gate**

After the `decomposition_seed` checklist item in §Stub Composition Co-Review Gate, add:

```
The co-review gate MUST additionally verify that the behavioral test for `decomposition_seed: true` when `--plan` not active (verification.md §Routing and Materiality Verification, NS adapter row) exists in the test suite and passes. Test file presence is a merge-blocking requirement — per verification.md, this is a P0 merge gate prerequisite.
```

- [ ] **Step 8: SY-22 — Fix unanchored cross-references in `source_artifacts` Provenance Review**

In §`source_artifacts` Provenance Review, replace:

```
Validates: capsule-contracts.md §Consumer Class (Contract 1) + §Contract 3 (provenance rule)
```

with:

```
Validates: [capsule-contracts.md §Consumer Class (Contract 1)](capsule-contracts.md#consumer-class-contract-1) + [capsule-contracts.md §Contract 3 (provenance rule)](capsule-contracts.md#contract-3-dialogue-feedback-capsule)
```

- [ ] **Step 9: SY-6 — Add Emission-Time Validation Step Ordering Gate**

After §Correction Rule Sequential Ordering Gate, add a new section:

```markdown
## Emission-Time Validation Step Ordering Gate

Validates: [routing-and-materiality.md §Affected-Surface Validity](routing-and-materiality.md#affected-surface-validity) (processing order steps 2-4)

**[Activates when emission-time validation code is authored]** PR checklist item: "Confirmed: emission-time validation steps are evaluated in order: (2) `classifier_source`, (3) `materiality_source`, (4) `hold_reason`. A structured warning from step 2 appears before step 3's warning in the diagnostic log path. Verified by structural inspection — the validation code path is a sequential chain with step 2 preceding step 3, step 3 preceding step 4."
```

- [ ] **Step 10: SY-9 — Add Abort-Path Independent Test Fixtures gate**

After §Partial Correction Failure Abort Gate, add:

```markdown
## Abort-Path Independent Test Fixtures Gate

Validates: [verification.md §Capsule Contract Verification](verification.md#capsule-contract-verification) (partial correction failure row — "Independent test mandate" clause)

**[Activates when dialogue stub abort-path code is authored]** PR checklist item: "Confirmed: two separate test fixtures exist — one for Step 0 case (c) abort path and one for partial correction failure abort path. No single shared fixture exercises both paths. Each fixture independently verifies all 7 post-abort assertions for its respective abort path. Verified by reviewing test file structure — two independent fixture functions/blocks, each with a complete assertion set."
```

- [ ] **Step 11: SY-27 — Add Budget Override Context-Compression Recovery Gate**

After §`budget_override_pending` Initialization Check, add:

```markdown
## Budget Override Context-Compression Recovery Gate

Validates: [routing-and-materiality.md §Budget Enforcement Mechanics](routing-and-materiality.md#budget-enforcement-mechanics) (override context-compression recovery)

**[Activates when budget override code is authored]** PR checklist item: "Confirmed: stub contains a branch detecting absent prior 'continue' message after budget exhaustion and context compression. That branch emits re-confirmation text containing 'context compression' and instructs the user to say 'continue' to allow one more hop. Verified by tracing the override state evaluation code path."
```

- [ ] **Step 12: SY-42 — Clarify teardown semantics in `upstream_handoff` Abort Teardown Check**

At the end of §`upstream_handoff` Abort Teardown Check, add:

```markdown
**Teardown semantics:** All four capability flags are set by the NS adapter at Stage B ([pipeline-integration.md §Two-Stage Admission](pipeline-integration.md#two-stage-admission) Stage B) — they are present when Step 0 runs. Teardown means: set the flag to `false` (or remove the key) regardless of whether the pipeline reached the stage where the flag is semantically consumed. A "torn down" flag MUST evaluate as `false` in any downstream check. Teardown is not a no-op — it clears flags that were initialized at Stage B but whose pipeline stage has not yet been reached.
```

- [ ] **Step 13: SY-34 + SY-35 + SY-36 — Add regression gate items to existing gates**

In §Thread Freshness Numeric Comparison Check, after the existing PR checklist item, add:

```
**Regression gate:** PRs touching thread-continuation comparison logic MUST confirm scenarios (7) and (8) from [verification.md §Routing and Materiality Verification](verification.md#routing-and-materiality-verification) pass. These are permanent regression tests, not one-time validation steps.
```

After §Correction Rule Sequential Ordering Gate, add to the existing checklist item:

```
Additionally confirmed: a valid tuple (e.g., `diagnosis/true/adversarial-review`) traverses the correction pipeline without reaching rule 5's defensive fallback. Verified by tracing the valid tuple through the if-else chain — the chain exits at the valid-tuple pass-through condition before rule 5 branch.
```

Add a new section after §Emission-Time Validation Step Ordering Gate:

```markdown
## Lineage Key Propagation Regression Gate

Validates: [lineage.md §Key Propagation](lineage.md#key-propagation) (`lineage_root_id` immutability)

**[Active for any PR touching key propagation or capsule minting logic]** PR checklist item: "Confirmed: `lineage_root_id` immutability regression test passes — multi-hop chain test asserting `lineage_root_id` string equality across all hops re-executed and passing."
```

- [ ] **Step 14: Verify all new anchored cross-references resolve**

Run: `grep -oP '\(([^)]+\.md#[^)]+)\)' docs/superpowers/specs/skill-composability/governance.md | sort -u`

Verify each anchor resolves to a heading in the target file.

- [ ] **Step 15: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): remediate governance.md gate accuracy + add missing gates from review round 13

Addresses SY-1, SY-2, SY-3, SY-5, SY-6, SY-9, SY-22, SY-27, SY-31, SY-34, SY-35, SY-36, SY-37, SY-42"
```

---

### Task 2: Fix verification.md — Test Coverage and Parity Table Repair

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/verification.md`

13 findings. The parity table needs comprehensive re-derivation (pattern cluster), not per-finding patches.

- [ ] **Step 1: Read the file**

Read `verification.md` in sections (it's large). Focus on: §Interim Materiality Verification Protocol, the partial correction failure row in §Capsule Contract Verification, §Routing and Materiality Verification, §Lineage Verification, §Validator Acceptance Criteria, §Deferred Verification.

- [ ] **Step 2: SY-18 + SY-4 + SY-38 — Re-derive the abort-path parity table**

In the partial correction failure row of §Capsule Contract Verification, replace the entire parity sub-table with a corrected version. The correct mapping (from routing-and-materiality.md's enumeration) is:

| Assertion | Step 0 case (c) | Partial correction failure |
|-----------|-----------------|---------------------------|
| No feedback capsule sentinel | (i) | (1) |
| No capsule body emitted | (ii) | (2) — explicit, not implicit |
| No durable file written | (iii) | (3) |
| Structured warning in prose | (iv) | (4) |
| No hop suggestion in prose | (v) | (5) |
| No `dialogue-orchestrated-briefing` sentinel | (vi) | (6) |
| All capability flags torn down | (vii) | (7) |

Key changes:
- SY-18: "No durable file" corrected from (5) to (3); "No hop suggestion" corrected from (7) to (5)
- SY-4: "No capsule body emitted" changed from "implicit in (1)" to explicit "(2)"
- SY-38: Assertions (f) and (g) consolidated into single "All capability flags torn down" row

Also add the explicit body-absence assertion to the partial correction failure test: "Assert no YAML block matching the feedback capsule schema appears in the output, independent of sentinel presence."

- [ ] **Step 3: SY-7 — Fix `hold_reason` grep pattern to POSIX-compatible**

In the `hold_reason` grep-based CI enforcement row, replace:

```
Pattern: `hold_reason.*(?!routing_pending|null)` or equivalent.
```

with:

```
Pattern (POSIX-compatible two-step): `grep 'hold_reason' <files> | grep -Ev 'hold_reason:\s*(routing_pending|null)\s*$'` — matches lines containing `hold_reason` assignment, then rejects lines where the value is exactly `routing_pending` or `null`. Does NOT require PCRE. Equivalent to the `classifier_source.*ambiguous` positive-match approach used for `classifier_source` and `materiality_source`.
```

- [ ] **Step 4: SY-8 — Add check #10 to validator acceptance criteria**

In §Validator Acceptance Criteria table, after check #9, add:

```
| 10 | `hold_reason` variable-assignment | [routing-and-materiality.md §Affected-Surface Validity](routing-and-materiality.md#affected-surface-validity) | `hold_reason` assignments in feedback capsule assembly path use only literal values from `{routing_pending, null}` — no variable-mediated assignments. Parallel to the `classifier_source`/`materiality_source` check (checks extending the same variable-assignment gap closure) | Governance.md §Constrained Field Literal-Assignment Assertion (active — covers all three fields) |
```

Also add to the minimum fixture set: "one stub that assigns `hold_reason` from a variable (fails check 10 — `hold_reason` variable-assignment)."

- [ ] **Step 5: SY-19 — Fix stale count "three consumer test cases"**

In the "Consumer-side `write_failed` handling" row, replace:

```
Behavioral: three consumer test cases
```

with:

```
Behavioral: five consumer test cases
```

- [ ] **Step 6: SY-23 — Add re-execution trigger to interim materiality protocol**

At the end of §Interim Materiality Verification Protocol, add:

```
The walk-through MUST also be re-executed on any PR that modifies routing-and-materiality.md §Affected-Surface Validity (correction rules 1-5, the 24-case matrix, or the consequence prohibitions). The PR description MUST include the re-execution confirmation.
```

- [ ] **Step 7: SY-24 — Add activation trigger for tautology_filter_applied CI check**

In the NS adapter `tautology_filter_applied` test row, CI enforcement clause, add:

```
Activation: when dialogue composition stub is authored (per delivery.md §Governance Gate Activation Checklist).
```

- [ ] **Step 8: SY-28 — Expand combined indeterminate test to verify all 6 template elements**

In the combined budget/override indeterminate row, expand the pass criterion:

Replace:

```
Verify (1) budget treated as not-exhausted, (2) prose warning emitted referencing both indeterminate sources (budget counter AND override state), satisfying the constrained semantic template
```

with:

```
Verify (1) budget treated as not-exhausted, (2) prose warning emitted containing all 6 ordered template elements: (a) "context compression" as cause, (b) "budget counter" unavailability, (c) "override" re-confirmation required, (d) proceeding as if budget available, (e) "continue" instruction, (f) "one more hop" scope. Assert elements appear in listed order by checking each appears after the previous in the output string
```

- [ ] **Step 9: SY-25 + SY-29 + SY-30 + SY-41 — Minor P2 verification additions**

**SY-25:** In the `topic_key` normalization rules row, add test fixture (5): "Two independent chains sharing the same `topic_key` but different `lineage_root_id` values — verify the budget counter for chain A is unaffected by hops in chain B."

**SY-29:** In the tautology filter Tiers 1 and 2 row, add: "Test case (3): inject a handoff with a task description that parrots a finding verbatim (Tier 2 match). Verify via structural trace that the Tier 3 model call is NOT invoked (Tier 3 skipped)."

**SY-30:** In the `supersedes` minting rule row, amend scenario (1) to add: "Assert `supersedes` key IS present in capsule YAML (key exists) AND value is `null` — a capsule omitting the `supersedes` key entirely fails this assertion."

**SY-41:** In the `supersedes` minting rule row, add: "Enforcement: governance.md §Stub Composition Co-Review Gate provides PR-level reviewer verification for `supersedes` key-presence."

- [ ] **Step 10: Verify cross-references**

Same grep check as Task 1 Step 14 for verification.md.

- [ ] **Step 11: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate verification.md test coverage + parity table from review round 13

Addresses SY-4, SY-7, SY-8, SY-18, SY-19, SY-23, SY-24, SY-25, SY-28, SY-29, SY-30, SY-38, SY-41"
```

---

### Task 3: Fix capsule-contracts.md — Contract Completeness

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/capsule-contracts.md`

5 findings — 3 P1, 2 P2.

- [ ] **Step 1: Read the file**

Read `capsule-contracts.md` fully.

- [ ] **Step 2: SY-16 — Move `supersedes` compatibility exception to shared section**

Before §Contract 1, add a new section:

```markdown
## Shared Validity Rules

**`supersedes` field compatibility (all three contracts):** Emitters MUST include `supersedes` in every capsule and set it to either the prior `artifact_id` of the same kind and subject, or `null` (per the minting rule in [lineage.md §DAG Structure](lineage.md#dag-structure)). Consumers MUST treat an absent `supersedes` key as equivalent to `supersedes: null` for v1 validity — absent `supersedes` does NOT make the capsule invalid. This is a narrow field-specific compatibility exception for `supersedes` only, not a broad reclassification of "optional" semantics. Governance and conformance tooling SHOULD still flag `supersedes` omission as an emitter defect (the minting rule is a MUST).

**Optional field absence (all three contracts):** Optional fields that are absent or null do NOT make the capsule invalid. Only required field absence or type violations trigger invalidity.
```

Remove the `supersedes` compatibility paragraph from §Validity Criteria (Contract 3), replacing it with: "See [Shared Validity Rules](#shared-validity-rules) for the `supersedes` field compatibility rule that applies to all three contracts."

Remove the duplicate "Optional field absence" paragraphs from Contracts 1 and 3, replacing each with: "See [Shared Validity Rules](#shared-validity-rules) for the optional field absence rule."

- [ ] **Step 3: SY-10 — Add diagnostic MUST to Contract 1 consumer class**

In §Consumer Class (Contract 1), after "NS validates the capsule if present; falls back to prose parsing if absent or invalid.", add:

```
When falling back, NS MUST emit a one-line prose diagnostic (per [foundations.md §Consumer Classes](foundations.md#consumer-classes)).
```

- [ ] **Step 4: SY-11 — Add `record_path` annotation to Contract 2 schema**

In §Schema (Contract 2), change the `record_path: null` line to:

```yaml
record_path: null  # Optional — always null in v1 (NS does not write files). Omitting this field does not invalidate the capsule.
```

- [ ] **Step 5: SY-13 — Add `hold_reason` constraint note to Contract 3 schema**

After the `hold_reason` annotation in the Contract 3 schema, add a schema constraint note:

```
**`hold_reason` value constraint:** `hold_reason` MUST be `routing_pending` or `null`/omitted. The normative constraint and emission-time validation gate are defined in [routing-and-materiality.md §Ambiguous Item Behavior](routing-and-materiality.md#ambiguous-item-behavior) and [§Affected-Surface Validity](routing-and-materiality.md#affected-surface-validity).
```

- [ ] **Step 6: SY-17 — Add `thread_created_at` precision note to Contract 3 validity**

In §Validity Criteria (Contract 3), after the required fields list, add:

```
**`thread_created_at` precision tolerance:** A value without milliseconds (e.g., `2026-03-18T14:30:52Z`) is well-typed for validity purposes — precision normalization is an emitter obligation (see schema annotation), not a consumer-side rejection criterion.
```

- [ ] **Step 7: Verify cross-references and commit**

```bash
git add docs/superpowers/specs/skill-composability/capsule-contracts.md
git commit -m "fix(spec): remediate capsule-contracts.md contract completeness from review round 13

Addresses SY-10, SY-11, SY-13, SY-16, SY-17"
```

---

### Task 4: Fix delivery.md — Gate Activation Tracking

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/delivery.md`

5 findings.

- [ ] **Step 1: Read delivery.md**

- [ ] **Step 2: SY-9 — Fix governance gate reference in activation checklist**

In §Governance Gate Activation Checklist, in the "Dialogue consumer stub (durable store behavior)" row, replace:

```
Abort-Path Independent Test Fixtures (two separate fixtures — one per abort path, no shared fixture)
```

with:

```
Abort-Path Independent Test Fixtures Gate (two separate fixtures — one per abort path, no shared fixture — see governance.md §Abort-Path Independent Test Fixtures Gate)
```

Add a new row to the checklist:

```
| Dialogue correction pipeline code (correction rules 1-5) | Abort-Path Independent Test Fixtures Gate (partial correction failure path fixture) |
```

- [ ] **Step 3: SY-24 — Add tautology_filter_applied CI check to activation checklist**

Add a row to the activation checklist:

```
| Dialogue composition stub (Stage A/B admission) | `tautology_filter_applied` key-presence grep-based CI check |
```

- [ ] **Step 4: SY-33 — Update item #10 to acknowledge active governance gate**

In Open Items, update item #10:

```
| 10 | Consumer-side 5-step check ordering structural verification | Deferred (automated) / **Active (interim: governance gate)** | Interim enforcement: [governance.md §Consumer Durable Store Check Ordering Gate](governance.md#consumer-durable-store-check-ordering-gate) provides active PR checklist enforcement (structural trace). Deferred automation: add to `validate_composition_contract.py` scope when implemented. Activation: when consumer stub code is authored. |
```

- [ ] **Step 5: SY-32 — Add sentinel suppression cascade test to open items**

Add item #13:

```
| 13 | `dialogue-orchestrated-briefing` cascade test file | Deferred (activates when dialogue stub is authored) | Three assertions: standalone coherence assertion (4), partial correction failure assertion (6), Step 0 case (c) sub-assertion (vi). Test file MUST be created in the same PR that authors the dialogue stub. Retirement condition: test file created and passing in dialogue stub authoring PR. |
```

- [ ] **Step 6: SY-26 — Add `record_path` schema non-null declaration to governance gate and delivery.md**

In governance.md §`record_path` Null-Prevention Review, after the existing PR checklist item, add:

```
Additionally confirmed: the feedback capsule schema definition declares `record_path` as a required non-null field (schema-level enforcement), not just that no code path emits null (behavioral enforcement). These are distinct checks — the schema declaration prevents null at the type level; the code-path trace prevents null at the implementation level.
```

In delivery.md §Open Items, update the note for validator check #3's interim path. Replace the reference to the nonexistent "deferred verification checklist" by adding to item #6's scope:

```
Validator check #3 interim: governance.md §`record_path` Null-Prevention Review provides active PR checklist enforcement (code-path trace + schema declaration check). Deferred automation: `validate_composition_contract.py` check #3 adds schema-level enforcement when implemented.
```

- [ ] **Step 7: SY-40 — Define COMPOSITION_HELPERS.md CI scope**

In item #12, update:

```
| 12 | `COMPOSITION_HELPERS.md` CI check scope | Active (interim) | CI check triggers on PRs modifying files in the feedback capsule assembly path. Scope: skill stub files (AR, NS, dialogue composition sections), composition contract, `COMPOSITION_HELPERS.md` itself, and any file imported by the dialogue skill's capsule emission code path. When a PR introduces helper functions in a file not in the enumerated list, the CI check MUST still trigger if `COMPOSITION_HELPERS.md` is not updated — use `COMPOSITION_HELPERS.md` diff as a secondary trigger alongside file-path matching. Do NOT apply to spec files, test fixtures, or documentation. |
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate delivery.md gate activation tracking from review round 13

Addresses SY-9, SY-24, SY-26, SY-32, SY-33, SY-40"
```

---

### Task 5: Fix routing-and-materiality.md — Behavioral Clarity

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`

4 findings — 1 P1, 3 P2.

- [ ] **Step 1: Read the relevant sections**

Read §Ambiguous Item Behavior, §Budget Enforcement Mechanics, §No Auto-Chaining.

- [ ] **Step 2: SY-12 — Add stage labels to Ambiguous Item Behavior table**

In §Ambiguous Item Behavior, change the first table's header from:

```
| Condition | User-Facing Behavior (pre-correction) |
```

Verify this header is already labeled "(pre-correction)" — it is. Add a cross-reference note after the `material: false` + `ambiguous` row:

```
Post-correction placement for this item: see [§Post-Correction Placement Rules](#post-correction-placement-rules) table below (emission-state view of the same item after correction pipeline runs).
```

- [ ] **Step 3: SY-14 — Add explicit Stage A → Step 0 case (b) cross-reference**

In §Material-Delta Gating Step 0, case (b), after "If no `upstream_handoff` exists: precondition trivially satisfied (standalone dialogue invocation).", add:

```
This includes the Stage A rejection path — when [pipeline-integration.md §Two-Stage Admission](pipeline-integration.md#two-stage-admission) Stage A rejects a capsule, `upstream_handoff` is never initialized, and Step 0 routes to this case.
```

- [ ] **Step 4: SY-39 — Extend budget indeterminate rule for NS-handoff-derived `lineage_root_id`**

In §Context compression resilience, after the indeterminate state paragraph, add:

```
**NS-handoff-derived `lineage_root_id`:** When `lineage_root_id` is inherited from an NS handoff (non-null, non-self — i.e., `lineage_root_id ≠ this artifact's artifact_id`) but the budget scan returns 0 matching artifacts, treat the counter as indeterminate and apply the same prose warning and not-exhausted default. This extends the indeterminate rule to cover the case where upstream hops are invisible due to context compression but the inherited `lineage_root_id` implies prior chain membership.
```

- [ ] **Step 5: SY-43 — Add enforcement-depth note to No Auto-Chaining**

At the end of §No Auto-Chaining, add:

```
**Enforcement depth for helper-mediated delegation (v1 limitation):** Until `validate_composition_contract.py` closes the helper-mediated delegation gap ([delivery.md](delivery.md#open-items) item #6 acceptance criterion), the co-review gate ([governance.md §Stub Composition Co-Review Gate](governance.md#stub-composition-co-review-gate)) is the sole enforcement mechanism for helper-mediated indirect delegation. The co-review gate MUST be treated as a hard gate (not advisory) for PRs introducing new helper functions in the feedback capsule assembly path.
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md
git commit -m "fix(spec): remediate routing-and-materiality.md behavioral clarity from review round 13

Addresses SY-12, SY-14, SY-39, SY-43"
```

---

### Task 6: Fix foundations.md + README.md — Minor P2 Fixes

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/foundations.md`
- Modify: `docs/superpowers/specs/skill-composability/README.md`

3 findings — all P2.

- [ ] **Step 1: SY-15 — Add provenance rule note to foundations.md consumer class table**

In §Consumer Classes, after the fallback source table, add:

```
**`source_artifacts` provenance rule (all consumer classes):** When a consumer falls back (advisory/tolerant) or rejects (strict/deterministic), the downstream capsule's `source_artifacts[]` MUST omit entries for any upstream capsule that was not structurally consumed. See [capsule-contracts.md §Consumer Class (Contract 1)](capsule-contracts.md#consumer-class-contract-1) and [§Contract 3](capsule-contracts.md#contract-3-dialogue-feedback-capsule) for per-contract provenance rules.
```

- [ ] **Step 2: SY-21 — Add external_artifacts cross-reference to foundations.md**

In §Three-Layer Delivery Authority, after "When the contract diverges from the spec, the spec is authoritative and the contract must be updated.", add:

```
**Conflict resolution rule:** The `spec_files_win` conflict rule for the composition contract is machine-readable in `spec.yaml`'s `external_artifacts` block. See `spec.yaml` lines 67–77 for the full external artifact declaration including `governed_by`, `authority_context`, and `conflict_rule` fields.
```

- [ ] **Step 3: SY-20 — Add "two-stage admission" to README pipeline description**

In README.md §Authority Model table, change the `pipeline` row description from:

```
Adaptive --plan, adapter pattern, decomposition, tautology filter, pipeline threading
```

to:

```
Adaptive --plan, two-stage admission, adapter pattern, decomposition, tautology filter, pipeline threading
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/skill-composability/foundations.md docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): remediate P2 findings in foundations.md + README.md from review round 13

Addresses SY-15, SY-20, SY-21"
```

---

## Finding Coverage Checklist

Every finding from the review report is addressed by this plan:

| SY | File | Task | Priority |
|----|------|------|----------|
| SY-1 | governance.md | Task 1 Step 2 | P1 |
| SY-2 | governance.md | Task 1 Step 3 | P2 |
| SY-3 | governance.md | Task 1 Step 4 | P1 |
| SY-4 | verification.md | Task 2 Step 2 | P1 |
| SY-5 | governance.md | Task 1 Step 5 | P1 |
| SY-6 | governance.md | Task 1 Step 9 | P1 |
| SY-7 | verification.md | Task 2 Step 3 | P1 |
| SY-8 | verification.md | Task 2 Step 4 | P1 |
| SY-9 | governance.md + delivery.md | Task 1 Step 10 + Task 4 Step 2 | P1 |
| SY-10 | capsule-contracts.md | Task 3 Step 3 | P1 |
| SY-11 | capsule-contracts.md | Task 3 Step 4 | P1 |
| SY-12 | routing-and-materiality.md | Task 5 Step 2 | P1 |
| SY-13 | capsule-contracts.md | Task 3 Step 5 | P1 |
| SY-14 | routing-and-materiality.md | Task 5 Step 3 | P1 |
| SY-15 | foundations.md | Task 6 Step 1 | P2 |
| SY-16 | capsule-contracts.md | Task 3 Step 2 | P1 |
| SY-17 | capsule-contracts.md | Task 3 Step 6 | P2 |
| SY-18 | verification.md | Task 2 Step 2 | P1 |
| SY-19 | verification.md | Task 2 Step 5 | P1 |
| SY-20 | README.md | Task 6 Step 3 | P2 |
| SY-21 | foundations.md | Task 6 Step 2 | P2 |
| SY-22 | governance.md | Task 1 Step 8 | P2 |
| SY-23 | verification.md | Task 2 Step 6 | P1 |
| SY-24 | verification.md + delivery.md | Task 2 Step 7 + Task 4 Step 3 | P1 |
| SY-25 | verification.md | Task 2 Step 9 | P2 |
| SY-26 | governance.md + delivery.md | Task 4 Step 6 | P1 |
| SY-27 | governance.md | Task 1 Step 11 | P1 |
| SY-28 | verification.md | Task 2 Step 8 | P1 |
| SY-29 | verification.md | Task 2 Step 9 | P2 |
| SY-30 | verification.md | Task 2 Step 9 | P2 |
| SY-31 | governance.md | Task 1 Step 7 | P1 |
| SY-32 | delivery.md | Task 4 Step 5 | P2 |
| SY-33 | delivery.md | Task 4 Step 4 | P1 |
| SY-34 | governance.md | Task 1 Step 13 | P2 |
| SY-35 | governance.md | Task 1 Step 13 | P2 |
| SY-36 | governance.md | Task 1 Step 13 | P2 |
| SY-37 | governance.md | Task 1 Step 6 | P1 |
| SY-38 | verification.md | Task 2 Step 2 | P1 |
| SY-39 | routing-and-materiality.md | Task 5 Step 4 | P2 |
| SY-40 | delivery.md | Task 4 Step 6 | P2 |
| SY-41 | verification.md | Task 2 Step 9 | P2 |
| SY-42 | governance.md | Task 1 Step 12 | P1 |
| SY-43 | routing-and-materiality.md | Task 5 Step 5 | P2 |
