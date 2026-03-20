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
