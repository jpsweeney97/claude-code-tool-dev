---
module: readme
status: active
normative: false
authority: supporting
---

# Engram Spec

Modular specification for Engram, a federated persistence and observability layer for Claude Code. Compiled from the approved design document at `docs/superpowers/specs/2026-03-16-engram-design.md`.

Engram consolidates three existing plugins — handoff (session state), ticket (work tracking), and the learning pipeline (knowledge capture) — into a single marketplace plugin with shared identity, indexing, and cross-subsystem coordination.

## Authority Model

| Authority | Concern | Default Claims |
|---|---|---|
| **foundation** | System identity, core invariant, design principles | `architecture_rule` |
| **data-contract** | Types, storage layout, reader protocol, query API | `interface_contract`, `persistence_schema` |
| **operations** | Cross-subsystem flows, save orchestration, failure handling | `behavior_contract` |
| **skill-contract** | Skill surface, chain protocol, trigger differentiation | `behavior_contract` |
| **enforcement** | Hooks, trust injection, protected paths, autonomy | `enforcement_mechanism` |
| **delivery** | Build sequence, migration, testing, rollback | `implementation_plan`, `verification_strategy` |
| **decisions** | Risks, open questions, deferred decisions | `decision_record` |
| **supporting** | Overview, reading order, and reference material | — |

**Precedence (summary — [spec.yaml](spec.yaml) is authoritative):** `operations` > `skill-contract` > `foundation` > `decisions` for `behavior_contract` claims. `data-contract` wins for all `interface_contract` and `persistence_schema` claims. See `spec.yaml` for full precedence and boundary rules.

## Reading Order

| # | File | Authority | Description |
|---|---|---|---|
| 1 | [foundations.md](foundations.md) | foundation | Core invariant (index-not-mutate), shadow authority anti-pattern, package structure, design principles |
| 2 | [types.md](types.md) | data-contract | RecordRef, RecordMeta, envelopes, lesson-meta, idempotency, write concurrency |
| 3 | [storage-and-indexing.md](storage-and-indexing.md) | data-contract | Dual-root storage layout, TTL, NativeReader protocol, query API, degradation model |
| 4 | [operations.md](operations.md) | operations | Cross-subsystem flows (defer, distill, triage, promote, search, timeline), save orchestration, failure handling |
| 5 | [skill-surface.md](skill-surface.md) | skill-contract | 13 skills table, chain protocol, save orchestration rules, trigger differentiation |
| 6 | [enforcement.md](enforcement.md) | enforcement | Hooks, protected-path enforcement, trust injection, SessionStart, autonomy model |
| 7 | [delivery.md](delivery.md) | delivery | Build sequence (Steps 0a–5), migration strategy, testing, rollback, success criteria |
| 8 | [decisions.md](decisions.md) | decisions | Named risks, open questions, deferred decisions |

## Cross-Reference Conventions

- Relative markdown links with semantic kebab-case anchors (e.g., `[core invariant](foundations.md#core-invariant)`)
- No section numbers as anchors
- Anchors stable across revisions unless the section's meaning changes
