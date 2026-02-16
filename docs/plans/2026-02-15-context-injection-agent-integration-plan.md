# Context Injection Agent Integration — Implementation Plan

> **ARCHIVE ONLY** — This is the original monolithic plan. The authoritative versions are the split delivery documents listed in the [manifest](2026-02-15-context-injection-agent-integration-manifest.md). This file is preserved for git history (commit `34c4f2c`). Do not execute from this file.

> ~~**For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.~~

**Goal:** Upgrade the context injection MCP server from "scout executor" to "conversation controller" — server owns ledger state, validates entries, computes derived fields, and makes continue/conclude decisions.

**Architecture:** Server-owned ledger state with "separate language from state" principle. Five deliveries: D1-D3 are pure additive modules (no existing code changes), D4 is concentrated integration (schema swap + pipeline rewiring + test migration), D5 is the agent rewrite. Agent becomes the language layer (semantic extraction + judgment), server becomes the state layer (validation + derivation + decisions).

**Tech Stack:** Python 3.12, Pydantic v2 (frozen/strict/forbid-extra), FastMCP, pytest, ripgrep

**References:**
- Planning brief: `docs/plans/2026-02-15-context-injection-agent-integration-planning-brief.md`
- Decisions (5 locked): `docs/plans/2026-02-15-context-injection-agent-integration-decisions.md`
- Exploration: `docs/plans/2026-02-15-context-injection-agent-integration.md`
- Design spec: `docs/plans/2026-02-11-conversation-aware-context-injection.md`
- Protocol contract (0.1.0): `docs/references/context-injection-contract.md`

**Branch:** Create `feature/context-injection-agent-integration` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

**Package directory:** `packages/context-injection/`

**Dependencies between deliveries:**
```
D1 (Ledger Validation) ─────┬──→ D4 (Schema 0.2.0 + Pipeline Integration) ──→ D5 (Agent Rewrite)
D2 (Conversation State) ────┤
D3 (Conversation Control) ──┘
```
- D1: independent (pure new module)
- D2: depends on D1 (uses LedgerEntry, CumulativeState types)
- D3: depends on D1 only (pure functions on D1 types — NOT on D2's ConversationState)
- D2 and D3 can be implemented in parallel
- D4: depends on D1 + D2 + D3 (wires all new modules into existing pipeline)
- D5: depends on D4 (agent uses 0.2.0 protocol)

---

## D1: Ledger Validation

Pure additive delivery. New `ledger.py` module + `test_ledger.py`. No existing code changes.

**Estimated new tests:** 200-300

### Task 1: Ledger types and enums

**Files:**
- Modify: `context_injection/enums.py` (add EffectiveDelta, QualityLabel, ValidationTier)
- Create: `context_injection/ledger.py` (LedgerEntry, LedgerEntryCounters, ValidationWarning, CumulativeState)
- Create: `tests/test_ledger.py`

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

**Step 7: Implement ledger types**

Create `context_injection/ledger.py`:

```python
"""Ledger validation types and computation.

Server-side validation of agent-provided ledger entries. Computes derived
fields (counters, quality, effective_delta) and validates structural and
referential constraints.
"""

from __future__ import annotations

from context_injection.enums import EffectiveDelta, QualityLabel, ValidationTier
from context_injection.types import Claim, ProtocolModel, Unresolved


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
    details: dict | None = None


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

Run: `cd packages/context-injection && uv run pytest tests/test_ledger.py -v`
Expected: PASS (all TestLedgerEnums + TestLedgerTypes tests)

**Step 9: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_ledger.py tests.

**Step 10: Commit**

```bash
git add packages/context-injection/context_injection/enums.py \
       packages/context-injection/context_injection/ledger.py \
       packages/context-injection/tests/test_ledger.py
git commit -m "feat(context-injection): add ledger types and enums (D1 Task 1)"
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

    Agent delta is free-form text; effective_delta is computed from counters.
    Disagreement: agent says 'static'/'no change' but computed is advancing/shifting,
    or agent says 'new'/'major' but computed is static.
    """
    agent_lower = agent_delta.lower()
    static_signals = {"static", "none", "no change", "no_change", "stable"}
    advancing_signals = {"new", "new_information", "major", "advancing"}

    if agent_lower in static_signals and effective_delta != EffectiveDelta.STATIC:
        return True
    if agent_lower in advancing_signals and effective_delta == EffectiveDelta.STATIC:
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

---

## D2: Conversation State Management

Pure additive delivery. New `conversation.py` + `checkpoint.py`. Extends `state.py` with conversations dict.

**Estimated new tests:** 100-150
**Depends on:** D1 complete (uses LedgerEntry, CumulativeState)

### Task 5: ConversationState class

**Files:**
- Create: `context_injection/conversation.py`
- Create: `tests/test_conversation.py`

Pydantic `BaseModel` with `ConfigDict(frozen=True)` — not ProtocolModel (internal state, not wire type). Projection methods use `model_copy(update={...})` to return new instances. Pipeline commits atomically by replacing `ctx.conversations[id] = projected`.

**Design refinement from outline:** `with_turn(entry)` simplified from `with_turn(entry, claims)` — claims derived from `entry.claims` since `validate_ledger_entry` constructs the entry with the same claims. No redundancy.

**Step 1: Write failing tests for construction and immutability**

Create `tests/test_conversation.py`:

```python
"""Conversation state management tests."""

import pytest
from pydantic import ValidationError

from context_injection.conversation import ConversationState
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
)
from context_injection.types import Claim, EvidenceRecord, Unresolved


def _make_entry(
    turn_number: int = 1,
    *,
    position: str = "Position",
    claims: list[Claim] | None = None,
    delta: str = "new_information",
    effective_delta: EffectiveDelta = EffectiveDelta.ADVANCING,
    quality: QualityLabel = QualityLabel.SUBSTANTIVE,
    unresolved: list[Unresolved] | None = None,
    unresolved_closed: int = 0,
) -> LedgerEntry:
    """Build a LedgerEntry for testing."""
    if claims is None:
        claims = [Claim(text=f"Claim {turn_number}", status="new", turn=turn_number)]
    if unresolved is None:
        unresolved = []
    counters = LedgerEntryCounters(
        new_claims=sum(1 for c in claims if c.status == "new"),
        revised=sum(1 for c in claims if c.status == "revised"),
        conceded=sum(1 for c in claims if c.status == "conceded"),
        unresolved_closed=unresolved_closed,
    )
    return LedgerEntry(
        position=position,
        claims=claims,
        delta=delta,
        tags=[],
        unresolved=unresolved,
        counters=counters,
        quality=quality,
        effective_delta=effective_delta,
        turn_number=turn_number,
    )


class TestConversationStateConstruction:
    """Construction and immutability."""

    def test_empty_state(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.conversation_id == "conv-1"
        assert state.entries == []
        assert state.claim_registry == []
        assert state.evidence_history == []
        assert state.closing_probe_fired is False
        assert state.last_checkpoint_id is None

    def test_frozen(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        with pytest.raises(ValidationError):
            state.conversation_id = "other"  # type: ignore[misc]
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_conversation.py::TestConversationStateConstruction -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.conversation'`

**Step 3: Write failing tests for projection methods**

Add to `tests/test_conversation.py`:

```python
class TestWithTurn:
    """with_turn: append entry, extend claim_registry."""

    def test_first_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        assert len(projected.entries) == 1
        assert projected.entries[0] is entry
        assert len(projected.claim_registry) == 1
        assert projected.claim_registry[0].text == "Claim 1"

    def test_second_turn_appends(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(turn_number=1)
        e2 = _make_entry(turn_number=2)
        projected = state.with_turn(e1).with_turn(e2)
        assert len(projected.entries) == 2
        assert len(projected.claim_registry) == 2
        assert projected.claim_registry[0].text == "Claim 1"
        assert projected.claim_registry[1].text == "Claim 2"

    def test_original_unchanged(self) -> None:
        """Immutable projection — original state not modified."""
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        _ = state.with_turn(entry)
        assert state.entries == []
        assert state.claim_registry == []

    def test_multi_claim_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(
            turn_number=1,
            claims=[
                Claim(text="A", status="new", turn=1),
                Claim(text="B", status="reinforced", turn=1),
            ],
        )
        projected = state.with_turn(entry)
        assert len(projected.claim_registry) == 2


class TestWithEvidence:
    """with_evidence: append evidence record."""

    def test_appends_evidence(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:foo.py", template_id="probe.file_repo_fact", turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.evidence_history) == 1
        assert projected.evidence_history[0].entity_key == "file:foo.py"

    def test_original_unchanged(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:foo.py", template_id="probe.file_repo_fact", turn=1,
        )
        _ = state.with_evidence(record)
        assert state.evidence_history == []


class TestWithClosingProbeFired:
    """with_closing_probe_fired: set flag."""

    def test_sets_flag(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        projected = state.with_closing_probe_fired()
        assert projected.closing_probe_fired is True
        assert state.closing_probe_fired is False


class TestWithCheckpointId:
    """with_checkpoint_id: update head checkpoint."""

    def test_sets_checkpoint_id(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        projected = state.with_checkpoint_id("abc123")
        assert projected.last_checkpoint_id == "abc123"
        assert state.last_checkpoint_id is None
```

**Step 4: Write failing tests for accessors and compute_cumulative_state**

Add to `tests/test_conversation.py`:

```python
class TestGetCumulativeClaims:
    """get_cumulative_claims: return claim registry copy."""

    def test_empty(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.get_cumulative_claims() == []

    def test_after_turns(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(turn_number=1)
        e2 = _make_entry(
            turn_number=2,
            claims=[
                Claim(text="X", status="new", turn=2),
                Claim(text="Y", status="reinforced", turn=2),
            ],
        )
        projected = state.with_turn(e1).with_turn(e2)
        claims = projected.get_cumulative_claims()
        assert len(claims) == 3  # 1 from turn 1, 2 from turn 2

    def test_returns_copy(self) -> None:
        """Returned list is a copy — mutations don't affect state."""
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        claims = projected.get_cumulative_claims()
        claims.clear()
        assert len(projected.get_cumulative_claims()) == 1


class TestGetEvidenceHistory:
    """get_evidence_history: return evidence list copy."""

    def test_empty(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        assert state.get_evidence_history() == []

    def test_after_evidence(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        record = EvidenceRecord(
            entity_key="file:a.py", template_id="probe.file_repo_fact", turn=1,
        )
        projected = state.with_evidence(record)
        assert len(projected.get_evidence_history()) == 1


class TestComputeCumulativeState:
    """compute_cumulative_state: aggregate from entries."""

    def test_empty_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        cumulative = state.compute_cumulative_state()
        assert cumulative.total_claims == 0
        assert cumulative.reinforced == 0
        assert cumulative.revised == 0
        assert cumulative.conceded == 0
        assert cumulative.unresolved_open == 0
        assert cumulative.unresolved_closed == 0
        assert cumulative.turns_completed == 0
        assert cumulative.effective_delta_sequence == []

    def test_single_entry(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="new", turn=1)],
        )
        projected = state.with_turn(entry)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.total_claims == 1
        assert cumulative.reinforced == 0
        assert cumulative.turns_completed == 1
        assert cumulative.effective_delta_sequence == [EffectiveDelta.ADVANCING]

    def test_multi_turn(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="new", turn=1)],
        )
        e2 = _make_entry(
            turn_number=2,
            claims=[
                Claim(text="A", status="reinforced", turn=2),
                Claim(text="B", status="revised", turn=2),
            ],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.total_claims == 3  # 1 + 2
        assert cumulative.reinforced == 1
        assert cumulative.revised == 1
        assert cumulative.turns_completed == 2
        assert cumulative.effective_delta_sequence == [
            EffectiveDelta.ADVANCING, EffectiveDelta.SHIFTING,
        ]

    def test_unresolved_open_from_latest(self) -> None:
        """unresolved_open comes from the latest entry only."""
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            unresolved=[Unresolved(text="Q1?", turn=1), Unresolved(text="Q2?", turn=1)],
        )
        e2 = _make_entry(
            turn_number=2,
            unresolved=[Unresolved(text="Q1?", turn=2)],
            unresolved_closed=1,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.unresolved_open == 1
        assert cumulative.unresolved_closed == 1

    def test_conceded_accumulated(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        e1 = _make_entry(
            turn_number=1,
            claims=[Claim(text="A", status="conceded", turn=1)],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        e2 = _make_entry(
            turn_number=2,
            claims=[Claim(text="B", status="conceded", turn=2)],
            effective_delta=EffectiveDelta.SHIFTING,
        )
        projected = state.with_turn(e1).with_turn(e2)
        cumulative = projected.compute_cumulative_state()
        assert cumulative.conceded == 2
```

**Step 5: Implement ConversationState**

Create `context_injection/conversation.py`:

```python
"""Conversation state management.

Immutable projection pattern: ConversationState is never mutated.
Projection methods return new instances via model_copy(update={...}).
Pipeline commits atomically by replacing the dict entry:
ctx.conversations[id] = projected.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from context_injection.enums import EffectiveDelta
from context_injection.ledger import CumulativeState, LedgerEntry
from context_injection.types import Claim, EvidenceRecord


class ConversationState(BaseModel):
    """Per-conversation state. Frozen — projection methods return new instances."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str
    entries: list[LedgerEntry] = []
    claim_registry: list[Claim] = []
    evidence_history: list[EvidenceRecord] = []
    closing_probe_fired: bool = False
    last_checkpoint_id: str | None = None

    def with_turn(self, entry: LedgerEntry) -> ConversationState:
        """New state with entry appended and claim_registry extended."""
        return self.model_copy(update={
            "entries": [*self.entries, entry],
            "claim_registry": [*self.claim_registry, *entry.claims],
        })

    def with_evidence(self, record: EvidenceRecord) -> ConversationState:
        """New state with evidence record appended."""
        return self.model_copy(update={
            "evidence_history": [*self.evidence_history, record],
        })

    def with_closing_probe_fired(self) -> ConversationState:
        """New state with closing_probe_fired set."""
        return self.model_copy(update={"closing_probe_fired": True})

    def with_checkpoint_id(self, checkpoint_id: str) -> ConversationState:
        """New state with last_checkpoint_id updated."""
        return self.model_copy(update={"last_checkpoint_id": checkpoint_id})

    def get_cumulative_claims(self) -> list[Claim]:
        """All claims from all turns (insertion-ordered). Returns copy."""
        return list(self.claim_registry)

    def get_evidence_history(self) -> list[EvidenceRecord]:
        """All evidence records (insertion-ordered). Returns copy."""
        return list(self.evidence_history)

    def compute_cumulative_state(self) -> CumulativeState:
        """Aggregate state across all validated ledger entries.

        total_claims: all claims across all entries (including reinforced).
        reinforced: scanned from claims (not tracked in counters).
        revised/conceded: from entry counters.
        unresolved_open: from latest entry's unresolved list.
        unresolved_closed: summed from entry counters.
        """
        total_claims = sum(len(e.claims) for e in self.entries)
        reinforced = sum(
            sum(1 for c in e.claims if c.status == "reinforced")
            for e in self.entries
        )
        revised = sum(e.counters.revised for e in self.entries)
        conceded = sum(e.counters.conceded for e in self.entries)
        unresolved_open = (
            len(self.entries[-1].unresolved) if self.entries else 0
        )
        unresolved_closed = sum(
            e.counters.unresolved_closed for e in self.entries
        )
        turns_completed = len(self.entries)
        effective_delta_sequence = [e.effective_delta for e in self.entries]

        return CumulativeState(
            total_claims=total_claims,
            reinforced=reinforced,
            revised=revised,
            conceded=conceded,
            unresolved_open=unresolved_open,
            unresolved_closed=unresolved_closed,
            turns_completed=turns_completed,
            effective_delta_sequence=effective_delta_sequence,
        )
```

**Step 6: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_conversation.py -v`
Expected: PASS (all construction, projection, accessor, and cumulative state tests)

**Step 7: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_conversation.py tests.

**Step 8: Commit**

```bash
git add packages/context-injection/context_injection/conversation.py \
       packages/context-injection/tests/test_conversation.py
git commit -m "feat(context-injection): add ConversationState with immutable projections (D2 Task 5)"
```

### Task 6: Checkpoint types and serialization

**Files:**
- Create: `context_injection/checkpoint.py`
- Create: `tests/test_checkpoint.py`

`StateCheckpoint` is a `ProtocolModel` (wire type — the `model_dump_json()` of this type is the opaque string in `TurnPacketSuccess.state_checkpoint`). The agent stores this string opaque and sends it back. The server deserializes to restore state.

`serialize_checkpoint` returns `tuple[str, str]` — `(checkpoint_id, checkpoint_string)`. The pipeline needs both: checkpoint_id for `with_checkpoint_id()` and `TurnPacketSuccess.checkpoint_id`; checkpoint_string for `TurnPacketSuccess.state_checkpoint`.

**Step 1: Write failing tests for StateCheckpoint and serialization**

Create `tests/test_checkpoint.py`:

```python
"""Checkpoint serialization and validation tests."""

import json

import pytest

from context_injection.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    CheckpointError,
    StateCheckpoint,
    deserialize_checkpoint,
    serialize_checkpoint,
)
from context_injection.conversation import ConversationState


class TestStateCheckpoint:
    """StateCheckpoint type construction."""

    def test_construction(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc123",
            parent_checkpoint_id=None,
            format_version="1",
            payload='{"conversation_id":"c1"}',
            size=25,
        )
        assert cp.checkpoint_id == "abc123"
        assert cp.parent_checkpoint_id is None
        assert cp.format_version == "1"

    def test_with_parent(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="def456",
            parent_checkpoint_id="abc123",
            format_version="1",
            payload="{}",
            size=2,
        )
        assert cp.parent_checkpoint_id == "abc123"


class TestSerializeCheckpoint:
    """serialize_checkpoint: state → (checkpoint_id, checkpoint_string)."""

    def test_round_trip(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        checkpoint_id, checkpoint_string = serialize_checkpoint(state, parent_id=None)
        assert len(checkpoint_id) == 32  # uuid4 hex
        restored, restored_id = deserialize_checkpoint(checkpoint_string)
        assert restored.conversation_id == "conv-1"
        assert restored_id == checkpoint_id

    def test_parent_id_preserved(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        _, cp_string = serialize_checkpoint(state, parent_id="parent-abc")
        parsed = json.loads(cp_string)
        assert parsed["parent_checkpoint_id"] == "parent-abc"

    def test_format_version_included(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        _, cp_string = serialize_checkpoint(state, parent_id=None)
        parsed = json.loads(cp_string)
        assert parsed["format_version"] == CHECKPOINT_FORMAT_VERSION

    def test_exceeds_size_cap_raises(self) -> None:
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        claims = [
            Claim(text=f"Long claim text {'x' * 200} {i}", status="new", turn=1)
            for i in range(100)
        ]
        counters = LedgerEntryCounters(
            new_claims=100, revised=0, conceded=0, unresolved_closed=0,
        )
        entry = LedgerEntry(
            position="x" * 500,
            claims=claims,
            delta="new",
            tags=[],
            unresolved=[],
            counters=counters,
            quality=QualityLabel.SUBSTANTIVE,
            effective_delta=EffectiveDelta.ADVANCING,
            turn_number=1,
        )
        state = ConversationState(conversation_id="conv-1").with_turn(entry)
        with pytest.raises(ValueError, match="exceeds"):
            serialize_checkpoint(state, parent_id=None)


class TestDeserializeCheckpoint:
    """deserialize_checkpoint: checkpoint_string → (state, checkpoint_id)."""

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint("not valid json")
        assert exc_info.value.code == "checkpoint_invalid"

    def test_wrong_format_version_raises(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version="999",
            payload='{"conversation_id":"c1"}',
            size=25,
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"
        assert "format version" in str(exc_info.value).lower()

    def test_corrupt_payload_raises(self) -> None:
        cp = StateCheckpoint(
            checkpoint_id="abc",
            parent_checkpoint_id=None,
            format_version=CHECKPOINT_FORMAT_VERSION,
            payload="not valid json",
            size=15,
        )
        with pytest.raises(CheckpointError) as exc_info:
            deserialize_checkpoint(cp.model_dump_json())
        assert exc_info.value.code == "checkpoint_invalid"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.checkpoint'`

**Step 3: Implement checkpoint types and serialization**

Create `context_injection/checkpoint.py`:

```python
"""Checkpoint serialization and chain validation.

Checkpoints are opaque state snapshots passed between server and agent.
The agent stores the checkpoint string and sends it back on the next turn.
The server deserializes and validates to restore conversation state.

Wire encoding: TurnPacketSuccess.state_checkpoint carries the
model_dump_json() of StateCheckpoint. This is double-encoded JSON
(outer = StateCheckpoint, inner payload = ConversationState).
"""

from __future__ import annotations

import uuid

from context_injection.conversation import ConversationState
from context_injection.types import ProtocolModel

CHECKPOINT_FORMAT_VERSION: str = "1"
"""Checkpoint serialization format. Increment on breaking changes."""

MAX_CHECKPOINT_PAYLOAD_BYTES: int = 16_384
"""Hard limit on serialized ConversationState payload (16 KB)."""


class StateCheckpoint(ProtocolModel):
    """Serialized conversation state for agent-side storage.

    Wire type: model_dump_json() of this type is the opaque string
    sent in TurnPacketSuccess.state_checkpoint.
    """

    checkpoint_id: str
    parent_checkpoint_id: str | None
    format_version: str
    payload: str
    size: int


class CheckpointError(Exception):
    """Checkpoint validation failure with error code.

    Codes map to ErrorDetail.code in D4:
    checkpoint_missing, checkpoint_invalid, checkpoint_stale.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def serialize_checkpoint(
    state: ConversationState, parent_id: str | None,
) -> tuple[str, str]:
    """Serialize state to checkpoint. Returns (checkpoint_id, checkpoint_string).

    checkpoint_string is the opaque payload for TurnPacketSuccess.state_checkpoint.
    Raises ValueError if payload exceeds MAX_CHECKPOINT_PAYLOAD_BYTES.
    """
    checkpoint_id = uuid.uuid4().hex
    payload = state.model_dump_json()
    payload_size = len(payload.encode("utf-8"))

    if payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES:
        raise ValueError(
            f"Checkpoint payload exceeds {MAX_CHECKPOINT_PAYLOAD_BYTES} bytes: "
            f"got {payload_size} bytes. Compact the ledger before serializing."
        )

    checkpoint = StateCheckpoint(
        checkpoint_id=checkpoint_id,
        parent_checkpoint_id=parent_id,
        format_version=CHECKPOINT_FORMAT_VERSION,
        payload=payload,
        size=payload_size,
    )
    return checkpoint_id, checkpoint.model_dump_json()


def deserialize_checkpoint(checkpoint_string: str) -> tuple[ConversationState, str]:
    """Deserialize checkpoint string. Returns (state, checkpoint_id).

    Raises CheckpointError("checkpoint_invalid") on corrupt or incompatible payload.
    """
    try:
        checkpoint = StateCheckpoint.model_validate_json(checkpoint_string)
    except Exception as e:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Failed to parse checkpoint envelope: {e}",
        ) from e

    if checkpoint.format_version != CHECKPOINT_FORMAT_VERSION:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Unsupported checkpoint format version: {checkpoint.format_version!r}, "
            f"expected {CHECKPOINT_FORMAT_VERSION!r}",
        )

    try:
        state = ConversationState.model_validate_json(checkpoint.payload)
    except Exception as e:
        raise CheckpointError(
            "checkpoint_invalid",
            f"Failed to deserialize conversation state from payload: {e}",
        ) from e

    return state, checkpoint.checkpoint_id
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: PASS (all StateCheckpoint, serialize, and deserialize tests)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/checkpoint.py \
       packages/context-injection/tests/test_checkpoint.py
git commit -m "feat(context-injection): add checkpoint types and serialization (D2 Task 6)"
```

### Task 7: Checkpoint chain validation and compaction

**Files:**
- Modify: `context_injection/checkpoint.py` (add validate_checkpoint_intake, compact_ledger)
- Modify: `tests/test_checkpoint.py`

Five-case intake policy for resolving conversation state at the start of each turn. The key distinction: `last_checkpoint_id is not None` reliably indicates "real state" vs "fresh empty state created by `get_or_create_conversation` after server restart." This lets the function route to checkpoint restore when the server has no real memory of the conversation.

Compaction: when entries exceed `MAX_ENTRIES_BEFORE_COMPACT`, keep only `KEEP_RECENT_ENTRIES` most recent and rebuild `claim_registry` from them. Trade-off: referential validation loses history beyond the window (acceptable — `REFERENTIAL_WARN` is the softest tier).

**Step 1: Write failing tests for checkpoint intake (all 5 cases)**

Add to `tests/test_checkpoint.py`:

```python
from context_injection.checkpoint import (
    validate_checkpoint_intake,
)


class TestValidateCheckpointIntake:
    """Checkpoint intake 5-case policy."""

    def test_turn_1_returns_in_memory(self) -> None:
        """Turn 1: checkpoint optional, use in-memory."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id=None, checkpoint_payload=None, turn_number=1,
        )
        assert result is state

    def test_turn_1_ignores_checkpoint(self) -> None:
        """Turn 1 with checkpoint present — checkpoint ignored."""
        state = ConversationState(conversation_id="conv-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id="orphan", checkpoint_payload="ignored",
            turn_number=1,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_match(self) -> None:
        """Turn > 1, real state, IDs match — use in-memory."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        result = validate_checkpoint_intake(
            state, checkpoint_id="cp-1", checkpoint_payload=None, turn_number=2,
        )
        assert result is state

    def test_turn_gt1_in_memory_ids_mismatch_raises(self) -> None:
        """Turn > 1, real state, IDs mismatch — stale error."""
        state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                state, checkpoint_id="cp-OLD", checkpoint_payload=None,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_stale"

    def test_turn_gt1_no_real_state_restores_from_checkpoint(self) -> None:
        """Turn > 1, server restarted (no real state) — restore from checkpoint."""
        in_memory = ConversationState(conversation_id="conv-1")
        # Create a checkpoint from real state
        real_state = ConversationState(
            conversation_id="conv-1",
        ).with_checkpoint_id("cp-1")
        _, cp_string = serialize_checkpoint(real_state, parent_id=None)
        result = validate_checkpoint_intake(
            in_memory, checkpoint_id="cp-1", checkpoint_payload=cp_string,
            turn_number=2,
        )
        assert result.conversation_id == "conv-1"
        assert result.last_checkpoint_id == "cp-1"

    def test_turn_gt1_no_real_state_no_checkpoint_raises(self) -> None:
        """Turn > 1, no real state, no checkpoint — missing error."""
        in_memory = ConversationState(conversation_id="conv-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id=None, checkpoint_payload=None,
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_missing"

    def test_turn_gt1_corrupt_checkpoint_raises(self) -> None:
        """Turn > 1, no real state, corrupt checkpoint — invalid error."""
        in_memory = ConversationState(conversation_id="conv-1")
        with pytest.raises(CheckpointError) as exc_info:
            validate_checkpoint_intake(
                in_memory, checkpoint_id="cp-1", checkpoint_payload="corrupt",
                turn_number=2,
            )
        assert exc_info.value.code == "checkpoint_invalid"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py::TestValidateCheckpointIntake -v`
Expected: FAIL — `ImportError: cannot import name 'validate_checkpoint_intake'`

**Step 3: Write failing tests for compact_ledger**

Add to `tests/test_checkpoint.py`:

```python
from context_injection.checkpoint import (
    KEEP_RECENT_ENTRIES,
    MAX_ENTRIES_BEFORE_COMPACT,
    compact_ledger,
)
from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.ledger import LedgerEntry, LedgerEntryCounters
from context_injection.types import Claim


def _make_entry(
    turn_number: int = 1,
    *,
    claims: list[Claim] | None = None,
) -> LedgerEntry:
    """Minimal LedgerEntry for checkpoint tests."""
    if claims is None:
        claims = [Claim(text=f"Claim {turn_number}", status="new", turn=turn_number)]
    counters = LedgerEntryCounters(
        new_claims=len(claims), revised=0, conceded=0, unresolved_closed=0,
    )
    return LedgerEntry(
        position=f"Position {turn_number}",
        claims=claims,
        delta="new_information",
        tags=[],
        unresolved=[],
        counters=counters,
        quality=QualityLabel.SUBSTANTIVE,
        effective_delta=EffectiveDelta.ADVANCING,
        turn_number=turn_number,
    )


class TestCompactLedger:
    """compact_ledger: reduce state size for checkpoint serialization."""

    def test_below_threshold_unchanged(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        entry = _make_entry(turn_number=1)
        projected = state.with_turn(entry)
        result = compact_ledger(projected)
        assert result is projected

    def test_above_threshold_trims_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        assert len(state.entries) == MAX_ENTRIES_BEFORE_COMPACT + 4
        result = compact_ledger(state)
        assert len(result.entries) == KEEP_RECENT_ENTRIES

    def test_keeps_most_recent_entries(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        total = MAX_ENTRIES_BEFORE_COMPACT + 5
        for i in range(1, total + 1):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        expected_start = total - KEEP_RECENT_ENTRIES + 1
        assert result.entries[0].turn_number == expected_start
        assert result.entries[-1].turn_number == total

    def test_claim_registry_rebuilt_from_recent(self) -> None:
        state = ConversationState(conversation_id="conv-1")
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        recent_turn_numbers = {e.turn_number for e in result.entries}
        for claim in result.claim_registry:
            assert claim.turn in recent_turn_numbers

    def test_preserves_other_fields(self) -> None:
        state = ConversationState(
            conversation_id="conv-1",
            closing_probe_fired=True,
            last_checkpoint_id="cp-5",
        )
        from context_injection.types import EvidenceRecord

        state = state.with_evidence(
            EvidenceRecord(entity_key="f:a.py", template_id="probe.file_repo_fact", turn=1),
        )
        for i in range(1, MAX_ENTRIES_BEFORE_COMPACT + 5):
            state = state.with_turn(_make_entry(turn_number=i))
        result = compact_ledger(state)
        assert result.closing_probe_fired is True
        assert result.last_checkpoint_id == "cp-5"
        assert len(result.evidence_history) == 1
```

**Step 4: Implement validate_checkpoint_intake and compact_ledger**

Add to `context_injection/checkpoint.py`:

```python
MAX_ENTRIES_BEFORE_COMPACT: int = 16
"""Trigger compaction when entries exceed this count."""

KEEP_RECENT_ENTRIES: int = 8
"""Number of recent entries to keep after compaction."""


def validate_checkpoint_intake(
    in_memory: ConversationState,
    checkpoint_id: str | None,
    checkpoint_payload: str | None,
    turn_number: int,
) -> ConversationState:
    """Resolve conversation state for a turn.

    Five-case policy:
    - Turn 1: use in_memory (checkpoint ignored)
    - Turn > 1, real state (last_checkpoint_id set), IDs match: use in_memory
    - Turn > 1, real state, IDs mismatch: checkpoint_stale error
    - Turn > 1, no real state, checkpoint present: restore from checkpoint
    - Turn > 1, no real state, no checkpoint: checkpoint_missing error

    in_memory: from ctx.get_or_create_conversation() — never None.
    "Real state" means last_checkpoint_id is not None (server has
    processed at least one turn for this conversation).
    """
    if turn_number <= 1:
        return in_memory

    has_real_state = in_memory.last_checkpoint_id is not None

    if has_real_state:
        if checkpoint_id == in_memory.last_checkpoint_id:
            return in_memory
        raise CheckpointError(
            "checkpoint_stale",
            f"Checkpoint ID mismatch: server has "
            f"{in_memory.last_checkpoint_id!r}, agent sent {checkpoint_id!r}",
        )

    # No real state (server restarted) — restore from checkpoint
    if checkpoint_payload is not None:
        state, _ = deserialize_checkpoint(checkpoint_payload)
        return state

    raise CheckpointError(
        "checkpoint_missing",
        f"Turn {turn_number} requires checkpoint: server has no in-memory "
        f"state and no checkpoint payload was provided",
    )


def compact_ledger(state: ConversationState) -> ConversationState:
    """Reduce state size by keeping only recent entries.

    Triggered before checkpoint serialization when approaching size cap.
    Keeps KEEP_RECENT_ENTRIES most recent entries and rebuilds
    claim_registry from them.

    Trade-off: referential validation loses history beyond the window.
    Acceptable because REFERENTIAL_WARN is the softest tier.
    """
    if len(state.entries) <= MAX_ENTRIES_BEFORE_COMPACT:
        return state

    recent = state.entries[-KEEP_RECENT_ENTRIES:]
    claims = [c for e in recent for c in e.claims]
    return state.model_copy(update={
        "entries": recent,
        "claim_registry": claims,
    })
```

**Step 5: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: PASS (all checkpoint tests — types, serialize, deserialize, intake, compaction)

**Step 6: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass.

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/checkpoint.py \
       packages/context-injection/tests/test_checkpoint.py
git commit -m "feat(context-injection): add checkpoint chain validation and compaction (D2 Task 7)"
```

### Task 8: AppContext extension

**Files:**
- Modify: `context_injection/state.py` (add conversations dict to AppContext)
- Modify: `tests/test_state.py`

Adds `conversations: dict[str, ConversationState]` to `AppContext` and `get_or_create_conversation` method. The method always returns a `ConversationState` — either existing (real state) or freshly created (empty). Checkpoint intake (Task 7) determines whether the fresh state is acceptable or a checkpoint restore is needed.

**Step 1: Write failing tests for AppContext conversations**

Add to `tests/test_state.py`:

```python
from context_injection.conversation import ConversationState


class TestAppContextConversations:
    """AppContext conversation management."""

    def test_conversations_empty_by_default(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        assert ctx.conversations == {}

    def test_get_or_create_new(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        assert isinstance(state, ConversationState)
        assert state.conversation_id == "conv-1"
        assert state.entries == []

    def test_get_or_create_returns_existing(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state1 = ctx.get_or_create_conversation("conv-1")
        state2 = ctx.get_or_create_conversation("conv-1")
        assert state1 is state2

    def test_multiple_conversations(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        s1 = ctx.get_or_create_conversation("conv-1")
        s2 = ctx.get_or_create_conversation("conv-2")
        assert s1.conversation_id == "conv-1"
        assert s2.conversation_id == "conv-2"
        assert len(ctx.conversations) == 2

    def test_conversation_replacement(self) -> None:
        """Pipeline commits by replacing dict entry."""
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        projected = state.with_checkpoint_id("cp-1")
        ctx.conversations["conv-1"] = projected
        retrieved = ctx.get_or_create_conversation("conv-1")
        assert retrieved.last_checkpoint_id == "cp-1"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestAppContextConversations -v`
Expected: FAIL — `ImportError: cannot import name 'ConversationState'` or `AttributeError: 'AppContext' object has no attribute 'conversations'`

**Step 3: Implement AppContext extension**

Add import to `context_injection/state.py`:

```python
from context_injection.conversation import ConversationState
```

Add field to `AppContext` class (after `entity_counter`):

```python
    conversations: dict[str, ConversationState] = field(default_factory=dict)
    """Per-conversation state, keyed by conversation_id."""
```

Add method to `AppContext` class (after `next_entity_id`):

```python
    def get_or_create_conversation(self, conversation_id: str) -> ConversationState:
        """Return existing conversation state or create empty one.

        The returned state may be "fresh" (no real state) if the server
        restarted. Checkpoint intake (validate_checkpoint_intake) determines
        whether to use it or restore from a checkpoint.
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState(
                conversation_id=conversation_id,
            )
        return self.conversations[conversation_id]
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py -v`
Expected: PASS (all existing state tests + new TestAppContextConversations)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All existing tests pass, plus new conversation and checkpoint tests.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/state.py \
       packages/context-injection/tests/test_state.py
git commit -m "feat(context-injection): add conversations dict to AppContext (D2 Task 8)"
```

---

## D3: Conversation Control + Ledger Summary

Pure additive delivery. New `control.py` module. Pure functions on D1 types.

**Estimated new tests:** 50-80
**Depends on:** D1 complete (uses LedgerEntry, CumulativeState, EffectiveDelta)

### Task 9: Conversation action computation

**Files:**
- Create: `context_injection/control.py`
- Create: `tests/test_control.py`

`compute_action` determines what the agent should do next based on conversation trajectory. It's a pure function with clear precedence rules — budget exhaustion is checked first (hard stop), then plateau detection (convergence signal), then closing probe sequencing (soft landing), otherwise continue.

**Step 1: Write failing tests for ConversationAction enum**

Create `tests/test_control.py`:

```python
"""Tests for conversation control — action computation and ledger summary."""

from __future__ import annotations

import pytest

from context_injection.control import ConversationAction


class TestConversationAction:
    """ConversationAction enum membership and string values."""

    def test_members(self) -> None:
        assert set(ConversationAction) == {
            ConversationAction.CONTINUE_DIALOGUE,
            ConversationAction.CLOSING_PROBE,
            ConversationAction.CONCLUDE,
        }

    def test_values_are_snake_case(self) -> None:
        assert ConversationAction.CONTINUE_DIALOGUE == "continue_dialogue"
        assert ConversationAction.CLOSING_PROBE == "closing_probe"
        assert ConversationAction.CONCLUDE == "conclude"

    def test_is_str_enum(self) -> None:
        assert isinstance(ConversationAction.CONTINUE_DIALOGUE, str)
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py::TestConversationAction -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context_injection.control'`

**Step 2: Write failing tests for compute_action**

Add test helper and test classes to `tests/test_control.py`:

```python
from context_injection.control import compute_action
from context_injection.enums import EffectiveDelta
from context_injection.ledger import LedgerEntry, LedgerEntryCounters
from context_injection.types import Claim, Unresolved


def _make_entry(
    *,
    turn_number: int = 1,
    position: str = "Test position",
    effective_delta: EffectiveDelta = EffectiveDelta.ADVANCING,
    claims: list[Claim] | None = None,
    unresolved: list[Unresolved] | None = None,
) -> LedgerEntry:
    """Create a minimal LedgerEntry for control tests."""
    return LedgerEntry(
        position=position,
        claims=claims or [],
        delta="high",
        tags=["architecture"],
        unresolved=unresolved or [],
        counters=LedgerEntryCounters(
            new_claims=len(claims) if claims else 0,
            revised=0,
            conceded=0,
            unresolved_closed=0,
        ),
        quality="substantive",
        effective_delta=effective_delta,
        turn_number=turn_number,
    )


class TestComputeActionBudgetExhausted:
    """Budget exhaustion takes highest precedence."""

    def test_budget_zero_returns_conclude(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, reason = compute_action(entries, budget_remaining=0, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE
        assert "budget" in reason.lower()

    def test_budget_negative_returns_conclude(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, reason = compute_action(entries, budget_remaining=-1, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE

    def test_budget_zero_trumps_advancing(self) -> None:
        """Even with advancing deltas, budget exhaustion concludes."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=0, closing_probe_fired=False)
        assert action == ConversationAction.CONCLUDE


class TestComputeActionPlateau:
    """Plateau = last 2 effective_deltas both STATIC."""

    def test_two_static_is_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CLOSING_PROBE
        assert "plateau" in reason.lower()

    def test_one_static_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_advancing_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_static_then_shifting_not_plateau(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionClosingProbe:
    """Closing probe sequencing — fire once, then conclude."""

    def test_plateau_without_closing_probe_fires_probe(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CLOSING_PROBE

    def test_plateau_with_closing_probe_already_fired_concludes(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONCLUDE
        assert "plateau" in reason.lower()

    def test_plateau_with_unresolved_and_probe_fired_continues(self) -> None:
        """Plateau + closing probe fired BUT unresolved items remain → continue."""
        entries = [
            _make_entry(
                turn_number=1,
                effective_delta=EffectiveDelta.STATIC,
            ),
            _make_entry(
                turn_number=2,
                effective_delta=EffectiveDelta.STATIC,
                unresolved=[Unresolved(text="Open question", turn=1)],
            ),
        ]
        action, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "unresolved" in reason.lower()

    def test_plateau_revived_by_advancing_resets(self) -> None:
        """If conversation advances after plateau, it's no longer plateau."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=4, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=True)
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionContinue:
    """Default path — conversation continues."""

    def test_single_entry_continues(self) -> None:
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_advancing_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.ADVANCING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_empty_entries_continues(self) -> None:
        """No entries = first turn, always continue."""
        action, reason = compute_action([], budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE
        assert "first" in reason.lower() or "no entries" in reason.lower()

    def test_shifting_entries_continue(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.SHIFTING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
        ]
        action, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_budget_one_continues(self) -> None:
        """budget_remaining=1 means one turn left — still continue."""
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(entries, budget_remaining=1, closing_probe_fired=False)
        assert action == ConversationAction.CONTINUE_DIALOGUE


class TestComputeActionReasonStrings:
    """Verify reason strings are descriptive (not just action names)."""

    def test_budget_reason_mentions_budget(self) -> None:
        _, reason = compute_action(
            [_make_entry()], budget_remaining=0, closing_probe_fired=False,
        )
        assert len(reason) > 10

    def test_plateau_reason_mentions_static(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        _, reason = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        assert len(reason) > 10

    def test_continue_reason_is_nonempty(self) -> None:
        _, reason = compute_action(
            [_make_entry()], budget_remaining=5, closing_probe_fired=False,
        )
        assert len(reason) > 0
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement ConversationAction and compute_action**

Create `context_injection/control.py`:

```python
"""Conversation control — action computation and ledger summary.

Pure functions on ledger types. No side effects, no I/O.
"""

from __future__ import annotations

from enum import StrEnum

from context_injection.enums import EffectiveDelta
from context_injection.ledger import LedgerEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_ENTRIES_FOR_PLATEAU: int = 2
"""Minimum consecutive STATIC entries to detect plateau."""


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ConversationAction(StrEnum):
    """Agent action based on conversation trajectory."""

    CONTINUE_DIALOGUE = "continue_dialogue"
    CLOSING_PROBE = "closing_probe"
    CONCLUDE = "conclude"


# ---------------------------------------------------------------------------
# Action computation
# ---------------------------------------------------------------------------


def _is_plateau(entries: list[LedgerEntry]) -> bool:
    """Check if the last MIN_ENTRIES_FOR_PLATEAU entries are all STATIC."""
    if len(entries) < MIN_ENTRIES_FOR_PLATEAU:
        return False
    recent = entries[-MIN_ENTRIES_FOR_PLATEAU:]
    return all(e.effective_delta == EffectiveDelta.STATIC for e in recent)


def _has_open_unresolved(entries: list[LedgerEntry]) -> bool:
    """Check if the latest entry has unresolved items."""
    if not entries:
        return False
    return len(entries[-1].unresolved) > 0


def compute_action(
    entries: list[LedgerEntry],
    budget_remaining: int,
    closing_probe_fired: bool,
) -> tuple[ConversationAction, str]:
    """Determine next conversation action from ledger trajectory.

    Precedence (highest to lowest):
    1. Budget exhausted → CONCLUDE
    2. Plateau detected (last 2 STATIC):
       a. Closing probe already fired + no open unresolved → CONCLUDE
       b. Closing probe already fired + open unresolved → CONTINUE (address them)
       c. Closing probe not fired → CLOSING_PROBE
    3. No plateau → CONTINUE_DIALOGUE

    Args:
        entries: Validated ledger entries (chronological order).
        budget_remaining: Turns remaining in the conversation budget.
            0 or negative means budget is exhausted.
        closing_probe_fired: Whether a closing probe was already sent.

    Returns:
        Tuple of (action, human-readable reason string).
    """
    # 1. Budget exhaustion — hard stop
    if budget_remaining <= 0:
        return (
            ConversationAction.CONCLUDE,
            f"Budget exhausted ({budget_remaining} turns remaining)",
        )

    # 2. Need entries for plateau detection
    if not entries:
        return (
            ConversationAction.CONTINUE_DIALOGUE,
            "No entries yet — first turn",
        )

    # 3. Plateau detection
    plateau = _is_plateau(entries)

    if plateau:
        if closing_probe_fired:
            # Check for unresolved items — if present, continue to address them
            if _has_open_unresolved(entries):
                return (
                    ConversationAction.CONTINUE_DIALOGUE,
                    f"Plateau detected but {len(entries[-1].unresolved)} unresolved "
                    f"item(s) remain — continuing to address them",
                )
            return (
                ConversationAction.CONCLUDE,
                "Plateau detected — last 2 turns STATIC, closing probe "
                "already fired, no unresolved items",
            )
        return (
            ConversationAction.CLOSING_PROBE,
            "Plateau detected — last 2 turns STATIC, firing closing probe",
        )

    # 4. Default — continue
    last_delta = entries[-1].effective_delta
    return (
        ConversationAction.CONTINUE_DIALOGUE,
        f"Conversation active — last delta: {last_delta}",
    )
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: PASS (all TestConversationAction + TestComputeAction* tests, ~22 tests)

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus new test_control.py tests.

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/control.py packages/context-injection/tests/test_control.py
git commit -m "feat(context-injection): add compute_action for conversation control (D3 Task 9)"
```

---

### Task 10: Ledger summary generation

**Files:**
- Modify: `context_injection/control.py`
- Modify: `tests/test_control.py`

`generate_ledger_summary` produces a compact text summary of the conversation ledger for injection into agent prompts. The format is designed for LLM consumption — each turn on one line with key metadata, followed by aggregate state and trajectory lines. Target: 300-400 tokens for an 8-turn conversation.

**Step 1: Write failing tests for generate_ledger_summary**

Add to `tests/test_control.py`:

```python
from context_injection.control import generate_ledger_summary
from context_injection.ledger import CumulativeState


class TestGenerateLedgerSummaryFormat:
    """Output format: turn lines + state line + trajectory line."""

    def test_single_entry_format(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                position="Initial analysis of auth module",
                effective_delta=EffectiveDelta.ADVANCING,
            ),
        ]
        cumulative = CumulativeState(
            total_claims=3,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=1,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)

        # Must contain turn line
        assert "T1:" in result
        assert "Initial analysis of auth module" in result
        assert "advancing" in result.lower()

        # Must contain state line
        assert "claims" in result.lower()

        # Must contain trajectory line
        assert "trajectory" in result.lower()

    def test_multi_entry_format(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                position="Auth module analysis",
                effective_delta=EffectiveDelta.ADVANCING,
                claims=[Claim(text="JWT is best", status="new", turn=1)],
            ),
            _make_entry(
                turn_number=2,
                position="Revised to OAuth",
                effective_delta=EffectiveDelta.SHIFTING,
                claims=[
                    Claim(text="JWT is best", status="revised", turn=2),
                    Claim(text="OAuth preferred", status="new", turn=2),
                ],
            ),
            _make_entry(
                turn_number=3,
                position="Confirmed OAuth approach",
                effective_delta=EffectiveDelta.STATIC,
                claims=[
                    Claim(text="OAuth preferred", status="reinforced", turn=3),
                ],
            ),
        ]
        cumulative = CumulativeState(
            total_claims=4,
            reinforced=1,
            revised=1,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=3,
            effective_delta_sequence=[
                EffectiveDelta.ADVANCING,
                EffectiveDelta.SHIFTING,
                EffectiveDelta.STATIC,
            ],
        )
        result = generate_ledger_summary(entries, cumulative)

        # All turn lines present
        assert "T1:" in result
        assert "T2:" in result
        assert "T3:" in result

        # State line has key counters
        assert "4" in result  # total_claims
        assert "reinforced" in result.lower()

    def test_turn_lines_include_tags(self) -> None:
        entries = [
            LedgerEntry(
                position="Security review",
                claims=[],
                delta="high",
                tags=["security", "auth"],
                unresolved=[],
                counters=LedgerEntryCounters(
                    new_claims=0, revised=0, conceded=0, unresolved_closed=0,
                ),
                quality="substantive",
                effective_delta=EffectiveDelta.ADVANCING,
                turn_number=1,
            ),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        assert "security" in result.lower()
        assert "auth" in result.lower()

    def test_trajectory_line_shows_sequence(self) -> None:
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.SHIFTING),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=3,
            effective_delta_sequence=[
                EffectiveDelta.ADVANCING,
                EffectiveDelta.SHIFTING,
                EffectiveDelta.STATIC,
            ],
        )
        result = generate_ledger_summary(entries, cumulative)
        # Trajectory should show the sequence
        lines = result.strip().split("\n")
        trajectory_lines = [l for l in lines if "trajectory" in l.lower()]
        assert len(trajectory_lines) == 1
        traj = trajectory_lines[0].lower()
        assert "advancing" in traj
        assert "shifting" in traj
        assert "static" in traj


class TestGenerateLedgerSummaryEdgeCases:
    """Edge cases: empty entries, long positions, many turns."""

    def test_empty_entries_returns_minimal(self) -> None:
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=0,
            effective_delta_sequence=[],
        )
        result = generate_ledger_summary([], cumulative)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "no turns" in result.lower() or "0" in result

    def test_position_truncated_if_long(self) -> None:
        """Positions longer than 80 chars should be truncated in summary."""
        long_position = "A" * 200
        entries = [
            _make_entry(turn_number=1, position=long_position),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        # The full 200-char position should NOT appear verbatim
        assert long_position not in result
        # But a truncated version should
        assert "T1:" in result

    def test_unresolved_count_in_state_line(self) -> None:
        entries = [
            _make_entry(
                turn_number=1,
                unresolved=[
                    Unresolved(text="Q1", turn=1),
                    Unresolved(text="Q2", turn=1),
                ],
            ),
        ]
        cumulative = CumulativeState(
            total_claims=0,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=2,
            unresolved_closed=0,
            turns_completed=1,
            effective_delta_sequence=[EffectiveDelta.ADVANCING],
        )
        result = generate_ledger_summary(entries, cumulative)
        assert "unresolved" in result.lower()


class TestGenerateLedgerSummaryTokenBudget:
    """Summary should stay within token budget (~300-400 tokens for 8 turns)."""

    def test_eight_turn_summary_within_budget(self) -> None:
        """8 turns should produce roughly 300-400 tokens (~1200-1600 chars)."""
        entries = [
            _make_entry(
                turn_number=i + 1,
                position=f"Analysis of component {i + 1} with findings",
                effective_delta=[
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.SHIFTING,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.STATIC,
                    EffectiveDelta.STATIC,
                    EffectiveDelta.ADVANCING,
                    EffectiveDelta.STATIC,
                ][i],
                claims=[Claim(text=f"Claim {i + 1}", status="new", turn=i + 1)],
            )
            for i in range(8)
        ]
        deltas = [e.effective_delta for e in entries]
        cumulative = CumulativeState(
            total_claims=8,
            reinforced=0,
            revised=0,
            conceded=0,
            unresolved_open=0,
            unresolved_closed=0,
            turns_completed=8,
            effective_delta_sequence=deltas,
        )
        result = generate_ledger_summary(entries, cumulative)

        # Rough token estimate: 1 token ≈ 4 chars
        char_count = len(result)
        estimated_tokens = char_count / 4
        assert estimated_tokens < 600, (
            f"Summary too long: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )
        assert estimated_tokens > 100, (
            f"Summary too short: ~{estimated_tokens:.0f} tokens ({char_count} chars)"
        )
```

Run: `cd packages/context-injection && uv run pytest tests/test_control.py::TestGenerateLedgerSummaryFormat -v`
Expected: FAIL — `ImportError: cannot import name 'generate_ledger_summary'`

**Step 2: Implement generate_ledger_summary**

Add to `context_injection/control.py` (after `compute_action`):

```python
from context_injection.ledger import CumulativeState, LedgerEntry

# (Update the existing import to include CumulativeState)

# ---------------------------------------------------------------------------
# Constants (add to existing constants section)
# ---------------------------------------------------------------------------

MAX_POSITION_LENGTH: int = 80
"""Maximum position string length in summary lines. Longer positions are truncated."""


# ---------------------------------------------------------------------------
# Ledger summary
# ---------------------------------------------------------------------------


def _truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _format_turn_line(entry: LedgerEntry) -> str:
    """Format a single turn line for the ledger summary.

    Format: T{n}: {position} ({effective_delta}, {tags})
    """
    position = _truncate(entry.position, MAX_POSITION_LENGTH)
    tags_str = ", ".join(entry.tags) if entry.tags else "none"
    return f"T{entry.turn_number}: {position} ({entry.effective_delta}, {tags_str})"


def generate_ledger_summary(
    entries: list[LedgerEntry],
    cumulative: CumulativeState,
) -> str:
    """Generate a compact text summary of the conversation ledger.

    Designed for injection into agent prompts. Each turn gets one line,
    followed by aggregate state and trajectory.

    Format:
        T1: [position] (effective_delta, tags)
        T2: [position] (effective_delta, tags)
        ...
        State: N claims (R reinforced, V revised, C conceded), U unresolved open
        Trajectory: advancing → shifting → static

    Target: 300-400 tokens for 8 turns (~1200-1600 chars).

    Args:
        entries: Validated ledger entries (chronological order).
        cumulative: Pre-computed cumulative state.

    Returns:
        Multi-line summary string.
    """
    if not entries:
        return "Ledger: No turns completed.\nState: 0 claims, 0 unresolved open"

    lines: list[str] = []

    # Turn lines
    for entry in entries:
        lines.append(_format_turn_line(entry))

    # State line
    state_parts = [
        f"{cumulative.total_claims} claims",
        f"{cumulative.reinforced} reinforced",
        f"{cumulative.revised} revised",
        f"{cumulative.conceded} conceded",
    ]
    state_line = f"State: {', '.join(state_parts)}, {cumulative.unresolved_open} unresolved open"
    lines.append(state_line)

    # Trajectory line
    if cumulative.effective_delta_sequence:
        deltas = " → ".join(
            d.value for d in cumulative.effective_delta_sequence
        )
        lines.append(f"Trajectory: {deltas}")

    return "\n".join(lines)
```

**Step 3: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_control.py -v`
Expected: PASS (all TestConversationAction + TestComputeAction* + TestGenerateLedgerSummary* tests, ~35-40 tests)

**Step 4: Run full suite to verify no regressions**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All ~739 existing tests pass, plus all test_control.py tests.

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/control.py packages/context-injection/tests/test_control.py
git commit -m "feat(context-injection): add generate_ledger_summary for agent prompt injection (D3 Task 10)"
```

---

## D4: Schema 0.2.0 + Pipeline Integration

Concentrated integration delivery. Changes types, rewires pipeline, migrates tests. Five tasks: 11 (types), 12 (test shape), 13a (pipeline), 13b (execute), 14 (integration).

**Estimated:** ~50 new tests + ~739 updated
**Depends on:** D1 + D2 + D3 complete
**Risk:** HIGH — tightly coupled changes (see planning brief Section 3)

**Commit strategy:** Tasks 11+12 commit together (type changes + test helpers are inseparable). Tasks 13a, 13b, 14 each get their own commit.

### Task 11: TurnRequest/TurnPacket 0.2.0 types

**Files:**
- Modify: `context_injection/types.py`
- Modify: `tests/test_types.py`

This task changes the wire protocol types. TurnRequest gains ledger fields (position, claims, delta, tags, unresolved) and checkpoint fields, loses context_claims and evidence_history. TurnPacketSuccess gains validated_entry, warnings, cumulative state, action/summary, and checkpoint. ErrorDetail gains codes for ledger validation and checkpoint errors.

**Step 1: Write failing tests for new TurnRequest fields**

Add to `tests/test_types.py`:

```python
class TestTurnRequest020:
    """0.2.0 TurnRequest field changes."""

    def test_new_required_fields(self) -> None:
        """TurnRequest requires position, claims, delta, tags, unresolved."""
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Initial analysis",
            claims=[],
            delta="high",
            tags=["architecture"],
            unresolved=[],
        )
        assert request.position == "Initial analysis"
        assert request.claims == []
        assert request.delta == "high"
        assert request.tags == ["architecture"]
        assert request.unresolved == []

    def test_checkpoint_fields_optional(self) -> None:
        """Checkpoint fields default to None."""
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Initial analysis",
            claims=[],
            delta="high",
            tags=[],
            unresolved=[],
        )
        assert request.state_checkpoint is None
        assert request.checkpoint_id is None

    def test_checkpoint_fields_set(self) -> None:
        request = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=2,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Follow-up",
            claims=[],
            delta="medium",
            tags=[],
            unresolved=[],
            state_checkpoint='{"checkpoint_id":"abc"}',
            checkpoint_id="abc",
        )
        assert request.state_checkpoint == '{"checkpoint_id":"abc"}'
        assert request.checkpoint_id == "abc"

    def test_context_claims_removed(self) -> None:
        """context_claims field no longer accepted (extra=forbid)."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version=SCHEMA_VERSION,
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="high",
                tags=[],
                unresolved=[],
                context_claims=[],
            )

    def test_evidence_history_removed(self) -> None:
        """evidence_history field no longer accepted (extra=forbid)."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version=SCHEMA_VERSION,
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="high",
                tags=[],
                unresolved=[],
                evidence_history=[],
            )
```

Add tests for TurnPacketSuccess changes:

```python
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    ValidationWarning,
)


class TestTurnPacketSuccess020:
    """0.2.0 TurnPacketSuccess new fields."""

    def test_new_fields_present(self) -> None:
        """TurnPacketSuccess includes validated_entry, warnings, cumulative, action, checkpoint."""
        entry = LedgerEntry(
            position="test",
            claims=[],
            delta="high",
            tags=[],
            unresolved=[],
            counters=LedgerEntryCounters(
                new_claims=0, revised=0, conceded=0, unresolved_closed=0,
            ),
            quality="substantive",
            effective_delta="advancing",
            turn_number=1,
        )
        cumulative = CumulativeState(
            total_claims=0, reinforced=0, revised=0, conceded=0,
            unresolved_open=0, unresolved_closed=0, turns_completed=1,
            effective_delta_sequence=["advancing"],
        )
        packet = TurnPacketSuccess(
            schema_version=SCHEMA_VERSION,
            status="success",
            entities=[],
            path_decisions=[],
            template_candidates=[],
            budget=Budget(
                evidence_count=0, evidence_remaining=3,
                scout_available=True, budget_status="under_budget",
            ),
            deduped=[],
            validated_entry=entry,
            warnings=[],
            cumulative=cumulative,
            action="continue_dialogue",
            action_reason="Conversation active",
            ledger_summary="T1: test (advancing)\nState: 0 claims",
            state_checkpoint='{"checkpoint_id":"abc"}',
            checkpoint_id="abc",
        )
        assert packet.validated_entry == entry
        assert packet.warnings == []
        assert packet.cumulative == cumulative
        assert packet.action == "continue_dialogue"
        assert packet.checkpoint_id == "abc"


class TestErrorDetail020:
    """0.2.0 ErrorDetail new codes."""

    @pytest.mark.parametrize("code", [
        "ledger_hard_reject",
        "checkpoint_missing",
        "checkpoint_invalid",
        "checkpoint_stale",
    ])
    def test_new_error_codes_accepted(self, code: str) -> None:
        error = ErrorDetail(code=code, message="test")
        assert error.code == code

    def test_existing_codes_still_work(self) -> None:
        for code in ["invalid_schema_version", "missing_required_field",
                      "malformed_json", "internal_error"]:
            error = ErrorDetail(code=code, message="test")
            assert error.code == code
```

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestTurnRequest020 tests/test_types.py::TestTurnPacketSuccess020 tests/test_types.py::TestErrorDetail020 -v`
Expected: FAIL — fields don't exist yet

**Step 2: Write failing test for schema version change**

Add to `tests/test_types.py`:

```python
class TestSchemaVersion020:
    """Schema version updated to 0.2.0."""

    def test_schema_version_constant(self) -> None:
        assert SCHEMA_VERSION == "0.2.0"

    def test_valid_version_accepted(self) -> None:
        request = TurnRequest(
            schema_version="0.2.0",
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="test",
            claims=[],
            delta="high",
            tags=[],
            unresolved=[],
        )
        assert request.schema_version == "0.2.0"

    def test_old_version_rejected(self) -> None:
        """0.1.0 is no longer valid."""
        with pytest.raises(ValidationError):
            TurnRequest(
                schema_version="0.1.0",
                turn_number=1,
                conversation_id="conv_1",
                focus=Focus(text="test", claims=[], unresolved=[]),
                posture="exploratory",
                position="test",
                claims=[],
                delta="high",
                tags=[],
                unresolved=[],
            )
```

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestSchemaVersion020 -v`
Expected: FAIL

**Step 3: Implement type changes**

Modify `context_injection/types.py`:

1. Update schema version:
```python
SchemaVersionLiteral = Literal["0.2.0"]
SCHEMA_VERSION: SchemaVersionLiteral = "0.2.0"
```

2. Update TurnRequest — add new fields, remove old:
```python
class TurnRequest(ProtocolModel):
    """Call 1 input: agent sends focus-scoped ledger data."""

    schema_version: SchemaVersionLiteral
    turn_number: int
    conversation_id: str
    focus: Focus
    posture: Literal["adversarial", "collaborative", "exploratory", "evaluative"]

    # --- 0.2.0: Ledger fields (top-level for validation) ---
    position: str
    claims: list[Claim]
    delta: str
    tags: list[str]
    unresolved: list[Unresolved]

    # --- 0.2.0: Checkpoint fields (optional — absent on turn 1) ---
    state_checkpoint: str | None = None
    checkpoint_id: str | None = None
```

Note: `context_claims` and `evidence_history` are REMOVED (not defaulted). Since ProtocolModel uses `extra="forbid"`, sending them will error.

3. Update ErrorDetail — add new codes:
```python
class ErrorDetail(ProtocolModel):
    """Error details in a TurnPacket error response."""

    code: Literal[
        "invalid_schema_version",
        "missing_required_field",
        "malformed_json",
        "internal_error",
        "ledger_hard_reject",
        "checkpoint_missing",
        "checkpoint_invalid",
        "checkpoint_stale",
    ]
    message: str
    details: dict | None = None
```

4. Update TurnPacketSuccess — add new fields:
```python
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    ValidationWarning,
)

class TurnPacketSuccess(ProtocolModel):
    """Successful TurnPacket response."""

    schema_version: SchemaVersionLiteral
    status: Literal["success"]
    entities: list[Entity]
    path_decisions: list[PathDecision]
    template_candidates: list[TemplateCandidate]
    budget: Budget
    deduped: list[DedupRecord]

    # --- 0.2.0: Ledger validation results ---
    validated_entry: LedgerEntry
    warnings: list[ValidationWarning]
    cumulative: CumulativeState

    # --- 0.2.0: Conversation control ---
    action: str
    action_reason: str
    ledger_summary: str

    # --- 0.2.0: Checkpoint ---
    state_checkpoint: str
    checkpoint_id: str
```

**Step 4: Run new type tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestTurnRequest020 tests/test_types.py::TestTurnPacketSuccess020 tests/test_types.py::TestErrorDetail020 tests/test_types.py::TestSchemaVersion020 -v`
Expected: PASS

**Step 5: Update existing version validation tests**

In `tests/test_types.py`, find existing tests that use `"0.2.0"` as an invalid version. Change the invalid version string from `"0.2.0"` to `"0.3.0"`. The test asserting `"0.1.0"` is valid should now assert it's invalid — but this is already covered by `TestSchemaVersion020.test_old_version_rejected`. Update the existing test to use `"0.3.0"` as the invalid version.

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: PASS (all type tests). Many other test files will now FAIL because they still construct TurnRequest with old fields — that's expected and fixed in Task 12.

---

### Task 12: Test shape migration

**Scope:** Mechanical changes ONLY — update request builders, version literals, and response field access. Semantic test rewrites (assertions about pipeline behavior that changed) go in Task 13a.

**Files:**
- Modify: `tests/test_pipeline.py` (`_make_turn_request` + callers)
- Modify: `tests/test_templates.py` (`_make_turn_request` + callers)
- Modify: `tests/test_execute.py` (TurnRequest construction)
- Modify: `tests/test_state.py` (`_make_turn_request` + callers)
- Modify: `tests/test_integration.py` (4 `TurnRequest.model_validate()` calls)

**Step 1: Update `_make_turn_request` in test_pipeline.py**

Current helper (line 34):
```python
def _make_turn_request(**overrides: Any) -> TurnRequest:
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=[], unresolved=[]),
        "context_claims": [],
        "evidence_history": [],
        "posture": "exploratory",
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)
```

Updated helper:
```python
def _make_turn_request(**overrides: Any) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=[], unresolved=[]),
        "posture": "exploratory",
        # 0.2.0 ledger fields
        "position": "Test position",
        "claims": [],
        "delta": "medium",
        "tags": ["test"],
        "unresolved": [],
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)
```

Then update callers that passed `context_claims=` or `evidence_history=` overrides:
- `context_claims=[...]` → remove (cumulative claims now come from ConversationState — semantic change handled in Task 13a)
- `evidence_history=[...]` → remove (evidence now comes from ConversationState — semantic change handled in Task 13a)

**Step 2: Update `_make_turn_request` in test_templates.py**

Current helper (line 42):
```python
def _make_turn_request(
    conversation_id: str = "conv_1",
    turn_number: int = 1,
    evidence_history: list[EvidenceRecord] | None = None,
) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        evidence_history=evidence_history or [],
        posture="exploratory",
    )
```

Updated helper:
```python
def _make_turn_request(
    conversation_id: str = "conv_1",
    turn_number: int = 1,
) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        posture="exploratory",
        position="Test position",
        claims=[],
        delta="medium",
        tags=["test"],
        unresolved=[],
    )
```

Update callers that pass `evidence_history=`: remove the argument. The evidence source migrates to ConversationState in Task 13a.

**Step 3: Update `_make_turn_request` in test_state.py**

Current helper (line 30):
```python
def _make_turn_request(
    conversation_id: str = "conv_1", turn_number: int = 1
) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        evidence_history=[],
        posture="exploratory",
    )
```

Updated helper:
```python
def _make_turn_request(
    conversation_id: str = "conv_1", turn_number: int = 1,
) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        posture="exploratory",
        position="Test position",
        claims=[],
        delta="medium",
        tags=["test"],
        unresolved=[],
    )
```

**Step 4: Update TurnRequest construction in test_execute.py**

test_execute.py doesn't have a `_make_turn_request` helper — it constructs TurnRequest inline in test setup. Find all `TurnRequest(` constructors and add the new required fields, remove `context_claims` and `evidence_history`.

Pattern for each TurnRequest constructor:
```python
# Old:
TurnRequest(
    schema_version=SCHEMA_VERSION,
    turn_number=1,
    conversation_id="conv_1",
    focus=Focus(text="test", claims=[...], unresolved=[...]),
    context_claims=[...],
    evidence_history=[...],
    posture="exploratory",
)

# New — add 0.2.0 fields, remove old fields:
TurnRequest(
    schema_version=SCHEMA_VERSION,
    turn_number=1,
    conversation_id="conv_1",
    focus=Focus(text="test", claims=[...], unresolved=[...]),
    posture="exploratory",
    position="Test position",
    claims=[...],         # same claims as focus.claims (or appropriate defaults)
    delta="medium",
    tags=["test"],
    unresolved=[...],     # same as focus.unresolved (or appropriate defaults)
)
```

**Step 5: Update test_integration.py model_validate calls**

Four `TurnRequest.model_validate()` calls at lines 32, 191, 262, 317. Each needs:
1. Add: `"position"`, `"claims"`, `"delta"`, `"tags"`, `"unresolved"` keys
2. Remove: `"context_claims"`, `"evidence_history"` keys

Example (line 32 call):
```python
# Old:
request = TurnRequest.model_validate({
    "schema_version": SCHEMA_VERSION,
    "turn_number": 3,
    "conversation_id": "conv_abc123",
    "focus": { ... },
    "context_claims": [...],
    "evidence_history": [...],
    "posture": "collaborative",
})

# New:
request = TurnRequest.model_validate({
    "schema_version": SCHEMA_VERSION,
    "turn_number": 3,
    "conversation_id": "conv_abc123",
    "focus": { ... },
    "posture": "collaborative",
    "position": "Whether the project uses YAML or TOML for configuration",
    "claims": [
        {"text": "The project uses settings.yaml", "status": "new", "turn": 3},
        {"text": "YAML chosen over TOML", "status": "new", "turn": 3},
    ],
    "delta": "high",
    "tags": ["configuration"],
    "unresolved": [
        {"text": "Whether config.yaml is the only config file", "turn": 3},
    ],
})
```

Repeat for all 4 calls. Keep focus unchanged (it still carries the full text + nested claims/unresolved for entity extraction). The new top-level fields carry the same data in a flat structure for ledger validation.

**Step 6: Update TurnPacketSuccess assertions in tests**

Tests that assert on TurnPacketSuccess fields need updating. The response now includes additional fields. For mechanical migration, tests that check `result.entities`, `result.path_decisions`, etc. don't need changes — those fields still exist. Tests that construct TurnPacketSuccess directly (if any) need the new fields added.

Focus on making the TurnRequest construction compile. Pipeline semantic tests that will fail because the pipeline doesn't yet produce the new response fields are deferred to Task 13a.

**Step 7: Run tests to assess migration state**

Run: `cd packages/context-injection && uv run pytest tests/ -v 2>&1 | tail -30`

Expected: Many tests pass (request construction now works). Some tests FAIL — these are semantic failures where:
- Pipeline tests assert old behavior (e.g., `context_claims` entity extraction)
- Pipeline doesn't yet produce new TurnPacketSuccess fields (validated_entry, etc.)
- Execute tests reference `evidence_history` from stored request

Count failures and categorize: shape failures (Task 12 missed something) vs semantic failures (Task 13a/13b scope). Fix any remaining shape failures.

**Step 8: Commit Tasks 11+12 together**

```bash
git add packages/context-injection/context_injection/types.py packages/context-injection/tests/test_types.py packages/context-injection/tests/test_pipeline.py packages/context-injection/tests/test_templates.py packages/context-injection/tests/test_execute.py packages/context-injection/tests/test_state.py packages/context-injection/tests/test_integration.py
git commit -m "feat(context-injection): update wire types to 0.2.0 schema + migrate test helpers (D4 Tasks 11-12)

TurnRequest: add position, claims, delta, tags, unresolved, checkpoint fields; remove context_claims, evidence_history.
TurnPacketSuccess: add validated_entry, warnings, cumulative, action, ledger_summary, checkpoint fields.
ErrorDetail: add ledger_hard_reject, checkpoint_missing, checkpoint_invalid, checkpoint_stale codes.

Tests compile but some semantic failures expected until pipeline rewiring (Task 13a)."
```

---

### Task 13a: Pipeline rewiring + semantic test migration

**Files:**
- Modify: `context_injection/pipeline.py`
- Modify: `tests/test_pipeline.py` (ConversationState setup + semantic test rewrites)
- Modify: `tests/test_integration.py` (process-turn semantic tests)

Pipeline signature unchanged: `process_turn(request: TurnRequest, ctx: AppContext) -> TurnPacketSuccess | TurnPacketError`. The pipeline resolves conversation state via `ctx.get_or_create_conversation(request.conversation_id)` internally.

**Step 1: Write failing tests for new pipeline behavior**

Add to `tests/test_pipeline.py`:

```python
from context_injection.checkpoint import CheckpointError
from context_injection.conversation import ConversationState
from context_injection.control import ConversationAction
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    ValidationWarning,
)


class TestPipelineConversationState:
    """Pipeline resolves and updates ConversationState."""

    def test_first_turn_creates_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_new")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "conv_new" in ctx.conversations

    def test_conversation_persists_across_turns(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_multi", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Pass checkpoint back
        r2 = _make_turn_request(
            conversation_id="conv_multi",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2


class TestPipelineLedgerValidation:
    """Pipeline validates ledger entry and returns it."""

    def test_success_includes_validated_entry(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(
            position="Auth module analysis",
            claims=[Claim(text="JWT is used", status="new", turn=1)],
            delta="high",
            tags=["architecture"],
        )
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.validated_entry.position == "Auth module analysis"
        assert result.validated_entry.turn_number == 1
        assert len(result.validated_entry.claims) == 1

    def test_hard_reject_returns_error(self) -> None:
        """Empty position should hard reject."""
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(position="")
        result = process_turn(request, ctx)
        assert result.status == "error"
        assert result.error.code == "ledger_hard_reject"


class TestPipelineActionComputation:
    """Pipeline computes action from conversation trajectory."""

    def test_first_turn_continues(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.action == ConversationAction.CONTINUE_DIALOGUE

    def test_action_reason_nonempty(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert len(result.action_reason) > 0


class TestPipelineCheckpoint:
    """Pipeline serializes and returns checkpoint."""

    def test_checkpoint_returned(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.state_checkpoint is not None
        assert result.checkpoint_id is not None
        assert len(result.checkpoint_id) > 0

    def test_checkpoint_id_stored_in_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_ckpt")
        result = process_turn(request, ctx)
        assert result.status == "success"
        conv = ctx.conversations["conv_ckpt"]
        assert conv.last_checkpoint_id == result.checkpoint_id


class TestPipelineLedgerSummary:
    """Pipeline generates ledger summary."""

    def test_summary_included(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(position="Test analysis")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "T1:" in result.ledger_summary
        assert "Test analysis" in result.ledger_summary


class TestPipelineCumulativeClaims:
    """Pipeline uses cumulative claims from ConversationState (replaces context_claims)."""

    def test_prior_claims_extracted_as_out_of_focus(self) -> None:
        """Claims from prior turns should be extracted as out-of-focus entities."""
        ctx = _make_ctx(git_files={"src/app.py"})

        # Turn 1: claim mentions src/app.py
        r1 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=1,
            claims=[Claim(text="The file src/app.py has the logic", status="new", turn=1)],
            position="Initial review",
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Turn 2: new focus, no mention of src/app.py — but prior claim should extract it
        r2 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=2,
            claims=[Claim(text="New claim about something else", status="new", turn=2)],
            position="Follow-up analysis",
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        # Prior claim entity should appear as out-of-focus
        out_of_focus = [e for e in result2.entities if not e.in_focus]
        file_entities = [e for e in out_of_focus if e.canonical == "src/app.py"]
        assert len(file_entities) > 0, "Prior claim's file entity should be extracted out-of-focus"


class TestPipelinePriorEvidence:
    """Pipeline uses evidence from ConversationState (replaces request.evidence_history)."""

    def test_evidence_from_conversation_used_for_dedup(self) -> None:
        """Evidence recorded in ConversationState should deduplicate templates."""
        ctx = _make_ctx(git_files={"src/app.py"})

        # Seed conversation with evidence record
        from context_injection.types import EvidenceRecord
        conv = ctx.get_or_create_conversation("conv_evidence")
        conv = conv.with_evidence(
            EvidenceRecord(
                entity_key="src/app.py",
                template_id="clarify.file_path",
                turn=1,
            ),
        )
        ctx.conversations["conv_evidence"] = conv

        # Turn 2: mention src/app.py again — should be deduped
        r2 = _make_turn_request(
            conversation_id="conv_evidence",
            turn_number=2,
            claims=[Claim(text="Check src/app.py", status="new", turn=2)],
            position="Second review",
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        # The src/app.py entity should be deduped
        deduped_keys = [d.entity_key for d in result2.deduped]
        assert "src/app.py" in deduped_keys
```

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelineConversationState -v`
Expected: FAIL — pipeline doesn't resolve ConversationState yet

**Step 2: Rewrite `_process_turn_inner` to 18-step pipeline**

Replace the body of `_process_turn_inner` in `context_injection/pipeline.py`:

```python
"""Call 1 pipeline: TurnRequest -> TurnPacketSuccess | TurnPacketError.

Composes the full v0.2.0 processing pipeline:
 1. Schema version validation
 2. Resolve ConversationState
 3. Checkpoint intake
 4. Snapshot prior state (claims + evidence)
 5. Entity extraction from focus + prior claims
 6. Path checking for Tier 1 file entities
 7. Template matching with prior evidence
 8. Budget computation from prior evidence
 9. Ledger entry validation
10. Build provisional state
11. Compute cumulative state, action, reason
12. Closing probe projection
13. Serialize checkpoint
14. Generate ledger summary
15. Record checkpoint ID in projected state
16. Store TurnRequestRecord for Call 2
17. Commit projected state
18. Return TurnPacketSuccess

Contract reference: docs/references/context-injection-contract.md
"""

from __future__ import annotations

import logging

from context_injection.checkpoint import (
    CheckpointError,
    compact_ledger,
    serialize_checkpoint,
    validate_checkpoint_intake,
)
from context_injection.control import compute_action, generate_ledger_summary
from context_injection.entities import extract_entities
from context_injection.ledger import validate_ledger_entry
from context_injection.paths import check_path_compile_time
from context_injection.state import (
    AppContext,
    TurnRequestRecord,
    make_turn_request_ref,
)
from context_injection.templates import compute_budget, match_templates
from context_injection.types import (
    SCHEMA_VERSION,
    Claim,
    Entity,
    ErrorDetail,
    PathDecision,
    TurnPacketError,
    TurnPacketSuccess,
    TurnRequest,
)

logger = logging.getLogger(__name__)

_PATH_CHECK_TYPES: frozenset[str] = frozenset({"file_loc", "file_path", "file_name"})


def process_turn(
    request: TurnRequest,
    ctx: AppContext,
) -> TurnPacketSuccess | TurnPacketError:
    """Process a Call 1 TurnRequest through the full pipeline."""
    try:
        return _process_turn_inner(request, ctx)
    except CheckpointError as exc:
        logger.warning("Checkpoint error: %s (code=%s)", exc, exc.code)
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(code=exc.code, message=str(exc)),
        )
    except Exception as exc:
        logger.exception("process_turn failed: %s", exc)
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="internal_error",
                message=f"process_turn failed: {exc}",
            ),
        )


def _process_turn_inner(
    request: TurnRequest,
    ctx: AppContext,
) -> TurnPacketSuccess | TurnPacketError:
    """Inner pipeline logic — 18-step orchestration."""

    # --- Step 1: Schema version validation ---
    if request.schema_version != SCHEMA_VERSION:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="invalid_schema_version",
                message=(
                    f"Expected schema_version={SCHEMA_VERSION!r}, "
                    f"got {request.schema_version!r}"
                ),
            ),
        )

    # --- Step 2: Resolve ConversationState ---
    base = ctx.get_or_create_conversation(request.conversation_id)

    # --- Step 3: Checkpoint intake ---
    base = validate_checkpoint_intake(
        in_memory=base,
        checkpoint_id=request.checkpoint_id,
        checkpoint_payload=request.state_checkpoint,
        turn_number=request.turn_number,
    )

    # --- Step 4: Snapshot prior state ---
    prior_claims: list[Claim] = base.get_cumulative_claims()
    prior_evidence = base.get_evidence_history()

    # --- Step 5: Entity extraction ---
    entities: list[Entity] = []

    for claim in request.focus.claims:
        entities.extend(
            extract_entities(
                claim.text,
                source_type="claim",
                in_focus=True,
                ctx=ctx,
            )
        )

    for unresolved_item in request.focus.unresolved:
        entities.extend(
            extract_entities(
                unresolved_item.text,
                source_type="unresolved",
                in_focus=True,
                ctx=ctx,
            )
        )

    for claim in prior_claims:
        entities.extend(
            extract_entities(
                claim.text,
                source_type="claim",
                in_focus=False,
                ctx=ctx,
            )
        )

    # --- Step 6: Path checking ---
    path_decisions: list[PathDecision] = []

    for entity in entities:
        if entity.tier != 1:
            continue
        if entity.type not in _PATH_CHECK_TYPES:
            continue

        result = check_path_compile_time(
            entity.canonical,
            repo_root=ctx.repo_root,
            git_files=ctx.git_files,
        )

        path_decisions.append(
            PathDecision(
                entity_id=entity.id,
                status=result.status,
                user_rel=result.user_rel,
                resolved_rel=result.resolved_rel,
                risk_signal=result.risk_signal,
                deny_reason=result.deny_reason,
                candidates=result.candidates,
                unresolved_reason=result.unresolved_reason,
            )
        )

    # --- Step 7: Template matching (with prior evidence) ---
    template_candidates, dedup_records, spec_registry = match_templates(
        entities,
        path_decisions,
        prior_evidence,
        request,
        ctx,
    )

    # --- Step 8: Budget computation (from prior evidence) ---
    budget = compute_budget(prior_evidence)

    # --- Step 9: Ledger entry validation ---
    prior_cumulative = base.compute_cumulative_state() if base.entries else None
    validated_entry, warnings = validate_ledger_entry(
        position=request.position,
        claims=request.claims,
        delta=request.delta,
        tags=request.tags,
        unresolved=request.unresolved,
        turn_number=request.turn_number,
        prior_cumulative=prior_cumulative,
    )

    # Check for hard reject
    hard_rejects = [w for w in warnings if w.tier == "hard_reject"]
    if hard_rejects:
        return TurnPacketError(
            schema_version=SCHEMA_VERSION,
            status="error",
            error=ErrorDetail(
                code="ledger_hard_reject",
                message=hard_rejects[0].message,
                details={"field": hard_rejects[0].field},
            ),
        )

    # --- Step 10: Build provisional state ---
    provisional = base.with_turn(validated_entry)

    # --- Step 11: Compute cumulative, action, reason ---
    cumulative = provisional.compute_cumulative_state()
    action, action_reason = compute_action(
        entries=provisional.entries,
        budget_remaining=budget.evidence_remaining,
        closing_probe_fired=provisional.closing_probe_fired,
    )

    # --- Step 12: Closing probe projection ---
    if action == "closing_probe":
        projected = provisional.with_closing_probe_fired()
    else:
        projected = provisional

    # --- Step 13: Serialize checkpoint ---
    projected = compact_ledger(projected)
    checkpoint_id, checkpoint_string = serialize_checkpoint(
        state=projected,
        parent_id=base.last_checkpoint_id,
    )

    # --- Step 14: Generate ledger summary ---
    ledger_summary = generate_ledger_summary(
        entries=projected.entries,
        cumulative=cumulative,
    )

    # --- Step 15: Record checkpoint ID ---
    projected = projected.with_checkpoint_id(checkpoint_id)

    # --- Step 16: Store TurnRequestRecord for Call 2 ---
    ref = make_turn_request_ref(request)
    record = TurnRequestRecord(
        turn_request=request,
        scout_options=spec_registry,
    )
    ctx.store_record(ref, record)

    # --- Step 17: Commit projected state ---
    ctx.conversations[request.conversation_id] = projected

    # --- Step 18: Return TurnPacketSuccess ---
    return TurnPacketSuccess(
        schema_version=SCHEMA_VERSION,
        status="success",
        entities=entities,
        path_decisions=path_decisions,
        template_candidates=template_candidates,
        budget=budget,
        deduped=dedup_records,
        validated_entry=validated_entry,
        warnings=warnings,
        cumulative=cumulative,
        action=action,
        action_reason=action_reason,
        ledger_summary=ledger_summary,
        state_checkpoint=checkpoint_string,
        checkpoint_id=checkpoint_id,
    )
```

**Step 3: Update semantic tests in test_pipeline.py**

Identify tests that assert on the old `context_claims`-based entity extraction. These need to be rewritten to set up ConversationState with prior claims instead:

Old pattern:
```python
def test_entities_extracted_from_context_claims(self):
    request = _make_turn_request(
        context_claims=[Claim(text="File src/app.py has logic", status="new", turn=1)],
    )
    result = process_turn(request, ctx)
    # assert on entities...
```

New pattern:
```python
def test_prior_claims_extracted_as_out_of_focus(self):
    ctx = _make_ctx(git_files={"src/app.py"})
    # Seed conversation with a prior turn's claims
    conv = ctx.get_or_create_conversation("conv_test")
    conv = conv.with_turn(LedgerEntry(
        position="Prior analysis",
        claims=[Claim(text="File src/app.py has logic", status="new", turn=1)],
        delta="medium", tags=["test"], unresolved=[],
        counters=LedgerEntryCounters(new_claims=1, revised=0, conceded=0, unresolved_closed=0),
        quality="substantive", effective_delta="advancing", turn_number=1,
    ))
    conv = conv.with_checkpoint_id("prior_ckpt")
    ctx.conversations["conv_test"] = conv

    request = _make_turn_request(
        conversation_id="conv_test",
        turn_number=2,
        checkpoint_id="prior_ckpt",
    )
    result = process_turn(request, ctx)
    # assert on out-of-focus entities...
```

Similarly, tests referencing `evidence_history` for template dedup or budget need to set up ConversationState with evidence records.

**Step 4: Update semantic tests in test_integration.py**

Integration tests that passed `evidence_history` or `context_claims` in request dicts and asserted on dedup/budget behavior need rewriting. The request dict no longer has these fields — the data comes from ConversationState.

For tests that previously tested "first turn with no history," little changes — the ConversationState is fresh. For tests that tested "turn with prior evidence," set up the conversation's evidence_history via `with_evidence()` before calling `process_turn`.

**Step 5: Run full test suite**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: Most tests pass. Remaining failures should be in test_execute.py (evidence source — Task 13b scope).

**Step 6: Fix any remaining test failures in pipeline/integration scope**

Iterate: run tests, identify failures, fix. Each fix should be small (field name changes, assertion updates). If a failure is in execute scope, leave it for Task 13b.

**Step 7: Run full suite to verify pipeline scope is green**

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py tests/test_integration.py tests/test_types.py tests/test_state.py tests/test_templates.py -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add packages/context-injection/context_injection/pipeline.py packages/context-injection/tests/test_pipeline.py packages/context-injection/tests/test_integration.py
git commit -m "feat(context-injection): rewrite pipeline to 18-step 0.2.0 flow with conversation state (D4 Task 13a)

Pipeline resolves ConversationState internally. Entity extraction uses cumulative claims
from conversation (replaces context_claims). Template matching and budget use evidence
from conversation (replaces evidence_history). Ledger validation, action computation,
checkpoint serialization, and summary generation integrated."
```

---

### Task 13b: Execute rewiring

**Files:**
- Modify: `context_injection/execute.py`
- Modify: `tests/test_execute.py`

Execute changes: `execute_scout` gets evidence count from ConversationState instead of `record.turn_request.evidence_history`. After successful scout execution, records evidence in ConversationState.

**Step 1: Write failing tests for evidence-from-conversation**

Add to `tests/test_execute.py`:

```python
from context_injection.conversation import ConversationState
from context_injection.types import EvidenceRecord


class TestExecuteEvidenceFromConversation:
    """execute_scout uses ConversationState for evidence count."""

    def test_budget_reflects_conversation_evidence(self, tmp_path: Path) -> None:
        """Evidence count comes from conversation state, not request."""
        # Set up ctx with a file
        (tmp_path / "src" / "app.py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("def hello(): pass")
        ctx = AppContext.create(
            repo_root=str(tmp_path),
            git_files={"src/app.py"},
        )

        # Seed conversation with 2 prior evidence records
        conv = ctx.get_or_create_conversation("conv_budget")
        conv = conv.with_evidence(
            EvidenceRecord(entity_key="file1.py", template_id="clarify.file_path", turn=1),
        )
        conv = conv.with_evidence(
            EvidenceRecord(entity_key="file2.py", template_id="clarify.file_path", turn=1),
        )
        ctx.conversations["conv_budget"] = conv

        # Process turn 1 to create a scout option
        request = _make_turn_request(
            conversation_id="conv_budget",
            claims=[Claim(text="Check src/app.py", status="new", turn=1)],
        )
        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Execute a scout — budget should reflect 2 prior + 1 new = 3
        if turn_result.template_candidates:
            scout_req = ScoutRequest(
                schema_version=SCHEMA_VERSION,
                scout_option_id=turn_result.template_candidates[0].scout_option_id,
                scout_token=turn_result.template_candidates[0].scout_token,
                turn_request_ref=turn_result.template_candidates[0].turn_request_ref,
            )
            scout_result = execute_scout(scout_req, ctx)
            # Budget should show 3 evidence items (2 prior + 1 new)
            assert scout_result.budget.evidence_count == 3

    def test_evidence_recorded_after_success(self, tmp_path: Path) -> None:
        """Successful scout execution records evidence in ConversationState."""
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "src" / "app.py").write_text("def hello(): pass")
        ctx = AppContext.create(
            repo_root=str(tmp_path),
            git_files={"src/app.py"},
        )

        # Process turn
        request = _make_turn_request(
            conversation_id="conv_record",
            claims=[Claim(text="Check src/app.py", status="new", turn=1)],
        )
        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Execute scout
        if turn_result.template_candidates:
            scout_req = ScoutRequest(
                schema_version=SCHEMA_VERSION,
                scout_option_id=turn_result.template_candidates[0].scout_option_id,
                scout_token=turn_result.template_candidates[0].scout_token,
                turn_request_ref=turn_result.template_candidates[0].turn_request_ref,
            )
            scout_result = execute_scout(scout_req, ctx)

            # Conversation should now have evidence
            conv = ctx.conversations["conv_record"]
            evidence = conv.get_evidence_history()
            assert len(evidence) >= 1
```

Run: `cd packages/context-injection && uv run pytest tests/test_execute.py::TestExecuteEvidenceFromConversation -v`
Expected: FAIL — execute_scout still reads from request.evidence_history

**Step 2: Implement execute changes**

Modify `context_injection/execute.py`:

1. In `execute_scout` function (around line 525), change evidence source:

```python
# Old (line 525):
evidence_history_len = len(record.turn_request.evidence_history)

# New:
conversation = ctx.get_or_create_conversation(record.turn_request.conversation_id)
evidence_history_len = len(conversation.get_evidence_history())
```

2. After successful scout execution, record evidence in conversation state. Add after the scout dispatch (after the `execute_read` / `execute_grep` call returns):

```python
# After scout execution, record evidence if successful
if isinstance(scout_result, ScoutResultSuccess):
    conversation = ctx.get_or_create_conversation(record.turn_request.conversation_id)
    conversation = conversation.with_evidence(
        EvidenceRecord(
            entity_key=option.entity_key,
            template_id=option.template_id,
            turn=record.turn_request.turn_number,
        ),
    )
    ctx.conversations[record.turn_request.conversation_id] = conversation
```

3. Add necessary imports:

```python
from context_injection.conversation import ConversationState
from context_injection.types import EvidenceRecord
```

**Step 3: Update existing execute tests**

Tests that previously relied on `evidence_history` in the stored request for budget calculations need updating. The evidence now comes from ConversationState. For tests that check budget values:

- If test had `evidence_history=[]` (most tests): budget should be 0 → still works because ConversationState starts empty
- If test had `evidence_history=[...]` with records: seed the ConversationState with matching evidence records

**Step 4: Run execute tests**

Run: `cd packages/context-injection && uv run pytest tests/test_execute.py -v`
Expected: PASS

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All tests pass (pipeline + execute both rewired)

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/execute.py packages/context-injection/tests/test_execute.py
git commit -m "feat(context-injection): rewire execute_scout to use ConversationState for evidence (D4 Task 13b)

Evidence count sourced from conversation.get_evidence_history() instead of
request.evidence_history. Successful scout execution records evidence via
conversation.with_evidence()."
```

---

### Task 14: Integration tests + protocol contract

**Files:**
- Modify: `tests/test_integration.py`
- Modify: `docs/references/context-injection-contract.md`

New integration tests verify the complete 0.2.0 flow end-to-end: Call 1 → Call 2 round-trip with ledger validation, multi-turn conversation with cumulative state, checkpoint pass-through, and action flow.

**Step 1: Write new 0.2.0 integration tests**

Add to `tests/test_integration.py`:

```python
from context_injection.control import ConversationAction
from context_injection.enums import EffectiveDelta


class TestIntegration020RoundTrip:
    """Full 0.2.0 Call 1 → Call 2 round trip."""

    def test_call1_returns_ledger_entry(self, tmp_path: Path) -> None:
        """Process turn returns validated ledger entry with all fields."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "config.py").write_text("DB_URL = 'postgres://...'")
        git_files = {"src/config.py"}
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_020",
            "focus": {
                "text": "Database configuration approach",
                "claims": [
                    {"text": "Project uses src/config.py for DB config", "status": "new", "turn": 1},
                ],
                "unresolved": [],
            },
            "posture": "collaborative",
            "position": "Database configuration analysis",
            "claims": [
                {"text": "Project uses src/config.py for DB config", "status": "new", "turn": 1},
            ],
            "delta": "high",
            "tags": ["configuration", "database"],
            "unresolved": [],
        })

        result = process_turn(request, ctx)
        assert result.status == "success"

        # Ledger entry
        assert result.validated_entry.position == "Database configuration analysis"
        assert result.validated_entry.turn_number == 1
        assert result.validated_entry.effective_delta in set(EffectiveDelta)

        # Cumulative state
        assert result.cumulative.turns_completed == 1
        assert result.cumulative.total_claims == 1

        # Action
        assert result.action == ConversationAction.CONTINUE_DIALOGUE
        assert len(result.action_reason) > 0

        # Checkpoint
        assert result.checkpoint_id is not None
        assert result.state_checkpoint is not None

        # Summary
        assert "T1:" in result.ledger_summary

    def test_call1_then_call2_round_trip(self, tmp_path: Path) -> None:
        """Full round-trip: Call 1 → get scout → Call 2 → execute scout."""
        (tmp_path / "main.py").write_text("def main():\n    print('hello')\n")
        git_files = {"main.py"}
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

        # Call 1
        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_roundtrip",
            "focus": {
                "text": "Main entry point",
                "claims": [
                    {"text": "main.py is the entry point", "status": "new", "turn": 1},
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
            "position": "Entry point analysis",
            "claims": [
                {"text": "main.py is the entry point", "status": "new", "turn": 1},
            ],
            "delta": "high",
            "tags": ["architecture"],
            "unresolved": [],
        })

        turn_result = process_turn(request, ctx)
        assert turn_result.status == "success"

        # Call 2 (if scout available)
        if turn_result.template_candidates:
            candidate = turn_result.template_candidates[0]
            scout_req = ScoutRequest(
                schema_version=SCHEMA_VERSION,
                scout_option_id=candidate.scout_option_id,
                scout_token=candidate.scout_token,
                turn_request_ref=candidate.turn_request_ref,
            )
            scout_result = execute_scout(scout_req, ctx)
            assert scout_result.status == "success"


class TestIntegration020MultiTurn:
    """Multi-turn conversation with state progression."""

    def test_two_turn_conversation(self, tmp_path: Path) -> None:
        """Second turn sees cumulative state from first turn."""
        (tmp_path / "app.py").write_text("x = 1")
        ctx = AppContext.create(repo_root=str(tmp_path), git_files={"app.py"})

        # Turn 1
        r1 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_multi",
            "focus": {"text": "App analysis", "claims": [
                {"text": "app.py contains state", "status": "new", "turn": 1},
            ], "unresolved": []},
            "posture": "exploratory",
            "position": "Initial app review",
            "claims": [{"text": "app.py contains state", "status": "new", "turn": 1}],
            "delta": "high",
            "tags": ["architecture"],
            "unresolved": [],
        })
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"
        assert result1.cumulative.turns_completed == 1

        # Turn 2 — pass checkpoint back
        r2 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 2,
            "conversation_id": "conv_multi",
            "focus": {"text": "Follow-up", "claims": [
                {"text": "app.py contains state", "status": "reinforced", "turn": 2},
            ], "unresolved": []},
            "posture": "collaborative",
            "position": "Confirmed app structure",
            "claims": [{"text": "app.py contains state", "status": "reinforced", "turn": 2}],
            "delta": "low",
            "tags": ["architecture"],
            "unresolved": [],
            "state_checkpoint": result1.state_checkpoint,
            "checkpoint_id": result1.checkpoint_id,
        })
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2
        assert result2.cumulative.reinforced >= 1

    def test_checkpoint_missing_on_turn2_without_state(self, tmp_path: Path) -> None:
        """Turn 2 without checkpoint or in-memory state → error."""
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=set())

        # Skip turn 1 — go straight to turn 2 without checkpoint
        r2 = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 2,
            "conversation_id": "conv_no_state",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "test",
            "claims": [],
            "delta": "medium",
            "tags": [],
            "unresolved": [],
        })
        result = process_turn(r2, ctx)
        assert result.status == "error"
        assert result.error.code == "checkpoint_missing"


class TestIntegration020ActionFlow:
    """Action computation in integration context."""

    def test_continue_on_first_turn(self, tmp_path: Path) -> None:
        ctx = AppContext.create(repo_root=str(tmp_path), git_files=set())
        request = TurnRequest.model_validate({
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_action",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "Initial analysis",
            "claims": [],
            "delta": "high",
            "tags": ["test"],
            "unresolved": [],
        })
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.action == ConversationAction.CONTINUE_DIALOGUE
```

Run: `cd packages/context-injection && uv run pytest tests/test_integration.py::TestIntegration020RoundTrip tests/test_integration.py::TestIntegration020MultiTurn tests/test_integration.py::TestIntegration020ActionFlow -v`
Expected: PASS (pipeline already rewired in Task 13a)

**Step 2: Update protocol contract**

Update `docs/references/context-injection-contract.md` to reflect 0.2.0 schema:

1. Update schema version from `0.1.0` to `0.2.0`
2. Add TurnRequest new fields: `position`, `claims`, `delta`, `tags`, `unresolved`, `state_checkpoint`, `checkpoint_id`
3. Document removed fields: `context_claims`, `evidence_history`
4. Add TurnPacketSuccess new fields: `validated_entry`, `warnings`, `cumulative`, `action`, `action_reason`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`
5. Add new ErrorDetail codes: `ledger_hard_reject`, `checkpoint_missing`, `checkpoint_invalid`, `checkpoint_stale`
6. Add conversation flow section: checkpoint pass-through, multi-turn state progression, action computation

**Step 3: Run full suite — final verification**

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: ALL tests pass — ~739 updated + ~50-80 new from D1-D4

Run: `cd packages/context-injection && uv run pytest tests/ -v --tb=short 2>&1 | tail -5`
Expected: All pass, zero failures

**Step 4: Commit**

```bash
git add packages/context-injection/tests/test_integration.py docs/references/context-injection-contract.md
git commit -m "feat(context-injection): add 0.2.0 integration tests + update protocol contract (D4 Task 14)

New round-trip, multi-turn, checkpoint, and action flow integration tests.
Protocol contract updated to 0.2.0 schema with ledger validation, conversation
control, and checkpoint fields."
```

---

## D5: Agent Rewrite

Rewrites `.claude/agents/codex-dialogue.md` Phase 2 conversation loop from 3-step manual ledger management to 7-step server-assisted scouting loop.

**Depends on:** D4 complete (server returns `action`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`, `template_candidates`)
**Risk:** Medium — instruction design (not code), single file, but high-stakes (governs all future Codex conversations)

### Task 15: Phase 2 conversation loop rewrite

**Files:**
- Modify: `.claude/agents/codex-dialogue.md`

**Step 1: Read the current agent file**

Read `.claude/agents/codex-dialogue.md` (324 lines). Verify:
- Frontmatter `tools:` line contains `mcp__codex__codex` and `mcp__codex__codex-reply`
- Phase 1 (Setup): lines 17-66
- Phase 2 (Conversation Loop): lines 68-185
- Phase 3 (Synthesis): lines 187-225
- Constraints: lines 227-234
- Output Format: lines 237-315

**Step 2: Update the YAML frontmatter**

Add context injection MCP tools to the `tools:` line.

Old (line 4):
```yaml
tools: Bash, Read, Glob, Grep, mcp__codex__codex, mcp__codex__codex-reply
```

New:
```yaml
tools: Bash, Read, Glob, Grep, mcp__codex__codex, mcp__codex__codex-reply, mcp__context-injection__process_turn, mcp__context-injection__execute_scout
```

**Step 3: Add context injection precondition**

Add after the existing MCP tools precondition (after line 15):

```markdown
- Context injection MCP tools `mcp__context-injection__process_turn` and `mcp__context-injection__execute_scout` must be available (context injection server running)
- If context injection tools are unavailable: conversation loop still works without Steps 2-4 of the per-turn loop (no server validation, no scouting, no checkpoint tracking). Fall back to the manual ledger management described in the Running Ledger section.
```

**Step 4: Replace Phase 2 conversation loop**

Replace the entire Phase 2 section (lines 68-185 of the current file) with the text below.
Keep Phase 1 (lines 17-66) and everything after Phase 2 (line 186+) intact.

The complete replacement text for Phase 2:

````markdown
## Phase 2: Conversation Loop

### Start the conversation

Call `mcp__codex__codex` with:

| Parameter | Value |
|-----------|-------|
| `prompt` | Assembled briefing |
| `model` | `"gpt-5.3-codex"` |
| `sandbox` | `read-only` |
| `approval-policy` | `never` |
| `config` | `{"model_reasoning_effort": "xhigh"}` |

Persist `threadId` from the response (prefer `structuredContent.threadId`, fall back to top-level `threadId`).

Use `threadId` as `conversation_id` for `process_turn` calls.

### Conversation state

Initialize after starting the conversation:

| State | Initial value | Purpose |
|-------|--------------|---------|
| `threadId` | From Codex response | For `codex-reply` calls |
| `conversation_id` | Same as `threadId` | For `process_turn` calls |
| `state_checkpoint` | `null` | Opaque string; store from `process_turn` response, pass back next turn |
| `checkpoint_id` | `null` | Opaque string; store from `process_turn` response, pass back next turn |
| `turn_count` | `1` | Turns completed |
| `evidence_count` | `0` | Scouts executed (for synthesis statistics) |

### Running ledger

The context injection server maintains the conversation ledger, computes counters, derives quality, detects convergence, and decides when to continue or conclude. The agent's role per turn:

1. **Extract** semantic data from the Codex response
2. **Send** to server via `process_turn`
3. **Act** on the server's `action` directive
4. **Pass through** checkpoints between turns

The server tracks: cumulative claim counts, plateau detection, closing probe state, evidence budget, and conversation state snapshots. The agent does not replicate this logic.

### Per-turn loop (7 steps)

After each Codex response, execute steps 1-7 in order.

#### Step 1: Extract semantic data

Read the Codex response and extract:

| Field | Type | How to extract |
|-------|------|---------------|
| `position` | `string` | 1-2 sentence summary of Codex's key point this turn |
| `claims` | `list[{text, status, turn}]` | Each distinct claim with status (see table below) |
| `delta` | `string` | Single label: `advancing`, `shifting`, or `static` (see table below) |
| `tags` | `list[string]` | 0-2 tags from the tag table below |
| `unresolved` | `list[{text, turn}]` | Questions this turn opened or left unanswered |

**Claim status:**

| Status | When to assign |
|--------|---------------|
| `new` | Claim appears for the first time in this conversation |
| `reinforced` | Previously stated claim repeated with new evidence or reasoning |
| `revised` | Codex changed position on a previously stated claim |
| `conceded` | Codex abandoned a previously stated claim |

**Delta** (required, single-label — the decision-relevant signal):

| Delta | Meaning |
|-------|---------|
| `advancing` | New reasoning, evidence, or genuine pushback introduced |
| `shifting` | Position changed (concession) or topic moved to a different thread |
| `static` | Previous points restated without new substance |

Classify honestly: different phrasing of the same point is `static`, not `advancing`.

**Tags** (optional, multi-label):

| Tag | Signal |
|-----|--------|
| `challenge` | Pushed back on a claim with evidence or reasoning |
| `concession` | Changed position based on the argument |
| `tangent` | Shifted to a weakly-related topic |
| `new_reasoning` | Introduced a novel argument or framework |
| `expansion` | Built on an existing thread, added depth |
| `restatement` | Repeated a previous point without new substance |

#### Step 2: Call `process_turn`

Call `mcp__context-injection__process_turn` with:

```json
{
  "request": {
    "schema_version": "0.2.0",
    "turn_number": <turn_count>,
    "conversation_id": "<conversation_id>",
    "focus": {
      "text": "<the overarching topic under discussion>",
      "claims": [{"text": "<claim>", "status": "<status>", "turn": <n>}, ...],
      "unresolved": [{"text": "<question>", "turn": <n>}, ...]
    },
    "posture": "<current posture>",
    "position": "<position from Step 1>",
    "claims": [{"text": "<claim>", "status": "<status>", "turn": <n>}, ...],
    "delta": "<delta from Step 1>",
    "tags": ["<tag1>", "<tag2>"],
    "unresolved": [{"text": "<question>", "turn": <n>}, ...],
    "state_checkpoint": "<from previous turn's response, or null>",
    "checkpoint_id": "<from previous turn's response, or null>"
  }
}
```

**Field mapping:**
- Set `focus.claims` and top-level `claims` to the same list.
- Set `focus.unresolved` and top-level `unresolved` to the same list.
- `focus.text` is the overarching topic (stable across turns), not the per-turn `position`.

**First turn:** Set `state_checkpoint` and `checkpoint_id` to `null`.

**Subsequent turns:** Pass `state_checkpoint` and `checkpoint_id` from the previous turn's `process_turn` response.

#### Step 3: Process the response

**On success** (`status: "success"`):

| Field | What to do |
|-------|-----------|
| `validated_entry` | Server-validated ledger entry. Use for follow-up composition — authoritative over your extraction. |
| `warnings` | Log internally. No action needed. |
| `cumulative` | Running totals: `total_claims`, `reinforced`, `revised`, `conceded`, `unresolved_open`. Use for conversation awareness. |
| `action` | **Directive:** `continue_dialogue`, `closing_probe`, or `conclude`. See Step 5. |
| `action_reason` | Human-readable explanation. Include in your internal reasoning. |
| `template_candidates` | Available scout options for evidence gathering. See Step 4. |
| `budget` | `scout_available` (bool), `evidence_count`, `evidence_remaining`. |
| `ledger_summary` | Compact trajectory summary. Use in follow-up composition. |
| `state_checkpoint` | **Store** — pass in next turn's request. |
| `checkpoint_id` | **Store** — pass in next turn's request. |

**On error** (`status: "error"`):

| Code | Recovery |
|------|----------|
| `checkpoint_stale` or `checkpoint_missing` | Retry once: set `state_checkpoint` and `checkpoint_id` to `null`. |
| `ledger_hard_reject` | Re-examine the Codex response, correct your extraction, retry `process_turn`. |
| Other codes | Do not retry. Synthesize from what you have (proceed to Phase 3). |

#### Step 4: Scout (optional)

**Skip this step** if `template_candidates` is empty OR `budget.scout_available` is `false`.

If scouts are available:

1. Select the highest-ranked candidate (lowest `rank` value)
2. Select its first `scout_option`
3. Call `mcp__context-injection__execute_scout`:

```json
{
  "request": {
    "schema_version": "0.2.0",
    "scout_option_id": "<from scout_option.id>",
    "scout_token": "<from scout_option.scout_token>",
    "turn_request_ref": "<conversation_id>:<turn_number>"
  }
}
```

4. On success:
   - Store `evidence_wrapper` (human-readable summary — include in follow-up)
   - Store `file_result` or `grep_result` if you need raw evidence data
   - Increment `evidence_count`
   - Note updated `budget`
5. On error: continue without evidence. Do not retry.

#### Step 5: Act on action

| Action | Do this |
|--------|---------|
| `continue_dialogue` | Compose follow-up (Step 6) and send (Step 7). |
| `closing_probe` | Compose closing probe: "Given our discussion, what's your final position on [highest-priority unresolved item from `validated_entry.unresolved`]?" Send (Step 7). |
| `conclude` | Exit the loop. Proceed to Phase 3 (Synthesis). |

The server handles plateau detection, budget exhaustion, and closing probe sequencing internally. Trust the `action` — do not override it with your own continue/conclude logic.

#### Step 6: Compose follow-up

Build the follow-up from these inputs. Priority order for choosing what to ask:

1. **Scout evidence** (if Step 4 produced results): Frame a question around `evidence_wrapper` using the evidence shape below
2. **Unresolved items** from `validated_entry.unresolved`
3. **Unprobed claims** tagged `new` in `validated_entry.claims`
4. **Weakest claim** in cumulative data (least-supported, highest-impact)
5. **Posture-driven probe** from the patterns table

**When evidence is available**, use this shape:

```
[repo facts — inline snippet with provenance (path:line)]
[disposition — what this means for the claim under discussion]
[one question — derived from the evidence, not from the original follow-up]
```

This forces Codex to engage with evidence by making it the premise of the question.

Use `ledger_summary` for conversation awareness — knowing which claims are settled, what's still open, and the conversation trajectory.

#### Patterns by posture

| Posture | Patterns |
|---------|----------|
| **Adversarial** | "I disagree because...", "What about failure mode X?", "This assumes Y — what if Y is false?" |
| **Collaborative** | "Building on that, what if...", "How would X combine with Y?", "What's the strongest version of this?" |
| **Exploratory** | "What other approaches exist?", "What am I not considering?", "How does this relate to X?" |
| **Evaluative** | "Is that claim accurate?", "What about coverage of X?", "Where are the gaps?" |

#### Step 7: Send follow-up

Send via `mcp__codex__codex-reply` with the persisted `threadId`.

Increment `turn_count`. Return to Step 1 for the next Codex response.

### Turn management

- Track turns used vs. budget (default 8, hard max 15).
- **Budget 1:** No follow-ups. Extract semantic data, call `process_turn` once, synthesize from the single response.
- **Budget 2:** Run both turns through the loop. The server's `action` guides whether to continue after turn 1.
- **Budget 3+:** The server handles convergence detection and closing probes via `action`. Trust the directive.
- If `mcp__codex__codex-reply` fails mid-conversation, call `process_turn` one final time with what you extracted, then synthesize from `ledger_summary`.
````

**Step 5: Update Phase 3 synthesis**

Add the following to the **Assembly process** section in Phase 3 (after the existing item 4 "Unresolved → Open Questions"):

```markdown
5. **Evidence trajectory:** For each turn where a scout was executed, note: what entity was scouted, what was found (or not found), and its impact on the conversation (premise falsified, claim supported, or ambiguous).
```

Add the following to the **Pre-flight checklist** (after the last existing checklist item):

```markdown
- [ ] Evidence statistics: scouts executed, entities scouted, impacts on conversation
```

**Step 6: Update output format**

Add to the **Conversation Summary** section (after the `Trajectory` line):

```markdown
- **Evidence:** [X scouts / Y turns, entities: ..., impacts: ...]
```

Add to the **Continuation** section (after "Recommended posture for continuation"):

```markdown
- **Evidence trajectory:** [which turns had evidence, what entities, what impacts]
```

Update the **Example** Conversation Summary to include evidence:

```markdown
- **Evidence:** 2 scouts / 4 turns (T2: `src/audit/store.py` — confirmed append-only pattern; T3: `config/schema.yaml` — found versioned envelope type)
```

Update the example Continuation section to include:

```markdown
- **Evidence trajectory:** T2 — `src/audit/store.py` read, confirmed append-only writes (claim supported); T3 — `config/schema.yaml` read, found envelope type with version field (claim supported)
```

**Step 7: Manual testing**

Run the codex-dialogue agent with a test topic that exercises the new loop:

1. **Start a test conversation:**

```
Use the Task tool to invoke the codex-dialogue agent:
  Topic: "Review the context injection pipeline architecture"
  Context: packages/context-injection/
  Goal: Evaluate the pipeline design
  Posture: evaluative
  Turn budget: 3
```

2. **Verify each per-turn loop iteration:**

- [ ] Agent extracts semantic data from Codex response (position, claims, delta, tags, unresolved)
- [ ] `process_turn` called with extracted data and correct schema version (`0.2.0`)
- [ ] Server response received with `action`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`
- [ ] `state_checkpoint` and `checkpoint_id` from response passed to next turn's request
- [ ] Agent follows `action` directive (continue_dialogue → follow-up, closing_probe → closing probe question, conclude → exit to synthesis)

3. **Verify scout integration (if template_candidates returned):**

- [ ] Scout evaluated when `budget.scout_available` is true
- [ ] `execute_scout` called with correct `scout_option_id`, `scout_token`, and `turn_request_ref`
- [ ] `evidence_wrapper` from scout included in follow-up composition
- [ ] Follow-up uses the evidence shape (repo facts → disposition → question)

4. **Verify synthesis:**

- [ ] Synthesis uses `ledger_summary` for trajectory (not manually reconstructed)
- [ ] Evidence trajectory included if scouts were executed
- [ ] Output format includes evidence statistics line
- [ ] Continuation section includes evidence trajectory

5. **Verify error recovery:**

- [ ] If `process_turn` returns `checkpoint_stale`, agent retries with null checkpoint
- [ ] If `execute_scout` fails, agent continues without evidence (no retry)
- [ ] If Codex reply fails mid-conversation, agent calls `process_turn` one final time and synthesizes

6. **Verify fallback (context injection unavailable):**

- [ ] If context injection MCP tools are not available, conversation loop degrades to manual ledger management
- [ ] Synthesis still produces valid output without evidence data

**Step 8: Commit**

```bash
git add .claude/agents/codex-dialogue.md
git commit -m "$(cat <<'EOF'
feat(agent): rewrite codex-dialogue Phase 2 to 7-step server-assisted loop

Replace manual ledger management with context injection server integration.
Agent extracts semantic data, server validates entries, tracks conversation
state, detects convergence, and controls closing probes via action directive.

Adds: process_turn calls, scout execution, checkpoint pass-through,
evidence-aware follow-ups, action-driven convergence detection.

Removes: manual counter computation, quality derivation, continue/conclude
rule evaluation, closing probe tracking.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Resolved Questions (from Codex Review)

These questions were open during plan writing and resolved via Codex consultation (thread `019c62da`):

1. **match_templates internal access:** Does NOT read `turn_request.context_claims` or `turn_request.evidence_history`. Only uses `turn_request.conversation_id` and `turn_request.turn_number` for HMAC token payloads (templates.py:280-281, 339-340). **templates.py is unchanged in D4.**

2. **Pipeline signature:** Locked to option (a) — `process_turn(request, ctx)` unchanged. Pipeline resolves conversation internally via `ctx.get_or_create_conversation(request.conversation_id)`. Keeps public API stable.

3. **D3 parameter design:** Keep D3 functions pure on D1 types (not ConversationState). Pipeline extracts data and passes it. Decoupling enables D2/D3 parallelism.

4. **Checkpoint ingestion gap:** Original plan omitted checkpoint intake from D4 pipeline. Now explicit in Task 13a step 3 and D2 Task 7 validation policy.

5. **Prospective state pattern:** Pipeline builds a projected ConversationState via `with_turn()`, computes all derived fields from it, then commits atomically by replacing the dict entry. No partial mutations.

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest tests/ -v`
Expected: All tests pass (~739 existing updated + ~400-580 new)

Run: `cd packages/context-injection && ruff check context_injection/ tests/`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `context_injection/ledger.py` | New | Ledger types, validation, counter/quality/delta computation |
| `context_injection/conversation.py` | New | ConversationState (per-conversation ledger + claim registry) |
| `context_injection/checkpoint.py` | New | Checkpoint serialization, chain validation, compaction |
| `context_injection/control.py` | New | Conversation action computation, ledger summary generation |
| `context_injection/types.py` | Modified | TurnRequest/TurnPacket 0.2.0 schema |
| `context_injection/enums.py` | Modified | EffectiveDelta, QualityLabel, ValidationTier, new error codes |
| `context_injection/pipeline.py` | Modified | Rewired to use ConversationState, new validation/control steps |
| `context_injection/execute.py` | Modified | Auto-record evidence, budget from ConversationState |
| `context_injection/state.py` | Modified | AppContext.conversations dict |
| `context_injection/server.py` | Modified | Minimal — pipeline resolves conversation internally |
| `tests/test_ledger.py` | New | D1 validation tests |
| `tests/test_conversation.py` | New | D2 state management tests |
| `tests/test_checkpoint.py` | New | D2 checkpoint tests |
| `tests/test_control.py` | New | D3 control + summary tests |
| `tests/test_*.py` (6 existing) | Modified | Schema 0.2.0 migration |
| `docs/references/context-injection-contract.md` | Modified | 0.2.0 protocol contract |
| `.claude/agents/codex-dialogue.md` | Modified | Phase 2 rewrite (7-step loop) |
