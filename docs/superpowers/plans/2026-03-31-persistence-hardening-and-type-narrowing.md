# Persistence Hardening and Type Narrowing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden JSONL replay across three stores (turn, lineage, journal) with shared corruption classification, and narrow stringly-typed fields in profiles and models.

**Architecture:** A shared `replay_jsonl()` helper in `server/replay.py` owns line decoding and corruption classification (mechanism). Per-store callbacks own schema validation and record application (policy). Each store migrates incrementally — helper first, then turn_store (simplest), lineage_store (adds unknown-op handling), journal (adds dataclass construction validation). A second branch narrows `ResolvedProfile` fields to `Literal` types and replaces `session: Any` with the concrete type.

**Tech Stack:** Python 3.11+, pytest, dataclasses, frozen dataclasses, `json`, `typing.Literal`

**Design spec:** `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md`

---

## File Map

### Branch 1: `fix/persistence-replay-hardening`

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` (repo root) | Update spec with review findings before coding begins |
| Create | `server/replay.py` | Shared replay helper, exception types, diagnostic model |
| Create | `tests/test_replay.py` | Helper unit tests (22 cases) |
| Modify | `server/turn_store.py` | Replace `_replay()` with `replay_jsonl` + callback, add `check_health()` |
| Modify | `tests/test_turn_store.py` | Add I2 regression + schema violation + `check_health` tests |
| Modify | `server/lineage_store.py` | Replace `_replay()` + `_apply_record()` with `replay_jsonl` + closure callback, add `check_health()` |
| Modify | `tests/test_lineage_store.py` | Add I4 regression + schema violation + `check_health` tests |
| Modify | `server/journal.py` | Replace `_terminal_phases()` with `replay_jsonl` + callback, add `check_health()` |
| Modify | `tests/test_journal.py` | Add schema violation + conditional requirement + `check_health` tests |
| Modify | `tests/test_recovery_coordinator.py` | Add controller-level corruption tests (journal fallback, turn metadata overwrite) |

### Branch 2: `chore/type-narrowing`

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `server/profiles.py` | Literal type aliases, narrow `ResolvedProfile` + `resolve_profile()`, runtime validation |
| Modify | `tests/test_profiles.py` | Add type-narrowing rejection tests + YAML ingress tests |
| Modify | `server/models.py` | Replace `session: Any` with `AppServerRuntimeSession` |
| Modify | `tests/test_models_r2.py` | Add session type annotation test |

---

## Branch 1: `fix/persistence-replay-hardening`

Create the branch before starting:

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git checkout main && git checkout -b fix/persistence-replay-hardening
```

### Task 0: Update Design Spec

**Files:**
- Modify: `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md`

**Context:** Three contract changes emerged from the plan review that must be canonical in the design spec before implementation starts. Without this, the implementation drifts from the spec and the spec becomes stale documentation rather than the authority.

- [ ] **Step 1: Update the design spec**

Apply these changes to `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md`:

1. **§Store Health API (line ~169):** Add after the `check_health` signature:

> **Outlier: Journal.** `OperationJournal.check_health()` takes `*, session_id: str` because the journal is session-per-call (not session-at-construction like TurnStore and LineageStore). This is the intentional exception to the uniform surface. The diagnostics-consumer branch must handle this signature difference.

2. **§Journal callback (line ~153):** Add after the existing field type table:

> **Per-operation+phase conditional requirements.** Recovery (`dialogue.py:446-592`) relies on specific fields existing for certain operation+phase combinations. The callback enforces these beyond the flat type checks above:
>
> | operation | phase | Additional required fields |
> |-----------|-------|--------------------------|
> | `thread_creation` | `dispatched` | `codex_thread_id` (str) |
> | `turn_dispatch` | any | `codex_thread_id` (str) |
> | `turn_dispatch` | `dispatched`/`completed` | `turn_sequence` (int) |
>
> **Compatibility decision: `runtime_id` on `turn_dispatch`.** NOT required. Missing `runtime_id` suppresses audit event emission (`dialogue.py:592,689`) but does not crash recovery. This is a data-quality gap, not a correctness failure. Requiring it would reject records from older writers.

3. **§LineageStore callback (line ~141):** Add after the line about extra fields being silently ignored:

> **Literal validation.** `status` is validated against `HandleStatus` and `capability_class` against `CapabilityProfile`. Unknown literal values are `SchemaViolation`. This is intentionally tighter than the extra-field policy: unknown enum values would cause semantic misinterpretation by the controller (wrong filtering, wrong lifecycle transitions). New enum values require coordinated rollout: update the `Literal` type first, then start writing the new value.
>
> **WARNING — Rollout-order constraint.** This validation is tighter than the extra-field policy. If a newer version of the plugin writes a new `status` or `capability_class` value to JSONL, and an older version of the plugin reads it, the older version will classify the record as `SchemaViolation` and silently skip the handle. The coordinated rollout requirement means: update `HandleStatus`/`CapabilityProfile` `Literal` types in all readers before any writer emits new values.

- [ ] **Step 2: Commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md
git commit -m "docs: update design spec with review findings

Add journal check_health outlier note, per-operation+phase conditional
requirements table, runtime_id tolerance compatibility decision, and
lineage literal validation contract with rollout-order warning.
These changes make the spec match the implementation plan before
coding begins."
```

---

All file paths below are relative to `packages/plugins/codex-collaboration/`.

### Task 1: Shared Replay Module

**Files:**
- Create: `server/replay.py`
- Create: `tests/test_replay.py`

- [ ] **Step 1: Write the test file**

Create `tests/test_replay.py`:

```python
"""Tests for shared JSONL replay helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from server.replay import (
    ReplayDiagnostic,
    ReplayDiagnostics,
    SchemaViolation,
    UnknownOperation,
    replay_jsonl,
)


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    """Pass-through callback that returns the record as-is."""
    return record


def _write_lines(path: Path, lines: list[str]) -> None:
    """Write raw lines to a file (one per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


class TestBasicReplay:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "missing.jsonl"
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert diags.diagnostics == ()

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert diags.diagnostics == ()

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "blank.jsonl"
        _write_lines(path, ["", "  ", "\t", json.dumps({"a": 1}), ""])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert results[0] == {"a": 1}
        assert diags.diagnostics == ()

    def test_single_valid_record(self, tmp_path: Path) -> None:
        path = tmp_path / "single.jsonl"
        _write_lines(path, [json.dumps({"key": "value"})])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert results[0] == {"key": "value"}

    def test_multiple_valid_records_preserve_order(self, tmp_path: Path) -> None:
        path = tmp_path / "multi.jsonl"
        _write_lines(path, [json.dumps({"n": i}) for i in range(3)])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 3
        assert [r["n"] for r in results] == [0, 1, 2]

    def test_callback_returning_none_not_collected(self, tmp_path: Path) -> None:
        path = tmp_path / "none.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), json.dumps({"a": 2})])
        results, _ = replay_jsonl(path, lambda r: None)
        assert results == ()


class TestCorruptionClassification:
    def test_trailing_truncation_after_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "trailing.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), "not valid json"])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "trailing_truncation"
        assert diags.diagnostics[0].line_number == 2

    def test_mid_file_corruption_before_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "midfile.jsonl"
        _write_lines(path, ["corrupt", json.dumps({"a": 1})])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "mid_file_corruption"
        assert diags.diagnostics[0].line_number == 1

    def test_mixed_trailing_and_mid_file(self, tmp_path: Path) -> None:
        path = tmp_path / "mixed.jsonl"
        _write_lines(path, [
            "corrupt1",            # line 1 — mid-file
            json.dumps({"a": 1}),  # line 2 — valid
            "corrupt2",            # line 3 — trailing
        ])
        results, diags = replay_jsonl(path, _identity)
        assert len(results) == 1
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[3] == "trailing_truncation"

    def test_all_corrupt_file_is_mid_file_corruption(self, tmp_path: Path) -> None:
        """No valid JSON prefix → all failures are mid-file corruption."""
        path = tmp_path / "allcorrupt.jsonl"
        _write_lines(path, ["bad1", "bad2", "bad3"])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 3
        assert all(d.label == "mid_file_corruption" for d in diags.diagnostics)

    def test_non_dict_json_counts_as_valid_json_for_classification(self, tmp_path: Path) -> None:
        """Non-dict JSON (array) is a schema violation but counts as
        successful JSON parse for trailing-truncation classification."""
        path = tmp_path / "nondict.jsonl"
        _write_lines(path, [
            "corrupt1",           # line 1 — mid-file (before valid JSON)
            json.dumps([1, 2]),   # line 2 — valid JSON, schema violation
            "corrupt2",           # line 3 — trailing (after valid JSON)
        ])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[2] == "schema_violation"
        assert labels[3] == "trailing_truncation"

    def test_schema_violation_counts_as_valid_json_for_classification(self, tmp_path: Path) -> None:
        """Callback SchemaViolation still counts as successful JSON parse
        for trailing-truncation classification."""
        path = tmp_path / "schemaclass.jsonl"
        _write_lines(path, [
            "corrupt",              # line 1 — mid-file
            json.dumps({"bad": 1}), # line 2 — callback raises SchemaViolation
            "corrupt2",             # line 3 — trailing
        ])

        def rejecting(record: dict[str, Any]) -> dict[str, Any]:
            raise SchemaViolation("always rejects")

        _, diags = replay_jsonl(path, rejecting)
        labels = {d.line_number: d.label for d in diags.diagnostics}
        assert labels[1] == "mid_file_corruption"
        assert labels[2] == "schema_violation"
        assert labels[3] == "trailing_truncation"


class TestExceptionHandling:
    def test_schema_violation_from_callback(self, tmp_path: Path) -> None:
        path = tmp_path / "schema.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])

        def bad_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise SchemaViolation("test violation")

        results, diags = replay_jsonl(path, bad_callback)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "test violation" in diags.diagnostics[0].detail

    def test_unknown_operation_from_callback(self, tmp_path: Path) -> None:
        path = tmp_path / "unknown.jsonl"
        _write_lines(path, [json.dumps({"op": "bogus"})])

        def unknown_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise UnknownOperation(record.get("op"))

        results, diags = replay_jsonl(path, unknown_callback)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "unknown_operation"
        assert "bogus" in diags.diagnostics[0].detail

    def test_programmer_bug_propagates(self, tmp_path: Path) -> None:
        path = tmp_path / "bug.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])

        def buggy_callback(record: dict[str, Any]) -> dict[str, Any]:
            raise ValueError("this is a bug")

        with pytest.raises(ValueError, match="this is a bug"):
            replay_jsonl(path, buggy_callback)

    def test_non_dict_json_array_produces_schema_violation(self, tmp_path: Path) -> None:
        path = tmp_path / "array.jsonl"
        _write_lines(path, [json.dumps([1, 2, 3])])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "list" in diags.diagnostics[0].detail

    def test_non_dict_json_string_produces_schema_violation(self, tmp_path: Path) -> None:
        path = tmp_path / "string.jsonl"
        _write_lines(path, [json.dumps("hello")])
        results, diags = replay_jsonl(path, _identity)
        assert results == ()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "str" in diags.diagnostics[0].detail


class TestDiagnosticsModel:
    def test_diagnostics_sorted_by_line_number(self, tmp_path: Path) -> None:
        path = tmp_path / "sorted.jsonl"
        _write_lines(path, [
            "corrupt",             # line 1 — mid-file corruption
            json.dumps({"a": 1}),  # line 2 — valid
            json.dumps([1]),       # line 3 — schema violation (non-dict)
            "corrupt2",            # line 4 — trailing truncation
        ])
        _, diags = replay_jsonl(path, _identity)
        line_numbers = [d.line_number for d in diags.diagnostics]
        assert line_numbers == [1, 3, 4]

    def test_has_warnings_true_for_mid_file_corruption(self, tmp_path: Path) -> None:
        path = tmp_path / "midwarn.jsonl"
        _write_lines(path, ["corrupt", json.dumps({"a": 1})])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is True

    def test_has_warnings_false_for_trailing_only(self, tmp_path: Path) -> None:
        path = tmp_path / "trail.jsonl"
        _write_lines(path, [json.dumps({"a": 1}), "corrupt"])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is False

    def test_has_warnings_false_for_no_diagnostics(self, tmp_path: Path) -> None:
        path = tmp_path / "clean.jsonl"
        _write_lines(path, [json.dumps({"a": 1})])
        _, diags = replay_jsonl(path, _identity)
        assert diags.has_warnings is False

    def test_unknown_operation_carries_op_attribute(self) -> None:
        exc = UnknownOperation("test_op")
        assert exc.op == "test_op"
        assert "test_op" in str(exc)

    def test_unknown_operation_with_none_op(self) -> None:
        exc = UnknownOperation(None)
        assert exc.op is None
        assert "None" in str(exc)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_replay.py -v`

Expected: All tests fail with `ModuleNotFoundError: No module named 'server.replay'`

- [ ] **Step 3: Create `server/replay.py` with complete implementation**

```python
"""Shared JSONL replay helper with corruption classification.

Single-pass replay with deferred trailing-truncation classification.
Per-store callbacks handle schema validation and record application.
See the persistence hardening design spec for the full contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar

T = TypeVar("T")


class SchemaViolation(Exception):
    """Raised by store callback when a parsed record has wrong/missing fields."""


class UnknownOperation(Exception):
    """Raised by store callback when a parsed record has an unrecognized op."""

    def __init__(self, op: str | None) -> None:
        self.op = op
        super().__init__(f"unknown operation: {op!r}")


@dataclass(frozen=True)
class ReplayDiagnostic:
    """Single diagnosed issue during JSONL replay."""

    line_number: int  # Physical file line number (1-based)
    label: Literal[
        "trailing_truncation",
        "mid_file_corruption",
        "schema_violation",
        "unknown_operation",
    ]
    detail: str


@dataclass(frozen=True)
class ReplayDiagnostics:
    """Collection of diagnostics from a single replay pass."""

    diagnostics: tuple[ReplayDiagnostic, ...]

    @property
    def has_warnings(self) -> bool:
        """True if any non-trailing diagnostics exist."""
        return any(
            d.label != "trailing_truncation" for d in self.diagnostics
        )


def replay_jsonl(
    path: Path,
    apply: Callable[[dict[str, Any]], T | None],
) -> tuple[tuple[T, ...], ReplayDiagnostics]:
    """Replay a JSONL file with corruption classification and structured diagnostics.

    Single-pass with deferred trailing-truncation classification:
    - Lines where json.loads fails are classified after the loop based on
      whether valid JSON appeared after them (mid-file) or not (trailing).
    - Non-dict JSON is a schema_violation emitted before the callback.
    - SchemaViolation and UnknownOperation from the callback are caught and diagnosed.
    - All other callback exceptions propagate as programmer bugs.
    """
    if not path.exists():
        return ((), ReplayDiagnostics(()))

    results: list[T] = []
    immediate_diagnostics: list[ReplayDiagnostic] = []
    pending_parse_failures: list[int] = []
    last_valid_json_line: int = 0

    with path.open(encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                pending_parse_failures.append(line_number)
                continue

            # JSON parsed successfully — record for trailing classification
            last_valid_json_line = line_number

            if type(parsed) is not dict:
                immediate_diagnostics.append(ReplayDiagnostic(
                    line_number=line_number,
                    label="schema_violation",
                    detail=f"expected JSON object, got {type(parsed).__name__}",
                ))
                continue

            try:
                result = apply(parsed)
            except SchemaViolation as exc:
                immediate_diagnostics.append(ReplayDiagnostic(
                    line_number=line_number,
                    label="schema_violation",
                    detail=str(exc),
                ))
                continue
            except UnknownOperation as exc:
                immediate_diagnostics.append(ReplayDiagnostic(
                    line_number=line_number,
                    label="unknown_operation",
                    detail=str(exc),
                ))
                continue

            if result is not None:
                results.append(result)

    # Deferred classification of parse failures
    classified: list[ReplayDiagnostic] = []
    for ln in pending_parse_failures:
        if last_valid_json_line == 0:
            label: Literal["trailing_truncation", "mid_file_corruption"] = "mid_file_corruption"
        elif ln > last_valid_json_line:
            label = "trailing_truncation"
        else:
            label = "mid_file_corruption"
        classified.append(ReplayDiagnostic(
            line_number=ln,
            label=label,
            detail="invalid JSON",
        ))

    all_diagnostics = sorted(
        immediate_diagnostics + classified,
        key=lambda d: d.line_number,
    )
    return (tuple(results), ReplayDiagnostics(tuple(all_diagnostics)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_replay.py -v`

Expected: All 22 tests pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: 359 existing + 22 new = 381 tests pass.

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/replay.py packages/plugins/codex-collaboration/tests/test_replay.py
git commit -m "feat: shared JSONL replay helper with corruption classification

Add server/replay.py with replay_jsonl() function for single-pass replay
with deferred trailing-truncation classification, SchemaViolation and
UnknownOperation exception types for per-store callbacks, and structured
ReplayDiagnostic/ReplayDiagnostics diagnostic model.

Foundation for I2/I3/I4 store migrations from T-03 second review."
```

---

### Task 2: Migrate TurnStore

**Files:**
- Modify: `server/turn_store.py`
- Modify: `tests/test_turn_store.py`

**Context:** TurnStore is the simplest store — 3 fields, no operation types. Fixes I2 (bare `record['collaboration_id']` crashes entire replay on malformed records).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_turn_store.py`. Add `import json` to the existing imports at the top of the file (alongside the existing `import os`). Then add this new test class:

```python
class TestReplayHardening:
    """I2 regression: malformed records must not crash replay."""

    def test_malformed_record_does_not_crash(self, tmp_path: Path) -> None:
        """I2: a record missing required fields must not crash replay."""
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"bad": "record"}) + "\n")
        store2 = TurnStore(tmp_path, "sess-1")
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_wrong_type_does_not_crash(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "collaboration_id": "collab-1",
                "turn_sequence": "not-an-int",
                "context_size": 100,
            }) + "\n")
        store2 = TurnStore(tmp_path, "sess-1")
        # Valid record survives; malformed record skipped
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_bool_as_int_rejected(self, tmp_path: Path) -> None:
        """type(True) is bool, not int — must not pass integer validation."""
        store = TurnStore(tmp_path, "sess-1")
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "collaboration_id": "collab-1",
                "turn_sequence": True,
                "context_size": 4096,
            }) + "\n")
        assert store.get("collab-1", turn_sequence=1) is None

    def test_check_health_returns_diagnostics(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"bad": "record"}) + "\n")
        diags = store.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        diags = store.check_health()
        assert diags.diagnostics == ()
        assert diags.has_warnings is False
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_turn_store.py::TestReplayHardening -v`

Expected: `test_malformed_record_does_not_crash` fails with `KeyError: 'collaboration_id'` (the I2 bug). `test_check_health_returns_diagnostics` fails with `AttributeError: 'TurnStore' object has no attribute 'check_health'`.

- [ ] **Step 3: Migrate `server/turn_store.py`**

Replace the full file content with:

```python
"""Per-turn metadata store: session-partitioned append-only JSONL.

Persists context_size per (collaboration_id, turn_sequence) for dialogue.read
enrichment. Crash-safe: append-only with fsync, incomplete trailing records
discarded on replay.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .replay import ReplayDiagnostics, SchemaViolation, replay_jsonl


def _turn_callback(record: dict[str, Any]) -> tuple[str, int]:
    """Validate and extract turn metadata from a JSONL record."""
    cid = record.get("collaboration_id")
    if not isinstance(cid, str):
        raise SchemaViolation("missing or non-string collaboration_id")
    seq = record.get("turn_sequence")
    if type(seq) is not int:
        raise SchemaViolation("missing or non-int turn_sequence")
    size = record.get("context_size")
    if type(size) is not int:
        raise SchemaViolation("missing or non-int context_size")
    return (f"{cid}:{seq}", size)


class TurnStore:
    """Append-only JSONL store for per-turn context_size."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "turns" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "turn_metadata.jsonl"

    def write(
        self,
        collaboration_id: str,
        *,
        turn_sequence: int,
        context_size: int,
    ) -> None:
        """Persist context_size for a turn. Idempotent — last write wins on replay."""
        record = {
            "collaboration_id": collaboration_id,
            "turn_sequence": turn_sequence,
            "context_size": context_size,
        }
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def get(self, collaboration_id: str, *, turn_sequence: int) -> int | None:
        """Return context_size for a specific turn, or None if not found."""
        all_turns = self._replay()
        return all_turns.get(f"{collaboration_id}:{turn_sequence}")

    def get_all(self, collaboration_id: str) -> dict[int, int]:
        """Return {turn_sequence: context_size} for all turns in a collaboration."""
        all_turns = self._replay()
        prefix = f"{collaboration_id}:"
        return {
            int(key.split(":", 1)[1]): value
            for key, value in all_turns.items()
            if key.startswith(prefix)
        }

    def check_health(self) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        _, diagnostics = replay_jsonl(self._store_path, _turn_callback)
        return diagnostics

    def _replay(self) -> dict[str, int]:
        """Replay JSONL log. Last record per key wins."""
        results, _ = replay_jsonl(self._store_path, _turn_callback)
        return dict(results)
```

- [ ] **Step 4: Run all turn_store tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_turn_store.py -v`

Expected: All existing tests (10) + new tests (5) = 15 pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass (381 + 5 = 386).

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/turn_store.py packages/plugins/codex-collaboration/tests/test_turn_store.py
git commit -m "fix: migrate TurnStore to shared replay helper (I2)

Replace inline _replay() with replay_jsonl() + _turn_callback().
Malformed records are now diagnosed instead of crashing entire replay.
Add check_health() for test/diagnostic support."
```

---

### Task 3: Migrate LineageStore

**Files:**
- Modify: `server/lineage_store.py`
- Modify: `tests/test_lineage_store.py`

**Context:** LineageStore uses a closure-captured accumulator pattern — the callback mutates an external `dict[str, CollaborationHandle]` and returns `None`. Fixes I4 (unknown operation types silently dropped). Also adds schema validation for all known ops.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_lineage_store.py` (the file already has `import json`):

```python
class TestReplayHardening:
    """I4 regression: unknown ops and schema violations must be diagnosed."""

    def test_unknown_op_does_not_crash(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "future_op",
                "collaboration_id": "collab-1",
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        # Unknown op skipped; original handle survives
        assert store2.get("collab-1") is not None

    def test_missing_op_does_not_crash(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"collaboration_id": "collab-1"}) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1") is not None

    def test_create_missing_required_field_skipped(self, tmp_path: Path) -> None:
        """Create op missing a required field is a schema violation."""
        store = LineageStore(tmp_path, "sess-1")
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "create",
                "collaboration_id": "collab-bad",
                # missing capability_class and other required fields
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None

    def test_update_status_wrong_type_skipped(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "update_status",
                "collaboration_id": "collab-1",
                "status": 123,  # wrong type
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        # Status unchanged — bad record skipped
        assert store2.get("collab-1").status == "active"

    def test_check_health_reports_unknown_op(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "future_op",
                "collaboration_id": "collab-1",
            }) + "\n")
        diags = store.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "unknown_operation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        diags = store.check_health()
        assert diags.diagnostics == ()

    def test_create_invalid_status_diagnosed_and_skipped(self, tmp_path: Path) -> None:
        """Unknown status literal is a schema violation — intentionally tighter
        than the extra-field policy. See compatibility decision in callback."""
        store = LineageStore(tmp_path, "sess-1")
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "create",
                "collaboration_id": "collab-bad",
                "capability_class": "advisory",
                "runtime_id": "rt-1",
                "codex_thread_id": "thread-1",
                "claude_session_id": "sess-1",
                "repo_root": "/repo",
                "created_at": "2026-01-01T00:00:00Z",
                "status": "banana",
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "status" in diags.diagnostics[0].detail

    def test_create_invalid_capability_class_diagnosed_and_skipped(
        self, tmp_path: Path
    ) -> None:
        """Unknown capability_class is a schema violation — intentionally tighter
        than the extra-field policy. See compatibility decision in callback."""
        store = LineageStore(tmp_path, "sess-1")
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "create",
                "collaboration_id": "collab-bad",
                "capability_class": "banana",
                "runtime_id": "rt-1",
                "codex_thread_id": "thread-1",
                "claude_session_id": "sess-1",
                "repo_root": "/repo",
                "created_at": "2026-01-01T00:00:00Z",
                "status": "active",
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "capability_class" in diags.diagnostics[0].detail

    def test_update_status_invalid_literal_diagnosed_and_skipped(
        self, tmp_path: Path
    ) -> None:
        """Unknown status literal on update_status is a schema violation."""
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "update_status",
                "collaboration_id": "collab-1",
                "status": "banana",
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").status == "active"
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "status" in diags.diagnostics[0].detail

    def test_update_runtime_wrong_type_runtime_id_skipped(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "update_runtime",
                "collaboration_id": "collab-1",
                "runtime_id": 123,
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").runtime_id == "rt-1"

    def test_update_runtime_wrong_type_codex_thread_id_skipped(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "update_runtime",
                "collaboration_id": "collab-1",
                "runtime_id": "rt-2",
                "codex_thread_id": 123,
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").codex_thread_id == "thread-1"

    def test_create_extra_field_ignored(self, tmp_path: Path) -> None:
        """Forward-compat: extra fields on create are silently ignored.
        Shared policy per design spec §Extra-Field Policy."""
        store = LineageStore(tmp_path, "sess-1")
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "op": "create",
                "collaboration_id": "collab-1",
                "capability_class": "advisory",
                "runtime_id": "rt-1",
                "codex_thread_id": "thread-1",
                "claude_session_id": "sess-1",
                "repo_root": "/repo",
                "created_at": "2026-01-01T00:00:00Z",
                "status": "active",
                "future_field": "some_value",
            }) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        handle = store2.get("collab-1")
        assert handle is not None
        assert handle.collaboration_id == "collab-1"
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_lineage_store.py::TestReplayHardening -v`

Expected: `test_unknown_op_does_not_crash` passes (current code silently drops unknown ops — same end result). `test_missing_op_does_not_crash` passes (current code returns early on missing op). `test_create_missing_required_field_skipped` may fail with `TypeError` (dataclass construction). `test_check_health_reports_unknown_op` fails with `AttributeError`. New literal/type tests fail because current code does no literal validation.

- [ ] **Step 3: Migrate `server/lineage_store.py`**

Replace the full file content with:

```python
"""Lineage store: session-partitioned append-only JSONL handle persistence.

See contracts.md §Lineage Store for the normative contract.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, get_args

from .models import CapabilityProfile, CollaborationHandle, HandleStatus
from .replay import ReplayDiagnostics, SchemaViolation, UnknownOperation, replay_jsonl

# Valid literal values from type aliases
_VALID_STATUSES: frozenset[str] = frozenset(get_args(HandleStatus))
_VALID_CAPABILITIES: frozenset[str] = frozenset(get_args(CapabilityProfile))

# Required string fields for create op (collaboration_id validated earlier)
_CREATE_REQUIRED_STR = (
    "capability_class", "runtime_id", "codex_thread_id",
    "claude_session_id", "repo_root", "created_at", "status",
)
_CREATE_OPTIONAL_STR = (
    "parent_collaboration_id", "fork_reason",
    "resolved_posture", "resolved_effort",
)


def _make_lineage_callback(
    handles: dict[str, CollaborationHandle],
) -> Callable[[dict[str, Any]], None]:
    """Create a replay callback that mutates the captured handles dict."""

    def apply(record: dict[str, Any]) -> None:
        op = record.get("op")
        if not isinstance(op, str):
            raise SchemaViolation("missing or non-string op")
        cid = record.get("collaboration_id")
        if not isinstance(cid, str):
            raise SchemaViolation("missing or non-string collaboration_id")

        if op == "create":
            for name in _CREATE_REQUIRED_STR:
                if not isinstance(record.get(name), str):
                    raise SchemaViolation(f"create op: {name} missing or not a string")
            for name in _CREATE_OPTIONAL_STR:
                val = record.get(name)
                if val is not None and not isinstance(val, str):
                    raise SchemaViolation(f"create op: {name} is not a string")
            rtb = record.get("resolved_turn_budget")
            if rtb is not None and type(rtb) is not int:
                raise SchemaViolation("create op: resolved_turn_budget is not an int")
            # Literal validation: reject unknown status/capability_class values.
            # Compatibility decision: unknown literals are SchemaViolation, not
            # forward-compatible. This is intentionally tighter than the extra-field
            # policy (which silently ignores additive keys). Rationale: status drives
            # controller behavior (filtering, lifecycle transitions) and capability_class
            # determines the execution model. A handle with status="quarantined" or
            # capability_class="delegation" from a newer writer would be semantically
            # misinterpreted by older readers — safer to skip than to create a handle
            # the reader cannot handle correctly. New enum values require coordinated
            # rollout: update the Literal type, then start writing the new value.
            if record["capability_class"] not in _VALID_CAPABILITIES:
                raise SchemaViolation(
                    f"create op: unknown capability_class {record['capability_class']!r}"
                )
            if record["status"] not in _VALID_STATUSES:
                raise SchemaViolation(
                    f"create op: unknown status {record['status']!r}"
                )
            # Build from known fields only (extra fields silently ignored)
            fields = {
                k: record[k]
                for k in CollaborationHandle.__dataclass_fields__
                if k in record
            }
            handles[cid] = CollaborationHandle(**fields)

        elif op == "update_status":
            if not isinstance(record.get("status"), str):
                raise SchemaViolation("update_status op: status missing or not a string")
            # Same literal validation rationale as create op (see comment above)
            if record["status"] not in _VALID_STATUSES:
                raise SchemaViolation(
                    f"update_status op: unknown status {record['status']!r}"
                )
            if cid in handles:
                handles[cid] = _replace_handle(handles[cid], status=record["status"])

        elif op == "update_runtime":
            if not isinstance(record.get("runtime_id"), str):
                raise SchemaViolation("update_runtime op: runtime_id missing or not a string")
            if cid in handles:
                updates: dict[str, Any] = {"runtime_id": record["runtime_id"]}
                if "codex_thread_id" in record:
                    if not isinstance(record["codex_thread_id"], str):
                        raise SchemaViolation(
                            "update_runtime op: codex_thread_id is not a string"
                        )
                    updates["codex_thread_id"] = record["codex_thread_id"]
                handles[cid] = _replace_handle(handles[cid], **updates)

        else:
            raise UnknownOperation(op)

        return None

    return apply


class LineageStore:
    """Persists CollaborationHandle records as append-only JSONL.

    All mutations append a new record. On read, the store replays the log —
    the last record for each collaboration_id wins. Incomplete trailing records
    (from crash mid-write) are discarded on load.
    """

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "lineage" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "handles.jsonl"

    def create(self, handle: CollaborationHandle) -> None:
        """Persist a new handle."""
        self._append({"op": "create", **asdict(handle)})

    def get(self, collaboration_id: str) -> CollaborationHandle | None:
        """Retrieve a handle by collaboration_id, or None if not found."""
        return self._replay().get(collaboration_id)

    def list(
        self,
        *,
        repo_root: str | None = None,
        status: HandleStatus | None = None,
    ) -> list[CollaborationHandle]:
        """Query handles with optional repo_root and status filters."""
        handles = list(self._replay().values())
        if repo_root is not None:
            handles = [h for h in handles if h.repo_root == repo_root]
        if status is not None:
            handles = [h for h in handles if h.status == status]
        return handles

    def update_status(self, collaboration_id: str, status: HandleStatus) -> None:
        """Transition handle lifecycle status."""
        self._append({
            "op": "update_status",
            "collaboration_id": collaboration_id,
            "status": status,
        })

    def update_runtime(
        self,
        collaboration_id: str,
        runtime_id: str,
        codex_thread_id: str | None = None,
    ) -> None:
        """Remap handle to a new runtime (and optionally a new thread identity)."""
        record: dict[str, str] = {
            "op": "update_runtime",
            "collaboration_id": collaboration_id,
            "runtime_id": runtime_id,
        }
        if codex_thread_id is not None:
            record["codex_thread_id"] = codex_thread_id
        self._append(record)

    def cleanup(self) -> None:
        """Remove the session directory. Called on session end."""
        if self._store_dir.exists():
            shutil.rmtree(self._store_dir)

    def check_health(self) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        handles: dict[str, CollaborationHandle] = {}
        _, diagnostics = replay_jsonl(
            self._store_path, _make_lineage_callback(handles)
        )
        return diagnostics

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _replay(self) -> dict[str, CollaborationHandle]:
        """Replay the JSONL log to reconstruct current handle state."""
        handles: dict[str, CollaborationHandle] = {}
        replay_jsonl(self._store_path, _make_lineage_callback(handles))
        return handles


def _replace_handle(handle: CollaborationHandle, **changes: Any) -> CollaborationHandle:
    """Return a new handle with specified fields replaced (frozen dataclass)."""
    return CollaborationHandle(**{**asdict(handle), **changes})
```

- [ ] **Step 4: Run all lineage_store tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_lineage_store.py -v`

Expected: All existing tests (12) + new tests (13) = 25 pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass (386 + 13 = 399).

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/lineage_store.py packages/plugins/codex-collaboration/tests/test_lineage_store.py
git commit -m "fix: migrate LineageStore to shared replay helper (I4)

Replace inline _replay() and _apply_record() with replay_jsonl() + closure
callback factory. Unknown ops now diagnosed via UnknownOperation. Schema
validation added for all known ops (create, update_status, update_runtime).
Add check_health() for test/diagnostic support."
```

---

### Task 4: Migrate Journal

**Files:**
- Modify: `server/journal.py`
- Modify: `tests/test_journal.py`

**Context:** Journal uses `OperationJournalEntry(**record)` for construction, which crashes on extra fields. The callback validates all field types before explicit construction, ignoring extra fields for forward compatibility. Journal's `operation` and `phase` values are validated against known sets (unlike lineage, where enum values are unchecked).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_journal.py`. Add `import json` to the existing imports at the top of the file:

```python
class TestReplayHardening:
    def test_wrong_type_field_does_not_crash(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "bad",
                "operation": "thread_creation",
                "phase": "intent",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                "turn_sequence": "not-an-int",
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1  # only the valid record

    def test_unknown_operation_value_skipped(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "bad",
                "operation": "future_operation",
                "phase": "intent",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1

    def test_bool_as_int_rejected_in_journal(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "turn_dispatch",
                "phase": "intent",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                "turn_sequence": True,
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0  # bad record skipped

    def test_extra_fields_ignored(self, tmp_path: Path) -> None:
        """Forward-compat: extra fields in a record must not crash replay."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "thread_creation",
                "phase": "intent",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                "future_field": "some_value",
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].idempotency_key == "k1"

    def test_check_health_reports_schema_violation(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"idempotency_key": 123}) + "\n")
        diags = journal.check_health(session_id="sess-1")
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        diags = journal.check_health(session_id="sess-1")
        assert diags.diagnostics == ()

    def test_turn_dispatch_without_codex_thread_id_skipped(self, tmp_path: Path) -> None:
        """Per-operation requirement: turn_dispatch needs codex_thread_id for recovery.
        dialogue.py:534-538 raises RuntimeError if codex_thread_id is None."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "turn_dispatch",
                "phase": "dispatched",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                "turn_sequence": 1,
                # no codex_thread_id — would crash recovery
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_thread_creation_dispatched_without_codex_thread_id_skipped(
        self, tmp_path: Path
    ) -> None:
        """Per-operation+phase: thread_creation at dispatched needs codex_thread_id.
        dialogue.py:469-473 raises RuntimeError if codex_thread_id is None."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "thread_creation",
                "phase": "dispatched",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                # no codex_thread_id — would crash recovery
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_thread_creation_intent_without_codex_thread_id_accepted(
        self, tmp_path: Path
    ) -> None:
        """Intent phase does not require codex_thread_id — dispatch hasn't happened."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "thread_creation",
                "phase": "intent",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1

    def test_turn_dispatch_dispatched_without_turn_sequence_skipped(
        self, tmp_path: Path
    ) -> None:
        """turn_dispatch at dispatched/completed requires turn_sequence for
        turn confirmation (dialogue.py:550-551)."""
        journal = OperationJournal(tmp_path / "plugin-data")
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        ops_path.parent.mkdir(parents=True, exist_ok=True)
        with ops_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "k1",
                "operation": "turn_dispatch",
                "phase": "dispatched",
                "collaboration_id": "c1",
                "created_at": "2026-01-01T00:00:00Z",
                "repo_root": "/repo",
                "codex_thread_id": "thread-1",
                # no turn_sequence — can never confirm turn
            }) + "\n")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_journal.py::TestReplayHardening -v`

Expected: `test_extra_fields_ignored` fails with `TypeError: __init__() got an unexpected keyword argument 'future_field'`. `test_check_health_reports_schema_violation` fails with `AttributeError`. Conditional requirement tests fail because current code has no per-operation+phase validation.

- [ ] **Step 3: Migrate `server/journal.py`**

Add imports near the top (after the existing `from pathlib import Path` line):

```python
from typing import Any

from .replay import ReplayDiagnostics, SchemaViolation, replay_jsonl
```

Add these constants and the callback function after the `default_plugin_data_path()` function, before the `OperationJournal` class:

```python
_VALID_OPERATIONS = frozenset(("thread_creation", "turn_dispatch"))
_VALID_PHASES = frozenset(("intent", "dispatched", "completed"))
_JOURNAL_REQUIRED_STR = (
    "idempotency_key", "operation", "phase",
    "collaboration_id", "created_at", "repo_root",
)
_JOURNAL_OPTIONAL_STR = ("codex_thread_id", "runtime_id")
_JOURNAL_OPTIONAL_INT = ("turn_sequence", "context_size")


def _journal_callback(
    record: dict[str, Any],
) -> tuple[str, OperationJournalEntry]:
    """Validate all fields and construct a journal entry."""
    for name in _JOURNAL_REQUIRED_STR:
        if not isinstance(record.get(name), str):
            raise SchemaViolation(f"{name} missing or not a string")
    if record["operation"] not in _VALID_OPERATIONS:
        raise SchemaViolation(f"unknown operation value: {record['operation']!r}")
    if record["phase"] not in _VALID_PHASES:
        raise SchemaViolation(f"unknown phase value: {record['phase']!r}")
    for name in _JOURNAL_OPTIONAL_STR:
        val = record.get(name)
        if val is not None and not isinstance(val, str):
            raise SchemaViolation(f"{name} is not a string")
    for name in _JOURNAL_OPTIONAL_INT:
        val = record.get(name)
        if val is not None and type(val) is not int:
            raise SchemaViolation(f"{name} is not an int")
    # Per-operation+phase conditional requirements.
    # Recovery (dialogue.py:446-592) relies on these fields existing for
    # specific operation+phase combinations. Without enforcement, type-valid
    # but incomplete records survive to recovery and crash with RuntimeError.
    op = record["operation"]
    phase = record["phase"]
    if op == "turn_dispatch":
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                "turn_dispatch requires codex_thread_id (string)"
            )
        if phase in ("dispatched", "completed"):
            ts = record.get("turn_sequence")
            if ts is None or type(ts) is not int:
                raise SchemaViolation(
                    f"turn_dispatch at {phase} requires turn_sequence (int)"
                )
    elif op == "thread_creation" and phase == "dispatched":
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                "thread_creation at dispatched requires codex_thread_id (string)"
            )
    # Compatibility decision: runtime_id on turn_dispatch is NOT required.
    # Missing runtime_id suppresses audit event emission (dialogue.py:592,689)
    # but does not crash recovery. Requiring it would reject records from
    # older writers that may not persist runtime_id on all turn_dispatch
    # entries. This is a data-quality gap, not a correctness failure.
    entry = OperationJournalEntry(
        idempotency_key=record["idempotency_key"],
        operation=record["operation"],
        phase=record["phase"],
        collaboration_id=record["collaboration_id"],
        created_at=record["created_at"],
        repo_root=record["repo_root"],
        codex_thread_id=record.get("codex_thread_id"),
        turn_sequence=record.get("turn_sequence"),
        runtime_id=record.get("runtime_id"),
        context_size=record.get("context_size"),
    )
    return (entry.idempotency_key, entry)
```

Replace the `_terminal_phases` method in the `OperationJournal` class with:

```python
    def _terminal_phases(self, session_id: str) -> dict[str, OperationJournalEntry]:
        """Replay the log and return the last record per idempotency key."""
        path = self._operations_path(session_id)
        results, _ = replay_jsonl(path, _journal_callback)
        return dict(results)
```

Add the `check_health` method to the `OperationJournal` class (after `_terminal_phases`):

```python
    def check_health(self, *, session_id: str) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        path = self._operations_path(session_id)
        _, diagnostics = replay_jsonl(path, _journal_callback)
        return diagnostics
```

- [ ] **Step 4: Run all journal tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_journal.py -v`

Expected: All existing tests (12) + new tests (10) = 22 pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass (399 + 10 = 409).

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/journal.py packages/plugins/codex-collaboration/tests/test_journal.py
git commit -m "fix: migrate Journal to shared replay helper

Replace OperationJournalEntry(**record) construction with explicit field
validation and construction via _journal_callback. Extra fields in records
no longer crash replay (forward-compat). Operation and phase values validated
against known sets. Per-operation+phase conditional requirements enforce
codex_thread_id on turn_dispatch (any phase) and thread_creation dispatched,
turn_sequence on turn_dispatch dispatched/completed. runtime_id on
turn_dispatch is tolerated as None (suppresses audit, does not crash).
Add check_health(session_id=) for test/diagnostic support."
```

- [ ] **Step 7: Write controller-level corruption tests**

These tests verify that malformed records don't break the layer above the stores — the `DialogueController` recovery and read paths. They exercise the full stack wired by the existing `_recovery_stack` helper in `test_recovery_coordinator.py`.

Add `import json` to the imports at the top of `tests/test_recovery_coordinator.py`. Then append to the `TestStartupRecoveryCoordinator` class:

```python
    def test_malformed_journal_terminal_row_falls_back_to_earlier(
        self, tmp_path: Path
    ) -> None:
        """When a completed terminal row is malformed and skipped by replay,
        the earlier valid row becomes the terminal phase. Recovery processes
        the fallback row deterministically."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        cid = start.collaboration_id

        # Valid turn_dispatch intent
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=cid,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        # Inject malformed "completed" terminal row for same idempotency key.
        # turn_sequence is a string → SchemaViolation → row skipped.
        # Last-write-wins falls back to the intent row.
        ops_path = (
            tmp_path / "plugin-data" / "journal" / "operations" / "sess-1.jsonl"
        )
        with ops_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "idempotency_key": "rt-1:thr-start:1",
                "operation": "turn_dispatch",
                "phase": "completed",
                "collaboration_id": cid,
                "created_at": "2026-03-28T00:01:00Z",
                "repo_root": str(tmp_path.resolve()),
                "codex_thread_id": "thr-start",
                "turn_sequence": "not-an-int",
            }) + "\n")

        # Recovery should not crash. The intent row becomes the terminal phase.
        # turn_dispatch intent with zero completed turns → handle marked 'unknown'.
        controller.recover_startup()

        handle = store.get(cid)
        assert handle is not None
        assert handle.status == "unknown"

    def test_malformed_turn_metadata_overwrite_survives_in_read(
        self, tmp_path: Path
    ) -> None:
        """A malformed TurnStore overwrite row is skipped. dialogue.read()
        uses the last valid context_size for that (cid, turn_sequence)."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "",
                    },
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        cid = start.collaboration_id

        # Write valid turn metadata
        turn_store.write(cid, turn_sequence=1, context_size=4096)

        # Inject malformed overwrite for same (cid, turn_sequence).
        # turn_sequence is a string → SchemaViolation → row skipped.
        # TurnStore last-write-wins keeps the valid row (4096).
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "collaboration_id": cid,
                "turn_sequence": "not-an-int",
                "context_size": 9999,
            }) + "\n")

        # dialogue.read() should use the valid metadata (4096), not crash
        result = controller.read(cid)
        assert len(result.turns) == 1
        assert result.turns[0].context_size == 4096
```

- [ ] **Step 8: Run controller-level corruption tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_recovery_coordinator.py -v`

Expected: All existing recovery tests pass. Two new corruption tests pass.

- [ ] **Step 9: Run full suite**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass (409 + 2 = 411).

- [ ] **Step 10: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py
git commit -m "test: controller-level corruption tests for journal and TurnStore

Verify that malformed JSONL records at the store level compose correctly
with the recovery coordinator and dialogue read path. Journal: malformed
terminal row falls back to earlier valid row, recovery processes the
fallback deterministically. TurnStore: malformed overwrite skipped,
dialogue.read uses last valid context_size."
```

---

## Branch 2: `chore/type-narrowing`

Merge Branch 1 first, then create this branch:

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git checkout main
# (merge fix/persistence-replay-hardening into main first)
git checkout -b chore/type-narrowing
```

### Task 5: F4 — Literal Types for ResolvedProfile

**Files:**
- Modify: `server/profiles.py`
- Modify: `tests/test_profiles.py`

**Context:** `ResolvedProfile` fields are `str` — typos like `posture="adversrial"` propagate silently. Define `Literal` type aliases and add runtime validation for YAML-loaded values. Code callers get static type checking; YAML callers get runtime validation.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_profiles.py`:

```python
class TestTypeNarrowing:
    """F4: Literal types catch invalid posture, effort, and turn_budget values."""

    def test_unknown_posture_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(explicit_posture="adversrial")  # typo

    def test_unknown_effort_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="unknown effort"):
            resolve_profile(explicit_effort="turbo")

    def test_zero_turn_budget_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget=0)

    def test_negative_turn_budget_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget=-1)

    def test_string_turn_budget_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget="5")  # type: ignore[arg-type]

    def test_bool_turn_budget_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget=True)  # type: ignore[arg-type]

    def test_valid_postures_accepted(self) -> None:
        for posture in (
            "collaborative", "adversarial", "exploratory", "evaluative", "comparative"
        ):
            resolved = resolve_profile(explicit_posture=posture)
            assert resolved.posture == posture

    def test_valid_efforts_accepted(self) -> None:
        for effort in ("minimal", "low", "medium", "high", "xhigh"):
            resolved = resolve_profile(explicit_effort=effort)
            assert resolved.effort == effort

    def test_positive_turn_budget_accepted(self) -> None:
        resolved = resolve_profile(explicit_turn_budget=1)
        assert resolved.turn_budget == 1

    def test_default_turn_budget_accepted(self) -> None:
        """Default turn_budget=6 must pass the new validation."""
        resolved = resolve_profile()
        assert resolved.turn_budget == 6


class TestYamlIngressValidation:
    """F4 YAML ingress: bad values loaded from YAML must be caught by
    runtime validation in resolve_profile(). Uses a real YAML file via
    _REFERENCES_DIR patch to exercise the full ingress path: file read,
    YAML parsing, key mapping (reasoning_effort → effort), and validation."""

    def _write_profile_yaml(
        self, tmp_path: Path, profile_name: str, fields: dict
    ) -> None:
        """Write a consultation-profiles.yaml with a single profile."""
        import yaml

        tmp_path.mkdir(parents=True, exist_ok=True)
        yaml_path = tmp_path / "consultation-profiles.yaml"
        yaml_path.write_text(
            yaml.dump({"profiles": {profile_name: fields}})
        )

    def _write_local_override_yaml(
        self, tmp_path: Path, profile_name: str, overrides: dict
    ) -> None:
        """Write a consultation-profiles.local.yaml with overrides."""
        import yaml

        local_path = tmp_path / "consultation-profiles.local.yaml"
        local_path.write_text(
            yaml.dump({"profiles": {profile_name: overrides}})
        )

    def test_yaml_bad_posture_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML profile with typo posture is caught at resolution time."""
        self._write_profile_yaml(tmp_path, "bad-profile", {
            "posture": "adversrial",
        })
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(profile_name="bad-profile")

    def test_yaml_bad_effort_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML reasoning_effort field maps to effort — bad value caught.
        Pins the file-key contract: YAML uses reasoning_effort, not effort."""
        self._write_profile_yaml(tmp_path, "bad-profile", {
            "reasoning_effort": "turbo",
        })
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown effort"):
            resolve_profile(profile_name="bad-profile")

    def test_yaml_non_int_turn_budget_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML turn_budget as string is caught by type(x) is int check."""
        self._write_profile_yaml(tmp_path, "bad-profile", {
            "turn_budget": "five",
        })
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(profile_name="bad-profile")

    def test_local_override_bad_posture_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bad posture in local override YAML is caught after merge.
        Exercises the full local-override merge path: base profile is valid,
        local override introduces a bad posture, merged result is rejected."""
        self._write_profile_yaml(tmp_path, "test-profile", {
            "posture": "collaborative",
        })
        self._write_local_override_yaml(tmp_path, "test-profile", {
            "posture": "adversrial",
        })
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(profile_name="test-profile")
```

- [ ] **Step 2: Run new tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_profiles.py::TestTypeNarrowing tests/test_profiles.py::TestYamlIngressValidation -v`

Expected: `test_unknown_posture_rejected` and `test_unknown_effort_rejected` fail (no validation). `test_zero_turn_budget_rejected` fails. `test_string_turn_budget_rejected` fails. The "accepted" tests pass (valid values already work). All YAML ingress tests fail (same reason — no validation yet), including `test_local_override_bad_posture_rejected`.

- [ ] **Step 3: Modify `server/profiles.py`**

Add `Literal` and `get_args` to the typing import:

```python
from typing import Any, Literal, get_args
```

Add type aliases after the `ProfileValidationError` class, before the `ResolvedProfile` dataclass:

```python
Posture = Literal["collaborative", "adversarial", "exploratory", "evaluative", "comparative"]
Effort = Literal["minimal", "low", "medium", "high", "xhigh"]
SandboxPolicy = Literal["read-only"]
ApprovalPolicy = Literal["never"]

_VALID_POSTURES: frozenset[str] = frozenset(get_args(Posture))
_VALID_EFFORTS: frozenset[str] = frozenset(get_args(Effort))
```

Replace the `ResolvedProfile` dataclass with narrowed types:

```python
@dataclass(frozen=True)
class ResolvedProfile:
    """Fully resolved execution controls."""

    posture: Posture
    turn_budget: int
    effort: Effort | None
    sandbox: SandboxPolicy
    approval_policy: ApprovalPolicy
```

Replace the `resolve_profile` function signature with narrowed parameter types:

```python
def resolve_profile(
    *,
    profile_name: str | None = None,
    explicit_posture: Posture | None = None,
    explicit_turn_budget: int | None = None,
    explicit_effort: Effort | None = None,
    explicit_sandbox: SandboxPolicy | None = None,
    explicit_approval_policy: ApprovalPolicy | None = None,
) -> ResolvedProfile:
```

Add validation between the resolution block (after `approval_policy = ...`) and the existing validation gate (`if sandbox != _DEFAULT_SANDBOX`):

```python
    # Type narrowing validation
    if posture not in _VALID_POSTURES:
        raise ProfileValidationError(
            f"Profile resolution failed: unknown posture. "
            f"Got: posture={posture!r:.100}"
        )
    if effort is not None and effort not in _VALID_EFFORTS:
        raise ProfileValidationError(
            f"Profile resolution failed: unknown effort. "
            f"Got: effort={effort!r:.100}"
        )
    if not (type(turn_budget) is int and turn_budget > 0):
        raise ProfileValidationError(
            f"Profile resolution failed: turn_budget must be a positive integer. "
            f"Got: turn_budget={turn_budget!r:.100}"
        )
```

Also export the type aliases so callers can use them. Add to the existing imports block in `tests/test_profiles.py`:

```python
from server.profiles import (
    load_profiles,
    resolve_profile,
    ProfileValidationError,
)
```

(No change needed — tests don't import the type aliases directly.)

- [ ] **Step 4: Run all profile tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_profiles.py -v`

Expected: All existing tests (9) + new tests (14) = 23 pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass.

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/profiles.py packages/plugins/codex-collaboration/tests/test_profiles.py
git commit -m "chore: narrow ResolvedProfile fields to Literal types (F4)

Define Posture, Effort, SandboxPolicy, ApprovalPolicy type aliases.
Narrow ResolvedProfile dataclass and resolve_profile() parameters.
Add runtime validation for posture (5 values), effort (5 values), and
turn_budget (positive int, type(x) is int rejects bools)."
```

---

### Task 6: F6 — Concrete Session Type

**Files:**
- Modify: `server/models.py`
- Modify: `tests/test_models_r2.py`

**Context:** `AdvisoryRuntimeState.session` is typed as `Any`. The concrete type `AppServerRuntimeSession` exists at `runtime.py:12`. Circular import (`models → runtime → models`) resolved via `TYPE_CHECKING` guard. `from __future__ import annotations` is already in `models.py`.

- [ ] **Step 1: Write failing test**

Append to `tests/test_models_r2.py`:

```python
def test_advisory_runtime_state_session_not_any() -> None:
    """F6: session field should reference AppServerRuntimeSession, not Any.

    This is a raw annotation-token assertion, not a resolved-type check.
    from __future__ import annotations makes all annotations strings at
    runtime. We compare string tokens — NOT get_type_hints(), which would
    trigger the circular import that TYPE_CHECKING is designed to avoid.
    """
    field_type = AdvisoryRuntimeState.__dataclass_fields__["session"].type
    assert field_type != "Any", "session field is still typed as Any"
    assert "AppServerRuntimeSession" in field_type
```

Add `AdvisoryRuntimeState` to the existing import:

```python
from server.models import (
    AdvisoryRuntimeState,
    CollaborationHandle,
    ...
)
```

- [ ] **Step 2: Run new test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py::test_advisory_runtime_state_session_not_any -v`

Expected: `AssertionError: session field is still typed as Any`

- [ ] **Step 3: Modify `server/models.py`**

Add the `TYPE_CHECKING` import guard. After the existing `from typing import Any, Literal` line:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime import AppServerRuntimeSession
```

Change the `session` field in `AdvisoryRuntimeState` from:

```python
    session: Any
```

to:

```python
    session: AppServerRuntimeSession
```

- [ ] **Step 4: Run all model tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py -v`

Expected: All existing tests (8) + new test (1) = 9 pass.

- [ ] **Step 5: Run full suite for regressions**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass. The `TYPE_CHECKING` guard prevents circular import at runtime.

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration
uv run ruff check . && uv run ruff format --check .
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/tests/test_models_r2.py
git commit -m "chore: narrow AdvisoryRuntimeState.session to AppServerRuntimeSession (F6)

Replace session: Any with session: AppServerRuntimeSession using
TYPE_CHECKING guard to avoid circular import. from __future__ import
annotations was already present — annotation resolves as string at
runtime, type checkers resolve it normally."
```

---

## Verification Checklist

After both branches are merged:

- [ ] All pre-existing tests pass unchanged
- [ ] `check_health()` available on all three stores
- [ ] Malformed JSONL records diagnosed, not crashed (I2)
- [ ] Mid-file corruption distinguished from trailing truncation (I3)
- [ ] Unknown lineage ops produce `unknown_operation` diagnostic (I4)
- [ ] Bool values rejected for integer fields in all stores
- [ ] Extra fields in journal and lineage records no longer crash replay
- [ ] Unknown `status`/`capability_class` literals rejected on lineage replay
- [ ] Per-operation+phase conditional requirements enforced in journal
- [ ] `runtime_id` tolerance on `turn_dispatch` documented (compatibility decision)
- [ ] Controller-level: malformed journal terminal row falls back to earlier valid row
- [ ] Controller-level: malformed TurnStore overwrite skipped, `dialogue.read()` uses last valid
- [ ] Typo postures/efforts rejected at profile resolution time (F4)
- [ ] YAML ingress path tested via `_REFERENCES_DIR` patch with real YAML, including local override merge path (F4)
- [ ] Non-positive `turn_budget` rejected (F4)
- [ ] `session` field annotation is `AppServerRuntimeSession` (F6)
