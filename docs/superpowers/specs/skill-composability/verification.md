---
module: verification
status: active
normative: true
authority: delivery
claims: [verification_strategy]
---

# Verification Strategy

Verification paths for normative MUST/MUST NOT claims in this spec. Each claim maps to one of: an automated test, a CI rule, a manual review protocol, or a documented deferral. Claims without a verification path are explicitly marked as gaps.

## Verification Instruments

| Instrument | Status | Reference |
|-----------|--------|-----------|
| `validate_composition_contract.py` | **P0 blocker — not implemented** | [delivery.md](delivery.md#open-items) item #6 |
| Materiality validation harness | **P0 blocker — not implemented** | [delivery.md](delivery.md#open-items) item #7 |
| Interim manual review protocol | Active | [foundations.md](foundations.md#versioning-and-drift-detection) |
| Sentinel version test scenarios | Specified below | — |

## Capsule Contract Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| AR capsule always emitted after prose output | [capsule-contracts.md](capsule-contracts.md#emission) | Behavioral: AR skill test — invoke AR, verify sentinel present in output |
| NS validates AR capsule if present; falls back to prose parsing if absent | [capsule-contracts.md](capsule-contracts.md#consumer-class) | Behavioral: two NS test cases — (1) AR capsule present → enriched handoff, (2) AR capsule absent → prose fallback + diagnostic emitted |
| Dialogue rejects invalid NS handoff but continues pipeline | [capsule-contracts.md](capsule-contracts.md#consumer-class-1) | Behavioral: two dialogue test cases — (1) valid handoff → enriched decomposition, (2) invalid handoff → rejection + normal pipeline proceeds |
| NS handoff emits one block per NS run (not per task) | [capsule-contracts.md](capsule-contracts.md#emission-1) | Behavioral: NS test — invoke NS with multiple tasks, verify single sentinel emitted containing `selected_tasks[]` list |
| Unknown sentinel version → reject capsule block, not skill session | [foundations.md](foundations.md#consumer-classes) | Behavioral: per-consumer test — inject `v999` sentinel, verify capsule rejected but skill invocation continues |
| `record_path` MUST be non-null for feedback capsules | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | `validate_composition_contract.py` — schema rule check |
| `material`/`suggested_arc` coherence constraint | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | Materiality harness — 24-case validity matrix |

## Routing and Materiality Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| Correction rules only fire on invalid tuples | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — 24-case validity matrix. Test both valid tuples (pass through uncorrected) and invalid tuples (corrected per rules 1-5) |
| `diagnosis` MUST NOT emit `next-steps` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| `planning` MUST NOT emit `adversarial-review` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| `evidence-only` MUST NOT emit AR, NS, or `ambiguous` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| Material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| Novelty veto: novel items bypass Tier 1, proceed through Tier 2 and Tier 3 | [routing-and-materiality.md](routing-and-materiality.md#novelty-veto-pre-check) | Materiality harness — §9.4 fixtures: novel item + Tier 1 pattern match → verify Tier 1 returns `no_match`, item reaches Tier 2/3 |
| Cross-tier guard: model-judged Tier 1 exclusion overridden by Tier 2 inclusion | [routing-and-materiality.md](routing-and-materiality.md#cross-tier-guard) | Materiality harness — §9.4 fixtures: item matching Tier 1 model exclusion + Tier 2 inclusion → verify `material: true` |
| Soft iteration budget: stop suggesting after 2 targeted loops per `lineage_root_id` | [routing-and-materiality.md](routing-and-materiality.md#soft-iteration-budget) | Behavioral: dialogue test — simulate 3-hop chain with same `lineage_root_id`, verify hop suggestion omitted after hop 2 |
| No auto-chaining: skills MUST NOT programmatically invoke another skill | [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) | Structural: review of skill stub text — verify no `/<skill>` invocation patterns in conditional logic. Platform architecture enforces at runtime |

## Lineage Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| Consumption discovery: reverse-scan newest-first, take first match only, no backtrack | [lineage.md](lineage.md#consumption-discovery) | Behavioral: two test scenarios — (1) context has [valid-older, valid-newer] → newer consumed; (2) context has [valid-older, invalid-newer] → no capsule consumed (not older) |
| Staleness detection priority ordering: superseded > unknown > stale_inputs > current | [lineage.md](lineage.md#staleness-detection) | Behavioral: four test scenarios — one per priority level. Verify first matching status applies |
| Must-not-infer-current rule: absent source_artifact → `unknown`, not `current` | [lineage.md](lineage.md#staleness-detection) | Behavioral: test scenario — required source_artifact absent from context → verify status is `unknown` |
| `lineage_root_id` immutability: never re-minted downstream | [lineage.md](lineage.md#key-propagation) | `validate_composition_contract.py` — verify all capsule schemas propagate `lineage_root_id` unchanged from upstream |
| Inheritance-first rule: only root of chain mints keys | [lineage.md](lineage.md#key-propagation) | Behavioral: multi-hop chain test — verify downstream skills inherit, not re-mint |

## Contract Drift Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| `implements_composition_contract: v1` present in participating stubs | [foundations.md](foundations.md#versioning-and-drift-detection) | `validate_composition_contract.py` — marker presence check |
| Stubs conform to contract's routing/materiality/lineage definitions | [foundations.md](foundations.md#versioning-and-drift-detection) | `validate_composition_contract.py` — semantic parity check |
| Contract changes accompanied by stub review | [foundations.md](foundations.md#versioning-and-drift-detection) | Interim manual review protocol — PR description checklist |

## Deferred Verification

| Claim | Source | Deferral Reason |
|-------|--------|-----------------|
| Tier 3 tautology filter model calibration | [pipeline-integration.md](pipeline-integration.md#three-tier-tautology-filter) | Deferred until v1 skill text is stable. **Pass criterion (when implemented):** The 4 Tier 3 examples in pipeline-integration.md (2 valid, 2 invalid) must all be classified correctly. Any misclassification = Tier 3 regression. Additional labeled cases may be added; the 4 examples are the minimum acceptance bar. |
| Tier 2 "reopens/contradicts resolved" | [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) | Deferred from v1 — NS handoff lacks explicit resolved-item set |
| Multi-session discovery | [lineage.md](lineage.md#discovery-algorithms) | Out of v1 scope — conversation-local only |
