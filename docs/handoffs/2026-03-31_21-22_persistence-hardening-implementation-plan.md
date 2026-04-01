---
date: 2026-03-31
time: "21:22"
created_at: "2026-04-01T01:22:33Z"
session_id: 80a018b4-e00c-4c5c-8a0c-b7871ce72fdf
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md
project: claude-code-tool-dev
branch: main
commit: ac097928
title: "persistence hardening implementation plan"
type: handoff
files:
  - docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md
  - packages/plugins/codex-collaboration/server/replay.py
  - packages/plugins/codex-collaboration/server/turn_store.py
  - packages/plugins/codex-collaboration/server/lineage_store.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/tests/test_replay.py
  - packages/plugins/codex-collaboration/tests/test_turn_store.py
  - packages/plugins/codex-collaboration/tests/test_lineage_store.py
  - packages/plugins/codex-collaboration/tests/test_journal.py
  - packages/plugins/codex-collaboration/tests/test_profiles.py
  - packages/plugins/codex-collaboration/tests/test_models_r2.py
---

# persistence hardening implementation plan

## Goal

Write a complete, executable implementation plan from the persistence hardening and type narrowing design spec (`docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md`). The plan must resolve all open API naming, module placement, test strategy, and type alias questions left from the design session, and produce bite-sized TDD tasks that a subagent can execute without re-reading any source file.

**Trigger:** Loaded the prior handoff (`2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md`) whose next step #1 was "Write implementation plan from design spec." User provided structured context: 5 key design facts and 4 open questions to resolve during planning.

**Stakes:** The plan is the input for the next session's implementation work. Incomplete or inconsistent code in the plan would produce bugs during execution. The four open questions (API names, validation placement, test strictness, type alias location) must be resolved in the plan — they cannot be deferred to implementation time without creating inconsistencies across the 6 tasks.

**Success criteria:** (1) Plan covers all 5 findings (I2, I3, I4, F4, F6). (2) Every task has complete code — no placeholders. (3) Type signatures, function names, and imports are consistent across tasks. (4) Self-review passes spec coverage, placeholder scan, and type consistency checks.

**Connection to project arc:** This plan enables implementation of correctness debt (I2/I3/I4) on delivered R2 infrastructure and cleanup (F4/F6) deferred from the T-03 safety substrate second review. AC6 analytics (actual roadmap work in packet 2b) remains deferred — user chose persistence hardening first to solidify the R2 substrate.

## Session Narrative

Session began by loading the prior handoff, which described the `codex.consult` resolution and persistence hardening design work. The handoff listed four next steps; step #1 was "Write implementation plan from design spec" using the `writing-plans` skill.

After archiving the handoff and confirming context, the user provided a structured message with two sections: "Relevant information" (5 key facts about the replay helper design) and "Open questions" (4 specific unknowns that needed resolution during planning). This was the seed for the plan — the user framed the problem space before plan writing rather than letting it emerge organically.

The 5 key facts provided:
1. Shared mechanism / local policy is the intended factoring
2. The replay helper contract centers on `replay_jsonl(...)` plus structured diagnostics with physical line numbers and deferred classification
3. `bool` must not pass integer validation; checks use `type(x) is int`
4. Control plane does not own all persistence stores — no control-plane-only health surface
5. `check_health()` is test/support only, not operational

The 4 open questions:
1. Exact helper/module API names in `server/replay.py`
2. Whether store-specific validation stays inline or gets small local helpers
3. How strict tests should be about diagnostic `detail` strings
4. Whether type aliases for narrowing belong in `models.py` or stay local to `profiles.py`

Invoked the `writing-plans` skill. The first phase was deep codebase reading — 11 files read in parallel batches:

**Batch 1 (design spec + 3 stores):** Read the design spec (330 lines), `turn_store.py` (73 lines), `lineage_store.py` (133 lines), `journal.py` (178 lines). The design spec was comprehensive — all contract tables, algorithm steps, per-store callback specifications, exception types, and test plans were fully specified. The stores confirmed the exact bug sites: `turn_store.py:70` (bare `record['collaboration_id']` — I2), `lineage_store.py:110-127` (no else branch — I4), `journal.py:144` (`OperationJournalEntry(**record)` — crashes on extra fields).

**Batch 2 (type targets + runtime):** Read `profiles.py` (137 lines), `models.py` (245 lines), `runtime.py:1-30`. Confirmed `ResolvedProfile` at `profiles.py:21-29` has 5 stringly-typed fields. Confirmed `AdvisoryRuntimeState.session` at `models.py:123` is `Any`. Confirmed `AppServerRuntimeSession` at `runtime.py:12` is the concrete type. Noted `from __future__ import annotations` already present in `models.py` — enabling the `TYPE_CHECKING` guard pattern.

**Batch 3 (existing tests):** Read all 5 test files (`test_turn_store.py`, `test_lineage_store.py`, `test_journal.py`, `test_profiles.py`, `test_models_r2.py`) plus `pyproject.toml`. Identified test patterns: `TestXxx` class grouping, `tmp_path` fixture, helper factories (`_make_handle()`, `_make_intent()`), `monkeypatch` for fsync tracking. Current test count: 359. Test config: `pythonpath = ["."]`, `testpaths = ["tests"]`.

No pivots during the reading phase — the design spec was complete and the codebase matched expectations from the prior session's knowledge.

The plan writing phase resolved all 4 open questions:

**Q1 (API names):** `replay_jsonl()` as the main function, `SchemaViolation` and `UnknownOperation` as exception types, `ReplayDiagnostic` and `ReplayDiagnostics` as diagnostic types. Per-store callbacks: `_turn_callback` (module-level function), `_make_lineage_callback` (factory returning closure), `_journal_callback` (module-level function).

**Q2 (Validation placement):** Module-level functions, not class methods. The lineage store requires a closure factory because the callback mutates a `dict[str, CollaborationHandle]` — the `replay_jsonl` helper's `apply` callback returns `T | None`, but lineage's callback returns `None` always and instead mutates the captured dict. The factory `_make_lineage_callback(handles)` creates the closure. Turn and journal callbacks are pure functions.

**Q3 (Test detail strictness):** Substring matching on diagnostic detail strings (e.g., `assert "collaboration_id" in diag.detail`), not exact string comparison. This prevents tests from breaking on message wording changes while still verifying the diagnostic identifies the right field.

**Q4 (Type alias placement):** `Posture`, `Effort`, `SandboxPolicy`, `ApprovalPolicy` defined in `profiles.py`, not `models.py`. These types are domain-specific to profile resolution — no other module references them.

The plan was written as 6 tasks with complete code blocks totaling 1490 lines. Each task follows TDD: write failing tests → run to verify failure → implement → run to verify pass → run full suite → commit. The self-review checked spec coverage (all 5 findings mapped), placeholder scan (none found), and type consistency (signatures, imports, return types consistent across all tasks).

User was presented with two execution options (subagent-driven vs inline) and immediately ran `/save` — indicating preference for plan → execution in separate sessions.

## Decisions

### Module-level callbacks, not class methods

**Choice:** Per-store replay callbacks are module-level functions (or factory functions), not methods on the store classes.

**Driver:** The `replay_jsonl()` helper expects `Callable[[dict[str, Any]], T | None]`. A bound method would work, but callbacks don't reference `self` — they validate record fields and construct domain objects. Module-level placement makes the helper/callback boundary explicit and enables direct unit testing.

**Alternatives considered:**
- **Class methods on each store** — would work but entangles the callback with store lifecycle. `check_health()` and `_replay()` both call the same callback; method placement suggests the callback is a store concern when it's actually a schema concern. Rejected for unclear responsibility boundaries.

**Trade-offs accepted:** The lineage callback factory (`_make_lineage_callback`) is slightly unusual — it returns a closure that mutates a captured dict. This is a non-obvious usage of the `replay_jsonl` generic interface but is documented in the design spec and the plan's code comments.

**Confidence:** High (E2) — the callback is pure validation + construction logic. Module-level placement matches Python convention for functions that don't need instance state. Verified by tracing both `_replay()` and `check_health()` call paths.

**Reversibility:** High — moving callbacks to methods is a refactor with no behavioral change.

**Change trigger:** If a fourth store with fundamentally different callback lifecycle needs (e.g., database transactions) is added, the module-level pattern may need revisiting.

### Substring matching for diagnostic detail assertions

**Choice:** Tests assert that diagnostic `detail` strings contain key substrings (field names, type names) rather than matching exact messages.

**Driver:** Diagnostic detail strings are developer-facing, not API contracts. Exact string matching would make tests brittle to wording changes. The important invariant is that the diagnostic identifies the correct field and failure mode, not the exact phrasing.

**Alternatives considered:**
- **Exact string matching** — rejected. Would require updating tests for any message wording change, creating maintenance burden with no correctness benefit.
- **No detail assertions at all** — rejected. Would not verify that diagnostics contain useful information. A diagnostic with `detail=""` would pass, defeating the purpose.

**Trade-offs accepted:** Substring matching could pass on coincidentally matching substrings in future detail messages. Unlikely given the specificity of field names like `"collaboration_id"` and type names like `"list"`.

**Confidence:** High (E1) — standard testing practice for human-readable messages.

**Reversibility:** High — tightening to exact match is additive.

**Change trigger:** If diagnostic details become part of a stable API (e.g., surfaced in `codex.status`), they need exact assertions and version stability.

### Type aliases local to profiles.py, not models.py

**Choice:** `Posture`, `Effort`, `SandboxPolicy`, `ApprovalPolicy` defined in `server/profiles.py`.

**Driver:** These types are consumed by `ResolvedProfile` and `resolve_profile()`, both in `profiles.py`. No other module imports or references them. Placing them in `models.py` would add exports without consumers.

**Alternatives considered:**
- **Define in models.py** — rejected. `models.py` is the shared data model module. These literals are profile-resolution domain types, not model types. `models.py` already imports from `typing` but doesn't define any `Literal` aliases for domain concepts (the existing `HandleStatus`, `AuthStatus`, `CapabilityProfile` are genuinely shared across modules).

**Trade-offs accepted:** If a future module needs to reference `Posture` (e.g., a YAML validator), it would import from `profiles.py` rather than `models.py`. This is a minor import path difference.

**Confidence:** High (E2) — verified by grepping for `posture` across the codebase. Only `profiles.py` and `control_plane.py` reference posture values. `control_plane.py` passes posture as a string from `resolve_profile()` — it doesn't need the type alias.

**Reversibility:** High — moving a type alias is a trivial refactor.

**Change trigger:** If `control_plane.py` or another module needs to type-check posture values at their boundary (not just pass them through).

### Lineage closure factory pattern for replay callback

**Choice:** `_make_lineage_callback(handles: dict[str, CollaborationHandle]) -> Callable[[dict[str, Any]], None]` — factory that returns a closure mutating the captured dict.

**Driver:** The lineage store's replay semantics are accumulator-based: the callback applies operations (create, update_status, update_runtime) to a mutable dict, building up handle state. The `replay_jsonl` helper returns `tuple[T, ...]` — results collected from callback return values. Since lineage's callback returns `None` (mutation, not return), the results tuple is empty and the real output is the closure-captured dict.

**Alternatives considered:**
- **Return value from callback** — rejected. The design spec (from the prior session) explicitly evaluated this and identified that "lineage uses `replay_jsonl` with a closure-captured accumulator" was the resolution after the user's P2 finding that splitting into `decode_jsonl` + `replay_jsonl` would recreate divergence one layer higher.
- **Instance method with self._handles** — rejected (see "Module-level callbacks" decision above).

**Trade-offs accepted:** The closure pattern is non-obvious: `_make_lineage_callback(handles)` creates a function that mutates `handles` as a side effect. Both `_replay()` and `check_health()` create fresh `handles` dicts and pass them to the factory. This is documented in the plan's code and the design spec.

**Confidence:** High (E2) — this was a deliberate design decision from the prior session, validated by the user's P2 finding. The plan implements it exactly as specified.

**Reversibility:** Medium — changing the callback pattern requires restructuring how lineage uses `replay_jsonl`.

**Change trigger:** If `replay_jsonl` is extended with a separate accumulator mode (e.g., a `reduce` parameter), the closure becomes unnecessary.

## Changes

### Created files

| File | Lines | Purpose |
|------|-------|---------|
| `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` | 1490 | Complete implementation plan with 6 TDD tasks, 52 new test cases, full code blocks |

### Files read but not modified

| File | Why read | Key patterns discovered |
|------|----------|----------------------|
| `server/turn_store.py` (73 lines) | I2 bug site, migration target | `_replay()` at line 56: inline JSONL loop. Line 70: `record['collaboration_id']` — bare key access crashes on missing field. No type validation. `write()` uses fsync. |
| `server/lineage_store.py` (133 lines) | I4 bug site, migration target | `_replay()` at line 88: inline JSONL loop delegates to `_apply_record()`. `_apply_record()` at line 105: `op = record.get("op")` → `if op == "create" ... elif ...` with no else. Unknown ops fall through silently. `_replace_handle` at line 130: module-level helper for frozen dataclass field replacement via `{**asdict(handle), **changes}`. |
| `server/journal.py` (178 lines) | Migration target | `_terminal_phases()` at line 129: `OperationJournalEntry(**record)` at line 144 crashes on extra fields (forward-compat bug). `_operations_path()` at line 148: `journal_dir / "operations" / f"{session_id}.jsonl"`. Has separate marker system (JSON, not JSONL) and audit log — only the operations JSONL uses replay. |
| `server/profiles.py` (137 lines) | F4 target | `ResolvedProfile` at line 21: `posture: str`, `effort: str | None`, `sandbox: str`, `approval_policy: str`. Resolution at lines 96-116: explicit flags override profile YAML values. Validation gate at lines 118-128: rejects non-default sandbox/approval but doesn't catch posture/effort typos. |
| `server/models.py` (245 lines) | F6 target | `AdvisoryRuntimeState` at line 111: mutable dataclass (not frozen). `session: Any` at line 123. Already has `from __future__ import annotations`. Already imports `Any` and `Literal` from `typing`. `CollaborationHandle` at line 158: 8 required str fields + 5 optional (4 `str | None`, 1 `int | None`). `OperationJournalEntry` at line 226: 6 required str fields + 4 optional (2 `str | None`, 2 `int | None`). |
| `server/runtime.py` (lines 1-30) | F6 concrete type | `AppServerRuntimeSession` at line 12: thin wrapper over `JsonRpcClient`. Imports `RuntimeHandshake`, `AccountState`, `TurnExecutionResult` from `.models`. |
| `tests/test_turn_store.py` (90 lines) | Test patterns | `TestWriteAndGet` (6 tests), `TestCrashRecovery` (3 tests), `TestGetAll` (2 tests). Uses `tmp_path` fixture, `monkeypatch` for fsync tracking. Direct store construction: `TurnStore(tmp_path, "sess-1")`. |
| `tests/test_lineage_store.py` (182 lines) | Test patterns | `_make_handle()` helper factory at line 16. `TestCreateAndGet` (4), `TestCrashRecovery` (3), `TestList` (3), `TestUpdateStatus` (2), `TestUpdateRuntime` (2), `TestCleanup` (2). Uses `json` import for direct JSONL manipulation in crash recovery tests. |
| `tests/test_journal.py` (212 lines) | Test patterns | `_make_intent()` helper factory at line 67. Mixed style: standalone functions for stale markers, `TestPhasedJournal` class for operations. `import pytest` appears mid-file at line 62 (above `_make_intent`). Direct path manipulation for operations JSONL in some tests. |
| `tests/test_profiles.py` (89 lines) | Test patterns | `TestLoadProfiles` (2), `TestResolveProfile` (8). Imports `load_profiles`, `resolve_profile`, `ProfileValidationError`. Tests specific profile names from bundled YAML (`quick-check`, `deep-review`, `debugging`). |
| `tests/test_models_r2.py` (162 lines) | Test patterns | Standalone test functions (no classes). Tests dataclass construction, frozen behavior, field counts, serialization. Uses `pytest.raises(FrozenInstanceError)`. Imports specific model types. |
| `pyproject.toml` (17 lines) | Test configuration | `requires-python = ">=3.11"`, `dependencies = ["pyyaml>=6.0"]`, dev deps: `pytest>=8.0`, `ruff>=0.8`. pytest config: `pythonpath = ["."]`, `testpaths = ["tests"]`. |

## Codebase Knowledge

### JSONL Replay Pattern (current — pre-migration)

All three stores share this inline replay pattern:

```
open file → iterate lines → strip → skip blank → json.loads → apply
                                                    ↓ fail: continue
```

Divergences after successful `json.loads`:

| Store | File:line | Post-parse behavior | Failure mode |
|-------|-----------|-------------------|--------------|
| TurnStore | `turn_store.py:70` | `record['collaboration_id']` — bare key access | `KeyError` crashes entire replay |
| LineageStore | `lineage_store.py:110-127` | `if op == "create" ... elif ...` — no else branch | Unknown ops silently dropped |
| Journal | `journal.py:144` | `OperationJournalEntry(**record)` — kwargs construction | `TypeError` on extra fields; no type validation |

### Store Ownership and Construction

| Store | Owner | Construction | Path pattern |
|-------|-------|-------------|--------------|
| `TurnStore` | `DialogueManager` (`dialogue.py:55`) | `TurnStore(plugin_data_path, session_id)` | `{data}/turns/{session}/turn_metadata.jsonl` |
| `LineageStore` | `DialogueManager` (`dialogue.py:55`) | `LineageStore(plugin_data_path, session_id)` | `{data}/lineage/{session}/handles.jsonl` |
| `OperationJournal` | `ControlPlane` (construction) | `OperationJournal(plugin_data_path)` | `{data}/journal/operations/{session}.jsonl` |

Key difference: TurnStore and LineageStore are session-partitioned (one file per session). Journal is shared (session_id is a parameter to methods, not construction).

### CollaborationHandle Field Inventory

Required (no default):
- `collaboration_id: str`, `capability_class: CapabilityProfile`, `runtime_id: str`
- `codex_thread_id: str`, `claude_session_id: str`, `repo_root: str`
- `created_at: str`, `status: HandleStatus`

Optional (defaulted):
- `parent_collaboration_id: str | None = None`, `fork_reason: str | None = None`
- `resolved_posture: str | None = None`, `resolved_effort: str | None = None`
- `resolved_turn_budget: int | None = None`

The lineage create callback validates all required fields as strings, optional strings if present, and `resolved_turn_budget` with `type(x) is int` (not `isinstance`).

### OperationJournalEntry Field Inventory

Required (no default):
- `idempotency_key: str`, `operation: Literal["thread_creation", "turn_dispatch"]`
- `phase: Literal["intent", "dispatched", "completed"]`, `collaboration_id: str`
- `created_at: str`, `repo_root: str`

Optional (defaulted):
- `codex_thread_id: str | None = None`, `turn_sequence: int | None = None`
- `runtime_id: str | None = None`, `context_size: int | None = None`

The journal callback validates `operation` and `phase` values against known sets (unlike lineage, where enum values are unchecked — forward-compatible). Unknown operation/phase values are `SchemaViolation`, not `UnknownOperation`.

### Test Infrastructure

| Pattern | Location | Usage |
|---------|----------|-------|
| `TestXxx` class grouping | All test files | Groups related tests by feature (e.g., `TestCrashRecovery`) |
| `tmp_path` fixture | All store tests | pytest built-in for temporary directories |
| `_make_handle()` factory | `test_lineage_store.py:16` | Creates `CollaborationHandle` with defaults |
| `_make_intent()` factory | `test_journal.py:67` | Creates `OperationJournalEntry` intent phase |
| `monkeypatch` fsync tracking | `test_turn_store.py:43`, `test_lineage_store.py:60` | Verifies crash-safety via fsync |
| Direct JSONL manipulation | All crash recovery tests | Opens store file, appends corrupt lines |
| No mocking framework | Across suite | `monkeypatch` only; no `unittest.mock` usage in store tests |

### Import Conventions

All source files in `server/` use `from __future__ import annotations`. Imports follow: stdlib → relative package imports. Type imports use `from typing import ...` (not `typing.TYPE_CHECKING` currently — F6 will be the first use of `TYPE_CHECKING` in `models.py`).

### Module Dependency Graph (area touched)

```
replay.py (NEW — no imports from server/)
    ↑
    ├── turn_store.py (imports replay_jsonl, SchemaViolation, ReplayDiagnostics)
    ├── lineage_store.py (imports replay_jsonl, SchemaViolation, UnknownOperation, ReplayDiagnostics)
    └── journal.py (imports replay_jsonl, SchemaViolation, ReplayDiagnostics)

models.py ──TYPE_CHECKING──→ runtime.py (F6: circular import guard)
    ↑                              │
    └──────────────────────────────┘ (runtime.py imports from models.py)

profiles.py (self-contained — Posture/Effort/SandboxPolicy/ApprovalPolicy defined locally)
```

`replay.py` is a foundation module with zero intra-package dependencies — only stdlib imports (`json`, `dataclasses`, `pathlib`, `typing`). This ensures no circular imports when all three stores import from it.

## Context

### Mental Model

This session was a **spec-to-plan translation** task. The design spec contained all architectural decisions; the plan's job was to decompose them into executable steps with correct, consistent code. The core challenge was not design (already done) but **cross-task type consistency**: ensuring that function signatures, import lists, and return types in Task 1's `replay.py` matched exactly what Tasks 2-4 expect, and that the diagnostic types match what `check_health()` returns.

The mechanism/policy split from the design spec maps directly to the task decomposition: Task 1 creates the shared mechanism (`replay_jsonl` + diagnostics), and Tasks 2-4 each provide per-store policy (callbacks). This decomposition means Tasks 2-4 are independent of each other and could theoretically execute in parallel (though the plan sequences them for incremental verification).

### Project State

- **Branch:** `main` at `ac097928`
- **Design spec:** Merged at `82b47191` / `851560f6` — ready for implementation
- **`codex.consult` open question:** Closed at `851560f6` — no longer blocking
- **Implementation plan:** Written and saved — ready for execution
- **Tests:** 359/359 passing (unchanged)
- **No implementation branches exist yet** — both `fix/persistence-replay-hardening` and `chore/type-narrowing` will be created at execution time

### Plan Structure

| Task | Branch | Scope | New tests |
|------|--------|-------|-----------|
| 1 | `fix/persistence-replay-hardening` | `server/replay.py` — shared helper + types | 22 |
| 2 | same | `server/turn_store.py` — migrate + check_health | 5 |
| 3 | same | `server/lineage_store.py` — migrate + check_health | 6 |
| 4 | same | `server/journal.py` — migrate + check_health | 6 |
| 5 | `chore/type-narrowing` | `server/profiles.py` — literal types + validation | 10 |
| 6 | same | `server/models.py` — concrete session type | 1 |
| **Total** | | | **50** |

## Learnings

### Open questions from design should be resolved in the plan, not during implementation

**Mechanism:** The prior handoff listed 4 open questions (API names, validation placement, test strictness, type alias location). These affect multiple tasks — if resolved inconsistently during implementation (e.g., Task 2 names the callback `_validate_turn` but Task 1's tests expect `_turn_callback`), the code won't compose.

**Evidence:** Resolving Q2 (validation placement) during plan writing revealed the lineage closure factory pattern, which affects how `_replay()` and `check_health()` are structured. If this had been decided during Task 3 implementation, Tasks 2 and 4 might have used a different pattern (e.g., class methods), creating inconsistency.

**Implication:** Plans derived from design specs should explicitly enumerate and resolve all open questions before defining tasks. The plan is the point of closure for design-level questions; implementation should not reopen them.

**Watch for:** Design specs that defer "implementation detail" questions — these may be cross-task consistency questions in disguise.

### Journal's `OperationJournalEntry(**record)` silently breaks on extra fields

**Mechanism:** The current `_terminal_phases()` at `journal.py:144` constructs entries via `OperationJournalEntry(**record)`. If a newer writer adds an extra field to the JSONL record, `**record` passes it as a keyword argument, and the frozen dataclass raises `TypeError: __init__() got an unexpected keyword argument 'future_field'`. This crashes the entire replay for a forward-compatibility issue.

**Evidence:** Verified by reading `journal.py:144` and the `OperationJournalEntry` dataclass at `models.py:226-244`. The dataclass has no `**kwargs` handling. Unlike lineage (which filters through `__dataclass_fields__`), journal has no extra-field protection.

**Implication:** The plan's journal callback constructs with explicit named arguments (10 specific fields), ignoring any extra keys. This matches lineage's existing pattern and the design spec's extra-field policy.

**Watch for:** Any future code that uses `SomeDataclass(**record)` for JSONL deserialization. If the record can have extra fields (from version skew or forward-compatibility), the construction will crash.

### `from __future__ import annotations` enables TYPE_CHECKING guard without runtime cost

**Mechanism:** When `from __future__ import annotations` is present, all annotations are strings at runtime — never evaluated. This means `TYPE_CHECKING` guard imports (`from .runtime import AppServerRuntimeSession`) add zero runtime import overhead. The annotation `session: AppServerRuntimeSession` is the string `"AppServerRuntimeSession"` at runtime, resolved only by type checkers.

**Evidence:** `models.py` already has `from __future__ import annotations` at line 3. The F6 change adds `TYPE_CHECKING` guard for the circular import (`models → runtime → models`). No runtime code in the package introspects `AdvisoryRuntimeState` annotations (verified by searching for `get_type_hints`, `__annotations__`, `__dataclass_fields__` usage).

**Implication:** The `TYPE_CHECKING` guard is safe for `AdvisoryRuntimeState` but would break if any code calls `typing.get_type_hints(AdvisoryRuntimeState)` at runtime — the import wouldn't be available.

**Watch for:** Future code that introspects annotations at runtime (serialization frameworks, validators). The test in the plan uses `__dataclass_fields__["session"].type` (string comparison) rather than `get_type_hints` (which would fail).

## Next Steps

### 1. Execute the implementation plan (subagent-driven recommended)

**Dependencies:** Plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` is complete and verified.

**What to read first:** The plan itself — it contains all code, test cases, and commands. No other files need to be read before starting.

**Approach suggestion:** Invoke `superpowers:subagent-driven-development` skill. The plan has 6 tasks; each is independently verifiable. Tasks 1-4 execute on `fix/persistence-replay-hardening` branch. After merging branch 1, tasks 5-6 execute on `chore/type-narrowing` branch.

**Acceptance criteria:** All 359 existing tests pass. 50 new tests added and passing. `check_health()` available on all three stores. Malformed records diagnosed (not crashed). Type narrowing catches typo postures/efforts.

### 2. (After Branch 1 merged) AC6 analytics emission

**Dependencies:** Branch 1 merged. Ticket T-20260330-03. Delivery roadmap at `delivery.md:255` (packet 2b).

**What to read first:** `delivery.md` for packet 2b acceptance criteria. `contracts.md` §Analytics for the event schema.

**Approach suggestion:** This is actual roadmap work (not debt/cleanup). Scope and plan separately.

### 3. (Future) Wire diagnostics consumer

**Dependencies:** Branch 1 merged. Spec amendment to `contracts.md` §RuntimeHealth.

**What to read first:** Design spec's Deferred Work section. Store ownership architecture (control plane owns journal; dialogue owns lineage/turn stores).

**Approach suggestion:** Decide ownership model for cross-store health checks before implementation. Either push health checks through the dialogue layer, or promote store ownership to the control plane.

## In Progress

Clean stopping point. Implementation plan written and saved to `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`. No implementation branches exist. No code changes in flight. Working tree clean.

## Open Questions

### AC6 analytics emission

Deferred from T-03. Actual roadmap work in packet 2b (`delivery.md:255`). Not addressed this session — user chose persistence hardening first. Ticket T-20260330-03 tracks it.

### Diagnostics consumer architecture

The design spec defers wiring `check_health()` to a production surface. The store ownership split (control plane owns journal; dialogue owns lineage/turn stores) means no single component can call all three without refactoring.

### Deferred review suggestions (S1-S16)

16 suggestions from the T-03 second review agents were not independently validated. Unchanged from prior handoff. May contain false positives.

## Risks

### Plan code may need adjustment during implementation

The plan contains 1490 lines of code written from reading, not execution. Subtle issues (import ordering, test fixture paths, edge cases in the deferred classification algorithm) may surface. The TDD structure mitigates this — each step verifies before proceeding, and failures are caught early.

### `check_health()` has no production consumer

Same risk from prior session. Replay diagnostics are structured and testable but operationally invisible. Mid-file corruption in production would be survivable (no crash) but undetected.

### Branch merge ordering matters

Branch 2 (`chore/type-narrowing`) must be created after Branch 1 is merged. If created in parallel, the type narrowing tests may interact with the replay migration in unexpected ways. The plan enforces sequential execution but a subagent must respect this ordering.

## References

| What | Where |
|------|-------|
| Implementation plan | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| `codex.consult` decision | `docs/superpowers/specs/codex-collaboration/decisions.md:115-141` |
| Delivery roadmap | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| Lineage store spec | `docs/superpowers/specs/codex-collaboration/contracts.md` §Lineage Store |
| Recovery/journal spec | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` |
| Prior handoff | `docs/handoffs/archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| PR #90 (T-03) | jpsweeney97/claude-code-tool-dev#90 — squash-merged at `43fa3ba5` |

## Gotchas

### Lineage closure pattern is non-obvious

`_make_lineage_callback(handles)` returns a closure that mutates the `handles` dict as a side effect and always returns `None`. Both `_replay()` and `check_health()` create fresh dicts and pass them to the factory. The `results` tuple from `replay_jsonl` is empty — the real output is the closure-captured dict. This is documented in the plan and design spec but is a pattern that would surprise a reader unfamiliar with the codebase.

### Journal's `_terminal_phases` has a different session_id pattern

TurnStore and LineageStore receive `session_id` at construction time (one store instance per session). Journal receives `session_id` as a parameter to `_terminal_phases()`, `list_unresolved()`, `check_idempotency()`, etc. This means `check_health()` on journal also takes `session_id` as a keyword argument: `check_health(*, session_id: str)` — different from the other two stores' `check_health()` which takes no arguments.

### `type(True) is int` is False — by design

Python's `bool` subclasses `int`: `isinstance(True, int)` returns `True`. The plan uses `type(x) is int` throughout to reject booleans. JSON `true`/`false` would pass `isinstance(x, int)` checks, so `type(x) is int` is the correct guard. This is a design spec requirement, not an implementation detail.

### Extra fields in journal records currently crash replay

The existing `OperationJournalEntry(**record)` at `journal.py:144` raises `TypeError` on extra fields. After migration, the callback constructs with 10 explicit named arguments, ignoring extras. This is a behavior change — previously forward-incompatible records crashed the journal; now they're handled gracefully.

### `TYPE_CHECKING` guard is the first in models.py

F6 introduces the first `TYPE_CHECKING` import guard in `models.py`. Future imports that need to break circular dependencies should follow the same pattern. Note that `get_type_hints(AdvisoryRuntimeState)` would fail at runtime because the import isn't available — this is acceptable because no runtime code introspects the annotations.

## User Preferences

**Structured problem framing:** User provided "Relevant information" (5 numbered facts) and "Open questions" (4 numbered items) as context before plan writing. This pre-framing style was also observed in the prior session (hypothesis-driven evaluation, 5 specific gates for native review comparison). User prefers to structure the problem space before asking Claude to work in it.

**Session boundaries at phase transitions:** User ran `/save` immediately after the plan was presented with execution options, without choosing an option. This indicates preference for clean phase separation: design → plan → execution happen in separate sessions. The handoff chain supports this workflow.

**Precision in open questions:** User's 4 open questions named exact concepts: "exact helper/module API names in `server/replay.py`", "whether store-specific validation stays inline or gets small local helpers." These are not vague — they identify the specific design surface that needs resolution. Future sessions should expect the same precision in problem statements.
