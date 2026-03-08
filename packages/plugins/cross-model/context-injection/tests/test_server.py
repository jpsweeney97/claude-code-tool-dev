"""Tests for the MCP server setup."""

from pathlib import Path
import subprocess
from unittest.mock import Mock, patch

from context_injection.server import (
    _load_git_files,
    create_server,
)


def test_server_has_name() -> None:
    server = create_server()
    assert server.name == "context-injection"


def test_server_has_process_turn_tool() -> None:
    server = create_server()
    # _tool_manager is private API; no public tool listing method in FastMCP v1.26.0.
    tools = server._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "process_turn" in tool_names


def test_server_has_execute_scout_tool() -> None:
    server = create_server()
    tools = server._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "execute_scout" in tool_names


def test_load_git_files_returns_set() -> None:
    """git ls-files from this repo should return non-empty set."""
    repo_root = next(
        (
            parent
            for parent in Path(__file__).resolve().parents
            if (parent / ".git").exists()
        ),
        None,
    )
    assert repo_root is not None, "Could not find .git directory in any parent"
    result = _load_git_files(str(repo_root))
    assert isinstance(result, set)
    assert len(result) > 0


def test_load_git_files_fail_closed() -> None:
    """Non-existent directory should return empty set (fail closed)."""
    result = _load_git_files("/nonexistent/path")
    assert result == set()


def test_load_git_files_timeout_returns_empty() -> None:
    """TimeoutExpired from subprocess -> empty set (fail closed)."""
    with patch(
        "context_injection.server.subprocess.run",
        side_effect=subprocess.TimeoutExpired("git", 10),
    ):
        result = _load_git_files("/any")
    assert result == set()


def test_load_git_files_nonzero_exit_returns_empty() -> None:
    """Non-zero exit code from git ls-files -> empty set (fail closed)."""
    with patch(
        "context_injection.server.subprocess.run",
        return_value=Mock(returncode=1, stderr="fatal: not a git repository"),
    ):
        result = _load_git_files("/any")
    assert result == set()
