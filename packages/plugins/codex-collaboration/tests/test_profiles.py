"""Tests for consultation profile resolver."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from server.profiles import (
    load_profiles,
    resolve_profile,
    ProfileValidationError,
)


class TestLoadProfiles:
    def test_loads_bundled_profiles(self) -> None:
        profiles = load_profiles()
        assert "quick-check" in profiles
        assert "deep-review" in profiles
        assert "debugging" in profiles
        assert len(profiles) >= 9

    def test_profile_has_required_fields(self) -> None:
        profiles = load_profiles()
        for name, profile in profiles.items():
            assert "posture" in profile or "phases" in profile, (
                f"profile {name} missing posture or phases"
            )
            assert "turn_budget" in profile, f"profile {name} missing turn_budget"


class TestResolveProfile:
    def test_named_profile_resolves(self) -> None:
        resolved = resolve_profile(profile_name="quick-check")
        assert resolved.posture == "collaborative"
        assert resolved.turn_budget == 1
        assert resolved.effort == "medium"
        assert resolved.sandbox == "read-only"
        assert resolved.approval_policy == "never"

    def test_no_profile_returns_defaults(self) -> None:
        resolved = resolve_profile()
        assert resolved.posture == "collaborative"
        assert resolved.effort is None  # No effort override
        assert resolved.sandbox == "read-only"
        assert resolved.approval_policy == "never"

    def test_unknown_profile_raises(self) -> None:
        with pytest.raises(ProfileValidationError, match="unknown profile"):
            resolve_profile(profile_name="nonexistent")

    def test_explicit_flags_override_profile(self) -> None:
        resolved = resolve_profile(
            profile_name="quick-check",
            explicit_posture="adversarial",
            explicit_turn_budget=10,
        )
        assert resolved.posture == "adversarial"
        assert resolved.turn_budget == 10
        # effort still from profile
        assert resolved.effort == "medium"

    def test_validation_rejects_sandbox_widening(self) -> None:
        with pytest.raises(ProfileValidationError, match="sandbox"):
            resolve_profile(explicit_sandbox="workspace-write")

    def test_validation_rejects_approval_widening(self) -> None:
        with pytest.raises(ProfileValidationError, match="approval"):
            resolve_profile(explicit_approval_policy="ask")

    def test_deep_review_resolves_xhigh_effort(self) -> None:
        resolved = resolve_profile(profile_name="deep-review")
        assert resolved.effort == "xhigh"
        assert resolved.posture == "evaluative"
        assert resolved.turn_budget == 8

    def test_phased_profile_rejected(self) -> None:
        """Phased profiles (e.g., debugging) are explicitly rejected in T-03."""
        with pytest.raises(ProfileValidationError, match="phased"):
            resolve_profile(profile_name="debugging")

    def test_all_non_phased_profiles_resolve(self) -> None:
        """All 8 non-phased bundled profiles resolve without error."""
        profiles = load_profiles()
        for name, defn in profiles.items():
            if "phases" in defn:
                continue  # Phased profiles are rejected (tested above)
            resolved = resolve_profile(profile_name=name)
            assert resolved.posture, f"profile {name} has no posture"


class TestExplicitOverridesWithoutProfile:
    """Explicit posture and turn_budget without a named profile."""

    def test_explicit_posture_only(self) -> None:
        resolved = resolve_profile(explicit_posture="adversarial")
        assert resolved.posture == "adversarial"
        assert resolved.turn_budget == 6  # default
        assert resolved.effort is None

    def test_explicit_turn_budget_only(self) -> None:
        resolved = resolve_profile(explicit_turn_budget=8)
        assert resolved.posture == "collaborative"  # default
        assert resolved.turn_budget == 8

    def test_explicit_posture_and_turn_budget(self) -> None:
        resolved = resolve_profile(
            explicit_posture="evaluative", explicit_turn_budget=6
        )
        assert resolved.posture == "evaluative"
        assert resolved.turn_budget == 6
        assert resolved.effort is None

    def test_explicit_overrides_beat_profile(self) -> None:
        resolved = resolve_profile(
            profile_name="deep-review",
            explicit_posture="adversarial",
            explicit_turn_budget=4,
        )
        assert resolved.posture == "adversarial"
        assert resolved.turn_budget == 4
        # effort still comes from profile
        assert resolved.effort == "xhigh"

    def test_all_corpus_posture_budget_combinations(self) -> None:
        """The four benchmark corpus rows must all resolve."""
        corpus = [
            ("evaluative", 6),   # B1
            ("adversarial", 6),  # B3
            ("evaluative", 6),   # B5
            ("comparative", 8),  # B8
        ]
        for posture, budget in corpus:
            resolved = resolve_profile(
                explicit_posture=posture, explicit_turn_budget=budget
            )
            assert resolved.posture == posture
            assert resolved.turn_budget == budget


class TestTypeNarrowing:
    """F4: Literal types catch invalid posture, effort, and turn_budget values."""

    def test_unknown_posture_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(explicit_posture="adversrial")  # type: ignore[arg-type]

    def test_empty_string_posture_rejected(self) -> None:
        """Empty string must not silently fall back to default."""
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(explicit_posture="")  # type: ignore[arg-type]

    def test_unknown_effort_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="unknown effort"):
            resolve_profile(explicit_effort="turbo")  # type: ignore[arg-type]

    def test_empty_string_effort_rejected(self) -> None:
        """Empty string must not silently fall back to default."""
        with pytest.raises(ProfileValidationError, match="unknown effort"):
            resolve_profile(explicit_effort="")  # type: ignore[arg-type]

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
            "collaborative",
            "adversarial",
            "exploratory",
            "evaluative",
            "comparative",
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

    def test_max_turn_budget_accepted(self) -> None:
        resolved = resolve_profile(explicit_turn_budget=15)
        assert resolved.turn_budget == 15

    def test_turn_budget_above_15_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget=16)

    def test_turn_budget_at_100_rejected(self) -> None:
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(explicit_turn_budget=100)

    def test_default_turn_budget_accepted(self) -> None:
        """Default turn_budget=6 must pass the new validation."""
        resolved = resolve_profile()
        assert resolved.turn_budget == 6


class TestYamlIngressValidation:
    """F4 YAML ingress: bad values loaded from YAML must be caught by
    runtime validation in resolve_profile(). Uses a real YAML file via
    _REFERENCES_DIR patch to exercise the full ingress path: file read,
    YAML parsing, key mapping (reasoning_effort -> effort), and validation."""

    def _write_profile_yaml(
        self, tmp_path: Path, profile_name: str, fields: dict
    ) -> None:
        """Write a consultation-profiles.yaml with a single profile."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        yaml_path = tmp_path / "consultation-profiles.yaml"
        yaml_path.write_text(yaml.dump({"profiles": {profile_name: fields}}))

    def _write_local_override_yaml(
        self, tmp_path: Path, profile_name: str, overrides: dict
    ) -> None:
        """Write a consultation-profiles.local.yaml with overrides."""
        local_path = tmp_path / "consultation-profiles.local.yaml"
        local_path.write_text(yaml.dump({"profiles": {profile_name: overrides}}))

    def test_yaml_bad_posture_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML profile with typo posture is caught at resolution time."""
        self._write_profile_yaml(
            tmp_path,
            "bad-profile",
            {"posture": "adversrial"},
        )
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(profile_name="bad-profile")

    def test_yaml_bad_effort_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML reasoning_effort field maps to effort -- bad value caught.
        Pins the file-key contract: YAML uses reasoning_effort, not effort."""
        self._write_profile_yaml(
            tmp_path,
            "bad-profile",
            {"reasoning_effort": "turbo"},
        )
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown effort"):
            resolve_profile(profile_name="bad-profile")

    def test_yaml_non_int_turn_budget_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """YAML turn_budget as string is caught by type(x) is int check."""
        self._write_profile_yaml(
            tmp_path,
            "bad-profile",
            {"turn_budget": "five"},
        )
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="turn_budget"):
            resolve_profile(profile_name="bad-profile")

    def test_local_override_bad_posture_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bad posture in local override YAML is caught after merge.
        Exercises the full local-override merge path: base profile is valid,
        local override introduces a bad posture, merged result is rejected."""
        self._write_profile_yaml(
            tmp_path,
            "test-profile",
            {"posture": "collaborative"},
        )
        self._write_local_override_yaml(
            tmp_path,
            "test-profile",
            {"posture": "adversrial"},
        )
        monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)
        with pytest.raises(ProfileValidationError, match="unknown posture"):
            resolve_profile(profile_name="test-profile")
