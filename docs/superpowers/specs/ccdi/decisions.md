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

## Deferred Items

The following items were identified during consultation but deferred to implementation. They are tracked in [delivery.md](delivery.md#known-open-items) under the `delivery` authority.
