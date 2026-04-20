"""Tests for tool-input safety policy."""

from __future__ import annotations

import pytest

from server.consultation_safety import (
    CONSULT_POLICY,
    DELEGATE_DECIDE_POLICY,
    DIALOGUE_REPLY_POLICY,
    DIALOGUE_START_POLICY,
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

    def test_unknown_tool_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            policy_for_tool("mcp__unknown__tool")


class TestExtractStrings:
    def test_content_fields_extracted(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset({"repo_root"}),
            content_fields=frozenset({"objective"}),
        )
        texts, unexpected = extract_strings(
            {"repo_root": "/tmp", "objective": "check this"}, policy
        )
        assert texts == ["check this"]
        assert unexpected == ()

    def test_expected_fields_skipped(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset({"repo_root"}),
            content_fields=frozenset({"objective"}),
        )
        texts, _ = extract_strings(
            {"repo_root": "/tmp/secret", "objective": "hello"}, policy
        )
        assert "/tmp/secret" not in texts

    def test_unknown_fields_scanned_by_default(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset(),
            scan_unknown_fields=True,
        )
        texts, unexpected = extract_strings({"surprise": "value"}, policy)
        assert texts == ["value"]
        assert "surprise" in unexpected

    def test_unknown_fields_skipped_when_disabled(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset(),
            scan_unknown_fields=False,
        )
        texts, unexpected = extract_strings({"surprise": "value"}, policy)
        assert texts == []
        assert "surprise" in unexpected

    def test_nested_dicts_traversed(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset({"data"}),
        )
        texts, _ = extract_strings({"data": {"nested": {"deep": "found"}}}, policy)
        assert "found" in texts

    def test_lists_traversed(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset({"items"}),
        )
        texts, _ = extract_strings({"items": ["a", "b"]}, policy)
        assert texts == ["a", "b"]

    def test_node_cap_raises(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset({"data"}),
        )
        huge = {"data": list(range(20000))}
        with pytest.raises(ToolInputLimitExceeded):
            extract_strings(huge, policy)

    def test_char_cap_raises(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=frozenset(),
            content_fields=frozenset({"data"}),
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
            {
                "objective": "clean review",
                "repo_root": "/tmp",
                "profile": "AKIAIOSFODNN7EXAMPLE",
            },
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

    def test_dialogue_start_posture_is_expected_not_scanned(self) -> None:
        """posture is an expected field — not scanned for credentials, no unexpected warning."""
        verdict = check_tool_input(
            {"repo_root": "/tmp", "posture": "adversarial"},
            DIALOGUE_START_POLICY,
        )
        assert verdict.action == "allow"
        assert verdict.unexpected_fields == ()

    def test_dialogue_start_turn_budget_is_expected_not_scanned(self) -> None:
        """turn_budget is an expected field — not flagged as unexpected."""
        verdict = check_tool_input(
            {"repo_root": "/tmp", "turn_budget": 6},
            DIALOGUE_START_POLICY,
        )
        assert verdict.action == "allow"
        assert verdict.unexpected_fields == ()

    def test_dialogue_start_all_new_fields_together(self) -> None:
        """All fields together: repo_root + profile + posture + turn_budget."""
        verdict = check_tool_input(
            {
                "repo_root": "/tmp",
                "profile": "deep-review",
                "posture": "evaluative",
                "turn_budget": 6,
            },
            DIALOGUE_START_POLICY,
        )
        assert verdict.action == "allow"
        assert verdict.unexpected_fields == ()


def test_delegate_decide_returns_decide_policy() -> None:
    policy = policy_for_tool(
        "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide"
    )
    assert policy is DELEGATE_DECIDE_POLICY


def test_delegate_decide_answers_field_is_scanned() -> None:
    verdict = check_tool_input(
        {
            "job_id": "job-1",
            "request_id": "req-1",
            "decision": "approve",
            "answers": {"q1": {"answers": ["sk-" + "a" * 40]}},
        },
        DELEGATE_DECIDE_POLICY,
    )
    assert verdict.action == "block"
