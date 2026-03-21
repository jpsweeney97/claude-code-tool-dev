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
| **adversarial-review** | Add AR capsule emission (with `lineage_root_id`) after prose output. Add `/next-steps` suggestion after review. Inline composition stub (small — consume feedback capsule, emit AR capsule, fallback behavior, hop suggestion). |
| **next-steps** | Add AR capsule consumption (advisory/tolerant). Add NS handoff block emission when suggesting dialogue. Inline composition stub (small — consume AR capsule, emit NS handoff, fallback behavior, hop suggestion). |
| **dialogue** | Add two-stage admission (Stage A: sentinel detection + validation, Stage B: normalize to `upstream_handoff`). Add `handoff_enriched` decomposition mode. Thread `upstream_handoff` through Steps 2-3 via capability flags. Add feedback capsule emission after synthesis. Add routing classification + materiality evaluation. Inline composition stub (large — routing, materiality, budget, discovery, consume/emit, fallback). |
| **Shared contract** | New file: composition contract at `packages/plugins/cross-model/references/composition-contract.md` — 12 sections + 3 appendices, ~950 lines. |

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
| 1 | Soft echo filter specification | Resolved | Examples added to Tier 3 (2026-03-19) |
| 2 | Composition contract file location | Resolved | File at `packages/plugins/cross-model/references/composition-contract.md` |
| 3 | `upstream_handoff` version field | Deferred | Sentinel versioning provides forward-compatibility; adds no value until v2 |
| 4 | codex-dialogue synthesis format | Resolved | No changes needed; `/dialogue` projects from existing Synthesis Checkpoint |
| 5 | Tier 2 "reopens/contradicts resolved" | Deferred from v1 | Requires resolved-item input surface; NS handoff lacks explicit resolved-item set |
| 6 | CI enforcement of contract drift | **P0 blocker** | `validate_composition_contract.py` does not exist. Contract→stub drift is a silent correctness bug ([foundations.md](foundations.md#versioning-and-drift-detection)). Interim manual review protocol added. Implement validator modeled on `validate_consultation_contract.py`: check `implements_composition_contract: v1` marker in stubs, verify sentinel registry consistency, detect ownership mismatches. |
| 7 | Materiality validation harness | **P0 blocker** | 12 executable materiality fixtures, 24-case validity matrix table, clause dependency manifest, Tier 3 calibration suite. The most complex behavioral logic (5 evaluation steps with ordering dependencies) has no test cases. Interim manual verification protocol added — see [verification.md](verification.md#interim-materiality-verification-protocol). See [verification.md](verification.md) for the full verification map. Section references are provisional — use semantic names (e.g., "the Materiality Fixtures section" and "the Correction Rules Table section") rather than numeric references until the composition contract is authored. |
