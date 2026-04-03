---
date: 2026-04-03
time: "04:05"
created_at: "2026-04-03T04:05:46Z"
session_id: a9b905a6-1593-4fc3-b5fe-43059733516a
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_02-06_t04-t4-evidence-provenance-rev17-design-review-team.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 41410dee
title: "T-04 T4 rev 18-19 — adversarial review, boundary precision, and authority model"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/cross-model/references/consultation-contract.md
---

# Handoff: T-04 T4 rev 18-19 — adversarial review, boundary precision, and authority model

## Goal

Execute the user's adversarial review of T4 rev 17, then address findings through revisions 18 and 19. The prior session ran a 6-reviewer design-review-team self-review (22 canonical findings). This session was the user's own hostile review followed by iterative counter-review cycles to produce and apply fixes.

**Trigger:** Prior session's explicit next step: "Next session we should run a thorough self-review with the design-review-team skill." That was completed; the handoff said: "Await user's adversarial review of revision 17."

**Stakes:** G3 (evidence provenance retention) is the last hard gate before T6 composition check. G1, G2, G4, G5 are all `Accepted (design)`. The adversarial review tests whether rev 17's boundary-precision and enforcement machinery are internally consistent and aligned with the benchmark and consultation contracts.

**Success criteria:** Adversarial review complete, findings addressed through revision(s), document ready for user's final hostile review of live rev 19 text. No acceptance this session — user explicitly said "I'll share the findings from my review in the next session."

**Connection to project arc:** T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). T4 is a parallel prerequisite for T6. All other gates accepted. G3 acceptance would unblock T6 composition check.

## Session Narrative

### Phase 1: User's adversarial review of rev 17

Session loaded the prior handoff (rev 17, design-review-team self-review). User immediately delivered their adversarial counter-review of both rev 17 and the self-review's calibration.

The user's key meta-finding: the self-review's top-line calibration was wrong. The review claimed "approaching acceptance" with "Contradictions: 0," but the user identified two live contradictions the self-review missed entirely:

1. **Methodology findings load-bearing contradiction** — the body (L1050, L1373) said pass-rule effect "requires a T7 amendment," while §6.2 and the checklist (L1564, L2230) already defined condition-5 semantics as the intended design. A consumer could not tell whether T4 was requesting a future amendment or already norming its effect.

2. **Benchmark validity mismatch** — T4 (L914) said a safety leak makes the run "invalid per the benchmark safety rule," but the benchmark distinguishes invalid runs (run-condition violations, L98) from safety violations (scored contract failures, L145, pass-rule condition 1, L171). T4 conflated two distinct benchmark categories.

The user also confirmed 6 self-review findings as real blockers (F1, F2, F3, F4, F5, F14), partially agreed with F6 (downgraded from 3-part P1 to single clarification), and judged F8, F10, F11, F12, F20, F21 as over-prioritized (implementation planning, not acceptance blockers).

The user identified one additional inconsistency: §6.2 uses `detection-method` (L1537) while all other locations use `detection` (L1044, L1366, L1564).

This produced an adjusted severity map: 8 true P1 blockers (the 2 user findings + F1, F2, F3, F4, F5, F14), 1 P2 (detection-method naming), remainder downgraded.

### Phase 2: Full hostile reread

User conducted a full hostile reread of live rev 17 using the adjusted frontier. The reread confirmed the 8 blockers were stable — no new P1s surfaced. This was a strong convergence signal: the remaining defects were well-enumerated.

The user's 9 findings from the hostile reread mapped 1:1 to the adjusted frontier: findings 1-8 were the P1 blockers, finding 9 was the P2 naming inconsistency.

### Phase 3: Rev 18 proposals and counter-review

I drafted 9 text proposals (one per finding), each with exact current anchor text, exact replacement text, and one-sentence rationale. The user counter-reviewed and accepted proposals 1, 3, 5, 9 as written. For proposals 2, 4, 6, 7, 8, the user provided specific rewrites:

- **Proposal 2** (safety interaction): User corrected aggregate vs. per-run semantics. `safety_violations == 0` is an aggregate count, not a per-run label.
- **Proposal 4** (query diversity): User tightened the objective criterion to avoid implying exactly one query per mandatory type.
- **Proposal 6** (detail typing): User identified a producer-model error — I had T4 "emitting" finding rows, but T4 produces source artifacts and T7/adjudication emits the rows. Also caught `classification_trace_ref` as undefined and `claim_id` as ambiguous.
- **Proposal 7** (wire format example): User caught that my replacement still omitted `claim_id` from the nested `classification_trace`, inconsistent with the schema.
- **Proposal 8** (scope_envelope guard): User identified a scope mismatch between the two insertion points (one said benchmark runs generally, the other was under scored-run prerequisites only).

I accepted the user's rewrites and also tightened proposal B1's `failed_criterion` from `int` to the actual `1|2|3` enum per user feedback.

### Phase 4: Rev 18 application and first hostile review

Applied all 9 proposals as rev 18 (15 individual edit operations). Updated revision header to rev 18.

The user's hostile review of live rev 18 produced a **Reject** verdict with a new defect category: **authority leakage**. Rev 18 had fixed internal contradictions but introduced a new problem — T4 was now claiming benchmark-invalidity authority it didn't own. The `scope_envelope` guard at §4.6 said missing scope makes the run "treated as invalid under the benchmark's run-condition model," citing [benchmark.md:98], but the benchmark's run-condition list doesn't mention `scope_envelope`.

Additional findings from the rev 18 review:
- `detail` field still not validator-ready (key names without types)
- Duplicate `claim_id` in nested `ClassificationTrace` without equality invariant
- `max_evidence` still undefined (triple-converged self-review finding F15)
- Checklist item 70 not updated for new prerequisites
- Query diversity still text-level only
- Safety-violating artifacts called "usable" without handling policy
- `scope_envelope` depends on consultation-layer transport the benchmark doesn't declare

Two key patterns identified: (1) authority leakage — T4 absorbing benchmark-contract semantics; (2) naming fields without fully executable closure.

### Phase 5: Rev 19 proposals and counter-review

I proposed separating fixes into T4-local corrections vs. design decisions needing user input. The user chose to batch everything — no intermediate revisions with known seams.

User's five design decisions:
- `detail` typing: type obvious fields, leave explanatory payloads as `str`, T7 must publish JSON Schema
- `max_evidence`: benchmark-contract parameter under change control, not T4 constant
- Query diversity: text-level mechanical rule + adjudicator backstop, no edit-distance hacks
- Safety artifacts: narrow to "benchmark adjudication purposes," operational handling is T7-owned
- `scope_envelope` transport: explicit benchmark amendment dependency

I drafted 8 proposals (A-H) with interaction map. User counter-reviewed and found 4 issues:
1. Readiness-gate drift between prerequisite block (6 items) and checklist item 70 (which mentioned both new items)
2. Factual error: "seven run conditions" should be eight
3. Wrong finding kind (`shape_inadequacy`) for semantically recycled retries
4. `failed_criterion` should be enum `1|2|3`, not just `int`

I corrected all four. User approved and I applied rev 19 edits.

### Phase 6: Rev 19 hostile review and second Reject

User's hostile review of live rev 19 produced another **Reject** with a deeper finding category: **comparability and auditability gaps**. The scope requirement only checked presence of non-empty `allowed_roots` — not effective search space, `source_classes`, value equality across runs, or `scope_root` selection. New prerequisites were also unauditable from the benchmark artifact set.

Additional findings:
- Stale "all four T7 dependencies" sentence (mechanical miss — should be seven after final fixes)
- Safety section still made an artifact-handling authorization claim T4 doesn't own
- `max_evidence` was only "fixed per comparison" without benchmark change-control binding
- Consultation-transport coupling undeclared in benchmark

I pushed back on scope, arguing that comparability rules (same scope across runs) are benchmark-owned, not T4-local. User agreed in principle but identified that `scope_root` derivation IS T4-local (T4's confinement table executes against it). The resolution: T4 owns `scope_root` derivation and per-step recording; the benchmark contract owns comparability rules. Amendment rows specify what the benchmark must solve.

### Phase 7: Final fixes applied

Applied 7 fixes incorporating user adjustments:
1. Updated "four dependencies" to seven with explicit rationale (items 1-4 gate artifact completeness, 5-7 gate comparability and auditability)
2. Removed artifact usability assertion entirely — artifact handling is T7-owned
3. Expanded scope amendment row to full benchmark-relevant scope configuration (allowed_roots equivalence, source_classes, scope_root selection rule)
4. Added scope_root derivation rule in §4.6 (T4-local)
5. Added artifact-auditability amendment row (run kind, scope config, benchmark parameters, per-step scope_root)
6. Strengthened max_evidence to benchmark change control
7. Updated checklist item 70 to mirror full prerequisite block

User noted the artifact-auditability item must become a scored-run blocker (prerequisite item 7), not just an amendment row. I added it as item 7 and updated the validator gate to (1)-(7).

Rev 19 is now at 2362 lines. User will hostile-review the live text in the next session.

## Decisions

### Authority boundary: T4 specifies requirements, benchmark contract implements

**Choice:** T4 specifies what the benchmark contract must solve (via §6.2 amendment table) but does not claim benchmark-contract authority (invalidity, run-condition status, artifact-handling policy).

**Driver:** User's rev 18 hostile review: "this recreates the exact cross-document authority split rev18 was supposed to eliminate" — when T4 said missing scope_envelope makes a run "treated as invalid under the benchmark's run-condition model." The benchmark contract at [benchmark.md:24] is "the only authority for the supersession decision."

**Rejected alternatives:**
- (a) T4 claims benchmark authority directly — rejected because it creates multiple normative sources for the same execution rules. User: "T4 keeps absorbing benchmark-contract and consultation-contract semantics, creating multiple normative sources."
- (b) T4 says nothing about benchmark requirements — rejected because T4's containment contract, budget gates, and methodology finding semantics all depend on benchmark-contract parameters that don't yet exist. The amendment table is the correct interface.

**Trade-offs:** T4 cannot enforce its own requirements without T7 landing the amendments. All seven scored-run prerequisites depend on T7 delivery. This is accepted because the alternative (T4 self-enforcing) creates the authority overreach.

**Confidence:** High (E2) — validated through two adversarial review cycles (rev 18 review caught the overreach, rev 19 review validated the corrected authority model).

**Reversibility:** Medium — if the benchmark contract is restructured to subsume T4-local concepts, the amendment table entries would need to become different-shaped references.

**Change trigger:** If T7 decides to restructure the benchmark contract in a way that doesn't match T4's amendment specifications, the amendment table entries need negotiation.

### Methodology-findings voice unification: "T4 specifies, T7 implements"

**Choice:** All four locations where methodology findings reference the pass rule now use consistent language: "T4 specifies the required semantics; T7 owns adding this condition to the benchmark contract; the live benchmark currently has four conditions."

**Driver:** User's initial counter-review: "Rev17 still says two different things about whether methodology findings are load-bearing" — body said "requires a T7 amendment" (hypothetical), dependency section defined condition-5 semantics (normative).

**Rejected alternatives:**
- (a) Adopt body's hedging voice everywhere — rejected because §6.2 and checklist already provided the normative semantics. Removing them would lose information.
- (b) Adopt §6.2's assertive voice everywhere, implying condition 5 exists — rejected because the live benchmark has only four conditions. User: "do not accidentally overcorrect into 'condition 5 already exists.'"

**Trade-offs:** The three-truth formulation ("live benchmark has four conditions; T4 specifies condition-5 semantics; T7 implements the amendment") is more verbose than either single voice. Accepted because precision prevents the exact ambiguity the finding identified.

**Confidence:** High (E2) — the contradiction was independently confirmed by both the user and me, with specific line references in both directions.

**Reversibility:** High — if the benchmark contract adds condition 5, the "live benchmark currently has four conditions" guard becomes stale and should be updated to reflect the new state.

**Change trigger:** T7 landing the methodology-finding-consequence amendment in the benchmark contract.

### Safety-leak taxonomy: scored contract failure, not invalid run

**Choice:** Containment failure is a `safety_violation` (scored contract failure contributing to aggregate `safety_violations` count), not a run-condition invalidation. Artifact handling is T7-owned.

**Driver:** User identified the benchmark's own taxonomy: invalid runs are run-condition violations ([benchmark.md:98]), safety violations are scored contract failures ([benchmark.md:145]) that affect pass-rule condition 1 ([benchmark.md:171]). T4 rev 17 conflated these.

**Rejected alternatives:**
- (a) Keep "run is invalid" language — rejected because it contradicts the benchmark's own taxonomy and changes whether run artifacts are reusable.
- (b) Say artifacts "remain usable for benchmark adjudication purposes" — initially accepted in rev 18, then rejected in rev 19 review because this is an artifact-handling authorization claim T4 doesn't own. User: "the leaked artifacts may be handed to adjudicators" is a different decision from "the run stays valid and scored."

**Trade-offs:** T4 now defers artifact-handling entirely to T7. This means a leaked run's artifacts have no defined handling policy until T7 specifies one. Accepted because the alternative (T4 authorizing access) is an authority overreach.

**Confidence:** High (E2) — the benchmark taxonomy is explicit. The aggregate-vs-per-run distinction was user-corrected (pass-rule condition 1 is aggregate `safety_violations == 0`, not a per-run label).

**Reversibility:** Low — the taxonomy distinction (invalid vs. safety-failing) is structural to how the benchmark works.

**Change trigger:** Benchmark contract restructuring that merges invalid-run and safety-failure categories (unlikely — they serve different purposes).

### scope_root derivation: T4-local execution semantics, benchmark-owned comparability

**Choice:** T4 defines scope_root derivation (constrained to `allowed_roots` membership, per-step recording in `ScoutStep.scope_root`). The benchmark contract owns comparability rules for scope_root selection across compared runs.

**Driver:** User's rev 19 review identified that scope_root is already T4's normative machinery (confinement table, ScoutStep schema), so T4 must say something about how it's derived. But comparability (same scope across runs) is a benchmark concern.

**Rejected alternatives:**
- (a) T4 defines the full scope comparability rule — rejected as authority overreach, same pattern as the scope_envelope invalid-run claim.
- (b) T4 says nothing about scope_root derivation — rejected because T4 already uses scope_root in its execution semantics without defining how it's selected.
- (c) T4 uses "the agent selects the root most relevant to the query target" — user rejected as too soft: "discretionary enough to preserve the gaming hole." Tightened to "anchored to the query target" with mandatory per-step recording.

**Trade-offs:** T4 constrains scope_root only to `allowed_roots` membership and recording. An agent can still choose a narrow scope_root that excludes contradictory files, as long as it's within `allowed_roots`. The benchmark amendment row specifies that the benchmark must define a tighter selection rule.

**Confidence:** Medium (E1) — the T4/benchmark boundary is correct, but the effectiveness of the scope_root constraint depends on how tightly the benchmark's comparability rule is defined (T7-owned).

**Reversibility:** High — scope_root derivation rule is a local paragraph in §4.6. Can be tightened when the benchmark defines the comparability rule.

**Change trigger:** T7 defining the benchmark-relevant scope configuration, which may impose stricter scope_root selection rules that T4 must implement.

### max_evidence: benchmark change control, not per-comparison recording

**Choice:** `max_evidence` is a benchmark-contract parameter under benchmark change control, not merely "fixed per comparison and recorded."

**Driver:** User: "this parameter directly controls candidate effort and evidence yield. If operators can choose it after seeing the corpus or after exploratory runs, the benchmark measures parameter tuning as much as system quality."

**Rejected alternatives:**
- (a) T4 defines the value (e.g., 6-8) — rejected because it's a benchmark tuning parameter, not a T4 design constant.
- (b) "Fixed per comparison" without change control — initially proposed, rejected by user because it allows post-hoc parameter selection.

**Trade-offs:** The current benchmark change-control clause ([benchmark.md:200-207]) covers corpus, adjudication labels, metrics, and pass rule but does not yet cover execution parameters. Bringing `max_evidence` under that regime requires the clause to be expanded — this is explicitly noted as part of the T7 amendment.

**Confidence:** High (E2) — the distinction between recording and governance is clear, and the user's gaming scenario (choosing max_evidence after seeing the corpus) demonstrates why mere recording is insufficient.

**Reversibility:** Medium — strengthening from recording to governance is a one-way ratchet (weakening would undermine benchmark credibility).

**Change trigger:** None expected — governance is strictly better than recording for benchmark integrity.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — Rev 18 and 19

**Status:** Uncommitted (rev 19, 2362 lines). User will hostile-review in next session.

**Rev 18 changes (9 proposals, 15 edit operations):**

| # | What changed | Where |
|---|-------------|-------|
| 1 | Methodology findings voice unified: "T4 specifies, T7 implements, live benchmark has four conditions" | §4.4 (L828), §4.7 (L1085), §5.3 (L1410), checklist item 68 (L2279) |
| 2 | Safety-leak taxonomy: `safety_violation` (scored failure), not invalid run. Aggregate count semantics. | §4.6 safety interaction (L947) |
| 3 | Sort tiebreaker: `(claim_key, status)` → `(claim_key, status, claim_text)` | §3.1.2 (L250), Phase 1 (L260), Phase 2 (L267), checklist 64 (L2254) |
| 4 | Query diversity: mandatory-type queries only, supplementary excluded. Formal criterion. | §4.4 second-attempt (L855) |
| 5 | ClassificationTrace state-machine invariants: 6-row validity table replacing prose | §4.7 (L1057) |
| 6 | Methodology finding `detail`: typed per-kind required keys, T4 contract floor, T7 JSON Schema | §6.2 amendment table (L1635) |
| 7 | Wire format example: full ClassificationTrace fields including claim_id | §5.2 (L1167) |
| 8 | Benchmark-run scope guard: scope_envelope required for all benchmark runs | §4.6 (L923), §6.2 prerequisite (L1571) |
| 9 | `detection-method` → `detection` normalization | §6.2 prerequisite item 2 (L1581) |

**Rev 19 changes (11 items in changelog, ~7 edit operations):**

| # | What changed | Where |
|---|-------------|-------|
| 1 | scope_envelope authority downgrade: local execution gate, not benchmark invalidity | §4.6 (L935) |
| 2 | scope_root derivation rule: anchored to query target, per-step recording | §4.6 (L913) |
| 3 | detail field fully typed: str/int/bool/enum on all required keys | §6.2 amendment table (L1635) |
| 4 | classification_trace.claim_id equality invariant | §5.2 canonical wire format (L1177) |
| 5 | max_evidence: benchmark change control, not per-comparison recording | §3.5 (L585), §6.2 amendment table (L1658), checklist 42 (L2180) |
| 6 | State-machine table: "Structurally valid?" with validator/adjudicator distinction | §4.7 (L1072) |
| 7 | Query diversity: text-level necessary but not sufficient, adjudicator backstop | §4.4 (L868) |
| 8 | Safety artifact handling: removed usability assertion, T7-owned | §4.6 (L960) |
| 9 | Artifact-auditability amendment row + prerequisite item 7 | §6.2 amendment table (L1662), prerequisite list (L1618) |
| 10 | Scope amendment row expanded: allowed_roots equivalence, source_classes, scope_root selection | §6.2 amendment table (L1648) |
| 11 | Scored-run dependencies: 4 → 7 items. Checklist item 70 updated. Stale "four" corrected. | §6.2 (L1616, L1639), checklist 70 (L2316) |

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Uncommitted.

## Codebase Knowledge

### T4 design contract structure (2362 lines, rev 19)

The document at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` has grown from 2253 (rev 17) to 2362 (rev 19), a 4.8% increase across two revisions. The growth is from:
- State-machine invariant table in §4.7 (+12 lines)
- scope_root derivation rule in §4.6 (+9 lines)
- Expanded amendment table (3 new rows: scope, max_evidence, artifact auditability) (+3 lines each)
- Prerequisite items 5-7 and rationale paragraph (+8 lines)
- Various text expansions for precision (+15 lines scattered)

Key sections and their current line ranges (approximate, will shift when rev 19 is committed):

| Section | Lines | Key surfaces |
|---------|-------|-------------|
| Revision history | L9-32 | 19 revision entries |
| §1 Decision | L34-42 | Core design choices |
| §3.1 Claim occurrence registry | L196-299 | Sort order now `(claim_key, status, claim_text)` |
| §3.5 Agent working state | L568-598 | Budget gates, `max_evidence` now declared as benchmark parameter |
| §4.4 Scout query coverage | L808-872 | Query diversity with adjudicator backstop |
| §4.6 Containment | L898-970 | scope_root derivation, benchmark-run scope requirement, safety interaction |
| §4.7 Claim-class scope | L971-1100 | ClassificationTrace, state-machine invariants |
| §5.2 Provenance index | L1156-1240 | Wire format with full trace example, claim_id equality invariant |
| §6.2 External dependencies | L1530-1665 | Prerequisites (7 items), amendment table (8 rows) |
| §8 Verification checklist | L2110-2340 | 70 items, items 42/64/68/70 updated |

### Benchmark contract surfaces verified this session

| Surface | Location | What was verified |
|---------|----------|-------------------|
| Run conditions | [benchmark.md:86-97] | Eight conditions listed; scope_envelope not among them |
| Invalid run rule | [benchmark.md:98-99] | Run-condition violations only |
| Safety violations | [benchmark.md:145-151] | Binary per run, contract failure, distinct from invalid |
| Pass rule | [benchmark.md:169-181] | Four conditions; condition 1 is aggregate `safety_violations == 0` |
| Change control | [benchmark.md:200-207] | Covers corpus, labels, metrics, pass rule; does NOT cover execution parameters |
| Artifacts | [benchmark.md:101-113] | Minimal manifest.json; no run kind, scope config, or new parameters |

### Consultation contract surface verified this session

| Surface | Location | What was verified |
|---------|----------|-------------------|
| scope_envelope default | [consultation-contract.md:127] | Absent = unrestricted (backwards compatibility) |
| scope_envelope immutability | [consultation-contract.md:131-134] | Set at delegation time, breach → stop + synthesize |

### Cross-document authority model (key insight from this session)

T4 sits between two external contracts:
- **Benchmark contract** ([benchmark.md]) — owns run conditions, pass rule, artifacts, change control
- **Consultation contract** ([consultation-contract.md]) — owns scope_envelope transport, delegation semantics

T4's authority boundary:
- **T4 owns:** claim lifecycle, scouting protocol, containment execution, provenance indexing, methodology finding semantics
- **T4 specifies (for T7):** what the benchmark contract must add (via §6.2 amendment table)
- **T4 does NOT own:** run-condition status, artifact-handling policy, pass-rule conditions, benchmark execution protocol, scope comparability rules

This boundary was established through two adversarial review cycles and is the main architectural insight of the session.

## Context

### Mental Model

This is an **authority boundary problem** masquerading as a specification-precision problem. The surface-level defects in rev 17 (contradictory voices, incorrect taxonomy, missing tiebreakers) were real, but the deeper issue was that T4 was gradually absorbing authority from two adjacent contracts (benchmark and consultation) through successive revisions. Each revision that "tightened" a T4 rule also pulled in more benchmark-contract semantics. Rev 18 fixed the surface contradictions but created a new authority overreach (scope_envelope invalidity claim). Rev 19 corrected the authority model by introducing the T4-specifies/T7-implements boundary.

The convergence trajectory across revisions maps to a maturity progression:
- Revs 11-14: structural (architecture, state model)
- Revs 15-16: enforcement (SHOULD→MUST, consistency)
- Rev 17: consequence machinery (methodology findings, condition 5)
- Rev 18: boundary precision (sort keys, invariants, taxonomy corrections)
- Rev 19: authority model (T4/benchmark/consultation jurisdiction)

Each category is strictly narrower than the last, which is the expected convergence pattern for adversarial review.

### Project State

Gate status unchanged from prior handoff — G3 remains Draft:

| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 19, awaiting hostile review)** | **T4: scouting position and evidence provenance** |

### Convergence trajectory update

Adding rev 18-19 to the trajectory:

- Rev 11: 4 criticals (semantic gaps — capability assumptions without specs)
- Rev 12: 2 criticals (new surface contract problems)
- Rev 13: 2 criticals (closure story failures, structural mismatches)
- Rev 14: 4 criticals (internal consistency, enforcement completeness)
- Rev 15: 1 critical, 2 high, 1 medium (pipeline boundary, enforcement inconsistency, hygiene)
- Rev 16: 0 criticals, 2 high, 1 medium (enforcement weight, readiness gap, SHOULD/MUST)
- Rev 17: 0 criticals, self-review: 0 P0, 14 P1, 8 P2
- **Rev 18: User hostile review → Reject. Critical: authority overreach (new category). High: detail typing, claim_id invariant, max_evidence, checklist drift.**
- **Rev 19: User hostile review → Reject. Critical: scope completeness, artifact auditability. High: stale dependency count, artifact handling authorization, max_evidence governance.**
- **Rev 19 (amended): Applied all fixes. Awaiting final hostile review.**

The defect categories are narrowing: structural → enforcement → consequence → boundary precision → authority model → comparability/auditability. Each round fixes the prior category and the next adversarial pass finds a deeper layer.

## Learnings

### Cross-document semantic contradictions are structurally invisible to parallel independent reviewers

**Mechanism:** When 6 reviewers each read the document through their assigned lens, contradictions spanning 3+ sections (§4.7, §5.3, §6.2) are invisible because no single reviewer holds both halves simultaneously. The methodology-findings load-bearing contradiction and the benchmark validity mismatch are both multi-location reasoning failures.

**Evidence:** Self-review produced 22 findings but 0 contradictions. User's adversarial review immediately found 2. The lateral messaging between reviewers didn't catch them because each reviewer saw one half of the contradiction in their assigned section.

**Implication:** For future design reviews, add a dedicated cross-section consistency pass after the parallel review — one reader checking all instances of the same concept across sections.

**Watch for:** The same structural weakness applies to any reviewer team with section-based specialization.

### Authority overreach is an emergent property of iterative specification tightening

**Mechanism:** Each revision that "tightens" a T4 rule also pulls in more benchmark-contract semantics. The scope_envelope guard in rev 18 was a direct product of this — I was fixing a real gap (fail-open default) by adding the tightest possible rule, which happened to claim benchmark-contract authority.

**Evidence:** Rev 18's §4.6 said "treated as invalid under the benchmark's run-condition model" — this was a natural-seeming tightening of the prior "containment is T4's mechanism" text, but it crossed the authority boundary.

**Implication:** When fixing specification gaps at contract boundaries, always check: "am I specifying what T4 requires, or am I implementing what the benchmark contract should contain?" The amendment table is the correct interface for the latter.

**Watch for:** Future revisions that add enforcement rules referencing external contract concepts. The pattern is: "X must be Y for safety" → "X not being Y makes the run invalid" → T4 is now defining benchmark validity.

### Adversarial review defect categories narrow predictably through maturity stages

**Mechanism:** Each adversarial review cycle finds defects in a strictly narrower category than the last. The pattern: structural → enforcement → consequence → boundary precision → authority model → comparability/auditability. This is because earlier categories are prerequisites — you can't have authority-model problems until the enforcement machinery exists, and you can't have comparability gaps until the authority model is defined.

**Evidence:** Revs 11-14 had structural critiques. Rev 15-16 had enforcement inconsistencies. Rev 17 had consequence machinery. Rev 18 had boundary precision. Rev 19 had authority and auditability. No round introduced defects in a previously-resolved category.

**Implication:** When a hostile review finds defects only in a new, narrower category, the specification is converging. When it finds defects in a previously-resolved category, there's been a regression.

**Watch for:** The next review's findings should be in an even narrower category than comparability/auditability. If they're in authority or boundary precision, something regressed.

### The counter-review pattern converges when finding counts decrease across rounds

**Mechanism:** This session had 4 counter-review rounds with decreasing finding counts: initial self-review (22) → user hostile reread (9) → first counter-review of proposals (4) → second counter-review (0 new, 5 rewrites). When a counter-review produces only refinements to existing proposals and no new defects, the proposal set is ready to apply.

**Evidence:** The transition from "4 findings" to "0 new findings, 5 rewrites" between counter-review rounds 1 and 2. The third counter-review of rev 19 proposals found 4 issues but all were in the proposals themselves, not new document defects.

**Implication:** Use finding-count trajectory as a convergence metric for counter-review cycles. Stop cycling when findings are refinements, not new defects.

## Next Steps

### 1. User hostile review of live rev 19 text

**Dependencies:** Rev 19 edits applied (this session).

**What to read first:** The live document at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — focus on the changed high-risk surfaces: §4.6 (L935-970), §6.2 (L1597-1665), checklist items 42/68/70.

**Expected:** User will hostile-review using the same adversarial perspectives (benchmark contract lawyer, schema implementer, gaming participant, post-hoc auditor). Findings should be in a narrower category than comparability/auditability if the specification is converging.

**Approach:** If findings accepted → address in rev 20 following the same proposal/counter-review pattern. If user is satisfied → proceed toward G3 acceptance.

### 2. Address any rev 19 findings in rev 20

**Dependencies:** User's hostile review (step 1).

**Key areas likely to need attention based on rev 19 trajectory:**
- The amendment table rows are now quite dense — user may want more precise language
- The artifact-auditability row is new and hasn't been through a full counter-review cycle on the actual text
- The scope_root derivation rule is minimal — user may want tighter constraints

### 3. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 4. Post-acceptance: modular split with /superspec:spec-writer

**Note:** Document has grown from 1492 (rev 11) to 2362 (rev 19), a 58% increase across eight sessions. Post-acceptance, use `/superspec:spec-writer` to create a modular structure.

## In Progress

**In Progress:** T4 design contract revision 19, all edits applied, awaiting user hostile review.

- **Approach:** Iterative adversarial review → proposal → counter-review → apply cycle. Rev 18 fixed internal contradictions and boundary precision. Rev 19 fixed authority model, comparability, and auditability.
- **State:** Rev 19 edits applied to live file. Uncommitted. 2362 lines.
- **Working:** Authority model (T4-specifies/T7-implements), methodology findings voice unification, safety-leak taxonomy, sort determinism, ClassificationTrace invariants, detail typing, wire format example, scope_root derivation, max_evidence governance, artifact auditability.
- **Not working / uncertain:** User has not yet hostile-reviewed the live rev 19 text. The amendment table rows are dense and new — they haven't been through a full counter-review on actual text. The artifact-auditability prerequisite (item 7) was added late in the cycle.
- **Open question:** Will the user's hostile review of rev 19 find issues in a narrower category (convergence) or re-open authority/comparability concerns (regression)?
- **Next action:** Wait for user's hostile review of live rev 19.

## Open Questions

1. **Will the user's hostile review of rev 19 converge or regress?** The defect category should narrow if the specification is converging. If the review finds authority-model or comparability issues in unchanged sections, the fix pattern needs to change.

2. **Is the artifact-auditability prerequisite (item 7) correctly scoped?** It was added late in the cycle to satisfy the user's requirement that auditability be a scored-run blocker, not just an amendment aspiration. The exact scope ("run kind, resolved scope configuration, benchmark parameters in manifest.json/runs.json; per-step scope_root recoverable from transcript") hasn't been through a dedicated counter-review.

3. **How tightly should the benchmark's scope_root selection rule be defined?** T4 constrains scope_root to `allowed_roots` membership and recording. The benchmark amendment row asks for a "selection rule or justification requirement." The right tightness depends on how much search-space narrowing the benchmark is willing to tolerate.

4. **Should the concession boundary (downgraded F6) be fully specified before G3?** User downgraded this from 3-part P1 to single clarification. The wire format already says conceded claims persist. The remaining gap (historical provenance entries vs. synthesis-scoped ledger) is narrow but hasn't been addressed in rev 18-19.

5. **When should the modular split happen?** The document is at 2362 lines and growing. Each revision adds ~30-50 lines of precision. Post-acceptance split with `/superspec:spec-writer` was the plan, but the growing length makes review harder.

## Risks

### Rev 19 amendment table is very dense

The §6.2 amendment table now has 8 rows, several of which are long (methodology finding format row is ~200 words in a single table cell). This density makes it harder for a reviewer to verify consistency between the amendment row specifications and the document's own normative text. The scope and artifact-auditability rows are new and haven't been through a full counter-review on actual text.

**Mitigation:** The user's hostile review is the counter-review. If density is a problem, the modular split (post-acceptance) would separate amendment specifications from the design narrative.

### Authority boundary may shift when T7 starts implementing

The T4-specifies/T7-implements model works now because T7 doesn't exist yet. When T7 starts implementing the amendment table entries, negotiation may be needed — T7 may want different scope, typing, or governance rules than what T4 specifies. The amendment table entries are T4's wish list, not a negotiated contract.

**Mitigation:** The amendment table is explicitly labeled as T7-owned ("Owner: T7"). T7 can modify the implementation as long as T4's execution semantics (containment, budget gates, methodology finding semantics) remain functional.

### Document growth trajectory

2362 lines at rev 19 (up from 1492 at rev 11, +58%). Each revision adds precision but also length. The verification checklist alone is 70 items. Post-acceptance modular split is planned but the growing size makes pre-acceptance review harder.

**Mitigation:** Post-acceptance, `/superspec:spec-writer` modular split. Pre-acceptance, the user's hostile-review approach (prioritizing changed surfaces, not re-reading unchanged text) manages the review burden.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 19, 2362 lines) |
| Design review report | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` | 22 canonical findings from self-review, calibration adjusted by user |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Authority source for run conditions, pass rule, artifacts, change control |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope transport, delegation semantics |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant, gate acceptance criteria |

## Gotchas

### The self-review's severity calibration was wrong — do not trust its top-line conclusions

The self-review at `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` claimed "Contradictions: 0" and "approaching acceptance." The user's adversarial review immediately found 2 contradictions and a benchmark taxonomy mismatch. The self-review's concrete section reads (individual findings F1-F22) are more trustworthy than its aggregate conclusions.

### Revision history entries must be compressed for rev 18+

Rev 18 originally had a full changelog entry (~15 lines). The user's pattern for prior revisions was compressed entries (~5-8 lines). Rev 18 and 19 entries are compressed to match. The full-detail changelogs are in this handoff's Changes section.

### The "four dependencies" → "seven dependencies" drift was mechanical but dangerous

When adding scored-run prerequisites 5-7, the concluding summary sentence at L1629 still said "all four T7 dependencies." This was a mechanical miss (the sentence was outside the edit region), but it directly undermined the fix — an implementer could reasonably treat items 5-7 as second-class additions. Always search for all numeric references to the dependency count when expanding the list.

### The Edit tool's old_string matching can cause cascade errors

When editing the rev 18 changelog entry, the Edit tool matched a broader string than intended (the old rev 18 entry contained "## 1. Decision" as a substring), creating a duplicate section header and a corrupted line. Required a cleanup edit. When editing long table-cell content, verify that the match string is unique in the file.

## User Preferences

**Counter-review pattern (confirmed this session):** User provides structured counter-review with priority levels ([P1], [P2], [Critical], [High], [Medium]), specific file:line references, "why it matters" / "how it fails in practice" explanations, and concrete required changes. This pattern was consistent across all review rounds.

**Separation of concerns between review rounds (confirmed this session):** User counter-reviews proposals before editing. Pattern: (1) Claude proposes, (2) user counter-reviews, (3) Claude tightens, (4) repeat until accepted, (5) THEN edit the draft. No skipping to edits.

**Batching preference:** User explicitly chose to batch all fixes rather than landing intermediate revisions with known seams: "There is no value in landing another intermediate revision that knowingly preserves open design seams in the same sections you are already touching."

**Authority-boundary sensitivity:** User is very attuned to which document owns which decision. The rev 18 "treated as invalid under the benchmark's run-condition model" overreach was caught immediately. User: "this recreates the exact cross-document authority split rev18 was supposed to eliminate."

**Precision over softness:** User consistently tightened soft language. "The agent selects the root most relevant to the query target" → "anchored to the query target." "Minimum required keys" → "Required keys by kind" with explicit types. "Fixed per comparison" → "under benchmark change control."

**Adversarial review style:** User applies named adversarial perspectives (benchmark contract lawyer, schema implementer, gaming participant, post-hoc auditor, safety reviewer). These are explicitly listed in the review under "Adversarial Perspectives Applied And What They Exposed."

**Durable record preference (confirmed):** User requested audit artifacts committed to the repo. Workspace cleanup after reports saved. Clean repo state preferred.
