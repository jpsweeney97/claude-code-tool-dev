"""Tests for codex_shim MCP compatibility server."""

from __future__ import annotations


class TestExtractReasoningEffort:
    """Extract model_reasoning_effort from MCP config object."""

    def test_extracts_from_config(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"model_reasoning_effort": "high"}) == "high"

    def test_defaults_to_xhigh(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort(None) == "xhigh"

    def test_defaults_on_missing_key(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"other_key": "value"}) == "xhigh"

    def test_defaults_on_non_string_value(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"model_reasoning_effort": 42}) == "xhigh"
