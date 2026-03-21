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

| Resolution | Convergence type | Confidence |
|-----------|-----------------|------------|
| Semantic hints with claim-index refs (not topic_ids) for prescriptive-claim detection | Convergence | High |
| ccdi_seed delegation-envelope field (file path) with sentinel-wrapped registry seed for handoff | Convergence | High |
| Prepare/commit split (Step 5.5 / Step 7.5) for turn-loop integration | Convergence | High |
| Durable vs attempt-local registry states | Convergence | High |
| CLI-only typed config file for tuning parameters | Convergence | High |
| Scout target always beats CCDI targeting | Convergence | High |
| Four version axes for schema evolution (three compatibility + one instance) | Concession | Medium |
| Three-layer test strategy with ccdi_trace replay harness | Concession | Medium |
| Staged rollout: initial CCDI first, mid-dialogue in shadow mode | Concession | Medium |

## External Contract Compatibility

| Decision | Rationale |
|----------|-----------|
| `ccdi_seed` delegation envelope field is additive to consultation contract §6 — no modification to §6 required | `ccdi_seed` is an optional field; its absence means mid-dialogue CCDI is disabled. Existing envelope consumers ignore unknown fields. |

## Normative Decision Constraints

The following locked decisions have implementation implications. Each is stated as a testable invariant.

| Decision | Invariant | Test Reference |
|----------|-----------|----------------|
| Do NOT put DocSearch in scout pipeline (Design Turn 1) | `execute_scout` and `process_turn` MUST NOT invoke any `topic_inventory.py` command or `search_docs` for CCDI purposes. CCDI search and context-injection search are separate pipelines. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Semantic hints use claim-index refs, not topic_ids (Review Turn 1) | The CLI MUST classify `claim_excerpt` to resolve `topic_key`; it MUST NOT accept `topic_key` as direct hint input from the agent. Hints contain `claim_excerpt`, not resolved keys. | delivery.md [Replay Harness](delivery.md#replay-harness-teststest_ccdi_replaypy): `hint_unknown_topic_ignored.replay.json` |
| CLI-only typed config file (Review Turn 2) | The agent MUST NOT Read files matching `*ccdi_config*`. All configuration is consumed exclusively by CLI tools via `--config` flag. | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
| Registry seed in sentinel block (Design Turn 3 / Review Turn 2) | Registry seed is transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags in `ccdi-gatherer` output. The delegation envelope carries a `ccdi_seed` file path, not inline JSON. | delivery.md [Boundary Contract Tests](delivery.md#boundary-contract-tests-test_ccdi_contractspy): sentinel extraction |
| Scout target always beats CCDI targeting (Review Turn 4) | When both CCDI and context-injection produce content for the same turn, scout-sourced repo evidence takes precedence. CCDI content is placed under `## Material` source-separated from repo evidence. | [foundations.md](foundations.md#design-principles): premise enrichment, not retargeting |
| Staged rollout: initial CCDI first, mid-dialogue in shadow mode (Review Turn 6) | Mid-dialogue CCDI MUST NOT commit registry state changes (`--mark-injected`) until the shadow-mode graduation gate approves. Graduation requires `graduation.json` with `status: "approved"`. | delivery.md [Shadow Mode Gate](delivery.md#shadow-mode-gate), Layer 2b graduation gate tests |

## Deferred Items

The following items were identified during consultation but deferred to implementation. They are tracked in [delivery.md](delivery.md#known-open-items) under the `delivery` authority.
