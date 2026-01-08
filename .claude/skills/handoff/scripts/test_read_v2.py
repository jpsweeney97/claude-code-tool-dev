#!/usr/bin/env python3
"""Tests for read_v2.py - handoff skill v2 read script."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetProjectName:
    """Test project name detection from git or directory."""

    def test_git_repo_uses_repo_name(self, tmp_path: Path, monkeypatch):
        """In a git repo, project name is the repo directory name."""
        # Create a git repo
        repo = tmp_path / "my-cool-project"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)

        monkeypatch.chdir(repo)

        from read_v2 import get_project_name

        assert get_project_name() == "my-cool-project"

    def test_non_git_uses_cwd_name(self, tmp_path: Path, monkeypatch):
        """Without git, project name is the current directory name."""
        non_git = tmp_path / "some-directory"
        non_git.mkdir()

        monkeypatch.chdir(non_git)

        # Need fresh import after changing directory
        import importlib

        import read_v2

        importlib.reload(read_v2)

        # Mock git failing to simulate non-git directory
        with patch("read_v2.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            assert read_v2.get_project_name() == "some-directory"

    def test_git_timeout_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git times out, fall back to current directory name."""
        non_git = tmp_path / "timeout-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import importlib

        import read_v2

        importlib.reload(read_v2)

        with patch("read_v2.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            assert read_v2.get_project_name() == "timeout-test"

    def test_git_not_found_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git is not installed, fall back to current directory name."""
        non_git = tmp_path / "no-git-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import importlib

        import read_v2

        importlib.reload(read_v2)

        with patch("read_v2.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            assert read_v2.get_project_name() == "no-git-test"
