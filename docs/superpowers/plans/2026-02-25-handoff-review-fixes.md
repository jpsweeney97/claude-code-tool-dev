# Handoff PR #26 Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all findings from the 4-agent PR review and adversarial Codex dialogue review of PR #26 (`feature/handoff-plugin-enhancements`).

**Architecture:** 5 tasks organized by file/commit boundary. Task 1 adds test infrastructure for cleanup.py. Tasks 2-3 fix Python code with TDD. Tasks 4-5 fix instruction document accuracy. All work stays on `feature/handoff-plugin-enhancements`.

**Tech Stack:** Python 3.11+, pytest, subprocess, pathlib. Markdown instruction documents.

**Revision:** Rev 3 — incorporates 5 findings from second adversarial Codex review (R1-R3 must-fix, R4-R5 should-fix). Rev 2 incorporated 12 findings from first review (B1-B4, I5-I9, M10-M12).

---

## Finding Reference

### PR Review Findings (4-agent review)

| ID | Severity | File | Summary |
|----|----------|------|---------|
| C1 | Critical | `cleanup.py:64,89` | `deleted.append()` runs after failed `trash` — return value lies |
| I1 | Important | `resuming-handoffs:135` | Glob comment claims `.archive/` exclusion — unverified |
| I2 | Important | `creating-handoffs:166-168` | Verification checklist inconsistent with Definition of Done |
| I3 | Important | `handoff-contract:88` | Known Limitation #1 uses "consumed" incorrectly |
| S1 | Suggestion | `cleanup.py` | Extract `_trash()` helper to deduplicate |
| S2 | Suggestion | `checkpointing:51` | Design rationale in procedure step 5 (Glob justification) |
| S3 | Suggestion | `checkpointing:55` | Design rationale in procedure step 5 (scope limitation) |
| S4 | Suggestion | `checkpointing:117` | Reference contract limitation by name, not number |
| S5 | Suggestion | `handoff-contract` | Add failure mode for `trash` in chain protocol cleanup |
| P1 | Pre-existing | `cleanup.py:26-39` | `get_project_name` silently swallows git failures |
| P2 | Pre-existing | `cleanup.py:65-66,90-91` | Broad `OSError` catch suppresses unexpected errors |

### Codex Dialogue Findings (adversarial review of rev 1)

| ID | Severity | Summary | Rev 1 Problem |
|----|----------|---------|---------------|
| B1 | Blocking | Glob→ls is a tool class regression | `ls` in Bash requires different permissions than Glob; `2>/dev/null` suppresses real errors |
| B2 | Blocking | Task 1 imports `_trash` before it exists | ImportError blocks ALL test collection in Task 1 |
| B3 | Blocking | No real C1 regression test for `prune_old_state_files` | Placeholder test was dead code (empty `with` body, `__wrapped__` fallback) |
| B4 | Blocking | `main()` has no top-level exception guard | Docstring says "always exits 0" but unhandled exception blocks SessionStart |
| I5 | Important | Glob recursion rationale is unverified | Neither "Glob is recursive" nor "Glob excludes .archive/" is proven |
| I6 | Important | Verification section is grep-only | No behavioral validation that /resume and /list-handoffs work after changes |
| I7 | Important | `test_stat_oserror_skipped` uses global `Path.stat` patch | May affect glob internals; couples to interpreter implementation |
| I8 | Important | Contract line 51 contradicts I3 fix | "consumed" in invariant vs "persists" in limitation #1 |
| I9 | Important | `pyproject.toml` with hatchling is overkill | Plugin is scripts + markdown, not an installable package |
| M10 | Minor | Preserve behavioral note in checkpointing line 51 | Rev 1 deleted the entire line including the useful "walk chain, don't scan" rule |
| M11 | Minor | "Archived files always have earlier timestamps" is a logic error | A just-archived file retains its original timestamp |
| M12 | Minor | Plan verification is string-presence checks only | Addressed by I6 |

### Second Codex Dialogue Findings (adversarial review of rev 2)

| ID | Severity | Summary | Rev 2 Problem |
|----|----------|---------|---------------|
| R1 | Must-fix | chmod(0o000) test is vacuous on macOS | File owner bypasses stat() permission bits; test passes without exercising OSError path |
| R2 | Must-fix | Post-filter sequencing not explicit in resume skill | Filter added inline but no ordering guarantee before "select most recent" step |
| R3 | Must-fix | main() docstring overpromises "Always 0" | `except Exception` doesn't catch BaseException subclasses; docstring should reflect this |
| R4 | Should-fix | `_trash` doesn't catch `PermissionError` | `OSError` subclass escapes the catch clause; outer catch prevents crash but _trash returns wrong value |
| R5 | Should-fix | I8 contract invariant "intended to be consumed" still ambiguous | Doesn't describe the actual read-then-cleanup lifecycle |
| R6 | Emerged | OSError comment wording depends on _trash broadening | If _trash catches OSError, outer catch is exclusively stat()-path; "primarily handles" → "handles" |
| R7 | Emerged | main() wiring test adds more value than archive-dir unit test | Assert both prune calls with correct args |

---

## Task 1: Add test infrastructure and baseline tests

**Files:**
- Create: `packages/plugins/handoff/pyproject.toml`
- Create: `packages/plugins/handoff/tests/__init__.py`
- Create: `packages/plugins/handoff/tests/test_cleanup.py`

**Addresses:** Enables TDD for Tasks 2-3. Incorporates B2 (no `_trash` import), I7/R1 (selective stat patch + hit assertion), I9 (minimal pyproject.toml).

### Step 1: Create minimal pyproject.toml

Create `packages/plugins/handoff/pyproject.toml`:

```toml
[project]
name = "handoff-plugin"
version = "1.1.0"
description = "Session handoff and resume plugin for Claude Code"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
```

No `[build-system]` section — this plugin is not an installable package (I9). Only test dependencies needed.

### Step 2: Create empty test init

Create `packages/plugins/handoff/tests/__init__.py` — empty file.

### Step 3: Write baseline tests for existing functions

Create `packages/plugins/handoff/tests/test_cleanup.py`. This file tests ONLY functions that exist in current cleanup.py — no `_trash` import (B2). Tests that depend on `_trash` are added in Task 2.

```python
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
        target = old.resolve()

        orig_stat = Path.stat
        hit = False

        def selective_stat(self_path: Path, *args: object, **kwargs: object) -> os.stat_result:
            """Raise OSError only for the target file, not for glob internals."""
            nonlocal hit
            if self_path.resolve() == target:
                hit = True
                raise OSError("permission denied")
            return orig_stat(self_path, *args, **kwargs)

        with patch("scripts.cleanup.Path.stat", autospec=True, side_effect=selective_stat):
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert hit is True, "Patch must exercise the target file's stat() path"
        assert result == []
```

**Note on `test_stat_oserror_skipped` (I7/R1):** Uses a selective `Path.stat` patch instead of `chmod(0o000)`. The chmod approach is vacuous on macOS — the file owner bypasses `stat()` permission bits, so the test passes without exercising the OSError path. The selective patch raises `OSError` only for the target file, and the `hit` assertion ensures the test is never vacuous. This is safe because `glob()` uses `os.scandir()` internally, not `Path.stat()`.

### Step 4: Run tests to verify baseline

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v
```

Expected: All tests PASS. These test existing behavior only.

### Step 5: Commit

```bash
git add packages/plugins/handoff/pyproject.toml packages/plugins/handoff/tests/
git commit -m "test(handoff): add test infrastructure and baseline cleanup.py tests"
```

---

## Task 2: Fix C1 — extract _trash, fix deleted.append, refactor prune_old_state_files (C1 + S1 + B3)

**Files:**
- Modify: `packages/plugins/handoff/scripts/cleanup.py`
- Modify: `packages/plugins/handoff/tests/test_cleanup.py`

**Addresses:** C1 (critical: deleted.append placement), S1 (extract _trash helper), B3 (real C1 regression test for prune_old_state_files), R4 (broaden _trash to catch OSError).

### Step 1: Write failing C1 regression test for prune_old_handoffs

Add to `tests/test_cleanup.py` in `TestPruneOldHandoffs`:

```python
    def test_failed_trash_not_in_deleted(self, tmp_path: Path) -> None:
        """C1 regression: files not trashed must not appear in deleted list."""
        old = tmp_path / "old.md"
        old.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))
        # Mock subprocess.run to raise FileNotFoundError (trash not installed)
        with patch(
            "scripts.cleanup.subprocess.run", side_effect=FileNotFoundError
        ):
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert result == [], "File should not be in deleted list when trash fails"
```

### Step 2: Run test to verify it fails

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py::TestPruneOldHandoffs::test_failed_trash_not_in_deleted -v
```

Expected: FAIL — `assert [PosixPath('.../old.md')] == []` — confirms C1 bug.

### Step 3: Extract _trash helper and fix deleted.append in both prune functions

In `packages/plugins/handoff/scripts/cleanup.py`:

**Add `_trash` function** after line 21 (after imports, before `get_project_name`):

```python
def _trash(path: Path) -> bool:
    """Attempt to move a file to trash. Returns True on success, False on failure.

    Failures are silent by design — this runs during SessionStart cleanup where
    blocking the session is worse than skipping a deletion.
    """
    try:
        subprocess.run(["trash", str(path)], capture_output=True, timeout=5, check=True)
        return True
    except FileNotFoundError:
        return False  # trash binary not installed — skip deletion
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False  # PermissionError, trash failure, or timeout — skip
```

**Replace the inner try/except + unconditional append in `prune_old_handoffs`** (lines 58-64):

Before:
```python
                try:
                    subprocess.run(["trash", str(handoff)], capture_output=True, timeout=5, check=True)
                except FileNotFoundError:
                    pass  # trash binary not installed — skip deletion, don't fall back to unlink
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass  # trash failed or timed out — skip, don't block session start
                deleted.append(handoff)
```

After:
```python
                if _trash(handoff):
                    deleted.append(handoff)
```

**Same replacement in `prune_old_state_files`** (lines 83-89): replace the inner try/except + append with `if _trash(state_file): deleted.append(state_file)`.

### Step 4: Refactor prune_old_state_files to accept state_dir parameter (B3)

This makes the function testable without monkeypatching `Path.home()`.

Before:
```python
def prune_old_state_files(max_age_hours: int = 24) -> list[Path]:
    """Delete state files older than max_age_hours. Returns list of deleted files."""
    state_dir = Path.home() / ".claude" / ".session-state"
    if not state_dir.exists():
        return []
```

After:
```python
def prune_old_state_files(max_age_hours: int = 24, *, state_dir: Path | None = None) -> list[Path]:
    """Delete state files older than max_age_hours. Returns list of deleted files."""
    if state_dir is None:
        state_dir = Path.home() / ".claude" / ".session-state"
    if not state_dir.exists():
        return []
```

Backwards compatible — the only caller is `main()` which uses `prune_old_state_files(max_age_hours=24)`.

### Step 5: Update C1 regression test to use _trash mock, add prune_old_state_files test

Update the import block in `tests/test_cleanup.py` to add `_trash` and `prune_old_state_files`:

```python
from scripts.cleanup import (
    _trash,
    get_project_name,
    prune_old_handoffs,
    prune_old_state_files,
)
```

Update `test_failed_trash_not_in_deleted` to mock `_trash` instead of `subprocess.run`:

```python
    def test_failed_trash_not_in_deleted(self, tmp_path: Path) -> None:
        """C1 regression: files not trashed must not appear in deleted list."""
        old = tmp_path / "old.md"
        old.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))
        with patch("scripts.cleanup._trash", return_value=False):
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert result == [], "File should not be in deleted list when trash fails"
```

Add `test_old_files_deleted` to verify the positive case:

```python
    def test_old_files_deleted(self, tmp_path: Path) -> None:
        old = tmp_path / "old.md"
        old.write_text("content")
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old, (old_time, old_time))
        with patch("scripts.cleanup._trash", return_value=True) as mock_trash:
            result = prune_old_handoffs(tmp_path, max_age_days=30)
        assert result == [old]
        mock_trash.assert_called_once_with(old)
```

Add `TestTrash` class:

```python
class TestTrash:
    """Tests for _trash helper."""

    def test_success_returns_true(self, tmp_path: Path) -> None:
        target = tmp_path / "file.md"
        target.write_text("content")
        with patch("scripts.cleanup.subprocess.run") as mock_run:
            assert _trash(target) is True
            mock_run.assert_called_once_with(
                ["trash", str(target)],
                capture_output=True,
                timeout=5,
                check=True,
            )

    def test_binary_not_found_returns_false(self, tmp_path: Path) -> None:
        target = tmp_path / "file.md"
        with patch(
            "scripts.cleanup.subprocess.run", side_effect=FileNotFoundError
        ):
            assert _trash(target) is False

    def test_trash_failure_returns_false(self, tmp_path: Path) -> None:
        target = tmp_path / "file.md"
        with patch(
            "scripts.cleanup.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "trash"),
        ):
            assert _trash(target) is False

    def test_timeout_returns_false(self, tmp_path: Path) -> None:
        target = tmp_path / "file.md"
        with patch(
            "scripts.cleanup.subprocess.run",
            side_effect=subprocess.TimeoutExpired("trash", 5),
        ):
            assert _trash(target) is False

    def test_oserror_returns_false(self, tmp_path: Path) -> None:
        """R4: PermissionError (OSError subclass) must not escape _trash."""
        target = tmp_path / "file.md"
        with patch(
            "scripts.cleanup.subprocess.run",
            side_effect=PermissionError("not executable"),
        ):
            assert _trash(target) is False
```

Add `TestPruneOldStateFiles` with real C1 regression test (B3):

```python
class TestPruneOldStateFiles:
    """Tests for prune_old_state_files."""

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        assert prune_old_state_files(state_dir=tmp_path / "nope") == []

    def test_old_state_files_deleted(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "session-state"
        state_dir.mkdir()
        old = state_dir / "handoff-abc123"
        old.write_text("/some/archive/path")
        old_time = time.time() - (25 * 60 * 60)  # 25 hours ago
        os.utime(old, (old_time, old_time))
        with patch("scripts.cleanup._trash", return_value=True):
            result = prune_old_state_files(max_age_hours=24, state_dir=state_dir)
        assert result == [old]

    def test_failed_trash_not_in_deleted(self, tmp_path: Path) -> None:
        """C1 regression: state files not trashed must not appear in deleted list (B3)."""
        state_dir = tmp_path / "session-state"
        state_dir.mkdir()
        old = state_dir / "handoff-abc123"
        old.write_text("/some/archive/path")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(old, (old_time, old_time))
        with patch("scripts.cleanup._trash", return_value=False):
            result = prune_old_state_files(max_age_hours=24, state_dir=state_dir)
        assert result == [], "State file should not be in deleted list when trash fails"

    def test_recent_state_files_not_deleted(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "session-state"
        state_dir.mkdir()
        recent = state_dir / "handoff-def456"
        recent.write_text("/some/archive/path")
        with patch("scripts.cleanup._trash") as mock_trash:
            result = prune_old_state_files(max_age_hours=24, state_dir=state_dir)
        assert result == []
        mock_trash.assert_not_called()

    def test_non_handoff_files_ignored(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "session-state"
        state_dir.mkdir()
        other = state_dir / "other-file"
        other.write_text("content")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(other, (old_time, old_time))
        with patch("scripts.cleanup._trash") as mock_trash:
            result = prune_old_state_files(max_age_hours=24, state_dir=state_dir)
        assert result == []
        mock_trash.assert_not_called()
```

### Step 6: Run all tests

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v
```

Expected: ALL tests pass. C1 regression tests pass for both `prune_old_handoffs` and `prune_old_state_files`.

### Step 7: Commit

```bash
git add packages/plugins/handoff/scripts/cleanup.py packages/plugins/handoff/tests/test_cleanup.py
git commit -m "fix(handoff): extract _trash helper, fix deleted.append, refactor prune_old_state_files (C1+S1+B3)

C1: deleted.append() was outside the try block in both prune functions,
causing files to be reported as deleted even when trash failed.
Fix: extract _trash() -> bool helper, condition append on success.
B3: refactor prune_old_state_files to accept state_dir parameter for
testability. Add C1 regression tests for both affected functions."
```

---

## Task 3: Harden cleanup.py — main() guard and error docs (B4 + P1 + P2)

**Files:**
- Modify: `packages/plugins/handoff/scripts/cleanup.py`
- Modify: `packages/plugins/handoff/tests/test_cleanup.py`

**Addresses:** B4 (main() exception guard), P1 (silent git fallback), P2 (broad OSError catch), R3 (weaken docstring), R6 (OSError comment wording), R7 (main() wiring test).

### Step 1: Write failing test for main() exception guard (B4)

Add to `tests/test_cleanup.py`:

```python
from scripts.cleanup import main


class TestMain:
    """Tests for main entry point."""

    def test_always_returns_zero(self) -> None:
        """B4: main() must return 0 even when internals raise."""
        with patch("scripts.cleanup.get_handoffs_dir", side_effect=RuntimeError("unexpected")):
            assert main() == 0

    def test_calls_both_prune_functions(self, tmp_path: Path) -> None:
        """R7: main() must call prune_old_handoffs twice and prune_old_state_files once."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        with (
            patch("scripts.cleanup.get_handoffs_dir", return_value=handoffs_dir),
            patch("scripts.cleanup.prune_old_handoffs") as mock_handoffs,
            patch("scripts.cleanup.prune_old_state_files") as mock_state,
        ):
            result = main()
        assert result == 0
        assert mock_handoffs.call_count == 2
        mock_handoffs.assert_any_call(handoffs_dir, max_age_days=30)
        mock_handoffs.assert_any_call(handoffs_dir / ".archive", max_age_days=90)
        mock_state.assert_called_once_with(max_age_hours=24)
```

### Step 2: Run test to verify it fails

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py::TestMain::test_always_returns_zero -v
```

Expected: FAIL — `RuntimeError: unexpected` propagates up. Confirms B4.

### Step 3: Add exception guard to main()

In `packages/plugins/handoff/scripts/cleanup.py`, replace `main`:

Before:
```python
def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old handoffs. Does not output anything.
    Users must explicitly run /resume to load handoffs.

    Returns:
        0 on success
    """
    handoffs_dir = get_handoffs_dir()

    # Prune active handoffs older than 30 days
    prune_old_handoffs(handoffs_dir, max_age_days=30)

    # Prune archived handoffs older than 90 days
    prune_old_handoffs(handoffs_dir / ".archive", max_age_days=90)

    # Prune stale state files older than 24 hours
    prune_old_state_files(max_age_hours=24)

    return 0
```

After:
```python
def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old handoffs. Does not output anything.
    Users must explicitly run /resume to load handoffs.

    Returns:
        0 on best-effort completion. A SessionStart hook must never block
        session start. Returns 0 unless process-level termination (e.g.
        SIGKILL, KeyboardInterrupt) interrupts execution.
    """
    try:
        handoffs_dir = get_handoffs_dir()

        # Prune active handoffs older than 30 days
        prune_old_handoffs(handoffs_dir, max_age_days=30)

        # Prune archived handoffs older than 90 days
        prune_old_handoffs(handoffs_dir / ".archive", max_age_days=90)

        # Prune stale state files older than 24 hours
        prune_old_state_files(max_age_hours=24)
    except Exception:
        pass  # Never block session start — cleanup is best-effort

    return 0
```

### Step 4: Add comments to get_project_name (P1)

Replace `get_project_name`:

Before:
```python
def get_project_name() -> str:
    """Get project name from git root directory or current directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return Path.cwd().name
```

After:
```python
def get_project_name() -> str:
    """Get project name from git root directory, falling back to current directory name.

    Fallback is intentional for non-git directories. For corrupted repos or
    missing git binary, the fallback may resolve to the wrong project name —
    accepted because cleanup targets are scoped to individual files with
    age-based pruning (misidentification doesn't delete wrong-age files).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
        # Non-zero return: not a git repo, or git error. Fall back to cwd.
    except subprocess.TimeoutExpired:
        pass  # Git hanging (disk issue, corrupted repo). Fall back to cwd.
    except FileNotFoundError:
        pass  # Git binary not installed. Fall back to cwd.
    return Path.cwd().name
```

### Step 5: Update OSError comments (P2)

In `prune_old_handoffs`, replace the outer except:

Before:
```python
        except OSError:
            pass  # Silently ignore errors during cleanup
```

After:
```python
        except OSError:
            pass  # Handles stat() TOCTOU: file removed between glob() and stat()
```

Same change in `prune_old_state_files`.

**Note (R6):** Since Task 2 broadens `_trash()` to catch `OSError` (including `PermissionError`), the outer `except OSError` is now exclusively stat()-path failures (TOCTOU race: `FileNotFoundError` if removed, `PermissionError` if permissions changed between glob and stat). The comment says "handles" (not "primarily handles") because `_trash()` absorbs all its own exceptions.

### Step 6: Run all tests

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v
```

Expected: All tests pass, including `test_always_returns_zero`.

### Step 7: Commit

```bash
git add packages/plugins/handoff/scripts/cleanup.py packages/plugins/handoff/tests/test_cleanup.py
git commit -m "fix(handoff): add main() exception guard, clarify error handling (B4+P1+P2)

B4: wrap main() body in try/except to enforce 'always exits 0' contract.
A SessionStart hook that crashes blocks the user's session.
P1: add docstring explaining get_project_name fallback behavior.
P2: update OSError comments to explain TOCTOU rationale."
```

---

## Task 4: Fix Glob handling in resuming-handoffs (I1 + B1 + I5)

**Files:**
- Modify: `packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`

**Addresses:** I1 (Glob comment inaccurate), B1 (keep Glob + post-filter instead of switching to Bash), I5 (don't assert Glob recursion without proof), M11 (remove incorrect timestamp reasoning), R2 (make post-filter sequencing explicit).

**Design rationale (B1):** Glob is a Claude Code built-in tool that requires no user permission. Bash requires permission approval. Switching from Glob to `ls` in Bash would change the tool permission class, degrading the user experience. Additionally, `ls ... 2>/dev/null` suppresses real errors (permission denied, path not found), and unquoted project paths break on spaces. The correct fix is to keep Glob and add an explicit post-filter to exclude `.archive/` paths.

### Step 1: Fix /resume procedure (line 110)

In `packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`, replace line 110:

Before:
```markdown
   - If no path: use Glob with `pattern="*.md"` and `path` set to the absolute path `$HOME/.claude/handoffs/<project>/` (expand `$HOME` — tilde `~` doesn't expand in Glob patterns)
```

After (R2 — explicit sub-steps with ordering):
```markdown
   - If no path:
     1. Use Glob with `pattern="*.md"` and `path` set to the absolute path `$HOME/.claude/handoffs/<project>/` (expand `$HOME` — tilde `~` doesn't expand in Glob patterns)
     2. Filter results to exclude any paths containing `.archive/`
     3. If no results remain after filtering, report "No handoffs found for this project" and **STOP**
     4. Select most recent by filename (format: `YYYY-MM-DD_HH-MM_*.md`)
```

### Step 2: Fix /list-handoffs procedure (line 135)

Replace line 135:

Before:
```markdown
1. Use Glob with `pattern="*.md"` and `path` set to the absolute path `$HOME/.claude/handoffs/<project>/` (excludes `.archive/` subdirectory; expand `$HOME`)
```

After (R2 — explicit sub-steps with ordering):
```markdown
1. Use Glob with `pattern="*.md"` and `path` set to the absolute path `$HOME/.claude/handoffs/<project>/` (expand `$HOME` — tilde `~` doesn't expand in Glob patterns)
2. Filter results to exclude any paths containing `.archive/`
3. Read frontmatter from each remaining file
```

### Step 3: Verify by reading the file

Read the modified lines to confirm:
- Glob tool is retained (not replaced with Bash `ls`) — preserves permission class (B1)
- No unverified claims about Glob recursion behavior (I5)
- Post-filter is explicit and works regardless of whether Glob recurses (B1)
- No incorrect "earlier timestamps" reasoning (M11)

### Step 4: Commit

```bash
git add packages/plugins/handoff/skills/resuming-handoffs/SKILL.md
git commit -m "fix(handoff): add .archive/ post-filter to Glob in resume skill (I1+B1)

Remove unverified claim about Glob excluding .archive/ subdirectory.
Add explicit post-filter to exclude .archive/ paths from results.
Keep Glob tool (not Bash ls) to preserve permission class."
```

---

## Task 5: Fix markdown accuracy across contract and skills (I2 + I3 + I8 + S2-S5 + M10)

**Files:**
- Modify: `packages/plugins/handoff/skills/creating-handoffs/SKILL.md`
- Modify: `packages/plugins/handoff/references/handoff-contract.md`
- Modify: `packages/plugins/handoff/skills/checkpointing/SKILL.md`

**Addresses:** I2, I3, I8, S2, S3, S4, S5, M10, R5 (stronger I8 wording).

### Step 1: Consolidate creating-handoffs verification checklist (I2)

In `packages/plugins/handoff/skills/creating-handoffs/SKILL.md`, replace lines 166-168:

Before:
```markdown
- [ ] Required fields present: date, time, created_at, project, title
- [ ] `type: handoff` present in generated frontmatter
- [ ] `session_id` present in generated frontmatter
```

After:
```markdown
- [ ] Required fields present: date, time, created_at, session_id, project, title, type (per contract)
```

### Step 2: Fix contract Known Limitation #1 wording (I3)

In `packages/plugins/handoff/references/handoff-contract.md`, replace line 88:

Before:
```markdown
1. **Resume-consume recovery:** If a session resumes a handoff but crashes before creating a new one, the state file is consumed but no successor exists. The chain has a gap. No automated recovery — the archived file is intact and can be manually re-resumed.
```

After:
```markdown
1. **Resume-crash recovery:** If a session resumes a handoff but crashes before creating a new one, the state file persists but no successor handoff references the archived file. The chain has a gap. No automated recovery — the archived file is intact and can be manually re-resumed. The orphaned state file is pruned by the 24-hour TTL.
```

### Step 3: Fix contract invariant consistency (I8)

In `packages/plugins/handoff/references/handoff-contract.md`, replace line 51:

Before:
```markdown
**Invariant:** State files are created by resume and consumed by the next create/checkpoint. A state file that persists beyond 24 hours is stale (cleanup.py prunes these).
```

After (R5 — describes actual lifecycle):
```markdown
**Invariant:** State files are created by resume; the next create/checkpoint reads them to populate `resumed_from`, then attempts cleanup via `trash`. If cleanup fails, the file may persist until TTL pruning (24 hours). A state file that persists beyond 24 hours is stale.
```

This replaces the ambiguous "consumed" with the actual read-then-cleanup lifecycle (R5). Consistent with the I3 fix and the S5 trash failure mode addition.

### Step 4: Add trash failure mode to contract chain protocol (S5)

In `packages/plugins/handoff/references/handoff-contract.md`, replace line 49:

Before:
```markdown
3. **Cleanup:** Use `trash` to remove state file at `~/.claude/.session-state/handoff-<session_id>` (if exists)
```

After:
```markdown
3. **Cleanup:** Use `trash` to remove state file at `~/.claude/.session-state/handoff-<session_id>` (if exists). If `trash` fails, warn the user that the state file persists but do not block handoff/checkpoint creation — the 24-hour TTL will clean it up.
```

### Step 5: Trim checkpointing step 5 — remove rationale, preserve behavioral note (S2 + S3 + M10)

In `packages/plugins/handoff/skills/checkpointing/SKILL.md`:

**Replace line 51** — remove performance/Glob justification, keep behavioral rule (M10):

Before:
```markdown
   - This is bounded to 2-3 file reads maximum — faster than Glob and correct across the resume/archive lifecycle (Glob scan of active directory fails because `/resume` archives files to `.archive/`)
```

After:
```markdown
   - Walk the `resumed_from` chain; do not scan the active directory (archived files are not in it)
```

**Replace line 55** — keep behavioral instruction, remove design justification (S3):

Before:
```markdown
   - **Scope limitation:** The guardrail only detects consecutive checkpoints within a single resume chain (connected via `resumed_from`). A user who checkpoints, closes the session, opens a new session without resuming, and checkpoints again will not trigger the guardrail because the chain is broken. This is by design — the guardrail is advisory, not a hard gate, and cross-chain detection would require scanning all archived files (O(n) reads).
```

After:
```markdown
   - **Scope limitation:** The guardrail only detects consecutive checkpoints within a single resume chain (connected via `resumed_from`). Cross-session checkpoints without `/resume` between them do not trigger the guardrail.
```

### Step 6: Remove parenthetical from checkpointing step 6 (S3)

In `packages/plugins/handoff/skills/checkpointing/SKILL.md`, line 60:

Before:
```markdown
   - Populate frontmatter `files:` from file paths listed in the Active Files section (the body section and frontmatter field serve complementary purposes: frontmatter enables machine-readable queries, body provides human-readable context)
```

After:
```markdown
   - Populate frontmatter `files:` from file paths listed in the Active Files section
```

### Step 7: Fix contract limitation reference (S4)

In `packages/plugins/handoff/skills/checkpointing/SKILL.md`, line 117:

Before:
```markdown
- This is informational — the chain link is skipped. No data loss. See contract Known Limitations §3.
```

After:
```markdown
- This is informational — the chain link is skipped. No data loss. See contract Known Limitations: State-file TTL race.
```

### Step 8: Verify all changes

Read each modified file to confirm:
- creating-handoffs: single verification line with all 7 fields
- handoff-contract: limitation #1 says "persists" not "consumed"; invariant says "intended to be consumed" (I8 consistency); cleanup step has failure mode
- checkpointing: behavioral note preserved (M10), no design rationale in step 5, no parenthetical in step 6, named reference in troubleshooting

### Step 9: Commit

```bash
git add packages/plugins/handoff/skills/creating-handoffs/SKILL.md packages/plugins/handoff/references/handoff-contract.md packages/plugins/handoff/skills/checkpointing/SKILL.md
git commit -m "fix(handoff): correct instruction accuracy across contract and skills (I2+I3+I8+S2-S5+M10)

- Consolidate verification checklist to match Definition of Done (I2)
- Fix 'consumed' wording in contract limitation #1 (I3)
- Soften contract invariant to 'intended to be consumed' for consistency (I8)
- Add trash failure mode to chain protocol cleanup (S5)
- Trim design rationale from checkpointing, preserve behavioral note (S2+S3+M10)
- Reference contract limitation by name not number (S4)"
```

---

## Verification

After all 5 tasks:

### Automated

```bash
cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v
```

Expected: All tests pass, including:
- C1 regression tests for BOTH `prune_old_handoffs` and `prune_old_state_files`
- `main()` exception guard test
- `_trash` helper unit tests
- Baseline get_project_name and prune behavior tests

### Manual — string-presence checks

```bash
cd packages/plugins/handoff
grep -n 'deleted.append' scripts/cleanup.py        # Should appear only inside 'if _trash(...)' blocks
grep -n 'excludes .archive' skills/resuming-handoffs/SKILL.md  # Should return no results
grep -n 'consumed but no successor' references/handoff-contract.md  # Should return no results
grep -n '§3' skills/checkpointing/SKILL.md          # Should return no results
grep -n 'except Exception' scripts/cleanup.py       # Should appear in main()
```

### Manual — behavioral validation (I6)

Verify `/resume` and `/list-handoffs` work correctly with the Glob + post-filter change:

1. **Create a test file in `.archive/`:** `echo "test" > ~/.claude/handoffs/claude-code-tool-dev/.archive/test-glob-check.md`
2. **Run `/list-handoffs`:** The test file should NOT appear in the table (post-filter excludes `.archive/` paths).
3. **Run `/resume`:** Should find the most recent active handoff, not the `.archive/` test file.
4. **Cleanup:** `trash ~/.claude/handoffs/claude-code-tool-dev/.archive/test-glob-check.md`

This validates that the post-filter works regardless of whether Glob is recursive.
