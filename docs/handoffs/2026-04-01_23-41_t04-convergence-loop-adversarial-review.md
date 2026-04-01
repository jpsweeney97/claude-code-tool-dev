---
date: 2026-04-01
time: "23:41"
created_at: "2026-04-01T23:41:37Z"
session_id: d8d5df7c-4419-4765-bcdb-b75fd71e41fe
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md
project: claude-code-tool-dev
branch: main
commit: 6ea3e331
title: "T-04 convergence loop adversarial review"
type: handoff
files:
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md
  - packages/plugins/cross-model/context-injection/context_injection/control.py
  - packages/plugins/cross-model/context-injection/context_injection/ledger.py
  - packages/plugins/cross-model/context-injection/context_injection/pipeline.py
  - packages/plugins/cross-model/context-injection/context_injection/conversation.py
  - packages/plugins/cross-model/agents/codex-dialogue.md
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/scripts/emit_analytics.py
  - packages/plugins/cross-model/scripts/event_schema.py
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/server/models.py
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
---

# T-04 convergence loop adversarial review

## Goal

Perform deep adversarial analysis of the convergence loop architecture for T-20260330-04 (dialogue parity and scouting retirement). The session's purpose was to stress-test the proposed benchmark-first design slice before any design document or code is written, ensuring the structural logic is sound and the risk surface is mapped.

**Trigger:** Session 11 completed T-04 reconnaissance — reading the cross-model dialogue architecture as semantic source. The user entered this session with a fully formed analysis of the convergence loop and three prioritized hypotheses. This session was the adversarial pass before moving to design.

**Stakes:** High. The convergence model is the load-bearing component for the benchmark. If the design is wrong here, the entire T-04 implementation can look complete while failing the benchmark's `converged_within_budget` metric. Getting the invariants right before design prevents expensive mid-implementation corrections.

**Success criteria:** (1) User's convergence analysis verified against source code. (2) Risks identified with severity, benchmark impact, and mitigations. (3) Corrections from user review incorporated. (4) Pre-design invariants established as hard gates for the T-04 design.

**Connection to project arc:** Session 12 in the codex-collaboration build chain. Sessions 1-10 built the runtime (460 tests, finalization durability, replay safety). Session 11 completed repo hygiene and T-04 reconnaissance. This session is the adversarial review gate between reconnaissance and design — the last checkpoint before implementation planning begins.

## Session Narrative

Resumed from the session 11 handoff. Session 11 left a clean stopping point: T-04 reconnaissance complete, cross-model architecture read and documented, no code written, no design decisions made.

**Phase 1: User-led convergence analysis.** The user opened with a fully formed analysis covering three hypotheses ordered by likelihood: (1) convergence and synthesis parity after removing `process_turn`/`execute_scout` — the highest-risk gap; (2) the deterministic briefing assembly pipeline as the real reusable asset; (3) benchmark harness and artifact production as the largest delivery risk. The user confirmed hypothesis 1 as the right first cut and presented detailed findings from their own exploration of the convergence loop.

The user's analysis identified the key architectural insight: the convergence policy in `control.py:58-142` is small and deterministic (budget exhaustion → plateau detection → closing probe sequencing → continue), and the heavyweight parts of `process_turn` specific to plugin-side scouting (checkpoints, entity extraction, template ranking, HMAC tokens, evidence budget) can be dropped for the benchmark candidate. The user proposed a "server-free but scout-capable" loop — distinct from `manual_legacy` (which is a no-scout fallback with `evidence_count = 0`).

The user also identified that codex-collaboration's current `dialogue.py` provides transport and durability but no semantic control layer — no ledger of claims/deltas/unresolved items, no convergence action computation, and no benchmark-facing epilogue contract. Phased profiles are still rejected in `profiles.py:98-105`.

**Phase 2: Adversarial review.** I read the full source files the user referenced — `control.py` (223 lines), `ledger.py` (270 lines), `pipeline.py:280-352` (process_turn steps 14-17), `conversation.py` (state model), `codex-dialogue.md:180-520` (7-step loop, manual_legacy, phase tracking, synthesis), `dialogue-synthesis-format.md:130-170` (epilogue), `emit_analytics.py:330-368` (convergence mapper), and the benchmark contract at `dialogue-supersession-benchmark.md:50-170`.

I identified 9 risks (A-I) across the proposed 7-point slice. The key findings:

1. **`effective_delta` is server-computed, not agent-reported** (`ledger.py:101-110`). The server computes delta from claim status counters (new → ADVANCING, revised/conceded → SHIFTING, else → STATIC), NOT from the agent's self-reported `delta` field. The `_delta_disagrees` warning (`ledger.py:113-127`) fires when the two diverge but is only a soft warning. This means T-04's convergence module must compute deltas from counters, not from narrative assessment.

2. **User's minimum state list conflated convergence with analytics state.** `compute_action` takes exactly 4 inputs: entries, budget_remaining, closing_probe_fired, optional phase_entries. Cumulative counters are derived. Evidence count and scope breach count are orchestration metrics, not convergence inputs.

3. **Phase support is a non-decision for the benchmark** — all 8 benchmark tasks use single postures (evaluative, adversarial, or comparative). The benchmark structurally cannot test phase support.

4. **`generate_ledger_summary` powers follow-up quality** — it's a compact per-turn text summary used by the agent for "conversation awareness" in follow-up composition, not just a diagnostic annotation.

5. **The convergence_reason_code mismatch** between `dialogue-synthesis-format.md:148` (null for non-converged) and `emit_analytics.py:337-368` (always set) is a two-layer processing issue, not runtime corruption. The emitter recomputes from raw state, not from the agent's epilogue field.

The user accepted the review, refined their design slice to separate convergence state from analytics state, and added `generate_ledger_summary` as a required port.

**Phase 3: User review of the adversarial review.** The user then performed a second-pass review of my analysis and found 6 corrections and 2 missing risks:

**Correction 1 (P1): Risk A — `compute_quality` misread.** I claimed `compute_quality` would catch fallback claims as SHALLOW. Wrong. `compute_quality` at `ledger.py:89-98` marks any turn with `new_claims > 0` as SUBSTANTIVE. A minimum-claim fallback with status `new` is always SUBSTANTIVE. My proposed "quality-based downgrade" would never fire. The real fix: explicit provenance marking (`synthetic_minimum_claim` or `claim_source=fallback`) so the computation layer can exclude fallback claims from `new_claims` counting.

**Correction 2 (P1): Risk B — prose parsing.** I proposed deriving `converged` by checking if `action_reason` contains "Budget exhausted". But `action_reason` is a formatted prose string (`control.py:104`: `f"Budget exhausted ({budget_remaining} turns remaining)"`), not a stable machine contract. This violates the "compute, don't assess" principle I articulated. The fix: T-04's `compute_action` must return a structured `TerminationCode` enum.

**Correction 3 (P1): Risk H — severity underrated.** I rated the mode field issue as Low/"naming choice". The user showed it's a multi-surface contract migration: `event_schema.py:137` (`VALID_MODES` frozenset), `SKILL.md:435` (epilogue parser with fallback), `dialogue-synthesis-format.md:86` (documented values). Invalid values are silently rewritten to `server_assisted` via fallback logic. Upgraded to Medium-High.

**Correction 4 (P2): Risk C — semantic overlap violates computation boundary.** I proposed "semantic overlap" for referential checks. The user correctly pointed out this reintroduces LLM judgment into the deterministic computation layer. Fix: normalized exact matching or explicit claim IDs.

**Correction 5 (P2): Risk F — entry survival, not just summary recomputation.** I focused on recomputing `ledger_summary`. The deeper issue: the entries themselves must survive context compression. Need a canonical ledger block re-emitted each turn.

**Correction 6 (P2): Risk E — drop mechanism, keep function.** I said "drop `unknown_claim_paths`" without distinguishing mechanism from function. The path-tracking machinery goes; provenance debt tracking stays as a simpler uncited-claims backlog.

**Missing Risk 1 (P1): Evidence retention.** Cross-model stores structured `scout_outcomes` per turn in `turn_history` (`codex-dialogue.md:308`). Synthesis format expects evidence trajectory (`dialogue-synthesis-format.md:123`). If T-04 only tracks `evidence_count`, synthesis can't produce provenance-backed citations, directly degrading `supported_claim_rate`.

**Missing Risk 2 (P2): `unresolved_closed` derivation.** `compute_counters` at `ledger.py:68-86` takes `unresolved_closed` as a caller-supplied parameter (docstring: "D1 has no access to prior state for comparing unresolved lists"). The pipeline diffs previous vs current unresolved lists to compute this. If T-04 omits the diff, `unresolved_closed` is always 0.

I verified each correction against the source code, updated the review document with inline correction notices, added the two missing risks (J, K), revised the severity table, and added a corrections log.

**Phase 4: Review artifact and handoff.** The corrected risk analysis was saved to `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md`. The user will turn it into a corrected risk register with exact invariants in the next session.

## Decisions

### Hypothesis 1 (convergence model) is the right first cut for T-04

**Choice:** Focus T-04's design on the convergence and synthesis parity gap, not on evidence gathering or benchmark harness.

**Driver:** The user's analysis: "If we get the convergence model wrong, the rest of the port can look complete while still failing the benchmark." The benchmark's `converged_within_budget` metric is a pass-rule gate — it cannot be compensated by other metrics.

**Alternatives considered:**
- **Hypothesis 2 first (briefing assembly)** — the briefing pipeline is more reusable as-is. Rejected because it's lower risk: the deterministic assembly logic has no behavioral dependencies.
- **Hypothesis 3 first (benchmark harness)** — largest delivery risk in absolute terms. Rejected because without a correct convergence model, the harness would produce invalid runs.

**Trade-offs accepted:** The briefing pipeline and benchmark harness are deferred. If convergence design takes longer than expected, the other components slip proportionally.

**Confidence:** High (E2) — convergence model directly feeds 2 of 4 pass-rule metrics (`converged_within_budget` and indirectly `supported_claim_rate` via follow-up quality).

**Reversibility:** High — no code written. Can switch focus at any time.

**Change trigger:** If the benchmark contract is revised to remove or weaken the convergence metric.

### Phase support deferred unconditionally for first T-04 cut

**Choice:** Exclude phased profiles from the benchmark-first T-04 slice.

**Driver:** All 8 benchmark tasks specify single postures (B1-B2,B5-B6: evaluative; B3: adversarial; B4,B7-B8: comparative). The benchmark structurally cannot test phase support. Implementing it for the first cut would be dead code relative to the benchmark.

**Alternatives considered:**
- **Include phase support in first cut** — achieves feature parity with cross-model's `codex-dialogue.md:465-497`. Rejected because it adds complexity (closing_probe_fired reset, phase_entries windowing, posture transitions) with zero benchmark impact.

**Trade-offs accepted:** Full cross-model feature parity is deferred. T-04's dialogue surface won't support multi-posture profiles until a follow-up.

**Confidence:** High (E2) — verified by reading the benchmark corpus at `dialogue-supersession-benchmark.md:60-69`. No phased profiles in any task.

**Reversibility:** High — phase support can be added later without redesigning the convergence model. The `phase_entries` parameter in `compute_action` is already optional (`control.py:63`).

**Change trigger:** If the benchmark corpus is expanded to include phased-profile tasks.

### convergence_reason_code: always set (emitter style)

**Choice:** Align with `emit_analytics.py:337-368` (always set `convergence_reason_code` with one of: `all_resolved`, `natural_convergence`, `budget_exhausted`, `error`, `scope_breach`) rather than `dialogue-synthesis-format.md:148` (null when not converged).

**Driver:** The emitter-style mapping is more informative — it tells you WHY the dialogue stopped regardless of convergence status. The benchmark's `converged_within_budget` metric needs the `converged` boolean from the structured termination code, not the reason code, so the format choice doesn't affect pass/fail.

**Alternatives considered:**
- **Null for non-converged (synthesis format style)** — simpler, fewer values. Rejected because it loses the distinction between budget exhaustion and error/scope breach, which matters for adjudication interpretation.

**Trade-offs accepted:** Diverges from the synthesis format's documented convention. T-04's design should document this as an intentional deviation.

**Confidence:** Medium (E1) — the emitter approach is strictly more informative. The risk is confusion if someone reads the synthesis format docs and expects null.

**Reversibility:** High — trivial to change the mapping.

**Change trigger:** If the benchmark adjudicator relies on the synthesis format convention (null) rather than reading the `converged` boolean directly.

### Drop unknown_claim_paths mechanism, keep provenance debt function

**Choice:** Remove the path-level template machinery (`[SRC:unknown]` extraction, tiered entity matching, selection tracking, per-path clearing) from T-04's state. Replace with a simpler uncited-claims backlog consulted during follow-up prioritization.

**Driver:** The `unknown_claim_paths` mechanism exists because cross-model's scouting is indirect (HMAC tokens, template selection, entity resolution). When the agent has direct file access (Glob/Grep/Read), the entire indirection layer is unnecessary. But the FUNCTION — ensuring uncited or unverified claims get follow-up priority — must survive.

**Alternatives considered:**
- **Port unknown_claim_paths verbatim** — ~30 lines of complex agent instructions (tiered matching against entity canonicals). Rejected because the mechanism solves a problem T-04 doesn't have (indirect tool access).
- **Drop provenance tracking entirely** — simplest. Rejected because uncited claims would disappear from follow-up prioritization, degrading synthesis citation quality.

**Trade-offs accepted:** The simpler backlog is less structured than path-level tracking. An uncited claim might get re-verified after already being checked, wasting a scouting round. Acceptable given the low frequency.

**Confidence:** Medium (E1) — the mechanism/function distinction is clear. The risk is in the replacement backlog's design (not yet specified).

**Reversibility:** High — the backlog is a state-tracking detail, not an architectural commitment.

**Change trigger:** If benchmark runs show uncited claims systematically not being addressed in follow-ups.

## Changes

### Created files

| File | Purpose |
|------|---------|
| `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risk analysis covering 11 risks (A-K) across the benchmark-first design slice. Includes corrections log from user review. Design-input artifact for T-04 planning. |

## Codebase Knowledge

### Cross-Model Convergence Architecture (4 layers, fully mapped)

This session's primary contribution is a detailed semantic map of the convergence system across 4 layers. All file:line references verified against source.

#### Layer 1: Ledger Validation (`ledger.py`)

| Function | Location | Purpose |
|----------|----------|---------|
| `validate_ledger_entry` | `ledger.py:143-238` | Structural validation: non-empty claims, turn bounds, referential consistency |
| `compute_counters` | `ledger.py:68-86` | Count new/revised/conceded claims. **Takes `unresolved_closed` from caller** — D1 has no access to prior state |
| `compute_quality` | `ledger.py:89-98` | SUBSTANTIVE if any non-reinforced activity (new, revised, conceded, or closures). **`new_claims > 0` → SUBSTANTIVE** — fallback claims are never SHALLOW |
| `compute_effective_delta` | `ledger.py:101-110` | ADVANCING if new claims, SHIFTING if revised/conceded, else STATIC. **Computed from counters, not from agent's `delta`** |
| `_delta_disagrees` | `ledger.py:113-127` | Soft warning when agent's self-reported delta contradicts computed effective_delta |
| `_referential_warnings` | `ledger.py:241-270` | Soft warning for reinforced/revised/conceded claims with no exact-text prior match |

**Critical insight:** `effective_delta` is the convergence-relevant signal. It is mechanically derived from claim status counters, NOT from the agent's narrative assessment of whether things are "advancing." This is the trust boundary between agent observation and convergence computation.

**`unresolved_closed` dependency:** `compute_counters` accepts `unresolved_closed` from its caller (the pipeline), which computes it by diffing previous vs current unresolved lists. If T-04 ports `compute_counters` without the diff, `unresolved_closed` is always 0, and closures are never counted as SUBSTANTIVE activity.

#### Layer 2: Convergence Control (`control.py`)

| Function | Location | Purpose |
|----------|----------|---------|
| `compute_action` | `control.py:58-142` | Deterministic action computation from ledger state |
| `generate_ledger_summary` | `control.py:167-223` | Compact text summary for agent follow-up composition |
| `_is_plateau` | `control.py:43-48` | Last `MIN_ENTRIES_FOR_PLATEAU` (2) entries all STATIC |
| `_has_open_unresolved` | `control.py:51-55` | Latest entry has unresolved items |

**`compute_action` inputs (exactly 4):**

| Input | Source | Required? |
|-------|--------|-----------|
| `entries` | Validated ledger entries (all turns) | Yes |
| `budget_remaining` | `MAX_TURNS - cumulative.turns_completed` | Yes |
| `closing_probe_fired` | Boolean flag | Yes |
| `phase_entries` | `entries[phase_start_index:]` for phase-local plateau detection | Optional (None for single-posture) |

**`compute_action` returns `(ConversationAction, str)` where the string is PROSE, not a machine contract.** The action is an enum (`CONTINUE_DIALOGUE`, `CLOSING_PROBE`, `CONCLUDE`). The reason is formatted text like `f"Budget exhausted ({budget_remaining} turns remaining)"`. T-04 must NOT derive `converged` by parsing this string.

**Closing probe policy (once per phase):** A closing probe fires at most once per phase. On phase transition, `closing_probe_fired` resets via `conversation.py:61-71` (`with_posture_change` sets `closing_probe_fired: False`). Within a phase, if the conversation advances after a closing probe (plateau broken), a second plateau skips the probe and proceeds directly to CONCLUDE.

**`generate_ledger_summary` output format:**
```
T1: [position] (effective_delta, tags)
T2: [position] (effective_delta, tags)
State: N claims (R reinforced, V revised, C conceded), U unresolved open
Trajectory: advancing → shifting → static
```
Target: 300-400 tokens for 8 turns. Used by the agent for "conversation awareness" in follow-up composition. Not cosmetic — directly affects follow-up quality.

#### Layer 3: Pipeline Integration (`pipeline.py`)

The pipeline orchestrates 17 steps per `process_turn` call. The convergence-relevant steps are:

| Step | Line | Operation |
|------|------|-----------|
| 12 | `pipeline.py:270-278` | Ledger entry validation (compute counters, quality, effective_delta) |
| 13 | `pipeline.py:280` | Build provisional state (append entry) |
| 14 | `pipeline.py:282-307` | Compute cumulative, reconcile posture/phase, compute action |
| 15 | `pipeline.py:309-313` | Closing probe projection (set flag if action is closing_probe) |
| 17 | `pipeline.py:322-326` | Generate ledger summary |

**Phase reconciliation detail (`pipeline.py:286-300`):** The pipeline tracks posture changes. First turn: set initial posture. Subsequent turns: if posture changed, create new phase at `with_posture_change(posture, phase_start_index=len(entries)-1)`. Then derive `phase_entries = provisional.get_phase_entries()` and pass to `compute_action`.

#### Layer 4: Server Conversation State (`conversation.py`)

```python
class ConversationState(BaseModel):
    conversation_id: str
    entries: tuple[LedgerEntry, ...] = ()
    claim_registry: tuple[Claim, ...] = ()
    evidence_history: tuple[EvidenceRecord, ...] = ()
    closing_probe_fired: bool = False
    last_checkpoint_id: str | None = None
    last_posture: str | None = None
    phase_start_index: int = 0
```

**Immutable projection pattern:** State is never mutated. `with_turn()`, `with_closing_probe_fired()`, `with_posture_change()` return new instances via `model_copy(update={...})`. Pipeline commits atomically by replacing the dict entry.

### Contract Surfaces for Mode Field

The synthesis `mode` field touches three surfaces that must be updated together:

| Surface | File | Constraint |
|---------|------|------------|
| Analytics validation | `event_schema.py:137` | `VALID_MODES = frozenset({"server_assisted", "manual_legacy"})` |
| Skill epilogue parser | `SKILL.md:435` | Invalid mode → fallback to `"server_assisted"`, `mode_source = "fallback"` |
| Synthesis format spec | `dialogue-synthesis-format.md:86` | Documents only two values |

An invalid mode value is silently rewritten to `server_assisted` by the skill's fallback logic, making baseline and candidate runs indistinguishable in the benchmark artifacts.

### Analytics Convergence Mapping (`emit_analytics.py:337-368`)

```python
def map_convergence(converged, unresolved_count, turn_count, turn_budget, scope_breach=False):
    if scope_breach: return ("scope_breach", "scope_breach")
    if converged and unresolved_count == 0: return ("all_resolved", "convergence")
    if converged and unresolved_count > 0: return ("natural_convergence", "convergence")
    if not converged and turn_count >= turn_budget: return ("budget_exhausted", "budget")
    return ("error", "error")  # fallback for contradictory state
```

This function recomputes from raw state (booleans, counts), NOT from the agent's epilogue. The emitter-style mapping is always-set (no null), unlike the synthesis format's nullable convention.

### codex-collaboration's Current Dialogue State

`dialogue.py:92-150` provides:
- Thread creation with journaled intent/dispatched phases
- Profile resolution (posture, effort, turn budget)
- Lineage-persisted `CollaborationHandle` with status tracking

`dialogue.py:335-404` provides:
- Reply dispatch with journaled intent and crash recovery
- Turn sequencing via `_next_turn_sequence` (contracts.md:266)
- Context assembly reuse from the consult pipeline

`models.py:160-200`: `OutcomeRecord` (analytics, sessions 8-10 AC6) tracks `outcome_type`, `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `turn_sequence`.

**What's missing for T-04:** No ledger entries, no claim tracking, no effective_delta computation, no convergence action computation, no ledger summary, no structured evidence records, no benchmark-facing epilogue contract.

### Benchmark Contract Details

**Corpus:** 8 tasks (B1-B8), all single-posture, all from codex-collaboration repo itself.

**Pass rule (ALL must hold):**
1. `safety_violations == 0`
2. Candidate `false_claim_count` ≤ baseline
3. Candidate `supported_claim_rate` within 0.10 of baseline
4. Candidate `converged_within_budget` ≥ baseline - 1

**`converged_within_budget` definition (`benchmark contract:159`):** "Binary result recorded by the dialogue orchestrator; if the system cannot emit it, the run is invalid."

**Required artifacts:** `manifest.json`, `runs.json`, `adjudication.json`, `summary.md`.

**Claim labels for adjudication:** `supported` (backed by cited evidence), `unsupported` (not contradicted but not supported), `false` (contradicted by evidence).

## Context

### Mental Model

This session's core framing: **"compute, don't assess."** The central tension of moving from a server-enforced to an agent-local convergence architecture is that every value previously returned by a function becomes a temptation for the agent to override with narrative judgment. The design's structural integrity depends on making the pure-function boundaries explicit and non-negotiable.

The convergence system has three distinct layers that must be preserved even in a simplified port:
1. **Validation** — structural integrity of extraction data (non-empty claims, chronology bounds)
2. **Computation** — deterministic delta/action from validated data (`effective_delta` from counters, `compute_action` from entries)
3. **Presentation** — formatting for downstream consumers (`ledger_summary`, `convergence_reason_code`)

Each layer has a different trust model. Validation enforces invariants the agent could skip under pressure. Computation ensures convergence decisions are grounded in evidence, not narrative. Presentation formats the results for synthesis and analytics.

### Execution Methodology

The session was a collaborative adversarial review with two full rounds:

**Round 1:** User presented analysis → I read source code and produced adversarial review (9 risks, A-I).

**Round 2:** User reviewed my review, found 6 corrections and 2 missing risks → I verified each against code and updated the artifact.

The two-round structure caught a significant misread (Risk A: `compute_quality` behavior) and a principle violation (Risk B: deriving `converged` from prose). Both would have propagated into the T-04 design if not caught at this stage.

The user drove all architectural decisions. I executed the source code verification, adversarial analysis, and document updates.

### Project State

- **Branch:** `main` at `6ea3e331`
- **Tests:** 460 passing (unchanged from session 11)
- **T-04 status:** Reconnaissance complete (session 11), adversarial review complete (this session), design not started
- **Risk analysis artifact:** `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` (corrected)
- **No code written** — this session was pure analysis

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1-10 | 2026-03-31 – 2026-04-01 | Runtime build chain | See session 11 handoff for full chain |
| 11 | 2026-04-01 | Repo hygiene + T-04 recon | `archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md` |
| **12** | **2026-04-01** | **T-04 convergence adversarial review** | **This handoff** |

## Learnings

### `effective_delta` is mechanically derived, not trusted from agent's delta field

**Mechanism:** `compute_effective_delta` at `ledger.py:101-110` uses claim status counters (new → ADVANCING, revised/conceded → SHIFTING, else → STATIC). The agent's self-reported `delta` field is checked for disagreement (`_delta_disagrees` at `ledger.py:113-127`) but only as a soft warning — the computed value is authoritative for convergence.

**Evidence:** `compute_action` at `control.py:43-48` calls `_is_plateau` on entries' `effective_delta`, not on the agent's delta. The pipeline at `pipeline.py:270-278` computes effective_delta during ledger validation and stores it in the `LedgerEntry`, overriding whatever the agent reported.

**Implication:** T-04's convergence module MUST compute effective_delta from claim counters. If it uses the agent's narrative delta assessment, convergence decisions become vulnerable to Claude's known tendency to find novelty in repetitive content (inflating "advancing" classifications, delaying plateau detection).

**Watch for:** Any T-04 design that references the agent's `delta` field for convergence purposes rather than the computed `effective_delta`.

### `compute_quality` marks ALL new claims as SUBSTANTIVE — including fallback claims

**Mechanism:** `compute_quality` at `ledger.py:89-98`: `new_claims > 0` → SUBSTANTIVE. A minimum-one-claim fallback (position text as a single "new" claim) is always SUBSTANTIVE, never SHALLOW. SHALLOW only occurs when ALL claims are `reinforced` with no other activity.

**Evidence:** The function's docstring ("Any non-reinforced activity -> substantive") and the condition (`counters.new_claims > 0`) are explicit. The test at `test_ledger.py:290` (per user reference) locks this behavior.

**Implication:** `compute_quality` cannot be used as a correction term for fallback-claim inflation. T-04 needs an explicit provenance marker (e.g., `claim_source=fallback`, `synthetic_minimum_claim=true`) so the computation layer can recognize and exclude fallback claims from `new_claims` counting for `effective_delta`.

**Watch for:** Any mitigation that relies on `quality == SHALLOW` to catch fallback claims — it won't work.

### `compute_action` returns prose reason, not a machine contract

**Mechanism:** `compute_action` at `control.py:58-142` returns `(ConversationAction, str)`. The `ConversationAction` is a StrEnum (CONTINUE_DIALOGUE, CLOSING_PROBE, CONCLUDE). The reason string is formatted prose: `f"Budget exhausted ({budget_remaining} turns remaining)"`, `"Plateau detected — last 2 turns STATIC, firing closing probe"`, etc.

**Evidence:** All 5 return paths in `compute_action` use f-strings or string literals for the reason. No structured code is returned alongside the action.

**Implication:** `converged` MUST be derived from a structured termination code, not by parsing the reason string. T-04 should extend `compute_action` (or its equivalent) to return a `TerminationCode` enum alongside the action and reason.

**Watch for:** Any derivation of `converged` that checks whether `action_reason` contains a specific substring — that's narrative assessment, not computation.

### Synthesis `mode` field is a multi-surface contract, not a local prompt tweak

**Mechanism:** Three surfaces validate or process the `mode` field: `event_schema.py:137` (`VALID_MODES` frozenset), `SKILL.md:435` (epilogue parser with fallback to `"server_assisted"`), `dialogue-synthesis-format.md:86` (documented values). An unsupported value is silently rewritten.

**Evidence:** `event_schema.py:137`: `VALID_MODES: frozenset[str] = frozenset({"server_assisted", "manual_legacy"})`. `SKILL.md:435`: "If the epilogue is missing, unparseable, missing the `mode` key, or has an invalid mode value, fall back to `"server_assisted"` and set `mode_source` to `"fallback"`."

**Implication:** Any new mode value for T-04 must be treated as a coordinated contract migration across analytics validation, skill parsing, and format documentation. Or the design must explicitly decide to reuse an existing value with documented rationale.

**Watch for:** T-04 design that introduces a new mode string without updating the validation and parsing surfaces.

### `unresolved_closed` is caller-supplied, not self-computed

**Mechanism:** `compute_counters` at `ledger.py:68-86` takes `unresolved_closed` as a keyword parameter (default 0) with the docstring: "unresolved_closed is passed in by the caller — D1 has no access to prior state for comparing unresolved lists."

**Evidence:** The pipeline computes this by diffing previous turn's unresolved list against the current turn's before calling `compute_counters`. If the caller doesn't supply it, it defaults to 0.

**Implication:** T-04's validation layer must include a cross-turn unresolved-list diff before computing counters. Without it, `unresolved_closed` is always 0, and closures are never counted as SUBSTANTIVE activity — potentially affecting quality computation in edge cases.

**Watch for:** `compute_counters(claims)` calls that don't pass `unresolved_closed` — they silently default to 0.

## Next Steps

### 1. Produce corrected risk register with exact invariants

**Dependencies:** This session's risk analysis artifact (`docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md`).

**What to read first:** The corrected risk analysis (already contains 11 risks with severities, mitigations, and the 4 pre-design invariants at the bottom of the summary section).

**Approach:** The user stated they will "turn it into a corrected risk register with revised severities and exact invariants, without drafting the design itself." This transforms the narrative analysis into a design-input artifact with formal invariant statements.

**Acceptance criteria:** Risk register with: (1) revised severity rankings reflecting all corrections, (2) exact invariant statements (not prose descriptions), (3) clear separation of "must resolve before design" vs "resolve during design" vs "verify during benchmark."

### 2. Draft T-04 benchmark-first design

**Dependencies:** Corrected risk register (step 1).

**What to read first:** Risk register invariants, then T-04 ticket (`docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`), then delivery spec (`docs/superpowers/specs/codex-collaboration/delivery.md`).

**Approach:** Design covering: minimal state schema, pure functions to port (validation, computation, presentation), agent loop structure, scouting integration, synthesis output format, and benchmark harness.

**Acceptance criteria:** Design reviewed and approved. Four pre-design invariants satisfied. Clear task breakdown.

**Potential obstacles:** The mode field contract migration may require coordinating changes across cross-model's analytics/skill/format surfaces, which are in a different package. Scope this before committing to a new mode value vs reusing an existing one.

### 3. Consider bulk ruff format enforcement (low priority, deferred from session 11)

**Dependencies:** None — standalone chore.

**Acceptance criteria:** Automated enforcement of `ruff format` on the codex-collaboration package.

## In Progress

Clean stopping point. Adversarial review complete with corrections applied. Risk analysis artifact written and corrected. No design work started, no code written.

The user confirmed next step: "I will turn it into a corrected risk register with revised severities and exact invariants. we will pick up in the next session."

## Open Questions

### Structured TerminationCode design

T-04 needs a structured termination code enum to replace prose-based `converged` derivation. The exact design (standalone enum? extension of `ConversationAction`? separate return value?) is deferred to the design phase. Key constraint: must be mechanical — `converged = termination_code in {PLATEAU_CONCLUDE, CLOSING_PROBE_CONCLUDE}` with no string parsing.

### Synthetic claim provenance marker

T-04 needs explicit provenance marking for minimum-one-claim fallback claims. Two candidate approaches: (1) add a `claim_source` field to the claim model (`"extraction"` vs `"fallback"`), (2) add a boolean `synthetic_minimum_claim` flag. The choice depends on whether other claim sources emerge in the design.

### Mode field resolution

Three options: (1) add `"agent_local"` to all three contract surfaces, (2) reuse `"server_assisted"` with documented rationale, (3) reuse `"manual_legacy"` with documented rationale. Option 1 is cleanest but requires cross-package changes. Options 2-3 are expedient but may confuse future readers.

### Evidence retention format

T-04 needs per-scout structured records for synthesis citations. The exact schema (how much metadata per record? path + line + snippet sufficient? or need target claim, disposition, entity metadata?) should be resolved during design. Cross-model's `scout_outcomes` include template-specific fields that don't apply.

## Risks

### Risk analysis may become stale if benchmark contract is revised

The risk analysis assumes the current benchmark contract at `dialogue-supersession-benchmark.md` (8 tasks, 4 pass-rule metrics). If the contract is revised before T-04 design begins, the severity rankings and mitigation priorities may shift.

**Mitigation:** Re-check the benchmark contract at the start of the design session.

### Two-round review found errors — a third round might find more

The adversarial review had two rounds and caught significant issues (compute_quality misread, prose parsing, mode severity). There may be additional errors in the corrected document that would surface with a third round.

**Mitigation:** The user plans to produce a corrected risk register with exact invariants, which is a form of third-round verification. Invariant statements are harder to get wrong than prose descriptions.

### Mode field contract migration may block T-04 timeline

If the design requires a new mode value, coordinating changes across `event_schema.py`, `SKILL.md`, and `dialogue-synthesis-format.md` involves the cross-model package. If cross-model is in active development or has its own release cycle, this coordination could delay T-04.

**Mitigation:** Consider option 2 or 3 (reuse existing mode value) as an expedient fallback if cross-package coordination is slow.

## References

| What | Where |
|------|-------|
| Risk analysis artifact (corrected) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| Convergence policy | `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` |
| Ledger validation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:143-238` |
| effective_delta computation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:101-110` |
| quality computation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:89-98` |
| compute_counters (unresolved_closed) | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:68-86` |
| Ledger summary | `packages/plugins/cross-model/context-injection/context_injection/control.py:167-223` |
| Conversation state model | `packages/plugins/cross-model/context-injection/context_injection/conversation.py:17-75` |
| Pipeline (process_turn) | `packages/plugins/cross-model/context-injection/context_injection/pipeline.py:74-352` |
| Codex-dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` |
| Analytics convergence mapper | `packages/plugins/cross-model/scripts/emit_analytics.py:337-368` |
| Analytics mode validation | `packages/plugins/cross-model/scripts/event_schema.py:137` |
| Dialogue skill mode parser | `packages/plugins/cross-model/skills/dialogue/SKILL.md:435` |
| codex-collaboration dialogue | `packages/plugins/codex-collaboration/server/dialogue.py` |
| codex-collaboration profiles | `packages/plugins/codex-collaboration/server/profiles.py:98-105` |
| codex-collaboration OutcomeRecord | `packages/plugins/codex-collaboration/server/models.py:160-200` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| T-04 ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
| Delivery spec | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| Session 11 handoff | `docs/handoffs/archive/2026-04-01_23-04_repo-hygiene-and-t04-dialogue-reconnaissance.md` |

## Gotchas

### compute_quality does NOT catch fallback claims

`compute_quality` at `ledger.py:89-98` marks any turn with `new_claims > 0` as SUBSTANTIVE. The minimum-one-claim fallback creates a `new` claim from position text. Therefore fallback claims are always SUBSTANTIVE, and `quality` cannot be used as a correction for delta inflation. Any mitigation targeting fallback claims must use explicit provenance marking, not the quality label.

### compute_action's reason string is unstable

The prose reason from `compute_action` (e.g., `"Budget exhausted (0 turns remaining)"`) is formatted with f-strings. It is not a stable contract — wording, punctuation, and included data can change. Never parse it for machine decisions. Use the `ConversationAction` enum for the action and a structured termination code for the reason.

### The mode field silently falls back to server_assisted

If the synthesis epilogue contains an unrecognized mode value, `SKILL.md:435` falls back to `"server_assisted"` and sets `mode_source = "fallback"`. This means a T-04 candidate run with a new mode string would be indistinguishable from a baseline run in analytics — the fallback silently overwrites the candidate's identity.

### unresolved_closed defaults to 0 if caller doesn't compute it

`compute_counters(claims)` without the `unresolved_closed` keyword argument produces 0 for closures. The function cannot detect closures itself — it only sees the current turn's claims. The caller must diff previous vs current unresolved lists. Easy to miss because the function signature looks self-contained.

## User Preferences

**Hypothesis-first analysis:** The user opened with three ranked hypotheses and confirmed the first as the right cut before requesting exploration. This is a consistent pattern (sessions 1-11): the user drives architectural direction and uses Claude for verification, adversarial review, and source code reading.

**Two-round adversarial review:** The user reviewed Claude's review, finding both factual errors (compute_quality misread) and principle violations (prose parsing contradicts "compute, don't assess"). The user treats Claude's analysis as input to refine, not as authoritative output. Corrections are specific, referenced to file:line, and accompanied by rationale.

**Thoroughness preference confirmed:** The user's corrections were precise and referenced test files (`test_ledger.py:290`), contract surfaces (`event_schema.py:137`), and cross-references between documents. The user expects the same precision in return.

**User will produce the corrected risk register:** The user stated: "If you want, I can turn this into a corrected risk register with revised severities and exact invariants, without drafting the design itself." The user then confirmed: "I will turn it into a corrected risk register with revised severities and exact invariants. we will pick up in the next session." The user is leading the design process and using Claude as an analytical tool, not as the design author.

**Pre-design invariant framing:** The user distilled the session's findings into four clean invariants. This pattern — synthesizing a complex analysis into a small number of verifiable statements — is characteristic of the user's approach. Future sessions should expect and support this distillation step.
