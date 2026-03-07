"""Tests for credential_scan module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


class TestScanTextContextual:
    """Contextual tier — block unless placeholder suppression."""

    def test_github_pat_blocked(self) -> None:
        result = scan_text("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_github_pat_suppressed_by_placeholder(self) -> None:
        result = scan_text("example: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "allow"

    def test_openai_sk_key(self) -> None:
        result = scan_text("sk-" + "a" * 40)
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_bearer_token(self) -> None:
        result = scan_text("Authorization: Bearer abcdefghij1234567890xyz")
        assert result.action == "block"
        assert result.tier == "contextual"


class TestScanTextBroad:
    """Broad tier — shadow only, no blocking."""

    def test_password_assignment_shadows(self) -> None:
        result = scan_text("password = mysecretvalue123")
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


class TestScanTextPriority:
    """Strict takes precedence over contextual."""

    def test_strict_before_contextual(self) -> None:
        text = "AKIAIOSFODNN7EXAMPLE and ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scan_text(text)
        assert result.tier == "strict"
