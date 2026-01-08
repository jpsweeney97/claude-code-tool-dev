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


class TestGetHandoffsDir:
    """Test handoffs directory resolution."""

    def test_returns_global_handoffs_path(self):
        """Handoffs directory is ~/.claude/handoffs/<project>/"""
        with patch("read_v2.get_project_name", return_value="my-project"):
            from read_v2 import get_handoffs_dir

            expected = Path.home() / ".claude" / "handoffs" / "my-project"
            assert get_handoffs_dir() == expected


class TestFindLatestHandoff:
    """Test finding most recent handoff file."""

    def test_returns_most_recent_by_mtime(self, tmp_path: Path):
        """Finds handoff with newest modification time."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        # Create older file
        old = handoffs_dir / "2026-01-01_10-00_old.md"
        old.write_text("old content")

        # Create newer file (touch to ensure newer mtime)
        import time

        time.sleep(0.01)
        new = handoffs_dir / "2026-01-08_14-30_new.md"
        new.write_text("new content")

        from read_v2 import find_latest_handoff

        assert find_latest_handoff(handoffs_dir) == new

    def test_returns_none_when_no_handoffs(self, tmp_path: Path):
        """Returns None when directory is empty."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        from read_v2 import find_latest_handoff

        assert find_latest_handoff(handoffs_dir) is None

    def test_returns_none_when_dir_missing(self, tmp_path: Path):
        """Returns None when directory doesn't exist."""
        from read_v2 import find_latest_handoff

        assert find_latest_handoff(tmp_path / "nonexistent") is None


class TestPruneOldHandoffs:
    """Test 30-day retention pruning."""

    def test_deletes_files_older_than_30_days(self, tmp_path: Path):
        """Files older than 30 days are deleted."""
        import os
        import time

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        # Create old file (simulate 31 days ago via mtime)
        old = handoffs_dir / "2025-12-01_10-00_ancient.md"
        old.write_text("old content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))

        # Create recent file
        recent = handoffs_dir / "2026-01-08_14-30_recent.md"
        recent.write_text("recent content")

        from read_v2 import prune_old_handoffs

        deleted = prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert deleted == [old]
        assert not old.exists()
        assert recent.exists()

    def test_keeps_files_within_retention(self, tmp_path: Path):
        """Files within 30 days are kept."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        recent = handoffs_dir / "2026-01-08_14-30_recent.md"
        recent.write_text("recent content")

        from read_v2 import prune_old_handoffs

        deleted = prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert deleted == []
        assert recent.exists()

    def test_handles_missing_directory(self, tmp_path: Path):
        """Gracefully handles missing directory."""
        from read_v2 import prune_old_handoffs

        deleted = prune_old_handoffs(tmp_path / "nonexistent", max_age_days=30)
        assert deleted == []