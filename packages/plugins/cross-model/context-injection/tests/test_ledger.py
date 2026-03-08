"""Ledger validation types and computation tests."""

import pytest
from pydantic import ValidationError

from context_injection.enums import EffectiveDelta, QualityLabel, ValidationTier
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,
    LedgerValidationError,
    ValidationWarning,
    compute_counters,
    compute_effective_delta,
    compute_quality,
    validate_ledger_entry,
)
from context_injection.types import Claim, Unresolved


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

    def test_compute_counters_rejects_negative_unresolved_closed(self) -> None:
        with pytest.raises(ValueError, match="unresolved_closed must be >= 0"):
            compute_counters([], unresolved_closed=-1)


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


class TestComputeQuality:
    """compute_quality: any non-reinforced activity -> substantive."""

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
        """new_claims > 0 -> advancing, even if revised also > 0."""
        counters = LedgerEntryCounters(new_claims=1, revised=1, conceded=0, unresolved_closed=0)
        assert compute_effective_delta(counters) == EffectiveDelta.ADVANCING

    def test_unresolved_closed_alone_is_static(self) -> None:
        """Unresolved closure doesn't change position -- it clarifies."""
        counters = LedgerEntryCounters(new_claims=0, revised=0, conceded=0, unresolved_closed=2)
        assert compute_effective_delta(counters) == EffectiveDelta.STATIC


class TestDeltaDisagreesTruthTable:
    """_delta_disagrees: all 9 canonical combinations + unknown."""

    @pytest.mark.parametrize(
        ("agent_delta", "effective", "expected"),
        [
            # agent=static vs all effective values
            ("static", EffectiveDelta.STATIC, False),
            ("static", EffectiveDelta.ADVANCING, True),
            ("static", EffectiveDelta.SHIFTING, True),
            # agent=advancing vs all effective values
            ("advancing", EffectiveDelta.STATIC, True),
            ("advancing", EffectiveDelta.ADVANCING, False),
            ("advancing", EffectiveDelta.SHIFTING, False),
            # agent=shifting vs all effective values
            ("shifting", EffectiveDelta.STATIC, True),
            ("shifting", EffectiveDelta.ADVANCING, False),
            ("shifting", EffectiveDelta.SHIFTING, False),
            # unknown agent delta -- always no disagreement
            ("new_information", EffectiveDelta.STATIC, False),
            ("correction", EffectiveDelta.ADVANCING, False),
            ("none", EffectiveDelta.SHIFTING, False),
        ],
    )
    def test_delta_disagrees(
        self, agent_delta: str, effective: EffectiveDelta, expected: bool,
    ) -> None:
        from context_injection.ledger import _delta_disagrees

        assert _delta_disagrees(agent_delta, effective) is expected


class TestSubstantiveStaticDocumentation:
    """quality=SUBSTANTIVE + effective_delta=STATIC is valid (unresolved closure)."""

    def test_unresolved_closed_is_substantive_but_static(self) -> None:
        """Closing unresolved questions is substantive progress but doesn't
        change position (static). This combination must be allowed."""
        counters = LedgerEntryCounters(
            new_claims=0, revised=0, conceded=0, unresolved_closed=2,
        )
        assert compute_quality(counters) == QualityLabel.SUBSTANTIVE
        assert compute_effective_delta(counters) == EffectiveDelta.STATIC


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

    def test_claim_future_turn_rejected(self) -> None:
        """Claim from turn 5 in a turn_number=2 entry is rejected."""
        with pytest.raises(LedgerValidationError) as exc_info:
            validate_ledger_entry(
                position="Position",
                claims=[Claim(text="A", status="new", turn=5)],
                delta="x",
                tags=[],
                unresolved=[],
                turn_number=2,
            )
        assert any("exceeds" in w.message for w in exc_info.value.warnings)

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
