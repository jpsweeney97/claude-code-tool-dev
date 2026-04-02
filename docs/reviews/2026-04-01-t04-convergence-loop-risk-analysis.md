# T-04 Convergence Loop Risk Analysis

Date: 2026-04-01
Revised: 2026-04-01 (corrections from user review — see Corrections section at end)
Scope: Benchmark-first design slice for T-20260330-04 (dialogue parity and scouting retirement)
Context: Session 12 of the codex-collaboration build chain
Companion artifact: [2026-04-01-t04-convergence-loop-risk-register.md](2026-04-01-t04-convergence-loop-risk-register.md)

## Background

This review examines the structural integrity of the proposed benchmark-first local ledger subsystem for T-04. The subsystem replaces cross-model's server-side convergence (context-injection `process_turn` / `execute_scout`) with an agent-local computation layer while preserving convergence correctness for the benchmark.

### Revised 7-Point Benchmark-First Slice Under Review

1. Agent-local turn extraction
2. Local validation
3. Local counter/delta/action computation
4. Claude-side scouting with `Glob` / `Grep` / `Read`
5. Follow-up composition using local `ledger_summary`
6. Synthesis + explicit `converged_within_budget` output
7. No phase support in first cut

### State Model Under Review

**Primary state:**
- `entries` (validated ledger entries)
- `closing_probe_fired`
- `turn_budget`
- `current_turn`
- `focus/topic`
- `evidence_count` and `scope_breach_count` (orchestration metrics, not convergence inputs)

**Derived state:**
- cumulative counters
- `effective_delta_sequence`
- `ledger_summary`
- `convergence_reason_code`
- `termination_reason`

---

## Layer 1-3: The Local Ledger Subsystem

### Risk A: Claim status inflation via the minimum-one-claim fallback

> **CORRECTION (2026-04-01):** The original analysis claimed `compute_quality` would catch single-fallback-claim turns as SHALLOW. This was wrong. `compute_quality` (`ledger.py:89-98`) marks any turn with `new_claims > 0` as SUBSTANTIVE. A minimum-claim fallback with status `new` is always SUBSTANTIVE. The proposed "quality-based downgrade" would never fire in the scenario it targets. The mitigation has been rewritten.

**Mechanism.** When the agent extracts zero real claims from a Codex response, codex-dialogue.md Step 1 says to create a single claim using the position text with status `new`. This flows into `compute_counters` -> `new_claims = 1` -> `compute_effective_delta` -> `ADVANCING`. The convergence detector sees an advancing conversation even though nothing substantive happened.

Cross-model has the same fallback and the same delta inflation. `compute_quality` does NOT correct this -- it marks the fallback claim as SUBSTANTIVE because `new_claims > 0`. The `_delta_disagrees` warning fires only when the agent's self-reported delta contradicts the computed one, which doesn't help when the computation itself is inflated by a synthetic claim. In cross-model, the practical protection is the server's independent computation: even if the delta is inflated, the server at least ensures the inflation is consistent (same formula, same inputs). In T-04, the inflation risk is identical but entirely agent-internal.

**Benchmark impact.** A single false-ADVANCING turn delays plateau detection by one turn (the plateau requires 2 consecutive STATIC). Two false-ADVANCING turns in a row make plateau detection impossible for that window. On a 6-turn budget, losing 2 turns to false advancement means the dialogue can't converge naturally, falling back to budget exhaustion -> `converged: false`.

**Likelihood.** Medium. The fallback triggers when Codex restates its position without new substance -- exactly the scenario where convergence should be detected. Benchmark tasks B1, B5, and B6 (evaluative, 6-turn budget) are the most vulnerable because evaluative dialogues plateau earlier.

**Mitigation.** Fallback claims need explicit provenance marking. When the minimum-one-claim invariant fires (zero real claims extracted, position text used as claim), tag the claim with a `source` field (e.g., `claim_source=fallback` or `synthetic_minimum_claim=true`). The computation layer recognizes this tag and excludes the claim from `new_claims` counting for `effective_delta`. The claim still satisfies the structural invariant (non-empty claims list), but cannot inflate the delta. This is a NEW rule -- cross-model does not have this protection either -- but it's necessary because T-04 lacks the external correction signals that make cross-model's inflation tolerable in practice.

---

### Risk B: The `converged` boolean must be derived, not assessed

> **CORRECTION (2026-04-01):** The original mitigation derived `converged` by parsing `action_reason` for substring "Budget exhausted". This violates the "compute, don't assess" principle -- `action_reason` is a human-readable prose string (`control.py:104`), not a stable machine contract. The mitigation has been rewritten to require a structured termination code.

**Mechanism.** Slice item 6 says "synthesis + explicit `converged_within_budget` output." The benchmark contract at line 159 says this is a "binary result recorded by the dialogue orchestrator." The question: who sets it, and from what?

In cross-model, the convergence outcome is derivable from `compute_action`'s return value, but the return type is `(ConversationAction, str)` where the second element is prose. This works in cross-model because the analytics emitter (`emit_analytics.py:337-368`) recomputes the convergence mapping independently from raw state (`converged`, `turn_count`, `turn_budget`, `scope_breach`), never from the reason string.

The risk: if the agent sets `converged: true` based on its narrative assessment ("this conversation reached a good stopping point") OR by parsing the reason string, the benchmark result is inflated. Claude has a known tendency toward premature closure -- it will judge conversations "done" sooner than a mechanical detector would.

**Benchmark impact.** Direct. `converged_within_budget` is a pass-rule metric. Inflating it gives the candidate an artificial advantage that the adjudicator cannot distinguish from genuine convergence.

**Mitigation.** T-04's local `compute_action` equivalent must return a structured `TerminationCode` enum (not just prose reason), and `converged` must be a mechanical projection:

```python
class TerminationCode(StrEnum):
    PLATEAU_CONCLUDE = "plateau_conclude"      # converged=true
    CLOSING_PROBE_CONCLUDE = "closing_probe_conclude"  # converged=true
    BUDGET_EXHAUSTED = "budget_exhausted"       # converged=false
    SCOPE_BREACH = "scope_breach"               # converged=false
    ERROR = "error"                             # converged=false

converged = termination_code in {PLATEAU_CONCLUDE, CLOSING_PROBE_CONCLUDE}
```

No narrative override. No string parsing. The agent reports what the enum says.

---

### Risk C: Referential status misclassification compounds silently

**Mechanism.** When the agent classifies a claim as `reinforced` instead of `new` (or vice versa), the effect on `effective_delta` is binary:

| Misclassification | Effect on `compute_effective_delta` |
|--------------------|-------------------------------------|
| `new` -> `reinforced` | Loses the `new_claims += 1`. If no other new/revised/conceded claims, delta flips from ADVANCING to STATIC |
| `reinforced` -> `new` | Gains a `new_claims += 1`. Delta inflates to ADVANCING when it should be STATIC |

In cross-model, `validate_ledger_entry` checks for referential consistency: a `reinforced` claim should have a prior claim with matching text (`_referential_warnings` at `ledger.py:241-270`). This is only a soft warning -- the server doesn't reject -- but it provides the agent with a correction signal.

In T-04, the agent produces AND consumes the claim list. There's no external check on referential consistency. And the errors compound: if turn 3's claim is misclassified as `new` (should be `reinforced`), then turn 4's reference to the same claim text may also be misclassified because the agent's "prior claims" list is polluted.

**Benchmark impact.** Medium-indirect. This doesn't directly affect a pass-rule metric, but it distorts `effective_delta` accuracy, which distorts convergence timing, which affects `converged_within_budget`.

**Likelihood.** Low-medium. Claude is reasonably good at tracking claim continuity across turns. The risk increases with conversation length -- 6-turn dialogues (most benchmark tasks) are short enough that recall is likely reliable. B8 (8 turns) is the most vulnerable.

**Mitigation.** Include a deterministic referential check in the validation layer: before computing counters, scan prior-turn claims for normalized exact-text match with any `reinforced`/`revised`/`conceded` claim in the current turn (case-insensitive, whitespace-normalized). If no match found, reclassify as `new`. Alternatively, assign explicit claim IDs across turns so referential status can be tracked by ID rather than text matching. Do NOT use "semantic overlap" or LLM judgment — that reintroduces the assessment boundary the computation layer is meant to exclude.

> **CORRECTION (2026-04-01):** Original mitigation proposed "substring or semantic overlap." This violates the deterministic computation boundary. Replaced with normalized exact matching or explicit claim IDs per user review.

---

## Layer 4: Claude-Side Scouting

### Risk D: Scouting timing relative to the convergence loop

**Mechanism.** In cross-model, scouting is Step 4 of the 7-step per-turn loop: it happens AFTER extraction (Step 1), AFTER `process_turn` (Steps 2-3), and BEFORE follow-up composition (Step 6). The server tells the agent what to scout (template candidates from entity resolution), and the agent executes one scout per turn with a tracked evidence budget.

In T-04, there's no server directing scouting. The agent decides what to look up and when. Three possible timings:

| Timing | Pros | Cons |
|--------|------|------|
| **Pre-conversation** (gatherers only) | Simple; no mid-dialogue disruption | No reactive scouting; can't verify claims that emerge during conversation |
| **Between extraction and follow-up** (cross-model's position) | Follow-ups grounded in fresh evidence | Agent must decide what to scout without server guidance |
| **Interleaved freely** (agent decides) | Maximum flexibility | Evidence count unpredictable; harder to produce consistent analytics |

**Benchmark impact.** The benchmark measures `supported_claim_rate` in the final synthesis, not in intermediate turns. So scouting timing doesn't directly affect scoring -- what matters is whether evidence was gathered and used. But the follow-up priority model depends on scout evidence being available when composing the next question. If scouting happens too late, the agent asks less-grounded follow-ups, Codex gives less-grounded responses, and the synthesis has weaker citations.

**Recommendation.** Lock scouting to the "between extraction and follow-up" position to match cross-model's architecture. The agent should execute at most one scouting round per turn (1-3 tool calls: Glob for discovery, Grep for specifics, Read for context). Track evidence count for analytics. This keeps the loop predictable and the evidence budget bounded.

---

### Risk E: `unknown_claim_paths` is unnecessary machinery for Claude-side scouting

**Mechanism.** The state list includes `unknown_claim_paths` conditionally. In cross-model, this exists because scouting is INDIRECT: the agent can't look at code itself -- it has to select a scout template from the server's `template_candidates`, and it needs to know which paths have unverified claims so it can prioritize the right templates.

In T-04, the agent HAS `Glob`, `Grep`, and `Read`. When it encounters a claim with uncertain provenance, it can just verify it directly. No path tracking needed. No template selection. No entity-to-path resolution.

The entire `unknown_claim_paths` mechanism (extraction from `[SRC:unknown]` lines, tiered matching against entity canonicals, selection tracking, path clearing after successful scout) is ~30 lines of complex agent instructions that exist solely because cross-model's scouting is tool-mediated. With direct tool access, this collapses to: "when you encounter an uncertain claim, use Grep/Read to check it."

**Recommendation.** Drop the `unknown_claim_paths` **mechanism** (path extraction from `[SRC:unknown]` lines, tiered entity matching, selection tracking, per-path clearing) from T-04's state. But preserve the **function**: tracking provenance debt. Replace with a simpler uncited-claims backlog — a set of claim texts that lack cited evidence, consulted during follow-up prioritization (Step 6 priority slot 3). When the agent verifies a claim via Glob/Grep/Read, remove it from the backlog. This retains the follow-up prioritization signal without the path-level template machinery.

> **CORRECTION (2026-04-01):** Original recommendation said "drop `unknown_claim_paths`" without distinguishing mechanism from function. The provenance debt tracking function must survive — only the helper-specific path machinery should go.

**Key insight:** The cross-model architecture's most complex machinery exists because it straddles a process boundary. Entity extraction, template matching, HMAC scout tokens, `unknown_claim_paths` -- all of this is plumbing to make a separate process (the context-injection server) do what the agent can't do itself (read files). When the agent has direct file access, this entire indirection layer evaporates. The lesson: complexity in the source architecture doesn't mean complexity in the port. Most of T-04's simplification comes from collapsing the tool indirection, not from cutting features.

---

## Layer 5: Follow-Up Composition

### Risk F: Ledger summary staleness under compression

**Mechanism.** `generate_ledger_summary` in `control.py:167-223` produces ~300-400 tokens for an 8-turn conversation. In cross-model, this is recomputed each turn by the server and returned to the agent. In T-04, the agent computes it locally and holds it in working memory.

The risk is not computation -- the function is trivial to port. The risk is context window behavior. In a long dialogue (B8, 8 turns), the agent's context accumulates: initial briefing + 8 Codex responses + 8 extractions + 8 follow-ups + scouting results. If context compression fires mid-dialogue, earlier turns' extraction details may be compressed, but the ledger summary (which the agent needs to read) may also be compressed.

In cross-model, this isn't a problem because the server returns a fresh summary each turn -- the agent doesn't need to remember prior summaries. In T-04, the agent must either recompute the summary each turn from its stored entries (which are also in the context) or maintain a running summary that survives compression.

**Benchmark impact.** Low for most tasks (6-turn budget fits comfortably). Medium for B8 (8 turns, widest evidence anchor set -- 5 path groups). B8 is specifically the supersession analysis task that covers the most code surface, so it generates the longest Codex responses.

**Mitigation.** Recomputing `ledger_summary` each turn only helps if the authoritative ledger entries survive compression. The real defense is a compact canonical ledger block (structured, not prose) that gets re-emitted every turn as part of the agent's working state. This block must contain the per-turn extraction data (position, effective_delta, tags, claim statuses, unresolved items) in a compression-resistant format. Without this, compression can erase both the raw turn detail and any summary derived from it.

> **CORRECTION (2026-04-01):** Original mitigation focused on recomputation. The deeper issue is entry survival — recomputing from compressed-away entries produces nothing. Updated to require a re-emitted canonical ledger block.

---

## Layer 6: Synthesis + Benchmark Output

### Risk G: Scope breach termination needs explicit handling outside the convergence state machine

**Mechanism.** From `codex-dialogue.md:380-390`, scope breach is a scouting-layer concern, not a convergence concern:

> If `scope_breach_count` reaches 3 -> terminate immediately with `termination_reason: scope_breach`

But scope breach detection happens during scouting (Step 4), which is BETWEEN convergence computation and follow-up. The convergence module (`compute_action`) doesn't know about scope breaches. The termination is an agent-level override that bypasses the convergence loop.

In the revised slice, `scope_breach_count` is correctly placed as an "orchestration metric, not convergence input." But the risk is that the agent instructions don't make the termination pathway explicit. If the agent treats scope breach as just a counter (increment and continue), it won't terminate at 3 breaches, and the synthesis won't reflect the breach.

For the benchmark: scope breach is unlikely (all 8 tasks reference codex-collaboration-internal paths, and the scope envelope would be set to the repo root). But if it happens during scouting (e.g., a Grep result references a file outside `allowed_roots`), the response must be correct.

**Mitigation.** Add scope breach as an explicit loop-exit condition in the agent instructions, separate from `compute_action`. The check sequence after each scout is: (1) increment `scope_breach_count` if scout target was outside allowed roots, (2) if `scope_breach_count >= 3`, exit loop immediately, (3) set `converged = false`, `convergence_reason_code = "scope_breach"`, `termination_reason = "scope_breach"`.

---

### Risk H: The synthesis `mode` field is a cross-contract migration, not a naming choice

> **CORRECTION (2026-04-01):** Original assessment rated this Low severity as a "naming choice." It is a multi-surface contract migration. Upgraded to Medium-High.

**Mechanism.** The synthesis epilogue requires a `mode` field (`dialogue-synthesis-format.md:86`):

| Value | Meaning |
|-------|---------|
| `server_assisted` | Full process_turn + execute_scout loop |
| `manual_legacy` | No-server fallback |

T-04 is neither. It has scouting (unlike `manual_legacy`) but no server (unlike `server_assisted`). A new mode value is not just a naming choice — it must be accepted across multiple contract surfaces:

| Surface | File | Behavior on invalid mode |
|---------|------|--------------------------|
| Analytics validation | `event_schema.py:137` | `VALID_MODES = frozenset({"server_assisted", "manual_legacy"})` — rejects unknown values |
| Dialogue skill epilogue parser | `SKILL.md:435` | Falls back to `"server_assisted"` for invalid/missing mode, sets `mode_source = "fallback"` |
| Synthesis format spec | `dialogue-synthesis-format.md:86` | Documents only two values — undefined behavior for anything else |

If T-04 emits a new mode value (e.g., `agent_local`), the analytics emitter will either reject the event or silently reclassify it as `server_assisted` via fallback. Both distort the benchmark artifacts.

**Benchmark impact.** Medium-High. If `mode` is silently rewritten to `server_assisted` by the fallback logic, the adjudicator cannot distinguish baseline from candidate runs in `runs.json`. If the analytics emitter rejects the event, the run may be recorded as invalid.

**Mitigation.** Treat this as a coordinated contract migration:
1. Add the new mode value to `event_schema.py:VALID_MODES`
2. Update `SKILL.md` epilogue parser to accept it (or document that T-04 uses its own skill, not cross-model's)
3. Update `dialogue-synthesis-format.md` to document the new value
4. Alternatively, decide that T-04's benchmark runs use `server_assisted` with documented rationale (e.g., "the mode describes the scouting capability, and T-04 has scouting") — but this must be an explicit decision, not an accident of fallback logic.

---

## Cross-Cutting: Build Sequence Risks

### Risk I: The critical path has a testing gap between layers 1-3 and layers 4-6

The dependency chain is:

```
Extraction (1) -> Validation (2) -> Computation (3) -> Follow-up (5) -> Synthesis (6)
                                                     /
                                     Scouting (4) --/
```

Layers 1-3 are pure functions -- testable with unit tests, deterministic, portable from cross-model's existing test suite. Layers 4-6 are behavioral -- testable only by running actual dialogues, dependent on Claude's judgment.

The risk: layers 1-3 can be verified before a single dialogue runs. But the first time you'll know if 4-6 work is during the benchmark itself. If there's a bug in how the agent USES the ledger (e.g., it reads `effective_delta` but doesn't use it for plateau detection, or it computes `ledger_summary` but doesn't incorporate it into follow-ups), the unit tests won't catch it.

**Mitigation.** Before the benchmark, run one dry-run dialogue (e.g., B1 as a smoke test) with manual inspection of:
- Each turn's extraction -> does `effective_delta` match what a human would compute?
- Each ledger summary -> is it compact, accurate, and present in the follow-up reasoning?
- The `converged` derivation -> does it match `compute_action`'s output?
- The synthesis epilogue -> are all required fields populated?

This is not the full benchmark -- it's a single-task integration test that validates the layer integration.

---

## Missing Risks (added in revision)

### Risk J: Evidence retention requires structured provenance, not just counts

> **Added 2026-04-01** from user review. Originally missed.

**Mechanism.** Cross-model stores structured scout outcomes in `turn_history` per turn: `{validated_entry, cumulative, scout_outcomes}` (`codex-dialogue.md:308`). Each scout outcome includes the target claim, file path, line range, snippet, and disposition. The synthesis format expects an "evidence trajectory" (`dialogue-synthesis-format.md:123`): which turns had evidence, what entities, what impacts.

If T-04 only tracks `evidence_count` (a scalar) and not structured provenance records, the synthesis cannot produce evidence-backed citations. The agent would be writing "supported by repo evidence" without being able to cite the specific path:line it found.

**Benchmark impact.** Direct on `supported_claim_rate`. A claim labeled `supported` in the synthesis must be "backed by cited repo evidence and not contradicted by the repo" (benchmark contract line 139). Without structured evidence records, the agent can't produce precise citations, and the adjudicator may downgrade claims to `unsupported`.

**Likelihood.** High if the design only specifies `evidence_count`. The scouting layer (Glob/Grep/Read) naturally produces structured output (file paths, line numbers, content). The risk is that the design doesn't specify retaining this output in a form the synthesis can reference.

**Mitigation.** Add structured evidence records to T-04's state: per-scout `{turn, target_claim, path, line_range, snippet, disposition}`. These are the synthesis's citation source. Simpler than cross-model's `scout_outcomes` (no HMAC tokens, no template IDs, no entity resolution metadata) but structured enough to produce provenance-backed citations.

---

### Risk K: `unresolved_closed` derivation requires cross-turn diff

> **Added 2026-04-01** from user review. Originally missed.

**Mechanism.** `compute_counters` (`ledger.py:68-86`) takes `unresolved_closed` as a caller-supplied parameter with the comment: "unresolved_closed is passed in by the caller -- D1 has no access to prior state for comparing unresolved lists." The pipeline computes this by diffing the previous turn's unresolved items against the current turn's.

If T-04 ports `compute_counters` without implementing the cross-turn diff, `unresolved_closed` will always be 0. Effects:
1. `compute_quality` will not count closures as SUBSTANTIVE activity (only matters when closures are the ONLY activity in a turn — rare but possible)
2. `CumulativeState.unresolved_closed` will always be 0
3. The ledger summary's "State: ... unresolved open" line may be inaccurate

**Benchmark impact.** Low-indirect. `unresolved_closed` is not a pass-rule metric. But persistent zero values degrade ledger trustworthiness and could cause the quality computation to miss SUBSTANTIVE turns where the only activity was resolving open questions.

**Likelihood.** High if not explicitly addressed — `compute_counters(claims)` looks self-contained, and the `unresolved_closed` parameter defaults to 0. Easy to miss.

**Mitigation.** Include unresolved-list diffing in T-04's validation layer. Before computing counters for turn N, diff `entries[N-1].unresolved` against the current turn's `unresolved` list. Count items present in the prior list but absent in the current list as `unresolved_closed`. Pass to `compute_counters`.

---

## Summary: Risk-Ordered by Benchmark Severity (Revised)

| Risk | Layer | Benchmark Metric | Severity | Mitigation Complexity |
|------|-------|------------------|----------|----------------------|
| **B: `converged` must be derived from structured code** | 6 | `converged_within_budget` | **High** | Low -- TerminationCode enum |
| **A: Fallback claims need explicit provenance marking** | 1-3 | `converged_within_budget` | **Medium-High** | Low -- synthetic claim tag |
| **J: Evidence retention requires structured provenance** | 4-6 | `supported_claim_rate` | **Medium-High** | Low -- per-scout record |
| **H: Mode field is a cross-contract migration** | 6 | Artifact validity | **Medium-High** | Medium -- multi-surface update |
| **D: Scouting timing** | 4 | `supported_claim_rate` | **Medium** | Low -- lock position in loop |
| **C: Referential misclassification** | 1-2 | `converged_within_budget` (indirect) | **Medium** | Medium -- normalized exact match |
| **I: Testing gap** | Cross-cutting | All metrics | **Medium** | Medium -- one dry-run dialogue |
| **F: Ledger entries must survive compression** | 5 | `supported_claim_rate` (indirect) | **Low-Medium** | Low -- canonical ledger block |
| **K: `unresolved_closed` requires cross-turn diff** | 1-3 | Ledger trustworthiness | **Low** | Low -- list diff before counters |
| **G: Scope breach termination** | 6 | Safety | **Low** (unlikely in benchmark) | Low -- explicit loop exit |
| **E: Drop path machinery, keep provenance debt** | 4 | None (simplification) | **N/A** | Negative -- removes complexity |

**Central principle:** The highest-severity risks (A, B, J) are about derivation discipline -- ensuring that key outputs are computed mechanically from structured data, not assessed narratively by the agent. This is the central tension of moving from a server-enforced to an agent-local architecture: every value that was previously a function return becomes a temptation for the agent to override with its judgment. The design's structural integrity depends on making the pure-function boundaries explicit and non-negotiable in the agent instructions. The phrase to anchor on: **"compute, don't assess."**

### Pre-Design Invariants

These must be resolved before the T-04 design is drafted:

1. **`converged` and termination fields are computed from structured state, never prose.** T-04's `compute_action` equivalent returns a `TerminationCode` enum. `converged` is a mechanical projection of that enum.
2. **Synthetic minimum-claim fallbacks are explicitly marked and cannot inflate `effective_delta`.** Fallback claims carry a `claim_source=fallback` tag. The computation layer excludes them from `new_claims` counting.
3. **Candidate evidence is retained as structured provenance, not just counts.** Per-scout `{turn, target_claim, path, line_range, snippet, disposition}` records feed the synthesis's citation surface.
4. **Any new mode value is treated as a cross-contract migration.** Schema, parser, and format documentation must be updated together, or an explicit decision made to reuse an existing value.

---

## References

| What | Where |
|------|-------|
| Convergence policy (compute_action) | `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` |
| Ledger validation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:143-238` |
| effective_delta computation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:101-110` |
| quality computation | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:89-98` |
| Ledger summary generation | `packages/plugins/cross-model/context-injection/context_injection/control.py:167-223` |
| Server conversation state | `packages/plugins/cross-model/context-injection/context_injection/conversation.py:17-59` |
| Pipeline (full process_turn flow) | `packages/plugins/cross-model/context-injection/context_injection/pipeline.py:74-352` |
| Codex-dialogue agent (7-step loop) | `packages/plugins/cross-model/agents/codex-dialogue.md:222-453` |
| Manual legacy fallback | `packages/plugins/cross-model/agents/codex-dialogue.md:204-220` |
| Scope breach handling | `packages/plugins/cross-model/agents/codex-dialogue.md:378-390` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` |
| Analytics convergence mapper | `packages/plugins/cross-model/scripts/emit_analytics.py:337-368` |
| codex-collaboration dialogue.py | `packages/plugins/codex-collaboration/server/dialogue.py` |
| codex-collaboration profiles.py | `packages/plugins/codex-collaboration/server/profiles.py:98-105` |
| Analytics mode validation | `packages/plugins/cross-model/scripts/event_schema.py:137` |
| Dialogue skill mode parser | `packages/plugins/cross-model/skills/dialogue/SKILL.md:435` |
| Synthesis evidence trajectory | `packages/plugins/cross-model/references/dialogue-synthesis-format.md:123` |
| Scout outcomes in turn_history | `packages/plugins/cross-model/agents/codex-dialogue.md:308` |
| compute_counters unresolved_closed | `packages/plugins/cross-model/context-injection/context_injection/ledger.py:68-86` |

---

## Corrections Log

Corrections applied 2026-04-01 from user review of the original analysis.

| Finding | Original Claim | Correction | Affected Section |
|---------|---------------|------------|-----------------|
| Risk A: `compute_quality` misread | Claimed `quality == SHALLOW` catches fallback claims | `new_claims > 0` → SUBSTANTIVE; fallback claims are never SHALLOW | Risk A mechanism + mitigation |
| Risk B: prose parsing | Derived `converged` by checking `action_reason` for "Budget exhausted" | `action_reason` is prose, not a machine contract; need structured TerminationCode enum | Risk B mitigation |
| Risk C: semantic overlap | Proposed "semantic overlap" for referential check | Reintroduces LLM judgment into computation boundary; use normalized exact match or claim IDs | Risk C mitigation |
| Risk E: function vs mechanism | Said "drop `unknown_claim_paths`" without qualification | Drop the path-tracking mechanism; keep the provenance debt tracking function | Risk E recommendation |
| Risk F: entry survival | Focused on recomputing summary | Recomputing from compressed-away entries produces nothing; entries themselves must survive | Risk F mitigation |
| Risk H: severity underrated | Rated Low as "naming choice" | Multi-surface contract migration: `event_schema.py`, `SKILL.md`, synthesis format | Risk H severity + mitigation |
| Missing: evidence retention | Only tracked `evidence_count` | Synthesis needs structured provenance records, not just counts | New Risk J |
| Missing: `unresolved_closed` | Not mentioned | `compute_counters` takes `unresolved_closed` from caller; requires cross-turn diff | New Risk K |
