"""Tests for consultation profile YAML validation."""
from __future__ import annotations

import pytest
from pathlib import Path


_PROFILES_PATH = (
    Path(__file__).resolve().parent.parent / "references" / "consultation-profiles.yaml"
)


def _profile(
    description: str = "test",
    sandbox: str = "read-only",
    approval_policy: str = "never",
    reasoning_effort: str = "high",
    **kwargs: object,
) -> dict:
    base: dict = {
        "description": description,
        "sandbox": sandbox,
        "approval_policy": approval_policy,
        "reasoning_effort": reasoning_effort,
    }
    base.update(kwargs)
    return base


class TestValidateProfile:
    def test_valid_single_phase(self) -> None:
        from scripts.validate_profiles import validate_profile
        errors = validate_profile("test", _profile(posture="collaborative", turn_budget=4))
        assert errors == []

    def test_valid_multi_phase(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=7,
            phases=[
                {"posture": "exploratory", "target_turns": 2, "description": "Phase 1"},
                {"posture": "evaluative", "target_turns": 3, "description": "Phase 2"},
                {"posture": "collaborative", "target_turns": 2, "description": "Phase 3"},
            ],
        )
        errors = validate_profile("test", profile)
        assert errors == []

    def test_posture_and_phases_mutual_exclusivity(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            posture="collaborative",
            phases=[{"posture": "adversarial", "target_turns": 2, "description": "x"}],
            turn_budget=4,
        )
        errors = validate_profile("test", profile)
        assert any("mutual" in e.lower() or "both" in e.lower() for e in errors)

    def test_adjacent_phases_distinct_postures(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=4,
            phases=[
                {"posture": "collaborative", "target_turns": 2, "description": "Phase 1"},
                {"posture": "collaborative", "target_turns": 2, "description": "Phase 2"},
            ],
        )
        errors = validate_profile("test", profile)
        assert any("adjacent" in e.lower() for e in errors)

    def test_phase_missing_posture(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=2,
            phases=[{"target_turns": 2, "description": "x"}],
        )
        errors = validate_profile("test", profile)
        assert any("posture" in e.lower() for e in errors)

    def test_phase_missing_target_turns(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=2,
            phases=[{"posture": "collaborative", "description": "x"}],
        )
        errors = validate_profile("test", profile)
        assert any("target_turns" in e.lower() for e in errors)

    def test_target_turns_must_be_positive(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=2,
            phases=[{"posture": "collaborative", "target_turns": 0, "description": "x"}],
        )
        errors = validate_profile("test", profile)
        assert any("target_turns" in e.lower() for e in errors)

    def test_turn_budget_gte_phase_count(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = _profile(
            turn_budget=2,
            phases=[
                {"posture": "exploratory", "target_turns": 1, "description": "1"},
                {"posture": "evaluative", "target_turns": 1, "description": "2"},
                {"posture": "collaborative", "target_turns": 1, "description": "3"},
            ],
        )
        errors = validate_profile("test", profile)
        assert any("turn_budget" in e.lower() for e in errors)

    def test_invalid_posture_value(self) -> None:
        from scripts.validate_profiles import validate_profile
        errors = validate_profile("test", _profile(posture="aggressive", turn_budget=4))
        assert any("posture" in e.lower() for e in errors)

    def test_missing_description(self) -> None:
        from scripts.validate_profiles import validate_profile
        profile = {"posture": "collaborative", "turn_budget": 4,
                   "sandbox": "read-only", "approval_policy": "never", "reasoning_effort": "high"}
        errors = validate_profile("test", profile)
        assert any("description" in e.lower() for e in errors)

    def test_neither_posture_nor_phases(self) -> None:
        from scripts.validate_profiles import validate_profile
        errors = validate_profile("test", _profile(turn_budget=4))
        assert any("posture" in e.lower() or "phases" in e.lower() for e in errors)


class TestValidateProfilesFile:
    def test_current_profiles_valid(self) -> None:
        from scripts.validate_profiles import validate_profiles_file
        errors = validate_profiles_file(_PROFILES_PATH)
        assert errors == [], f"Current profiles have errors: {errors}"


class TestLocalOverrideValidation:
    def test_local_override_validated_if_exists(self) -> None:
        from scripts.validate_profiles import validate_profiles_file
        local_path = _PROFILES_PATH.parent / "consultation-profiles.local.yaml"
        if local_path.exists():
            errors = validate_profiles_file(local_path)
            assert errors == [], f"Local profile override has errors: {errors}"

    def test_validate_profiles_file_missing_is_noop(self) -> None:
        from scripts.validate_profiles import validate_profiles_file
        errors = validate_profiles_file(Path("/nonexistent/profiles.yaml"))
        assert len(errors) == 1
        assert "failed to load" in errors[0].lower()
