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


import asyncio
from unittest.mock import patch, MagicMock


class TestCreateServer:
    """FastMCP server creation and tool registration."""

    def test_server_has_codex_tool(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tools = server._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "codex" in tool_names

    def test_server_has_codex_reply_tool(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tools = server._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "codex-reply" in tool_names

    def test_server_name_is_codex(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        assert server.name == "codex"

    def test_codex_tool_schema_is_flat(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        props = tool.parameters["properties"]
        assert "prompt" in props
        assert "model" in props
        assert "config" in props
        # No nested "params" wrapper
        assert "params" not in props


class TestRoundTrip:
    """Full round-trip: mock consult, dispatch through FastMCP tool, verify response."""

    @patch("scripts.codex_shim.consult")
    def test_codex_new_conversation(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        from mcp.types import CallToolResult
        mock_consult.return_value = {
            "status": "ok",
            "dispatched": True,
            "continuation_id": "thr_new",
            "response_text": "Analysis complete.",
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
            "runtime_failures": [],
            "error": None,
            "dispatch_state": "complete",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        result = asyncio.run(tool.run({
            "prompt": "review this code",
            "config": {"model_reasoning_effort": "high"},
            "model": "o3-pro",
        }))
        assert isinstance(result, CallToolResult)
        assert result.structuredContent["threadId"] == "thr_new"
        assert result.content[0].text == "Analysis complete."
        mock_consult.assert_called_once_with(
            prompt="review this code",
            model="o3-pro",
            reasoning_effort="high",
        )

    @patch("scripts.codex_shim.consult")
    def test_codex_reply_passes_thread_id(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        from mcp.types import CallToolResult
        mock_consult.return_value = {
            "status": "ok",
            "dispatched": True,
            "continuation_id": "thr_continued",
            "response_text": "Follow-up answer.",
            "token_usage": None,
            "runtime_failures": [],
            "error": None,
            "dispatch_state": "complete",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex-reply"]
        result = asyncio.run(tool.run({
            "prompt": "elaborate on point 2",
            "threadId": "thr_original",
        }))
        assert isinstance(result, CallToolResult)
        assert result.structuredContent["threadId"] == "thr_continued"
        mock_consult.assert_called_once_with(
            prompt="elaborate on point 2",
            thread_id="thr_original",
        )

    @patch("scripts.codex_shim.consult")
    def test_codex_blocked_returns_error(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        mock_consult.return_value = {
            "status": "blocked",
            "dispatched": False,
            "error": "credential detected",
            "continuation_id": None,
            "response_text": None,
            "token_usage": None,
            "runtime_failures": [],
            "dispatch_state": "no_dispatch",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        result = asyncio.run(tool.run({"prompt": "AKIAIOSFODNN7EXAMPLE"}))
        assert result.isError is True
        assert "Blocked" in result.content[0].text
