"""Tests for credential_scan module."""

from __future__ import annotations

from scripts.credential_scan import ScanResult, scan_text


class TestScanResult:
    """ScanResult dataclass shape."""

    def test_allow_result(self) -> None:
        r = ScanResult(action="allow", tier=None, reason=None)
        assert r.action == "allow"
        assert r.tier is None

    def test_block_result(self) -> None:
        r = ScanResult(action="block", tier="strict", reason="AWS key")
        assert r.action == "block"
        assert r.tier == "strict"


class TestScanTextStrict:
    """Strict tier — hard-block, near-zero FP."""

    def test_aws_access_key(self) -> None:
        result = scan_text("key is AKIAIOSFODNN7EXAMPLE")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_pem_private_key(self) -> None:
        result = scan_text("-----BEGIN RSA PRIVATE KEY-----")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_jwt_token(self) -> None:
        result = scan_text("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_basic_auth_header_strict(self) -> None:
        result = scan_text("Authorization: Basic dXNlcjpwYXNz")
        assert result.action == "block"
        assert result.tier == "strict"


class TestScanTextContextual:
    """Contextual tier — block unless placeholder suppression."""

    def test_github_pat_blocked(self) -> None:
        result = scan_text("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_github_pat_suppressed_by_placeholder(self) -> None:
        result = scan_text("example: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "allow"

    def test_second_contextual_match_still_blocks(self) -> None:
        token1 = "ghp_" + "A" * 36
        token2 = "ghp_" + "B" * 36
        prompt = f"An example GitHub PAT: {token1} {'x' * 80} real: {token2}"
        result = scan_text(prompt)
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_openai_sk_key(self) -> None:
        result = scan_text("sk-" + "a" * 40)
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_bearer_token(self) -> None:
        result = scan_text("Authorization: Bearer abcdefghij1234567890xyz")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_slack_xoxb_token(self) -> None:
        result = scan_text("xoxb-1234-5678-abcdef")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_slack_xoxp_token(self) -> None:
        result = scan_text("xoxp-1234-5678-abcdef")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_slack_xoxs_token(self) -> None:
        result = scan_text("xoxs-1234-5678-abcdef")
        assert result.action == "block"
        assert result.tier == "contextual"


class TestScanTextBroad:
    """Broad tier — shadow only, no blocking."""

    def test_password_assignment_shadows(self) -> None:
        result = scan_text("password = mysecretvalue123")
        assert result.action == "shadow"
        assert result.tier == "broad"

    def test_encryption_key_assignment(self) -> None:
        result = scan_text("encryption_key = mysecret123")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_signing_key_assignment(self) -> None:
        result = scan_text("signing_key = mysecret123")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_api_secret_assignment(self) -> None:
        result = scan_text("api_secret = mysecret123")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_credential_assignment(self) -> None:
        result = scan_text("credential = mysecret123")
        assert result.action == "shadow"
        assert result.tier == "broad"


class TestScanTextClean:
    """Clean text — no matches."""

    def test_normal_text_allows(self) -> None:
        result = scan_text("Fix the flaky test in auth_test.py")
        assert result.action == "allow"
        assert result.tier is None
        assert result.reason is None

    def test_empty_string_allows(self) -> None:
        result = scan_text("")
        assert result.action == "allow"


class TestScanTextReasonFormat:
    """Reason field uses family.name, not regex fragment."""

    def test_strict_reason_uses_family_name(self) -> None:
        result = scan_text("key is AKIAIOSFODNN7EXAMPLE")
        assert result.reason == "strict:aws_access_key_id"

    def test_contextual_reason_uses_family_name(self) -> None:
        result = scan_text("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.reason == "contextual:github_pat"

    def test_broad_reason_uses_family_name(self) -> None:
        result = scan_text("password = mysecretvalue123")
        assert result.reason == "broad:credential_assignment"


class TestScanTextPriority:
    """Strict takes precedence over contextual."""

    def test_strict_before_contextual(self) -> None:
        text = "AKIAIOSFODNN7EXAMPLE and ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scan_text(text)
        assert result.tier == "strict"


class TestCredentialAssignmentStrong:
    """Strong machine-secret key names should block at contextual tier."""

    def test_api_key_line_anchored_blocks(self) -> None:
        """Line-anchored assignment blocks."""
        result = scan_text("api_key = real_secret_value_123")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_client_secret_blocks(self) -> None:
        result = scan_text("client_secret = prod_abc123def456")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_private_key_blocks(self) -> None:
        result = scan_text("private_key = a1b2c3d4e5f6g7h8")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_signing_key_blocks(self) -> None:
        result = scan_text("signing_key = real_key_material_here")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_export_prefix_blocks(self) -> None:
        """export keyword before key name should still match."""
        result = scan_text("export access_token = eyJhbGciOiJIUzI1N")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_indented_assignment_blocks(self) -> None:
        """Indented assignment (config files) should match."""
        result = scan_text("  api_key = real_secret_value_123")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_mid_sentence_does_not_block(self) -> None:
        """Key name mid-sentence is NOT line-anchored — should NOT block."""
        result = scan_text("the access_token = eyJhbGciOiJIUzI1N is used for auth")
        # Mid-sentence: not line-anchored, so strong family does not match.
        # Falls through to broad family which matches but only shadows.
        assert result.action != "block" or result.tier != "contextual"

    def test_strong_with_placeholder_allows(self) -> None:
        """Line-anchored match with bypass word in value allows."""
        result = scan_text("api_key = your-key-here")
        assert result.action == "allow"

    def test_strong_with_dummy_allows(self) -> None:
        """Line-anchored match with bypass word in value allows."""
        result = scan_text("api_key = placeholder_value_here")
        assert result.action == "allow"

    def test_yaml_bare_key_does_not_block(self) -> None:
        """YAML bare key form (value on next line) should not false-positive."""
        result = scan_text("api_key:\n  value: real_secret_value_123")
        assert result.action != "block"

    def test_password_stays_shadow(self) -> None:
        """Generic 'password' should remain broad (shadow-only)."""
        result = scan_text("password = test123456")
        assert result.action == "shadow"
        assert result.tier == "broad"

    def test_credential_stays_shadow(self) -> None:
        """Generic 'credential' should remain broad (shadow-only)."""
        result = scan_text("credential = myvalue123")
        assert result.action == "shadow"
        assert result.tier == "broad"


class TestTierCaching:
    """Tier-filtered tuples are precomputed at module level."""

    def test_strict_families_is_tuple(self) -> None:
        from scripts.credential_scan import _STRICT_FAMILIES
        assert isinstance(_STRICT_FAMILIES, tuple)
        assert len(_STRICT_FAMILIES) > 0

    def test_contextual_families_is_tuple(self) -> None:
        from scripts.credential_scan import _CONTEXTUAL_FAMILIES
        assert isinstance(_CONTEXTUAL_FAMILIES, tuple)
        assert len(_CONTEXTUAL_FAMILIES) > 0

    def test_broad_families_is_tuple(self) -> None:
        from scripts.credential_scan import _BROAD_FAMILIES
        assert isinstance(_BROAD_FAMILIES, tuple)
        assert len(_BROAD_FAMILIES) > 0

    def test_all_tiers_covered(self) -> None:
        from scripts.credential_scan import (
            _STRICT_FAMILIES,
            _CONTEXTUAL_FAMILIES,
            _BROAD_FAMILIES,
        )
        from scripts.secret_taxonomy import FAMILIES

        egress_families = [f for f in FAMILIES if f.egress_enabled]
        cached_count = len(_STRICT_FAMILIES) + len(_CONTEXTUAL_FAMILIES) + len(_BROAD_FAMILIES)
        assert cached_count == len(egress_families)
