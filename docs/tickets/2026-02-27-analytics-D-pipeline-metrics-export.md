# T-D: Context Injection Pipeline Metrics Export

```yaml
id: T-D
date: 2026-02-27
status: open
priority: medium
branch: feature/pipeline-metrics
blocked_by: [T-C]
blocks: [T-E]
related: [T-A, T-B, T-C, T-E]
effort: M (2-3 sessions)
```

## Summary

Add an optional `pipeline_metrics` field to `TurnPacketSuccess` responses from the context injection MCP server. This surfaces rich server-side observability data (entity counts, template match rates, deduplication statistics, checkpoint sizes, path decision distributions) that currently exists in transient pipeline state but is discarded after each response.

**Value:** Enriches turn-level events (T-C) with server-side data. Enables identifying bottlenecks (template matching returning zero candidates), tracking security posture (redaction rates), and monitoring server health (checkpoint sizes approaching 16 KB cap).

## Rationale

The context injection server's 17-step pipeline produces rich intermediate state that's consumed internally and discarded. The agent receives structured types (`TurnPacketSuccess`) but many diagnostic signals are lost:

| Signal | Currently Available | With Pipeline Metrics |
|--------|--------------------|-----------------------|
| Entity count | Derivable (count `entities` list) | Explicit, with per-type breakdown |
| Template match rate | Not available | `eligible / total_entities` |
| Dedup rate | Derivable (count `deduped` list) | Explicit ratio |
| Checkpoint size | Not available | Bytes (approaching 16 KB cap?) |
| Plateau detection | Implicit in `action` field | Explicit boolean + reason |
| Path decision distribution | Derivable (count by status) | Aggregated counts |
| Budget utilization | Available in `budget` field | Already available (no change needed) |

## Design

### New Model: `PipelineMetrics`

Add to `types.py`:

```python
class PipelineMetrics(ProtocolModel):
    """Optional observability data from the Call 1 pipeline."""

    # Entity extraction (Steps 7-8)
    entity_count: int
    entity_types: dict[str, int]  # e.g., {"file_loc": 3, "symbol": 2, "file_hint": 1}
    focus_entity_count: int
    prior_entity_count: int

    # Path decisions (Step 9)
    path_decisions_allowed: int
    path_decisions_denied: int
    path_decisions_unresolved: int
    risk_signal_count: int

    # Template matching (Step 10)
    template_candidates_count: int
    dedup_count: int
    dedup_entity_already_scouted: int
    dedup_template_already_used: int

    # Checkpoint (Step 16)
    checkpoint_size_bytes: int

    # Control (Step 14)
    plateau_detected: bool
    entries_count: int  # total ledger entries in conversation
```

### Schema Version

This is a backwards-compatible addition (new optional field on existing response). Two options:

**Option A: Same schema version, optional field**
Add `pipeline_metrics: PipelineMetrics | None = None` to `TurnPacketSuccess`. Old clients ignore it. No version bump needed.

**Problem:** The model uses `extra="forbid"`, so old clients with strict validation would reject the response. But the context injection server and the dialogue agent are always deployed together (same plugin), so version skew is unlikely.

**Option B: Schema version bump to 0.3.0**
Bump `SCHEMA_VERSION` to `"0.3.0"`. Add `pipeline_metrics` as a required field.

**Problem:** Requires updating the dialogue agent's schema version in TurnRequest. More churn.

**Recommendation:** Option A. The `extra="forbid"` constraint is on the *model* definition, not on the consumer. Since the agent receives the response as a dict from MCP, it can simply ignore unknown fields. Add `pipeline_metrics` as optional (`None` default) for forward compatibility.

### Pipeline Changes (`pipeline.py`)

Collect metrics at each step of `_process_turn_inner`:

```python
def _process_turn_inner(request, ctx):
    # ... existing steps 1-16 ...

    # Collect pipeline metrics (between step 16 and step 17)
    metrics = PipelineMetrics(
        entity_count=len(entities),
        entity_types=_count_entity_types(entities),
        focus_entity_count=sum(1 for e in entities if e.in_focus),
        prior_entity_count=sum(1 for e in entities if not e.in_focus),
        path_decisions_allowed=sum(1 for pd in path_decisions if pd.status == "allowed"),
        path_decisions_denied=sum(1 for pd in path_decisions if pd.status == "denied"),
        path_decisions_unresolved=sum(1 for pd in path_decisions if pd.status == "unresolved"),
        risk_signal_count=sum(1 for pd in path_decisions if pd.risk_signal),
        template_candidates_count=len(template_candidates),
        dedup_count=len(dedup_records),
        dedup_entity_already_scouted=sum(
            1 for d in dedup_records if d.reason == "entity_already_scouted"
        ),
        dedup_template_already_used=sum(
            1 for d in dedup_records if d.reason == "template_already_used"
        ),
        checkpoint_size_bytes=len(checkpoint_string.encode("utf-8")),
        plateau_detected=_is_plateau_from_action(action),
        entries_count=len(projected.entries),
    )

    return TurnPacketSuccess(
        # ... existing fields ...
        pipeline_metrics=metrics,  # NEW
    )
```

### Agent Integration

The `codex-dialogue` agent reads `pipeline_metrics` from the TurnPacket and includes it in the turn-level event (T-C):

```json
{
  "event": "turn_completed",
  "pipeline_metrics": {
    "entity_count": 12,
    "template_candidates_count": 3,
    "dedup_count": 2,
    "checkpoint_size_bytes": 4820,
    "plateau_detected": false
  }
}
```

The agent passes through the metrics dict without interpretation — raw data for downstream analysis.

### Test Changes

Add tests for:
1. `PipelineMetrics` model validation
2. Metric collection accuracy (entity counts match actual entities, etc.)
3. Checkpoint size calculation correctness
4. `pipeline_metrics` field present in `TurnPacketSuccess` responses
5. Backwards compatibility: old tests still pass with the new optional field

## Files to Modify

| File | Action | Change |
|------|--------|--------|
| `packages/context-injection/context_injection/types.py` | Modify | Add `PipelineMetrics` model |
| `packages/context-injection/context_injection/pipeline.py` | Modify | Collect and attach metrics |
| `packages/context-injection/tests/test_pipeline.py` | Modify | Verify metrics in responses |
| `packages/context-injection/tests/test_types.py` | Modify | Test `PipelineMetrics` model |
| `packages/plugins/cross-model/agents/codex-dialogue.md` | Modify | Pass metrics to turn events |
| `packages/plugins/cross-model/scripts/emit_analytics.py` | Modify | Accept `pipeline_metrics` in turn events |

## Acceptance Criteria

1. `TurnPacketSuccess` responses include `pipeline_metrics` field
2. All metric values are accurate (verified by test assertions)
3. Existing 969 tests still pass (no regressions)
4. `checkpoint_size_bytes` correctly measures the serialized checkpoint
5. Agent can read and forward metrics to turn events
6. Metrics are JSON-serializable

## Risks

- **Model validation strictness:** `extra="forbid"` on ProtocolModel means any consumer using the Pydantic model directly will reject new fields. Since the agent receives MCP responses as dicts, this is fine for the primary consumer. But any test that constructs `TurnPacketSuccess` without `pipeline_metrics` will need updating.
- **Performance:** Metric collection is O(n) on existing lists (entities, path_decisions, dedup_records). These lists are small (typically <50 items). Negligible overhead.
- **Schema drift:** New fields in `PipelineMetrics` don't require a schema version bump (it's an additive optional field). But changing existing field semantics would.

## Design Decisions

1. **Optional, not required:** `pipeline_metrics` defaults to `None` so old code doesn't break.
2. **Aggregated counts, not raw data:** The agent already receives `entities`, `path_decisions`, etc. as full lists. Metrics provide pre-aggregated summaries for the event log, not duplicates of existing data.
3. **No step timings:** Timing instrumentation is a separate concern (T-E). This ticket focuses on counting metrics that require no new infrastructure.
