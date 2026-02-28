"""Tests for project_paths.py — shared path utilities."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.project_paths import get_handoffs_dir, get_project_name


class TestGetProjectName:
    """Tests for get_project_name."""

    def test_returns_git_root_name(self) -> None:
        with patch("scripts.project_paths.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "/Users/jp/Projects/myproject\n"
            name, source = get_project_name()
        assert name == "myproject"
        assert source == "git"

    def test_falls_back_to_cwd(self) -> None:
        with patch("scripts.project_paths.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            name, source = get_project_name()
        assert source == "cwd"


class TestGetProjectNameExceptions:
    """Exception paths in get_project_name."""

    def test_git_not_found_falls_back_to_cwd(self) -> None:
        with patch("scripts.project_paths.subprocess.run", side_effect=FileNotFoundError):
            name, source = get_project_name()
            assert source == "cwd"

    def test_timeout_falls_back_to_cwd(self) -> None:
        with patch(
            "scripts.project_paths.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="git", timeout=5),
        ):
            name, source = get_project_name()
            assert source == "cwd"

    def test_oserror_falls_back_to_cwd(self) -> None:
        with patch("scripts.project_paths.subprocess.run", side_effect=OSError("disk error")):
            name, source = get_project_name()
            assert source == "cwd"

    def test_exception_logs_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("scripts.project_paths.subprocess.run", side_effect=FileNotFoundError):
            get_project_name()
        assert "Warning: git project detection failed" in capsys.readouterr().err


class TestGetHandoffsDir:
    """Tests for get_handoffs_dir."""

    def test_returns_handoffs_path(self) -> None:
        with patch("scripts.project_paths.get_project_name", return_value=("myproject", "git")):
            result = get_handoffs_dir()
        assert result == Path.home() / ".claude" / "handoffs" / "myproject"
