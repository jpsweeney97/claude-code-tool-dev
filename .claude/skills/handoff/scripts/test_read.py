#!/usr/bin/env python3
"""Tests for read.py - handoff skill SessionStart hook script.

The script now only prunes old handoffs silently. It does NOT auto-inject
or prompt for handoffs. Users must explicitly run /resume.
"""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch


class TestGetProjectName:
    """Test project name detection from git or directory."""

    def test_git_repo_uses_repo_name(self, tmp_path: Path, monkeypatch):
        """In a git repo, project name is the repo directory name."""
        repo = tmp_path / "my-cool-project"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)

        monkeypatch.chdir(repo)

        from read import get_project_name

        assert get_project_name() == "my-cool-project"

    def test_non_git_uses_cwd_name(self, tmp_path: Path, monkeypatch):
        """Without git, project name is the current directory name."""
        import importlib

        non_git = tmp_path / "some-directory"
        non_git.mkdir()

        monkeypatch.chdir(non_git)

        import read

        importlib.reload(read)

        with patch("read.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            assert read.get_project_name() == "some-directory"

    def test_git_timeout_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git times out, fall back to current directory name."""
        import importlib

        non_git = tmp_path / "timeout-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import read

        importlib.reload(read)

        with patch("read.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            assert read.get_project_name() == "timeout-test"

    def test_git_not_found_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git is not installed, fall back to current directory name."""
        import importlib

        non_git = tmp_path / "no-git-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import read

        importlib.reload(read)

        with patch("read.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            assert read.get_project_name() == "no-git-test"


class TestGetHandoffsDir:
    """Test handoffs directory resolution."""

    def test_returns_global_handoffs_path(self):
        """Handoffs directory is ~/.claude/handoffs/<project>/"""
        with patch("read.get_project_name", return_value="my-project"):
            from read import get_handoffs_dir

            expected = Path.home() / ".claude" / "handoffs" / "my-project"
            assert get_handoffs_dir() == expected


class TestPruneOldHandoffs:
    """Test 30-day retention pruning."""

    def test_deletes_files_older_than_30_days(self, tmp_path: Path):
        """Files older than 30 days are deleted."""
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

        from read import prune_old_handoffs

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

        from read import prune_old_handoffs

        deleted = prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert deleted == []
        assert recent.exists()

    def test_handles_missing_directory(self, tmp_path: Path):
        """Gracefully handles missing directory."""
        from read import prune_old_handoffs

        deleted = prune_old_handoffs(tmp_path / "nonexistent", max_age_days=30)
        assert deleted == []

    def test_boundary_file_just_under_30_days(self, tmp_path: Path):
        """File just under 30 days should NOT be deleted."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        boundary = handoffs_dir / "2025-12-09_10-00_boundary.md"
        boundary.write_text("just under 30 days old")
        # 30 days minus 1 minute = safely under the boundary
        boundary_time = time.time() - (30 * 24 * 60 * 60) + 60
        os.utime(boundary, (boundary_time, boundary_time))

        from read import prune_old_handoffs

        deleted = prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert deleted == []
        assert boundary.exists()

    def test_boundary_file_just_over_30_days(self, tmp_path: Path):
        """File just over 30 days should be deleted."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        boundary = handoffs_dir / "2025-12-09_10-00_boundary.md"
        boundary.write_text("just over 30 days old")
        # 30 days plus 1 minute = safely over the boundary
        boundary_time = time.time() - (30 * 24 * 60 * 60) - 60
        os.utime(boundary, (boundary_time, boundary_time))

        from read import prune_old_handoffs

        deleted = prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert len(deleted) == 1
        assert not boundary.exists()


class TestPruneOldHandoffsRobustness:
    """Test race condition and permission handling in prune_old_handoffs."""

    def test_handles_file_deleted_between_stat_and_unlink(self, tmp_path: Path):
        """Race condition: file deleted after stat, before unlink."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        old = handoffs_dir / "2025-12-01_10-00_race.md"
        old.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))

        from read import prune_old_handoffs

        prune_old_handoffs(handoffs_dir, max_age_days=30)

        assert not old.exists()

    def test_handles_permission_error_silently(self, tmp_path: Path, monkeypatch):
        """Permission error is silently ignored, continues with other files."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        # Create old files
        old1 = handoffs_dir / "2025-12-01_10-00_first.md"
        old1.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old1, (old_time, old_time))

        old2 = handoffs_dir / "2025-12-02_10-00_second.md"
        old2.write_text("content")
        os.utime(old2, (old_time, old_time))

        # Mock unlink to raise PermissionError on first file
        original_unlink = Path.unlink

        def mock_unlink(self, missing_ok=False):
            if self.name == "2025-12-01_10-00_first.md":
                raise PermissionError("Access denied")
            return original_unlink(self, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        from read import prune_old_handoffs

        # Should complete without raising
        prune_old_handoffs(handoffs_dir, max_age_days=30)

        # First file should still exist (permission error), second should be deleted
        assert old1.exists()
        assert not old2.exists()


class TestMain:
    """Test CLI entry point."""

    def test_silent_exit_with_handoffs(self, tmp_path: Path, monkeypatch):
        """Exits silently even when handoffs exist (no output, no prompts)."""
        import sys
        from io import StringIO

        handoffs_dir = tmp_path / ".claude" / "handoffs" / "test-project"
        handoffs_dir.mkdir(parents=True)

        handoff = handoffs_dir / "2026-01-08_14-30_test.md"
        handoff.write_text("""---
title: Test handoff
---

# Handoff: Test handoff
""")

        monkeypatch.setattr("read.get_handoffs_dir", lambda: handoffs_dir)

        captured = StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        from read import main

        exit_code = main()

        # Should produce NO output - explicit resume only
        assert captured.getvalue() == ""
        assert exit_code == 0

    def test_silent_exit_when_no_handoff(self, tmp_path: Path, monkeypatch):
        """Exits silently with exit code 0 when no handoff found."""
        import sys
        from io import StringIO

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir(parents=True)

        monkeypatch.setattr("read.get_handoffs_dir", lambda: empty_dir)

        captured = StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        from read import main

        exit_code = main()

        assert captured.getvalue() == ""
        assert exit_code == 0

    def test_prunes_old_handoffs_silently(self, tmp_path: Path, monkeypatch):
        """Prunes old handoffs without any output."""
        import sys
        from io import StringIO

        handoffs_dir = tmp_path / ".claude" / "handoffs" / "test-project"
        handoffs_dir.mkdir(parents=True)

        # Create old file
        old = handoffs_dir / "2025-12-01_10-00_old.md"
        old.write_text("old content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))

        monkeypatch.setattr("read.get_handoffs_dir", lambda: handoffs_dir)

        captured = StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        from read import main

        exit_code = main()

        # Should produce no output
        assert captured.getvalue() == ""
        assert exit_code == 0
        # Old file should be pruned
        assert not old.exists()
