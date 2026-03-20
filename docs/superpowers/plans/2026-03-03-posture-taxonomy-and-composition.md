# Posture Taxonomy Redesign and Phase Composition

**Date:** 2026-03-03
**Status:** Codex-Reviewed — Ready for Spec Amendments
**Purpose:** Extend the 4-posture taxonomy to 5 postures (adding `comparative`), broaden evaluative follow-up patterns, add two new profiles, and introduce phase composition — multi-posture dialogues with per-phase transitions requiring minimal server changes.
**Depends on:** codex-dialogue agent v2 (ledger + scouting loop, committed), context injection MCP server (969 tests, deployed)
**Codex review:** 6-turn evaluative dialogue. Thread `019cb50e-107e-7cd0-bc25-19dc50c451f8`. Key outcome: rejected three-way evaluative split in favor of 2+1 framing.

---

## 1. Problem Statement

The current posture taxonomy has four values: adversarial, collaborative, exploratory, evaluative. Three of six consultation profiles map to evaluative, but they serve genuinely different conversational purposes:

| Profile | Uses evaluative for | Actually needs |
|---------|-------------------|----------------|
| `deep-review` | Architecture audit — structural implications, scalability | Structural analysis, downstream constraints |
| `code-review` | Correctness verification — bugs, edge cases | Evidence-based verification against specification |
| `planning` | Decision/trade-off assessment — comparing options | Structured comparison across criteria |

The evaluative overload is a **2+1 problem**: deep-review and code-review are genuinely similar verification tasks that both belong under evaluative (with broadened patterns), while planning is a genuinely different comparison task that needs its own posture.

Additionally, the collaborative posture only appears in `quick-check` (1 turn), leaving no profile for sustained multi-turn brainstorming. And no profile exists for the common "choose between N options" workflow.

Finally, real consultation workflows have natural phase transitions (explore → evaluate → decide) that a single-posture-per-dialogue model cannot express.

### What This Design Does

- Extends the 4-posture enum to 5 postures (adding `comparative`)
- Broadens evaluative follow-up patterns to cover both structural analysis and correctness verification
- Adds two new profiles: `decision-making` and `collaborative-ideation`
- Migrates the `planning` profile to the new `comparative` posture
- Introduces phase composition: profiles can define ordered posture phases with target turns
- Defines a three-release sequence to isolate risk: taxonomy → server convergence → composition

### What This Design Does Not Do

- Split evaluative into analytical/critical (Codex review determined this is a 2+1 problem, not 3-way)
- Implement posture-aware template ranking (posture-agnostic by design — see Section 5)
- Add per-phase sandbox changes (sandbox is immutable per conversation)
- Change sandbox or approval_policy for any profile (all remain read-only/never)

---

## 2. Posture Taxonomy: 4 → 5

### Unchanged

| Posture | Intent | Follow-up Patterns |
|---------|--------|-------------------|
| **adversarial** | Challenge, stress-test, probe failure modes | "I disagree because…", "What about failure mode X?", "This assumes Y — what if Y is false?" |
| **collaborative** | Build together, ideate, combine | "Building on that, what if…", "How would X combine with Y?", "What's the strongest version of this?" |
| **exploratory** | Map territory, don't commit, chart options | "What other approaches exist?", "What am I not considering?", "How does this relate to X?" |

### Broadened (existing posture, expanded patterns)

| Posture | Intent | Follow-up Patterns |
|---------|--------|-------------------|
| **evaluative** | Verification, structural analysis, correctness, quality assessment | "Is that claim accurate? Show evidence.", "What are the structural implications of X?", "What edge cases exist?", "What constraints does this create downstream?", "What happens when Y scales by 10x?", "Does this match the documented behavior?" |

The evaluative patterns are broadened from the current set ("Is that claim accurate?", "What about coverage of X?", "Where are the gaps?") to cover both architectural probing and correctness verification. This addresses the pre-existing pattern quality problem where evaluative skewed toward verification and underserved architecture review.

### New

| Posture | Intent | Follow-up Patterns |
|---------|--------|-------------------|
| **comparative** | Structured option comparison, trade-off analysis, ranking | "How does A compare to B on criterion X?", "What trade-offs haven't been surfaced?", "Which option optimizes for Z?", "What's the decision matrix across these criteria?" |

### Why 5 postures, not 6

The original design proposed a three-way evaluative split (analytical/critical/comparative). Codex review (6-turn evaluative dialogue) identified the **2+1 framing**: deep-review and code-review are both verification tasks that belong under evaluative with broadened patterns, while planning is genuinely different (structured comparison). The analytical/critical distinction — while conceptually clean — doesn't map to a behavioral boundary the agent can reliably exploit.

Evidence: the codex-dialogue agent's posture table is the sole consumer of posture. It selects one pattern set per posture. The difference between "What are the structural implications?" (analytical) and "Show evidence for that claim" (critical) is a within-pattern variation, not a between-posture boundary.

### Deferred postures

| Posture | Why deferred |
|---------|-------------|
| **Socratic** | Overlaps with exploratory. Revisit if exploratory proves too broad. |
| **Dialectic/synthesizing** | Convergence detection already drives toward synthesis. Revisit after phase composition. |
| **Mentoring/teaching** | Low priority — current use cases are decision-oriented. |

---

## 3. Profile Changes

### Migrated profiles

| Profile | Old Posture | New Posture | Other Changes |
|---------|-------------|-------------|---------------|
| `planning` | evaluative | **comparative** | None |

`deep-review` and `code-review` remain `evaluative` — the broadened pattern set covers both.

### New profiles

#### decision-making

```yaml
decision-making:
  description: >
    Choose between N options with explicit criteria. Codex evaluates trade-offs,
    surfaces unstated constraints, and ranks alternatives. Provide options and
    evaluation criteria in the briefing material.
  sandbox: read-only
  approval_policy: never
  reasoning_effort: xhigh
  posture: comparative
  turn_budget: 6
```

**Turn budget rationale:** Decision-making benefits from iteration (Codex proposes ranking → Claude challenges → they refine), but converges faster than open-ended review because the option space is bounded. 6 turns balances depth with convergence.

#### collaborative-ideation

```yaml
collaborative-ideation:
  description: >
    Sustained brainstorming and idea generation over multiple turns. Build on
    each other's proposals, combine approaches, explore "what if" scenarios.
    Use when generating options, not evaluating them.
  sandbox: read-only
  approval_policy: never
  reasoning_effort: high
  posture: collaborative
  turn_budget: 6
```

**Reasoning effort rationale:** `high` rather than `xhigh`. Ideation benefits from breadth over exhaustive depth. `xhigh` encourages thorough analysis that can slow creative momentum.

### Unchanged profiles

| Profile | Posture | Turns | Reasoning |
|---------|---------|-------|-----------|
| `quick-check` | collaborative | 1 | medium |
| `deep-review` | evaluative | 8 | xhigh |
| `code-review` | evaluative | 4 | high |
| `adversarial-challenge` | adversarial | 6 | xhigh |
| `exploratory` | exploratory | 6 | high |

### Complete profile table (8 profiles)

| Profile | Posture | Turns | Reasoning | Primary Use Case |
|---------|---------|-------|-----------|-----------------|
| `quick-check` | collaborative | 1 | medium | Fast sanity check |
| `collaborative-ideation` | collaborative | 6 | high | Sustained brainstorming |
| `exploratory` | exploratory | 6 | high | Solution space mapping |
| `deep-review` | evaluative | 8 | xhigh | Architecture/quality audit |
| `code-review` | evaluative | 4 | high | Correctness verification |
| `adversarial-challenge` | adversarial | 6 | xhigh | Stress-test decisions |
| `planning` | comparative | 8 | xhigh | Plan review, design trade-offs |
| `decision-making` | comparative | 6 | xhigh | Choose between N options |

---

## 4. Phase Composition

### Motivation

Many real workflows have natural posture transitions:

| Workflow | Natural Phases |
|----------|---------------|
| Debugging | exploratory → evaluative → collaborative |
| Architecture design | exploratory → comparative → adversarial |
| Feature design | collaborative → comparative → evaluative |

Single-posture profiles force the user to pick one posture for the entire dialogue, losing the natural progression. Phase composition lets a profile define an ordered sequence of postures with target turns.

### Design: Option A (profile-level phases)

Three options were considered:

| Option | Mechanism | Pro | Con |
|--------|-----------|-----|-----|
| **A: Profile-level phases** | Transitions defined in YAML | Declarative, predictable, testable | Rigid phase boundaries |
| B: Agent-driven transitions | Agent decides when to shift based on dynamics | Adaptive | Complex logic, hard to test |
| C: Hybrid | Profile defines allowed transitions, agent decides timing | Bounded creativity | Most complex, needs trigger vocabulary |

**Option A selected** as the first step. Rationale:
- Can be implemented with minimal server convergence changes (see Section 4.3)
- Option A profiles migrate to Option C later by adding trigger fields — strict superset
- Real usage of Option A reveals which transitions matter before building adaptive logic

### Schema

```yaml
debugging:
  description: >
    Multi-phase debugging consultation. Explores the problem space, verifies
    hypotheses against evidence, then collaboratively designs a fix.
  sandbox: read-only
  approval_policy: never
  reasoning_effort: high
  phases:
    - posture: exploratory
      target_turns: 2
      description: Map the problem space — what could cause this?
    - posture: evaluative
      target_turns: 3
      description: Verify hypotheses against evidence
    - posture: collaborative
      target_turns: 2
      description: Design the fix together
  turn_budget: 7  # hard cap across all phases
```

### Budget rules

| Rule | Behavior |
|------|----------|
| Phase target is **advisory** | A phase may end early if its work is complete |
| Total budget is a **hard cap** | `current_turn >= turn_budget` forces conclude regardless of phase |
| Convergence overrides phase boundaries | If the server returns `action: conclude`, the dialogue ends regardless of remaining phases |
| Phase exhaustion | If a phase's target turns are consumed, transition to next phase. If no next phase, conclude. |
| Minimum 1 turn per phase | Every phase gets at least one turn — otherwise it shouldn't be a phase |

### Server changes required for phase composition

Codex review identified concrete failure modes with purely agent-side phase tracking:

| Failure Mode | Cause | Impact |
|-------------|-------|--------|
| **Plateau inheritance** | `compute_action` uses full ledger history. Exploratory turns' `static` deltas pollute the next phase's plateau detection. | False convergence — dialogue ends prematurely in a later phase |
| **Closing probe consumption** | One-shot closing probe fires in an early phase, consuming the closure budget before later phases run. | Later phases never get a closing probe |

**Minimal server changes (Release B):**

| Change | Component | Purpose |
|--------|-----------|---------|
| Add `last_posture` field | `ConversationState` | Track most recent posture value |
| Add `phase_start_index` field | `ConversationState` | Index of first entry in current phase |
| Phase-local convergence window | `compute_action` in `control.py` | Compute convergence on entries since last posture change |
| Reset closing probe on posture change | `compute_action` in `control.py` | Each phase gets its own closing probe budget |

**Backward compatibility:** When posture never changes (single-posture dialogues), the convergence window equals the full history and closing probe behaves identically to today. Parity tests must prove identical behavior.

### Phase transition mechanics

The codex-dialogue agent tracks `current_phase_index` alongside `current_turn`. At the start of each turn:

1. Check if `current_turn >= turn_budget` → conclude (hard cap)
2. Check if server returned `action: conclude` → conclude (convergence)
3. Compute turns spent in current phase
4. If turns_in_phase >= current phase's `target_turns`, advance `current_phase_index`
5. Set `posture` in the next `process_turn` request to `phases[current_phase_index].posture`

**Phase transition signaling:** The agent explicitly signals transitions to Codex via follow-up prompts ("We've explored the problem space — now let's verify the leading hypothesis against evidence."). This is agent-side only — no TurnRequest schema changes.

### Backwards compatibility

Profiles without `phases` continue to work exactly as today — the `posture` field at the top level is the single posture for all turns. The `phases` key is optional. When `phases` is present, the top-level `posture` field is omitted.

Validation rule: a profile must have either `posture` (single-phase) or `phases` (multi-phase), not both. If both are present, reject with a validation error.

### First composed profile: debugging

```yaml
debugging:
  description: >
    Multi-phase debugging consultation. Explores the problem space, verifies
    hypotheses against evidence, then collaboratively designs a fix. Provide
    the error, reproduction steps, and relevant code in the briefing material.
  sandbox: read-only
  approval_policy: never
  reasoning_effort: high
  phases:
    - posture: exploratory
      target_turns: 2
      description: Map the problem space — what could cause this?
    - posture: evaluative
      target_turns: 3
      description: Verify hypotheses against evidence
    - posture: collaborative
      target_turns: 2
      description: Design the fix together
  turn_budget: 7
```

---

## 5. Wire Protocol Impact

### Changes required (Release A — taxonomy)

| Component | Change | Breaking? |
|-----------|--------|-----------|
| `enums.py` Posture enum | Add `COMPARATIVE` | Yes (internal) |
| `types.py` TurnRequest.posture | Add `"comparative"` to Literal union | Yes (internal) |
| `context-injection-contract.md` | Update Posture enum documentation | Yes (spec) |
| `codex-dialogue.md` | Broaden evaluative patterns, add comparative patterns, update posture selection | Yes (agent) |
| `consultation-profiles.yaml` | Migrate `planning`, add 2 new profiles | Yes (config) |
| `consultation-contract.md` | Update profile definitions | Yes (spec) |
| `/dialogue` SKILL.md | Add `comparative` to `--posture` flag validation | Yes (skill) |
| `/codex` SKILL.md | Add `comparative` to posture documentation | Yes (skill) |
| Test fixtures using `"evaluative"` | No changes needed — evaluative is retained | No |

### Changes required (Release B — server convergence)

| Component | Change | Breaking? |
|-----------|--------|-----------|
| `conversation.py` ConversationState | Add `last_posture`, `phase_start_index` | Yes (internal) |
| `control.py` compute_action | Phase-local convergence window, closing probe reset | Yes (internal) |
| Parity tests | Prove identical single-posture behavior | New tests |

### Changes required (Release C — composition activation)

| Component | Change | Breaking? |
|-----------|--------|-----------|
| `consultation-profiles.yaml` | Add `phases` schema, `debugging` profile | Yes (config) |
| `codex-dialogue.md` | Phase tracking logic, transition signaling | Yes (agent) |
| `consultation-contract.md` | Add phase composition section | Yes (spec) |

### Changes NOT required

| Component | Why unchanged |
|-----------|--------------|
| `process_turn` request structure | Posture is already a per-turn string field — new values are transparent |
| `execute_scout` | Does not use posture |
| HMAC token flow | Does not include posture |
| Redaction pipeline | Does not use posture |
| Template matching | Posture-agnostic by design (see below) |

### Template ranking: posture-agnostic by design

The `enums.py` comment "Reserved for template ranking adjustments" is a premature abstraction. Template ranking operates over extracted entities (claim-driven), so posture-aware ranking can only reorder existing candidates, not discover new evidence classes. The comment should be reworded to "Currently posture-agnostic by design" and template ranking remains posture-unaware.

### Key insight: per-turn posture enables composition

The wire protocol was designed with `posture` as a per-turn field on `TurnRequest`, not per-conversation. This means the context injection server already accepts different postures on different turns of the same conversation. Phase composition requires server changes only for convergence detection (Release B), not for the wire protocol itself.

---

## 6. Agent Behavior Changes

### Posture selection (Phase 1)

Current disambiguation:

```
If the goal includes "find problems" or "challenge assumptions," use Adversarial.
If "assess quality" or "check coverage," use Evaluative.
```

New disambiguation:

| Signal in goal | Posture |
|----------------|---------|
| "find problems", "challenge assumptions", "stress-test" | adversarial |
| "brainstorm", "ideate", "build on", "what if" | collaborative |
| "research", "explore", "map", "what exists" | exploratory |
| "verify", "assess quality", "check coverage", "architecture review", "edge cases", "structural implications" | evaluative |
| "compare options", "trade-offs", "which is better", "rank", "choose between" | comparative |

### Follow-up composition (Phase 2, Step 6)

The posture-driven follow-up table expands from 4 rows to 5. The evaluative row is broadened significantly. See Section 2 for the full pattern sets.

### Phase tracking (new, Phase 2 — Release C)

For multi-phase profiles, the agent adds phase tracking to the existing turn loop:

```
Before each turn:
  1. Check hard cap (turn_budget)
  2. Check convergence (server action)
  3. Check phase target → advance phase if exhausted
  4. Set posture from current phase
  5. If phase changed, compose transition signal for follow-up
```

### Synthesis (Phase 3)

Add to synthesis output:
- **Phase trajectory:** Which phases were entered, how many turns each consumed, whether any were skipped by convergence
- **Recommended posture for continuation:** Already exists — extend to recommend phase composition if dynamics suggest it

---

## 7. Release Plan

### Release A: Taxonomy

| Action | Files |
|--------|-------|
| Add `COMPARATIVE` to Posture enum | `enums.py` |
| Add `"comparative"` to TurnRequest Literal | `types.py` |
| Broaden evaluative follow-up patterns | `codex-dialogue.md` |
| Add comparative follow-up patterns | `codex-dialogue.md` |
| Update posture selection disambiguation | `codex-dialogue.md` |
| Migrate `planning` profile to `comparative` | `consultation-profiles.yaml` |
| Add `decision-making` profile | `consultation-profiles.yaml` |
| Add `collaborative-ideation` profile | `consultation-profiles.yaml` |
| Add `comparative` to SKILL.md posture flags | `/dialogue` SKILL.md, `/codex` SKILL.md |
| Update Posture enum in contract | `context-injection-contract.md` |
| Update profile section in contract | `consultation-contract.md` |
| Reword "reserved for template ranking" comment | `enums.py` |
| Add `TestPosture` assertion for comparative | `test_enums.py` |

**Release gate:** Posture lockstep check across 5 locations (source enum, vendored enum, contract, analytics validator, skill docs). All must list the same 5 values.

### Release B: Server Convergence (behind flag)

| Action | Files |
|--------|-------|
| Add `last_posture`, `phase_start_index` to ConversationState | `conversation.py` |
| Phase-local convergence window in compute_action | `control.py` |
| Reset closing probe on posture change | `control.py` |
| Parity tests: single-posture behavior identical | New test file |
| Feature flag: `PHASE_AWARE_CONVERGENCE` | `control.py` or env var |

**Release gate:** All 969+ existing tests pass. Parity tests prove identical single-posture behavior with flag on and off.

### Release C: Composition Activation

| Action | Files |
|--------|-------|
| Add `phases` schema to profiles | `consultation-profiles.yaml` |
| Add `debugging` composed profile | `consultation-profiles.yaml` |
| Phase tracking logic in agent | `codex-dialogue.md` |
| Phase transition signaling | `codex-dialogue.md` |
| Phase composition section in contract | `consultation-contract.md` |
| Phase trajectory in synthesis | `codex-dialogue.md` |

**Release gate:** Debugging profile produces correct phase transitions in manual test dialogue.

---

## 8. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Partial rollout drift** — posture values updated in one location but not others | High | Silent desync between source and vendored copies | Release gate: posture lockstep check across 5 locations |
| **Rollback incompatibility** — `ConversationState` uses `extra="forbid"`, old binaries reject new fields | Medium | Cannot rollback Release B without data migration | Define rollback strategy before Release B ships |
| **Evaluative pattern quality** — broadened patterns may not serve both deep-review and code-review well | Medium | Regression in dialogue quality for one profile | User testing before Release A ships; measure follow-up pattern diversity |
| **False convergence in phases** — plateau detection may still fire incorrectly despite phase-local window | Low | Premature phase termination | Parity tests + manual testing of composed profiles |

---

## 9. Open Questions (Post-Review)

1. **Same-posture consecutive phases.** If a composed profile has two consecutive evaluative phases with different intents, the server's phase-local window won't detect the boundary. May need an explicit `phase_id` field. Deferred to post-Release B.

2. **Comparative follow-up patterns.** The proposed patterns need user testing before codifying. Release A should include them as initial patterns with the expectation of refinement.

3. **Rollback compatibility.** `ConversationState` checkpoint changes in Release B need a migration/rollback strategy. The `extra="forbid"` constraint means old binaries reject new fields.

---

## 10. Success Criteria

| Criterion | Release | Measurement |
|-----------|---------|-------------|
| All 969 existing tests pass with new posture value | A | Test suite green |
| Broadened evaluative patterns produce diverse follow-ups | A | Manual verification with deep-review and code-review dialogues |
| Comparative posture produces distinct follow-up patterns | A | Manual verification with planning and decision-making dialogues |
| Posture lockstep check passes across 5 locations | A | Automated validation |
| Single-posture behavior identical with phase-aware convergence | B | Parity tests pass |
| Phase composition correctly transitions postures mid-dialogue | C | Manual test with debugging profile |
| Phase trajectory appears in synthesis output | C | Manual verification |

---

## Appendix A: Codex Review Synthesis

**Thread:** `019cb50e-107e-7cd0-bc25-19dc50c451f8`
**Turns:** 6 of 8 budget
**Converged:** Yes — all 5 open questions answered, zero unresolved items

### Key outcomes

| Finding | Confidence | Basis |
|---------|-----------|-------|
| Reject three-way split; add only comparative (5-posture) | High | Convergence — 2+1 framing emerged from dialogue |
| Phase composition requires minimal server change | High | Convergence — plateau inheritance and closing probe failure modes identified |
| Three-release sequencing (A→B→C) | High | Convergence — isolates regression risk |
| Do not activate template ranking | High | Convergence — ranking is entity-driven, not posture-driven |
| Partial rollout drift is highest-probability failure | Medium | Codex proposed, Claude agreed |
| Evaluative patterns have pre-existing quality problem | Medium | Codex proposed, Claude agreed |

### Emerged insights

- **2+1 framing:** The evaluative overload is not a three-way split but a two-similar-plus-one-different problem
- **Phase-local convergence window:** Minimum viable server change for phase composition
- **Posture lockstep check:** Concrete release gate across 5 source locations
