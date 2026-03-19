"""Consultation profile YAML validator.

Validates consultation-profiles.yaml against contract §14 invariants:
- posture/phases mutual exclusivity
- Adjacent phases have distinct postures
- Phase required fields (posture, target_turns, description)
- turn_budget >= number of phases
- Posture values in VALID_POSTURES
- Required profile fields (description)
"""
from __future__ import annotations

from pathlib import Path

import yaml

if __package__:
    from scripts.event_schema import VALID_POSTURES
else:
    from event_schema import VALID_POSTURES  # type: ignore[import-not-found,no-redef]


def validate_profile(name: str, profile: dict) -> list[str]:
    """Validate a single profile. Returns list of error strings."""
    errors: list[str] = []

    if not isinstance(profile, dict):
        return [f"{name}: profile must be a dict"]

    # Required field: description
    if "description" not in profile:
        errors.append(f"{name}: missing required field 'description'")

    has_posture = "posture" in profile
    has_phases = "phases" in profile

    # Mutual exclusivity
    if has_posture and has_phases:
        errors.append(f"{name}: has both 'posture' and 'phases' — must have one or the other")
    elif not has_posture and not has_phases:
        errors.append(f"{name}: must have either 'posture' or 'phases'")

    # Single-phase posture validation
    if has_posture and not has_phases:
        posture = profile["posture"]
        if not isinstance(posture, str) or posture not in VALID_POSTURES:
            errors.append(f"{name}: invalid posture {posture!r}")

    # Multi-phase validation
    if has_phases and not has_posture:
        phases = profile["phases"]
        if not isinstance(phases, list) or len(phases) == 0:
            errors.append(f"{name}: 'phases' must be a non-empty list")
        else:
            _validate_phases(name, phases, profile, errors)

    return errors


def _validate_phases(
    name: str, phases: list, profile: dict, errors: list[str]
) -> None:
    """Validate phase list invariants."""
    for i, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"{name}: phase {i} must be a dict")
            continue

        # Required phase fields
        for field in ("posture", "target_turns", "description"):
            if field not in phase:
                errors.append(f"{name}: phase {i} missing required field '{field}'")

        # Posture value — reject non-strings and invalid strings
        posture = phase.get("posture")
        if posture is not None:
            if not isinstance(posture, str) or posture not in VALID_POSTURES:
                errors.append(f"{name}: phase {i} invalid posture {posture!r}")

        # target_turns >= 1
        tt = phase.get("target_turns")
        if tt is not None:
            if not isinstance(tt, int) or isinstance(tt, bool) or tt < 1:
                errors.append(f"{name}: phase {i} target_turns must be int >= 1, got {tt!r}")

    # Adjacent posture distinctness
    postures = [p.get("posture") for p in phases if isinstance(p, dict)]
    for i in range(len(postures) - 1):
        if postures[i] == postures[i + 1]:
            errors.append(
                f"{name}: adjacent phases {i} and {i+1} have same posture "
                f"{postures[i]!r} — phases would silently merge"
            )

    # turn_budget >= number of phases (minimum 1 turn per phase)
    turn_budget = profile.get("turn_budget")
    if isinstance(turn_budget, int) and not isinstance(turn_budget, bool):
        if turn_budget < len(phases):
            errors.append(
                f"{name}: turn_budget ({turn_budget}) < number of phases ({len(phases)})"
            )


def validate_profiles_file(path: Path) -> list[str]:
    """Load and validate a consultation-profiles.yaml file."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"failed to load profiles: {exc}"]

    if not isinstance(data, dict) or "profiles" not in data:
        return ["profiles file must contain a 'profiles' key"]

    profiles = data["profiles"]
    if not isinstance(profiles, dict):
        return ["'profiles' must be a mapping"]

    errors: list[str] = []
    for name, profile in profiles.items():
        errors.extend(validate_profile(str(name), profile))
    return errors
