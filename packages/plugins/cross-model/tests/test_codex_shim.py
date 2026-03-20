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


from mcp.types import CallToolResult, TextContent


class TestBuildResponse:
    """Translate adapter result dict to MCP CallToolResult."""

    def test_success_has_structured_content(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": "thr_123",
            "response_text": "Here is the analysis.",
            "token_usage": {"input_tokens": 10, "output_tokens": 5},
            "runtime_failures": [],
            "error": None,
        })
        assert isinstance(result, CallToolResult)
        assert result.isError is False
        assert result.structuredContent == {
            "threadId": "thr_123",
            "content": "Here is the analysis.",
        }
        assert len(result.content) == 1
        assert result.content[0].text == "Here is the analysis."

    def test_blocked_is_error(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "blocked",
            "error": "AWS key detected",
        })
        assert result.isError is True
        assert "Blocked" in result.content[0].text

    def test_error_is_error(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "error",
            "error": "codex not found on PATH",
        })
        assert result.isError is True
        assert "codex not found" in result.content[0].text

    def test_timeout_preserves_partial_token(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "timeout_uncertain",
            "error": "exec failed: process timeout",
            "continuation_id": "thr_partial",
        })
        assert result.isError is True
        assert "Timeout" in result.content[0].text
        assert result.structuredContent == {"threadId": "thr_partial", "content": ""}

    def test_timeout_without_token(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "timeout_uncertain",
            "error": "exec failed: process timeout",
            "continuation_id": None,
        })
        assert result.isError is True
        assert result.structuredContent == {"threadId": None, "content": ""}

    def test_null_response_text_uses_empty_string(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": "thr_456",
            "response_text": None,
        })
        assert result.isError is False
        assert result.structuredContent["content"] == ""
        assert result.content[0].text == ""

    def test_null_continuation_id_preserved(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": None,
            "response_text": "Some response",
        })
        assert result.structuredContent["threadId"] is None
