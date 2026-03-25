"""Tests for consultation_safety shared module."""

from __future__ import annotations

import pytest

from scripts.consultation_safety import (
    ToolScanPolicy,
    extract_strings,
    ToolInputLimitExceeded,
)


class TestExtractStrings:
    """extract_strings traverses tool_input per policy."""

    def test_scans_content_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox"},
            content_fields={"prompt"},
        )
        texts, unexpected = extract_strings(
            {"prompt": "hello world", "sandbox": "read-only"}, policy
        )
        assert texts == ["hello world"]
        assert unexpected == []

    def test_skips_expected_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox", "model"},
            content_fields={"prompt"},
        )
        texts, _ = extract_strings(
            {"prompt": "test", "sandbox": "read-only", "model": "gpt-5"}, policy
        )
        assert texts == ["test"]

    def test_reports_unexpected_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox"},
            content_fields={"prompt"},
        )
        texts, unexpected = extract_strings(
            {"prompt": "test", "diagnostics": "extra"}, policy
        )
        assert "diagnostics" in unexpected

    def test_traverses_nested_dicts(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"config"},
        )
        texts, _ = extract_strings(
            {"config": {"nested": "secret value"}}, policy
        )
        assert "secret value" in texts

    def test_rejects_non_dict_input(self) -> None:
        policy = ToolScanPolicy(expected_fields=set(), content_fields=set())
        with pytest.raises(TypeError, match="tool_input must be dict"):
            extract_strings("not a dict", policy)

    def test_node_cap_exceeded(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"data"},
            scan_unknown_fields=True,
        )
        data: dict = {"data": {}}
        current = data["data"]
        for i in range(200):
            current[f"k{i}"] = {}
            for j in range(60):
                current[f"k{i}"][f"v{j}"] = "x"
        with pytest.raises(ToolInputLimitExceeded):
            extract_strings(data, policy)


from unittest.mock import patch, MagicMock

from scripts.consultation_safety import SafetyVerdict, check_tool_input, START_POLICY


class TestSafetyVerdict:
    """SafetyVerdict represents credential scan outcome."""

    def test_allow_verdict(self) -> None:
        v = SafetyVerdict(action="allow")
        assert v.action == "allow"
        assert v.reason is None

    def test_block_verdict(self) -> None:
        v = SafetyVerdict(action="block", reason="AWS key detected", tier="strict")
        assert v.action == "block"
        assert v.tier == "strict"

    def test_unexpected_fields_tracked(self) -> None:
        v = SafetyVerdict(action="allow", unexpected_fields=["bogus"])
        assert v.unexpected_fields == ["bogus"]


class TestCheckToolInput:
    """check_tool_input runs credential scan on tool_input per policy."""

    @patch("scripts.consultation_safety.scan_text")
    def test_clean_input_allows(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="allow", tier=None, reason=None)
        verdict = check_tool_input({"prompt": "fix the test"}, START_POLICY)
        assert verdict.action == "allow"

    @patch("scripts.consultation_safety.scan_text")
    def test_credential_blocks(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="block", tier="strict", reason="AWS key")
        verdict = check_tool_input({"prompt": "AKIAIOSFODNN7EXAMPLE"}, START_POLICY)
        assert verdict.action == "block"
        assert verdict.tier == "strict"

    @patch("scripts.consultation_safety.scan_text")
    def test_shadow_allows_with_reason(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="shadow", tier="broad", reason="password-like")
        verdict = check_tool_input({"prompt": "password=foo"}, START_POLICY)
        assert verdict.action == "shadow"

    @patch("scripts.consultation_safety.scan_text")
    def test_worst_verdict_wins(self, mock_scan: MagicMock) -> None:
        """When multiple texts scanned, worst action wins (block > shadow > allow)."""
        mock_scan.side_effect = [
            MagicMock(action="allow", tier=None, reason=None),
            MagicMock(action="block", tier="strict", reason="key found"),
        ]
        verdict = check_tool_input(
            {"prompt": "safe", "base-instructions": "has key"}, START_POLICY
        )
        assert verdict.action == "block"

    def test_non_dict_raises(self) -> None:
        with pytest.raises(TypeError):
            check_tool_input("not a dict", START_POLICY)

    @patch("scripts.consultation_safety.scan_text")
    def test_unexpected_fields_reported(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="allow", tier=None, reason=None)
        verdict = check_tool_input(
            {"prompt": "test", "bogus_field": "data"}, START_POLICY
        )
        assert "bogus_field" in verdict.unexpected_fields


class TestDelegationPolicy:
    """DELEGATION_POLICY scans only the prompt field for credential egress."""

    def test_delegation_policy_exists(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY is not None

    def test_delegation_policy_content_fields(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY.content_fields == {"prompt"}

    def test_delegation_policy_expected_fields(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert "model" in DELEGATION_POLICY.expected_fields
        assert "sandbox" in DELEGATION_POLICY.expected_fields
        assert "reasoning_effort" in DELEGATION_POLICY.expected_fields
        assert "full_auto" in DELEGATION_POLICY.expected_fields

    def test_delegation_policy_does_not_scan_unknown_fields(self):
        """Unknown fields are rejected by validation, not dispatched to Codex.
        Scanning them conflates 'unexpected input' with 'egress risk'."""
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY.scan_unknown_fields is False

    def test_delegation_policy_blocks_credential_in_prompt(self):
        from scripts.consultation_safety import DELEGATION_POLICY, check_tool_input
        result = check_tool_input(
            {"prompt": "AKIAIOSFODNN7EXAMPLE", "model": "o3-pro", "sandbox": "read-only"},
            DELEGATION_POLICY,
        )
        assert result.action == "block"

    def test_delegation_policy_allows_clean_prompt(self):
        from scripts.consultation_safety import DELEGATION_POLICY, check_tool_input
        result = check_tool_input(
            {"prompt": "safe prompt", "model": "o3-pro", "sandbox": "read-only"},
            DELEGATION_POLICY,
        )
        assert result.action == "allow"


class TestTierRankExport:
    """TIER_RANK is a public constant for use by codex_guard.py."""

    def test_tier_rank_exported(self):
        from scripts.consultation_safety import TIER_RANK
        assert isinstance(TIER_RANK, dict)

    def test_tier_rank_ordering(self):
        from scripts.consultation_safety import TIER_RANK
        assert TIER_RANK["strict"] < TIER_RANK["contextual"]


class TestDelegationPolicyFieldSync:
    """DELEGATION_POLICY fields must stay in sync with codex_delegate._KNOWN_FIELDS."""

    def test_policy_covers_known_fields(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        from scripts.codex_delegate import _KNOWN_FIELDS

        policy_fields = DELEGATION_POLICY.expected_fields | DELEGATION_POLICY.content_fields
        assert policy_fields == _KNOWN_FIELDS, (
            f"DELEGATION_POLICY fields {policy_fields} != "
            f"codex_delegate._KNOWN_FIELDS {_KNOWN_FIELDS}"
        )
