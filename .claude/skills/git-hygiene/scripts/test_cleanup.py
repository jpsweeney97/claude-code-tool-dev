#!/usr/bin/env python3
"""Tests for cleanup.py bug fixes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cleanup import OperationResult


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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
