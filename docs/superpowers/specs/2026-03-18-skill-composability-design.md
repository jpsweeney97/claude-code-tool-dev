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
- File-based persistence requirements (conversation-local is sufficient for v1)
- Changes to the global CLAUDE.md protocols (Adversarial Self-Review, Next Steps Planning remain independent behaviors)

## Design Decisions

### D1: Composability model is thin structural overlay

Each skill remains fully standalone and human-usable. Composition is additive — structured capsules and sentinels are appended to or alongside existing prose output. No skill requires upstream context to function.

**Alternatives considered:**
- **Observational only** (document the implicit format mapping, no structural changes): Too brittle — finding identity breaks, severity carry-forward is unreliable from prose parsing.
- **Full protocol** (formal schemas with validation, required fields): Over-couples skills, pushes AR toward remediation logic, violates standalone principle.
- **Orchestrator meta-skill**: Over-engineers a 3-skill pipeline. Revisit if pipeline grows beyond these skills.

### D2: Two consumer classes

| Class | Behavior | Used by |
|-------|----------|---------|
| Advisory/tolerant | Validate if capsule present; fall back to prose parsing if absent or invalid | NS consuming AR capsule |
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
topic_key: <coarse grouping key — same as subject_key unless reviewing a facet of a broader topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
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
topic_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
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

The NS handoff threads through the full `/dialogue` pipeline, not just Step 0:

| Pipeline stage | How handoff is consumed |
|----------------|----------------------|
| Pre-Step 0 | Parse sentinel → normalize to `upstream_handoff` pipeline state |
| Step 0 (`handoff_enriched` mode) | Seed decomposition: planning_question from focus_question + done_when; assumptions from source_findings; key_terms from task context entities |
| Step 2 | Gatherer seeds enriched with task names, finding entities, decision gate conditions |
| Step 3 | Deterministic projection of source_findings and decision_gates into briefing Context section |
| Step 3c | Zero-output fallback preserves upstream context as sole grounding |

### Posture precedence

```
explicit --posture > --profile > NS recommended_posture > default collaborative
```

NS does not derive multi-phase profiles from a single posture hint. If future handoff-driven phases are needed, NS would emit `recommended_phases[]`.

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
topic_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
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
```

Note: `classifier_source` narrowed to `rule | model` (no `ambiguous`).

---

## Adaptive `--plan` (Two Decomposition Modes)

### Mode selection

| Condition | Mode | Behavior |
|-----------|------|----------|
| `--plan` set, no NS handoff detected | `raw_input` | Current behavior — decompose from user's question |
| `--plan` set AND `<!-- next-steps-dialogue-handoff:v1 -->` detected | `handoff_enriched` | Seed decomposition from task context, findings, decision gates |
| `--plan` not set, NS handoff present | N/A | Handoff state available to later steps (gatherer seeds, briefing assembly) but no decomposition runs |
| `--plan` not set, no NS handoff | N/A | Current behavior unchanged |

### Enriched decomposition seeding

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

### Material-Delta Gating

An item is **material** if any of:
- Introduces a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface
- Introduces a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface
- Reopens or contradicts something previously RESOLVED
- Crosses an action threshold: assumption status → `wishful`, finding severity → `blocking`/`high`, task → on/off critical path, decision gate → changed branch outcome

An item is **not material** if only:
- A restatement or example of an existing item
- An implementation detail below the current abstraction level
- A low-support idea with no affected upstream refs
- An open question already present in the source snapshot

### Guardrails

1. **No auto-chaining.** Skills suggest the next arc; the user confirms. No skill auto-invokes another.
2. **Material-delta gating.** Do not recommend a hop unless something changed relative to the source snapshot.
3. **Soft iteration budget.** After 2 targeted loops in the same topic (same `topic_key`), stop suggesting further hops automatically. Report remaining open items. User can override. The budget uses `topic_key` (coarse grouping), not `subject_key` (exact lineage), so related reviews on different facets of the same topic share a budget.

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

---

## Lineage Model

### Artifact identity

An artifact is one skill-run snapshot. The capsule is the machine-readable projection of that artifact — not a separate entity.

| Skill run | Artifact kind |
|-----------|--------------|
| One adversarial-review run | `adversarial_review` |
| One next-steps run | `next_steps_plan` |
| One /dialogue run | `dialogue_feedback` |

### Two identity keys

Each artifact carries two identity keys serving different purposes:

| Key | Purpose | Format | Example | Used by |
|-----|---------|--------|---------|---------|
| `subject_key` | Exact lineage matching (staleness, supersession) | kebab-case, deterministic from target | `redaction-pipeline` | Staleness detection, `supersedes` links |
| `topic_key` | Coarse grouping (soft iteration budget) | kebab-case, broader than subject_key | `redaction-pipeline` | Loop guardrails only |

For simple targets, `subject_key` and `topic_key` may be identical. They diverge when a subject is a specific facet of a broader topic (e.g., subject_key `redaction-format-layer` under topic_key `redaction-pipeline`).

**Normalization rules for `subject_key` (exact key — minimally lossy):**
- Lowercase, replace spaces/underscores with hyphens
- Remove leading/trailing whitespace
- No character limit — preserve full target specificity for exact lineage matching
- Derived from the skill's basis field when minting, or inherited from upstream capsule

**Normalization rules for `topic_key` (coarse key — grouping):**
- Same base normalization as `subject_key`
- Additionally: strip articles (a, an, the), trailing qualifiers, and implementation-specific suffixes
- Limit to 50 characters, truncate at word boundary
- Represents the broadest topic this analysis belongs to

**Inheritance-first propagation:**
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
- AR (standalone) → mints `redaction-pipeline`
- NS (consumes AR capsule) → inherits `redaction-pipeline`
- Dialogue (consumes NS handoff) → inherits `redaction-pipeline`
- AR (re-review consuming dialogue feedback capsule) → inherits `redaction-pipeline`

### Artifact ID format

```
<kind-prefix>:<subject_key>:<created_at_compact>
```

Where `created_at_compact` is the `created_at` ISO 8601 value with separators removed: `YYYYMMDDTHHMMSS` at minimum, with fractional seconds appended when the `created_at` field includes them (e.g., `YYYYMMDDTHHMMSS.fff`). The timestamp component MUST preserve the full precision of the `created_at` field — do not truncate fractional seconds. All three skills MUST use the same precision.

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

### Staleness detection

Consuming skills detect staleness and warn the user:

| Status | Condition | Consumer behavior |
|--------|-----------|------------------|
| `current` | No superseder exists; all source_artifacts are current | Proceed normally |
| `superseded` | A newer same-kind same-subject artifact exists | Prefer the newer one |
| `stale_inputs` | One or more source_artifacts has been superseded | Warn; suggest rebase before continuing |
| `unknown` | Insufficient lineage metadata | Do not block; fall back to current behavior |

### File persistence

Optional. `record_path` in the capsule points to a durable file when one exists (e.g., `docs/reviews/<slug>.md` for AR). The file carries the same artifact metadata in frontmatter. The file path is a locator, not the identity — `artifact_id` is the identity.

NS does not write files today. If `docs/plans/` is added later, use the same `artifact_id` scheme rather than inventing a second identity system.

---

## Shared Composition Contract

A thin reference document (~50-80 lines) loaded by all participating skills. Governs:

- Artifact metadata schema (artifact_id, subject_key, supersedes, source_artifacts)
- Capsule sentinel formats and version handling
- Consumer class definitions (advisory/tolerant vs strict/deterministic)
- Routing classification rules and precedence
- Material-delta definitions
- Staleness detection rules
- Capsule emission rule: "same schema when externalized, no schema obligation when used as internal reasoning scaffolding"

Each skill gets a short self-contained stub referencing the contract:
- What upstream capsule it can consume
- What downstream capsule it emits
- When to suggest the next hop

**File location:** `packages/plugins/cross-model/references/composition-contract.md` — alongside the consultation contract, since all three skills interact through the cross-model dialogue system.

---

## Skill Text Summary

| Skill | Changes required |
|-------|-----------------|
| **adversarial-review** | Add AR capsule emission after prose output. Add `/next-steps` suggestion. Add composition contract stub. |
| **next-steps** | Add AR capsule consumption (advisory/tolerant). Add NS handoff block emission when suggesting dialogue. Add composition contract stub. |
| **dialogue** | Add NS handoff detection and `upstream_handoff` pipeline state. Add `handoff_enriched` decomposition mode to Step 0. Thread handoff through Steps 2-3. Add dialogue feedback capsule emission after synthesis. Add routing classification. Add composition contract stub. |
| **Shared contract** | New file: composition contract governing artifact schemas, consumer classes, routing, staleness. |

---

## Open Items

1. **Soft echo filter specification**: Exact validation rule distinguishing "source-finding parrot" from legitimate source-finding-derived assumption in the tautology filter.
2. **Composition contract file location**: Alongside consultation contract or separate shared location.
3. **upstream_handoff version field**: Whether to include a version field for forward-compatibility with future handoff schemas.
4. **codex-dialogue synthesis format**: Whether the agent's existing Synthesis Checkpoint output needs any changes to support capsule derivation (likely no — `/dialogue` can project from existing output).

## Cross-Model Validation

Architecture validated via Codex collaborative dialogue (thread `019d0284-a997-7ce2-8dbc-8d344c589de2`, 5 turns + 3 continuation turns). 11 items resolved, 3 emerged concepts integrated into design. All design decisions reached high-confidence convergence.
