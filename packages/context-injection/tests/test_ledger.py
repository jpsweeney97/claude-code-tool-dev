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


class TestStrictnessPreservation:
    """Re-exported Claim rejects type coercion (strict=True)."""

    def test_claim_rejects_string_turn(self) -> None:
        """strict=True means str '1' is not coerced to int 1."""
        with pytest.raises(ValidationError):
            Claim(text="A", status="new", turn="1")  # type: ignore[arg-type]

    def test_claim_rejects_float_turn(self) -> None:
        with pytest.raises(ValidationError):
            Claim(text="A", status="new", turn=1.0)  # type: ignore[arg-type]


class TestInvalidClaimStatus:
    """Claim.status rejects values outside the Literal constraint."""

    def test_unknown_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Claim(text="A", status="unknown", turn=1)  # type: ignore[arg-type]

    def test_empty_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Claim(text="A", status="", turn=1)  # type: ignore[arg-type]

    def test_valid_statuses_accepted(self) -> None:
        for status in ("new", "reinforced", "revised", "conceded"):
            claim = Claim(text="A", status=status, turn=1)
            assert claim.status == status


class TestImmutability:
    """LedgerEntry and CumulativeState are frozen (immutable)."""

    def test_ledger_entry_frozen(self) -> None:
        counters = LedgerEntryCounters(
            new_claims=1, revised=0, conceded=0, unresolved_closed=0,
        )
        entry = LedgerEntry(
            position="P", claims=[Claim(text="A", status="new", turn=1)],
            delta="new_information", tags=[], unresolved=[], counters=counters,
            quality=QualityLabel.SUBSTANTIVE, effective_delta=EffectiveDelta.ADVANCING,
            turn_number=1,
        )
        with pytest.raises(ValidationError):
            entry.position = "changed"  # type: ignore[misc]

    def test_cumulative_state_frozen(self) -> None:
        state = CumulativeState(
            total_claims=0, reinforced=0, revised=0, conceded=0,
            unresolved_open=0, unresolved_closed=0, turns_completed=0,
            effective_delta_sequence=[],
        )
        with pytest.raises(ValidationError):
            state.total_claims = 5  # type: ignore[misc]


class TestNegativeCounterRejection:
    """Counter fields reject negative values via Field(ge=0)."""

    @pytest.mark.parametrize("field", ["new_claims", "revised", "conceded", "unresolved_closed"])
    def test_ledger_entry_counters_reject_negative(self, field: str) -> None:
        kwargs = {"new_claims": 0, "revised": 0, "conceded": 0, "unresolved_closed": 0}
        kwargs[field] = -1
        with pytest.raises(ValidationError):
            LedgerEntryCounters(**kwargs)

    @pytest.mark.parametrize(
        "field",
        ["total_claims", "reinforced", "revised", "conceded",
         "unresolved_open", "unresolved_closed", "turns_completed"],
    )
    def test_cumulative_state_rejects_negative(self, field: str) -> None:
        kwargs = {
            "total_claims": 0, "reinforced": 0, "revised": 0, "conceded": 0,
            "unresolved_open": 0, "unresolved_closed": 0, "turns_completed": 0,
            "effective_delta_sequence": [],
        }
        kwargs[field] = -1
        with pytest.raises(ValidationError):
            CumulativeState(**kwargs)
