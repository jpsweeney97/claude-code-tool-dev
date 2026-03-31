---
module: readme
status: active
normative: false
authority: supporting
---

# Codex Collaboration Spec

Modular specification for `codex-collaboration`, a Claude Code plugin that gives Claude structured second-opinion, dialogue, and delegation capabilities via OpenAI Codex. Compiled from the approved design document at [`docs/superpowers/specs/2026-03-27-codex-collaboration-plugin-design.md`](../2026-03-27-codex-collaboration-plugin-design.md).

The design uses a split-runtime model: one long-lived advisory App Server runtime for consultation and dialogue, and one ephemeral execution App Server runtime per delegation job, always isolated in its own git worktree. A control plane inside the plugin mediates all requests; Claude never interacts with App Server directly.

## Relationship to Official Plugin

The official OpenAI plugin (`openai/codex-plugin-cc`) provides a packaged local integration: local Codex CLI, local app server, shared auth and config, same-checkout execution, and native review, task, and thread utilities.

This spec takes a different architectural approach. `codex-collaboration` centers a mediating control plane, structured capability flows, durable lineage, isolated execution, and explicit promotion back into the primary workspace.

Where the surfaces overlap, the overlap is intentional. This spec adds structured contracts, trust enforcement, and recovery semantics that the official plugin does not provide.

The official plugin is reference context for understanding the Codex integration landscape, not the architectural shell this spec converges toward.

Official plugin comparison is pinned to upstream commit `9cb4fe4`. If upstream changes materially, re-evaluate comparison claims.

## Authority Model

| Authority | Concern | Default Claims |
|---|---|---|
| **foundation** | Scope, trust model, runtime domains, flow baselines, defaults | `architecture_rule` |
| **contracts** | MCP tool surface, data model types, audit event schema, response shapes | `interface_contract` |
| **promotion-contract** | Promotion state machine, preconditions, typed rejections, artifact integrity | `behavior_contract` |
| **advisory-policy** | Advisory runtime lifecycle, policy fingerprints, widening/narrowing, rotation | `behavior_contract`, `enforcement_mechanism` |
| **recovery-contract** | Operation journal, audit log behavior, crash recovery, concurrency, retention | `behavior_contract` |
| **delivery** | Build sequence, compatibility policy, test strategy | `implementation_plan`, `verification_strategy` |
| **decisions** | Greenfield rules, accepted tradeoffs, open questions | `decision_record` |
| **supporting** | Overview, reading order | — |

**Precedence (summary — [spec.yaml](spec.yaml) is authoritative):** Protocol files win for their respective behavioral domains. `contracts` wins for all `interface_contract` claims. `advisory-policy` wins for `enforcement_mechanism` claims. `foundation` is the fallback for architectural questions. `decisions` participates only via fallback order, not claim-specific precedence.

## Reading Order

| # | File | Authority | Description |
|---|---|---|---|
| 1 | [foundations.md](foundations.md) | foundation | Scope, trust model, runtime domains, approval invariant, core flow baselines, chosen defaults |
| 2 | [contracts.md](contracts.md) | contracts | MCP tool surface, logical data model types, audit event schema, typed response shapes |
| 3 | [promotion-protocol.md](promotion-protocol.md) | promotion-contract | Promotion preconditions, state machine, artifact hash integrity, rollback |
| 4 | [advisory-runtime-policy.md](advisory-runtime-policy.md) | advisory-policy | Policy fingerprints, privilege widening/narrowing, freeze-and-rotate, reap conditions |
| 5 | [recovery-and-journal.md](recovery-and-journal.md) | recovery-contract | Two-log architecture, idempotency keys, crash recovery, concurrency limits, retention |
| 6 | [delivery.md](delivery.md) | delivery | Build sequence, compatibility policy, plugin structure, test strategy |
| 7 | [dialogue-supersession-benchmark.md](dialogue-supersession-benchmark.md) | delivery | Fixed-corpus benchmark contract for retiring context-injection by default |
| 8 | [decisions.md](decisions.md) | decisions | Greenfield rules, accepted tradeoffs, architecture option analysis, open questions |

## Cross-Reference Conventions

- Relative markdown links with semantic kebab-case anchors (e.g., `[promotion protocol](promotion-protocol.md#preconditions)`)
- No section numbers as anchors
- Anchors stable across revisions unless the section's meaning changes
