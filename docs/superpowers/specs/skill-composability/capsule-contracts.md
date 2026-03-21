---
module: capsule-contracts
status: active
normative: true
authority: capsule-contract
---

# Capsule Contracts

Three capsule contracts define the inter-skill data exchange format. Each contract specifies a sentinel, schema, consumer class, and emission rules. For identity key semantics used in capsule schemas, see [lineage.md](lineage.md#three-identity-keys). For how dialogue processes the NS handoff, see [pipeline-integration.md](pipeline-integration.md#two-stage-admission).

## Sentinel Registry

| Sentinel | Producer | Consumer | Consumer Class |
|----------|----------|----------|----------------|
| `<!-- ar-capsule:v1 -->` | adversarial-review | next-steps | Advisory/tolerant |
| `<!-- next-steps-dialogue-handoff:v1 -->` | next-steps | dialogue | Strict/deterministic |
| `<!-- dialogue-feedback-capsule:v1 -->` | dialogue | adversarial-review, next-steps | Advisory/tolerant |

`<!-- dialogue-orchestrated-briefing -->` is a distinct sentinel meaning "/dialogue already assembled the full Codex briefing." This sentinel is emitted by dialogue for internal pipeline tracking only. No external consumers in v1 — no schema, consumer class, or behavior contract is defined. Documented here to prevent future misuse. The NS handoff sentinel is input to dialogue's pipeline, not a replacement. The NS sentinel never reaches codex-dialogue.

### Unknown Version Behavior

When a consumer encounters a sentinel with an unrecognized version (e.g., `<!-- ar-capsule:v2 -->` when only `v1` is known): reject the capsule block, not the skill session. A version mismatch prevents capsule consumption but does not break the skill invocation. The consumer proceeds as if no capsule exists, applying its consumer class fallback behavior (see [foundations.md](foundations.md#consumer-classes)).

## Contract 1: AR → NS (AR Capsule)

### Purpose

Give NS stable, machine-referenceable access to AR findings without requiring prose parsing. Preserves AR's principle of separating diagnosis from remediation.

### Consumer Class

Advisory/tolerant. NS validates the capsule if present; falls back to prose parsing if absent or invalid.

**Provenance in fallback:** When NS falls back to prose parsing (capsule absent or invalid), the NS handoff MUST omit `source_artifacts` entries for the absent capsule. Do not reference an AR `artifact_id` that was not structurally consumed. This preserves lineage integrity — downstream consumers can trust that `source_artifacts` entries represent structurally validated provenance, not prose-derived references.

### Emission

AR appends the capsule after its prose output (after the Confidence Check section). The capsule is always emitted — it costs nothing to produce and NS can ignore it.

### Schema

```yaml
artifact_id: ar:<subject_key>:<created_at_compact>
artifact_kind: adversarial_review
subject_key: <kebab-case derived from review_target, or inherited from upstream feedback capsule>
topic_key: <optional — non-authoritative descriptive metadata; omit or set equal to subject_key when not needed>
lineage_root_id: <this artifact's artifact_id if standalone; inherited unchanged from upstream capsule if consuming one>
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
assumptions:
  - assumption_id: A1
    text: <assumption text>
    status: validated | plausible | wishful
    if_wrong: <one-sentence consequence>
open_questions:
  - <question text>
```

### Design Notes

- **Finding IDs are snapshot-scoped.** `finding_id` is a machine reference within one review run. The `artifact_id` provides snapshot identity. Cross-run remapping is not normative — a materially changed review forces NS to rebase.
- **`if_wrong` preserves diagnostic mechanism** without crossing into remediation. AR says "if this assumption fails, X breaks" — NS decides what to do about it.
- **Excludes task decomposition, dependency maps, or sequencing.** These are NS's domain.

## Contract 2: NS → Dialogue (NS Handoff Block)

### Purpose

Give dialogue's `--plan` flag structured task context, dependencies, originating findings, and decision gates — enabling enriched decomposition instead of starting from scratch.

### Consumer Class (Contract 2)

Strict/deterministic. Dialogue rejects an invalid handoff block but continues its normal pipeline (gatherers, briefing assembly, delegation). It does not fall back to a different data source.

**Validity criteria:** A handoff block is invalid if: (1) any required field (`artifact_id`, `artifact_kind`, `lineage_root_id`, `created_at`, `subject_key`, `focus_question`, `selected_tasks`) is absent or not well-typed, (2) `artifact_kind` is not `next_steps_plan`, or (3) `selected_tasks` is present but empty. Missing optional fields (`topic_key`, `recommended_posture`, `source_findings`, `source_assumptions`, `source_open_questions`, `out_of_scope`, `decision_gates`) do not invalidate the capsule.

### Emission (Contract 2)

NS emits one handoff block when it suggests `/dialogue`. The block's `selected_tasks[]` list contains the tasks recommended for this dialogue invocation — typically the highest-risk task or recommended first move. One block per NS run, not one block per task.

### Schema

```yaml
artifact_id: ns:<subject_key>:<created_at_compact>
artifact_kind: next_steps_plan
subject_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
topic_key: <optional — non-authoritative descriptive metadata; inherited from AR capsule if consumed, otherwise derived or omitted>
lineage_root_id: <inherited from AR capsule if consumed; otherwise this artifact's artifact_id>
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
source_assumptions:
  - assumption_id: A1
    text: <assumption text>
    status: validated | plausible | wishful
    if_wrong: <one-sentence consequence>
source_open_questions:
  - <question text>
out_of_scope:
  - <parked item>
```

### Forwarding Rules

`source_findings`, `source_assumptions`, and `source_open_questions` follow the same selective forwarding pattern:

- **When AR capsule was consumed:** Selectively forward items relevant to the selected tasks. Not a full copy — include only items that inform the dialogue's focus question.
- **When no AR capsule was consumed:** All three fields are empty arrays.
- **Reachability guarantee:** These fields close cross-schema reachability gaps where [routing](routing-and-materiality.md#routing-classification) and [materiality](routing-and-materiality.md#material-delta-gating) rules reference AR capsule fields. Deterministic routing and materiality clauses MUST be evaluable from the direct source snapshot (the NS handoff); they MUST NOT read through to transitive upstream capsules. When no NS handoff is consumed (standalone dialogue invocation), this guarantee is vacuously satisfied — there is no transitive upstream chain. Routing and materiality evaluate items against conversation context only.

## Contract 3: Dialogue Feedback Capsule

### Purpose

Enable iterative refinement by giving AR and NS structured access to dialogue outcomes — what was resolved, what emerged, and what needs re-review or replanning.

### Consumer Class (Contract 3)

Advisory/tolerant. AR and NS validate the feedback capsule if present; fall back to conversation context if absent or invalid.

### Emission (Contract 3)

The `/dialogue` skill (not the codex-dialogue agent) appends the feedback capsule after presenting the synthesis to the user. Derived from the existing Synthesis Checkpoint output — not a new parallel format.

### Schema

```yaml
artifact_id: dialogue:<subject_key>:<created_at_compact>
artifact_kind: dialogue_feedback
subject_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
topic_key: <optional — non-authoritative descriptive metadata; inherited from NS handoff if consumed, otherwise derived or omitted>
lineage_root_id: <inherited from NS handoff if consumed; otherwise this artifact's artifact_id>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior dialogue artifact_id for this subject_key, or null>
source_artifacts:  # Direct edges only — AR artifact excluded per provenance rule ([lineage.md](lineage.md#dag-structure))
  - artifact_id: <NS artifact_id if handoff was consumed>
    artifact_kind: next_steps_plan
    role: plan
record_path: <path to .claude/composition/feedback/ file — MUST be non-null>
record_status: <ok | write_failed — MUST always be present; set to ok on successful write, write_failed when durable file write fails>

thread_id: <Codex thread ID>
thread_created_at: <ISO 8601, UTC, millisecond precision — when the Codex thread was established; used as the comparison baseline for thread continuation checks (see [routing-and-materiality.md](routing-and-materiality.md#thread-continuation-vs-fresh-start))>
converged: <true | false>
turn_count: <int>

resolved:
  - item_id: R1
    text: <what was resolved>
    confidence: high | medium | low
unresolved:
  - item_id: U1
    text: <what remains open>
    hold_reason: <routing_pending | null — set to routing_pending when item was held from ambiguous routing prompt (see [routing-and-materiality.md](routing-and-materiality.md#ambiguous-item-behavior)); null or omitted for items unresolved for other reasons>
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

### Schema Constraints

- **`material`/`suggested_arc` coherence:** The [affected-surface validity matrix and correction rules](routing-and-materiality.md#affected-surface-validity) (normative authority: routing-and-materiality) are the single source of truth for valid tuples in the emitted wire format. Capsules MUST be emitted in their post-correction state.
- **`record_status` semantics:** See [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) for the normative write-failure recovery procedure, consumer-side contract, and enforcement rules. `record_status` MUST always be present (`ok` or `write_failed`).

### Design Notes

- `classifier_source` is narrowed to `rule | model` — no `ambiguous` value. Every classification is performed by either a rule or the model.
- `record_path` MUST be non-null for feedback capsules. See [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence).
