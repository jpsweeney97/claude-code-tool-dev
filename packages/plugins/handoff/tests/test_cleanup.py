"""Tests for cleanup.py — SessionStart hook script."""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.cleanup import (
    get_project_name,
    prune_old_handoffs,
)


class TestGetProjectName:
    """Tests for get_project_name."""

    def test_git_success(self) -> None:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/home/user/my-project\n"
        )
        with patch("scripts.cleanup.subprocess.run", return_value=mock_result):
            assert get_project_name() == "my-project"

    def test_git_not_installed_falls_back(self) -> None:
        with patch(
            "scripts.cleanup.subprocess.run", side_effect=FileNotFoundError
        ):
            assert get_project_name() == Path.cwd().name

    def test_git_timeout_falls_back(self) -> None:
        with patch(
            "scripts.cleanup.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 5),
        ):
            assert get_project_name() == Path.cwd().name

    def test_not_a_repo_falls_back(self) -> None:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="", stderr="not a git repository"
        )
        with patch("scripts.cleanup.subprocess.run", return_value=mock_result):
            assert get_project_name() == Path.cwd().name


class TestPruneOldHandoffs:
    """Tests for prune_old_handoffs — baseline behavior."""

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        assert prune_old_handoffs(tmp_path / "nope") == []

    def test_recent_files_not_deleted(self, tmp_path: Path) -> None:
        recent = tmp_path / "recent.md"
        recent.write_text("content")
        with patch("scripts.cleanup.subprocess.run") as mock_run:
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert result == []
        mock_run.assert_not_called()

    def test_non_md_files_ignored(self, tmp_path: Path) -> None:
        txt = tmp_path / "old.txt"
        txt.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(txt, (old_time, old_time))
        with patch("scripts.cleanup.subprocess.run") as mock_run:
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert result == []
        mock_run.assert_not_called()

    def test_stat_oserror_skipped(self, tmp_path: Path) -> None:
        """P2 test: stat failures on individual files don't crash the function (I7/R1)."""
        old = tmp_path / "old.md"
        old.write_text("content")
        target_str = str(old)

        orig_stat = Path.stat

        hit = False

        def selective_stat(self_path: Path, *args: object, **kwargs: object) -> os.stat_result:
            """Raise OSError only for the target file, not for glob internals."""
            nonlocal hit
            if str(self_path) == target_str:
                hit = True
                raise OSError("permission denied")
            return orig_stat(self_path, *args, **kwargs)

        with patch("scripts.cleanup.Path.stat", autospec=True, side_effect=selective_stat):
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert hit is True, "Patch must exercise the target file's stat() path"
        assert result == []
