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

The co-review gate MUST also verify the NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags (key presence, not just value correctness) — absence is a gate failure requiring remediation before merge.

The co-review gate MUST also verify the NS adapter sets `decomposition_seed: true` only when `--plan` was active AND decomposition seeding actually ran — per pipeline-integration.md §Two-Stage Admission Stage B. A false `decomposition_seed` causes Step 0 case (c) abort with no recovery path. PR checklist item: "Confirmed: NS adapter's `decomposition_seed` assignment is conditional on `--plan` being active. Verified by tracing the adapter code path."

The co-review gate enforcement surface covers ALL adapter exit paths, including Stage A rejection (where `upstream_handoff` is never initialized). When Stage A rejects a capsule, the adapter exits before `upstream_handoff` is constructed — `tautology_filter_applied` key-presence cannot be checked on an object that does not exist. PR checklist item: "Confirmed: adapter exit paths are exhaustively enumerated — including schema-validation-failure paths where `upstream_handoff` is never initialized. For rejection paths: verified no capability flags leak into pipeline state."

The co-review gate MUST verify that `supersedes` is always present (not omitted) in emitted capsules, per the emitter-side MUST in lineage.md §DAG Structure. Consumer-side tolerance (treating absent `supersedes` as null) does NOT relax the emitter obligation — the consumer compatibility exception is defensive, not normative.

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

## `record_path` Null-Prevention Review

Validates: routing-and-materiality.md §Selective Durable Persistence + capsule-contracts.md §Contract 3 (Dialogue Feedback Capsule) (`record_path` non-null requirement)

PR checklist item: "Confirmed: no null or uninitialized state is reachable for `record_path` from any emission path. Verified by tracing all code paths from capsule assembly entry to `record_path` assignment — including exception paths before write attempt (path construction failure). The path variable is assigned before any operation that could throw."

## Thread Freshness Numeric Comparison Check

Validates: routing-and-materiality.md §Thread Continuation vs Fresh Start (timestamp comparison rule)

PR checklist item: "Confirmed: thread continuation vs. fresh start comparison uses parsed numeric timestamps (millisecond precision), not string comparison. Verified by reviewing the comparison code path for `created_at` vs `thread_created_at`."

## `budget_override_pending` Initialization Check

Validates: routing-and-materiality.md §Budget Enforcement Mechanics (initialization invariant)

PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry — not left to default-falsy behavior. Verified by reviewing the initialization code path at stub entry point."

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

1. "Confirmed: exactly one authoritative write point for `hold_reason` exists — the routing stage sets `hold_reason: routing_pending` for held ambiguous items. No other code path assigns a non-null `hold_reason` value."
2. "Confirmed: later stages (capsule assembly, emission-time gate) can only propagate or omit `hold_reason` — they MUST NOT clear, replace, or default over an existing `routing_pending` value."
3. "Confirmed: `hold_reason` assignments are only present in code paths that write to `unresolved[]`, not to `feedback_candidates[]`. Verified by reviewing all code paths that populate `feedback_candidates[]` — none contain `hold_reason` field assignments."

**Accepted v1 limitation:** Stage differentiation (whether `hold_reason` was set at routing time vs capsule assembly time) cannot be proven mechanically without a new observable trace field. This governance gate is the sole enforcement for provenance claims. The behavioral test in verification.md asserts the final emitted value, not assignment timing.

**Validator scope extension:** When `validate_composition_contract.py` is implemented (delivery.md item #6), add structural checks for: `hold_reason` at correct emitted path (`unresolved[]` only), never in `feedback_candidates[]`, value from allowed set `{routing_pending, null}`.
