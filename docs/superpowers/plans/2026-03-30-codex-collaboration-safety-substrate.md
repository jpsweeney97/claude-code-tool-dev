# T-03: Codex-Collaboration Safety Substrate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the cross-model safety substrate (credential scanning, tool-input safety policy, consultation profiles, learning retrieval) into codex-collaboration, upgrade the existing redaction boundary to use the shared taxonomy, and wire the benchmark contract into the spec reading order.

**Architecture:** Two-boundary safety model. Outer boundary: PreToolUse hook (`codex_guard.py`) scans raw MCP tool arguments and blocks via exit 2 + stderr (Claude Code ignores JSON on exit 2; fail-closed on parse errors). Inner boundary: `context_assembly._redact_text()` sanitizes all server-injected content (file excerpts, learnings, summaries) using the shared secret taxonomy with per-match placeholder bypass before Codex sees it. Profiles resolve to execution controls (effort, posture, turn_budget) via a plugin-owned resolver; sandbox/approval remain gated, phased profiles explicitly rejected, until freeze-and-rotate and phase-progression support exist respectively.

**Tech Stack:** Python 3.14, pytest, YAML (consultation profiles), Claude Code plugin hooks

**Spec/implementation note:** `foundations.md:133` says the hook guard "validates the final packet produced by the control plane," but Claude Code's PreToolUse fires before the MCP tool executes. The hook sees raw tool args, not the assembled packet. The inner boundary (`_redact_text`) handles assembled content. This plan implements the practical architecture, not the spec's idealized description.

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `server/secret_taxonomy.py` | Pattern families with tiered enforcement, placeholder bypass |
| `server/credential_scan.py` | Tiered egress scanner consuming taxonomy |
| `server/consultation_safety.py` | Policy-driven tool-input traversal and scanning |
| `server/profiles.py` | Profile resolver: YAML loading, local overrides, validation gate |
| `server/retrieve_learnings.py` | Learning retrieval for briefing injection |
| `scripts/codex_guard.py` | PreToolUse hook script (fail-closed outer boundary) |
| `references/consultation-profiles.yaml` | Named consultation profiles |
| `tests/test_secret_taxonomy.py` | Taxonomy tests |
| `tests/test_credential_scan.py` | Scanner tests |
| `tests/test_consultation_safety.py` | Safety policy tests |
| `tests/test_profiles.py` | Profile resolver tests |
| `tests/test_retrieve_learnings.py` | Learning retrieval tests |
| `tests/test_codex_guard.py` | Hook guard tests |

### Modified files

| File | Change |
|------|--------|
| `server/context_assembly.py:54-80,393-397` | Replace inline `_SECRET_PATTERNS` with taxonomy-backed per-match redaction |
| `server/context_assembly.py:94-120` | Wire learning retrieval into packet assembly via `_build_text_entries()` |
| `server/runtime.py:109-130` | Accept `effort` parameter on `run_turn()` |
| `server/control_plane.py:130-206` | Thread profile/effort through consult dispatch |
| `server/models.py:32-48` | Add `profile` field to `ConsultRequest` |
| `server/models.py:157-172` | Add `resolved_posture`, `resolved_effort`, `resolved_turn_budget` to `CollaborationHandle` |
| `server/mcp_server.py:28-38` | Expose `profile` in `codex.consult` and `codex.dialogue.start` tool schemas |
| `server/dialogue.py:64-142` | Accept profile on `start()`, resolve and persist on handle |
| `server/dialogue.py:144-234` | Read stored profile from handle, pass effort/posture to assembly + runtime |
| `server/prompt_builder.py:40-47` | Accept and embed posture in prompt text |
| `hooks/hooks.json` | Add PreToolUse hook entry for `codex_guard.py` with matcher-group schema |
| `docs/superpowers/specs/codex-collaboration/contracts.md:35-51` | Add 3 optional profile fields to CollaborationHandle table |
| `tests/test_context_assembly.py` | Update tests for taxonomy-backed redaction + learnings-in-briefing regression |
| `tests/test_models_r2.py:39-53` | Update handle serialization test for 13 fields |
| `tests/test_dialogue.py` | Add profile persistence + crash-recovery replay tests |

---

## Task 1: Secret Taxonomy

**Files:**
- Create: `server/secret_taxonomy.py`
- Create: `tests/test_secret_taxonomy.py`

- [ ] **Step 1: Write taxonomy tests**

```python
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
        text = f"for example AKIAIOSFODNN7EXAMPLE"
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_secret_taxonomy.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.secret_taxonomy'`

- [ ] **Step 3: Implement secret_taxonomy.py**

Port from `packages/plugins/cross-model/scripts/secret_taxonomy.py`. The module is self-contained — zero internal dependencies. Copy the exact pattern definitions, `SecretFamily` dataclass, `check_placeholder_bypass()` function, and `FAMILIES` tuple. Remove the CLI `__main__` block if present.

```python
"""Shared secret pattern taxonomy for egress scanning and redaction.

Ported from cross-model/scripts/secret_taxonomy.py. Semantic source only —
the codex-collaboration package owns this copy.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT, Basic Auth).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow telemetry only. No blocking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Tier = Literal["strict", "contextual", "broad"]
PLACEHOLDER_BYPASS_WINDOW = 100

PLACEHOLDER_BYPASS_WORDS = [
    "format",
    "example",
    "looks",
    "placeholder",
    "dummy",
    "sample",
    "suppose",
    "hypothetical",
    "redact",
    "redacted",
    "your-",
    "my-",
    "[redacted",
]


@dataclass(frozen=True)
class SecretFamily:
    """Pattern family with independent egress and redaction controls."""

    name: str
    pattern: re.Pattern[str]
    tier: Tier
    placeholder_bypass: list[str]
    redact_template: str
    redact_enabled: bool
    egress_enabled: bool


def check_placeholder_bypass(text: str, family: SecretFamily) -> bool:
    """Return True when placeholder/example language appears near a match.

    If ``text`` contains one or more family matches, each match is evaluated
    against a 100-character window. If no match is present, ``text`` is
    treated as a pre-sliced window.
    """
    if not family.placeholder_bypass:
        return False

    bypass_words = tuple(word.lower() for word in family.placeholder_bypass)
    matches = list(family.pattern.finditer(text))
    if not matches:
        context = text.lower()
        return any(word in context for word in bypass_words)

    for match in matches:
        start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
        end = min(len(text), match.end() + PLACEHOLDER_BYPASS_WINDOW)
        context = text[start:end].lower()
        if any(word in context for word in bypass_words):
            return True
    return False


FAMILIES: tuple[SecretFamily, ...] = (
    SecretFamily(
        name="aws_access_key_id",
        pattern=re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        tier="strict",
        placeholder_bypass=[],
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="pem_private_key",
        pattern=re.compile(
            r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|ENCRYPTED\s+)?PRIVATE\s+KEY-----"
        ),
        tier="strict",
        placeholder_bypass=[],
        redact_template="[REDACTED:value]",
        redact_enabled=False,
        egress_enabled=True,
    ),
    SecretFamily(
        name="jwt_token",
        pattern=re.compile(
            r"\beyJ[A-Za-z0-9_-]{5,}\.eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b"
        ),
        tier="strict",
        placeholder_bypass=[],
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="basic_auth_header",
        pattern=re.compile(
            r"(?i)(authorization\s*:\s*basic\s+)([A-Za-z0-9+/=]{8,})"
        ),
        tier="strict",
        placeholder_bypass=[],
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="github_pat",
        pattern=re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="gitlab_pat",
        pattern=re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="stripe_publishable_key",
        pattern=re.compile(r"\b(?:pk_live|pk_test)_[A-Za-z0-9]{24,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="openai_api_key",
        pattern=re.compile(r"\bsk-[A-Za-z0-9]{40,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="bearer_auth_header",
        pattern=re.compile(
            r"(?i)((?:authorization\s*:\s*)?bearer\s+)([A-Za-z0-9\-._~+/]{20,}=*)"
        ),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="url_userinfo",
        pattern=re.compile(r"(://[^@/\s:]+:)([^@/\s]{6,})(@)"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]\3",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_bot_token",
        pattern=re.compile(r"\bxoxb-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_user_token",
        pattern=re.compile(r"\bxoxp-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="slack_session_token",
        pattern=re.compile(r"\bxoxs-[A-Za-z0-9-]{10,}\b"),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template="[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="credential_assignment_strong",
        pattern=re.compile(
            r"(?im)^[\t ]*(?:export\s+)?"
            r"((?:api_key|apikey|api_secret|client_secret|"
            r"private_key|secret_key|encryption_key|signing_key|"
            r"access_token|auth_token)[^\S\n]*[=:][^\S\n]*)"
            r"[\"']?([^\s\"']{6,})[\"']?"
        ),
        tier="contextual",
        placeholder_bypass=list(PLACEHOLDER_BYPASS_WORDS),
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
    SecretFamily(
        name="credential_assignment",
        pattern=re.compile(
            r"(?i)((?:password|passwd|secret|credential)\s*[=:]\s*)"
            r"[\"']?([^\s\"']{6,})[\"']?"
        ),
        tier="broad",
        placeholder_bypass=[],
        redact_template=r"\1[REDACTED:value]",
        redact_enabled=True,
        egress_enabled=True,
    ),
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_secret_taxonomy.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add server/secret_taxonomy.py tests/test_secret_taxonomy.py
git commit -m "feat(codex-collaboration): add secret pattern taxonomy (T-03 AC2)"
```

---

## Task 2: Credential Scanner

**Files:**
- Create: `server/credential_scan.py`
- Create: `tests/test_credential_scan.py`

- [ ] **Step 1: Write scanner tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_credential_scan.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.credential_scan'`

- [ ] **Step 3: Implement credential_scan.py**

Port from `packages/plugins/cross-model/scripts/credential_scan.py`. Remove the conditional `if __package__` import pattern — use direct relative import.

```python
"""Tiered credential scanner for advisory tool calls.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow telemetry only. No blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .secret_taxonomy import (
    FAMILIES,
    PLACEHOLDER_BYPASS_WINDOW,
    check_placeholder_bypass,
)


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning text for credentials."""

    action: Literal["allow", "block", "shadow"]
    tier: str | None
    reason: str | None


def _families_for_tier(tier: str) -> tuple:
    return tuple(
        family
        for family in FAMILIES
        if family.egress_enabled and family.tier == tier
    )


_STRICT_FAMILIES = _families_for_tier("strict")
_CONTEXTUAL_FAMILIES = _families_for_tier("contextual")
_BROAD_FAMILIES = _families_for_tier("broad")


def scan_text(text: str) -> ScanResult:
    """Scan text for credentials. Returns on first match.

    Priority: strict > contextual > broad > allow.
    """
    for family in _STRICT_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="block",
                tier="strict",
                reason=f"strict:{family.name}",
            )

    for family in _CONTEXTUAL_FAMILIES:
        for match in family.pattern.finditer(text):
            start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
            end = min(len(text), match.end() + PLACEHOLDER_BYPASS_WINDOW)
            if not check_placeholder_bypass(text[start:end], family):
                return ScanResult(
                    action="block",
                    tier="contextual",
                    reason=f"contextual:{family.name}",
                )

    for family in _BROAD_FAMILIES:
        if family.pattern.search(text):
            return ScanResult(
                action="shadow",
                tier="broad",
                reason=f"broad:{family.name}",
            )

    return ScanResult(action="allow", tier=None, reason=None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_credential_scan.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add server/credential_scan.py tests/test_credential_scan.py
git commit -m "feat(codex-collaboration): add tiered credential scanner (T-03 AC1)"
```

---

## Task 3: Upgrade Inner Redaction Boundary

**Files:**
- Modify: `server/context_assembly.py:54-80,242-256,393-397`
- Modify: existing `tests/test_context_assembly.py`

This task replaces the 8 inline `_SECRET_PATTERNS` with taxonomy-backed redaction using `secret_taxonomy.FAMILIES`. Also adds `_redact_text()` on `repo_identity.branch` in `_render_packet()`.

- [ ] **Step 1: Write tests for taxonomy-backed redaction**

Add to the existing test file. These test that the upgraded `_redact_text` catches patterns the old inline set missed (e.g., GitLab PAT, Slack tokens, JWT, strong credential assignment).

```python
class TestTaxonomyBackedRedaction:
    """Verify _redact_text uses the full secret taxonomy."""

    def test_aws_key_redacted(self) -> None:
        from server.context_assembly import _redact_text
        result = _redact_text("key is AKIAIOSFODNN7EXAMPLE here")
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED:value]" in result

    def test_gitlab_pat_redacted(self) -> None:
        from server.context_assembly import _redact_text
        pat = "glpat-" + "A" * 20
        result = _redact_text(f"export TOKEN={pat}")
        assert pat not in result

    def test_slack_bot_token_redacted(self) -> None:
        from server.context_assembly import _redact_text
        result = _redact_text("token xoxb-1234567890-abcdef")
        assert "xoxb-" not in result

    def test_jwt_redacted(self) -> None:
        from server.context_assembly import _redact_text
        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        result = _redact_text(f"token: {jwt}")
        assert jwt not in result

    def test_placeholder_context_not_redacted(self) -> None:
        from server.context_assembly import _redact_text
        pat = "ghp_" + "A" * 36
        text = f"for example the format is {pat}"
        result = _redact_text(text)
        # Contextual family with placeholder bypass — should NOT redact
        assert pat in result

    def test_per_match_bypass_does_not_suppress_real_tokens(self) -> None:
        """One example token must not suppress redaction of a real token in the same string."""
        from server.context_assembly import _redact_text
        pat = "ghp_" + "A" * 36
        real_pat = "ghp_" + "B" * 36
        # First occurrence has "example" nearby, second does not
        text = f"example format: {pat}\nproduction: {real_pat}"
        result = _redact_text(text)
        # Example token kept, real token redacted
        assert pat in result
        assert real_pat not in result

    def test_clean_text_unchanged(self) -> None:
        from server.context_assembly import _redact_text
        text = "This is a normal code review comment."
        assert _redact_text(text) == text

    def test_branch_name_redacted_in_render(self) -> None:
        """repo_identity.branch passes through _redact_text."""
        from server.context_assembly import _redact_text
        # A branch name containing a secret pattern should be redacted
        branch = "feature/password=hunter2abc"
        result = _redact_text(branch)
        assert "hunter2abc" not in result
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_context_assembly.py::TestTaxonomyBackedRedaction -v`
Expected: FAIL on GitLab PAT, Slack, JWT tests (old patterns don't cover them)

- [ ] **Step 3: Replace _SECRET_PATTERNS with taxonomy-backed redaction**

In `server/context_assembly.py`, replace lines 54-80 (the `_SECRET_PATTERNS` tuple) and lines 393-397 (the `_redact_text` function):

Remove:
```python
_SECRET_PATTERNS: tuple[
    tuple[re.Pattern[str], str | Callable[[re.Match[str]], str]],
    ...,
] = (
    ... all 8 patterns ...
)
```

Replace `_redact_text` with:
```python
def _redact_text(value: str) -> str:
    """Redact secrets using the shared taxonomy with per-match placeholder bypass.

    Contextual families check each match independently against its local
    100-char window. A placeholder near one match does NOT suppress redaction
    of other matches of the same family elsewhere in the string.

    Templates that use backreferences (e.g. r"\\1[REDACTED:value]\\3") are
    expanded via match.expand() so capture groups resolve correctly inside
    the replacement function.
    """
    from .secret_taxonomy import FAMILIES, PLACEHOLDER_BYPASS_WINDOW

    redacted = value
    for family in FAMILIES:
        if not family.redact_enabled:
            continue
        if family.tier == "contextual" and family.placeholder_bypass:
            # Per-match bypass: each match is independently checked against
            # its local window. A placeholder near one match does NOT suppress
            # redaction of other matches in the same string.
            bypass_words = tuple(w.lower() for w in family.placeholder_bypass)

            def _replace(match: re.Match[str], _bw: tuple[str, ...] = bypass_words) -> str:
                start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
                end = min(len(redacted), match.end() + PLACEHOLDER_BYPASS_WINDOW)
                context = redacted[start:end].lower()
                if any(word in context for word in _bw):
                    return match.group(0)  # Keep original — placeholder context
                return match.expand(family.redact_template)

            redacted = family.pattern.sub(_replace, redacted)
        else:
            # Strict/broad tiers: always redact, no bypass
            redacted = family.pattern.sub(family.redact_template, redacted)
    return redacted
```

Also add `_redact_text` to the `repo_identity.branch` field in `_render_packet()`. Change line 254:

```python
"branch": repo_identity.branch,
```

to:

```python
"branch": _redact_text(repo_identity.branch),
```

Remove the now-unused imports: `Callable` (if only used by `_SECRET_PATTERNS` type hint), and the `_replace_prefixed_secret`/`_replace_url_userinfo` helper functions (lines 46-51).

- [ ] **Step 4: Run ALL context assembly tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_context_assembly.py -v`
Expected: all PASS (existing tests + new taxonomy tests). Some existing tests may need adjustments if they assert on the exact `[redacted]` placeholder text (old) vs `[REDACTED:value]` (new taxonomy template).

- [ ] **Step 5: Commit**

```bash
git add server/context_assembly.py tests/test_context_assembly.py
git commit -m "feat(codex-collaboration): upgrade inner redaction to shared taxonomy (T-03 AC1/AC2)"
```

---

## Task 4: Tool-Input Safety Policy

**Files:**
- Create: `server/consultation_safety.py`
- Create: `tests/test_consultation_safety.py`

- [ ] **Step 1: Write safety policy tests**

```python
"""Tests for tool-input safety policy."""

from __future__ import annotations

import pytest

from server.consultation_safety import (
    CONSULT_POLICY,
    DIALOGUE_REPLY_POLICY,
    DIALOGUE_START_POLICY,
    SafetyVerdict,
    ToolInputLimitExceeded,
    ToolScanPolicy,
    check_tool_input,
    extract_strings,
    policy_for_tool,
)


class TestPolicyRouting:
    def test_consult_tool_returns_consult_policy(self) -> None:
        policy = policy_for_tool(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult"
        )
        assert policy is CONSULT_POLICY

    def test_dialogue_reply_returns_reply_policy(self) -> None:
        policy = policy_for_tool(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply"
        )
        assert policy is DIALOGUE_REPLY_POLICY

    def test_dialogue_start_returns_start_policy(self) -> None:
        policy = policy_for_tool(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.start"
        )
        assert policy is DIALOGUE_START_POLICY

    def test_unknown_tool_returns_consult_policy(self) -> None:
        policy = policy_for_tool("mcp__unknown__tool")
        assert policy is CONSULT_POLICY


class TestExtractStrings:
    def test_content_fields_extracted(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"repo_root"},
            content_fields={"objective"},
        )
        texts, unexpected = extract_strings(
            {"repo_root": "/tmp", "objective": "check this"}, policy
        )
        assert texts == ["check this"]
        assert unexpected == []

    def test_expected_fields_skipped(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"repo_root"},
            content_fields={"objective"},
        )
        texts, _ = extract_strings(
            {"repo_root": "/tmp/secret", "objective": "hello"}, policy
        )
        assert "/tmp/secret" not in texts

    def test_unknown_fields_scanned_by_default(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields=set(),
            scan_unknown_fields=True,
        )
        texts, unexpected = extract_strings({"surprise": "value"}, policy)
        assert texts == ["value"]
        assert "surprise" in unexpected

    def test_unknown_fields_skipped_when_disabled(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields=set(),
            scan_unknown_fields=False,
        )
        texts, unexpected = extract_strings({"surprise": "value"}, policy)
        assert texts == []
        assert "surprise" in unexpected

    def test_nested_dicts_traversed(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"data"},
        )
        texts, _ = extract_strings(
            {"data": {"nested": {"deep": "found"}}}, policy
        )
        assert "found" in texts

    def test_lists_traversed(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"items"},
        )
        texts, _ = extract_strings({"items": ["a", "b"]}, policy)
        assert texts == ["a", "b"]

    def test_node_cap_raises(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"data"},
        )
        huge = {"data": list(range(20000))}
        with pytest.raises(ToolInputLimitExceeded):
            extract_strings(huge, policy)

    def test_char_cap_raises(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"data"},
        )
        big_string = "x" * (300 * 1024)
        with pytest.raises(ToolInputLimitExceeded):
            extract_strings({"data": big_string}, policy)


class TestCheckToolInput:
    def test_clean_input_allows(self) -> None:
        verdict = check_tool_input(
            {"objective": "review architecture", "repo_root": "/tmp"},
            CONSULT_POLICY,
        )
        assert verdict.action == "allow"

    def test_strict_secret_blocks(self) -> None:
        verdict = check_tool_input(
            {"objective": "use AKIAIOSFODNN7EXAMPLE", "repo_root": "/tmp"},
            CONSULT_POLICY,
        )
        assert verdict.action == "block"
        assert verdict.tier == "strict"

    def test_contextual_secret_blocks(self) -> None:
        key = "sk-" + "a" * 40
        verdict = check_tool_input(
            {"objective": f"key is {key}", "repo_root": "/tmp"},
            CONSULT_POLICY,
        )
        assert verdict.action == "block"
        assert verdict.tier == "contextual"

    def test_placeholder_context_allows(self) -> None:
        key = "sk-" + "a" * 40
        verdict = check_tool_input(
            {"objective": f"example format: {key}", "repo_root": "/tmp"},
            CONSULT_POLICY,
        )
        assert verdict.action == "allow"

    def test_worst_verdict_wins(self) -> None:
        pat = "ghp_" + "A" * 36
        verdict = check_tool_input(
            {"objective": f"AKIAIOSFODNN7EXAMPLE and {pat}", "repo_root": "/tmp"},
            CONSULT_POLICY,
        )
        assert verdict.action == "block"
        assert verdict.tier == "strict"

    def test_profile_field_is_scanned(self) -> None:
        """profile is a content_field — credentials in profile names are caught."""
        verdict = check_tool_input(
            {"objective": "clean review", "repo_root": "/tmp", "profile": "AKIAIOSFODNN7EXAMPLE"},
            CONSULT_POLICY,
        )
        assert verdict.action == "block"

    def test_dialogue_start_profile_scanned(self) -> None:
        """profile in dialogue.start is also scanned."""
        verdict = check_tool_input(
            {"repo_root": "/tmp", "profile": "sk-" + "a" * 40},
            DIALOGUE_START_POLICY,
        )
        assert verdict.action == "block"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_consultation_safety.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement consultation_safety.py**

Port from `packages/plugins/cross-model/scripts/consultation_safety.py`. Key changes:
- Direct relative import instead of conditional `if __package__`
- Remap tool names from cross-model to codex-collaboration MCP names
- Rename policies: `START_POLICY` → `CONSULT_POLICY`, add `DIALOGUE_START_POLICY`, `DIALOGUE_REPLY_POLICY`

```python
"""Tool-input safety policy for codex-collaboration advisory flows.

Policy-driven traversal and credential scanning of MCP tool arguments.
The hook guard (codex_guard.py) calls this module to validate raw tool
input before the MCP server processes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .credential_scan import scan_text

_NODE_CAP = 10_000
_CHAR_CAP = 256 * 1024


@dataclass(frozen=True)
class ToolScanPolicy:
    """Controls which tool_input fields are scanned for egress secrets."""

    expected_fields: set[str]
    content_fields: set[str]
    scan_unknown_fields: bool = True


class ToolInputLimitExceeded(RuntimeError):
    """Raised when tool_input traversal exceeds configured safety caps."""


CONSULT_POLICY = ToolScanPolicy(
    expected_fields={"repo_root", "explicit_paths"},
    content_fields={"objective", "profile"},
)

DIALOGUE_START_POLICY = ToolScanPolicy(
    expected_fields={"repo_root"},
    content_fields={"profile"},
)

DIALOGUE_REPLY_POLICY = ToolScanPolicy(
    expected_fields={"collaboration_id", "explicit_paths"},
    content_fields={"objective"},
    # Actual reply schema: collaboration_id, objective, explicit_paths.
    # No profile (stored on handle), no repo_root (not in reply schema),
    # no message/supplementary_context (not yet exposed — forward-looking
    # fields removed to match the real tool surface).
)

_TOOL_POLICY_MAP: dict[str, ToolScanPolicy] = {
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult": CONSULT_POLICY,
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.start": DIALOGUE_START_POLICY,
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply": DIALOGUE_REPLY_POLICY,
}


def policy_for_tool(tool_name: str) -> ToolScanPolicy:
    """Return the scan policy for a given MCP tool name."""
    return _TOOL_POLICY_MAP.get(tool_name, CONSULT_POLICY)


def extract_strings(tool_input: object, policy: ToolScanPolicy) -> tuple[list[str], list[str]]:
    """Extract string-bearing values selected by the scan policy.

    Returns (texts_to_scan, unexpected_fields).
    Raises ToolInputLimitExceeded if traversal exceeds caps.
    """
    if not isinstance(tool_input, dict):
        raise TypeError(f"tool_input must be dict. Got: {tool_input!r:.100}")

    texts_to_scan: list[str] = []
    unexpected_fields: list[str] = []
    seen_unexpected: set[str] = set()
    node_count = 0
    char_count = 0
    stack: list[tuple[object, bool, bool]] = [(tool_input, False, True)]

    while stack:
        value, scan_strings, is_root = stack.pop()
        node_count += 1
        if node_count > _NODE_CAP:
            raise ToolInputLimitExceeded("tool_input traversal failed: node cap exceeded")

        if isinstance(value, str):
            char_count += len(value)
            if char_count > _CHAR_CAP:
                raise ToolInputLimitExceeded("tool_input traversal failed: char cap exceeded")
            if scan_strings:
                texts_to_scan.append(value)
            continue

        if value is None or isinstance(value, (bool, int, float)):
            continue

        if isinstance(value, dict):
            for key, child in reversed(list(value.items())):
                child_scan = scan_strings
                if is_root:
                    if key in policy.content_fields:
                        child_scan = True
                    elif key in policy.expected_fields:
                        child_scan = False
                    else:
                        key_name = str(key)
                        if key_name not in seen_unexpected:
                            unexpected_fields.append(key_name)
                            seen_unexpected.add(key_name)
                        child_scan = policy.scan_unknown_fields
                stack.append((child, child_scan, False))
            continue

        if isinstance(value, (list, tuple)):
            for child in reversed(value):
                stack.append((child, scan_strings, False))
            continue

        if isinstance(value, (set, frozenset)):
            for child in value:
                stack.append((child, scan_strings, False))
            continue

        raise TypeError(f"tool_input traversal failed: unsupported value. Got: {value!r:.100}")

    return texts_to_scan, unexpected_fields


_ACTION_RANK = {"block": 0, "shadow": 1, "allow": 2}
TIER_RANK = {"strict": 0, "contextual": 1}


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of running credential scan on tool_input."""

    action: Literal["allow", "block", "shadow"]
    reason: str | None = None
    tier: str | None = None
    unexpected_fields: list[str] = field(default_factory=list)


def check_tool_input(tool_input: object, policy: ToolScanPolicy) -> SafetyVerdict:
    """Run credential scan on tool_input per policy. Returns worst verdict."""
    texts, unexpected = extract_strings(tool_input, policy)

    worst_action = "allow"
    worst_reason: str | None = None
    worst_tier: str | None = None

    for text in texts:
        result = scan_text(text)
        result_rank = _ACTION_RANK.get(result.action, 2)
        current_rank = _ACTION_RANK.get(worst_action, 2)

        if result_rank < current_rank:
            worst_action = result.action
            worst_reason = result.reason
            worst_tier = result.tier
        elif result_rank == current_rank and result.action == "block":
            if TIER_RANK.get(result.tier or "", 99) < TIER_RANK.get(worst_tier or "", 99):
                worst_reason = result.reason
                worst_tier = result.tier

    return SafetyVerdict(
        action=worst_action,
        reason=worst_reason,
        tier=worst_tier,
        unexpected_fields=unexpected,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_consultation_safety.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add server/consultation_safety.py tests/test_consultation_safety.py
git commit -m "feat(codex-collaboration): add tool-input safety policy (T-03 AC3)"
```

---

## Task 5: PreToolUse Hook Guard

**Files:**
- Create: `scripts/codex_guard.py`
- Create: `tests/test_codex_guard.py`
- Modify: `hooks/hooks.json`

**Hook protocol:** Exit 2 + stderr for deny and parse/read failures. Exit 0 with no output for allow. Claude Code ignores stdout JSON on exit 2 (docs: "You must choose one approach per hook, not both … Claude Code only processes JSON on exit 0. If you exit 2, any JSON is ignored."). This matches the proven pattern in `cross-model/scripts/codex_guard.py`.

**PreToolUse decision control note:** The modern structured approach uses `hookSpecificOutput.permissionDecision` (allow/deny/ask) on exit 0. Top-level `decision` and `reason` are deprecated for PreToolUse. This script uses exit 2 + stderr instead of either JSON path because fail-closed on every error path is more valuable at a security boundary than structured feedback.

- [ ] **Step 1: Write hook guard tests**

The hook runs as a subprocess receiving JSON on stdin. Tests assert on `returncode` and `stderr` content — never on stdout JSON (Claude Code ignores it on exit 2).

```python
"""Tests for codex_guard.py PreToolUse hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "scripts" / "codex_guard.py"
)


def _run_hook(tool_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "session_id": "test-session",
    })
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
    )


class TestHookAllowsCleanInput:
    def test_consult_with_clean_objective(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp/repo", "objective": "review the architecture"},
        )
        assert result.returncode == 0

    def test_status_tool_allowed(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.status",
            {"repo_root": "/tmp/repo"},
        )
        assert result.returncode == 0

    def test_non_plugin_tool_ignored(self) -> None:
        result = _run_hook("Read", {"file_path": "/etc/passwd"})
        assert result.returncode == 0

    def test_dialogue_reply_clean(self) -> None:
        """Reply schema: collaboration_id, objective, explicit_paths — no repo_root."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply",
            {"collaboration_id": "c1", "objective": "clean review"},
        )
        assert result.returncode == 0


class TestHookBlocksSecrets:
    def test_aws_key_in_objective_blocks(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": "use AKIAIOSFODNN7EXAMPLE"},
        )
        assert result.returncode == 2
        assert "credential" in result.stderr.lower() or "blocked" in result.stderr.lower()

    def test_openai_key_blocks(self) -> None:
        key = "sk-" + "a" * 40
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": f"key: {key}"},
        )
        assert result.returncode == 2

    def test_placeholder_context_allows(self) -> None:
        key = "sk-" + "a" * 40
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": f"example format {key}"},
        )
        assert result.returncode == 0

    def test_dialogue_reply_scans_objective(self) -> None:
        """Reply schema has collaboration_id, objective, explicit_paths — no repo_root."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply",
            {
                "collaboration_id": "c1",
                "objective": "AKIAIOSFODNN7EXAMPLE",
            },
        )
        assert result.returncode == 2

    def test_profile_with_credential_blocks(self) -> None:
        """Credential in profile field is caught — profile is a content_field."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": "clean", "profile": "AKIAIOSFODNN7EXAMPLE"},
        )
        assert result.returncode == 2


class TestHookFailsClosed:
    def test_empty_stdin_blocks(self) -> None:
        """Parse failure on empty input must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input="",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2
        assert "failed to parse" in proc.stderr.lower() or "stdin" in proc.stderr.lower()

    def test_malformed_json_blocks(self) -> None:
        """Invalid JSON must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input="not json",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2

    def test_missing_tool_input_blocks(self) -> None:
        """Missing tool_input on a plugin tool must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input=json.dumps({
                "hook_event_name": "PreToolUse",
                "tool_name": "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            }),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_codex_guard.py -v`
Expected: FAIL — script does not exist

- [ ] **Step 3: Implement codex_guard.py**

```python
#!/usr/bin/env python3
"""PreToolUse hook: fail-closed credential scanning on codex-collaboration tool args.

Reads JSON from stdin with {tool_name, tool_input}.
Exit 0 = allow, exit 2 = block (reason on stderr).

Claude Code ignores stdout on exit 2. All feedback goes to stderr,
which Claude Code feeds back to Claude as an error message.

Only scans tools with the codex-collaboration MCP prefix. Other tools pass through.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add package root to sys.path for server imports
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

_TOOL_PREFIX = "mcp__plugin_codex-collaboration_codex-collaboration__"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError, UnicodeDecodeError) as e:
        # Cannot parse input — fail closed.
        print(f"codex-guard: failed to parse stdin ({e})", file=sys.stderr)
        return 2

    tool_name = data.get("tool_name", "")
    if not isinstance(tool_name, str) or not tool_name.startswith(_TOOL_PREFIX):
        return 0  # Not our tool — pass through

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        # Plugin tool with missing/malformed input — fail closed.
        print("codex-guard: missing or invalid tool_input", file=sys.stderr)
        return 2

    # Status tool has no user content — always allow
    if tool_name == f"{_TOOL_PREFIX}codex.status":
        return 0

    from server.consultation_safety import check_tool_input, policy_for_tool

    try:
        policy = policy_for_tool(tool_name)
        verdict = check_tool_input(tool_input, policy)
    except Exception as e:
        # Safety module error — fail closed.
        print(f"codex-guard: internal error ({e})", file=sys.stderr)
        return 2

    if verdict.action == "block":
        print(
            f"codex-guard: credential detected ({verdict.reason}). "
            "Remove the secret before retrying.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Register hook in hooks.json**

Read current `hooks/hooks.json`, merge the PreToolUse entry into the existing file. Use the matcher-group schema (`matcher` on the group, `type`/`command` in nested `hooks` array) consistent with every in-repo plugin hook. Use explicit tool-name alternation with escaped dots — `.` is a regex metacharacter; `codex\.consult` matches only the literal dot. Exclude `codex.status` (no user content) and `codex.dialogue.read` (read-only, no outbound content).

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/publish_session_id.py\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_codex-collaboration_codex-collaboration__codex\\.consult|mcp__plugin_codex-collaboration_codex-collaboration__codex\\.dialogue\\.start|mcp__plugin_codex-collaboration_codex-collaboration__codex\\.dialogue\\.reply",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/codex_guard.py\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_codex_guard.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/codex_guard.py tests/test_codex_guard.py hooks/hooks.json
git commit -m "feat(codex-collaboration): add PreToolUse hook guard (T-03 AC1/AC3)"
```

---

## Task 6: Learning Retrieval

**Files:**
- Create: `server/retrieve_learnings.py`
- Create: `tests/test_retrieve_learnings.py`
- Modify: `server/context_assembly.py` (wire learnings into packet assembly)
- Modify: `tests/test_context_assembly.py` (regression test for learnings in briefings)

- [ ] **Step 1: Write learning retrieval tests**

```python
"""Tests for learning retrieval."""

from __future__ import annotations

from pathlib import Path
from server.retrieve_learnings import (
    LearningEntry,
    filter_by_relevance,
    format_for_briefing,
    parse_learnings,
    retrieve_learnings,
)


class TestParseLearnings:
    def test_parses_single_entry(self) -> None:
        text = "### 2026-03-15 [safety, scanning]\n\nCredential scanning uses tiered enforcement.\n"
        entries = parse_learnings(text)
        assert len(entries) == 1
        assert entries[0].date == "2026-03-15"
        assert entries[0].tags == ["safety", "scanning"]
        assert "tiered enforcement" in entries[0].content

    def test_parses_multiple_entries(self) -> None:
        text = (
            "### 2026-03-15 [safety]\n\nFirst entry.\n\n"
            "### 2026-03-16 [profiles]\n\nSecond entry.\n"
        )
        entries = parse_learnings(text)
        assert len(entries) == 2
        assert entries[0].date == "2026-03-15"
        assert entries[1].date == "2026-03-16"

    def test_empty_text_returns_empty(self) -> None:
        assert parse_learnings("") == []

    def test_detects_promote_meta(self) -> None:
        text = "### 2026-03-15 [tag]\n<!-- promote-meta status=promoted -->\nContent.\n"
        entries = parse_learnings(text)
        assert entries[0].promoted is True


class TestFilterByRelevance:
    def test_tag_match_scores_higher(self) -> None:
        entries = [
            LearningEntry(date="2026-01-01", tags=["safety"], content="unrelated"),
            LearningEntry(date="2026-01-02", tags=["other"], content="safety note"),
        ]
        filtered = filter_by_relevance(entries, "safety")
        assert filtered[0].date == "2026-01-01"  # tag match = 2 pts

    def test_zero_score_filtered_out(self) -> None:
        entries = [
            LearningEntry(date="2026-01-01", tags=["profiles"], content="profile config"),
        ]
        filtered = filter_by_relevance(entries, "safety")
        assert filtered == []


class TestFormatForBriefing:
    def test_formats_entries_as_markdown(self) -> None:
        entries = [
            LearningEntry(date="2026-03-15", tags=["safety"], content="Content here."),
        ]
        result = format_for_briefing(entries, max_entries=5)
        assert "### 2026-03-15 [safety]" in result
        assert "Content here." in result
        assert "learnings-injected: 1" in result

    def test_respects_max_entries(self) -> None:
        entries = [
            LearningEntry(date=f"2026-01-0{i}", tags=["t"], content=f"e{i}")
            for i in range(1, 6)
        ]
        result = format_for_briefing(entries, max_entries=2)
        assert "learnings-injected: 2" in result

    def test_empty_entries_returns_empty(self) -> None:
        assert format_for_briefing([]) == ""


class TestRetrieveLearnings:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = retrieve_learnings("safety", path=tmp_path / "missing.md")
        assert result == ""

    def test_end_to_end(self, tmp_path: Path) -> None:
        path = tmp_path / "learnings.md"
        path.write_text(
            "### 2026-03-15 [safety, scanning]\n\nCredential scanning uses tiered enforcement.\n\n"
            "### 2026-03-16 [profiles]\n\nProfiles resolve execution controls.\n"
        )
        result = retrieve_learnings("safety scanning", path=path)
        assert "tiered enforcement" in result
        assert "learnings-injected:" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_retrieve_learnings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement retrieve_learnings.py**

Port from `packages/plugins/cross-model/scripts/retrieve_learnings.py`. Accept `repo_root` as parameter for path construction. Remove CLI `__main__` block.

```python
"""Retrieve relevant learning entries for consultation briefings.

Fail-soft: missing file, empty file, or parse errors return empty string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_ENTRY_HEADER = re.compile(r"^### (\d{4}-\d{2}-\d{2})\s+\[([^\]]+)\]")
_PROMOTE_META = re.compile(r"<!--\s*promote-meta\s+")


@dataclass(frozen=True)
class LearningEntry:
    """A single parsed learning entry."""

    date: str
    tags: list[str] = field(default_factory=list)
    content: str = ""
    promoted: bool = False


def parse_learnings(text: str) -> list[LearningEntry]:
    """Parse learnings markdown into LearningEntry objects."""
    entries: list[LearningEntry] = []
    current_date: str | None = None
    current_tags: list[str] = []
    content_lines: list[str] = []
    has_promote_meta = False

    def _flush() -> None:
        nonlocal current_date, current_tags, content_lines, has_promote_meta
        if current_date is not None:
            content = "\n".join(content_lines).strip()
            entries.append(LearningEntry(
                date=current_date,
                tags=current_tags,
                content=content,
                promoted=has_promote_meta,
            ))
        current_date = None
        current_tags = []
        content_lines = []
        has_promote_meta = False

    for line in text.splitlines():
        match = _ENTRY_HEADER.match(line)
        if match:
            _flush()
            current_date = match.group(1)
            current_tags = [t.strip() for t in match.group(2).split(",")]
            continue

        if current_date is not None:
            if _PROMOTE_META.search(line):
                has_promote_meta = True
                continue
            content_lines.append(line)

    _flush()
    return entries


def filter_by_relevance(
    entries: list[LearningEntry], query: str,
) -> list[LearningEntry]:
    """Filter entries by tag or content keyword overlap with query."""
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored: list[tuple[int, LearningEntry]] = []
    for entry in entries:
        score = 0
        entry_tags_lower = {t.lower() for t in entry.tags}
        content_lower = entry.content.lower()

        for word in query_words:
            if word in entry_tags_lower:
                score += 2
        for word in query_words:
            if word in content_lower:
                score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def format_for_briefing(
    entries: list[LearningEntry], max_entries: int = 5,
) -> str:
    """Format selected entries as markdown for briefing injection."""
    if not entries:
        return ""

    selected = entries[:max_entries]
    lines: list[str] = []
    for entry in selected:
        lines.append(f"### {entry.date} [{', '.join(entry.tags)}]")
        lines.append("")
        lines.append(entry.content)
        lines.append("")

    lines.append(f"<!-- learnings-injected: {len(selected)} -->")
    return "\n".join(lines)


def retrieve_learnings(
    query: str,
    *,
    repo_root: Path,
    max_entries: int = 5,
) -> str:
    """End-to-end: read file, filter, format. Fail-soft on errors.

    repo_root is required — plugin cwd is CLAUDE_PLUGIN_ROOT, not the
    user's repository. Callers must pass the resolved repo root.
    """
    path = repo_root / "docs" / "learnings" / "learnings.md"

    try:
        text = path.read_text()
    except (OSError, IOError):
        return ""

    entries = parse_learnings(text)
    if not entries:
        return ""

    filtered = filter_by_relevance(entries, query)
    return format_for_briefing(filtered, max_entries=max_entries)
```

Add these additional tests after the parse/filter/format tests:

```python
class TestRetrieveLearnings:
    def test_resolves_path_from_repo_root(self, tmp_path: Path) -> None:
        """repo_root determines the learnings file location, not cwd."""
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_text(
            "### 2026-03-15 [safety]\n\nTest learning.\n"
        )
        result = retrieve_learnings("safety", repo_root=tmp_path)
        assert "Test learning" in result

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Fail-soft when learnings file does not exist."""
        result = retrieve_learnings("anything", repo_root=tmp_path)
        assert result == ""

    def test_cwd_does_not_affect_resolution(self, tmp_path: Path, monkeypatch: object) -> None:
        """Prove that cwd is irrelevant — only repo_root matters."""
        import os
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_text(
            "### 2026-03-15 [test]\n\nContent.\n"
        )
        # Change cwd to a directory with no learnings
        monkeypatch.chdir(tmp_path / "docs")
        result = retrieve_learnings("test", repo_root=tmp_path)
        assert "Content" in result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_retrieve_learnings.py -v`
Expected: all PASS

- [ ] **Step 5: Wire learnings into assemble_context_packet()**

In `server/context_assembly.py`, add learning retrieval inside `assemble_context_packet()`. Learnings must be routed through `_build_text_entries()` — **not** appended as raw `_ContextEntry` — because `_build_text_entries()` applies `_redact_text()` at construction time, and `_render_packet()` emits `entry.content` unchanged at line 284. The `_ContextEntry` dataclass has only three fields (`category`, `label`, `content`) — no `token_estimate`.

After the existing `_build_text_entries()` calls for `supplementary_context` (inside `assemble_context_packet()`), add:

```python
    # Inject relevant learnings into supplementary context (fail-soft).
    # Routed through _build_text_entries so learnings pass through _redact_text()
    # at construction time — _render_packet() does not redact entry content.
    from .retrieve_learnings import retrieve_learnings
    learnings_text = retrieve_learnings(request.objective, repo_root=request.repo_root)
    if learnings_text:
        entries["supplementary_context"].extend(
            _build_text_entries("supplementary_context", (learnings_text,))
        )
```

This insertion point is shared by both `codex.consult` (via `control_plane.codex_consult()`) and `codex.dialogue.reply` (via `DialogueController.reply()`), since both call `assemble_context_packet()`.

- [ ] **Step 6: Add regression test for learnings in briefings**

In `tests/test_context_assembly.py`, add a test that exercises `assemble_context_packet()` with a `ConsultRequest` whose `repo_root` points to a directory with learnings, then verifies the rendered packet contains the learning content. This pins the shared-path assumption so it cannot silently drift.

```python
class TestLearningsInBriefing:
    def test_learnings_appear_in_packet(self, tmp_path: Path) -> None:
        """Learnings from repo_root appear in assembled packet."""
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_text(
            "### 2026-03-15 [safety]\n\nCredential scanning insight.\n"
        )
        request = ConsultRequest(
            repo_root=tmp_path,
            objective="review safety scanning",
        )
        repo_identity = RepoIdentity(
            repo_root=tmp_path, branch="main", head="abc123"
        )
        packet = assemble_context_packet(request, repo_identity, profile="advisory")
        # Learnings appear in the rendered packet under supplementary_context.
        # Content passes through _redact_text() via _build_text_entries().
        assert "Credential scanning insight" in packet.payload
```

This test covers both consult and dialogue reply because `DialogueController.reply()` calls the same `assemble_context_packet()` function with the same `ConsultRequest` shape (verified at `dialogue.py:198-211`).

- [ ] **Step 7: Run full context assembly tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_context_assembly.py tests/test_retrieve_learnings.py -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add server/retrieve_learnings.py tests/test_retrieve_learnings.py server/context_assembly.py tests/test_context_assembly.py
git commit -m "feat(codex-collaboration): add learning retrieval wired into packet assembly (T-03 AC5)"
```

---

## Task 7: Consultation Profiles + Runtime Effort Wiring

**Files:**
- Create: `references/consultation-profiles.yaml`
- Create: `server/profiles.py`
- Create: `tests/test_profiles.py`
- Modify: `server/runtime.py:109-130`
- Modify: `server/models.py:32-48`
- Modify: `server/mcp_server.py:28-38`
- Modify: `server/control_plane.py:130-206`
- Modify: `server/prompt_builder.py:40-47`

This is the largest task. It has 4 sub-parts.

### 7a: Profile resolver + YAML

- [ ] **Step 1: Write profile resolver tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_profiles.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create consultation-profiles.yaml**

Copy from `packages/plugins/cross-model/references/consultation-profiles.yaml` verbatim. Create `references/` directory if needed.

- [ ] **Step 4: Implement profiles.py**

```python
"""Consultation profile resolver.

Resolution order: explicit flags > named profile > contract defaults.
Validation gate: rejects sandbox != read-only or approval_policy != never
until freeze-and-rotate is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ProfileValidationError(RuntimeError):
    """Raised when a resolved profile requires capabilities not yet implemented."""


@dataclass(frozen=True)
class ResolvedProfile:
    """Fully resolved execution controls."""

    posture: str
    turn_budget: int
    effort: str | None
    sandbox: str
    approval_policy: str


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
    explicit_posture: str | None = None,
    explicit_turn_budget: int | None = None,
    explicit_effort: str | None = None,
    explicit_sandbox: str | None = None,
    explicit_approval_policy: str | None = None,
) -> ResolvedProfile:
    """Resolve execution controls from profile + explicit overrides."""
    profile: dict[str, Any] = {}
    if profile_name is not None:
        profiles = load_profiles()
        profile = profiles.get(profile_name, {})

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
        or profile.get("posture", _DEFAULT_POSTURE)
    )
    turn_budget = (
        explicit_turn_budget
        if explicit_turn_budget is not None
        else profile.get("turn_budget", _DEFAULT_TURN_BUDGET)
    )
    effort = (
        explicit_effort
        or profile.get("reasoning_effort")
    )
    sandbox = (
        explicit_sandbox
        or profile.get("sandbox", _DEFAULT_SANDBOX)
    )
    approval_policy = (
        explicit_approval_policy
        or profile.get("approval_policy", _DEFAULT_APPROVAL)
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
```

- [ ] **Step 5: Run profile resolver tests**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/test_profiles.py -v`
Expected: all PASS

- [ ] **Step 6: Add PyYAML dependency**

Check if `pyyaml` is already available in the workspace. If not, add it to the package's `pyproject.toml` dependencies.

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run python -c "import yaml; print(yaml.__version__)"`

If it fails, add `pyyaml` to `[project.dependencies]` in `pyproject.toml`.

- [ ] **Step 7: Commit profile resolver and YAML**

```bash
git add server/profiles.py tests/test_profiles.py references/consultation-profiles.yaml
git commit -m "feat(codex-collaboration): add consultation profile resolver with validation gate (T-03 AC4)"
```

### 7b: Wire effort on turn/start

- [ ] **Step 8: Add effort parameter to run_turn()**

In `server/runtime.py`, modify `run_turn()` signature and payload:

```python
def run_turn(
    self,
    *,
    thread_id: str,
    prompt_text: str,
    output_schema: dict[str, Any],
    effort: str | None = None,
) -> TurnExecutionResult:
    """Start a turn and collect notifications until completion."""

    params: dict[str, Any] = {
        "threadId": thread_id,
        "input": [{"type": "text", "text": prompt_text}],
        "cwd": str(self._repo_root),
        "approvalPolicy": "never",
        "sandboxPolicy": {"type": "readOnly"},
        "summary": "concise",
        "personality": "pragmatic",
        "outputSchema": output_schema,
    }
    if effort is not None:
        params["effort"] = effort

    result = self._client.request("turn/start", params)
    # ... rest unchanged
```

- [ ] **Step 9: Update FakeRuntimeSession to accept effort**

`FakeRuntimeSession.run_turn()` at `tests/test_control_plane.py:89` does not accept an `effort` keyword. This fake is imported by `test_dialogue.py:19` and `test_dialogue_integration.py:20`. Once callers pass `effort=...`, the suite breaks with `TypeError`. Update the fake before changing callers:

```python
def run_turn(
    self,
    *,
    thread_id: str,
    prompt_text: str,
    output_schema: dict[str, object],
    effort: str | None = None,
) -> TurnExecutionResult:
    if self.run_turn_error is not None:
        raise self.run_turn_error
    self.run_turn_calls += 1
    self.completed_turn_count += 1
    self.last_prompt_text = prompt_text
    self.last_output_schema = output_schema
    self.last_effort = effort  # Capture for assertion in profile tests
    return TurnExecutionResult(
        turn_id="turn-1",
        agent_message=self.agent_message.replace("thr-start", thread_id),
    )
```

Also add `last_effort: str | None = None` to `FakeRuntimeSession.__init__()`. This is the capture mechanism that Step 18 tests rely on — `captured_turn_params["effort"]` in those tests should reference `fake_session.last_effort` instead.

- [ ] **Step 10: Write test for effort parameter**

Add to `tests/test_mcp_server.py` or a new runtime test file. The test should use `FakeJsonRpcClient` (or similar) to capture the request params and verify the wire format:

```python
def test_run_turn_includes_effort_when_provided(self) -> None:
    """effort parameter is included in turn/start payload."""
    # Use FakeJsonRpcClient to capture the request params
    # Key assertion: when effort="high", turn/start includes "effort": "high"
    # When effort=None, the field is absent from the params dict
    ...
```

The exact test shape depends on how `runtime.py` is tested. The key assertion: when `effort="high"` is passed, the `turn/start` request includes `"effort": "high"`. When `effort=None`, the field is absent.

- [ ] **Step 11: Commit effort wiring**

```bash
git add server/runtime.py tests/test_control_plane.py
git commit -m "feat(codex-collaboration): wire effort parameter on turn/start (T-03 AC4)"
```

### 7c: Add profile to ConsultRequest, dialogue.start, and MCP schemas

- [ ] **Step 12: Add profile field to ConsultRequest**

In `server/models.py`, add to `ConsultRequest`:

```python
@dataclass(frozen=True)
class ConsultRequest:
    """Caller-facing consult request for the advisory runtime."""

    repo_root: Path
    objective: str
    user_constraints: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    explicit_paths: tuple[Path, ...] = ()
    explicit_snippets: tuple[str, ...] = ()
    task_local_paths: tuple[Path, ...] = ()
    broad_repository_summaries: tuple[str, ...] = ()
    promoted_summaries: tuple[str, ...] = ()
    delegation_summaries: tuple[str, ...] = ()
    supplementary_context: tuple[str, ...] = ()
    external_research_material: tuple[str, ...] = ()
    parent_thread_id: str | None = None
    network_access: bool = False
    profile: str | None = None
```

- [ ] **Step 13: Add resolved profile fields to CollaborationHandle**

In `server/models.py`, add three optional fields to `CollaborationHandle`. These persist the resolved profile state at dialogue start time. `reply()` reads them from the stored handle rather than re-resolving or accepting per-turn overrides.

```python
@dataclass
class CollaborationHandle:
    # ... existing fields ...
    parent_collaboration_id: str | None = None
    resolved_posture: str | None = None
    resolved_effort: str | None = None
    resolved_turn_budget: int | None = None
```

**Crash recovery limitation:** The recovery path at `dialogue.py:448` reconstructs handles from `OperationJournalEntry` data, which has no profile fields (`OperationJournalEntry` at `models.py:221` has no profile payload slots). A crash between `thread/start` and `lineage_store.create()` produces a recovered handle with `resolved_posture=None`, `resolved_effort=None`, `resolved_turn_budget=None`. This is acceptable for T-03:

- Pre-T-03 handles had no profile state at all — `None` is the same baseline behavior
- `reply()` must treat `None` as "no override": effort=None means no `effort` field on `turn/start`, posture=None means no posture instruction in the prompt
- The window is narrow: only a crash between thread creation (`dialogue.py:92`) and lineage persist (`dialogue.py:122`)

Full journal integration (adding profile fields to `OperationJournalEntry` and the recovery path) is out of scope for T-03 but should be addressed when the journal schema is next revised.

- [ ] **Step 13b: Update contract spec and model tests for new handle fields**

In `docs/superpowers/specs/codex-collaboration/contracts.md`, add the three new optional fields to the CollaborationHandle table (after `status` row, around line 50):

```markdown
| `resolved_posture` | string? | Posture from profile resolved at dialogue start. Null for consultations and crash-recovered handles |
| `resolved_effort` | string? | Effort level from profile resolved at dialogue start. Null means no effort override |
| `resolved_turn_budget` | int? | Turn budget from profile resolved at dialogue start. Null means default budget |
```

In `tests/test_models_r2.py`, update the serialization test:

```python
def test_collaboration_handle_serializes_to_dict() -> None:
    handle = CollaborationHandle(
        collaboration_id="collab-1",
        capability_class="advisory",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
        claude_session_id="sess-1",
        repo_root="/repo",
        created_at="2026-03-28T00:00:00Z",
        status="active",
    )
    d = asdict(handle)
    assert d["collaboration_id"] == "collab-1"
    assert d["parent_collaboration_id"] is None
    assert d["resolved_posture"] is None
    assert d["resolved_effort"] is None
    assert d["resolved_turn_budget"] is None
    assert len(d) == 13
```

- [ ] **Step 14: Expose profile in MCP tool schemas**

In `server/mcp_server.py`, add `profile` to both `codex.consult` and `codex.dialogue.start` input schemas:

For `codex.consult` (around line 33):
```python
"properties": {
    "repo_root": {"type": "string"},
    "objective": {"type": "string"},
    "explicit_paths": {"type": "array", "items": {"type": "string"}},
    "profile": {"type": "string", "description": "Named consultation profile (e.g., quick-check, deep-review)"},
},
```

For `codex.dialogue.start` (around line 45):
```python
"properties": {
    "repo_root": {"type": "string", "description": "Repository root path"},
    "profile": {"type": "string", "description": "Named consultation profile — resolved once at start, persisted for all subsequent replies"},
},
"required": ["repo_root"],
```

- [ ] **Step 15: Update consult dispatch to pass profile through**

In `server/mcp_server.py`, update the `codex.consult` dispatch (around line 223):

```python
request = ConsultRequest(
    repo_root=Path(arguments["repo_root"]),
    objective=arguments["objective"],
    explicit_paths=tuple(
        Path(p) for p in arguments.get("explicit_paths", ())
    ),
    profile=arguments.get("profile"),
)
```

- [ ] **Step 16: Update dialogue.start to resolve and persist profile**

In `server/mcp_server.py`, update the `codex.dialogue.start` dispatch (around line 232):

```python
if name == "codex.dialogue.start":
    controller = self._ensure_dialogue_controller()
    result = controller.start(
        Path(arguments["repo_root"]),
        profile_name=arguments.get("profile"),
    )
    return asdict(result)
```

In `server/dialogue.py`, update `start()` signature and handle creation. Only resolve and store profile state when `profile_name` is explicitly provided — `None` means "no profile, no overrides," which preserves pre-T-03 behavior for calls without a profile. This ensures consult and dialogue cannot diverge on their default posture path.

```python
def start(
    self, repo_root: Path, *, profile_name: str | None = None,
) -> DialogueStartResult:
    """Create a durable dialogue thread and persist handle with resolved profile."""
    resolved_posture: str | None = None
    resolved_effort: str | None = None
    resolved_turn_budget: int | None = None
    if profile_name is not None:
        from .profiles import resolve_profile
        resolved = resolve_profile(profile_name=profile_name)
        resolved_posture = resolved.posture
        resolved_effort = resolved.effort
        resolved_turn_budget = resolved.turn_budget

    # ... existing thread creation code ...

    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="advisory",
        runtime_id=runtime.runtime_id,
        codex_thread_id=thread_id,
        claude_session_id=self._session_id,
        repo_root=str(resolved_root),
        created_at=created_at,
        status="active",
        resolved_posture=resolved_posture,
        resolved_effort=resolved_effort,
        resolved_turn_budget=resolved_turn_budget,
    )
    self._lineage_store.create(handle)
    # ... rest unchanged ...
```

- [ ] **Step 17: Update dialogue.reply to use stored profile state**

In `server/dialogue.py`, update `reply()` to read profile state from the handle and pass it through. The handle is accessed via `self._lineage_store.get(collaboration_id)` (not `.load()` — that method does not exist; the read API is `get()` at `lineage_store.py:35`).

```python
def reply(self, *, collaboration_id: str, ...) -> DialogueReplyResult:
    # ... existing handle loading via get() ...

    # ... existing context assembly ...
    packet = assemble_context_packet(request, repo_identity, profile="advisory")

    # Use stored profile state from dialogue.start.
    # None is valid — means no profile was set at start (or handle was crash-recovered).
    # None effort → no effort field on turn/start. None posture → no posture instruction.
    posture = handle.resolved_posture  # may be None
    effort = handle.resolved_effort    # may be None

    # ... existing journal write ...

    try:
        turn_result = runtime.session.run_turn(
            thread_id=handle.codex_thread_id,
            prompt_text=build_consult_turn_text(packet.payload, posture=posture),
            output_schema=CONSULT_OUTPUT_SCHEMA,
            effort=effort,
        )
```

- [ ] **Step 18: Thread profile through control_plane.codex_consult()**

In `server/control_plane.py`, resolve profile only when explicitly provided — matching the dialogue contract. `None` means no overrides, preserving pre-T-03 behavior:

```python
def codex_consult(self, request: ConsultRequest) -> ConsultResult:
    # ... existing code up to packet assembly ...

    posture: str | None = None
    effort: str | None = None
    if request.profile is not None:
        from .profiles import resolve_profile
        resolved = resolve_profile(profile_name=request.profile)
        posture = resolved.posture
        effort = resolved.effort

    # ... existing thread/turn dispatch ...
    turn_result = runtime.session.run_turn(
        thread_id=thread_id,
        prompt_text=build_consult_turn_text(packet.payload, posture=posture),
        output_schema=CONSULT_OUTPUT_SCHEMA,
        effort=effort,
    )
```

- [ ] **Step 19: Write tests for dialogue profile persistence**

Add to `tests/test_dialogue.py` (or a new `tests/test_dialogue_profiles.py`):

These tests use `FakeRuntimeSession` (updated in Step 9 to capture `last_effort`). Replace references to the undefined `captured_turn_params` with `fake_session.last_effort`.

```python
class TestDialogueProfilePersistence:
    def test_start_stores_resolved_profile_on_handle(self) -> None:
        """dialogue.start resolves profile and persists state on handle."""
        # Start dialogue with profile="deep-review"
        result = controller.start(repo_root, profile_name="deep-review")
        handle = lineage_store.get(result.collaboration_id)
        assert handle.resolved_posture == "evaluative"
        assert handle.resolved_effort == "xhigh"
        assert handle.resolved_turn_budget == 8

    def test_reply_uses_stored_profile_state(self) -> None:
        """dialogue.reply reads effort/posture from handle, not from arguments."""
        # Start with deep-review profile
        start_result = controller.start(repo_root, profile_name="deep-review")
        # Reply — verify effort/posture are passed to run_turn
        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="continue review",
        )
        # Assert the runtime received effort="xhigh" via FakeRuntimeSession capture
        assert fake_session.last_effort == "xhigh"

    def test_start_without_profile_stores_none(self) -> None:
        """No profile means no overrides stored — None, not resolved defaults.

        This preserves pre-T-03 behavior: calls without explicit profile
        produce no posture instruction and no effort override. Consult and
        dialogue follow the same contract: None profile → None stored fields.
        """
        result = controller.start(repo_root)
        handle = lineage_store.get(result.collaboration_id)
        assert handle.resolved_posture is None
        assert handle.resolved_effort is None
        assert handle.resolved_turn_budget is None

    def test_phased_profile_rejected_at_start(self) -> None:
        """Phased profiles raise at dialogue.start, not silently collapse."""
        with pytest.raises(ProfileValidationError, match="phased"):
            controller.start(repo_root, profile_name="debugging")

    def test_crash_recovered_handle_works_without_profile(self) -> None:
        """Crash-recovered handle (no profile state) still supports reply."""
        # Simulate a crash-recovered handle: no profile fields
        handle = CollaborationHandle(
            collaboration_id="recovered-1",
            capability_class="advisory",
            runtime_id=runtime.runtime_id,
            codex_thread_id="thr-1",
            claude_session_id="sess-1",
            repo_root=str(repo_root),
            created_at="2026-03-30T00:00:00Z",
            status="active",
            # resolved_posture, resolved_effort, resolved_turn_budget all default to None
        )
        lineage_store.create(handle)
        # Reply should work — no effort override, no posture instruction
        reply_result = controller.reply(
            collaboration_id="recovered-1",
            objective="continue after crash",
        )
        # Verify no effort was sent to runtime via FakeRuntimeSession capture
        assert fake_session.last_effort is None
```

- [ ] **Step 20: Run full test suite**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/ -q`
Expected: all PASS

- [ ] **Step 21: Commit schema + wiring**

```bash
git add server/models.py server/mcp_server.py server/control_plane.py server/dialogue.py server/profiles.py docs/superpowers/specs/codex-collaboration/contracts.md tests/
git commit -m "feat(codex-collaboration): wire profile through consult and dialogue dispatch (T-03 AC4)"
```

### 7d: Wire posture into prompt builder

- [ ] **Step 22: Accept posture in build_consult_turn_text()**

In `server/prompt_builder.py`:

```python
def build_consult_turn_text(packet_payload: str, *, posture: str | None = None) -> str:
    """Build the single text input item for `turn/start`."""
    posture_instruction = ""
    if posture is not None:
        posture_instruction = f" Adopt a {posture} posture for this advisory turn."

    return (
        "Use the following structured task packet as the only authority for this advisory turn. "
        f"Stay within read-only advisory scope and return valid JSON matching the requested output schema.{posture_instruction}\n\n"
        f"{packet_payload}"
    )
```

Callers updated in Steps 17 and 18 above (dialogue.reply and control_plane.codex_consult). No separate caller update step needed.

- [ ] **Step 23: Run full test suite**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/ -q`
Expected: all PASS

- [ ] **Step 24: Commit posture wiring**

```bash
git add server/prompt_builder.py
git commit -m "feat(codex-collaboration): wire posture into prompt builder (T-03 AC4)"
```

---

## Task 8: Benchmark Contract Wiring

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/spec.yaml` (or equivalent index)
- Modify: `docs/superpowers/specs/codex-collaboration/delivery.md`

This is documentation-only.

- [ ] **Step 1: Check spec.yaml for reading order**

Run: `cat docs/superpowers/specs/codex-collaboration/spec.yaml`
Identify where to add the benchmark contract reference.

- [ ] **Step 2: Add benchmark reference to spec reading order**

Add `dialogue-supersession-benchmark.md` to the modules list in `spec.yaml`.

- [ ] **Step 3: Add benchmark reference to delivery.md**

Add a reference to `dialogue-supersession-benchmark.md` as the authority for the context-injection retirement decision. The benchmark contract already exists — this just wires it into the reading order.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/spec.yaml docs/superpowers/specs/codex-collaboration/delivery.md
git commit -m "docs(codex-collaboration): wire benchmark contract into spec reading order (T-03 AC7/AC8)"
```

---

## Task 9: Full Verification

- [ ] **Step 1: Run complete test suite**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration && uv run pytest tests/ -v`
Expected: all PASS (239 existing + new tests)

- [ ] **Step 2: Verify acceptance criteria**

| AC | Verification |
|----|-------------|
| AC1: Credential scanning fails closed | `test_codex_guard.py` — hook returns exit 2 + stderr on credential match; exit 2 on parse/read errors (fail-closed). Never writes JSON to stdout |
| AC2: Secret taxonomy used by scanner | `test_secret_taxonomy.py` + `test_credential_scan.py` — 14 families, tiered |
| AC3: Tool-input safety policy | `test_consultation_safety.py` — policy routing, field extraction, caps |
| AC4: Consultation profiles resolve | `test_profiles.py` — 8 of 9 non-phased profiles resolve; `debugging` (phased) explicitly rejected until phase-progression support. `test_dialogue_profiles.py` — start stores resolved state on handle, reply reuses stored effort/posture, crash-recovered handle works with None defaults. `test_models_r2.py` — handle serialization covers 13 fields. `contracts.md` — 3 new optional fields documented |
| AC5: Learning retrieval | `test_retrieve_learnings.py` — parse, filter, fail-soft with required `repo_root` (not CWD). `test_context_assembly.py::TestLearningsInBriefing` — learnings wired into shared `assemble_context_packet()` via `_build_text_entries()` (redaction at construction time), covering both consult and dialogue reply |
| AC6: Analytics emission | **DEFERRED** — Thread C checkpoint before implementation |
| AC7: Benchmark contract exists | File exists at `dialogue-supersession-benchmark.md` |
| AC8: Spec docs point to benchmark | `spec.yaml` and `delivery.md` reference it |

- [ ] **Step 3: Commit any fixups**

If tests revealed issues, fix and commit.

---

## Deferred: Task 10 — Analytics Emission (AC6)

**Not included in this plan.** Thread C (profile/audit schema expansion) must be investigated before implementation. The key question: which profile fields are first-class `AuditEvent` fields vs which go in `extra`? The answer affects both the model change and the journal query surface.

**When to plan:** After Tasks 1-8 are implemented, checkpoint with user on Thread C, then write Task 10 as a follow-up plan.
