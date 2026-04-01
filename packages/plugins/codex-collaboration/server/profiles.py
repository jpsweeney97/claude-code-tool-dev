"""Consultation profile resolver.

Resolution order: explicit flags > named profile > contract defaults.
Validation gate: rejects sandbox != read-only or approval_policy != never
until freeze-and-rotate is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args

import yaml


class ProfileValidationError(RuntimeError):
    """Raised when a resolved profile requires capabilities not yet implemented."""


Posture = Literal[
    "collaborative", "adversarial", "exploratory", "evaluative", "comparative"
]
Effort = Literal["minimal", "low", "medium", "high", "xhigh"]
SandboxPolicy = Literal["read-only"]
ApprovalPolicy = Literal["never"]

_VALID_POSTURES: frozenset[str] = frozenset(get_args(Posture))
_VALID_EFFORTS: frozenset[str] = frozenset(get_args(Effort))


@dataclass(frozen=True)
class ResolvedProfile:
    """Fully resolved execution controls."""

    posture: Posture
    turn_budget: int
    effort: Effort | None
    sandbox: SandboxPolicy
    approval_policy: ApprovalPolicy


_DEFAULT_POSTURE = "collaborative"
_DEFAULT_TURN_BUDGET = 6
_DEFAULT_SANDBOX = "read-only"
_DEFAULT_APPROVAL = "never"

_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def load_profiles(
    base_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Load profiles from YAML. Merges local overrides if present."""
    base = base_path or _REFERENCES_DIR
    profiles_path = base / "consultation-profiles.yaml"
    if not profiles_path.exists():
        return {}

    with open(profiles_path) as f:
        data = yaml.safe_load(f) or {}

    profiles: dict[str, dict[str, Any]] = data.get("profiles", {})

    local_path = base / "consultation-profiles.local.yaml"
    if local_path.exists():
        with open(local_path) as f:
            local_data = yaml.safe_load(f) or {}
        for name, overrides in local_data.get("profiles", {}).items():
            if name in profiles:
                profiles[name] = {**profiles[name], **overrides}
            else:
                profiles[name] = overrides

    return profiles


def resolve_profile(
    *,
    profile_name: str | None = None,
    explicit_posture: Posture | None = None,
    explicit_turn_budget: int | None = None,
    explicit_effort: Effort | None = None,
    explicit_sandbox: SandboxPolicy | None = None,
    explicit_approval_policy: ApprovalPolicy | None = None,
) -> ResolvedProfile:
    """Resolve execution controls from profile + explicit overrides."""
    profile: dict[str, Any] = {}
    if profile_name is not None:
        profiles = load_profiles()
        if profile_name not in profiles:
            raise ProfileValidationError(
                f"Profile resolution failed: unknown profile. "
                f"Got: profile_name={profile_name!r:.100}"
            )
        profile = profiles[profile_name]

    # Phased profiles are explicitly rejected until phase-progression support exists.
    # Silent collapse to the default posture would misrepresent the profile's intent.
    if "phases" in profile:
        raise ProfileValidationError(
            f"Profile resolution failed: phased profiles require phase-progression "
            f"support (not yet implemented). Profile {profile_name!r} defines phases. "
            f"Use a non-phased profile or omit the profile parameter."
        )

    posture = (
        explicit_posture
        if explicit_posture is not None
        else profile.get("posture", _DEFAULT_POSTURE)
    )
    turn_budget = (
        explicit_turn_budget
        if explicit_turn_budget is not None
        else profile.get("turn_budget", _DEFAULT_TURN_BUDGET)
    )
    effort = (
        explicit_effort
        if explicit_effort is not None
        else profile.get("reasoning_effort")
    )
    sandbox = (
        explicit_sandbox
        if explicit_sandbox is not None
        else profile.get("sandbox", _DEFAULT_SANDBOX)
    )
    approval_policy = (
        explicit_approval_policy
        if explicit_approval_policy is not None
        else profile.get("approval_policy", _DEFAULT_APPROVAL)
    )

    # Type narrowing validation
    if posture not in _VALID_POSTURES:
        raise ProfileValidationError(
            f"Profile resolution failed: unknown posture. Got: posture={posture!r:.100}"
        )
    if effort is not None and effort not in _VALID_EFFORTS:
        raise ProfileValidationError(
            f"Profile resolution failed: unknown effort. Got: effort={effort!r:.100}"
        )
    if not (type(turn_budget) is int and turn_budget > 0):
        raise ProfileValidationError(
            f"Profile resolution failed: turn_budget must be a positive integer. "
            f"Got: turn_budget={turn_budget!r:.100}"
        )

    # Validation gate: reject policy widening until freeze-and-rotate exists
    if sandbox != _DEFAULT_SANDBOX:
        raise ProfileValidationError(
            f"Profile resolution failed: sandbox widening requires freeze-and-rotate "
            f"(not yet implemented). Got: sandbox={sandbox!r}"
        )
    if approval_policy != _DEFAULT_APPROVAL:
        raise ProfileValidationError(
            f"Profile resolution failed: approval widening requires freeze-and-rotate "
            f"(not yet implemented). Got: approval_policy={approval_policy!r}"
        )

    return ResolvedProfile(
        posture=posture,
        turn_budget=turn_budget,
        effort=effort,
        sandbox=sandbox,
        approval_policy=approval_policy,
    )
