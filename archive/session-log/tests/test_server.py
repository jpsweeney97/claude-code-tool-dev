"""Tests for MCP server security utilities and tool handlers."""

from pathlib import Path
from unittest.mock import patch


class TestGetSessionPathValidation:
    """Test path traversal prevention in get_session."""

    def test_valid_path_within_claude_dir(self, tmp_path):
        """Test that valid paths within .claude are allowed."""
        from security import validate_summary_path

        # Create mock .claude structure
        claude_dir = tmp_path / ".claude"
        sessions_dir = claude_dir / "sessions"
        sessions_dir.mkdir(parents=True)
        summary_file = sessions_dir / "2025-01-01_test.md"
        summary_file.write_text("# Test")

        result = validate_summary_path(str(summary_file), claude_dir)
        assert result == str(summary_file)

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        from security import validate_summary_path

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Attempt to traverse outside .claude
        malicious_path = str(claude_dir / ".." / "etc" / "passwd")

        result = validate_summary_path(malicious_path, claude_dir)
        assert result is None

    def test_nonexistent_path_returns_none(self, tmp_path):
        """Test that nonexistent paths return None."""
        from security import validate_summary_path

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        result = validate_summary_path(str(claude_dir / "nonexistent.md"), claude_dir)
        assert result is None

    def test_symlink_escape_blocked(self, tmp_path):
        """Test that symlinks escaping .claude are blocked."""
        from security import validate_summary_path

        claude_dir = tmp_path / ".claude"
        sessions_dir = claude_dir / "sessions"
        sessions_dir.mkdir(parents=True)

        # Create a file outside .claude
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("secret data")

        # Create symlink inside .claude pointing outside
        symlink = sessions_dir / "escape.md"
        symlink.symlink_to(outside_file)

        result = validate_summary_path(str(symlink), claude_dir)
        assert result is None


class TestGetToolDefinitions:
    """Test the get_tool_definitions function."""

    def test_returns_expected_tools(self):
        """Test that get_tool_definitions returns all tools."""
        from tool_handlers import get_tool_definitions

        tools = get_tool_definitions()

        assert len(tools) == 3
        tool_names = {t["name"] for t in tools}
        assert tool_names == {"list_sessions", "get_session", "search_sessions"}

    def test_list_sessions_has_correct_schema(self):
        """Test that list_sessions tool has correct input schema."""
        from tool_handlers import get_tool_definitions

        tools = get_tool_definitions()
        list_sessions_tool = next(t for t in tools if t["name"] == "list_sessions")

        schema = list_sessions_tool["inputSchema"]
        assert "project" in schema["properties"]
        assert "after" in schema["properties"]
        assert "before" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_get_session_has_required_filename(self):
        """Test that get_session tool requires filename."""
        from tool_handlers import get_tool_definitions

        tools = get_tool_definitions()
        get_session_tool = next(t for t in tools if t["name"] == "get_session")

        assert "filename" in get_session_tool["inputSchema"].get("required", [])


class TestHandleTool:
    """Test the handle_tool function."""

    def test_list_sessions_returns_json(self):
        """Test list_sessions returns JSON formatted results."""
        from tool_handlers import handle_tool

        with patch("tool_handlers.db_list_sessions", return_value=[]):
            result = handle_tool("list_sessions", {})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "[]" in result[0].text

    def test_list_sessions_with_filters(self):
        """Test list_sessions passes filters correctly."""
        from tool_handlers import handle_tool

        mock_sessions = [
            {"filename": "test.md", "project": "test-project"}
        ]

        with patch("tool_handlers.db_list_sessions", return_value=mock_sessions) as mock:
            result = handle_tool("list_sessions", {
                "project": "test-project",
                "after": "2025-01-01",
                "before": "2025-12-31",
                "limit": 10,
            })

            mock.assert_called_once_with(
                project="test-project",
                after="2025-01-01",
                before="2025-12-31",
                limit=10,
            )

        assert "test-project" in result[0].text

    def test_get_session_not_found(self):
        """Test get_session with nonexistent session."""
        from tool_handlers import handle_tool

        with patch("tool_handlers.db_get_session", return_value=None):
            result = handle_tool("get_session", {"filename": "nonexistent.md"})

        assert "not found" in result[0].text.lower()

    def test_get_session_missing_filename(self):
        """Test get_session without filename parameter."""
        from tool_handlers import handle_tool

        result = handle_tool("get_session", {})

        assert "filename required" in result[0].text.lower()

    def test_get_session_returns_content(self, tmp_path):
        """Test get_session returns markdown content when path is valid."""
        from tool_handlers import handle_tool

        mock_session = {
            "filename": "test.md",
            "summary_path": str(tmp_path / "test.md"),
        }

        # Create a mock markdown file
        (tmp_path / "test.md").write_text("# Test Session\n\nContent here.")

        with patch("tool_handlers.db_get_session", return_value=mock_session):
            with patch("tool_handlers.validate_summary_path", return_value=str(tmp_path / "test.md")):
                result = handle_tool("get_session", {"filename": "test.md"})

        assert "Test Session" in result[0].text

    def test_get_session_invalid_path_returns_metadata(self):
        """Test get_session returns metadata when path validation fails."""
        from tool_handlers import handle_tool

        mock_session = {
            "filename": "test.md",
            "summary_path": "/some/path/test.md",
            "project": "test-project",
        }

        with patch("tool_handlers.db_get_session", return_value=mock_session):
            with patch("tool_handlers.validate_summary_path", return_value=None):
                result = handle_tool("get_session", {"filename": "test.md"})

        # Should return explicit error when path validation fails
        assert "Error:" in result[0].text
        assert "path validation failed" in result[0].text.lower()

    def test_unknown_tool(self):
        """Test calling unknown tool."""
        from tool_handlers import handle_tool

        result = handle_tool("unknown_tool", {})

        assert "unknown tool" in result[0].text.lower()

    def test_get_session_handles_read_error(self, tmp_path):
        """Test get_session handles file read errors gracefully."""
        from tool_handlers import handle_tool

        mock_session = {
            "filename": "test.md",
            "summary_path": str(tmp_path / "test.md"),
        }

        with patch("tool_handlers.db_get_session", return_value=mock_session):
            with patch("tool_handlers.validate_summary_path", return_value=str(tmp_path / "test.md")):
                # File doesn't exist, so read_text will raise FileNotFoundError (OSError subclass)
                result = handle_tool("get_session", {"filename": "test.md"})

        assert "error" in result[0].text.lower()

    def test_get_session_handles_permission_error(self, tmp_path):
        """Test get_session handles permission errors gracefully."""
        from tool_handlers import handle_tool

        mock_session = {
            "filename": "test.md",
            "summary_path": str(tmp_path / "test.md"),
        }

        with patch("tool_handlers.db_get_session", return_value=mock_session):
            with patch("tool_handlers.validate_summary_path", return_value=str(tmp_path / "test.md")):
                with patch.object(Path, "read_text", side_effect=PermissionError("Access denied")):
                    result = handle_tool("get_session", {"filename": "test.md"})

        assert "permission denied" in result[0].text.lower()
