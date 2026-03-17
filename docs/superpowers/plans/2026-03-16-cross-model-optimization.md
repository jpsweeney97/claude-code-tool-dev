# Cross-Model Plugin Optimization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden event log permissions, consolidate event schema into a single source of truth, and fix credential regex drift — the three highest-value optimization findings from the cross-model plugin review.

**Architecture:** Three independent phases targeting the `packages/plugins/cross-model/scripts/` layer. Phase 1 migrates `codex_guard.py` to delegate to `event_log.py` (fixing file permissions and atomicity). Phase 2 extracts shared event schema definitions into a new `event_schema.py` module. Phase 3 fixes concrete regex divergences between egress and ingress credential scanners and adds a parity test corpus.

**Tech Stack:** Python 3.11+, pytest, no new dependencies.

**Source:** Codex dialogue `019cf9da-dd7e-75d2-b66e-a5b370802f20` (5 turns, collaborative, all resolved).

---

## File Structure

### Phase 1 files

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `scripts/codex_guard.py` | Remove local `_LOG_PATH`, `_ts()`, `_append_log()`; import from `event_log` |
| Modify | `scripts/event_log.py` | Update D26 docstring to reflect completed migration |
| Modify | `scripts/credential_scan.py` | Cache tier-filtered tuples at module level |
| Modify | `tests/test_codex_guard.py` | Verify existing tests pass (mock targets unchanged) |
| Create | `tests/test_codex_guard_log_delegation.py` | New tests verifying delegation to `event_log` |

### Phase 2 files

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `scripts/event_schema.py` | Single source of truth for event field definitions, enum sets, schema version resolution |
| Modify | `scripts/emit_analytics.py` | Import schema from `event_schema.py`, remove local definitions |
| Modify | `scripts/read_events.py` | Import required-fields from `event_schema.py`, remove local definitions |
| Modify | `scripts/compute_stats.py` | Import from `event_schema.py` instead of accessing `read_events._REQUIRED_FIELDS` |
| Create | `tests/test_event_schema.py` | Tests for the new schema module |
| Modify | `tests/test_emit_analytics.py` | Verify existing tests pass after extraction |
| Modify | `tests/test_read_events.py` | Verify existing tests pass after extraction |

### Phase 3 files

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `context-injection/context_injection/redact.py` | Split `_AUTH_HEADER_RE` into bearer + basic; document JWT difference |
| Create | `testdata/credential_parity_corpus.json` | Neutral test corpus for cross-scanner parity |
| Create | `tests/test_credential_parity.py` | Parity tests: both scanners run against shared corpus |

All paths relative to `packages/plugins/cross-model/`.

---

## Task 1: Migrate codex_guard.py to event_log.py (Phase 1a)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/codex_guard.py:29-95`
- Modify: `packages/plugins/cross-model/scripts/event_log.py:1-11`
- Create: `packages/plugins/cross-model/tests/test_codex_guard_log_delegation.py`
- Test: `packages/plugins/cross-model/tests/test_codex_guard.py`

- [ ] **Step 1: Run existing codex_guard tests to establish baseline**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py -v`
Expected: All 10 tests PASS

- [ ] **Step 2: Write test verifying codex_guard delegates to event_log.append_log**

Create `tests/test_codex_guard_log_delegation.py`:

```python
"""Tests verifying codex_guard delegates logging to event_log module."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from scripts.codex_guard import handle_post


def test_append_log_calls_event_log():
    """_append_log wrapper delegates to event_log.append_log."""
    with patch("scripts.codex_guard._raw_append_log") as mock_raw:
        from scripts.codex_guard import _append_log

        _append_log({"event": "test"})
        mock_raw.assert_called_once_with({"event": "test"})


def test_ts_is_event_log_ts():
    """After migration, _ts should be event_log.ts."""
    import scripts.codex_guard as mod
    import scripts.event_log as ev

    assert mod._ts is ev.ts


def test_log_path_not_defined_locally():
    """codex_guard should not define its own _LOG_PATH."""
    import scripts.codex_guard as mod

    source = open(mod.__file__).read()
    assert "_LOG_PATH = " not in source
```

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard_log_delegation.py -v`
Expected: FAIL — `_raw_append_log` not found, `_ts is not ev.ts`

- [ ] **Step 3: Migrate codex_guard.py — replace local implementations with imports**

In `scripts/codex_guard.py`, make these changes:

1. Remove the local `_LOG_PATH`, `_ts()`, and `_append_log()` definitions (lines 50, 84-94)
2. Remove `import datetime` and `from pathlib import Path` (no longer needed)
3. Add import-alias delegation after the existing `credential_scan` import block:

```python
try:
    from event_log import ts as _ts, append_log as _raw_append_log
except ModuleNotFoundError:
    from scripts.event_log import ts as _ts, append_log as _raw_append_log


def _append_log(entry: dict) -> None:
    """Delegate to event_log.append_log, discarding the bool return.

    codex_guard callers expect None return (fire-and-forget).
    event_log.append_log returns bool. This wrapper preserves the
    original call-site semantics while gaining POSIX atomicity and
    0o600 permission enforcement.
    """
    _raw_append_log(entry)
```

The wrapper is needed because existing call sites (lines 171, 198, 214, 250) call `_append_log()` without checking a return value, and the mock target `scripts.codex_guard._append_log` must remain stable for tests.

- [ ] **Step 4: Run all codex_guard tests to verify no regressions**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py tests/test_codex_guard_log_delegation.py -v`
Expected: All tests PASS (12 total — 10 existing + 2 new identity checks pass, 1 source check passes)

- [ ] **Step 5: Update event_log.py D26 docstring**

Replace lines 1-11 of `scripts/event_log.py`:

```python
"""Shared event log helpers for cross-model plugin analytics.

Used by all analytics-emitting cross-model scripts, including codex_guard.py
(migrated from local implementations — see commit history for D26 context).

Exports:
    LOG_PATH: Path to ~/.claude/.codex-events.jsonl
    ts() -> str: ISO 8601 UTC with Z suffix (second precision)
    append_log(entry) -> bool: Atomic append, returns success
    session_id() -> str | None: From CLAUDE_SESSION_ID, nullable
"""
```

- [ ] **Step 6: Run full plugin test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v`
Expected: All 163+ tests PASS

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/codex_guard.py packages/plugins/cross-model/scripts/event_log.py packages/plugins/cross-model/tests/test_codex_guard_log_delegation.py
git commit -m "fix: migrate codex_guard.py to event_log.py for POSIX atomic writes and 0o600 permissions

Replaces local _LOG_PATH, _ts(), _append_log() in codex_guard.py with
import-alias delegation to event_log module. Fixes file permission gap
where codex_guard could create the event log with default umask instead
of 0o600. Reverses D26 decision — the microsecond timestamp precision
difference did not justify maintaining a separate, less secure append
implementation.

Thin wrapper preserves _append_log(entry) -> None call-site semantics
and test mock target stability."
```

---

## Task 2: Cache credential tier tuples (Phase 1b)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/credential_scan.py:46-51`
- Test: `packages/plugins/cross-model/tests/test_credential_scan.py`

- [ ] **Step 1: Run existing credential_scan tests to establish baseline**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_scan.py -v`
Expected: All tests PASS

- [ ] **Step 2: Write test verifying tier tuples are cached at module level**

Add to `tests/test_credential_scan.py`:

```python
class TestTierCaching:
    """Tier-filtered tuples are precomputed at module level."""

    def test_strict_families_is_tuple(self) -> None:
        from scripts.credential_scan import _STRICT_FAMILIES
        assert isinstance(_STRICT_FAMILIES, tuple)
        assert len(_STRICT_FAMILIES) > 0

    def test_contextual_families_is_tuple(self) -> None:
        from scripts.credential_scan import _CONTEXTUAL_FAMILIES
        assert isinstance(_CONTEXTUAL_FAMILIES, tuple)
        assert len(_CONTEXTUAL_FAMILIES) > 0

    def test_broad_families_is_tuple(self) -> None:
        from scripts.credential_scan import _BROAD_FAMILIES
        assert isinstance(_BROAD_FAMILIES, tuple)
        assert len(_BROAD_FAMILIES) > 0

    def test_all_tiers_covered(self) -> None:
        from scripts.credential_scan import (
            _STRICT_FAMILIES,
            _CONTEXTUAL_FAMILIES,
            _BROAD_FAMILIES,
        )
        from scripts.secret_taxonomy import FAMILIES

        egress_families = [f for f in FAMILIES if f.egress_enabled]
        cached_count = len(_STRICT_FAMILIES) + len(_CONTEXTUAL_FAMILIES) + len(_BROAD_FAMILIES)
        assert cached_count == len(egress_families)
```

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_scan.py::TestTierCaching -v`
Expected: FAIL — `_STRICT_FAMILIES` not defined

- [ ] **Step 3: Cache tier tuples at module level in credential_scan.py**

In `scripts/credential_scan.py`, make two changes:

**Change 1:** Add 3 cache lines immediately after the existing `_families_for_tier` function (after line 51):

```python
# Precomputed tier buckets — FAMILIES is immutable (frozen dataclasses in a tuple).
_STRICT_FAMILIES: tuple = _families_for_tier("strict")
_CONTEXTUAL_FAMILIES: tuple = _families_for_tier("contextual")
_BROAD_FAMILIES: tuple = _families_for_tier("broad")
```

**Change 2:** In `scan_text()`, replace the 3 `_families_for_tier()` calls with cached tuples:

```python
# Line 60: _families_for_tier("strict")  →  _STRICT_FAMILIES
# Line 69: _families_for_tier("contextual")  →  _CONTEXTUAL_FAMILIES
# Line 81: _families_for_tier("broad")  →  _BROAD_FAMILIES
```

Keep `_families_for_tier` function as-is — it's still used to compute the cached tuples at module load time. Do not rewrite `scan_text` — only change the 3 iterator references.

- [ ] **Step 4: Run all credential_scan and codex_guard tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_scan.py tests/test_codex_guard.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/credential_scan.py packages/plugins/cross-model/tests/test_credential_scan.py
git commit -m "perf: cache tier-filtered credential family tuples at module level

Precompute _STRICT_FAMILIES, _CONTEXTUAL_FAMILIES, _BROAD_FAMILIES at
import time instead of rebuilding from FAMILIES on every scan_text()
call. FAMILIES is immutable (frozen dataclasses in a tuple), so this
is safe. Eliminates 3 tuple constructions per scan invocation."
```

---

## Task 3: Create event_schema.py (Phase 2a)

**Files:**
- Create: `packages/plugins/cross-model/scripts/event_schema.py`
- Create: `packages/plugins/cross-model/tests/test_event_schema.py`

- [ ] **Step 1: Write failing tests for event_schema module**

Create `tests/test_event_schema.py`:

```python
"""Tests for event_schema — single source of truth for event field definitions."""

from __future__ import annotations


class TestRequiredFieldsByEvent:
    """REQUIRED_FIELDS_BY_EVENT contains all structured event types."""

    def test_has_dialogue_outcome(self) -> None:
        from scripts.event_schema import REQUIRED_FIELDS_BY_EVENT
        assert "dialogue_outcome" in REQUIRED_FIELDS_BY_EVENT

    def test_has_consultation_outcome(self) -> None:
        from scripts.event_schema import REQUIRED_FIELDS_BY_EVENT
        assert "consultation_outcome" in REQUIRED_FIELDS_BY_EVENT

    def test_has_delegation_outcome(self) -> None:
        from scripts.event_schema import REQUIRED_FIELDS_BY_EVENT
        assert "delegation_outcome" in REQUIRED_FIELDS_BY_EVENT

    def test_values_are_frozensets(self) -> None:
        from scripts.event_schema import REQUIRED_FIELDS_BY_EVENT
        for event_type, fields in REQUIRED_FIELDS_BY_EVENT.items():
            assert isinstance(fields, frozenset), f"{event_type} should be frozenset"


class TestStructuredEventTypes:
    """STRUCTURED_EVENT_TYPES derived from REQUIRED_FIELDS_BY_EVENT."""

    def test_derived_from_required_fields(self) -> None:
        from scripts.event_schema import (
            REQUIRED_FIELDS_BY_EVENT,
            STRUCTURED_EVENT_TYPES,
        )
        assert STRUCTURED_EVENT_TYPES == frozenset(REQUIRED_FIELDS_BY_EVENT)

    def test_is_frozenset(self) -> None:
        from scripts.event_schema import STRUCTURED_EVENT_TYPES
        assert isinstance(STRUCTURED_EVENT_TYPES, frozenset)


class TestRequiredFieldsFunction:
    """required_fields() accessor with default."""

    def test_known_type_returns_fields(self) -> None:
        from scripts.event_schema import required_fields
        fields = required_fields("dialogue_outcome")
        assert "posture" in fields
        assert "turn_count" in fields

    def test_unknown_type_returns_empty(self) -> None:
        from scripts.event_schema import required_fields
        assert required_fields("unknown_type") == frozenset()


class TestResolveSchemaVersion:
    """resolve_schema_version() determines version from feature flags."""

    def test_base_version(self) -> None:
        from scripts.event_schema import resolve_schema_version, SCHEMA_VERSION
        assert resolve_schema_version({}) == SCHEMA_VERSION

    def test_provenance_bumps_to_020(self) -> None:
        from scripts.event_schema import resolve_schema_version
        assert resolve_schema_version({"provenance_unknown_count": 0}) == "0.2.0"

    def test_planning_bumps_to_030(self) -> None:
        from scripts.event_schema import resolve_schema_version
        assert resolve_schema_version({"question_shaped": True}) == "0.3.0"

    def test_planning_takes_precedence(self) -> None:
        from scripts.event_schema import resolve_schema_version
        event = {"question_shaped": False, "provenance_unknown_count": 0}
        assert resolve_schema_version(event) == "0.3.0"


class TestEnumSets:
    """Enum value sets are exported."""

    def test_valid_postures(self) -> None:
        from scripts.event_schema import VALID_POSTURES
        assert "collaborative" in VALID_POSTURES
        assert "adversarial" in VALID_POSTURES

    def test_valid_modes(self) -> None:
        from scripts.event_schema import VALID_MODES
        assert "server_assisted" in VALID_MODES
        assert "manual_legacy" in VALID_MODES

    def test_valid_termination_reasons(self) -> None:
        from scripts.event_schema import VALID_TERMINATION_REASONS
        assert "convergence" in VALID_TERMINATION_REASONS

    def test_valid_convergence_codes(self) -> None:
        from scripts.event_schema import VALID_CONVERGENCE_CODES
        assert "all_resolved" in VALID_CONVERGENCE_CODES

    def test_count_fields(self) -> None:
        from scripts.event_schema import COUNT_FIELDS
        assert "turn_count" in COUNT_FIELDS
        assert "scout_count" in COUNT_FIELDS
```

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_event_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.event_schema'`

- [ ] **Step 2: Create event_schema.py**

Create `scripts/event_schema.py`:

```python
"""Single source of truth for cross-model event field definitions.

All event-producing scripts (emit_analytics.py, codex_delegate.py) and
event-consuming scripts (read_events.py, compute_stats.py) import field
definitions from this module.

This module owns:
- Required field sets per event type
- Valid enum values for constrained fields
- Schema version resolution logic
- Count field definitions

This module does NOT own:
- Log I/O (see event_log.py)
- Event construction or validation logic (stays in each producer/consumer)
- Validation depth (read_events validates presence only; emit_analytics
  validates enums and cross-field invariants)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

SCHEMA_VERSION: str = "0.1.0"
"""Base schema version. Feature-flag fields bump this automatically."""


def _is_non_negative_int(value: object) -> bool:
    """Check value is a non-negative int, excluding bool."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def resolve_schema_version(event: dict) -> str:
    """Determine schema version from feature-flag fields.

    Precedence: planning (0.3.0) > provenance (0.2.0) > base (0.1.0).
    """
    if event.get("question_shaped") is not None:
        return "0.3.0"
    if _is_non_negative_int(event.get("provenance_unknown_count")):
        return "0.2.0"
    return SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Required fields per event type
# ---------------------------------------------------------------------------

REQUIRED_FIELDS_BY_EVENT: dict[str, frozenset[str]] = {
    "dialogue_outcome": frozenset({
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "converged",
        "convergence_reason_code",
        "termination_reason",
        "resolved_count",
        "unresolved_count",
        "emerged_count",
        "seed_confidence",
        "mode",
    }),
    "consultation_outcome": frozenset({
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "termination_reason",
        "mode",
    }),
    "delegation_outcome": frozenset({
        "schema_version",
        "event",
        "ts",
        "consultation_id",
        "session_id",
        "thread_id",
        "dispatched",
        "sandbox",
        "full_auto",
        "credential_blocked",
        "dirty_tree_blocked",
        "readable_secret_file_blocked",
        "commands_run_count",
        "exit_code",
        "termination_reason",
        "model",
        "reasoning_effort",
    }),
}

STRUCTURED_EVENT_TYPES: frozenset[str] = frozenset(REQUIRED_FIELDS_BY_EVENT)
"""Event types that have required-field schemas. Derived from REQUIRED_FIELDS_BY_EVENT."""

KNOWN_UNSTRUCTURED_TYPES: frozenset[str] = frozenset({
    "block", "shadow", "consultation",
})
"""Event types that are valid but have no required-field schema."""


def required_fields(event_type: str) -> frozenset[str]:
    """Return required fields for an event type, or empty frozenset if unknown."""
    return REQUIRED_FIELDS_BY_EVENT.get(event_type, frozenset())


# ---------------------------------------------------------------------------
# Enum value sets
# ---------------------------------------------------------------------------

VALID_POSTURES: frozenset[str] = frozenset({
    "adversarial", "collaborative", "exploratory", "evaluative", "comparative",
})

VALID_SEED_CONFIDENCE: frozenset[str] = frozenset({"normal", "low"})

VALID_SHAPE_CONFIDENCE: frozenset[str] = frozenset({"high", "medium", "low"})

VALID_CONVERGENCE_CODES: frozenset[str] = frozenset({
    "all_resolved", "natural_convergence", "budget_exhausted", "error", "scope_breach",
})

VALID_MODES: frozenset[str] = frozenset({"server_assisted", "manual_legacy"})

VALID_MODE_SOURCES: frozenset[str] = frozenset({"epilogue", "fallback"})

VALID_LOW_SEED_CONFIDENCE_REASONS: frozenset[str] = frozenset({
    "thin_citations", "few_files", "zero_output", "provenance_violations",
})

VALID_TERMINATION_REASONS: frozenset[str] = frozenset({
    "convergence", "budget", "error", "scope_breach", "complete",
})

# ---------------------------------------------------------------------------
# Count fields (non-negative int validation)
# ---------------------------------------------------------------------------

COUNT_FIELDS: frozenset[str] = frozenset({
    "turn_count",
    "turn_budget",
    "resolved_count",
    "unresolved_count",
    "emerged_count",
    "assumption_count",
    "gatherer_a_lines",
    "gatherer_b_lines",
    "citations_total",
    "unique_files_total",
    "gatherer_a_unique_paths",
    "gatherer_b_unique_paths",
    "shared_citation_paths",
    "counter_count",
    "confirm_count",
    "open_count",
    "claim_count",
    "scout_count",
    "scope_root_count",
    "provenance_unknown_count",
    "assumptions_generated_count",
    "ambiguity_count",
})
```

- [ ] **Step 3: Run event_schema tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_event_schema.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/cross-model/scripts/event_schema.py packages/plugins/cross-model/tests/test_event_schema.py
git commit -m "feat: add event_schema.py as single source of truth for event field definitions

Extracts REQUIRED_FIELDS_BY_EVENT, STRUCTURED_EVENT_TYPES, enum value
sets (VALID_POSTURES, VALID_MODES, etc.), COUNT_FIELDS, and
resolve_schema_version() into a shared module.

STRUCTURED_EVENT_TYPES derived as frozenset(REQUIRED_FIELDS_BY_EVENT)
to prevent second source of truth."
```

---

## Task 4: Migrate consumers to event_schema.py (Phase 2b)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:40-114`
- Modify: `packages/plugins/cross-model/scripts/read_events.py:25-81`
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py:386-388`
- Test: `packages/plugins/cross-model/tests/test_emit_analytics.py`
- Test: `packages/plugins/cross-model/tests/test_read_events.py`
- Test: `packages/plugins/cross-model/tests/test_compute_stats.py`

- [ ] **Step 1: Run all consumer tests to establish baseline**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py tests/test_read_events.py tests/test_compute_stats.py -v`
Expected: All tests PASS

- [ ] **Step 2: Migrate emit_analytics.py — replace local definitions with imports**

In `scripts/emit_analytics.py`:

1. Add import block after the `event_log` import (around line 38):

```python
try:
    from event_schema import (
        SCHEMA_VERSION as _SCHEMA_VERSION,
        resolve_schema_version as _resolve_schema_version,
        VALID_POSTURES as _VALID_POSTURES,
        VALID_SEED_CONFIDENCE as _VALID_SEED_CONFIDENCE,
        VALID_SHAPE_CONFIDENCE as _VALID_SHAPE_CONFIDENCE,
        VALID_CONVERGENCE_CODES as _VALID_CONVERGENCE_CODES,
        VALID_MODES as _VALID_MODES,
        VALID_MODE_SOURCES as _VALID_MODE_SOURCES,
        VALID_LOW_SEED_CONFIDENCE_REASONS as _VALID_LOW_SEED_CONFIDENCE_REASONS,
        VALID_TERMINATION_REASONS as _VALID_TERMINATION_REASONS,
        COUNT_FIELDS as _COUNT_FIELDS,
        REQUIRED_FIELDS_BY_EVENT,
    )
    _DIALOGUE_REQUIRED = REQUIRED_FIELDS_BY_EVENT["dialogue_outcome"]
    _CONSULTATION_REQUIRED = REQUIRED_FIELDS_BY_EVENT["consultation_outcome"]
except ModuleNotFoundError:
    from scripts.event_schema import (
        SCHEMA_VERSION as _SCHEMA_VERSION,
        resolve_schema_version as _resolve_schema_version,
        VALID_POSTURES as _VALID_POSTURES,
        VALID_SEED_CONFIDENCE as _VALID_SEED_CONFIDENCE,
        VALID_SHAPE_CONFIDENCE as _VALID_SHAPE_CONFIDENCE,
        VALID_CONVERGENCE_CODES as _VALID_CONVERGENCE_CODES,
        VALID_MODES as _VALID_MODES,
        VALID_MODE_SOURCES as _VALID_MODE_SOURCES,
        VALID_LOW_SEED_CONFIDENCE_REASONS as _VALID_LOW_SEED_CONFIDENCE_REASONS,
        VALID_TERMINATION_REASONS as _VALID_TERMINATION_REASONS,
        COUNT_FIELDS as _COUNT_FIELDS,
        REQUIRED_FIELDS_BY_EVENT,
    )
    _DIALOGUE_REQUIRED = REQUIRED_FIELDS_BY_EVENT["dialogue_outcome"]
    _CONSULTATION_REQUIRED = REQUIRED_FIELDS_BY_EVENT["consultation_outcome"]
```

2. Remove these local definitions (lines 44-114):
   - `_SCHEMA_VERSION` (replaced by import)
   - `_VALID_POSTURES`, `_VALID_SEED_CONFIDENCE`, `_VALID_SHAPE_CONFIDENCE`, `_VALID_CONVERGENCE_CODES`, `_VALID_MODES`, `_VALID_MODE_SOURCES`, `_VALID_LOW_SEED_CONFIDENCE_REASONS`, `_VALID_TERMINATION_REASONS` (replaced by imports)
   - `_COUNT_FIELDS`, `_DIALOGUE_REQUIRED`, `_CONSULTATION_REQUIRED` (replaced by imports)
   - `_resolve_schema_version` function (replaced by import)

   **Keep `_is_non_negative_int` as a local function** — it's used by `validate()` (line 692) for count field validation, independently of schema resolution. Do not remove it.

- [ ] **Step 3: Run emit_analytics tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py -v`
Expected: All tests PASS

- [ ] **Step 4: Migrate read_events.py — replace local definitions with imports**

In `scripts/read_events.py`:

1. Add import block after the existing imports:

```python
try:
    from event_schema import (
        REQUIRED_FIELDS_BY_EVENT,
        STRUCTURED_EVENT_TYPES,
        KNOWN_UNSTRUCTURED_TYPES,
    )
    # Convert frozensets to sets for backwards compatibility with validate_event()
    _REQUIRED_FIELDS: dict[str, set[str]] = {
        k: set(v) for k, v in REQUIRED_FIELDS_BY_EVENT.items()
    }
except ModuleNotFoundError:
    from scripts.event_schema import (
        REQUIRED_FIELDS_BY_EVENT,
        STRUCTURED_EVENT_TYPES,
        KNOWN_UNSTRUCTURED_TYPES,
    )
    _REQUIRED_FIELDS: dict[str, set[str]] = {
        k: set(v) for k, v in REQUIRED_FIELDS_BY_EVENT.items()
    }
```

2. Remove the local `_REQUIRED_FIELDS` dict definition (lines 29-77) and `_KNOWN_UNSTRUCTURED` set (line 80).

3. Update `validate_event()` to use the imported `KNOWN_UNSTRUCTURED_TYPES`:

```python
def validate_event(event: dict) -> list[str]:
    event_type = classify(event)
    if event_type == "unknown":
        return ["unknown event type: missing 'event' field"]
    required = _REQUIRED_FIELDS.get(event_type)
    if required is None:
        if event_type in KNOWN_UNSTRUCTURED_TYPES:
            return []
        return [f"unknown event type: '{event_type}'"]
    missing = required - set(event.keys())
    if missing:
        return [f"missing required field: {f}" for f in sorted(missing)]
    return []
```

**Critical guardrail:** `validate_event()` must remain **presence-only** — it checks whether required fields exist, nothing more. Do NOT add enum validation, type checks, or cross-field invariants here. Those checks belong in `emit_analytics.validate()` only. Adding them here would cause `compute_stats` to reject historical events that were written under older validation rules.

- [ ] **Step 5: Run read_events tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_read_events.py -v`
Expected: All tests PASS

- [ ] **Step 6: Migrate compute_stats.py — remove private-API dependency**

In `scripts/compute_stats.py`, replace line 388:

```python
# Before:
if isinstance(et, str) and et in read_events._REQUIRED_FIELDS:

# After:
try:
    from event_schema import STRUCTURED_EVENT_TYPES
except ModuleNotFoundError:
    from scripts.event_schema import STRUCTURED_EVENT_TYPES
# ... (at top of file, near other imports)

# Then at line 388:
if isinstance(et, str) and et in STRUCTURED_EVENT_TYPES:
```

Move the import to the top-level import block in `compute_stats.py`.

- [ ] **Step 7: Run compute_stats tests and full suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_compute_stats.py -v`
Expected: All tests PASS

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v`
Expected: All 163+ tests PASS

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py packages/plugins/cross-model/scripts/read_events.py packages/plugins/cross-model/scripts/compute_stats.py
git commit -m "refactor: migrate event consumers to shared event_schema.py

emit_analytics.py, read_events.py, and compute_stats.py now import
field definitions, enum sets, and schema version logic from
event_schema.py instead of maintaining independent copies.

Removes compute_stats.py's private-API dependency on
read_events._REQUIRED_FIELDS (replaced with
event_schema.STRUCTURED_EVENT_TYPES).

IMPORTANT: read_events.validate_event() remains presence-only.
Enum and cross-field validation stays in emit_analytics.validate()."
```

---

## Task 5: Fix auth-header regex and add parity tests (Phase 3)

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/context_injection/redact.py:85-86`
- Create: `packages/plugins/cross-model/testdata/credential_parity_corpus.json`
- Create: `packages/plugins/cross-model/tests/test_credential_parity.py`
- Test: `packages/plugins/cross-model/context-injection/tests/test_redact.py`

- [ ] **Step 1: Run existing redact tests to establish baseline**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_redact.py -v`
Expected: All tests PASS

- [ ] **Step 2: Write parity test corpus**

Create `testdata/credential_parity_corpus.json`. This is a neutral data file — both the egress scanner (`credential_scan.scan_text`) and the ingress scanner (`redact.redact_known_secrets`) run against it. Divergences are intentional and documented.

```json
{
  "_comment": "Cross-scanner credential parity corpus. Tests that both egress and ingress scanners detect the same credential patterns. Documented divergences are intentional.",
  "cases": [
    {
      "id": "jwt_standard",
      "input": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Both detect. Ingress lacks \\b boundary — intentionally broader for redaction."
    },
    {
      "id": "aws_access_key",
      "input": "AKIAIOSFODNN7EXAMPLE",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Both detect via prefix pattern."
    },
    {
      "id": "github_pat",
      "input": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Egress contextual tier (placeholder bypass); ingress always redacts."
    },
    {
      "id": "pem_private_key",
      "input": "-----BEGIN RSA PRIVATE KEY-----",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "PEM regex MUST be identical across scanners."
    },
    {
      "id": "bearer_token",
      "input": "Authorization: Bearer abcdefghij1234567890xyz",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Both detect bearer auth."
    },
    {
      "id": "basic_auth",
      "input": "Authorization: Basic dXNlcjpwYXNz",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Both detect basic auth."
    },
    {
      "id": "basic_word_false_positive",
      "input": "This is a basic setup guide for authentication.",
      "egress_action": "allow",
      "ingress_redacts": false,
      "note": "After auth-header split, ingress should NOT redact 'basic setup'. If ingress_redacts is true, the auth regex is too broad."
    },
    {
      "id": "credential_assignment",
      "input": "password = mysecretvalue123",
      "egress_action": "shadow",
      "ingress_redacts": true,
      "note": "Egress shadows (broad tier, no block); ingress redacts."
    },
    {
      "id": "url_userinfo",
      "input": "postgres://admin:supersecret@db.example.com/mydb",
      "egress_action": "block",
      "ingress_redacts": true,
      "note": "Both detect URL userinfo credentials."
    },
    {
      "id": "clean_text",
      "input": "Fix the flaky test in auth_test.py",
      "egress_action": "allow",
      "ingress_redacts": false,
      "note": "No credentials — both scanners should pass clean."
    }
  ]
}
```

- [ ] **Step 3: Write parity tests**

**Prerequisite:** The `context-injection` package must be importable from the plugin test environment. This is already the case via the uv workspace defined in the repo root `pyproject.toml`, which links all packages. Verify with: `cd packages/plugins/cross-model && python -c "from context_injection.redact import redact_known_secrets; print('OK')"`

Create `tests/test_credential_parity.py`:

```python
"""Parity tests: egress and ingress credential scanners vs shared corpus.

Both scanners run against testdata/credential_parity_corpus.json.
Divergences are documented in the corpus — tests verify documented
expectations match actual behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.credential_scan import scan_text

# Import ingress scanner from context-injection package
from context_injection.redact import redact_known_secrets


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    corpus_path = Path(__file__).resolve().parent.parent / "testdata" / "credential_parity_corpus.json"
    data = json.loads(corpus_path.read_text())
    return data["cases"]


class TestEgressCorpus:
    """Egress scanner (credential_scan.scan_text) matches corpus expectations."""

    def test_all_cases(self, corpus: list[dict]) -> None:
        for case in corpus:
            result = scan_text(case["input"])
            expected = case["egress_action"]
            actual = result.action
            assert actual == expected, (
                f"[{case['id']}] egress expected {expected!r}, got {actual!r}. "
                f"Note: {case.get('note', '')}"
            )


class TestIngressCorpus:
    """Ingress scanner (redact.redact_known_secrets) matches corpus expectations."""

    def test_all_cases(self, corpus: list[dict]) -> None:
        for case in corpus:
            _, count = redact_known_secrets(case["input"])
            expected_redacts = case["ingress_redacts"]
            actual_redacts = count > 0
            assert actual_redacts == expected_redacts, (
                f"[{case['id']}] ingress expected redacts={expected_redacts!r}, "
                f"got count={count}. Note: {case.get('note', '')}"
            )


class TestPemParity:
    """PEM regex must be identical across scanners."""

    def test_pem_regex_identical(self) -> None:
        from scripts.secret_taxonomy import FAMILIES
        from context_injection.redact import _PEM_PRIVATE_KEY_RE

        pem_family = next(f for f in FAMILIES if f.name == "pem_private_key")
        assert pem_family.pattern.pattern == _PEM_PRIVATE_KEY_RE.pattern, (
            f"PEM regex divergence:\n"
            f"  egress:  {pem_family.pattern.pattern!r}\n"
            f"  ingress: {_PEM_PRIVATE_KEY_RE.pattern!r}"
        )
```

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_parity.py -v`
Expected: FAIL on `basic_word_false_positive` — ingress currently redacts "basic setup" due to the combined `_AUTH_HEADER_RE`

- [ ] **Step 4: Fix _AUTH_HEADER_RE in redact.py — split bearer and basic**

In `context-injection/context_injection/redact.py`, replace the combined `_AUTH_HEADER_RE` (line 85-86):

```python
# Before:
_AUTH_HEADER_RE = re.compile(
    r"(?i)((?:bearer|basic)\s+)[A-Za-z0-9\-._~+/]+=*"
)

# After:
_BEARER_AUTH_RE = re.compile(
    r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]{20,}=*"
)
_BASIC_AUTH_RE = re.compile(
    r"(?i)((?:authorization\s*:\s*)?basic\s+)[A-Za-z0-9+/]{8,}=*"
)
```

Then update `redact_known_secrets()` to use both patterns:

```python
    # Apply in order: most specific first
    text = _JWT_RE.sub(_replace_simple, text)
    text = _BEARER_AUTH_RE.sub(_replace_auth, text)
    text = _BASIC_AUTH_RE.sub(_replace_auth, text)
    text = _API_KEY_PREFIX_RE.sub(_replace_simple, text)
    text = _URL_USERINFO_RE.sub(_replace_url, text)
    text = _CREDENTIAL_RE.sub(_replace_credential, text)
```

The key changes:
- Bearer requires 20+ chars after the keyword (real tokens are long)
- Basic requires `authorization:` prefix OR base64-looking content (8+ chars with base64 alphabet only)
- "basic setup" no longer matches because "setup" contains non-base64 chars and is too short

- [ ] **Step 5: Add JWT documentation comment in redact.py**

Add a comment above `_JWT_RE` in `redact.py`:

```python
# JWT pattern intentionally lacks \b word boundaries (unlike secret_taxonomy.py).
# Ingress over-matching is acceptable for redaction — false positives are
# harmless (text is already being redacted). The egress scanner uses \b
# for precision because false positives there block Codex calls.
_JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]{5,}\.eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+"
)
```

- [ ] **Step 6: Run redact tests and parity tests**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_redact.py -v`
Expected: All tests PASS (some may need updating if they tested the old combined regex)

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_parity.py -v`
Expected: All tests PASS (including `basic_word_false_positive`)

- [ ] **Step 7: Run full test suites**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest -v`
Expected: All 991 tests PASS

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v`
Expected: All plugin tests PASS

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/cross-model/context-injection/context_injection/redact.py packages/plugins/cross-model/testdata/credential_parity_corpus.json packages/plugins/cross-model/tests/test_credential_parity.py
git commit -m "fix: split auth-header regex to prevent false positives, add credential parity tests

Splits _AUTH_HEADER_RE into _BEARER_AUTH_RE and _BASIC_AUTH_RE with
tighter matching:
- Bearer requires 20+ char token (real tokens are long)
- Basic requires authorization: prefix or base64 content (8+ chars)
- 'basic setup' no longer false-positives

Adds testdata/credential_parity_corpus.json — neutral test corpus that
both egress (credential_scan) and ingress (redact) scanners run against.
Documents intentional divergences (JWT boundary, auth-header precision).

Verifies PEM regex is identical across both scanners."
```

---

## Verification Checklist

After all tasks complete:

- [ ] `cd packages/plugins/cross-model && uv run pytest tests/ -v` — all plugin tests pass
- [ ] `cd packages/plugins/cross-model/context-injection && uv run pytest -v` — all 991 context-injection tests pass
- [ ] `cd packages/plugins/cross-model && uv run ruff check scripts/ tests/` — no lint errors
- [ ] `cd packages/plugins/cross-model/context-injection && uv run ruff check context_injection/ tests/` — no lint errors
- [ ] `grep -r "_LOG_PATH\s*=" scripts/codex_guard.py` returns empty (local definition removed)
- [ ] `grep -r "read_events._REQUIRED_FIELDS" scripts/compute_stats.py` returns empty (private-API removed)
- [ ] Event log created by codex_guard.py has 0o600 permissions (verified by test_event_log.py::test_creates_log_with_private_permissions)
