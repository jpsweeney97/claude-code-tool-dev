---
date: 2026-04-02
time: "02:23"
created_at: "2026-04-02T06:23:52Z"
session_id: f6191468-89e1-486a-b122-93d5919fec24
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_23-38_t04-gate-g4-mode-strategy-accepted.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 75946e49
title: "T-04 T4 evidence provenance — revision 8, adversarial review cycle"
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
---

# Handoff: T-04 T4 evidence provenance — revision 8, adversarial review cycle

## Goal

Close gate G3 (evidence provenance retention) — the last remaining hard gate before T6 (composition check) can begin. G1, G2, G4, G5 are `Accepted (design)`. G3 requires: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface. The risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:67` governs G3. Related risks: J (evidence retention), D (scouting timing), F (compression), E (simplification).

**Trigger:** G3 was the last remaining gate. Previous session completed T5 (mode strategy), moving G4 to accepted. This session is the T4 design contract iterative review cycle.

**Stakes:** All 5 hard gates must reach `Accepted (design)` before T6 composition check can start (`risk-register.md:79-81`). T4 is the parallel prerequisite that designs how evidence flows through the dialogue loop.

**Success criteria:** User accepts the T4 design contract. G3 moves to `Accepted (design)`.

**Pattern switch:** The user changed the review pattern for this work: Claude drafts, user provides adversarial review. Previous sessions had the user drafting and Claude reviewing. The user provides structured reviews with Critical/High severity ratings, specific file:line evidence, and required changes. Verdicts so far: Reject on every revision through rev 7/7.1. Rev 8 is awaiting review.

## Session Narrative

This session was a single continuous adversarial review cycle over the T4 design contract. The document went through revisions 5 → 6 → 6.1 → 7 → 7.1 → 8, driven by the user's structured reviews with increasing specificity.

### Rev 5 → Rev 6: The synthesis-boundary fix

Session began with the user's review of rev 5 (drafted in the prior session). Three critical failures, all tracing to one root cause: trying to route evidence through the scored synthesis artifact. The `<!-- evidence-data -->` JSON block embedded in the synthesis would contaminate claim inventory, inflate `citation_count`, and create safety-violation risk. Tier-3 snippet recovery reads violated the single capture point. Error-path export assumed synthesis would succeed even on T1 `error` termination.

Rev 6 was a structural rewrite. Key moves: evidence persists through the run transcript (not synthesis), single capture point is absolute (no recovery reads), same-text same-key merger replaces recency fallback, unresolved-item scouting added as secondary target type, `candidate_matches` added for structured audit. These moves survived — the transcript-based approach and no-recovery-reads rule have held through all subsequent revisions.

### Rev 6 → Rev 6.1: Internal consistency fixes

User found 4 targeted issues: (1) same-text merger conflicted with concession lifecycle — a conceded occurrence would capture reintroduced claims via merger, (2) `evidence.json` not in the benchmark artifact set, (3) `candidate_matches` had no explicit emission surface in the transcript, (4) ScoutNotes invisible to synthesis evidence trajectory. Fixed with: concession exception ("live" occurrence check via verification_state membership), evidence.json contract gap acknowledged with two-tier authority, scouting assessment block defined, ScoutNote trajectory projection added.

### Rev 6.1 review → Rev 7: Feature removal

The user submitted a comprehensive review. I cross-checked line references against the actual revision 7 file (which I'd already written) and found 12 of 14 findings were already addressed. The two genuinely new findings were: (1) within-turn processing order for concession and resurrection not specified, (2) `evidence_log` to per-turn `scout_outcomes` projection not declared.

Key pivot in rev 7: **removed unresolved-item scouting entirely**. The user's review demonstrated 4 critical incompatibilities — follow-up contract requires evidence shape (snippet, provenance, disposition) that ScoutNotes lack; uncited ScoutNote.finding text contaminates scored synthesis; scout budget diverges from pipeline-data scout_count; synthesis trajectory expects evidence-shaped entries. Making it first-class would require a synthetic claim model. The complexity was disproportionate.

Also removed `candidate_matches` — agent-authored per-match polarity is self-reporting, not provenance. The audit mechanism is match_digest + raw output + human comparison.

Added: dead-occurrence exclusion in referent resolution, per-claim attempt limit (max=1), scout query coverage rule (entity-definition query mandatory), pending-round emission for interrupted rounds, atomic round commit (evidence block re-emission in step 5e).

### Rev 7.1: Two targeted fixes

Added within-turn two-phase processing (Phase 1: concessions before Phase 2: registrations) and declared the `evidence_log` → `scout_outcomes` projection with affected consumer (synthesis assembler).

### Rev 7/7.1 → Rev 8: Identity semantics and audit scaling

User's review of rev 7/7.1 found 3 critical, 4+ high issues. The criticals:

1. **Forced-new dual semantic state:** When a `reinforced` claim's referent is dead, T4 makes it "new" for identity but it stays `reinforced` for T2/T3 counters. One claim, two incompatible statuses.
2. **Revised claims escape merger:** The "different text by definition" assumption was wrong — extractor errors and convergent revisions can produce same-text revised claims, recreating the collision class the design claimed to have eliminated.
3. **match_digest breaks on large outputs:** Capped at 20 lines, single-file format. On broad greps across multiple files, contradictory uncited lines hide beyond the cap.

The high findings: attempt limit too rigid (max=1 freezes hard claims), query coverage too weak (single definition query satisfiable with minimal effort), migration set incomplete (only synthesis assembler declared, not follow-up/evidence surfaces), transcript fidelity outsourced to T7 clarification.

Rev 8 fixes: (1) forced-new reclassification — dead-referent `reinforced` claims reclassified to `new` before T2/T3 processing (declared T2/T3 input change), (2) merger extended to revised claims — convergent re-expression merges, (3) authoritative omission surface is mechanical diff (raw output minus citations) computable by harness without agent self-report, (4) graduated attempt limit (1 for `not_found`, 2 for `conflicted`/`ambiguous`), (5) two mandatory query types (entity-definition AND falsification), (6) full helper-era migration enumeration in §6.1, (7) transcript fidelity as benchmark-contract prerequisite with explicit degradation path.

## Decisions

### Evidence persists through transcript, not synthesis artifact

**Choice:** Evidence data is NOT embedded in the scored synthesis. The audit chain uses the run transcript (evidence block re-emissions + raw tool output).

**Driver:** Benchmark scores the final synthesis (`benchmark.md:118-119`). Embedded JSON contaminates claim inventory, inflates `citation_count`, creates safety-violation risk if snippets contain sensitive material. User's rev-5 review: "trying to smuggle a machine artifact and a recovery mechanism through the scored synthesis instead of giving them their own clean contract."

**Rejected:** `<!-- evidence-data -->` block in synthesis epilogue (rev 5) — contaminated scoring surface. Evidence in `<!-- pipeline-data -->` (rev 3 era) — same problem.

**Implication:** The harness or reviewer must work with the transcript for evidence audit. The synthesis stays clean for scoring and safety review. `evidence.json` is an optional T7 convenience, not load-bearing.

**Trade-offs:** Audit requires transcript parsing rather than structured JSON in a known location. Acceptable because transcript is already required by benchmark spec.

**Confidence:** High (E2) — the failure mode (scoring contamination) is mechanically demonstrable; the fix (transcript-based) works with existing benchmark infrastructure.

**Reversibility:** Low — this is a foundational architectural choice. All subsequent design (audit chain, error paths, compression) builds on it.

**Change trigger:** If the benchmark spec defines a separate, non-scored artifact channel for machine data, evidence could move there instead of the transcript.

### No snippet recovery reads — single capture point absolute

**Choice:** When compression hits tier 3 (snippets dropped), the agent uses `path:line_range` coordinates without quoting code. No Read calls during synthesis.

**Driver:** G3 requires a single fixed capture point. Recovery reads during synthesis are a second evidence-gathering phase — not in evidence_log, not counted in scout_count, not governed by scope-breach semantics.

**Rejected:** Tier-3 recovery reads (rev 5) — violates G3. The adjudicator can verify by reading the cited file if needed.

**Implication:** Tier-3 synthesis citations are coordinate-only. Less rich, but auditable and consistent.

**Trade-offs:** B8 (8-turn benchmark task) will routinely hit tier 3. Synthesis citations will lack inline code quotes. Acceptable because the adjudicator has the cited files.

**Confidence:** High (E2) — the violation of G3 is structurally clear.

**Reversibility:** Low — deeply embedded in the compression and audit model.

**Change trigger:** If the benchmark introduces a non-scouting file-access mechanism for synthesis preparation.

### Removed unresolved-item scouting (rev 7)

**Choice:** Claim-only scouting. One-turn delay accepted.

**Driver:** Rev 6 review demonstrated 4 critical incompatibilities: (1) follow-up contract requires evidence shape ScoutNotes lack (`codex-dialogue.md:421-429`), (2) uncited findings contaminate scored synthesis, (3) scout budget diverges from pipeline-data scout_count, (4) synthesis trajectory expects evidence-shaped entries.

**Rejected:** Unresolved-item scouting as secondary target type (rev 6) — 4 contract breaks. Unresolved-item scouting as primary mechanism (rev 3 era) — even worse integration complexity.

**Implication:** One-turn delay on repo-verifiable questions. At most 20% of scout budget on a 6-turn run. Extension path preserved: `ScoutTarget = ClaimRef | QuestionRef` for future work.

**Trade-offs:** One wasted scout turn per question cycle. Accepted because making unresolved-item scouting first-class requires a synthetic claim model and T2/T3 changes — disproportionate for benchmark-first.

**Confidence:** High (E2) — the 4 contract breaks were individually demonstrated by the reviewer with specific file:line evidence.

**Reversibility:** Medium — adding it back requires the full evidence-surface integration (follow-up, synthesis, accounting).

**Change trigger:** If benchmark results show the one-turn delay materially degrades `supported_claim_rate`.

### Dropped candidate_matches (rev 7)

**Choice:** Agent-authored per-match polarity assessments are not provenance. Authoritative omission surface is the mechanical diff: raw tool output minus citations.

**Driver:** User's rev-6 review: "this is the agent's self-report masquerading as provenance." The agent can mislabel contradictory matches as `neutral`, and downstream tooling preserves the story.

**Rejected:** Agent-authored `candidate_matches` in ScoutStep (rev 6) — self-report. Scouting assessment block as required transcript surface (rev 6.1) — same problem with added parsing complexity.

**Implication:** Audit requires comparing citations against raw tool output (both in transcript). The harness can mechanically compute uncited lines. No agent self-report is load-bearing.

**Trade-offs:** Reviewer workflow is slightly more manual — must reconstruct omissions from raw output rather than reading a pre-digested summary. Acceptable because the mechanical diff is more trustworthy.

**Confidence:** High (E2) — the trust model inversion is clear: provenance that requires re-auditing to verify doesn't save work.

**Reversibility:** High — adding a mechanical (not agent-authored) match classifier is a harness-side feature, not a T4 change.

**Change trigger:** If a mechanical harness-side tool can classify match polarity from raw output without agent involvement.

### Same-text merger extended to revised claims (rev 8)

**Choice:** Both `new` and `revised` claims subject to same-text same-key merger against live occurrences.

**Driver:** The "different text by definition" assumption for revised claims was wrong. Extractor errors produce duplicate revised claims; convergent revisions across turns produce same-text revised claims. Without merger, these create identical-text live collisions — the same class the design eliminated for `new` claims.

**Rejected:** Revised claims exempt from merger (rev 1-7) — creates the collision it was supposed to prevent.

**Implication:** A `revised` claim whose normalized text matches a live occurrence shares that occurrence's ClaimRef. The claim keeps its original `revised` status for T2/T3 counters (merger invisible to T2/T3).

**Trade-offs:** A genuine revision that happens to converge to existing text gets merged rather than creating a new identity. This is semantically correct — convergent re-expression is not a new truth condition.

**Confidence:** High (E2) — the failure mode (duplicate live occurrences) is the exact problem merger was designed to prevent. Extension to `revised` is logically necessary.

**Reversibility:** High — construction rules table change only.

**Change trigger:** If the extractor gains a mechanism to distinguish genuine convergent revisions from duplicate emissions.

### Forced-new reclassification for dead referents (rev 8)

**Choice:** When a referential claim's referent has no live occurrences, reclassify to `status = "new"`, `claim_source = "extracted"` before T2/T3 processing.

**Driver:** Without reclassification, a `reinforced` claim with a dead referent is simultaneously "new" for T4 identity and "reinforced" for T2/T3 counters. One claim, two incompatible semantic states. T2 counts `reinforced` differently from `new` — the counter mismatch is a contract violation.

**Rejected:** Keeping the claim as `reinforced` for T2/T3 (rev 7) — dual semantic state. Forbidding forced-new entirely (making dead-referent a hard error) — too restrictive, valid dialogue can concede and reassert.

**Implication:** This IS a T2/T3 input change (declared in §6). T2 counter computation sees a `new` claim where the extractor originally said `reinforced`. Correctly — the claim is functionally a fresh assertion when its referent no longer exists.

**Trade-offs:** The reclassification changes what T2/T3 see. Declared explicitly. The alternative (letting the dual state persist) is worse.

**Confidence:** High (E2) — the semantic inconsistency is mechanically demonstrable.

**Reversibility:** Medium — removing requires a different resolution for the dual-state problem.

**Change trigger:** If T3 gains a mechanism to prevent referential claims from targeting conceded occurrences upstream.

### Graduated attempt limit (rev 8)

**Choice:** `not_found` claims get 1 attempt, `conflicted`/`ambiguous` get 2.

**Driver:** Rev 7's flat `max_attempts = 1` froze hard claims after one shot. `conflicted` and `ambiguous` have real evidence — a second scout with different queries may clarify. `not_found` has nothing to find.

**Rejected:** Flat max=1 (rev 7) — too rigid, freezes inconclusive claims. No limit (rev 1-6) — allows budget monopolization.

**Implication:** Claims with real but inconclusive evidence get a second chance. `not_found` claims are correctly deprioritized immediately.

**Trade-offs:** Second attempts consume budget. On a 6-turn run with 5-6 claims, at most 1-2 claims will get re-scouted.

**Confidence:** Medium (E1) — the graduation logic is sound but untested against the benchmark corpus.

**Reversibility:** High — attempt limits are a parameter change.

**Change trigger:** If benchmark results show second attempts rarely change outcomes, revert to flat cap.

### Two mandatory query types: definition AND falsification (rev 8)

**Choice:** Each scouting round must include at least one entity-definition query and one falsification-oriented query.

**Driver:** Disposition from full output closes citation cherry-picking but not query-selection bias. A biased agent can search for confirming patterns, miss contradicting evidence elsewhere, and honestly report "full output contained no contradiction."

**Rejected:** Single definition-query rule (rev 7) — too weak, satisfiable with a token-compliant low-value query. No query constraint (rev 1-6) — no protection against systematic bias.

**Implication:** Scout rounds execute 2-3 calls. Two are mandatory types. `query_type` field in ScoutStep classifies each. Post-hoc auditing detects systematic bias across the benchmark corpus. Not foolproof (agent can craft weak falsification queries) but raises the bar.

**Trade-offs:** Adds complexity to scouting. Falsification queries for some claims are hard to formulate. Accepted because the alternative (no bias protection) is worse.

**Confidence:** Medium (E1) — the coverage requirement is logically sound but query quality depends on agent judgment.

**Reversibility:** High — instruction-level constraint, auditable post-hoc.

**Change trigger:** If benchmark results show systematic falsification query weakness, replace with claim-class-specific deterministic recipes.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — T4 design contract

**Status:** Untracked (not committed). 950 lines. Revision 8.

**Purpose:** Design contract for scouting position and evidence provenance in the T-04 benchmark-first local dialogue loop. Governs gate G3.

**Key sections:**
- §1 Decision (10 points)
- §2 Why This Direction (rationale for every design choice)
- §3 State Shape: occurrence registry with same-text merger + concession exception (§3.1), two-phase within-turn processing (§3.1.2), referent resolution with dead-occurrence exclusion (§3.1.1), ClaimRef (§3.2), EvidenceRecord/ScoutStep/CitationSpan with match_digest and query_type (§3.3), verification state model with scout_attempts (§3.4), agent working state (§3.5), compression-resistant evidence block with atomic commit (§3.6), pending-round emission (§3.7), transcript-based evidence persistence (§3.8), transcript fidelity prerequisite (§3.9)
- §4 Scouting Position: per-turn loop with 2a/2b/2c phases and 5a-5e scout substeps (§4.1), skip conditions (§4.2), target selection with graduated attempt limit (§4.3), query coverage rule with definition+falsification types (§4.4), scope breach (§4.5)
- §5 Synthesis: evidence trajectory with scout_outcomes projection (§5.1), aggregation (§5.2), transcript-complete audit chain with mechanical diff (§5.3)
- §6 Non-changes + declared T2/T3 input changes + helper-era migration enumeration (§6.1)
- §7 Rejected alternatives (30 items across 8 revisions)
- §8 Verification items (34 items)

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Not committed — the file is untracked.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop

| Layer | Step | Evidence interaction |
|-------|------|---------------------|
| 1 | Extract semantic data | Claims extracted from Codex response |
| 2a | Phase 1: status changes | Concessions remove from verification_state; reinforcements resolve referents |
| 2b | Phase 1.5: reclassification | Dead-referent claims reclassified to `new` |
| 2c | Phase 2: registrations | New/revised claims checked for same-text merger against live occurrences |
| 3 | Compute counters | T2 counter computation (reclassified claims visible here) |
| 4 | Control decision | T1 ControlDecision — conclude/continue/scope_breach |
| 5a | Target selection | Priority: unverified(0) > conflicted(<2) > ambiguous(<2) > skip |
| 5b | Tool execution | 2-3 calls: definition + falsification mandatory |
| 5c | Assessment | Disposition from full output; citation selection with polarity preservation |
| 5d | Record creation | EvidenceRecord created, verification state updated |
| 5e | Atomic commit | Evidence block re-emitted (captured in transcript) |
| 6 | Follow-up composition | Uses evidence record (entity, disposition, citations) |
| 7 | Send follow-up | Codex receives evidence-grounded question |

### Key contract surfaces and their T4 interactions

| Surface | Location | T4 interaction |
|---------|----------|---------------|
| Follow-up evidence shape | `codex-dialogue.md:421-429` | Requires snippet + provenance + disposition + question. ScoutNotes lacked these → removed |
| Pipeline-data scout_count | `dialogue-synthesis-format.md:150` | Maps to `len(evidence_log)`. One accounting concept |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | Keys off `turn_history.scout_outcomes`. T4 projects `evidence_log` by turn |
| T2 counter computation | `t2:152-161` | `new_claims = count(status == "new")`. Forced-new reclassification feeds into this |
| T3 registry | `t3:144-148` | `set[claim_key]` — existence only. T4 builds parallel occurrence registry |
| Benchmark scoring | `benchmark.md:118-119` | Scores final synthesis. No evidence data allowed in scored artifact |
| Benchmark transcript | `benchmark.md:95-96` | "retain raw run transcript." T4 interprets as untruncated tool output |
| T1 error boundary | `t1:§5.1 (line 136-151)` | Error when structured state invalid. Evidence persists via transcript independently |
| T5 agent_local | `t5:50-53` | No process_turn, no execute_scout, direct tools. T4 defines local scouting |
| Context-injection evidence_wrapper | `context-injection-contract.md:673` | Helper-era surface. Severed by agent_local, replaced by EvidenceRecord |

### Helper-era surfaces severed by agent_local (§6.1 migration table)

| Helper-era surface | T4 replacement |
|-------------------|---------------|
| `evidence_wrapper` in follow-up | Evidence block entry (entity, disposition, citations) |
| `evidence_wrapper` in `scout_outcomes` | `EvidenceRecord` (§5.1 projection) |
| `read_result` / `grep_result` storage | Raw tool output in transcript |
| `execute_scout` call | Direct Glob/Grep/Read |
| `scout_token` / `scout_option` | T4 target selection |
| `budget.scout_available` | `evidence_count >= max_evidence` |
| `template_candidates` | T4 verification state |

### Patterns discovered

- **Merger as identity unification:** Same-text same-key live occurrences merge to prevent evidence orphaning. Conceded occurrences excluded (verification_state membership check). Extended to both `new` and `revised` claims in rev 8.
- **Two-phase processing for deterministic identity:** Phase 1 (concessions) before Phase 2 (registrations) ensures merger checks see post-concession verification_state. Prevents ordering-dependent identity semantics.
- **Mechanical diff as audit authority:** Raw tool output minus citations = uncited lines. Computable by harness without agent self-report. match_digest is a convenience guide, not the authority.
- **Atomic round commit:** Evidence block re-emitted in step 5e (within scouting), not at end of turn. Error after 5e doesn't lose evidence. Interrupted rounds get pending-round markers.

## Context

### Mental Model

This is a **contract convergence problem**. The T4 design contract must satisfy multiple governing contracts simultaneously (benchmark spec, T1 termination, T2/T3 counters, T5 mode strategy, synthesis format, follow-up composition). Each adversarial review cycle tightens internal consistency by finding contract interactions the draft mishandles.

The convergence trajectory: rev 5 had fundamental architecture problems (evidence in synthesis), rev 6 introduced features that broke 4 contracts (unresolved-item scouting), rev 7 removed the broken features and strengthened the core, rev 8 fixed identity semantics and audit scaling. Each cycle finds fewer critical issues and they become more targeted — from "wrong architecture" to "wrong identity semantics in an edge case."

### Project State

T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). Critical path: T2→T3→T6→T7→T8. T4 is a parallel prerequisite for T6.

Gate status:
| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 8 under review)** | **T4: scouting position and evidence provenance** |

### Risk Register Context

G3 governs Risk J ("Evidence tracked only as counts, not as reusable provenance") at `risk-register.md:67`. Required control: "Persist per-scout evidence records: `{turn, target_claim, path, line_range, snippet, disposition}` at the fixed scout-capture point." T4's EvidenceRecord satisfies this with additional fields (entity, steps, match_digest, citations, query_type).

## Learnings

### Unresolved-item scouting as secondary mechanism breaks 4 contracts simultaneously

**Mechanism:** Lighter records (no disposition, no citations) are incompatible with consumers that expect evidence-shaped entries. The follow-up contract, synthesis scoring, pipeline-data accounting, and evidence trajectory all assume one evidence shape.

**Evidence:** Rev 6 review findings 1-4 each trace to a different contract surface that expects full evidence semantics.

**Implication:** Adding a secondary target type to a tightly coupled loop requires the secondary mechanism to satisfy the SAME contracts as the primary. Lighter alternatives that skip required fields create contract violations at every consumer.

**Watch for:** Future extension (`ScoutTarget = ClaimRef | QuestionRef`) must give questions full evidence treatment or route them through a completely separate channel.

### Agent-authored summaries are not provenance

**Mechanism:** `candidate_matches` with polarity assessments is the agent's self-report. A biased agent can label contradictory matches `neutral` and the downstream chain preserves the story. Provenance must be mechanically derivable or independently verifiable.

**Evidence:** Rev 7 review finding 6: "this makes the audit chain depend on model honesty at the exact point where the design claims rigor."

**Implication:** The authoritative audit surface must be computable from non-agent-authored sources. Raw tool output (authoritative) + citations (agent-selected) → mechanical diff = uncited lines. No self-report layer needed.

### Identity semantics must be consistent across all consumers

**Mechanism:** A claim that is `new` for identity but `reinforced` for counters has a dual semantic state. T2/T3 treat it as `reinforced` (no effect on `new_claims` count), but T4 treats it as a fresh assertion. The reclassification (Phase 1.5) makes them consistent.

**Evidence:** Rev 8 finding 1: "one claim now has two incompatible semantic states."

**Implication:** When T4 overrides extraction status (forced-new reclassification), the override must propagate to ALL consumers. Declaring the change isn't enough — it must happen before any consumer sees the claim.

### Merger rules must cover all registration paths

**Mechanism:** Same-text collision prevention only worked for `new` claims. `revised` claims were exempt ("different text by definition"). But the assumption was wrong — extractor errors and convergent revisions produce same-text revised claims.

**Evidence:** Rev 8 finding 2 demonstrated the failure path.

**Implication:** Any rule that prevents a class of errors must cover ALL paths that can introduce the error. "This path doesn't need the check because of an assumption" is fragile — verify the assumption holds for all inputs.

## Next Steps

### 1. Await user's adversarial review of revision 8

**Dependencies:** None — draft is ready.

**What to read first:** The current T4 design contract at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (950 lines, revision 8).

**Expected:** The user will provide a structured review with Critical/High findings, specific file:line evidence, and required changes. If the verdict is Reject, address findings and produce revision 9. If Accept, proceed to G3 promotion.

**Approach:** For each finding, trace the specific contract interaction and fix it. Check all cross-references to ensure internal consistency. The convergence pattern suggests rev 8 may be close to acceptance — the remaining issues are about identity semantics and audit scaling, not fundamental architecture.

### 2. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 3. Consider committing the T4 design contract

**Note:** The T4 file is currently untracked on branch `docs/t04-t4-scouting-and-evidence-provenance`. Consider committing after acceptance (or even before, to preserve revision history). The branch is 12+ commits ahead of origin — consider pushing.

## In Progress

**In Progress:** T4 design contract revision 8, awaiting adversarial review.

- **Approach:** Iterative adversarial review — Claude drafts, user reviews with structured findings, Claude revises.
- **State:** Draft complete. 950 lines. All 7 required changes from rev 7/7.1 review addressed. Not committed.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, one accounting concept) has stabilized since rev 6/7. The identity model (merger, concession, referent resolution, forced-new reclassification) reached consistency in rev 8.
- **Not working / uncertain:** Whether the graduated attempt limit (1 for not_found, 2 for conflicted/ambiguous) is well-calibrated. Whether the falsification query requirement is strong enough. Whether the mechanical diff audit surface satisfies the user's expectations for large-output auditability.
- **Open question:** Will the user find new contract interactions in rev 8 that need fixing?
- **Next action:** Wait for user's review of rev 8. Address findings if Reject. Promote G3 if Accept.

## Open Questions

1. **Is the graduated attempt limit well-calibrated?** The user's rev 7 review said max=1 was too rigid. Rev 8 offers max=2 for conflicted/ambiguous. This is untested against the benchmark corpus (which doesn't exist yet). May need adjustment during T8.

2. **Is the falsification query requirement enforceable enough?** The user's rev 7 review said query coverage was "too weak and openly unenforced." Rev 8 adds a second mandatory type. Post-hoc auditing detects bias across the corpus but can't prevent it in individual runs.

3. **Does the mechanical diff audit surface scale?** On large outputs (80+ matches across multiple files), the diff is mechanically complete but may be unwieldy for human reviewers. A harness-side summarization tool would help but is T7 scope.

4. **Should the T4 contract be committed before acceptance?** Currently untracked. Committing would preserve revision history in git. But the iterative review cycle may produce more revisions.

## Risks

### Rev 8 may introduce new issues while fixing old ones

Each revision cycle has introduced 1-2 new issues. Rev 6 added unresolved-item scouting (4 contract breaks). Rev 7 added flat attempt limit (too rigid). The forced-new reclassification and revised-claim merger in rev 8 may have similar blind spots.

**Mitigation:** The user's adversarial reviews are thorough. Each cycle finds fewer critical issues. The convergence trajectory is clear.

### Transcript fidelity is load-bearing but not contractually guaranteed

T4's audit chain depends on untruncated tool output in the transcript. The benchmark spec says "retain raw run transcript" but doesn't define "raw." If a harness implementation truncates, the mechanical diff audit surface breaks.

**Mitigation:** T4 declares this as a prerequisite with an explicit degradation path ("verifiable up to the evidence block"). T7 should clarify the benchmark contract.

### The design contract is 950 lines and growing

Each revision adds rejected alternatives, verification items, and rationale. The document is getting unwieldy for reference. After acceptance, a modular split would help.

**Mitigation:** Post-acceptance, use /superspec:spec-writer to create a modular structure.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 authority, gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation, claim_source |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry, normalization, claim_key |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules, artifact requirements, safety |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape, evidence_wrapper |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Pipeline-data, scout_outcomes, evidence trajectory |
| Context-injection contract | `packages/plugins/cross-model/references/context-injection-contract.md` | evidence_wrapper, scout tokens (helper-era) |

## Gotchas

### Line-number references in reviews can be version-stale

The user prepared one review against revision 6.1 after revision 7 had already been written. 12 of 14 findings referenced features that rev 7 had already removed. Cross-check line numbers against the ACTUAL file content before addressing findings — the review may be against a stale version.

### Merger must cover ALL registration paths

The "different text by definition" exemption for revised claims was wrong for 7 revisions. When adding a check to prevent a class of errors, verify the check covers every path that can introduce the error — not just the most common one.

### Phase ordering determines identity semantics

Within-turn claim processing order matters when concessions and registrations can interact. Two-phase processing (Phase 1: status changes, Phase 2: registrations) makes results deterministic. Without explicit phasing, same input can produce different identity based on claim list ordering.

## User Preferences

**Review pattern:** User provides structured adversarial reviews with consistent format: Critical Failures, High-Risk Assumptions, Real-World Breakpoints, Hidden Dependencies, Adversarial Attack Surface, Required Changes. Each finding has: flaw description with file:line references, "Why it matters" (contract impact), "How it fails in practice" (concrete failure mode), severity, "What must change" (specific required fix).

**Rigor expectation:** Every finding has specific evidence. The user catches subtle contract interactions — forced-new creating dual semantic state, revised claims escaping merger, match_digest failing on large outputs. Hand-waving ("accepted as edge case," "extractor error") is consistently rejected.

**Structural solutions preferred:** User prefers design fixes over acknowledged limitations. Rev 5's "recency accepted as edge case" was rejected. Rev 7's "max_attempts=1 covers all cases" was rejected. Rev 8's graduated limit and merger extension were the kind of structural solutions the user accepts.

**Clean separation valued:** The evidence-out-of-synthesis decision was immediately validated. The user called it "the right move" in the next review. Mixing concerns (machine data in scored artifact) is a red flag.

**Contract completeness expected:** Every surface that changes must be declared. Migration sets must be complete. Dependencies on future work (T7 clarification) are treated as design flaws, not follow-up items.
