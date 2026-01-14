# Git-Hygiene PR Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical safety issues and add missing test coverage for the git-hygiene skill PR before merge.

**Architecture:** Address silent failure in `get_worktree_branches()` by returning `Optional[set]`, add input validation for CLI args, and write behavioral tests for safety-critical code paths in preflight.py and cleanup.py.

**Tech Stack:** Python 3.12 stdlib only (skill scripts), pytest for testing

---

## Task 1: Fix get_worktree_branches() Silent Failure

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/common.py:62-71`
- Modify: `.claude/skills/git-hygiene/scripts/cleanup.py:88-96`
- Test: `.claude/skills/git-hygiene/scripts/test_common.py`

**Step 1: Write the failing test**

Add to `test_common.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_common.py::test_get_worktree_branches_returns_none_on_error -v`

Expected: FAIL - currently returns `set()` not `None`

**Step 3: Update get_worktree_branches signature and implementation**

In `common.py`, change:

```python
def get_worktree_branches() -> Optional[set[str]]:
    """Get branches checked out in worktrees. Returns None on error."""
    code, stdout, _ = run_git(["worktree", "list", "--porcelain"])
    if code != 0:
        return None
    branches = set()
    for line in stdout.split("\n"):
        if line.startswith("branch refs/heads/"):
            branches.add(line.replace("branch refs/heads/", ""))
    return branches
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_common.py::test_get_worktree_branches_returns_none_on_error -v`

Expected: PASS

**Step 5: Update delete_branch to handle None worktree result**

In `cleanup.py:88-96`, change:

```python
    # Check if branch is in a worktree
    worktree_branches = get_worktree_branches()
    if worktree_branches is None:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message="Could not verify worktree status - refusing to delete for safety",
        )
    if branch in worktree_branches:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message=f"Branch '{branch}' is checked out in a worktree",
        )
```

**Step 6: Run all tests to verify no regressions**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest -v`

Expected: All tests PASS

**Step 7: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/common.py .claude/skills/git-hygiene/scripts/cleanup.py .claude/skills/git-hygiene/scripts/test_common.py
git commit -m "fix(git-hygiene): make get_worktree_branches fail-safe

Return None on error instead of empty set. Callers must now handle
the error case explicitly to prevent safety bypasses when worktree
command fails."
```

---

## Task 2: Add Input Validation for Stash Indices

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/cleanup.py:438-441`

**Step 1: Write the failing test**

Add to `test_cleanup.py`:

```python
import subprocess
import sys


def test_invalid_stash_index_shows_error():
    """Non-integer stash index gives user-friendly error."""
    result = subprocess.run(
        [sys.executable, "cleanup.py", "--stashes", "0,abc,2", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr.lower() or "integer" in result.stderr.lower()


def test_negative_stash_index_shows_error():
    """Negative stash index gives user-friendly error."""
    result = subprocess.run(
        [sys.executable, "cleanup.py", "--stashes", "-1,0", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "non-negative" in result.stderr.lower() or "negative" in result.stderr.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_cleanup.py::test_invalid_stash_index_shows_error test_cleanup.py::test_negative_stash_index_shows_error -v`

Expected: FAIL - currently crashes with unhandled ValueError or accepts negative indices

**Step 3: Add input validation in main()**

In `cleanup.py`, replace lines 438-440:

```python
    # Parse inputs
    branches = args.branches.split(",") if args.branches else None

    stashes = None
    if args.stashes:
        try:
            stashes = [int(i.strip()) for i in args.stashes.split(",")]
        except ValueError:
            parser.error(f"Invalid stash index in '{args.stashes}': expected comma-separated integers")
        if any(i < 0 for i in stashes):
            parser.error(f"Invalid stash index in '{args.stashes}': indices must be non-negative")
```

**Step 4: Run tests to verify they pass**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_cleanup.py::test_invalid_stash_index_shows_error test_cleanup.py::test_negative_stash_index_shows_error -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/cleanup.py .claude/skills/git-hygiene/scripts/test_cleanup.py
git commit -m "fix(git-hygiene): validate stash indices in CLI

- Catch ValueError for non-integer input
- Reject negative indices
- Show user-friendly error messages via argparse"
```

---

## Task 3: Add Preflight Safety Tests

**Files:**
- Create: `.claude/skills/git-hygiene/scripts/test_preflight.py`

**Step 1: Create test file with imports**

Create `test_preflight.py`:

```python
#!/usr/bin/env python3
"""Tests for preflight.py safety checks."""

import os
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from preflight import check_active_operations, check_shallow, run_preflight


class TestCheckActiveOperations:
    """Tests for detecting active git operations."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True, check=True)
        cls.git_dir = Path(cls.temp_dir) / ".git"

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_detects_merge_in_progress(self):
        """MERGE_HEAD file indicates merge in progress."""
        merge_head = self.git_dir / "MERGE_HEAD"
        merge_head.write_text("abc123\n")
        try:
            ops = check_active_operations(self.git_dir)
            assert "merge" in ops
        finally:
            merge_head.unlink()

    def test_detects_rebase_merge(self):
        """rebase-merge directory indicates rebase in progress."""
        rebase_dir = self.git_dir / "rebase-merge"
        rebase_dir.mkdir()
        try:
            ops = check_active_operations(self.git_dir)
            assert "rebase" in ops
        finally:
            rebase_dir.rmdir()

    def test_detects_cherry_pick(self):
        """CHERRY_PICK_HEAD file indicates cherry-pick in progress."""
        cherry_head = self.git_dir / "CHERRY_PICK_HEAD"
        cherry_head.write_text("abc123\n")
        try:
            ops = check_active_operations(self.git_dir)
            assert "cherry-pick" in ops
        finally:
            cherry_head.unlink()

    def test_clean_repo_has_no_operations(self):
        """Clean repo returns empty list."""
        ops = check_active_operations(self.git_dir)
        assert ops == []


class TestRunPreflight:
    """Integration tests for run_preflight."""

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

    def test_clean_repo_is_safe(self):
        """Clean repo passes preflight."""
        result = run_preflight()
        assert result.safe is True
        assert result.active_operations == []

    def test_merge_blocks_preflight(self):
        """Active merge blocks preflight."""
        git_dir = Path(self.temp_dir) / ".git"
        merge_head = git_dir / "MERGE_HEAD"
        merge_head.write_text("abc123\n")
        try:
            result = run_preflight()
            assert result.safe is False
            assert "merge" in result.active_operations
        finally:
            merge_head.unlink()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
```

**Step 2: Run tests to verify they pass**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_preflight.py -v`

Expected: All PASS (tests existing functionality)

**Step 3: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/test_preflight.py
git commit -m "test(git-hygiene): add preflight safety tests

Test detection of merge, rebase, and cherry-pick operations.
Verify clean repos pass preflight checks."
```

---

## Task 4: Add delete_branch Safety Tests

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/test_cleanup.py`

**Step 1: Add safety check tests**

Add to `test_cleanup.py`:

```python
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cleanup import delete_branch


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
        op_result = delete_branch("main")
        assert op_result.success is False
        assert "default branch" in op_result.message.lower()

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
```

**Step 2: Run tests to verify they pass**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest test_cleanup.py::TestDeleteBranchSafety -v`

Expected: All PASS (tests existing functionality)

**Step 3: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/test_cleanup.py
git commit -m "test(git-hygiene): add delete_branch safety tests

Test that current branch and default branch cannot be deleted.
Verify merged branches can be deleted with undo command."
```

---

## Task 5: Run Full Test Suite and Final Commit

**Step 1: Run full test suite**

Run: `cd .claude/skills/git-hygiene/scripts && python -m pytest -v`

Expected: All tests PASS (should be ~18-20 tests now)

**Step 2: Stage all changes and review**

Run: `git status && git diff --staged`

**Step 3: Create final summary commit if needed**

If all individual commits are clean, skip this step. Otherwise:

```bash
git add -A
git commit -m "fix(git-hygiene): address PR review findings

- Make get_worktree_branches fail-safe (return None on error)
- Add CLI input validation for stash indices
- Add preflight safety tests
- Add delete_branch safety tests

Closes review items from PR #1"
```

---

## Summary

| Task | Priority | Risk Addressed |
|------|----------|----------------|
| 1. Fix get_worktree_branches | Critical | Safety bypass via silent failure |
| 2. Input validation | Important | Unhandled exceptions |
| 3. Preflight tests | Critical | Safety-critical code untested |
| 4. delete_branch tests | Critical | Safety-critical code untested |
| 5. Final verification | Required | Ensure no regressions |

**Total estimated tasks:** 5 main tasks, ~25 individual steps
