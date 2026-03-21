---
module: verification
status: active
normative: true
authority: delivery-verification
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
| Standalone coherence test (3-case) | Active (interim) | See Capsule Contract Verification table — 3 behavioral tests (one per skill) |
| Grep-based CI checks (contract marker, auto-chaining) | Active (interim) | See Contract Drift and Routing Verification tables |

### Interim Materiality Verification Protocol

Until the materiality harness is implemented, any implementation of materiality evaluation logic MUST be manually walked through:

1. The 24-case validity matrix (3 `affected_surface` values × 2 `material` values × 4 `suggested_arc` values). For each case: verify the tuple either passes through uncorrected (valid) or is corrected per rules 1-5 (invalid).
2. The 4 consequence prohibitions with explicit fixture inputs:
   - Input: `affected_surface=diagnosis`, `material=true`, `suggested_arc=next-steps` → expected: corrected to `adversarial-review` (rule 3). Prohibition: `diagnosis` MUST NOT emit `next-steps`.
   - Input: `affected_surface=planning`, `material=true`, `suggested_arc=adversarial-review` → expected: corrected to `next-steps` (rule 4). Prohibition: `planning` MUST NOT emit `adversarial-review`.
   - Input: `affected_surface=evidence-only`, `material=true`, `suggested_arc=adversarial-review` → expected: corrected to `dialogue_continue` (rule 2). Prohibition: `evidence-only` MUST NOT emit AR, NS, or `ambiguous`.
   - Input: `affected_surface=diagnosis`, `material=true`, `suggested_arc=dialogue_continue` → expected: corrected to `adversarial-review` (rule 1 does not apply since material=true; this exercises prohibition 4: material diagnosis/planning MUST NOT silently remain `dialogue_continue`). Verify correction rule fires.
3. The novelty veto: one case where a novel item pattern-matches a Tier 1 exclusion class → verify Tier 1 returns `no_match`.
4. The cross-tier guard: one case where Tier 1 model exclusion is overridden by Tier 2 inclusion → verify `material: true`.

The PR description MUST confirm this walk-through was completed. This protocol is a P0 prerequisite for merging materiality implementation.

## Capsule Contract Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| AR capsule always emitted after prose output | [capsule-contracts.md](capsule-contracts.md#emission) | Behavioral: AR skill test — invoke AR, verify sentinel present in output |
| NS validates AR capsule if present; falls back to prose parsing if absent or invalid | [capsule-contracts.md](capsule-contracts.md#consumer-class) | Behavioral: three NS test cases — (1) AR capsule present → enriched handoff, (2) AR capsule absent → prose fallback + diagnostic emitted, (3) AR capsule present but invalid → schema rejection + prose fallback + diagnostic emitted |
| NS MUST omit `source_artifacts` entries for absent/invalid AR capsule in fallback | [capsule-contracts.md](capsule-contracts.md#consumer-class) | Behavioral: in NS test cases (2) and (3) above, verify emitted NS handoff contains no `source_artifacts` entry referencing an AR `artifact_id` |
| Dialogue rejects invalid NS handoff but continues pipeline | [capsule-contracts.md](capsule-contracts.md#consumer-class-contract-2) | Behavioral: two dialogue test cases — (1) valid handoff → enriched decomposition, (2) invalid handoff → rejection + normal pipeline proceeds |
| NS handoff emits one block per NS run (not per task) | [capsule-contracts.md](capsule-contracts.md#emission-contract-2) | Behavioral: NS test — invoke NS with multiple tasks, verify single sentinel emitted containing `selected_tasks[]` list |
| Unknown sentinel version → reject capsule block, not skill session | [capsule-contracts.md](capsule-contracts.md#unknown-version-behavior) | Behavioral: per-consumer test — inject `v999` sentinel for each consumer scenario: (1) NS consuming unknown-version AR capsule, (2) Dialogue consuming unknown-version NS handoff, (3) AR consuming unknown-version feedback capsule, (4) NS consuming unknown-version feedback capsule. Verify capsule rejected but skill invocation continues with class-appropriate fallback |
| `record_path` MUST be non-null for feedback capsules (happy path) | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | Behavioral (interim): dialogue test — invoke dialogue with writable filesystem, verify emitted feedback capsule has non-null `record_path` pointing to a valid `.claude/composition/feedback/` path. `validate_composition_contract.py` adds automated schema enforcement when implemented |
| `record_path` MUST be non-null on write failure; `record_status: write_failed` MUST be set | [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) | Behavioral (interim): dialogue test (write-failure) — inject a write failure by pointing `record_path` to a non-writable directory (e.g., `chmod 000` on target directory) before capsule assembly. Assert independently: (1) prose warning emitted with intended path, (2) capsule emitted with `record_path` set to intended path (non-null, asserted separately from success case), (3) `record_status: write_failed` present |
| `material`/`suggested_arc` coherence constraint | [capsule-contracts.md](capsule-contracts.md#schema-constraints) | Standalone (interim): 6 bounded cases. `material: false` (3 cases): verify `adversarial-review`, `next-steps`, `ambiguous` are each corrected to `dialogue_continue` (rule 1). `material: true` (3 cases): (1) `evidence-only` + `adversarial-review` → corrected to `dialogue_continue` (rule 2), (2) `diagnosis` + `next-steps` → corrected to `adversarial-review` (rule 3), (3) `planning` + `adversarial-review` → corrected to `next-steps` (rule 4). Full 24-case validity matrix via materiality harness when implemented |
| Emission-time enforcement: correction pipeline is a required gate before `feedback_candidates[]` assembly | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Behavioral: construct feedback capsule assembly path, verify all `feedback_candidates[]` entries reflect post-correction state. Structural: verify capsule assembly code path has no branch that writes `feedback_candidates[]` from raw (pre-correction) classification output — correction rules MUST fire before the list is populated, not after |
| Partial correction failure: capsule MUST be fully corrected or not emitted | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Behavioral: inject an entry with unexpected field type mid-list into `feedback_candidates[]` → verify capsule assembly aborts entirely, not partially emitted |
| Standalone coherence: every skill MUST function correctly with only its inline stub | [foundations.md](foundations.md#three-layer-delivery-authority) | Behavioral (interim): 3 test scenarios — invoke each skill (AR, NS, dialogue) without any upstream capsule present and without access to the composition contract. Verify the skill completes its normal output without error or degraded behavior |

## Routing and Materiality Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| Correction rules only fire on invalid tuples | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — 24-case validity matrix. Test both valid tuples (pass through uncorrected) and invalid tuples (corrected per rules 1-5) |
| `diagnosis` MUST NOT emit `next-steps` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| `planning` MUST NOT emit `adversarial-review` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| `evidence-only` MUST NOT emit AR, NS, or `ambiguous` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| Material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue` | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — dedicated prohibition test cases |
| Novelty veto: novel items bypass Tier 1, proceed through Tier 2 and Tier 3 | [routing-and-materiality.md](routing-and-materiality.md#novelty-veto-pre-check) | Materiality harness — materiality fixtures: novel item + Tier 1 pattern match → verify Tier 1 returns `no_match`, item reaches Tier 2/3 |
| Cross-tier guard: model-judged Tier 1 exclusion overridden by Tier 2 inclusion | [routing-and-materiality.md](routing-and-materiality.md#cross-tier-guard) | Materiality harness — materiality fixtures: item matching Tier 1 model exclusion + Tier 2 inclusion → verify `material: true` |
| Soft iteration budget: stop suggesting after 2 targeted loops per `lineage_root_id` | [routing-and-materiality.md](routing-and-materiality.md#soft-iteration-budget) | Behavioral: dialogue test — simulate 3-hop chain with same `lineage_root_id`, verify hop suggestion omitted after hop 2. Test fixtures: (1) Positive: Artifact 1 = `ar:subject:timestamp` (`adversarial_review`) with matching `lineage_root_id`, Artifact 2 = `ns:subject:timestamp` (`next_steps_plan`) with same `lineage_root_id` → verify budget counter reads 2 (exhausted). (2) Negative: pre-seed 2 `dialogue_feedback` artifacts (same-kind, not cross-skill transitions) with same `lineage_root_id` → verify budget counter reads 0 (not exhausted). Fixture format: YAML capsule blocks injected into test conversation context |
| Ambiguous item non-response: hold behavior and unresolved reporting | [routing-and-materiality.md](routing-and-materiality.md#ambiguous-item-behavior) | Behavioral: invoke dialogue with a `material: true` + `ambiguous` item, do not respond to the routing prompt, proceed to capsule emission. Verify (1) item appears in `unresolved[]` with `hold_reason: routing_pending`, (2) no hop suggestion emitted for this item, (3) no budget consumed |
| Budget indeterminate state: treat as not-exhausted + emit prose warning | [routing-and-materiality.md](routing-and-materiality.md#budget-enforcement-mechanics) | Behavioral: dialogue test — pre-seed only a `dialogue_feedback` capsule with a `lineage_root_id`, but NOT the corresponding upstream AR or NS artifacts (simulating compressed context). Verify (1) budget treated as not-exhausted, (2) prose warning emitted containing the specified text about context compression |
| No auto-chaining: skills MUST NOT programmatically invoke another skill | [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) | (1) Structural: review of skill stub text — verify no `/<skill>` invocation patterns in conditional logic. (2) Automated (interim): grep-based CI check on stub files — fail if `/<adversarial-review>`, `/<next-steps>`, or `/<dialogue>` patterns appear in conditional or feedback capsule processing blocks. Additionally check that `continuation_warranted` and `suggested_arc` are not read in conditional branches that emit user-facing text formatted as skill invocation prompts (de-facto chaining). (3) Platform architecture provides primary runtime enforcement |
| Posture precedence: `--posture > --profile > upstream_handoff > default` | [pipeline-integration.md](pipeline-integration.md#posture-precedence) | Behavioral: four dialogue test scenarios — (1) `upstream_handoff.recommended_posture` set + explicit `--posture` flag → verify explicit flag wins, (2) `upstream_handoff.recommended_posture` set, no `--posture`/`--profile` → verify handoff posture applied, (3) `--profile` set + `upstream_handoff.recommended_posture` set, no `--posture` → verify `--profile` wins over handoff, (4) `--posture` and `--profile` both set → verify `--posture` wins |
| Thread continuation: new artifact → new thread | [routing-and-materiality.md](routing-and-materiality.md#thread-continuation-vs-fresh-start) | Behavioral: four dialogue test scenarios — (1) new NS artifact in context → verify fresh `/dialogue` invocation with new briefing (not thread continuation), (2) same goal + same snapshot set + operational termination → verify thread continuation is permitted, (3) same goal + same snapshot + unresolved items include a diagnosis-surface finding → verify fresh start required, (4) same goal + same snapshot + prior termination was scope breach (not operational) → verify fresh start required |

## Lineage Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| Consumption discovery: reverse-scan newest-first, take first match only, no backtrack | [lineage.md](lineage.md#consumption-discovery) | Behavioral: two test scenarios — (1) context has [valid-older, valid-newer] → newer consumed; (2) context has [valid-older, invalid-newer] → no capsule consumed (not older) |
| Staleness detection priority ordering: superseded > unknown > stale_inputs > current | [lineage.md](lineage.md#staleness-detection) | Behavioral: four test scenarios — (1) Priority 1 (`superseded`): context has [artifact-v1, artifact-v2 with same `artifact_kind`+`subject_key`] → consuming v1 → status `superseded`. (2) Priority 2 (`unknown`): context has artifact but its required `source_artifact` is absent → status `unknown`. (3) Priority 3 (`stale_inputs`): context has artifact with `source_artifact` X, AND context has X-v2 superseding X → status `stale_inputs` (warn + suggest rebase). (4) Priority 4 (`current`): context has artifact, all `source_artifacts` present, no superseders → status `current`. Verify first matching status applies |
| Must-not-infer-current rule: absent source_artifact → `unknown`, not `current` | [lineage.md](lineage.md#staleness-detection) | Behavioral: test scenario — required source_artifact absent from context → verify status is `unknown` |
| `lineage_root_id` immutability: never re-minted downstream | [lineage.md](lineage.md#key-propagation) | Behavioral (interim): multi-hop chain test — assert `lineage_root_id` value equality (exact string match) across all hops, not just inheritance pattern. `validate_composition_contract.py` adds automated schema enforcement when implemented |
| Inheritance-first rule: only root of chain mints keys | [lineage.md](lineage.md#key-propagation) | Behavioral: multi-hop chain test — verify downstream skills inherit `subject_key`, `topic_key`, and `lineage_root_id` from upstream, not re-mint from their own basis fields |
| `topic_key` optionality: capsule schemas accept missing `topic_key` without rejection | [lineage.md](lineage.md#key-propagation) | Behavioral: NS handoff validity test — omit `topic_key` from handoff block → verify dialogue accepts the capsule as valid (not rejected for missing field). Cross-reference [capsule-contracts.md](capsule-contracts.md#contract-2-ns--dialogue-ns-handoff-block) validity criteria |
| `created_at` precision: all three skills MUST use millisecond precision | [lineage.md](lineage.md#artifact-id-format) | Behavioral (interim): multi-skill capsule chain test — verify all emitted `artifact_id` values match `YYYYMMDDTHHMMSS.sss` format with exactly 3 fractional digits. Test cases: (1) timestamp at second precision → verify `.000` appended, (2) timestamp at microsecond precision → verify truncated to milliseconds |
| `source_artifacts[]` records direct edges only (no transitive provenance) | [lineage.md](lineage.md#dag-structure) | Behavioral: invoke dialogue consuming an NS handoff produced from an AR capsule (3-artifact chain). Verify the emitted feedback capsule's `source_artifacts[]` lists only the NS artifact (`artifact_kind: next_steps_plan`) and does NOT include the AR artifact (`artifact_kind: adversarial_review`) |

## Contract Drift Verification

| Claim | Source | Verification Path |
|-------|--------|-------------------|
| `implements_composition_contract: v1` present in participating stubs | [foundations.md](foundations.md#versioning-and-drift-detection) | Automated (interim): `grep -l 'implements_composition_contract: v1'` against known stub paths (adversarial-review, next-steps, dialogue skill files). Fail if any participating stub is missing the marker. `validate_composition_contract.py` adds full semantic validation when implemented |
| Stubs conform to contract's routing/materiality/lineage definitions | [foundations.md](foundations.md#versioning-and-drift-detection) | `validate_composition_contract.py` — semantic parity check |
| Contract changes accompanied by stub review | [foundations.md](foundations.md#versioning-and-drift-detection) | Automated (interim): CI check — grep PR description for stub-impact checklist keywords (`stub-impact` or `composition stub reviewed`) on any PR touching `composition-contract.md` or the three participating skill stubs. Flag absence as a CI warning. Manual: PR description checklist confirming which stubs were reviewed and whether updates are needed |

## Deferred Verification

| Claim | Source | Deferral Reason |
|-------|--------|-----------------|
| Tier 3 tautology filter model calibration | [pipeline-integration.md](pipeline-integration.md#three-tier-tautology-filter) | Deferred until v1 skill text is stable. **Interim verification:** During implementation, author MUST manually evaluate the 4 Tier 3 examples from pipeline-integration.md (2 valid, 2 invalid) and confirm correct classification before merging decomposition seeding changes. PR description MUST include the classification result for each example. **Pass criterion (when implemented):** All 4 examples must classify correctly. Any misclassification = Tier 3 regression. Additional labeled cases may be added; the 4 examples are the minimum acceptance bar. |
| Tier 2 "reopens/contradicts resolved" | [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) | Deferred from v1 — NS handoff lacks explicit resolved-item set |
| Multi-session discovery | [lineage.md](lineage.md#discovery-algorithms) | Out of v1 scope — conversation-local only |
| Boundary rule compliance (spec.yaml boundary_rules) | [spec.yaml](spec.yaml) | Process verification (out of automated scope): boundary rule adherence depends on PR review process. Recommend adding a CODEOWNERS or review checklist entry ensuring that PRs touching capsule-contract, routing, lineage, or pipeline files include a tagged reviewer from the required authority list. Governance constraint, not a runtime behavioral test |
