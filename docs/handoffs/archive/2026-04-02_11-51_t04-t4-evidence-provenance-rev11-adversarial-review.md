---
date: 2026-04-02
time: "11:51"
created_at: "2026-04-02T15:51:06Z"
session_id: f968262b-e941-4f13-829a-37f65cb8f933
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_02-23_t04-t4-evidence-provenance-rev8-adversarial-review.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 8e59b072
title: "T-04 T4 evidence provenance — revisions 9-11, adversarial review cycle"
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
  - packages/plugins/cross-model/references/context-injection-contract.md
  - packages/plugins/cross-model/references/consultation-contract.md
  - packages/plugins/cross-model/scripts/event_schema.py
---

# Handoff: T-04 T4 evidence provenance — revisions 9-11, adversarial review cycle

## Goal

Close gate G3 (evidence provenance retention) — the last remaining hard gate before T6 (composition check) can begin. G1, G2, G4, G5 are `Accepted (design)`. G3 requires: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface. The risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:67` governs G3.

**Trigger:** Previous session (handoff archived at `docs/handoffs/archive/2026-04-02_02-23_t04-t4-evidence-provenance-rev8-adversarial-review.md`) left revision 8 awaiting adversarial review. This session received that review and iterated through revisions 9, 10, and 11.

**Stakes:** All 5 hard gates must reach `Accepted (design)` before T6 composition check can start (`risk-register.md:79-81`). T4 is the parallel prerequisite that designs how evidence flows through the dialogue loop.

**Success criteria:** User accepts the T4 design contract. G3 moves to `Accepted (design)`.

**Pattern:** Claude drafts, user provides adversarial review with Critical/High severity ratings, specific file:line evidence, and required changes. Three review cycles completed this session. Revision 11 is awaiting review.

## Session Narrative

### Revision 8 review → Revision 9: Propagation completeness, authority grounding, schema/scope

Session began by loading the prior handoff and receiving the user's adversarial review of revision 8. The review contained 3 critical, 4 high, 3 medium findings, 2 hidden dependencies. The criticals were:

1. **Dead-referent `revised` claims kept dual semantic state** — rev 8 fixed the dual-state problem for `reinforced` but explicitly exempted `revised` at T4#L224: "no change needed (already enters Phase 2 as `revised`)." The user demonstrated this creates the identical dual state: "new" for identity, "revised" for counters and synthesis trajectory.

2. **Authoritative omission surface not contractually grounded** — the word "authoritative" appeared in 4 places without qualification, while §3.9 admitted transcript fidelity was only a prerequisite the benchmark didn't yet guarantee. The user: "amend the benchmark contract first... or stop calling the diff authoritative."

3. **Safety/containment gap for direct tools** — T4 replaced helper-era `execute_scout` (which had truncation/redaction at `context-injection-contract.md:665-683`) with direct Glob/Grep/Read but defined no containment model. The benchmark treats forbidden-path leakage as a hard safety failure at `benchmark.md:145`.

Rev 9 was a major structural expansion (951→1232 lines). Key moves:
- Extended Phase 1.5 reclassification to both `reinforced` and `revised`
- Made "authoritative" conditional on §3.9 throughout; elevated transcript fidelity to blocking external dependency
- Added §4.6 "Direct-tool containment contract" with pre-execution confinement, post-containment capture model, and safety interaction
- Added §4.7 "Claim-class scope" with scoutable/relational-scoutable/not-scoutable
- Changed synthesis→record join from informal to `evidence_map` in pipeline-data
- Made harness compute mechanical diff by default (not gated on match_digest)
- Added `scout_budget_spent` for abandoned-round budget
- Fixed SHOULD→MUST for query diversity with objective criteria
- Relaxed round budget from 2-3 to 2-5
- Split helper-era migration claim into T4-replaces + T5-external-blockers

### Revision 9 review → Revision 10: Wiring prose into state model

User's review of rev 9 found 1 critical, 4 high, 1 medium. The shift: rev 8 had design problems, rev 9 had **prose-without-wiring** problems. The fixes existed conceptually but weren't encoded in the state model.

Key findings:
1. **`not_scoutable` was prose-only** — §4.7 said claims get `ambiguous` with `reason: "not_scoutable"` but `VerificationEntry` had no reason field, target selection still retried `ambiguous`, no `EvidenceRecord` could encode it. Critical.
2. **`evidence_map` keyed by `claim_key` not deterministic** — `claim_key` not unique across merged/paraphrased claims. High.
3. **Abandoned rounds only consumed claim-local budget** — `scout_attempts += 1` but not `evidence_count`. Global budget still keyed off completed evidence only. High.
4. **Containment cited benchmark tool-class restriction** — lines 93-94 restrict tools, not scope roots. Actual immutable scope is `scope_envelope` in consultation contract. High.
5. **Transcript-fidelity blocker had no owner** — named as blocked but with no landing surface, target doc, or verification criteria. Medium.

Rev 10 fixes (1232→1398 lines):
- Wired `not_scoutable` as terminal verification status in §3.4 enum, lifecycle table, and target selection skip
- Added objective classification criteria (3 conditions) and adjudicator audit
- Changed `evidence_map` from `claim_key` to `ClaimRef` key; added synthesis checkpoint `[ref:]` annotations
- Added `scout_budget_spent` counter with `max_scout_rounds` gate to §3.5 working state
- Re-grounded §4.6 containment in `scope_envelope` from `consultation-contract.md:127-131`
- Removed blame-shifting "harness bug" language; declared safety dependency explicitly
- Assigned transcript-fidelity blocker to T7 with specific target files and normative edits
- Named `evidence_map` consumer (epilogue schema, parser, schema validation, checkpoint parser)

### Revision 10 review → Revision 11: Boundary completeness

User's review of rev 10 found 0 critical, 2 high, 1 medium. The shift: fixes worked within T4 but didn't fully propagate to adjacent contracts or cover all paths.

Key findings:
1. **Deterministic join stops at checkpoint boundary** — `[ref:]` worked for checkpoint claims, but free-text narrative claims fell back to "approximate content matching." Benchmark scores every factual claim, not just checkpoint entries. High.
2. **`not_scoutable` only applied to new extracted claims** — revised, forced-new, and reintroduction all still entered at `unverified`. Synthesis-format contract didn't know about the new status. High.
3. **Dual-budget accounting contradiction** — `scout_budget_spent` described as incrementing on round start AND in lifecycle entries (double-counting). Stale "one concept" sentence. Medium.

Rev 11 fixes (1398→1492 lines):
- Checkpoint completeness rule: every factual narrative claim MUST have a checkpoint entry with `[ref:]`. No approximate matching. Missing = synthesis defect
- `not_scoutable` scoutable/not-scoutable split added to ALL 4 registration paths (new, revised, forced-new, reintroduction)
- Synthesis-format contract updates declared as external blockers in §6.2 (checkpoint grammar, completeness rule, `not_scoutable` in claim/evidence trajectory)
- `scout_budget_spent` single increment point at step 5b. Removed from all lifecycle entries. "One concept" replaced with two-concept separation table

## Decisions

### Extend forced-new reclassification to `revised` claims (rev 9)

**Choice:** Both `reinforced` AND `revised` with dead referents reclassified to `status = "new"`, `claim_source = "extracted"` before any consumer sees them.

**Driver:** User's rev 8 review finding C1: "the same event is still 'new' for identity/evidence state but 'revised' for counters and claim trajectory." The synthesis `validated_entry` surface at `dialogue-synthesis-format.md:7` builds claim trajectory from per-turn records — a `revised` claim with no living referent produces an incoherent trajectory entry.

**Rejected:** `revised` exempt from reclassification (rev 8) — creates identical dual-state problem that reclassification was designed to fix for `reinforced`.

**Implication:** T2/T3 input change declared for both `reinforced` and `revised`. Synthesis `validated_entry` trajectory also declared as affected surface.

**Trade-offs:** A genuine revision whose referent happens to be dead gets reclassified. Semantically correct — the claim is not revising anything that exists.

**Confidence:** High (E2) — the dual-state problem is structurally identical to the `reinforced` case already fixed. Mechanically demonstrable.

**Reversibility:** Low — reclassification is entangled with T2/T3 counter computation and synthesis trajectory.

**Change trigger:** If T3 gains a mechanism to prevent referential claims from targeting conceded occurrences upstream, dead-referent forced-new becomes unnecessary.

### Make authoritative language conditional on transcript fidelity (rev 9)

**Choice:** Every "authoritative" claim in the document is qualified with "given transcript fidelity (§3.9)." Transcript fidelity elevated from "prerequisite" to blocking external dependency with specific normative requirements.

**Driver:** User's rev 8 review finding C2: "the draft itself admits transcript fidelity is only a prerequisite, not an existing guarantee." The benchmark at `benchmark.md:95` says "retain the raw run transcript" with no normative definition of "raw" or "untruncated."

**Rejected:** Unconditional "authoritative" claims (rev 8) — authority without contractual foundation.

**Implication:** T4 implementation gated until benchmark contract specifies untruncated tool output normatively. Degradation path declared: without it, audit degrades to "verifiable up to the evidence block."

**Trade-offs:** T4 cannot be implemented until an external contract change lands. This is the correct trade-off — implementing with ungrounded authority claims is worse.

**Confidence:** High (E2) — the benchmark contract text is clear about what it does and doesn't say.

**Reversibility:** High — once the benchmark contract is amended, conditional language can be removed.

**Change trigger:** Benchmark contract amendment with normative transcript fidelity clause.

### Direct-tool containment contract (rev 9)

**Choice:** Add §4.6 defining pre-execution confinement, post-containment capture, and the meaning of "raw" in the provenance story ("unprocessed by the agent, not unfiltered by the harness").

**Driver:** User's rev 8 review finding C3: "you cannot promise full raw output in the transcript and also promise no forbidden-path or secret leakage without an explicit containment/redaction contract."

**Rejected:** No containment model (rev 8) — left safety and provenance in tension. Also rejected: citing benchmark tool-class restriction (lines 93-94) as scope-root authority — those lines restrict tools, not scope. Actual immutable scope is `scope_envelope` from `consultation-contract.md:127-131` (fixed in rev 10).

**Implication:** Transcript captures post-containment output. Containment is deterministic (scope roots immutable per benchmark row). Mechanical diff operates on post-containment output. Secret redaction within allowed scope declared as explicit external blocker owned by T7.

**Trade-offs:** Post-containment output is not "raw" in the strictest sense. Accepted because containment is harness-level, not agent-level — the agent cannot influence what containment filters.

**Confidence:** High (E2) — the tension between safety and provenance is structurally clear. Containment resolves it without compromising either.

**Reversibility:** Low — deeply embedded in the provenance model.

**Change trigger:** If the benchmark defines a different containment model or if secret redaction within allowed scope changes the provenance requirements.

### `not_scoutable` as terminal verification status (rev 10)

**Choice:** Add `not_scoutable` to the `VerificationEntry` status enum. Terminal state entered at Phase 2 registration, excluded from target selection (priority 4 skip). No `EvidenceRecord` created. Objective classification criteria: agent must be able to identify (1) entity fitting grammar, (2) definition query, (3) falsification query — if any missing, claim is `not_scoutable`.

**Driver:** User's rev 9 review finding C1: the `not_scoutable` path existed only in §4.7 prose. `VerificationEntry` had no field for it, target selection still retried `ambiguous` claims.

**Rejected:** `not_scoutable` as prose-only `ambiguous` with reason field (rev 9) — `VerificationEntry` had no reason field, target selection retried. Also rejected: `not_scoutable` only for new extracted claims (rev 10) — revised, forced-new, and reintroduction all missed.

**Implication:** All 4 registration paths (new, revised, forced-new, reintroduction) have scoutable/not-scoutable split. Adjudicator audits all classifications. `not_scoutable` claims MUST appear in scored synthesis (agent cannot suppress via classification). Synthesis-format contract needs update (declared as external blocker in §6.2).

**Trade-offs:** Adds complexity to every claim registration path. Accepted because the alternative (hard claims silently entering the `unverified`→scout cycle they can't benefit from) wastes budget and produces formally compliant but substantively useless evidence.

**Confidence:** Medium (E1) — classification criteria are logically sound but untested. Gaming risk (over-classifying to avoid scouting) mitigated by adjudicator audit.

**Reversibility:** Medium — removing requires collapsing all lifecycle paths back to single entry, removing from target selection, and removing synthesis-format contract dependency.

**Change trigger:** If benchmark results show systematic misclassification, tighten criteria or add deterministic rules per claim class.

### Checkpoint completeness rule (rev 11)

**Choice:** Every factual claim in the synthesis narrative MUST have a corresponding checkpoint entry with a `[ref:]` annotation. The checkpoint is the completeness surface for evidence linkage, not just a summary. Missing entry = synthesis defect flagged by harness.

**Driver:** User's rev 10 review finding H1: "checkpoint claims get a structured ClaimRef join, but any factual claim written only in the narrative still falls back to approximate content matching."

**Rejected:** Approximate content matching for free-text narrative claims (rev 10) — the benchmark scores every factual claim, including free-text. Non-deterministic provenance for scored claims is a design gap.

**Implication:** Strengthens existing checkpoint consistency rule from "must be consistent with narrative" to "must be complete relative to narrative's factual claims." The synthesis assembler (agent) bears the burden. A missing checkpoint entry is detectable and already penalized by the adjudicator.

**Trade-offs:** Agent must now ensure 100% checkpoint coverage of factual claims. Harder synthesis assembly. Accepted because the alternative (non-deterministic provenance for some scored claims) undermines the entire evidence chain.

**Confidence:** Medium (E1) — logically sound but checkpoint-completeness has never been verified against real synthesis assembly.

**Reversibility:** High — the rule is a constraint on synthesis assembly, not a structural change to the evidence model.

**Change trigger:** If benchmark results show systematic checkpoint incompleteness, add harness-side enforcement rather than relaxing the rule.

### Single increment point for `scout_budget_spent` (rev 11)

**Choice:** `scout_budget_spent` increments exactly once per round at step 5b (first tool call). NOT in lifecycle entries. Lifecycle tracks claim-local state only (`scout_attempts`).

**Driver:** User's rev 10 review finding M1: rev 10 incremented `scout_budget_spent` in lifecycle entries (Evidence stored, not_found stored, Pending round) AND described it as incrementing on round start — double-counting.

**Rejected:** Incrementing in lifecycle entries (rev 10) — a completed round would increment at 5b (start) and again in lifecycle (completion).

**Implication:** Two separate accounting concepts with clearly separated concerns: evidence budget (`evidence_count`, drives synthesis/analytics/pipeline-data) and effort budget (`scout_budget_spent`, internal guardrail only). `scout_count` in pipeline-data maps to evidence budget only.

**Trade-offs:** None — this is a bug fix, not a trade-off.

**Confidence:** High (E2) — double-counting is mechanically demonstrable.

**Reversibility:** High — accounting rule change only.

**Change trigger:** None — fixing double-counting is unconditionally correct.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — T4 design contract

**Status:** Untracked (not committed). 1492 lines. Revision 11.

**Purpose:** Design contract for scouting position and evidence provenance in the T-04 benchmark-first local dialogue loop. Governs gate G3.

**Key structural additions in rev 9-11:**
- §4.6 "Direct-tool containment contract" — pre-execution confinement, post-containment capture, safety interaction, allowed-scope safety dependency
- §4.7 "Claim-class scope" — scoutable/relational-scoutable/not-scoutable with terminal status, classification criteria, adjudicator audit, synthesis policy
- §6.2 "External blockers for `agent_local` mode" — T5 migration set, transcript fidelity (T7), allowed-scope safety (T7), synthesis-format contract updates (T7), `evidence_map` consumer (T7)

**Key state model changes in rev 9-11:**
- `not_scoutable` added to `VerificationEntry` status enum (terminal)
- `scout_budget_spent` added to agent working state with two-surface budget model
- `evidence_map` in pipeline-data keyed by `ClaimRef` (not `claim_key`)
- Synthesis checkpoint carries `[ref:]` annotations with checkpoint completeness rule
- Entity grammar extended: `<entity> × <entity>` for relational claims

**Growth trajectory:** 951 (rev 8) → 1232 (rev 9) → 1398 (rev 10) → 1492 (rev 11). The growth is primarily new sections (§4.6, §4.7, §6.2), rejected alternatives (7.31-7.43), and verification items (35-48).

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Not committed — the file is untracked.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop (updated from rev 8)

| Layer | Step | Evidence interaction |
|-------|------|---------------------|
| 1 | Extract semantic data | Claims extracted from Codex response |
| 2a | Phase 1: status changes | Concessions remove from verification_state; reinforcements resolve referents |
| 2b | Phase 1.5: reclassification | Dead-referent claims (`reinforced` AND `revised`) reclassified to `new`. Not-scoutable classification applied |
| 2c | Phase 2: registrations | New/revised claims checked for same-text merger against live occurrences. Scoutable → `unverified`. Not scoutable → `not_scoutable` (terminal) |
| 3 | Compute counters | T2 counter computation (reclassified claims visible here) |
| 4 | Control decision | T1 ControlDecision — conclude/continue/scope_breach |
| 5a | Target selection | Priority: unverified(0) > conflicted(<2) > ambiguous(<2) > skip (terminal states incl. `not_scoutable`) |
| 5b | Tool execution | `scout_budget_spent += 1` here. 2-5 calls: definition + falsification mandatory. Post-containment capture |
| 5c | Assessment | Disposition from full post-containment output; citation selection with polarity preservation |
| 5d | Record creation | EvidenceRecord created, verification state updated, `scout_attempts += 1` |
| 5e | Atomic commit | Evidence block re-emitted (captured in transcript) |
| 6 | Follow-up composition | Uses evidence record (entity, disposition, citations) |
| 7 | Send follow-up | Codex receives evidence-grounded question |

### Key contract surfaces and their T4 interactions (updated)

| Surface | Location | T4 interaction |
|---------|----------|---------------|
| Follow-up evidence shape | `codex-dialogue.md:421-429` | Requires snippet + provenance + disposition + question |
| Pipeline-data scout_count | `dialogue-synthesis-format.md:150` | Maps to `evidence_count`. NOT `scout_budget_spent` |
| Pipeline-data evidence_map | New (§5.2) | `ClaimRef`-keyed map of record indices. T7 consumer |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | Keys off `turn_history.scout_outcomes`. Record index included per entry |
| Claim trajectory | `dialogue-synthesis-format.md:16` | Needs `not_scoutable` in vocabulary (§6.2 blocker) |
| Synthesis checkpoint | `dialogue-synthesis-format.md:126-134` | Needs `[ref:]` annotations and completeness rule (§6.2 blocker) |
| T2 counter computation | `t2:152-161` | `new_claims = count(status == "new")`. Forced-new reclassification feeds into this |
| Benchmark scoring | `benchmark.md:118-119` | Scores final synthesis. No evidence data in scored artifact |
| Benchmark safety | `benchmark.md:145` | Forbidden-path leakage = safety failure. Containment required |
| Scope envelope | `consultation-contract.md:127-131` | Immutable `allowed_roots` set at delegation time. Authority for containment |
| T5 mode migration | `event_schema.py:137`, `dialogue-synthesis-format.md:86,144`, `SKILL.md:435` | `VALID_MODES` still only `server_assisted`/`manual_legacy`. External blocker |

### Two budget surfaces (new in rev 10, fixed in rev 11)

| Surface | Counter | Gate | Drives | Pipeline-data |
|---------|---------|------|--------|---------------|
| Evidence budget | `evidence_count` (`len(evidence_log)`) | `evidence_count >= max_evidence` | Synthesis trajectory, analytics, `scout_count` | Yes |
| Effort budget | `scout_budget_spent` | `scout_budget_spent >= max_scout_rounds` | Effort gate only | No (internal) |

`scout_budget_spent` increments exactly once at step 5b. NOT in lifecycle entries. `max_scout_rounds = max_evidence + 2`.

### External blockers enumerated (§6.2)

| Category | Owner | Count | Key items |
|----------|-------|-------|-----------|
| T5 migration set | T5 | 5 | Mode enum, synthesis format, dialogue skill, tests |
| Transcript fidelity | T7 | 4 | Normative clause, parseable format, transcript parser, diff engine |
| Allowed-scope safety | T7 | 2 | Secret handling policy, redaction/provenance interaction |
| `evidence_map` consumer | T7 | 4 | Epilogue schema, parser, schema validation, checkpoint parser |
| Synthesis-format updates | T7 | 4 | Checkpoint grammar `[ref:]`, completeness rule, `not_scoutable` in claim/evidence trajectory |

## Context

### Mental Model

This is a **contract convergence problem with adversarial review as the tightening mechanism**. The T4 design contract must satisfy multiple governing contracts simultaneously (benchmark spec, T1 termination, T2/T3 counters, T5 mode strategy, synthesis format, follow-up composition, consultation contract). Each adversarial review cycle finds interactions the draft mishandles, and the fixes are traced to specific contract surfaces.

**Convergence trajectory across this session:** Rev 8 had fundamental propagation failures (dead-referent dual-state, ungrounded authority claims, no containment). Rev 9 had prose-without-wiring problems (new concepts described but not encoded in the state model). Rev 10 had boundary-completeness problems (fixes worked within T4 but didn't fully propagate to adjacent contracts or all paths). Rev 11 has potential issues pending review — the user will share findings next session.

The convergence is clear from the severity pattern: rev 8→9 had 3 critical, rev 9→10 had 1 critical, rev 10→11 had 0 critical. Issues are becoming more targeted and less structural.

### Project State

T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). Critical path: T2→T3→T6→T7→T8. T4 is a parallel prerequisite for T6.

Gate status:
| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 11 under review)** | **T4: scouting position and evidence provenance** |

## Learnings

### Authority claims require contractual foundations, not assumptions

**Mechanism:** The word "authoritative" in a design document means nothing if the contract it depends on doesn't guarantee the required properties. The benchmark says "retain raw run transcript" but doesn't define "raw" or "untruncated."

**Evidence:** Rev 8 used "authoritative" in 4 places. User's review: "the draft itself admits transcript fidelity is only a prerequisite, not an existing guarantee."

**Implication:** Authority claims must be conditional until the upstream contract is amended. Better to declare a blocking dependency than to claim authority you don't have.

**Watch for:** Any design that says "X is authoritative because Y exists" — verify that Y's contract actually guarantees what's needed.

### Prose without wiring is not a contract

**Mechanism:** A design section that says "claims classified as X" is not a contract if the state model has no field for X, the lifecycle has no path for X, and target selection doesn't know about X.

**Evidence:** Rev 9's `not_scoutable` existed only in §4.7 prose. `VerificationEntry` had no status for it, target selection retried `ambiguous` claims, no `EvidenceRecord` could encode it.

**Implication:** Every design concept must be wired into: (1) the state model (types/enums), (2) the lifecycle table (transitions), (3) all consumers (target selection, synthesis, pipeline-data). If any is missing, the concept is prose, not contract.

**Watch for:** New features described in their own section but not propagated to the existing state model and lifecycle.

### Fixes must cover ALL paths through the state model

**Mechanism:** When adding a new status/classification to a state model, every path that creates entries must be updated. Missing even one path creates a loophole.

**Evidence:** Rev 10 added `not_scoutable` for "New extracted claim" but missed: revised claims (new occurrence), forced-new (dead referent), reintroduction after concession. All three entered at `unverified` regardless.

**Implication:** When adding a status/classification, enumerate ALL lifecycle events that create entries and add the split to each one. Don't assume "the most common path" is sufficient.

### Budget surfaces serving different purposes must have separate increment points

**Mechanism:** When two counters serve different purposes (evidence quality vs effort control), they must increment at different points in the lifecycle. Incrementing both in the same lifecycle event causes double-counting.

**Evidence:** Rev 10 incremented `scout_budget_spent` in lifecycle entries (Evidence stored, not_found stored, Pending round) AND described it as incrementing on round start. A completed round would increment at both points.

**Implication:** Define exactly one increment point per counter. Lifecycle tables track claim-local state only. Conversation-wide counters have their own increment point in the loop, not in the lifecycle.

### Deterministic joins require completeness surfaces, not approximate matching

**Mechanism:** A deterministic join from prose to structured data requires the prose surface to be complete — every relevant item must have a structured counterpart. Approximate content matching is not deterministic.

**Evidence:** Rev 10's `[ref:]` annotations worked for checkpoint claims but free-text narrative claims fell back to "approximate content matching." The benchmark scores every factual claim.

**Implication:** The checkpoint completeness rule (rev 11) eliminates the approximate path by requiring every factual claim to have a checkpoint entry. Missing entry = synthesis defect, not a design gap.

## Next Steps

### 1. Await user's adversarial review of revision 11

**Dependencies:** None — draft is ready.

**What to read first:** The current T4 design contract at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (1492 lines, revision 11). Key sections to verify:
- §3.4 lifecycle table: all 4 registration paths have scoutable/not-scoutable split
- §3.5 working state: two budget surfaces with single increment point at 5b
- §4.7 claim-class scope: terminal status, objective criteria, adjudicator audit, synthesis policy
- §5.2: checkpoint completeness rule, ClaimRef-keyed evidence_map, [ref:] annotations
- §6.2: all external blockers with owners and targets

**Expected:** User stated "next session I will share my review findings." If Accept → promote G3. If Reject → revision 12.

**Approach:** For each finding, trace the specific contract interaction and fix it. The convergence pattern suggests rev 11 is close — the remaining issues (if any) should be about boundary completeness, not design correctness.

### 2. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 3. Consider committing the T4 design contract

**Note:** The T4 file is currently untracked on branch `docs/t04-t4-scouting-and-evidence-provenance`. 1492 lines, revision 11. Consider committing after acceptance (or before, to preserve revision history). The branch has multiple commits ahead of origin.

## In Progress

**In Progress:** T4 design contract revision 11, awaiting adversarial review.

- **Approach:** Iterative adversarial review — Claude drafts, user reviews with structured findings, Claude revises.
- **State:** Draft complete. 1492 lines. Three review cycles completed this session (rev 8→9→10→11). Not committed.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) has stabilized since rev 6/7. The identity model (merger, concession, referent resolution, forced-new reclassification for both types) reached consistency in rev 9. The state model wiring (`not_scoutable` terminal status, two-surface budget, ClaimRef-keyed evidence_map) reached consistency in rev 11.
- **Not working / uncertain:** Whether the checkpoint completeness rule is achievable in practice (agent must ensure every factual narrative claim has a checkpoint entry). Whether the `not_scoutable` classification criteria are tight enough to prevent gaming. Whether the synthesis-format external blockers will be accepted by T7.
- **Open question:** Will the user find new boundary-completeness issues in rev 11?
- **Next action:** Wait for user's review of rev 11. Address findings if Reject. Promote G3 if Accept.

## Open Questions

1. **Is the checkpoint completeness rule achievable in practice?** The agent must now ensure 100% coverage of factual claims in the checkpoint. This is a new synthesis assembly burden. Untested against real synthesis assembly.

2. **Are the `not_scoutable` classification criteria tight enough?** An agent is incentivized to over-classify hard claims. The adjudicator audit mitigates this, but there's no harness-side enforcement during the run itself.

3. **Will the synthesis-format external blockers be accepted?** §6.2 declares 4 synthesis-format updates (checkpoint grammar, completeness rule, `not_scoutable` in two trajectory sections) as T7 blockers. These require changes to a contract that T4 doesn't own.

4. **Should the T4 contract be committed before acceptance?** Currently untracked. 1492 lines. Committing would preserve revision history but the file may need more revisions.

5. **Document size concern.** 1492 lines and growing. After acceptance, modular split would help. `/superspec:spec-writer` was mentioned in the prior handoff.

## Risks

### Rev 11 may still have boundary-completeness issues

The convergence pattern (3 critical → 1 critical → 0 critical) suggests design-level issues are resolved, but boundary-completeness issues (propagation to adjacent contracts, all paths covered) may persist.

**Mitigation:** The user's adversarial reviews are thorough. Each cycle finds fewer and more targeted issues.

### External blocker set is large and T7-heavy

§6.2 now has 19 external blockers, 15 of which are owned by T7. T4 implementation is gated on many of these. If T7 is slow to deliver, T4 stays blocked.

**Mitigation:** The blockers are correctly identified — better to have them visible than hidden. Some (transcript fidelity, safety) are truly blocking; others (evidence_map consumer, checkpoint parser) could be deferred to implementation phase.

### 1492-line document is unwieldy

Each revision adds rejected alternatives, verification items, and rationale. The document has grown 57% in this session (951→1492).

**Mitigation:** Post-acceptance, use /superspec:spec-writer to create a modular structure. The growth is proportionate to the number of contract interactions being resolved.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 11) |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 authority, gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation, claim_source |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry, normalization, claim_key |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition, migration set |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules, artifact requirements, safety |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Pipeline-data, scout_outcomes, checkpoint grammar |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope (immutable scope roots) |
| Context-injection contract | `packages/plugins/cross-model/references/context-injection-contract.md` | Helper-era truncation/redaction surfaces (severed by agent_local) |
| Event schema | `packages/plugins/cross-model/scripts/event_schema.py` | VALID_MODES (still missing agent_local) |

## Gotchas

### Line-number references in reviews can be version-stale

The user prepares reviews against a specific revision. If Claude writes a new revision before the review arrives, line numbers may be stale. Cross-check line numbers against the ACTUAL file content before addressing findings.

### Containment source is consultation contract, not benchmark

The benchmark restricts tool classes (Glob/Grep/Read) at lines 93-94. The actual immutable scope roots come from `scope_envelope` in `consultation-contract.md:127-131`. Rev 9 incorrectly cited the benchmark; rev 10 fixed this.

### Phase ordering is deterministic but easy to break

Within-turn claim processing order matters when concessions and registrations can interact. Two-phase processing (Phase 1: status changes, Phase 1.5: reclassification, Phase 2: registrations with scoutable classification) makes results deterministic. Adding a new claim kind must update ALL three phases.

### Budget model has two surfaces with different purposes

`evidence_count` (pipeline-data visible, drives analytics) vs `scout_budget_spent` (internal only, effort guardrail). Don't confuse them. The lifecycle table only touches `scout_attempts` (claim-local). `scout_budget_spent` increments at step 5b only.

### `not_scoutable` applies to ALL registration paths

New, revised (new occurrence), forced-new (dead referent), and reintroduction after concession all have scoutable/not-scoutable split. Missing any path creates a loophole where hard-to-scout claims enter the scout cycle.

## User Preferences

**Review pattern:** User provides structured adversarial reviews with consistent format: Critical Failures, High-Risk Assumptions, Real-World Breakpoints, Hidden Dependencies, Required Changes. Each finding has: flaw description with file:line references, "Why it matters" (contract impact), "How it fails in practice" (concrete failure mode), severity, "What must change" (specific required fix).

**Rigor expectation:** Every finding has specific evidence. The user catches subtle contract interactions — forced-new creating dual semantic state, revised claims escaping merger, not_scoutable lacking state model wiring. Hand-waving is consistently rejected.

**Structural solutions preferred:** User prefers design fixes over acknowledged limitations. Rev 9's `not_scoutable` as prose was rejected for lack of wiring. Rev 10's `evidence_map` keyed by `claim_key` was rejected for non-determinism.

**Clean separation valued:** The evidence-out-of-synthesis decision, the two-surface budget model, the lifecycle/conversation-wide counter separation — all validated by the user's acceptance pattern.

**Contract completeness expected:** Every surface that changes must be declared. Migration sets must be complete. Dependencies on future work must have owners, target docs, and verification criteria. Blockers without ownership are treated as design flaws.

**Convergence tolerance:** The user accepts iterative convergence. Three review cycles in one session, each finding fewer and more targeted issues. The verdict pattern (Major revision → Major revision → Major revision) doesn't mean lack of progress — the severity pattern (3 critical → 1 critical → 0 critical) shows clear convergence.
