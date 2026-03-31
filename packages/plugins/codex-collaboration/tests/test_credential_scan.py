"""Tests for tiered credential scanning."""

from __future__ import annotations

from server.credential_scan import ScanResult, scan_text


class TestStrictTier:
    def test_aws_key_blocks(self) -> None:
        result = scan_text("use AKIAIOSFODNN7EXAMPLE for access")
        assert result.action == "block"
        assert result.tier == "strict"
        assert "aws_access_key_id" in (result.reason or "")

    def test_pem_header_blocks(self) -> None:
        result = scan_text("-----BEGIN RSA PRIVATE KEY-----")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_jwt_blocks(self) -> None:
        token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        result = scan_text(f"token: {token}")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_basic_auth_blocks(self) -> None:
        result = scan_text("Authorization: Basic dXNlcjpwYXNzd29yZA==")
        assert result.action == "block"
        assert result.tier == "strict"


class TestContextualTier:
    def test_github_pat_blocks_without_placeholder(self) -> None:
        pat = "ghp_" + "A" * 36
        result = scan_text(f"export GH_TOKEN={pat}")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_github_pat_allows_with_placeholder(self) -> None:
        pat = "ghp_" + "A" * 36
        result = scan_text(f"for example the format is {pat}")
        assert result.action == "allow"

    def test_openai_key_blocks(self) -> None:
        key = "sk-" + "a" * 40
        result = scan_text(f"OPENAI_API_KEY={key}")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_openai_key_allows_with_placeholder(self) -> None:
        key = "sk-" + "a" * 40
        result = scan_text(f"your key looks like {key}")
        assert result.action == "allow"

    def test_bearer_blocks(self) -> None:
        result = scan_text("Bearer " + "x" * 25)
        assert result.action == "block"
        assert result.tier == "contextual"


class TestBroadTier:
    def test_password_assignment_shadows(self) -> None:
        result = scan_text("password = hunter2abc")
        assert result.action == "shadow"
        assert result.tier == "broad"

    def test_short_password_allows(self) -> None:
        result = scan_text("password = hi")
        assert result.action == "allow"


class TestCleanInput:
    def test_clean_text_allows(self) -> None:
        result = scan_text("This is a normal consultation about architecture.")
        assert result.action == "allow"
        assert result.tier is None
        assert result.reason is None


class TestPriorityOrdering:
    def test_strict_wins_over_contextual(self) -> None:
        pat = "ghp_" + "A" * 36
        text = f"AKIAIOSFODNN7EXAMPLE and {pat}"
        result = scan_text(text)
        assert result.action == "block"
        assert result.tier == "strict"
