---
date: 2026-04-02
time: "02:29"
created_at: "2026-04-02T02:29:07Z"
session_id: afe7b6b5-af7e-4258-a557-5f123bdce1a4
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_00-36_t04-risk-register-and-design-plan.md
project: claude-code-tool-dev
branch: main
commit: 54d160ce
title: "T-04 gate resolution: T1 structured termination, T2 synthetic claims, T3 referential continuity"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
  - packages/plugins/cross-model/context-injection/context_injection/ledger.py
  - packages/plugins/cross-model/context-injection/context_injection/control.py
  - packages/plugins/cross-model/context-injection/context_injection/base_types.py
  - packages/plugins/cross-model/context-injection/context_injection/pipeline.py
  - packages/plugins/cross-model/scripts/emit_analytics.py
---

# T-04 gate resolution: T1 structured termination, T2 synthetic claims, T3 referential continuity

## Goal

Resolve hard gates G1 (structured termination), G2 (synthetic claim provenance), and G5 (deterministic referential continuity) from the T-04 benchmark-first design plan, moving each from `Proposed (source analysis)` to `Accepted (design)`. This is session 14 in the codex-collaboration build chain.

**Trigger:** Session 13 completed the risk register adversarial review (5 gates, 11 risks) and produced the 9-task design plan (T0-T8). The user verified T0 (benchmark contract pin) between sessions and stated the plan's session sketch: T2 first (critical path), then T1, then T3.

**Stakes:** High. These three gates define the machine contracts for termination, claim provenance, and referential continuity — the foundational computation layer for the benchmark-first candidate. Errors in these contracts propagate into every downstream design task (T4-T8) and the eventual implementation. Getting them right now prevents mid-implementation rework.

**Success criteria:** (1) T2 accepted with `claim_source` field and counter exclusion. (2) T1 accepted with `ControlDecision` struct and mechanical projection table. (3) T3 accepted with explicit `referent_text` hybrid and idempotent normalization. (4) Risk register updated to reflect gate status changes. (5) All three contracts survive adversarial review with no unresolved required changes.

**Connection to project arc:** Session 14 in the codex-collaboration build chain. Sessions 1-10 built the runtime (460 tests). Session 11 did repo hygiene. Session 12 was the adversarial review of the convergence loop. Session 13 reviewed the risk register and produced the design plan. This session resolves 3 of 5 hard gates — the first session of actual design work.

## Session Narrative

Resumed from the session 13 handoff. The user had already completed T0 (benchmark contract verification) before the session started — `git diff e26da8e2..HEAD` on the benchmark contract was empty, confirming no drift from the April 1, 2026 pin. The user noted one precision issue: the register says "4 pass-rule metrics" but the benchmark has 6 metrics total with 4 used as pass/fail gates. Wording looseness, not contract drift.

I agreed with the user's proposed sequencing — T2 first because it's on the critical path (T2→T3→T6→T7→T8), then T1 since it's independent parallel work. The user preferred sequential over parallel execution to maintain focus.

**Phase 1: T2 and T1 drafting (user work).** The user drafted both design contracts between messages. T2 at `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` proposes `claim_source: extracted | minimum_fallback` with counter exclusion for fallback claims and exact-text unresolved diffing. T1 at `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` proposes a `ControlDecision` struct separating `action` from `termination_code`, with a mechanical projection table to benchmark-facing fields.

**Phase 2: T2 first review — clean pass.** I verified T2 against the current source code: `compute_counters` at `ledger.py:68-86`, `compute_quality` at `ledger.py:89-98`, `compute_effective_delta` at `ledger.py:101-110`, and the pipeline's unresolved diff at `pipeline.py:260-267`. Every claim in the contract matched the source code. The counter filter (`claim_source == "extracted"`) correctly produces SHALLOW + STATIC for all-fallback turns. The `unresolved_closed` derivation is a verbatim transcription of the existing pipeline. The defensive rule for malformed mixed input is already satisfied by the filter operating on `claim_source`. No required changes.

**Phase 3: T1 first review — three findings.** I verified T1 against `compute_action` at `control.py:58-142`, `map_convergence` at `emit_analytics.py:337-368`, and the scope_breach handling across the codebase. Found three issues:

1. **(High) Budget-convergence precedence change.** T1's pseudocode puts budget exhaustion above plateau detection. But the current analytics layer (`map_convergence`) checks `converged` before `budget_exhausted`. This means a dialogue that converges on its exact last turn would be reported as `budget_exhausted` under T1, but as `converged` under the current analytics. Benchmark-visible behavior change that needed explicit acknowledgment.

2. **(Medium) Error production path unspecified.** The verification path required testing `termination_code="error"`, but the pseudocode had no error branch. Needed to specify whether `error` comes from within the decision function or from an external wrapper.

3. **(Low-Medium) `unresolved_open` in inputs list.** Listed as a "required structured input" but derived from `entries` in the pseudocode. Inconsistency between the inputs list and the algorithm.

**Phase 4: T1 revision and re-review — defensible.** The user folded all three findings. Lines 127-131 now make the budget-precedence change explicit as an "intentional tightening relative to the current analytics split." Section 5.1 defines `error` as an orchestration-wrapper concern with three concrete examples. `unresolved_open` removed from inputs, noted as derived. Re-review found no remaining issues. I verified the pseudocode is a complete, invariant-preserving decision tree: seven branches covering all possible input states, with the biconditional (`action == "conclude"` ↔ `termination_code != null`) holding in every branch.

The user promoted G2 to `Accepted (design)` after the first review (T2 was clean), then promoted G1 after the re-review.

**Phase 5: T3 drafting and first review — three findings.** The user drafted T3 at `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md`. Core choice: explicit `referent_text` hybrid where referential claims must name the prior claim they refer to, with a deterministic normalization function deriving `claim_key` and `referent_key`. Invalid referentials are reclassified to `new` before counters run. Synthetic fallback claims excluded from the registry.

I verified against `_referential_warnings` at `ledger.py:245-270` (current exact-text matching), the `Claim` type at `base_types.py:20-25`, and the cumulative claim registry via `get_cumulative_claims` at `conversation.py:77-79`. Found three issues:

1. **(Medium) `require` failure modes unspecified.** Three `require` statements in the validation pseudocode had no specified behavior on violation. These are pipeline-integrity assertions (not extractor imprecision), so they should be hard errors — consistent with T2's `ValueError` approach.

2. **(Low-Medium) Punctuation sensitivity undocumented.** The normalization function explicitly did not strip punctuation, but trailing punctuation differences are the most common single-character LLM extraction variance. Needed either punctuation stripping or explicit rationale.

3. **(Low-Medium) Registry construction attribution error.** Section 5.2 attributed `claim_key` derivation to T2, but T2 doesn't derive `claim_key` — T3 does.

**Phase 6: T3 revision and second review — two findings.** The user addressed all three, adding hard-error semantics for `require` violations, trailing sentence punctuation stripping (`. , ; : ! ?`) with rationale, and corrected attribution. Also took the non-blocking convergence-cascade observation and made it explicit in the accepted-limitation section.

Second review found:

1. **(Medium) Normalization non-idempotency.** The five-step normalization function applies trim at step 2 and strip-trailing-punctuation at step 5. When punctuation stripping reveals trailing whitespace (e.g., `"JWT is better ."` → strip `.` → `"jwt is better "`), the result has a trailing space that a second normalization would remove. Concrete trace: `normalize(normalize("JWT is better .")) ≠ normalize("JWT is better .")`. A normalization function used for key derivation must be idempotent.

2. **(Medium) No verification items for the normalization function itself.** 8 test items covered claim validation but none tested the normalizer directly — no idempotency, casefold, punctuation stripping, or whitespace collapse tests.

**Phase 7: T3 final revision — defensible.** The user added a sixth normalization step (final trim after punctuation stripping), making the function idempotent. Added 5 normalizer-specific verification items (items 1-5 in section 9). Also added a note about `reinforced` extraction convenience. Final review confirmed idempotency, verified all 13 verification items cover both normalizer and validation, and cross-checked against G5's required design outcome. Defensible. G5 promoted to `Accepted (design)`.

## Decisions

### T2: Claim-level provenance with `claim_source` field (user's design, Claude reviewed)

**Choice:** Add `claim_source: "extracted" | "minimum_fallback"` to the normalized claim record. Counter computation filters on `claim_source == "extracted"` only. `unresolved_closed` derived by exact-text set diff against the immediately prior turn.

**Driver:** `compute_quality()` marks any `new_claims > 0` turn as SUBSTANTIVE, and `compute_effective_delta()` marks it as ADVANCING (`ledger.py:89-110`). If fallback claims are indistinguishable from real `new` claims, the candidate loop mechanically overstates progress.

**Alternatives considered:**
- **Overload `status` with a fifth value** — rejected because `status` describes semantic relationship across turns, while provenance describes why the claim exists. A synthetic minimum claim is not a fifth semantic relationship.
- **Turn-level fallback flag** — rejected because T3 needs claim-level exclusion for continuity matching. Turn-level flags are too coarse.
- **Post-hoc quality/delta downgrade** — rejected because it duplicates counter logic and breaks the "compute, don't assess" rule. Exclusion must happen at the counting boundary.

**Trade-offs accepted:** Adds a field to every claim record. Minimal overhead — the field is binary and derived at normalization time.

**Confidence:** High (E2) — verified against source code at `ledger.py:68-110` and `pipeline.py:260-267`. Every claim in the contract matches existing behavior, with the addition of the `claim_source` filter.

**Reversibility:** High — `claim_source` is additive. Removing it restores current behavior.

**Change trigger:** If the minimum-one-claim invariant is relaxed (empty-claim turns become legal), `claim_source` is unnecessary.

### T1: Structured `ControlDecision` separating action from termination code (user's design, Claude reviewed)

**Choice:** The controller returns `ControlDecision { action, termination_code }` instead of `(action, prose_reason)`. `converged`, `convergence_reason_code`, and `termination_reason` are projected mechanically from `termination_code` plus structured state. Scope breach enters the same structured path with highest precedence.

**Driver:** The current system has two authorities for convergence: the control layer (`compute_action` returns `CONCLUDE` with prose) and the analytics layer (`map_convergence` checks `converged` independently). T1 unifies these into one structured authority, preventing prose-parsing shortcuts and `conclude`-means-converged assumptions.

**Alternatives considered:**
- **Keep `(action, prose_reason)` and parse prose later** — rejected because prose is not a stable machine contract. Risk B in the register: a future template change silently changes the parser's meaning.
- **Treat `action == "conclude"` as convergence** — rejected because `conclude` is overloaded (budget exhaustion, scope breach, and error also conclude).
- **Keep scope breach outside the termination contract** — rejected because it creates split-brain state between control and epilogue fields.

**Trade-offs accepted:** Budget exhaustion takes precedence over plateau/convergence. A dialogue that converges on its exact last turn (`budget_remaining == 0`) is reported as `budget_exhausted`, not `converged`. This is an intentional tightening: under the current analytics split, the agent's narrative can override the budget constraint; under T1, it cannot.

**Confidence:** High (E2) — verified pseudocode is a complete decision tree covering all possible input states. The biconditional invariant (`conclude` ↔ non-null `termination_code`) holds in every branch.

**Reversibility:** Medium — `ControlDecision` replaces the current return type. The mapping table can be revised without changing the struct.

**Change trigger:** If the budget-precedence behavior causes benchmark results to diverge significantly from expected convergence rates, the precedence order could be revised (plateau before budget). The projection table would update accordingly.

### T3: Deterministic hybrid with explicit `referent_text` and idempotent normalization (user's design, Claude reviewed)

**Choice:** Referential claims (`reinforced`, `revised`, `conceded`) carry an explicit `referent_text` field. A 6-step normalization function (NFKC → trim → collapse whitespace → casefold → strip trailing sentence punctuation → trim) derives `claim_key` and `referent_key`. The validator checks `referent_key` against a cumulative prior-claim registry. Failed lookups reclassify the claim to `new`. Synthetic fallback claims are excluded from the registry.

**Driver:** The current cross-model reference uses exact text matching on the CURRENT claim text (`_referential_warnings` at `ledger.py:245-270`). This fails for `revised` and `conceded` where the current text has changed — the prior claim text is what identifies the referent, not the current claim text. Pure claim IDs were rejected because there's no existing ID surface in the protocol (`base_types.py:20-25`).

**Alternatives considered:**
- **Pure normalized exact match on current claim text** — rejected because it makes `revised` and `conceded` brittle even in non-paraphrase cases.
- **Full claim IDs** — rejected for the benchmark-first slice because it widens the protocol surface more than needed. Deferred to a future design if the hybrid proves insufficient.
- **Semantic overlap or LLM-judged continuity** — rejected because it violates G5's deterministic computation boundary.
- **Warning-only referential validation** — rejected because T-04 lacks an external correcting authority (unlike cross-model where `_referential_warnings` is warning-only because a separate server owns authoritative state). Bad labels feed directly into counters.

**Trade-offs accepted:** The extraction layer (LLM) must provide exact-enough `referent_text` for referential claims. If the extractor can't name the prior claim text (paraphrase, missing context), the claim is reclassified to `new`, potentially over-counting advancement and delaying convergence detection. This is accepted as a bounded benchmark-first limitation.

**Confidence:** Medium-High (E2) — the contract's deterministic boundary is sound and verified against source code. The uncertainty is in extraction quality: how reliably the LLM copies prior claim text into `referent_text`. The benchmark will reveal the reclassification rate.

**Reversibility:** Medium — the `referent_text` field is additive to `ClaimRecord`. The normalization function is self-contained. Full claim IDs could replace the hybrid without changing other contracts.

**Change trigger:** If benchmark results show a high reclassification rate (>20% of referential claims reclassified to `new`), the hybrid is too fragile and full claim IDs should be reconsidered. If the rate is low (<5%), the hybrid is validated.

## Changes

### Created files

| File | Purpose |
|------|---------|
| `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | Accepted design artifact for G1. Defines `ControlDecision` struct, 7-branch pseudocode, error boundary, projection table, and 7 verification items. 239 lines. |
| `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Accepted design artifact for G2. Defines `claim_source` field, counter filtering, `unresolved_closed` derivation, and 6 verification items. 227 lines. |
| `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Accepted design artifact for G5. Defines `referent_text` hybrid, 6-step idempotent normalization, registry construction, validation/reclassification pseudocode, and 13 verification items. 328 lines. |

### Modified files

| File | Change | Purpose |
|------|--------|---------|
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G1 → `Accepted (design)`, G2 → `Accepted (design)`, G5 → `Accepted (design)` | Reflects gate promotions from this session. G3 and G4 remain `Proposed (source analysis)`. |

### User-modified files (between messages, not by Claude)

All four files above were authored by the user. Claude served as adversarial reviewer only — no design artifacts were written by Claude this session. The design contracts reflect the user's architectural decisions refined through iterative adversarial review.

## Codebase Knowledge

### Source Code References (verified this session)

All references were verified against current source to scrutinize the design contracts:

| What | Location | Used for |
|------|----------|----------|
| `Claim` type (text, status, turn) | `base_types.py:20-25` | T2: confirmed no existing `claim_source` field; T3: confirmed no existing `referent_text` or `claim_key` |
| `compute_counters` (all claims counted) | `ledger.py:68-86` | T2: confirmed fallback claims would inflate `new_claims` without filtering |
| `compute_quality` (any counter > 0 → SUBSTANTIVE) | `ledger.py:89-98` | T2: confirmed all-fallback turns would be SUBSTANTIVE without exclusion |
| `compute_effective_delta` (new_claims > 0 → ADVANCING) | `ledger.py:101-110` | T2: confirmed fallback inflation would show false ADVANCING |
| `compute_action` (budget > plateau > default) | `control.py:58-142` | T1: verified current precedence, confirmed scope_breach is absent from control layer |
| `map_convergence` (converged > budget priority) | `emit_analytics.py:337-368` | T1: identified that analytics layer has OPPOSITE precedence from control layer — converged checked before budget |
| `build_dialogue_outcome` (scope_breach post-hoc) | `emit_analytics.py:376-449` | T1: confirmed scope_breach is detected post-hoc from synthesis parsing, not from control decisions |
| Pipeline unresolved diff (exact-text frozenset) | `pipeline.py:260-267` | T2: confirmed `unresolved_closed` derivation matches T2's pseudocode exactly |
| `_referential_warnings` (exact text, warning-only) | `ledger.py:245-270` | T3: confirmed current system uses current-claim-text matching (not referent), and warns rather than reclassifies |
| `get_cumulative_claims` (full claim history) | `conversation.py:77-79` | T3: confirmed registry should be cumulative across all prior turns |
| Scope breach handling (agent level, not control) | `codex-dialogue.md:380-381`, `emit_analytics.py:392-394` | T1: confirmed scope breach is currently handled at agent level, not in `compute_action` |
| `ConversationAction` enum | `control.py:30` | T1: confirmed three values (CONTINUE_DIALOGUE, CLOSING_PROBE, CONCLUDE) preserved |
| `ClaimStatus` enum | `enums.py:44-50` | T3: confirmed four statuses (new, reinforced, revised, conceded) |
| `_REFERENTIAL_STATUSES` frozenset | `ledger.py:241` | T3: confirmed referential statuses are {reinforced, revised, conceded} |

### Key Architectural Insight: The Current Split-Brain

The most important finding for T1 was that the current system has two independent authorities for convergence:

1. **Control layer** (`compute_action` at `control.py:58-142`): Returns `CONCLUDE` with a prose reason. Budget exhaustion is checked first (line 100-105), so a last-turn convergence says "Budget exhausted."

2. **Analytics layer** (`map_convergence` at `emit_analytics.py:337-368`): Takes `converged` as an independent boolean from the agent's synthesis. Checks `converged` before `budget_exhausted` (lines 356-360). So a last-turn convergence says "converged."

T1 eliminates this split by making `converged` a mechanical projection from `termination_code`, which is produced by the control layer. The analytics layer becomes downstream, not parallel.

### Normalization Function Detail (T3 — final verified form)

The T3 normalization function went through three revisions. The final 6-step version is:

1. Unicode NFKC normalization (handles `ﬁ` → `fi`, `…` → `...`, full-width → ASCII)
2. Trim leading/trailing whitespace
3. Collapse internal whitespace runs to a single space
4. Casefold (locale-independent lowercase)
5. Strip trailing sentence punctuation: `. , ; : ! ?` (rstrip-all, not single-character)
6. Trim leading/trailing whitespace (idempotency fix — step 5 can expose whitespace shielded by punctuation)

The idempotency property `normalize(normalize(x)) == normalize(x)` is required for key derivation correctness and is verified by test item 1 in T3's verification path. Without step 6, `normalize("JWT is better .")` produces `"jwt is better "` (trailing space), which normalizes differently on a second pass.

### Cross-Contract Dependency Graph

```
T2 (claim_source) ──→ T3 (registry excludes minimum_fallback)
                 └──→ T3 (counter filtering happens before T3 validation)

T1 (ControlDecision) ──→ standalone (no T2/T3 dependency)

T3 (claim_key, referent_key) ──→ depends on T2 (claim_source field exists)
```

T1 and T2 are orthogonal. T3 depends on T2 (G2→C dependency in the register). All three contracts reference the same underlying source code but at different layers: T2 at layers 1-3 (claim normalization, counter computation), T1 at cross-cutting orchestration and layer 6 (control decisions, benchmark projection), T3 at layer 2 (referential validation between normalization and counter computation).

## Context

### Mental Model

This session's framing: **"adversarial refinement as a convergence mechanism."** The user drafts design contracts, Claude attacks them, the user revises, Claude re-attacks. The cycle terminates when required changes drop to zero. This mirrors the convergence loop itself — each review round either finds issues (ADVANCING/SHIFTING) or doesn't (STATIC → plateau → acceptance).

The design contracts themselves follow a pattern: **state shape → owning layers → deterministic algorithm boundary → verification path.** This structure makes each contract self-contained and auditable. The boundary between what the contract decides and what it defers is explicit in every document (sections titled "What T{n} Does Not Change" or "What T{n} Intentionally Leaves To T{n+1}").

### Execution Methodology

Iterative adversarial review with two-pass scrutiny:
- **Pass 1:** Obvious flaws, contradictions, omissions, weak assumptions. Source code verification of every claim.
- **Pass 2:** Second-order effects, edge cases, hidden dependencies, failure modes under non-ideal conditions.

Each contract went through 2-3 review cycles:
- T2: 1 cycle (clean on first pass)
- T1: 2 cycles (3 findings → revision → defensible)
- T3: 3 cycles (3 findings → revision → 2 findings → revision → defensible)

The user's revision pattern: address all required changes, often improve beyond what was asked (e.g., T3's convergence-cascade note was non-blocking but the user made it explicit anyway).

### Project State

- **Branch:** `main` at `54d160ce`
- **Tests:** 460 passing (unchanged since session 11)
- **Local main ahead of origin by 8+ commits** (handoff archives, risk analysis, register, plan, plus archived session 13 handoff)
- **T-04 gate status:**

| Gate | Status | Accepting artifact |
|------|--------|--------------------|
| G1 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` |
| G2 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| G3 | `Proposed (source analysis)` | — |
| G4 | `Proposed (source analysis)` | — |
| G5 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |

- **Working tree:** 1 modified file (register), 3 untracked files (T1, T2, T3 design notes). All uncommitted.
- **No code written** — sessions 12-14 have been pure analysis, planning, and design.

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1-10 | 2026-03-31 – 2026-04-01 | Runtime build chain | See session 11 handoff |
| 11 | 2026-04-01 | Repo hygiene + T-04 recon | `archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md` |
| 12 | 2026-04-01 | T-04 convergence adversarial review | `archive/2026-04-01_23-41_t04-convergence-loop-adversarial-review.md` |
| 13 | 2026-04-02 | Risk register review + design plan | `archive/2026-04-02_00-36_t04-risk-register-and-design-plan.md` |
| **14** | **2026-04-02** | **Gate resolution: T1, T2, T3** | **This handoff** |

## Learnings

### Normalization functions used for key derivation must be idempotent

**Mechanism:** A normalization function that strips trailing punctuation can reveal trailing whitespace that an earlier trim step already handled. If the function doesn't trim again after stripping, `normalize(normalize(x)) ≠ normalize(x)` for inputs with whitespace before trailing punctuation. The concrete trace: `normalize("JWT is better .")` produces `"jwt is better "` (trailing space), but `normalize("jwt is better ")` produces `"jwt is better"` (no trailing space).

**Evidence:** Discovered during T3 second review. The user's 5-step normalization (NFKC → trim → collapse → casefold → strip punctuation) failed the idempotency check. Adding a sixth step (final trim) fixed it.

**Implication:** Any future normalization function that adds a stripping step after an earlier whitespace step needs to re-apply whitespace handling. The test is simple: `assert normalize(normalize(x)) == normalize(x)` for representative inputs. This should be a standing verification item for any key-derivation normalizer.

**Watch for:** Normalization functions that add processing steps incrementally (as this one did across review rounds). Each new step may interact with earlier steps.

### Warning-only validation is inadequate for self-consuming loops

**Mechanism:** Cross-model's `_referential_warnings` (`ledger.py:245-270`) emits warnings but doesn't change claim statuses. This works because a separate server owns the authoritative derived state — the warnings inform a human reviewer. In T-04's benchmark-first candidate, the same local loop that extracts claims also consumes them for counters. A warning about a bad `reinforced` label doesn't fix the fact that the label suppresses a `new_claims` increment.

**Evidence:** T3 section 5.4 argument. The three failure modes: (1) bad `reinforced` suppresses `new_claims`, (2) bad `new` inflates `effective_delta`, (3) misclassification pollutes the next turn's prior-claim history.

**Implication:** When designing validation for a self-consuming pipeline (no external correcting authority), validation must canonicalize, not just warn. The system must be in a known-good state before computation proceeds. This principle extends beyond claim validation to any pipeline stage that both produces and consumes its own state.

**Watch for:** Systems that inherit warning-only patterns from multi-authority architectures when deployed in single-authority contexts.

### Split-brain convergence detection is a real architectural issue

**Mechanism:** The current cross-model system has two independent authorities for convergence: the control layer (budget > plateau precedence) and the analytics layer (converged > budget precedence). These can produce different answers for the same dialogue — specifically when a dialogue converges on its exact last turn.

**Evidence:** `compute_action` at `control.py:100-105` checks budget first. `map_convergence` at `emit_analytics.py:354-360` checks `converged` first. A dialogue with `budget_remaining == 0` and a converging plateau gets `budget_exhausted` from control but `converged` from analytics.

**Implication:** T1's structured termination contract eliminates this split by making `converged` a mechanical projection from the control layer's `termination_code`. The analytics layer becomes downstream. Any future design that separates control from reporting must ensure the reporting layer projects from control decisions, not from independent narrative assessment.

**Watch for:** Multiple layers independently deriving the same field (here: `converged`) from different precedence rules.

### Reclassification to `new` over-counts but bounds the error

**Mechanism:** When a referential claim (`reinforced`, `revised`, `conceded`) can't prove its referent, reclassification to `new` means `new_claims` increments. This inflates `effective_delta` (false ADVANCING) and can delay plateau detection and convergence. In repeated failure cases, the dialogue runs to budget exhaustion instead of converging naturally.

**Evidence:** T3 section 6 (documented non-goals, lines 248-255). The consequence chain: bad referent → reclassify to `new` → inflate `new_claims` → ADVANCING instead of STATIC → prevent plateau → delay convergence.

**Implication:** The reclassification rate is a key health metric for the benchmark. If it's low (<5%), the hybrid works. If it's high (>20%), the ledger's ADVANCING/SHIFTING distinction is unreliable and claim IDs should be reconsidered. The benchmark will reveal this.

**Watch for:** High reclassification rates in benchmark tasks with heavy claim revision (Codex changing positions frequently).

## Next Steps

### 1. Start T4 (scouting position and evidence provenance) or T5 (mode contract discipline)

**Dependencies:** T4 depends on Risk D (scouting position must be fixed before evidence records can be finalized). T5 (G4) is largely independent — mode strategy can be resolved in parallel.

**What to read first:** The design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` for task scope. Then:
- For T4: Risk register G3 required design outcome and linked risks (J, D, F, E). Source analysis sections on scouting and evidence provenance. Current scouting implementation in `codex-dialogue.md` and `execute.py`.
- For T5: Risk register G4 required design outcome and linked risk H. `VALID_MODES` at `event_schema.py:137`. Mode-consuming contracts across the codebase.

**Approach:** The user suggested T4 is the bigger integration surface and T5 is the narrower decision. T5 could clear quickly if the decision is to reuse an existing mode value. T4 requires designing the scout-capture point, evidence record schema, and synthesis citation surface — more substantial design work.

**Acceptance criteria:** For T4: user explicitly accepts the scouting position and evidence schema, G3 moves to Accepted. For T5: user explicitly accepts the mode decision, G4 moves to Accepted.

**Potential obstacles:** T4 is the most complex remaining gate by feature surface — it touches layers 4-6 (scouting, follow-up, synthesis). Risk D must be resolved before G3 can be finalized (scouting position → evidence record schema dependency). May need more than one review cycle.

### 2. Commit the current design artifacts

**Dependencies:** None — the files exist and are ready.

**What to do:** The working tree has 1 modified file and 3 untracked files. These should be committed together as a coherent design milestone (3 gates accepted).

**Approach:** Single commit with the register update and all three design notes. Branch protection applies — may need a working branch.

### 3. After G3 and G4: T6 composition check

**Dependencies:** All 5 gates must be `Accepted (design)` before T6 can start.

**What it does:** T6 is an adversarial composition step — it checks whether the independently-accepted gates compose into one consistent design. This is where "plans fail at composition, not decomposition" (session 13's framing) gets tested.

**Risk:** The three accepted contracts (T1, T2, T3) were designed to be orthogonal, but T6 will verify this. The main interaction point is T2→T3 (claim_source feeds into registry exclusion). T1 is genuinely independent.

## In Progress

Clean stopping point. Three gates resolved (G1, G2, G5). Two gates remaining (G3, G4). Working tree has uncommitted design artifacts. No design work in flight — the user explicitly asked for a handoff at this natural boundary.

## Open Questions

### What reclassification rate is acceptable for T3?

The T3 contract accepts over-counting as a bounded limitation. But "bounded" needs empirical calibration. If >20% of referential claims fail referent matching, the ledger's ADVANCING/SHIFTING distinction becomes unreliable. The benchmark's 8 tasks will reveal this. If the rate is too high, claim IDs (rejected alternative B) come back into scope.

### Should T4 and T5 be done sequentially or in parallel?

The plan puts them in the same phase (Phase 1) as parallel work. But the user preferred sequential execution for T1/T2/T3. T5 is likely quick (mode decision). T4 is larger. Sequential T5→T4 would clear the easier gate first. Parallel execution with a /codex consultation for T5 is possible but the user hasn't requested it.

### Local main is now 8+ commits ahead of origin

The handoff chain (sessions 11-14) has accumulated commits that haven't been pushed. The design artifacts are also uncommitted. If coordination becomes necessary (e.g., someone else needs the design plans), pushing is needed.

## Risks

### Design work is pure docs — no implementation feedback until T8

Sessions 12-14 have been analysis, planning, and design. No code has been written. The earliest implementation feedback is T8 (implement minimal executable slice and run dry-run). If a design decision only manifests failure under execution (e.g., the canonical ledger block is too large for context, or the evidence record shape doesn't serialize), it won't surface until sessions 5-6 of the plan.

### T3's extraction burden is untested

The `referent_text` mechanism requires the extraction layer (LLM) to copy prior claim text exactly enough to survive normalization. No empirical data exists on how reliably the LLM does this. The benchmark is the first real test. If the LLM frequently paraphrases when copying, the reclassification rate could be high enough to make the ledger unreliable.

### Uncommitted design artifacts

Three untracked design notes and one modified register are sitting in the working tree. If the working tree is reset or the session state is lost before committing, the accepted design work would need to be recreated from the handoff's descriptions.

## References

| What | Where |
|------|-------|
| T1 design contract (accepted) | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` |
| T2 design contract (accepted) | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| T3 design contract (accepted) | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |
| Risk register (3 gates accepted) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| Source analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| T-04 ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Control layer (compute_action) | `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` |
| Ledger functions (counters, quality, delta) | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:68-110` |
| Referential warnings | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:245-270` |
| Analytics convergence mapper | `packages/plugins/cross-model/scripts/emit_analytics.py:337-368` |
| Pipeline unresolved diff | `packages/plugins/cross-model/context-injection/context_injection/pipeline.py:260-267` |
| Claim type | `packages/plugins/cross-model/context-injection/context_injection/base_types.py:20-25` |
| Cumulative claims | `packages/plugins/cross-model/context-injection/context_injection/conversation.py:77-79` |
| Session 13 handoff | `docs/handoffs/archive/2026-04-02_00-36_t04-risk-register-and-design-plan.md` |

## Gotchas

### The register has 5 gates, not 4 — and 3 are now accepted

Session 12's pre-design invariants listed 4 gates. Session 13 promoted referential continuity to G5 (5 gates total). This session accepted G1, G2, and G5. Only G3 and G4 remain `Proposed`. Future references to "the 4 invariants" or "all gates proposed" are outdated.

### T3's normalization has 6 steps, not 5

The normalization function went through three revisions during review. The final version has 6 steps (with the idempotency-ensuring final trim). Any reimplementation must include all 6 steps — omitting the final trim reintroduces the non-idempotency bug.

### Budget-precedence is intentionally different from current analytics

T1's contract says a dialogue that converges on its last turn reports as `budget_exhausted`. The current analytics layer (`map_convergence`) would report it as `converged`. This is documented and intentional, but someone comparing benchmark results between the current system and the T-04 candidate should expect this difference.

### T3's `require` failures are hard errors, not reclassifications

The validation pseudocode has two failure modes: `require` violations (hard error, pipeline corruption) and referent lookup failures (reclassification to `new`, expected extractor imprecision). These are distinct. Implementing `require` as reclassification would silently mask upstream bugs.

### Design artifacts are uncommitted

The three design notes are untracked. The register modification is unstaged. A `git checkout .` or similar destructive action would lose the register changes. The design notes would survive (untracked files aren't affected by checkout) but wouldn't be in the history.

## User Preferences

**Iterative adversarial refinement continued:** Consistent with sessions 12-13. The user drafts design artifacts, presents them for adversarial review, revises against findings, and gets re-reviewed. The cycle continues until required changes reach zero. The user does not treat Claude's first review as authoritative — they expect real issues and revise against them.

**Improvements beyond what was asked:** On T3, the user took the non-blocking convergence-cascade observation and made it explicit in the accepted-limitation section. On T1, the user restructured the document to separate the error boundary into its own subsection rather than just adding a note. Pattern: the user uses Claude's review as input to broader improvements, not as a fix-list.

**Sequential over parallel:** The user explicitly preferred sequential T2→T1→T3 over parallel execution: "I would rather do them sequentially, because doing them in parallel divides our attention." This is a strong preference for focused single-thread design work.

**Decisive about non-blocking issues:** After T2 passed clean on first review, the user immediately promoted G2 and moved on. No hesitation when the artifact is ready. Same pattern as session 13's register review.

**Escalating scrutiny requests:** The user's scrutiny requests escalated through the session. First: "scrutinize." Second: "scrutinize" with specific line references. Third: "Red-team this with no mercy. Assume it is flawed, fragile, and exposed. Attack every assumption." The user wants adversarial pressure to increase as artifacts mature.

**Leads all design decisions:** All three design contracts were authored by the user. Claude provided adversarial review and source-code verification only. The user's stated framing: "If the revised T1 contract is acceptable, I'll move G1 to Accepted and then proceed to T3." The user drives the workflow — Claude validates.
