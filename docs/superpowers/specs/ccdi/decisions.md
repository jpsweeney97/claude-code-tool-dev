---
module: decisions
status: active
normative: true
authority: decisions
---

# CCDI Design Decisions

Locked decisions from two Codex consultation threads.

## Design Dialogue

Thread: `019d0c24-29c9-7bf1-a2f4-d50f3056553b` (7 turns)

| Turn | Topic | Decision |
|------|-------|----------|
| 1 | Approach selection | Approach 1 (subagent + scout) recommended; do NOT put DocSearch in scout pipeline |
| 2 | Component design | Hierarchical topic inventory, topic registry with lifecycle state, compact fact packets |
| 3 | Optimization | Detect aggressively/inject conservatively, search wide/inject narrow, session-local caching |
| 4 | Spec-level detail | Full data models, classifier walkthrough, registry transition rules, packet format |
| 5 | Simplification | Drop inverted indexes, keep alias objects, persist semantics / derive performance |
| 6 | Integration gaps | Coarse-grained CLI commands, optional cross-plugin dependency, MCP client for inventory, CCDI-lite for /codex |
| 7 | Testing review | Boundary contract tests, false-positive contexts, registry partial-coverage, external failure paths |

## Review Dialogue

Thread: `019d0c5d-59d7-7ec2-9a90-c0e6b44bdcd0` (6 turns)

System design review surfaced 7 findings and 2 tensions; 6-turn dialogue resolved all major items:

| Turn | Resolution | Convergence type | Confidence |
|------|-----------|-----------------|------------|
| 1 | Semantic hints with claim-index refs (not topic_ids) for prescriptive-claim detection | Convergence | High |
| 2 | ccdi_seed delegation-envelope field (file path) with sentinel-wrapped registry seed for handoff | Convergence | High |
| 2 | CLI-only typed config file for tuning parameters | Convergence | High |
| 3 | Prepare/commit split (Step 5.5 / Step 7.5) for turn-loop integration | Convergence | High |
| 3 | Durable vs attempt-local registry states | Convergence | High |
| 4 | Scout target always beats CCDI targeting | Convergence | High |
| 5 | Four version axes for schema evolution (three compatibility + one instance) | Concession | Medium |
| 5 | Four-layer test strategy with ccdi_trace replay harness (Layer 1: unit, 2a: replay, 2b: agent sequence, 3: shadow) | Concession | Medium |
| 6 | Staged rollout: initial CCDI first, mid-dialogue in shadow mode | Concession | Medium |

## External Contract Compatibility

| Decision | Rationale |
|----------|-----------|
| `ccdi_seed` delegation envelope field is additive to consultation contract §6 — no modification to §6 required | `ccdi_seed` is an optional field; its absence means mid-dialogue CCDI is disabled. Existing envelope consumers ignore unknown fields. |

## Normative Decision Constraints

The following locked decisions have implementation implications. Each is stated as a testable invariant. Per `spec.yaml` claim_precedence, component contracts (classifier-contract, registry-contract, packet-contract, integration) outrank decisions for `behavior_contract` and `interface_contract` claims. The invariants below are authoritative only when component contracts are silent — when a component contract specifies the same behavior, the component contract is the normative source and these rows serve as cross-references.

| Decision | Invariant | Test Reference |
|----------|-----------|----------------|
| Do NOT put DocSearch in scout pipeline (Design Turn 1) | Does not invoke `topic_inventory.py` or `search_docs` for CCDI purposes — see [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants) for the authoritative behavioral constraint. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Semantic hints use claim-index refs, not topic_ids (Review Turn 1) | CLI classifies `claim_excerpt` to resolve `topic_key`; does not accept `topic_key` as direct hint input — see [registry.md#semantic-hints](registry.md#semantic-hints) for the authoritative interface contract. | delivery.md [Replay Harness](delivery.md#replay-harness-teststestccdireplaypy): `hint_unknown_topic_ignored.replay.json` |
| CLI-only typed config file (Review Turn 2) | Agent does not read `*ccdi_config*` files — see [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants) for the authoritative behavioral constraint. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Registry seed in sentinel block (Design Dialogue Turn 3 / Review Dialogue Turn 2) | Registry seed transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags — see [integration.md#registry-seed-handoff](integration.md#registry-seed-handoff) for the authoritative handoff contract. | delivery.md [Boundary Contract Tests](delivery.md#boundary-contract-tests-testccdicontractspy): sentinel extraction |
| Scout target always beats CCDI targeting (Review Turn 4) | Scout-sourced repo evidence takes precedence when both produce content for the same turn — see [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants) for the authoritative behavioral constraint (under `behavior_contract` authority). Design principle: [foundations.md#design-principles](foundations.md#design-principles). | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Staged rollout: initial CCDI first, mid-dialogue in shadow mode (Review Turn 6) | Does not commit injections or deferrals until graduation gate approves — see [integration.md#shadow-mode-registry-invariant](integration.md#shadow-mode-registry-invariant) for the authoritative behavioral constraint. Automatic suppression IS permitted in shadow mode. | [integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) (behavioral contract), delivery.md [Graduation Protocol and Kill Criteria](delivery.md#graduation-protocol-and-kill-criteria), Layer 2b graduation gate tests |
| Agent pre-dispatch threshold is a fixed heuristic (Spec Review Round 6) | Agent-side injection threshold uses hardcoded defaults; divergence from config overrides is intentional — see [data-model.md#configuration-ccdiconfigjson](data-model.md#configuration-ccdiconfigjson) config consumer scope note for the authoritative specification. | [integration.md](integration.md) CCDI-lite and Full CCDI flows, [data-model.md](data-model.md#configuration-ccdiconfigjson) config consumer scope note |

## Deferred Items

The following items were identified during consultation but deferred to implementation. They are tracked in [delivery.md](delivery.md#known-open-items) under the `delivery` authority.
