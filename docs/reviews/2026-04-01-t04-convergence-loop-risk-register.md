# T-04 Convergence Loop Risk Register

Date: 2026-04-01
Scope: Benchmark-first design slice for T-20260330-04 (dialogue parity and scouting retirement)
Status: Pre-design gate register
Source analysis: [2026-04-01-t04-convergence-loop-risk-analysis.md](2026-04-01-t04-convergence-loop-risk-analysis.md)
Benchmark contract: dialogue-supersession-benchmark.md (as of 2026-04-01, 8 tasks, 4 pass-rule metrics)

This document is the design-input artifact for the T-04 benchmark-first convergence slice.
The source analysis remains the narrative explanation. This register is the condensed handoff:
hard gates, tracked risks, required controls, and verification expectations.

## Gate Status Model

This register is a review-time enforcement artifact, not a runtime mechanism.
Exploratory design drafting may interleave with gate resolution, but:

- no design may be signed off while any hard gate remains `Proposed`,
- no implementation may start while any hard gate is not `Resolved (design)`.

| Status | Meaning | Satisfying artifact |
|--------|---------|---------------------|
| `Proposed (source analysis)` | A candidate resolution exists only in review/analysis material. It is input to design, not an accepted decision. | Review or analysis document only |
| `Accepted (design)` | The design has chosen a direction and named the state/output shape, owning layer, deterministic algorithm boundary, and verification path. | Draft design section or explicit design decision note |
| `Resolved (design)` | The final design locks the exact contract, algorithm, dependency ordering, and pass/fail verification artifact needed before implementation. | Final design doc with linked verification plan |

## Hard Gate Invariants

These five invariants are the mandatory hard gates for the T-04 design review.

| Gate | Status | Primary layer | Invariant | Required design outcome | Linked risks |
|------|--------|---------------|-----------|-------------------------|--------------|
| `G1` | `Proposed (source analysis)` | 6 | **Structured termination derivation**. `converged`, `convergence_reason_code`, and `termination_reason` MUST be derived from structured controller/orchestrator state, never prose. | A structured termination code or equivalent machine contract exists, with a mapping table to benchmark-facing fields. | `B`, `G` |
| `G2` | `Proposed (source analysis)` | 1-3 | **Synthetic claim provenance**. Any claim created only to satisfy the minimum-one-claim rule MUST be explicitly marked and MUST NOT inflate `effective_delta`. | The state schema distinguishes fallback claims from real claims, and counter computation excludes synthetic fallback claims from `new_claims`, so both `effective_delta` and `compute_quality` treat an all-synthetic turn as `STATIC`/`SHALLOW` unless other real activity exists. | `A` |
| `G3` | `Proposed (source analysis)` | 4-6 | **Evidence provenance retention**. Every accepted scout result MUST be retained as structured provenance, not just counted. | A fixed scout-capture point in the loop is chosen, a per-scout evidence record schema exists, and the synthesis citation surface is defined to consume those records. | `J`, `D`, `F`, `E` |
| `G4` | `Proposed (source analysis)` | 6 / contract surfaces | **Mode contract discipline**. A new mode value MUST NOT be introduced unless all consuming contracts migrate together. | Either a coordinated multi-surface mode migration is specified, or the design explicitly reuses an existing mode with rationale. | `H` |
| `G5` | `Proposed (source analysis)` | 1-2 | **Deterministic referential continuity**. Cross-turn claim continuity MUST be tracked by a deterministic mechanism that does not depend on LLM semantic judgment. | The design explicitly chooses claim IDs, normalized exact match with documented non-goals, or another deterministic hybrid, and specifies how synthetic claims are excluded from continuity matching. | `C` |

## Layer Legend

| Layer | Meaning |
|-------|---------|
| `1-3` | Agent-local turn extraction, local validation, and local counter/delta/action computation |
| `4` | Claude-side scouting with `Glob`, `Grep`, and `Read` |
| `5` | Follow-up composition using local ledger state and `ledger_summary` |
| `6` | Synthesis, benchmark-facing outcome fields, and artifact emission |
| `Cross-cutting` | Multi-layer orchestration, dependency ordering, or verification work |

## Resolution Order And Dependencies

These are the non-obvious ordering constraints for gate closure and risk resolution.

| Dependency | Why it matters |
|------------|----------------|
| `G1 -> G` | Scope-breach termination must emit through the same structured termination contract as normal convergence/budget exits. |
| `G2 -> C` | Synthetic-claim tagging is an input to referential checking because synthetic claims should not participate in continuity matching, but resolving `G2` does **not** resolve Risk `C`. |
| `D -> G3/J` | Scouting position must be fixed before evidence records can be finalized, because the record schema needs a stable capture point and target-claim association. |
| `D + I` | Risks `D` and `I` may share one dry-run artifact, but that artifact must prove both loop order and end-to-end state consistency. |
| `G4` | Mode strategy is largely independent, but if a new mode value remains in play it must be closed before design sign-off because downstream contracts already validate mode values. |

## Risk Register

| ID | Risk | Layer | Benchmark surface | Severity | Likelihood | Gate class | Required control | Verification expectation |
|----|------|-------|-------------------|----------|------------|------------|------------------|--------------------------|
| `B` | `converged` derived from narrative judgment or prose strings | 6 | `converged_within_budget` | High | Medium | Hard Gate `G1` | Local controller emits structured termination code; benchmark-facing fields are projected mechanically. | Unit tests for termination mapping plus one integration assertion from structured termination state to synthesis epilogue. |
| `A` | Minimum-one-claim fallback inflates `effective_delta` | 1-3 | `converged_within_budget` | Medium-High | Medium | Hard Gate `G2` | Fallback claims carry explicit provenance and are excluded from `new_claims`, so they cannot inflate either `effective_delta` or `compute_quality`. | Unit tests covering all-synthetic turns, real-new-claim turns, and mixed real+synthetic turns. |
| `J` | Evidence tracked only as counts, not as reusable provenance | 4-6 | `supported_claim_rate` | Medium-High | High if unspecified | Hard Gate `G3` | Persist per-scout evidence records: `{turn, target_claim, path, line_range, snippet, disposition}` at the fixed scout-capture point. | Synthesis test proves citations come from stored evidence records rather than reconstructed memory. |
| `H` | Candidate `mode` value not migrated across parser/schema/spec surfaces | 6 | Artifact validity | Medium-High | Medium if a new mode remains in scope | Hard Gate `G4` | Update every mode-consuming contract together, or explicitly reuse an existing value with documented rationale. | Contract/tests updated together: schema validation, parser acceptance, synthesis-format docs. |
| `D` | Scouting occurs at inconsistent points in the loop | 4 | `supported_claim_rate` | Medium | Medium | Design Control | Lock scouting between extraction and follow-up; at most one scout round per turn. This decision is a prerequisite for finalizing `G3`. | Same dry-run artifact as `I`: each turn with scouting shows `extract -> control -> scout -> follow-up` in that order. |
| `C` | Referential status errors compound across turns | 1-2 | `converged_within_budget` (indirect) | Medium | Low-Medium | Hard Gate `G5` | Choose and document a deterministic continuity mechanism. Synthetic claims are excluded from continuity matching. | Validation tests cover repeated, revised, conceded, paraphrased, and synthetic-claim cases under the chosen mechanism. |
| `I` | Integration gap between pure functions and behavioral dialogue loop | Cross-cutting | All metrics | Medium | Medium-High unless a dry-run is specified | Design Control | Run one pre-benchmark dry-run dialogue before the corpus benchmark. | Same dry-run artifact as `D`, with explicit pass criteria: stored `effective_delta` equals recomputation from counters, each scout record attaches to a target claim before the next prompt, final outcome fields equal projection from structured termination state, and the epilogue is complete and internally consistent. |
| `F` | Compression drops ledger detail needed for follow-ups | 5 | `supported_claim_rate` (indirect) | Low-Medium | Low-Medium | Design Control | Re-emit a compact canonical ledger block each turn. | Prompt/state inspection shows the block survives and remains sufficient to recompute `ledger_summary`. |
| `K` | `unresolved_closed` remains zero because cross-turn diff is omitted | 1-3 | Ledger trustworthiness | Low | High if not explicit | Design Control | Diff prior and current unresolved lists before counter computation. | Unit tests for closure-only and mixed closure turns. |
| `G` | Scope-breach termination omitted from loop-exit logic | 6 | Safety | Low | Low | Design Control | Treat `scope_breach_count >= 3` as an explicit orchestration-level loop exit using the same structured termination contract as other exits. | Integration test or state-mapping test for scope-breach termination. |
| `E` | Helper-specific `unknown_claim_paths` machinery survives unnecessarily | 4 | None | N/A | N/A | Simplification | Drop path/template machinery; keep only an uncited-claims backlog for provenance debt. | Design review confirms the simplified state still preserves follow-up prioritization. |

## Design Acceptance Checklist

The T-04 design is ready to leave the gate-review stage only when all of the following are true:

1. All hard gates are at least `Accepted (design)` before design sign-off, and all hard gates reach `Resolved (design)` before implementation starts.
2. One pre-benchmark dry-run verification artifact is specified with explicit pass/fail criteria and may satisfy Risks `D` and `I` together.

## Notes for the Design Phase

- The design should treat `B`, `A`, `J`, `H`, and `C` as blockers, not as later polish.
- `E` is not a failure risk; it is a simplification guardrail. The function to preserve is provenance debt tracking, not the helper-era path machinery.
- `G` and `K` are low severity but still structural. They should be resolved in the first design pass so the local ledger does not begin with known blind spots.
- The governing phrase for the entire register is: **compute, don't assess**.
