---
module: readme
status: active
normative: false
authority: supporting
---

# T-04 T4: Scouting Position and Evidence Provenance

Modular specification for the T4 design contract — scouting mechanics,
evidence provenance, containment enforcement, and benchmark readiness.

**Source:** Compiled from the monolithic design document at revision 21
(commit `214ef168`, 2441 lines, "Defensible" verdict after 6 hostile
review rounds). The archived monolith is at
[archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md](../archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md).
A compatibility shim at the original path redirects existing references.

**Context:** T4 from the
[benchmark-first design plan](../2026-04-01-t04-benchmark-first-design-plan.md).
Related gate: G3 in
[convergence loop risk register](../../reviews/2026-04-01-t04-convergence-loop-risk-register.md).
Depends on: T2 accepted at
[T2 contract](../2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md).

**Status:** This README is supporting documentation for the canonical
normative T4 specification in this directory. The T4 spec remains under
`docs/plans/` for historical continuity and stable references; that location
is not a signal that the contract is planning scratch or otherwise
non-normative. Future T4 edits should continue to land here unless a later
tooling-backed relocation is explicitly approved.

## Authority Model

Each file carries frontmatter declaring its `authority` (from `spec.yaml`)
and optional `claims`. All normative conflicts between files resolve to
`ambiguity_finding` — there is no precedence hierarchy. Each normative
clause lives in exactly one canonical location; apparent conflict between
files is always a spec defect.

| Authority | Default Claims | Description |
|---|---|---|
| foundation | architecture_rule, decision_record | Core decisions, rationale, transcript fidelity |
| state-model | persistence_schema, interface_contract | Schemas, state machines, wire formats |
| scouting-behavior | behavior_contract | Loop mechanics, targeting, query coverage, classification |
| containment | enforcement_mechanism | Scope confinement, safety interaction |
| provenance | interface_contract, behavior_contract | Citation surface, audit chain, omission surface |
| benchmark-readiness | enforcement_mechanism | Blockers, prerequisite gates, amendment obligations |
| boundaries | implementation_plan | Non-changes, migration enumeration |
| supporting | *(none)* | Rejected alternatives, conformance matrix, crosswalk |

## Reading Order

| # | File | Authority | Description |
|---|------|-----------|-------------|
| 1 | [foundations.md](foundations.md) | foundation | Core decisions (T4-F-01–T4-F-13), rationale, transcript fidelity dependency |
| 2 | [state-model.md](state-model.md) | state-model | Occurrence registry, ClaimRef, evidence record, verification state, budgets, compression, persistence |
| 3 | [scouting-behavior.md](scouting-behavior.md) | scouting-behavior | Per-turn loop, skip/targeting, query coverage, claim classification, methodology findings |
| 4 | [containment.md](containment.md) | containment | Scope breach, direct-tool containment, scope_root derivation, safety |
| 5 | [provenance-and-audit.md](provenance-and-audit.md) | provenance | Evidence trajectory, provenance index, claim ledger, audit chain, omission surface |
| 6 | [benchmark-readiness.md](benchmark-readiness.md) | benchmark-readiness | Prerequisite gates, non-scoring classification, amendment table |
| 7 | [boundaries.md](boundaries.md) | boundaries | Non-changes, helper-era migration, declared input changes |
| 8 | [rejected-alternatives.md](rejected-alternatives.md) | supporting | Rejected alternatives 7.1–7.61 |
| 9 | [conformance-matrix.md](conformance-matrix.md) | supporting | 70-item verification matrix citing canonical requirement IDs |
| 10 | [crosswalk.md](crosswalk.md) | supporting | Monolith section/line → modular file/requirement ID mapping |

## Cross-Reference Conventions

- **Requirement IDs:** `T4-{prefix}-{seq}` (e.g., `T4-SM-01`). Stable
  across file reorganization. Each normative clause carries its ID as a
  heading anchor.
- **Cross-file links:** `[T4-CT-03](containment.md#t4-ct-03)` — ID-based,
  not section-number-based.
- **Conformance matrix:** Each item cites one or more requirement IDs.
  The matrix is non-normative; the cited requirements are authoritative.
- **Crosswalk:** Maps monolith sections and line ranges to modular
  locations. Historical handoff references resolve through this.

## Boundary Rules

Changes to one authority trigger review of dependent authorities:

| Changed | Must Review |
|---|---|
| foundation | provenance, containment, benchmark-readiness |
| state-model | scouting-behavior, provenance, benchmark-readiness |
| containment | provenance, benchmark-readiness |
| scouting-behavior | provenance, benchmark-readiness |
| provenance | benchmark-readiness |
| benchmark-readiness | provenance, containment |
