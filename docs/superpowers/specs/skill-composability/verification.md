---
module: verification
status: active
normative: true
authority: delivery
---

# Verification Strategy

Verification paths for normative MUST/MUST NOT claims in this spec. Each claim maps to one of: an automated test, a CI rule, a manual review protocol, or a documented deferral. Claims without a verification path are explicitly marked as gaps.

## Verification Instruments

| Instrument | Status | Reference |
|-----------|--------|-----------|
| `validate_composition_contract.py` | **P0 blocker — not implemented** | [delivery.md](delivery.md#open-items) item #6 |
| Materiality validation harness | **P0 blocker — not implemented** | [delivery.md](delivery.md#open-items) item #7 |
| Interim manual review protocol (contract drift) | Active | [foundations.md](foundations.md#versioning-and-drift-detection) |
| Interim manual review protocol (materiality) | Active | See below |
| Sentinel version test scenarios | Specified below | — |
| Standalone coherence test (3-case) | Active (interim) | See Capsule Contract Verification table |
| Grep-based CI checks (contract marker, auto-chaining) | Active (interim) | See Contract Drift and Routing Verification tables |

### Interim Materiality Verification Protocol

Until the materiality harness is implemented, any implementation of materiality evaluation logic MUST be manually walked through:

1. The 24-case validity matrix (3 `affected_surface` values × 2 `material` values × 4 `suggested_arc` values). For each case: verify the tuple either passes through uncorrected (valid) or is corrected per rules 1-5 (invalid).
2. The 4 consequence prohibitions: `diagnosis` → no `next-steps`; `planning` → no `adversarial-review`; `evidence-only` → no AR/NS/`ambiguous`; material `diagnosis`/`planning` → no silent `dialogue_continue`.
3. The novelty veto: one case where a novel item pattern-matches a Tier 1 exclusion class → verify Tier 1 returns `no_match`.
4. The cross-tier guard: one case where Tier 1 model exclusion is overridden by Tier 2 inclusion → verify `material: true`.

The PR description MUST confirm this walk-through was completed. This protocol is a P0 prerequisite for merging materiality implementation.

## Capsule Contract Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| AR capsule always emitted after prose output | [capsule-contracts.md](capsule-contracts.md#emission) | Behavioral: AR skill test — invoke AR, verify sentinel present in output |
| NS validates AR capsule if present; falls back to prose parsing if absent or invalid | [capsule-contracts.md](capsule-contracts.md#consumer-class) | Behavioral: three NS test cases — (1) AR capsule present → enriched handoff, (2) AR capsule absent → prose fallback + diagnostic emitted, (3) AR capsule present but invalid → schema rejection + prose fallback + diagnostic emitted |
| NS MUST omit `source_artifacts` entries for absent/invalid AR capsule in fallback | [capsule-contracts.md](capsule-contracts.md#consumer-class) | Behavioral: in NS test cases (2) and (3) above, verify emitted NS handoff contains no `source_artifacts` entry referencing an AR `artifact_id` |
| Dialogue rejects invalid NS handoff but continues pipeline | [capsule-contracts.md](capsule-contracts.md#consumer-class-1) | Behavioral: two dialogue test cases — (1) valid handoff → enriched decomposition, (2) invalid handoff → rejection + normal pipeline proceeds |
| NS handoff emits one block per NS run (not per task) | [capsule-contracts.md](capsule-contracts.md#emission-1) | Behavioral: NS test — invoke NS with multiple tasks, verify single sentinel emitted containing `selected_tasks[]` list |
| Unknown sentinel version → reject capsule block, not skill session | [capsule-contracts.md](capsule-contracts.md#unknown-version-behavior) | Behavioral: per-consumer test — inject `v999` sentinel for each consumer scenario: (1) NS consuming unknown-version AR capsule, (2) Dialogue consuming unknown-version NS handoff, (3) AR consuming unknown-version feedback capsule, (4) NS consuming unknown-version feedback capsule. Verify capsule rejected but skill invocation continues with class-appropriate fallback |
| `record_path` MUST be non-null for feedback capsules | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | Behavioral (interim): dialogue test — invoke dialogue, verify emitted feedback capsule has non-null `record_path` pointing to a valid `.claude/composition/feedback/` path. Also verify write-failure path emits `record_status: write_failed` (not `record_path: null`). `validate_composition_contract.py` adds automated schema enforcement when implemented |
| `material`/`suggested_arc` coherence constraint | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | Standalone (interim): verify the 3 invalid `suggested_arc` values when `material: false` (`adversarial-review`, `next-steps`, `ambiguous`) are corrected to `dialogue_continue`. Bounded test — 3 cases. Full 24-case validity matrix via materiality harness when implemented |
| Emission-time enforcement: correction pipeline runs before capsule assembly | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Behavioral: construct feedback capsule assembly path, verify all `feedback_candidates[]` entries reflect post-correction state |

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
| Soft iteration budget: stop suggesting after 2 targeted loops per `lineage_root_id` | [routing-and-materiality.md](routing-and-materiality.md#soft-iteration-budget) | Behavioral: dialogue test — simulate 3-hop chain with same `lineage_root_id`, verify hop suggestion omitted after hop 2. Test fixture: pre-seed conversation context with 2 completed cross-skill hop artifacts (each with matching `lineage_root_id` and distinct `artifact_kind` transitions). Fixture format: YAML capsule blocks injected into test conversation context |
| No auto-chaining: skills MUST NOT programmatically invoke another skill | [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) | (1) Structural: review of skill stub text — verify no `/<skill>` invocation patterns in conditional logic. (2) Automated (interim): grep-based CI check on stub files — fail if `/<adversarial-review>`, `/<next-steps>`, or `/<dialogue>` patterns appear in conditional or feedback capsule processing blocks. Platform architecture provides runtime enforcement |
| Posture precedence: `--posture > --profile > upstream_handoff > default` | [pipeline-integration.md](pipeline-integration.md#posture-precedence) | Behavioral: two dialogue test scenarios — (1) `upstream_handoff.recommended_posture` set + explicit `--posture` flag → verify explicit flag wins, (2) `upstream_handoff.recommended_posture` set, no `--posture`/`--profile` → verify handoff posture applied |
| Thread continuation: new artifact → new thread | [routing-and-materiality.md](routing-and-materiality.md#thread-continuation-vs-fresh-start) | Behavioral: two dialogue test scenarios — (1) new NS artifact in context → verify fresh `/dialogue` invocation with new briefing (not thread continuation), (2) same goal + same snapshot set + operational termination → verify thread continuation is permitted |

## Lineage Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| Consumption discovery: reverse-scan newest-first, take first match only, no backtrack | [lineage.md](lineage.md#consumption-discovery) | Behavioral: two test scenarios — (1) context has [valid-older, valid-newer] → newer consumed; (2) context has [valid-older, invalid-newer] → no capsule consumed (not older) |
| Staleness detection priority ordering: superseded > unknown > stale_inputs > current | [lineage.md](lineage.md#staleness-detection) | Behavioral: four test scenarios — one per priority level. Verify first matching status applies |
| Must-not-infer-current rule: absent source_artifact → `unknown`, not `current` | [lineage.md](lineage.md#staleness-detection) | Behavioral: test scenario — required source_artifact absent from context → verify status is `unknown` |
| `lineage_root_id` immutability: never re-minted downstream | [lineage.md](lineage.md#key-propagation) | Behavioral (interim): multi-hop chain test — assert `lineage_root_id` value equality (exact string match) across all hops, not just inheritance pattern. `validate_composition_contract.py` adds automated schema enforcement when implemented |
| Inheritance-first rule: only root of chain mints keys | [lineage.md](lineage.md#key-propagation) | Behavioral: multi-hop chain test — verify downstream skills inherit `subject_key`, `topic_key`, and `lineage_root_id` from upstream, not re-mint from their own basis fields |

## Contract Drift Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| `implements_composition_contract: v1` present in participating stubs | [foundations.md](foundations.md#versioning-and-drift-detection) | Automated (interim): `grep -l 'implements_composition_contract: v1'` against known stub paths (adversarial-review, next-steps, dialogue skill files). Fail if any participating stub is missing the marker. `validate_composition_contract.py` adds full semantic validation when implemented |
| Stubs conform to contract's routing/materiality/lineage definitions | [foundations.md](foundations.md#versioning-and-drift-detection) | `validate_composition_contract.py` — semantic parity check |
| Contract changes accompanied by stub review | [foundations.md](foundations.md#versioning-and-drift-detection) | Interim manual review protocol — PR description checklist |

## Deferred Verification

| Claim | Source | Deferral Reason |
|-------|--------|-----------------|
| Tier 3 tautology filter model calibration | [pipeline-integration.md](pipeline-integration.md#three-tier-tautology-filter) | Deferred until v1 skill text is stable. **Pass criterion (when implemented):** The 4 Tier 3 examples in pipeline-integration.md (2 valid, 2 invalid) must all be classified correctly. Any misclassification = Tier 3 regression. Additional labeled cases may be added; the 4 examples are the minimum acceptance bar. |
| Tier 2 "reopens/contradicts resolved" | [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) | Deferred from v1 — NS handoff lacks explicit resolved-item set |
| Multi-session discovery | [lineage.md](lineage.md#discovery-algorithms) | Out of v1 scope — conversation-local only |
