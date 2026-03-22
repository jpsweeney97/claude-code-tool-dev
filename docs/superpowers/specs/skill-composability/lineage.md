---
module: lineage
status: active
normative: true
authority: lineage
---

# Lineage Model

## Artifact Identity

An artifact is one skill-run snapshot. The capsule is the machine-readable projection of that artifact — not a separate entity. For capsule schemas using these identity fields, see [capsule-contracts.md](capsule-contracts.md).

| Skill Run | Artifact Kind |
|-----------|---------------|
| One adversarial-review run | `adversarial_review` |
| One next-steps run | `next_steps_plan` |
| One /dialogue run | `dialogue_feedback` |

## Three Identity Keys

Each artifact carries three identity keys serving different purposes:

| Key | Purpose | Format | Used by |
|-----|---------|--------|---------|
| `subject_key` | Exact lineage matching (staleness, supersession) | kebab-case, deterministic from target | Staleness detection, `supersedes` links |
| `topic_key` | Non-authoritative descriptive metadata for UX and analytics | kebab-case, broader than subject_key | Display only — NOT a control key |
| `lineage_root_id` | Budget isolation — identifies the composition chain | Full `artifact_id` of root artifact, copied unchanged | Soft iteration budget ([guardrails](routing-and-materiality.md#soft-iteration-budget)) |

`subject_key` and `topic_key` may be identical for simple targets. They diverge when a subject is a specific facet of a broader topic (e.g., `subject_key` = `redaction-format-layer` under `topic_key` = `redaction-pipeline`).

`lineage_root_id` is always a full `artifact_id`, not a kebab-case string.

### subject_key Normalization (exact — minimally lossy)

- Lowercase, replace spaces/underscores with hyphens
- Remove leading/trailing whitespace
- No character limit — preserve full target specificity for exact lineage matching
- Derived from the skill's basis field when minting, or inherited from upstream capsule

### topic_key Normalization (descriptive — non-authoritative)

- Same base normalization as `subject_key`
- Additionally: strip articles (a, an, the), trailing qualifiers, and implementation-specific suffixes
- Limit to 50 characters, truncate at word boundary
- NOT used for budget enforcement or any control decisions. Collisions between independent chains sharing the same `topic_key` are harmless — budget tracks by `lineage_root_id`.

**Optionality recommendation:** Both evaluative and exploratory Codex dialogues recommended making `topic_key` optional in v1 — no consumer uses it for control decisions, and it can be derived from `subject_key` when needed.

## Key Propagation

**Inheritance-first rule:** Only the root of a composition chain mints keys. All downstream skills inherit. This eliminates cross-skill key drift.

| Condition | subject_key | topic_key | lineage_root_id |
|-----------|-------------|-----------|-----------------|
| No upstream capsule consumed (root) | Mint from basis field | Mint from basis field | Set to this artifact's `artifact_id` |
| Upstream capsule consumed (downstream) | Inherit from upstream | Inherit from upstream | Copy unchanged from upstream |

`lineage_root_id` is immutable within a chain — never re-minted downstream. All artifacts in a single composition chain share the same `lineage_root_id`; independent chains have different values by construction.

`lineage_root_id` serves budget isolation only, not freshness detection or staleness — those are separate concerns handled by `subject_key` and `supersedes`.

### Basis Fields (key minting at chain root)

| Skill | Basis Field | Example |
|-------|-------------|---------|
| adversarial-review | `review_target` | "the redaction pipeline" → `redaction-pipeline` |
| next-steps | Primary topic of the plan | "redaction pipeline remediation" → `redaction-pipeline-remediation` |
| dialogue | Goal/question topic | "redaction pipeline architecture" → `redaction-pipeline-architecture` |

### Propagation Example

1. AR (standalone) → mints `subject_key: redaction-pipeline`, sets `lineage_root_id: ar:redaction-pipeline:20260318T143052.123`
2. NS (consumes AR) → inherits `subject_key: redaction-pipeline`, inherits `lineage_root_id`
3. Dialogue (consumes NS) → inherits both keys unchanged
4. AR (re-review consuming feedback) → inherits both keys unchanged — same `lineage_root_id` throughout

## Artifact ID Format

```
<kind-prefix>:<subject_key>:<created_at_compact>
```

`created_at_compact` is the `created_at` value with separators removed: `YYYYMMDDTHHMMSS.sss` (always 3 fractional digits).

**Precision rule:** All three skills MUST use millisecond precision. Pad `.000` if only second-level precision is available; truncate to milliseconds if higher precision is provided.

**Prefixes:** `ar:` (adversarial_review), `ns:` (next_steps_plan), `dialogue:` (dialogue_feedback).

Examples:

- `ar:redaction-pipeline:20260318T143052.123`
- `ns:redaction-pipeline:20260318T144215.456`
- `dialogue:redaction-pipeline:20260318T151033.789`

## DAG Structure

Two edge types connect artifacts:

| Edge | Connects | Purpose |
|------|----------|---------|
| `supersedes` | Same-kind, same-subject artifacts | Version chain within one artifact family |
| `source_artifacts[]` | Cross-kind artifacts | Provenance graph showing what this run consumed |

**`supersedes` minting rule:** `supersedes` MUST reference the most recent prior artifact of the same `artifact_kind` and `subject_key` visible in conversation context at the time of capsule emission. For `dialogue_feedback` artifacts, also check the durable store at `.claude/composition/feedback/` (per the step-0 durable store check in [consumption discovery](#consumption-discovery)) before determining `supersedes` — the most recent prior artifact across both conversation context and the durable store is the correct supersession target. If multiple prior artifacts exist, take the one with the latest `created_at`. If no prior artifact of the same kind and subject exists, set `supersedes: null`.

Each `source_artifacts[]` entry includes `artifact_id`, `artifact_kind`, and `role` (e.g., `diagnosis`, `plan`).

**Provenance rule:** `source_artifacts[]` records direct edges only — artifacts that this run directly parsed and validated. Transitive provenance is recovered by traversing upstream `source_artifacts[]` references. Dialogue's feedback capsule lists NS (direct consumer) but not AR (transitive — reached via NS's own `source_artifacts[]`).

## Discovery Algorithms

Two distinct algorithms serve different purposes within conversation-local scope (v1). Both operate on the conversation context available to the current skill invocation.

### Consumption Discovery

Used when a skill wants to consume an upstream capsule:

0. **For `dialogue_feedback` sentinels only:** Before scanning conversation context, check the durable store at `.claude/composition/feedback/` for matching artifacts by `subject_key`. If found, prefer the durable result per the source resolution precedence in [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence). If not found (or durable store unavailable), proceed to step 1.
1. Reverse-scan available conversation context newest-first for the expected sentinel.
2. Take the first match only.
3. Validate the candidate capsule schema.
4. If invalid, reject and stop — do not backtrack to older capsules. Proceed as if no capsule exists.
5. If no sentinel found, proceed without structural handoff.

Single-result, no-backtrack algorithm. Step 0 applies only to `dialogue_feedback` consumption; all other capsule types start at step 1.

### Staleness Discovery

Used to determine whether a consumed artifact has been superseded:

1. Scan available conversation context for all valid capsules matching a given `artifact_kind` and `subject_key`.
2. Index by `artifact_id` and `created_at`.
3. Compare against the consumed artifact to detect supersession.

Multi-scan algorithm that may return multiple results.

**Scope boundary:** "Available conversation context" means the context visible to the current skill invocation. Multi-session discovery is out of v1 scope.

## Staleness Detection

Consuming skills detect staleness and warn the user. Evaluate in priority order — the first matching status applies:

| Priority | Status | Condition | Consumer Behavior |
|----------|--------|-----------|-------------------|
| 1 | `superseded` | Positive evidence: newer same-kind same-subject artifact in available context | Prefer the newer one (by latest `created_at`). If the newest valid artifact has a schema validation failure, treat as `unknown` (Priority 2) — do not backtrack to an older valid artifact |
| 2 | `unknown` | Required direct `source_artifact` absent from context or unparseable | Do not block; fall back to current behavior |
| 3 | `stale_inputs` | Direct `source_artifact` has a newer visible superseder | Warn; suggest rebase |
| 4 | `current` | No superseder exists; all source_artifacts current | Proceed normally |

**Must-not-infer-current rule:** Do not infer `current` from missing evidence. If a required source artifact is absent from context, status is `unknown`, not `current`. `current` requires positive evidence that no superseder exists.

## File Persistence

Optional for AR capsules (`record_path` may be null or a path to `docs/reviews/`). Always null for NS in v1 — NS does not write files today (see [delivery.md](delivery.md#open-items)). Mandatory (non-null) for `dialogue_feedback` capsules — `record_path` MUST be non-null. See [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) for the normative enforcement rule, write-failure recovery procedure, and consumer-side contract. The schema definition (including the non-null field annotation) is in [capsule-contracts.md](capsule-contracts.md#contract-3-dialogue-feedback-capsule).

When present, `record_path` points to a durable file carrying the same artifact metadata in frontmatter. The file path is a locator, not the identity — `artifact_id` is the identity.

NS does not write files today. If `docs/plans/` is added later, use the same `artifact_id` scheme. See [delivery.md](delivery.md#open-items) for pending implementation items.
