---
date: 2026-04-02
time: "17:53"
created_at: "2026-04-02T17:53:38Z"
session_id: 9abd6240-b3e8-447f-bca0-3dff7df64510
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_12-49_t04-t4-evidence-provenance-rev14-claim-ledger-and-g3-separation.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 1514b40b
title: "T-04 T4 evidence provenance — revisions 15-16, enforcement and pipeline boundary"
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

# Handoff: T-04 T4 evidence provenance — revisions 15-16, enforcement and pipeline boundary

## Goal

Close gate G3 (evidence provenance retention) — the last remaining hard gate before T6 (composition check) can begin. G1, G2, G4, G5 are `Accepted (design)`. G3 requires: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface. The risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:67` governs G3.

**Trigger:** Previous session completed revision 14. This session received the user's adversarial review of rev 14, iterated through revisions 15 and 16 in response.

**Stakes:** All 5 hard gates must reach `Accepted (design)` before T6 composition check can start (`risk-register.md:79-81`). T4 is the parallel prerequisite that designs how evidence flows through the dialogue loop.

**Success criteria:** User accepts the T4 design contract. G3 moves to `Accepted (design)`.

**Pattern:** Claude drafts, user provides adversarial review with Critical/High severity ratings, specific file:line evidence, and required changes. Two review cycles completed this session (rev 14→15→16). Revision 16 is awaiting review.

## Session Narrative

### Rev 14 review → Revision 15: Enforcement completeness

Session began by loading the prior handoff and receiving the user's adversarial review of revision 14. The review contained 4 critical, 3 high findings. The shift from rev 13's review: rev 13's criticals were about structural separation (checkpoint vs ledger, G3 scope). Rev 14's criticals were about **internal consistency and enforcement completeness** — the separation was done conceptually but not mechanically cleaned up, and the new surfaces lacked enforceable consequences.

The 4 criticals were:

1. **Stale checkpoint-based provenance references** — §5.3 audit chain still routed through `checkpoint [ref: N]` at L1156 and L1163, despite §5.2 L1093 declaring "The checkpoint is NOT the provenance surface." Verification item 37 repeated the stale join. Six+ locations throughout the document.

2. **Silent mode downgrade** — L1303-1304 allowed `agent_local` runs to be "silently downgraded to `server_assisted`" when T5 surfaces weren't ready. Benchmark spec at L52 says plugin-side scouting invalidates runs — same logic applies to mode mismatch.

3. **Narrative-to-ledger relationship undefined** — claim ledger existed as a second factual-claim surface, but no rule defined how narrative relates to it, whether narrative may introduce independent facts, or how deduplication works. Same fact in prose and ledger = six claims or three?

4. **G3 vs benchmark readiness gap** — G3 was narrower than the scored benchmark surface. Closing G3 didn't prevent failing `supported_claim_rate` because unsupported narrative claims were outside any gate.

The 3 high-risk assumptions were:
- `not_scoutable` bucket too broad for the corpus (B1/B4/B5/B7/B8 dominated by cross-system claims)
- Full-file omission penalty too strong (discourages correct broad reads)
- Fixed 2-5 call round model too brittle for multi-entity tasks

I proposed 7 fixes (RC1-RC6, H7) for counter-review. User tightened 4 proposals before editing:

- **RC2:** Don't say "adjudicator uses ledger as inventory source" — contradicts benchmark's full-synthesis scoring at `benchmark.md:118`. Safer: every factual claim must map to a ledger entry; missing = scored normally AND flagged as violation.
- **RC4:** Option A (benchmark-execution prerequisite, not new G6 gate), but must name concrete enforcement point (runner/manifest validator rejects runs).
- **RC5:** Decomposition obligation needs DecompositionTrace fields for auditability. Qualify: decompose only when truth condition preserved.
- **RC6:** "Files explicitly named in claim text" is too permissive — eligibility depends on file-level truth conditions, not path mention.

Rev 15 integrated all adjustments (1916→2058 lines).

### Rev 15 review → Revision 16: Pipeline boundary and enforcement consistency

User's review of rev 15 found 4 findings (1 critical, 2 high, 1 medium) plus 2 medium-risk assumptions. The review's character: rev 15's fixes introduced **new boundary and consistency problems**.

Key findings:

1. **Decomposition creates T2/T3 pipeline boundary violation (Critical)** — mandatory runtime decomposition creates subclaims at T4's Phase 2 without defining how they enter the T2/T3 pipeline. T2 only knows `claim_source: "extracted"` and `"minimum_fallback"` (`t2.md:101`). T3 registry filters on `claim_source == "extracted"` (`t3.md:143`). Decomposed subclaims have no defined source, counter semantics, or continuity behavior.

2. **Narrative-to-ledger MUST narrower than benchmark (High)** — T4 said "repository state, implementation behavior, or contract requirements" but benchmark also scores "current code relationships" (`benchmark.md:128`). Loophole for relationship claims.

3. **Pre-T7 enforcement story internally inconsistent (High)** — §5.2 said adjudicator catches violations pre-T7; §6.2 said benchmark runs impossible pre-T7. Can't be both.

4. **Hygiene failures (Medium)** — header still said rev 14, checklist had SHOULD for ledger completeness, item numbering duplicated 58/59.

Plus two medium-risk assumptions:
- Under-reading and claim-shape findings had no defined benchmark projection path
- Mode-mismatch failure artifact not attached to any benchmark artifact surface

Rev 16 fixes (2058→2118 lines):
- **Decomposition converted to audit-side** — agent MUST NOT register subclaims (T2/T3 boundary). SHOULD consider decomposition, records in ClassificationTrace. Adjudicator audits adequacy as methodology finding. §7.55 rejected alternative added.
- **Category list aligned with benchmark** — added "current code relationships"
- **Enforcement story made single-valued** — benchmark runs blocked until T7. All "adjudicator catches pre-T7" language removed from benchmark sections.
- **Methodology findings defined** — under-reading, shape inadequacy, misclassification appear in `adjudication.json`. Don't change claim labels. Format is T7 dependency.
- **Mode-mismatch artifact** — defined as `runs.json` invalid-run entry. T7 dependency.
- **Hygiene** — header to rev 16, checklist renumbered 55-70, item 45 SHOULD→MUST.

## Decisions

### Convert decomposition from mandatory runtime to audit-side analysis (rev 16)

**Choice:** Remove mandatory runtime decomposition. Agent SHOULD consider decomposition and record analysis in ClassificationTrace. Agent MUST NOT register decomposed subclaims. Adjudicator evaluates adequacy as methodology finding.

**Driver:** User's rev 15 review finding C1: T2 defines two claim sources (`extracted`, `minimum_fallback` at `t2.md:101`). T3 registry filters on `claim_source == "extracted"` (`t3.md:143`). Decomposed subclaims would have no defined source, counter semantics, or continuity behavior — "the system being scored is no longer the system T2/T3 describe."

**Rejected:** (a) Mandatory runtime decomposition with subclaim registration (rev 15) — creates pipeline-boundary violation. No defined `claim_source`, breaks T2 counter computation and T3 registry construction. (b) Moving decomposition upstream into T2/T3 extraction — large cross-contract change, out of T4 scope.

**Implication:** Over-classification pressure comes from the audit layer (adjudicator evaluates whether decomposition was possible) rather than the pipeline layer (agent creates new claims). Same constraint, no boundary violation. If runtime decomposition is desired later, it requires T2/T3 pipeline integration.

**Trade-offs:** Decomposed subclaims don't get scouted — the hard claim stays `not_scoutable` and its subclaims are only noted in the trace. Accepted because the pipeline integrity concern outweighs the marginal evidence gain.

**Confidence:** High (E2) — the pipeline boundary problem is mechanically demonstrated by the `claim_source` enum and T2/T3 filter logic.

**Reversibility:** High — adding runtime decomposition later requires T2/T3 changes but doesn't affect T4's existing architecture.

**Change trigger:** If T2/T3 add a `decomposed` claim source with proper counter and continuity semantics.

### Narrative-to-ledger MUST (rev 15, tightened rev 16)

**Choice:** Every factual claim in any benchmark-scored category (repository state, implementation behavior, contract or spec requirements, current code relationships — mirroring `benchmark.md:123-128` exactly) MUST have a corresponding claim ledger entry. Narrative-only factual claims are synthesis-contract violations.

**Driver:** User's rev 14 review finding C3: "the same fact can appear once in narrative and once in the ledger with slightly different wording, and adjudication becomes semantic guesswork again." Rev 15 counter-review tightened: don't redirect adjudicator inventory (contradicts benchmark) — instead add a contract obligation.

**Rejected:** (a) SHOULD rule (rev 14) — no contract cost for omission. (b) Adjudicator uses ledger as inventory source (rev 15 first proposal) — contradicts benchmark's full-synthesis scoring at `benchmark.md:118`. (c) Prohibiting narrative facts without amending benchmark — overreach.

**Implication:** The benchmark still drives claim enumeration. T4 adds a normative rule about where claims must appear. The dedup rule is for harness/checker join path, not adjudication. Full-synthesis scoring preserved.

**Trade-offs:** Agents must populate the ledger for every factual claim, increasing synthesis workload. Accepted because the alternative (unprovenanced narrative claims) is the problem being solved.

**Confidence:** Medium (E1) — structurally sound and aligned with benchmark, but untested against real synthesis assembly.

**Reversibility:** Medium — removing the MUST would re-create the narrative gap.

**Change trigger:** If agents consistently fail to populate the ledger, consider harness-generated ledger from `claim_provenance_index`.

### Pre-T7 enforcement: benchmark runs blocked (rev 16)

**Choice:** Benchmark runs MUST NOT proceed until T7 narrative-claim inventory and ledger completeness checker are operational. Runner/manifest validator enforces. All "adjudicator catches violations before T7" language removed from benchmark-oriented sections.

**Driver:** User's rev 15 review finding C3: §5.2 said adjudicator catches violations pre-T7; §6.2 said benchmark runs are impossible pre-T7. "That is not a corner case; it is the default execution path right now."

**Rejected:** (a) Pre-T7 adjudicator enforcement with benchmark allowed (rev 15) — contradicts the benchmark-execution prerequisite in the same document. (b) Dropping the benchmark prerequisite (weakens enforcement). (c) G6 gate (cross-document governance change, not needed for T4's defect).

**Implication:** The narrative-to-ledger MUST is a synthesis contract obligation that agents must comply with regardless. But the benchmark enforcement point is T7-only. Before T7, no benchmark runs occur.

**Trade-offs:** No benchmark validation of the narrative-to-ledger rule until T7 lands. Accepted because the alternative (contradictory enforcement story) is worse.

**Confidence:** High (E2) — the contradiction was clear in the rev 15 text.

**Reversibility:** High — if pre-T7 benchmark runs become needed, define how violations appear in adjudication.

**Change trigger:** None.

### Methodology findings as adjudication type (rev 16)

**Choice:** Under-reading, claim-shape inadequacy, and misclassification appear in `adjudication.json` as methodology findings. They do not change claim labels (`supported`/`unsupported`/`false`). Format is T7 adjudication-format dependency.

**Driver:** User's rev 15 review finding H5: "the benchmark only has `supported`, `unsupported`, `false`, and `safety_violation`." Under-reading findings need a defined projection path to change incentives.

**Rejected:** (a) No defined projection (rev 15) — findings become advisory commentary that doesn't affect benchmark output. (b) Changing claim labels based on methodology — over-reaches into adjudication semantics.

**Implication:** T7 must define the methodology finding format in `adjudication.json` and in `runs.json` (for mode-mismatch). Two new entries in the benchmark-contract amendment dependencies table (§6.2).

**Trade-offs:** Methodology findings are informational, not scoring. Agents may treat them as non-consequential. Accepted because the alternative (no projection) is worse, and defining scoring consequences requires benchmark amendment.

**Confidence:** Medium (E1) — architecturally clean but requires T7 to define the format.

**Reversibility:** High — methodology finding format can be extended later.

**Change trigger:** If agents systematically ignore methodology findings, escalate to scoring consequences.

### Hard invalid-run for mode mismatch, scoped to benchmark (rev 15, tightened rev 16)

**Choice:** Benchmark `agent_local` runs with missing T5 surfaces MUST hard-fail (not degrade). Failure artifact writes to `runs.json` as invalid-run entry. Non-benchmark contexts may define their own fallback policy.

**Driver:** User's rev 14 review finding C2: "you can record an apparently valid candidate run that actually exercised the wrong evidence path, contaminating the comparison." Benchmark at `benchmark.md:52` says plugin-side scouting invalidates runs — same logic.

**Rejected:** Silent downgrade to `server_assisted` (rev 14) — contaminates comparison.

**Implication:** Mode-mismatch artifact destination defined (`runs.json`), scoped to benchmark. Non-benchmark use is out of scope.

**Trade-offs:** None — hard-fail on wrong evidence path is unconditionally correct for benchmark integrity.

**Confidence:** High (E2) — the contamination mechanism is demonstrated by the benchmark's own invalid-run rules.

**Reversibility:** N/A — this corrects a defect.

**Change trigger:** None.

### Stale provenance surface cleanup (rev 15)

**Choice:** All checkpoint-based `[ref:]` references in §5.3, verification checklist, and rejected-alternatives "Changed to" sentences updated to claim ledger. Revision history kept historical. ~12 edits.

**Driver:** User's rev 14 review finding C1: the separation was declared in §5.2 but the audit chain in §5.3 still routed through checkpoint. "one implementation will parse refs from the claim ledger while another still expects checkpoint refs."

**Rejected:** N/A — mechanical cleanup.

**Implication:** One canonical provenance authority chain. Claim ledger is the single join surface.

**Trade-offs:** None — fixes a consistency defect.

**Confidence:** High (E2) — grep verification showed all stale references cleaned.

**Reversibility:** N/A.

**Change trigger:** None.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — T4 design contract

**Status:** Untracked (not committed). 2118 lines. Revision 16.

**Purpose:** Design contract for scouting position and evidence provenance in the T-04 benchmark-first local dialogue loop. Governs gate G3.

**Key structural changes in rev 15-16:**

*Rev 15:*
- All stale checkpoint-based `[ref:]` references → claim ledger (§5.3, §7, verification checklist)
- Narrative-to-ledger relationship: claim ledger canonical, every factual claim MUST have ledger entry
- Dedup rule for harness/checker join path (not adjudication)
- Silent mode downgrade → hard invalid-run, scoped to benchmark
- Benchmark-execution prerequisite: runner/manifest validator rejects when T7 unavailable
- Decomposition obligation with extended ClassificationTrace (later revised in rev 16)
- Corpus calibration: dry-run report by task ID
- Read-scope eligibility: file-level truth conditions, not path mention
- Under-reading finding added (adjudicator, non-mechanical)
- Claim-shape adequacy: query coverage must match claim structure

*Rev 16:*
- Decomposition converted from mandatory runtime → audit-side analysis
- Agent MUST NOT register decomposed subclaims (T2/T3 pipeline boundary)
- §7.55 rejected alternative added for mandatory decomposition
- Narrative-to-ledger categories aligned with benchmark exactly (added "current code relationships")
- Pre-T7 enforcement single-valued: benchmark blocked until T7, "adjudicator catches pre-T7" removed
- Methodology findings defined: under-reading, shape inadequacy, misclassification → `adjudication.json`
- Mode-mismatch artifact → `runs.json` invalid-run entry
- Header updated to rev 16, checklist renumbered 55-70, item 45 SHOULD→MUST

**Growth trajectory:** 1492 (rev 11) → 1762 (rev 12) → 1881 (rev 13) → 1916 (rev 14) → 2058 (rev 15) → 2118 (rev 16). Rev 15 was the largest jump (+142, enforcement machinery). Rev 16 was primarily corrections (+60, fixing rev 15's boundary and consistency problems).

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Not committed.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop (unchanged from rev 14)

| Layer | Step | Evidence interaction |
|-------|------|---------------------|
| 1 | Extract semantic data | Claims extracted from Codex response |
| 2a | Phase 1: status changes | Concessions remove from verification_state; reinforcements resolve referents. Claims sorted by `(claim_key, status)` ascending |
| 2b | Phase 1.5: reclassification | Dead-referent claims (`reinforced` AND `revised`) reclassified to `new`. Not-scoutable classification applied |
| 2c | Phase 2: registrations | Claims sorted by `(claim_key, status)` ascending. `claim_id` allocated at new entry creation. Scoutable → `unverified`. Not scoutable → `not_scoutable` (terminal, ClassificationTrace stored) |
| 3 | Compute counters | T2 counter computation (reclassified claims visible here) |
| 4 | Control decision | T1 ControlDecision — conclude/continue/scope_breach |
| 5a | Target selection | Priority: unverified(0) > conflicted(<2) > ambiguous(<2) > skip (terminal states incl. `not_scoutable`) |
| 5b | Tool execution | `scout_budget_spent += 1` here. 2-5 calls: definition + falsification mandatory. `read_anchor` recorded per Read. `expected_contradiction_target` recorded per falsification query. Post-containment capture |
| 5c | Assessment | Disposition from full post-containment output; citation selection with polarity preservation |
| 5d | Record creation | EvidenceRecord created, verification state updated, `scout_attempts += 1`, provenance index updated (record_indices appended) |
| 5e | Atomic commit | Evidence block re-emitted (captured in transcript) |
| 6 | Follow-up composition | Uses evidence record (entity, disposition, citations) |
| 7 | Send follow-up | Codex receives evidence-grounded question |

### Key contract surfaces and T4 interactions (updated for rev 16)

| Surface | Location | T4 interaction |
|---------|----------|---------------|
| Follow-up evidence shape | `codex-dialogue.md:421-429` | Requires snippet + provenance + disposition + question |
| Pipeline-data scout_count | `dialogue-synthesis-format.md:150` | Maps to `evidence_count`. NOT `scout_budget_spent` |
| Pipeline-data claim_provenance_index | §5.2 | Dense JSON array, `claim_id`-keyed. T7 consumer |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | Keys off `turn_history.scout_outcomes`. Record index included per entry |
| Claim trajectory | `dialogue-synthesis-format.md:16` | Needs `not_scoutable` in vocabulary (§6.2 blocker) |
| Claim ledger | §5.2 | `## Claim Ledger` section with `FACT:` lines, `[ref: N]`, `[evidence:]` annotations |
| Synthesis checkpoint | `dialogue-synthesis-format.md:126-134` | Outcome-based (RESOLVED/UNRESOLVED/EMERGED). Unchanged from synthesis-format contract |
| T2 counter computation | `t2:152-161` | `new_claims = count(status == "new")`. Forced-new reclassification feeds into this. **Only counts `claim_source == "extracted"`** — decomposed subclaims MUST NOT be registered |
| T3 registry construction | `t3:143-148` | `prior_registry` filters on `claim_source == "extracted"` — decomposed subclaims would be invisible |
| Benchmark scoring | `benchmark.md:118-119` | Scores final synthesis (full, not just ledger/checkpoint) |
| Benchmark claim categories | `benchmark.md:123-128` | Repository state, implementation behavior, contract or spec requirements, current code relationships. T4 narrative-to-ledger MUST mirrors this list exactly |
| Benchmark metrics | `benchmark.md:157` | `supported_claim_rate`, `false_claim_count`, citations, safety. No methodology finding metric (T7 dependency) |
| Benchmark artifacts | `benchmark.md:101-114` | `manifest.json`, `runs.json`, `adjudication.json`, `summary.md`. Mode-mismatch → `runs.json`. Methodology findings → `adjudication.json` |
| Scope envelope | `consultation-contract.md:127-131` | Immutable `allowed_roots` set at delegation time. Authority for containment |
| G3 invariant | `risk-register.md:35` | "accepted scout results retained as structured provenance" — satisfied by Tier 1 chain |

### T2/T3 pipeline boundary (critical for decomposition decision)

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
| None | Narrative-only claims | No join | Synthesis-contract violation (§5.2). Benchmark runs blocked until T7 enforcement |

### Extended ClassificationTrace fields (rev 15-16)

```text
ClassificationTrace {
  claim_id: int
  candidate_entity: str | null
  failed_criterion: 1 | 2 | 3
  decomposition_attempted: bool
  subclaims_considered: list[str] | null
  residual_reason: str | null
}
```

New fields are audit-side data. The agent records decomposition analysis; the adjudicator evaluates adequacy. No pipeline entries created.

### External blockers enumerated (§6.2, updated for rev 16)

| Category | Owner | Count | Key items |
|----------|-------|-------|-----------|
| T5 migration set | T5 | 5 | Mode enum, synthesis format, dialogue skill, tests |
| Transcript fidelity | T7 | 4 | Normative clause, parseable format, transcript parser, diff engine |
| Allowed-scope safety | T7 | 2 | Secret handling policy, redaction/provenance interaction |
| `claim_provenance_index` consumer | T7 | 4 | Epilogue schema, parser, schema validation, claim ledger [ref:] parser |
| Synthesis-format updates | T7 | 4 | Claim ledger section, `not_scoutable` in claim/evidence trajectory |
| Narrative-claim enforcement | T7 | 3 | Inventory tool, ledger completeness checker, coverage metric |
| **Benchmark-contract amendments** | **T7** | **2** | **Methodology finding format in `adjudication.json`, mode-mismatch artifact in `runs.json`** |

## Context

### Mental Model

This is a **contract convergence problem where each fix must be evaluated for boundary effects**, now past the structural-separation phase (rev 14) and in the **enforcement-completeness and consistency phase** (rev 15-16).

**Convergence trajectory across two sessions:**
- Rev 11: 4 criticals (semantic gaps — capability assumptions without specs)
- Rev 12: 2 criticals (new surface contract problems)
- Rev 13: 2 criticals (closure story failures, structural mismatches)
- Rev 14: 4 criticals (internal consistency, enforcement completeness)
- Rev 15: 1 critical, 2 high, 1 medium (pipeline boundary, enforcement inconsistency, hygiene)

Criticals have shifted from design architecture (rev 12-13) → structural separation (rev 14) → enforcement consistency and cross-contract boundaries (rev 15-16). The core architecture has been stable since rev 7. Each review cycle fixes one class of problem but the fixes introduce new contract surface that needs its own review.

**Key structural insight from rev 16:** Constraints that create artifacts crossing pipeline boundaries (T2/T3 `claim_source` enum) belong at the audit layer (adjudicator evaluation), not the pipeline layer (runtime claim registration). Audit-side pressure achieves the same constraint without boundary violations.

### Project State

T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). Critical path: T2→T3→T6→T7→T8. T4 is a parallel prerequisite for T6.

Gate status:
| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 16 under review)** | **T4: scouting position and evidence provenance** |

## Learnings

### Pipeline-boundary constraints belong at the audit layer, not the pipeline layer

**Mechanism:** When a quality constraint (decomposition obligation) would create artifacts (subclaims) that cross pipeline boundaries (T2/T3 `claim_source` enum), the constraint should live at the audit layer (adjudicator evaluation) rather than the pipeline layer (runtime registration). The audit creates the same pressure without creating undefined state in downstream contracts.

**Evidence:** Rev 15 mandatory decomposition created subclaims with no `claim_source` (`t2.md:101`), no counter semantics (`t2.md:153-156`), no continuity behavior (`t3.md:143-148`). Rev 16 converted to audit-side — same constraint, no boundary violation.

**Implication:** When adding constraints to one contract, verify that the constraint's artifacts are consumable by adjacent contracts. If not, move the constraint to the audit/evaluation layer.

**Watch for:** Any new T4 mechanism that generates claims or modifies claim state outside the defined T2/T3 processing pipeline.

### Enforcement stories must be single-valued per context

**Mechanism:** Rev 15 had two contradictory enforcement paths for narrative-only claims: (1) adjudicator catches violations pre-T7 (§5.2), (2) benchmark runs blocked until T7 (§6.2). Both can't be the "default execution path."

**Evidence:** User's review: "The document now has two enforcement stories for missing ledger entries: pre-T7 adjudicator detection and pre-T7 benchmark rejection. That is not a corner case; it is the default execution path right now."

**Implication:** When defining enforcement, choose one mechanism per execution context. Don't hedge with "adjudicator catches X but also runs are blocked without Y" — pick the blocking one and remove the other.

**Watch for:** Enforcement language that describes both a fallback and a prerequisite for the same condition.

### Category alignment with consuming contracts is a completeness requirement

**Mechanism:** T4's narrative-to-ledger MUST said "repository state, implementation behavior, or contract requirements." The benchmark's claim inventory at `benchmark.md:123-128` also includes "current code relationships." The gap created a loophole for exactly the claim class the benchmark uses heavily.

**Evidence:** User's review: "an agent can still put relationship claims in narrative prose without ledger entries and technically not violate the local MUST text."

**Implication:** When a rule mirrors an external contract's categories, mirror them exactly. Don't paraphrase — use the same list.

**Watch for:** Any normative rule that references a category list from another contract but doesn't reproduce it verbatim.

### Fixes that introduce new contract surface need their own review

**Mechanism:** Rev 15 fixed rev 14's problems but introduced a pipeline boundary violation (decomposition), an enforcement inconsistency (pre-T7 contradiction), and a category alignment gap. Each fix created new contract surface that required verification against adjacent contracts.

**Evidence:** Rev 15 had 4 findings. Only one (hygiene) was about stale content. The other three were about new content introduced by rev 15 fixes.

**Implication:** After a large batch of fixes, expect a follow-up review. Budget for it. The fixes are not "done" when the edits land — they're done when the review cycle closes.

**Watch for:** The temptation to declare a large fix batch as "complete" without verifying cross-references and boundary effects.

## Next Steps

### 1. Await user's adversarial review of revision 16

**Dependencies:** None — draft is ready.

**What to read first:** The current T4 design contract at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (2118 lines, revision 16). Key sections to verify:
- §4.4: Claim-shape adequacy (normative, query coverage must match claim structure)
- §4.7: Decomposition analysis (audit-side, not runtime). MUST NOT register subclaims. ClassificationTrace extended. Corpus calibration requirement.
- §5.2: Narrative-to-ledger relationship (MUST, categories mirror benchmark exactly). Scoring interaction. Dedup rule. Mechanical enforcement (benchmark blocked until T7).
- §5.3: Read-scope rule (file-level truth conditions). Under-reading finding (methodology finding, adjudicator, non-mechanical).
- §6.2: Hard invalid-run for mode mismatch (benchmark behavior, `runs.json`). Benchmark-execution prerequisite (runner/manifest validator). Benchmark-contract amendment dependencies (methodology finding format, mode-mismatch artifact).
- §7.55: Rejected alternative for mandatory runtime decomposition.
- §8 items 55-70: Verification checklist (sequential numbering, no duplicates).

**Expected:** User stated "I will share the findings of my review in the next session." If Accept → promote G3. If Reject → revision 17.

**Approach:** The convergence trajectory suggests rev 16 is the cleanup of rev 15's boundary effects. Remaining findings (if any) should be about the specific rev 16 content (methodology finding projection, audit-side decomposition adequacy) rather than fundamental design issues.

### 2. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 3. Consider committing the T4 design contract

**Note:** The T4 file is currently untracked on branch `docs/t04-t4-scouting-and-evidence-provenance`. 2118 lines, revision 16. Consider committing after acceptance.

## In Progress

**In Progress:** T4 design contract revision 16, awaiting adversarial review.

- **Approach:** Iterative adversarial review — Claude drafts, user reviews with structured findings, Claude revises. Five review cycles across two sessions (rev 11→12→13→14 in prior session, rev 14→15→16 in this session).
- **State:** Draft complete. 2118 lines. Not committed.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) has been stable since rev 6/7. The identity model reached consistency in rev 9. The state model wiring reached consistency in rev 12. The structural separation (claim ledger vs checkpoint, G3 vs narrative coverage) reached consistency in rev 14. The enforcement and boundary story reached consistency in rev 16.
- **Not working / uncertain:** Whether the methodology finding format (T7 dependency) will create sufficient incentive pressure. Whether the audit-side decomposition analysis will be meaningfully populated by agents under token pressure. Whether the `not_scoutable` classification rate against the actual corpus is acceptable.
- **Open question:** Will the user find issues in rev 16's audit-side decomposition, methodology finding projection, or enforcement story?
- **Next action:** Wait for user's review of rev 16. Address findings if Reject. Promote G3 if Accept.

## Open Questions

1. **Will the methodology finding format create sufficient incentive pressure?** Methodology findings don't change claim labels. Agents may treat them as non-consequential. The format is a T7 dependency — T7 can extend it to affect scoring if needed.

2. **Will agents populate the ClassificationTrace decomposition fields?** The decomposition analysis is SHOULD (audit-side), not MUST (runtime). Under token pressure, agents may skip it. The adjudicator still audits decomposition adequacy regardless of trace quality.

3. **Is the `not_scoutable` classification rate acceptable against the corpus?** The corpus calibration requirement (dry-run report by task ID) is in the contract. If the rate is too high for B1/B4/B5/B7/B8, criteria or decomposition rules must be tightened.

4. **Should the T4 contract be committed before acceptance?** Currently untracked. 2118 lines. Committing preserves revision history.

5. **Document size concern.** 2118 lines and growing (+626 from rev 11's 1492). After acceptance, modular split would help.

## Risks

### Rev 16 may still have issues in audit-side decomposition or methodology findings

The audit-side decomposition is a structural change from rev 15's mandatory runtime approach. The methodology finding format is new — its projection path through `adjudication.json` is declared as T7 dependency but the format itself is undefined.

**Mitigation:** The user's reviews are thorough. Each cycle finds fewer and more targeted issues. The convergence trajectory suggests rev 16 is approaching acceptance.

### T7 dependency load continues to grow

§6.2 now has ~24 external blockers plus 2 benchmark-contract amendments, most owned by T7. Rev 16 added methodology finding format and mode-mismatch artifact schema.

**Mitigation:** The blockers are correctly identified and scoped. Some are true gating (transcript fidelity, narrative-claim inventory) while others can be deferred to implementation phase (methodology finding format).

### 2118-line document is unwieldy

Each revision adds rejected alternatives, verification items, and rationale. The document has grown 42% across two sessions (1492→2118).

**Mitigation:** Post-acceptance, use /superspec:spec-writer to create a modular structure.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 16, 2118 lines) |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant (L35), gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation (`t2:152-161`), `claim_source` (`t2:101`), extractor order |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry construction (`t3:143-148`), normalization (`t3:118`), claim_key derivation |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition, migration set |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules (L118-123), claim categories (L123-128), metrics (L157), artifacts (L101-114), safety (L145) |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Checkpoint grammar (L55-65, L126-134), pipeline-data, scout_outcomes |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope (L127-131, immutable scope roots) |
| Event schema | `packages/plugins/cross-model/scripts/event_schema.py` | VALID_MODES (L137, still missing agent_local) |

## Gotchas

### Decomposition is audit-side only — do NOT register subclaims

Agent MUST NOT register decomposed subclaims as pipeline entries. T2/T3 have no `claim_source` for decomposed claims. Records decomposition analysis in ClassificationTrace for adjudicator review. §7.55 rejected alternative explains why mandatory runtime decomposition was removed.

### Narrative-to-ledger categories must mirror benchmark exactly

The list at §5.2 must match `benchmark.md:123-128` verbatim: repository state, implementation behavior, contract or spec requirements, current code relationships. Missing any category creates a loophole. Rev 16 added "current code relationships" after rev 15 omitted it.

### Pre-T7 enforcement is single-valued: benchmark runs blocked

No "adjudicator catches violations before T7" language in benchmark-oriented sections. The narrative-to-ledger MUST is a contract obligation; enforcement is T7-only. Benchmark runs don't happen without T7.

### Methodology findings don't change claim labels

Under-reading, shape inadequacy, and misclassification appear in `adjudication.json` as methodology findings. They do NOT change `supported`/`unsupported`/`false` labels. The format is a T7 dependency — not yet defined in the benchmark contract.

### Mode-mismatch is benchmark behavior, not blanket runtime policy

The hard invalid-run rule at §6.2 is scoped to benchmark execution. Non-benchmark contexts may define their own mode-fallback policy. Don't apply benchmark fail-closed logic to general product behavior.

### `claim_id` allocation depends on intra-phase ordering

Claims must be sorted by `(claim_key, status)` ascending before Phase 1 and Phase 2 processing (§3.1.2). Without this sort, `claim_id` allocation is non-deterministic.

### Omission boundary is fixed at read time

Full-file reads get full-file omission surface. No post-citation enclosing-scope shrinking. Whole-file eligibility depends on file-level truth conditions, not path mention.

### Phase ordering matters for claim_id determinism

Within-turn claim processing order: Phase 1 → Phase 1.5 → Phase 2. Adding a new claim kind must update ALL three phases AND maintain the intra-phase sort.

## User Preferences

**Review pattern:** User provides structured adversarial reviews with consistent format: Critical Failures, High-Risk Assumptions, Real-World Breakpoints, Hidden Dependencies, Required Changes. Each finding has: flaw description with file:line references, "Why it matters" (contract impact), "How it fails in practice" (concrete failure mode), severity, "What must change" (specific required fix).

**Rigor expectation:** Every finding has specific evidence. The user catches subtle contract interactions — pipeline boundary violations (`claim_source` enum), category alignment gaps (missing "current code relationships"), enforcement contradictions (pre-T7 adjudicator + pre-T7 blocking). Hand-waving is consistently rejected.

**Counter-review before editing:** User counter-reviews proposed approaches before edits. Rev 15's counter-review caught 4 issues in the initial proposals. The pattern works — present approach, receive counter-review, edit.

**Cross-contract awareness:** User evaluates fixes for boundary effects against adjacent contracts. Rev 16's critical finding was that rev 15's decomposition obligation created subclaims incompatible with T2/T3's pipeline. Fixes must be evaluated not just for internal consistency but for cross-contract compatibility.

**Single-valued enforcement:** User rejects contradictory enforcement stories. "Either pre-T7 benchmark runs are impossible, or they are valid with a defined adjudication surface. They cannot be both."

**Concrete enforcement points:** Prose-only prerequisites are treated as wishes, not gates. The benchmark-execution prerequisite needed a named enforcement point (runner/manifest validator) to be credible.

**Structural solutions preferred:** Splitting concerns over adapting surfaces. Audit-side over pipeline-side when boundaries are at risk. Exact category mirroring over paraphrasing.

**Convergence tolerance:** Accepts iterative convergence. Five review cycles across two sessions, each finding fewer and more targeted issues. The user expects fixes to introduce new surface that needs review — budgets for follow-up cycles.
