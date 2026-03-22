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
| Item references upstream `finding_id` or `assumption_id` (see note below) | `adversarial-review` | Diagnosis surface changed |
| Item references upstream `task_id`, `gate_id` (within `decision_gates[]`), or critical path | `next-steps` | Planning surface changed |
| Item references neither, is evidence/framing question | `dialogue_continue` | Same scope, still gathering |
| Item hits both AR and NS surfaces | `adversarial-review` | Diagnosis before planning (precedence) |

**Definition of "upstream" for deterministic routing:** "Upstream" means IDs present in the consumed NS handoff's forwarded fields (`source_findings[]`, `source_assumptions[]`). When no NS handoff was consumed (standalone dialogue invocation), no IDs qualify as upstream references — deterministic routing rules requiring upstream ID matches cannot fire, and classification falls through to the model classification pass. AR capsules visible in conversation context but not ingested via the NS handoff adapter are NOT upstream sources for routing purposes.

For items without explicit upstream ID references: constrained LLM classification pass. Output one of `adversarial-review | next-steps | dialogue_continue | ambiguous`, name the affected surface, provide a one-line reason, and record `classifier_source: model`.

### Dimension Independence

`classifier_source` and `suggested_arc` are independent dimensions:

- `classifier_source` describes the classification *method* (deterministic rule vs. LLM judgment)
- `suggested_arc` describes the routing *outcome* (where the item should go)
- `ambiguous` is a valid outcome but not a valid method — every classification is performed by either a rule or the model. `classifier_source` MUST be `rule` or `model`. `ambiguous` is never a valid `classifier_source` value and MUST NOT appear in the emitted capsule. If an implementation produces `classifier_source: ambiguous`, treat as unexpected state, correct to `classifier_source: rule`, and emit a structured warning

### Ambiguous Item Behavior

`ambiguous` items enter the materiality gate like any other item. This table describes user-facing behavior during feedback evaluation (pre-correction classification). The [correction rules](#affected-surface-validity) subsequently transform these tuples before capsule emission — `material: false` + `suggested_arc: ambiguous` is corrected to `dialogue_continue` in the emitted wire format.

| Condition | User-Facing Behavior (pre-correction) |
|-----------|----------------------------------------|
| `material: false` + `suggested_arc: ambiguous` | Informational only. Reported to user but does not surface as a routing decision. No hop suggested. Corrected to `dialogue_continue` (rule 1); omitted from `feedback_candidates[]` and `unresolved[]` as informational-only. |
| `material: true` + `suggested_arc: ambiguous` | Manual routing bucket. User presented three actions: (1) send to adversarial-review, (2) send to next-steps, (3) hold. Default is **hold** — no hop occurs, no budget consumed. |

For `material: false` + `ambiguous` items, "reported to user" means included in prose synthesis output only. These items pass through the correction pipeline first; rule 1 normalizes `suggested_arc` to `dialogue_continue`, and the placement stage then omits them from `feedback_candidates[]` and `unresolved[]`. They appear in prose synthesis only — not in the machine-readable capsule.

**Disambiguation guidance:** If the ambiguity is "need more evidence before knowing which surface owns this item," the correct `suggested_arc` is `dialogue_continue`, not `ambiguous`. Use `ambiguous` only when the item is material but it is genuinely unclear whether diagnosis or planning owns the resolution.

**Non-response behavior:** If the user does not respond to the ambiguous routing prompt within the current skill invocation, treat as `hold`. A "response" is a user message that explicitly selects one of the three presented routing actions (send to AR, send to NS, or hold) for that specific item. Any other user action — invoking a different skill, asking an unrelated question, pressing enter without addressing the routing prompt, or ending the session — constitutes non-response. Pending ambiguous items are reported in the feedback capsule's `unresolved[]` list with `hold_reason: routing_pending` if a feedback capsule is emitted. The routing stage MUST set `hold_reason` to exactly `routing_pending` (no other value) when an ambiguous item is held. Implementations may set `hold_reason` either at the routing stage or at capsule assembly time, provided the value is `routing_pending` for held ambiguous items. The routing-stage attribution is architectural guidance, not a sequencing constraint — any implementation path that produces `hold_reason: routing_pending` for held ambiguous items satisfies the contract. They are not carried into subsequent invocations — no cross-session tracking of pending routing decisions in v1.

**Hold item loss (v1 limitation):** If the session terminates before a feedback capsule is emitted (user abandons dialogue, operational interruption), held ambiguous items are lost. This is an expected v1 loss path — conversation-local state has no recovery mechanism for interrupted sessions. The durable feedback file (see [selective durable persistence](#selective-durable-persistence)) only captures items that reach capsule emission.

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

**Correction rules** (deterministic, ordered — apply only when `suggested_arc` is not in the valid set for the given `(affected_surface, material)` pair; valid tuples pass through uncorrected). Rules MUST be evaluated in listed order (1, 2, 3, 4, 5). Parallel or out-of-order evaluation is prohibited — the "no remaining invalid tuples" claim in rule 5 holds only under sequential ordered evaluation:

1. If `material = false` AND `suggested_arc ≠ dialogue_continue` → correct to `dialogue_continue`
2. If `affected_surface = evidence-only` AND `suggested_arc ≠ dialogue_continue` → correct to `dialogue_continue`
3. If `affected_surface = diagnosis` AND `material = true` AND `suggested_arc ∉ {adversarial-review, ambiguous}` → correct to `adversarial-review`
4. If `affected_surface = planning` AND `material = true` AND `suggested_arc ∉ {next-steps, ambiguous}` → correct to `next-steps`
5. No remaining invalid tuples are possible given the matrix — if reached, emit `dialogue_continue` as the defensive fallback, set `classifier_source: rule`, and log a structured unexpected-state warning with the original `(affected_surface, material, suggested_arc)` tuple. Do NOT emit `ambiguous` — it is only valid for `diagnosis/true` and `planning/true` surfaces, which cannot be guaranteed in an unexpected state. `dialogue_continue` is the only `suggested_arc` valid for every `(affected_surface, material)` combination in the matrix.

Corrected outcomes record `classifier_source: rule`. Correction rules do NOT alter `materiality_source` — corrections affect routing classification (`suggested_arc`) only, not the materiality evaluation result. The `materiality_source` value reflects the tier that determined the `material` field and is preserved unchanged through the correction pipeline.

**Emission-time enforcement:** The correction pipeline is a required gate before `feedback_candidates[]` is written — capsule assembly MUST NOT begin until all entries have passed through the correction pipeline. Entries MUST be processed sequentially in list order; the correction pipeline evaluates one `(affected_surface, material, suggested_arc)` tuple at a time. Every `feedback_candidates[]` entry in the emitted capsule MUST reflect post-correction state. Capsule assembly paths that bypass the correction pipeline (e.g., direct model output projection) MUST still apply correction rules before writing `feedback_candidates[]`. The gate MUST additionally validate `classifier_source ∈ {rule, model}` for every `feedback_candidates[]` entry — an entry with `classifier_source` outside this set is an unexpected-state error; correct to `classifier_source: rule` and log a structured warning with the original value (see also [capsule-contracts.md](capsule-contracts.md#schema-constraints) for the parallel interface-layer constraint). The gate MUST also validate `materiality_source ∈ {rule, model}` for every `feedback_candidates[]` entry — an entry with `materiality_source` outside this set is an unexpected-state error; correct to `materiality_source: rule` and log a structured warning with the original value. This validation is parallel to `classifier_source` validation. The correction pipeline preserves `materiality_source` unchanged — meaning an invalid value set during materiality evaluation is corrected to `rule` at this gate before reaching the wire format.

**Partial correction failure:** If the correction pipeline fails partway through `feedback_candidates[]` processing (unexpected state in any entry), abort capsule assembly entirely and surface a prose error to the user — do NOT emit a partially corrected capsule. The capsule MUST be either fully corrected or not emitted. A partially corrected capsule is a silent protocol violation.

**Post-abort behavior:** When capsule assembly is aborted due to partial correction failure: (1) the dialogue skill MUST complete its normal prose synthesis output — the abort affects only the machine-readable capsule, not the user-facing prose, (2) the sentinel MUST NOT be emitted — suppress both the sentinel comment and the capsule body. A lone sentinel without a capsule body is NOT a valid emission state and is not equivalent to "no capsule." Consumers see "no capsule" state, (3) no durable file is written, (4) the structured warning MUST include the failing entry's index and the unexpected state values to support debugging, (5) hop suggestion text MUST NOT be emitted in the prose output — routing classification state is incomplete (parallel to [Step 0 case (c)](#material-delta-gating) post-abort behavior). The skill invocation is NOT terminated — only capsule emission is skipped.

**Consequence prohibitions** (with enforcing correction rule):

- `diagnosis` MUST NOT emit `next-steps` — enforced by rule 3
- `planning` MUST NOT emit `adversarial-review` — enforced by rule 4
- `evidence-only` MUST NOT emit AR, NS, or `ambiguous` — enforced by rule 2
- Material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue` — enforced by rules 3 and 4, which check `material = true` explicitly and correct to the appropriate arc regardless of how `dialogue_continue` was assigned

## Material-Delta Gating

Evaluate materiality using three tiers with a cross-tier guard. Tier 1 rule-based exclusions are final. Tier 1 model-judged exclusions are provisional.

**Precondition (Step 0):** Before running materiality evaluation, check the `upstream_handoff` pipeline state:

- (a) If `upstream_handoff` exists and `tautology_filter_applied` is `true`: precondition satisfied — items were filtered during decomposition seeding.
- (b) If no `upstream_handoff` exists: precondition trivially satisfied (standalone dialogue invocation).
- (c) If `upstream_handoff` exists, `decomposition_seed` was used (i.e., `handoff_enriched` mode activated per [pipeline-integration.md](pipeline-integration.md#decomposition-behavior)), AND `tautology_filter_applied` is `false` or absent: do NOT proceed with materiality evaluation — this is an unexpected pipeline state (decomposition ran but the tautology filter did not complete). Emit a structured warning and abort materiality evaluation for those items. Materiality evaluation on unfiltered decomposition items may classify upstream-framing echoes as material. When materiality evaluation is aborted for these items, abort capsule assembly entirely — do NOT emit a capsule with unclassified items. Post-abort behavior for Step 0 case (c) abort (enumerated — do not rely on "analogous to" cross-references): (1) the dialogue skill MUST complete its normal prose synthesis output — the abort affects only the machine-readable capsule, not the user-facing prose, (2) the sentinel MUST NOT be emitted — suppress both the sentinel comment and the capsule body, (3) no durable file is written at `.claude/composition/feedback/`, (4) the prose error MUST identify the failed precondition (`tautology_filter_applied` is false/absent despite decomposition having run). Hop suggestion text MUST NOT be emitted in the prose output when capsule assembly is aborted — the routing classification is in an unknown state.
- (d) If `upstream_handoff` exists but `decomposition_seed` was not used (e.g., `--plan` not set, or `--plan` set but `decomposition_seed` not available — see [pipeline-integration.md](pipeline-integration.md#decomposition-behavior) rows 3-5): precondition satisfied — the tautology filter does not apply when decomposition seeding did not run. No decomposition items exist to filter.

The `tautology_filter_applied` flag is set by the decomposition seeding stage when the [tautology filter](pipeline-integration.md#three-tier-tautology-filter) runs successfully (see [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage B capability flags). The materiality evaluator detects "decomposition_seed was used" by checking whether `upstream_handoff.decomposition_seed` is `true` in the capability flags set by the adapter at Stage B. This is a direct flag read, not a historical execution trace — the evaluator does not re-derive whether decomposition actually ran. Case (c) fires when both conditions hold: `decomposition_seed: true` AND `tautology_filter_applied ∈ {false, absent}`. Case (c) is restricted to scenarios where decomposition was attempted because `tautology_filter_applied: false` is expected and correct when decomposition did not run (case d).

### Novelty Veto (Pre-Check)

Before Tier 1, check whether the item introduces any new content relative to the source snapshot: a new failure mode, causal mechanism, consequence, dependency, gate effect, or contradiction.

If the item introduces novel content, Tier 1 MUST return `no_match` regardless of exclusion class fit. Proceed to Tier 2; if Tier 2 does not match, proceed to Tier 3.

**Tie-breaking rule:** When the novelty determination is uncertain (the item neither clearly introduces nor clearly restates known content), treat as novel — Tier 1 returns `no_match`. Novelty veto errors MUST favor false positives (unnecessary Tier 2/3 evaluation) over false negatives (suppression of potentially material items).

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

If the Tier 1 match used rule judgment (`materiality_source: rule`), the exclusion is final — skip Tiers 2-3, UNLESS Tier 2 criteria are also met (e.g., a restatement that also changes an assumption status to `wishful`). When both Tier 1 rule exclusion and Tier 2 inclusion criteria apply, Tier 2 takes precedence — the item is material. When a Tier 1 rule exclusion is overridden by Tier 2 inclusion, set `material: true`, `materiality_source: rule` (Tier 2 determination — the Tier 2 inclusion is the operative classification, not the Tier 1 exclusion). The Tier 1 rule exclusion is a default, not an absolute override of Tier 2 deterministic inclusions.

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

**Enforcement basis:** Application-layer checks are the primary enforcement mechanism — stub text review and grep-based CI prevent auto-chaining patterns from being introduced into skill stubs. See [verification.md](verification.md) for the specific checks. The platform-architectural constraint (skills cannot invoke tools without user-visible tool calls) provides ambient defense-in-depth but is NOT relied upon as the primary enforcement path — platform behavior is outside this spec's control boundary and may change independently. The composition system must enforce no-auto-chaining at the application layer regardless of platform guarantees.

**Capsule-level prohibition:** Feedback capsule fields (`continuation_warranted`, `feedback_candidates[].suggested_arc`) are informational signals to the user. Skill stubs MUST NOT use `continuation_warranted` or `suggested_arc` fields to programmatically trigger another skill invocation by any means — including direct invocation patterns, conditional branches leading to invocation (regardless of whether user-facing text is emitted), or indirect delegation chains through helper functions. These fields inform the hop suggestion text presented to the user only, not an automatic dispatch.

**Enforcement coverage note:** Grep-based CI and stub text review can detect direct invocation patterns and conditional branches but cannot structurally detect helper-mediated indirect delegation chains. Any helper function referenced from a composition stub's feedback capsule assembly path MUST be co-reviewed as part of the stub review and documented in the PR checklist. This is a known coverage gap in the interim enforcement — `validate_composition_contract.py` may add deeper static analysis when implemented.

### Material-Delta Gating (Guardrail)

Do not recommend a hop unless something changed relative to the source snapshot.

### Soft Iteration Budget

After 2 targeted loops in the same composition chain (same `lineage_root_id`), stop suggesting further hops automatically. Report remaining open items. User can override.

The budget uses `lineage_root_id` (chain identity), not `topic_key` (descriptive) or `subject_key` (exact lineage). Independent composition chains never share a budget. See [lineage.md](lineage.md#three-identity-keys) for key purposes and [lineage.md](lineage.md#key-propagation) for propagation rules.

#### Budget Enforcement Mechanics

**Targeted loop definition:** One targeted loop = one completed composition hop where a skill run produces a new artifact that is structurally consumed by the next skill in the chain via capsule sentinel. A hop suggested but not confirmed by the user does not consume a loop. `dialogue_continue` hops (same skill, no arc change) do not consume a loop — only cross-skill hops (`adversarial-review`, `next-steps`) count. Dialogue-to-dialogue arcs (same `artifact_kind: dialogue_feedback`) do not consume budget by design — the budget tracks AR↔NS surface hops, not dialogue continuation depth.

**What counts as "structurally consumed":** An artifact counts toward the budget counter if and only if it passed the [consumption discovery](lineage.md#consumption-discovery) validation gate (sentinel found, schema validated, capsule accepted) and represents a cross-skill transition (`artifact_kind ∈ {adversarial_review, next_steps_plan}`) — `dialogue_feedback` artifacts are excluded per the targeted loop definition above. Invalid or rejected capsules do not count toward the budget.

**Counting algorithm:** The budget counter counts the number of valid non-root artifacts in the lineage chain sharing the current `lineage_root_id` whose `artifact_kind` is `adversarial_review` or `next_steps_plan`. `dialogue_feedback` artifacts are excluded — only AR↔NS surface hops consume budget per the targeted loop definition. For example: if AR is the root, a chain [AR, NS] has counter = 1 because NS is the only valid non-root artifact. A chain [AR, NS, AR-re-review] has counter = 2 because NS and AR-re-review are both valid non-root artifacts — this reaches the default targeted-loop limit. A chain [AR, NS, dialogue_feedback] has counter = 1 (AR excluded as root, dialogue_feedback excluded from the valid set). This counts per-artifact, not per-transition — each non-root artifact that passed consumption discovery and has a qualifying `artifact_kind` adds 1 to the counter.

**Counter storage:** Conversation-local for v1. The dialogue skill's composition stub maintains the count by scanning the conversation context for artifacts sharing the current `lineage_root_id` and counting distinct cross-skill transitions. The scan MUST count only artifacts with valid sentinels and parseable schemas. Continue scanning past invalid capsules (do not stop at first invalid entry) — unlike consumption discovery's no-backtrack rule, the budget scan is a full-scan algorithm. Raw sentinel text with invalid or unparseable capsule content (e.g., a sentinel comment present but the capsule block malformed) MUST NOT increment the counter.

**Context compression resilience:** In long sessions, Claude Code compresses prior conversation turns, which may remove earlier hop artifacts from the visible context. When a feedback capsule in the current conversation context references a `lineage_root_id` but no prior artifacts with that `lineage_root_id` are visible in available context, the counter is indeterminate. In this case: treat the budget as not-exhausted and MUST emit a prose warning that: (1) identifies the cause as context compression, (2) notes that prior hop artifacts are not visible, and (3) states the system is proceeding as if budget is available. The exact wording may vary. Do NOT silently treat indeterminate state as exhausted or as zero. This is a known v1 limitation of conversation-local storage; a durable counter file would eliminate it but is deferred.

**Enforcement action:** When the budget is exhausted (2 targeted loops counted for the current `lineage_root_id`): (1) omit the hop suggestion block from the feedback capsule presentation, (2) emit a prose notice: "Composition budget reached for this chain (2/2 hops). Remaining open items listed below. Say 'continue' to override." (3) set `continuation_warranted` based on the synthesis outcome regardless of budget — the field remains informational.

**Override mechanism:** User says "continue" (or equivalent confirmation) in the next prompt. The override applies to the current `lineage_root_id` only and permits one additional hop. The budget does not reset — each override permits exactly one more hop.

## Thread Continuation vs Fresh Start

**Hard rule: new artifact → new thread.**

**Continue existing Codex thread** only when ALL of:

- Same goal
- Same upstream snapshot set (no new AR or NS artifact) — **deterministic check:** if ANY AR or NS capsule sentinel appears in conversation context with a `created_at` timestamp after the current feedback capsule's `thread_created_at` value (see [capsule-contracts.md](capsule-contracts.md#contract-3-dialogue-feedback-capsule) for the field definition), this condition MUST evaluate as false (no model judgment permitted). `thread_created_at` records when the Codex thread was established, providing the comparison baseline. Timestamp comparison MUST be performed as a parsed numeric comparison (not string comparison) using millisecond-precision UTC values. Both operands MUST be normalized to millisecond precision before comparison per the precision rule in [lineage.md](lineage.md#artifact-id-format)
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

**Source resolution precedence** (numbered as precedence levels to distinguish from the Material-Delta Gating tiers):

1. Explicit reference (artifact ID provided by user or upstream)
2. Durable store (`.claude/composition/feedback/`)
3. Conversation-local (sentinel scan of visible context)

The durable file uses the same wire format as the conversation capsule. `record_path` in the dialogue feedback capsule MUST be non-null and MUST point to the durable file.

**Consumer-side contract for durable store lookup:** When checking the durable store (precedence level 2): first check `record_path` nullity. If `record_path` is null (which violates the emitter-side MUST but may occur due to bugs), treat as an unexpected state — emit a one-line prose warning and MUST fall through to conversation-local sentinel scan (precedence level 3). Do NOT block the skill invocation or treat null `record_path` as a terminal error. If `record_path` is non-null but the file does not exist, check `record_status`. If `record_status: write_failed`, MUST fall through to conversation-local sentinel scan (precedence level 3). If `record_status` is `ok` but the file is missing, treat as an unexpected state — emit a one-line prose warning and MUST fall through to precedence level 3. If `record_status` is absent (emitter bug), treat as an unexpected state — emit a one-line prose warning and MUST fall through to conversation-local sentinel scan (precedence level 3). When `record_status` is absent, fall through to conversation-local scan even if the durable file appears to exist at `record_path` — an absent `record_status` indicates an emitter bug that may have produced a corrupt or incomplete file. Do not attempt to read or use a file when `record_status` is absent. Do NOT block the skill invocation on a missing durable file or any unexpected durable-store state.

**Write failure recovery:** If the durable file write fails (disk full, permission error, path unavailable): (1) surface a prose warning to the user identifying the write failure and the intended file path, (2) the emitted capsule MUST include `record_status: write_failed` and MUST set `record_path` to the intended path (the path that was attempted, not null), (3) the capsule remains consumable via conversation-local sentinel scan but cross-session resolution via durable store will fail. Do NOT emit a capsule with `record_path: null` — this violates the non-null MUST and silently degrades the feedback arc.

On a successful durable file write, the emitted capsule MUST set `record_status: ok`. `record_status` MUST always be present; omitting it is an emitter bug (see consumer-side contract above for how absent `record_status` is handled).

**Path construction rule:** The fully-resolved durable file path MUST be computed and stored to a local variable before initiating the write operation. The error handler MUST read the path from this pre-computed variable, not re-derive it. `record_path` MUST be a fully-resolved absolute filesystem path (not relative), constructed at the time of the write attempt. "Intended path" means this pre-computed absolute path (e.g., `/Users/user/project/.claude/composition/feedback/dialogue-redaction-pipeline-20260318T151033.789.md`), not a directory or template. The path pre-computation MUST occur before the correction pipeline gate — the fully-resolved path is needed by the error handler regardless of whether the correction pipeline succeeds or aborts. Ordering relative to the correction gate: compute path → run correction pipeline → write file (if correction succeeds) or reference path in error handler (if correction fails).
