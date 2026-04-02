---
date: 2026-04-02
time: "00:36"
created_at: "2026-04-02T00:36:51Z"
session_id: d8d5df7c-4419-4765-bcdb-b75fd71e41fe
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_23-41_t04-convergence-loop-adversarial-review.md
project: claude-code-tool-dev
branch: main
commit: e26da8e2
title: "T-04 risk register adversarial review and benchmark-first design plan"
type: handoff
files:
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - packages/plugins/cross-model/context-injection/context_injection/control.py
  - packages/plugins/cross-model/context-injection/context_injection/ledger.py
  - packages/plugins/cross-model/scripts/event_schema.py
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
---

# T-04 risk register adversarial review and benchmark-first design plan

## Goal

Adversarially review the user's T-04 risk register, then produce a reviewed and accepted design plan for the T-04 benchmark-first convergence slice. This is session 13 in the codex-collaboration build chain.

**Trigger:** Session 12 completed the adversarial review of the convergence loop architecture, producing a corrected risk analysis with 11 risks (A-K) and 4 pre-design invariants. The user stated they would condense the narrative analysis into a formal risk register with revised severities and exact invariants. This session reviews that register and builds the design plan on top of it.

**Stakes:** High. The risk register is the design-entry gate for T-04 — if the register has structural problems, the design will inherit them. The plan sequences 6 sessions of design and implementation work; a bad plan means wasted sessions or mid-plan restructuring.

**Success criteria:** (1) Risk register survives adversarial review and is ready to gate design work. (2) Design plan sequences T-04 tasks with correct dependencies, realistic session estimates, and honest risk identification. (3) Both artifacts committed to `main`.

**Connection to project arc:** Session 13 in the codex-collaboration build chain. Sessions 1-10 built the runtime (460 tests). Session 11 did repo hygiene and T-04 reconnaissance. Session 12 was the adversarial review of the convergence loop. This session transitions from analysis to planning — the last pre-design session before gate resolution work begins.

## Session Narrative

Resumed from the session 12 handoff. The user had already created the risk register between sessions — this was their work, done outside of Claude, transforming the session 12 narrative analysis into a condensed gate artifact.

**Phase 1: Risk register adversarial review (first round).** The user presented the risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` and asked for an unforgiving review. I read both the register (64 lines) and the source analysis (347 lines), then verified key source code references still matched (`ledger.py:68-110`, `control.py:58-142`, `event_schema.py:137`, benchmark contract pass rules).

Found no critical failures but 7 required changes, two High severity:

1. **Gate resolution criteria undefined (High).** The register had gates that said what must be true but not when they were true. No status model, no satisfying artifact definition. The design author couldn't tell whether the source analysis's proposals (e.g., the `TerminationCode` enum) counted as gate resolutions or needed independent design confirmation.

2. **Risk C mislinked to G2 (High).** C (referential misclassification) was linked to G2 (synthetic claim provenance). These are independent problems — G2 is about fallback claims inflating delta, C is about real claims being misclassified as `reinforced` vs `new`. Linking C to G2 implied resolving G2 would address C, which it wouldn't. Additionally, Risk C's mitigation (normalized exact matching) had an unresolved tension: Codex paraphrases claims across turns, and exact matching would miss those paraphrases, but semantic overlap was correctly prohibited (violates the computation boundary).

3-7: All-synthetic-turn degenerate case (Medium), D→G3 dependency chain (Medium), redundant acceptance checklist (Medium), missing layer legend (Medium), dropped likelihood column (Low-Medium), subjective dry-run pass criteria (Low-Medium).

**Phase 2: User revises register; second review.** The user revised the register addressing all 7 changes. Key structural improvements:

- Added a gate status model with three states: `Proposed (source analysis)`, `Accepted (design)`, `Resolved (design)`, each with a defined satisfying artifact. Enforcement language: "no design may be signed off while any hard gate remains Proposed."
- Promoted referential continuity to its own hard gate G5, unlinked from G2. The register now has 5 gates (G1-G5).
- Clarified that synthetic claim exclusion applies through counter computation, so an all-synthetic turn is both STATIC and SHALLOW.
- Added a layer legend, dependency/ordering section, likelihood column, and explicit shared dry-run pass criteria.
- Collapsed the acceptance checklist from 4 items to 2 (eliminating gate duplication).

I re-reviewed and rated the register "Defensible" with 4 minor residual observations (no benchmark contract validity pin, mixed likelihood conventions, slightly vague "outcome fields" in Risk I, G5's paraphrase tension deferred to design). None blocking.

The user accepted the "Defensible" verdict and chose not to revise further: "I'm not making another revision on the residual notes as written. They're real but non-blocking." Added only the benchmark contract pin to the header (one-line edit), which I committed on a `docs/t04-risk-register-pin` branch and merged to `main`.

**Phase 3: Design plan — three review rounds.** The user presented a design plan (v1) for the T-04 benchmark-first work: 6 tasks (T1-T6), 3 phases, 4-session estimate.

**Plan v1 review.** Found 5 required changes:

1. **Risk I orphaned (High).** The register's Risk I (integration dry-run) was not assigned to any task. T6 said "define the verification packet" but defining and executing a dry-run are different activities. The dry-run wouldn't happen until an unspecified session after the plan's scope.

2. **T5 composition check missing (High).** T5 (consolidation) only checked whether each gate individually reached Accepted, not whether the combination of accepted gates was internally consistent. T1-T4 resolve gates independently in different sessions; T5 is the first time they're composed. The failure mode: accepted gates that don't compose (e.g., T1's termination contract doesn't have a clean composition point with T3's evidence schema).

3. **Session estimate has no buffer (Medium).** 4 sessions with zero slack. Session 12 found 6 corrections in a review artifact; design decisions are at least as likely to need revision.

4. **T2 bundles three sub-problems of different difficulty (Medium).** T2 covered G2 (straightforward), G5 (hard — paraphrase tension), and K (trivial). The session could bog down on G5 while G2 and K sit idle.

5. **Benchmark contract prereq missing (Low).** No verification that the contract hasn't changed since the register was pinned.

**Plan v2.** User revised, addressing all 5 changes and making 3 improvements beyond what I asked for:
- Split old T2 into T2 (G2+K, straightforward) and T3 (G5, hard). This eliminated the bundling problem entirely — better than my suggested time-box.
- Added T7 (dry-run execution) as a dedicated task, separate from T6 (verification definition).
- Added T0 (benchmark contract pin verification) as Phase 0.
- Expanded session estimate to "4 minimum, realistically 5."
- Changed critical path to T2→T3→T6→T7 and highest-risk identification from T2 to T3.

Re-reviewed: "Defensible — one clarification needed." The one issue: T7 says "execute the pre-benchmark dry-run" but the plan puts T7 before the first coding slice. The dry-run requires a running candidate dialogue loop — layers 4-6 don't exist until after implementation. Two possible readings: (A) T7 is a design walkthrough (weaker), or (B) T7 is actual execution (can't happen before implementation).

**Plan v3 (final).** User chose Reading B: "The dry-run should be an actual execution gate, not a paper walkthrough." Split T7 into T7 (define minimal executable slice) and T8 (implement and run). Expanded to T0-T8 across 6 phases, 5-6 session estimate. Critical path: T2→T3→T6→T7→T8.

I reviewed v3 as ready — no required changes, two non-blocking observations (T7 could absorb into T6 in practice, session 6 is highest-variance because it's the first execution feedback). User asked to save the plan to a file; I wrote it to `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`, committed, and merged to `main`.

## Decisions

### Risk register gate status model (3 states)

**Choice:** Add a three-state gate lifecycle: `Proposed (source analysis)` → `Accepted (design)` → `Resolved (design)`, each with a defined satisfying artifact.

**Driver:** The original register had gates that said what must be true but couldn't tell you when they were true. The source analysis already proposed concrete solutions (e.g., `TerminationCode` enum for G1), creating ambiguity about whether those proposals counted as gate resolution.

**Alternatives considered:**
- **Binary (open/closed)** — simpler. Rejected because it doesn't distinguish "someone proposed a solution" from "the design confirmed it" from "it's locked for implementation."
- **No status tracking** — treat the register as a checklist. Rejected because a gate document that can't tell you when a gate is resolved isn't a gate.

**Trade-offs accepted:** Three states add ceremony. The design author must explicitly move each gate through two transitions. Accepted because the ceremony prevents the failure mode: treating a proposal as an accepted decision without explicit confirmation.

**Confidence:** High (E2) — the status model directly addresses the ambiguity I identified in review, and the user's implementation matches the pattern.

**Reversibility:** High — it's metadata in a markdown table. Can simplify to binary if the three-state model proves unnecessary.

**Change trigger:** If gate resolution always happens in a single step (Proposed → Resolved with no intermediate), the Accepted state is unnecessary.

### Promote referential continuity to its own hard gate (G5)

**Choice:** Create G5 ("Deterministic referential continuity") as a standalone gate, unlinking Risk C from G2.

**Driver:** G2 (synthetic claim provenance) and Risk C (referential misclassification) are independent problems. G2 is about fallback claims inflating `effective_delta`. C is about the agent misclassifying real claims as `reinforced` vs `new`. Linking C to G2 implied resolving G2 addresses C — it doesn't. The register's G2→C dependency note in the resolution order section correctly says: "resolving G2 does NOT resolve Risk C."

**Alternatives considered:**
- **Keep C under G2** — saves a gate. Rejected because it creates false confidence that G2 resolution addresses C. When the design author resolves G2, they'd check off C as "handled."
- **Leave C as ungated Design Control** — C would get resolved during design without a hard gate. Rejected because C's referential matching tension (exact match vs claim IDs vs hybrid) requires an explicit design decision; it shouldn't be deferred.

**Trade-offs accepted:** 5 gates instead of 4. More design work before the "all gates Accepted" milestone. Accepted because a missed referential continuity decision is harder to fix post-implementation than the cost of one more design session.

**Confidence:** High (E2) — the independence of G2 and C is clear from the source code: `compute_counters` (`ledger.py:68-86`) counts claim statuses for G2, while `_referential_warnings` (`ledger.py:241-270`) checks claim text matching for C. Different functions, different inputs, different failure modes.

**Reversibility:** High — G5 can be demoted back to a Design Control risk if the design finds referential continuity is simpler than expected.

**Change trigger:** If the design chooses explicit claim IDs, referential continuity becomes trivial (ID lookup instead of text matching), and G5 may not warrant a hard gate.

### T-04 design plan: 9 tasks (T0-T8) with dry-run as post-minimal-implementation gate

**Choice:** Structure the T-04 design and verification work as 9 tasks across 6 phases, with the pre-benchmark dry-run positioned after a minimal executable slice is implemented (T8), not before implementation.

**Driver:** The dry-run requires a running candidate dialogue loop — it can't be a paper exercise. The register's Risk I requires "one pre-benchmark dry-run dialogue" with pass criteria that check stored values ("`effective_delta` equals recomputation from counters," "each scout record attaches to a target claim"). These checks require executable code.

**Alternatives considered:**
- **6 tasks, dry-run as pre-implementation gate (v1)** — T6 defines and executes the dry-run before coding. Rejected because the dry-run can't execute without code. The plan would have an impossible step.
- **7 tasks, dry-run as separate task but still pre-implementation (v2)** — T7 executes the dry-run after T6 defines it. Rejected for the same reason — "execute" requires implementation.
- **Design walkthrough instead of real dry-run (Reading A)** — T7 traces a hypothetical dialogue on paper. Rejected because it's weaker verification than the register intends. The register wants observable artifacts from real execution.

**Trade-offs accepted:** 6 phases and 5-6 sessions is significant calendar time for design work before the broader T-04 implementation. Front-loads design, back-loads execution — the earliest feedback from real code is session 5-6. Accepted because the gate system's purpose is to prevent exactly the kind of mid-implementation corrections that would cost more than front-loaded design.

**Confidence:** Medium (E1) — the plan structure is sound, but the 5-6 session estimate is untested. T3 (referential continuity) is the most likely overflow point.

**Reversibility:** Medium — the plan's task decomposition could be restructured, but the risk register's gates constrain the degrees of freedom. Gates G1-G5 must all be resolved regardless of plan structure.

**Change trigger:** If the first session (T0+T2+T1) reveals that gate resolution is faster than expected, the plan could compress. If T3 overflows, the plan extends.

### Critical path identification: T2→T3→T6→T7→T8

**Choice:** T3 (deterministic referential continuity) is the highest-risk task and the bottleneck on the critical path.

**Driver:** T3 is the hardest unresolved design decision. It must choose between exact matching (too strict for Codex paraphrases), claim IDs (adds state complexity), or a hybrid. The register's G5 says the mechanism must be deterministic and must document its non-goals (acknowledged false negatives from paraphrases). This is the most likely point for the design to need an extra iteration.

**Alternatives considered:**
- **T2 as highest-risk (v1 plan)** — T2 was the old bundled task covering G2+G5+K. After splitting, T2 (G2+K only) is straightforward. T3 (G5) is the hard part.
- **T4 as highest-risk** — T4 (scouting and evidence contract) is the most complex gate by feature surface. Rejected because its components (scout position, evidence schema, provenance debt) are individually tractable; none has the fundamental tension that G5's paraphrase problem has.

**Trade-offs accepted:** Identifying T3 as the bottleneck means the plan's slack is concentrated around session 2 (where T3 runs). If T3 resolves quickly, the plan compresses; if it overflows, sessions 3-6 all slip.

**Confidence:** Medium (E1) — T3 is the hardest decision on paper, but it's possible T4 or T6 (composition) turns out to be harder in practice.

**Reversibility:** High — critical path identification is planning, not implementation. Can be revised after any session.

**Change trigger:** If T3 resolves quickly (e.g., claim IDs are obviously correct), the critical path shifts to T4→T6→T7→T8.

## Changes

### Created files

| File | Purpose |
|------|---------|
| `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | 9-task sequenced plan (T0-T8) for resolving the 5 hard gates, composing them, implementing a minimal slice, and running the pre-benchmark dry-run. 78 lines. Committed at `e26da8e2`. |

### Modified files

| File | Change | Purpose |
|------|--------|---------|
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | Added benchmark contract pin line in header | Pins the register's severity rankings to the 2026-04-01 benchmark contract (8 tasks, 4 pass-rule metrics). Committed at `e26da8e2`. |

### User-modified files (between sessions, not by Claude)

| File | Change | Purpose |
|------|--------|---------|
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | Major revision: gate status model, G5 promotion, layer legend, dependency section, likelihood column, checklist collapse | Transformed the v1 register (4 gates, no status tracking) into the v2 register (5 gates, 3-state lifecycle, dependency ordering). This was the user's work presented at session start. |
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Added companion artifact pointer | Links the narrative analysis to the condensed register so design-phase readers land on the register first. |

## Codebase Knowledge

### Risk Register Structure (current state at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`)

The register is now a 89-line artifact with the following structure:

| Section | Purpose |
|---------|---------|
| Gate Status Model | 3-state lifecycle (Proposed→Accepted→Resolved) with satisfying artifacts |
| Hard Gate Invariants | 5 gates (G1-G5) with status, primary layer, invariant, required outcome, linked risks |
| Layer Legend | 5-row mapping (1-3: ledger, 4: scouting, 5: follow-up, 6: synthesis, cross-cutting) |
| Resolution Order | 5 dependency entries (G1→G, G2→C, D→G3/J, D+I, G4 independence) |
| Risk Register | 11 risks (B, A, J, H, D, C, I, F, K, G, E) with severity, likelihood, gate class, controls, verification |
| Design Acceptance Checklist | 2 items: all gates Accepted/Resolved, one dry-run artifact |
| Notes for Design Phase | Blockers list, simplification guidance, governing phrase |

### Five Hard Gates

| Gate | Invariant | Layer | Status |
|------|-----------|-------|--------|
| G1 | Structured termination derivation | 6 | `Proposed (source analysis)` |
| G2 | Synthetic claim provenance | 1-3 | `Proposed (source analysis)` |
| G3 | Evidence provenance retention | 4-6 | `Proposed (source analysis)` |
| G4 | Mode contract discipline | 6 / contract surfaces | `Proposed (source analysis)` |
| G5 | Deterministic referential continuity | 1-2 | `Proposed (source analysis)` |

All gates are still `Proposed`. Design work has not started.

### Design Plan Structure (current state at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`)

9 tasks across 6 phases:

| Phase | Tasks | Description |
|-------|-------|-------------|
| 0 | T0 | Benchmark contract pin verification |
| 1 | T1, T2, T4, T5 | Parallel gate resolution (G1, G2+K, G3+D, G4) |
| 2 | T3 | Referential continuity (G5) — depends on T2 |
| 3 | T6 | Adversarial composition of all accepted gates |
| 4 | T7 | Define minimal executable slice for dry-run |
| 5 | T8 | Implement minimal slice and run pre-benchmark dry-run |

Critical path: T2→T3→T6→T7→T8. Highest-risk: T3.

### Source Code References (verified this session)

All references from session 12 were re-verified against current source:

| What | Location | Verified |
|------|----------|----------|
| `compute_counters` (unresolved_closed parameter) | `ledger.py:68-86` | Yes — default 0, caller-supplied |
| `compute_quality` (new_claims → SUBSTANTIVE) | `ledger.py:89-98` | Yes — any new_claims > 0 = SUBSTANTIVE |
| `compute_effective_delta` (counters → delta) | `ledger.py:101-110` | Yes — ADVANCING/SHIFTING/STATIC |
| `compute_action` (4 inputs, prose reason) | `control.py:58-142` | Yes — returns (ConversationAction, str) |
| `VALID_MODES` frozenset | `event_schema.py:137` | Yes — {"server_assisted", "manual_legacy"} |
| Benchmark pass rule (4 conditions) | `dialogue-supersession-benchmark.md:169+` | Yes — safety, false claims, supported rate, convergence |
| Benchmark corpus (8 tasks, all single-posture) | `dialogue-supersession-benchmark.md:60-69` | Yes — B1-B8, 6-8 turn budgets |

## Context

### Mental Model

This session's framing: **"plans fail at composition, not decomposition."** The register's decomposition into gates was correct from session 12. The hard part was ensuring the gates compose — that independently-resolved design decisions work together. The gate status model (Proposed→Accepted→Resolved) and T6's composition check are the structural responses to this framing.

The plan's framing: **"verification ladder."** Each phase builds a stronger form of confidence: individual gate acceptance (Phase 1-2) → compositional confidence (Phase 3) → execution confidence (Phase 4-5). Failures at each level have different signatures: composition failure reopens gates, execution failure reopens design controls, benchmark failure triggers the ticket's decision rule.

### Execution Methodology

Three-round adversarial review on both artifacts (register and plan). Each round:
1. User presents artifact
2. Claude performs adversarial review (requested: "unforgiving," "maximum rigor and skepticism")
3. User revises, addressing findings and sometimes improving beyond what was asked
4. Claude re-reviews, confirming fixes and identifying residual issues

The plan went through 3 full rounds (v1→v2→v3), each addressing the previous round's required changes. The register went through 2 rounds (v1→v2).

### Project State

- **Branch:** `main` at `e26da8e2`
- **Tests:** 460 passing (unchanged since session 11)
- **Local main ahead of origin by 6 commits** (handoff archives, risk analysis, risk register, plan)
- **T-04 status:** Analysis complete (session 12), register reviewed and accepted (this session), plan reviewed and accepted (this session), design work not yet started
- **No code written** — sessions 12-13 have been pure analysis and planning

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1-10 | 2026-03-31 – 2026-04-01 | Runtime build chain | See session 11 handoff |
| 11 | 2026-04-01 | Repo hygiene + T-04 recon | `archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md` |
| 12 | 2026-04-01 | T-04 convergence adversarial review | `archive/2026-04-01_23-41_t04-convergence-loop-adversarial-review.md` |
| **13** | **2026-04-02** | **Risk register review + design plan** | **This handoff** |

## Learnings

### Gate documents need status tracking, not just requirements

**Mechanism:** A gate document that says "X must be true" without saying "X is currently [proposed/accepted/resolved]" can't function as an enforcement mechanism. The design author can't distinguish "someone proposed a solution in the analysis" from "the design confirmed and locked the solution." The gap is especially dangerous when the analysis proposes concrete implementations (like a `TerminationCode` enum) — it looks resolved but isn't.

**Evidence:** The v1 register had 4 gates with invariants and required outcomes but no status column. After review, the user added a 3-state lifecycle (Proposed→Accepted→Resolved) with satisfying artifacts for each state. The enforcement language ("no sign-off while Proposed, no implementation while not Resolved") makes the gate operational.

**Implication:** Future gate documents should include status tracking from the start. The pattern: each gate gets a current state, a transition rule, and a defined artifact that satisfies each transition.

**Watch for:** Gate documents that list requirements without tracking which are met.

### Mis-linking risks to gates creates false confidence

**Mechanism:** Linking Risk C (referential misclassification) to Gate G2 (synthetic claim provenance) implied that resolving G2 would address C. In practice, they're independent — G2 is about fallback claims, C is about real claim classification. When the design author resolves G2, they'd mark C as "handled" without it actually being addressed.

**Evidence:** The v1 register linked C to G2. After review, the user promoted C to its own gate (G5) and added a dependency note: "resolving G2 does NOT resolve Risk C." The register's resolution order section makes the relationship explicit: G2 feeds G5 (synthetic claims are excluded from continuity matching) but doesn't resolve it.

**Implication:** Risk-to-gate linkage should mean "this gate's resolution addresses this risk," not "this risk is related to this gate's topic." When a risk requires its own design decision independent of the linked gate, it needs its own gate.

**Watch for:** Gates with multiple linked risks where the risks have different failure mechanisms.

### Plans fail at composition, not decomposition

**Mechanism:** The v1 plan decomposed T-04 into 6 independent tasks, each resolving a gate. The weakness wasn't the decomposition — it was the composition step (T5) that only checked status, not consistency. Gates resolved independently can make locally-optimal choices that don't compose globally (e.g., T1's termination contract doesn't have a clean composition point with T3's evidence schema).

**Evidence:** After review, the user added an explicit composition check to T6: "if the accepted gates do not compose into one consistent design, reopen the conflicting gates." This makes T6 adversarial rather than administrative.

**Implication:** Any plan that resolves design decisions in parallel needs an explicit composition/integration step that checks for cross-decision consistency, not just individual completion.

**Watch for:** Consolidation steps that only check "is each part done?" rather than "do the parts work together?"

### Dry-runs can't gate implementation they depend on

**Mechanism:** The v2 plan had T7 (execute dry-run) before the first coding slice. But the dry-run's pass criteria require executable code — "stored `effective_delta` equals recomputation from counters" can't be checked without code that stores those values. The plan had an impossible dependency: the dry-run was supposed to gate implementation, but depended on implementation existing.

**Evidence:** The user split T7 into T7 (define minimal slice) and T8 (implement and execute), making the dry-run a post-minimal-implementation gate rather than a pre-implementation gate. The plan now has: design → minimal implementation → dry-run → broader implementation.

**Implication:** Execution-based verification must be positioned after the minimal implementation it needs, not before all implementation. The pattern: split "build" into "minimal testable slice" and "full build," with the verification gate between them.

**Watch for:** Plans that position execution gates before the code they test.

## Next Steps

### 1. Start T0 (benchmark contract verification) and T2 (synthetic claims + closure accounting)

**Dependencies:** None — T0 is a quick git log check. T2 depends only on T0.

**What to read first:** The design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` for task scope. Then the risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` for G2's required design outcome. Then the source analysis for the detailed Risk A and Risk K mechanism descriptions.

**Approach:** T0: verify `dialogue-supersession-benchmark.md` is unchanged since 2026-04-01. T2: design the fallback-claim provenance tag (G2) and the unresolved-list diffing rule (Risk K). These are the simplest gate decisions and should clear quickly.

**Acceptance criteria:** T0: benchmark contract confirmed unchanged or drift identified. T2: user explicitly accepts the synthetic claim model, G2 moves to Accepted.

**Potential obstacles:** T2 is straightforward — the main design question (tag shape: `claim_source=fallback` vs `synthetic_minimum_claim=true`) is a small decision. Unlikely to overflow session 1.

### 2. Start T1 (structured termination contract) in the same session

**Dependencies:** T0 only.

**What to read first:** Risk register G1 required outcome. Then `control.py:58-142` for the current `compute_action` return type. Then the source analysis Risk B for the `TerminationCode` enum proposal.

**Approach:** Design the structured termination code. The source analysis already proposes a concrete `TerminationCode` enum (5 values: `PLATEAU_CONCLUDE`, `CLOSING_PROBE_CONCLUDE`, `BUDGET_EXHAUSTED`, `SCOPE_BREACH`, `ERROR`). The design decision is whether to adopt, modify, or replace this proposal.

**Acceptance criteria:** User explicitly accepts the termination contract, G1 moves to Accepted.

**Potential obstacles:** G1 is medium complexity. The main question is how `converged` is derived mechanically from the termination code. The source analysis's proposal (`converged = termination_code in {PLATEAU_CONCLUDE, CLOSING_PROBE_CONCLUDE}`) is concrete but needs explicit user approval.

### 3. Session 2: T3 (referential continuity) — highest-risk task

**Dependencies:** T2 must be complete (G2→C dependency).

**What to read first:** Risk register G5 required outcome. Then the source analysis Risk C for the paraphrase tension. Then `ledger.py:241-270` for cross-model's current `_referential_warnings` implementation.

**Approach:** Choose between exact matching, claim IDs, or hybrid. Document non-goals (acknowledged paraphrase misclassification). The design must specify how synthetic claims (from G2) are excluded from continuity matching.

**Acceptance criteria:** User explicitly accepts the continuity mechanism, G5 moves to Accepted.

**Potential obstacles:** This is the highest-risk task. The paraphrase tension is real — exact matching will miss paraphrases, but semantic matching violates the computation boundary. May need an empirical check against a baseline transcript to assess paraphrase frequency before committing. Could overflow session 2.

## In Progress

Clean stopping point. Risk register reviewed and accepted. Design plan reviewed, accepted, and committed. All 5 gates still at `Proposed (source analysis)`. No design work started, no code written.

The user confirmed the plan and asked for a handoff. Next session starts with T0, T2, and T1 per the plan's session sketch.

## Open Questions

### Claim IDs vs exact matching for G5

The register's G5 offers three options: claim IDs, normalized exact match with documented non-goals, or a deterministic hybrid. The source analysis prohibits semantic overlap but doesn't evaluate the trade-offs between the remaining options. This is the core design question for T3 (session 2). Claim IDs add state complexity but eliminate the paraphrase problem. Exact matching is simpler but produces known false negatives.

### T7/T6 boundary in practice

The plan has T7 (define minimal executable slice) as a separate phase after T6 (composition). In practice, T7's output naturally falls out of T6's composition pass — if T6 produces a coherent design, the minimal testable subset is a direct projection. Whether T7 is a separate session or a section within the T6 session will depend on T6's complexity.

### How often does Codex paraphrase claims across turns?

This is the empirical question underlying T3's design decision. If Codex paraphrases frequently in the benchmark tasks, exact matching produces widespread misclassification and G5 needs claim IDs. If paraphrasing is rare, exact matching with documented non-goals may be sufficient. The design should include a quick check against a baseline transcript before committing.

## Risks

### Session estimate may compress or expand

The plan estimates 5-6 sessions before the broader implementation packet. If gate resolution is faster than expected (T2+T1 in one session, T3 resolves quickly), it could compress to 4. If T3 or T6 reopens design work, it could expand to 7+. The plan's structure accommodates both, but the calendar impact is significant either way.

### Local main is 6 commits ahead of origin

Not blocking, but accumulating. If coordination becomes necessary (e.g., someone else needs the risk analysis or plan), the local commits need to be pushed. The plan's "out of scope" list parks this, but it's a growing liability.

### First execution feedback is session 5-6

The plan front-loads design (sessions 1-4) and back-loads execution (sessions 5-6). If the design has a flaw that only manifests under execution (e.g., the canonical ledger block is too large for context, or the evidence record shape doesn't serialize into the synthesis format), it won't surface until session 5-6. This is inherent to the gate-based approach and accepted as a trade-off.

## References

| What | Where |
|------|-------|
| Risk register (reviewed, accepted) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Source analysis (corrected, session 12) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| Design plan (reviewed, accepted) | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| T-04 ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Convergence policy (compute_action) | `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` |
| Ledger validation (counters, quality, delta) | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:68-110` |
| Referential warnings | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:241-270` |
| Mode validation | `packages/plugins/cross-model/scripts/event_schema.py:137` |
| Session 12 handoff | `docs/handoffs/archive/2026-04-01_23-41_t04-convergence-loop-adversarial-review.md` |

## Gotchas

### The register has 5 gates now, not 4

Session 12's pre-design invariants listed 4 gates. This session promoted referential continuity to G5, making 5. Future references to "the 4 invariants" from session 12 are outdated — the register is the authority and has 5 gates.

### Gate status is metadata, not enforcement

The gate status model (Proposed→Accepted→Resolved) lives in a markdown table. There's no automated enforcement — the design author must manually update statuses and honor the "no sign-off while Proposed" rule. The register is a communication artifact with enforcement language, not a runtime mechanism.

### The plan's task numbers don't map 1:1 to gates

T0 has no gate (benchmark pin). T2 maps to G2. T3 maps to G5 (not G3). T4 maps to G3. T5 maps to G4. T6-T8 are post-gate tasks. The numbering follows the plan's sequencing, not the register's gate numbering. When referring to specific gates, use G-numbers; when referring to plan tasks, use T-numbers.

### Risk register was revised by the user, not by Claude

The major structural changes (gate status model, G5 promotion, layer legend, dependency section, likelihood column, checklist collapse) were all done by the user between sessions. Claude reviewed and added only the benchmark contract pin (one line). The register reflects the user's design judgment, not Claude's proposals.

## User Preferences

**Iterative adversarial refinement:** The user's workflow this session was consistent: present work → receive adversarial review → revise → get re-reviewed. Three rounds on the plan, two on the register. The user does not treat Claude's first review as authoritative — they expect it to find real issues, revise against those issues, and get confirmation.

**Decisive about non-blocking issues:** After the register's re-review came back "Defensible" with 4 minor residual observations, the user said: "I'm not making another revision on the residual notes as written. They're real but non-blocking, and the current document now does the important job." This is scope discipline — the user stops iterating when the artifact does its job, not when every observation is addressed.

**Improvements beyond what was asked:** The user's plan v2 didn't just address my 5 required changes — it made 3 structural improvements I didn't suggest (T2/T3 split, T3 as highest-risk identification, T0 as Phase 0). The user uses Claude's review as input to a broader revision, not as a fix-list to check off.

**Leads architectural decisions:** Consistent with sessions 11-12: the user drives all structural choices (gate promotion, plan sequencing, critical path identification). Claude provides adversarial review and verification. The user stated in the plan: "If I were sequencing the next few sessions concretely, I'd do them like this" — the session sketch is the user's, not Claude's.

**Precision expectation maintained:** The user's register revisions included specific dependency arrows (G2→C, D→G3), explicit pass criteria for the dry-run, and a gate status model with satisfying artifacts. Every revision added precision, not just coverage. This matches sessions 11-12 where corrections were referenced to file:line.
