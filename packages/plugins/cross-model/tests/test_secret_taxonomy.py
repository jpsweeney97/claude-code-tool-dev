"""Tests for the shared secret taxonomy."""

from __future__ import annotations

import re

from scripts.secret_taxonomy import FAMILIES, check_placeholder_bypass


def test_no_duplicate_family_names() -> None:
    names = [family.name for family in FAMILIES]
    assert len(names) == len(set(names))


def test_all_patterns_compile() -> None:
    assert all(isinstance(family.pattern, re.Pattern) for family in FAMILIES)


def test_tier_enabled_consistency() -> None:
    for family in FAMILIES:
        if family.tier in {"strict", "contextual"}:
            assert family.egress_enabled is True

    pem = next(family for family in FAMILIES if family.name == "pem_private_key")
    assert pem.redact_enabled is False


def test_credential_assignment_strong_is_contextual() -> None:
    family = next(f for f in FAMILIES if f.name == "credential_assignment_strong")
    assert family.tier == "contextual"
    assert family.egress_enabled is True
    assert family.placeholder_bypass  # non-empty


def test_credential_assignment_broad_narrowed() -> None:
    family = next(f for f in FAMILIES if f.name == "credential_assignment")
    assert family.tier == "broad"
    # api_key should NOT match the narrowed broad pattern
    assert family.pattern.search("api_key = real_value_123") is None
    # password SHOULD still match
    assert family.pattern.search("password = test123456") is not None


def test_placeholder_bypass_logic() -> None:
    family = next(family for family in FAMILIES if family.name == "github_pat")
    nearby_text = "example: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
    far_text = (
        "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        + " "
        + ("x" * 220)
        + "example token"
    )

    assert check_placeholder_bypass(nearby_text, family) is True
    assert check_placeholder_bypass(far_text, family) is False
