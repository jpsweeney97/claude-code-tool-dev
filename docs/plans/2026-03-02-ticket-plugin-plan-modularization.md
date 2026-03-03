# Ticket Plugin Phase 1 — Plan Modularization Design

## Problem

The Phase 1 implementation plan (`docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`) is ~4870 lines with 15 TDD tasks and ~128 tests. An executing agent cannot hold the full plan effectively in context, and reviewing all 15 tasks at once after execution provides no early defect detection.

**Goals:** Reduce per-module context load for executing agents. Enable gated review between modules to catch issues early.

**Non-goals:** Parallelization (the dependency chain is sequential). Modifying the canonical plan (it remains the immutable reference).

**Precondition (Gate 0):** Before M1 starts, verify `superpowers:executing-plans` sub-skill compatibility. The canonical plan's first line requires this sub-skill. If the sub-skill has constraints on module size, handoff shape, or checkpoint format, those affect all 5 modules and must be resolved before execution begins.

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

**Task 14 relocated to M2.** Parse is the highest fan-out contract — 5 downstream tasks import from `ticket_parse`. Migration golden tests validate the parser immediately after it's built, catching defects before M3-M5 build on top. Within M2, execution is phased: implement Task 3 first, then execute Task 14's golden tests. Task 14 also depends on `make_gen1/2/3/4_ticket` conftest fixtures from Task 1 (M1) — satisfied because M1 executes before M2.

**Tasks 8-11 kept together in M4.** All four modify `ticket_engine_core.py` and `test_engine.py`. Splitting across module boundaries creates partial-file handoffs — the highest-risk boundary type. M4 at ~1924 lines is the largest module, but well within agent context capacity (~200k tokens). Reliability is managed through internal checkpoints.

**Task 15 grouped with M5.** Final suite run and cleanup belong with integration.

**Canonical plan is immutable.** Task numbers are not renumbered. Module execution order (e.g., M2 runs Task 3 then Task 14) is specified in this design, not in the plan itself.

## Gated Review Protocol

At each module boundary, execution pauses for review. Review is contract-aware, not just "did pytest pass."

### Gate Card Format

Each boundary produces a gate card (~20 lines) included in the handoff prompt for the next module:

```
## Gate Card: M{N} → M{N+1}
commit_sha: <sha>            # Post-gate commit on a clean tree. Gate card is committed.
commands_to_run: ["uv run pytest tests/", ...]
must_pass_files: [<derived from mapping table below>]
api_surface_expected:
  - module_name: [exported_symbol_1, exported_symbol_2, ...]
verdict: PASS | FAIL | PASS_WITH_WARNINGS
warnings: []                 # Non-blocking concerns carried to next module's review
```

**commit_sha semantics:** The SHA references a committed, clean-tree state. The executing agent commits all module work, then the reviewer evaluates committed state. The gate card itself is committed as part of the handoff.

### Module → Task → Test File Mapping

`must_pass_files` is derived from this table, not hand-curated:

| Module | Tasks | Test Files |
|--------|-------|------------|
| M1 | 1-2 | (none — scaffold only; conftest.py verified implicitly by M2) |
| M2 | 3, 14 | test_parse.py, test_migration.py |
| M3 | 4-7 | test_id.py, test_render.py, test_read.py, test_dedup.py |
| M4 | 8-11 | test_engine.py |
| M5 | 12-13, 15 | test_entrypoints.py, test_integration.py |

Each gate's `must_pass_files` is the cumulative set: all test files from the current module and all prior modules.

### Boundary Risk Classification

| Boundary | Risk | Gate Type | Rationale |
|----------|------|-----------|-----------|
| M1→M2 | Medium | Standard | Scaffold + conftest.py fixtures — semantic fixture drift risk propagates to all modules |
| M2→M3 | Medium | Standard+ | Parse is high fan-out; migration golden tests validate it |
| M3→M4 | High | Critical | Widest import surface — M4 imports from all 5 utility modules |
| M4→M5 | High | Critical | Round-trip fidelity — engine write→parse readback must be verified |

**Gate type definitions:**

- **Standard:** Run `must_pass_files` (cumulative). Verify `api_surface_expected` symbols exist. Binary verdict.
- **Standard+:** Standard + forward-dependency sentinels. Verify downstream import contracts are satisfiable by running import-only smoke tests for the next module's known imports. At M2→M3: verify `ticket_parse` exports satisfy M3's Tasks 6 and 7 import needs (`ParsedTicket`, `parse_ticket`, `extract_fenced_yaml`).
- **Critical:** Standard+ + re-run all upstream module test files. Verify exported symbols + signatures match expectations. At M3→M4: full upstream re-run. At M4→M5: round-trip gate probe (see below).

**M4→M5 round-trip gate probe:** Task 14 (M2) validates parse→read, but nothing validates write→parse. `_render_canonical_frontmatter` does manual YAML string formatting with data-dependent edge cases (commas in tags, unescaped quotes in source fields). Gate command (not a plan mutation): create/update/close/reopen via `engine_execute`, then `parse_ticket` readback with field-level fidelity checks. This probe runs at gate time, not during M4 execution.

### Failure Recovery

1. **Retry locally** (2 attempts within the module)
2. **Run upstream sentinel tests** — the previous gate's `must_pass_files`. If they pass, the defect is in the current module. If they fail, the defect is upstream.
3. **If sentinels fail → remediation cycle:** Stop current module. Re-enter the upstream module's session. Fix the defect. Produce a new `commit_sha` + updated gate card + root-cause note. The remediation cycle completes when the upstream gate re-passes.
4. **Cross-boundary edits disallowed** unless a remediation cycle is explicitly triggered by sentinel failure (step 3). An executing agent must never edit files owned by a prior module during normal execution.

## Internal Execution Strategy

### M4 Engine (Tasks 8-11, ~1924 lines)

Internal checkpoints after each task (8, 9, 10) and after Task 11 slices 1, 3, and 6. Each checkpoint has 3 required components:

1. **Test barrier** — `uv run pytest tests/test_engine.py` must pass
2. **Git commit** — durable snapshot for rollback
3. **Invariant ledger** — 6-10 lines with concrete schema (see below)

**Invariant ledger schema:**

```
## Checkpoint: after Task {N} / Slice {S}
test_classes: [TestEngineClassify, TestEnginePlan, ...]
per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5, ...}
exports: [engine_classify, engine_plan, ...]
next_task_depends_on: [engine_classify, engine_plan, ...]
```

**Monotonic subset enforcement:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. This catches the "pass-while-wrong" scenario where an agent accidentally deletes a test class block during Task 11 appends — pytest passes (deleted tests aren't collected) but the monotonicity check fails.

Task 11 executes as vertical TDD slices:

| Slice | Content | Checkpoint? |
|-------|---------|-------------|
| 1 | Shared helpers (`_render_canonical_frontmatter`, `_is_valid_transition`, `_check_transition_preconditions`, constants) + tests | Yes |
| 2 | `_execute_create` + tests | Git commit only |
| 3 | `_execute_update` + tests | Yes |
| 4 | `_execute_close` + tests | Git commit only |
| 5 | `_execute_reopen` + tests | Git commit only |
| 6 | `engine_execute` dispatcher + integration-level tests | Yes (final M4 checkpoint) |

All slices get a git commit. Slices 1, 3, and 6 get full checkpoints (test barrier + commit + invariant ledger). The others get commit-only snapshots for rollback.

### M2 Parse+Migration (Tasks 3, 14)

Phased execution:

1. Implement Task 3 (parser, ~617 lines of plan)
2. Brief invariant summary of parse API surface
3. Execute Task 14 (migration golden tests, ~169 lines of plan)

### M1, M3, M5

Standard sequential TDD flow. No special internal strategy — all under 1000 lines.

## Provenance

- **Collaborative dialogue:** Thread `019cb19e-f668-7913-8e00-198815906978`, 6/12 turns, converged. Established 5-module split, Task 14 relocation, Tasks 8-11 unsplittable, contract-aware gates (all High confidence).
- **Adversarial review:** Thread `019cb1b9-209f-7520-993d-4ec13ab8d390`, 5/10 turns, converged. Found 4 P0 + 3 P1 + 3 P2 defects. All P0 and P1 findings applied in this revision.
- **Open questions (non-blocking):** M4 ledger enforcement mechanism (manual check vs. automated script), whether design should explicitly label itself as process-reliant vs. deterministically enforced.
