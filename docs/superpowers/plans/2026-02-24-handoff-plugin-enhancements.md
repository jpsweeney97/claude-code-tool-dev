# Handoff Plugin Enhancements

```yaml
date: 2026-02-24
status: planning
plugin: packages/plugins/handoff/
```

## Motivation

Analysis of 244 handoffs produced over 43 days (Jan 12 – Feb 24, 2026) revealed five high-leverage gaps in the handoff plugin.

### Usage Profile

| Metric | Value |
|--------|-------|
| Total handoffs | 244 (243 archived + 1 active) |
| Projects | 1 (`claude-code-tool-dev`) |
| Chain rate (`resumed_from`) | 80% (194/243) |
| Average per day | 7.4 (peak: 25) |
| Under 100 lines | 30% (74 handoffs) |
| Over 300 lines (target met) | 56% (137 handoffs) |

### Quality Evolution

Early handoffs (Jan 12-19, pre-synthesis guide) averaged 75 lines. Recent handoffs (Feb 20+) consistently hit 300-573 lines. The synthesis guide transformed quality — but quality floor has no programmatic enforcement.

## Enhancement Summary

| # | Enhancement | Ticket | Key Problem | Status |
|---|-------------|--------|-------------|--------|
| 1 | Search/query | [handoff-search](../tickets/handoff-search.md) | 244 handoffs, zero queryability | planning |
| 2 | Knowledge graduation | [handoff-distill](../tickets/handoff-distill.md) | 90-day retention = knowledge loss | planning |
| 3 | Quality enforcement | [handoff-quality-hook](../tickets/handoff-quality-hook.md) | 30% under 100 lines | planning |
| 4 | Chain visualization | [handoff-chain-viz](../tickets/handoff-chain-viz.md) | 80% chained, chains invisible | planning |
| 5 | Checkpoint tier | [handoff-checkpoints](../tickets/handoff-checkpoints.md) | 7.4/day overhead, context cost | planning |

## Dependencies

```
#5 Checkpoints ──affects──▶ #3 Quality Hook (thresholds differ by type)
#2 Distill ───uses────▶ #1 Search (optional — could reuse section extraction)
```

All other enhancements are independent.

## Implementation Order

Start with #5 (Checkpoints) — changes the data model and affects #3.
Remaining order determined after brainstorming each.

## Bug Fixes (included)

- `cleanup.py` uses `unlink()` instead of `trash` — violates project convention
- `resumed_from` stores absolute paths — fragile across environments
