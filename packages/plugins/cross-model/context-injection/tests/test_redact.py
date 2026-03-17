"""Tests for redaction types, PEM detection, generic token scanner, and orchestration."""

from __future__ import annotations

import pytest

import context_injection.redact as redact_mod
from context_injection.classify import FileKind
from context_injection.redact_formats import FormatSuppressed
from context_injection.redact import (
    RedactedText,
    RedactionStats,
    RedactOutcome,
    SuppressedText,
    SuppressionReason,
    contains_pem_private_key,
    redact_known_secrets,
    redact_text,
)


# --- Type tests ---


class TestSuppressionReason:
    def test_all_members(self) -> None:
        assert SuppressionReason.UNSUPPORTED_CONFIG_FORMAT == "unsupported_config_format"
        assert SuppressionReason.FORMAT_DESYNC == "format_desync"
        assert SuppressionReason.PEM_PRIVATE_KEY_DETECTED == "pem_private_key_detected"

    def test_is_strenum(self) -> None:
        assert isinstance(SuppressionReason.FORMAT_DESYNC, str)


class TestRedactionStats:
    def test_construction(self) -> None:
        stats = RedactionStats(format_redactions=2, token_redactions=3)
        assert stats.format_redactions == 2
        assert stats.token_redactions == 3

    def test_frozen(self) -> None:
        stats = RedactionStats(format_redactions=0, token_redactions=0)
        with pytest.raises(AttributeError):
            stats.format_redactions = 1


class TestRedactedText:
    def test_construction(self) -> None:
        stats = RedactionStats(format_redactions=1, token_redactions=2)
        r = RedactedText(text="safe", stats=stats)
        assert r.text == "safe"
        assert r.stats is stats

    def test_frozen(self) -> None:
        r = RedactedText(text="x", stats=RedactionStats(0, 0))
        with pytest.raises(AttributeError):
            r.text = "y"


class TestSuppressedText:
    def test_construction(self) -> None:
        s = SuppressedText(reason=SuppressionReason.PEM_PRIVATE_KEY_DETECTED)
        assert s.reason == SuppressionReason.PEM_PRIVATE_KEY_DETECTED

    def test_frozen(self) -> None:
        s = SuppressedText(reason=SuppressionReason.FORMAT_DESYNC)
        with pytest.raises(AttributeError):
            s.reason = SuppressionReason.PEM_PRIVATE_KEY_DETECTED

    def test_union_discriminates(self) -> None:
        r: RedactOutcome = RedactedText(text="x", stats=RedactionStats(0, 0))
        s: RedactOutcome = SuppressedText(reason=SuppressionReason.FORMAT_DESYNC)
        assert isinstance(r, RedactedText)
        assert isinstance(s, SuppressedText)


# --- PEM detection ---


class TestContainsPemPrivateKey:
    @pytest.mark.parametrize("header", [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN DSA PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN ENCRYPTED PRIVATE KEY-----",
    ])
    def test_detects_private_key_types(self, header: str) -> None:
        text = f"prefix\n{header}\nkey data\n-----END PRIVATE KEY-----"
        assert contains_pem_private_key(text) is True

    def test_embedded_in_config(self) -> None:
        text = "# Config\nkey=val\n-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n"
        assert contains_pem_private_key(text) is True

    def test_rejects_public_key(self) -> None:
        assert contains_pem_private_key("-----BEGIN PUBLIC KEY-----\ndata") is False

    def test_rejects_certificate(self) -> None:
        assert contains_pem_private_key("-----BEGIN CERTIFICATE-----\ndata") is False

    def test_rejects_rsa_public_key(self) -> None:
        assert contains_pem_private_key("-----BEGIN RSA PUBLIC KEY-----\ndata") is False

    def test_empty(self) -> None:
        assert contains_pem_private_key("") is False

    def test_no_pem(self) -> None:
        assert contains_pem_private_key("regular code\nno secrets") is False


# --- Generic token scanner ---


class TestRedactKnownSecrets:
    # Bearer/Basic auth
    def test_bearer_token(self) -> None:
        result, count = redact_known_secrets("Authorization: Bearer abc123def456ghi789jkl0")
        assert count == 1
        assert "abc123def456ghi789jkl0" not in result
        assert "Bearer [REDACTED:value]" in result

    def test_bearer_case_insensitive(self) -> None:
        result, count = redact_known_secrets("authorization: bearer abc123def456ghi789jkl0")
        assert count == 1
        assert "abc123def456ghi789jkl0" not in result

    def test_bearer_extra_whitespace(self) -> None:
        result, count = redact_known_secrets("Header:  Bearer   abc123def456ghi789jkl0")
        assert count == 1
        assert "abc123def456ghi789jkl0" not in result

    def test_basic_auth(self) -> None:
        result, count = redact_known_secrets("Authorization: Basic dXNlcjpwYXNzd29yZA==")
        assert count == 1
        assert "dXNlcjpwYXNzd29yZA==" not in result
        assert "Basic [REDACTED:value]" in result

    # JWT
    def test_jwt(self) -> None:
        jwt = (
            "eyJhbGciOiJIUzI1NiJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
            ".dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        result, count = redact_known_secrets(f"token: {jwt}")
        assert count >= 1
        assert "eyJhbGci" not in result
        assert "[REDACTED:value]" in result

    # API key prefixes
    @pytest.mark.parametrize("key", [
        "sk-1234567890abcdefghij",
        "pk_live_1234567890abcdef",
        "pk_test_1234567890abcdef",
        "ghp_1234567890abcdefgh",
        "gho_1234567890abcdefgh",
        "ghs_1234567890abcdefgh",
        "ghr_1234567890abcdefgh",
        "glpat-1234567890abcdef",
        "xoxb-1234567890abcdefgh",
        "xoxp-1234567890abcdefgh",
        "xoxs-1234567890abcdefgh",
        "AKIAIOSFODNN7EXAMPLE",
    ])
    def test_api_key_prefixes(self, key: str) -> None:
        result, count = redact_known_secrets(f"key = {key}")
        assert count >= 1
        assert key not in result

    def test_short_api_key_not_redacted(self) -> None:
        """API key prefix with < 10 chars after prefix -- not redacted."""
        result, count = redact_known_secrets("key = sk-short")
        assert count == 0
        assert "sk-short" in result

    # Credential assignment
    def test_credential_equals(self) -> None:
        result, count = redact_known_secrets("password=supersecret123")
        assert count == 1
        assert "supersecret123" not in result
        assert "password=[REDACTED:value]" in result

    def test_credential_colon(self) -> None:
        result, count = redact_known_secrets("password: supersecret123")
        assert count == 1
        assert "supersecret123" not in result

    def test_credential_quoted_double(self) -> None:
        result, count = redact_known_secrets('api_key="mysecretvalue123"')
        assert count >= 1
        assert "mysecretvalue123" not in result

    def test_credential_quoted_single(self) -> None:
        result, count = redact_known_secrets("secret='mysecretvalue123'")
        assert count >= 1
        assert "mysecretvalue123" not in result

    def test_credential_export_prefix(self) -> None:
        result, count = redact_known_secrets("export PASSWORD=mysecretvalue123")
        assert count == 1
        assert "mysecretvalue123" not in result

    def test_credential_short_value_not_redacted(self) -> None:
        """RHS < 6 chars not redacted."""
        result, count = redact_known_secrets("password=short")
        assert count == 0
        assert "short" in result

    def test_credential_non_secret_key(self) -> None:
        """password_policy not matched — suffix _policy puts '_' before '=', not whitespace."""
        result, count = redact_known_secrets("password_policy=require_strong")
        assert count == 0
        assert "require_strong" in result

    def test_credential_case_insensitive(self) -> None:
        result, count = redact_known_secrets("PASSWORD=mysecretvalue123")
        assert count == 1
        assert "mysecretvalue123" not in result

    @pytest.mark.parametrize("line", [
        "DB_PASSWORD=secret123456",
        "MYSQL_PASSWORD=secret123456",
        "POSTGRES_PASSWORD=secret123456",
    ])
    def test_credential_prefixed_names(self, line: str) -> None:
        """Prefixed credentials like DB_PASSWORD= are caught by substring match."""
        result, count = redact_known_secrets(line)
        assert count == 1
        assert "secret123456" not in result

    # URL userinfo
    def test_url_userinfo(self) -> None:
        result, count = redact_known_secrets("https://admin:secret123@db.example.com")
        assert count >= 1
        assert "secret123" not in result
        assert "admin:" in result

    def test_url_no_password(self) -> None:
        """No colon after user -- no URL userinfo redaction."""
        result, count = redact_known_secrets("https://user@host.com/path")
        assert "user@host.com" in result

    def test_url_percent_encoded(self) -> None:
        result, count = redact_known_secrets("https://user:pa%3Ass@host.com")
        assert count >= 1
        assert "pa%3Ass" not in result

    # False positives
    def test_empty(self) -> None:
        result, count = redact_known_secrets("")
        assert result == ""
        assert count == 0

    def test_no_secrets(self) -> None:
        text = "const x = 42\nprint('hello')\n"
        result, count = redact_known_secrets(text)
        assert result == text
        assert count == 0

    def test_code_variable_not_redacted(self) -> None:
        """password_length is not a credential key."""
        result, count = redact_known_secrets("password_length = len(user_input)")
        assert count == 0

    # Mixed content
    def test_mixed_multiple_patterns(self) -> None:
        text = (
            "password=mysecretpassword123\n"
            "Authorization: Bearer abcdefghijklmnopqrstu\n"
            "key=ghp_abcdefghij1234567890\n"
        )
        result, count = redact_known_secrets(text)
        assert count >= 3
        assert "mysecretpassword123" not in result
        assert "abcdefghijklmnopqrstu" not in result
        assert "ghp_abcdefghij1234567890" not in result


# --- Orchestration ---


class TestRedactText:
    # --- PEM short-circuit ---

    def test_pem_short_circuit_code(self) -> None:
        text = "val=1\n-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n"
        result = redact_text(text=text, classification=FileKind.CODE)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.PEM_PRIVATE_KEY_DETECTED

    def test_pem_short_circuit_config(self) -> None:
        """PEM detection runs before format dispatch."""
        text = "KEY=val\n-----BEGIN EC PRIVATE KEY-----\ndata"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.PEM_PRIVATE_KEY_DETECTED

    # --- All config formats handled ---

    def test_all_config_kinds_dispatched(self) -> None:
        """No config kind triggers UNSUPPORTED_CONFIG_FORMAT suppression."""
        for kind in FileKind:
            if kind.is_config:
                result = redact_text(text="key = value\n", classification=kind)
                if isinstance(result, SuppressedText):
                    assert result.reason != SuppressionReason.UNSUPPORTED_CONFIG_FORMAT, (
                        f"{kind} still triggers UNSUPPORTED_CONFIG_FORMAT"
                    )

    # --- Format dispatch ---

    def test_env_dispatch(self) -> None:
        result = redact_text(text="DB_PASS=secret123456\n", classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)
        assert "secret123456" not in result.text
        assert result.stats.format_redactions == 1

    def test_ini_dispatch(self) -> None:
        result = redact_text(text="[db]\npass = secret123456\n", classification=FileKind.CONFIG_INI)
        assert isinstance(result, RedactedText)
        assert "secret123456" not in result.text

    def test_ini_properties_mode(self) -> None:
        """path ending .properties triggers properties_mode=True."""
        text = "db.pass=secret123456\\\n  continued\n"
        result = redact_text(
            text=text, classification=FileKind.CONFIG_INI, path="/app/db.properties",
        )
        assert isinstance(result, RedactedText)
        assert "continued" not in result.text

    def test_json_dispatch(self) -> None:
        result = redact_text(text='{"key": "secret"}', classification=FileKind.CONFIG_JSON)
        assert isinstance(result, RedactedText)
        assert "secret" not in result.text
        assert result.stats.format_redactions == 1

    def test_json_desync_suppresses(self) -> None:
        result = redact_text(text="{key: value}", classification=FileKind.CONFIG_JSON)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.FORMAT_DESYNC

    def test_yaml_dispatch(self) -> None:
        result = redact_text(text="host: secret_host\n", classification=FileKind.CONFIG_YAML)
        assert isinstance(result, RedactedText)
        assert "secret_host" not in result.text
        assert result.stats.format_redactions == 1

    def test_toml_dispatch(self) -> None:
        result = redact_text(text='key = "secret"\n', classification=FileKind.CONFIG_TOML)
        assert isinstance(result, RedactedText)
        assert "secret" not in result.text
        assert result.stats.format_redactions == 1

    def test_toml_orphaned_close_still_redacts(self) -> None:
        """Orphaned triple-quote is an excerpt boundary artifact, not desync."""
        result = redact_text(
            text='orphaned\n"""\nkey = "secret"\n', classification=FileKind.CONFIG_TOML,
        )
        assert isinstance(result, RedactedText)
        assert "secret" not in result.text

    # --- Two-stage pipeline ---

    def test_code_generic_only(self) -> None:
        result = redact_text(text="tok=ghp_1234567890abcdefgh\n", classification=FileKind.CODE)
        assert isinstance(result, RedactedText)
        assert "ghp_1234567890abcdefgh" not in result.text
        assert result.stats.format_redactions == 0
        assert result.stats.token_redactions >= 1

    def test_unknown_generic_only(self) -> None:
        result = redact_text(text="password=supersecret123\n", classification=FileKind.UNKNOWN)
        assert isinstance(result, RedactedText)
        assert "supersecret123" not in result.text
        assert result.stats.format_redactions == 0

    # --- 4 footgun pattern tests (D1 Codex review carry-forward) ---

    def test_footgun_suppressed_early_return(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FOOTGUN 1: FormatSuppressed -> SuppressedText, NOT original text with generic scan."""
        monkeypatch.setattr(
            redact_mod, "redact_env",
            lambda text: FormatSuppressed(reason="test_desync"),
        )
        result = redact_text(text="SECRET=hunter2\n", classification=FileKind.CONFIG_ENV)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.FORMAT_DESYNC

    def test_footgun_zero_redactions_still_scans(self) -> None:
        """FOOTGUN 2: redactions_applied=0 must NOT skip generic scan.

        Uses a bare line (no key=) so the ENV format redactor passes it through
        with 0 redactions, then the generic token scanner catches the token.
        """
        text = "Bearer abcdefghijklmnop123456\n"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)
        assert result.stats.format_redactions == 0
        assert result.stats.token_redactions >= 1

    def test_footgun_generic_runs_for_config(self) -> None:
        """FOOTGUN 3a: generic scan runs for is_config=True.

        Uses a bare line (no key=, no # prefix) so the ENV format redactor
        passes it through with 1 value redaction, then the generic token
        scanner catches the ghp token on the bare line.
        """
        text = "KEY=val\nghp_1234567890abcdefgh\n"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)
        assert "ghp_1234567890abcdefgh" not in result.text
        assert result.stats.token_redactions >= 1

    def test_footgun_generic_runs_for_non_config(self) -> None:
        """FOOTGUN 3b: generic scan runs for is_config=False."""
        result = redact_text(text="tok=ghp_1234567890abcdefgh", classification=FileKind.CODE)
        assert isinstance(result, RedactedText)
        assert "ghp_1234567890abcdefgh" not in result.text

    # --- 3 backstop docstring coverage tests ---

    def test_backstop_generic_unconditional(self) -> None:
        """Generic scan runs even when format catches everything."""
        text = "SECRET=ghp_1234567890abcdefgh\n"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)

    def test_backstop_suppressed_no_text(self) -> None:
        """SuppressedText has no text field — impossible to leak original."""
        result = redact_text(text="sensitive", classification=FileKind.CONFIG_JSON)
        assert isinstance(result, SuppressedText)
        assert not isinstance(result, RedactedText)

    def test_backstop_is_config_gates_format_only(self) -> None:
        """is_config gates format parsing, NOT generic redaction."""
        result = redact_text(text="password=supersecret123", classification=FileKind.CODE)
        assert isinstance(result, RedactedText)
        assert "supersecret123" not in result.text
        assert result.stats.format_redactions == 0
        assert result.stats.token_redactions >= 1
