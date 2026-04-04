# T-20260403-01: T7 conceptual-query corpus design constraint

```yaml
id: T-20260403-01
date: 2026-04-03
status: open
priority: high
tags: [codex-collaboration, benchmark, t7, scope, corpus-design]
blocked_by: []
blocks: [T6-composition-check]
effort: medium
```

## Context

T4 rev 21 (`214ef168`) blocks scored benchmark runs until T7 defines a
validator-enforceable conceptual-query root-selection rule. G3 is now
accepted (`dd14aab4`), all 5 hard gates are at `Accepted (design)`, and
T6 composition check is unblocked.

The conceptual-query viability risk was assessed and resolved via ADR:
`docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`

**Decision:** benchmark v1 satisfies the T4 blocker through corpus
design constraints, not a root-selection algorithm. Comparability over
coverage.

## Problem

T4's §4.6 scope_root derivation has three cases:

1. **Path-targeted:** deterministic (shallowest root). Solved.
2. **Cross-root:** deterministic (per-target root). Solved.
3. **Conceptual multi-root:** no validator-enforceable selection rule
   exists that is both faithful and mechanically checkable.

Without resolution, scored benchmark runs remain blocked indefinitely.

## Scope

**In scope:**

- Amend the benchmark contract run conditions to encode the scored-corpus
  constraint: conceptual queries in scored tasks must be single-root by
  construction or path-anchored after decomposition
- Review all 8 benchmark tasks for conceptual multi-root exposure; flag
  any that require ambiguous selection
- Design decomposition guidance for tasks that can be restructured
- Exclude tasks that cannot satisfy the constraint from benchmark v1
  scored comparisons
- Validate that benchmark v1 coverage remains adequate after exclusions

**Out of scope (deferred):**

- All-roots requirement as experimental benchmark branch (future work)
- General conceptual multi-root selection algorithm
- Changes to T4's anti-narrowing constraint or scope_root recording

## Acceptance criteria

1. Benchmark contract run conditions include the corpus design constraint
2. No scored benchmark v1 task requires ambiguous conceptual multi-root
   `scope_root` selection
3. T4's §4.6 blocker is satisfied (the "rule" is: the ambiguous case
   does not arise in scored runs)
4. T6 composition check can evaluate benchmark v1 coverage adequacy

## Dependencies

| Dependency | Direction | What |
|------------|-----------|------|
| T4 rev 21 | Input | §4.6 blocker, §6.2 amendment row |
| ADR | Input | Conceptual-query scope constraint decision |
| Benchmark contract | Output | Run conditions amendment |
| T6 composition check | Unblocks | Coverage adequacy evaluation |

## References

- T4 design contract: `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md`
- ADR: `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`
- Benchmark contract: `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
- Risk register: `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`
