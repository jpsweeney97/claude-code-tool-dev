---
date: 2026-04-04
time: "14:56"
created_at: "2026-04-04T18:56:23Z"
session_id: 23b93862-5fd7-4428-be8d-e2481df2c849
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-04_14-11_t6-composition-check-three-passes.md
project: claude-code-tool-dev
branch: main
commit: 2f22bdc9
title: T6 composition analysis — four review passes to near-final draft
type: handoff
files:
  - docs/notes/t6-composition-check-analysis.md
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/cross-model/references/consultation-contract.md
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/scripts/event_schema.py
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
---

# Handoff: T6 composition analysis — four review passes to near-final draft

## Goal

Continue the T6 composition check from the prior session. The prior session
produced a third-pass analysis that was judged "close but not ready." The user
said they would review the T6 verdict and share findings in this session.

**Trigger:** The prior handoff's first next step was "User reviews T6 verdict
and shares findings." The user arrived with a prepared adversarial review.

**Stakes:** Medium-High. T6 is the design gate between accepted T1-T5 designs
and T7 (defining the executable slice). A premature T6 closure pushes design
bugs into implementation. A false T6 failure reopens gates unnecessarily.

**Connection to project arc:** T4 close-out → reclassification → Path-2
encoding → T6 composition (3 prior passes) → **T6 composition (this session,
4 more review passes)** → T6 closure pending synthesis contract consolidation
→ T7 executable slice → T8 dry-run.

**Success criteria:** A T6 analysis document that the user accepts as a
credible decision artifact — correct scope, complete source set, evidence-
backed verdicts, and explicit ownership for all unresolved boundaries.

## Session Narrative

### Phase 1: User's first review of the third-pass analysis

Loaded the prior handoff (`2026-04-04_14-11_t6-composition-check-three-passes.md`).
The user asked me to read the existing analysis at
`docs/notes/t6-composition-check-analysis.md` before sharing their findings.

The user provided Pass 1 scrutiny with 5 findings across 2 passes (P1: 3
findings, P2: 3 findings). All findings were correct:

**P1-1 (Critical):** T6 closes too early. The mid-round scope-breach path is a
loop-structure gap at the exact boundary T6 is supposed to settle. The note
said "defer to T7 and close T6" when it should say "T6 remains open until this
control-flow rule is locked." The loop structure IS the composition of T1's
termination contract with T4's per-turn scouting loop — the "orchestration
layer" connecting them is precisely what T6 produces.

**P1-2 (High):** The synthesis contract is not actually composed. "Split
authority" was correctly distinguished from "design conflict" but the conclusion
was wrong. Compatibility is not consolidation. T6's done-when requires "one
consistent benchmark-first design" — two documents describing different surfaces
is not one consistent contract.

**P1-3 (High):** Two of three T7 deferrals are T6 work. Scope-breach exit rule
and synthesis contract unification are consolidation work. Only B8 anchor-
adequacy is genuinely T7.

**P2-1 (High):** The scope-breach choice is benchmark-visible (transcript
shape, pending-round behavior, turn count, termination cause, safety
interpretation). Not neutral orchestration plumbing.

**P2-2 (Medium):** Split synthesis contract creates a silent-failure path.
`event_schema.py:137` rejects `agent_local`. `SKILL.md:435` falls back to
`server_assisted`.

**P2-3 (Low):** `normative: false` characterization of
`dialogue-synthesis-format.md` was ungrounded — the file has no such
frontmatter.

**User's verdict:** "Not ready as a final T6 closeout. T6 remains open pending
explicit closure of the mid-round scope-breach exit rule and unification of the
synthesis contract surface."

**Key insight recognized:** The same error pattern across all prior passes was
**scope displacement** — reclassifying T6 work as belonging to a different
phase. Pass 2 pushed it to T7/T8 (implementation readiness). Pass 3 pushed it
to an "orchestration layer" (implying something outside T1-T5).

Updated the document: loop structure and synthesis contract verdicts changed to
"DOES NOT YET COMPOSE."

### Phase 2: User's comprehensive adversarial review

The user provided a structured adversarial review with a premise check, 3
critical failures, 2 high-risk assumptions, 2 real-world breakpoints, 2 hidden
dependencies, and 6 required changes. Verdict: "Reject."

**Premise check (Critical):** The note isn't answering the right question. The
T7 ticket (`t7-conceptual-query-corpus-design-constraint.md:113-114`,
acceptance criterion 4 at `:125`) explicitly requires T6 to record whether
benchmark-v1 coverage remains adequate under the constrained corpus. The note
refused this at lines 74-81.

**Critical Failure 1:** Coverage adequacy dodged.

**Critical Failure 2:** Ownerless third state. "Does not yet compose" + "no
gate needs reopening" is not authorized by the design plan
(`benchmark-first-design-plan.md:52`), which has exactly two states: compose
(done) or reopen conflicting gates.

**Critical Failure 3 (most consequential):** The loop analysis omitted an
adjacent authoritative contract. `consultation-contract.md:131-133` already
specifies immediate stop on scope breach: "On scope breach, the agent MUST: 1.
Stop the consultation immediately. 2. Proceed to Phase 3 synthesis with
termination_reason: scope_breach." The note's main "loop does not compose"
argument was built on an incomplete three-spec source set. With four specs, the
ambiguity resolves.

**High-Risk Assumptions:** (1) `agent_local` and `scope_envelope` bridge hidden
as "tracked, not T6 items" when they're either blockers or need proof they're
outside T6. (2) State model verdict too thin — T3/T4 identity boundary not
analyzed.

**Required Changes (6):**
1. Add coverage adequacy verdict (B4, B8)
2. Re-run loop analysis with consultation contract
3. Replace "no gate needs reopening" with ownership table
4. Elevate `agent_local`/`scope_envelope` or prove outside T6
5. State model T3/T4 identity analysis
6. Name authoritative synthesis surface

**Pivotal discovery:** Reading `consultation-contract.md:131-133` resolved the
entire loop ambiguity. The four-spec control flow:
Detection (T4-CT-01:23) → Threshold (T4-CT-01:30) → Immediate stop
(consultation contract §6:131) → Pending-round marker (T4-SM-09) → T1
termination → Phase 3 synthesis (consultation contract §6:133).

The loop structure verdict **flipped** from "DOES NOT YET COMPOSE" to
"COMPOSES." Did extensive source reading (T7 ticket, consultation contract,
design plan, T3 design note, T4 state model lifecycle table, benchmark
contract corpus compliance, benchmark readiness) and rewrote the entire
document.

### Phase 3: User's third review — fairness ≠ adequacy

The user provided 4 targeted findings. Verdict: "Major revision — much closer."

**Finding 1 (High):** Coverage adequacy outruns evidence. B8 "adequate" verdict
conflated comparability (both systems face same constraints) with adequacy
(benchmark credibly answers the supersession question). B8 can still admit
structurally weak decompositions with no benchmark consequence.

**Finding 2 (High):** T3/T4 identity proof cites wrong path. The conceded-
referent path for referential claims goes through T4-SM-03 (`state-model.md:
141-153`) → NO_LIVE_REFERENT → Phase 1.5 forced-new (`state-model.md:89-97`).
The "reintroduction after concession" lifecycle rows (`state-model.md:390-391`)
are a separate mechanism for new extracted claims matching conceded text, not
for referential claims with dead referents.

**Finding 3 (High):** Consolidation artifact doesn't cover T5 migration
surfaces. The artifact's canonical surface is `dialogue-synthesis-format.md`,
but T5's Primary Migration Set (`t5:195-206`) requires coordinated changes to
7 surfaces (normative contract, schema, producer contract, test enforcement).
A doc-only consolidation leaves `agent_local` rejected or coerced.

**Finding 4 (Medium):** `scope_envelope` bridge overclaims "direct." Path-
anchor population is direct; `allowed_roots` equivalence and `source_classes`
are still open per `dialogue-supersession-benchmark.md:170-173`.

**User's pattern identified:** "Treats fairness or compatibility as if that were
enough to prove adequacy or closure." Applied 8 targeted edits.

### Phase 4: Final review — one remaining contradiction

User's final review found one material issue: the T3/T4 identity boundary
paragraph at line 9 still said T3 reclassifies dead-referent claims to `new`,
citing `t3:171-183`. But those T3 lines only cover missing `referent_text` or
missing `prior_registry` membership — the conceded-but-still-in-registry case
passes T3 and is caught by T4-SM-03.

**Verdict: "Minor revision."** Fixed by narrowing T3's role to prior-registry
validation and attributing the no-live-occurrence check to T4-SM-03 + Phase
1.5. "The rest of the previously serious issues now look repaired rather than
merely rephrased."

## Decisions

### Decision 1: Loop structure COMPOSES (consultation contract resolves ambiguity)

**Choice:** Retract the "loop does not yet compose" finding and replace with
"loop composes" after discovering the consultation contract's immediate-stop
specification.

**Driver:** `consultation-contract.md:131-133` specifies: "On scope breach, the
agent MUST: 1. Stop the consultation immediately. 2. Proceed to Phase 3
synthesis with termination_reason: scope_breach." This is the fourth
authoritative spec. The four-spec control flow is fully determined:
Detection (T4-CT-01:23) → Threshold (T4-CT-01:30) → Immediate stop
(consultation contract §6:131) → State capture (T4-SM-09) → T1 termination →
Phase 3 synthesis (consultation contract §6:133).

**Alternatives considered:**
- **Keep "does not yet compose" with narrowed residual** — rejected because the
  four-spec control flow is fully determined. The remaining question (whether
  T1's algorithm evaluates or termination is directly produced) is an
  implementation mechanism, not a design ambiguity. The behavior (immediate stop,
  scope_breach cause, pending-round marker, Phase 3 synthesis) is fully
  specified.

**Trade-offs accepted:** The loop verdict flipped, removing one of T6's two
blockers. Only the synthesis contract consolidation remains. Risk: if the
consultation contract is amended, the loop analysis would need revision.

**Confidence:** High (E2) — four authoritative specs traced through the control
flow. User accepted the analysis in the subsequent review (did not challenge
the loop composition finding in any of the three remaining reviews).

**Reversibility:** High — if a fifth spec contradicts the control flow, the
analysis can be rerun.

**What would change this decision:** If the consultation contract's "stop
immediately" is qualified to allow mid-round completion, or if the T4-SM-09
pending-round emission is found to conflict with the immediate-stop semantics.

### Decision 2: Coverage adequacy is "adequate for comparability; B8 conditional for supersession credibility"

**Choice:** Split the B8 adequacy verdict into comparability (proven) and
supersession credibility (conditional on T7 enforcement gaps).

**Driver:** User's finding: "same narrowed surface for both systems" proves
fairness, not adequacy. B8 can still admit structurally weak decompositions with
no benchmark consequence (no `methodology_finding_threshold`, T4-BR-07 item 4)
and has no decision rule for anchor inadequacy.

**Alternatives considered:**
- **Unconditional "adequate"** — rejected because it equates comparability with
  adequacy. The benchmark could be "cleanly executable but strategically
  worthless" if enforcement gaps remain.
- **"Not adequate"** — rejected because the Path-2 constraint doesn't eliminate
  any gate mechanic. The issue is enforcement, not structure.

**Trade-offs accepted:** The conditional verdict means T7 must close B8
enforcement gaps for adequacy to become unconditional. Creates a T7 dependency.

**Confidence:** High (E2) — grounded in the benchmark contract's explicit
enforcement gaps (`dialogue-supersession-benchmark.md:168-175`,
`benchmark-readiness.md:131-142`) and the user's scrutiny.

**Reversibility:** High — upgrades to unconditional when T7 closes the gaps.

**What would change this decision:** Benchmark contract amended with
`methodology_finding_threshold` and anchor-adequacy decision rule.

### Decision 3: T6 consolidation artifact scoped to specification, not consumer code

**Choice:** The T6 consolidation artifact covers the synthesis contract
specification (`dialogue-synthesis-format.md`). Consumer-code changes
(`event_schema.py`, `SKILL.md`, tests) are T7 executable-slice work per T5 §6
Primary Migration Set.

**Driver:** T6's scope is "consolidate T1-T5 into one consistent benchmark-
first design" (`benchmark-first-design-plan.md:39`) — design is specified in
documents. T7 "defines the minimal executable slice"
(`benchmark-first-design-plan.md:41`) — includes consumer-code updates.

**Alternatives considered:**
- **Expand T6 to include consumer-code changes** — rejected because it
  collapses the T6/T7 boundary. T6 is design composition; T7 is executable
  slice.
- **Don't track consumer-code changes** — rejected because `agent_local`
  rejection by `event_schema.py:137` is a live invalid-run path. Must be
  tracked somewhere.

**Trade-offs accepted:** T6 can be "finished" with a doc-only consolidation
while `agent_local` is still rejected by code. Correct for T6's scope but
creates a T7 obligation. T5's Primary Migration Set (`t5:195-206`) defines the
7 consumer-code surfaces T7 must update.

**Confidence:** High (E2) — grounded in the design plan's T6/T7 boundary
definition.

**Reversibility:** High — if the design plan is amended.

**What would change this decision:** Design plan redefining T6 to include
implementation readiness.

### Decision 4: `scope_envelope` bridge is T7 work (with narrowed claim)

**Choice:** Path-anchor population (corpus row anchors → `allowed_roots`) is a
direct mapping and is T7 executable-slice work. But the full T4-BR-07 item 5
has open subrequirements beyond path-anchor population.

**Driver:** Five-point proof in the note:
1. T4 specifies WHAT `scope_envelope` must contain (`containment.md:94-100`)
2. Benchmark contract specifies WHAT `allowed_roots` are
   (`dialogue-supersession-benchmark.md:73-76, 147-152`)
3. Path-anchor population is a direct mapping
4. No T1-T5 design change required
5. T4 anticipated this and deferred via T4-BR-07 item 5

User's correction: the "direct mapping" claim only covers path-anchor
population. `allowed_roots` equivalence, `source_classes` inclusion, and named
`scope_envelope` as a benchmark run parameter remain open
(`dialogue-supersession-benchmark.md:170-173`). These are unresolved benchmark-
policy specifications, not T1-T5 design gaps.

**Alternatives considered:**
- **Claim the entire bridge is "direct"** — rejected per user's scrutiny.
  Path-anchor population is direct; equivalence and source_classes are policy
  decisions.

**Trade-offs accepted:** The narrower claim is less clean but more honest. The
next session using this note cannot mistake "copy anchor paths" for the whole
T7 job.

**Confidence:** High (E2) — grounded in the benchmark contract's explicit list
of open subrequirements.

**Reversibility:** N/A — factual precision, not a design choice.

**What would change this decision:** Nothing — the open subrequirements are
stated in the benchmark contract text.

## Changes

### `docs/notes/t6-composition-check-analysis.md` — T6 composition check

**Purpose:** Iterative refinement of the T6 composition check analysis from a
rejected draft to a near-final decision artifact.

**Approach:** Four rounds of user adversarial review, each producing targeted
edits or full rewrites. The document went through these states:

| Round | Key change | Verdict |
|-------|-----------|---------|
| 1 (user Pass 1-2) | Loop and synthesis verdicts → "DOES NOT YET COMPOSE" | Not ready |
| 2 (user adversarial review) | Full rewrite: consultation contract added, coverage adequacy, T3/T4 identity, ownership table | Reject → Major revision |
| 3 (user targeted review) | B8 conditional, conceded-referent path corrected, consolidation scoped, scope_envelope narrowed | Major revision |
| 4 (user final review) | T3 role narrowed to prior-registry validation | Minor revision |

**Current document state:** 7 sections. Verdicts: state model COMPOSES, loop
structure COMPOSES, synthesis contract DOES NOT YET COMPOSE, coverage adequacy
adequate for comparability (B8 conditional). One consolidation artifact with
named canonical surface, merge table, and done-when. Two T7 deferrals with
justification.

No other files were modified this session. Analysis only.

## Codebase Knowledge

### T6 Composition Boundary Architecture

T6 checks three composition boundaries. The accepted designs span these files:

| Boundary | Gate designs | Composition result |
|----------|-------------|-------------------|
| State model | T1 (`ControlDecision` read-only), T2 (`claim_source` excluded per T4-SM-06), T3 (`prior_registry` → referential validation), T4 (`occurrence_registry`, `verification_state`, `claim_id`) | COMPOSES — T3/T4 identity boundary verified |
| Loop structure | T1 (step 4 control decision), T4-SB-01 (per-turn loop), T4-CT-01 (scope breach), consultation contract §6 (immediate stop), T4-SM-09 (pending round) | COMPOSES — four-spec control flow coherent |
| Synthesis contract | T4-PR-01/03/05 (provenance surfaces), T4-BD-01/02 (boundary declarations), T5 §6 (mode), `dialogue-synthesis-format.md` (consumer contract) | DOES NOT YET COMPOSE — split across two documents |

### Scope-Breach Exit: Four-Spec Control Flow

| Step | Authority | File:line | Behavior |
|------|-----------|-----------|----------|
| Detection | T4-CT-01 | `containment.md:23` | Per-call counting. N out-of-scope results = 1 breach |
| Threshold | T4-CT-01 | `containment.md:30` | `scope_breach_count >= 3` mid-round triggers exit |
| Immediate stop | Consultation contract §6 | `consultation-contract.md:131-132` | "Stop the consultation immediately" |
| State capture | T4-SM-09 | `state-model.md:516-527` | Pending-round marker: target, steps, reason |
| Termination | T4-CT-01 → T1 | `containment.md:30` | T1-format termination with `scope_breach` |
| Synthesis | Consultation contract §6 | `consultation-contract.md:133` | Phase 3 with `scope_breach` in pipeline-data |

The per-turn loop's interrupt point is between tool calls at step 5b. Scope-
breach detection fires post-execution (`containment.md:23`). "Stop immediately"
means next tool call does not execute. Steps 5c-5e, 6-7 skipped. Budget
accounting: `scout_budget_spent` already incremented at step 5b start
(`state-model.md:452-453`); interrupted round counts.

### T3/T4 Identity Boundary

T3 validates referential integrity: `referent_text` presence and `referent_key`
membership in `prior_registry` (`t3:171-183`). T3 reclassifies to `new` only
when `referent_text` is null or `referent_key` is absent.

T4-SM-03 validates liveness: filters to occurrences with live entries in
`verification_state` (`state-model.md:141-144`). If all matching occurrences
are conceded, returns `NO_LIVE_REFERENT` (`state-model.md:149-153`), routing
to Phase 1.5 forced-new reclassification (`state-model.md:89-97`).

These compose correctly but serve different functions:
- T3 catches missing referents (text or key absent)
- T4-SM-03 catches dead-but-present referents (key exists, no live occurrences)

The "reintroduction after concession" lifecycle rows (`state-model.md:390-391`)
are a separate Phase 2 mechanism for new extracted claims matching conceded
text — NOT the path for referential claims with conceded referents.

`claim_id` allocation happens AFTER Phase 1.5 AND Phase 2
(`state-model.md:323-324`). Phase 1.5 reclassification changes status before
any consumer sees it (`state-model.md:131-134`).

### Synthesis Contract Split

| Document | What it specifies |
|----------|-------------------|
| `dialogue-synthesis-format.md` (consumer-facing) | 7 assembly sections, checkpoint grammar, `server_assisted\|manual_legacy` epilogue |
| T4 spec tree | `EvidenceRecord` schema, `claim_provenance_index` wire format, `## Claim Ledger` grammar, `not_scoutable` |

The T6 consolidation artifact names `dialogue-synthesis-format.md` as the
canonical surface. Five surfaces must merge:

| Surface | Design source | Target in format doc |
|---------|--------------|---------------------|
| `EvidenceRecord` | T4-PR-01 (`provenance-and-audit.md:15-63`) | Evidence trajectory section |
| `claim_provenance_index` | T4-PR-03 (`provenance-and-audit.md:65-106`) | Pipeline-data epilogue |
| `## Claim Ledger` grammar | T4-PR-05 (`provenance-and-audit.md:121-163`) | New 8th assembly section |
| `not_scoutable` | T4-BD-02 | Claim/evidence trajectory sections |
| `agent_local` mode | T5 §6 (`t5:195-206`) | Mode vocabulary and epilogue |

Consumer-code surfaces (T5 Primary Migration Set: `event_schema.py`,
`SKILL.md`, 3 test files) are T7 implementation of this specification.

### Coverage Adequacy Under Constrained Corpus

B1-B7: Corpus-compliant, Path-2 doesn't change them.
B4: Narrowed anchor set — breadth reduced, gate mechanics preserved,
comparability preserved (`dialogue-supersession-benchmark.md:85-87`).
B8: Anchored decomposition — 3 path groups, cross-root scouting preserved,
longest turn budget (8), exercises scope confinement and evidence budget
(`dialogue-supersession-benchmark.md:92-113`).

B8 comparability: adequate. B8 supersession credibility: conditional on
`methodology_finding_threshold` (T4-BR-07 item 4) and anchor-adequacy decision
rule.

### `scope_envelope` Bridge

Path-anchor population (corpus row anchors → `allowed_roots`) is a direct
mapping. But T4-BR-07 item 5 has open subrequirements beyond population
(`dialogue-supersession-benchmark.md:170-173`): named `scope_envelope` as
benchmark run parameter, `allowed_roots` equivalence for compared runs,
`source_classes` inclusion or explicit irrelevance. These are unresolved
benchmark-policy specifications.

### T5 Primary Migration Set

7 surfaces that must accept `agent_local` (`t5:195-206`):

| Layer | Surface | File |
|-------|---------|------|
| Normative contract | Mode definition | `dialogue-synthesis-format.md` |
| Normative contract | Pipeline epilogue | `dialogue-synthesis-format.md` |
| Schema | Enum definition | `event_schema.py` |
| Producer contract | Dialogue skill pipeline | `SKILL.md` |
| Test enforcement | Schema enum assertion | `test_event_schema.py` |
| Test enforcement | Analytics builder/validator | `test_emit_analytics_legacy.py` |
| Test enforcement | Active parser fixtures | `test_emit_analytics.py` |

First 2 rows: T6 consolidation artifact. Remaining 5 rows: T7 implementation.

## Context

### Mental Model

T6 is a **design coherence checkpoint**, not an implementation readiness gate.
The value is catching incompatible state shapes, ordering conflicts, or semantic
contradictions BEFORE defining the executable slice.

The recurring error across all drafts was **scope displacement** — reclassifying
T6 work as belonging to a different phase:
- Prior session Pass 2: Displaced to implementation readiness (T7/T8)
- Prior session Pass 3: Displaced to "orchestration layer" (outside T1-T5)
- This session Round 1: Displaced mid-round exit to T7
- This session Round 2: Fairness/compatibility conflated with adequacy/closure

The correction that finally separated the consolidation artifact cleanly:
**design specification** (what the contract says) and **implementation** (what
the code accepts) are distinct. T6 consolidation addresses specification. T7
implementation addresses code. Confusing these collapses the T6/T7 boundary.

### Project State

All D-prime cross-model work (T1-T5) verified end-to-end. T4 closed at SY-13.
Benchmark contract has Path-2 corpus constraint. T6 analysis near-final after
four review passes this session. T7 ticket open.

T6 status: State model and loop structure compose. Synthesis contract does not
yet compose — consolidation artifact specified, work not started. Coverage
adequacy adequate for comparability, B8 conditional for supersession
credibility.

### Environment

Working in `claude-code-tool-dev` monorepo on `main`. Origin up to date. No
branches open. Analysis-only session — no code changes. The T6 analysis
document at `docs/notes/t6-composition-check-analysis.md` is the only modified
file.

## Learnings

### Fairness ≠ adequacy

**Mechanism:** "Same narrowed surface for both systems" proves comparability —
both systems face the same constraints, so scores are comparable. But
comparability does not prove adequacy — the benchmark can be comparable while
being too weak to answer the supersession question credibly. Adequacy requires
enforcement (e.g., `methodology_finding_threshold` for structurally weak
decompositions).

**Evidence:** User's scrutiny: "Those two positions do not coexist cleanly. 'Same
narrowed surface for both systems' proves fairness, not adequacy."

**Implication:** When evaluating benchmark coverage, distinguish comparability
(fairness between compared systems) from adequacy (ability to answer the
measurement question credibly). The former is about equivalence; the latter is
about measurement strength.

**Watch for:** The same conflation appearing in B1-B7 analysis or in T7/T8
dry-run evaluation. Comparability is necessary but not sufficient for a
credible benchmark.

### T3/T4 dead-referent check is split across two gates

**Mechanism:** T3 validates referential integrity: `referent_text` presence and
`referent_key` membership in `prior_registry` (`t3:171-183`). T3 reclassifies
to `new` only when text is null or key is absent. The conceded-but-still-in-
registry case PASSES T3 because the key remains in `prior_registry`.

T4-SM-03 validates liveness: filters to occurrences with live entries in
`verification_state` (`state-model.md:141-144`). All-conceded → NO_LIVE_REFERENT
→ Phase 1.5 forced-new (`state-model.md:89-97, 149-153`).

**Evidence:** T3 validation algorithm at `t3:171-183`. T4-SM-03 at
`state-model.md:136-162`. Phase 1.5 at `state-model.md:89-97`.

**Implication:** Don't describe the dead-referent check as a single-gate
operation. T3 catches missing referents; T4 catches dead-but-present referents.
Both compose correctly but must be described separately.

**Watch for:** The "reintroduction after concession" lifecycle rows
(`state-model.md:390-391`) describe a DIFFERENT mechanism — Phase 2 re-
extraction, not referential claims with dead referents. Don't confuse the two.

### The consultation contract is an authoritative scope-breach spec

**Mechanism:** `consultation-contract.md:131-133` specifies immediate-stop
behavior on scope breach. This is a fourth authoritative spec alongside T4-CT-01,
risk register G:74, and T1:98. Including it resolves the loop-structure ambiguity
entirely.

**Evidence:** The prior analysis built its main "loop does not compose" argument
on three specs and concluded "no spec authorizes any one of these." The
consultation contract authorizes option 1 (immediate stop).

**Implication:** When analyzing composition boundaries, enumerate ALL
authoritative specs — not just the T1-T5 gate designs. Adjacent contracts
(consultation contract, benchmark contract) may resolve ambiguities that appear
unresolved within the gate designs alone.

**Watch for:** Other composition boundaries where an adjacent contract provides
the missing specification. The consultation contract may resolve other
orchestration-layer questions in T7.

### Design specification ≠ implementation — a T6/T7 precision

**Mechanism:** T6 consolidation addresses specification (what the contract says).
T7 implementation addresses code (what consumers accept). A T6 consolidation
artifact focused on `dialogue-synthesis-format.md` correctly addresses the
specification gap. But it cannot claim to "address" the `event_schema.py`
rejection or `SKILL.md` fallback — those are T7 consumer-code work.

**Evidence:** T5 Primary Migration Set (`t5:195-206`) defines 7 surfaces. 2 are
normative contract (T6 consolidation). 5 are code (T7 implementation). The
note incorrectly claimed "addressed by the consolidation artifact" for all 7.

**Implication:** When scoping a consolidation artifact, be precise about what
"addresses" means. Specifying `agent_local` in the contract doesn't make code
accept it. Track both halves explicitly.

**Watch for:** The inverse error — T7 claiming that consumer-code changes are
"just implementation" without verifying the specification is consistent first.

## Next Steps

### 1. User reviews T6 analysis draft and shares findings

**Dependencies:** None.

**What to read first:** `docs/notes/t6-composition-check-analysis.md` — the
current state after four review passes this session. Last verdict: "Minor
revision." One material contradiction was fixed (T3 role narrowed).

**User's stated intent:** "I will review this draft and then share my findings
in the next session."

### 2. If T6 analysis accepted: synthesis contract consolidation

**Dependencies:** T6 analysis accepted (possibly with modifications from user
review).

**What to read first:**
- `docs/notes/t6-composition-check-analysis.md` — consolidation artifact
  specification (canonical surface, merge table, done-when)
- `packages/plugins/cross-model/references/dialogue-synthesis-format.md` — the
  canonical surface to be updated
- T4 design sources: `provenance-and-audit.md` (T4-PR-01/03/05),
  `boundaries.md` (T4-BD-01/02)
- `docs/plans/2026-04-02-t04-t5-mode-strategy.md:195-206` (T5 Primary
  Migration Set specification surfaces)

**Work to do:** Update `dialogue-synthesis-format.md` to include all 5 surfaces
from the merge table. This is the T6 consolidation artifact's done-when:
"specifies every surface that T4 and T5 designs require; no consumer needs the
T4 spec tree to know what the synthesis contains."

**Note:** The user writes substantive amendments themselves. Claude's role is
analysis, verification, and review.

### 3. After synthesis contract consolidation: T6 closes, T7 begins

**Dependencies:** Consolidation accepted.

**What to read first:**
- `benchmark-first-design-plan.md:41-42` (T7 definition)
- `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` (T7
  ticket)

**T7 picks up:**
- B8 anchor-adequacy decision rule
- `scope_envelope` harness wiring (path-anchor population + open
  subrequirements from `dialogue-supersession-benchmark.md:170-173`)
- T5 Primary Migration Set consumer-code surfaces (5 of 7 rows from `t5:195-206`)

## In Progress

Clean stopping point. T6 analysis went through four review passes this session.
The last verdict was "Minor revision" — one material contradiction fixed. No
work is in flight.

**State:** `main` at `2f22bdc9`, origin up to date. Working tree has one
modified file (`docs/notes/t6-composition-check-analysis.md`). Analysis-only
session — no code changes.

## Open Questions

1. **Does the user accept the T6 analysis draft?** The four-pass analysis
   produced specific verdicts (state model composes, loop structure composes,
   synthesis contract does not yet compose, coverage adequate for comparability
   with B8 conditional) and a consolidation artifact. The user will review.

2. **Is the B8 conditional verdict the right position?** The note says B8 is
   "adequate for comparability; conditional for supersession credibility." The
   user may want a stronger or different formulation.

3. **Who does the synthesis contract consolidation?** The user writes substantive
   amendments. The consolidation work is updating `dialogue-synthesis-format.md`
   with T4/T5 surfaces. The user may want to do this themselves or may delegate.

## Risks

1. **User may find additional issues in the analysis.** Each review round found
   issues the prior round missed. The "minor revision" verdict is encouraging
   but not a guarantee of acceptance. The user's review is the authority.

2. **Synthesis contract consolidation may surface unstated invariants.**
   Merging T4's surfaces into `dialogue-synthesis-format.md` may reveal that
   consumers depend on fixed section counts, parsers drop unknown pipeline-data
   fields, or the claim-ledger grammar conflicts with checkpoint grammar.
   Mitigated by T4-BD-01/02's explicit change declarations.

3. **T7 may discover that consumer-code changes require specification revisions.**
   If `event_schema.py` or `SKILL.md` have constraints not visible in the
   specification (e.g., validation logic that rejects structurally valid
   `agent_local` values), T7 may route back to the T6 specification.

## References

| What | Where |
|------|-------|
| T6 analysis (working draft) | `docs/notes/t6-composition-check-analysis.md` |
| T6 authoritative definition | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:38-39` |
| T6 decision gate | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:52` |
| T7 ticket | `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` |
| T7 coverage adequacy obligation | `t7-conceptual-query-corpus-design-constraint.md:113-114, :125` |
| Consultation contract (scope breach) | `packages/plugins/cross-model/references/consultation-contract.md:131-133` |
| T4 spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/` |
| T4-SM-03 referent resolution | `state-model.md:136-162` |
| T4-SM-09 pending round | `state-model.md:516-527` |
| T4-CT-01 scope breach | `containment.md:20-31` |
| T4-SB-01 per-turn loop | `scouting-behavior.md:13-31` |
| Phase 1.5 forced-new | `state-model.md:89-97` |
| claim_id allocation | `state-model.md:320-332` |
| Lifecycle table | `state-model.md:376-393` |
| T3 validation algorithm | `2026-04-02-t04-t3-deterministic-referential-continuity.md:171-183` |
| T5 Primary Migration Set | `2026-04-02-t04-t5-mode-strategy.md:195-206` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Corpus compliance | `dialogue-supersession-benchmark.md:71-113` |
| Run conditions | `dialogue-supersession-benchmark.md:126-155` |
| Scored-run prereqs | `dialogue-supersession-benchmark.md:157-180` |
| T4-BR-07 prereq gate | `benchmark-readiness.md:121-142` |
| T4-BR-04 provenance consumer | `benchmark-readiness.md:79-91` |
| T4-BR-05 synthesis format | `benchmark-readiness.md:92-103` |
| Consumer-facing synthesis contract | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Prior session handoff | `docs/handoffs/archive/2026-04-04_14-11_t6-composition-check-three-passes.md` |

## Gotchas

1. **The consultation contract is an authoritative scope-breach spec.** The T6
   analysis previously missed it. `consultation-contract.md:131-133` specifies
   immediate stop. Without it, the loop analysis concludes "no spec authorizes
   any one of these." With it, the ambiguity resolves. Always include adjacent
   contracts when analyzing composition boundaries.

2. **T3's dead-referent handling is narrower than it appears.** T3 only checks
   `referent_text` presence and `prior_registry` membership (`t3:171-183`). The
   conceded-but-still-in-registry case PASSES T3. T4-SM-03 catches it via
   live-occurrence filtering. Don't attribute the full dead-referent check to T3.

3. **"Reintroduction after concession" is NOT the dead-referent path.** The
   lifecycle rows at `state-model.md:390-391` are a Phase 2 re-extraction
   mechanism for new claims matching conceded text. Referential claims with
   conceded referents go through T4-SM-03 → NO_LIVE_REFERENT → Phase 1.5
   forced-new. Different mechanism, different trigger.

4. **T6 consolidation ≠ T5 migration.** The T6 consolidation artifact covers
   the specification (2 of 7 T5 Primary Migration Set surfaces). The remaining
   5 surfaces are consumer-code T7 work. "Addressed by the consolidation
   artifact" only applies to the specification gap, not the code gap.

5. **B8 "adequate" for comparability, NOT for supersession credibility.** B8
   can admit structurally weak decompositions with no benchmark consequence.
   Supersession credibility depends on `methodology_finding_threshold` and
   anchor-adequacy decision rule — both T7 items.

6. **`scope_envelope` "direct mapping" applies to path-anchor population only.**
   `allowed_roots` equivalence, `source_classes`, and named `scope_envelope` as
   a benchmark run parameter are open subrequirements
   (`dialogue-supersession-benchmark.md:170-173`).

## Conversation Highlights

**Four-round adversarial review structure:** The user provided structured
reviews with severity labels (Critical/High/Medium/Low), specific file:line
citations, "why it matters" / "how it fails in practice" framing, and a closing
paragraph identifying what survives scrutiny.

**Scope displacement identified as recurring pattern:** User observed that every
draft reclassified T6 work as something else — implementation readiness,
orchestration layer, T7 deferral. The correction was always the same: anchor to
the design plan's definition of T6.

**Fairness ≠ adequacy correction:** User caught the conflation of comparability
(both systems face same constraints) with adequacy (benchmark answers the
question credibly). This is the same structural error as scope displacement —
treating a necessary condition as sufficient.

**Consultation contract discovery:** The user's "Critical Failure 3" citation of
`consultation-contract.md:131-133` was the session's pivotal moment. It resolved
the entire loop ambiguity and flipped the loop verdict from "does not compose"
to "composes."

**User's review verdicts across this session:**
- Round 1: "Not ready as a final T6 closeout"
- Round 2: "Reject" (6 required changes)
- Round 3: "Major revision" (4 findings, much closer)
- Round 4: "Minor revision" (1 remaining contradiction)

## User Preferences

**Provides structured adversarial reviews.** Multiple passes with severity
labels and specific file:line citations. Closing paragraph identifies what
survives scrutiny. Findings were consistently correct across all rounds.

**Expects correct scope definition.** T6 is design composition, not
implementation readiness. The user catches and corrects scope drift.

**Values evidence-backed analysis.** Every finding cites specific file paths
and line numbers. Analysis that makes claims without citations is "inference,
not proof."

**Reviews findings in subsequent sessions.** User said: "I will review this
draft and then share my findings in the next session."

**Writes substantive amendments themselves.** Claude's role is analysis,
verification, and review. This was consistent across prior sessions.

**Expects precision over convenience.** Catches conflation (fairness/adequacy,
specification/implementation, T6/T7 scope) and requires the distinction to be
explicit in the artifact. "Those two positions do not coexist cleanly."

**Works in closed units with clear scope boundaries.** Each review round
maintained a clear boundary between what T6 owns and what belongs elsewhere.
