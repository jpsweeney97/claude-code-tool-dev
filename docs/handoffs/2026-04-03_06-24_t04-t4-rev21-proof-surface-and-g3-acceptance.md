---
date: 2026-04-03
time: "06:24"
created_at: "2026-04-03T06:24:05Z"
session_id: 942db47c-77eb-457c-9ec4-1965f7845a64
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_04-47_t04-t4-rev20-scope-control-and-integration-alignment.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 9a1edacd
title: "T-04 T4 rev 21 — proof-surface architecture, G3 acceptance, conceptual-query ADR"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
  - docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md
  - docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md
---

# Handoff: T-04 T4 rev 21 — proof-surface architecture, G3 acceptance, conceptual-query ADR

## Goal

Apply rev 21 to the T4 design contract, achieve G3 acceptance through hostile review, and resolve the conceptual-query viability risk that could block scored benchmark runs.

**Trigger:** Prior session ended with rev 20 (amended) applied — `scope_root_rationale` removed, justification prohibited, all surfaces unified. User's hostile review was the entry point for this session.

**Stakes:** G3 (evidence provenance retention) was the last unaccepted hard gate. G1, G2, G4, G5 were all `Accepted (design)`. G3 acceptance unblocks T6 composition check and the final design sign-off.

**Success criteria:** Rev 21 achieves "Defensible" verdict in hostile review. G3 moves to `Accepted (design)`. Conceptual-query viability risk resolved with a concrete T7 path.

**Connection to project arc:** T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). T4 is a parallel prerequisite for T6. G3 acceptance was the last gate blocking design sign-off.

## Session Narrative

### Phase 1: User hostile review of amended rev 20 (review round 1)

Loaded the prior handoff (rev 20 scope control and integration alignment). User delivered their hostile review of the amended rev 20. The review found **no critical failures** in scope control — the `scope_root_rationale` removal and justification prohibition landed correctly. But it found a new defect category: **readiness under-specification**.

The critical finding: parser/diff not in the scored-run blocker set. The note at L1486 claimed mechanical diff was "always available, not gated" while the parser/diff engine that produces it was explicitly listed as "separate T7 deliverables" outside the scored-run prerequisites. The note's strongest audit surface — authoritative omission detection — was specified but not required to exist before scored runs proceeded.

User's required changes: (1) add parser/diff to scored-run prerequisites, (2) update checklist item 32, (3) reconcile "always available" language, (4) make conceptual-query blocker explicitly non-decaying.

### Phase 2: Rev 21 first pass (10 edits)

Proposed 4 changes (A, B, C, D). User counter-reviewed with 2 corrections: §5.3 not §5.1 for omission surface reference, and item 70 needed parser/diff as a distinct final entry not tacked onto item 7's clause. Applied all 10 edits in parallel — rev 21 at 2408 lines.

Changes: new prerequisite item 8 (parser/diff operational), runner clause (1)-(8), "all eight" dependencies, category explanation (operational readiness), "always available" reconciled, verification cross-reference, checklist item 32 (full §3.9 dependency), checklist item 70 (distinct 8th entry), conceptual-query blocker (non-decaying), rev history.

### Phase 3: Second hostile review — prose-model lag (review round 2)

User's verdict: **minor revision**. First "minor" in the cycle. Found §3.9 opening paragraph still said "T4 implementation MUST NOT proceed" (blanket blocker contradicting the graduated readiness model), and auditability amendment row missing harness toolchain identity. Applied 4 edits: §3.9 graduated model, auditability row + item 7 harness toolchain, rev history.

### Phase 4: Third hostile review — runner enforcement gap (review round 3)

User found checklist item 70 dropped harness toolchain identity, and runner clause overclaimed manifest-validator enforceability for item 8 (operational machinery can't be proved from metadata alone). Applied 4 edits: item 70 harness toolchain, runner split ((1)-(7) manifest-verifiable, (8) runner-only), item 70 enforcement distinction, rev history.

### Phase 5: Fourth hostile review — proof-surface completeness (review round 4)

**Key pivot in the session.** User escalated from minor to **major revision**. The review found the note still couldn't prove the omission machinery actually ran for a scored run. "Runner-only trust is exactly what the auditability row says must not be load-bearing." The note claimed post-hoc auditability but delivered runtime trust.

This was a deeper architectural issue than prior rounds: the note needed a **derived proof surface** — an artifact that proves the parser/diff ran on the specific scored transcript, not just that it was operational when the runner started.

I proposed Option A (derived omission-audit artifact) over Option B (execution attestation marker). User counter-reviewed with 6 findings that tightened the proof model: (1) artifact must be run-bound, not just present; (2) evidence-record keyed, not per-claim; (3) success semantics needed, not just presence; (4) non-scoring run classification needed; (5) don't reopen ownership leak — T4 defines floor, T7 owns schema; (6) scale trap with naive content duplication.

Applied 12 edits in parallel — the largest single batch of the session:
- New §6.2 amendment row (derived omission-audit proof surface with 4-part contract floor)
- Item 8 recast from "operational" to "produce the proof surface" with acceptance test
- Runner enforcement unified: (1)-(8) all manifest-verifiable via proof artifact
- Non-scoring run classification: exploratory vs policy-influencing
- Mirror alignment: benchmark config version/digest, "run transcript" across surfaces
- §3.9 non-scoring reference updated

### Phase 6: Fifth hostile review — support-surface lag (review round 5)

User's verdict: **minor revision**. Found 4 remaining issues: (1) proof-surface completeness clause conflicted with synthesis-used scope — `claim_provenance_index` retains historical entries but omission surface is only for synthesis-used records; (2) no validator-grade schema dependency for proof surface; (3) threshold-setting bootstrap loop in calibration classification; (4) checklist item 70 still used old "operational" wording. Applied 5 edits.

### Phase 7: Sixth hostile review — Defensible (review round 6)

**Verdict: Defensible.** First acceptance in the entire review cycle. No critical failures. No high-risk assumptions in reviewed surfaces. The prior runtime-trust gap was closed by item 8 + proof surface. Remaining risk is external (T7 benchmark contract amendments), not internal.

### Phase 8: G3 acceptance

Committed rev 21 at `214ef168`. Read the risk register gate model. Presented G3 acceptance argument: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface — all satisfied by T4 rev 21. Updated risk register: G3 from `Proposed (source analysis)` to `Accepted (design)` with satisfying artifact. Committed at `dd14aab4`.

### Phase 9: Conceptual-query viability resolution

User identified this as the highest-leverage remaining risk. I presented 3 paths: all-roots, corpus design constraint, record-but-don't-compare. User recommended **Path 2 (corpus design constraint)**: scored runs exclude ambiguous conceptual multi-root queries, T7 satisfies the blocker through task design not algorithm invention. Key rationale: "for scored benchmark runs, comparability outranks coverage."

User created the ADR at `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md` (gitignored locally). I created the T7 execution ticket at `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` and committed at `9a1edacd`.

## Decisions

### Derived omission-audit proof surface (new §6.2 amendment row)

**Choice:** Require T7 to persist a derived omission-audit artifact for each scored run. Contract floor: (a) run binding — `run_id`, transcript digest, toolchain identity; (b) evidence-record keyed — one entry per evidence record used in synthesis, referencing uncited matches by path/line spans/digests; (c) completeness — every synthesis-active scouted evidence record has a corresponding entry, no unresolved extraction failures; (d) manifest binding — artifact digest in `manifest.json`/`runs.json`. T4 defines floor; T7 owns schema, storage, naming.

**Driver:** User: "The document still cannot prove that the load-bearing omission machinery actually ran for a scored run... Runner-only trust is exactly what the auditability row says must not be load-bearing."

**Rejected alternatives:**
- (a) **Execution attestation marker** — runner writes metadata record (digest, version, success). Rejected because it attests to invocation but doesn't persist output. A reviewer still can't verify what the machinery produced without re-running.
- (b) **Runtime-trust with better paperwork** — user's phrase for any approach that records metadata about the machinery without proving it ran on this transcript. "That is still runtime trust, not a real proof surface."
- (c) **Per-claim artifact** — I initially described completeness as "per claim" but the omission surface is defined per evidence record (L1405). User caught this: "Those are not the same set, because `claim_provenance_index` retains historical and conceded scouted claims."

**Trade-offs:** Adds a T7 obligation (new artifact + validator-grade schema). T7's implementation complexity increases. Accepted because without the proof surface, the note's claimed post-hoc auditability is false.

**Confidence:** High (E2) — validated through 3 hostile review rounds. The proof-surface concept survived counter-review for run binding, completeness scope, success semantics, scale trap, and ownership boundary.

**Reversibility:** Medium — the amendment row defines a contract floor, not an implementation. T7 can implement it however it wants. But removing the proof requirement would reopen the runtime-trust gap.

**Change trigger:** If the benchmark decides runner trust is acceptable (unlikely given the auditability row's own stated goal of eliminating operator testimony as a dependency).

### Runner enforcement unification: (1)-(8) all manifest-verifiable

**Choice:** Reverse the earlier "(1)-(7) manifest, (8) runner-only" split. With the proof surface, item 8 is now manifest-verifiable: the runner produces the artifact, the manifest records its digest, and a post-hoc validator confirms run binding and completeness.

**Driver:** The proof surface's existence makes item 8 artifact-verifiable, not just runtime-verifiable. The earlier split was correct when item 8 had no artifact; it became wrong once the proof surface was added.

**Rejected alternatives:**
- (a) **Keep the split** — maintain "(1)-(7) manifest, (8) runner-only" even with the proof surface. Rejected because it would understate the enforcement model — a validator can now check item 8 from artifacts.

**Trade-offs:** The manifest validator now needs to understand the proof surface artifact (artifact digest check, completeness validation). Accepted because that's the point — mechanical verification over trust.

**Confidence:** High (E2) — the proof surface's manifest binding (part d of the contract floor) explicitly enables this.

**Reversibility:** High — editorial change to runner clause text.

**Change trigger:** If the proof surface is removed or downgraded (which would reopen the runtime-trust gap).

### Non-scoring run classification: exploratory vs policy-influencing

**Choice:** Split non-scoring runs into two classes: (a) exploratory shakedowns — permitted before any prerequisites, non-evidentiary, MUST NOT inform benchmark policy; (b) policy-influencing calibration — requires all eight prerequisites because their conclusions shape the benchmark's rules. Exception: initial `methodology_finding_threshold` is a benchmark contract decision (T7-owned), not a calibration output.

**Driver:** User: "non-scoring runs are still permitted before the parser/diff machinery is operational, but the note only forbids using them for pass/fail comparisons. It does not forbid them from steering calibration, policy, or threshold decisions."

**Rejected alternatives:**
- (a) **Single class with pass/fail restriction** — the previous model. Rejected because it allows pre-readiness observations to shape the benchmark's rules even when barred from the scored aggregate.
- (b) **No pre-readiness runs at all** — too restrictive; exploratory shakedowns are valuable for format/schema testing without policy influence.

**Trade-offs:** Policy-influencing calibration (e.g., `not_scoutable` rate validation) now requires all 8 prerequisites, which means full §3.9 machinery must be operational before calibration can inform criteria tuning. This delays the calibration timeline.

**Confidence:** Medium (E1) — the threshold bootstrap exception was caught by the user and resolved, but the boundary between "exploratory" and "policy-influencing" may need further precision during T7 implementation.

**Reversibility:** Medium — the classification is in §6.2 text and checklist item 70. Changing it requires updating both surfaces.

**Change trigger:** T7 discovering that the all-prerequisites requirement for calibration is impractical, which would require negotiating a middle ground.

### Conceptual-query scope constraint: corpus design for benchmark v1

**Choice:** Scored benchmark v1 excludes ambiguous conceptual multi-root queries. T7 satisfies the T4 blocker through corpus design constraints: conceptual queries must be single-root by construction or path-anchored after decomposition. All-roots available as experimental branch only. "Record but do not compare" rejected.

**Driver:** User: "For scored benchmark runs, comparability outranks coverage. I do not think a 'smart' selective rule is likely to be both faithful and mechanically enforceable without slipping back into agent-judgment trust."

**Rejected alternatives:**
- (a) **All-roots requirement** — deterministic and enforceable, but "creates benchmark cost driven by rule design rather than system quality." Kept as experimental branch, not base rule.
- (b) **Record but do not compare** — user: "structurally incoherent. If conceptual multi-root scope choices still affect what the candidate sees, they still affect the scored output." Collapses back to Path 2 once you follow the consequence chain.
- (c) **Invent a validator-enforceable selection algorithm** — user: "I do not think a 'smart' selective rule is likely to be both faithful and mechanically enforceable without slipping back into agent-judgment trust."

**Trade-offs:** Benchmark v1 gives up some coverage in exchange for clean comparability. Some realistic task shapes are pushed out of scored v1.

**Confidence:** High (E2) — user's assessment independently reached the same conclusion as the T4 note's analysis. Path 3 was rejected for structural incoherence, not preference.

**Reversibility:** Medium — the ADR records the decision, but it constrains T7's task design and benchmark contract amendments. Reversing would require a new benchmark version.

**Change trigger:** Experimental all-roots branch demonstrating that the budget and evidence surfaces remain usable under the cost pressure.

### G3 acceptance

**Choice:** Move G3 from `Proposed (source analysis)` to `Accepted (design)` based on T4 rev 21 at `214ef168`.

**Driver:** T4 rev 21 satisfies all three required design outcomes: fixed scout-capture point (§3.3, §3.6), per-scout evidence record schema (§3.1 ScoutStep, §5.2 claim_provenance_index), synthesis citation surface (§5.1 claim ledger, §5.2 provenance index, §5.3 mechanical omission diff + proof surface). Hostile review verdict: Defensible after 6 rounds.

**Rejected alternatives:**
- (a) **Wait for T7 amendments before accepting** — rejected because G3 is a design gate, not an implementation gate. The T7 dependencies are external to the design acceptance criterion.
- (b) **Promote directly to Resolved (design)** — rejected because `Resolved (design)` means "final design locks exact contract, algorithm, dependency ordering." The T7 amendment rows are not yet absorbed into the benchmark contract.

**Trade-offs:** G3 is accepted with known external dependencies (10 amendment rows for T7). The design is internally defensible but not yet executable as a benchmark contract.

**Confidence:** High (E2) — validated through 6 hostile review rounds with progressively narrower defect categories.

**Reversibility:** Low — accepting G3 unblocks T6 composition check and downstream work. Reverting would require re-review.

**Change trigger:** Discovery of an internal contradiction in the T4 design that wasn't caught in the 6 review rounds (unlikely given the narrowing defect trajectory).

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — Rev 21

**Status:** Committed at `214ef168`. 2441 lines (up from 2390 at rev 20 amended, +51 net / +262 insertions, -74 deletions).

**Rev 21 changes (18 numbered, across 4 amendment passes):**

| # | What changed | Where |
|---|-------------|-------|
| 1 | Parser/diff as scored-run prerequisite (item 8) | §6.2 |
| 2 | "Always available" reconciled to "not gated by agent choices; requires operational §3.9" | §5.3 reviewer workflow |
| 3 | Checklist item 32: full §3.9 dependency shape | Checklist |
| 4 | Conceptual-query blocker: explicitly non-decaying | §4.6 |
| 5 | Verification sentence cross-references item 8 | §3.9 |
| 6 | §3.9 opening: graduated readiness model (spec sub-dependency vs operational readiness) | §3.9 |
| 7 | Harness toolchain identity in auditability (item 7, amendment row) | §6.2 |
| 8 | Runner enforcement split → later reversed in (12) | §6.2 |
| 9 | Checklist item 70 harness toolchain + enforcement distinction | Checklist |
| 10 | Derived omission-audit proof surface (new amendment row, 4-part contract floor) | §6.2 |
| 11 | Item 8 recast: acceptance test = proof surface + run binding + completeness | §6.2 |
| 12 | Runner enforcement unified: (1)-(8) all manifest-verifiable | §6.2 |
| 13 | Non-scoring run classification: exploratory vs policy-influencing | §6.2, §3.9, item 70 |
| 14 | Mirror alignment: benchmark config version/digest, "run transcript" | Item 7, amendment row, item 70 |
| 15 | Proof-surface completeness scoped to synthesis-active records (per §5.3) | Amendment row |
| 16 | Validator-grade schema dependency for proof surface | Amendment row |
| 17 | Threshold bootstrap: initial value is T7 benchmark contract decision | §6.2 non-scoring |
| 18 | Checklist item 70 item-8 mirror: proof-surface production with acceptance test | Checklist |

### `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` — G3 accepted

**Status:** Committed at `dd14aab4`.

G3 row updated from `Proposed (source analysis)` to `Accepted (design)` with satisfying artifact reference: T4 rev 21 at `214ef168` (2441 lines, 70-item checklist, 8-item scored-run prerequisite block, derived omission-audit proof surface). Hostile review verdict: Defensible.

### `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md` — ADR (local)

**Status:** Local only (gitignored). Created by user.

Records the benchmark-v1 decision: scored runs exclude ambiguous conceptual multi-root queries. T7 satisfies the T4 blocker through corpus design constraints. All-roots as experimental branch. "Record but do not compare" rejected.

### `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` — T7 ticket

**Status:** Committed at `9a1edacd`. T-20260403-01.

T7 execution ticket: amend benchmark contract run conditions for scored-corpus constraint, review 8 benchmark tasks for conceptual multi-root exposure, design decomposition paths, validate benchmark v1 coverage adequacy.

## Codebase Knowledge

### T4 design contract structure (2441 lines, rev 21)

Key sections and their current line ranges (approximate — may shift slightly from the 18 edits):

| Section | Lines (approx) | Key surfaces |
|---------|-------|-------------|
| Revision history | L9-34 | 21 revision entries |
| §1 Decision | L36-44 | Core design choices |
| §3.1 ScoutStep schema | L366-378 | scope_root: str (no rationale field) |
| §3.5 Agent working state | L569-599 | Budget gates, max_evidence as benchmark parameter |
| §3.9 Transcript fidelity | L700-720 | Graduated readiness model (spec sub-dependency vs operational) |
| §4.4 Scout query coverage | L809-873 | Query diversity with adjudicator backstop |
| §4.6 Containment | L899-941 | scope_root derivation (3 cases), conceptual-query blocker (non-decaying) |
| §5.2 Provenance index | L1157-1241 | Wire format, claim_id equality invariant |
| §5.3 Omission surface | L1387-1500 | Mechanical diff, reviewer workflow, proof surface reference |
| §6.1 Transcript fidelity deps | L1571-1600 | 4 dependency rows, spec sub-dependency verification |
| §6.2 Prerequisites | L1635-1710 | 8 items, 3 categories, runner clause, non-scoring classification |
| §6.2 Amendment table | L1695-1731 | 10 amendment rows including proof surface |
| §8 Verification checklist | L2111-2441 | 70 items, items 32/42/57/64/68/70 updated in rev 21 |

### Cross-surface alignment status (rev 21 final)

Three load-bearing surfaces for scope formalization are now aligned:

| Surface | What it says | Aligned? |
|---------|-------------|----------|
| Prerequisite item 5 | "selection rule for all query types including conceptual queries" | Yes |
| Amendment row | "selection rule for all query types" + justification prohibition | Yes |
| Checklist item 70 | "selection rule for all query types" | Yes |

### Prerequisite block structure (8 items, 3 categories)

| Category | Items | Enforcement | What they gate |
|----------|-------|-------------|---------------|
| Artifact completeness | 1-4 | Manifest-verifiable | Schemas and formats exist |
| Comparability and auditability | 5-7 | Manifest-verifiable | Rules are defined, metadata recorded |
| Operational readiness + proof | 8 | Runner + manifest (via proof surface) | Machinery ran, artifact proves it |

### Amendment table (10 rows in §6.2)

| Row | Surface | Owner |
|-----|---------|-------|
| 1 | Methodology finding format | T7 |
| 2 | Methodology finding consequence | T7 |
| 3 | Adjudication scope | T7 |
| 4 | Mode-mismatch failure artifact | T7 |
| 5 | Benchmark-run scope formalization | T7 |
| 6 | Evidence budget parameter | T7 |
| 7 | Benchmark artifact auditability | T7 |
| 8 | Omission-audit proof surface | T7 |
| 9 | Allowed-scope safety | T7 |
| 10 | Transcript format/parser/diff | T7 |

### Risk register gate model

| Status | Meaning |
|--------|---------|
| `Proposed (source analysis)` | Candidate resolution in review material only |
| `Accepted (design)` | Design chosen, state/output shape named |
| `Resolved (design)` | Final contract locked, verification plan linked |

All 5 gates now at `Accepted (design)`. Design sign-off condition met. T6 composition check unblocked.

## Context

### Mental Model

This session's core problem evolved through 6 review rounds:

**Starting frame (rev 20):** Readiness under-specification — the note correctly names dependencies but the blocker ledger doesn't force every component its audit story depends on.

**Middle frame (rounds 2-3):** Prose-model lag — older text written under a simpler blocker model hasn't been updated to match the graduated readiness system.

**Final frame (rounds 4-6):** Proof-surface completeness — the note's claimed post-hoc auditability depended on runtime trust. The fix: a derived artifact whose existence *is* the proof that the machinery ran.

The general principle: **declaring requirements is necessary but insufficient for a benchmark; artifacts must carry the proof.** This is the difference between a specification (what must be true) and a verifiable contract (how a later reviewer proves it was true).

### Convergence trajectory

Defect categories narrowed monotonically across the full review cycle (revisions 11-21):

| Rev | Category | Verdict |
|-----|----------|---------|
| 11-14 | Structural gaps, surface contracts, closure, internal consistency | Critical |
| 15 | Pipeline boundary | Critical (1) |
| 16 | Enforcement weight | High (2) |
| 17 | Consequence machinery | Self-review |
| 18 | Authority overreach | Reject |
| 19 | Comparability/auditability gaps | Reject |
| 20 first | Cross-surface integration, explanation-vs-control | Reject (2 critical) |
| 20 amended | Readiness under-specification | Major revision |
| **21 round 1** | Prose-model lag | Minor revision |
| **21 round 2** | Runner enforcement gap | Minor revision |
| **21 round 3** | Proof-surface completeness | Major revision |
| **21 round 4** | Support-surface lag | Minor revision |
| **21 round 5** | — | **Defensible** |

### Project State

| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Accepted (design)** | **T4: scouting position and evidence provenance** |

## Learnings

### A derived proof artifact is stronger than an execution attestation

**Mechanism:** When machinery is load-bearing for post-hoc audit, recording that it ran (attestation) is weaker than persisting what it produced (proof). An attestation depends on trusting the runner's claim; a derived artifact can be independently verified.

**Evidence:** The user's hostile review exposed that "runner-only trust is exactly what the auditability row says must not be load-bearing." The proof surface's existence proves execution, its content proves correctness, and its manifest digest proves integrity.

**Implication:** For any future benchmark surface claimed as "post-hoc auditable," verify that the audit chain ends in an artifact, not a runtime gate. If the chain terminates at "the runner checked," the audit claim is false.

**Watch for:** The pattern "we recorded the version, so it's auditable" — version metadata proves identity, not execution. The proof surface pattern (derived artifact with run binding) is the stronger model.

### Defect categories narrow monotonically in converging specifications

**Mechanism:** Each hostile review round finds the deepest remaining defect class. If the specification is converging, each round's category is strictly narrower than the last. The trajectory from structural → enforcement → authority → comparability → readiness → proof serves as a health signal.

**Evidence:** The T4 review cycle from rev 11 to rev 21 followed this exact pattern. When rev 21 round 3 escalated to "major" (proof surface), it was still a narrower category (proof-surface completeness) than the prior round's finding (prose-model lag vs. proof-surface completeness).

**Implication:** If a hostile review finds a defect in a *broader* category than the previous round, something regressed. Use the category trajectory as a convergence metric.

**Watch for:** Reviews that appear to converge (minor, minor, minor) but are actually finding the same category repeatedly — that's oscillation, not convergence.

### "Plausibly covers" and similar soft language are red flags in normative specification text

**Mechanism:** When writing specification rules, test each adjective/adverb for determinism: can two conforming implementations reach different conclusions given the same inputs? If yes, the word is judgment disguised as a rule.

**Evidence:** User caught "plausibly covers" immediately: "That phrase is just rationale smuggled back in as prose." This led to the Path A decision (remove `scope_root_rationale`, require deterministic selection only).

**Implication:** Words like "relevant," "appropriate," "suitable," "reasonable," "plausible" in normative text should be either (a) replaced with mechanical definitions or (b) explicitly deferred to an authority that will define them.

**Watch for:** New normative text introduced during integration or amendment writing that re-introduces soft language.

### Non-authoritative explanation fields are not comparability controls

**Mechanism:** A field explicitly labeled "non-authoritative — agent explanation, not proof" cannot serve as the sole control for benchmark comparability. The benchmark needs to verify that two runs made equivalent choices; a non-authoritative field only tells the benchmark what the agent claims about its choice.

**Evidence:** `scope_root_rationale` was added to ScoutStep and removed in the same revision. User: "the system that writes defensible rationales can outperform the system that actually searched more honestly." The general principle: if the field only makes the agent explain itself rather than constraining its behavior, it belongs in debugging instrumentation, not the benchmark's control path.

**Implication:** Any field labeled "non-authoritative" in the audit inventory should not appear in the control path. This applies broadly to benchmark design.

**Watch for:** Future revisions that use audit fields as control mechanisms — the pattern is: "we need the agent to explain X" → "let's add a field for X" → "now let's require X in the audit path."

## Next Steps

### 1. T6 composition check

**Dependencies:** All 5 gates at `Accepted (design)`.

**What to read first:** The T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` — T6 is described there. It checks whether the 5 accepted design contracts compose coherently.

**Approach:** T6 should verify that the T1-T5 contracts don't contradict each other and that the end-to-end pipeline (extraction → scouting → synthesis → benchmark adjudication) has no gaps.

### 2. T7 conceptual-query corpus design constraint (T-20260403-01)

**Dependencies:** ADR at `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`.

**What to read first:** The ticket at `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md`. Then the benchmark contract at `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` to review existing task definitions.

**Approach:** Review all 8 benchmark tasks for conceptual multi-root exposure. Design decomposition paths for tasks that can be restructured. Exclude tasks that cannot satisfy the constraint.

### 3. Post-acceptance modular split with /superspec:spec-writer

**Dependencies:** G3 accepted, rev 21 committed.

**What to read first:** The T4 design contract (2441 lines). At this size, a modular split into `spec.yaml` + per-section files would improve navigability.

**Approach:** Use `/superspec:spec-writer` to create the modular structure. The T4 note is now stable enough for this — the hostile review cycle is complete.

## In Progress

**Clean stopping point.** Rev 21 committed, G3 accepted, conceptual-query ADR created, T7 ticket filed. No work in flight.

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Uncommitted changes: none.

## Open Questions

1. **Does the conceptual-query corpus constraint narrow benchmark v1 coverage too much?** The ADR accepts this tradeoff, but the T6 composition check should validate that benchmark v1 scenarios remain adequate after excluding ambiguous conceptual multi-root cases.

2. **When should the modular split happen?** Document at 2441 lines. Post-acceptance split with `/superspec:spec-writer` was the plan. The review cycle is now complete, making this a good time.

3. **Should `docs/decisions/` be un-gitignored?** The conceptual-query ADR is local-only because `docs/decisions/` is in `.gitignore`. The T7 ticket references it but the ADR itself isn't version-controlled.

## Risks

### T7 amendment absorption is the bottleneck

The live benchmark contract still has not absorbed the 10 T7-owned amendment rows from T4. Benchmark readiness requires all amendments to land. T4 is now honest about this dependency chain, but the actual work is on T7's side.

**Mitigation:** T7 ticket (T-20260403-01) created for the highest-priority item (conceptual-query corpus constraint). Remaining amendments need similar execution tracking.

### Conceptual-query viability under all-roots experimental branch

If the experimental all-roots branch shows unacceptable cost (budget distortion, evidence surface degradation), there may be no broader scored rule for future benchmark versions. Conceptual multi-root tasks would remain permanently excluded from scored comparisons.

**Mitigation:** The ADR frames this as an open question for future evaluation, not a commitment.

### Document size (2441 lines)

The T4 design contract is large and growing. At this scale, cross-surface integration defects become harder to catch visually. The modular split will help but hasn't happened yet.

**Mitigation:** Post-acceptance `/superspec:spec-writer` split is planned.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | Rev 21, 2441 lines, Defensible verdict |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 status, gate acceptance criteria |
| Conceptual-query ADR | `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md` | Benchmark v1 scope constraint (local, gitignored) |
| T7 execution ticket | `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` | Corpus design constraint implementation |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Run conditions, artifacts, change control |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope transport, allowed_roots |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Design review report | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` | 22 canonical findings from self-review |

## Gotchas

### The runner enforcement split was applied and then reversed in the same revision

Rev 21 changes 8-9 split enforcement into "(1)-(7) manifest-verifiable, (8) runner-only." Changes 12 reversed this after the proof surface was added, unifying all 8 as manifest-verifiable. The reversal was architecturally correct — the proof surface's manifest binding enables post-hoc validation. Future editors should not re-introduce the split unless the proof surface is removed.

### `docs/decisions/` is gitignored

The conceptual-query ADR exists locally only. The T7 ticket references it but the ADR itself isn't version-controlled. If the decision needs to be shared across machines or developers, either un-gitignore `docs/decisions/` or move the ADR to a tracked location.

### Proof-surface completeness is scoped to synthesis-active records, not all provenance entries

`claim_provenance_index` retains historical and conceded entries (L1226-1229). The omission surface is defined for "every evidence record used in the synthesis" (L1405). The proof surface's completeness clause aligns to the synthesis-used set, not all historical entries. If a future revision changes the omission surface scope, the proof surface completeness clause must match.

### Parallel edits to the T4 design contract work when anchor text is unique and non-overlapping

This session applied up to 12 edits in a single parallel batch to the 2400+ line file. All succeeded because each edit's old_string was unique and the edits targeted non-overlapping regions. When editing long table-cell content in amendment rows, use specific phrases from within the cell (not the full cell) as anchors.

## User Preferences

**Scope discipline — commit before continuing:** User: "commit rev 21 first, then proceed toward formal G3 acceptance. Reasoning: rev 21 now looks like a coherent, defensible checkpoint. If you keep editing before freezing this state, you risk reopening a note that is finally internally coherent."

**Comparability over coverage:** User: "for scored benchmark runs, comparability outranks coverage." This principle drove the conceptual-query decision (Path 2) and echoes the `scope_root_rationale` removal — preferring enforceable constraints over broader coverage under weaker controls.

**Counter-review pattern (confirmed):** Structured findings with priority levels ([P1], [P2], [Critical], [High], [Medium]). The user applies progressively deeper adversarial perspectives across rounds. Named reviewer personas: benchmark runner implementer, schedule-pressured benchmark maintainer, post-hoc auditor, candidate team optimizing dry runs, validator implementer, checklist-driven reviewer.

**Authority-boundary enforcement (confirmed):** User: "Be careful not to reopen the ownership leak you just spent several rounds removing." T4 defines contract floors; T7 owns schemas, implementations, and artifact naming.

**Medium findings as follow-ups (confirmed):** User explicitly deprioritized medium-severity items (non-scoring run labeling, conceptual-query viability, anti-narrowing enforcement) as "not T4-draft blockers... either already partially fenced or benchmark/T7-facing residual risks."

**ADR creation by user:** The conceptual-query ADR was created by the user directly, not by Claude. The user crafted the full 225-line decision record following the existing pattern in `docs/decisions/`. Claude created the execution ticket.
