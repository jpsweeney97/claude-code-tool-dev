"""Tests for packages/plugins/cross-model/scripts/codex_guard.py.

Tests the PreToolUse credential detection hook and PostToolUse logging hook.
Imports the guard module directly via importlib (same pattern as test_consultation_contract_sync.py).
"""

from __future__ import annotations

import importlib.util
import json
from io import StringIO
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "codex_guard.py"
)
SPEC = importlib.util.spec_from_file_location("codex_guard", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pre(prompt: str, tool: str = "mcp__plugin_cross-model_codex__codex") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "session_id": "test-session",
        "tool_input": {"prompt": prompt},
    }


def _post(prompt: str = "hello", result: str = "world") -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__plugin_cross-model_codex__codex",
        "session_id": "test-session",
        "tool_input": {"prompt": prompt},
        "tool_response": {"content": result},
    }


# ---------------------------------------------------------------------------
# Strict tier: hard-block patterns
# ---------------------------------------------------------------------------


class TestStrictPatterns:
    def test_aws_access_key_blocks(self) -> None:
        assert MODULE.handle_pre(_pre("key: AKIAIOSFODNN7EXAMPLE")) == 2

    def test_pem_rsa_private_key_blocks(self) -> None:
        assert MODULE.handle_pre(_pre("-----BEGIN RSA PRIVATE KEY-----")) == 2

    def test_pem_private_key_no_type_blocks(self) -> None:
        assert MODULE.handle_pre(_pre("-----BEGIN PRIVATE KEY-----")) == 2

    def test_jwt_token_blocks(self) -> None:
        jwt = (
            "eyJhbGciOiJIUzI1NiJ9"
            ".eyJzdWIiOiJ1c2VyMTIzNDU2Nzg5MCJ9"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        assert MODULE.handle_pre(_pre(f"Authorization header: {jwt}")) == 2


# ---------------------------------------------------------------------------
# Contextual tier: block unless placeholder suppression applies
# ---------------------------------------------------------------------------


class TestContextualPatterns:
    def test_github_pat_blocks(self) -> None:
        token = "ghp_" + "A" * 36
        assert MODULE.handle_pre(_pre(f"token: {token}")) == 2

    def test_openai_key_blocks(self) -> None:
        key = "sk-" + "a" * 40
        assert MODULE.handle_pre(_pre(f"OPENAI_API_KEY={key}")) == 2

    def test_bearer_token_blocks(self) -> None:
        assert MODULE.handle_pre(_pre("Authorization: Bearer " + "x" * 30)) == 2

    def test_url_userinfo_blocks(self) -> None:
        assert MODULE.handle_pre(_pre("Connect to postgres://user:s3cr3tp@ss@db.host/mydb")) == 2


# ---------------------------------------------------------------------------
# Placeholder suppression: contextual patterns suppressed by meta-language
# ---------------------------------------------------------------------------


class TestPlaceholderSuppression:
    def test_openai_key_format_discussion_allowed(self) -> None:
        prompt = "OpenAI API keys look like sk- followed by 40 characters. Example: sk-" + "x" * 40
        assert MODULE.handle_pre(_pre(prompt)) == 0

    def test_github_token_example_allowed(self) -> None:
        token = "ghp_" + "A" * 36
        assert MODULE.handle_pre(_pre(f"An example GitHub PAT looks like: {token}")) == 0

    def test_redacted_placeholder_allowed(self) -> None:
        assert MODULE.handle_pre(_pre("Use [REDACTED: credential material] in place of real tokens")) == 0


# ---------------------------------------------------------------------------
# Clean prompts: always allowed
# ---------------------------------------------------------------------------


class TestCleanPrompts:
    def test_plain_question_allowed(self) -> None:
        assert MODULE.handle_pre(_pre("What is the capital of France?")) == 0

    def test_code_review_prompt_allowed(self) -> None:
        assert MODULE.handle_pre(_pre("Review this Python function for bugs:\n\ndef add(a, b):\n    return a + b")) == 0

    def test_empty_prompt_allowed(self) -> None:
        assert MODULE.handle_pre(_pre("")) == 0


# ---------------------------------------------------------------------------
# Fail-closed: invalid or non-string inputs handled safely
# ---------------------------------------------------------------------------


class TestFailClosed:
    def test_non_string_prompt_coerced_and_allowed(self) -> None:
        data = _pre("hello")
        data["tool_input"]["prompt"] = 12345
        assert MODULE.handle_pre(data) == 0

    def test_main_fails_closed_on_invalid_json(self, monkeypatch) -> None:
        """main() must return 2 when stdin cannot be parsed (PreToolUse default)."""
        monkeypatch.setattr("sys.stdin", StringIO("not valid json{{{"))
        result = MODULE.main()
        assert result == 2

    def test_missing_tool_input_allows(self) -> None:
        data = {"hook_event_name": "PreToolUse", "tool_name": "mcp__plugin_cross-model_codex__codex"}
        assert MODULE.handle_pre(data) == 0


# ---------------------------------------------------------------------------
# PostToolUse: always returns 0, never blocks
# ---------------------------------------------------------------------------


class TestPostToolUse:
    def test_post_always_returns_0(self) -> None:
        assert MODULE.handle_post(_post()) == 0

    def test_post_with_aws_key_in_result_still_returns_0(self) -> None:
        assert MODULE.handle_post(_post(result="AKIAIOSFODNN7EXAMPLE")) == 0

    def test_post_codex_reply_returns_0(self, tmp_path, monkeypatch) -> None:
        """PostToolUse works for codex-reply tool variant."""
        monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
        data = _post()
        data["tool_name"] = "mcp__plugin_cross-model_codex__codex-reply"
        assert MODULE.handle_post(data) == 0

    def test_post_thread_id_from_structured_content(self, tmp_path, monkeypatch) -> None:
        """thread_id_present is True when threadId is in structuredContent."""
        monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
        data = _post()
        data["tool_response"] = {
            "content": "response text",
            "structuredContent": {"threadId": "thread_abc123"},
        }
        MODULE.handle_post(data)
        log = json.loads((tmp_path / "events.jsonl").read_text().strip())
        assert log["thread_id_present"] is True

    def test_post_thread_id_from_top_level_response(self, tmp_path, monkeypatch) -> None:
        """thread_id_present is True when threadId is at top level of tool_response."""
        monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
        data = _post()
        data["tool_response"] = {
            "content": "response text",
            "threadId": "thread_abc123",
        }
        MODULE.handle_post(data)
        log = json.loads((tmp_path / "events.jsonl").read_text().strip())
        assert log["thread_id_present"] is True

    def test_post_thread_id_absent(self, tmp_path, monkeypatch) -> None:
        """thread_id_present is False when no threadId anywhere."""
        monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
        data = _post()
        MODULE.handle_post(data)
        log = json.loads((tmp_path / "events.jsonl").read_text().strip())
        assert log["thread_id_present"] is False

    def test_post_empty_data_returns_0(self) -> None:
        assert MODULE.handle_post({}) == 0


# ---------------------------------------------------------------------------
# Security hardening: regression tests for review findings
# ---------------------------------------------------------------------------


class TestSecurityHardening:
    def test_contextual_second_match_blocks_when_first_suppressed(self) -> None:
        """P1: _check_contextual must check ALL matches, not just the first."""
        token1 = "ghp_" + "A" * 36
        token2 = "ghp_" + "B" * 36
        # Padding pushes "example" >100 chars from second token
        padding = "x" * 80
        prompt = f"An example GitHub PAT: {token1} {padding} real: {token2}"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_html_context_does_not_suppress_real_key(self) -> None:
        """P1: angle brackets must not suppress contextual detection."""
        key = "sk-" + "a" * 40
        prompt = f"<div>{key}</div>"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_angle_bracket_comparison_does_not_suppress(self) -> None:
        """P1: comparison operators near tokens must not suppress."""
        token = "ghp_" + "A" * 36
        prompt = f"if count > 0; export TOKEN={token}"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_like_without_looks_does_not_suppress(self) -> None:
        """P3: standalone 'like' must not suppress contextual detection."""
        token = "ghp_" + "A" * 36
        prompt = f"I would like to use my token: {token}"
        assert MODULE.handle_pre(_pre(prompt)) == 2
