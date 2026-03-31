"""Tests for consultation profile resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.profiles import (
    ResolvedProfile,
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

    def test_unknown_profile_returns_defaults(self) -> None:
        resolved = resolve_profile(profile_name="nonexistent")
        assert resolved.posture == "collaborative"

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
