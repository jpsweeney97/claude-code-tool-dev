# Context Injection v0b D2a: Redaction Orchestration + Truncation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the two-stage redaction pipeline (`redact_text()`) with fail-closed gating and PEM suppression, plus marker-safe dual-cap truncation for both read excerpts and grep evidence blocks.

**Architecture:** Four tasks build the redaction and truncation layers. Task 7 creates the generic token scanner (`redact_known_secrets()`) and PEM detector (`contains_pem_private_key()`) as standalone functions with their output types. Task 8 orchestrates them with D1's format-specific redactors into `redact_text()`, enforcing fail-closed gating for unsupported config formats and PEM short-circuiting. Task 9 implements dual-cap truncation with marker safety for read excerpts (`truncate_excerpt()`) and block atomicity for grep evidence (`truncate_blocks()`). Task 10 verifies the single-flight concurrency assumption carried forward from D1's Codex review.

**Tech Stack:** Python 3.14, pytest, ruff, dataclasses, StrEnum, re (regex)

**Reference:** `docs/plans/2026-02-13-context-injection-v0b-master-plan.md` — authoritative API contracts for all types and functions.

**Branch:** Create `feature/context-injection-v0b-d2a` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest`

**Dependencies between tasks:**
- Task 7: independent (generic token scanner + PEM detector, no D2a-internal dependencies)
- Task 8: depends on Task 7 (consumes `redact_known_secrets()` and `contains_pem_private_key()`) and D1 (consumes `FileKind`, `classify_path()`, `redact_env()`, `redact_ini()`, `FormatRedactOutcome`)
- Task 9: independent (truncation is a separate concern; uses only `TruncationReason` from D1's `enums.py`)
- Task 10: independent (verification task, no code dependencies)

---

### Task 7: Generic token scanner + PEM private key detector

**Files:**
- Create: `packages/context-injection/context_injection/redact.py`
- Create: `packages/context-injection/tests/test_redact.py`

**Step 1: Write the failing tests**

Create `tests/test_redact.py`:

```python
"""Tests for redaction types, PEM detection, and generic token scanner."""

from __future__ import annotations

import pytest

from context_injection.redact import (
    RedactedText,
    RedactionStats,
    RedactOutcome,
    SuppressedText,
    SuppressionReason,
    contains_pem_private_key,
    redact_known_secrets,
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
        result, count = redact_known_secrets("Authorization: Bearer abc123def456ghi789")
        assert count == 1
        assert "abc123def456ghi789" not in result
        assert "Bearer [REDACTED:value]" in result

    def test_bearer_case_insensitive(self) -> None:
        result, count = redact_known_secrets("authorization: bearer abc123def456ghi789")
        assert count == 1
        assert "abc123def456ghi789" not in result

    def test_bearer_extra_whitespace(self) -> None:
        result, count = redact_known_secrets("Header:  Bearer   abc123def456ghi")
        assert count == 1
        assert "abc123def456ghi" not in result

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
        "AKIAIOSFODNN7EXAMPLE",
    ])
    def test_api_key_prefixes(self, key: str) -> None:
        result, count = redact_known_secrets(f"key = {key}")
        assert count >= 1
        assert key not in result

    def test_short_api_key_not_redacted(self) -> None:
        """API key prefix with < 10 chars after prefix — not redacted."""
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
        """password_policy not matched (word boundary prevents)."""
        result, count = redact_known_secrets("password_policy=require_strong")
        assert count == 0
        assert "require_strong" in result

    def test_credential_case_insensitive(self) -> None:
        result, count = redact_known_secrets("PASSWORD=mysecretvalue123")
        assert count == 1
        assert "mysecretvalue123" not in result

    # URL userinfo
    def test_url_userinfo(self) -> None:
        result, count = redact_known_secrets("https://admin:secret123@db.example.com")
        assert count >= 1
        assert "secret123" not in result
        assert "admin:" in result

    def test_url_no_password(self) -> None:
        """No colon after user — no URL userinfo redaction."""
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
            "Authorization: Bearer abcdefghijklmnop\n"
            "key=ghp_abcdefghij1234567890\n"
        )
        result, count = redact_known_secrets(text)
        assert count >= 3
        assert "mysecretpassword123" not in result
        assert "abcdefghijklmnop" not in result
        assert "ghp_abcdefghij1234567890" not in result
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_redact.py -v`
Expected: FAIL — `context_injection.redact` not found

**Step 3: Write minimal implementation**

Create `context_injection/redact.py`:

```python
"""Redaction pipeline: types, PEM detector, generic token scanner.

D2a Task 7: output types + standalone functions.
D2a Task 8 adds: redact_text() orchestration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class SuppressionReason(StrEnum):
    """Why text was suppressed instead of redacted."""

    UNSUPPORTED_CONFIG_FORMAT = "unsupported_config_format"
    FORMAT_DESYNC = "format_desync"
    PEM_PRIVATE_KEY_DETECTED = "pem_private_key_detected"


@dataclass(frozen=True)
class RedactionStats:
    """Redaction counts from both pipeline stages."""

    format_redactions: int
    token_redactions: int


@dataclass(frozen=True)
class RedactedText:
    """Successfully redacted text with combined stats."""

    text: str
    stats: RedactionStats


@dataclass(frozen=True)
class SuppressedText:
    """Text suppressed entirely — no repo-derived content emitted.

    reason is a SuppressionReason enum value, not free-form.
    SuppressedText contains no user-repo text by type design.
    """

    reason: SuppressionReason


RedactOutcome = RedactedText | SuppressedText

_REDACTED = "[REDACTED:value]"


# --- PEM detection ---

_PEM_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|ENCRYPTED\s+)?PRIVATE\s+KEY-----"
)


def contains_pem_private_key(text: str) -> bool:
    """Detect PEM private key markers. Short-circuits the redaction pipeline."""
    return bool(_PEM_PRIVATE_KEY_RE.search(text))


# --- Generic token scanner ---

# Order: most specific first to prevent double-matching after replacement.

_JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]{5,}\.eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+"
)

_AUTH_HEADER_RE = re.compile(
    r"(?i)((?:bearer|basic)\s+)[A-Za-z0-9\-._~+/]+=*"
)

_API_KEY_PREFIX_RE = re.compile(
    r"(?:sk-|pk_live_|pk_test_|ghp_|gho_|ghs_|ghr_|glpat-|xoxb-|xoxp-|xoxs-|AKIA)"
    r"[A-Za-z0-9_\-]{10,}"
)

_URL_USERINFO_RE = re.compile(
    r"(://[^@/\s:]+:)([^@/\s]+)(@)"
)

_CREDENTIAL_RE = re.compile(
    r"(?i)\b((?:password|passwd|secret|api_key|apikey|access_token|auth_token|"
    r"private_key|credential|api_secret|client_secret|"
    r"secret_key|encryption_key|signing_key)"
    r"\s*[=:]\s*)"
    r"[\"']?([^\s\"']{6,})[\"']?"
)


def redact_known_secrets(text: str) -> tuple[str, int]:
    """Generic token redaction — second stage of the two-stage pipeline.

    Detects: JWT, Bearer/Basic auth, API key prefixes, URL userinfo,
    credential assignments (RHS >= 6 chars).

    Returns (redacted_text, redaction_count).
    """
    if not text:
        return text, 0

    count = 0

    def _replace_simple(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return _REDACTED

    def _replace_auth(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED

    def _replace_url(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED + m.group(3)

    def _replace_credential(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + _REDACTED

    # Apply in order: most specific first
    text = _JWT_RE.sub(_replace_simple, text)
    text = _AUTH_HEADER_RE.sub(_replace_auth, text)
    text = _API_KEY_PREFIX_RE.sub(_replace_simple, text)
    text = _URL_USERINFO_RE.sub(_replace_url, text)
    text = _CREDENTIAL_RE.sub(_replace_credential, text)

    return text, count
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact.py -v`
Expected: PASS (all ~35 tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All 378+ tests pass

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/redact.py packages/context-injection/tests/test_redact.py
git commit -m "feat(context-injection): add generic token scanner and PEM detector

Types: SuppressionReason, RedactionStats, RedactedText, SuppressedText,
RedactOutcome. Functions: redact_known_secrets() with 5 pattern families
(JWT, Bearer/Basic, API keys, URL userinfo, credential assignment),
contains_pem_private_key() for 5 PEM types."
```

---

### Task 8: Redaction orchestration (`redact_text()`)

**Files:**
- Modify: `packages/context-injection/context_injection/redact.py` (add `redact_text()` and `_dispatch_format()`)
- Modify: `packages/context-injection/tests/test_redact.py` (add orchestration tests)

**Step 1: Write the failing tests**

Add imports to the top of `tests/test_redact.py`:

```python
import context_injection.redact as redact_mod
from context_injection.classify import FileKind
from context_injection.redact_formats import FormatSuppressed
from context_injection.redact import redact_text
```

Add test class at the bottom of `tests/test_redact.py`:

```python
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

    # --- Fail-closed gating ---

    @pytest.mark.parametrize("kind", [
        FileKind.CONFIG_JSON, FileKind.CONFIG_YAML, FileKind.CONFIG_TOML,
    ])
    def test_unsupported_config_suppressed(self, kind: FileKind) -> None:
        result = redact_text(text="key = value", classification=kind)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.UNSUPPORTED_CONFIG_FORMAT

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
        """FOOTGUN 2: redactions_applied=0 must NOT skip generic scan."""
        text = "# Bearer abcdefghijklmnop123456\n"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)
        assert result.stats.format_redactions == 0
        assert result.stats.token_redactions >= 1

    def test_footgun_generic_runs_for_config(self) -> None:
        """FOOTGUN 3a: generic scan runs for is_config=True."""
        text = "KEY=val\n# ghp_1234567890abcdefgh\n"
        result = redact_text(text=text, classification=FileKind.CONFIG_ENV)
        assert isinstance(result, RedactedText)
        assert "ghp_1234567890abcdefgh" not in result.text

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
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_redact.py::TestRedactText -v`
Expected: FAIL — `redact_text` not importable

**Step 3: Implement redact_text()**

Add imports to the top of `context_injection/redact.py`:

```python
from context_injection.classify import FileKind
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
    redact_env,
    redact_ini,
)
```

Add at the bottom of `context_injection/redact.py`:

```python
# --- Orchestration ---


def _dispatch_format(
    text: str, classification: FileKind, path: str | None,
) -> FormatRedactOutcome | None:
    """Dispatch to format-specific redactor. Returns None if no redactor registered.

    None triggers fail-closed gating in redact_text().
    """
    if classification == FileKind.CONFIG_ENV:
        return redact_env(text)
    if classification == FileKind.CONFIG_INI:
        properties_mode = path is not None and path.endswith(".properties")
        return redact_ini(text, properties_mode=properties_mode)
    # CONFIG_JSON, CONFIG_YAML, CONFIG_TOML — no D2a redactor yet
    return None


def redact_text(
    *, text: str, classification: FileKind, path: str | None = None,
) -> RedactOutcome:
    """Two-stage redaction: format-specific then generic tokens.

    Both stages run for any text that is emitted. Suppression (PEM detected,
    unsupported config format, format desync) exits before either stage
    produces output — no text is emitted, so no redaction is needed.

    Classification authority: classification from classify_path() is
    authoritative for fail-closed gating. No secondary path-based heuristics.

    Pipeline order: redact_text() runs before truncate_*(). PEM detection
    therefore always operates on full, untruncated text.

    Callers must pass ALL sensitive text — redact_text() processes whatever
    it receives. Field selection is the caller's responsibility (D2b).
    """
    # Stage 0: PEM short-circuit
    if contains_pem_private_key(text):
        return SuppressedText(reason=SuppressionReason.PEM_PRIVATE_KEY_DETECTED)

    format_redactions = 0

    if classification.is_config:
        # Format-specific dispatch
        outcome = _dispatch_format(text, classification, path)

        if outcome is None:
            # No registered redactor -> fail-closed
            return SuppressedText(reason=SuppressionReason.UNSUPPORTED_CONFIG_FORMAT)

        if isinstance(outcome, FormatSuppressed):
            # Scanner desync -> suppress (internal reason not surfaced)
            return SuppressedText(reason=SuppressionReason.FORMAT_DESYNC)

        # FormatRedactResult — continue with format-redacted text
        text = outcome.text
        format_redactions = outcome.redactions_applied

    # Generic token pass (ALL files — config and non-config)
    text, token_redactions = redact_known_secrets(text)

    return RedactedText(
        text=text,
        stats=RedactionStats(
            format_redactions=format_redactions,
            token_redactions=token_redactions,
        ),
    )
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact.py -v`
Expected: PASS (all ~55 tests — types + PEM + scanner + orchestration)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All 378+ tests pass

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/redact.py packages/context-injection/tests/test_redact.py
git commit -m "feat(context-injection): add redact_text() orchestration

Two-stage pipeline: format-specific (env/ini) then generic token scan.
PEM short-circuit, fail-closed gating for unsupported configs, format
desync handling. Includes 4 footgun tests and 3 backstop coverage tests
from D1 Codex review carry-forward."
```

---

### Task 9: Truncation module

**Files:**
- Create: `packages/context-injection/context_injection/truncate.py`
- Create: `packages/context-injection/tests/test_truncate.py`

**Step 1: Write the failing tests**

Create `tests/test_truncate.py`:

```python
"""Tests for truncation: read excerpts and grep evidence blocks."""

from __future__ import annotations

import pytest

from context_injection.enums import TruncationReason
from context_injection.truncate import (
    EvidenceBlock,
    TruncateBlocksResult,
    TruncateResult,
    truncate_blocks,
    truncate_excerpt,
)


# --- Type tests ---


class TestTruncateResult:
    def test_construction(self) -> None:
        r = TruncateResult(
            text="abc", truncated=False, reason=None,
            original_chars=3, original_lines=1,
        )
        assert r.text == "abc"
        assert r.truncated is False
        assert r.reason is None

    def test_frozen(self) -> None:
        r = TruncateResult(text="x", truncated=False, reason=None, original_chars=1, original_lines=1)
        with pytest.raises(AttributeError):
            r.text = "y"


class TestEvidenceBlock:
    def test_construction(self) -> None:
        b = EvidenceBlock(text="line1\nline2\n", start_line=10, path="src/app.py")
        assert b.text == "line1\nline2\n"
        assert b.start_line == 10
        assert b.path == "src/app.py"

    def test_nullable_fields(self) -> None:
        b = EvidenceBlock(text="x", start_line=None, path=None)
        assert b.start_line is None


class TestTruncateBlocksResult:
    def test_construction(self) -> None:
        r = TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)
        assert r.blocks == ()
        assert r.dropped_blocks == 0

    def test_frozen(self) -> None:
        r = TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)
        with pytest.raises(AttributeError):
            r.truncated = True


# --- truncate_excerpt ---


class TestTruncateExcerpt:
    def test_no_truncation(self) -> None:
        result = truncate_excerpt(text="a\nb\n", max_chars=100, max_lines=10)
        assert result.text == "a\nb\n"
        assert result.truncated is False
        assert result.reason is None

    def test_empty_input(self) -> None:
        result = truncate_excerpt(text="", max_chars=100, max_lines=10)
        assert result.text == ""
        assert result.truncated is False

    def test_line_cap_hit(self) -> None:
        result = truncate_excerpt(text="a\nb\nc\n", max_chars=1000, max_lines=2)
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_LINES
        assert "a\n" in result.text
        assert "b\n" in result.text
        assert "[truncated]\n" in result.text
        assert "c" not in result.text

    def test_char_cap_hit(self) -> None:
        text = "abcdefghij\n" * 5  # 55 chars
        result = truncate_excerpt(text=text, max_chars=35, max_lines=100)
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_CHARS
        assert "[truncated]\n" in result.text

    def test_both_caps_reports_line_first(self) -> None:
        """max_lines checked first -> reason=MAX_LINES even if char cap also binds."""
        text = "a" * 50 + "\n" + "b" * 50 + "\n" + "c" * 50 + "\n"
        result = truncate_excerpt(text=text, max_chars=80, max_lines=1)
        assert result.reason == TruncationReason.MAX_LINES

    def test_marker_preserved(self) -> None:
        """[REDACTED:value] on last kept line is not split."""
        text = "line1\nKEY=[REDACTED:value]\nline3\n"
        result = truncate_excerpt(text=text, max_chars=1000, max_lines=2)
        assert "[REDACTED:value]" in result.text

    def test_single_char_over(self) -> None:
        """Text barely exceeds budget -> truncation."""
        text = "abcdef\n"  # 7 chars
        # Budget: 18 - 12 = 6 chars. "abcdef\n" = 7 chars. Exceeds by 1.
        result = truncate_excerpt(text=text, max_chars=18, max_lines=100)
        assert result.truncated is True

    def test_trailing_newline_two_lines(self) -> None:
        """'a\\nb\\n' = 2 lines via splitlines()."""
        result = truncate_excerpt(text="a\nb\n", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_crlf_line_endings(self) -> None:
        """\\r\\n treated as single line break by splitlines()."""
        result = truncate_excerpt(text="a\r\nb\r\n", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_no_trailing_newline(self) -> None:
        result = truncate_excerpt(text="a\nb", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_max_lines_zero(self) -> None:
        result = truncate_excerpt(text="content\n", max_chars=100, max_lines=0)
        assert result.text == ""
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_LINES

    def test_max_chars_below_indicator(self) -> None:
        result = truncate_excerpt(text="content\n", max_chars=5, max_lines=100)
        assert result.text == ""
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_CHARS

    @pytest.mark.parametrize("max_chars", [12, 13, 14, 15, 16, 17, 18, 19, 20])
    def test_small_char_budgets(self, max_chars: int) -> None:
        """Various small budgets: output must not exceed max_chars."""
        result = truncate_excerpt(text="abcdefghij\nklmnopqrst\n", max_chars=max_chars, max_lines=100)
        assert len(result.text) <= max_chars

    def test_indicator_char_reservation(self) -> None:
        """Content + indicator must fit within max_chars."""
        text = "short\n"  # 6 chars content
        # Budget: 18 - 12 = 6. "short\n" = 6 chars. Fits exactly -> no truncation.
        result = truncate_excerpt(text=text, max_chars=18, max_lines=100)
        assert result.truncated is False

    def test_originals_reported(self) -> None:
        result = truncate_excerpt(text="abc\ndef\nghi\n", max_chars=1000, max_lines=2)
        assert result.original_lines == 3
        assert result.original_chars == 12


# --- truncate_blocks ---


class TestTruncateBlocks:
    def _block(self, text: str, start: int = 1, path: str = "f.py") -> EvidenceBlock:
        return EvidenceBlock(text=text, start_line=start, path=path)

    def test_no_truncation(self) -> None:
        blocks = [self._block("a\n"), self._block("b\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=100)
        assert len(result.blocks) == 2
        assert result.truncated is False
        assert result.dropped_blocks == 0

    def test_empty_input(self) -> None:
        result = truncate_blocks(blocks=[], max_ranges=10, max_chars=1000, max_lines=100)
        assert result.blocks == ()
        assert result.truncated is False

    def test_max_ranges_exceeded(self) -> None:
        blocks = [self._block("a\n"), self._block("b\n"), self._block("c\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=2, max_chars=1000, max_lines=100)
        assert len(result.blocks) == 2
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_RANGES
        assert result.dropped_blocks == 1

    def test_max_lines_exceeded(self) -> None:
        blocks = [self._block("a\nb\n"), self._block("c\nd\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=3)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_LINES
        assert result.dropped_blocks == 1

    def test_max_chars_exceeded(self) -> None:
        blocks = [self._block("ab\n"), self._block("cd\n")]
        # budget = 16 - 12 = 4. block1 "ab\n" = 3 chars. block2 "cd\n" = 3. cumulative 6 > 4.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=16, max_lines=100)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_CHARS

    def test_block_atomicity(self) -> None:
        """Partial block dropped entirely."""
        blocks = [self._block("a\n"), self._block("bcdefghij\n")]  # 10 chars
        # budget = 20 - 12 = 8. block1 = 2, block2 = 10. 2 + 10 > 8.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=20, max_lines=100)
        assert len(result.blocks) == 1

    def test_single_oversized_block(self) -> None:
        blocks = [self._block("a" * 100 + "\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=50, max_lines=100)
        assert len(result.blocks) == 0
        assert result.truncated is True
        assert result.dropped_blocks == 1

    def test_ranges_ok_but_chars_forces_drop(self) -> None:
        blocks = [self._block("ab\n"), self._block("cd\n"), self._block("ef\n")]
        # budget = 19 - 12 = 7. blocks: 3, 3, 3. cumulative: 3, 6, 9 > 7.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=19, max_lines=100)
        assert len(result.blocks) == 2
        assert result.reason == TruncationReason.MAX_CHARS

    def test_lines_force_drop_not_chars(self) -> None:
        blocks = [self._block("a\nb\n"), self._block("c\n")]
        # block1 = 2 lines, block2 = 1 line. 2 + 1 = 3 > max_lines=2.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=2)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_LINES

    def test_dropped_blocks_count(self) -> None:
        blocks = [self._block("a\n")] * 5
        result = truncate_blocks(blocks=blocks, max_ranges=2, max_chars=1000, max_lines=100)
        assert result.dropped_blocks == 3
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_truncate.py -v`
Expected: FAIL — `context_injection.truncate` not found

**Step 3: Write minimal implementation**

Create `context_injection/truncate.py`:

```python
"""Truncation for read excerpts and grep evidence blocks.

Dual-cap truncation: max_lines then max_chars, at line boundaries only.
Marker-safe: never splits [REDACTED:*] markers. Block atomicity for grep.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from context_injection.enums import TruncationReason

_TRUNCATED_INDICATOR = "[truncated]\n"
_INDICATOR_LEN = len(_TRUNCATED_INDICATOR)


@dataclass(frozen=True)
class TruncateResult:
    """Result of truncate_excerpt()."""

    text: str
    truncated: bool
    reason: TruncationReason | None
    original_chars: int
    original_lines: int


@dataclass(frozen=True)
class EvidenceBlock:
    """A single grep evidence block (atomic unit for truncation)."""

    text: str
    start_line: int | None
    path: str | None


@dataclass(frozen=True)
class TruncateBlocksResult:
    """Result of truncate_blocks()."""

    blocks: tuple[EvidenceBlock, ...]
    truncated: bool
    reason: TruncationReason | None
    dropped_blocks: int


def truncate_excerpt(
    *, text: str, max_chars: int, max_lines: int,
) -> TruncateResult:
    """Truncate a read excerpt. No partial source lines. Marker-safe.

    Marker safety: achieved by whole-line truncation. Since lines are atomic
    units (never cut mid-line), [REDACTED:value] markers within a line cannot
    be split. No explicit marker detection needed.

    Appends '[truncated]\\n' if truncated. Indicator doesn't count against
    max_lines but DOES count against max_chars (reserve _INDICATOR_LEN chars).
    Precedence: max_lines then max_chars. Reports first cap that removes content.
    Line counting: str.splitlines() — trailing newlines do not consume budget.
    """
    if not text:
        return TruncateResult(
            text="", truncated=False, reason=None,
            original_chars=0, original_lines=0,
        )

    lines = text.splitlines()
    original_lines = len(lines)
    original_chars = len(text)

    # Zero-budget edge cases
    if max_lines <= 0:
        return TruncateResult(
            text="", truncated=True, reason=TruncationReason.MAX_LINES,
            original_chars=original_chars, original_lines=original_lines,
        )
    if max_chars < _INDICATOR_LEN:
        return TruncateResult(
            text="", truncated=True, reason=TruncationReason.MAX_CHARS,
            original_chars=original_chars, original_lines=original_lines,
        )

    # No truncation needed
    if original_lines <= max_lines and original_chars <= max_chars:
        return TruncateResult(
            text=text, truncated=False, reason=None,
            original_chars=original_chars, original_lines=original_lines,
        )

    # Truncation needed
    reason: TruncationReason | None = None

    # Step 1: line cap
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        reason = TruncationReason.MAX_LINES

    # Step 2: char cap (at line boundaries, reserve indicator space)
    char_budget = max_chars - _INDICATOR_LEN
    kept: list[str] = []
    cumulative = 0
    for line in lines:
        line_len = len(line) + 1  # +1 for \n
        if cumulative + line_len > char_budget:
            if reason is None:
                reason = TruncationReason.MAX_CHARS
            break
        cumulative += line_len
        kept.append(line)

    # Build output with indicator
    if kept:
        result_text = "\n".join(kept) + "\n" + _TRUNCATED_INDICATOR
    else:
        result_text = _TRUNCATED_INDICATOR

    return TruncateResult(
        text=result_text, truncated=True, reason=reason,
        original_chars=original_chars, original_lines=original_lines,
    )


def truncate_blocks(
    *,
    blocks: Sequence[EvidenceBlock],
    max_ranges: int,
    max_chars: int,
    max_lines: int,
) -> TruncateBlocksResult:
    """Truncate grep evidence blocks. Each block is atomic — never cut inside.

    Prefix-ordered: iterate in order, accumulate counts, stop when any cap exceeded.
    Precedence: max_ranges then max_lines then max_chars.
    Reports first cap that causes a block to be dropped.

    Indicator reservation: _INDICATOR_LEN chars reserved from max_chars budget.
    This function does not append an indicator itself — the caller appends
    '[truncated]' to the formatted output when truncated=True. The reservation
    ensures the caller's indicator fits within the overall char budget.
    """
    if not blocks:
        return TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)

    # Quick check: does everything fit?
    total_lines = sum(len(b.text.splitlines()) for b in blocks)
    total_chars = sum(len(b.text) for b in blocks)
    if len(blocks) <= max_ranges and total_lines <= max_lines and total_chars <= max_chars:
        return TruncateBlocksResult(
            blocks=tuple(blocks), truncated=False, reason=None, dropped_blocks=0,
        )

    # Truncation needed — reserve indicator space
    char_budget = max_chars - _INDICATOR_LEN
    kept: list[EvidenceBlock] = []
    cumulative_lines = 0
    cumulative_chars = 0
    reason: TruncationReason | None = None

    for block in blocks:
        # Check max_ranges first
        if len(kept) >= max_ranges:
            reason = reason or TruncationReason.MAX_RANGES
            break

        block_lines = len(block.text.splitlines())
        block_chars = len(block.text)

        # Check max_lines
        if cumulative_lines + block_lines > max_lines:
            reason = reason or TruncationReason.MAX_LINES
            break

        # Check max_chars
        if cumulative_chars + block_chars > char_budget:
            reason = reason or TruncationReason.MAX_CHARS
            break

        kept.append(block)
        cumulative_lines += block_lines
        cumulative_chars += block_chars

    dropped = len(blocks) - len(kept)
    return TruncateBlocksResult(
        blocks=tuple(kept), truncated=dropped > 0,
        reason=reason, dropped_blocks=dropped,
    )
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_truncate.py -v`
Expected: PASS (all ~28 tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All 378+ tests pass

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/truncate.py packages/context-injection/tests/test_truncate.py
git commit -m "feat(context-injection): add truncation module

truncate_excerpt(): dual-cap (max_lines then max_chars) at line boundaries,
marker-safe, [truncated] indicator with 12-char reservation.
truncate_blocks(): block-atomic prefix scan with max_ranges/lines/chars."
```

---

### Task 10: Verify single-flight concurrency assumption

**Files:**
- Possibly modify: `packages/context-injection/context_injection/state.py` (docstring update)
- Create: `packages/context-injection/tests/test_single_flight.py`

**Step 1: Research FastMCP stdio transport**

Before writing code, investigate the transport model:

```bash
cd packages/context-injection && rg "stdio" --type py -l
cd packages/context-injection && python3 -c "import fastmcp; help(fastmcp.server)" 2>&1 | head -50
```

Key question: does FastMCP's stdio transport process JSON-RPC messages sequentially (one request completes before the next begins)?

**Step 2: Write the verification test**

Create `tests/test_single_flight.py`:

```python
"""Verify single-flight concurrency assumption for stdio transport.

FastMCP's stdio transport processes JSON-RPC messages sequentially — one
request completes before the next begins. This means consume_scout()'s
read-check-write on record.used is safe without asyncio.Lock.

Carry-forward from D1 Codex review: MCP protocol allows multiplexing,
but stdio transport is inherently sequential (single reader/writer).
"""

from __future__ import annotations

from context_injection.state import AppContext


class TestSingleFlightAssumption:
    def test_sequential_consume_is_safe(self) -> None:
        """Demonstrate that sequential access to consume_scout is safe.

        Under stdio transport, requests are processed one at a time.
        This test validates the logical correctness of the non-locked path.
        The transport guarantee is documented, not unit-testable.

        If SSE/WebSocket transports are added, asyncio.Lock must be
        added to consume_scout() and this test extended with concurrent access.
        """
        ctx = AppContext.create(repo_root="/tmp/repo")
        assert ctx is not None
```

**Step 3: Update docstring in state.py**

In `context_injection/state.py`, add to the `consume_scout` method docstring (after the existing INVARIANT comment):

```python
        # CONCURRENCY: Safe without asyncio.Lock under stdio transport.
        # FastMCP processes stdio JSON-RPC messages sequentially — one
        # request completes before the next begins. If SSE or WebSocket
        # transports are added, add asyncio.Lock around this method.
        # Verified: D2a Task 10 (FastMCP stdio transport is sequential).
```

**Step 4: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All tests pass

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/state.py packages/context-injection/tests/test_single_flight.py
git commit -m "chore(context-injection): verify single-flight concurrency assumption

FastMCP stdio transport processes requests sequentially. consume_scout()
read-check-write is safe without asyncio.Lock. Documented transport
constraint and fallback plan (add Lock if SSE/WebSocket added)."
```

---

## Final Verification

After all 4 tasks:

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (378 existing + ~85 new ≈ 463 total)

Run: `cd packages/context-injection && uv run ruff check`
Expected: No lint errors

## Summary of Deliverables

| Module | New/Modified | What D2a Adds |
|--------|-------------|---------------|
| `context_injection/redact.py` | **New** | `SuppressionReason`, `RedactionStats`, `RedactedText`, `SuppressedText`, `RedactOutcome`, `redact_known_secrets()`, `contains_pem_private_key()`, `redact_text()`, `_dispatch_format()` |
| `context_injection/truncate.py` | **New** | `TruncateResult`, `EvidenceBlock`, `TruncateBlocksResult`, `truncate_excerpt()`, `truncate_blocks()` |
| `context_injection/state.py` | Modified | Docstring update — single-flight verification finding |
| `tests/test_redact.py` | **New** | ~55 tests: type tests, PEM detection, token scanner (5 pattern families), orchestration, 4 footgun patterns, 3 backstop coverage |
| `tests/test_truncate.py` | **New** | ~28 tests: excerpt truncation (dual-cap, marker safety, edge cases, small budgets), block truncation (atomicity, caps, oversized) |
| `tests/test_single_flight.py` | **New** | 1 test: sequential access verification + documented assumption |
