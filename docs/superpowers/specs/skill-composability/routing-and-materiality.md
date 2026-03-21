---
module: routing-and-materiality
status: active
normative: true
authority: routing
---

# Routing and Materiality

## Routing Classification

Classification happens in `/dialogue` (the orchestrator), not in the codex-dialogue agent. Deterministic-first:

| Signal | Suggested Arc | Rationale |
|--------|--------------|-----------|
| Item references upstream `finding_id` or `assumption_id` | `adversarial-review` | Diagnosis surface changed |
| Item references upstream `task_id`, `gate_id` (within `decision_gates[]`), or critical path | `next-steps` | Planning surface changed |
| Item references neither, is evidence/framing question | `dialogue_continue` | Same scope, still gathering |
| Item hits both AR and NS surfaces | `adversarial-review` | Diagnosis before planning (precedence) |

For items without explicit upstream ID references: constrained LLM classification pass. Output one of `adversarial-review | next-steps | dialogue_continue | ambiguous`, name the affected surface, provide a one-line reason, and record `classifier_source: model`.

### Dimension Independence

`classifier_source` and `suggested_arc` are independent dimensions:

- `classifier_source` describes the classification *method* (deterministic rule vs. LLM judgment)
- `suggested_arc` describes the routing *outcome* (where the item should go)
- `ambiguous` is a valid outcome but not a valid method — every classification is performed by either a rule or the model

### Ambiguous Item Behavior

`ambiguous` items enter the materiality gate like any other item:

| Condition | Behavior |
|-----------|----------|
| `material: false` + `suggested_arc: ambiguous` | Informational only. Reported to user but does not surface as a routing decision. No hop suggested. |
| `material: true` + `suggested_arc: ambiguous` | Manual routing bucket. User presented three actions: (1) send to adversarial-review, (2) send to next-steps, (3) hold. Default is **hold** — no hop occurs, no budget consumed. |

**Disambiguation guidance:** If the ambiguity is "need more evidence before knowing which surface owns this item," the correct `suggested_arc` is `dialogue_continue`, not `ambiguous`. Use `ambiguous` only when the item is material but it is genuinely unclear whether diagnosis or planning owns the resolution.

**Non-response behavior:** If the user does not respond to the ambiguous routing prompt within the current skill invocation (moves on, invokes a different skill, or ends the session), treat as `hold`. Pending ambiguous items are reported in the feedback capsule's `unresolved[]` list if a feedback capsule is emitted. They are not carried into subsequent invocations — no cross-session tracking of pending routing decisions in v1.

## Affected-Surface Validity

After routing classification and materiality evaluation, validate the tuple `(affected_surface, material, suggested_arc)`:

| `affected_surface` | `material` | Valid `suggested_arc` Values |
|--------------------|------------|------------------------------|
| `diagnosis` | `true` | `adversarial-review`, `ambiguous` |
| `planning` | `true` | `next-steps`, `ambiguous` |
| `evidence-only` | `true` | `dialogue_continue` |
| `diagnosis` | `false` | `dialogue_continue` |
| `planning` | `false` | `dialogue_continue` |
| `evidence-only` | `false` | `dialogue_continue` |

**Correction rules** (deterministic, ordered — apply only when `suggested_arc` is not in the valid set for the given `(affected_surface, material)` pair; valid tuples pass through uncorrected):

1. If `material = false` AND `suggested_arc ≠ dialogue_continue` → correct to `dialogue_continue`
2. If `affected_surface = evidence-only` AND `suggested_arc ≠ dialogue_continue` → correct to `dialogue_continue`
3. If `affected_surface = diagnosis` AND `material = true` AND `suggested_arc ∉ {adversarial-review, ambiguous}` → correct to `adversarial-review`
4. If `affected_surface = planning` AND `material = true` AND `suggested_arc ∉ {next-steps, ambiguous}` → correct to `next-steps`
5. No remaining invalid tuples are possible given the matrix — if reached, emit `ambiguous` as a defensive fallback and log an unexpected-state warning.

Corrected outcomes record `classifier_source: rule`.

**Consequence prohibitions:**

- `diagnosis` MUST NOT emit `next-steps`
- `planning` MUST NOT emit `adversarial-review`
- `evidence-only` MUST NOT emit AR, NS, or `ambiguous`
- Material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue`

## Material-Delta Gating

Evaluate materiality using three tiers with a cross-tier guard. Tier 1 rule-based exclusions are final. Tier 1 model-judged exclusions are provisional.

**Precondition:** Items entering materiality evaluation MUST have passed through the [tautology filter](pipeline-integration.md#three-tier-tautology-filter) during decomposition seeding (when `--plan` + `upstream_handoff` is active). Materiality evaluation on unfiltered items may classify upstream-framing echoes as material. When no tautology filter ran (no `upstream_handoff`), this precondition is trivially satisfied — there is no upstream framing to echo.

### Novelty Veto (Pre-Check)

Before Tier 1, check whether the item introduces any new content relative to the source snapshot: a new failure mode, causal mechanism, consequence, dependency, gate effect, or contradiction.

If the item introduces novel content, Tier 1 MUST return `no_match` regardless of exclusion class fit. Proceed to Tier 2; if Tier 2 does not match, proceed to Tier 3.

**Rationale:** Items with novel content can pattern-match Tier 1 exclusion classes (e.g., a novel architectural consequence might look like an "exact restatement") but MUST NOT be pre-screened out.

### Tier 1 — Pre-Screening Exclusions (closed v1 set)

An item is **provisionally not material** if any of these apply (and the novelty veto did not fire):

- An exact restatement or example of an existing item in the source snapshot
- An open question already present in the source snapshot
- A clearly unsupported tangent with no affected upstream refs

This is a closed set for v1. Do not add exclusion classes without updating this list.

Set `materiality_source: rule` when the exclusion is clear-cut; set `materiality_source: model` with a one-line reason when it required interpretation.

### Cross-Tier Guard

If the Tier 1 match used model judgment (`materiality_source: model`), the exclusion is provisional. Check Tier 2 before finalizing:

- If Tier 2 would include the item → Tier 2 takes precedence. Set `material: true`, `materiality_source: rule`.
- If Tier 2 does not match → the Tier 1 model exclusion stands. Set `material: false`.

If the Tier 1 match used rule judgment (`materiality_source: rule`), the exclusion is final. Skip Tiers 2-3.

### Tier 2 — Rule-Based Inclusions (deterministic)

An item is **material** if any of:

- Crosses an action threshold: assumption status → `wishful`, finding severity → `blocking`/`high`, task → on/off critical path, decision gate → changed branch outcome

If Tier 2 matches: `material: true`, `materiality_source: rule`. Skip Tier 3.

**Deferred from v1:** "Reopens or contradicts something previously resolved" removed — NS handoff has no explicit resolved-item set, making this branch unreachable from dialogue's direct source snapshot. See [capsule-contracts.md](capsule-contracts.md#forwarding-rules) reachability guarantee.

### Tier 3 — Semantic Evaluation (model fallback)

If neither Tier 1 nor Tier 2 matched (or if Tier 1 returned `no_match` due to novelty veto):

- Does the item introduce a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface?
- Does it introduce a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface?
- Is this an implementation detail below the current abstraction level?

Set `materiality_source: model`. Provide a one-line `materiality_reason`. See also the [tautology filter](pipeline-integration.md#three-tier-tautology-filter), which prevents upstream framing echo during decomposition seeding — a related guard operating at the input stage (Step 0) rather than the feedback classification stage.

For pending implementation items (CI enforcement, validation harness), see [delivery.md](delivery.md#open-items).

### Dimension Note

`materiality_source` is separate from `classifier_source`. `classifier_source` describes the routing classification method. `materiality_source` describes the materiality evaluation method. Do not conflate.

## Guardrails

### No Auto-Chaining

Skills suggest the next arc; the user confirms. No skill auto-invokes another.

**Enforcement basis:** Claude Code's tool invocation model is the enforcement mechanism — skills cannot invoke tools (including other skill invocations) without user-visible tool calls that the user can interrupt or deny. This is a platform-architectural constraint, not an application-layer check. A violation would require Claude to autonomously invoke a skill invocation pattern (e.g., emitting `/<skill>` as a tool call) without user confirmation, which the host platform does not permit.

**Capsule-level prohibition:** Feedback capsule fields (`continuation_warranted`, `feedback_candidates[].suggested_arc`) are informational signals to the user. Skill stubs MUST NOT use these fields to programmatically trigger another skill invocation. They inform the hop suggestion text presented to the user, not an automatic dispatch.

### Material-Delta Gating

Do not recommend a hop unless something changed relative to the source snapshot.

### Soft Iteration Budget

After 2 targeted loops in the same composition chain (same `lineage_root_id`), stop suggesting further hops automatically. Report remaining open items. User can override.

The budget uses `lineage_root_id` (chain identity), not `topic_key` (descriptive) or `subject_key` (exact lineage). Independent composition chains never share a budget. See [lineage.md](lineage.md#key-propagation) for `lineage_root_id` propagation rules.

#### Budget Enforcement Mechanics

**Targeted loop definition:** One targeted loop = one completed composition hop where a skill run produces a new artifact that is structurally consumed by the next skill in the chain via capsule sentinel. A hop suggested but not confirmed by the user does not consume a loop. `dialogue_continue` hops (same skill, no arc change) do not consume a loop — only cross-skill hops (`adversarial-review`, `next-steps`) count.

**Counter storage:** Conversation-local for v1. The dialogue skill's composition stub maintains the count by scanning the conversation context for artifacts sharing the current `lineage_root_id` and counting distinct cross-skill transitions. No durable counter file is needed — the artifacts themselves are the ledger.

**Enforcement action:** When the budget is exhausted (2 targeted loops counted for the current `lineage_root_id`): (1) omit the hop suggestion block from the feedback capsule presentation, (2) emit a prose notice: "Composition budget reached for this chain (2/2 hops). Remaining open items listed below. Say 'continue' to override." (3) set `continuation_warranted` based on the synthesis outcome regardless of budget — the field remains informational.

**Override mechanism:** User says "continue" (or equivalent confirmation) in the next prompt. The override applies to the current `lineage_root_id` only and permits one additional hop. The budget does not reset — each override permits exactly one more hop.

## Thread Continuation vs Fresh Start

**Hard rule: new artifact → new thread.**

**Continue existing Codex thread** only when ALL of:

- Same goal
- Same upstream snapshot set (no new AR or NS artifact)
- Unresolved items are evidence/clarification questions, not changed diagnosis or plan
- Prior termination was operational (budget exhaustion, scope breach resolved, interruption)

**Fresh `/dialogue` with new briefing** when ANY of:

- New AR snapshot exists
- New NS snapshot exists
- Posture or focus changed materially
- Selected task/gate set changed

Never inject updated AR/NS artifacts into an existing Codex thread. Once diagnosis or planning has changed, the old conversation state is stale.

## Selective Durable Persistence

Only `dialogue_feedback` gets durable persistence. AR→NS and NS→dialogue arcs remain conversation-local in v1.

**Rationale:** The feedback arc (dialogue → AR/NS) is the only composition path that reliably crosses invocation boundaries. AR→NS and NS→dialogue happen in rapid sequence within a single session. Dialogue feedback may be consumed hours or sessions later.

| Arc | Transport | Persistence |
|-----|-----------|-------------|
| AR → NS | Conversation-local (sentinel scan) | None |
| NS → Dialogue | Conversation-local (sentinel scan) | None |
| Dialogue → AR/NS (feedback) | Conversation-local + durable file | `.claude/composition/feedback/` (gitignored) |

**Source resolution precedence:**

1. Explicit reference (artifact ID provided by user or upstream)
2. Durable store (`.claude/composition/feedback/`)
3. Conversation-local (sentinel scan of visible context)

The durable file uses the same wire format as the conversation capsule. `record_path` in the dialogue feedback capsule MUST be non-null and MUST point to the durable file.

**Write failure recovery:** If the durable file write fails (disk full, permission error, path unavailable): (1) surface a prose warning to the user identifying the write failure and intended path, (2) emit the feedback capsule with `record_path` set to the intended path and an additional `record_status: write_failed` field, (3) the capsule remains consumable via conversation-local sentinel scan but cross-session resolution via durable store will fail. Do NOT emit a capsule with `record_path: null` — this violates the non-null MUST and silently degrades the feedback arc.
