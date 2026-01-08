#!/usr/bin/env python3
"""Tests for read.py - handoff skill read script."""

import subprocess
from pathlib import Path
from unittest.mock import patch


class TestGetProjectName:
    """Test project name detection from git or directory."""

    def test_git_repo_uses_repo_name(self, tmp_path: Path, monkeypatch):
        """In a git repo, project name is the repo directory name."""
        # Create a git repo
        repo = tmp_path / "my-cool-project"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)

        monkeypatch.chdir(repo)

        from read import get_project_name

        assert get_project_name() == "my-cool-project"

    def test_non_git_uses_cwd_name(self, tmp_path: Path, monkeypatch):
        """Without git, project name is the current directory name."""
        non_git = tmp_path / "some-directory"
        non_git.mkdir()

        monkeypatch.chdir(non_git)

        # Need fresh import after changing directory
        import importlib

        import read

        importlib.reload(read)

        # Mock git failing to simulate non-git directory
        with patch("read.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            assert read.get_project_name() == "some-directory"

    def test_git_timeout_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git times out, fall back to current directory name."""
        non_git = tmp_path / "timeout-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import importlib

        import read

        importlib.reload(read)

        with patch("read.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            assert read.get_project_name() == "timeout-test"

    def test_git_not_found_falls_back_to_cwd(self, tmp_path: Path, monkeypatch):
        """If git is not installed, fall back to current directory name."""
        non_git = tmp_path / "no-git-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import importlib

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

        from read import find_latest_handoff

        assert find_latest_handoff(handoffs_dir) == new

    def test_returns_none_when_no_handoffs(self, tmp_path: Path):
        """Returns None when directory is empty."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        from read import find_latest_handoff

        assert find_latest_handoff(handoffs_dir) is None

    def test_returns_none_when_dir_missing(self, tmp_path: Path):
        """Returns None when directory doesn't exist."""
        from read import find_latest_handoff

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


class TestCheckRecency:
    """Test 24-hour recency threshold."""

    def test_recent_under_24h(self, tmp_path: Path):
        """File under 24h old is 'recent'."""
        handoff = tmp_path / "handoff.md"
        handoff.write_text("content")
        # File is just created, so definitely under 24h

        from read import is_recent

        assert is_recent(handoff, hours=24) is True

    def test_old_over_24h(self, tmp_path: Path):
        """File over 24h old is not 'recent'."""
        import os
        import time

        handoff = tmp_path / "handoff.md"
        handoff.write_text("content")

        # Set mtime to 25 hours ago
        old_time = time.time() - (25 * 60 * 60)
        os.utime(handoff, (old_time, old_time))

        from read import is_recent

        assert is_recent(handoff, hours=24) is False


class TestExtractTitle:
    """Test extracting title from handoff frontmatter and content."""

    def test_extracts_from_frontmatter(self):
        """Extracts title from YAML frontmatter."""
        content = """---
date: 2026-01-08
title: Auth middleware implementation
---

# Handoff: Auth middleware implementation
"""
        from read import extract_title

        assert extract_title(content) == "Auth middleware implementation"

    def test_falls_back_to_heading(self):
        """Falls back to H1 heading if no frontmatter title."""
        content = """---
date: 2026-01-08
---

# Handoff: JWT token refresh
"""
        from read import extract_title

        assert extract_title(content) == "JWT token refresh"

    def test_returns_untitled_when_missing(self):
        """Returns 'Untitled' when no title found."""
        content = "Just some content"
        from read import extract_title

        assert extract_title(content) == "Untitled"


class TestFormatOutput:
    """Test the three output modes based on recency."""

    def test_recent_auto_injects_content(self, tmp_path: Path):
        """<24h: outputs [Resuming: title] with content."""
        handoff = tmp_path / "handoff.md"
        handoff.write_text("""---
title: Auth middleware
---

# Handoff: Auth middleware

## Goal
Implement JWT authentication.

## Next Steps
1. Add refresh endpoint
""")

        from read import format_output

        output = format_output(handoff, is_recent=True)

        assert output.startswith("[Resuming: Auth middleware]")
        assert "Implement JWT authentication" in output

    def test_old_prompts_for_resume(self, tmp_path: Path):
        """>24h: outputs prompt asking whether to resume."""
        handoff = tmp_path / "2026-01-05_10-00_old-work.md"
        handoff.write_text("""---
title: Database migration
date: 2026-01-05
---

# Handoff: Database migration
""")

        from read import format_output

        output = format_output(handoff, is_recent=False)

        assert "[Found handoff from" in output
        assert "Database migration" in output
        assert "Resume from this?]" in output


class TestMain:
    """Test CLI entry point."""

    def test_outputs_recent_handoff(self, tmp_path: Path, monkeypatch):
        """Outputs auto-injected content for recent handoff."""
        import sys
        from io import StringIO

        # Create handoffs directory structure
        handoffs_dir = tmp_path / ".claude" / "handoffs" / "test-project"
        handoffs_dir.mkdir(parents=True)

        handoff = handoffs_dir / "2026-01-08_14-30_test.md"
        handoff.write_text("""---
title: Test handoff
---

# Handoff: Test handoff

## Goal
Test goal content.
""")

        # Mock get_handoffs_dir to return our test directory
        monkeypatch.setattr("read.get_handoffs_dir", lambda: handoffs_dir)

        # Capture stdout
        captured = StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        from read import main

        exit_code = main()

        output = captured.getvalue()
        assert "[Resuming: Test handoff]" in output
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
        assert exit_code == 0  # No handoff is a valid state, not an error


class TestPruneOldHandoffsRobustness:
    """Test race condition and permission handling in prune_old_handoffs."""

    def test_handles_file_deleted_between_stat_and_unlink(self, tmp_path: Path):
        """Race condition: file deleted after stat, before unlink."""
        import os
        import time

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        # Create old file
        old = handoffs_dir / "2025-12-01_10-00_race.md"
        old.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))

        from read import prune_old_handoffs

        # File should be pruned without error even if missing_ok handles deletion
        prune_old_handoffs(handoffs_dir, max_age_days=30)

        # Should complete without raising, file should be gone
        assert not old.exists()

    def test_handles_permission_error_on_unlink(self, tmp_path: Path, monkeypatch):
        """Permission error logs warning, continues."""
        import os
        import sys
        import time
        from io import StringIO

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

        # Capture stderr for warning
        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        from read import prune_old_handoffs

        # Should complete without raising
        prune_old_handoffs(handoffs_dir, max_age_days=30)

        # Second file should be deleted, first should still exist
        assert old1.exists()  # Permission error prevented deletion
        assert not old2.exists()  # Successfully deleted
        assert "Warning" in stderr_capture.getvalue()
        assert "first.md" in stderr_capture.getvalue()


class TestFindLatestHandoffRobustness:
    """Test permission error handling in find_latest_handoff."""

    def test_handles_stat_permission_error(self, tmp_path: Path, monkeypatch):
        """Permission error on stat skips file, doesn't crash."""
        import time

        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir(parents=True)

        # Create two files
        unreadable = handoffs_dir / "2026-01-01_10-00_unreadable.md"
        unreadable.write_text("unreadable content")

        time.sleep(0.01)
        readable = handoffs_dir / "2026-01-02_10-00_readable.md"
        readable.write_text("readable content")

        # Mock stat to raise on first file (must accept follow_symlinks kwarg)
        original_stat = Path.stat

        def mock_stat(self, *, follow_symlinks=True):
            if self.name == "2026-01-01_10-00_unreadable.md":
                raise PermissionError("Access denied")
            return original_stat(self, follow_symlinks=follow_symlinks)

        monkeypatch.setattr(Path, "stat", mock_stat)

        from read import find_latest_handoff

        # Should return the readable file, not crash
        result = find_latest_handoff(handoffs_dir)
        assert result == readable


class TestFormatOutputRobustness:
    """Test file read error handling in format_output."""

    def test_handles_unreadable_file(self, tmp_path: Path, monkeypatch):
        """Returns error message, doesn't crash."""
        handoff = tmp_path / "unreadable.md"
        handoff.write_text("content")

        # Mock read_text to raise
        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if self.name == "unreadable.md":
                raise PermissionError("Access denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        from read import format_output

        result = format_output(handoff, is_recent=True)
        assert "[Error reading handoff:" in result
        assert "Access denied" in result


class TestExtractDateRobustness:
    """Test mtime fallback when filename is unparseable."""

    def test_fallback_to_mtime_when_filename_unparseable(self, tmp_path: Path):
        """Uses mtime when no date in filename."""
        from datetime import datetime

        handoff = tmp_path / "random-name-no-date.md"
        handoff.write_text("content")

        from read import extract_date

        result = extract_date(handoff)

        # Should return today's date (file was just created)
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result == expected


class TestGetProjectNameRobustness:
    """Test timeout warning in get_project_name."""

    def test_git_timeout_logs_warning(self, tmp_path: Path, monkeypatch):
        """Logs to stderr on timeout."""
        import sys
        from io import StringIO

        non_git = tmp_path / "timeout-warning-test"
        non_git.mkdir()
        monkeypatch.chdir(non_git)

        import importlib

        import read

        importlib.reload(read)

        # Capture stderr
        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        with patch("read.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
            result = read.get_project_name()

        assert result == "timeout-warning-test"
        assert "Warning" in stderr_capture.getvalue()
        assert "timed out" in stderr_capture.getvalue()
