"""Tests for secret pattern taxonomy."""

from __future__ import annotations

from server.secret_taxonomy import (
    FAMILIES,
    SecretFamily,
    Tier,
    check_placeholder_bypass,
)


class TestFamilyStructure:
    def test_families_is_nonempty_tuple(self) -> None:
        assert isinstance(FAMILIES, tuple)
        assert len(FAMILIES) > 0

    def test_all_families_are_frozen_dataclasses(self) -> None:
        for family in FAMILIES:
            assert isinstance(family, SecretFamily)

    def test_tier_values_are_valid(self) -> None:
        valid: set[Tier] = {"strict", "contextual", "broad"}
        for family in FAMILIES:
            assert family.tier in valid, f"{family.name} has invalid tier {family.tier}"

    def test_each_family_has_compiled_pattern(self) -> None:
        import re
        for family in FAMILIES:
            assert isinstance(family.pattern, re.Pattern), f"{family.name} pattern not compiled"

    def test_strict_families_have_no_placeholder_bypass(self) -> None:
        for family in FAMILIES:
            if family.tier == "strict":
                assert family.placeholder_bypass == [], (
                    f"strict family {family.name} must not have placeholder bypass"
                )


class TestStrictTierPatterns:
    def test_aws_access_key_matches(self) -> None:
        family = _family("aws_access_key_id")
        assert family.pattern.search("key is AKIAIOSFODNN7EXAMPLE here")

    def test_aws_access_key_rejects_short(self) -> None:
        family = _family("aws_access_key_id")
        assert family.pattern.search("AKIASHORT") is None

    def test_pem_private_key_matches(self) -> None:
        family = _family("pem_private_key")
        assert family.pattern.search("-----BEGIN RSA PRIVATE KEY-----")

    def test_pem_private_key_has_redact_pattern(self) -> None:
        family = _family("pem_private_key")
        assert family.redact_pattern is not None

    def test_jwt_token_matches(self) -> None:
        family = _family("jwt_token")
        assert family.pattern.search(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )

    def test_basic_auth_matches(self) -> None:
        family = _family("basic_auth_header")
        assert family.pattern.search("Authorization: Basic dXNlcjpwYXNz")


class TestContextualTierPatterns:
    def test_github_pat_matches(self) -> None:
        family = _family("github_pat")
        assert family.pattern.search("ghp_" + "A" * 36)

    def test_openai_key_matches(self) -> None:
        family = _family("openai_api_key")
        assert family.pattern.search("sk-" + "a" * 40)

    def test_bearer_token_matches(self) -> None:
        family = _family("bearer_auth_header")
        assert family.pattern.search("Bearer " + "x" * 25)

    def test_slack_bot_token_matches(self) -> None:
        family = _family("slack_bot_token")
        assert family.pattern.search("xoxb-1234567890-abcdef")


class TestPlaceholderBypass:
    def test_bypass_returns_true_for_example_context(self) -> None:
        family = _family("github_pat")
        text = f"for example the format is ghp_{'A' * 36}"
        assert check_placeholder_bypass(text, family) is True

    def test_bypass_returns_false_for_real_context(self) -> None:
        family = _family("github_pat")
        text = f"export GH_TOKEN=ghp_{'A' * 36}"
        assert check_placeholder_bypass(text, family) is False

    def test_bypass_disabled_for_strict_tier(self) -> None:
        family = _family("aws_access_key_id")
        text = "for example AKIAIOSFODNN7EXAMPLE"
        assert check_placeholder_bypass(text, family) is False

    def test_bypass_checks_window_around_match(self) -> None:
        family = _family("openai_api_key")
        padding = "x" * 200
        text = f"placeholder context here sk-{'a' * 40}{padding}"
        assert check_placeholder_bypass(text, family) is True

    def test_bypass_rejects_distant_placeholder_word(self) -> None:
        family = _family("openai_api_key")
        padding = "x" * 200
        text = f"placeholder{padding}sk-{'a' * 40}"
        assert check_placeholder_bypass(text, family) is False


class TestBroadTierPatterns:
    def test_credential_assignment_matches(self) -> None:
        family = _family("credential_assignment")
        assert family.pattern.search("password = hunter2abc")

    def test_credential_assignment_ignores_short_values(self) -> None:
        family = _family("credential_assignment")
        assert family.pattern.search("password = hi") is None


def _family(name: str) -> SecretFamily:
    for f in FAMILIES:
        if f.name == name:
            return f
    raise KeyError(f"No family named {name!r}")
