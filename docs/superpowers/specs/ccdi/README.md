---
module: readme
status: active
normative: false
authority: supporting
---

# Claude Code Docs Injection (CCDI) — Spec

Modular specification for CCDI: automatic detection and injection of Claude Code extension documentation into Codex consultations.

**Source design document:** `docs/superpowers/specs/2026-03-20-ccdi-design.md`

## Authority Model

8 normative authorities govern the spec; this README is a non-normative supporting entry point. See [spec.yaml](spec.yaml) for the full manifest including precedence and boundary rules.

*(This table is an informative summary — see [spec.yaml](spec.yaml) for the authoritative source.)*

| Authority | Claims | Scope | Normative |
|-----------|--------|-------|-----------|
| `foundation` | architecture_rule | Cross-cutting architecture, design principles, resilience principle, topic hierarchy, component inventory, scope boundary | Yes |
| `data-model` | persistence_schema, architecture_rule | Topic inventory schema, version axes, overlay merge semantics, config schema, lifecycle | Yes |
| `classifier-contract` | behavior_contract, interface_contract | Two-stage pipeline, confidence levels, injection thresholds | Yes |
| `registry-contract` | behavior_contract, interface_contract | State machine, transitions, scheduling, semantic hints | Yes |
| `packet-contract` | behavior_contract, interface_contract | Fact packets, token budgets, citation format, rendering | Yes |
| `integration` | behavior_contract, interface_contract | CLI interface, data flows, prepare/commit, delegation | Yes |
| `delivery` | implementation_plan, verification_strategy | Rollout, testing, diagnostics | Yes |
| `decisions` | decision_record | Locked design decisions from Codex dialogues | Yes |
| `supporting` | *(none)* | README and reference material | No |

*Note: §pipeline-isolation-invariants-subset in integration.md contains behavioral invariants whose provenance is traced to decisions.md. The `elevated_sections` registration in spec.yaml is a cross-reference pointer, not an authority elevation — `claim_precedence` already ranks integration above decisions for `behavior_contract`.*

**Highest-risk review surface:** The classifier-registry boundary — where classifier output drives registry scheduling decisions. Changes to confidence semantics or injection thresholds in [classifier.md](classifier.md) directly affect scheduling behavior in [registry.md](registry.md).

## Reading Order

| # | File | Authority | Description |
|---|------|-----------|-------------|
| 1 | [foundations.md](foundations.md) | foundation | Architecture, design principles, resilience principle, topic hierarchy, scope boundary |
| 2 | [decisions.md](decisions.md) | decisions | Locked decisions from design and review dialogues with Codex |
| 3 | [data-model.md](data-model.md) | data-model | CompiledInventory schema, version axes, overlay merge, config, lifecycle |
| 4 | [classifier.md](classifier.md) | classifier-contract | Two-stage pipeline, confidence levels, injection thresholds, worked example |
| 5 | [registry.md](registry.md) | registry-contract | Topic registry state machine, scheduling rules, semantic hints, caches |
| 6 | [packets.md](packets.md) | packet-contract | Fact packet structure, token budgets, citation format, rendered output |
| 7 | [integration.md](integration.md) | integration | CLI interface, data flows, prepare/commit protocol, inventory generation |
| 8 | [delivery.md](delivery.md) | delivery | Rollout strategy, testing strategy, test matrices, diagnostics |

Note: The `supporting` authority (this README) is excluded from the reading order — it is entry point documentation, not a spec file.

## Cross-Reference Conventions

- Relative markdown links: `[classifier.md](classifier.md)`, `[data-model.md](data-model.md#alias)`
- Semantic kebab-case anchors: `#topic-record`, `#state-transitions`
- Source citations: `[ccdocs:<chunk_id>]` format within rendered packet examples
- Design doc section references: `§1`, `§2`, etc. refer to the source design document
