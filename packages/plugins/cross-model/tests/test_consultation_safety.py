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
