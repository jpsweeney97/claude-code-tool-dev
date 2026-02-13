"""Tests for the MCP server setup."""

import os

from context_injection.server import _load_git_files, create_server


def test_server_has_name() -> None:
    server = create_server()
    assert server.name == "context-injection"


def test_server_has_process_turn_tool() -> None:
    server = create_server()
    # _tool_manager is private API; no public tool listing method in FastMCP v1.26.0.
    tools = server._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "process_turn_tool" in tool_names


def test_load_git_files_returns_set() -> None:
    """git ls-files from this repo should return non-empty set."""
    # tests/test_server.py -> tests/ -> context-injection/ -> packages/ -> repo root
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    result = _load_git_files(repo_root)
    assert isinstance(result, set)
    assert len(result) > 0


def test_load_git_files_fail_closed() -> None:
    """Non-existent directory should return empty set (fail closed)."""
    result = _load_git_files("/nonexistent/path")
    assert result == set()
