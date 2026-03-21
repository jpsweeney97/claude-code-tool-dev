---
module: readme
status: active
normative: false
authority: supporting
---

# Skill Composability Spec

Structural contracts for composing adversarial-review (AR), next-steps (NS), and dialogue skills into an analysis pipeline with feedback loops. Enables machine-referenceable data exchange through capsules and sentinels while preserving each skill's standalone operation.

**Source:** [2026-03-18-skill-composability-design.md](../2026-03-18-skill-composability-design.md)

## Authority Model

| Authority | Description | Default Claims |
|-----------|-------------|----------------|
| `foundation` | Composability model, scope, consumer classes, cross-cutting invariants | `architecture_rule` |
| `decisions` | Locked design decisions D1-D5 | `decision_record` |
| `capsule-contract` | Capsule schemas, sentinels, wire format | `interface_contract` |
| `pipeline` | Adaptive --plan, adapter pattern, decomposition, tautology filter | `behavior_contract` |
| `routing` | Routing classification, material-delta gating tiers, affected-surface validity matrix, guardrails, thread freshness, feedback persistence | `behavior_contract`, `enforcement_mechanism` |
| `lineage` | Identity keys, DAG, discovery, staleness | `interface_contract`, `behavior_contract` |
| `delivery-plan` | Implementation plan, open items, deferred work | `implementation_plan` |
| `delivery-verification` | Verification paths, test instruments, deferred verification | `verification_strategy` |
| `supporting` | Navigation, reference | (none) |

### Precedence

- Normative files take precedence over non-normative
- `behavior_contract`: routing > pipeline > lineage
- `interface_contract`: capsule-contract > lineage
- Fallback: foundation > capsule-contract > routing > pipeline > lineage > decisions > delivery-plan > delivery-verification > supporting

### Boundary Rules

| When This Changes | Also Review |
|-------------------|-------------|
| capsule-contract | pipeline, routing, lineage |
| routing | pipeline, lineage, delivery-plan |
| lineage | capsule-contract, routing, delivery-plan |
| pipeline | capsule-contract, routing, delivery-plan |

## Reading Order

| # | File | Authority | Description |
|---|------|-----------|-------------|
| 1 | [foundations.md](foundations.md) | foundation | Problem, scope, composability model, consumer classes, authority layers |
| 2 | [decisions.md](decisions.md) | decisions | Design decisions D1-D5 with alternatives considered |
| 3 | [capsule-contracts.md](capsule-contracts.md) | capsule-contract | AR capsule, NS handoff, and feedback capsule schemas |
| 4 | [lineage.md](lineage.md) | lineage | Identity keys, artifact IDs, DAG structure, discovery, staleness |
| 5 | [pipeline-integration.md](pipeline-integration.md) | pipeline | Adapter pattern, two-stage admission, decomposition, tautology filter |
| 6 | [routing-and-materiality.md](routing-and-materiality.md) | routing | Routing classification, material-delta tiers, validity matrix, guardrails |
| 7 | [delivery.md](delivery.md) | delivery-plan | Skill text changes, open items |
| 8 | [verification.md](verification.md) | delivery-verification | Verification paths for normative claims, test instruments, deferred verification |

## Cross-Reference Conventions

- Relative markdown links with semantic kebab-case anchors
- `[file.md](file.md#anchor)` format
- Anchors match heading text, lowercased and hyphenated
