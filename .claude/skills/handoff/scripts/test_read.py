#!/usr/bin/env python3
"""Tests for read.py - handoff skill SessionStart hook script.

The script prunes old handoffs, archives, and state files silently.
It does NOT auto-inject or prompt for handoffs. Users must explicitly
run /resume.
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


class TestGetSessionStateDir:
    """Test session state directory resolution."""

    def test_returns_session_state_path(self):
        """Session state directory is ~/.claude/.session-state/"""
        from read import get_session_state_dir

        expected = Path.home() / ".claude" / ".session-state"
        assert get_session_state_dir() == expected


class TestPruneOldArchives:
    """Test 90-day retention pruning for archived handoffs."""

    def test_deletes_archives_older_than_90_days(self, tmp_path: Path):
        """Archived files older than 90 days are deleted."""
        handoffs_dir = tmp_path / "handoffs"
        archive_dir = handoffs_dir / ".archive"
        archive_dir.mkdir(parents=True)

        # Create old archived file (simulate 91 days ago via mtime)
        old = archive_dir / "2025-10-01_10-00_ancient.md"
        old.write_text("old archived content")
        old_time = time.time() - (91 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))

        # Create recent archived file
        recent = archive_dir / "2026-01-08_14-30_recent.md"
        recent.write_text("recent archived content")

        from read import prune_old_archives

        deleted = prune_old_archives(handoffs_dir, max_age_days=90)

        assert deleted == [old]
        assert not old.exists()
        assert recent.exists()

    def test_keeps_archives_within_retention(self, tmp_path: Path):
        """Archived files within 90 days are kept."""
        handoffs_dir = tmp_path / "handoffs"
        archive_dir = handoffs_dir / ".archive"
        archive_dir.mkdir(parents=True)

        recent = archive_dir / "2026-01-08_14-30_recent.md"
        recent.write_text("recent archived content")

        from read import prune_old_archives

        deleted = prune_old_archives(handoffs_dir, max_age_days=90)

        assert deleted == []
        assert recent.exists()

    def test_handles_missing_archive_directory(self, tmp_path: Path):
        """Gracefully handles missing .archive directory."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)
        # .archive does not exist

        from read import prune_old_archives

        deleted = prune_old_archives(handoffs_dir, max_age_days=90)
        assert deleted == []

    def test_handles_missing_handoffs_directory(self, tmp_path: Path):
        """Gracefully handles missing handoffs directory."""
        from read import prune_old_archives

        deleted = prune_old_archives(tmp_path / "nonexistent", max_age_days=90)
        assert deleted == []


class TestPruneOldStateFiles:
    """Test 24-hour retention pruning for session state files."""

    def test_deletes_state_files_older_than_24_hours(self, tmp_path: Path, monkeypatch):
        """State files older than 24 hours are deleted."""
        state_dir = tmp_path / ".session-state"
        state_dir.mkdir(parents=True)

        monkeypatch.setattr("read.get_session_state_dir", lambda: state_dir)

        # Create old state file (simulate 25 hours ago via mtime)
        old = state_dir / "handoff-old-session-id"
        old.write_text("/path/to/archived/handoff.md")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(old, (old_time, old_time))

        # Create recent state file
        recent = state_dir / "handoff-recent-session-id"
        recent.write_text("/path/to/another/handoff.md")

        from read import prune_old_state_files

        deleted = prune_old_state_files(max_age_hours=24)

        assert deleted == [old]
        assert not old.exists()
        assert recent.exists()

    def test_keeps_state_files_within_retention(self, tmp_path: Path, monkeypatch):
        """State files within 24 hours are kept."""
        state_dir = tmp_path / ".session-state"
        state_dir.mkdir(parents=True)

        monkeypatch.setattr("read.get_session_state_dir", lambda: state_dir)

        recent = state_dir / "handoff-recent-session-id"
        recent.write_text("/path/to/handoff.md")

        from read import prune_old_state_files

        deleted = prune_old_state_files(max_age_hours=24)

        assert deleted == []
        assert recent.exists()

    def test_handles_missing_state_directory(self, tmp_path: Path, monkeypatch):
        """Gracefully handles missing state directory."""
        monkeypatch.setattr(
            "read.get_session_state_dir", lambda: tmp_path / "nonexistent"
        )

        from read import prune_old_state_files

        deleted = prune_old_state_files(max_age_hours=24)
        assert deleted == []

    def test_only_prunes_handoff_prefixed_files(self, tmp_path: Path, monkeypatch):
        """Only files matching handoff-* pattern are pruned."""
        state_dir = tmp_path / ".session-state"
        state_dir.mkdir(parents=True)

        monkeypatch.setattr("read.get_session_state_dir", lambda: state_dir)

        # Create old state file with handoff prefix
        old_handoff = state_dir / "handoff-old-session"
        old_handoff.write_text("content")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(old_handoff, (old_time, old_time))

        # Create old file without handoff prefix (should not be touched)
        other_file = state_dir / "other-state-file"
        other_file.write_text("other content")
        os.utime(other_file, (old_time, old_time))

        from read import prune_old_state_files

        deleted = prune_old_state_files(max_age_hours=24)

        assert deleted == [old_handoff]
        assert not old_handoff.exists()
        assert other_file.exists()  # Should not be deleted


class TestMainIntegration:
    """Test that main() calls all pruning functions."""

    def test_main_calls_all_pruning_functions(self, tmp_path: Path, monkeypatch):
        """main() should call prune_old_handoffs, prune_old_archives, prune_old_state_files."""
        handoffs_dir = tmp_path / ".claude" / "handoffs" / "test-project"
        archive_dir = handoffs_dir / ".archive"
        state_dir = tmp_path / ".session-state"

        handoffs_dir.mkdir(parents=True)
        archive_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        # Create old files in each location
        old_handoff = handoffs_dir / "2025-12-01_10-00_old.md"
        old_handoff.write_text("old handoff")
        old_handoff_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old_handoff, (old_handoff_time, old_handoff_time))

        old_archive = archive_dir / "2025-10-01_10-00_archived.md"
        old_archive.write_text("old archive")
        old_archive_time = time.time() - (91 * 24 * 60 * 60)
        os.utime(old_archive, (old_archive_time, old_archive_time))

        old_state = state_dir / "handoff-old-session"
        old_state.write_text("/path/to/handoff.md")
        old_state_time = time.time() - (25 * 60 * 60)
        os.utime(old_state, (old_state_time, old_state_time))

        monkeypatch.setattr("read.get_handoffs_dir", lambda: handoffs_dir)
        monkeypatch.setattr("read.get_session_state_dir", lambda: state_dir)

        from read import main

        exit_code = main()

        assert exit_code == 0
        assert not old_handoff.exists(), "Old handoff should be pruned"
        assert not old_archive.exists(), "Old archive should be pruned"
        assert not old_state.exists(), "Old state file should be pruned"

    def test_main_keeps_recent_files(self, tmp_path: Path, monkeypatch):
        """main() should keep files within their retention periods."""
        handoffs_dir = tmp_path / ".claude" / "handoffs" / "test-project"
        archive_dir = handoffs_dir / ".archive"
        state_dir = tmp_path / ".session-state"

        handoffs_dir.mkdir(parents=True)
        archive_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        # Create recent files in each location
        recent_handoff = handoffs_dir / "2026-01-08_14-30_recent.md"
        recent_handoff.write_text("recent handoff")

        recent_archive = archive_dir / "2026-01-08_14-30_archived.md"
        recent_archive.write_text("recent archive")

        recent_state = state_dir / "handoff-recent-session"
        recent_state.write_text("/path/to/handoff.md")

        monkeypatch.setattr("read.get_handoffs_dir", lambda: handoffs_dir)
        monkeypatch.setattr("read.get_session_state_dir", lambda: state_dir)

        from read import main

        exit_code = main()

        assert exit_code == 0
        assert recent_handoff.exists(), "Recent handoff should be kept"
        assert recent_archive.exists(), "Recent archive should be kept"
        assert recent_state.exists(), "Recent state file should be kept"
