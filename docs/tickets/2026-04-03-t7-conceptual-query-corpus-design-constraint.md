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

## Corpus Compliance Review

All 8 benchmark tasks were reviewed against T4's `scope_root` derivation cases.

| Task | Prompt character | T4 case | Status |
|------|------------------|---------|--------|
| B1 | Evaluative across named spec + implementation files | Cross-root deterministic | Compliant as written |
| B2 | Analytical within one implementation subtree | Path-targeted | Compliant as written |
| B3 | Adversarial review across named implementation, test, and ticket surfaces | Cross-root deterministic | Compliant as written |
| B4 | Open-ended planning across four explicit plugin/artifact anchors | Cross-root deterministic | Compliant as written; anchor set narrower than a full-repo installability audit |
| B5 | Evaluative across named policy + runtime files | Cross-root deterministic | Compliant as written |
| B6 | Evaluative across named spec + schema + model surfaces | Cross-root deterministic | Compliant as written |
| B7 | Forward-compatibility planning across named lineage/runtime/spec surfaces | Cross-root deterministic | Compliant as written |
| B8 | Comparative supersession question spanning two subsystems | Anchored decomposition required | Compliant only via benchmark-contract decomposition |

## B8 Resolution

B8 stays in benchmark v1. It does not require exclusion, but it also does not
remain a free-form conceptual multi-root search. The authoritative decomposition
now lives in the benchmark contract's
[`Corpus Compliance`](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md#corpus-compliance)
section.

**Resolution:** B8 is Path-2 compliant by documented decomposition. The scored
task remains valid because the benchmark contract can treat it as deterministic
cross-root scouting rather than ambiguous conceptual multi-root selection.

## Change Control Review Note

This ticket's contract amendment was reviewed against
`T4-BR-09` amendment row 5 and `T4-BR-07` prerequisite item 5.

- Delivered here:
  benchmark-scoped `allowed_roots` from corpus anchors and a
  validator-enforceable elimination of ambiguous conceptual multi-root scored
  tasks
- Still open outside this ticket:
  named `scope_envelope` as a run-condition parameter,
  baseline/candidate `allowed_roots` equivalence,
  and `source_classes` inclusion or explicit irrelevance

The broader T4-BR-07 prerequisite gate remains open even though this ticket's
Path-2 corpus-design work is now closed.

## Delivery Status

Delivered in this ticket:

- benchmark contract run-condition amendment for the Path-2 corpus-design rule
- corpus compliance classification for B1-B8
- authoritative B8 scored-run resolution via benchmark-contract decomposition

Still open for follow-through:

- T6 composition review must record whether benchmark v1 coverage remains
  adequate under the constrained corpus
- broader T4-BR-07 prerequisites outside the conceptual-query slice remain
  open benchmark-readiness work

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
