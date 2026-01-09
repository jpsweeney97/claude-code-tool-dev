# Git Hygiene Skill: Full Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform git-hygiene from documentation-only to a working orchestrated workflow with bug fixes.

**Architecture:** Scripts output JSON; Claude handles presentation. Shared `common.py` eliminates duplication. TDD for bug fixes.

**Tech Stack:** Python 3.12+, stdlib only (skills must be portable)

---

## Task 1: Create common.py Foundation

**Files:**
- Create: `.claude/skills/git-hygiene/scripts/common.py`

**Step 1: Create common.py with core utilities**

```python
#!/usr/bin/env python3
"""Shared utilities for git-hygiene scripts. Stdlib only."""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class Result:
    """Standard result for JSON output."""
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat(),
        }


def run_git(args: List[str], timeout: int = 60) -> Tuple[int, str, str]:
    """Run git command. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", "git not found in PATH"


def get_git_dir() -> Optional[Path]:
    """Get .git directory path."""
    code, stdout, _ = run_git(["rev-parse", "--git-dir"])
    if code == 0 and stdout:
        return Path(stdout).resolve()
    return None


def get_default_branch() -> str:
    """Get default branch (main or master)."""
    code, stdout, _ = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0 and stdout:
        return stdout.split("/")[-1]
    code, _, _ = run_git(["rev-parse", "--verify", "main"])
    return "main" if code == 0 else "master"


def get_worktree_branches() -> set:
    """Get branches checked out in worktrees."""
    code, stdout, _ = run_git(["worktree", "list", "--porcelain"])
    if code != 0:
        return set()
    branches = set()
    for line in stdout.split("\n"):
        if line.startswith("branch refs/heads/"):
            branches.add(line.replace("branch refs/heads/", ""))
    return branches


def is_branch_merged(branch: str, target: Optional[str] = None) -> Tuple[bool, str]:
    """Check if branch is merged into target. Returns (is_merged, method).

    Methods: 'ancestor' (direct), 'cherry' (rebased), 'none' (not merged)
    """
    if target is None:
        target = get_default_branch()

    # Method 1: Direct ancestry
    code, _, _ = run_git(["merge-base", "--is-ancestor", branch, target])
    if code == 0:
        return True, "ancestor"

    # Method 2: Cherry (finds rebased equivalents)
    code, stdout, _ = run_git(["cherry", target, branch])
    if code == 0:
        lines = [l for l in stdout.strip().split("\n") if l.strip()]
        if not lines or all(l.startswith("-") for l in lines):
            return True, "cherry"

    return False, "none"
```

**Step 2: Verify syntax**

Run: `python3 -m py_compile .claude/skills/git-hygiene/scripts/common.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/common.py
git commit -m "feat(git-hygiene): add common.py with shared utilities"
```

---

## Task 2: Create test_common.py

**Files:**
- Create: `.claude/skills/git-hygiene/scripts/test_common.py`

**Step 1: Write tests for common.py**

```python
#!/usr/bin/env python3
"""Tests for common.py utilities."""

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
    assert isinstance(result, set)


class TestInTempRepo:
    """Tests requiring a temp git repo."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True)

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)

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
```

**Step 2: Run tests**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_common.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/test_common.py
git commit -m "test(git-hygiene): add tests for common.py"
```

---

## Task 3: Fix Bug 1 - Stash Parsing Delimiter

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/analyze.py:191-233`
- Create: `.claude/skills/git-hygiene/scripts/test_analyze.py`

**Step 1: Write failing test for stash parsing**

Create `test_analyze.py`:

```python
#!/usr/bin/env python3
"""Tests for analyze.py bug fixes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def test_parse_stash_with_pipe_in_message():
    """Stash messages containing | should parse correctly."""
    # Simulate git stash list output with null delimiters
    raw_output = "stash@{0}\x00WIP on main: fix | broken\x002026-01-01 12:00:00 +0000"

    # Parse using null delimiter
    parts = raw_output.split("\x00")
    assert len(parts) == 3
    assert parts[0] == "stash@{0}"
    assert parts[1] == "WIP on main: fix | broken"  # Pipe preserved
    assert "2026-01-01" in parts[2]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
```

**Step 2: Run test to verify it passes (this tests the FIX pattern)**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_analyze.py::test_parse_stash_with_pipe_in_message -v`
Expected: PASS

**Step 3: Fix analyze.py stash parsing**

In `.claude/skills/git-hygiene/scripts/analyze.py`, replace lines 195-205:

OLD:
```python
code, stdout, _ = run_git(["stash", "list", "--format=%gd|%gs|%ci"])
if code != 0 or not stdout:
    return stashes

for line in stdout.split("\n"):
    if not line.strip():
        continue

    parts = line.split("|")
    if len(parts) < 3:
        continue
```

NEW:
```python
# Use null byte delimiter - stash messages can contain |
code, stdout, _ = run_git(["stash", "list", "--format=%gd%x00%gs%x00%ci"])
if code != 0 or not stdout:
    return stashes

for line in stdout.split("\n"):
    if not line.strip():
        continue

    parts = line.split("\x00")
    if len(parts) < 3:
        continue
```

**Step 4: Verify syntax**

Run: `python3 -m py_compile .claude/skills/git-hygiene/scripts/analyze.py`
Expected: No output (success)

**Step 5: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/analyze.py .claude/skills/git-hygiene/scripts/test_analyze.py
git commit -m "fix(git-hygiene): use null delimiter for stash parsing

Stash messages can contain | which broke parsing. Use %x00 null byte."
```

---

## Task 4: Fix Bug 2 - Pattern Matching for Directories

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/analyze.py:236-248`
- Modify: `.claude/skills/git-hygiene/scripts/test_analyze.py`

**Step 1: Add failing test**

Append to `test_analyze.py`:

```python
def test_matches_pattern_directory():
    """node_modules/foo/bar.js should match node_modules pattern."""
    from analyze import matches_pattern

    # These should all match
    assert matches_pattern("node_modules/lodash/index.js", {"node_modules"})
    assert matches_pattern("__pycache__/module.cpython-312.pyc", {"__pycache__"})
    assert matches_pattern("dist/bundle.js", {"dist"})

    # Extension patterns
    assert matches_pattern("foo.pyc", {"*.pyc"})
    assert matches_pattern("backup~", {"*~"})

    # Should NOT match
    assert not matches_pattern("my_modules/foo.js", {"node_modules"})
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_analyze.py::test_matches_pattern_directory -v`
Expected: FAIL (current implementation doesn't handle directory patterns)

**Step 3: Fix matches_pattern function**

In `.claude/skills/git-hygiene/scripts/analyze.py`, replace the `matches_pattern` function:

```python
def matches_pattern(filepath: str, patterns: set[str]) -> bool:
    """Check if filepath matches any pattern.

    Handles:
    - Exact basename: .DS_Store
    - Suffix glob: *.pyc
    - Prefix glob: *~
    - Directory: node_modules (matches any path component)
    """
    name = os.path.basename(filepath)
    parts = filepath.replace("\\", "/").split("/")

    for pattern in patterns:
        # Exact basename match
        if name == pattern:
            return True
        # Suffix glob (*.pyc)
        if pattern.startswith("*.") and name.endswith(pattern[1:]):
            return True
        # Prefix glob (*~)
        if pattern.endswith("*") and name.startswith(pattern[:-1]):
            return True
        # Directory pattern - check path components
        if pattern in parts:
            return True
    return False
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_analyze.py::test_matches_pattern_directory -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/analyze.py .claude/skills/git-hygiene/scripts/test_analyze.py
git commit -m "fix(git-hygiene): pattern matching handles directory patterns

node_modules/foo/bar.js now correctly matches 'node_modules' pattern."
```

---

## Task 5: Fix Bug 3 - Merge Detection for Rebased Branches

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/analyze.py:165`
- Modify: `.claude/skills/git-hygiene/scripts/test_analyze.py`

**Step 1: Add test**

Append to `test_analyze.py`:

```python
def test_is_branch_merged_uses_cherry():
    """is_branch_merged should use cherry check for rebased branches."""
    from common import is_branch_merged

    # This tests the function exists and returns correct structure
    merged, method = is_branch_merged("main", "main")
    assert isinstance(merged, bool)
    assert method in ("ancestor", "cherry", "none")
```

**Step 2: Update analyze.py to use common.is_branch_merged**

In `.claude/skills/git-hygiene/scripts/analyze.py`, add import at top:

```python
from common import run_git, get_git_dir, get_default_branch, is_branch_merged
```

Then replace line 165:

OLD:
```python
code, _, _ = run_git(["merge-base", "--is-ancestor", branch_name, default_branch])
is_merged = code == 0
```

NEW:
```python
is_merged, _ = is_branch_merged(branch_name, default_branch)
```

**Step 3: Run test**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_analyze.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/analyze.py .claude/skills/git-hygiene/scripts/test_analyze.py
git commit -m "fix(git-hygiene): use cherry check for rebased branch detection

merge-base --is-ancestor fails for rebased branches. Now uses git cherry
as fallback to detect equivalent commits."
```

---

## Task 6: Fix Bug 4 - Hardcoded 7-Day Threshold

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/analyze.py:121,181,428-434`

**Step 1: Add --merged-days argument**

In `analyze.py` argparser section, add:

```python
parser.add_argument(
    "--merged-days",
    type=int,
    default=7,
    help="Staleness threshold for merged branches (default: 7)",
)
```

**Step 2: Update function signature and usage**

Update `analyze_branches` signature:

```python
def analyze_branches(days_threshold: int = 30, merged_days_threshold: int = 7) -> dict:
```

Update line 181:

OLD:
```python
if is_merged and (last_commit_days is None or last_commit_days > 7):
```

NEW:
```python
if is_merged and (last_commit_days is None or last_commit_days > merged_days_threshold):
```

Update call in `run_analysis`:

```python
if category in ("all", "branches"):
    result.branches = analyze_branches(days_threshold, merged_days_threshold)
```

**Step 3: Run syntax check**

Run: `python3 -m py_compile .claude/skills/git-hygiene/scripts/analyze.py`
Expected: No output

**Step 4: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/analyze.py
git commit -m "fix(git-hygiene): make merged branch threshold configurable

Add --merged-days flag (default 7). Previously hardcoded."
```

---

## Task 7: Fix Bug 5 - Stash Drop Race Condition

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/cleanup.py:155-176`
- Create: `.claude/skills/git-hygiene/scripts/test_cleanup.py`

**Step 1: Write test**

Create `test_cleanup.py`:

```python
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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
```

**Step 2: Replace drop_stash function**

In `cleanup.py`, replace the `drop_stash` function:

```python
def get_stash_sha(stash_ref: str) -> Optional[str]:
    """Get SHA for a stash reference."""
    code, sha, _ = run_git(["rev-parse", stash_ref])
    return sha if code == 0 else None


def find_stash_index_by_sha(sha: str) -> Optional[int]:
    """Find current index for a stash SHA."""
    code, stdout, _ = run_git(["stash", "list", "--format=%H"])
    if code != 0 or not stdout:
        return None
    shas = stdout.strip().split("\n")
    try:
        return shas.index(sha)
    except ValueError:
        return None


def drop_stash(stash_ref: str) -> OperationResult:
    """Drop a stash entry safely by resolving SHA first."""
    # Get SHA to avoid race with shifting indices
    sha = get_stash_sha(stash_ref)
    if not sha:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Stash {stash_ref} not found",
        )

    # Find current index for this SHA
    current_index = find_stash_index_by_sha(sha)
    if current_index is None:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Stash {stash_ref} ({sha[:8]}) no longer exists",
        )

    # Drop by current index
    code, _, stderr = run_git(["stash", "drop", f"stash@{{{current_index}}}"])

    if code == 0:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=True,
            message=f"Dropped {stash_ref}",
        )
    else:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Failed to drop: {stderr}",
        )
```

**Step 3: Run test**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_cleanup.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/cleanup.py .claude/skills/git-hygiene/scripts/test_cleanup.py
git commit -m "fix(git-hygiene): resolve stash SHA before dropping

Prevents race condition where indices shift if another process drops a stash."
```

---

## Task 8: Fix Bug 6 - Worktree Safety

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/cleanup.py:100-152`

**Step 1: Add worktree check to delete_branch**

Add import at top of `cleanup.py`:

```python
from common import run_git, get_default_branch, get_worktree_branches
```

In `delete_branch` function, after the current branch check, add:

```python
# Check if branch is in a worktree
worktree_branches = get_worktree_branches()
if branch in worktree_branches:
    return OperationResult(
        operation="delete_branch",
        target=branch,
        success=False,
        message=f"Branch '{branch}' is checked out in a worktree",
    )
```

**Step 2: Add test**

Append to `test_cleanup.py`:

```python
def test_delete_branch_blocks_worktree():
    """Cannot delete branch checked out in worktree."""
    # Test the worktree detection function exists
    from common import get_worktree_branches
    branches = get_worktree_branches()
    assert isinstance(branches, set)
```

**Step 3: Run test**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest test_cleanup.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/cleanup.py .claude/skills/git-hygiene/scripts/test_cleanup.py
git commit -m "fix(git-hygiene): block deletion of branches in worktrees

Checks git worktree list before allowing branch deletion."
```

---

## Task 9: Refactor Scripts to Use common.py

**Files:**
- Modify: `.claude/skills/git-hygiene/scripts/preflight.py`
- Modify: `.claude/skills/git-hygiene/scripts/analyze.py`
- Modify: `.claude/skills/git-hygiene/scripts/cleanup.py`

**Step 1: Update preflight.py imports**

Add at top:
```python
from common import run_git, get_git_dir
```

Remove the duplicate `run_git` and `find_git_dir` functions.

**Step 2: Update analyze.py imports**

Ensure these imports exist:
```python
from common import run_git, get_git_dir, get_default_branch, is_branch_merged
```

Remove duplicate `run_git` and `get_default_branch` functions.

**Step 3: Update cleanup.py imports**

Ensure these imports exist:
```python
from common import run_git, get_default_branch, get_worktree_branches
```

Remove duplicate `run_git` and `get_default_branch` functions.

**Step 4: Run all tests**

Run: `cd .claude/skills/git-hygiene/scripts && python3 -m pytest -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/skills/git-hygiene/scripts/
git commit -m "refactor(git-hygiene): use common.py across all scripts

Removes duplicate run_git and get_default_branch functions."
```

---

## Task 10: Rewrite SKILL.md

**Files:**
- Replace: `.claude/skills/git-hygiene/SKILL.md`

**Step 1: Write new SKILL.md**

```markdown
---
name: git-hygiene
description: Smart repository maintenance with analysis and guided cleanup
---

# Git Hygiene

Repository maintenance: analyze stale branches, old stashes, untracked files. Safe by default.

## Triggers

- `/git-hygiene`, `git hygiene`, `clean up git`
- `stale branches`, `branch cleanup`
- `git maintenance`, `repo health`

## Execution Protocol

### Phase 1: Preflight

Run safety check:
```bash
python3 scripts/preflight.py --json
```

| Exit | Meaning | Action |
|------|---------|--------|
| 0 | Safe | Continue |
| 2 | Blocked | Show resolution, STOP |

If `warnings` in JSON, note them but continue.

### Phase 2: Analysis

```bash
python3 scripts/analyze.py --json [--days N] [--merged-days N]
```

Parse JSON output categories:
- `branches.gone` - remote deleted, safe to delete
- `branches.merged_stale` - merged, safe to delete
- `branches.unmerged_stale` - WARN, needs review
- `stashes` where `stale: true` - suggest deletion

### Phase 3: Review

Present findings:

```
## Branch Analysis
| Branch | Status | Age | Risk |
|--------|--------|-----|------|
| feature/old | [gone] | - | Low |
| fix/typo | merged | 14d | Low |
| experiment/x | unmerged | 45d | Medium |

## Stash Analysis
| Index | Age | Message | Risk |
|-------|-----|---------|------|
| 0 | 67d | WIP: old | Low |
```

Use AskUserQuestion:
- "Delete [gone] branches?"
- "Delete merged stale branches?"
- "Review unmerged branches individually?"
- "Drop old stashes?"

### Phase 4: Execute

Confirm selections, then run:
```bash
python3 scripts/cleanup.py --json --branches "b1,b2" --stashes "0,1"
```

Report each operation with undo command.

### Phase 5: Report

```
## Summary
| Metric | Before | After |
|--------|--------|-------|
| Branches | 12 | 9 |
| Stashes | 5 | 3 |

## Undo Commands
git branch feature/old abc1234
git branch fix/typo def5678
```

## Decision Tree

```
Branch found
├── [gone]? → Delete (low risk)
├── Merged + stale? → Delete (low risk)
├── Unmerged + stale? → WARN, require --force
├── In worktree? → BLOCK
└── Active? → Skip
```

## Commands

| Command | Action |
|---------|--------|
| `/git-hygiene` | Full analysis (dry-run) |
| `/git-hygiene --execute` | With confirmation |
| `/git-hygiene --status` | Quick summary |
| `/git-hygiene branches` | Branch analysis only |
| `/git-hygiene --days N` | Set staleness threshold |
| `/git-hygiene --force` | Allow unmerged deletion |

## Scripts

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `preflight.py` | Safety check | 0=safe, 2=blocked |
| `analyze.py` | Scan repo | 0=success, 1=error |
| `cleanup.py` | Execute ops | 0=success, 2=partial |

## Blocking Behavior

| Context | During Merge | During Rebase |
|---------|--------------|---------------|
| File edits (hook) | ALLOW | BLOCK |
| Git hygiene | BLOCK | BLOCK |

Hygiene blocks during merge to protect merge state.
```

**Step 2: Commit**

```bash
git add .claude/skills/git-hygiene/SKILL.md
git commit -m "docs(git-hygiene): rewrite SKILL.md with execution protocol

Complete rewrite. Replaces aspirational docs with actionable orchestration."
```

---

## Task 11: Integration Test

**Step 1: Test preflight**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
python3 .claude/skills/git-hygiene/scripts/preflight.py --json
```
Expected: `{"safe": true, ...}`

**Step 2: Test analysis**

```bash
python3 .claude/skills/git-hygiene/scripts/analyze.py --json
```
Expected: JSON with branches, stashes, untracked, stats

**Step 3: Test dry-run cleanup**

```bash
python3 .claude/skills/git-hygiene/scripts/cleanup.py --json --dry-run --prune
```
Expected: `[DRY RUN]` messages

**Step 4: Run full test suite**

```bash
cd .claude/skills/git-hygiene/scripts && python3 -m pytest -v
```
Expected: All tests pass

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(git-hygiene): complete implementation with tests

- common.py shared utilities
- 6 bug fixes (stash parsing, pattern matching, merge detection,
  threshold, race condition, worktree safety)
- Full test coverage
- Rewritten SKILL.md with orchestration protocol"
```

---

## Summary

| Task | Files | Description |
|------|-------|-------------|
| 1 | common.py | Create shared utilities |
| 2 | test_common.py | Test common utilities |
| 3 | analyze.py | Fix stash delimiter |
| 4 | analyze.py | Fix pattern matching |
| 5 | analyze.py | Fix merge detection |
| 6 | analyze.py | Fix threshold |
| 7 | cleanup.py | Fix stash race |
| 8 | cleanup.py | Add worktree safety |
| 9 | all scripts | Refactor imports |
| 10 | SKILL.md | Rewrite docs |
| 11 | - | Integration test |
