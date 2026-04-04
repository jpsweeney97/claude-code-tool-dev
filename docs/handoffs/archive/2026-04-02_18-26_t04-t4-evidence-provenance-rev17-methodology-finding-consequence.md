---
date: 2026-04-02
time: "18:26"
created_at: "2026-04-02T18:26:55Z"
session_id: beecbbe2-50c9-4c1b-917e-59f1e610e7f8
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_17-53_t04-t4-evidence-provenance-rev16-enforcement-and-pipeline-boundary.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 28a7e67a
title: "T-04 T4 evidence provenance — rev 17, methodology finding consequence and enforcement weight"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/cross-model/agents/codex-dialogue.md
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/references/consultation-contract.md
  - packages/plugins/cross-model/scripts/event_schema.py
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
---

# Handoff: T-04 T4 evidence provenance — rev 17, methodology finding consequence and enforcement weight

## Goal

Close gate G3 (evidence provenance retention) — the last remaining hard gate before T6 (composition check) can begin. G1, G2, G4, G5 are `Accepted (design)`. G3 requires: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface. The risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:67` governs G3.

**Trigger:** Previous session completed revision 16. This session received the user's adversarial review of rev 16 and iterated through four rounds of counter-review to produce revision 17.

**Stakes:** All 5 hard gates must reach `Accepted (design)` before T6 composition check can start (`risk-register.md:79-81`). T4 is the parallel prerequisite that designs how evidence flows through the dialogue loop.

**Success criteria:** User accepts the T4 design contract. G3 moves to `Accepted (design)`.

**Pattern:** Claude proposes fixes, user provides structured counter-review with specific contract-level issues, Claude tightens proposals, repeat. This session had four counter-review rounds on the fix proposals before editing the draft.

**Next session:** User requests a thorough self-review of rev 17 using the `design-review-team` skill before sharing the user's own adversarial review.

## Session Narrative

### Rev 16 review received: enforcement weight, not architecture

Session loaded the prior handoff and immediately received the user's adversarial review of rev 16. The review found no critical architectural failures — a qualitative shift from prior review cycles. Three findings, all about enforcement weight and contract integration:

1. **[P1] Methodology findings non-binding** (`t4.md:813-825`) — under-reading, shape-inadequacy, and misclassification defined as methodology findings in `adjudication.json` but explicitly excluded from claim labels. The benchmark pass rule (`benchmark.md:169-181`) only consumes claim labels, convergence, and safety. Findings are visible but non-load-bearing.

2. **[P1] Readiness gate omits new T7 dependencies** (`t4.md:1495-1513`) — the benchmark-execution prerequisite blocks on T7 narrative inventory/checker but not on the two new T7 output-schema dependencies rev 16 itself introduced (methodology-finding format in `adjudication.json`, mode-mismatch entries in `runs.json`).

3. **[P2] Decomposition SHOULD behaves like MUST** (`t4.md:970-1009`) — normative text says SHOULD but trace section treats `decomposition_attempted: false` as a finding. Practical rule is MUST; formal keyword is SHOULD.

The user's verdict: major revision, but the core scouting architecture holds. Required changes: (1) give methodology findings benchmark consequence, (2) extend readiness gate, (3) fix SHOULD/MUST inconsistency, (4) define narrative-ledger violation output format.

### Proposal round 1: three RCs

Proposed three fixes for counter-review:

- **RC1:** Methodology findings get `methodology_finding_count ≤ baseline` pass-rule condition (same comparison approach as `false_claim_count`). Narrative-ledger violations typed as methodology finding subtype. Stale "creates pressure" language replaced with honest T7-dependency framing.

- **RC2:** Extend benchmark-execution prerequisite to include all T7 schema dependencies (inventory/checker + methodology-finding format + mode-mismatch schema). Add `methodology_finding_count` metric as fourth prerequisite.

- **RC3:** Decomposition SHOULD → MUST with `failed_criterion == 1` exception (no entity = no decomposition needed).

### Counter-review round 1: three issues found

User counter-reviewed and found:

1. **[P1] RC1 counting unit undefined** — "one claim could plausibly yield multiple findings, and one narrative paragraph could plausibly hide multiple ledger misses." Needed explicit `finding_kind` taxonomy, counting unit per `(run_id, claim_id, finding_kind)`, and detection-method field.

2. **[P1] RC3 criterion-1 exception too broad** — "Criterion 1 only says the original claim lacks an identified entity; decomposition is precisely the step that asks whether subclaims could have identifiable entities." The most abstract claims would get the least decomposition pressure.

3. **[P2] RC2 blocks calibration runs** — "benchmark runs MUST NOT proceed" would also block T4's required corpus calibration dry runs (`t4.md:1042`), creating a circular dependency.

### Proposal round 2: tightened RCs

- **RC1 (v2):** Added five finding kinds (`under_reading`, `shape_inadequacy`, `misclassification`, `decomposition_skipped`, `narrative_ledger_violation`), counting unit per `(run_id, claim_id, finding_kind)`, `detection: judgment | mechanical` field, narrative-ledger violations as methodology finding subtype.

- **RC2 (v2):** Changed trigger from "benchmark runs" to "scored benchmark runs and pass/fail comparisons." Non-scoring calibration dry runs explicitly permitted.

- **RC3 (v2):** Removed criterion-1 exception entirely. Decomposition check is always MUST. Valid "nothing to decompose" path: `decomposition_attempted: true, subclaims_considered: [], residual_reason` populated. `decomposition_attempted: false` is always a `decomposition_skipped` finding.

RC2 and RC3 accepted. RC1 needed further work.

### Counter-review round 2: fundamental asymmetry in RC1

User found two P1 issues in RC1 v2:

1. **Comparative metric unsound** — the benchmark compares a baseline system against a candidate system (`benchmark.md:49`). None of the five finding kinds are symmetric: the baseline doesn't produce scouting traces, `ClassificationTrace`, or a claim ledger. `candidate ≤ baseline` comparison is structurally unsound — baseline count would be zero or undefined. Referenced `benchmark.md:49`, `benchmark.md:118`, `benchmark.md:171`.

2. **Row key breaks on its target** — a `narrative_ledger_violation` identifies a claim present in synthesis but absent from ledger. By definition, it has no ledger `claim_id`. The schema breaks on exactly the violation it's meant to count. Referenced `benchmark.md:123`.

Also a P2: adjudication authority section in benchmark only describes scoring the final synthesis — if methodology findings are load-bearing and derive from process artifacts (query traces, `ClassificationTrace`), the benchmark must expand scope.

### Proposal round 3: RC1 v3

Complete rework:

- **Candidate-only threshold gate** (not comparative metric) — the baseline doesn't produce the artifact surfaces, so comparison is structurally impossible.
- **`inventory_claim_id` as row key** (not ledger `claim_id`) — the T7 adjudicator's claim inventory is the only identifier that exists for ALL factual claims including narrative-only ones.
- **Adjudication scope amendment** — new §6.2 dependency requiring benchmark to expand adjudicator authority to include candidate process artifacts.

### Counter-review round 3: two contract clarifications

User found:

1. **[P1] Threshold not pinned** — benchmark contract at `benchmark.md:202` freezes the contract surface per version. A `methodology_finding_threshold` as a runtime configuration parameter could be tuned after seeing results. Must be part of the versioned contract, recorded in `manifest.json`.

2. **[P2] Breach semantics undefined** — benchmark reserves invalid runs for run-condition violations (`benchmark.md:98`). If threshold breach is treated as invalid run, the operator can rerun until findings fall below threshold. Must explicitly define: threshold breach is a valid scored run that fails condition 5.

### Final tightening

Added both clarifications. Then user's final counter-review caught one absolute sentence: "MUST NOT be rerun" conflicts with other legitimate rerun paths. Softened to: "methodology-gate breach alone is not grounds for invalidation or rerun."

All three RCs accepted. Edited the draft. Rev 16 (2118 lines) → Rev 17 (2253 lines, +135 lines).

## Decisions

### Candidate-only threshold gate for methodology findings (rev 17, four counter-review rounds)

**Choice:** Methodology findings use a candidate-only per-run threshold gate (pass-rule condition 5) rather than a comparative metric. The `methodology_finding_threshold` is a normative value pinned in the versioned benchmark contract, recorded in `manifest.json`. T7 defines the initial threshold value.

**Driver:** User's rev 17 counter-review round 2: "The benchmark compares the cross-model baseline against the codex-collaboration candidate. None of the five finding kinds are symmetric — the baseline system produces no scouting traces, `ClassificationTrace`, or claim ledger." The `candidate ≤ baseline` comparison was structurally unsound for all five kinds — the baseline count would be zero or undefined. Referenced `benchmark.md:49`, `benchmark.md:118`, `benchmark.md:171`.

**Rejected alternatives:**

(a) Non-binding methodology findings (rev 16) — findings recorded in `adjudication.json` but excluded from pass/fail. Candidate accumulates findings and still passes, making the audit surface non-load-bearing. Rejected for lack of enforcement weight.

(b) Comparative `methodology_finding_count ≤ baseline` (rev 17 proposal round 1) — symmetric with `false_claim_count` comparison. Rejected because none of the five finding kinds are symmetric — the baseline doesn't produce the artifact surfaces.

(c) Ledger `claim_id` as finding row key (rev 17 proposal round 2) — `narrative_ledger_violation` findings by definition identify claims absent from the ledger, which have no ledger `claim_id`. Schema breaks on exactly the violation it counts. Rejected.

(d) Runtime-configurable threshold (rev 17 proposal round 3) — threshold as a benchmark configuration parameter set by T7. But benchmark contract freezes the contract surface per version (`benchmark.md:202`). Operator could tighten or loosen after seeing results. Rejected for reproducibility.

(e) Threshold breach as invalid run (implicit in early discussions) — treating methodology-gate failures as invalid runs would allow rerunning until findings fall below threshold, defeating the gate. Invalid runs are reserved for run-condition violations (`benchmark.md:98`). Rejected.

**Implication:** Five finding kinds defined: `under_reading` (judgment), `shape_inadequacy` (judgment), `misclassification` (judgment), `decomposition_skipped` (mechanical), `narrative_ledger_violation` (mechanical). Finding rows keyed by `inventory_claim_id` from T7 adjudicator claim inventory, with optional `ledger_claim_id` cross-reference. Detection field distinguishes `judgment` from `mechanical`. The benchmark contract must expand adjudicator authority to include candidate process artifacts alongside final synthesis.

**Trade-offs:** T7 now has a larger amendment surface — finding format, threshold, adjudication scope, and mode-mismatch schema. Threshold value is T7's responsibility — T4 cannot know the appropriate threshold without corpus data. Before T7 delivers, methodology findings exist as structured audit data without pass/fail consequences.

**Confidence:** High (E2) — the asymmetry is mechanically demonstrated by the benchmark's system comparison structure (`benchmark.md:49`) and the absence of baseline-side process artifacts.

**Reversibility:** High — the threshold gate adds a pass-rule condition without changing existing conditions. Removing it later requires only a contract version increment.

**Change trigger:** If the benchmark evolves to score both systems' process artifacts symmetrically, the comparative metric approach would become viable again.

### Decomposition analysis MUST with trace-based exception (rev 17)

**Choice:** Decomposition analysis is MUST, no criterion-based exceptions. `decomposition_attempted: false` is always a `decomposition_skipped` methodology finding. The valid "nothing to decompose" path is `decomposition_attempted: true, subclaims_considered: [], residual_reason` populated — the agent must perform the check, not skip it.

**Driver:** User's rev 16 review finding [P2]: "the agent SHOULD consider decomposition, but the trace section still says 'no decomposition attempt' is itself a finding. No clear cases where skipping is acceptable." User's counter-review of rev 17 RC3 initial proposal: "Criterion 1 only says the original claim lacks an identified entity; decomposition is precisely the step that asks whether subclaims could have identifiable entities. Exempting criterion-1 failures gives the most abstract claims the least decomposition pressure, which is backward."

**Rejected alternatives:**

(a) SHOULD with implicit MUST semantics (rev 16) — normative keyword said SHOULD but trace treated skipping as a finding. Two reviewers could diverge on whether skipping was acceptable discretion or a defect.

(b) MUST with criterion-1 exception (rev 17 proposal round 1) — exempted decomposition when `failed_criterion == 1` (no entity). But whole-claim criterion-1 failure doesn't imply no entity-bearing subclaims exist. The most abstract claims (all criterion-1 failures) would get no decomposition pressure.

**Implication:** Every `not_scoutable` classification must include a decomposition trace. The overhead is bounded — the check may conclude quickly with `subclaims_considered: []`. The adjudicator still evaluates whether the agent's decomposition was adequate.

**Trade-offs:** Additional token cost for decomposition trace on every `not_scoutable` claim. Accepted because the alternative (over-classification escape hatch) is worse.

**Confidence:** High (E2) — the criterion-1 loophole is mechanically demonstrated: a claim like "the auth system delegates to the cache layer" fails criterion-1 for the whole claim but has decomposable subclaims with identifiable entities.

**Reversibility:** High — narrowing MUST back to SHOULD is a single-keyword change.

**Change trigger:** If agents systematically produce trivial decomposition traces (all empty) under token pressure, consider whether the MUST is producing useful data or just ceremony.

### Readiness gate scoped to scored runs (rev 17)

**Choice:** Benchmark-execution prerequisite extended to all four T7 dependencies. Scoped to scored runs — calibration dry runs permitted but MUST NOT be used for pass/fail comparisons.

**Driver:** User's rev 16 review finding [P1]: readiness gate only blocked on narrative inventory/checker, not on the two new T7 schema dependencies (methodology-finding format, mode-mismatch entries). User's counter-review: "MUST NOT proceed" would also block T4's corpus calibration requirement (`t4.md:1042`), creating a circular dependency.

**Rejected:** (a) Gate without schema dependencies (rev 16) — benchmark "ready" while `adjudication.json` and `runs.json` lack required structures. (b) Gate blocking all runs including calibration (initial rev 17 RC2) — creates circular dependency with corpus calibration requirement.

**Implication:** Four T7 dependencies gate scored runs: (1) narrative inventory/checker, (2) methodology-finding format in `adjudication.json`, (3) mode-mismatch schema in `runs.json`, (4) `methodology_finding_threshold` in benchmark contract. The `methodology_finding_threshold` is itself versioned per `benchmark.md:202` and recorded in `manifest.json`.

**Trade-offs:** Longer runway to benchmark-ready — T7 now must deliver all four items, not just the inventory. Accepted because producing artifacts with undefined shapes is worse than waiting.

**Confidence:** High (E2) — the readiness gap is self-evident from reading the prerequisite against the amendment table in the same section.

**Reversibility:** Medium — removing a prerequisite item weakens the gate but doesn't create backward-compatibility issues.

**Change trigger:** None anticipated — prerequisite completeness is unconditionally correct.

### Threshold breach is a valid scored run (rev 17 clarification)

**Choice:** A methodology-gate breach alone is not grounds for invalidation or rerun. The run is valid and scored; the breach fails pass-rule condition 5.

**Driver:** User's counter-review round 3: invalid runs are reserved for run-condition violations (`benchmark.md:98`). User's final counter-review: "MUST NOT be rerun" too absolute — a run may ALSO have an independent invalid-run condition.

**Rejected:** (a) Threshold breach as invalid run (implicit) — allows gaming by rerunning until findings fall below threshold. (b) "MUST NOT be rerun" absolute (rev 17 proposal round 4) — conflicts with other legitimate rerun paths.

**Implication:** Pass-rule condition 5 is a quality gate. A run can fail condition 5 and pass conditions 1-4, or vice versa. All conditions must pass for the benchmark to pass.

**Trade-offs:** None — this corrects a conceptual error, not a preference.

**Confidence:** High (E2) — the distinction between invalid-run and failed-run is established by `benchmark.md:98`.

**Reversibility:** N/A — corrects a defect in the proposal language.

**Change trigger:** None.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — T4 design contract

**Status:** Untracked (not committed). 2253 lines. Revision 17.

**Purpose:** Design contract for scouting position and evidence provenance in the T-04 benchmark-first local dialogue loop. Governs gate G3.

**Key structural changes in rev 17:**

*Methodology finding consequence (RC1):*
- Five finding kinds defined: `under_reading` (judgment), `shape_inadequacy` (judgment), `misclassification` (judgment), `decomposition_skipped` (mechanical), `narrative_ledger_violation` (mechanical)
- Finding row schema: `(run_id, inventory_claim_id, finding_kind, detection, ledger_claim_id?, detail)`
- Row keyed by T7 `inventory_claim_id`, not ledger `claim_id`
- Candidate-only per-run threshold gate (pass-rule condition 5)
- `methodology_finding_threshold` pinned in versioned benchmark contract, recorded in `manifest.json`
- Threshold breach = valid scored run failing condition 5, not an invalid run
- Adjudication scope amendment: benchmark must expand to candidate process artifacts
- All stale "creates pressure" / "for system comparison" language replaced with honest T7-dependency framing
- Narrative-ledger violations typed as `narrative_ledger_violation` methodology finding
- §6.2 benchmark-contract amendment table: 2 → 4 rows (finding format, finding consequence, adjudication scope, mode-mismatch)

*Readiness gate extension (RC2):*
- Prerequisite extended to 4 T7 dependencies (narrative inventory/checker + methodology-finding format + mode-mismatch schema + threshold)
- Scoped to scored runs — calibration dry runs permitted but MUST NOT be used for pass/fail
- §6.2 prerequisite now numbered list with rationale per item

*Decomposition MUST (RC3):*
- SHOULD → MUST, no criterion-based exceptions
- `decomposition_attempted: false` always a `decomposition_skipped` finding
- Valid "nothing to decompose": `decomposition_attempted: true, subclaims_considered: [], residual_reason` populated
- Trace semantics updated throughout §4.7

*Rejected alternatives:*
- 7.56: Non-binding methodology findings (rev 16)
- 7.57: SHOULD decomposition with implicit MUST semantics (rev 16)
- 7.58: Comparative methodology-finding metric (rev 17 proposal)
- 7.59: Ledger `claim_id` as methodology finding row key (rev 17 proposal)
- 7.60: Methodology-gate breach as invalid run (rev 17 clarification)
- 7.61: Criterion-1 exception for decomposition (rev 17 proposal)

*Verification checklist:*
- Item 58: decomposition MUST, no exceptions
- Item 68: five finding kinds, threshold gate, valid/scored semantics
- Item 70: all 4 T7 deps, scored runs only, calibration carve-out

**Growth trajectory:** 1492 (rev 11) → 1762 (rev 12) → 1881 (rev 13) → 1916 (rev 14) → 2058 (rev 15) → 2118 (rev 16) → 2253 (rev 17). Rev 17 growth is split between enforcement machinery (~50 lines in §4.4/§4.7/§5.2/§5.3/§6.2) and rejected-alternatives history (~66 lines for 7.56-7.61).

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Not committed.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop (unchanged from rev 14)

| Layer | Step | Evidence interaction |
|-------|------|---------------------|
| 1 | Extract semantic data | Claims extracted from Codex response |
| 2a | Phase 1: status changes | Concessions remove from verification_state; reinforcements resolve referents. Claims sorted by `(claim_key, status)` ascending |
| 2b | Phase 1.5: reclassification | Dead-referent claims (`reinforced` AND `revised`) reclassified to `new`. Not-scoutable classification applied |
| 2c | Phase 2: registrations | Claims sorted by `(claim_key, status)` ascending. `claim_id` allocated at new entry creation. Scoutable → `unverified`. Not scoutable → `not_scoutable` (terminal, ClassificationTrace stored). **Decomposition check is MUST before `not_scoutable` classification** |
| 3 | Compute counters | T2 counter computation (reclassified claims visible here) |
| 4 | Control decision | T1 ControlDecision — conclude/continue/scope_breach |
| 5a | Target selection | Priority: unverified(0) > conflicted(<2) > ambiguous(<2) > skip (terminal states incl. `not_scoutable`) |
| 5b | Tool execution | `scout_budget_spent += 1` here. 2-5 calls: definition + falsification mandatory. `read_anchor` recorded per Read. `expected_contradiction_target` recorded per falsification query. Post-containment capture |
| 5c | Assessment | Disposition from full post-containment output; citation selection with polarity preservation |
| 5d | Record creation | EvidenceRecord created, verification state updated, `scout_attempts += 1`, provenance index updated (record_indices appended) |
| 5e | Atomic commit | Evidence block re-emitted (captured in transcript) |
| 6 | Follow-up composition | Uses evidence record (entity, disposition, citations) |
| 7 | Send follow-up | Codex receives evidence-grounded question |

### Key contract surfaces and T4 interactions (updated for rev 17)

| Surface | Location | T4 interaction |
|---------|----------|---------------|
| Follow-up evidence shape | `codex-dialogue.md:421-429` | Requires snippet + provenance + disposition + question |
| Pipeline-data scout_count | `dialogue-synthesis-format.md:150` | Maps to `evidence_count`. NOT `scout_budget_spent` |
| Pipeline-data claim_provenance_index | §5.2 | Dense JSON array, `claim_id`-keyed. T7 consumer |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | Keys off `turn_history.scout_outcomes`. Record index included per entry |
| Claim trajectory | `dialogue-synthesis-format.md:16` | Needs `not_scoutable` in vocabulary (§6.2 blocker) |
| Claim ledger | §5.2 | `## Claim Ledger` section with `FACT:` lines, `[ref: N]`, `[evidence:]` annotations |
| Synthesis checkpoint | `dialogue-synthesis-format.md:126-134` | Outcome-based (RESOLVED/UNRESOLVED/EMERGED). Unchanged from synthesis-format contract |
| T2 counter computation | `t2:152-161` | `new_claims = count(status == "new")`. **Only counts `claim_source == "extracted"`** — decomposed subclaims MUST NOT be registered |
| T3 registry construction | `t3:143-148` | `prior_registry` filters on `claim_source == "extracted"` — decomposed subclaims would be invisible |
| Benchmark scoring | `benchmark.md:118-119` | Scores final synthesis (full, not just ledger/checkpoint) |
| Benchmark claim categories | `benchmark.md:123-128` | Repository state, implementation behavior, contract or spec requirements, current code relationships. T4 narrative-to-ledger MUST mirrors this list exactly |
| Benchmark metrics | `benchmark.md:157` | `supported_claim_rate`, `false_claim_count`, citations, safety. **New:** `methodology_finding_count` (T7 dependency) |
| Benchmark pass rule | `benchmark.md:169-181` | 4 conditions. **New condition 5:** per-run `methodology_finding_threshold` gate (T7 dependency) |
| Benchmark artifacts | `benchmark.md:101-114` | `manifest.json` (**new:** records threshold), `runs.json`, `adjudication.json` (**new:** methodology findings), `summary.md` |
| Scope envelope | `consultation-contract.md:127-131` | Immutable `allowed_roots` set at delegation time. Authority for containment |
| G3 invariant | `risk-register.md:35` | "accepted scout results retained as structured provenance" — satisfied by Tier 1 chain |

### Methodology finding schema (rev 17 — new)

```text
MethodologyFinding {
  run_id: str
  inventory_claim_id: int        # from T7 adjudicator claim inventory
  finding_kind: enum             # 5 values per taxonomy
  detection: "judgment" | "mechanical"
  ledger_claim_id: int | null    # cross-ref, null for narrative_ledger_violation
  detail: str
}
```

| `finding_kind` | Detection | Source | T4 section |
|----------------|-----------|--------|------------|
| `under_reading` | judgment | Adjudicator evaluates read scope vs. claim shape | §5.3 |
| `shape_inadequacy` | judgment | Adjudicator evaluates query set vs. claim structure | §4.4 |
| `misclassification` | judgment | Adjudicator reviews `not_scoutable` classification | §4.7 |
| `decomposition_skipped` | mechanical | Trace inspection: `decomposition_attempted == false` | §4.7 |
| `narrative_ledger_violation` | mechanical | Harness: claim in synthesis, no ledger entry | §5.2 |

### T2/T3 pipeline boundary (unchanged — critical for decomposition decision)

| Contract | Field | Constraint | T4 implication |
|----------|-------|-----------|----------------|
| T2 | `claim_source` | `"extracted"` or `"minimum_fallback"` (`t2.md:101`) | No third source defined. Decomposed subclaims have no entry path |
| T2 | Counter computation | Filters `claim_source == "extracted"` (`t2.md:153-156`) | Decomposed subclaims would be invisible to counters |
| T3 | `prior_registry` | Filters `claim_source == "extracted"` (`t3.md:143-148`) | Decomposed subclaims would not appear in continuity registry |

### Two provenance tiers (unchanged)

| Tier | Claims | Join chain | Guarantee |
|------|--------|-----------|-----------|
| 1 (scouted) | Claims that went through scouting | `claim_id` → `record_indices` → evidence blocks → tool output | Full mechanical chain (given transcript fidelity §3.9) |
| 2 (not_scoutable) | Claims classified not_scoutable | `claim_id` → `ClassificationTrace` → adjudicator audit | Classification provenance only. No evidence chain |
| None | Narrative-only claims | No join | Synthesis-contract violation (§5.2). `narrative_ledger_violation` methodology finding. Scored runs blocked until T7 enforcement |

### Extended ClassificationTrace fields (rev 15-17)

```text
ClassificationTrace {
  claim_id: int
  candidate_entity: str | null
  failed_criterion: 1 | 2 | 3
  decomposition_attempted: bool     # MUST be true (rev 17)
  subclaims_considered: list[str] | null
  residual_reason: str | null
}
```

Rev 17 change: `decomposition_attempted` is now MUST — `false` is always a `decomposition_skipped` methodology finding. No criterion-based exceptions.

### External blockers enumerated (§6.2, updated for rev 17)

| Category | Owner | Count | Key items |
|----------|-------|-------|-----------|
| T5 migration set | T5 | 5 | Mode enum, synthesis format, dialogue skill, tests |
| Transcript fidelity | T7 | 4 | Normative clause, parseable format, transcript parser, diff engine |
| Allowed-scope safety | T7 | 2 | Secret handling policy, redaction/provenance interaction |
| `claim_provenance_index` consumer | T7 | 4 | Epilogue schema, parser, schema validation, claim ledger [ref:] parser |
| Synthesis-format updates | T7 | 4 | Claim ledger section, `not_scoutable` in claim/evidence trajectory |
| Narrative-claim enforcement | T7 | 3 | Inventory tool, ledger completeness checker, coverage metric |
| **Benchmark-contract amendments** | **T7** | **4** | **Methodology finding format, methodology finding consequence (threshold + pass rule), adjudication scope expansion, mode-mismatch artifact** |

Benchmark-contract amendments grew from 2 (rev 16) to 4 (rev 17).

## Context

### Mental Model

This is a **contract convergence problem in the enforcement-weight phase**, past structural separation (rev 14) and enforcement-consistency (rev 16). Rev 17's central insight: **enforcement weight at the benchmark boundary requires symmetry analysis** — consequences that reference comparative metrics must verify both systems produce the relevant artifacts.

**Convergence trajectory across three sessions:**
- Rev 11: 4 criticals (semantic gaps — capability assumptions without specs)
- Rev 12: 2 criticals (new surface contract problems)
- Rev 13: 2 criticals (closure story failures, structural mismatches)
- Rev 14: 4 criticals (internal consistency, enforcement completeness)
- Rev 15: 1 critical, 2 high, 1 medium (pipeline boundary, enforcement inconsistency, hygiene)
- Rev 16: 0 criticals, 2 high, 1 medium (enforcement weight, readiness gap, SHOULD/MUST)
- **Rev 17: awaiting review** — expected remaining findings are about specific enforcement details, not architecture or enforcement mechanism design

Criticals have progressed: design architecture → structural separation → enforcement consistency → enforcement weight → (predicted) enforcement details. Each class is strictly less severe than the previous.

**Key structural insights gained this session:**

1. **Candidate-only metrics are fundamentally different from comparative metrics.** When two systems don't share artifact surfaces, comparison is structurally unsound. The right enforcement shape is a threshold gate, not a baseline comparison.

2. **Row keys must survive their own use case.** A key (`claim_id`) that doesn't exist for one finding kind (`narrative_ledger_violation`) breaks the schema on its target violation. The key must come from the consuming surface (T7 adjudicator inventory), not the producing surface (T4 claim ledger).

3. **Contract versioning pins thresholds.** A tunable threshold is a reproducibility hole. If the contract surface is frozen per version (`benchmark.md:202`), enforcement parameters must be part of the frozen surface.

4. **Valid-run vs. invalid-run is a semantic boundary.** Quality failures (methodology-gate breach) and procedural failures (run-condition violations) are different categories. Conflating them allows gaming (rerun until quality improves).

### Project State

T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). Critical path: T2→T3→T6→T7→T8. T4 is a parallel prerequisite for T6.

Gate status:
| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 17 under review)** | **T4: scouting position and evidence provenance** |

## Learnings

### Comparative metrics require symmetric artifact surfaces

**Mechanism:** The benchmark compares a baseline system against a candidate system. A comparative metric (`candidate ≤ baseline`) only works when both systems produce the measured artifact. If only the candidate produces the artifact (because the baseline system lacks the infrastructure), the baseline count is zero or undefined, making the comparison meaningless.

**Evidence:** Methodology findings depend on candidate-side scouting traces, `ClassificationTrace`, and claim ledger. The baseline system (`benchmark.md:49`) produces none of these. All five finding kinds fail the symmetry test.

**Implication:** When designing enforcement for candidate-only quality measures, use absolute thresholds rather than comparative metrics. The threshold must be part of the versioned contract surface to prevent post-hoc tuning.

**Watch for:** Any future metric that references baseline comparison but depends on artifacts only one system produces.

### Schema keys must survive their own use case

**Mechanism:** A finding row keyed by `claim_id` from the T4 claim ledger breaks when the finding type is "claim absent from ledger" — by definition, that claim has no ledger `claim_id`. The key must come from the consuming system (T7 adjudicator claim inventory), not the producing system (T4 claim ledger).

**Evidence:** `narrative_ledger_violation` identifies a factual claim present in synthesis but absent from ledger. No ledger entry → no `claim_id` → row key is undefined.

**Implication:** When defining a finding/violation schema, ensure the key exists for ALL possible finding instances, including the failure case the finding is meant to detect.

**Watch for:** Any schema where the key references a surface that the violation implies is absent.

### Enforcement parameters must be pinned in versioned contracts

**Mechanism:** The benchmark contract at `benchmark.md:202` freezes the contract surface per version. An enforcement threshold that lives outside the frozen surface is a tunable knob — it can be adjusted after seeing results, undermining reproducibility.

**Evidence:** `methodology_finding_threshold` initially proposed as a runtime configuration parameter. The benchmark artifact set (`benchmark.md:106`) doesn't record configuration parameters. Result: operator could tighten or loosen the gate post-hoc.

**Implication:** Any load-bearing threshold or configuration value must be part of the versioned contract and recorded in the per-run manifest.

**Watch for:** Enforcement parameters described as "configurable" that actually need to be frozen.

### Valid-run vs. invalid-run is a semantic boundary, not an implementation detail

**Mechanism:** Invalid runs are reserved for procedural failures (run-condition violations per `benchmark.md:98`) and may be rerun. Quality failures (methodology-gate breach) must count as valid scored runs that fail a pass condition — otherwise the operator can rerun until findings fall below threshold.

**Evidence:** Early proposal language said "MUST NOT be rerun" which conflicted with legitimate independent rerun triggers. Fixed to "alone is not grounds for invalidation or rerun."

**Implication:** When defining new pass-rule conditions, explicitly specify whether breach invalidates the run or fails a condition on a valid run. The default should be "valid scored run that fails condition N" unless there's a procedural reason for invalidation.

**Watch for:** Any new enforcement mechanism that doesn't clearly state whether failure = invalid run or failure = scored failing run.

### Counter-review depth correlates with contract surface precision

**Mechanism:** This session required four counter-review rounds to converge RC1 (methodology finding consequence). Each round found a different class of under-specification: counting unit → asymmetry → key identity → versioning → breach semantics. The proposals were directionally correct from round 1 but lacked the contract-level precision needed for mechanical implementation.

**Evidence:** RC2 (readiness gate) converged in one round (well-scoped, straightforward extension). RC3 (decomposition MUST) converged in one round after the criterion-1 exception was rejected. RC1 required four rounds because it crossed the T4/benchmark contract boundary, introducing new artifact surfaces, metrics, and pass-rule conditions.

**Implication:** Proposals that cross contract boundaries need more review rounds. Budget for it — especially when defining new metrics, keys, and enforcement mechanisms that must survive their own use cases.

**Watch for:** The temptation to ship cross-contract proposals after a single counter-review round.

## Next Steps

### 1. Run design-review-team skill for thorough self-review of rev 17

**Dependencies:** None — draft is ready.

**What to read first:** The current T4 design contract at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (2253 lines, revision 17).

**Approach:** User explicitly requested: "Next session we should run a thorough self-review with the design-review-team skill." This would deploy 6 specialized reviewers (Structural+Cognitive, Behavioral, Data, Reliability+Operational, Change, Trust & Safety) to analyze the design through category-specific lenses.

**Key sections to verify in self-review:**
- §4.4: Methodology finding `finding_kind` and `detection` fields in shape-inadequacy language
- §4.7: Decomposition MUST (no exceptions), trace semantics, adjudicator audit finding kinds
- §5.2: Narrative-ledger violation as `narrative_ledger_violation` methodology finding, `inventory_claim_id` key
- §5.3: Under-reading finding with `finding_kind`, `detection`, honest enforcement language
- §6.2: Comprehensive readiness gate (4 items), scored/calibration distinction, 4-row amendment table
- §7.56-7.61: Six rejected alternatives documenting the iteration path
- §8 items 58, 68, 70: Updated verification checklist items

**Expected:** Self-review may find internal consistency issues in the new rev 17 content, especially around the methodology finding schema being referenced consistently across §4.4, §4.7, §5.2, §5.3, and §6.2.

### 2. Await user's adversarial review of revision 17

**Dependencies:** Design-review-team self-review (step 1) — user wants self-review first.

**Expected:** User stated reviews would continue. If Accept → promote G3. If Reject → revision 18.

**Approach:** The convergence trajectory suggests rev 17 should be approaching acceptance. Rev 16's findings were enforcement-weight (not architecture). Rev 17 addresses enforcement weight with concrete mechanisms. Remaining findings (if any) should be about enforcement details, not design.

### 3. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 4. Consider committing the T4 design contract

**Note:** The T4 file is currently untracked on branch `docs/t04-t4-scouting-and-evidence-provenance`. 2253 lines, revision 17. Consider committing after acceptance.

### 5. Post-acceptance: modular split with /superspec:spec-writer

**Note:** Document has grown from 1492 (rev 11) to 2253 (rev 17), a 51% increase across three sessions. Post-acceptance, use `/superspec:spec-writer` to create a modular structure.

## In Progress

**In Progress:** T4 design contract revision 17, awaiting self-review and then adversarial review.

- **Approach:** Iterative adversarial review — Claude drafts, user reviews with structured findings, Claude revises. Seven review cycles across three sessions (rev 11→12→13→14 in first session, rev 14→15→16 in second session, rev 16→17 in this session).
- **State:** Draft complete. 2253 lines. Not committed.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) has been stable since rev 6/7. The identity model reached consistency in rev 9. The state model wiring reached consistency in rev 12. The structural separation (claim ledger vs checkpoint, G3 vs narrative coverage) reached consistency in rev 14. The enforcement and boundary story reached consistency in rev 16. The enforcement weight and contract integration reached consistency in rev 17.
- **Not working / uncertain:** Whether the per-run threshold gate is the right enforcement shape vs. aggregate enforcement. Whether the `inventory_claim_id` concept translates cleanly to T7 implementation. Whether the adjudication scope expansion is tractable for the benchmark adjudicator. Whether the 2253-line document is still reviewable as a single file.
- **Open question:** Will the design-review-team self-review surface issues that the iterative counter-review missed?
- **Next action:** Run `design-review-team` skill on the T4 design contract.

## Open Questions

1. **Is the per-run threshold the right enforcement shape?** An aggregate threshold (across runs) would smooth outliers but hide systematic issues in specific task types. Per-run catches individual bad runs but may be too strict for complex tasks with many claims. The threshold value is T7's responsibility — T4 defines the mechanism.

2. **Will `inventory_claim_id` translate cleanly to T7?** The concept assumes T7's adjudicator claim inventory assigns a stable identifier to each factual claim. If the inventory uses a different identification scheme, the finding schema needs updating.

3. **Is the adjudication scope expansion tractable?** The benchmark adjudicator currently "scores the final synthesis" (`benchmark.md:118`). Expanding to candidate process artifacts (query traces, `ClassificationTrace`, claim ledger) significantly increases adjudicator burden. May need tooling support.

4. **Should the T4 contract be committed before acceptance?** Currently untracked. 2253 lines. Committing preserves revision history but may invite premature review.

5. **Document size.** 2253 lines and growing (+761 from rev 11's 1492, +51% across three sessions). After acceptance, modular split would help. The `superspec:spec-writer` skill is the intended tool.

## Risks

### Rev 17 may have internal consistency issues in methodology finding references

Five sections reference methodology findings (§4.4, §4.7, §5.2, §5.3, §6.2). Each section was edited independently. The finding-kind names, detection fields, and enforcement language may have subtle inconsistencies across sections — e.g., whether all five sections reference the same `finding_kind` enum values, whether the `inventory_claim_id` key is mentioned consistently.

**Mitigation:** The design-review-team self-review (next step 1) should catch cross-reference inconsistencies. Additionally, the user's adversarial review has consistently found this class of issue.

### T7 dependency load continues to grow

§6.2 now has ~26 external blockers plus 4 benchmark-contract amendments (up from 2 in rev 16). T7 must deliver: narrative inventory, ledger checker, methodology-finding format, methodology-finding consequence (threshold + pass rule), adjudication scope expansion, and mode-mismatch schema.

**Mitigation:** The blockers are correctly identified and scoped. Some are true gating (transcript fidelity, narrative-claim inventory) while others can be incrementally delivered (methodology finding format can precede threshold calibration).

### 2253-line document may exceed single-file reviewability

Each revision adds rejected alternatives, verification items, and rationale. The document has grown 51% across three sessions (1492→2253).

**Mitigation:** Post-acceptance, use `/superspec:spec-writer` to create a modular structure.

### Threshold value is deferred to T7

T4 defines the mechanism but T7 sets the initial threshold value. If T7 sets the threshold too high, methodology findings become non-consequential in practice. If too low, legitimate complex tasks may fail.

**Mitigation:** The threshold is versioned and recorded in `manifest.json`, enabling post-calibration adjustment via contract version increment.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 17, 2253 lines) |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant (L35), gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation (`t2:152-161`), `claim_source` (`t2:101`), extractor order |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry construction (`t3:143-148`), normalization (`t3:118`), claim_key derivation |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition, migration set |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules (L118-123), claim categories (L123-128), metrics (L157), pass rule (L169-181), artifacts (L101-114), contract versioning (L202), safety (L145) |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Checkpoint grammar (L55-65, L126-134), pipeline-data, scout_outcomes |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope (L127-131, immutable scope roots) |
| Event schema | `packages/plugins/cross-model/scripts/event_schema.py` | VALID_MODES (L137, still missing agent_local) |

## Gotchas

### Methodology findings use `inventory_claim_id`, not ledger `claim_id`

Finding rows are keyed by the T7 adjudicator's `inventory_claim_id` — the identifier assigned during claim enumeration. NOT the T4 ledger `claim_id`. The ledger `claim_id` only exists for claims that have ledger entries; `narrative_ledger_violation` findings by definition identify claims WITHOUT ledger entries.

### Methodology-gate breach is a valid scored run, not an invalid run

A run that exceeds `methodology_finding_threshold` is a valid scored run that fails pass-rule condition 5. It is NOT an invalid run. Invalid runs are reserved for run-condition violations (`benchmark.md:98`). A breach alone is not grounds for invalidation or rerun.

### Decomposition is MUST with no exceptions

`decomposition_attempted: false` is ALWAYS a `decomposition_skipped` methodology finding, regardless of which criterion failed for the whole claim. The valid "nothing to decompose" path is `decomposition_attempted: true, subclaims_considered: [], residual_reason` populated. Criterion-1 exception was explicitly rejected (§7.61).

### Readiness gate is scoped to scored runs

Calibration dry runs (corpus calibration per §4.7, schema shakedown) are permitted before T7 dependencies land. Their results MUST NOT be used for pass/fail comparisons. Only scored runs require all four T7 dependencies.

### Threshold is versioned, not configurable

`methodology_finding_threshold` is part of the versioned benchmark contract (`benchmark.md:202`), recorded in `manifest.json`. It is NOT a runtime configuration parameter. Changing it requires a contract version increment.

### Five finding kinds, two detection methods

| Kind | Detection | Key |
|------|-----------|-----|
| `under_reading` | judgment | `inventory_claim_id` |
| `shape_inadequacy` | judgment | `inventory_claim_id` |
| `misclassification` | judgment | `inventory_claim_id` |
| `decomposition_skipped` | mechanical | `inventory_claim_id` |
| `narrative_ledger_violation` | mechanical | `inventory_claim_id` |

All keyed by `inventory_claim_id`. Optional `ledger_claim_id` cross-reference for kinds that have one (all except `narrative_ledger_violation`).

### Narrative-to-ledger categories must mirror benchmark exactly

The list at §5.2 must match `benchmark.md:123-128` verbatim: repository state, implementation behavior, contract or spec requirements, current code relationships. Missing any category creates a loophole.

### Pre-T7 enforcement is single-valued: scored benchmark runs blocked

No "adjudicator catches violations before T7" language in benchmark-oriented sections. The narrative-to-ledger MUST is a contract obligation; enforcement is T7-only. Scored benchmark runs don't happen without T7.

### `claim_id` allocation depends on intra-phase ordering

Claims must be sorted by `(claim_key, status)` ascending before Phase 1 and Phase 2 processing (§3.1.2). Without this sort, `claim_id` allocation is non-deterministic.

### §6.2 benchmark-contract amendment table has 4 rows (up from 2)

Rev 17 added: methodology finding consequence (threshold + pass rule) and adjudication scope expansion. The original 2 rows (finding format, mode-mismatch artifact) remain. All 4 are readiness gate prerequisites.

## User Preferences

**Counter-review pattern:** User provides structured counter-review with priority levels ([P1], [P2]), specific file:line references, "why it matters" explanations, and concrete required changes. Follows the same adversarial review format as full design reviews.

**Contract-level precision:** User evaluates proposals against the consuming contract's structure, not just internal consistency. The `claim_id` key issue was caught by checking what identifier exists for `narrative_ledger_violation` findings. The asymmetry issue was caught by checking what artifact surfaces both benchmark systems produce. The versioning issue was caught by checking `benchmark.md:202`.

**Convergence tolerance with depth:** User accepts iterative convergence (four counter-review rounds for RC1) but expects each round to address the specific issues raised. No hand-waving — "define the counting unit", "decide whether it's comparative or candidate-only", "pin the threshold".

**Separation of concerns between review rounds:** User counter-reviews proposals before editing. The pattern is: (1) Claude proposes, (2) user counter-reviews, (3) Claude tightens, (4) repeat until accepted, (5) THEN edit the draft. This session had four counter-review rounds before a single edit was made.

**Explicit scope direction:** User explicitly stated next session's approach: "Next session we should run a thorough self-review with the design-review-team skill." This directs the session plan.

**Absolute language sensitivity:** User catches absolute statements that conflict with other legitimate paths. "MUST NOT be rerun" was too absolute because other independent rerun triggers exist. Prefers "alone is not grounds for" over "MUST NOT".
