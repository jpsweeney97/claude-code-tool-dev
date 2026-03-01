# T-B: Derived Metrics Module

```yaml
id: T-B
date: 2026-02-27
status: open
priority: high
branch: feature/derived-metrics
blocked_by: [T-A]
blocks: []
related: [T-A, T-C, T-D]
effort: S (1 session)
```

## Summary

Create a `compute_metrics.py` module that computes derived metrics from the event log. These are second-order signals not directly present in individual events but derivable from the existing data through aggregation and correlation.

**Value:** Transforms raw events into actionable intelligence. The convergence velocity metric alone tells users whether their consultation habits are improving over time. Combined with T-A's presentation layer, this creates a complete analytics pipeline from raw events to user-facing insights.

## Rationale

The event log contains rich per-consultation data (45 fields for `dialogue_outcome`), but individual events are snapshots. The interesting signals emerge from cross-event analysis:
- Is convergence getting faster over time?
- Do certain postures produce better outcomes?
- Are scouts actually helping resolve claims?
- Which context quality signals predict convergence?

## Design

### Module: `packages/plugins/cross-model/scripts/compute_metrics.py`

Pure Python, no dependencies beyond stdlib. Reads event log via `read_events.py` library API.

### Derived Metrics

#### 1. Convergence Velocity
```
velocity = turn_count / turn_budget  (0.0 = instant, 1.0 = budget exhausted)
```
- Per-dialogue metric. Lower is better.
- Aggregate: mean, median, p90 over time window.
- Breakdown by posture.

#### 2. Scout ROI (Return on Investigation)
```
scout_roi = resolved_count / max(scout_count, 1)
```
- Per-dialogue metric. Higher means scouts are more productive.
- Aggregate: mean over time window.
- Compares: `scout_count=0` dialogues vs `scout_count>0` for convergence rate difference.

#### 3. Claim Volatility Index
```
volatility = (emerged_count + unresolved_count) / max(resolved_count, 1)
```
- Per-dialogue metric. Higher means more turbulence.
- Useful for identifying dialogues that generate more questions than answers.

#### 4. Context Quality Score
```
quality = weighted_sum(
    citations_total * 0.3,
    unique_files_total * 0.3,
    shared_citation_paths * 0.2,
    (1 - gatherer_retry_rate) * 0.2
)
```
- Normalized 0-1 scale.
- Correlate with convergence rate to validate whether better context → better outcomes.

#### 5. Posture Effectiveness
Per posture:
- Convergence rate
- Average convergence velocity
- Average resolved count
- Average scout count

Enables data-driven posture selection.

#### 6. Mode Fallback Rate
```
fallback_rate = count(mode="manual_legacy") / total_dialogues
```
- Tracks reliability of context injection server.
- Spikes indicate MCP server issues.

#### 7. Session Trends
Rolling averages (7-event window) of:
- Convergence velocity
- Scout ROI
- Context quality score

Enables "are things getting better?" analysis.

### Output Format

```python
def compute_all(events: list[dict], period_days: int | None = None) -> MetricsReport:
    """Compute all derived metrics. Returns structured report."""

@dataclass
class MetricsReport:
    period_start: str  # ISO 8601
    period_end: str
    total_events: int
    convergence: ConvergenceMetrics
    scout: ScoutMetrics
    context_quality: ContextQualityMetrics
    posture: dict[str, PostureMetrics]
    trends: TrendMetrics
```

JSON-serializable for consumption by T-A's `/codex stats` skill.

### Integration with T-A

T-A's `/codex stats` skill invokes `compute_metrics.py` instead of doing inline aggregation:
```bash
python3 "{plugin_root}/scripts/compute_metrics.py" --period 30d --json
```

The skill formats the JSON output into its markdown sections.

## Files to Create

| File | Action | Purpose |
|------|--------|---------|
| `packages/plugins/cross-model/scripts/compute_metrics.py` | Create | Metrics computation |
| `packages/plugins/cross-model/scripts/test_compute_metrics.py` | Create | Unit tests |

## Acceptance Criteria

1. All 7 metric categories computed correctly
2. Handles empty event log (returns zeroed metrics, not errors)
3. Schema version tolerance (0.1.0-0.3.0 events processed correctly)
4. Period filtering works correctly
5. JSON output is clean and parseable
6. Unit tests cover edge cases: single event, all postures, zero scouts, budget=1

## Dependencies

- `read_events.py` library API (exists)
- T-A provides the presentation surface (but module is independently useful)

## Risks

- **Small sample sizes:** With few dialogues, statistical metrics are meaningless. Add `sample_size` field to each metric; T-A can suppress display when `n < 3`.
- **Schema version gaps:** Older events lack fields used by metrics. Use `.get()` with defaults; mark metrics as `"insufficient_data"` when key fields are missing from >50% of events.
