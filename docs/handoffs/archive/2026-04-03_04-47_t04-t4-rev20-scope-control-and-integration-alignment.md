---
date: 2026-04-03
time: "04:47"
created_at: "2026-04-03T04:47:56Z"
session_id: 48f02aff-5c03-4552-a63e-d4585d799f1a
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_04-05_t04-t4-rev18-rev19-adversarial-review-and-boundary-precision.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 6e646255
title: "T-04 T4 rev 20 — scope control vs. explanation, cross-surface integration alignment"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/cross-model/references/consultation-contract.md
---

# Handoff: T-04 T4 rev 20 — scope control vs. explanation, cross-surface integration alignment

## Goal

Apply rev 20 to the T4 design contract, fixing cross-surface integration defects from the user's hostile review of rev 19, then respond to the user's hostile review of rev 20 which surfaced a deeper architectural issue: non-authoritative explanation fields being used as comparability controls.

**Trigger:** Prior session ended with rev 19 edits applied, awaiting user's hostile review. User delivered that review at session start with 4 findings (all integration defects in the readiness and auditability surfaces), then hostile-reviewed the applied rev 20 and found 2 critical failures in the scope control architecture.

**Stakes:** G3 (evidence provenance retention) is the last hard gate before T6 composition check. G1, G2, G4, G5 are all `Accepted (design)`. The adversarial review tests whether the design contract's normative surfaces are internally consistent and aligned with the benchmark and consultation contracts.

**Success criteria:** Rev 20 applied with all cross-surface integration defects fixed, scope control architecture sound. User's hostile review of the amended rev 20 is the next session's entry point.

**Connection to project arc:** T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). T4 is a parallel prerequisite for T6. All other gates accepted. G3 acceptance would unblock T6 composition check.

## Session Narrative

### Phase 1: User's hostile review of rev 19

Session loaded the prior handoff (rev 18-19 adversarial review). User delivered their hostile review of live rev 19. The review found no new critical-severity failures — the authority-overreach class from rev 18 appeared materially improved. The remaining findings were all high-severity integration defects in the readiness and auditability surfaces:

1. **Prerequisite items 5-6 weaker than amendment rows and checklist** — item 5 said only "`scope_envelope` presence formalized as a benchmark run condition" while the amendment row and checklist required `allowed_roots` equivalence, `source_classes`, and `scope_root` selection rules.
2. **Stale transcript-fidelity verification sentence** — said "T4 implementation unblocked" when scored-run readiness has seven additional prerequisites.
3. **scope_root derivation underdefined for multi-root cases** — "anchored to the query target" was too soft; overlapping `allowed_roots` (not guaranteed disjoint per consultation-contract.md:49) not handled.
4. **Audit path inconsistent** — prerequisite item 7 allowed "transcript or extracted scout-step artifact"; checklist item 70 said "transcript" only; the extracted artifact had no schema or owner.

The user's meta-finding: "local fixes land, but cross-surface integration lags behind them." This was the same pattern from rev 18-19 but at a deeper layer.

### Phase 2: First proposal cycle

I drafted 4 proposals (A-D), one per finding. User counter-reviewed with 3 findings:

- **P1:** Proposal D incomplete — transcript-only recovery not wired through §3.9 dependency rows (they only required mechanical diff extraction, not per-step metadata recovery).
- **P2:** Proposal C still subjective — "broadest relevant domain" is a judgment call; overlapping roots not handled.
- **P3:** Proposal A item 5 narrowed the amendment row's solution space — hard-coded "selection rule" and "source_classes disposition" instead of preserving "selection rule or justification requirement" and "inclusion or explicit irrelevance."

User disposition: B ready, A good with wording fix, C and D not ready as written.

### Phase 3: Second proposal cycle

I revised all proposals. Key changes:
- A: isomorphic wording with amendment row (per P3)
- C: shallowest-root rule for overlapping roots, `scope_root_rationale: str | null` field for conceptual-query selection rationale, explicit benchmark-comparability boundary call for determinism
- D: four-part edit — prerequisite item 7 (D1), amendment row (D2), §3.9 transcript format row (D3), §3.9 transcript parser row (D4)

User counter-reviewed with 1 finding:

- **P1:** Proposal C is now a schema expansion — `scope_root_rationale` needs to be declared in ScoutStep and checklist item 57, not just referenced in prose.

User disposition: A, B, D ready. C ready if schema change folded in. The clean additions: `scope_root_rationale: str | null` in ScoutStep, `scope_root_rationale` in item 57's non-authoritative audit fields.

### Phase 4: Rev 20 applied (first pass)

Applied all proposals as rev 20 — 10 edit operations. File grew from 2362 to 2387 lines (+1.1%, smallest growth of any revision since rev 15).

Changes:
- Status line: rev 19 → rev 20
- Rev history: rev 20 entry added
- ScoutStep schema: `scope_root_rationale: str | null` added
- §4.6 scope_root derivation: 3-case rule (path-targeted shallowest, conceptual with rationale, cross-root shallowest)
- §3.9 transcript format row: per-step metadata recovery added
- §3.9 transcript parser row: ScoutStep fields extraction added
- §3.9 verification: narrowed to transcript fidelity dependency resolution
- §6.2 prerequisite items 5-7: expanded to match amendment row/checklist
- §6.2 amendment row: "or extracted scout-step artifact" → transcript-only with §3.9 cross-reference
- Checklist item 57: `scope_root_rationale` added
- Checklist item 70: "selection rule for all query types" added

### Phase 5: User's hostile review of rev 20 — Reject

User's hostile review found 2 critical failures and 3 high-severity findings. The critical failures were:

**Critical 1: Cross-surface integration still incomplete.** Prerequisite item 5 and the amendment row said "selection rule or justification requirement," but checklist item 70 compressed it to "selection." The note claimed cross-surface integration but the three load-bearing surfaces still didn't agree.

**Critical 2: scope_root_rationale not threaded through audit path.** The field existed in ScoutStep and was required for conceptual queries, but the prerequisite, auditability row, and checklist only required `scope_root` recoverability from transcript — not the rationale. For conceptual queries, the rationale was the only new control, but it wasn't part of the required audit artifacts.

High-severity findings:
- Justification-only benchmark policy permitted despite `scope_root_rationale` being explicitly non-authoritative (item 57)
- Verification sentence still resolved the dependency before parser/diff-engine readiness
- `scope_root_rationale` nullable without validator invariants

The user's meta-finding was deeper than integration drift: **"The document still prefers explanation after the fact over enforceable, benchmark-observable control."** `scope_root_rationale` was a non-authoritative self-explanation field being used as a comparability mechanism. That's structurally wrong — a benchmark needs enforceable constraints, not better post-hoc storytelling.

### Phase 6: Design decision — Path A vs. Path B

I presented two coherent paths:

- **Path A:** Remove `scope_root_rationale`, require deterministic selection only. Eliminate "or justification requirement" from all surfaces. Conceptual-query determinism deferred to benchmark contract.
- **Path B:** Keep `scope_root_rationale`, thread it end-to-end (transcript format, parser, auditability prerequisites, amendment row, checklist, validator rules, adjudication authority expansion).

I assessed Path A as stronger. User agreed decisively and added a critical correction: "Do not replace `scope_root_rationale` with 'the shallowest `allowed_root` that plausibly covers the query domain.' That phrase is just rationale smuggled back in as prose. 'Plausibly covers' is not deterministic."

The user's stronger Path A:
- Shallowest-root for path-targeted queries (deterministic, already working)
- Shallowest-root for cross-root queries (deterministic)
- For conceptual multi-root: don't invent a local pseudo-rule. `scope_root` must be in `allowed_roots` and recorded per step; scored benchmark runs blocked until benchmark contract defines the rule.

### Phase 7: Rev 20 amended (Path A)

Applied 8 edits implementing Path A:
1. Deleted `scope_root_rationale` from ScoutStep schema
2. Rewrote conceptual-query bullet — explicit benchmark deferral, no rationale, anti-narrowing constraint kept
3. Item 5: "selection rule for all query types including conceptual queries" (no justification alternative)
4. Amendment row: "selection rule for all query types" + "A justification-only policy is insufficient: `scope_root` selection must be enforceable by a validator without trusting agent narrative."
5. Verification sentence: "spec sub-dependency" with parser/diff-engine as separate T7 deliverables
6. Checklist item 57: `scope_root_rationale` removed
7. Checklist item 70: "selection rule for all query types" — matches item 5 and amendment row
8. Rev history updated to document rationale removal and why

File at 2390 lines. User will hostile-review in next session.

## Decisions

### Path A: Remove scope_root_rationale, require deterministic selection only

**Choice:** Remove `scope_root_rationale` from ScoutStep and all dependent surfaces. Require the benchmark to define a deterministic selection rule for all query types including conceptual queries. T4 records what happened (scope_root per step); T7 defines what counts as comparable. Scored runs blocked until the rule exists.

**Driver:** User: "Path B doubles down on the exact failure class the review surfaced: it turns a benchmark-control problem into an explanation-and-adjudication problem. That is the wrong direction for this document. A benchmark needs enforceable comparability, not better post-hoc storytelling."

**Rejected alternatives:**
- (a) **Path B — keep rationale, thread end-to-end:** Rejected because it creates high integration cost (parser, transcript schema, checklist, validator rules, adjudication authority) without pre-hoc comparability. User: "the system that writes defensible rationales can outperform the system that actually searched more honestly." The fundamental issue is structural: non-authoritative self-explanation is too weak for benchmark comparability regardless of how thoroughly it's threaded.
- (b) **"Shallowest root that plausibly covers the query domain"** — rejected as a replacement for `scope_root_rationale` because "plausibly covers" is not deterministic. User: "That phrase is just rationale smuggled back in as prose."
- (c) **Require all roots for conceptual queries** — considered but rejected as too restrictive given budget constraints (`max_evidence`, `max_scout_rounds`). Could force wasteful searches in irrelevant roots.

**Trade-offs:** Scored benchmark runs are blocked until T7 defines a conceptual-query root-selection rule. If T7 can't define one, runs stay blocked. The conceptual-query case has NO local T4 rule — only constraints (allowed_roots membership, anti-narrowing) and recording. User accepted: "If conceptual multi-root scope selection is truly benchmark-load-bearing, the benchmark must own a real rule. If it cannot, scored runs are not ready."

**Confidence:** High (E2) — validated through two adversarial review cycles (rev 20 first pass caught the explanation-over-control pattern; Path A confirmed by user's independent analysis reaching the same conclusion).

**Reversibility:** High — the field removal is simple to reverse if needed. If T7 later defines a selection rule that requires T4-local rationale recording for debugging (not control), the field can be re-added as instrumentation. The key distinction: instrumentation vs. control.

**Change trigger:** T7 defining a selection rule that requires T4-local amendments. If T7's rule depends on per-step rationale as input (unlikely given the "enforceable by validator" constraint), the field would need to return with enforcement semantics, not non-authoritative semantics.

### Justification-only policy explicitly prohibited in amendment row

**Choice:** The amendment row for benchmark-run scope formalization now says: "A justification-only policy is insufficient: `scope_root` selection must be enforceable by a validator without trusting agent narrative."

**Driver:** User identified that the "selection rule or justification requirement" alternative created an incentive structure favoring the weakest acceptable benchmark amendment. User: "schedule pressure will push T7 toward the cheaper, less constraining option." And: "non-authoritative self-explanation is too weak to be a sufficient comparability control."

**Rejected alternatives:**
- (a) **Keep "or justification requirement"** — rejected because it allows the benchmark to ship a weak scope policy that doesn't actually constrain agent behavior. The agent writes a plausible rationale, the benchmark gets paperwork instead of a constraint.
- (b) **Remove scope selection from amendment row entirely** — rejected because T4's containment contract depends on scope_root, and unconstrained choice demonstrably permits search-space narrowing that biases evidence coverage.

**Trade-offs:** Constrains T7's solution space — T7 cannot ship a justification-only scope policy. Accepted because a justification-only policy would recreate the `scope_root_rationale` problem at the benchmark level.

**Confidence:** High (E2) — the non-authoritative nature of explanation fields is structural. Checklist item 57 explicitly labels them as "agent explanation, not proof."

**Reversibility:** Low — relaxing this prohibition would undermine the authority model. If T7 argues that justification is sufficient for some cases, the right answer is to define what "sufficient justification" means mechanically (which makes it a selection rule, not a justification requirement).

**Change trigger:** None expected. If anything, the constraint should get stricter (requiring specific selection algorithms rather than any validator-enforceable rule).

### Conceptual-query scope_root: T4 constrains and records, does not define a rule

**Choice:** For conceptual queries with multiple roots, T4 does not define a deterministic selection rule. T4 constrains scope_root to `allowed_roots` membership, requires per-step recording in `ScoutStep.scope_root`, and applies the anti-narrowing constraint ("MUST NOT select a narrower root to exclude files that might contain contradictory evidence"). Full determinism deferred to benchmark contract via §6.2 amendment row.

**Driver:** User: "'Plausibly covers' is not deterministic." The space of possible conceptual-query/root combinations is too varied for a simple T4-local rule. Any rule T4 invents either (a) isn't actually deterministic (judgment call disguised as a rule) or (b) is too restrictive (search all roots regardless of relevance).

**Rejected alternatives:**
- (a) **"Broadest relevant domain"** — rejected as subjective. Two implementations could choose different roots for the same conceptual claim.
- (b) **"Shallowest root that plausibly covers the query domain"** — rejected as "rationale smuggled back as prose."
- (c) **Require selection rationale recording** — rejected because non-authoritative explanation doesn't help the benchmark verify compliance.
- (d) **Require searching all roots** — too restrictive given budget constraints.

**Trade-offs:** The conceptual-query case has no T4-local determinism. Two conforming T4 implementations can choose different roots for the same broad claim, as long as both are in `allowed_roots` and neither violates the anti-narrowing constraint. This means pre-benchmark comparability is not guaranteed for conceptual queries. Accepted because the benchmark's comparability rule (T7-owned) is what actually closes the gap.

**Confidence:** Medium (E1) — the analysis is sound but the effectiveness of the anti-narrowing constraint without a deterministic rule is untested. The constraint is behavioral (agent MUST NOT), not mechanically enforceable at T4 level.

**Reversibility:** High — the conceptual-query paragraph in §4.6 is a local edit. If T7 defines a selection rule, T4 can adopt it and the paragraph becomes more specific.

**Change trigger:** T7 defining the benchmark-relevant scope configuration, which may impose a specific conceptual-query root-selection algorithm that T4 must implement.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — Rev 20 (amended)

**Status:** Uncommitted (rev 20, 2390 lines). User will hostile-review in next session.

**Rev 20 changes (first pass — 10 edit operations, then 8 amendment edits):**

| # | What changed | Where (final line numbers) |
|---|-------------|---------------------------|
| 1 | scope_root derivation: 3-case rule with shallowest-root for path-targeted/cross-root, explicit benchmark deferral for conceptual, anti-narrowing constraint | §4.6 (L914-937) |
| 2 | scope_root_rationale added then removed from ScoutStep schema | §3.1 (L373) — field no longer present |
| 3 | Prerequisite items 5-6 expanded to match amendment row/checklist: scope configuration with `allowed_roots` equivalence, `source_classes` inclusion or irrelevance, `scope_root` selection rule for all query types; `max_evidence` under benchmark change control | §6.2 (L1640-1650) |
| 4 | Prerequisite item 7: transcript-only scope_root recovery (extracted scout-step artifact removed) | §6.2 (L1651-1653) |
| 5 | §3.9 transcript format row: per-step metadata recovery including resolved scope_root | §6.1 (L1575) |
| 6 | §3.9 transcript parser row: ScoutStep fields extraction including scope_root | §6.1 (L1576) |
| 7 | §3.9 verification: narrowed to spec sub-dependency; parser and diff-engine listed as separate T7 deliverables | §6.1 (L1579-1584) |
| 8 | Amendment row: "selection rule for all query types" + explicit justification prohibition | §6.2 (L1687) |
| 9 | Checklist item 57: scope_root_rationale removed (was added then removed in same rev) | Checklist (L2298-2299) |
| 10 | Checklist item 70: "selection rule for all query types" matching item 5 and amendment row | Checklist (L2375-2390) |
| 11 | Rev history: rev 20 entry with 5-point changelog documenting rationale removal | Revision history (L33) |

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Uncommitted.

## Codebase Knowledge

### T4 design contract structure (2390 lines, rev 20 amended)

Document at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` grew from 2362 (rev 19) to 2390 (rev 20), net +28 lines (+1.2%). This is the smallest growth of any revision since rev 15. The growth is from expanded prerequisite items, three-case scope_root derivation rule, and verification sentence expansion. Offset by scope_root_rationale removal and editorial compression.

Key sections and their current line ranges:

| Section | Lines | Key surfaces |
|---------|-------|-------------|
| Revision history | L9-33 | 20 revision entries |
| §1 Decision | L35-43 | Core design choices |
| §3.1 ScoutStep schema | L365-377 | scope_root: str (no rationale field) |
| §3.5 Agent working state | L568-598 | Budget gates, max_evidence declared as benchmark parameter |
| §4.4 Scout query coverage | L808-872 | Query diversity with adjudicator backstop |
| §4.6 Containment | L898-970 | scope_root derivation (3 cases), benchmark-run scope requirement, safety interaction |
| §4.7 Claim-class scope | L971-1100 | ClassificationTrace, state-machine invariants |
| §5.2 Provenance index | L1156-1240 | Wire format with full trace example, claim_id equality invariant |
| §6.1 Transcript fidelity | L1570-1584 | 4 dependency rows, spec sub-dependency verification, per-step metadata recovery |
| §6.2 External dependencies | L1630-1690 | Prerequisites (7 items), amendment table (8 rows), justification prohibition |
| §8 Verification checklist | L2110-2390 | 70 items, items 42/57/64/68/70 updated |

### Cross-surface alignment status (rev 20 amended)

The three load-bearing surfaces for scope formalization now say:

| Surface | What it says about scope_root selection | Line |
|---------|----------------------------------------|------|
| Prerequisite item 5 | "selection rule for all query types including conceptual queries" | L1645 |
| Amendment row | "selection rule for all query types including conceptual queries" + justification prohibition | L1687 |
| Checklist item 70 | "selection rule for all query types" | L2383-2384 |

Item 5 and the amendment row are isomorphic (amendment row adds enforcement rationale). Checklist 70 says "for all query types" (compression that preserves semantics — "all" includes conceptual). The justification prohibition appears only in the amendment row (appropriate — it's an implementation constraint for T7, not a T4 normative rule).

### Scope_root audit path (unified to transcript-only)

| Surface | What it requires | Line |
|---------|-----------------|------|
| §3.9 transcript format row | Transcript format sufficient for mechanical diff extraction AND per-step metadata recovery (including resolved scope_root) | L1575 |
| §3.9 transcript parser row | Extract tool inputs/outputs/evidence blocks AND per-step scout metadata (ScoutStep fields including scope_root) | L1576 |
| Prerequisite item 7 | Per-step scope_root recoverable from transcript | L1651-1653 |
| Amendment auditability row | scope_root choices recoverable from transcript format (§3.9 cross-reference) | L1689 |
| Checklist item 70 | Per-step scope_root recoverable from transcript | L2388 |

All five surfaces specify transcript as the single recovery path. §3.9 rows explicitly carry the per-step metadata load. The extracted scout-step artifact alternative has been removed from all surfaces.

### Benchmark and consultation contract surfaces verified this session

| Surface | Location | What was verified |
|---------|----------|-------------------|
| Run conditions | [benchmark.md:86-97] | Eight conditions; scope_envelope not among them |
| Change control | [benchmark.md:200-207] | Covers corpus, labels, metrics, pass rule; does NOT cover execution parameters |
| Artifacts | [benchmark.md:101-112] | Minimal manifest.json; no scout-step artifact |
| allowed_roots | [consultation-contract.md:49] | List of paths from briefing assembly — not guaranteed disjoint |
| scope_envelope | [consultation-contract.md:127] | Absent = unrestricted; immutable once set |

## Context

### Mental Model

This is an **explanation-vs-control problem** layered on top of the authority boundary problem from the prior session.

The prior session established: T4 specifies requirements, the benchmark contract implements them. This session discovered a finer distinction within T4's own scope: **T4 constrains and records** vs. **T4 defines rules**. For scope_root selection:

- **Path-targeted queries:** T4 defines a rule (shallowest allowed_root containing the path). Deterministic, enforceable.
- **Cross-root queries:** T4 defines a rule (shallowest root containing each search target). Deterministic, enforceable.
- **Conceptual queries:** T4 cannot define a deterministic rule without either (a) inventing pseudo-rules that aren't actually deterministic, or (b) using explanation fields that aren't actually enforceable. The honest answer: T4 constrains (allowed_roots membership, anti-narrowing) and records (scope_root per step), but the benchmark must own the comparability rule.

The general principle surfaced: **A non-authoritative self-explanation field is not a comparability control.** If the field only makes the agent explain itself rather than constraining its behavior, it belongs in debugging instrumentation, not the benchmark's control path. This applies broadly to benchmark design — any field labeled "non-authoritative" in the audit inventory should not appear in the control path.

### Convergence trajectory update

Adding rev 20 to the trajectory:

- Rev 11: 4 criticals (semantic gaps)
- Rev 12: 2 criticals (surface contract problems)
- Rev 13: 2 criticals (closure story failures)
- Rev 14: 4 criticals (internal consistency)
- Rev 15: 1 critical, 2 high, 1 medium (pipeline boundary)
- Rev 16: 0 criticals, 2 high, 1 medium (enforcement weight)
- Rev 17: 0 criticals, self-review 14 P1 (consequence machinery)
- Rev 18: User reject — authority overreach (new category)
- Rev 19: User reject — comparability/auditability gaps
- **Rev 20 (first pass): User reject — 2 critical: cross-surface integration incomplete, scope_root_rationale not threaded through audit. 3 high: justification-only policy allowed, verification too early, nullable without invariants.**
- **Rev 20 (amended): Applied Path A — scope_root_rationale removed, justification prohibited, all surfaces unified. Awaiting hostile review.**

Defect categories: structural → enforcement → consequence → boundary precision → authority model → comparability/auditability → cross-surface integration → **explanation-vs-control**. Each round finds a strictly narrower category. The explanation-vs-control finding is the deepest yet — it's about the fundamental nature of what kind of field can serve as a benchmark control.

### Project State

Gate status unchanged:

| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 20 amended, awaiting hostile review)** | **T4: scouting position and evidence provenance** |

## Learnings

### Non-authoritative explanation fields are not comparability controls

**Mechanism:** A field explicitly labeled "non-authoritative — agent explanation, not proof" (checklist item 57) cannot serve as the sole control for benchmark comparability. The benchmark needs to verify that two runs made equivalent scope choices; a non-authoritative rationale field only tells the benchmark what the agent claims about its choice, not whether the choice was correct.

**Evidence:** `scope_root_rationale` was added to ScoutStep as a non-authoritative audit field. The conceptual-query rule said "the agent MUST record the selection rationale in `ScoutStep.scope_root_rationale`." But the prerequisite, auditability row, and checklist only required `scope_root` recoverability — not the rationale. The user's review exposed that even if the rationale were threaded through all audit surfaces, it would still be a weak control: "the system that writes defensible rationales can outperform the system that actually searched more honestly."

**Implication:** Any field labeled "non-authoritative" in the audit inventory (item 57) should not appear in the benchmark's control path. Non-authoritative fields are debugging instrumentation. Control fields must be either (a) mechanically deterministic (shallowest-root rule) or (b) enforceable by a validator without trusting agent narrative.

**Watch for:** Future revisions that use audit fields as control mechanisms. The pattern is: "we need the agent to explain X" → "let's add a field for X" → "now let's require X in the audit path" → field is non-authoritative but used as a control.

### "Plausibly covers" is rationale smuggled as prose

**Mechanism:** When replacing a soft control (scope_root_rationale) with a rule, the replacement can contain the same judgment call hidden in different words. "The shallowest `allowed_root` that plausibly covers the query domain" sounds like a rule but "plausibly covers" is a judgment call — two implementations can reach different conclusions.

**Evidence:** User caught this immediately: "That phrase is just rationale smuggled back in as prose. 'Plausibly covers' is not deterministic."

**Implication:** When writing specification rules, test each adjective/adverb for determinism: can two conforming implementations reach different conclusions given the same inputs? If yes, the word is soft and needs to be either (a) replaced with a mechanical definition or (b) explicitly deferred to an authority that will define it.

**Watch for:** "Relevant," "appropriate," "suitable," "reasonable," "plausible" in normative specification text. These are judgment-call words that look like constraints but aren't.

### Integration fixes that remove machinery are convergent signals

**Mechanism:** Rev 20's first pass added scope_root_rationale (new field, new recording requirement, new audit surface). The amended rev 20 removed it. The removal produced a simpler, stronger specification: fewer fields, fewer surfaces to keep aligned, no explanation-vs-control tension.

**Evidence:** Rev 20 first pass: 2387 lines, 2 critical failures. Rev 20 amended: 2390 lines (slightly more due to justification prohibition), 0 known critical failures. The line count barely changed but the architectural quality improved significantly.

**Implication:** When a specification revision adds machinery (fields, surfaces, recording requirements) to fix integration defects, ask whether the machinery is solving the right problem. If the fix requires extensive cross-surface threading to work, the machinery itself may be the problem. A fix that removes machinery while tightening constraints is a stronger convergence signal.

**Watch for:** Revisions where the line count grows significantly due to integration threading. Compare against the alternative of removing the surface that created the integration need.

### Cross-surface integration requires literal isomorphism, not semantic equivalence

**Mechanism:** Checklist item 70 said "scope_root selection" while item 5 said "scope_root selection rule or justification requirement." These are semantically close but implementation-distinct: an implementer satisfying "selection" could ship a justification-only policy, while item 5 explicitly allowed it. A checklist-driven reviewer might reject the same implementation that an item-5-driven reviewer accepts.

**Evidence:** The user's critical finding 1 on rev 20: "one implementer can ship a justification-only benchmark rule and call item 5 satisfied, while a checklist-driven reviewer rejects it for lacking a real selection rule."

**Implication:** When multiple surfaces (prerequisite list, amendment rows, checklist) describe the same requirement, they must be literally isomorphic on the normative content or explicitly mark which is canonical and which is a summary. "Close enough" creates implementation-distinct interpretations.

**Watch for:** Checklist items that compress prerequisite language. The compression can silently drop alternatives, qualifiers, or constraints that change what counts as compliant.

## Next Steps

### 1. User hostile review of live rev 20 (amended)

**Dependencies:** Rev 20 amendments applied (this session).

**What to read first:** The live document at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — focus on the changed high-risk surfaces:
- §4.6 scope_root derivation (L914-937) — conceptual-query case now has no local rule, explicit benchmark deferral
- §6.2 prerequisites (L1640-1653) — items 5-7 expanded, selection rule for all query types
- §6.2 amendment row (L1687) — justification prohibition is new
- §3.9 verification (L1579-1584) — spec sub-dependency only
- Checklist items 57 (L2298) and 70 (L2375-2390) — scope_root_rationale removed, selection rule aligned

**Expected:** The next review's findings should be in an even narrower category than explanation-vs-control if the specification is converging. If findings re-open scope control or cross-surface integration, something regressed.

**Approach:** If findings accepted → address in rev 21 following the proposal/counter-review pattern. If user is satisfied → proceed toward G3 acceptance.

### 2. Address any rev 20 findings in rev 21

**Dependencies:** User's hostile review (step 1).

**Key areas likely to need attention:**
- The anti-narrowing constraint ("MUST NOT select a narrower root to exclude contradictory evidence") is behavioral, not mechanically enforceable. User may want this acknowledged more explicitly.
- The justification prohibition in the amendment row is new and hasn't been through a counter-review on its exact wording.
- The verification sentence change from "resolved" to "spec sub-dependency" may need further tightening if the user considers parser/diff-engine readiness part of the transcript fidelity dependency.

### 3. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 4. Post-acceptance: modular split with /superspec:spec-writer

**Note:** Document at 2390 lines. Post-acceptance, use `/superspec:spec-writer` to create a modular structure.

## In Progress

**In Progress:** T4 design contract revision 20 (amended), all edits applied, awaiting user hostile review.

- **Approach:** Iterative adversarial review → proposal → counter-review → apply cycle. Rev 20 first pass fixed cross-surface integration (prerequisites, amendment rows, checklist alignment). Rev 20 amendment removed scope_root_rationale and prohibited justification-only policies.
- **State:** Rev 20 edits applied to live file. Uncommitted. 2390 lines.
- **Working:** Authority model (T4-specifies/T7-implements), methodology findings voice, safety-leak taxonomy, sort determinism, ClassificationTrace invariants, detail typing, wire format, scope_root derivation (shallowest-root for path-targeted/cross-root, explicit benchmark deferral for conceptual), max_evidence governance, artifact auditability, transcript-only recovery, cross-surface integration (prerequisites, amendment rows, checklist now aligned), justification prohibition.
- **Not working / uncertain:** User has not yet hostile-reviewed the amended rev 20 text. The anti-narrowing constraint for conceptual queries is behavioral, not mechanically enforceable at T4 level — the benchmark's comparability rule is what closes the gap. The justification prohibition in the amendment row is new.
- **Open question:** Will the user's hostile review of amended rev 20 converge or find a still-narrower defect category?
- **Next action:** Wait for user's hostile review of live rev 20 (amended).

## Open Questions

1. **Is the anti-narrowing constraint enforceable?** The conceptual-query case says "the agent MUST NOT select a narrower root to exclude files that might contain contradictory evidence." This is a behavioral norm, not a mechanical check. A conforming implementation could violate it without detection unless the benchmark's adjudicator specifically audits scope_root choices against claim evidence. Is this acknowledged explicitly enough?

2. **Is the justification prohibition correctly scoped?** The amendment row says "A justification-only policy is insufficient: `scope_root` selection must be enforceable by a validator without trusting agent narrative." This constrains T7's solution space. Is T7's solution space adequately understood for this constraint to be right? What if some query types genuinely can't have a deterministic rule?

3. **Should the concession boundary be fully specified before G3?** User downgraded this in the prior session from 3-part P1 to single clarification. It hasn't been addressed in rev 18-20. The gap (historical provenance entries vs. synthesis-scoped ledger) is narrow.

4. **When should the modular split happen?** Document at 2390 lines and growing. Post-acceptance split with `/superspec:spec-writer` was the plan, but the review cycle continues.

## Risks

### Anti-narrowing constraint is behavioral without mechanical enforcement

The conceptual-query case relies on a MUST NOT constraint that the T4 validator cannot check. A conforming implementation could select a narrow root (excluding contradictory evidence) and appear structurally valid. The benchmark's adjudicator would need to audit scope_root choices against evidence distribution to detect violations, but this audit authority isn't explicitly granted.

**Mitigation:** The benchmark's scope formalization (§6.2 amendment row) will define the selection rule, which supersedes the anti-narrowing constraint. The constraint is a T4-local behavioral norm for the interim; the benchmark rule is the enforcement mechanism.

### Justification prohibition may over-constrain T7

The amendment row now explicitly says justification-only policies are insufficient. If some edge cases in conceptual-query scope selection genuinely resist deterministic rules, T7 may need to negotiate. The amendment table entries are T4's specification, not a negotiated contract.

**Mitigation:** The prohibition is on "justification-only" — T7 can still define a rule that has a justification component as long as the primary selection mechanism is validator-enforceable.

### Document growth trajectory

2390 lines at rev 20 (up from 1492 at rev 11, +60%). Each revision adds precision but also length. Post-acceptance modular split is planned.

**Mitigation:** Rev 20's net growth was only +28 lines (+1.2%) — the smallest increment since rev 15. The specification may be approaching asymptotic complexity for its scope.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 20, 2390 lines) |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Authority source for run conditions, pass rule, artifacts, change control |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope transport, allowed_roots semantics (not guaranteed disjoint) |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant, gate acceptance criteria |
| Design review report | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` | 22 canonical findings from self-review, calibration adjusted by user |

## Gotchas

### scope_root_rationale was added and removed in the same revision

Rev 20's first pass added `scope_root_rationale: str | null` to ScoutStep and checklist item 57. The user's hostile review identified it as a non-authoritative field being used as a control — the wrong kind of mechanism for benchmark comparability. The amended rev 20 removed it. The rev history entry at L33 documents both the addition and removal to prevent future sessions from re-introducing it.

### "Plausibly covers" and similar soft language are red flags in normative text

The user caught "plausibly covers" as judgment disguised as a rule. Normative specification text should be tested word-by-word for determinism: "Can two conforming implementations reach different conclusions given the same inputs?" Words like "relevant," "appropriate," "plausible," "reasonable" fail this test and should be either mechanically defined or explicitly deferred to an authority.

### The verification sentence has been revised three times across revisions 18-20

Rev 18: "T4 implementation unblocked when..." (too broad — implied general T4 readiness)
Rev 20 first: "The transcript fidelity dependency is resolved when..." (too early — resolved before parser/diff-engine)
Rev 20 amended: "The spec sub-dependency is satisfied when..." (correct — explicitly separates spec from implementation deliverables)

Future edits to §3.9 should verify the verification sentence still accurately describes what it resolves.

### Parallel edits to the same file work when anchor text is unique and non-overlapping

This session applied 10 edits in two parallel batches (5 each) to the same 2387-line file, then 7 more in parallel for the Path A amendments. All succeeded because each edit's old_string was unique in the file and the edits targeted non-overlapping regions. When editing long table-cell content in amendment rows, use specific phrases from within the cell (not the full cell) as anchors.

## User Preferences

**Counter-review pattern (confirmed this session):** Three counter-review rounds, each producing structured findings with priority levels ([P1], [P2], [Critical], [High]). Finding quality increased through the rounds — first round caught wording issues, second caught schema expansion, third caught architectural flaws. The user applies progressively deeper adversarial perspectives across rounds.

**Explanation-vs-control sensitivity (new this session):** User rejects non-authoritative fields as comparability controls. The distinction between explanation (debugging instrumentation) and control (benchmark-enforceable constraint) is load-bearing. User: "A benchmark needs enforceable comparability, not better post-hoc storytelling."

**Pseudo-determinism detection (new this session):** User catches judgment calls disguised as rules. "Plausibly covers" was immediately flagged as "rationale smuggled back as prose." Normative text must be testable for mechanical determinism.

**Batching preference (confirmed):** User chose Path A as a batch rather than incremental changes. Consistent with prior session's preference for batching all fixes rather than landing intermediate revisions with known seams.

**Authority-boundary sensitivity (confirmed):** User continues to enforce strict ownership boundaries. Path A was preferred because it "keeps the ownership split clean. T4 records what happened. T7 defines what counts as comparable."

**Adversarial perspectives (confirmed):** User applied: benchmark maintainer under schedule pressure, candidate implementer optimizing to win, post-hoc auditor with only benchmark artifacts. These are the same named perspectives from the prior session, applied to the new findings.
