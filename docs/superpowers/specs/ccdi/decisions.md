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
| Do NOT put DocSearch in scout pipeline (Design Turn 1) | `execute_scout` and `process_turn` MUST NOT invoke any `topic_inventory.py` command or `search_docs` for CCDI purposes. CCDI search and context-injection search are separate pipelines. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Semantic hints use claim-index refs, not topic_ids (Review Turn 1) | The CLI MUST classify `claim_excerpt` to resolve `topic_key`; it MUST NOT accept `topic_key` as direct hint input from the agent. Hints contain `claim_excerpt`, not resolved keys. | delivery.md [Replay Harness](delivery.md#replay-harness-teststest_ccdi_replaypy): `hint_unknown_topic_ignored.replay.json` |
| CLI-only typed config file (Review Turn 2) | The agent MUST NOT Read files matching `*ccdi_config*`. All configuration is consumed exclusively by CLI tools via `--config` flag. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Registry seed in sentinel block (Design Dialogue Turn 3 / Review Dialogue Turn 2) | Registry seed is transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags in `ccdi-gatherer` output. The delegation envelope carries a `ccdi_seed` file path, not inline JSON. | delivery.md [Boundary Contract Tests](delivery.md#boundary-contract-tests-test_ccdi_contractspy): sentinel extraction |
| Scout target always beats CCDI targeting (Review Turn 4) | When both CCDI and context-injection produce content for the same turn, scout-sourced repo evidence takes precedence. CCDI content is placed under `## Material` source-separated from repo evidence. | [foundations.md](foundations.md#design-principles): premise enrichment, not retargeting |
| Staged rollout: initial CCDI first, mid-dialogue in shadow mode (Review Turn 6) | Mid-dialogue CCDI MUST NOT commit injections (`--mark-injected`) or deferrals (`--mark-deferred`) until the shadow-mode graduation gate approves. Automatic suppression via `build-packet` empty output IS permitted in shadow mode — it reflects classifier-driven state, not agent commitment. In shadow mode, the prepare cycle runs for diagnostic purposes. Graduation requires `graduation.json` with `status: "approved"`. | [integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) (behavioral contract), delivery.md [Shadow Mode Gate](delivery.md#shadow-mode-gate), Layer 2b graduation gate tests |
| Agent pre-dispatch threshold is a fixed heuristic (Spec Review Round 6) | The agent-side injection threshold check uses hardcoded defaults (1 high-confidence, 2+ medium same-family). Divergence from `initial_threshold_*` config overrides is intentional — the agent MUST NOT observe configured threshold values. | [integration.md](integration.md) CCDI-lite and Full CCDI flows, [data-model.md](data-model.md#configuration-ccdi_configjson) config consumer scope note |

## Deferred Items

The following items were identified during consultation but deferred to implementation. They are tracked in [delivery.md](delivery.md#known-open-items) under the `delivery` authority.
