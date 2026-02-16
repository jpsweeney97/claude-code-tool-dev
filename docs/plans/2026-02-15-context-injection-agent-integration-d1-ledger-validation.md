# D1: Ledger Validation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D1 of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Define ledger types, validation rules, and computed fields (counters, quality, effective_delta) for the server-owned ledger.
**Execution order position:** 1 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

No prerequisites. D1 is the first delivery and is independent of all others.

## Files in Scope

**Create:**
- `context_injection/base_types.py` — Extracted base types (`ProtocolModel`, `Claim`, `Unresolved`) to break import cycle (DD-1)
- `context_injection/ledger.py` — Ledger types, validation, counter/quality/delta computation
- `tests/test_ledger.py` — D1 validation tests

**Modify:**
- `context_injection/enums.py` — EffectiveDelta, QualityLabel, ValidationTier, new error codes
- `context_injection/types.py` — Remove `ProtocolModel`, `Claim`, `Unresolved` class definitions; re-export from `base_types`; remove unused `BaseModel`/`ConfigDict` pydantic imports
- `tests/test_types.py` — Add `TestBaseTypeReexports` re-export identity test

**Out of scope:** All files not listed above.

## Done Criteria

- All D1 tests pass
- Ledger types validate correctly
- Counter, quality, and effective_delta computation is deterministic and fully tested

## Scope Boundary

This document covers D1 only. After completing all tasks in this delivery, stop. Do not proceed to subsequent deliveries.

---

Mostly additive (one extraction edit to `types.py`). New `base_types.py`, `ledger.py` module + `test_ledger.py`. One modification to `types.py` (extract base types) and `test_types.py` (re-export identity test).

**Estimated new tests:** ~50-70 (the "200-300" estimate in the manifest is for all deliveries combined)

### Task 1: Ledger types and enums

**Files:**
- Modify: `context_injection/enums.py` (add EffectiveDelta, QualityLabel, ValidationTier)
- Create: `context_injection/base_types.py` (ProtocolModel, Claim, Unresolved — extracted from types.py per DD-1)
- Modify: `context_injection/types.py` (remove 3 class defs, add re-exports from base_types, remove unused BaseModel/ConfigDict imports)
- Create: `context_injection/ledger.py` (LedgerEntry, LedgerEntryCounters, ValidationWarning, CumulativeState)
- Create: `tests/test_ledger.py`
- Modify: `tests/test_types.py` (add TestBaseTypeReexports)

**Step 1: Write failing tests for new enums**

Create `tests/test_ledger.py`:

```python
"""Ledger validation types and computation tests."""

import pytest
from pydantic import ValidationError

from context_injection.enums import EffectiveDelta, QualityLabel, ValidationTier


class TestLedgerEnums:
    """D1 enum values match contract."""

    def test_effective_delta_values(self) -> None:
        assert EffectiveDelta.ADVANCING == "advancing"
        assert EffectiveDelta.SHIFTING == "shifting"
        assert EffectiveDelta.STATIC == "static"

    def test_quality_label_values(self) -> None:
        assert QualityLabel.SUBSTANTIVE == "substantive"
        assert QualityLabel.SHALLOW == "shallow"

    def test_validation_tier_values(self) -> None:
        assert ValidationTier.HARD_REJECT == "hard_reject"
        assert ValidationTier.SOFT_WARN == "soft_warn"
        assert ValidationTier.REFERENTIAL_WARN == "referential_warn"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestLedgerEnums -v`
Expected: FAIL — `ImportError: cannot import name 'EffectiveDelta' from 'context_injection.enums'`

**Step 3: Implement new enums**

Add to end of `context_injection/enums.py`:

```python
class EffectiveDelta(StrEnum):
    """Server-computed effective delta for a ledger entry."""

    ADVANCING = "advancing"
    SHIFTING = "shifting"
    STATIC = "static"


class QualityLabel(StrEnum):
    """Server-computed quality label for a ledger entry."""

    SUBSTANTIVE = "substantive"
    SHALLOW = "shallow"


class ValidationTier(StrEnum):
    """Validation warning severity tier."""

    HARD_REJECT = "hard_reject"
    SOFT_WARN = "soft_warn"
    REFERENTIAL_WARN = "referential_warn"
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestLedgerEnums -v`
Expected: PASS (3 tests)

**Step 4a: Write and run re-export identity test**

Add to `tests/test_types.py`:

```python
class TestBaseTypeReexports:
    """Verify types.py re-exports are identity-equal to base_types.py originals."""

    def test_reexport_identity(self) -> None:
        from context_injection.base_types import Claim as BaseClaim
        from context_injection.base_types import ProtocolModel as BaseProtocolModel
        from context_injection.base_types import Unresolved as BaseUnresolved
        from context_injection.types import Claim, ProtocolModel, Unresolved

        assert ProtocolModel is BaseProtocolModel
        assert Claim is BaseClaim
        assert Unresolved is BaseUnresolved
```

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestBaseTypeReexports -v`
Expected: FAIL until `base_types.py` is created and `types.py` is modified (Step 7).

**Step 5: Write failing tests for ledger types**

Add to `tests/test_ledger.py`:

```python
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    ValidationWarning,
)
from context_injection.types import Claim, Unresolved


class TestLedgerTypes:
    """Type construction, field access, and immutability."""

    def test_counters_construction(self) -> None:
        counters = LedgerEntryCounters(
            new_claims=2, revised=1, conceded=0, unresolved_closed=1,
        )
        assert counters.new_claims == 2
        assert counters.revised == 1
        assert counters.conceded == 0
        assert counters.unresolved_closed == 1

    def test_counters_frozen(self) -> None:
        counters = LedgerEntryCounters(
            new_claims=1, revised=0, conceded=0, unresolved_closed=0,
        )
        with pytest.raises(ValidationError):
            counters.new_claims = 5  # type: ignore[misc]

    def test_counters_forbids_extra(self) -> None:
        with pytest.raises(ValidationError):
            LedgerEntryCounters(
                new_claims=1, revised=0, conceded=0, unresolved_closed=0,
                extra_field="nope",  # type: ignore[call-arg]
            )

    def test_ledger_entry_construction(self) -> None:
        counters = LedgerEntryCounters(
            new_claims=1, revised=0, conceded=0, unresolved_closed=0,
        )
        entry = LedgerEntry(
            position="Model claims X is correct",
            claims=[Claim(text="X is correct", status="new", turn=1)],
            delta="new_information",
            tags=["factual"],
            unresolved=[],
            counters=counters,
            quality=QualityLabel.SUBSTANTIVE,
            effective_delta=EffectiveDelta.ADVANCING,
            turn_number=1,
        )
        assert entry.position == "Model claims X is correct"
        assert len(entry.claims) == 1
        assert entry.turn_number == 1
        assert entry.quality == QualityLabel.SUBSTANTIVE
        assert entry.effective_delta == EffectiveDelta.ADVANCING

    def test_ledger_entry_with_unresolved(self) -> None:
        counters = LedgerEntryCounters(
            new_claims=0, revised=0, conceded=0, unresolved_closed=0,
        )
        entry = LedgerEntry(
            position="Exploring question",
            claims=[],
            delta="none",
            tags=[],
            unresolved=[Unresolved(text="Is X true?", turn=1)],
            counters=counters,
            quality=QualityLabel.SHALLOW,
            effective_delta=EffectiveDelta.STATIC,
            turn_number=1,
        )
        assert len(entry.unresolved) == 1
        assert entry.unresolved[0].text == "Is X true?"

    def test_validation_warning_construction(self) -> None:
        warning = ValidationWarning(
            tier=ValidationTier.SOFT_WARN,
            field="delta",
            message="Delta says 'static' but counters show new claims",
            details={"delta": "static", "new_claims": 3},
        )
        assert warning.tier == ValidationTier.SOFT_WARN
        assert warning.field == "delta"
        assert warning.details is not None

    def test_validation_warning_optional_details(self) -> None:
        warning = ValidationWarning(
            tier=ValidationTier.HARD_REJECT,
            field="claims",
            message="Claims list is empty",
        )
        assert warning.details is None

    def test_cumulative_state_construction(self) -> None:
        state = CumulativeState(
            total_claims=5,
            reinforced=2,
            revised=1,
            conceded=0,
            unresolved_open=1,
            unresolved_closed=1,
            turns_completed=3,
            effective_delta_sequence=[
                EffectiveDelta.ADVANCING,
                EffectiveDelta.SHIFTING,
                EffectiveDelta.STATIC,
            ],
        )
        assert state.total_claims == 5
        assert state.turns_completed == 3
        assert len(state.effective_delta_sequence) == 3

    def test_cumulative_state_empty(self) -> None:
        state = CumulativeState(
            total_claims=0, reinforced=0, revised=0, conceded=0,
            unresolved_open=0, unresolved_closed=0, turns_completed=0,
            effective_delta_sequence=[],
        )
        assert state.total_claims == 0
        assert state.effective_delta_sequence == []
```

**Step 6: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestLedgerTypes -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.ledger'`

**Step 7: Extract base types, modify types.py, then implement ledger types**

Create `context_injection/base_types.py` (DD-1: break import cycle between `types.py` and `ledger.py`):

```python
"""Base protocol types extracted from types.py to break import cycle.

Canonical rule: all code imports from `types.py` (which re-exports these).
Only `ledger.py` imports directly from `base_types.py`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProtocolModel(BaseModel):
    """Base model for all protocol types."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Claim(ProtocolModel):
    """A claim from the ledger."""

    text: str
    status: str
    turn: int


class Unresolved(ProtocolModel):
    """An unresolved question from the ledger."""

    text: str
    turn: int
```

Modify `context_injection/types.py`:
- Remove `ProtocolModel`, `Claim`, `Unresolved` class definitions
- Add re-exports from `base_types`: `from context_injection.base_types import Claim, ProtocolModel, Unresolved`
- Remove now-unused `BaseModel` and `ConfigDict` pydantic imports (if no other types in the file use them directly)

Create `context_injection/ledger.py`:

```python
"""Ledger validation types and computation.

Server-side validation of agent-provided ledger entries. Computes derived
fields (counters, quality, effective_delta) and validates structural and
referential constraints.
"""

from __future__ import annotations

from context_injection.enums import EffectiveDelta, QualityLabel, ValidationTier
from context_injection.base_types import Claim, ProtocolModel, Unresolved


class LedgerEntryCounters(ProtocolModel):
    """Claim status counts for a single ledger entry."""

    new_claims: int
    revised: int
    conceded: int
    unresolved_closed: int


class LedgerEntry(ProtocolModel):
    """Validated ledger entry for a single conversation turn."""

    position: str
    claims: list[Claim]
    delta: str
    tags: list[str]
    unresolved: list[Unresolved]
    counters: LedgerEntryCounters
    quality: QualityLabel
    effective_delta: EffectiveDelta
    turn_number: int


class ValidationWarning(ProtocolModel):
    """Validation warning attached to a ledger entry."""

    tier: ValidationTier
    field: str
    message: str
    details: dict[str, Any] | None = None


class CumulativeState(ProtocolModel):
    """Aggregated state across all validated ledger entries."""

    total_claims: int
    reinforced: int
    revised: int
    conceded: int
    unresolved_open: int
    unresolved_closed: int
    turns_completed: int
    effective_delta_sequence: list[EffectiveDelta]
```

**Step 8: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py tests/test_types.py::TestBaseTypeReexports -v`
Expected: PASS (all TestLedgerEnums + TestLedgerTypes + TestBaseTypeReexports tests)

**Step 9: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_ledger.py tests.

**Step 10: Commit**

```bash
git add packages/context-injection/context_injection/enums.py \
       packages/context-injection/context_injection/base_types.py \
       packages/context-injection/context_injection/types.py \
       packages/context-injection/context_injection/ledger.py \
       packages/context-injection/tests/test_types.py \
       packages/context-injection/tests/test_ledger.py
git commit -m "feat(context-injection): add ledger types and enums, extract base_types (D1 Task 1)"
```

### Task 2: Counter, quality, and effective_delta computation

**Files:**
- Modify: `context_injection/ledger.py` (add compute_counters, compute_quality, compute_effective_delta)
- Modify: `tests/test_ledger.py`

Three pure functions. `compute_counters` counts claims by status (reinforced claims are not counted — they don't indicate new substance). `unresolved_closed` is passed in by the caller (D4 pipeline computes it from prior vs current unresolved lists) since D1 has no access to prior state.

**Step 1: Write failing tests for compute_counters**

Add to `tests/test_ledger.py`:

```python
from context_injection.ledger import (
    compute_counters,
    compute_effective_delta,
    compute_quality,
)


class TestComputeCounters:
    """compute_counters: count claims by status."""

    def test_all_new_claims(self) -> None:
        claims = [
            Claim(text="A", status="new", turn=1),
            Claim(text="B", status="new", turn=1),
        ]
        counters = compute_counters(claims)
        assert counters.new_claims == 2
        assert counters.revised == 0
        assert counters.conceded == 0
        assert counters.unresolved_closed == 0

    def test_mixed_statuses(self) -> None:
        claims = [
            Claim(text="A", status="new", turn=1),
            Claim(text="B", status="revised", turn=1),
            Claim(text="C", status="conceded", turn=1),
            Claim(text="D", status="reinforced", turn=1),
        ]
        counters = compute_counters(claims)
        assert counters.new_claims == 1
        assert counters.revised == 1
        assert counters.conceded == 1
        assert counters.unresolved_closed == 0

    def test_empty_claims(self) -> None:
        counters = compute_counters([])
        assert counters.new_claims == 0
        assert counters.revised == 0
        assert counters.conceded == 0
        assert counters.unresolved_closed == 0

    def test_reinforced_not_counted_as_new(self) -> None:
        claims = [
            Claim(text="A", status="reinforced", turn=1),
            Claim(text="B", status="reinforced", turn=1),
        ]
        counters = compute_counters(claims)
        assert counters.new_claims == 0
        assert counters.revised == 0
        assert counters.conceded == 0

    def test_unresolved_closed_passthrough(self) -> None:
        counters = compute_counters([], unresolved_closed=3)
        assert counters.unresolved_closed == 3
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestComputeCounters -v`
Expected: FAIL — `ImportError: cannot import name 'compute_counters' from 'context_injection.ledger'`

**Step 3: Write failing tests for compute_quality and compute_effective_delta**

Add to `tests/test_ledger.py`:

```python
class TestComputeQuality:
    """compute_quality: any non-reinforced activity → substantive."""

    def test_new_claims_substantive(self) -> None:
        counters = LedgerEntryCounters(new_claims=1, revised=0, conceded=0, unresolved_closed=0)
        assert compute_quality(counters) == QualityLabel.SUBSTANTIVE

    def test_revised_substantive(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=1, conceded=0, unresolved_closed=0)
        assert compute_quality(counters) == QualityLabel.SUBSTANTIVE

    def test_conceded_substantive(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=1, unresolved_closed=0)
        assert compute_quality(counters) == QualityLabel.SUBSTANTIVE

    def test_unresolved_closed_substantive(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=0, unresolved_closed=2)
        assert compute_quality(counters) == QualityLabel.SUBSTANTIVE

    def test_all_zero_shallow(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=0, unresolved_closed=0)
        assert compute_quality(counters) == QualityLabel.SHALLOW


class TestComputeEffectiveDelta:
    """compute_effective_delta: advancing > shifting > static."""

    def test_new_claims_advancing(self) -> None:
        counters = LedgerEntryCounters(new_claims=1, revised=0, conceded=0, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.ADVANCING

    def test_revised_shifting(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=1, conceded=0, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.SHIFTING

    def test_conceded_shifting(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=1, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.SHIFTING

    def test_all_zero_static(self) -> None:
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=0, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.STATIC

    def test_new_takes_priority_over_revised(self) -> None:
        """new_claims > 0 → advancing, even if revised also > 0."""
        counters = LedgerEntryCounters(new_claims=1, revised=1, conceded=0, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.ADVANCING

    def test_unresolved_closed_alone_is_static(self) -> None:
        """Unresolved closure doesn't change position — it clarifies."""
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=0, unresolved_closed=2)
        assert compute_effective_delta(counters) == EffectiveDelta.STATIC
```

**Step 4: Implement all three functions**

Add to `context_injection/ledger.py`:

```python
def compute_counters(
    claims: list[Claim], *, unresolved_closed: int = 0,
) -> LedgerEntryCounters:
    """Count claims by status. Reinforced claims are not counted.

    unresolved_closed is passed in by the caller — D1 has no access
    to prior state for comparing unresolved lists.
    """
    return LedgerEntryCounters(
        new_claims=sum(1 for c in claims if c.status == "new"),
        revised=sum(1 for c in claims if c.status == "revised"),
        conceded=sum(1 for c in claims if c.status == "conceded"),
        unresolved_closed=unresolved_closed,
    )


def compute_quality(counters: LedgerEntryCounters) -> QualityLabel:
    """Any non-reinforced activity → substantive."""
    if (
        counters.new_claims > 0
        or counters.revised > 0
        or counters.conceded > 0
        or counters.unresolved_closed > 0
    ):
        return QualityLabel.SUBSTANTIVE
    return QualityLabel.SHALLOW


def compute_effective_delta(counters: LedgerEntryCounters) -> EffectiveDelta:
    """Compute effective delta. Priority: advancing > shifting > static.

    Unresolved closure alone doesn't change position — it clarifies.
    """
    if counters.new_claims > 0:
        return EffectiveDelta.ADVANCING
    if counters.revised > 0 or counters.conceded > 0:
        return EffectiveDelta.SHIFTING
    return EffectiveDelta.STATIC
```

**Step 5: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py -v`
Expected: PASS (all enum, type, and computation tests)

**Step 6: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/ledger.py \
       packages/context-injection/tests/test_ledger.py
git commit -m "feat(context-injection): add counter, quality, and effective_delta computation (D1 Task 2)"
```

### Task 3: Hard and soft validation

**Files:**
- Modify: `context_injection/ledger.py` (add LedgerValidationError, validate_ledger_entry)
- Modify: `tests/test_ledger.py`

Pydantic handles type/field validation at parse time. `validate_ledger_entry` handles semantic validation: structural hard rejects (empty claims, bad turn number) and consistency soft warnings (delta/counter mismatch, empty position). Hard rejects raise `LedgerValidationError`; soft warnings are returned alongside the valid entry.

**Step 1: Write failing tests for hard rejects**

Add to `tests/test_ledger.py`:

```python
from context_injection.ledger import (
    LedgerValidationError,
    validate_ledger_entry,
)


class TestValidateLedgerEntryHardReject:
    """Hard rejects raise LedgerValidationError."""

    def test_empty_claims_rejected(self) -> None:
        with pytest.raises(LedgerValidationError) as exc_info:
            validate_ledger_entry(
                position="Some position",
                claims=[],
                delta="none",
                tags=[],
                unresolved=[],
                turn_number=1,
            )
        assert len(exc_info.value.warnings) == 1
        assert exc_info.value.warnings[0].tier == ValidationTier.HARD_REJECT
        assert exc_info.value.warnings[0].field == "claims"

    def test_turn_number_zero_rejected(self) -> None:
        with pytest.raises(LedgerValidationError) as exc_info:
            validate_ledger_entry(
                position="Position",
                claims=[Claim(text="A", status="new", turn=0)],
                delta="new_information",
                tags=[],
                unresolved=[],
                turn_number=0,
            )
        assert exc_info.value.warnings[0].field == "turn_number"

    def test_negative_turn_number_rejected(self) -> None:
        with pytest.raises(LedgerValidationError):
            validate_ledger_entry(
                position="Position",
                claims=[Claim(text="A", status="new", turn=-1)],
                delta="x",
                tags=[],
                unresolved=[],
                turn_number=-1,
            )

    def test_multiple_hard_rejects_all_reported(self) -> None:
        """All hard rejects collected, not just first one."""
        with pytest.raises(LedgerValidationError) as exc_info:
            validate_ledger_entry(
                position="Position",
                claims=[],
                delta="x",
                tags=[],
                unresolved=[],
                turn_number=0,
            )
        assert len(exc_info.value.warnings) == 2  # empty claims + bad turn_number
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestValidateLedgerEntryHardReject -v`
Expected: FAIL — `ImportError: cannot import name 'LedgerValidationError'`

**Step 3: Write failing tests for soft warnings**

Add to `tests/test_ledger.py`:

```python
class TestValidateLedgerEntrySoftWarn:
    """Soft warnings return alongside valid entry."""

    def test_empty_position_warns(self) -> None:
        entry, warnings = validate_ledger_entry(
            position="",
            claims=[Claim(text="A", status="new", turn=1)],
            delta="new_information",
            tags=[],
            unresolved=[],
            turn_number=1,
        )
        assert entry is not None
        assert len(warnings) == 1
        assert warnings[0].tier == ValidationTier.SOFT_WARN
        assert warnings[0].field == "position"

    def test_delta_counter_mismatch_warns(self) -> None:
        """Agent says 'static' but computed effective_delta is 'advancing'."""
        entry, warnings = validate_ledger_entry(
            position="Has new info",
            claims=[Claim(text="A", status="new", turn=1)],
            delta="static",
            tags=[],
            unresolved=[],
            turn_number=1,
        )
        assert entry is not None
        delta_warnings = [w for w in warnings if w.field == "delta"]
        assert len(delta_warnings) == 1
        assert delta_warnings[0].tier == ValidationTier.SOFT_WARN

    def test_shifting_contradicts_static_effective_delta(self) -> None:
        """Agent says 'shifting' but computed effective_delta is 'static' (CC-8 bug fix)."""
        entry, warnings = validate_ledger_entry(
            position="Only reinforced claims",
            claims=[Claim(text="A", status="reinforced", turn=2)],
            delta="shifting",
            tags=[],
            unresolved=[],
            turn_number=2,
        )
        assert entry is not None
        delta_warnings = [w for w in warnings if w.field == "delta"]
        assert len(delta_warnings) == 1
        assert delta_warnings[0].tier == ValidationTier.SOFT_WARN

    def test_no_warnings_on_valid_entry(self) -> None:
        entry, warnings = validate_ledger_entry(
            position="Model claims X",
            claims=[Claim(text="X", status="new", turn=1)],
            delta="new_information",
            tags=["factual"],
            unresolved=[],
            turn_number=1,
        )
        assert entry is not None
        assert warnings == []

    def test_valid_entry_fields_correct(self) -> None:
        entry, _ = validate_ledger_entry(
            position="Position",
            claims=[Claim(text="A", status="new", turn=1)],
            delta="new_information",
            tags=["tag1"],
            unresolved=[],
            turn_number=1,
        )
        assert entry.position == "Position"
        assert entry.turn_number == 1
        assert entry.counters.new_claims == 1
        assert entry.quality == QualityLabel.SUBSTANTIVE
        assert entry.effective_delta == EffectiveDelta.ADVANCING

    def test_unresolved_closed_passed_through(self) -> None:
        entry, _ = validate_ledger_entry(
            position="Position",
            claims=[Claim(text="A", status="reinforced", turn=2)],
            delta="stable",
            tags=[],
            unresolved=[],
            turn_number=2,
            unresolved_closed=1,
        )
        assert entry.counters.unresolved_closed == 1
        assert entry.quality == QualityLabel.SUBSTANTIVE
```

**Step 4: Implement LedgerValidationError and validate_ledger_entry**

Add to `context_injection/ledger.py`:

```python
class LedgerValidationError(Exception):
    """Hard rejection of a ledger entry."""

    def __init__(self, warnings: list[ValidationWarning]) -> None:
        self.warnings = warnings
        super().__init__(f"{len(warnings)} hard validation error(s)")


def validate_ledger_entry(
    position: str,
    claims: list[Claim],
    delta: str,
    tags: list[str],
    unresolved: list[Unresolved],
    turn_number: int,
    *,
    unresolved_closed: int = 0,
    prior_claims: list[Claim] | None = None,
) -> tuple[LedgerEntry, list[ValidationWarning]]:
    """Build and validate a LedgerEntry.

    Raises LedgerValidationError for hard rejects (empty claims, bad turn_number).
    Returns (entry, soft_warnings) on success.

    prior_claims: if provided, enables referential validation (Task 4).
    """
    hard: list[ValidationWarning] = []
    soft: list[ValidationWarning] = []

    # --- Hard rejects ---
    if not claims:
        hard.append(ValidationWarning(
            tier=ValidationTier.HARD_REJECT,
            field="claims",
            message="Claims list is empty — each turn must have at least one claim",
        ))
    if turn_number < 1:
        hard.append(ValidationWarning(
            tier=ValidationTier.HARD_REJECT,
            field="turn_number",
            message=f"Turn number must be >= 1, got {turn_number}",
        ))

    if hard:
        raise LedgerValidationError(hard)

    # --- Compute derived fields ---
    counters = compute_counters(claims, unresolved_closed=unresolved_closed)
    quality = compute_quality(counters)
    effective_delta = compute_effective_delta(counters)

    # --- Soft warnings ---
    if not position:
        soft.append(ValidationWarning(
            tier=ValidationTier.SOFT_WARN,
            field="position",
            message="Position is empty — agent should summarize their current stance",
        ))

    if delta and _delta_disagrees(delta, effective_delta):
        soft.append(ValidationWarning(
            tier=ValidationTier.SOFT_WARN,
            field="delta",
            message=(
                f"Agent-reported delta {delta!r} disagrees with "
                f"computed effective_delta {effective_delta.value!r}"
            ),
            details={"agent_delta": delta, "effective_delta": effective_delta.value},
        ))

    # --- Referential warnings (Task 4 extension point) ---
    if prior_claims is not None:
        soft.extend(_referential_warnings(claims, prior_claims))

    entry = LedgerEntry(
        position=position,
        claims=claims,
        delta=delta,
        tags=tags,
        unresolved=unresolved,
        counters=counters,
        quality=quality,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )
    return entry, soft


def _delta_disagrees(agent_delta: str, effective_delta: EffectiveDelta) -> bool:
    """Check if agent's self-reported delta contradicts computed effective_delta.

    Canonical 3-way semantic logic:
    - "static" contradicts non-STATIC (advancing or shifting)
    - "advancing" or "shifting" contradicts STATIC
    - Unknown agent delta values fall through (no disagreement)
    """
    agent_lower = agent_delta.lower()

    if agent_lower == "static" and effective_delta != EffectiveDelta.STATIC:
        return True
    if agent_lower in {"advancing", "shifting"} and effective_delta == EffectiveDelta.STATIC:
        return True
    return False


def _referential_warnings(
    claims: list[Claim], prior_claims: list[Claim],
) -> list[ValidationWarning]:
    """Stub for Task 4 referential validation."""
    return []
```

**Step 5: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py -v`
Expected: PASS (all tests including hard reject and soft warn)

**Step 6: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/ledger.py \
       packages/context-injection/tests/test_ledger.py
git commit -m "feat(context-injection): add hard and soft ledger validation (D1 Task 3)"
```

### Task 4: Referential validation

**Files:**
- Modify: `context_injection/ledger.py` (implement `_referential_warnings`)
- Modify: `tests/test_ledger.py`

Replaces the `_referential_warnings` stub from Task 3. Uses exact text match for claim comparison (deterministic, follows "deterministic over heuristic" tenet). Referential warnings are `REFERENTIAL_WARN` tier — softer than `SOFT_WARN` because the agent may have legitimately rephrased.

Claims checked: `reinforced` (no prior matching text), `conceded` (no prior matching text), `revised` (no prior matching text). Status `new` is excluded — new claims have no referent by definition.

**Step 1: Write failing tests for referential warnings**

Add to `tests/test_ledger.py`:

```python
class TestReferentialValidation:
    """Referential warnings when claim status doesn't match prior history."""

    def test_reinforced_with_matching_prior_no_warning(self) -> None:
        prior = [Claim(text="X is true", status="new", turn=1)]
        entry, warnings = validate_ledger_entry(
            position="Reaffirming X",
            claims=[Claim(text="X is true", status="reinforced", turn=2)],
            delta="stable",
            tags=[],
            unresolved=[],
            turn_number=2,
            prior_claims=prior,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert referential == []

    def test_reinforced_no_matching_prior_warns(self) -> None:
        prior = [Claim(text="Y is true", status="new", turn=1)]
        entry, warnings = validate_ledger_entry(
            position="Reaffirming X",
            claims=[Claim(text="X is true", status="reinforced", turn=2)],
            delta="stable",
            tags=[],
            unresolved=[],
            turn_number=2,
            prior_claims=prior,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert len(referential) == 1
        assert "reinforced" in referential[0].message
        assert "X is true" in referential[0].message

    def test_conceded_no_matching_prior_warns(self) -> None:
        prior = [Claim(text="Y is true", status="new", turn=1)]
        entry, warnings = validate_ledger_entry(
            position="Withdrawing",
            claims=[Claim(text="X was wrong", status="conceded", turn=2)],
            delta="correction",
            tags=[],
            unresolved=[],
            turn_number=2,
            prior_claims=prior,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert len(referential) == 1
        assert "conceded" in referential[0].message

    def test_revised_no_matching_prior_warns(self) -> None:
        prior = [Claim(text="Y is true", status="new", turn=1)]
        entry, warnings = validate_ledger_entry(
            position="Revising",
            claims=[Claim(text="X updated", status="revised", turn=2)],
            delta="correction",
            tags=[],
            unresolved=[],
            turn_number=2,
            prior_claims=prior,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert len(referential) == 1
        assert "revised" in referential[0].message

    def test_new_claim_never_triggers_referential(self) -> None:
        """New claims have no prior referent — never warns."""
        entry, warnings = validate_ledger_entry(
            position="New info",
            claims=[Claim(text="Z is novel", status="new", turn=1)],
            delta="new_information",
            tags=[],
            unresolved=[],
            turn_number=1,
            prior_claims=[],
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert referential == []

    def test_no_prior_claims_skips_referential(self) -> None:
        """When prior_claims is None, referential checks are skipped."""
        entry, warnings = validate_ledger_entry(
            position="Position",
            claims=[Claim(text="X", status="reinforced", turn=1)],
            delta="stable",
            tags=[],
            unresolved=[],
            turn_number=1,
            prior_claims=None,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert referential == []

    def test_multiple_referential_warnings(self) -> None:
        prior = [Claim(text="A", status="new", turn=1)]
        entry, warnings = validate_ledger_entry(
            position="Position",
            claims=[
                Claim(text="X", status="reinforced", turn=2),
                Claim(text="Y", status="conceded", turn=2),
            ],
            delta="mixed",
            tags=[],
            unresolved=[],
            turn_number=2,
            prior_claims=prior,
        )
        referential = [w for w in warnings if w.tier == ValidationTier.REFERENTIAL_WARN]
        assert len(referential) == 2
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py::TestReferentialValidation -v`
Expected: FAIL — tests pass vacuously because `_referential_warnings` returns `[]`. The `test_reinforced_no_matching_prior_warns` test will fail with `assert len(referential) == 1` (gets 0).

**Step 3: Implement _referential_warnings**

Replace the stub in `context_injection/ledger.py`:

```python
_REFERENTIAL_STATUSES: frozenset[str] = frozenset({"reinforced", "revised", "conceded"})
"""Claim statuses that imply a prior referent exists."""


def _referential_warnings(
    claims: list[Claim], prior_claims: list[Claim],
) -> list[ValidationWarning]:
    """Check that claims with referential statuses have matching prior claims.

    Uses exact text match (deterministic). Referential warnings are softer
    than soft warnings — the agent may have legitimately rephrased.
    """
    prior_texts = frozenset(c.text for c in prior_claims)
    warnings: list[ValidationWarning] = []

    for claim in claims:
        if claim.status not in _REFERENTIAL_STATUSES:
            continue
        if claim.text not in prior_texts:
            warnings.append(ValidationWarning(
                tier=ValidationTier.REFERENTIAL_WARN,
                field="claims",
                message=(
                    f"Claim marked {claim.status!r} but no prior claim with "
                    f"matching text found: {claim.text!r:.80}"
                ),
                details={"status": claim.status, "text": claim.text},
            ))

    return warnings
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py -v`
Expected: PASS (all D1 tests)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus all new test_ledger.py tests.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/ledger.py \
       packages/context-injection/tests/test_ledger.py
git commit -m "feat(context-injection): add referential validation (D1 Task 4)"
```
