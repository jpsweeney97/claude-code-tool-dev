---
date: 2026-04-04
time: "14:11"
created_at: "2026-04-04T18:11:45Z"
session_id: 5a25e336-ddff-4c44-a44e-8e46f50d1431
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-04_00-49_t4-reclassification-and-path2-benchmark-amendment.md
project: claude-code-tool-dev
branch: main
commit: 58e07db2
title: T6 composition check — three passes to defensible verdict
type: handoff
files:
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/foundations.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - docs/superpowers/specs/codex-collaboration/README.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
  - docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md
  - packages/plugins/cross-model/scripts/event_schema.py
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
---

# Handoff: T6 composition check — three passes to defensible verdict

## Goal

Run the T6 composition check defined at `benchmark-first-design-plan.md:39`:
"consolidate T1-T5 into one consistent benchmark-first design" — done when the
accepted gates compose into a single coherent state model, loop structure, and
synthesis contract; if they do not, the conflicting gates are reopened.

**Trigger:** The prior session completed T4 reclassification and the Path-2
benchmark contract amendment. The handoff's first next step was T6, with three
narrowed questions: (1) do gates compose post-Path-2, (2) is corpus coverage
adequate, (3) are T4 ↔ contract gaps documented.

**Stakes:** Medium-High. T6 is the design gate between accepted T1-T5 designs
and T7 (defining the executable slice). A premature T6 closure pushes design
bugs into implementation. A false T6 failure reopens gates unnecessarily.

**Connection to project arc:** T4 close-out → reclassification → Path-2
encoding → **T6 composition** → T7 executable slice → T8 dry-run → scored
benchmark runs.

## Session Narrative

### Phase 1: Thorough file exploration

Loaded the prior handoff (`2026-04-04_00-49_t4-reclassification-and-path2-
benchmark-amendment.md`). The user asked to proceed with T6 with thorough
exploration.

Read extensively in parallel — the full T4 spec tree (7 modules: foundations,
state-model, scouting-behavior, containment, provenance-and-audit,
benchmark-readiness, boundaries), all five T1-T5 design notes, the benchmark
contract, the risk register, the T7 ticket, the codex-collaboration README,
T4's spec.yaml, and the T6 definition from the archived Codex handoff at
`~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-01_23-38_t5-accepted-
g4-closed-g3-next.md:1099-1121`.

The Codex handoff gave the original T6 questions: (1) Do T1 termination fields
compose with T4 evidence records and T5 mode output? (2) Do T2/T3 claim rules
compose with T4 citation storage? (3) Incompatible state shapes or ordering
assumptions?

### Phase 2: First analysis — overclaimed "T6 satisfied"

Produced a composition analysis structured as three questions (gate composition,
corpus coverage, T4-vs-contract gaps). Concluded "T6 satisfied" with all three
as clean.

User provided Pass 1 scrutiny with 7 findings (4 P1, 3 P2). Every finding was
correct:

- **Gap inventory incomplete** (P1): Omitted T4-BR-01 (T5 migration surfaces),
  T4-BR-03 (allowed-scope safety), T4-BR-04 (claim_provenance_index consumer),
  T4-BR-05 (synthesis-format updates). The live consumers at
  `event_schema.py:137` still show
  `VALID_MODES = {"server_assisted", "manual_legacy"}` — would reject
  `agent_local`.
- **"Fairness preserved" unsupported** (P1): T4-BR-07 item 5 has open
  subrequirements (`scope_envelope`, `allowed_roots` equivalence,
  `source_classes`). Without formalization, fairness is design intent not
  enforcement.
- **Loop structure not reviewed** (P1): Q1 table checked high-level data flow
  but skipped control-to-scout ordering, dual budgets, pending-round emission,
  abandoned-round accounting, one-turn delay.
- **T5→T4 "Clean" is too generous** (P1): T4-BR-01 says missing T5 migration
  surfaces make an `agent_local` benchmark run invalid.
- **B8 enforcement gap** (P2): No `methodology_finding_threshold` means weak
  decomposition has no benchmark consequence.
- **Coverage taxonomy-based not risk-based** (P2): Showing type coverage doesn't
  show the corpus exercises gate-specific failure modes.
- **Anchor-bounded gaming path understated** (P2): Both systems can miss the
  same off-anchor contradiction.

The scrutiny verdict was accurate: "this is not ready as a T6 closeout. It
reads more like 'Path-2 did not obviously break T1-T5' than 'T6 is satisfied.'"

### Phase 3: Second analysis — better but still wrong

Restructured around the three T6 boundaries (state model, loop structure,
synthesis contract). Added the complete gap inventory. Traced loop structure
interactions. Mapped corpus to gate risks rather than types.

But introduced new errors:

- Described scope-breach mid-round exit as a "timing subtlety" with a
  one-turn-lag interpretation that no spec authorizes
- Made T6 closure depend on downstream migration work (collapsing T7/T8 into T6)
- Misread the one-turn delay as applying to all new claims (it's about
  unresolved questions becoming scoutable, per `scouting-behavior.md:71-75`)
- Overclaimed risk coverage ("all 8 exercise G2")
- Misdiagnosed BR-04/05 as missing design (the design exists in T4; the problem
  is split contract authority)

User provided Pass 2 scrutiny with 9 findings (P1: 5, P2: 4). Again correct on
all counts, and crucially identified the scope error: T6 evaluates design
composition, not implementation readiness. The design plan puts implementation
readiness in T7/T8.

### Phase 4: Third analysis — correct scope, defensible verdict

Corrected the scope: T6 asks whether the accepted DESIGNS compose. T7 defines
the executable slice. T8 implements it.

Final verdict:
- **State model: COMPOSES.** No gate reopening needed.
- **Loop structure: COMPOSES with one UNDERSPECIFICATION.** Scope-breach
  mid-round exit semantics are ambiguous between T4-CT-01:30, risk register
  G:74, and T1:98. Not a gate conflict — an orchestration-layer specification
  gap for T7.
- **Synthesis contract: DESIGN COMPOSES, contract authority is SPLIT.** T4's
  extensions (EvidenceRecord, claim_provenance_index, ## Claim Ledger,
  not_scoutable) are additive + declared migrations. No field conflicts. But
  `dialogue-synthesis-format.md` and T4's design docs describe different
  surfaces. Contract reconciliation is T7 work.

Three items deferred to T7. Two global preconditions tracked. User said they
will review and share findings in the next session.

## Decisions

### Decision 1: T6 evaluates design composition, not implementation readiness

**Choice:** Scope T6 to the design plan's definition — do the accepted gate
DESIGNS compose? — rather than checking whether the implementation is ready
for benchmark runs.

**Driver:** `benchmark-first-design-plan.md:38-39` defines T6 as
"consolidate T1-T5 into one consistent benchmark-first design" and T7 as
"define the minimal executable slice." Implementation readiness belongs to T7/T8.
User's scrutiny (Pass 2, finding P1-3) correctly identified that making T6
depend on migration work rewrites the project plan.

**Alternatives considered:**
- **T6 as implementation gate** — check that all consumer surfaces accept the
  new design outputs. Rejected because the design plan explicitly separates
  design consolidation (T6) from executable slice definition (T7).

**Trade-offs accepted:** T6 can close with known consumer surface gaps. The
synthesis contract split and T5 migration set are deferred to T7. Risk: T7
may discover that the synthesis contract reconciliation requires design changes,
which would route back to T6.

**Confidence:** High (E2) — grounded in the design plan text and the user's
scrutiny correction.

**Reversibility:** High — T6's verdict can be revisited if T7 finds design
conflicts during reconciliation.

**What would change this decision:** If the design plan is amended to make T6
responsible for consumer surface readiness.

### Decision 2: Scope-breach mid-round exit is an underspecification, not a gate conflict

**Choice:** Classify the scope-breach exit ambiguity as an orchestration-layer
underspecification to be resolved in T7, rather than a gate conflict requiring
T1 or T4 to be reopened.

**Driver:** Three specs describe the scope-breach exit path differently:
T4-CT-01:30 says mid-round → pending marker → T1 termination; risk register
G:74 says "orchestration-level loop exit"; T1:98 checks `scope_breach_count`
at step 4 (before scouting). Both T1 and T4 are internally consistent —
the gap is in the orchestration layer connecting them.

**Alternatives considered:**
- **Reopen T1** to add an interrupt handler for mid-round scope breach.
  Rejected because T1's ControlDecision algorithm is correct within its scope —
  it just doesn't specify when it evaluates during mid-round events.
- **Reopen T4** to change scope breach to defer to the next T1 evaluation.
  Rejected because T4-CT-01 intentionally describes a mid-round exit, not a
  deferred check.

**Trade-offs accepted:** The ambiguity persists until T7 specifies the
orchestration-layer control flow. If T7 discovers that neither interpretation
works, a gate may need reopening.

**Confidence:** Medium (E1) — grounded in the three spec texts. Haven't
verified that either interpretation produces correct behavior across all edge
cases.

**Reversibility:** High — T7 can reopen gates if the orchestration
specification reveals a design conflict.

**What would change this decision:** T7 finding that the mid-round exit requires
T1's algorithm to change (e.g., adding an interrupt check at step 5b).

### Decision 3: Synthesis contract split is a reconciliation problem, not a design conflict

**Choice:** T4's extensions to the synthesis contract (EvidenceRecord,
claim_provenance_index, ## Claim Ledger, not_scoutable) are additive and
declared. The split between `dialogue-synthesis-format.md` and T4's design
docs is a contract authority problem, not a design conflict.

**Driver:** T4-BD-01 and T4-BD-02 explicitly declare what changes (scout_outcomes
→ EvidenceRecord, new claim_provenance_index field, new ## Claim Ledger section,
not_scoutable vocabulary expansion) and what doesn't change (checkpoint grammar,
pipeline-data scout_count mapping, T3 continuity registry). The extensions are
additive or declared migrations with no field-level conflicts.

**Alternatives considered:**
- **Treat as design conflict requiring T4 gate reopening** — rejected because
  the two documents don't contradict each other. T4 adds surfaces;
  `dialogue-synthesis-format.md` doesn't prohibit them. The problem is that the
  consumer-facing document hasn't been updated, not that the designs disagree.

**Trade-offs accepted:** Two authoritative documents describe different versions
of the synthesis contract until T7 reconciles them. A reader who only reads
`dialogue-synthesis-format.md` would have an incomplete picture.

**Confidence:** High (E2) — verified T4-BD-01/02 declarations against the
existing synthesis format. No field conflicts found.

**Reversibility:** High — reconciliation is additive (merge T4 surfaces into
existing format).

**What would change this decision:** If T7 discovers that T4's extensions
conflict with an unstated invariant in the synthesis format (e.g., if consumers
depend on there being exactly 7 sections, or if the pipeline-data parser
silently drops unknown fields).

## Changes

No repo changes this session. Analysis only.

## Codebase Knowledge

### T6 Authoritative Definition

`benchmark-first-design-plan.md:39`:
> `T6: consolidate T1-T5 into one consistent benchmark-first design` — done
> when: the accepted gates compose into a single coherent state model, loop
> structure, and synthesis contract; if they do not, the conflicting gates are
> reopened

Three explicit composition boundaries. T6 does NOT own implementation readiness
— that's T7/T8.

### T4 Spec Tree Structure

7 modules, all `normative: true`:

| Module | Authority | Lines | Key IDs |
|--------|-----------|-------|---------|
| foundations.md | foundation | 322 | T4-F-01 through F-13. 13 locked decisions |
| state-model.md | state-model | 573 | T4-SM-01 through SM-10. ClaimOccurrence, EvidenceRecord, VerificationEntry, AgentWorkingState |
| scouting-behavior.md | scouting-behavior | 335 | T4-SB-01 through SB-05. Per-turn loop, target selection, query coverage, claim-class scope |
| containment.md | containment | 153 | T4-CT-01 through CT-05. Scope breach, confinement, post-containment capture, safety |
| provenance-and-audit.md | provenance | 415 | T4-PR-01 through PR-14. Evidence trajectory, synthesis-record join, claim ledger, mechanical diff |
| benchmark-readiness.md | benchmark-readiness | 232 | T4-BR-01 through BR-09. Migration surfaces, prerequisite gates, amendment dependencies |
| boundaries.md | boundaries | 58 | T4-BD-01 through BD-03. Non-changes, declared input changes, helper-era migration |

spec.yaml has 6 normative authorities + 2 non-normative (supporting,
boundaries). Boundary rules define cross-authority review triggers.

### Live Consumer Surfaces (Synthesis Contract)

| Surface | File | Current State | T4/T5 Requires |
|---------|------|---------------|-----------------|
| Mode enum | `event_schema.py:137` | `{"server_assisted", "manual_legacy"}` | Add `"agent_local"` |
| Mode source enum | `event_schema.py:139` | `{"epilogue", "fallback"}` | `agent_local` uses `null` (T5:129) |
| Synthesis mode field | `dialogue-synthesis-format.md:86` | `server_assisted` or `manual_legacy` | Add `agent_local` |
| Pipeline-data mode | `dialogue-synthesis-format.md:144` | `"server_assisted"` or `"manual_legacy"` | Add `"agent_local"` |
| Skill parser | `SKILL.md:435` | Accepts only `server_assisted`/`manual_legacy`, falls back to `server_assisted` | Accept `agent_local` |
| Claim trajectory | `dialogue-synthesis-format.md:16` | `new → reinforced/revised/conceded` | Add `not_scoutable` |
| Pipeline-data fields | `dialogue-synthesis-format.md:140-170` | No `claim_provenance_index` | Add per T4-PR-03 |
| Synthesis sections | `dialogue-synthesis-format.md:9` | 7 assembly sections | Add `## Claim Ledger` per T4-PR-05 |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | `evidence_wrapper` strings | `EvidenceRecord` per T4-PR-01 |

### T4-BR Full Inventory

| Blocker | What | Category | Tracked Where |
|---------|------|----------|---------------|
| BR-01 | T5 migration: enum, synthesis format, epilogue, skill parser | Synthesis contract | T5 §6 |
| BR-02 | Transcript fidelity: "raw" undefined, format spec, parser, diff engine | Artifact | T4-F-13 |
| BR-03 | Allowed-scope safety: secret policy, redaction interaction | **Safety** | T4-BR-03 |
| BR-04 | Provenance consumer: `claim_provenance_index` in epilogue, parser, `[ref:]` parser | Synthesis contract | T4-BR-04 |
| BR-05 | Synthesis format: `## Claim Ledger`, `not_scoutable` vocabulary | Synthesis contract | T4-BR-05 |
| BR-06 | Narrative inventory: claim inventory tool, ledger checker, coverage metric | Artifact | T4-BR-06 |
| BR-07.1-4 | Artifact completeness: inventory, methodology format, mode-mismatch, threshold | Artifact | T4-BR-07 |
| BR-07.5 | Scope formalization: `scope_envelope`, `allowed_roots` equivalence, `source_classes` | Comparability | T4-BR-07 (partial: Path-2) |
| BR-07.6-8 | Evidence budget, artifact auditability, omission proof | Comparability/Operational | T4-BR-07 |
| BR-09 | 10 T7 amendment rows | T7 obligations | T4-BR-09 |

BR-01, BR-04, BR-05 are **synthesis contract** gaps that directly relate to
T6's third composition boundary. They are not design conflicts (T4's design
is fully specified) — they are split contract authority.

### Scope-Breach Mid-Round Exit: The Three Specs

| Source | Line | What it says |
|--------|------|--------------|
| T4-CT-01 | containment.md:30 | `scope_breach_count >= 3` mid-round → pending-round marker (T4-SM-09) → T1 termination |
| Risk register G | risk-register.md:74 | "Treat scope_breach_count >= 3 as an explicit orchestration-level loop exit using the same structured termination contract as other exits" |
| T1 algorithm | t1:98 | `if scope_breach_count >= 3: return {conclude, scope_breach}` — evaluated at step 4, before scouting |

The ambiguity: T1's algorithm runs at step 4 (before scouting). T4 describes a
mid-round exit during step 5b (during scouting). The per-turn loop
(T4-SB-01:13-31) has no explicit interrupt point within step 5. Neither spec is
wrong within its own scope — the gap is in the orchestration layer that connects
them.

### Cross-Contract Control Gap

The benchmark contract says evidence anchors define `allowed_roots`
(`dialogue-supersession-benchmark.md:74-76`). T4 containment says `allowed_roots`
come from `scope_envelope` in consultation configuration
(`containment.md:94-100`). The bridge — populating `scope_envelope` from
corpus anchors — is not specified. T4-CT-04 (`containment.md:106-118`) requires
`scope_envelope` for any benchmark run. T4-BR-07 item 5 tracks this as open.
This is a cross-contract gap between benchmark policy and runtime enforcement.

### One-Turn Delay (Corrected Understanding)

`scouting-behavior.md:71-75`: "Unresolved questions become scoutable claims one
turn after Codex responds. At most one lost scout per question cycle."

This applies specifically to **unresolved questions** from Codex, NOT to all
new claims. New extracted claims enter `verification_state` during Phase 2
(step 2c, `state-model.md:113-127`) as `unverified` with `scout_attempts=0`
and are priority-1 targets at step 5a (`scouting-behavior.md:46`) of the **same
turn**.

## Context

### Mental Model

T6 is a **design coherence checkpoint**, not an implementation readiness gate.
The value is catching incompatible state shapes, ordering conflicts, or semantic
contradictions BEFORE defining the executable slice. The scrutiny process
revealed that the hardest part of T6 is correctly scoping it — the temptation
to evaluate implementation readiness (consumer surfaces, live code) instead of
design composition is strong because the live code is visible and the design
composition is abstract.

The three T6 boundaries (state model, loop structure, synthesis contract) map
to different kinds of composition failure:
- **State model:** field-level type conflicts, circular dependencies, dual-write
  hazards
- **Loop structure:** ordering violations, budget interaction bugs, control-flow
  contradictions
- **Synthesis contract:** incompatible output fields, undeclared breaking changes,
  semantic contradictions in what the synthesis contains

### Project State

All D-prime cross-model work (T1-T5) verified end-to-end. T4 closed at SY-13.
Benchmark contract has Path-2 corpus constraint. T6 analysis complete (three
passes). T7 ticket open. Working tree clean on `main` at `58e07db2`.

### Environment

Working in `claude-code-tool-dev` monorepo on `main`. Origin up to date. No
branches open. Analysis-only session — no code changes.

## Learnings

### Scope-breach mid-round exit is an unresolved design specification

**Mechanism:** T4-CT-01:30 describes a mid-round exit path. T1's algorithm
evaluates scope_breach_count at step 4 (before scouting). The per-turn loop has
no explicit interrupt within step 5. Three specs describe the same path
differently without specifying when T1's termination fires relative to mid-round
events.

**Evidence:** T4-CT-01:30 ("pending-round marker → T1 termination"), risk
register G:74 ("orchestration-level loop exit"), T1:98 (step-4 check only).

**Implication:** T7 must specify the orchestration-layer control flow: does the
per-turn loop have an interrupt path for mid-round scope breach, or is T1's
step-4 evaluation the only exit point?

**Watch for:** The resolution may affect abandoned-round accounting (T4-SM-09)
and effort budget consumption (T4-SM-07:454-458) if the interrupt path changes
whether step 5 completes.

### Split contract authority masks as implementation lag

**Mechanism:** When a design spec (T4 provenance-and-audit.md) fully specifies a
new surface (claim_provenance_index wire format, claim ledger grammar) but the
consumer-facing contract (dialogue-synthesis-format.md) doesn't reflect it, the
gap looks like "just update the docs." But the consumer-facing document IS the
contract that implementations code against. Having two authoritative documents
describe different versions of the same surface is split-brain state.

**Evidence:** T4-PR-03 (`provenance-and-audit.md:65-106`) fully specifies the
claim_provenance_index wire format. T4-PR-05 (`provenance-and-audit.md:121-163`)
fully specifies the claim ledger grammar. Neither surface appears in
`dialogue-synthesis-format.md`.

**Implication:** Don't call this "missing design" or "implementation lag" — the
design exists. The problem is that two authoritative sources describe different
versions of the synthesis contract. Reconciliation (merging T4 surfaces into the
consumer-facing format) is the correct action, not re-specification.

**Watch for:** Pointing work at "BR-04/05 design" when the design is already
done. The work is contract reconciliation, not design.

### T6 scope drift toward implementation readiness

**Mechanism:** When evaluating whether designs compose, it's tempting to check
whether the live codebase can execute those designs. The live consumer surfaces
(`event_schema.py`, `SKILL.md` parser) are concrete and checkable. The design
composition is abstract. The result: T6 analysis drifts toward implementation
readiness (which belongs to T7/T8), and the recommended sequence collapses
downstream work into T6 prerequisites.

**Evidence:** Second-pass analysis recommended T5 migration + BR-04/05 design as
"prerequisites for T6 closure." User's scrutiny (Pass 2, finding P1-3)
correctly identified this as silently rewriting the project plan.

**Implication:** When evaluating design composition, anchor to the design plan's
definition. Check whether DESIGNS are compatible, not whether IMPLEMENTATIONS
accept the designs. Defer implementation readiness to the phase that owns it.

**Watch for:** The inverse error — T6 closing too fast by ignoring the synthesis
contract boundary entirely. The correct middle ground: verify that T4's
extensions are compatible with the existing synthesis format DESIGN (they are —
additive + declared migrations), but don't require the consumer implementations
to be updated.

### "Fairness preserved" is design intent until scope formalization lands

**Mechanism:** The benchmark contract says compared runs must be under "the same
conditions" and Path-2 defines per-task `allowed_roots` from evidence anchors.
But T4-CT-04 requires `scope_envelope` with `allowed_roots` in consultation
configuration, and T4-BR-07 item 5 requires `allowed_roots` equivalence between
compared runs. The bridge between anchor-derived roots and runtime scope_envelope
is not specified. Without it, fairness depends on operator discipline.

**Evidence:** `containment.md:94-100` (scope_envelope authority),
`containment.md:106-118` (T4-CT-04 requirement), `benchmark-readiness.md:139`
(item 5 open). `dialogue-supersession-benchmark.md:147-152` (anchors define
allowed_roots for scored runs, but no mechanism for equivalence enforcement).

**Implication:** Don't claim "both systems face the same constraint" without
qualification. Say "design intent, pending enforcement via T4-BR-07 item 5."

**Watch for:** T7 needing to wire scope_envelope population from corpus anchors.
This is a cross-contract bridge, not a single-document amendment.

## Next Steps

### 1. User reviews T6 verdict and shares findings

**Dependencies:** None.

**What to read first:** The final T6 verdict (third pass in this conversation).
Key claims to verify:
- State model composes (no conflicts found)
- Loop structure composes with one underspecification (scope-breach exit)
- Synthesis contract design composes (additive + declared) but authority is split

**User's stated intent:** "I will review that and share my findings in the next
session."

### 2. If T6 verdict accepted: proceed to T7

**Dependencies:** T6 accepted (possibly with modifications from user review).

**What to read first:**
- `benchmark-first-design-plan.md:41-42` (T7 definition: "define the minimal
  executable slice required for a real dry-run")
- The three T7 items from this session's T6 analysis

**T7 must address:**
1. Scope-breach mid-round exit semantics — specify the orchestration-layer
   control flow
2. Synthesis contract reconciliation — merge T4's provenance, claim ledger, and
   `not_scoutable` surfaces into `dialogue-synthesis-format.md`
3. B8 anchor-adequacy decision rule — define when the benchmark operator should
   invoke Change Control to expand B8's path groups

**T7 also picks up two global preconditions:**
- T5 Primary Migration Set (event_schema enum, synthesis format, skill parser)
- scope_envelope ↔ corpus anchor bridge (T4-BR-07 item 5 → T4-CT-04)

### 3. If T6 verdict rejected: address specific findings

**Dependencies:** User's review identifies issues.

**Approach:** Route each finding to the appropriate response:
- Design conflict → reopen the relevant gate
- Underspecification → add to T7 items
- Scope disagreement → discuss T6 definition

## In Progress

Clean stopping point. T6 analysis went through three passes. The third-pass
verdict is the deliverable. No work is in flight.

**State:** `main` at `58e07db2`, origin up to date. Working tree clean. No
branches open. Analysis-only session — no code changes produced.

## Open Questions

1. **Does the user accept the T6 verdict?** The three-pass analysis produced
   a specific disposition (state model composes, loop structure composes with
   one underspecification, synthesis contract design composes but authority is
   split) and three T7 items. The user will review and share findings.

2. **Is the scope-breach exit a T7 item or a gate-reopening?** This session
   classified it as an orchestration-layer underspecification for T7. The user
   may disagree — if the ambiguity is viewed as a T1/T4 conflict rather than an
   orchestration gap, a gate must reopen.

3. **Does B8 need an anchor-adequacy decision rule before T7?** Deferred to T7
   in this analysis, but the user may want it addressed as a benchmark contract
   amendment prerequisite.

## Risks

1. **Scope-breach resolution may require gate reopening.** If T7 discovers that
   the mid-round exit requires changes to T1's algorithm or T4's containment
   contract, work routes back to T6. Risk mitigated by the fact that both specs
   are internally consistent — the gap is in the connector, not the gates.

2. **Synthesis contract reconciliation may surface hidden conflicts.** Merging
   T4's surfaces into `dialogue-synthesis-format.md` may reveal unstated
   invariants (e.g., consumers that drop unknown pipeline-data fields, parsers
   that expect fixed section counts). Risk mitigated by T4-BD-01/02's explicit
   change declarations.

3. **Three-pass analysis may have residual errors.** Each scrutiny round found
   errors in the prior pass. The user's next-session review may find issues in
   the third pass that this analysis missed. Calibration note: the first pass had
   structural gaps (wrong scope, missing inventory); the second pass had factual
   errors (one-turn delay, scope-breach characterization, BR-04/05 misdiagnosis);
   each round was better than the last.

## References

| What | Where |
|------|-------|
| T6 authoritative definition | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:38-39` |
| T6 original questions (Codex) | `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-01_23-38_t5-accepted-g4-closed-g3-next.md:1099-1121` |
| T4 spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| T4 spec.yaml | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| T1 design note | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` |
| T2 design note | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| T3 design note | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |
| T5 design note | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| T7 ticket | `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` |
| Event schema (live) | `packages/plugins/cross-model/scripts/event_schema.py` |
| Synthesis format (live) | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` |
| Dialogue skill (live) | `packages/plugins/cross-model/skills/dialogue/SKILL.md` |
| Prior session handoff | `docs/handoffs/archive/2026-04-04_00-49_t4-reclassification-and-path2-benchmark-amendment.md` |

## Gotchas

1. **T6 definition is in the design plan, not in T4 or the Codex handoff.** The
   authoritative T6 definition is at `benchmark-first-design-plan.md:39`. The
   Codex handoff (`2026-04-01_23-38_t5...md:1099-1121`) provides additional
   questions but is not the authoritative scope. The design plan owns T6's
   done-when criteria.

2. **One-turn delay applies to unresolved questions, not all new claims.**
   `scouting-behavior.md:71-75` specifically says "Unresolved questions become
   scoutable claims one turn after Codex responds." New extracted claims are
   scoutable in the same turn via Phase 2 registration → priority-1 target
   selection.

3. **BR-04/05 design is done — the problem is contract authority.** T4-PR-03
   fully specifies claim_provenance_index wire format. T4-PR-05 fully specifies
   claim ledger grammar. Don't treat these as "design needed" — treat them as
   "contract reconciliation needed" (merge into
   `dialogue-synthesis-format.md`).

4. **Mode migration is a global precondition, not per-task.** Either `agent_local`
   works end-to-end (event schema → synthesis format → skill parser) or no
   candidate benchmark run produces valid analytics events. Don't frame this as
   something individual corpus rows exercise.

5. **Risk coverage is structural, not empirical.** All 8 corpus tasks go through
   the same per-turn loop, so all tasks touch T1-T5 gate mechanics. But no task
   is designed to force specific edge cases (fallback-claim creation, referential
   failure, scope-breach exit, budget-edge behavior). Edge-case calibration is
   T7/T8 dry-run work.

## Conversation Highlights

**Three-pass refinement:** The T6 analysis went through three complete passes,
each triggered by structured adversarial review from the user. Each pass was
materially better than the last:
- Pass 1: Structural gaps (wrong scope, missing inventory). Verdict too generous.
- Pass 2: Factual errors (one-turn delay, scope-breach characterization, BR-04/05
  misdiagnosis). Scope drift toward implementation readiness.
- Pass 3: Correctly scoped to design composition with defensible verdicts.

**The critical scope correction:** Pass 2's recommended sequence made T6 depend
on T5 migration + BR-04/05 design work. The user's scrutiny identified this as
silently rewriting the project plan. The correction — T6 evaluates design
composition, T7 owns implementation readiness — was the most important insight
of the session.

**Adversarial review structure:** User provided two passes per scrutiny round,
each finding labeled with severity (Critical/High/Medium) and line citations.
Findings were always correct. The "what survives scrutiny" closing paragraph
acknowledged what was right before stating what was wrong.

## User Preferences

**Provides structured adversarial reviews.** Two passes (P1, P2) with severity
labels and specific file:line citations. Closing paragraph identifies what
survives scrutiny.

**Expects correct scope definition.** T6 is design composition, not
implementation readiness. The user catches and corrects scope drift.

**Values evidence-backed analysis.** Every finding in the scrutiny cited specific
file paths and line numbers. Analysis that makes claims without citations is
considered "inference, not proof."

**Reviews findings in subsequent sessions.** User said: "I will review that and
share my findings in the next session." This means the T6 verdict is not
final until the user reviews it.

**Writes substantive amendments themselves.** Consistent with prior sessions:
for both the reclassification and the Path-2 amendment, the user authored
doc changes. Claude's role is analysis, verification, and review.

**Works in closed units with clear scope boundaries.** Each scrutiny round
maintained a clear boundary between what T6 owns and what belongs to T7/T8.
