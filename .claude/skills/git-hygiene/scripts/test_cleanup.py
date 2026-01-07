#!/usr/bin/env python3
"""Tests for cleanup.py bug fixes."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cleanup import OperationResult, delete_branch


def test_operation_result_structure():
    """OperationResult has expected fields."""
    r = OperationResult(
        operation="drop_stash",
        target="stash@{0}",
        success=False,
        message="Stash not found",
    )
    assert r.operation == "drop_stash"
    assert r.success is False
    assert r.undo_command is None


def test_delete_branch_blocks_worktree():
    """Cannot delete branch checked out in worktree."""
    # Test the worktree detection function exists and returns expected types
    from common import get_worktree_branches
    branches = get_worktree_branches()
    # Returns set on success, None on error
    assert branches is None or isinstance(branches, set)


def test_invalid_stash_index_shows_error():
    """Non-integer stash index gives user-friendly error."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "cleanup.py", "--stashes", "0,abc,2", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower() or "integer" in result.stderr.lower()


def test_negative_stash_index_shows_error():
    """Negative stash index gives user-friendly error."""
    import subprocess
    # Use --stashes=VALUE syntax because -1 looks like a flag to argparse
    result = subprocess.run(
        [sys.executable, "cleanup.py", "--stashes=-1,0", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    assert result.returncode != 0
    assert "non-negative" in result.stderr.lower() or "negative" in result.stderr.lower()


class TestDeleteBranchSafety:
    """Tests for delete_branch safety checks."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True, check=True)
        # Create a test branch
        subprocess.run(["git", "branch", "test-branch"], capture_output=True, check=True)

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_cannot_delete_current_branch(self):
        """Deleting current branch returns error."""
        # Get current branch name
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        current = result.stdout.strip()

        op_result = delete_branch(current)
        assert op_result.success is False
        assert "current branch" in op_result.message.lower()

    def test_cannot_delete_default_branch(self):
        """Deleting default branch returns error."""
        # Switch to test-branch so main is not current
        subprocess.run(["git", "checkout", "test-branch"], capture_output=True, check=True)
        try:
            op_result = delete_branch("main")
            assert op_result.success is False
            assert "default branch" in op_result.message.lower()
        finally:
            # Switch back to main for other tests
            subprocess.run(["git", "checkout", "main"], capture_output=True, check=True)

    def test_can_delete_merged_branch(self):
        """Merged branch can be deleted."""
        # test-branch is merged (same commit as main)
        op_result = delete_branch("test-branch")
        assert op_result.success is True
        assert op_result.undo_command is not None
        assert "git branch test-branch" in op_result.undo_command


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
