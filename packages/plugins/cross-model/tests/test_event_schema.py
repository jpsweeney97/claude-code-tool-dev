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


class TestIsNonNegativeInt:
    """is_non_negative_int() edge cases."""

    def test_true_is_excluded(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(True) is False

    def test_false_is_excluded(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(False) is False

    def test_negative_one(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(-1) is False

    def test_zero(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(0) is True

    def test_one(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(1) is True

    def test_string_is_excluded(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int("5") is False

    def test_none_is_excluded(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(None) is False

    def test_float_is_excluded(self) -> None:
        from scripts.event_schema import is_non_negative_int
        assert is_non_negative_int(1.0) is False


class TestKnownUnstructuredTypes:
    """KNOWN_UNSTRUCTURED_TYPES membership."""

    def test_expected_members(self) -> None:
        from scripts.event_schema import KNOWN_UNSTRUCTURED_TYPES
        assert KNOWN_UNSTRUCTURED_TYPES == frozenset({"block", "shadow", "consultation"})
