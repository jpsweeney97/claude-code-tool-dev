---
module: governance
status: active
normative: true
authority: governance
---

# Governance

PR review gate procedures for composition system changes. Each gate cites the normative clause it enforces — gates are derivative, not independently normative.

## Stub Composition Co-Review Gate

Validates: routing-and-materiality.md §No Auto-Chaining + pipeline-integration.md §Two-Stage Admission Stage B (enforcement basis)

Reviewer confirms no helper-mediated indirect skill delegation via static code inspection. PR checklist item: "Confirmed: stub does not programmatically invoke any skill via model output or helper delegation chains. Helper functions in the feedback capsule assembly path: [explicitly name each function]. Composition paths verified by static inspection of the named functions."

Reviewer (not author) MUST independently verify the helper function list is complete and that no named function delegates to another skill. For each named helper function: confirm no assignment of `classifier_source` or `materiality_source` outside the literal set `{rule, model}`.

PR checklist item: "Confirmed: NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags. Key presence verified (not just value correctness). Absence is a gate failure requiring remediation before merge."

The co-review gate MUST also verify the NS adapter sets `decomposition_seed: true` only when `--plan` was active AND decomposition seeding actually ran — per pipeline-integration.md §Two-Stage Admission Stage B. A false `decomposition_seed` causes Step 0 case (c) abort with no recovery path. PR checklist item: "Confirmed: `decomposition_seed: true` is only reachable when `--plan` was active AND decomposition seeding actually ran. Verified by enumerating ALL code paths that assign or initialize `decomposition_seed` (not only the adapter's primary path — include default initializers, copy-construction, merge operations, and conditional branches), and confirming none set it to `true` outside the conditional gate."

The co-review gate MUST additionally verify that the behavioral test for `decomposition_seed: true` when `--plan` not active (verification.md §Routing and Materiality Verification, NS adapter row) exists in the test suite and passes. Test file presence is a merge-blocking requirement — per verification.md, this is a P0 merge gate prerequisite.

The co-review gate enforcement surface covers ALL adapter exit paths, including Stage A rejection (where `upstream_handoff` is never initialized). When Stage A rejects a capsule, the adapter exits before `upstream_handoff` is constructed — `tautology_filter_applied` key-presence cannot be checked on an object that does not exist. PR checklist item: "Confirmed: adapter exit paths are exhaustively enumerated — including schema-validation-failure paths where `upstream_handoff` is never initialized. For rejection paths: verified `decomposition_seed`, `gatherer_seed`, `briefing_context`, and `tautology_filter_applied` are all absent from pipeline state — `upstream_handoff` is never initialized, so no capability flag key exists in any state object. Verified by tracing the Stage A rejection branch to confirm it exits before any capability flag assignment."

The co-review gate MUST verify that `supersedes` is always present (not omitted) in emitted capsules, per the emitter-side MUST in [capsule-contracts.md §Validity Criteria (Contract 3)](capsule-contracts.md#validity-criteria-contract-3) (field-presence obligation) and the minting rule in [lineage.md §DAG Structure](lineage.md#dag-structure) (value-assignment rule). Consumer-side tolerance (treating absent `supersedes` as null) does NOT relax the emitter obligation — the consumer compatibility exception is defensive, not normative.

## Helper Function Tracking

Validates: routing-and-materiality.md §No Auto-Chaining (enforcement basis)

Any function called from the feedback capsule assembly path MUST be tracked in a checked-in list (`COMPOSITION_HELPERS.md` or equivalent) and diffed on each PR — this makes new helpers visible without requiring deep static analysis.

`COMPOSITION_HELPERS.md` (or equivalent) is a required deliverable for any PR that introduces helper functions called from the feedback capsule assembly path. The file MUST exist before the co-review gate can pass — absence of the file when helper functions exist is a gate failure, not a deferral.

**CI scope activation for composition contract:** The PR that creates `packages/plugins/cross-model/references/composition-contract.md` MUST enable the no-auto-chaining grep check for the contract file in CI configuration. The grep check self-activates during contract authoring — a co-reviewer MUST verify the CI scope was updated as part of the contract authoring PR.

## Constrained Field Literal-Assignment Assertion

Validates: routing-and-materiality.md §Dimension Independence (literal-assignment convention for `classifier_source` and `materiality_source`) + routing-and-materiality.md §Ambiguous Item Behavior + §Affected-Surface Validity (literal-assignment convention for `hold_reason`)

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

## `record_path` Null-Prevention Review

Validates: routing-and-materiality.md §Selective Durable Persistence + capsule-contracts.md §Contract 3 (Dialogue Feedback Capsule) (`record_path` non-null requirement)

PR checklist item: "Confirmed: no null or uninitialized state is reachable for `record_path` from any emission path. Verified by tracing all code paths from capsule assembly entry to `record_path` assignment — including all exception paths before write attempt (path construction failure, permission errors, directory creation failures, and any other pre-write exception). The path variable is assigned before any operation that could throw."

Additionally confirmed: the feedback capsule schema definition declares `record_path` as a required non-null field (schema-level enforcement), not just that no code path emits null (behavioral enforcement). These are distinct checks — the schema declaration prevents null at the type level; the code-path trace prevents null at the implementation level.

## Thread Freshness Numeric Comparison Check

Validates: routing-and-materiality.md §Thread Continuation vs Fresh Start (timestamp comparison rule)

PR checklist item: "Confirmed: thread continuation vs. fresh start comparison uses parsed numeric timestamps (millisecond precision), not string comparison. Verified by reviewing the comparison code path for `created_at` vs `thread_created_at`."

**Regression gate:** PRs touching thread-continuation comparison logic MUST confirm scenarios (7) and (8) from [verification.md §Routing and Materiality Verification](verification.md#routing-and-materiality-verification) pass. These are permanent regression tests, not one-time validation steps.

## `budget_override_pending` Initialization Check

Validates: routing-and-materiality.md §Budget Enforcement Mechanics (initialization invariant)

PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry for each `lineage_root_id` — not left to default-falsy behavior. A new skill invocation always starts with a clean override state. Verified by reviewing the initialization code path at stub entry point — initialization is per-invocation, not session-persistent."

## Budget Override Context-Compression Recovery Gate

Validates: [routing-and-materiality.md §Budget Enforcement Mechanics](routing-and-materiality.md#budget-enforcement-mechanics) (override context-compression recovery)

**[Activates when budget override code is authored]** PR checklist item: "Confirmed: stub contains a branch detecting absent prior 'continue' message after budget exhaustion and context compression. That branch emits re-confirmation text containing 'context compression' and instructs the user to say 'continue' to allow one more hop. Verified by tracing the override state evaluation code path."

## `dialogue-orchestrated-briefing` Sentinel Suppression Check

Validates: capsule-contracts.md §Sentinel Registry (internal sentinel scope)

**[Activates when dialogue stub is authored]** PR checklist item: "Confirmed: `<!-- dialogue-orchestrated-briefing -->` does not appear in any code path that writes to conversation context or user-visible output. The sentinel is internal pipeline state only. Verified by reviewing all output-writing code paths in the dialogue stub."

Retirement: when `validate_composition_contract.py` includes sentinel scope enforcement.

## `upstream_handoff` Abort Teardown Check

Validates: routing-and-materiality.md §Material-Delta Gating Step 0 case (c) + §Affected-Surface Validity post-abort behavior (flag teardown invariant)

**[Activates when dialogue abort-path code is authored]** PR checklist item: "Confirmed: all `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) are torn down after each abort path. Verified using the phase-and-abort coverage table below."

**Phase-and-abort coverage table:** Each row names the stub phase where a capability flag becomes semantically live, the reachable abort condition, the required post-abort rule, and the linked reinvocation test case.

| Flag | Semantically Live At | Abort Condition | Post-Abort Rule | Reinvocation Case |
|------|---------------------|-----------------|-----------------|-------------------|
| `decomposition_seed` | Step 0 materiality precondition | Case (c): filter not applied | Any later invocation MUST recompute from currently visible inputs; no prior flag carried forward | Post-abort reinvocation: no enriched decomposition behavior |
| `gatherer_seed` | Steps 2-3 gatherer enrichment | Case (c) or partial correction failure | Same | Post-abort reinvocation: no gatherer enrichment from prior handoff |
| `briefing_context` | Briefing assembly | Case (c) or partial correction failure | Same | Post-abort reinvocation: no upstream context injection |
| `tautology_filter_applied` | Step 0 precondition check | Case (c) or partial correction failure | Same | Post-abort reinvocation: precondition re-evaluated from scratch |

The reinvocation test (verification.md) is a **corroborating regression check** — absence of capability-flag-dependent behavior is evidence of teardown, not standalone proof. The governance gate (structural reviewer trace) is the primary enforcement layer.

**Teardown semantics:** All four capability flags are set by the NS adapter at Stage B ([pipeline-integration.md §Two-Stage Admission](pipeline-integration.md#two-stage-admission) Stage B) — they are present when Step 0 runs. Teardown means: set the flag to `false` (or remove the key) regardless of whether the pipeline reached the stage where the flag is semantically consumed. A "torn down" flag MUST evaluate as `false` in any downstream check. Teardown is not a no-op — it clears flags that were initialized at Stage B but whose pipeline stage has not yet been reached.

## Step 0 Flag Read Source Verification

Validates: routing-and-materiality.md §Material-Delta Gating Step 0 (case c/d boundary)

**[Activates when materiality evaluator code is authored]** PR checklist item: "Confirmed: materiality evaluator reads `decomposition_seed` from `upstream_handoff.decomposition_seed` (direct flag read from the capability flags set by the adapter at Stage B). The evaluator does NOT derive decomposition status from `--plan` CLI state or any other source. Verified by tracing the evaluator's data source for the case (c)/(d) branching decision."

## Consumer Durable Store Check Ordering Gate

Validates: routing-and-materiality.md §Selective Durable Persistence (check ordering invariant)

PR checklist item: "Confirmed: consumer-side durable store lookup checks fields in order (1) `record_path` nullity, (2) file existence at `record_path`, (3) `record_status` field presence, (4) `record_status` value, (5) file content integrity. Step 3 precedes any file I/O. Verified by tracing the consumer code path as a sequential short-circuit chain."

Cross-reference: routing-and-materiality.md §Check ordering defines the normative 5-step sequence. Consumer-side case (3) behavioral test (absent `record_status` with file existing at path) is the specific ordering verification test per verification.md.

## `hold_reason` Assignment and Placement Review

Validates: routing-and-materiality.md §Ambiguous Item Behavior (assignment precedence) + §Affected-Surface Validity (emission-time gate, list-membership constraint)

PR checklist requires reviewer to confirm:

1. "Confirmed: `hold_reason: routing_pending` is set for all held ambiguous items before capsule emission — verified that no held ambiguous item reaches `unresolved[]` without `hold_reason: routing_pending`, regardless of which stage (routing or capsule assembly) set it. If set at the routing stage, capsule assembly MUST NOT overwrite it. No code path sets `hold_reason` to any value other than `routing_pending` or `null`."
2. "Confirmed: if `hold_reason: routing_pending` is set at the routing stage, capsule assembly and emission-time gate MUST NOT clear, replace, or default over the existing value. If `hold_reason` is set only at capsule assembly time, no routing-stage write exists for that item. Verified by tracing all write sites for `hold_reason`."
3. "Confirmed: `hold_reason` assignments are only present in code paths that write to `unresolved[]`, not to `feedback_candidates[]`. Verified by reviewing all code paths that populate `feedback_candidates[]` — none contain `hold_reason` field assignments."

**Accepted v1 limitation:** Stage differentiation (whether `hold_reason` was set at routing time vs capsule assembly time) cannot be proven mechanically without a new observable trace field. This governance gate is the sole enforcement for provenance claims. The behavioral test in verification.md asserts the final emitted value, not assignment timing.

**Validator scope extension:** When `validate_composition_contract.py` is implemented (delivery.md item #6), add structural checks for: `hold_reason` at correct emitted path (`unresolved[]` only), never in `feedback_candidates[]`, value from allowed set `{routing_pending, null}`.

## `source_artifacts` Provenance Review

Validates: [capsule-contracts.md §Consumer Class (Contract 1)](capsule-contracts.md#consumer-class-contract-1) + [capsule-contracts.md §Contract 3 (provenance rule)](capsule-contracts.md#contract-3-dialogue-feedback-capsule)

PR checklist item: "Confirmed: when Stage A rejects a capsule (invalid schema), the dialogue feedback capsule emitted in that invocation omits `source_artifacts` entries for the rejected upstream artifact. Verified by tracing the rejection branch — `source_artifacts[]` is populated only from successfully consumed upstream artifacts, never from rejected capsules."

## Tier 3 Tautology Filter Calibration Gate

Validates: pipeline-integration.md §Three-Tier Tautology Filter (Tier 3 model calibration)

**[Activates when decomposition seeding PR is authored]** PR checklist item: "Confirmed: all 4 Tier 3 examples from pipeline-integration.md (2 valid, 2 invalid) classify correctly. PR description includes classification result for each example. Any misclassification blocks merge until Tier 3 prompt is revised."

## Partial Correction Failure Abort Gate

Validates: routing-and-materiality.md §Affected-Surface Validity (partial correction failure post-abort behavior)

**[Activates when correction pipeline code is authored]** PR checklist item: "Confirmed: when rule 5 fires (partial correction failure), capsule assembly aborts and all 7 post-abort assertions hold: (1) no feedback capsule sentinel emitted, (2) no capsule body emitted, (3) no durable file written, (4) structured warning with entry index and unexpected state values emitted, (5) no hop suggestion text in prose output, (6) no `dialogue-orchestrated-briefing` sentinel in output, (7) all `upstream_handoff` capability flags torn down. Verified by tracing the abort code path."

## Abort-Path Independent Test Fixtures Gate

Validates: [verification.md §Capsule Contract Verification](verification.md#capsule-contract-verification) (partial correction failure row — "Independent test mandate" clause)

**[Activates when dialogue stub abort-path code is authored]** PR checklist item: "Confirmed: two separate test fixtures exist — one for Step 0 case (c) abort path and one for partial correction failure abort path. No single shared fixture exercises both paths. Each fixture independently verifies all 7 post-abort assertions for its respective abort path. Verified by reviewing test file structure — two independent fixture functions/blocks, each with a complete assertion set."

## Correction Rule Sequential Ordering Gate

Validates: routing-and-materiality.md §Affected-Surface Validity (correction rule ordering)

**[Activates when correction pipeline code is authored]** PR checklist item: "Confirmed: correction rules are evaluated as a sequential if-else chain in listed order (1→2→3→4→5). An entry matching rule 1 does NOT proceed to rule 2 evaluation. Verified by structural inspection — the correction code path is a sequential short-circuit chain, not independent parallel checks. Additionally confirmed: a valid tuple (e.g., `diagnosis/true/adversarial-review`) traverses the correction pipeline without reaching rule 5's defensive fallback. Verified by tracing the valid tuple through the if-else chain — the chain exits at the valid-tuple pass-through condition before rule 5 branch."

## Emission-Time Validation Step Ordering Gate

Validates: [routing-and-materiality.md §Affected-Surface Validity](routing-and-materiality.md#affected-surface-validity) (processing order steps 2-4)

**[Activates when emission-time validation code is authored]** PR checklist item: "Confirmed: emission-time validation steps are evaluated in order: (2) `classifier_source`, (3) `materiality_source`, (4) `hold_reason`. A structured warning from step 2 appears before step 3's warning in the diagnostic log path. Verified by structural inspection — the validation code path is a sequential chain with step 2 preceding step 3, step 3 preceding step 4."

## Lineage Key Propagation Regression Gate

Validates: [lineage.md §Key Propagation](lineage.md#key-propagation) (`lineage_root_id` immutability)

**[Active for any PR touching key propagation or capsule minting logic]** PR checklist item: "Confirmed: `lineage_root_id` immutability regression test passes — multi-hop chain test asserting `lineage_root_id` string equality across all hops re-executed and passing."
