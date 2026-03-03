# Ticket Plugin Phase 1 — Plan Modularization Design

## Problem

The Phase 1 implementation plan (`docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`) is ~4870 lines with 15 TDD tasks and ~128 tests. An executing agent cannot hold the full plan effectively in context, and reviewing all 15 tasks at once after execution provides no early defect detection.

**Goals:** Reduce per-module context load for executing agents. Enable gated review between modules to catch issues early.

**Non-goals:** Parallelization (the dependency chain is sequential). Modifying the canonical plan during active module execution (the remediation cycle in §Failure Recovery is the sole exception).

**Precondition (Gate 0):** Before M1 starts, verify `superpowers:executing-plans` sub-skill compatibility. The canonical plan's first line requires this sub-skill.

Gate 0 verification commands:
1. Invoke the skill: confirm it exists in `~/.claude/skills/executing-plans/SKILL.md` and loads without error.
2. Check module size constraint: confirm the skill can accept a module plan of ~1924 lines (M4's size).
3. Check non-sequential execution: confirm the skill can handle M2's task order (Task 3 → Task 14, skipping Tasks 4-13).
4. Check checkpoint format: confirm the skill's checkpoint format is compatible with the invariant ledger schema (§Internal Execution Strategy).

**Pass/fail:** All 4 checks must pass. If any fails, resolve the constraint before proceeding — constraints affect all 5 modules. Gate 0 is run by the incoming module executor; any failed check blocks M1 start and is escalated to reviewer/user for environment/skill remediation.

Gate 0 produces a lightweight preflight card (checks 1-4 results + PASS/FAIL + runner identity) committed before M1 starts. The M1 handoff prompt includes this Gate 0 preflight card.

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

**Canonical plan is read-only during active module execution.** Task numbers are not renumbered. Module execution order (e.g., M2 runs Task 3 then Task 14) is specified in this design, not in the plan itself. The remediation cycle (§Failure Recovery, step 3) may re-enter an upstream module to fix defects — this is the sole exception to read-only access. "Read-only" applies to the canonical plan file only; gate artifacts (gate card and evidence) are allowed repository updates under the two-SHA model.

## Gated Review Protocol

At each module boundary, execution pauses for review. Review is contract-aware, not just "did pytest pass."

### Gate Card Format

Each boundary produces a gate card (~20 lines) included in the handoff prompt for the next module:

```
## Gate Card: M{N} → M{N+1}
evaluated_sha: <sha>         # Executor's final commit — the state under review.
handoff_sha: <sha>           # Reviewer's commit after gate card + evidence are added.
commands_to_run: ["uv run pytest tests/", ...]
must_pass_files: [<derived from mapping table below>]
api_surface_expected:
  - module_name: [exported_symbol_1, exported_symbol_2, ...]
verdict: PASS | FAIL
warnings: []                 # Orthogonal to verdict. Non-blocking concerns carried forward.
probe_evidence:              # Command outputs / structured results tied to evaluated_sha.
  - command: "..."
    result: "..."
```

`warnings` are non-blocking. "Carried forward" means warnings remain visible in committed prior gate cards for subsequent reviewers; duplication into each new gate card is optional.

`probe_evidence` is reviewer-authored at gate time and records one entry per probe command executed at that gate. If no probe commands run, set `probe_evidence: []`; at M4→M5, record 4 entries (one per round-trip vector).

**Two-SHA semantics:** The executor commits all module work (`evaluated_sha`). The reviewer runs gate checks against that state, then commits the gate card and evidence artifacts (`handoff_sha`). The next module's handoff prompt references `handoff_sha`. Reviewer gate commits MUST modify only gate artifacts [M]. Before the next module starts, the incoming executor verifies `evaluated_sha..handoff_sha` changes are gate-artifact-only [M] (upgradeable to [S] with an allowlist diff script).

### Module → Task → Test File Mapping

`must_pass_files` is derived from this table, not hand-curated:

| Module | Tasks | Test Files |
|--------|-------|------------|
| M1 | 1-2 | (none — scaffold only; conftest smoke at M1→M2 gate, see below) |
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

- **Standard:** Run `must_pass_files` (cumulative). Verify `api_surface_expected` symbols exist via import check. Verdict is mechanically derived: PASS iff all commands exit 0 and all expected symbols import successfully [T]. At M1→M2: import and call `make_gen1_ticket(tmp_dir)`, `make_gen2_ticket(tmp_dir)`, `make_gen3_ticket(tmp_dir)`, `make_gen4_ticket(tmp_dir)`; assert each returns a `Path` to a file containing fenced YAML. This smoke test must NOT import `parse_ticket` (Task 3 not built yet).
- **Standard+:** Standard + forward-dependency sentinels. Import-only smoke tests for the next module's known imports. At M2→M3: verify `ticket_parse` exports satisfy M3's Tasks 4 and 6 import needs — `extract_fenced_yaml`, `parse_yaml_block` (Task 4) and `ParsedTicket`, `parse_ticket` (Task 6). Task 5 and Task 7 do not import from `ticket_parse`.
- **Critical:** Standard+ + re-run all upstream module test files + downstream preflight (import-only smoke for the module after next, when applicable). At M3→M4: full upstream re-run + verify M4's import subset (`ParsedTicket`, `parse_ticket`, `extract_fenced_yaml`, `parse_yaml_block` from `ticket_parse`; `find_ticket_by_id`, `list_tickets` from `ticket_read`; `dedup_fingerprint`, `normalize`, `target_fingerprint` from `ticket_dedup`; `allocate_id`, `build_filename` from `ticket_id`; `render_ticket` from `ticket_render`). At M4→M5: round-trip gate probe (see below).

**Enforcement tags:** `[T]` = test-enforced, `[S]` = script-enforced, `[M]` = manual review, `[A]` = advisory. Tags apply to gate-critical MUST/SHALL rules only. Untagged policy constraints default to reviewer enforcement [M]; explicit tags are required only for gate-critical MUST/SHALL checks.

**M4→M5 round-trip gate probe [T]:** Task 14 (M2) validates parse→read, but nothing validates write→parse. `_render_canonical_frontmatter` does manual YAML string formatting with data-dependent edge cases. This probe runs at gate time, not during M4 execution.

Concrete probe vectors (4 operations, each with adversarial inputs):

1. **Create** with adversarial tags: `tags: ["auth,api", "[wip]", "plain"]` and `source: {"type": "ad-hoc", "ref": "say \"hello\"", "session": "test"}`. Assert: `parse_ticket` readback produces identical `tags` list and `source` dict (field-level equality).
2. **Update** the created ticket: change `status: open → in-progress`, add tag `"colon: value"`. Assert: all prior fields preserved + new tag present in readback.
3. **Close** the ticket: `status: in-progress → done`. Assert: readback `status == "done"`, all fields preserved.
4. **Reopen** the ticket: `status: done → open`. Assert: readback `status == "open"`, all fields preserved.

**Pass/fail:** All 4 readbacks must produce field-level equality. Any field mismatch = FAIL. The probe vectors exercise the known failure modes of `_render_canonical_frontmatter`: commas in flow-style lists, brackets in tags, and double quotes in string values. Field-level equality is semantic equality on the fields asserted by each probe vector, with required keys present. `None` and missing keys are not equivalent.

Any round-trip probe mismatch is deterministic and triggers Failure Recovery step 3 (re-enter M4 via remediation cycle).

### Failure Recovery

**Trigger conditions:** A failure event is any nonzero exit from: test command, import check, lint, or runtime execution during module work. Failures are classified as **transient** (timeout, flaky test — retry is appropriate) or **deterministic** (assertion failure, import error — retry will not help). After 2 retries of a transient failure, or 1 occurrence of a deterministic failure, escalate to step 2.

1. **Retry locally** (max 2 attempts, transient failures only). Deterministic failures skip directly to step 2.
2. **3-branch attribution:** Run the previous gate's sentinel commands (`commands_to_run` and any smoke checks) as sentinel tests. Base case: if prior gate has no `must_pass_files` (M1→M2), run that gate's `commands_to_run` smoke checks as sentinels.
   - **Sentinels fail → upstream fault.** The defect was introduced before the current module. Proceed to step 3.
   - **Sentinels pass, failure is in a file owned by the current module → local fault.** Fix within the current module.
   - **Sentinels pass, but failure involves cross-module interaction (e.g., import works but returns wrong type) → boundary fault.** The upstream contract is technically satisfied but semantically wrong. Reviewer produces a decision record (owner_module, evidence, scope_of_edits, rerun_commands) and authorizes a scoped remediation cycle (step 3). No "escalate and wait" state — the decision record is mandatory before proceeding.
3. **If upstream fault → remediation cycle:** Stop current module. Re-enter the upstream module to fix the defect. Produce a new `evaluated_sha` + updated gate card + root-cause note. The remediation cycle completes when the upstream gate re-passes.
4. **Cross-boundary edits disallowed** unless a remediation cycle is explicitly triggered by upstream or boundary fault (steps 2-3). An executing agent must never edit files owned by a prior module during normal execution.

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

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares the current ledger against the prior checkpoint's ledger (both are committed artifacts). This catches the "pass-while-wrong" scenario where an agent accidentally deletes a test class block during Task 11 appends — pytest passes (deleted tests aren't collected) but the monotonicity check fails. Detection occurs at the next full checkpoint (slices 1, 3, 6), not immediately — commit-only slices (2, 4, 5) are unmonitored. Upgradeable to `[S]` when an automated comparison script exists.

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
- **Adversarial review (round 2):** Thread `019cb1b9-209f-7520-993d-4ec13ab8d390`, 5/10 turns, converged. Found 4 P0 + 3 P1 + 3 P2 defects. All P0 and P1 applied.
- **Adversarial review (round 3):** Thread `019cb1d9-c7b3-7142-8800-8daadf4a5bd9`, 5/10 turns, converged. Found 4 P0 + 5 P1 + 2 P2 defects (11 total). Key findings: self-certification gap, wrong sentinel imports, non-executable probe, immutability deadlock.
- **Collaborative findings triage:** Thread `019cb1ee-ebdb-72f2-a025-85f9a4324e43`, 6/10 turns, converged. Rejected 2 heavyweight mechanisms (Boundary Contract Manifest, Errata Overlay). All 11 findings applied as lightweight inline fixes. Emerged: enforcement tags, probe_evidence block, 3-branch attribution model.
- **Adversarial review (round 4):** Thread `019cb213-fd9b-7f72-860a-54b87db5e2ed`, 6/10 turns, converged. Found 1 P0 + 8 P1 + 5 P2 defects. Key findings: boundary fault deadlock, enforcement tag coverage, gate-time failure ownership, dual-doc freeze, warnings carry-forward, sentinel attribution scope, two-SHA identity.
- **Collaborative findings triage (round 4):** Thread `019cb22b-a96f-72c2-ae99-9ae3b504e2c9`, 6/10 turns, converged. Applied 12 of 14 findings as lightweight inline fixes. Rejected P2-1 (speculative blast-radius). Deferred P1-4 (monotonicity upgrade control). Emerged: integrated step 2 rewrite, executor cross-verification, semantic equality softening.
- **Open questions (non-blocking):** Whether monotonicity enforcement should be upgraded from `[M]` to `[S]` before M4 execution, and what trigger condition / go-no-go criterion should govern that decision.
