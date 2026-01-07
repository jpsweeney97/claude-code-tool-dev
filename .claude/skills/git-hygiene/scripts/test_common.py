#!/usr/bin/env python3
"""Tests for common.py utilities."""

import shutil
import subprocess
import tempfile
import os
from pathlib import Path

# Import from same directory
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common import Result, run_git, get_git_dir, get_default_branch, get_worktree_branches, is_branch_merged


def test_result_to_dict():
    """Result serializes to dict with timestamp."""
    r = Result(success=True, message="ok", data={"count": 5})
    d = r.to_dict()
    assert d["success"] is True
    assert d["message"] == "ok"
    assert d["data"]["count"] == 5
    assert "timestamp" in d


def test_run_git_success():
    """run_git returns stdout on success."""
    code, stdout, stderr = run_git(["--version"])
    assert code == 0
    assert "git version" in stdout


def test_run_git_failure():
    """run_git handles bad commands."""
    code, stdout, stderr = run_git(["not-a-command-xyz"])
    assert code != 0


def test_get_worktree_branches_empty():
    """get_worktree_branches returns set."""
    result = get_worktree_branches()
    # Result can be set or None (on error), check for set when successful
    assert result is None or isinstance(result, set)


def test_get_worktree_branches_returns_none_on_error(monkeypatch):
    """get_worktree_branches returns None when git command fails."""
    def mock_run_git(args, timeout=60):
        if args[0] == "worktree":
            return 1, "", "error: unknown option"
        return 0, "", ""

    monkeypatch.setattr("common.run_git", mock_run_git)
    from common import get_worktree_branches
    result = get_worktree_branches()
    assert result is None


class TestInTempRepo:
    """Tests requiring a temp git repo."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True, check=True)

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_get_git_dir(self):
        """get_git_dir finds .git directory."""
        git_dir = get_git_dir()
        assert git_dir is not None
        assert git_dir.name == ".git"

    def test_get_default_branch(self):
        """get_default_branch returns main or master."""
        branch = get_default_branch()
        assert branch in ("main", "master")

    def test_is_branch_merged_self(self):
        """Branch is merged into itself."""
        branch = get_default_branch()
        merged, method = is_branch_merged(branch, branch)
        assert merged is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
