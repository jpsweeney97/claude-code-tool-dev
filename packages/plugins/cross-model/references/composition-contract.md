# Composition Contract

**Version:** 0.1.0
**Status:** Draft
**Purpose:** Define the canonical composition semantics for structured artifact exchange between `adversarial-review`, `next-steps`, and `dialogue`. This contract is authoritative for protocol design and change control; inline stubs are authoritative for runtime execution.

---

## 1. Purpose, Scope, and Non-Goals

This contract governs composition between:

- The `adversarial-review` skill
- The `next-steps` skill
- The `dialogue` skill

Composition in this contract means: detecting registered sentinels, validating and consuming registered capsules, propagating shared artifact metadata, maintaining lineage across artifacts, and applying shared cross-skill semantics such as consumer behavior, discovery, and staleness.

**In scope:**

- Registered sentinels and capsule wire formats for cross-skill artifact exchange
- Shared artifact metadata semantics and artifact DAG rules
- Consumer classes and capsule-consumption outcomes
- Conversation-local discovery and staleness semantics
- Canonical ownership of shared composition semantics

**Out of scope:**

- The `codex-dialogue` agent synthesis format
- Automatic multi-skill orchestration
- Dialogue-internal `upstream_handoff` state shape, capability flags, or stage threading
- Codex transport, safety pipeline, relay format, or other consultation-layer behavior
- Posture resolution order; when posture resolution is required, implementations SHOULD follow [consultation-contract.md](consultation-contract.md) §14 instead of redefining it here

**Non-goals:**

- Making upstream capsules mandatory for any skill to function
- Replacing existing human-readable skill output with machine-readable output
- Defining file-persistence requirements beyond the selective durable persistence specified in §6 for `dialogue_feedback` artifacts

This contract defines the shared protocol surface only. It MUST NOT require any skill to depend on runtime access to this file.

---

## 2. Normative Terms, Authority Model, and Execution Ownership

| Term | Meaning |
|------|---------|
| **MUST** | Required. Violation is a contract breach. |
| **MUST NOT** | Prohibited. Violation is a contract breach. |
| **SHOULD** | Recommended. Omit only with documented rationale. |
| **canonical semantics** | The protocol rules defined by this contract. |
| **executable projection** | The runtime-operational subset of canonical semantics carried by an inline stub. |
| **consumer class** | The consumption behavior assigned to a registry row in §4 and defined in §7. |
| **registered capsule** | A capsule whose sentinel/version pair appears in the registry in §4. |

### Authority model

| Layer | Authority | Audience |
|-------|-----------|----------|
| Composition contract | Canonical protocol semantics and change control | Skill authors, reviewers, CI |
| Inline stubs | Runtime-operational instructions | Claude during skill execution |
| Design document | Rationale and tradeoff history | Human readers only |

**Precedence and runtime rule:**

1. This contract is authoritative for intended composition semantics.
2. Inline stubs are authoritative for runtime execution because Claude reads the stubs, not this file.
3. A skill MUST be able to execute its owned semantics correctly from its inline stub alone.
4. An inline stub MUST NOT rely on "see composition contract for full algorithm" as a runtime dependency.
5. Missing runtime access to this contract MUST NOT fail closed and MUST NOT block skill execution.
6. Divergence between this contract and an owning stub is a repository defect, even though runtime behavior will follow the stub until corrected.

### Execution ownership rule

**Inclusion in this contract defines protocol semantics, not universal execution responsibility.**

A skill MUST execute a shared semantic only if both conditions hold:

1. Its inline stub declares that responsibility.
2. This section's ownership matrix assigns that semantic to that skill for the current version.

A non-owning skill MUST NOT implement a local variant of a shared semantic unless ownership is added here and the affected stub is updated in the same change.

### Execution-ownership matrix

| Shared semantic | v1 owner(s) | Runtime surface | Notes |
|----------------|-------------|-----------------|-------|
| AR capsule emission | `adversarial-review` | AR inline stub | Emit timing is stub-defined; wire format is contract-defined |
| AR capsule consumption | `next-steps` | NS inline stub | Advisory/tolerant consumer |
| NS handoff emission | `next-steps` | NS inline stub | Emit timing is stub-defined |
| NS handoff admission and consumption | `dialogue` | Dialogue inline stub | Strict/deterministic consumer |
| Feedback capsule emission | `dialogue` | Dialogue inline stub | Produced by skill, not agent |
| Feedback capsule consumption | `adversarial-review`, `next-steps` | AR/NS inline stubs | Advisory/tolerant consumer |
| Consumption discovery | Owning consumer skill | Consumer inline stub | Algorithm defined in §7+§8; v1 consumers are NS, dialogue, AR |
| Routing classification | `dialogue` | Dialogue inline stub | Dialogue-only in v1 |
| Material-delta evaluation | `dialogue` | Dialogue inline stub | Dialogue-only in v1 |
| Iteration-budget enforcement | `dialogue` | Dialogue inline stub | Dialogue-only in v1 |
| Thread freshness decisions | `dialogue` | Dialogue inline stub | Dialogue-only in v1 |

Stub-specific version markers and parity requirements are defined later in §12. Contract-only edits to executed semantics are not sufficient for conformance.

---

## 3. Shared Vocabulary and Composition Model

| Term | Definition |
|------|------------|
| `artifact` | One skill-run snapshot in the composition chain |
| `capsule` | The machine-readable projection of an artifact |
| `sentinel` | The HTML comment marker that announces a capsule wire format and version |
| `subject_key` | Exact lineage key used for supersession and staleness |
| `topic_key` | Non-authoritative descriptive key for display and summaries |
| `lineage_root_id` | Chain identifier used for budget isolation |
| `source snapshot` | The direct upstream artifact set structurally consumed by the current run |
| `direct provenance` | A `source_artifacts` edge to an artifact actually parsed and validated by this run |
| `available conversation context` | The context visible to the current skill invocation |
| `externalized artifact` | A composition artifact emitted into the conversation for downstream consumption |

### Composition model

1. Composition is additive. Structured capsules and sentinels are appended to or alongside human-readable output; they do not replace it.
2. No skill MUST require upstream context to function.
3. Each skill run produces a new artifact snapshot. Composition does not mutate prior artifacts in place.
4. Lineage is represented by explicit metadata and DAG edges, not by implicit conversation memory.
5. User confirmation remains the circuit breaker for cross-skill movement; this contract defines how artifacts move, not when a hop is authorized.

### Artifact model

| Skill run | Artifact kind |
|-----------|---------------|
| One `adversarial-review` run | `adversarial_review` |
| One `next-steps` run | `next_steps_plan` |
| One `dialogue` run | `dialogue_feedback` |

A capsule is not a separate artifact type. It is the externalized machine-readable representation of the artifact produced by that run.

---

## 4. Sentinel Registry and Versioning

This registry is the authoritative list of externalized composition wire formats for v1. A composition capsule MUST use a row from this table.

| sentinel | version | producer_skill | consumer_skills | consumer_class | artifact_kind | schema_ref |
|----------|---------|----------------|-----------------|----------------|---------------|------------|
| `<!-- ar-capsule:v1 -->` | `v1` | `adversarial-review` | `["next-steps"]` | `advisory_tolerant` | `adversarial_review` | `Appendix A` |
| `<!-- next-steps-dialogue-handoff:v1 -->` | `v1` | `next-steps` | `["dialogue"]` | `strict_deterministic` | `next_steps_plan` | `Appendix B` |
| `<!-- dialogue-feedback-capsule:v1 -->` | `v1` | `dialogue` | `["adversarial-review","next-steps"]` | `advisory_tolerant` | `dialogue_feedback` | `Appendix C` |

### Registry rules

1. An externalized composition artifact MUST use a sentinel/version pair that appears in this registry.
2. The `consumer_class` for a capsule MUST be taken from this registry row and interpreted using §7.
3. Unknown sentinel names are ignored. They do not count as registered capsules.
4. A known sentinel with an unsupported version MUST be rejected for consumption.
5. Version mismatch is **reject block, not session**: it MUST prevent capsule consumption, and it MUST NOT fail the enclosing skill invocation.
6. If a registered sentinel is detected, the consumer MUST validate the capsule against the schema referenced by `schema_ref`.
7. Internal-only markers that are not composition capsules MUST NOT be added to this registry.
8. Any change to a registry row MUST update the contract, affected stub projections, and conformance assets in the same change.

---

## 5. Capsule Externalization Rule

This section defines when the shared wire format applies.

1. When a skill externalizes a composition artifact for downstream consumption, it MUST use the registered sentinel and canonical schema for that artifact.
2. Internal reasoning scaffolding has no schema obligation under this contract.
3. A skill MAY use equivalent reasoning structures internally without externalizing them.
4. Global CLAUDE-level behaviors MAY emit the same schema only when the user explicitly requests an externalized artifact; absent explicit externalization, this contract imposes no capsule requirement on internal reasoning.
5. This section defines wire-format obligations only. Emit timing, trigger conditions, and hop suggestions are runtime behaviors owned by inline stubs.

---

## 6. Artifact Metadata and DAG Semantics

All registered capsule schemas MUST include the shared metadata fields below using these exact field names.

| Field | Required | Semantics |
|-------|----------|-----------|
| `artifact_id` | Yes | Stable snapshot identifier for this artifact |
| `artifact_kind` | Yes | One of the registered artifact kinds in §3 |
| `subject_key` | Yes | Exact lineage key for supersession and staleness |
| `topic_key` | Yes | Descriptive metadata only; not a control key |
| `lineage_root_id` | Yes | Composition-chain identifier copied unchanged through descendants |
| `created_at` | Yes | ISO 8601 UTC timestamp for this artifact |
| `supersedes` | Yes | Prior same-kind same-subject artifact ID, or `null` |
| `source_artifacts` | Yes | Direct upstream artifacts structurally consumed by this run |
| `record_path` | Yes | Durable file locator, or `null` |

### Identity keys

| Key | Purpose | Control status |
|-----|---------|----------------|
| `subject_key` | Exact lineage matching and supersession | Authoritative for lineage control |
| `topic_key` | UX, summaries, analytics | Descriptive only; MUST NOT control behavior |
| `lineage_root_id` | Budget isolation for one composition chain | Authoritative for chain identity |

### Key normalization rules

**`subject_key` normalization (exact key — minimally lossy):**

1. Lowercase the value.
2. Replace spaces and underscores with hyphens.
3. Remove leading and trailing whitespace.
4. No character limit — preserve full target specificity for exact lineage matching.
5. Derived from the skill's basis field when minting, or inherited unchanged from upstream capsule.

**`topic_key` normalization (descriptive — non-authoritative):**

1. Apply the same base normalization as `subject_key`.
2. Additionally strip articles (`a`, `an`, `the`), trailing qualifiers, and implementation-specific suffixes.
3. Limit to 50 characters, truncating at a word boundary.
4. Represents the broadest topic this analysis belongs to.

**Basis fields for key minting (when no upstream capsule is consumed):**

| Skill | Basis field | Example |
|-------|-------------|---------|
| `adversarial-review` | `review_target` | "the redaction pipeline" → `redaction-pipeline` |
| `next-steps` | Primary topic of the plan | "redaction pipeline remediation" → `redaction-pipeline-remediation` |
| `dialogue` | Goal/question topic | "redaction pipeline architecture" → `redaction-pipeline-architecture` |

### Key propagation rules

1. If a skill directly consumes an upstream capsule, it MUST inherit `subject_key` unchanged from that capsule.
2. If a skill directly consumes an upstream capsule, it MUST inherit `topic_key` unchanged from that capsule.
3. If a skill directly consumes an upstream capsule, it MUST inherit `lineage_root_id` unchanged from that capsule.
4. If no upstream capsule is directly consumed, the skill is the root of a new composition chain and MUST set `lineage_root_id` to its own `artifact_id`.
5. Only the root artifact in a composition chain may mint new lineage keys. Downstream direct consumers MUST inherit rather than re-mint.
6. `topic_key` MUST NOT be used for budget enforcement, staleness, or any other control decision.

### Artifact ID format

`artifact_id` MUST use this format:

```text
<kind-prefix>:<subject_key>:<created_at_compact>
```

Where:

- `kind-prefix` is `ar`, `ns`, or `dialogue`
- `created_at_compact` is `created_at` with separators removed: `YYYYMMDDTHHMMSS.sss`

### Timestamp rules

1. `created_at` MUST be an ISO 8601 UTC timestamp.
2. All three skills MUST use millisecond precision.
3. If only second-level precision is available, implementations MUST pad `.000`.
4. If higher-than-millisecond precision is available, implementations MUST truncate to milliseconds.
5. `artifact_id` MUST be derived from the millisecond-precision `created_at` value used in the capsule.

### DAG rules

| Edge | Meaning |
|------|---------|
| `supersedes` | Same-kind, same-subject version chain |
| `source_artifacts[]` | Cross-kind direct provenance |

Each `source_artifacts[]` entry MUST include:

- `artifact_id`
- `artifact_kind`
- `role`

### Provenance rules

1. `source_artifacts[]` MUST record direct provenance only.
2. A run MUST NOT record transitive provenance in `source_artifacts[]`.
3. A `source_artifacts[]` entry MUST refer only to an artifact that this run actually parsed and validated.
4. When a consumer falls back because an upstream capsule is absent or invalid, downstream output MUST omit any `source_artifacts[]` entry for that absent or invalid capsule.
5. A run MUST NOT mint provenance from prose-only inference.

### `record_path` rule

`record_path` is a locator, not identity. If present, it points to a durable file representing the same artifact. `artifact_id` remains the canonical identity.

### Durable persistence requirements

Not all artifact kinds require durable persistence in v1. The feedback arc (dialogue → AR/NS) is the only composition path that reliably crosses invocation boundaries, where conversation context compaction may erase the capsule before the downstream consumer runs.

| Artifact kind | `record_path` requirement | Rationale |
|---------------|--------------------------|-----------|
| `adversarial_review` | MAY be `null` | AR→NS consumption happens in rapid sequence; compaction risk is low |
| `next_steps_plan` | MAY be `null` | NS→dialogue consumption happens in rapid sequence; compaction risk is low |
| `dialogue_feedback` | MUST be non-null | Feedback consumption may happen after significant conversation; compaction risk is high |

**Durable store for `dialogue_feedback`:**

1. The `/dialogue` skill MUST write each feedback artifact to `.claude/composition/feedback/`.
2. Filename MUST be `dialogue--<subject_key>--<created_at_compact>.md` (filesystem-safe projection; `artifact_id` stays in-file as canonical identity).
3. File format MUST use the same sentinel and capsule payload as the conversation-local capsule. Optional non-normative prose body MAY follow.
4. The durable file is the same wire shape as the conversation capsule — one format, one validator.
5. The `.claude/composition/feedback/` directory SHOULD be gitignored.

---

## 7. Consumer Classes and Consumption Outcomes

This section defines how a skill behaves after its stub declares an expected upstream capsule and §4 identifies the applicable consumer class.

### Consumer class definitions

| Consumer class | Required behavior |
|----------------|-------------------|
| `advisory_tolerant` | Validate if a candidate capsule is present. If no valid capsule is consumed, fall back to non-capsule behavior defined by the owning stub. A one-line prose diagnostic is required on fallback. |
| `strict_deterministic` | Validate if a candidate capsule is present. If no valid capsule is consumed, continue the normal pipeline without structured handoff and without synthesizing an equivalent handoff from another source. |

### Advisory/tolerant requirements

An `advisory_tolerant` consumer:

1. MUST attempt structural consumption when the expected sentinel is found.
2. MUST validate the candidate against the registered schema.
3. MUST fall back if the expected sentinel is absent, the version is unsupported, or schema validation fails.
4. MUST emit a one-line prose diagnostic whenever it falls back from structural consumption.
5. MAY continue using prose parsing or other local non-capsule behavior defined by its stub.
6. MUST treat unsupported version as consumption failure, not invocation failure.
7. MUST NOT reference the rejected or absent capsule in downstream provenance.

### Strict/deterministic requirements

A `strict_deterministic` consumer:

1. MUST attempt structural consumption when the expected sentinel is found.
2. MUST validate the candidate against the registered schema.
3. MUST reject the handoff if the version is unsupported or schema validation fails.
4. MUST continue its normal non-handoff pipeline after rejection.
5. MUST NOT synthesize an equivalent structured handoff from prose, conversation context, or another alternate source.
6. MUST treat unsupported version as consumption failure, not invocation failure.
7. SHOULD emit a one-line prose diagnostic when it rejects a detected handoff.
8. MAY proceed silently when no expected sentinel is present.

### Consumption outcome matrix

| Condition | `advisory_tolerant` outcome | `strict_deterministic` outcome |
|-----------|-----------------------------|--------------------------------|
| No expected sentinel found | Fall back to local non-capsule behavior; emit one-line diagnostic | Continue normal pipeline without structural handoff |
| Expected sentinel found, supported version, valid schema | Consume capsule and use structured data | Consume capsule and use structured data |
| Expected sentinel found, unsupported version | Reject capsule; fall back; emit one-line diagnostic | Reject capsule; continue normal pipeline; SHOULD emit one-line diagnostic |
| Expected sentinel found, supported version, invalid or unparseable schema | Reject capsule; fall back; emit one-line diagnostic | Reject capsule; continue normal pipeline; SHOULD emit one-line diagnostic |

### Fallback and rejection rules

1. Capsule consumption is all-or-nothing. A consumer MUST NOT partially consume an invalid capsule.
2. Once a candidate capsule is selected for validation, a consumer MUST apply the no-backtrack rule defined in §8.
3. Rejection of a capsule MUST NOT terminate the skill invocation unless another contract explicitly requires termination for unrelated reasons.
4. A valid structurally consumed capsule MAY be referenced in downstream provenance. A rejected or absent capsule MUST NOT be referenced in downstream provenance.
5. Consumer behavior in this section applies only to registered composition capsules. Unregistered or unknown markers are ignored.

---

## 8. Discovery and Staleness Semantics

This section defines two distinct conversation-local algorithms:

- **Consumption discovery**: used when a skill wants to consume an upstream capsule now
- **Staleness discovery**: used when a skill wants to determine whether a consumed artifact has been superseded

These algorithms serve different purposes and MUST NOT be conflated.

### 8.1 Scope Boundary and Source Resolution

Discovery operates across multiple sources with defined precedence.

1. `available conversation context` means the context visible to the current skill invocation.
2. A consumer MUST NOT infer facts about unseen prior sessions from absence in current context.

### 8.1b Source Resolution

Before running consumption discovery, a consumer MUST resolve the artifact source using this precedence:

| Priority | Source | When available |
|----------|--------|----------------|
| 1 | Explicit reference | User or stub state provides a specific `artifact_id` or `record_path` |
| 2 | Durable store | A durable store exists for the target `artifact_kind` (v1: `.claude/composition/feedback/` for `dialogue_feedback`) |
| 3 | Conversation-local | Available conversation context contains the expected sentinel |

**Resolution rules:**

1. Source resolution MUST try sources in precedence order.
2. If the highest-precedence available source yields a valid artifact, use it.
3. If the highest-precedence available source yields no result or an invalid candidate, fall through to the next source.
4. If an explicit reference (priority 1) is provided and the referenced artifact is missing or invalid, resolution MUST fail rather than silently falling through. Explicit references represent user intent.
5. For durable store scans (priority 2) without an explicit `artifact_id`: scan the store directory, parse valid artifacts of the target kind, and select the newest compatible artifact matching the target `subject_key`.
6. No index is required in v1. Directory scan is sufficient.
7. Once a source is selected, consumption discovery (§8.2) runs within that source.

**v1 applicability:** Source resolution with durable store applies to `dialogue_feedback` consumption only. AR capsule and NS handoff consumption skip priority 2 (no durable store exists for those artifact kinds in v1) and proceed directly from priority 1 to priority 3.

### 8.2 Consumption Discovery

Consumption discovery is a **single-result, newest-first, no-backtrack** algorithm that runs within the source selected by §8.1b.

**Algorithm:**

1. Reverse-scan available conversation context newest-first for the expected sentinel declared by the owning stub.
2. Take the first matching sentinel only.
3. Validate that candidate against the registered version and schema.
4. If the candidate is invalid or unsupported, reject it and stop.
5. Do not backtrack to older matching sentinels after rejecting the first candidate.
6. If no expected sentinel is found, proceed without structural handoff.

**Rules:**

1. Consumption discovery MUST select at most one candidate.
2. Consumption discovery MUST prefer recency over historical search breadth.
3. A consumer MUST NOT merge fields from multiple candidate capsules.
4. A consumer MUST NOT partially consume a candidate capsule.
5. Rejection at this stage is a capsule-consumption failure, not a skill-invocation failure.

### 8.3 Staleness Discovery

Staleness discovery is a **multi-scan** algorithm used after a capsule has been consumed or when a consumer wants to assess freshness of direct inputs.

**Algorithm:**

1. Scan available conversation context for all valid capsules matching a target `artifact_kind` and `subject_key`.
2. Index matches by `artifact_id` and `created_at`.
3. Compare the consumed artifact and its direct `source_artifacts` against the indexed set to detect newer visible superseders.

**Rules:**

1. Staleness discovery MUST consider all valid matching capsules visible in current context.
2. Staleness discovery MUST ignore invalid and unparseable capsules for indexing purposes.
3. Staleness discovery MAY be run after successful consumption discovery.
4. Staleness discovery MUST NOT alter which capsule was consumed; it only evaluates freshness.

### 8.4 Ordered Staleness Evaluation

Staleness status MUST be evaluated in this order. The first matching status applies.

| Priority | Status | Condition | Consumer behavior |
|----------|--------|-----------|-------------------|
| 1 | `superseded` | Positive evidence shows a newer same-kind same-subject artifact exists in available context | Prefer the newer artifact |
| 2 | `unknown` | A required direct `source_artifact` is absent from available context, invalid, or unparseable | Do not block; continue with caution |
| 3 | `stale_inputs` | A direct `source_artifact` has a newer visible superseder in available context | Warn and suggest rebasing |
| 4 | `current` | No superseder exists in available context and all required direct inputs are current within available context | Proceed normally |

### 8.5 Must-Not-Infer-Current Rule

1. A consumer MUST NOT infer `current` from missing evidence.
2. If a required direct `source_artifact` is absent from available context, the status MUST be `unknown`, not `current`.
3. `current` requires positive evidence that no newer same-kind same-subject artifact is visible in available context.

---

## 9. Routing, Materiality, and Budget Rules

**Applicability (v1):** This section is executed by `dialogue` only.

Other skills MAY consume outcomes produced under these rules, but they MUST NOT implement local variants of routing, materiality, or budget behavior unless the ownership matrix in §2 is updated and the affected stub is co-edited.

Deterministic clauses in this section MUST be evaluable from the direct source snapshot available to `dialogue`; implementations MUST NOT read through to transitive upstream capsules or other non-snapshot context to satisfy a deterministic comparator.

### 9.1 Routing Classification

Routing classification determines which next hop, if any, a feedback candidate suggests.

Routing MUST be deterministic-first.

| Signal | `suggested_arc` | Rationale |
|--------|-----------------|-----------|
| Item references upstream `finding_id` or `assumption_id` | `adversarial-review` | Diagnosis surface changed |
| Item references upstream `task_id`, `decision_gate_id`, or critical path | `next-steps` | Planning surface changed |
| Item references neither and is an evidence/framing question | `dialogue_continue` | Same scope; continue gathering |
| Item hits both AR and NS surfaces | `adversarial-review` | Diagnosis before planning |

**Fallback: constrained model pass**

If deterministic routing does not classify the item, a constrained model pass MAY be used.

When used, it MUST:

1. Output exactly one of: `adversarial-review`, `next-steps`, `dialogue_continue`, `ambiguous`
2. Name the `affected_surface`
3. Provide a one-line reason
4. Record `classifier_source: model`

If deterministic routing classifies the item, the result MUST record `classifier_source: rule`.

### 9.2 Dimension Independence

1. `classifier_source` and `suggested_arc` are independent dimensions.
2. `classifier_source` describes the classification method: `rule` or `model`.
3. `suggested_arc` describes the routing outcome.
4. `ambiguous` is a valid routing outcome.
5. `ambiguous` is NOT a valid classifier method.

### 9.3 Ambiguous Handling

All `ambiguous` items enter materiality evaluation like any other item.

| Condition | Behavior |
|-----------|----------|
| `material: false` and `suggested_arc: ambiguous` | Informational only; no hop suggested |
| `material: true` and `suggested_arc: ambiguous` | Manual routing bucket; present `adversarial-review`, `next-steps`, or `hold`; default is `hold` |

**Disambiguation rule:**

If the uncertainty is "more evidence is needed before deciding which surface owns this," the correct routing outcome is `dialogue_continue`, not `ambiguous`.

### 9.4 Material-Delta Evaluation

Materiality is evaluated in ordered tiers with a cross-tier guard.

#### Pre-check: Novelty Veto

Before Tier 1, the evaluator MUST check whether the item introduces any new content relative to the source snapshot, including:

- New failure mode
- New causal mechanism
- New consequence
- New dependency
- New gate effect
- New contradiction

If the item introduces novel content, Tier 1 MUST return `no_match` regardless of exclusion-class fit. Evaluation then proceeds directly to Tier 2.

#### Tier 1: Pre-Screening Exclusions

An item is provisionally not material if any of these apply and the novelty veto did not fire:

- Exact restatement or example of an existing item in the source snapshot
- Open question already present in the source snapshot
- Clearly unsupported tangent with no affected upstream refs

This Tier 1 exclusion set is **closed for v1**. Implementations MUST NOT add exclusion classes without a contract update.

**Tier 1 source tracking:**

- Use `materiality_source: rule` when the exclusion is clear-cut
- Use `materiality_source: model` when the exclusion required interpretation

#### Cross-Tier Guard

If Tier 1 matched using `materiality_source: model`, the exclusion is provisional.

The evaluator MUST then check Tier 2:

- If Tier 2 would include the item, Tier 2 takes precedence and the final result MUST be `material: true` with `materiality_source: rule`
- If Tier 2 would not include the item, the Tier 1 exclusion stands and the final result is `material: false`

If Tier 1 matched using `materiality_source: rule`, the exclusion is final and Tiers 2-3 are skipped.

#### Tier 2: Deterministic Inclusions

An item is material if any of these apply:

- It crosses an action threshold:
  - assumption status changes to `wishful`
  - finding severity changes to `blocking` or `high`
  - task moves on or off the critical path
  - decision gate changes branch outcome

If Tier 2 matches, the final result MUST be `material: true` with `materiality_source: rule`.

**Deferred from v1:** Reopened-or-contradicted resolved-state comparison is deferred until `dialogue` has a direct resolved-item input surface in its source snapshot.

#### Tier 3: Semantic Fallback

If neither Tier 1 nor Tier 2 produced a final result, semantic evaluation MAY be used.

Tier 3 asks whether the item:

- Introduces a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface
- Introduces a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface
- Is an implementation detail below the current abstraction level

If Tier 3 is used, the evaluator MUST:

1. Record `materiality_source: model`
2. Provide a one-line `materiality_reason`
3. Emit a final boolean `material`

### 9.5 Materiality Dimension Independence

1. `materiality_source` and `classifier_source` are independent dimensions.
2. `materiality_source` describes how materiality was determined.
3. `classifier_source` describes how routing was determined.
4. An implementation MUST NOT collapse these into one field.

### 9.6 Affected-Surface Validity Check

After routing classification (§9.1) and materiality evaluation (§9.4), `dialogue` MUST validate the final tuple `(affected_surface, material, suggested_arc)` against the matrix below.

This check applies to **all** routing outcomes, including:

- deterministic rule-produced outcomes
- constrained model-produced outcomes
- outcomes later reconsidered after materiality evaluation

An invalid tuple MUST NOT be emitted as a final `FeedbackCandidate` route.

#### Validity matrix

| `affected_surface` | `material` | Valid `suggested_arc` values |
|--------------------|------------|------------------------------|
| `diagnosis` | `true` | `adversarial-review`, `ambiguous` |
| `planning` | `true` | `next-steps`, `ambiguous` |
| `evidence-only` | `true` | `dialogue_continue` |
| `diagnosis` | `false` | `dialogue_continue`, `ambiguous` |
| `planning` | `false` | `dialogue_continue`, `ambiguous` |
| `evidence-only` | `false` | `dialogue_continue` |

#### Post-classification correction rules

If a classified route is invalid under the matrix:

1. The invalid pair MUST be rejected.
2. The router MUST apply a deterministic correction before emission.
3. If `material = false`, the corrected `suggested_arc` MUST be `dialogue_continue`.
4. Else if `affected_surface = evidence-only`, the corrected `suggested_arc` MUST be `dialogue_continue`.
5. Else the corrected `suggested_arc` MUST be `ambiguous`.
6. Any corrected outcome produced by this validity check MUST record `classifier_source: rule`.

#### Consequences

1. `affected_surface: diagnosis` MUST NOT emit `suggested_arc: next-steps`.
2. `affected_surface: planning` MUST NOT emit `suggested_arc: adversarial-review`.
3. `affected_surface: evidence-only` MUST NOT emit `suggested_arc: adversarial-review`, `next-steps`, or `ambiguous`.
4. A material item whose affected surface is `diagnosis` or `planning` MUST NOT silently remain `dialogue_continue`.
5. The materiality gate does not repair bad routing by itself; this validity check is the required post-classification constraint that prevents invalid route acceptance.

#### Interpretation note

`affected_surface` constrains which routing outcomes are admissible. It does not replace the deterministic routing rules in §9.1, and it does not replace materiality evaluation in §9.4. It is a post-classification validity gate applied after both have run.

### 9.7 Hop Suggestion Guardrails

1. A hop MUST NOT be suggested unless there is material delta relative to the source snapshot.
2. A suggested hop MUST always require explicit user confirmation before execution.
3. The user remains the circuit breaker for every hop in the composition chain.

### 9.8 Iteration Budget

The composition chain uses a soft iteration budget keyed by `lineage_root_id`.

1. Budget tracking MUST use `lineage_root_id`.
2. Budget tracking MUST NOT use `topic_key`.
3. Budget tracking MUST NOT use `subject_key` as the chain identifier.
4. After 2 targeted loops within the same `lineage_root_id`, automatic further hop suggestion MUST stop.
5. When the soft limit is reached, the skill SHOULD report remaining open items.
6. The user MAY override the soft limit explicitly.

---

## 10. Thread Freshness and Continuation

**Applicability (v1):** This section is executed by `dialogue` only.

This section governs when a Codex thread may continue versus when a new thread is required because upstream composition artifacts changed.

### 10.1 Hard Rule

**New artifact → new thread.**

If a new AR or NS artifact is introduced into the active composition chain, dialogue MUST start a fresh thread.

### 10.2 Continue Conditions

Dialogue MAY continue an existing Codex thread only when **all** of the following are true:

1. The goal is unchanged.
2. The upstream snapshot set is unchanged.
3. Unresolved items are evidence or clarification questions only, not changed diagnosis or plan.
4. Prior termination was operational, such as budget exhaustion, interruption, or resolved scope issue.

### 10.3 Fresh-Start Triggers

Dialogue MUST start a fresh thread when **any** of the following are true:

1. A new AR snapshot exists.
2. A new NS snapshot exists.
3. Posture or focus changed materially.
4. The selected task set or decision-gate set changed.

### 10.4 Injection Prohibition

Updated AR or NS artifacts MUST NOT be injected into an existing Codex thread. Once diagnosis or planning has changed, the prior dialogue state is stale.

---

## 11. Governance Locks

These rules are non-negotiable. Implementations MUST NOT override them.

1. **No auto-chaining:** A skill MAY suggest a next hop, but it MUST NOT invoke another skill in the composition chain without explicit user confirmation.
2. **Registered wire formats only:** Any externalized composition artifact MUST use a sentinel/version pair registered in §4 and conform to the schema inventory for that artifact.
3. **Provenance integrity:** `source_artifacts` MUST contain only direct parsed-and-validated upstream artifacts. Implementations MUST NOT record transitive provenance or prose-derived provenance.
4. **Registry-mediated evolution:** Any change to a sentinel, sentinel version, consumer class, execution ownership, or canonical schema inventory MUST update the contract, affected stub projections, and conformance assets in the same change.

---

## 12. Conformance and Drift Detection

An implementation is conformant when the contract, owning stubs, and conformance checks agree on shared semantics and ownership.

### 12.1 Required Marker

Every participating skill stub MUST declare:

```yaml
implements_composition_contract: v1
```

### 12.2 Recommended Ruleset Markers

Owning stubs SHOULD declare finer-grained markers for executed semantics, for example:

```yaml
implements_routing_ruleset: v1
implements_materiality_ruleset: v1
implements_discovery_ruleset: v1
implements_thread_freshness_ruleset: v1
```

Only the owning stub for a ruleset SHOULD declare that ruleset marker.

### 12.3 Drift Rules

1. CI MUST fail if a contract change modifies an executed semantic without a corresponding co-edit to the owning stub.
2. CI MUST fail if a stub declares ownership for a semantic that is not assigned to it in §2.
3. CI MUST fail if a required participating stub omits `implements_composition_contract: v1`.
4. CI SHOULD verify that stub-declared consumed and emitted sentinels match the registry in §4.
5. CI SHOULD verify that ruleset markers match the ownership matrix in §2.

### 12.4 Schema Inventory Status

Until schema-parity tooling exists, the appendices in this document are **metadata-only field inventories**.

Under this v1 fallback:

1. The appendices define required fields, types, and constraints.
2. The appendices do not define canonical YAML ordering or exact serialization layout.
3. Inline stubs remain the only full runtime schema texts.
4. A future upgrade to full canonical schemas MAY occur only after parity tooling is available to compare stub projections against contract-owned schema blocks.

### 12.5 Repository Defect Rule

If this contract and an owning stub diverge, runtime will follow the stub, but the repository is non-conformant until the drift is corrected.

---

## Appendix A. AR Capsule Field Inventory (`<!-- ar-capsule:v1 -->`)

**Status:** Metadata-only inventory for v1. This appendix defines required fields and constraints, not canonical YAML ordering.

### A.1 Top-Level Fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST use prefix `ar:` and the format defined in §6 |
| `artifact_kind` | `string` | Yes | MUST equal `adversarial_review` |
| `subject_key` | `string` | Yes | MUST follow §6 key rules |
| `topic_key` | `string` | Yes | Descriptive only; MUST NOT control behavior |
| `lineage_root_id` | `string` | Yes | MUST follow §6 propagation rules |
| `created_at` | `string` | Yes | MUST be ISO 8601 UTC with millisecond precision |
| `supersedes` | `string \| null` | Yes | MUST reference a prior same-kind same-subject artifact or be `null` |
| `source_artifacts` | `SourceArtifact[]` | Yes | MAY be empty; MUST contain only direct validated inputs |
| `record_path` | `string \| null` | Yes | Locator only; not identity |
| `review_target` | `string` | Yes | Non-empty, one-line description of the reviewed target |
| `overall_confidence` | `integer` | Yes | MUST be in the inclusive range `1..5` |
| `findings` | `Finding[]` | Yes | MAY be empty; IDs are snapshot-scoped |
| `assumptions` | `Assumption[]` | Yes | MAY be empty |
| `open_questions` | `string[]` | Yes | MAY be empty |

### A.2 Nested Types

**SourceArtifact**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST identify a direct validated upstream artifact |
| `artifact_kind` | `string` | Yes | MUST match the upstream artifact kind |
| `role` | `string` | Yes | Non-empty provenance role label |

**Finding**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `finding_id` | `string` | Yes | MUST be unique within this artifact |
| `severity` | `string` | Yes | MUST be one of `blocking`, `high`, `moderate`, `low` |
| `summary` | `string` | Yes | Non-empty one-line summary |

**Assumption**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `assumption_id` | `string` | Yes | MUST be unique within this artifact |
| `text` | `string` | Yes | Non-empty |
| `status` | `string` | Yes | MUST be one of `validated`, `plausible`, `wishful` |
| `if_wrong` | `string` | Yes | Non-empty one-line consequence |

---

## Appendix B. NS Handoff Field Inventory (`<!-- next-steps-dialogue-handoff:v1 -->`)

**Status:** Metadata-only inventory for v1. This appendix defines required fields and constraints, not canonical YAML ordering.

### B.1 Top-Level Fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST use prefix `ns:` and the format defined in §6 |
| `artifact_kind` | `string` | Yes | MUST equal `next_steps_plan` |
| `subject_key` | `string` | Yes | MUST follow §6 key rules |
| `topic_key` | `string` | Yes | Descriptive only; MUST NOT control behavior |
| `lineage_root_id` | `string` | Yes | MUST follow §6 propagation rules |
| `created_at` | `string` | Yes | MUST be ISO 8601 UTC with millisecond precision |
| `supersedes` | `string \| null` | Yes | MUST reference a prior same-kind same-subject artifact or be `null` |
| `source_artifacts` | `SourceArtifact[]` | Yes | MAY be empty; MUST omit absent or invalid AR provenance on fallback |
| `record_path` | `string \| null` | Yes | MUST be `null` in v1 unless future persistence is added |
| `focus_question` | `string` | Yes | Non-empty; defines what dialogue should resolve |
| `recommended_posture` | `string` | Yes | MUST be one of `adversarial`, `collaborative`, `exploratory`, `evaluative`, `comparative` |
| `selected_tasks` | `SelectedTask[]` | Yes | MUST contain at least one task |
| `decision_gates` | `DecisionGate[]` | Yes | MAY be empty |
| `source_findings` | `SourceFinding[]` | Yes | MAY be empty |
| `source_assumptions` | `SourceAssumption[]` | Yes | MAY be empty |
| `source_open_questions` | `string[]` | Yes | MAY be empty |
| `out_of_scope` | `string[]` | Yes | MAY be empty |

### B.2 Nested Types

**SourceArtifact**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST identify a direct validated upstream artifact |
| `artifact_kind` | `string` | Yes | MUST match the upstream artifact kind |
| `role` | `string` | Yes | Non-empty provenance role label |

**SelectedTask**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `task_id` | `string` | Yes | MUST be unique within this artifact |
| `task` | `string` | Yes | Non-empty task description |
| `why_now` | `string` | Yes | Non-empty explanation of dialogue value |
| `depends_on` | `string[]` | Yes | MAY be empty; each value SHOULD reference another `task_id` in the same artifact |
| `done_when` | `string` | Yes | Non-empty strategic completion condition |

**DecisionGate**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `gate_id` | `string` | Yes | MUST be unique within this artifact |
| `after` | `string` | Yes | SHOULD reference a `task_id` in `selected_tasks` |
| `condition` | `string` | Yes | Non-empty branch condition |

**SourceFinding**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `finding_id` | `string` | Yes | SHOULD reference an upstream AR `finding_id` when present |
| `severity` | `string` | Yes | MUST be one of `blocking`, `high`, `moderate`, `low` |
| `summary` | `string` | Yes | Non-empty one-line summary |

**SourceAssumption**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `assumption_id` | `string` | Yes | SHOULD reference an upstream AR `assumption_id` when present |
| `status` | `string` | Yes | MUST be one of `validated`, `plausible`, `wishful` |
| `text` | `string` | Yes | Non-empty |

### B.3 Forwarding Rules

`source_findings`, `source_assumptions`, and `source_open_questions` are plan-scoped projections of diagnosis context, not a requirement to reproduce the full AR capsule.

1. When `next-steps` structurally consumes a valid AR capsule, it SHOULD populate these fields with the upstream findings, assumptions, and open questions that materially inform the handoff's `focus_question`, `selected_tasks`, or `decision_gates`.
2. Any forwarded `finding_id`, `assumption_id`, `status`, or question string MUST preserve the upstream AR value without local renumbering or reinterpretation.
3. If no valid AR capsule was structurally consumed, `source_findings`, `source_assumptions`, and `source_open_questions` MUST be empty.

---

## Appendix C. Dialogue Feedback Field Inventory (`<!-- dialogue-feedback-capsule:v1 -->`)

**Status:** Metadata-only inventory for v1. This appendix defines required fields and constraints, not canonical YAML ordering.

### C.1 Top-Level Fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST use prefix `dialogue:` and the format defined in §6 |
| `artifact_kind` | `string` | Yes | MUST equal `dialogue_feedback` |
| `subject_key` | `string` | Yes | MUST follow §6 key rules |
| `topic_key` | `string` | Yes | Descriptive only; MUST NOT control behavior |
| `lineage_root_id` | `string` | Yes | MUST follow §6 propagation rules |
| `created_at` | `string` | Yes | MUST be ISO 8601 UTC with millisecond precision |
| `supersedes` | `string \| null` | Yes | MUST reference a prior same-kind same-subject artifact or be `null` |
| `source_artifacts` | `SourceArtifact[]` | Yes | MAY be empty; MUST contain only direct validated inputs |
| `record_path` | `string` | Yes | MUST be non-null; MUST point to the durable feedback artifact at `.claude/composition/feedback/` per §6 |
| `thread_id` | `string` | Yes | Non-empty Codex thread identifier |
| `converged` | `boolean` | Yes | Final convergence state for this dialogue run |
| `turn_count` | `integer` | Yes | MUST be greater than or equal to `1` |
| `resolved` | `ResolvedItem[]` | Yes | MAY be empty |
| `unresolved` | `OpenItem[]` | Yes | MAY be empty |
| `emerged` | `OpenItem[]` | Yes | MAY be empty |
| `continuation_warranted` | `boolean` | Yes | Indicates whether more dialogue may still be useful |
| `recommended_posture` | `string \| null` | Yes | If non-null, MUST be one of `adversarial`, `collaborative`, `exploratory`, `evaluative`, `comparative` |
| `feedback_candidates` | `FeedbackCandidate[]` | Yes | MAY be empty |

### C.2 Nested Types

**SourceArtifact**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `artifact_id` | `string` | Yes | MUST identify a direct validated upstream artifact |
| `artifact_kind` | `string` | Yes | MUST match the upstream artifact kind |
| `role` | `string` | Yes | Non-empty provenance role label |

**ResolvedItem**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `item_id` | `string` | Yes | MUST be unique within `resolved` |
| `text` | `string` | Yes | Non-empty |
| `confidence` | `string` | Yes | MUST be one of `high`, `medium`, `low` |

**OpenItem**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `item_id` | `string` | Yes | MUST be unique within its list |
| `text` | `string` | Yes | Non-empty |

**FeedbackCandidate**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `item_id` | `string` | Yes | MUST reference a candidate item from the dialogue result set |
| `suggested_arc` | `string` | Yes | MUST be one of `adversarial-review`, `next-steps`, `dialogue_continue`, `ambiguous` |
| `affected_surface` | `string` | Yes | MUST be one of `diagnosis`, `planning`, `evidence-only` |
| `affected_refs` | `string[]` | Yes | MAY be empty; references to upstream artifacts or item IDs |
| `material` | `boolean` | Yes | Final materiality result |
| `materiality_reason` | `string` | Yes | Non-empty one-line explanation |
| `classifier_source` | `string` | Yes | MUST be `rule` or `model` |
| `materiality_source` | `string` | Yes | MUST be `rule` or `model` |

### C.3 Independence Constraint

For `FeedbackCandidate` rows:

1. `classifier_source` and `materiality_source` MUST be tracked independently.
2. `classifier_source` MUST describe routing method only.
3. `materiality_source` MUST describe materiality method only.
4. A candidate MAY have mixed provenance, such as `classifier_source: rule` and `materiality_source: model`.
