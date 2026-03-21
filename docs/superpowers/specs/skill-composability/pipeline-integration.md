---
module: pipeline-integration
status: active
normative: true
authority: pipeline
---

# Pipeline Integration

## Design Principle: Adapters Not Modes

Dialogue's internal interface uses a generic `upstream_handoff` state. Type-specific logic lives at the ingestion edge as adapters, not as decomposition modes. Adding a future upstream skill type means adding an adapter, not a new mode table entry.

## Two-Stage Admission

### Stage A — Detect and Validate (type-specific)

Reverse-scan conversation context newest-first for a known upstream sentinel (see [lineage.md](lineage.md#consumption-discovery) for the full consumption discovery algorithm; [capsule-contracts.md](capsule-contracts.md) for schema definitions). v1 recognizes:

| Sentinel | Producer | Adapter |
|----------|----------|---------|
| `<!-- next-steps-dialogue-handoff:v1 -->` | next-steps | NS adapter |

If a sentinel is detected, validate the capsule schema against the expected format. If invalid, reject the capsule (strict consumer class — see [foundations.md](foundations.md#consumer-classes)) and proceed as if no upstream handoff exists.

**Note:** The distinction between "NS never ran" and "NS ran but did not suggest /dialogue" is invisible to dialogue at Stage A — both present as "no sentinel found." Proceed identically in both cases. The user's decision to invoke /dialogue directly is sufficient authorization regardless of whether NS emitted a handoff.

Future upstream skills register new sentinels and adapters here. The pipeline below Stage A is unchanged.

### Stage B — Normalize to `upstream_handoff` (generic)

The adapter normalizes the validated capsule into a generic `upstream_handoff` pipeline state with capability flags:

| Capability Flag | Meaning | NS Adapter Sets |
|----------------|---------|-----------------|
| `decomposition_seed` | Can seed decomposition fields (planning_question, assumptions, key_terms, ambiguities) | `true` |
| `gatherer_seed` | Can seed gatherer search terms with task/finding entities | `true` |
| `briefing_context` | Can inject source_findings and decision_gates into briefing assembly | `true` |
| `tautology_filter_applied` | Confirms items passed through the [tautology filter](#three-tier-tautology-filter) during decomposition seeding — required precondition for [materiality evaluation](routing-and-materiality.md#material-delta-gating) | Set to `true` after tautology filter runs successfully during `handoff_enriched` decomposition; `false` otherwise |

The pipeline gates enrichment on what the adapter provides, not what type produced it. A future adapter that provides `gatherer_seed` but not `decomposition_seed` would enrich gatherer prompts without affecting decomposition.

## Decomposition Behavior

| Condition | Behavior |
|-----------|----------|
| `--plan` set, no `upstream_handoff` | `raw_input` — decompose from user's question (current behavior) |
| `--plan` set, `upstream_handoff` with `decomposition_seed` | `handoff_enriched` — seed decomposition from upstream context |
| `--plan` set, `upstream_handoff` without `decomposition_seed` | `raw_input` — decompose from question; upstream context available to later stages via other capability flags |
| `--plan` not set, `upstream_handoff` present | No decomposition; upstream context available to later steps via capability flags |
| `--plan` not set, no `upstream_handoff` | Current behavior unchanged |

## Enriched Decomposition Seeding

When `decomposition_seed` is available, handoff context supplements (not replaces) the decomposition from the user's actual question:

| Decomposition Field | `raw_input` Source | `handoff_enriched` Source |
|---------------------|-------------------|--------------------------|
| `planning_question` | Decompose from raw question | Derive from `focus_question` + `done_when` |
| `assumptions` | Extract from question | Seed from `source_findings` (each finding implies a testable assumption) |
| `key_terms` | Extract from question | Seed from task context entities — names, concepts, file paths from findings |
| `ambiguities` | Extract from question | Seed from `decision_gates` conditions |

## Pipeline Threading

The NS handoff threads through the full `/dialogue` pipeline via the generic `upstream_handoff` state. Each stage consumes capability flags, not the NS schema directly:

| Pipeline Stage | Capability Consumed | How Upstream Context Is Used |
|----------------|--------------------|-----------------------------|
| Pre-Step 0 (Stage A/B) | — | Parse sentinel → validate → normalize to `upstream_handoff` via adapter |
| Step 0 | `decomposition_seed` | Seed planning_question, assumptions, key_terms, ambiguities |
| Step 2 | `gatherer_seed` | Gatherer prompts enriched with task names, finding entities, decision gate conditions |
| Step 3 | `briefing_context` | Deterministic projection of source_findings and decision_gates into briefing Context section |
| Step 3c | `briefing_context` | Zero-output fallback preserves upstream context as sole grounding |

**Boundary clarification:** The `upstream_handoff` state couples to pipeline stages documented in the dialogue skill's SKILL.md. This is documented interface coupling through a generic internal interface, not NS-specific coupling. Items emerging from dialogue are classified via [routing and materiality](routing-and-materiality.md#routing-classification) rules. For skill text changes implementing this pipeline, see [delivery.md](delivery.md#skill-text-changes).

## Posture Precedence

```
explicit --posture > upstream_handoff recommended_posture > default collaborative
```

**Deferred:** `--profile` (multi-phase posture profiles) is deferred from v1. When implemented, it would sit between `--posture` and `upstream_handoff` in the precedence chain. See [delivery.md](delivery.md#open-items).

Upstream handoffs do not derive multi-phase profiles from a single posture hint. If future handoff-driven phases are needed, upstream skills would emit `recommended_phases[]`.

## Three-Tier Tautology Filter

In `handoff_enriched` mode, prevent echo of upstream framing:

| Tier | Filter | Rule |
|------|--------|------|
| 1 | **Question set** | Do not restate `focus_question` or the user's raw question as an assumption |
| 2 | **Plan metadata set** | Do not parrot task descriptions, `done_when` conditions, or dependency statements |
| 3 | **Soft echo set** | `source_findings` can inspire derived assumptions but not be restated verbatim. A derived assumption MUST operationalize the finding (make it testable against the codebase), not merely reword it |

### Tier 3 Examples

Given source finding `F1: "NS handoff deeply couples to dialogue's internal pipeline stages"`:

| Derived Assumption | Valid? | Reason |
|--------------------|--------|--------|
| "The NS handoff references dialogue's internal pipeline stages" | No — restatement | Restates the finding without operationalizing |
| "Dialogue's pipeline stages could be refactored without breaking the NS handoff contract" | Yes | Makes the finding testable against the codebase |
| "The pipeline stages referenced by the NS handoff are documented as public interface" | Yes | Tests whether coupling is to a public or internal surface |
| "The NS handoff couples to dialogue's pipeline" | No — restatement | Removes specificity without adding testability |
