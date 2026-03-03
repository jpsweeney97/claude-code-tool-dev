# Ticket Plugin Phase 1 — Plan Modularization Design

## Problem

The Phase 1 implementation plan (`docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`) is ~4870 lines with 15 TDD tasks and ~128 tests. An executing agent cannot hold the full plan effectively in context, and reviewing all 15 tasks at once after execution provides no early defect detection.

**Goals:** Reduce per-module context load for executing agents. Enable gated review between modules to catch issues early.

**Non-goals:** Parallelization (the dependency chain is sequential). Modifying the canonical plan (it remains the immutable reference).

## Module Structure

5 modules executed sequentially with gated review between each.

| Module | Tasks | ~Lines | ~Tests | Theme |
|--------|-------|--------|--------|-------|
| M1 Foundation | 1-2 | 500 | 0 | Scaffold + contract ref doc |
| M2 Parse+Migration | 3, 14 | 784 | 25 | Parser + migration golden tests |
| M3 Utilities | 4-7 | 975 | 42 | ID + render + read + dedup |
| M4 Engine | 8-11 | 1924 | 49 | classify + plan + preflight + execute |
| M5 Integration | 12-13, 15 | 617 | 9 | Entrypoints + integration + final |

### Design Decisions

**Task 14 relocated to M2.** Parse is the highest fan-out contract — 5 downstream tasks import from `ticket_parse`. Migration golden tests validate the parser immediately after it's built, catching defects before M3-M5 build on top. Within M2, execution is phased: implement Task 3 first, then execute Task 14's golden tests.

**Tasks 8-11 kept together in M4.** All four modify `ticket_engine_core.py` and `test_engine.py`. Splitting across module boundaries creates partial-file handoffs — the highest-risk boundary type. M4 at ~1924 lines is the largest module, but well within agent context capacity (~200k tokens). Reliability is managed through internal checkpoints.

**Task 15 grouped with M5.** Final suite run and cleanup belong with integration.

**Canonical plan is immutable.** Task numbers are not renumbered. Module execution order (e.g., M2 runs Task 3 then Task 14) is specified in this design, not in the plan itself.

## Gated Review Protocol

At each module boundary, execution pauses for review. Review is contract-aware, not just "did pytest pass."

### Gate Card Format

Each boundary produces a gate card (~20 lines) included in the handoff prompt for the next module:

```
## Gate Card: M{N} → M{N+1}
commit_sha: <sha>
commands_to_run: ["uv run pytest tests/", ...]
must_pass_files: [test_parse.py, test_id.py, ...]
api_surface_expected:
  - module_name: [exported_symbol_1, exported_symbol_2, ...]
verdict: PASS | FAIL
```

### Boundary Risk Classification

| Boundary | Risk | Gate Type | Rationale |
|----------|------|-----------|-----------|
| M1→M2 | Low | Standard | No code produced by M1, just scaffold |
| M2→M3 | Medium | Standard+ | Parse is high fan-out; migration golden tests validate it |
| M3→M4 | High | Critical | Widest import surface — M4 imports from all 5 utility modules |
| M4→M5 | Medium | Standard | Engine is complete; entrypoints are thin wrappers |

**Critical boundary (M3→M4):** Re-runs upstream sentinel tests. Verifies exported symbols + signatures match expectations.

### Failure Recovery

1. Retry locally (2 attempts within the module)
2. Run upstream sentinel tests — if they fail, the defect is upstream
3. If sentinels fail: stop, open remediation cycle on the upstream module
4. Cross-boundary edits disallowed unless remediation cycle explicitly invoked

## Internal Execution Strategy

### M4 Engine (Tasks 8-11, ~1924 lines)

Internal checkpoints after each task (8, 9, 10, mid-11). Each checkpoint has 3 components:

1. **Test barrier** — `uv run pytest tests/test_engine.py` must pass
2. **Git commit** — durable snapshot for rollback
3. **Invariant ledger** — 6-10 lines naming what the next task may depend on

Task 11 executes as vertical TDD slices:

| Slice | Content |
|-------|---------|
| 1 | Shared helpers (`_render_canonical_frontmatter`, `_is_valid_transition`, `_check_transition_preconditions`, constants) + tests |
| 2 | `_execute_create` + tests |
| 3 | `_execute_update` + tests |
| 4 | `_execute_close` + tests |
| 5 | `_execute_reopen` + tests |
| 6 | `engine_execute` dispatcher + integration-level tests |

Each slice gets a git commit.

### M2 Parse+Migration (Tasks 3, 14)

Phased execution:

1. Implement Task 3 (parser, ~617 lines of plan)
2. Brief invariant summary of parse API surface
3. Execute Task 14 (migration golden tests, ~169 lines of plan)

### M1, M3, M5

Standard sequential TDD flow. No special internal strategy — all under 1000 lines.

## Provenance

- **Codex dialogue:** Thread `019cb19e-f668-7913-8e00-198815906978`, collaborative posture, 6/12 turns, converged.
- **Key convergence points:** 5-module split (High), Task 14 relocation (High), Tasks 8-11 unsplittable (High), contract-aware gates (High).
- **Open questions (non-blocking):** API surface encoding in gate cards, `executing-plans` sub-skill manifest compatibility, M4 invariant ledger standardization.
