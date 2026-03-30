"""Tests for auto_commit.py — narrow-scope git commit for handoff state changes."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.auto_commit import auto_commit, check_git_state, main


class TestCheckGitState:
    """Tests for check_git_state — git precondition checks."""

    def test_no_git_repo(self) -> None:
        mock = MagicMock()
        mock.returncode = 128
        mock.stdout = ""
        with patch("scripts.auto_commit.subprocess.run", return_value=mock):
            ok, reason = check_git_state()
        assert ok is False
        assert "No git repository" in reason

    def test_detached_head(self) -> None:
        git_dir_mock = MagicMock(returncode=0, stdout="/tmp/repo/.git\n")
        head_mock = MagicMock(returncode=1, stdout="")

        def side_effect(cmd, **kwargs):
            if "symbolic-ref" in cmd:
                return head_mock
            return git_dir_mock

        with (
            patch("scripts.auto_commit.subprocess.run", side_effect=side_effect),
            patch("scripts.auto_commit.Path.exists", return_value=False),
        ):
            ok, reason = check_git_state()
        assert ok is False
        assert "Detached HEAD" in reason

    def test_rebase_in_progress(self) -> None:
        git_dir_mock = MagicMock(returncode=0, stdout="/tmp/repo/.git\n")

        with (
            patch("scripts.auto_commit.subprocess.run", return_value=git_dir_mock),
            patch("scripts.auto_commit.Path.exists", side_effect=lambda: True),
        ):
            # Need to patch Path specifically for rebase-merge
            with patch.object(Path, "exists", return_value=True):
                ok, reason = check_git_state()
        assert ok is False
        assert "Rebase in progress" in reason

    def test_normal_state(self) -> None:
        git_dir_mock = MagicMock(returncode=0, stdout="/tmp/repo/.git\n")
        head_mock = MagicMock(returncode=0, stdout="refs/heads/main\n")

        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if "symbolic-ref" in cmd:
                return head_mock
            return git_dir_mock

        with (
            patch("scripts.auto_commit.subprocess.run", side_effect=side_effect),
            patch.object(Path, "exists", return_value=False),
        ):
            ok, reason = check_git_state()
        assert ok is True
        assert reason == ""

    def test_git_timeout(self) -> None:
        with patch(
            "scripts.auto_commit.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 5),
        ):
            ok, reason = check_git_state()
        assert ok is False
        assert "Git check failed" in reason

    def test_git_not_found(self) -> None:
        with patch(
            "scripts.auto_commit.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            ok, reason = check_git_state()
        assert ok is False
        assert "Git check failed" in reason


class TestAutoCommit:
    """Tests for auto_commit — stage + commit."""

    def test_skips_when_git_state_bad(self) -> None:
        with patch("scripts.auto_commit.check_git_state", return_value=(False, "Detached HEAD")):
            ok, reason = auto_commit(["file.md"], "test message")
        assert ok is False
        assert "Detached HEAD" in reason

    def test_stages_and_commits(self) -> None:
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
        with (
            patch("scripts.auto_commit.check_git_state", return_value=(True, "")),
            patch("scripts.auto_commit.subprocess.run", mock_run),
        ):
            ok, reason = auto_commit(["docs/handoffs/test.md"], "docs(handoff): save test")
        assert ok is True
        # Verify git add was called
        add_calls = [c for c in mock_run.call_args_list if "add" in c[0][0]]
        assert len(add_calls) == 1
        # Verify git commit --only was called
        commit_calls = [c for c in mock_run.call_args_list if "commit" in c[0][0]]
        assert len(commit_calls) == 1
        assert "--only" in commit_calls[0][0][0]

    def test_staged_mode_skips_add(self) -> None:
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
        with (
            patch("scripts.auto_commit.check_git_state", return_value=(True, "")),
            patch("scripts.auto_commit.subprocess.run", mock_run),
        ):
            ok, reason = auto_commit(["docs/handoffs/test.md"], "msg", staged=True)
        assert ok is True
        add_calls = [c for c in mock_run.call_args_list if "add" in c[0][0]]
        assert len(add_calls) == 0

    def test_commit_failure(self) -> None:
        mock_run = MagicMock(return_value=MagicMock(returncode=1, stderr="pre-commit hook failed"))
        with (
            patch("scripts.auto_commit.check_git_state", return_value=(True, "")),
            patch("scripts.auto_commit.subprocess.run", mock_run),
        ):
            ok, reason = auto_commit(["file.md"], "msg")
        assert ok is False
        assert "Commit failed" in reason


class TestMain:
    """Tests for main — CLI entry point."""

    def test_success_returns_zero(self) -> None:
        with patch("scripts.auto_commit.auto_commit", return_value=(True, "")):
            assert main(["-m", "test", "file.md"]) == 0

    def test_failure_returns_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("scripts.auto_commit.auto_commit", return_value=(False, "No git repository")):
            assert main(["-m", "test", "file.md"]) == 1
        assert "No git repository" in capsys.readouterr().err

    def test_staged_flag_passed(self) -> None:
        with patch("scripts.auto_commit.auto_commit", return_value=(True, "")) as mock:
            main(["-m", "test", "--staged", "file.md"])
        mock.assert_called_once_with(["file.md"], "test", staged=True)
