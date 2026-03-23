---
module: delivery
status: active
normative: true
authority: delivery-plan
---

# Delivery

## Skill Text Changes

| Skill | Changes Required |
|-------|-----------------|
| **adversarial-review** | Add AR capsule emission (with `lineage_root_id`) after prose output. Add `/next-steps` suggestion after review. Composition stub (small — consume feedback capsule, emit AR capsule, fallback behavior, hop suggestion). |
| **next-steps** | Add AR capsule consumption (advisory/tolerant). Add NS handoff block emission when suggesting dialogue. Composition stub (small — consume AR capsule, emit NS handoff, fallback behavior, hop suggestion). |
| **dialogue** | Add two-stage admission (Stage A: sentinel detection + validation, Stage B: normalize to `upstream_handoff`). Add `handoff_enriched` decomposition mode. Thread `upstream_handoff` through Steps 2-3 via capability flags. Add feedback capsule emission after synthesis. Add routing classification + materiality evaluation. Composition stub (large — routing, materiality, budget, discovery, consume/emit, fallback). |
| **Shared contract** | New file: composition contract at `packages/plugins/cross-model/references/composition-contract.md` — structure and size estimated — to be finalized when authored (item #6). See [foundations.md §Three-Layer Delivery Authority](foundations.md#three-layer-delivery-authority) for required content areas. |

### Governance Gate Activation Checklist

See [governance.md §Gate Activation Conditions](governance.md#gate-activation-conditions) for the authoritative table of which gates activate when each artifact is authored.

### AR Skill Text Addition

Add after the Confidence Check section:

> If this review surfaced multiple findings that need coordinated action, suggest `/next-steps` to sequence the work.

Add capsule emission instructions (always emit after prose output).

### NS Skill Text Addition

Add handoff block emission when suggesting dialogue. Update existing dialogue suggestion to include the sentinel block.

### Dialogue Skill Text Addition

The dialogue skill receives the most extensive changes. Insert additions at these locations:

1. **Stage A/B admission logic:** Before the existing decomposition step (Step 0). Add sentinel detection (reverse-scan for `<!-- next-steps-dialogue-handoff:v1 -->`), schema validation, and normalization to `upstream_handoff` via the NS adapter.
2. **Feedback capsule emission:** After the existing Synthesis Checkpoint output. Assemble `feedback_candidates[]` from synthesis items, run routing classification and materiality evaluation, apply the correction pipeline, and emit the capsule with sentinel.
3. **Routing classification + materiality evaluation:** Within the feedback capsule assembly path. Cross-reference [routing-and-materiality.md](routing-and-materiality.md#routing-classification) for the full evaluation flow.
4. **Composition stub:** The largest stub of the three skills. Must cover: routing, materiality, budget enforcement, consumption discovery, capsule emit/consume, fallback behavior, and hop suggestion logic.

## Open Items

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Soft echo filter specification | Resolved | Examples added to [Tier 3](pipeline-integration.md#three-tier-tautology-filter) (tautology filter) (2026-03-19) |
| 2 | Composition contract file location | Resolved | File at `packages/plugins/cross-model/references/composition-contract.md` |
| 3 | `upstream_handoff` version field | Deferred | Sentinel versioning provides forward-compatibility; adds no value until v2 |
| 4 | codex-dialogue synthesis format | Resolved | No changes needed; `/dialogue` projects from existing Synthesis Checkpoint |
| 5 | Tier 2 (materiality) "reopens/contradicts resolved" | Deferred from v1 | Requires resolved-item input surface; NS handoff lacks explicit resolved-item set |
| 6 | CI enforcement of contract drift | **P0 blocker** | `validate_composition_contract.py` does not exist. Contract→stub drift is a silent correctness bug ([foundations.md](foundations.md#versioning-and-drift-detection)). Interim manual review protocol added. Implement validator modeled on `validate_consultation_contract.py`: check `implements_composition_contract: v1` marker in stubs, verify sentinel registry consistency, detect ownership mismatches. Retirement condition: when `validate_composition_contract.py` passes all 10 acceptance criteria in CI. Validator check #3 interim: governance.md §`record_path` Null-Prevention Review provides active PR checklist enforcement (code-path trace + schema declaration check). Deferred automation: `validate_composition_contract.py` check #3 adds schema-level enforcement when implemented. |
| 7 | Materiality validation harness | **P0 blocker** | Materiality fixtures per [verification.md](verification.md#interim-materiality-verification-protocol) (authoritative test design), 24-case validity matrix table, clause dependency manifest, Tier 3 calibration suite. The most complex behavioral logic (Step 0 precondition, novelty veto, three-tier materiality evaluation, and the correction pipeline — with ordering dependencies) has no test cases. Interim manual verification protocol added — see [verification.md](verification.md#interim-materiality-verification-protocol). The verification test design (table rows, test scenarios, assertion criteria) lives in [verification.md](verification.md#routing-and-materiality-verification) — this item tracks the harness implementation, not the test specification. See [verification.md](verification.md) for the full verification map. Section references are provisional — use semantic names (e.g., "the Materiality Fixtures section" and "the Correction Rules Table section") rather than numeric references until the composition contract is authored. Retirement condition: when materiality harness implements all test scenarios in the [Routing and Materiality Verification](verification.md#routing-and-materiality-verification) table. |
| | **Promotion gate** | | See [governance.md §Promotion Gate](governance.md#promotion-gate). |
| 8 | Interim drift mitigation protocol | Active (interim, retired when item #6 passes CI covering all 10 acceptance criteria in [verification.md](verification.md#validator-acceptance-criteria-validate_composition_contractpy)) | Bidirectional manual review protocol. See [governance.md §Contract-Stub Bidirectional Review Gate](governance.md#contract-stub-bidirectional-review-gate) for the normative enforcement procedures. See [foundations.md](foundations.md#versioning-and-drift-detection) for the architectural invariant this protocol protects. |
| 9 | `--profile` (multi-phase posture profiles) | Deferred from v1 | When implemented, would sit between `--posture` and `upstream_handoff` in the [posture precedence](pipeline-integration.md#posture-precedence) chain. Not defined in v1 — posture precedence is `--posture > upstream_handoff > default collaborative`. |
| 10 | Consumer-side 5-step check ordering structural verification | Deferred | Interim enforcement: [governance.md §Consumer Durable Store Check Ordering Gate](governance.md#consumer-durable-store-check-ordering-gate) provides active PR checklist enforcement (structural trace). Deferred automation: add to `validate_composition_contract.py` scope when implemented. Activation: when consumer stub code is authored. |
| 11 | Thread continuation parsed-numeric enforcement | Deferred | Add to `validate_composition_contract.py` scope: static analysis check that thread continuation comparison code uses parsed numeric timestamps (millisecond precision), not string comparison. Activation: when dialogue stub's thread continuation code is authored. Cross-reference: verification.md scenarios (7) and (8) provide behavioral regression tests; this item adds structural enforcement that the implementation uses parsed comparison, not just that specific inputs produce correct output. |
| 12 | `COMPOSITION_HELPERS.md` CI check scope | Active (interim) | CI check triggers on PRs modifying files in the feedback capsule assembly path. Scope: skill stub files (AR, NS, dialogue composition sections), composition contract, `COMPOSITION_HELPERS.md` itself, and any file imported by the dialogue skill's capsule emission code path. When a PR introduces helper functions in a file not in the enumerated list, the CI check MUST still trigger if `COMPOSITION_HELPERS.md` is not updated — use `COMPOSITION_HELPERS.md` diff as a secondary trigger alongside file-path matching. Do NOT apply to spec files, test fixtures, or documentation. |
| 13 | `dialogue-orchestrated-briefing` cascade test file | Deferred (activates when dialogue stub is authored) | A single test file containing three independent fixture functions/blocks: (1) standalone coherence assertion (4), (2) partial correction failure assertion (6), (3) Step 0 case (c) sub-assertion (vi). Assertions (2) and (3) MUST be in separate fixture functions per governance.md §Abort-Path Independent Test Fixtures Gate — they MUST NOT share a single fixture. Test file MUST be created in the same PR that authors the dialogue stub. Retirement condition: test file created and passing in dialogue stub authoring PR. |

**Note on enforcement coverage gap:** The helper-mediated indirect delegation detection gap (see [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) enforcement coverage note) has no closure timeline in v1. The gap is documented and mitigated by the co-review gate in [governance.md](governance.md#stub-composition-co-review-gate); deeper static analysis is deferred to `validate_composition_contract.py` (item #6). `validate_composition_contract.py` acceptance criteria MUST include (item #6 scope): behavioral test for helper functions listed in `COMPOSITION_HELPERS.md` — verify no listed function delegates to another skill via model output or helper delegation chains.
