"""Regression tests for codex_guard hook after credential_scan extraction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scripts.codex_guard import handle_pre, handle_post


def _make_pre_data(
    prompt: str = "safe prompt",
    tool: str = "mcp__plugin_cross-model_codex__codex",
    tool_input: dict | None = None,
) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "session_id": "test-session",
        "tool_input": tool_input if tool_input is not None else {"prompt": prompt},
    }


class TestHandlePre:
    """PreToolUse handler blocks on credentials."""

    @patch("scripts.codex_guard._append_log")
    def test_clean_prompt_allows(self, _mock_log: MagicMock) -> None:
        assert handle_pre(_make_pre_data("fix the auth test")) == 0

    @patch("scripts.codex_guard._append_log")
    def test_aws_key_blocks(self, _mock_log: MagicMock) -> None:
        assert handle_pre(_make_pre_data("key AKIAIOSFODNN7EXAMPLE")) == 2

    @patch("scripts.codex_guard._append_log")
    def test_broad_tier_allows(self, _mock_log: MagicMock) -> None:
        """Broad tier is shadow-only, does not block."""
        assert handle_pre(_make_pre_data("password = mysecretvalue123")) == 0

    @patch("scripts.codex_guard._append_log")
    def test_scan_base_instructions(self, _mock_log: MagicMock) -> None:
        data = _make_pre_data(
            tool_input={
                "prompt": "safe prompt",
                "base-instructions": "Authorization: Basic dXNlcjpwYXNz",
            }
        )
        assert handle_pre(data) == 2

    @patch("scripts.codex_guard._append_log")
    def test_scan_developer_instructions(self, _mock_log: MagicMock) -> None:
        data = _make_pre_data(
            tool_input={
                "prompt": "safe prompt",
                "developer-instructions": "xoxb-1234-5678-abcdef",
            }
        )
        assert handle_pre(data) == 2

    @patch("scripts.codex_guard._append_log")
    def test_scan_nested_config(self, _mock_log: MagicMock) -> None:
        data = _make_pre_data(
            tool_input={
                "prompt": "safe prompt",
                "config": {"notes": "Authorization: Basic dXNlcjpwYXNz"},
            }
        )
        assert handle_pre(data) == 2

    @patch("scripts.codex_guard._append_log")
    def test_unknown_field_logged(self, mock_log: MagicMock) -> None:
        data = _make_pre_data(
            tool_input={
                "prompt": "safe prompt",
                "diagnostics": {"note": "still safe"},
            }
        )
        assert handle_pre(data) == 0
        first_call = mock_log.call_args_list[0].args[0]
        assert first_call["event"] == "shadow"
        assert first_call["reason"] == "unexpected_fields"
        assert first_call["unexpected_fields"] == ["diagnostics"]

    @patch("scripts.codex_guard._append_log")
    def test_node_cap_exceeded(self, mock_log: MagicMock) -> None:
        tool_input = {"prompt": "safe prompt", "payload": ["x"] * 10001}
        assert handle_pre(_make_pre_data(tool_input=tool_input)) == 2
        entry = mock_log.call_args.args[0]
        assert entry["event"] == "block"
        assert "node cap exceeded" in entry["reason"]

    @patch("scripts.codex_guard._append_log")
    def test_char_cap_exceeded(self, mock_log: MagicMock) -> None:
        tool_input = {"prompt": "x" * ((256 * 1024) + 1)}
        assert handle_pre(_make_pre_data(tool_input=tool_input)) == 2
        entry = mock_log.call_args.args[0]
        assert entry["event"] == "block"
        assert "char cap exceeded" in entry["reason"]


class TestHandlePost:
    """PostToolUse handler always returns 0 and logs consultation events."""

    @patch("scripts.codex_guard._append_log")
    def test_always_allows(self, _mock_log: MagicMock) -> None:
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {"content": "response"},
        }
        assert handle_post(data) == 0

    @patch("scripts.codex_guard._append_log")
    def test_thread_id_from_tool_input(self, mock_log: MagicMock) -> None:
        """Extracts threadId string from tool_input."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test", "threadId": "thread-from-input"},
            "tool_response": {"content": "response"},
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert entry["thread_id"] == "thread-from-input"

    @patch("scripts.codex_guard._append_log")
    def test_thread_id_from_tool_response(self, mock_log: MagicMock) -> None:
        """Extracts threadId string from top-level tool_response."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {"content": "response", "threadId": "thread-from-response"},
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert entry["thread_id"] == "thread-from-response"

    @patch("scripts.codex_guard._append_log")
    def test_thread_id_from_structured_content(self, mock_log: MagicMock) -> None:
        """Extracts threadId string from tool_response.structuredContent."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {
                "content": "response",
                "structuredContent": {"threadId": "thread-from-structured"},
            },
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert entry["thread_id"] == "thread-from-structured"

    @patch("scripts.codex_guard._append_log")
    def test_thread_id_input_takes_priority(self, mock_log: MagicMock) -> None:
        """When multiple sources have threadId, tool_input wins."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test", "threadId": "input-thread"},
            "tool_response": {"content": "response", "threadId": "response-thread"},
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert entry["thread_id"] == "input-thread"

    @patch("scripts.codex_guard._append_log")
    def test_thread_id_none_when_absent(self, mock_log: MagicMock) -> None:
        """thread_id is None when no source has threadId."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {"content": "response"},
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert entry["thread_id"] is None

    @patch("scripts.codex_guard._append_log")
    def test_no_thread_id_present_field(self, mock_log: MagicMock) -> None:
        """Old thread_id_present bool field is replaced by thread_id string."""
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__plugin_cross-model_codex__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test", "threadId": "thread-123"},
            "tool_response": {"content": "response"},
        }
        handle_post(data)
        entry = mock_log.call_args.args[0]
        assert "thread_id_present" not in entry
