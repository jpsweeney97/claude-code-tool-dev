---
module: rejected-alternatives
status: active
normative: false
authority: supporting
---

# Rejected Alternatives

Non-normative decision history. Each entry records what was proposed, why
it was rejected, and what replaced it. Entries reference canonical
requirement IDs in the modular spec where applicable.

## Revisions 1-3

Flat evidence (7.1), per-tool-call disposition (7.2), cross-model
scout_outcomes (7.3), full tool output (7.4), evidence in pipeline
epilogue (7.5), claim_key-only join (7.6), boolean backlog (7.7),
single-path ToolCallResult (7.8), lossy summary row (7.9), scout before
control (7.10), "later wins" (7.11), inferred T3 occurrence (7.12),
internal-only records (7.13), same-turn dedup (7.14), disposition from
citation subset (7.15), recency-only binding (7.16), tool result order
(7.17), agent-written evidence (7.18), unresolved-item scouting as
primary mechanism (7.19).

## 7.20: Per-Tool Citation Caps

Rejected: Read=1 conflicts with polarity-preserving rule.
See [T4-F-04](foundations.md#t4-f-04).

## 7.21: Only Register New Claims

Rejected: revised claims need registration for referential resolution.
See [T4-SM-01](state-model.md#t4-sm-01).

## 7.22: Derive Disposition From Citations

Rejected: polarity-preserving rule and mechanical diff audit prevent
cherry-picking. See [T4-SM-05](state-model.md#t4-sm-05),
[T4-PR-11](provenance-and-audit.md#t4-pr-11).

## 7.23: Snippet Recovery Reads During Synthesis

Rejected: violates G3 single capture point. See [T4-F-07](foundations.md#t4-f-07).

## 7.24: Evidence Export Via Synthesis Epilogue

Rejected: contaminates scored synthesis. See [T4-F-08](foundations.md#t4-f-08).

## 7.25: Recency Fallback for Same-Text Collisions

Rejected: same-text same-key merger prevents orphaning.
See [T4-SM-01](state-model.md#t4-sm-01).

## 7.26: Agent-Authored candidate_matches as Provenance

Rejected: agent self-report is not provenance. Mechanical diff (raw
output minus citations) provides the authoritative omission surface.
See [T4-PR-11](provenance-and-audit.md#t4-pr-11).

## <a id="727-unresolved-item-scouting-as-secondary-target-type"></a>7.27: Unresolved-Item Scouting as Secondary Target Type

Rejected: 4 critical incompatibilities (follow-up contract, synthesis
scoring, pipeline-data accounting, evidence trajectory).
See [T4-F-09](foundations.md#t4-f-09).

## 7.28: Flat max_attempts_per_claim = 1

Rejected: too rigid. `conflicted` and `ambiguous` claims need a second
attempt — the evidence was real but inconclusive. `not_found` correctly
gets only one attempt. Graduated limit
([T4-SB-03](scouting-behavior.md#t4-sb-03)) balances coverage with
resolution.

## 7.29: Revised Claims Exempt From Merger

Rejected: the "different text by definition" assumption is wrong.
See [T4-SM-01](state-model.md#t4-sm-01) merger rule.

## 7.30: Single Definition-Query Coverage Rule

Rejected: too weak. An agent can satisfy it with one token-compliant but
low-value query. Two mandatory types cover both actual behavior and claim
negation. See [T4-SB-04](scouting-behavior.md#t4-sb-04).

## 7.31: Revised Claims Exempt From Forced-New Reclassification

Rejected: creates dual semantic state. See [T4-SM-02](state-model.md#t4-sm-02) Phase 1.5.

## 7.32: match_digest as Escalation Gate for Mechanical Diff

Rejected: reintroduces trust in non-authoritative summary surface. The
harness MUST compute the diff by default.
See [T4-PR-11](provenance-and-audit.md#t4-pr-11).

## 7.33: 2-3 Call Round Budget

Rejected: too tight for claims requiring grep-plus-read for each query
type. 2-5 call budget gives room for meaningful evidence gathering while
preventing monopolization. See [T4-SB-04](scouting-behavior.md#t4-sb-04).

## 7.34: SHOULD for Second-Attempt Query Diversity

Rejected: `SHOULD` contradicted verification item 18 (which treated
difference as required). MUST with objective criteria resolves the
contradiction. See [T4-SB-04](scouting-behavior.md#t4-sb-04).

## 7.35: "Full Helper-Era Migration Enumeration" Claim

Rejected: overstated readiness. T4 enumerates scouting-surface
replacements; T5's primary migration set is separate and complementary.
See [T4-BD-03](boundaries.md#t4-bd-03).

## 7.36: not_scoutable as Prose-Only Ambiguous

Rejected: `VerificationEntry` had no `reason` field, target selection
still retried. Wired as terminal verification status.
See [T4-SM-06](state-model.md#t4-sm-06), [T4-SB-05](scouting-behavior.md#t4-sb-05).

## 7.37: evidence_map Keyed by claim_key

Rejected: `claim_key` is not a unique synthesis-claim identifier.
Changed to `claim_id`-keyed map.
See [T4-PR-03](provenance-and-audit.md#t4-pr-03).

## 7.38: Abandoned Rounds Consume Only Claim-Local Budget

Rejected: repeated failed rounds could burn tool effort indefinitely.
Added `scout_budget_spent` counter.
See [T4-SM-07](state-model.md#t4-sm-07).

## 7.39: Containment Cited to Benchmark Tool-Class Restriction

Rejected: benchmark lines 93-94 only restrict tool classes, not scope
roots. Reground in consultation contract.
See [T4-CT-03](containment.md#t4-ct-03).

## 7.40: Blocker Without Ownership

Rejected: a blocker that names no owner is an indefinite pause point.
Assigned to T7 with specific targets.
See [T4-BR-02](benchmark-readiness.md#t4-br-02).

## 7.41: Approximate Content Matching for Narrative Claims

Rejected: replaced with claim ledger completeness rule. No approximate
matching path exists.
See [T4-PR-06](provenance-and-audit.md#t4-pr-06).

## 7.42: not_scoutable Only for New Extracted Claims

Rejected: extended to ALL claim registration paths.
See [T4-SM-06](state-model.md#t4-sm-06) lifecycle.

## 7.43: scout_budget_spent Incremented in Lifecycle Entries

Rejected: double-counting. Single increment point at step 5b.
See [T4-SM-07](state-model.md#t4-sm-07).

## 7.44: Checkpoint as Sole Scored Factual Surface

Rejected: moving scoring from full synthesis to checkpoint creates an
escape hatch. **Rev 14-15 resolution:** the claim ledger
([T4-PR-05](provenance-and-audit.md#t4-pr-05)) provides the inventory
without restricting the scored surface.

## 7.45: Multi-Ref Checkpoint Lines for Claim Compression

Rejected: one line with three refs is ambiguous. One claim ledger line =
one atomic claim. See [T4-PR-05](provenance-and-audit.md#t4-pr-05).

## 7.46: Overloading evidence_map With Classification Traces

Rejected: mixes evidence provenance with classification audit. Fixed
with explicit `type` field and two variants.
See [T4-PR-03](provenance-and-audit.md#t4-pr-03).

## 7.47: Text-Embedded ClaimRef as [ref:] Join Key

Rejected: T3 normalization does not guarantee absence of structural
characters. Fixed: `claim_id: int` as opaque, parse-safe join key.
See [T4-PR-03](provenance-and-audit.md#t4-pr-03).

## 7.48: Checkpoint Completeness as MUST Rule

Rejected: unenforceable without narrative factual-claim inventory. Claim
ledger completeness is MUST with enforcement deferred to T7.
See [T4-PR-06](provenance-and-audit.md#t4-pr-06),
[T4-BR-06](benchmark-readiness.md#t4-br-06).

## 7.49: NOT_SCOUTABLE as Checkpoint Tag

Rejected: mixes two axes (outcome vs evidence state). Evidence state
encoded as `[evidence: not_scoutable]` annotation.
See [T4-PR-05](provenance-and-audit.md#t4-pr-05).

## 7.50: Enclosing-Scope Heuristic for Full-File Read Omission

Rejected: shape-gaming exploit. Boundary determined at read time, not
citation time.
See [T4-PR-11](provenance-and-audit.md#t4-pr-11),
[T4-PR-12](provenance-and-audit.md#t4-pr-12).

## 7.51: Narrative Provenance Gap as "Bounded" Without Penalty

Rejected: visible but not penalized is not bounded. Rev 13 made it a G3
gate; rev 14 separated it from G3.
See [T4-PR-08](provenance-and-audit.md#t4-pr-08).

## 7.52: Checkpoint as Dual-Purpose Outcome Summary and Provenance Ledger

Rejected: two incompatible roles. Fixed: separate claim ledger.
See [T4-PR-05](provenance-and-audit.md#t4-pr-05).

## 7.53: Narrative Coverage Gap as G3 Blocker

Rejected: G3 concerns scouted provenance, not narrative claims.
See [T4-PR-08](provenance-and-audit.md#t4-pr-08).

## 7.54: checkpoint_coverage_rate as Independent G3 Option

Rejected: the metric depends on the same machinery as the checker. Single
mechanism: T7 inventory.
See [T4-BR-06](benchmark-readiness.md#t4-br-06).

## 7.55: Mandatory Runtime Decomposition of not_scoutable Claims

Rejected: T2/T3 pipeline boundary violation. Decomposition is audit-side
analysis.
See [T4-SB-05](scouting-behavior.md#t4-sb-05).

## 7.56: Non-Binding Methodology Findings

Rejected: a candidate could accumulate findings and still pass.
Per-run threshold gate added as condition 5.
See [T4-BR-07](benchmark-readiness.md#t4-br-07),
[T4-BR-09](benchmark-readiness.md#t4-br-09).

## 7.57: SHOULD Decomposition With Implicit MUST Semantics

Rejected: practical rule behaved like MUST while keyword said SHOULD.
Fixed: decomposition analysis is MUST, no exceptions.
See [T4-SB-05](scouting-behavior.md#t4-sb-05).

## 7.58: Comparative Methodology-Finding Metric

Rejected: baseline count would be zero or undefined. Fixed:
candidate-only per-run threshold gate.
See [T4-BR-07](benchmark-readiness.md#t4-br-07).

## 7.59: Ledger claim_id as Methodology Finding Row Key

Rejected: narrative-only claims have no ledger `claim_id`. Fixed: keyed
by `inventory_claim_id`.
See [T4-BR-09](benchmark-readiness.md#t4-br-09).

## 7.60: Methodology-Gate Breach as Invalid Run

Rejected: would allow rerunning until findings fall below threshold.
Breach fails condition 5, not run validity.
See [T4-BR-07](benchmark-readiness.md#t4-br-07).

## 7.61: Criterion-1 Exception for Decomposition

Rejected: criterion-1 failure for the whole claim does not imply no
entity-bearing subclaims exist. Decomposition check is always MUST.
See [T4-SB-05](scouting-behavior.md#t4-sb-05).
