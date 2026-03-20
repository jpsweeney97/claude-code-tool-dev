# Skill Composability Design

**Date:** 2026-03-18
**Status:** Draft
**Branch:** feature/skill-creator-session
**Dependencies:** adversarial-review skill, next-steps skill, cross-model:dialogue skill (all merged to main)

## Problem

Three skills form a natural analysis pipeline — adversarial-review (AR) produces findings, next-steps (NS) turns findings into a phased plan, and dialogue consults Codex on specific tasks. Today they compose only through implicit conversation context: AR's output is free-form markdown, NS references `/dialogue` in a prose suggestion, and dialogue's `--plan` flag decomposes from the raw user question without awareness of upstream context.

This creates three gaps:
1. **No structural contracts** between skills — finding identity, severity carry-forward, and task references rely on prose parsing.
2. **No guided handoffs** — AR doesn't suggest NS, NS's suggestion of dialogue is prose-only, and dialogue's synthesis has no downstream consumer contract.
3. **No feedback loop** — dialogue synthesis (RESOLVED/UNRESOLVED/EMERGED) cannot feed back into AR for re-review or NS for replanning.

## Scope

**In scope:**
- Structural contracts between AR, NS, and dialogue
- Capsule and sentinel formats for inter-skill data exchange
- Adaptive `--plan` behavior when upstream context is present
- Feedback loop architecture (dialogue → AR/NS)
- Lineage model for artifact versioning and staleness detection
- Shared composition contract governing cross-skill semantics

**Out of scope:**
- Changes to the codex-dialogue agent's synthesis format (capsules are assembled by the `/dialogue` skill, not the agent)
- Automatic multi-skill orchestration (user remains the circuit breaker)
- File-based persistence requirements (conversation-local is sufficient for v1, except `dialogue_feedback` which has selective durable persistence — see Feedback Loop Architecture)
- Changes to the global CLAUDE.md protocols (Adversarial Self-Review, Next Steps Planning remain independent behaviors)

## Design Decisions

### D1: Composability model is standalone-first, protocol-rich composition

Each skill remains fully standalone and human-usable. Composition is additive — structured capsules and sentinels are appended to or alongside existing prose output. No skill requires upstream context to function.

**Alternatives considered:**
- **Observational only** (document the implicit format mapping, no structural changes): Too brittle — finding identity breaks, severity carry-forward is unreliable from prose parsing.
- **Full protocol** (formal schemas with validation, required fields): Over-couples skills, pushes AR toward remediation logic, violates standalone principle.
- **Orchestrator meta-skill**: Over-engineers a 3-skill pipeline. Revisit if pipeline grows beyond these skills.

### D2: Two consumer classes

| Class | Behavior | Used by |
|-------|----------|---------|
| Advisory/tolerant | Validate if capsule present; fall back to prose parsing if absent or invalid. Emit a one-line prose diagnostic when falling back (e.g., "AR capsule not detected; lineage tracking unavailable for this run.") | NS consuming AR capsule |
| Strict/deterministic | Reject invalid capsule but continue normal pipeline (no fallback to different data source) | Dialogue consuming NS handoff |

Unknown sentinel versions: "reject block, not session" — a version mismatch prevents capsule consumption but does not break the skill invocation.

### D3: Feedback loop topology is targeted arcs with user ratification

Dialogue synthesis feeds back to AR or NS individually based on what emerged, not as a full pipeline re-run. The user confirms each hop. No auto-chaining.

### D4: State is snapshot-based with lineage

Each skill run produces a new artifact. No growing context across iterations. Lineage references (supersedes, source_artifacts) enable staleness detection without requiring full history carry-forward.

### D5: Global CLAUDE.md protocols do not auto-emit capsules

Capsules are for externalized artifacts from explicit skill invocations. The global Adversarial Self-Review and Next Steps Planning protocols may emit the same schema only on explicit user request. Rule: "same schema when externalized, no schema obligation when used as internal reasoning scaffolding."

---

## Contract 1: AR → NS (AR Capsule)

### Purpose

Give NS stable, machine-referenceable access to AR findings without requiring prose parsing. Preserves AR's principle of separating diagnosis from remediation.

### Consumer class

Advisory/tolerant. NS validates the capsule if present; falls back to prose parsing if absent or invalid.

**Provenance in fallback:** When NS falls back to prose parsing (capsule absent or invalid), the NS handoff MUST omit `source_artifacts` entries for the absent capsule. Do not reference an AR `artifact_id` that was not structurally consumed. This preserves lineage integrity — downstream consumers can trust that `source_artifacts` entries represent structurally validated provenance, not prose-derived references.

### When emitted

AR appends the capsule after its prose output (after the Confidence Check section). The capsule is always emitted when the adversarial-review skill runs — it costs nothing to produce and NS can ignore it.

### Sentinel

```
<!-- ar-capsule:v1 -->
```

### Schema

```yaml
artifact_id: ar:<subject_key>:<created_at_compact>
artifact_kind: adversarial_review
subject_key: <kebab-case derived from review_target, or inherited from upstream feedback capsule>
topic_key: <non-authoritative descriptive metadata — same as subject_key unless reviewing a facet of a broader topic>
lineage_root_id: <this artifact's artifact_id if standalone (root of chain); inherited unchanged from upstream capsule if consuming one>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior artifact_id of same kind and subject_key, or null>
source_artifacts: <[] if standalone; include upstream feedback capsule if re-review triggered by dialogue feedback>
record_path: <path to docs/reviews/ file or null>

review_target: <one-line description of what was reviewed>
overall_confidence: <1-5>
findings:
  - finding_id: F1
    severity: blocking | high | moderate | low
    summary: <one-line description>
  - finding_id: F2
    severity: high
    summary: ...
assumptions:
  - assumption_id: A1
    text: <assumption text>
    status: validated | plausible | wishful
    if_wrong: <one-sentence consequence>
open_questions:
  - <question text>
```

### Design notes

- **Finding IDs are snapshot-scoped.** `finding_id` is a machine reference within one review run. A separate `artifact_id` provides snapshot identity. Cross-run remapping is not normative — a materially changed review forces NS to rebase.
- **`if_wrong` preserves diagnostic mechanism** without crossing into remediation. AR says "if this assumption fails, X breaks" — NS decides what to do about it.
- **Excludes task decomposition, dependency maps, or sequencing.** These are NS's domain.

### AR skill text changes

Add after the Confidence Check section:

```
## After the review

If this review surfaced multiple findings that need coordinated action,
suggest `/next-steps` to sequence the work.
```

Add capsule emission instructions (always emit after prose output).

---

## Contract 2: NS → Dialogue (NS Handoff Block)

### Purpose

Give dialogue's `--plan` flag structured task context, dependencies, originating findings, and decision gates — enabling enriched decomposition instead of starting from scratch.

### Consumer class

Strict/deterministic. Dialogue rejects an invalid handoff block but continues its normal pipeline (gatherers, briefing assembly, delegation). It does not fall back to a different data source.

### When emitted

NS emits one handoff block per recommended task when it suggests `/dialogue`. Typically accompanies the highest-risk task or recommended first move.

### Sentinel

```
<!-- next-steps-dialogue-handoff:v1 -->
```

This is distinct from `<!-- dialogue-orchestrated-briefing -->`, which means "/dialogue already assembled the full Codex briefing." The NS handoff is input to dialogue's pipeline, not a replacement for it. The NS sentinel never reaches codex-dialogue.

### Schema

```yaml
artifact_id: ns:<subject_key>:<created_at_compact>
artifact_kind: next_steps_plan
subject_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
topic_key: <non-authoritative descriptive metadata — inherited from AR capsule if consumed, otherwise derived from plan topic>
lineage_root_id: <inherited from AR capsule if consumed; otherwise this artifact's artifact_id (root of chain)>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior NS artifact_id for this subject_key, or null>
source_artifacts:
  - artifact_id: <AR artifact_id if AR capsule was consumed, omit entry if not>
    artifact_kind: adversarial_review
    role: diagnosis
record_path: null

focus_question: <what this dialogue should resolve>
recommended_posture: <adversarial | collaborative | exploratory | evaluative | comparative>
selected_tasks:
  - task_id: T2
    task: <task description>
    why_now: <why this task is recommended for dialogue>
    depends_on: [T1]
    done_when: <strategic completion condition>
decision_gates:
  - gate_id: G1
    after: T2
    condition: <if X then path A; otherwise path B>
source_findings:
  - finding_id: F1
    severity: blocking
    summary: <from AR capsule>
  - finding_id: F3
    severity: high
    summary: ...
out_of_scope:
  - <parked item>
```

### Pipeline threading

The NS handoff threads through the full `/dialogue` pipeline via the generic `upstream_handoff` state. Each stage consumes capability flags, not the NS schema directly:

| Pipeline stage | Capability consumed | How upstream context is used |
|----------------|--------------------|-----------------------------|
| Pre-Step 0 | (Stage A/B) | Parse sentinel → validate → normalize to `upstream_handoff` via adapter |
| Step 0 | `decomposition_seed` | Seed decomposition: planning_question from focus_question + done_when; assumptions from source_findings; key_terms from task context entities |
| Step 2 | `gatherer_seed` | Gatherer prompts enriched with task names, finding entities, decision gate conditions |
| Step 3 | `briefing_context` | Deterministic projection of source_findings and decision_gates into briefing Context section |
| Step 3c | `briefing_context` | Zero-output fallback preserves upstream context as sole grounding |

**Boundary clarification:** The `upstream_handoff` state couples to pipeline stages documented in the dialogue skill's SKILL.md. This is documented interface coupling through a generic internal interface, not NS-specific coupling.

### Posture precedence

```
explicit --posture > --profile > upstream_handoff recommended_posture > default collaborative
```

Upstream handoffs do not derive multi-phase profiles from a single posture hint. If future handoff-driven phases are needed, upstream skills would emit `recommended_phases[]`.

### NS skill text changes

Add handoff block emission when suggesting dialogue. Update the existing line 157 suggestion to include the sentinel block.

---

## Contract 3: Dialogue → AR/NS (Feedback Capsule)

### Purpose

Enable iterative refinement by giving AR and NS structured access to dialogue outcomes — what was resolved, what emerged, and what needs re-review or replanning.

### Consumer class

Advisory/tolerant (same as AR capsule). AR and NS validate the feedback capsule if present; fall back to conversation context if absent.

### When emitted

The `/dialogue` skill (not the codex-dialogue agent) appends the feedback capsule after presenting the synthesis to the user. Derived from the existing Synthesis Checkpoint — not a new parallel format.

### Sentinel

```
<!-- dialogue-feedback-capsule:v1 -->
```

### Schema

```yaml
artifact_id: dialogue:<subject_key>:<created_at_compact>
artifact_kind: dialogue_feedback
subject_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
topic_key: <non-authoritative descriptive metadata — inherited from NS handoff if consumed, otherwise derived from goal topic>
lineage_root_id: <inherited from NS handoff if consumed; otherwise this artifact's artifact_id (root of chain)>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior dialogue artifact_id for this subject_key, or null>
source_artifacts:
  - artifact_id: <NS artifact_id if handoff was consumed>
    artifact_kind: next_steps_plan
    role: plan
record_path: null

thread_id: <Codex thread ID>
converged: <true | false>
turn_count: <int>

resolved:
  - item_id: R1
    text: <what was resolved>
    confidence: high | medium | low
unresolved:
  - item_id: U1
    text: <what remains open>
emerged:
  - item_id: E1
    text: <new concept or risk that emerged>

continuation_warranted: <true | false>
recommended_posture: <posture or null>

feedback_candidates:
  - item_id: E1
    suggested_arc: adversarial-review | next-steps | dialogue_continue | ambiguous
    affected_surface: diagnosis | planning | evidence-only
    affected_refs: [<upstream artifact_id/finding_id references>]
    material: true | false
    materiality_reason: <one-line explanation>
    classifier_source: rule | model
    materiality_source: rule | model
```

Note: `classifier_source` narrowed to `rule | model` (no `ambiguous`).

---

## Adaptive `--plan` (Two-Stage Admission with Adapter Pattern)

### Design principle: adapters not modes

Dialogue's internal interface uses a generic `upstream_handoff` state. Type-specific logic lives at the ingestion edge as adapters, not as decomposition modes. Adding a future upstream skill type means adding an adapter, not a new mode table entry.

### Two-stage admission

**Stage A — Detect and validate (type-specific):**

Scan conversation context for a known upstream sentinel. v1 recognizes:

| Sentinel | Producer | Adapter |
|----------|----------|---------|
| `<!-- next-steps-dialogue-handoff:v1 -->` | next-steps | NS adapter |

If a sentinel is detected, validate the capsule schema against the expected format. If invalid, reject the capsule (strict consumer class) and proceed as if no upstream handoff exists.

Future upstream skills register new sentinels and adapters here. The pipeline below Stage A is unchanged.

**Stage B — Normalize to `upstream_handoff` (generic):**

The adapter normalizes the validated capsule into a generic `upstream_handoff` pipeline state with capability flags:

| Capability flag | Meaning | NS adapter sets |
|----------------|---------|-----------------|
| `decomposition_seed` | Can seed decomposition fields (planning_question, assumptions, key_terms, ambiguities) | `true` |
| `gatherer_seed` | Can seed gatherer search terms with task/finding entities | `true` |
| `briefing_context` | Can inject source_findings and decision_gates into briefing assembly | `true` |

The pipeline gates enrichment on what the adapter provides, not what type produced it. A future adapter that provides `gatherer_seed` but not `decomposition_seed` would enrich gatherer prompts without affecting decomposition.

### Decomposition behavior

| Condition | Behavior |
|-----------|----------|
| `--plan` set, no `upstream_handoff` | `raw_input` — decompose from user's question (current behavior) |
| `--plan` set, `upstream_handoff` with `decomposition_seed` | `handoff_enriched` — seed decomposition from upstream context |
| `--plan` set, `upstream_handoff` without `decomposition_seed` | `raw_input` — decompose from question; upstream context available to later stages via other capability flags |
| `--plan` not set, `upstream_handoff` present | No decomposition; upstream context available to later steps (gatherer seeds, briefing assembly) via capability flags |
| `--plan` not set, no `upstream_handoff` | Current behavior unchanged |

### Enriched decomposition seeding

When `decomposition_seed` is available:

| Decomposition field | `raw_input` source | `handoff_enriched` source |
|---------------------|-------------------|--------------------------|
| `planning_question` | Decompose from raw question | Derive from `focus_question` + `done_when` condition |
| `assumptions` | Extract from question | Seed from `source_findings` (each finding implies a testable assumption) |
| `key_terms` | Extract from question | Seed from task context entities — names, concepts, file paths from findings |
| `ambiguities` | Extract from question | Seed from `decision_gates` conditions — the unknowns that matter |

Enriched mode **adds to** the decomposition, not replaces it. The user's actual question still drives the primary decomposition; the handoff context supplements it.

### Three-tier tautology filter

In `handoff_enriched` mode, prevent echo of upstream framing:

1. **Question set** — do not restate the focus_question or the user's raw question as an assumption
2. **Plan metadata set** — do not parrot task descriptions, done_when conditions, or dependency statements
3. **Soft echo set** — source_findings can inspire derived assumptions but not be restated verbatim. A derived assumption must operationalize the finding (make it testable against the codebase), not merely reword it.

**Tier 3 examples:**

Given source finding `F1: "NS handoff deeply couples to dialogue's internal pipeline stages"`:

| Derived assumption | Valid? | Reason |
|--------------------|--------|--------|
| "The NS handoff references dialogue's internal pipeline stages" | No — restatement | Restates the finding in assumption form without operationalizing it |
| "Dialogue's pipeline stages could be refactored without breaking the NS handoff contract" | Yes — operationalizable | Makes the finding testable against the codebase: check whether pipeline stages are referenced in the NS schema |
| "The pipeline stages referenced by the NS handoff are documented as public interface" | Yes — operationalizable | Tests whether the coupling is to a public or internal surface — a factual codebase question |
| "The NS handoff couples to dialogue's pipeline" | No — restatement | Removes specificity ("internal pipeline stages") without adding testability |

---

## Feedback Loop Architecture

### Routing Classification

Classification happens in `/dialogue` (the orchestrator), not in the codex-dialogue agent. Deterministic-first:

| Signal | Suggested arc | Rationale |
|--------|--------------|-----------|
| Item references upstream `finding_id` or `assumption_id` | `adversarial-review` | Diagnosis surface changed |
| Item references upstream `task_id`, `decision_gate_id`, or critical path | `next-steps` | Planning surface changed |
| Item references neither, is evidence/framing question | `dialogue_continue` | Same scope, still gathering |
| Item hits both AR and NS surfaces | `adversarial-review` | Diagnosis before planning (precedence) |

For items without explicit upstream ID references: constrained LLM classification pass. Must output one of `ar | ns | dialogue_continue | ambiguous`, name the affected surface, provide a one-line reason, and record `classifier_source: model`.

**Dimension independence:** `classifier_source` and `suggested_arc` are independent dimensions. `classifier_source` describes the classification *method* (deterministic rule vs. LLM judgment). `suggested_arc` describes the routing *outcome* (where the item should go). `ambiguous` is a valid outcome (`suggested_arc = ambiguous` means the router could not determine a clear destination) but not a valid method — every classification is performed by either a rule or the model.

**Consumer behavior for `ambiguous` items:**

`ambiguous` items enter the materiality gate like any other item. Their routing behavior depends on the materiality result:

| Condition | Behavior |
|-----------|----------|
| `material: false` + `suggested_arc: ambiguous` | Informational only. Reported to user but does not surface as a routing decision. No hop suggested. |
| `material: true` + `suggested_arc: ambiguous` | Manual routing bucket. User is presented three actions: (1) send to adversarial-review, (2) send to next-steps, (3) hold. Default is **hold** — no hop occurs, no budget consumed. |

**Disambiguation guidance:** If the ambiguity is "need more evidence before knowing which surface owns this item," the correct `suggested_arc` is `dialogue_continue` (same dialogue, still gathering evidence), not `ambiguous`. Use `ambiguous` only when the item is material but it is genuinely unclear whether diagnosis or planning owns the resolution.

### Affected-Surface Validity Check

After routing classification and materiality evaluation, `dialogue` validates the final tuple `(affected_surface, material, suggested_arc)` against a validity matrix. This check prevents invalid routing combinations from silently passing through.

| `affected_surface` | `material` | Valid `suggested_arc` values |
|--------------------|------------|------------------------------|
| `diagnosis` | `true` | `adversarial-review`, `ambiguous` |
| `planning` | `true` | `next-steps`, `ambiguous` |
| `evidence-only` | `true` | `dialogue_continue` |
| `diagnosis` | `false` | `dialogue_continue`, `ambiguous` |
| `planning` | `false` | `dialogue_continue`, `ambiguous` |
| `evidence-only` | `false` | `dialogue_continue` |

**Correction rules** (deterministic, ordered):
1. If `material = false` → `dialogue_continue`
2. If `affected_surface = evidence-only` → `dialogue_continue`
3. Otherwise → `ambiguous` (manual routing bucket with `hold` default)

Corrected outcomes record `classifier_source: rule`. **Consequence prohibitions:** `diagnosis` MUST NOT emit `next-steps`; `planning` MUST NOT emit `adversarial-review`; `evidence-only` MUST NOT emit AR, NS, or `ambiguous`; material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue`.

See composition contract §9.6 for normative specification.

### Material-Delta Gating

Evaluate materiality using three tiers with a cross-tier guard. Tier 1 rule-based exclusions are final. Tier 1 model-judged exclusions are provisional — they must pass through Tier 2 before finalizing.

**Pre-check — Novelty veto:**

Before Tier 1, check whether the item introduces any new content relative to the source snapshot: a new failure mode, causal mechanism, consequence, dependency, gate effect, or contradiction. If the item introduces novel content, Tier 1 MUST return `no_match` regardless of exclusion class fit. Proceed directly to Tier 2.

Rationale: items with novel content can pattern-match Tier 1 exclusion classes (e.g., a novel architectural consequence might look like an "implementation detail") but should never be pre-screened out. The novelty veto prevents this class of false negatives.

**Tier 1 — Pre-screening exclusions (closed v1 set):**

An item is **provisionally not material** if any of these apply (and the novelty veto did not fire):
- An exact restatement or example of an existing item in the source snapshot
- An open question already present in the source snapshot
- A clearly unsupported tangent with no affected upstream refs

This is a closed set for v1. Do not add exclusion classes without updating this list.

Set `materiality_source: rule` when the exclusion is clear-cut; set `materiality_source: model` with a one-line reason when it required interpretation.

**Cross-tier guard:** If the Tier 1 match used model judgment (`materiality_source: model`), the exclusion is provisional. Check Tier 2 before finalizing:
- If Tier 2 would include the item → Tier 2 takes precedence. Set `material: true`, `materiality_source: rule`.
- If Tier 2 does not match → the Tier 1 model exclusion stands. Set `material: false`.

If the Tier 1 match used rule judgment (`materiality_source: rule`), the exclusion is final. Skip Tiers 2-3.

**Tier 2 — Rule-based inclusions (deterministic):**

An item is **material** if any of:
- Crosses an action threshold: assumption status → `wishful`, finding severity → `blocking`/`high`, task → on/off critical path, decision gate → changed branch outcome

If Tier 2 matches, the item is material. Set `material: true`, `materiality_source: rule`. Skip Tier 3.

**Deferred from v1:** "Reopens or contradicts something previously resolved" removed from Tier 2 — NS handoff has no explicit resolved-item set, making this branch unreachable from `dialogue`'s direct source snapshot. See composition contract §9.4 deferral note.

**NS handoff schema enrichment (2026-03-20):** To close cross-schema reachability gaps where §9.4 and §9.1 reference AR capsule fields not present in the NS handoff, Appendix B now includes `source_assumptions: SourceAssumption[]` and `source_open_questions: string[]`. These follow the existing `source_findings` selective forwarding pattern. B.3 Forwarding Rules govern population semantics. The composition contract §9 header now includes an explicit reachability rule: deterministic clauses MUST be evaluable from the direct source snapshot; MUST NOT read through to transitive upstream capsules.

**Tier 3 — Semantic evaluation (model fallback):**

If neither Tier 1 nor Tier 2 matched (or if Tier 1 returned `no_match` due to the novelty veto), evaluate using judgment:
- Does the item introduce a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface?
- Does it introduce a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface?
- Is this an implementation detail below the current abstraction level? (Moved from Tier 1 — this criterion requires too much judgment for pre-screening.)

Set `materiality_source: model`. Provide a one-line `materiality_reason`.

**Note:** `materiality_source` is a separate dimension from `classifier_source`. `classifier_source` describes the routing classification method (for `suggested_arc`). `materiality_source` describes the materiality evaluation method. Do not conflate them.

### Guardrails

1. **No auto-chaining.** Skills suggest the next arc; the user confirms. No skill auto-invokes another.
2. **Material-delta gating.** Do not recommend a hop unless something changed relative to the source snapshot.
3. **Soft iteration budget.** After 2 targeted loops in the same composition chain (same `lineage_root_id`), stop suggesting further hops automatically. Report remaining open items. User can override. The budget uses `lineage_root_id` (chain identity), not `topic_key` (descriptive) or `subject_key` (exact lineage). This ensures independent composition chains never share a budget, even if they happen to cover similar topics.

### Thread Continuation vs Fresh Start

**Hard rule: new artifact → new thread.**

Continue existing Codex thread only when ALL of:
- Same goal
- Same upstream snapshot set (no new AR or NS artifact)
- Unresolved items are evidence/clarification questions, not changed diagnosis or plan
- Prior termination was operational (budget exhaustion, scope breach resolved, interruption)

Fresh `/dialogue` with new briefing when ANY of:
- New AR snapshot exists
- New NS snapshot exists
- Posture or focus changed materially
- Selected task/gate set changed

Never inject updated AR/NS artifacts into an existing Codex thread. Once diagnosis or planning has changed, the old conversation state is stale.

### Selective Durable Persistence

**Decision (2026-03-20):** Only `dialogue_feedback` gets durable persistence. AR→NS and NS→dialogue arcs remain conversation-local in v1.

**Rationale:** The feedback arc (dialogue → AR/NS) is the only composition path that reliably crosses invocation boundaries. AR→NS and NS→dialogue happen in rapid sequence within a single session. Dialogue feedback may be consumed hours or sessions later.

| Arc | Transport | Persistence |
|-----|-----------|-------------|
| AR → NS | Conversation-local (sentinel scan) | None |
| NS → Dialogue | Conversation-local (sentinel scan) | None |
| Dialogue → AR/NS (feedback) | Conversation-local + durable file | `.claude/composition/feedback/` (gitignored) |

**Source resolution precedence** (composition contract §8.1b):
1. Explicit reference (artifact ID provided by user or upstream)
2. Durable store (`.claude/composition/feedback/`)
3. Conversation-local (sentinel scan of visible context)

The durable file uses the same wire format as the conversation capsule. `record_path` in the dialogue feedback capsule MUST be non-null and MUST point to the durable file (composition contract Appendix C constraint).

---

## Lineage Model

### Artifact identity

An artifact is one skill-run snapshot. The capsule is the machine-readable projection of that artifact — not a separate entity.

| Skill run | Artifact kind |
|-----------|--------------|
| One adversarial-review run | `adversarial_review` |
| One next-steps run | `next_steps_plan` |
| One /dialogue run | `dialogue_feedback` |

### Three identity keys

Each artifact carries three identity keys serving different purposes:

| Key | Purpose | Format | Example | Used by |
|-----|---------|--------|---------|---------|
| `subject_key` | Exact lineage matching (staleness, supersession) | kebab-case, deterministic from target | `redaction-pipeline` | Staleness detection, `supersedes` links |
| `topic_key` | Non-authoritative descriptive metadata for UX, summaries, and analytics | kebab-case, broader than subject_key | `redaction-pipeline` | Display only; NOT a control key |
| `lineage_root_id` | Budget isolation — identifies the composition chain | The root artifact's `artifact_id`, copied unchanged | `ar:redaction-pipeline:20260318T143052.123` | Soft iteration budget guardrails |

`subject_key` and `topic_key` may be identical for simple targets. They diverge when a subject is a specific facet of a broader topic (e.g., subject_key `redaction-format-layer` under topic_key `redaction-pipeline`). `lineage_root_id` is always distinct from the other keys — it is a full `artifact_id`, not a kebab-case string.

**Normalization rules for `subject_key` (exact key — minimally lossy):**
- Lowercase, replace spaces/underscores with hyphens
- Remove leading/trailing whitespace
- No character limit — preserve full target specificity for exact lineage matching
- Derived from the skill's basis field when minting, or inherited from upstream capsule

**Normalization rules for `topic_key` (descriptive — non-authoritative):**
- Same base normalization as `subject_key`
- Additionally: strip articles (a, an, the), trailing qualifiers, and implementation-specific suffixes
- Limit to 50 characters, truncate at word boundary
- Represents the broadest topic this analysis belongs to
- `topic_key` is descriptive metadata for UX and analytics. It is NOT used for budget enforcement or any control decisions. Collisions between independent chains sharing the same `topic_key` are harmless because budget tracks by `lineage_root_id`.
- **Optionality recommendation:** Both evaluative and exploratory Codex dialogues recommended making `topic_key` optional in v1 — no consumer uses it for control decisions, and it can be derived from `subject_key` when needed. The composition contract currently includes it as required in all appendices; consider relaxing to optional in a future contract amendment.

**`lineage_root_id` propagation:**
- When a skill is the root of a composition chain (no upstream capsule consumed), set `lineage_root_id` to this artifact's own `artifact_id`.
- When a skill consumes an upstream capsule, copy `lineage_root_id` unchanged from that capsule.
- `lineage_root_id` is immutable within a chain — it is never re-minted downstream. This guarantees that all artifacts in a single composition chain share the same `lineage_root_id`, while independent chains have different values by construction.
- `lineage_root_id` serves budget isolation only, not freshness detection or staleness — those are separate concerns handled by `subject_key` and `supersedes`.

**Inheritance-first propagation (subject_key, topic_key):**
- If a skill directly consumes an upstream capsule (any kind), it inherits both `subject_key` and `topic_key` from that capsule.
- If no upstream capsule is directly consumed, the skill mints both keys from its own basis field (see table below).
- **Rule:** Only the root of a composition chain mints keys. All downstream skills inherit. This eliminates cross-skill key drift.

**Basis fields for key minting (when no upstream capsule is consumed):**

| Skill | Basis field | Example |
|-------|-------------|---------|
| adversarial-review | `review_target` | "the redaction pipeline" → `redaction-pipeline` |
| next-steps | Primary topic of the plan | "redaction pipeline remediation" → `redaction-pipeline-remediation` |
| dialogue | Goal/question topic | "redaction pipeline architecture" → `redaction-pipeline-architecture` |

**Examples of inheritance in the feedback loop:**
- AR (standalone) → mints `subject_key: redaction-pipeline`, sets `lineage_root_id: ar:redaction-pipeline:20260318T143052.123`
- NS (consumes AR capsule) → inherits `subject_key: redaction-pipeline`, inherits `lineage_root_id: ar:redaction-pipeline:20260318T143052.123`
- Dialogue (consumes NS handoff) → inherits both keys unchanged
- AR (re-review consuming dialogue feedback capsule) → inherits both keys unchanged — same `lineage_root_id` throughout

### Artifact ID format

```
<kind-prefix>:<subject_key>:<created_at_compact>
```

Where `created_at_compact` is the `created_at` value with separators removed: `YYYYMMDDTHHMMSS.sss` (always 3 fractional digits). All three skills MUST use millisecond precision. Pad `.000` if only second-level precision is available from the runtime; truncate to milliseconds if higher precision is provided.

Examples:
- `ar:redaction-pipeline:20260318T143052.123`
- `ns:redaction-pipeline:20260318T144215.456`
- `dialogue:redaction-pipeline:20260318T151033.789`

**Artifact ID prefixes:** `ar:` (adversarial_review), `ns:` (next_steps_plan), `dialogue:` (dialogue_feedback).

The timestamp component provides collision resistance derived from the full `created_at` precision. Two runs on the same subject at different times produce different artifact IDs. The sequence-based format (`:<01>`) is removed — timestamps are strictly more unique.

### DAG structure

Two edge types:

| Edge | Connects | Purpose |
|------|----------|---------|
| `supersedes` | Same-kind, same-subject artifacts | Version chain within one artifact family |
| `source_artifacts[]` | Cross-kind artifacts | Provenance graph showing what this run consumed |

Each `source_artifacts[]` entry includes `artifact_id`, `artifact_kind`, and `role` (e.g., `diagnosis`, `plan`).

**Provenance rule:** `source_artifacts[]` records direct edges only — artifacts that this run directly parsed and validated. Transitive provenance is recovered by traversing upstream `source_artifacts[]` references. Example: dialogue's feedback capsule lists NS (direct consumer) but not AR (transitive — reached via NS's own `source_artifacts[]`).

### Artifact discovery (v1 — conversation-local)

Two distinct discovery algorithms serve different purposes within conversation-local scope. Both operate on the conversation context available to the current skill invocation.

**Consumption discovery** — used when a skill wants to consume an upstream capsule:

1. Reverse-scan the available conversation context newest-first for the expected sentinel (e.g., `<!-- ar-capsule:v1 -->`).
2. Take the first match only.
3. Validate the candidate capsule schema.
4. If invalid, reject and stop — do not backtrack to older capsules. Proceed as if no capsule exists.
5. If no sentinel is found in available context, proceed without structural handoff.

This is a single-result, no-backtrack algorithm. It finds the most recent valid capsule or nothing.

**Staleness discovery** — used to determine whether a consumed artifact has been superseded:

1. Scan the available conversation context for all valid capsules matching a given `artifact_kind` and `subject_key`.
2. Index by `artifact_id` and `created_at`.
3. Compare against the consumed artifact to detect supersession.

This is a multi-scan algorithm that may return multiple results. It requires scanning more broadly than consumption discovery.

**Scope boundary:** "Available conversation context" means the context visible to the current skill invocation. Multi-session discovery (capsules from prior conversations) is explicitly out of v1 scope.

### Staleness detection

Consuming skills detect staleness and warn the user. Evaluate in this order — the first matching status applies:

| Priority | Status | Condition | Consumer behavior |
|----------|--------|-----------|------------------|
| 1 | `superseded` | Positive evidence that a newer same-kind same-subject artifact exists in available context | Prefer the newer one |
| 2 | `unknown` | A required direct `source_artifact` is absent from available context or its capsule is unparseable | Do not block; fall back to current behavior |
| 3 | `stale_inputs` | A direct `source_artifact` has a newer visible superseder in available context | Warn; suggest rebase before continuing |
| 4 | `current` | No superseder exists; all source_artifacts are current within available context | Proceed normally |

**Must-not-infer-current rule:** Do not infer `current` from missing evidence. If a required source artifact is absent from context (it may have been compacted away, or produced in a prior session), the status is `unknown`, not `current`. `current` requires positive evidence that no superseder exists in the available context.

### File persistence

Optional. `record_path` in the capsule points to a durable file when one exists (e.g., `docs/reviews/<slug>.md` for AR). The file carries the same artifact metadata in frontmatter. The file path is a locator, not the identity — `artifact_id` is the identity.

NS does not write files today. If `docs/plans/` is added later, use the same `artifact_id` scheme rather than inventing a second identity system.

---

## Shared Composition Contract

### Three-layer authority model

The composition system distributes authority across three layers:

| Layer | Owner | Authority | Audience |
|-------|-------|-----------|----------|
| **Composition contract** | Shared reference document | Normative — protocol core that governs cross-skill semantics | Skill authors modifying composition behavior |
| **Inline stubs** (per skill) | Each participating skill | Runtime authority — role-specific operational subset | Claude during skill execution |
| **Design document** (this file) | Design author | Explanatory — rationale and tradeoff discussion | Non-normative; not loaded at runtime |

**Contract owns protocol core (normative):**
- Sentinel/version rules and unknown-version handling
- Artifact metadata schema (artifact_id, subject_key, lineage_root_id, supersedes, source_artifacts)
- Consumer class definitions (advisory/tolerant vs strict/deterministic)
- Routing classification rules and precedence
- Material-delta tier semantics (novelty veto, cross-tier guard, tier definitions)
- Budget semantics (lineage_root_id tracking, soft iteration limit)
- Staleness semantics (ordered algorithm, must-not-infer-current)
- Discovery algorithms (consumption vs staleness)
- Capsule emission rule: "same schema when externalized, no schema obligation when used as internal reasoning scaffolding"

**Stubs own role-specific operations (runtime authority):**
- What upstream capsule this skill can consume
- What downstream capsule this skill emits
- Fallback behavior when upstream capsule is absent or invalid
- Which shared semantics this skill executes (e.g., dialogue executes routing and materiality; AR and NS do not)
- When to suggest the next hop

Stub sizes are asymmetric by design — dialogue's stub is largest (routing, materiality, budget, discovery), AR and NS stubs are smaller (consume/emit with fallback). Do not target a symmetric line count.

Every skill must function correctly with only its inline stub. The contract is additive context — skill authors consult it when modifying composition behavior, but Claude does not require it at runtime.

### Versioning and drift detection

Contract versioning is a CI/review-time concern, not runtime. Each skill stub includes `implements_composition_contract: v1` as a drift detection marker. Sentinel versioning (`v1` in sentinel comments) handles runtime wire compatibility. Contract version stays out of capsule schemas.

**File location:** `packages/plugins/cross-model/references/composition-contract.md` (950 lines) — alongside the consultation contract, since all three skills interact through the cross-model dialogue system. The contract now exists and includes:

- §1-§3: Purpose, normative terms with ownership matrix, shared vocabulary
- §4: Sentinel registry (7-column machine-parseable table)
- §5-§6: Capsule externalization rule, artifact metadata with DAG semantics and durable persistence for `dialogue_feedback`
- §7-§8: Consumer classes, discovery and staleness semantics with source resolution pre-step
- §9: Routing, materiality (with §9 reachability rule), budget rules, affected-surface validity matrix (§9.6)
- §10-§12: Thread freshness, governance locks (4), conformance and drift detection
- Appendices A-C: AR capsule, NS handoff (with `source_assumptions`, `source_open_questions`, B.3 Forwarding Rules), dialogue feedback field inventories

**Inverted authority model:** Unlike the consultation contract (which IS runtime-loaded), the composition contract is NOT. Stubs carry the runtime projection. Contract→stub drift is a silent correctness bug detectable only by CI (§12).

---

## Skill Text Summary

| Skill | Changes required |
|-------|-----------------|
| **adversarial-review** | Add AR capsule emission (with `lineage_root_id`) after prose output. Add `/next-steps` suggestion. Inline composition stub (small — consume feedback capsule, emit AR capsule, fallback behavior, hop suggestion). |
| **next-steps** | Add AR capsule consumption (advisory/tolerant). Add NS handoff block emission when suggesting dialogue. Inline composition stub (small — consume AR capsule, emit NS handoff, fallback behavior, hop suggestion). |
| **dialogue** | Add two-stage admission (Stage A: sentinel detection + validation, Stage B: normalize to `upstream_handoff` with capability flags). Add `handoff_enriched` decomposition mode. Thread `upstream_handoff` through Steps 2-3 via capability flags. Add feedback capsule emission after synthesis. Add routing classification + materiality evaluation. Inline composition stub (large — routing, materiality, budget, discovery, consume/emit, fallback). |
| **Shared contract** | New file: composition contract owning protocol core (sentinel/version rules, artifact metadata, consumer classes, routing, material-delta, budget, staleness, discovery). |

---

## Open Items

1. ~~**Soft echo filter specification**~~: Resolved — examples added to tier 3 (2026-03-19).
2. **Composition contract file location**: Resolved — file exists at `packages/plugins/cross-model/references/composition-contract.md` (950 lines, 12 sections + 3 appendices). Inverted authority model: stubs are runtime-authoritative, contract is authoring-authoritative. CI is the only drift detection mechanism (§12).
3. **upstream_handoff version field**: Deferred — sentinel versioning (`v1`) provides forward-compatibility. Version field adds no value until v2 exists.
4. **codex-dialogue synthesis format**: Resolved — no changes needed. `/dialogue` projects feedback capsule from existing Synthesis Checkpoint output.
5. **Tier 2 "reopens/contradicts previously resolved"**: Deferred from v1 — requires a direct resolved-item input surface in `dialogue`'s source snapshot. NS handoff has no explicit resolved-item set. See composition contract §9.4 deferral note.
6. **CI enforcement of composition contract drift rules**: Not yet implemented — §12 specifies drift markers and CI rules, but no `validate_composition_contract.py` script exists. The consultation contract's checker (`validate_consultation_contract.py`) is the structural precedent.
7. **Materiality validation harness**: Designed (T4 dialogue) but not yet implemented — 12 executable §9.4 fixtures, 24-case §9.6 exhaustive table, clause dependency manifest, Tier 3 calibration suite (6 minimal pairs).

## Cross-Model Validation

Architecture validated via Codex collaborative dialogue (thread `019d0284-a997-7ce2-8dbc-8d344c589de2`, 5 turns + 3 continuation turns). 11 items resolved, 3 emerged concepts integrated into design. All design decisions reached high-confidence convergence.

**Design review amendments (2026-03-19):** System design review surfaced 7 findings (F1-F7) and 2 tensions (T1-T2). Codex collaborative dialogue (thread `019d0682-3f52-70a1-b7ed-e536ad2b8652`, 5 turns) resolved all findings. Key amendments: split-field identity model (F3 emerged concept), direct-edge provenance (F2), classifier dimension separation (F4), inline-stub authority model (F6). ~~F1 closed by counter-evidence (pipeline steps are the public contract)~~ F1 reopened by second-pass review — see below. F5/F7 accepted as v1 tradeoffs.

**Second-pass review amendments (2026-03-19):** Second-pass system design review surfaced 7 findings (F1-F7) and 1 tension (T1). Codex evaluative dialogue (thread `019d0728-c61a-7c03-b67c-f13512cd3d85`, 6 turns) resolved all findings. Key amendments: F1 reopened — advisory fallback diagnostic added, invalid SS2 claim removed; F3 canonical millisecond precision; F4 material-delta tiered into ordered evaluation; D1 reframed to "standalone-first, protocol-rich composition." F2/F7 accepted with low-cost fixes. F5/F6 deferred. Emerged: `ar_input_mode` degradation field (deferred), `materiality_source` field (integrated into tiered material-delta), v1 scope narrowing option (declined — full v1 confirmed).

**Third-pass review amendments (2026-03-19):** System design review surfaced 6 findings (F1-F6) and 2 tensions (T1-T2). Codex collaborative dialogue (thread `019d091b-5077-7672-8a16-1dd46aca7894`, 6 turns) resolved all findings. Key amendments:
- F3 (HIGH): Cross-tier guard with novelty veto — provisional Tier 1 model exclusions must survive Tier 2; items with novel content bypass Tier 1 entirely; "implementation detail" moved to Tier 3; closed v1 exclusion set.
- F1: Two-stage adapter pattern — generic `upstream_handoff` state with capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`); v1 producer set NS-only; "adapters not modes" extensibility.
- F4+T2: Discovery algorithms — two distinct algorithms (consumption: single, no-backtrack; staleness: multi-scan); ordered staleness evaluation (superseded > unknown > stale_inputs > current); must-not-infer-current rule.
- F6: `lineage_root_id` — first-class schema field for budget isolation; `topic_key` demoted to descriptive metadata; budget tracks by `lineage_root_id` not `topic_key`.
- F5/T1: Three-layer authority model — contract owns protocol core (normative), stubs own role-specific operations (runtime authority), design doc owns rationale (explanatory); asymmetric stub sizes; CI-enforced versioning.
- F2: Ambiguous routing — manual routing bucket gated on `material=true`; hold default; `dialogue_continue` vs `ambiguous` distinction clarified.
- Emerged: novelty veto, capability flags on `upstream_handoff`, `lineage_root_id`, two distinct discovery algorithms.

**Fourth-pass: System design review and composition contract (2026-03-20):** System design review (8 deep lenses) surfaced 7 findings (3 high-priority) and 2 tensions. Evaluative Codex dialogue (thread `019d0966-0746-7c13-88bd-7c07fc17ab19`, 6/12 turns, converged) produced split verdict: architecture 3/5 (sound), implementation 2/5 (7 hard gates before coding). Key emerged concepts: route/materiality coherence gap, persistence requirement for feedback loop, authority vacuum risk. Exploratory Codex dialogue (thread `019d0989-3af1-7e23-b2b6-79d5ef94513e`, 5+3 turns, converged) drafted the composition contract (12 sections + 3 appendices) with inverted authority model: stubs are runtime-authoritative, contract is authoring-authoritative. Key decisions: selective durable persistence for `dialogue_feedback` only (§6), affected-surface validity matrix (§9.6), source resolution pre-step (§8.1b).

Exploratory Codex dialogue (thread `019d09cf-c967-7f73-bb33-f4e1fa419411`, 6 turns, converged) designed materiality validation harness: hybrid approach (behavioral tests + structural checker with clause dependency manifest + deferred golden fixtures), 12 executable §9.4 fixtures, exhaustive 24-case §9.6 table. Discovered 4 cross-schema reachability gaps where §9.4 and §9.1 reference AR capsule fields not present in NS handoff. Collaborative continuation (same thread, turns 7-9, converged) resolved all 4 gaps: gaps 1, 2, 4 via NS handoff schema enrichment (`source_assumptions`, `source_open_questions`); gap 3 (Tier 2 "reopens previously resolved") deferred from v1. Contract amendments: §9 reachability rule, §9.4 Tier 2 deferral, Appendix B enrichment + B.3 Forwarding Rules. Contract now 950 lines.
