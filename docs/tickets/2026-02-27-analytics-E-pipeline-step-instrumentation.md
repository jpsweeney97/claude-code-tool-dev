# T-E: Pipeline Step Instrumentation

```yaml
id: T-E
date: 2026-02-27
status: open
priority: low
branch: feature/pipeline-instrumentation
blocked_by: [T-D]
blocks: []
related: [T-C, T-D]
effort: M (2 sessions)
```

## Summary

Add timing instrumentation to each of the 17 pipeline steps in the context injection MCP server. This enables latency debugging, performance profiling, and identifying which steps dominate processing time.

**Value:** Performance diagnostics for the most complex component in the system. When a dialogue turn feels slow, this data tells you whether entity extraction, template matching, or checkpoint serialization is the bottleneck. Lowest priority because performance has not been a reported issue — but this is the kind of instrumentation you wish you'd had when you need it.

## Rationale

The 17-step pipeline (`pipeline.py:_process_turn_inner`) orchestrates entity extraction, path checking, template matching, ledger validation, checkpoint serialization, and more. Each step has different computational characteristics:

| Step | Operation | Expected Cost |
|------|-----------|---------------|
| 1-2 | Schema/guard validation | Negligible |
| 3-4 | State resolution + checkpoint intake | Low (memory ops) |
| 5 | Turn cap guard | Negligible |
| 6 | Prior state snapshot | Low (memory traversal) |
| 7-8 | Entity extraction + disambiguation | Medium (regex on all claims) |
| 9 | Path canonicalization + denylist | Medium (filesystem + git ls-files lookup) |
| 10 | Template matching | Medium-High (cartesian product of entities × templates × dedupe) |
| 11 | Budget computation | Low |
| 12 | Ledger validation | Low |
| 13-15 | State building + action computation | Low |
| 16 | Checkpoint serialization | Medium (JSON serialize + HMAC) |
| 17 | Summary + store + commit | Low |

Without instrumentation, we can only guess at these costs.

## Design

### Step Timer Context Manager

Add to `pipeline.py`:

```python
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

@dataclass
class StepTimings:
    """Timing data for pipeline steps."""
    steps: dict[str, float] = field(default_factory=dict)
    total_ms: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"steps": self.steps, "total_ms": self.total_ms}

@contextmanager
def _step_timer(timings: StepTimings, step_name: str):
    """Time a pipeline step."""
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        timings.steps[step_name] = round(elapsed_ms, 2)
```

### Pipeline Integration

Wrap each step group:

```python
def _process_turn_inner(request, ctx):
    timings = StepTimings()
    pipeline_start = time.monotonic()

    with _step_timer(timings, "validation"):
        # Steps 1-2: Schema + guard validation
        ...

    with _step_timer(timings, "state_resolution"):
        # Steps 3-5: State + checkpoint + cap guard
        ...

    with _step_timer(timings, "entity_extraction"):
        # Steps 6-8: Prior state + extraction + disambiguation
        ...

    with _step_timer(timings, "path_checking"):
        # Step 9: Path canonicalization + denylist
        ...

    with _step_timer(timings, "template_matching"):
        # Step 10: Template matching
        ...

    with _step_timer(timings, "ledger_validation"):
        # Steps 11-12: Budget + ledger validation
        ...

    with _step_timer(timings, "state_building"):
        # Steps 13-15: Provisional state + action + closing probe
        ...

    with _step_timer(timings, "checkpoint"):
        # Step 16: Compaction + serialization
        ...

    with _step_timer(timings, "finalization"):
        # Step 17: Summary + store + commit
        ...

    timings.total_ms = round((time.monotonic() - pipeline_start) * 1000, 2)

    # Include in PipelineMetrics (extends T-D)
    metrics = PipelineMetrics(
        ...,
        step_timings=timings.to_dict(),
    )
```

### Step Grouping Rationale

Individual step timing (17 separate timers) is too granular. Group into 9 logical phases:
1. `validation` (steps 1-2)
2. `state_resolution` (steps 3-5)
3. `entity_extraction` (steps 6-8)
4. `path_checking` (step 9)
5. `template_matching` (step 10)
6. `ledger_validation` (steps 11-12)
7. `state_building` (steps 13-15)
8. `checkpoint` (step 16)
9. `finalization` (step 17)

### Extending `PipelineMetrics` (from T-D)

Add to `PipelineMetrics`:

```python
class PipelineMetrics(ProtocolModel):
    # ... existing fields from T-D ...

    # Step timings (T-E)
    step_timings: dict[str, float] | None = None  # step_name -> ms
    total_pipeline_ms: float | None = None
```

### Call 2 Timing

Also instrument `execute_scout` (Call 2) in `execute.py`:

```python
class ScoutTimings:
    path_check_ms: float
    execution_ms: float       # read or grep
    redaction_ms: float
    truncation_ms: float
    total_ms: float
```

Add to `ScoutResultSuccess`:
```python
scout_timings: dict[str, float] | None = None
```

### Agent Forwarding

The `codex-dialogue` agent forwards timings in turn events (T-C):

```json
{
  "event": "turn_completed",
  "pipeline_metrics": {
    "step_timings": {
      "entity_extraction": 12.5,
      "template_matching": 45.2,
      "checkpoint": 8.1
    },
    "total_pipeline_ms": 78.3
  }
}
```

## Files to Modify

| File | Action | Change |
|------|--------|--------|
| `packages/context-injection/context_injection/pipeline.py` | Modify | Add step timing around each phase |
| `packages/context-injection/context_injection/execute.py` | Modify | Add scout execution timing |
| `packages/context-injection/context_injection/types.py` | Modify | Extend `PipelineMetrics` with timing fields |
| `packages/context-injection/tests/test_pipeline.py` | Modify | Verify timing fields present and positive |
| `packages/context-injection/tests/test_execute.py` | Modify | Verify scout timing fields |

## Acceptance Criteria

1. All 9 pipeline step groups have timing measurements
2. Timings are in milliseconds, rounded to 2 decimal places
3. `total_pipeline_ms` approximately equals sum of step timings
4. Call 2 scout execution has 4-phase timing breakdown
5. Timing fields are optional (None when instrumentation disabled)
6. Existing 969 tests still pass
7. Overhead of instrumentation is < 1ms per pipeline call (benchmark)

## Risks

- **Timing accuracy:** `time.monotonic()` has microsecond resolution on most platforms. Sub-millisecond steps will show as 0.0. This is fine — those steps are not bottlenecks.
- **Test determinism:** Timing values are non-deterministic. Tests should assert `>= 0`, not exact values. For integration tests, assert `total_pipeline_ms > 0`.
- **Schema churn:** Adding `step_timings` to `PipelineMetrics` is additive (optional field). No schema version bump needed beyond what T-D establishes.

## Design Decisions

1. **Grouped, not per-step:** 9 groups instead of 17 individual steps. Reduces noise while preserving diagnostic value.
2. **Optional field:** `step_timings` is `None` when instrumentation is disabled (though we always enable it). Forward-compatible.
3. **No percentiles or histograms:** Raw timings per-call. Aggregation happens in the analytics layer (T-A/T-B). The server should emit raw data, not computed statistics.
4. **Both Call 1 and Call 2:** Scout execution timing is equally valuable — a slow grep or a large-file read can dominate total turn latency.
