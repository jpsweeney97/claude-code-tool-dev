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

## `record_path` Null-Prevention Review

Validates: capsule-contracts.md §Schema Constraints (`record_path` non-null requirement)

PR checklist item: "Confirmed: no null or uninitialized state is reachable for `record_path` from any emission path. Verified by tracing all code paths from capsule assembly entry to `record_path` assignment — including exception paths before write attempt (path construction failure). The path variable is assigned before any operation that could throw."

## Thread Freshness Numeric Comparison Check

Validates: routing-and-materiality.md §Thread Continuation vs Fresh Start (timestamp comparison rule)

PR checklist item: "Confirmed: thread continuation vs. fresh start comparison uses parsed numeric timestamps (millisecond precision), not string comparison. Verified by reviewing the comparison code path for `created_at` vs `thread_created_at`."

## `budget_override_pending` Initialization Check

Validates: routing-and-materiality.md §Budget Enforcement Mechanics (initialization invariant)

PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry — not left to default-falsy behavior. Verified by reviewing the initialization code path at stub entry point."
