---
date: 2026-04-03
time: "02:06"
created_at: "2026-04-03T02:06:21Z"
session_id: 2d7c58fa-bcda-4877-90ca-ba3134259022
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_18-26_t04-t4-evidence-provenance-rev17-methodology-finding-consequence.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 3ac55dd9
title: "T-04 T4 evidence provenance — rev 17 design-review-team self-review"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
---

# Handoff: T-04 T4 evidence provenance — rev 17 design-review-team self-review

## Goal

Execute the design-review-team skill on T4 rev 17 as a thorough self-review, per user's explicit request in the prior session: "Next session we should run a thorough self-review with the design-review-team skill."

**Trigger:** Prior session completed rev 17 of the T4 design contract (scouting position and evidence provenance). User wanted a multi-reviewer self-review before their own adversarial review. The design-review-team deploys 6 specialized Sonnet reviewers in parallel, each analyzing the design through a different analytical lens.

**Stakes:** G3 (evidence provenance retention) is the last hard gate before T6 composition check. G1, G2, G4, G5 are all `Accepted (design)`. The self-review tests whether rev 17's methodology finding consequence machinery, readiness gate extension, and decomposition MUST are internally consistent before the user's adversarial review.

**Success criteria:** Self-review complete, findings catalogued, durable record saved. No design changes in this session — findings are input for the user's adversarial review and potential rev 18.

**Connection to project arc:** T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). T4 is a parallel prerequisite for T6. All other gates accepted. G3 acceptance would unblock T6 composition check.

## Session Narrative

### Loading and framing

Session loaded the prior handoff (rev 17, methodology finding consequence and enforcement weight). User confirmed the next step: run design-review-team on rev 17. This was an execution session — the task was well-defined, the skill was specified, and the approach was prescribed.

### Phase 1: Frame

Read the full 2253-line T4 design contract in four 300-line chunks plus the final 153 lines. Also read the design-review-team skill references: `staffing-rules.md`, `tension-registry.md`, `system-design-dimensions.md` (46 lenses across 8 categories), and `reviewer-briefs.md` (6 role definitions with collaboration playbooks).

Framing decisions:
- **Scope:** `subsystem` — T4 defines one component within the larger T-04 dialogue loop, not the full system
- **Archetypes:** Data pipeline (claims flow through extraction → classification → scouting → provenance indexing) + Financial/regulated (auditability, correctness, deterministic allocation, versioned contract surfaces). Medium-high confidence on both
- **Stakes:** `high` — design contract governing a gate, 17 adversarial revisions, cascading T7 dependencies

Generated the emphasis map by intersecting the two archetypes against the lens weighting table. Data pipeline primary lenses: Data Flow Clarity, Schema Governance, Idempotency & Safety. Financial/regulated primary lenses: Auditability, Correctness, Durability. Combined per-reviewer: 4 categories at primary (Behavioral, Data, Reliability, Trust & Safety), 1 at secondary (Change), 2 at background (Structural, Cognitive). No reviewers suppressed — all had meaningful surface.

### Phase 2: Staff

Generated per-run tension playbooks by intersecting the canonical tension registry with the active roster and emphasis map. Seven canonical tensions checked; all reviewer pairs active. CT-1 (Performance ↔ Correctness) and CT-4 (Security ↔ Operability) flagged as high-attention given primary emphasis on both sides. CT-6 (Consistency ↔ Availability) also high-attention. The remaining tensions were low or secondary attention.

### Phase 3: Review

Spawned 6 Sonnet reviewers in parallel via agent teams. Each received:
- Role ID, categories owned, emphasis levels
- Path to `frame.md` (framing context written to `.design-review-workspace/framing/`)
- Instructions to read their section of `reviewer-briefs.md` and the shared lens framework
- Per-run tension playbook entries
- Finding schema (inlined in spawn prompt — too critical for file reference)
- Output file path in `.design-review-workspace/findings/`
- Key section pointers into the 2253-line document (line ranges for relevant sections)

Reviewer completion order: change (first), reliability-operational, trust-safety, data, behavioral, structural-cognitive (last — completed silently, task marked done but no explicit completion message before shutdown).

**Cross-reviewer lateral messaging was active and productive:**
- change → data: CH-1 schema versioning gap affects `claim_provenance_index` wire format
- change → structural-cognitive: CH-2 extensibility concern traces to closed enum pattern
- behavioral → reliability-operational: BH-5 layer-2 phase transition atomicity gap
- reliability-operational → behavioral: RO-2 crash detection gap creates runtime risk
- trust-safety → reliability-operational: CT-4 tension — secret-handling blocker creates operational constraint
- data → behavioral: CT-1 note on diff lifecycle

After initial findings were written, reviewers continued cross-review coordination, producing 4 additional followup findings (BH-6, BH-7, DA-8, RO-7) that refined existing canonical findings. Key chain: BH-5 (atomicity gap) → RO-6 (rollback specification) → BH-6 (terminal marker) converged on a single implementation recommendation: atomic layer-2 rollback → T1 error → structured terminal record.

### Phase 4: Synthesize

Read all 6 findings files (28 raw findings + 4 cross-review followups). Performed:

1. **Canonicalization:** All findings followed the prescribed schema. Zero normalization rewrites.

2. **Deduplication:** Identified 4 merge clusters:
   - `max_evidence` undefined: BH-3 + DA-6 + RO-5 → triple independent convergence (strongest signal)
   - Layer-2 atomicity: BH-5 + RO-6 → cross-lens followup confirmation
   - Transcript fidelity degradation: RO-1 + TS-3 → independent convergence
   - Concession boundary: DA-3 + DA-4 + DA-7 → related pattern extension at same surface

3. **Corroboration assessment:** 4 corroborated findings. Zero contradictions.

4. **Tension mapping:** 3 tensions emitted (all canonical): CT-1 (Correctness ↔ Performance on diff computation), CT-4 (Security ↔ Operability on secret handling), CT-3 (Completeness ↔ Changeability on schema evolution).

5. **Prioritization:** 14 P1, 8 P2, 0 P0.

### Phase 5: Deliver and cleanup

Wrote synthesis ledger to `.design-review-workspace/synthesis/ledger.md` and full report to `.design-review-workspace/synthesis/report.md`. Presented findings summary to user. Sent shutdown requests to all 6 reviewers — all approved and terminated cleanly. TeamDelete succeeded.

User requested saving to `docs/audits/` — committed at `3ac55dd9`. User then requested workspace cleanup — trashed `.design-review-workspace/`.

## Decisions

### Framing: Data pipeline + Financial/regulated archetypes at subsystem scope

**Choice:** Reviewed T4 as a subsystem with Data pipeline + Financial/regulated archetype combination.

**Driver:** T4's core concern is data flow (claims → phases → evidence → provenance indexing) mapped to Data pipeline. The emphasis on auditability, correctness, deterministic allocation, versioned contract surfaces, and reproducibility mapped to Financial/regulated. Both at medium-high confidence.

**Rejected alternatives:**

(a) System scope — would review the entire T-04 dialogue loop (T1-T5 + benchmark). T4 is one component with well-defined interfaces. System scope would dilute reviewer attention. The user requested self-review of the T4 contract specifically.

(b) Interface scope — would focus on T4's contract boundaries with T1-T3, T5, T7. Too narrow — misses the internal state model, processing phases, and evidence model design. The core architecture (which has survived 17 revisions) is worth having reviewers validate.

(c) Event-driven/streaming archetype — the dialogue loop has event-driven characteristics (claims flow through phases, evidence blocks re-emitted per round). But T4's design is fundamentally sequential (single-agent loop, deterministic processing order), not event-driven. The archetype would misweight Backpressure and Concurrency Safety at the expense of Auditability and Schema Governance.

**Trade-offs:** Background emphasis on Structural and Cognitive means those categories got sentinel-level checks only. Acceptable because the core architecture has been adversarially reviewed 17 times — structural defects at this stage would be surprising. The reviewers confirmed this: structural-cognitive found zero structural defects, only two boundary definition gaps in rev 17 additions.

**Confidence:** High (E2) — archetype selection validated by reviewer finding distribution. Data reviewer produced highest finding density (7 findings), followed by reliability (6) — both at primary emphasis. Background-emphasis reviewers (structural-cognitive) produced only 3, all at boundary-level. Finding density correlates with emphasis, confirming the archetype weighting was appropriate.

**Reversibility:** N/A — review is complete. A re-review with different framing would produce different emphasis but likely the same high-priority findings.

**Change trigger:** None — review is done.

## Changes

### `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` — Design review report

**Status:** Committed at `3ac55dd9`.

**Purpose:** Durable record of the 6-reviewer design review of T4 rev 17. Full report with 22 canonical findings, 3 tensions, audit metrics, coverage assessment.

**Key sections:** Review Snapshot (metrics), Focus and Coverage (per-reviewer summary), Findings (F1-F22 with priority, lens, decision state, anchor, corroboration, problem, impact, recommendation), Tension Map (T1-T3), Questions / Next Probes (4 questions for the user).

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Committed.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop (unchanged from prior session)

The prior handoff documented this in full (7-layer pipeline from extraction to follow-up). No new architectural understanding was gained — this session validated existing understanding through 6 independent reviews. The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) received zero structural critiques from any reviewer.

### Self-review findings summary (22 canonical, for future-Claude to act on)

Future-Claude will need this to understand what the user's adversarial review is responding to. Organized by theme with finding IDs matching the audit report at `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md`.

**Correctness loopholes (2 findings):**
- **F1 (P1):** Intra-phase sort `(claim_key, status)` has no tiebreaker — two same-key same-status claims in one turn produce non-deterministic `claim_id`. Fix: add `claim_text` as tertiary sort key in §3.1.2.
- **F2 (P1):** Second-attempt query diversity can be satisfied by a novel supplementary query while reusing identical definition and falsification queries. Fix: type-aware diversity (at least one mandatory-type query must differ) in §4.4.

**Schema and wire format gaps (5 findings):**
- **F3 (P1):** `residual_reason` nullability is a conditional-required rule that lives in prose but not schema. `{subclaims_considered: [], residual_reason: null}` is invalid per prose but accepted by schema. Fix: explicit invariant in §4.7.
- **F4 (P1):** Methodology finding `detail` field is untyped — five finding kinds likely need different structures. T4/T7 will produce incompatible output. Fix: per-kind minimum content floor in §6.2.
- **F5 (P1):** Wire format example in §5.2 omits 3 of 6 ClassificationTrace fields (`decomposition_attempted`, `subclaims_considered`, `residual_reason`). Fix: complete example.
- **F6 (P1, corroborated — 3 data findings):** Concession lifecycle has 3 gaps: (a) no status field in ProvenanceEntry for conceded claims, (b) dense-array representation for conceded slots undefined, (c) no ledger policy for conceded claims. Root cause: concession removes from `verification_state` and retains in `claim_provenance_index` but doesn't specify how the split presents to external consumers.
- **F11 (P1):** No schema versioning on wire formats with named T7 consumers. Revisions 9-12 each broke schemas — safe against a doc but not against deployed parsers. Fix: monotonic `schema_version: int` on `claim_provenance_index` and `ClassificationTrace` pipeline-data surfaces.

**Safety and trust boundaries (2 findings):**
- **F13 (P1):** Allowed-scope secret handling has no interim constraint. Helper-era `redactions_applied`/`risk_signal` removed. "Curated corpus" assumption is not enforced. Fix: interim pre-execution safeguard + named audit prerequisite.
- **F14 (P1):** Absent `scope_envelope` defaults to unrestricted (consultation contract backwards compat). No benchmark-specific fail-closed guard. Fix: one-line addition to §4.6 or §6.2.

**Operational readiness (5 findings):**
- **F8 (P1, corroborated — RO-1 + TS-3):** Transcript fidelity degradation produces no artifact-level signal. Auditor cannot distinguish compliant from non-compliant runs. Fix: `transcript_fidelity_contract_resolved: bool` in `manifest.json`.
- **F9 (P1):** Crash/abort recovery path is "rerun" with no harness detection mechanism. Fix: define crash detection boundary (e.g., synthesis artifact + `runs.json` entry both must exist).
- **F10 (P1):** T7 prerequisite block (4 items) is atomic with no partial-readiness path. Fix: decompose into tiers or document T7 as sole unblocking authority.
- **F12 (P1):** Verification checklist (70 items) mixes pre-T7 and T7-required items. Fix: tag each item.
- **F15 (P2, corroborated — BH-3 + DA-6 + RO-5, triple convergence):** `max_evidence` undefined. All budget gates, compression tiers, and effort budget formula reference it. Fix: define normative values or delegate to benchmark contract.

**Additional P2 findings (3):**
- **F16 (P2, corroborated — BH-5 + RO-6):** Layer-2 mid-phase failure leaves intermediate state with no rollback. Fix: define atomicity contract.
- **F17 (P2):** Mechanical diff performance envelope uncharacterized for full-file reads on large files. Fix: performance note.
- **F18 (P2):** Phase 1 reinforced processing doesn't describe NO_LIVE_REFERENT path inline. Fix: add branch.
- **F19 (P2):** Claim-class taxonomy closed with no documented extension blast radius. Fix: enumeration note.
- **F20 (P2):** Benchmark-execution prerequisite has no amendment path for threshold errors. Fix: threshold amendment procedure.
- **F21 (P2):** Evidence durability depends on transcript retention T4 doesn't own. Fix: durability statement.
- **F22 (P2):** `ledger_claim_id` vs `claim_id` naming inconsistency in finding row schema. Fix: rename or parenthetical.

### Key contract surfaces verified by reviewers

| Surface | Location | Reviewer(s) that verified |
|---------|----------|--------------------------|
| Claim occurrence registry | t4.md §3.1 (lines 196-299) | behavioral (sort determinism), structural-cognitive (Phase 1 legibility) |
| Verification state model | t4.md §3.4 (lines 446-527) | behavioral (lifecycle correctness), data (concession boundary) |
| Agent working state | t4.md §3.5 (lines 533-598) | behavioral (budget gates), data (provenance index), reliability (config clarity) |
| Evidence persistence | t4.md §3.8-3.9 (lines 658-718) | reliability (durability, crash recovery, degradation), trust-safety (audit conditionality) |
| Scout query coverage | t4.md §4.4 (lines 785-858) | behavioral (diversity loophole) |
| Containment contract | t4.md §4.6 (lines 874-934) | trust-safety (scope_envelope default, secret handling) |
| Claim-class scope | t4.md §4.7 (lines 935-1078) | structural-cognitive (ClassificationTrace schema), data (wire format), change (extensibility) |
| Provenance index | t4.md §5.2 (lines 1113-1267) | data (serialization handoff, concession boundary, wire format), change (versioning) |
| Audit chain | t4.md §5.3 (lines 1273-1403) | behavioral (diff performance), trust-safety (audit authority conditionality) |
| External blockers | t4.md §6.2 (lines 1450-1568) | reliability (prerequisite block), change (testability partition, amendment path), structural-cognitive (detail field) |
| Verification items | t4.md §8 (lines 1965-2253) | change (pre-T7/T7-required partition) |

### Methodology finding schema interactions (rev 17 — verified for internal consistency)

Five sections reference methodology findings (§4.4, §4.7, §5.2, §5.3, §6.2). The self-review confirmed:
- All five sections reference the same `finding_kind` enum values consistently
- The `inventory_claim_id` key is used consistently across sections
- The `detection: judgment | mechanical` distinction is consistent
- The `methodology_finding_threshold` is consistently described as versioned, pinned, and recorded in `manifest.json`

The internal consistency issues found were not about the methodology finding schema itself but about adjacent structures: the `detail` field being untyped (SC-2/F4), the wire format example omitting three ClassificationTrace fields (DA-2/F5), and the `residual_reason` nullability rule not being schema-encoded (SC-1/F3).

## Context

### Mental Model

This is a **review validation session**, not a design session. The T4 design contract has been through 17 adversarial revisions. The self-review tests whether the architecture and its enforcement machinery are internally consistent from 6 independent analytical perspectives. The finding class (specification gaps at contract boundaries, not structural critiques) confirms the design is mature.

**Key frame from the review:** The 14 P1 findings cluster into 4 themes:
1. **Correctness loopholes** (F1, F2): Mechanical gaps in formal criteria (sort tiebreaker, query diversity). These are the kind of gaps that adversarial review catches well — they're about the logical completeness of rules.
2. **Schema/wire format gaps** (F3-F5, F6, F11): Under-specification at the boundary between T4 and T7. Expected for a contract that declares T7 dependencies but hasn't yet been consumed by T7.
3. **Safety boundaries** (F13, F14): Configuration defaults that are safe for curated corpora but unguarded for general use. The design explicitly scopes to curated corpora but doesn't enforce the scoping.
4. **Operational readiness** (F8-F10, F12, F15): Gaps in the operational infrastructure around the design (crash detection, degradation signaling, testability partition, budget configuration). These are implementation preparation gaps, not design defects.

### Project State

Gate status unchanged from prior handoff:

| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 17, self-review complete)** | **T4: scouting position and evidence provenance** |

### Convergence trajectory update

Adding the self-review to the trajectory from the prior handoff:

- Rev 11: 4 criticals (semantic gaps — capability assumptions without specs)
- Rev 12: 2 criticals (new surface contract problems)
- Rev 13: 2 criticals (closure story failures, structural mismatches)
- Rev 14: 4 criticals (internal consistency, enforcement completeness)
- Rev 15: 1 critical, 2 high, 1 medium (pipeline boundary, enforcement inconsistency, hygiene)
- Rev 16: 0 criticals, 2 high, 1 medium (enforcement weight, readiness gap, SHOULD/MUST)
- Rev 17: 0 criticals, awaiting user adversarial review
- **Self-review (rev 17): 0 P0, 14 P1, 8 P2 — all specification gaps at contract boundaries, no structural critiques**

The self-review confirms the convergence trajectory: finding severity continues to decrease. The remaining findings are about contract-boundary precision, not architecture or enforcement mechanism design.

## Learnings

### Triple convergence is the strongest corroboration signal

**Mechanism:** When 3 reviewers from 3 different analytical lenses independently converge on the same finding, the finding is almost certainly real and significant. In this review, `max_evidence` being undefined was found by behavioral (budget gates inert), data (compression tiers illustrative), and reliability (configuration surface unspecified). Each reviewer discovered the gap through a different entry point in the document and characterized it through a different concern.

**Evidence:** BH-3 (§3.5 budget gates → undefined `max_evidence`), DA-6 (§3.6 compression accounting → ungrounded tiers), RO-5 (§3.5 `max_scout_rounds = max_evidence + 2` → silently tethered configuration). Three sections, three lenses, one root cause.

**Implication:** For future design reviews, triple-convergence findings should be treated as near-certain issues. The independent discovery means the gap is visible from multiple analytical angles, not an artifact of one reviewer's perspective.

**Watch for:** False triple convergence — three reviewers might independently find the same obvious gap (like a typo) without it being architecturally significant. The convergence must be through different lenses at different document locations to be meaningful.

### Cross-reviewer lateral messaging produces genuinely better recommendations

**Mechanism:** The BH-5 → RO-6 → BH-6 chain is the strongest example. Behavioral identified the layer-2 atomicity gap (failure containment lens). Reliability confirmed and extended with rollback specification (recoverability lens). Then behavioral proposed a structured terminal record that ties into the existing §6.2 transcript format blocker. The final composite recommendation (atomic rollback → T1 error → structured terminal record) is more implementable than any single reviewer's version.

**Evidence:** BH-5 identified the problem but recommended either (a) atomic rollback or (b) named partial states. RO-6 converged on option (a) and added: "cross-reference with RO-2: harness crash-detection should also cover T1 error paths from layer-2 rollback." BH-6 then proposed the specific terminal record format. The three-finding chain produced a single actionable implementation path.

**Implication:** Agent team reviews with lateral messaging enabled produce qualitatively different output than parallel independent reviews. The collaboration playbooks (static per-reviewer rules + per-run tension entries) are the enabling mechanism. Without them, the reviewers would have produced three separate findings with three separate recommendations.

**Watch for:** Lateral messaging can also produce echo-chamber effects where one reviewer's framing biases another's. The `provenance: followup` and `prompted_by` fields in the finding schema make this traceable — always check whether followup findings add genuinely new evidence or just restate the original finding from a different angle.

### Three architectural tensions mapped — each with concrete anchors

The review identified 3 tensions from the canonical tension registry, all with concrete anchors in the T4 design:

1. **CT-1: Correctness ↔ Performance (F17).** Full-file omission diffs prevent shape-gaming (§7.50 explicitly rejected the enclosing-scope heuristic) but have unbounded per-record computational cost at the harness layer. A 2000-line module read with a presence/absence claim produces a 2000-line diff. The correctness property (no post-citation boundary shrinking) is well-justified; the performance envelope is uncharacterized.

2. **CT-4: Security ↔ Operability (F13).** The allowed-scope secret handling dependency blocks non-curated corpus use until T7 resolves redaction/provenance interaction. The "curated corpus" assumption is stated but not enforced — a load-bearing safety assumption with no guard. Likely failure story: `.env` files in a "curated" corpus leak secrets verbatim into transcript artifacts.

3. **CT-3: Completeness ↔ Changeability (F11, F19).** The design's specification depth (2253 lines, 70 verification items, 8+ schemas) is the product of 17 adversarial revisions. This completeness makes schema evolution expensive once T7 consumers exist. Rev 9-12 each changed load-bearing schemas against a design doc (safe); the same changes against deployed parsers require coordinated version bumps with no versioning mechanism defined.

### Design review finding themes predict design maturity stage

**Mechanism:** The 14 P1 findings cluster into 4 themes that correspond to a specific maturity stage: (1) correctness loopholes in formal criteria, (2) schema/wire format under-specification at cross-contract boundaries, (3) unguarded configuration defaults, (4) operational preparation gaps. These are all "boundary tightening" findings — not structural, not architectural, not about enforcement mechanisms.

**Evidence:** Zero P0 findings. Zero structural critiques from structural-cognitive reviewer (which explicitly checked Purpose Fit, Responsibility Partitioning, Dependency Direction, Composability). The data reviewer's highest-density surface was the concession boundary (3 related findings) — an edge case in the provenance lifecycle, not a core design flaw.

**Implication:** The finding theme distribution confirms the convergence trajectory from the prior handoff: the design is past structural separation (rev 14), past enforcement consistency (rev 16), past enforcement weight (rev 17), and now in the contract-boundary precision phase. The self-review validates that the user's adversarial review should focus on whether the specific P1 findings warrant revision or are acceptable as implementation-time specifications.

**Watch for:** A self-review finding zero P0s does not mean the design is finished — it means the design has no findings at the severity level the review team is calibrated to detect. The user's adversarial review may find issues the team review missed, particularly contract-level precision issues that require deep cross-contract knowledge.

## Next Steps

### 1. Await user's adversarial review of revision 17

**Dependencies:** Self-review complete (this session).

**What to read first:** The audit report at `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` — user should review the 22 findings and 4 questions before conducting their own adversarial review.

**Expected:** User may accept some findings as-is (address in rev 18), reject others (rationale), and potentially find issues the team review missed. The user's prior review pattern: structured counter-review with priority levels, specific file:line references, "why it matters" explanations, and concrete required changes.

**Approach:** If findings are accepted → address in rev 18 following the same proposal/counter-review pattern as prior sessions. If user has their own findings → integrate with self-review findings.

### 2. Address accepted findings in revision 18

**Dependencies:** User's adversarial review (step 1).

**Key findings likely requiring contract edits:**
- F1 (sort tiebreaker): Add `claim_text` as tertiary sort key. Small change in §3.1.2 and verification item 64.
- F2 (query diversity): Tighten to type-aware diversity. Change in §4.4, verification item 18, §7.34.
- F3 (residual_reason invariant): Add explicit invariant alongside schema in §4.7.
- F5 (wire format example): Update example in §5.2 to show complete ClassificationTrace.
- F6 (concession boundary): Three related additions to §3.4, §5.2.
- F14 (scope_envelope guard): One-line addition to §4.6 or §6.2.

**Key findings likely deferred (documentation/metadata, not contract changes):**
- F4 (detail field typing): Per-kind content specification — may be a T7 decision
- F12 (verification checklist partition): Pre-T7/T7-required tags on existing items
- F15 (max_evidence): Define or delegate to benchmark contract

### 3. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract (after rev 18 or however many revisions are needed).

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 4. Post-acceptance: modular split with /superspec:spec-writer

**Note:** Document has grown from 1492 (rev 11) to 2253 (rev 17), a 51% increase across three sessions. Post-acceptance, use `/superspec:spec-writer` to create a modular structure. Rev 18 changes will likely add lines (new invariant, updated examples, concession boundary policy), pushing toward 2300+.

## In Progress

**In Progress:** T4 design contract revision 17, self-review complete, awaiting user adversarial review.

- **Approach:** Self-review via design-review-team (6 Sonnet reviewers in parallel) → user adversarial review → address findings → accept.
- **State:** Self-review complete. 22 canonical findings documented. Audit report committed. No design changes made this session.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) validated as sound by 6 independent reviewers. The methodology finding consequence machinery (rev 17 addition) validated as internally consistent. The identity model, state model, structural separation, enforcement consistency, and enforcement weight all validated.
- **Not working / uncertain:** 14 P1 specification gaps at contract boundaries. The user must decide which to address in rev 18 vs. defer to implementation. The 4 questions from the report (concession boundary timing, T7 prerequisite decomposition, max_evidence ownership, verification checklist partition timing) need user answers.
- **Open question:** Will the user's adversarial review find issues the team review missed? The team review was calibrated for architectural and specification gaps; the user reviews for contract-level precision and cross-contract integration.
- **Next action:** Wait for user's adversarial review of rev 17, informed by the audit report.

## Open Questions

1. **Should the concession boundary (F6) be fully specified before G3 acceptance?** None of the three concession gaps block the G3 invariant (scouted provenance retention). But they will block T7 harness implementation. If G3 acceptance means "T7 can start building," the concession boundary needs resolution now.

2. **Is the T7 prerequisite block intentionally atomic (F10)?** Item 1 (narrative inventory) gates `supported_claim_rate` validity. Items 2-4 gate artifact structural completeness. Could items 2-4 unblock independently?

3. **What is the expected `max_evidence` range (F15)?** Compression accounting implies 6-8. Is this a T4 parameter, benchmark-contract parameter, or per-task-class parameter? Three reviewers independently flagged this.

4. **Should the verification checklist be partitioned before acceptance (F12)?** If T4 implementation starts immediately after G3 acceptance, implementors need the pre-T7/T7-required partition at acceptance time, not after.

5. **Will the user's adversarial review surface issues the team review missed?** The team review was calibrated for architectural lenses. The user's strength is contract-level precision and cross-contract integration (demonstrated across revs 11-17). These are complementary perspectives.

## Risks

### Self-review findings may overlap with or contradict user's adversarial review findings

The 22 self-review findings are from 6 Sonnet reviewers. The user's adversarial review is from a human with deep cross-contract knowledge. The finding sets may partially overlap, partially complement, or occasionally contradict. The user's prior pattern (structured counter-review with priority levels) handles this well — the self-review findings are input, not authority.

**Mitigation:** Present the audit report as input for the user's review, not as pre-accepted findings. The user decides which findings warrant revision.

### Rev 18 scope may be large

If the user accepts most P1 findings plus their own, rev 18 could be substantial. F6 alone (concession boundary) has three sub-gaps requiring additions to §3.4, §5.2. F1 and F2 are small edits. F5 is an example update. The combined scope is manageable but should be estimated before starting.

**Mitigation:** Propose changes for counter-review before editing, following the established pattern from rev 17 (four counter-review rounds before a single edit).

### Document continues to grow

Rev 17 is 2253 lines. Rev 18 will add lines (new invariant, updated examples, concession boundary policy, possibly new rejected alternatives). Growth trajectory: 1492 → 2253 (+51%) across three sessions. The superspec:spec-writer modular split should happen soon after acceptance.

**Mitigation:** Post-acceptance, modular split is the explicit next step (step 4 above).

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 17, 2253 lines) |
| Design review report (this session's output) | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` | 22 canonical findings, 3 tensions, audit metrics |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant (L35), gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation, `claim_source`, extractor order |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry construction, normalization, claim_key derivation |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition, migration set |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules, claim categories, metrics, pass rule, artifacts, safety |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Checkpoint grammar, pipeline-data, scout_outcomes |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope (immutable scope roots) |
| Event schema | `packages/plugins/cross-model/scripts/event_schema.py` | VALID_MODES (still missing agent_local) |

## Gotchas

### Self-review finding count is higher than adversarial review finding count — this is expected

The self-review produced 22 canonical findings (14 P1, 8 P2). Prior adversarial reviews typically produced 2-4 findings per round. This does not mean rev 17 has more issues — it means the 6-reviewer team format applies a wider lens set. Many P1 findings (F7 serialization handoff, F8 manifest.json flag, F12 checklist partition, F15 max_evidence) are specification completeness gaps that would not surface in adversarial review focused on contract-level precision.

### Cross-review followup findings refine but don't change the canonical count

The reviewers produced 4 additional findings (BH-6, BH-7, DA-8, RO-7) during cross-review coordination after the initial 28. These refine existing canonical findings' recommendations rather than adding new concerns. The canonical count remains 22. The updated findings files contain these refinements, but the audit report captures the initial synthesis.

### Audit report was synthesized from initial 28 findings, not the final 32

The synthesis (22 canonical findings) was performed on the initial 28 raw findings. The 4 cross-review followups arrived after synthesis. They refine F6 (concession boundary — typed tombstone recommendation), F9/F16 (crash detection + layer-2 atomicity — terminal record chain), F13 (secret handling — operational ownership), and F17 (diff performance — lifecycle/storage). The refined recommendations are improvements but don't change finding priorities or the overall assessment.

### The design-review-team skill requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

The skill checks this environment variable as a prerequisite. If not set, it hard-stops. This session confirmed it was set. Future sessions using the skill need the same environment variable.

## User Preferences

**Explicit scope direction:** User explicitly requested: "Yes - /design-review-team" when offered continuation from the handoff. No ambiguity about what was wanted.

**Durable record preference:** User requested saving to `docs/audits/` — prefers audit artifacts committed to the repo for traceability. The audit report is the deliverable, not the workspace findings.

**Workspace cleanup preference:** User requested cleanup of `.design-review-workspace/` after the report was saved to `docs/audits/`. Prefers clean repo state — working artifacts are intermediate, not permanent.

**Counter-review pattern (from prior sessions, still applicable):** User provides structured counter-review with priority levels ([P1], [P2]), specific file:line references, "why it matters" explanations, and concrete required changes. Follows the same adversarial review format as full design reviews.

**Separation of concerns between review rounds (from prior sessions, still applicable):** User counter-reviews proposals before editing. Pattern: (1) Claude proposes, (2) user counter-reviews, (3) Claude tightens, (4) repeat until accepted, (5) THEN edit the draft.
