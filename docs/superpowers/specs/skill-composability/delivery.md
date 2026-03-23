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

Governance gates in [governance.md](../skill-composability/governance.md) become active when their referenced artifacts are first created. When authoring any of the following, the PR MUST confirm the corresponding governance gates are applied:

| Artifact | Gates Activated |
|----------|----------------|
| Composition contract (`composition-contract.md`) | Contract Marker Verification, `topic_key` Scope Guard |
| Composition stubs (AR, NS, dialogue) | Stub Composition Co-Review, Helper Function Tracking, Constrained Field Literal-Assignment, `budget_override_pending` Initialization |
| Dialogue consumer stub (durable store behavior) | Consumer Durable Store Check Ordering, `upstream_handoff` Abort Teardown Check |
| `COMPOSITION_HELPERS.md` | Helper Function Tracking (diffing requirement) |

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
4. **Inline composition stub:** The largest stub of the three skills. Must cover: routing, materiality, budget enforcement, consumption discovery, capsule emit/consume, fallback behavior, and hop suggestion logic.

## Open Items

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Soft echo filter specification | Resolved | Examples added to [Tier 3](pipeline-integration.md#three-tier-tautology-filter) (tautology filter) (2026-03-19) |
| 2 | Composition contract file location | Resolved | File at `packages/plugins/cross-model/references/composition-contract.md` |
| 3 | `upstream_handoff` version field | Deferred | Sentinel versioning provides forward-compatibility; adds no value until v2 |
| 4 | codex-dialogue synthesis format | Resolved | No changes needed; `/dialogue` projects from existing Synthesis Checkpoint |
| 5 | Tier 2 (materiality) "reopens/contradicts resolved" | Deferred from v1 | Requires resolved-item input surface; NS handoff lacks explicit resolved-item set |
| 6 | CI enforcement of contract drift | **P0 blocker** | `validate_composition_contract.py` does not exist. Contract→stub drift is a silent correctness bug ([foundations.md](foundations.md#versioning-and-drift-detection)). Interim manual review protocol added. Implement validator modeled on `validate_consultation_contract.py`: check `implements_composition_contract: v1` marker in stubs, verify sentinel registry consistency, detect ownership mismatches. Retirement condition: when `validate_composition_contract.py` passes all 9 acceptance criteria in CI. |
| 7 | Materiality validation harness | **P0 blocker** | Materiality fixtures per [verification.md](verification.md#interim-materiality-verification-protocol) (authoritative test design), 24-case validity matrix table, clause dependency manifest, Tier 3 calibration suite. The most complex behavioral logic (Step 0 precondition, novelty veto, three-tier materiality evaluation, and the correction pipeline — with ordering dependencies) has no test cases. Interim manual verification protocol added — see [verification.md](verification.md#interim-materiality-verification-protocol). The verification test design (table rows, test scenarios, assertion criteria) lives in [verification.md](verification.md#routing-and-materiality-verification) — this item tracks the harness implementation, not the test specification. See [verification.md](verification.md) for the full verification map. Section references are provisional — use semantic names (e.g., "the Materiality Fixtures section" and "the Correction Rules Table section") rather than numeric references until the composition contract is authored. Retirement condition: when materiality harness implements all test scenarios in the [Routing and Materiality Verification](verification.md#routing-and-materiality-verification) table. |
| | **Promotion gate** | | Composition system MUST NOT be promoted to production (`~/.claude/`) while either P0 blocker is open. |
| 8 | Interim drift mitigation protocol | Active (interim, retired when item #6 passes CI covering all 9 acceptance criteria in [verification.md](verification.md#validator-acceptance-criteria-validate_composition_contractpy)) | Bidirectional manual review protocol (until item #6 CI enforcement exists). **Contract → stub:** Any modification to the composition contract's routing, materiality, lineage, or capsule schema sections MUST be accompanied by a manual review of all three participating skill stubs (adversarial-review, next-steps, dialogue) against the updated contract text. The PR description MUST include a stub-impact checklist confirming which stubs were reviewed and whether updates are needed. **Stub → contract:** Any modification to a participating skill stub's composition section MUST be accompanied by verification that the change conforms to the current contract. The PR description MUST confirm the stub change does not diverge from contract intent. See [foundations.md](foundations.md#versioning-and-drift-detection) for the architectural invariant this protocol protects. PR review gate procedures are defined in [governance.md](governance.md). |
| 9 | `--profile` (multi-phase posture profiles) | Deferred from v1 | When implemented, would sit between `--posture` and `upstream_handoff` in the [posture precedence](pipeline-integration.md#posture-precedence) chain. Not defined in v1 — posture precedence is `--posture > upstream_handoff > default collaborative`. |
| 10 | Consumer-side 5-step check ordering structural verification | Deferred | Add to `validate_composition_contract.py` scope: verify consumer code implements the 5-step durable store check in strict sequential order (nullity → existence → presence → value → integrity) with explicit short-circuit at each step. Activation: when consumer stub code is authored. |
| 11 | Thread continuation parsed-numeric enforcement | Deferred | Add to `validate_composition_contract.py` scope: static analysis check that thread continuation comparison code uses parsed numeric timestamps (millisecond precision), not string comparison. Activation: when dialogue stub's thread continuation code is authored. Cross-reference: verification.md scenarios (7) and (8) provide behavioral regression tests; this item adds structural enforcement that the implementation uses parsed comparison, not just that specific inputs produce correct output. |

**Note on enforcement coverage gap:** The helper-mediated indirect delegation detection gap (see [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) enforcement coverage note) has no closure timeline in v1. The gap is documented and mitigated by the co-review gate in [governance.md](governance.md#stub-composition-co-review-gate); deeper static analysis is deferred to `validate_composition_contract.py` (item #6). `validate_composition_contract.py` acceptance criteria MUST include (item #6 scope): behavioral test for helper functions listed in `COMPOSITION_HELPERS.md` — verify no listed function delegates to another skill via model output or helper delegation chains.
