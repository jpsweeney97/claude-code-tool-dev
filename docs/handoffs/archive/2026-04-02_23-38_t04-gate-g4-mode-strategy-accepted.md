---
date: 2026-04-02
time: "23:38"
created_at: "2026-04-02T03:38:32Z"
session_id: 9a1bc285-069e-4bc8-90da-37288e8fbdbd
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_02-29_t04-gate-resolution-t1-t2-t3.md
project: claude-code-tool-dev
branch: main
commit: adcaac61
title: "T-04 gate G4 mode strategy accepted — G3 is the last remaining gate"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
---

# T-04 gate G4 mode strategy accepted — G3 is the last remaining gate

## Goal

Resolve the remaining hard gates from the T-04 benchmark-first design plan. This session targeted G4 (mode contract discipline) via T5 (mode strategy). The broader goal is to clear all 5 hard gates so T6 (composition check) can proceed. Session 15 in the codex-collaboration build chain.

**Trigger:** Session 14 accepted G1, G2, and G5 (structured termination, synthetic claim provenance, deterministic referential continuity). The user had completed those three design contracts and asked to continue with the remaining gates. The handoff recommended T5 first (narrower gate, lower branching cost) then T4.

**Stakes:** High. G4 determines whether the T-04 benchmark-first candidate introduces a new mode value or reuses an existing one. The mode field flows through normative contracts, analytics schema, test fixtures, and operator documentation. Getting the taxonomy right prevents downstream migration churn. Getting it wrong either lies about what the candidate is (`server_assisted` reuse) or commits to unnecessary contract surface (`agent_local` if reuse was sufficient).

**Success criteria:** (1) G4 accepted with either a defensible reuse rationale or a complete migration set. (2) Risk register updated. (3) Design artifact committed. (4) No unresolved required changes from adversarial review.

**Connection to project arc:** Session 15. Sessions 1-10 built the runtime (460 tests). Session 11 repo hygiene. Session 12 convergence loop adversarial review. Session 13 risk register and design plan. Session 14 accepted G1, G2, G5. This session accepted G4. G3 (evidence provenance) is the last gate before T6 (composition check).

## Session Narrative

Resumed from the session 14 handoff. Working tree had 1 modified file (register with G1/G2/G5 promotions) and 3 untracked files (T1/T2/T3 design contracts), all uncommitted from session 14.

**Phase 1: Baseline commit.** The user recommended committing the design artifacts as a clean baseline before starting new gate work. Reasoning: a single commit saying "this is the accepted baseline" provides a tight diff target if later gates force revisiting earlier assumptions. Committed at `3411895e`: 4 files (3 design notes + register update), 794 insertions.

**Phase 2: Sequencing decision.** The user presented a structured decision analysis for T4-vs-T5 ordering. The analysis ranked T5 first because: (a) T4 and T5 are parallel prerequisites for T6, not a ranked pair where T4 dominates; (b) T5 is the narrower contract decision and can collapse the state space by resolving the reuse-vs-migration fork before T4; (c) the critical path is T2→T3→T6→T7→T8, and T4/T5 are off-path prerequisites. The user recommended a short source pass to confirm T4 doesn't constrain T5 before committing to this order.

**Phase 3: Mode surface mapping — three rounds.** I did the source pass to map mode-consuming contracts. The first pass found 6 locations in the analytics/event layer (`event_schema.py`, `emit_analytics.py`, dialogue/codex SKILL.md). The user corrected this with 6 findings, identifying normative contracts (`codex-dialogue.md:17`, `dialogue-synthesis-format.md:86,144`), downstream consumers (`compute_stats.py:256`, `HANDBOOK.md:256`), and test enforcement surfaces (`test_event_schema.py:85`, `test_emit_analytics_legacy.py:670,989,1740`, `test_emit_analytics.py:96,167`) that I had missed. The user's core critique: "Your map says the surface is 'all in the analytics/event layer,' but the repo's live mode contract is also defined in the delegated-agent instructions and the machine-output format."

I produced a corrected map with ~16 locations across 4 layers (normative contracts, schema/validation, producers, downstream consumers/tests). The user found 3 more errors: (P1) `mode` is NOT required on `delegation_outcome` — I had incorrectly claimed it was required on all 3 event types; (P2) test rows were mislabeled — `test_emit_analytics_legacy.py:695` is about `mode_source` absence, not mode validation; (P3) README and other operator docs also encode the two-mode model. After the third correction round, the user confirmed: "The corrected map now matches the repo on the points that mattered."

**Phase 4: T5 drafting (user work).** The user drafted the T5 design note at `docs/plans/2026-04-02-t04-t5-mode-strategy.md`. The draft chose the migration branch: a third mode value `agent_local` defined by dialogue-loop ownership (who owns state and convergence computation, who selects and executes scouting, whether the agent consumes helper-produced outputs or runs the loop itself). The user's argument: reusing `server_assisted` would require redefining it away from the cross-model helper mechanism that the current normative docs describe, erasing the main distinction the field carries.

**Phase 5: First review (scrutinize) — three findings.** I reviewed the T5 draft against the verified source surfaces. Found three issues:

1. **(Medium) `mode_source` behavior for `agent_local` unspecified.** The draft never mentioned `mode_source`. For `server_assisted`, `mode_source` distinguishes epilogue-parsed from fallback. For `agent_local`, the mode is intrinsically known — not parsed from an epilogue. The draft needed to specify what `mode_source` should be.

2. **(Medium) Migration row puts `agent_local` definition in `codex-dialogue.md`.** That agent will never emit `agent_local`. The definition belongs in the T-04 candidate's own contract, not in the cross-model agent's instructions.

3. **(Low-Medium) Verification path omits `mode_source` testing.** None of the 7 verification items mentioned `mode_source`.

**Phase 6: T5 revision and second review (review-strategy) — defensible.** The user addressed all three findings. Added section 3.5 defining `mode_source = null` for `agent_local` with rationale (mode is intrinsically determined, not parsed), error-path behavior (mode stays `agent_local`, termination fields carry the error), and pre-start abandonment behavior (`manual_legacy`, not `agent_local`). Removed `codex-dialogue.md` from the migration set. Added verification item 8 for `mode_source = null` acceptance. Second review found no required changes. The user promoted G4 to `Accepted (design)`.

## Decisions

### T5: Third mode `agent_local` via migration, not reuse of `server_assisted` (user's design, Claude reviewed)

**Choice:** Introduce `agent_local` as a third dialogue mode value for the T-04 benchmark-first candidate. Mode taxonomy defined by loop-ownership semantics: `server_assisted` (external helper owns structured state), `agent_local` (agent owns structured state locally), `manual_legacy` (no structured state, degraded fallback).

**Driver:** The current normative contract ties `server_assisted` to helper-mediated dialogue (`codex-dialogue.md:17`: "Start in `server_assisted` mode. If context injection tools are unavailable at conversation start, switch to `manual_legacy`"). The T-04 local loop is structurally different: it does not use `process_turn`/`execute_scout`, does not have helper-owned convergence logic, but does keep structured local state and scouts with direct host tools. It is neither `server_assisted` nor `manual_legacy`.

**Alternatives considered:**
- **Reuse `server_assisted`** — rejected because the current definition is tied to helper-mediated dialogue. Reuse would require broadening the term until it stops distinguishing the helper loop from the local loop.
- **Reuse `manual_legacy`** — rejected because `manual_legacy` is the degraded no-scout fallback. T-04 has structured state and planned scouting. Calling it `manual_legacy` collapses a meaningful distinction.
- **Transport-specific value (`cli_exec`)** — rejected because mode is about loop semantics, not transport. A transport label would be fragile under runtime changes.
- **Multi-field split (separate transport and orchestration fields)** — rejected for this slice because it widens the contract more than G4 requires.

**Trade-offs accepted:** Higher ceremony (third enum value, ~10-file migration set across 4 layers). The migration set includes normative contracts (`dialogue-synthesis-format.md`), schema (`event_schema.py`), producer contracts (`dialogue/SKILL.md`), and test enforcement (3 test files). Support docs (HANDBOOK, README) are follow-up, not gate-blocking. This is the more expensive branch, but it's the less misleading one.

**Confidence:** High (E2) — verified against all mode-consuming surfaces across 3 rounds of source mapping correction. The ownership-based taxonomy has no ambiguous gaps between values.

**Reversibility:** Medium — enum expansion is additive, but the three-value semantics are now committed. Removing `agent_local` later would require recategorizing T-04 events.

**Change trigger:** If T4 reintroduces helper-mediated scout direction or helper-owned state, T6 must reopen T5 rather than forcing that result under `agent_local`. If the T-04 candidate doesn't survive T8's dry-run, the mode value is unused but doesn't need removal (it's still a valid taxonomy entry for any future agent-local loop).

### `mode_source = null` for `agent_local` dialogue outcomes (user's design, Claude reviewed)

**Choice:** `agent_local` dialogue outcomes emit `mode_source = null`. No new `VALID_MODE_SOURCES` enum value.

**Driver:** `mode_source` distinguishes values parsed from a dialogue agent's epilogue (`"epilogue"`) from values supplied by parser fallback (`"fallback"`). For `agent_local`, the mode is intrinsically known by orchestration state — not parsed from an agent's self-report. Using `"epilogue"` would be misleading; using `"fallback"` would suggest the mode was a default, not a determination. `null` correctly means "epilogue/fallback provenance doesn't apply."

**Alternatives considered:**
- **`mode_source = "epilogue"`** — rejected because even if the implementation emits a machine-readable block, it's not the authority that decides the mode.
- **`mode_source = "direct"` (new enum value)** — rejected as unnecessary for this slice. `null` already carries the correct semantics.

**Trade-offs accepted:** `null` is indistinguishable from "field never set" at the value level. Mitigated by the combination: `mode = "agent_local"` + `mode_source = null` is unambiguous and no existing code path produces this combination.

**Confidence:** High (E2) — verified validator accepts null for dialogue_outcome (`emit_analytics.py:609-612`), and `VALID_MODE_SOURCES` doesn't need expansion.

**Reversibility:** High — `null` is the current default when pipeline omits the field. No schema change to revert.

**Change trigger:** If future analytics need to distinguish "intrinsically known mode" from "field not set," a new `mode_source` value would be warranted. Until then, `null` is sufficient.

### Sequencing: T5 first, then T4 (user's analysis, Claude confirmed)

**Choice:** Resolve G4 (mode strategy) before G3 (evidence provenance).

**Driver:** T5 is the narrower gate with the lowest branching cost. The critical path is T2→T3→T6→T7→T8; T4 and T5 are parallel prerequisites for T6. T5 can collapse the reuse-vs-migration fork before T4's larger integration surface, reducing the state space for T4.

**Alternatives considered:**
- **T4 first** — rejected because it doesn't clear the easier gate first and leaves G4 unresolved during the larger design work.
- **Bounded framing pass on both** — rejected because it produces no gate closure and risks drifting back into analysis.

**Trade-offs accepted:** Doesn't front-load the larger integration risk (T4). Acceptable because T4 and T5 are genuinely independent at the field level (confirmed by source pass).

**Confidence:** High — source pass confirmed T4 doesn't constrain T5 at the enum-field level. Mode semantics are tied to scouting availability, but T5's ownership-based definition is stable under T4 variations.

**Reversibility:** High — sequencing choice was one-session scope.

**Change trigger:** Would have switched to T4 first if the source pass showed T4 implicitly forces a new mode value.

## Changes

### Created files

| File | Purpose |
|------|---------|
| `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | Accepted design artifact for G4. Defines `agent_local` as third dialogue mode, ownership-based taxonomy, `mode_source = null` semantics, primary migration set (7 surfaces), explicit non-changes (8 surfaces), rejected alternatives (4), and 8 verification items. 330 lines. |

### Modified files

| File | Change | Purpose |
|------|--------|---------|
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G4 → `Accepted (design)` | Reflects gate promotion. G3 is the only remaining gate at `Proposed (source analysis)`. |

### Commits this session

| Commit | Message | Files |
|--------|---------|-------|
| `3411895e` | `docs: accept T-04 gates G1 G2 G5 with design contracts` | 4 files (T1, T2, T3 design notes + register with G1/G2/G5 promotions) |
| `adcaac61` | `docs: accept T-04 gate G4 with mode strategy contract` | 2 files (T5 design note + register with G4 promotion) |

### User-modified files (between messages, not by Claude)

The T5 design note was authored and revised by the user. Claude served as adversarial reviewer only. The T5 revision between the first and second review (adding section 3.5, removing `codex-dialogue.md` from migration set, adding verification item 8) was done by the user between messages.

## Codebase Knowledge

### Mode-Consuming Contract Surface (verified across 3 rounds)

The full mode surface spans 4 layers with ~16 locations. This map was verified through 3 rounds of source-level correction between Claude and the user.

**Layer 1: Normative contracts (define what mode means)**

| Surface | Location | What it defines |
|---------|----------|----------------|
| Agent mode gating | `codex-dialogue.md:17-18` | When each mode activates (CI tool availability → mode selection). `server_assisted` if `process_turn`/`execute_scout` available; `manual_legacy` fallback otherwise. No mid-conversation switching. |
| Synthesis format (human-readable) | `dialogue-synthesis-format.md:86` | Mode field in conversation summary. "Set once at conversation start." |
| Pipeline epilogue (machine-parsed) | `dialogue-synthesis-format.md:144` | Mode field in `<!-- pipeline-data -->` JSON block. Allowed values listed. |
| Consultation contract | `consultation-contract.md:477` | References `manual_legacy` fallback path for pre-briefing injection. |

**Layer 2: Schema and validation**

| Surface | Location | What it enforces |
|---------|----------|-----------------|
| Enum definition | `event_schema.py:137` | `VALID_MODES = frozenset({"server_assisted", "manual_legacy"})` |
| Mode sources | `event_schema.py:139` | `VALID_MODE_SOURCES = frozenset({"epilogue", "fallback"})` |
| Required fields | `event_schema.py:69,81` | `mode` required on `dialogue_outcome` and `consultation_outcome`. NOT on `delegation_outcome` (lines 83-94). |
| Hard validation | `emit_analytics.py:601-605` | Rejects unknown modes. Delegates to `VALID_MODES`. |
| Mode source validation | `emit_analytics.py:607-614` | `mode_source` nullable on dialogue_outcome, rejected on other types. |

**Layer 3: Producers**

| Surface | Location | How mode enters |
|---------|----------|----------------|
| Dialogue outcome builder | `emit_analytics.py:441-442` | `parsed.get("mode") or pipeline.get("mode", "server_assisted")`. Passes through parsed mode. |
| Consultation outcome builder | `emit_analytics.py:512` | `pipeline.get("mode", "server_assisted")`. Always `server_assisted`. |
| Dialogue skill pipeline | `dialogue/SKILL.md:435-436` | Parses mode from agent's `<!-- pipeline-data -->` epilogue. Fallback: `"server_assisted"` + `mode_source: "fallback"`. |
| Codex skill | `codex/SKILL.md:256,267` | Hardcoded `"server_assisted"`. |

**Layer 4: Downstream consumers and test enforcement**

| Surface | Location | What it locks |
|---------|----------|---------------|
| Stats aggregation | `compute_stats.py:256` | `mode_counts` via Counter (auto-handles new keys). |
| Operator guidance | `HANDBOOK.md:256` | "Interpret dialogue quality metrics in mode context." |
| README | `README.md:413` | References two-mode model. |
| Schema enum test | `test_event_schema.py:85-88` | Asserts `server_assisted` and `manual_legacy` in `VALID_MODES`. |
| Mode propagation tests | `test_emit_analytics_legacy.py:665-698` | `server_assisted` default, `manual_legacy` propagation, `mode_source` epilogue/fallback, `mode_source` absent on consultation. |
| Invalid mode rejection | `test_emit_analytics_legacy.py:989-993` | Unknown mode values rejected by validator. |
| Manual legacy fixture | `test_emit_analytics_legacy.py:1739-1748` | End-to-end `manual_legacy` validation. |
| Active parser fixtures | `test_emit_analytics.py:96-99,174` | `manual_legacy` baked into parser test fixtures. |

### Key architectural insight: mode contract is scattered, not centralized

The mode taxonomy has no single source of truth. Semantics are defined inline across `codex-dialogue.md` (when to use each mode), `dialogue-synthesis-format.md` (what each mode means in output), and `event_schema.py` (enum validation). The T5 decision chose not to centralize this — it keeps the scattered pattern and adds `agent_local` to the existing locations. The T5 design note itself serves as the de facto taxonomy document until the T-04 candidate's own contract is written.

### Cross-contract dependency graph (updated from session 14)

```
T2 (claim_source) ──→ T3 (registry excludes minimum_fallback)
                 └──→ T3 (counter filtering before T3 validation)

T1 (ControlDecision) ──→ standalone

T3 (claim_key, referent_key) ──→ depends on T2 (claim_source field)

T5 (agent_local) ──→ standalone (no T1/T2/T3/T4 dependency at field level)
                 └──→ semantic coupling to T4 (mode defined by ownership; T4 must not reintroduce helper mediation)
```

## Conversation Highlights

**Source pass correction — round 1 (user's 6 findings):**

The user's first correction message was the most substantive exchange in the session. It identified two High findings and four Medium findings, each with specific file:line evidence. The user's framing: "Your map says the surface is 'all in the analytics/event layer,' but the repo's live mode contract is also defined in the delegated-agent instructions and the machine-output format." This reframed the source pass from "find where the field is used" to "find where the contract is defined, enforced, and consumed." The user also flagged the "genuinely orthogonal" claim about T4/T5 as too strong: "They are orthogonal at the enum-field level, but not fully at the semantics level."

**Source pass correction — round 2 (user's 3 findings):**

After the corrected map, the user applied priority labels (P1/P2/P3) for the first time in the session. P1 was the factual error about delegation_outcome requiring mode — the user cited `event_schema.py:83` and `emit_analytics.py:575` directly. P2 was the mislabeled test row. P3 acknowledged that the map was "close" but noted README and HANDBOOK as additional surfaces. The user's conclusion: "The corrected map now matches the repo on the points that mattered... The remaining risk is not the T5 recommendation itself. The risk is using this map as the implementation checklist for a third-mode migration and silently missing non-primary consumers or tests."

**T5 draft framing:**

The user introduced the T5 draft with a pre-emptive justification: "The current normative contract still ties `server_assisted` to the helper-mediated `process_turn` / `execute_scout` loop, while `manual_legacy` is the degraded no-scout fallback. On that contract, the T-04 local ledger loop is neither." This preempted the reuse argument before the review even started. The user also explicitly positioned the remaining risk: "The draft's main pressure point is deliberate: it keeps `/codex` consultation semantics unchanged while expanding the shared mode enum for dialogue."

**Review escalation pattern:**

The user applied `/scrutinize` for the first review, then `/review-strategy` for the second. The scrutinize pass found implementation-level gaps (mode_source, migration target, verification path). The strategy pass evaluated structural risks and fragile assumptions. This is a deliberate two-lens approach: find the concrete issues first, then stress-test the strategic position. The user used this same escalation in session 14 for T3 (which went through 3 review cycles).

## Context

### Mental Model

This session's framing: **"contract surface mapping as a prerequisite for taxonomy decisions."** The T5 decision couldn't be made until the full mode surface was mapped. The mapping took 3 rounds because the first pass searched for field usage (where `mode` appears in code) rather than contract surface (where `mode` is defined, produced, validated, consumed, and locked by tests). The lesson: a complete contract surface includes definition, production, validation, and consumption — searching for the field name in code only finds the middle two.

The user's framing of T5 itself: "this is the narrower truthful contract" — the mode field should accurately describe what the candidate IS, not what it vaguely resembles. The ownership boundary (who owns state and convergence computation) is more stable than capability boundaries (does it scout?) or transport boundaries (how does it reach Codex?).

### Execution Methodology

Source-verified adversarial review with escalating scrutiny:
- **Source pass:** 3 rounds of correction to build the mode surface map (6 findings → 3 findings → verified)
- **First review (/scrutinize):** 3 findings on T5 draft (mode_source gap, wrong migration target, verification gap)
- **Second review (/review-strategy):** Defensible, no required changes

The user corrected Claude's source pass twice before drafting T5. This is the reverse of the session 14 pattern (user drafts, Claude reviews). In this session, Claude did preliminary research, the user corrected it, then the user drafted on top of the corrected map.

### Project State

- **Branch:** `main` at `adcaac61`
- **Tests:** 460 passing (unchanged since session 11)
- **Local main ahead of origin by 12+ commits** (sessions 11-15 design work, handoff archives)
- **T-04 gate status:**

| Gate | Status | Accepting artifact |
|------|--------|--------------------|
| G1 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` |
| G2 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| G3 | `Proposed (source analysis)` | — |
| G4 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` |
| G5 | `Accepted (design)` | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |

- **Working tree:** Clean. All design artifacts committed.
- **No code written** — sessions 12-15 have been pure analysis, planning, and design.

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1-10 | 2026-03-31 – 2026-04-01 | Runtime build chain | See session 11 handoff |
| 11 | 2026-04-01 | Repo hygiene + T-04 recon | `archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md` |
| 12 | 2026-04-01 | T-04 convergence adversarial review | `archive/2026-04-01_23-41_t04-convergence-loop-adversarial-review.md` |
| 13 | 2026-04-02 | Risk register review + design plan | `archive/2026-04-02_00-36_t04-risk-register-and-design-plan.md` |
| 14 | 2026-04-02 | Gate resolution: T1, T2, T3 | `archive/2026-04-02_02-29_t04-gate-resolution-t1-t2-t3.md` |
| **15** | **2026-04-02** | **Gate G4 mode strategy accepted** | **This handoff** |

## Learnings

### Source pass for contract surfaces must search across 4 layers, not just code usage

**Mechanism:** A naive source pass searches for where a field name appears in code (grep for `mode`). This finds producers (builders) and validators but misses: (1) normative contracts that define what the field means (agent instructions, synthesis format docs), (2) downstream consumers that interpret or aggregate the field (stats, operator docs), and (3) test enforcement that locks current behavior (enum assertions, propagation tests, fixtures).

**Evidence:** First source pass found 6 locations in the analytics/event layer. The user's corrections expanded this to ~16 locations across 4 layers: normative contracts (`codex-dialogue.md:17`, `dialogue-synthesis-format.md:86,144`), schema/validation (`event_schema.py`, `emit_analytics.py`), producers (SKILL.md pipeline parsing), and downstream consumers/tests (stats, HANDBOOK, README, 5 test files). The first pass missed the most important layer (normative contracts — where mode is defined).

**Implication:** Any future contract surface mapping should enumerate all 4 layers explicitly: (1) definition (what does the field mean?), (2) production (what sets it?), (3) validation (what enforces it?), (4) consumption (what reads and interprets it?). Searching for field usage in code only reliably finds layers 2 and 3.

**Watch for:** Fields that are defined in prose documents (agent instructions, synthesis formats) rather than in code. These are the hardest to find by searching and the most important for taxonomy decisions.

### `mode` is NOT required on `delegation_outcome`

**Mechanism:** `delegation_outcome` has its own required field set at `event_schema.py:83-94` that does not include `mode`. The validator at `emit_analytics.py:575-576` explicitly skips all mode/posture/convergence checks for delegation events: `if event_type != "delegation_outcome":`.

**Evidence:** Verified by reading `event_schema.py:83-94` and `emit_analytics.py:575-576`. The first corrected source pass incorrectly claimed mode was required on all 3 event types — the user caught this as a P1 factual error.

**Implication:** Delegation events are structurally different from dialogue/consultation events. Future contract changes that touch the shared schema must check which event types each field applies to — the required field sets are not identical.

**Watch for:** Assumptions that all event types share the same required fields. They don't. Check `REQUIRED_FIELDS_BY_EVENT` at `event_schema.py:63-94`.

### Taxonomy decisions require ownership-based boundaries, not capability-based

**Mechanism:** The T5 decision defined mode by who owns the dialogue loop (external helper, agent itself, or degraded fallback), not by what capabilities the loop has (does it scout? does it track state?). The ownership boundary is more stable under future changes: T4 can change scouting details without affecting mode classification, because mode is about who runs the loop, not what the loop does.

**Evidence:** The user's T5 draft section 2: "The accurate dividing line is therefore ownership of the dialogue mechanism." Verified by checking that the ownership boundary produces clean three-way classification with no ambiguous edge cases.

**Implication:** Future taxonomy additions (if needed) should extend the ownership axis. A capability-based taxonomy would create classification ambiguity for hybrid cases (e.g., local state but helper-directed scouting).

**Watch for:** T4's design introducing helper-mediated elements that blur the ownership boundary. If this happens, T6 must reopen T5.

## Next Steps

### 1. Start T4 (scouting position and evidence provenance) — the last gate

**Dependencies:** T4 depends on Risk D (scouting position must be fixed before evidence records can be finalized). T4 is the prerequisite for G3, which is the last gate before T6.

**What to read first:**
- Design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` for T4 scope
- Risk register G3 required design outcome and linked risks (J, D, F, E) at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`
- Source analysis sections on scouting and evidence provenance at `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md`
- Current scouting implementation in `codex-dialogue.md` (scouting phases) and `execute.py` (scout execution)
- `emit_analytics.py:376-449` (`build_dialogue_outcome` — where evidence fields are currently derived)

**Approach:** The user drafts the T4 design contract covering: (1) fixed scout-capture point in the loop, (2) per-scout evidence record schema, (3) synthesis citation surface that consumes those records. Claude reviews adversarially against the source code.

**Acceptance criteria:** User explicitly accepts the scouting position and evidence schema. G3 moves to `Accepted (design)`. All 5 gates then at `Accepted`, and T6 (composition check) can start.

**Potential obstacles:** T4 is the most complex remaining gate by feature surface — it touches layers 4-6 (scouting, follow-up, synthesis). The session 14 handoff noted T4 may need more than one review cycle. Risk D must be resolved before G3 can be finalized.

### 2. After G3: T6 composition check

**Dependencies:** All 5 gates must be `Accepted (design)`.

**What it does:** Adversarial composition check — do the 5 independently-accepted gates compose into one consistent design? Main interaction points: T2→T3 (claim_source feeds registry exclusion), T5→T4 semantic coupling (mode defined by ownership; T4 must not reintroduce helper mediation). T1 is genuinely independent.

**Risk:** "Plans fail at composition, not decomposition" (session 13's framing). The main composition risk is T4's evidence schema interacting with T2's claim_source filtering and T3's referential validation.

### 3. Consider pushing to origin

**Dependencies:** None technical.

**Context:** Local main is now 12+ commits ahead of origin. All design work (sessions 11-15) is committed locally but not pushed. If coordination becomes necessary, pushing is needed.

## In Progress

Clean stopping point. G4 accepted, all design artifacts committed, working tree clean. No design work in flight.

## Open Questions

### Will T4's scouting design stay within the `agent_local` ownership boundary?

T5's acceptance is contingent on T4 not reintroducing helper-mediated scout direction. If T4's evidence schema requires a helper service for scouting, T6 must reopen T5. The T-04 candidate is defined as a local loop, so this is unlikely but must be verified at T6.

### What is the right depth for T4's evidence record schema?

T4's G3 required design outcome says "a per-scout evidence record schema exists." The complexity is in the schema's granularity: does each scout record need `{turn, target_claim, path, line_range, snippet, disposition}` (as the register suggests), or can it be simpler for the benchmark-first slice? The user will need to balance completeness against implementation scope.

### Local main is now 12+ commits ahead of origin

Same as session 14. Accumulated design commits haven't been pushed. No coordination pressure yet.

## Risks

### Design work is pure docs — no implementation feedback until T8

Sessions 12-15 have been analysis, planning, and design. No code written. The earliest implementation feedback is T8 (implement minimal executable slice and run dry-run). If a design decision only manifests failure under execution (e.g., the evidence record shape doesn't serialize, or mode routing doesn't compose), it won't surface until the implementation sessions.

### T4 is the largest remaining design surface

T4 touches layers 4-6 and has 4 linked risks (J, D, F, E). The session 14 handoff estimated it may need more than one review cycle. If T4 proves contentious, it delays T6 and the entire implementation timeline.

### Source pass reliability

This session demonstrated that Claude's source passes can miss important contract surfaces. The first pass found 6/16 locations. The user caught the remaining 10 across 2 correction rounds. For T4's source verification, the lesson is to explicitly enumerate all 4 layers (definition, production, validation, consumption) rather than searching for field names in code.

## References

| What | Where |
|------|-------|
| T5 design contract (accepted) | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` |
| T1 design contract (accepted) | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` |
| T2 design contract (accepted) | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| T3 design contract (accepted) | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |
| Risk register (4 gates accepted, 1 proposed) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| Source analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| T-04 ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Mode gating (agent instructions) | `packages/plugins/cross-model/agents/codex-dialogue.md:17-18` |
| Synthesis format (mode definition) | `packages/plugins/cross-model/references/dialogue-synthesis-format.md:86,144` |
| Mode enum | `packages/plugins/cross-model/scripts/event_schema.py:137` |
| Mode validation | `packages/plugins/cross-model/scripts/emit_analytics.py:601-614` |
| Dialogue outcome builder | `packages/plugins/cross-model/scripts/emit_analytics.py:441-442` |
| Stats aggregation | `packages/plugins/cross-model/scripts/compute_stats.py:256` |
| Session 14 handoff | `docs/handoffs/archive/2026-04-02_02-29_t04-gate-resolution-t1-t2-t3.md` |

## Gotchas

### `mode` required fields differ by event type

`mode` is required for `dialogue_outcome` and `consultation_outcome` but NOT for `delegation_outcome`. The validator at `emit_analytics.py:575-576` skips all mode/posture/convergence checks for delegation events. Don't assume all event types share the same required fields — check `REQUIRED_FIELDS_BY_EVENT` at `event_schema.py:63-94`.

### Source passes that search for field names miss normative contracts

The mode surface has ~16 locations across 4 layers. Searching for `mode` in code finds producers and validators but misses agent instructions (`codex-dialogue.md:17`) and synthesis format docs (`dialogue-synthesis-format.md:86,144`) that define what the field means. For taxonomy decisions, the definition layer is the most important and the easiest to miss.

### `mode_source` is null for `agent_local`, not a new enum value

The T5 contract specifies `mode_source = null` for `agent_local` dialogue outcomes. This means "epilogue/fallback provenance doesn't apply" — the mode is intrinsically known. Don't introduce a new `VALID_MODE_SOURCES` value for this. `null` is already accepted by the validator for dialogue_outcome events.

### T5's acceptance is contingent on T4 staying within the ownership boundary

If T4's scouting design reintroduces helper-mediated scout direction or helper-owned state, T6 must reopen T5. The `agent_local` classification assumes the agent owns the full loop including scouting. This is stated explicitly in T5 section 4 and section 3.5.

### 4 of 5 gates accepted, but the register still shows G3 as Proposed

The register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` now has G1, G2, G4, G5 at `Accepted (design)` and only G3 at `Proposed (source analysis)`. Future references to "remaining gates" or "gates still proposed" should say G3 only, not G3 and G4.

## User Preferences

**Adversarial reviewer role continued:** Consistent with sessions 12-14. The user drafts all design artifacts. Claude provides adversarial review and source-code verification. The user does not ask Claude to draft design contracts.

**Escalating scrutiny levels:** The user applied both `/scrutinize` and `/review-strategy` to the same T5 artifact. The first review found implementation-level gaps (mode_source, migration row, verification path). The second review evaluated the corrected artifact at a strategic level (fragile assumptions, scenarios where it breaks, signals that validate/falsify). Pattern: the user uses multiple scrutiny lenses on the same artifact to find different classes of issues.

**Source verification as a collaborative tool:** The user corrected Claude's source pass with specific file:line evidence. The user classified findings by priority (P1/P2/P3 in the second correction round) with specific remediation guidance for each. The user does not accept source claims without verification — every claim about the mode surface was checked against the actual files.

**Decisive acceptance pattern:** After the second review found no required changes, the user immediately promoted G4 and requested the handoff. No hesitation or additional review requests when the artifact is ready. Same pattern as session 14.

**Precise critique formatting:** The user's correction messages follow a consistent structure: numbered findings, each with severity, specific file:line evidence, explanation of why the current claim is wrong, and what the correct claim should be. This is the same format across sessions 12-15.
