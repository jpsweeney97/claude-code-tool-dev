# Handoff docs/ Storage Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move handoff storage from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`, making handoffs git-tracked project documentation with auto-commit on every state change.

**Architecture:** Update path resolution in `project_paths.py`, create `auto_commit.py` for testable git commit logic, strip handoff pruning from `cleanup.py`, update `is_handoff_path()` to match `docs/handoffs/`, add legacy fallback to search/triage, update skills with git commit steps and `Bash` in `allowed-tools`. All changes land in a single atomic commit.

**Tech Stack:** Python 3, pytest, subprocess (git), pathlib

**Spec:** `docs/superpowers/specs/2026-03-29-handoff-docs-storage-design.md`

**All paths are relative to:** `packages/plugins/handoff/` unless prefixed with repo root markers.

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `scripts/project_paths.py` | Path resolution: `docs/handoffs`, legacy dir, `archive/` |
| Create | `scripts/auto_commit.py` | Git state check → stage → commit (~30 lines core) |
| Modify | `scripts/cleanup.py` | Strip handoff pruning; session-state only |
| Modify | `scripts/quality_check.py` | `is_handoff_path()` matches `docs/handoffs/` |
| Modify | `scripts/search.py` | `archive/` rename + legacy fallback |
| Modify | `scripts/triage.py` | `archive/` rename + legacy fallback |
| Modify | `tests/test_project_paths.py` | Assert `docs/handoffs`, test legacy dir |
| Create | `tests/test_auto_commit.py` | Git state checks, narrow staging, edge cases |
| Modify | `tests/test_cleanup.py` | Remove handoff pruning tests |
| Modify | `tests/test_quality_check.py` | New path matching assertions + near-miss cases |
| Modify | `tests/test_search.py` | `archive/` rename |
| Modify | `tests/test_triage.py` | `archive/` rename |
| Modify | `tests/test_distill.py` | `archive/` rename (line 875) |
| Modify | `skills/save/SKILL.md` | Paths + auto_commit call + `Bash` in allowed-tools |
| Modify | `skills/load/SKILL.md` | Paths + auto_commit call + `Bash` + legacy fallback |
| Modify | `skills/quicksave/SKILL.md` | Paths + auto_commit call + `Bash` |
| Modify | `skills/distill/SKILL.md` | Path refs only |
| Modify | `references/handoff-contract.md` | Storage, retention, chain protocol |
| Modify | `references/format-reference.md` | Storage, retention |
| Modify | `README.md` | Paths, retention, hook description |
| Modify | `CHANGELOG.md` | New entry |
| Modify | `<repo>/.gitignore` | Remove `.claude/handoffs/` |
| Modify | `<repo>/.claude/settings.json` | Remove `**/.claude/handoffs/**` from GITFLOW_ALLOW_FILES |
| Modify | `<repo>/.claude/hooks/test_require_gitflow.py` | Update test path |
| Modify | `<repo>/.claude/skills/changelog/SKILL.md` | Update archive path |
| Modify | `<repo>/.claude/skills/changelog/references/entry-writing.md` | Update archive path |

---

### Task 1: Update project_paths.py

**Files:**
- Modify: `scripts/project_paths.py`
- Test: `tests/test_project_paths.py`

- [ ] **Step 1: Update get_handoffs_dir and get_archive_dir, add get_legacy_handoffs_dir**

Replace the entire `get_handoffs_dir`, `get_archive_dir` functions and add `get_legacy_handoffs_dir`:

```python
def get_handoffs_dir() -> Path:
    """Get handoffs directory: <project_root>/docs/handoffs/"""
    root, _ = get_project_root()
    return root / "docs" / "handoffs"


def get_archive_dir() -> Path:
    """Return the archive directory for the current project's handoffs."""
    return get_handoffs_dir() / "archive"


def get_legacy_handoffs_dir() -> Path:
    """Get legacy handoffs directory: <project_root>/.claude/handoffs/

    Used by search, triage, and load for fallback discovery of
    pre-migration handoff files.
    """
    root, _ = get_project_root()
    return root / ".claude" / "handoffs"
```

- [ ] **Step 2: Update test_project_paths.py**

Replace the `TestGetHandoffsDir` class:

```python
class TestGetHandoffsDir:
    """Tests for get_handoffs_dir."""

    def test_returns_docs_handoffs_path(self) -> None:
        with patch(
            "scripts.project_paths.get_project_root",
            return_value=(Path("/Users/jp/Projects/myproject"), "git"),
        ):
            result = get_handoffs_dir()
        assert result == Path("/Users/jp/Projects/myproject") / "docs" / "handoffs"
```

Replace the `TestGetArchiveDir` class:

```python
class TestGetArchiveDir:
    def test_returns_archive_subdir(self) -> None:
        result = get_archive_dir()
        assert result.name == "archive"
        assert result.parent.name == "handoffs"

    def test_is_child_of_handoffs_dir(self) -> None:
        archive = get_archive_dir()
        handoffs = get_handoffs_dir()
        assert archive.parent == handoffs
```

Add new `TestGetLegacyHandoffsDir` class and update imports:

```python
from scripts.project_paths import (
    get_archive_dir,
    get_handoffs_dir,
    get_legacy_handoffs_dir,
    get_project_name,
    get_project_root,
)


class TestGetLegacyHandoffsDir:
    """Tests for get_legacy_handoffs_dir — fallback path for pre-migration files."""

    def test_returns_claude_handoffs_path(self) -> None:
        with patch(
            "scripts.project_paths.get_project_root",
            return_value=(Path("/Users/jp/Projects/myproject"), "git"),
        ):
            result = get_legacy_handoffs_dir()
        assert result == Path("/Users/jp/Projects/myproject") / ".claude" / "handoffs"
```

- [ ] **Step 3: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_project_paths.py -v`
Expected: All pass.

---

### Task 2: Create auto_commit.py

**Files:**
- Create: `scripts/auto_commit.py`
- Create: `tests/test_auto_commit.py`

- [ ] **Step 1: Write test_auto_commit.py**

```python
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
        head_mock = MagicMock(returncode=0, stdout="refs/heads/main\n")

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_auto_commit.py -v`
Expected: ImportError (module not found)

- [ ] **Step 3: Write auto_commit.py**

```python
#!/usr/bin/env python3
"""auto_commit.py — Narrow-scope git commit for handoff state changes.

Checks git state, stages specified files, commits with provided message.
Used by save/load/quicksave skills after file writes or archive moves.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def check_git_state() -> tuple[bool, str]:
    """Return (can_commit, reason). Checks: no repo, detached HEAD, rebase."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return False, "No git repository"
        git_dir = Path(r.stdout.strip())
        r2 = subprocess.run(
            ["git", "symbolic-ref", "-q", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if r2.returncode != 0:
            return False, "Detached HEAD"
        if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
            return False, "Rebase in progress"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return False, f"Git check failed: {exc}"
    return True, ""


def auto_commit(
    files: list[str], message: str, *, staged: bool = False,
) -> tuple[bool, str]:
    """Stage files and commit with --only. Returns (success, reason)."""
    ok, reason = check_git_state()
    if not ok:
        return False, reason
    try:
        if not staged:
            for f in files:
                subprocess.run(
                    ["git", "add", "--", f],
                    capture_output=True, text=True, timeout=10, check=True,
                )
        r = subprocess.run(
            ["git", "commit", "--only", *files, "-m", message],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return False, f"Commit failed: {r.stderr.strip()}"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
        return False, f"Commit failed: {exc}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    """CLI: auto_commit.py -m MESSAGE [--staged] [FILES...]"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-commit handoff files")
    parser.add_argument("files", nargs="*", help="Files to commit")
    parser.add_argument("-m", "--message", required=True, help="Commit message")
    parser.add_argument("--staged", action="store_true", help="Files already staged")
    args = parser.parse_args(argv)
    ok, reason = auto_commit(args.files, args.message, staged=args.staged)
    if not ok:
        print(f"Warning: Handoff saved but not committed — {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_auto_commit.py -v`
Expected: All pass.

---

### Task 3: Strip cleanup.py handoff pruning

**Files:**
- Modify: `scripts/cleanup.py`
- Modify: `tests/test_cleanup.py`

- [ ] **Step 1: Remove get_project_root, get_handoffs_dir, prune_old_handoffs from cleanup.py**

Remove these three functions entirely:
- `get_project_root()` (lines 42–66)
- `get_handoffs_dir()` (lines 69–70)
- `prune_old_handoffs()` (lines 73–88)

- [ ] **Step 2: Rewrite main() to call only prune_old_state_files**

Replace the `main()` function body:

```python
def main() -> int:
    """Main entry point for SessionStart hook.

    Silently prunes old state files. Does not touch handoff files
    (those are git-tracked in docs/handoffs/ — manual cleanup only).

    Returns:
        0 on best-effort completion. A SessionStart hook must never block
        session start. Only BaseException subclasses (e.g., KeyboardInterrupt,
        SystemExit) propagate — these indicate process-level termination.
    """
    try:
        prune_old_state_files(max_age_hours=24)
    except Exception:
        pass  # Never block session start — cleanup is best-effort

    return 0
```

- [ ] **Step 3: Update test_cleanup.py imports**

Replace the imports:

```python
from scripts.cleanup import (
    _trash,
    main,
    prune_old_state_files,
)
```

- [ ] **Step 4: Remove deleted-function test classes from test_cleanup.py**

Delete these entire test classes:
- `TestGetProjectRoot` (lines 19–55)
- `TestGetHandoffsDir` (lines 58–65)
- `TestPruneOldHandoffs` (lines 68–133)

- [ ] **Step 5: Update TestMain to match new behavior**

Replace the `TestMain` class:

```python
class TestMain:
    """Tests for main entry point."""

    def test_always_returns_zero(self) -> None:
        """main() must return 0 even when internals raise."""
        with patch("scripts.cleanup.prune_old_state_files", side_effect=RuntimeError("unexpected")):
            assert main() == 0

    def test_calls_prune_state_files_only(self) -> None:
        """main() calls prune_old_state_files once. No handoff pruning."""
        with patch("scripts.cleanup.prune_old_state_files") as mock_state:
            result = main()
        assert result == 0
        mock_state.assert_called_once_with(max_age_hours=24)
```

- [ ] **Step 6: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v`
Expected: All pass.

---

### Task 4: Update quality_check.py matching rule

**Files:**
- Modify: `scripts/quality_check.py`
- Modify: `tests/test_quality_check.py`

- [ ] **Step 1: Replace is_handoff_path in quality_check.py**

Replace the entire `is_handoff_path` function:

```python
def is_handoff_path(file_path: str) -> bool:
    """Check if file is a handoff/checkpoint (active or archived).

    Valid: <root>/docs/handoffs/<file>.md, <root>/docs/handoffs/archive/<file>.md
    Invalid: non-.md, deeper nesting, no docs parent, handoffs-variant directories.
    """
    path = Path(file_path)

    if path.suffix != ".md":
        return False

    parts = path.parts
    for i in range(len(parts) - 1):
        if parts[i] == "docs" and parts[i + 1] == "handoffs":
            remaining = parts[i + 2:]
            # Direct child of handoffs/
            if len(remaining) == 1:
                return True
            # Direct child of handoffs/archive/
            if len(remaining) == 2 and remaining[0] == "archive":
                return True
            return False

    return False
```

- [ ] **Step 2: Update docstrings at top of file**

Replace lines 5–6:

```python
checkpoint (path under <project_root>/docs/handoffs/), validates:
```

Replace line 354 comment (inside old is_handoff_path, now gone — new docstring is in the replacement above).

- [ ] **Step 3: Update HANDOFF_PATH fixture in test_quality_check.py**

```python
HANDOFF_PATH = str(
    Path("/tmp/test-project")
    / "docs"
    / "handoffs"
    / "2026-02-26_16-00_test.md"
)
```

- [ ] **Step 4: Replace TestIsHandoffPath class in test_quality_check.py**

```python
class TestIsHandoffPath:
    """Tests for is_handoff_path — file path detection."""

    def test_valid_active_handoff(self) -> None:
        assert is_handoff_path(HANDOFF_PATH) is True

    def test_valid_any_project_root(self) -> None:
        path = "/Users/jp/Projects/myproject/docs/handoffs/2026-02-26_test.md"
        assert is_handoff_path(path) is True

    def test_valid_archived_handoff(self) -> None:
        path = "/tmp/proj/docs/handoffs/archive/test.md"
        assert is_handoff_path(path) is True

    def test_non_handoff_directory(self) -> None:
        assert is_handoff_path("/tmp/random/file.md") is False

    def test_non_md_file(self) -> None:
        path = "/tmp/proj/docs/handoffs/file.txt"
        assert is_handoff_path(path) is False

    def test_nested_too_deep(self) -> None:
        """File nested under a subdirectory of handoffs/ is rejected."""
        path = "/tmp/proj/docs/handoffs/subdir/deep/file.md"
        assert is_handoff_path(path) is False

    def test_no_docs_parent_rejected(self) -> None:
        """handoffs/ without docs/ parent is not a valid handoff path."""
        path = "/tmp/handoffs/file.md"
        assert is_handoff_path(path) is False

    def test_handoffs_without_file_rejected(self) -> None:
        """Path ending at handoffs/ directory itself is rejected."""
        path = "/tmp/proj/docs/handoffs/"
        assert is_handoff_path(path) is False

    def test_handoffs_variant_rejected(self) -> None:
        """handoffs-v2 is not handoffs."""
        path = "/tmp/proj/docs/handoffs-v2/foo.md"
        assert is_handoff_path(path) is False

    def test_other_docs_variant_rejected(self) -> None:
        """other-docs is not docs."""
        path = "/tmp/proj/other-docs/handoffs/foo.md"
        assert is_handoff_path(path) is False

    def test_legacy_path_rejected(self) -> None:
        """Old .claude/handoffs/ path should not match."""
        path = "/tmp/proj/.claude/handoffs/test.md"
        assert is_handoff_path(path) is False
```

- [ ] **Step 5: Update TestMain archive test**

Replace `test_archive_path_silent`:

```python
    def test_archive_path_validates(self) -> None:
        """Archive path IS validated (is_handoff_path matches it)."""
        archive_path = str(
            Path("/tmp/test-project")
            / "docs"
            / "handoffs"
            / "archive"
            / "old.md"
        )
        content = _make_content()
        result, output = _run_main(
            _make_hook_input(archive_path, content)
        )
        assert result == 0
        # Valid content → no output (silent success)
        assert output == ""
```

- [ ] **Step 6: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py -v`
Expected: All pass.

---

### Task 5: Update search.py

**Files:**
- Modify: `scripts/search.py`
- Modify: `tests/test_search.py`

- [ ] **Step 1: Add archive_name parameter and legacy fallback imports**

Update imports to include `get_legacy_handoffs_dir`:

```python
    from scripts.project_paths import get_handoffs_dir, get_legacy_handoffs_dir, get_project_name
except ModuleNotFoundError:  # Direct execution (python3 scripts/search.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.handoff_parsing import HandoffFile, Section, parse_handoff  # type: ignore[no-redef]
    from scripts.project_paths import get_handoffs_dir, get_legacy_handoffs_dir, get_project_name  # type: ignore[no-redef]
```

- [ ] **Step 2: Add archive_name parameter to search_handoffs**

Change the function signature and the archive directory line:

```python
def search_handoffs(
    handoffs_dir: Path,
    query: str,
    *,
    regex: bool = False,
    skipped: list[dict] | None = None,
    archive_name: str = "archive",
) -> list[dict]:
```

Replace line 61 (`archive_dir = handoffs_dir / ".archive"`) with:

```python
    archive_dir = handoffs_dir / archive_name
```

- [ ] **Step 3: Add legacy fallback to main()**

After `results = search_handoffs(handoffs_dir, args.query, ...)`, before the return statement, add legacy fallback:

```python
    # Legacy fallback: check .claude/handoffs/ for pre-migration files
    legacy_warning = None
    try:
        legacy_dir = get_legacy_handoffs_dir()
        if legacy_dir.exists():
            legacy_results = search_handoffs(
                legacy_dir, args.query, regex=args.regex,
                skipped=skipped_files, archive_name=".archive",
            )
            if legacy_results:
                legacy_warning = (
                    "Found handoffs at legacy location `.claude/handoffs/`. "
                    "Run `/save` to migrate — the next save will write to `docs/handoffs/`."
                )
                results.extend(legacy_results)
                results.sort(key=lambda r: r["date"], reverse=True)
    except Exception:
        pass  # Legacy check is best-effort
```

Add `"legacy_warning": legacy_warning` to both the success and error JSON return dicts.

- [ ] **Step 4: Update test_search.py archive reference**

Replace in `test_searches_archive_subdirectory`:

```python
        archive = tmp_path / "archive"
```

Replace in `TestSearchCLI.test_end_to_end_json_output`:

```python
        archive = handoffs_dir / "archive"
```

- [ ] **Step 5: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_search.py -v`
Expected: All pass.

---

### Task 6: Update triage.py

**Files:**
- Modify: `scripts/triage.py`
- Modify: `tests/test_triage.py`

- [ ] **Step 1: Add legacy import**

Add `get_legacy_handoffs_dir` to both import blocks:

```python
    from scripts.project_paths import get_handoffs_dir, get_legacy_handoffs_dir
except ModuleNotFoundError:
    ...
    from scripts.project_paths import get_handoffs_dir, get_legacy_handoffs_dir  # type: ignore[no-redef]
```

- [ ] **Step 2: Add archive_name parameter to _scan_handoff_dirs**

Change line 256 from `.archive` to parameterized:

```python
def _scan_handoff_dirs(
    handoffs_dir: Path, *, archive_name: str = "archive",
) -> list[Path]:
    """Collect handoff files from active and archive directories.

    P1-3 fix: filters to files modified within the last _LOOKBACK_DAYS days.
    """
    cutoff = time.time() - (_LOOKBACK_DAYS * 86400)
    paths: list[Path] = []

    for search_dir in [handoffs_dir, handoffs_dir / archive_name]:
        if not search_dir.exists():
            continue
        for p in sorted(search_dir.glob("*.md")):
            try:
                if p.stat().st_mtime >= cutoff:
                    paths.append(p)
            except OSError as exc:
                warnings.warn(f"Cannot stat handoff file {p}: {exc}", stacklevel=2)
                continue
    return paths
```

- [ ] **Step 3: Add legacy fallback to generate_report**

After scanning the primary handoffs dir, add legacy scan:

```python
    # Legacy fallback: also scan .claude/handoffs/ for pre-migration files
    legacy_found = False
    try:
        legacy_dir = get_legacy_handoffs_dir()
        if legacy_dir.exists():
            for path in _scan_handoff_dirs(legacy_dir, archive_name=".archive"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    warnings.warn(f"Cannot read handoff file {path}: {exc}", stacklevel=2)
                    continue
                items, skipped = extract_handoff_items(text, path.name)
                if items:
                    legacy_found = True
                all_items.extend(items)
                total_skipped_prose += skipped
    except Exception:
        pass  # Legacy check is best-effort
```

Add `"legacy_warning"` to the return dict (update `TriageReport` TypedDict to include it as optional):

```python
class TriageReport(TypedDict, total=False):
    open_tickets: list[OpenTicket]
    orphaned_items: list[MatchResult]
    matched_items: list[MatchResult]
    match_counts: dict[str, int]
    skipped_prose_count: int
    legacy_warning: str | None
```

Actually, simpler: keep `TriageReport` as-is (total=True) and add the legacy_warning only in the return dict at the call site. Or: just include it in the JSON output in `main()`, not in `generate_report()`.

Simplest approach — add it in `main()` after calling `generate_report()`:

```python
    report = generate_report(args.tickets_dir, args.handoffs_dir)
    # Check for legacy handoffs
    try:
        legacy_dir = get_legacy_handoffs_dir()
        if legacy_dir.exists() and any(legacy_dir.glob("*.md")):
            report["legacy_warning"] = (
                "Found handoffs at legacy location `.claude/handoffs/`. "
                "Run `/save` to migrate — the next save will write to `docs/handoffs/`."
            )
    except Exception:
        pass
```

Wait, the `generate_report()` function is what scans handoff dirs. The legacy scanning should happen there, not in main(). Let me reconsider.

Actually, re-reading the spec:

> | `triage.py` | Checks both directories (primary then legacy) | Same as search |

The scanning should be in `generate_report()` since it's the function that scans directories. But the warning should be returned to the caller. Let me keep it simple:

In `generate_report()`, after scanning primary dir, also scan legacy dir. Return a `legacy_warning` field in the report dict.

For TypedDict compatibility, I'll add `legacy_warning` as a `NotRequired` field:

```python
class TriageReport(TypedDict):
    open_tickets: list[OpenTicket]
    orphaned_items: list[MatchResult]
    matched_items: list[MatchResult]
    match_counts: dict[str, int]
    skipped_prose_count: int
    legacy_warning: str | None
```

And initialize `legacy_warning = None` in the function, setting it if legacy files are found.

Actually, this changes the TypedDict which could break tests. Let me check. The test asserts:
```python
assert "open_tickets" in report
```

Adding a new field won't break existing tests. And the new field is always present (just `None` by default).

- [ ] **Step 4: Update test_triage.py archive references**

Replace `test_includes_archive`:

```python
    def test_includes_archive(self, tmp_path: Path) -> None:
        from scripts.triage import generate_report

        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()

        handoffs_dir = tmp_path / "handoffs"
        archive_dir = handoffs_dir / "archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "archived.md").write_text(HANDOFF_WITH_OPEN_QUESTIONS)

        report = generate_report(tickets_dir, handoffs_dir)
        # Should find items from archived handoff (all manual_review since no matching tickets)
        assert len(report["orphaned_items"]) > 0
```

- [ ] **Step 5: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_triage.py -v`
Expected: All pass.

---

### Task 7: Update test_distill.py

**Files:**
- Modify: `tests/test_distill.py`

- [ ] **Step 1: Replace .archive with archive at line 875**

Change:
```python
        path_b = tmp_path / ".archive" / "handoff.md"
```
To:
```python
        path_b = tmp_path / "archive" / "handoff.md"
```

- [ ] **Step 2: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py -v`
Expected: All pass.

---

### Task 8: Update skill files

**Files:**
- Modify: `skills/save/SKILL.md`
- Modify: `skills/load/SKILL.md`
- Modify: `skills/quicksave/SKILL.md`
- Modify: `skills/distill/SKILL.md`

All skill updates use bulk search-and-replace. After replacements, add git commit steps and update frontmatter.

- [ ] **Step 1: Update save/SKILL.md**

**Frontmatter:** Add `Bash` to `allowed-tools`:
```yaml
allowed-tools: Write, Read, Edit, Glob, Grep, Bash
```

**Path replacements (apply globally):**
- `.claude/handoffs/` → `docs/handoffs/`
- `.claude/handoffs` (without trailing slash in `ls` commands) → `docs/handoffs`

**Add auto_commit call:** After step 8 ("Write file"), add:

```markdown
8b. **Auto-commit the handoff:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn: "Handoff saved but not committed — <reason>". The file is already written; only the commit is skipped.
```

**Update verification:** Change `ls` commands to use `docs/handoffs`.

**Update troubleshooting:** Change path references to `docs/handoffs/`.

**Remove permission note:** The "Write access to `<project_root>/.claude/handoffs/`" constraint and the STOP about `.claude/handoffs/` not being writable should reference `docs/handoffs/` instead. The directory bootstrapping note: "If `docs/handoffs/` doesn't exist, create it with `mkdir -p`."

- [ ] **Step 2: Update load/SKILL.md**

**Frontmatter:** Add `Bash` to `allowed-tools`:
```yaml
allowed-tools: Write, Read, Edit, Glob, Grep, Bash
```

**Path replacements (apply globally):**
- `.claude/handoffs/.archive/` → `docs/handoffs/archive/`
- `.claude/handoffs/` → `docs/handoffs/`
- `.claude/handoffs` (in `ls` commands) → `docs/handoffs`
- `.archive/` (standalone references) → `archive/`

**Update Bash `ls` commands:** Change from:
```bash
ls "$(git rev-parse --show-toplevel)/.claude/handoffs"/*.md 2>/dev/null
```
To:
```bash
ls "$(git rev-parse --show-toplevel)/docs/handoffs"/*.md 2>/dev/null
```

**Add legacy fallback to procedure step 2:**
```markdown
   - If no output from primary location, check legacy location:
     1. `ls "$(git rev-parse --show-toplevel)/.claude/handoffs"/*.md 2>/dev/null`
     2. If found, report: "Found handoffs at legacy location `.claude/handoffs/`. Run `/save` to migrate — the next save will write to `docs/handoffs/`."
     3. Use the legacy file for this load
```

**Add auto_commit call after archive move (step 5):**
```markdown
5b. **Auto-commit the archive:**
   ```bash
   git mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" --staged "<archive_path>"
   ```
   If `git mv` fails (file is untracked — e.g., loaded from legacy `.claude/handoffs/`), fall back:
   ```bash
   mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" "<archive_path>"
   ```
   If the commit fails, warn: "Handoff archived but not committed — <reason>".
```

**Update Storage section:** Change retention references — remove "30 days active, 90 days archive", replace with "No auto-prune".

**Update Background Cleanup section:** Remove items 1-2 (prune handoffs/archives). Keep only item 3 (prune state files).

- [ ] **Step 3: Update quicksave/SKILL.md**

**Path replacements:**
- `.claude/handoffs/` → `docs/handoffs/`
- `.claude/handoffs` (in commands) → `docs/handoffs`

**Add auto_commit call:** After step 6 ("Write file"), add the same auto_commit step as save:
```markdown
6b. **Auto-commit the checkpoint:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn but continue.
```

**Note:** quicksave currently has no `allowed-tools` in frontmatter. Add:
```yaml
allowed-tools: Write, Read, Bash
```

- [ ] **Step 4: Update distill/SKILL.md**

**Path replacements only (no git additions):**
- `.claude/handoffs/` → `docs/handoffs/`
- `.claude/handoffs` (in commands) → `docs/handoffs`
- `.archive/` → `archive/`

Change the `ls` command in step 1:
```bash
ls -t "$(git rev-parse --show-toplevel)/docs/handoffs"/*.md | head -1
```

Change "skip `.archive/`" to "skip `archive/`".

Change example paths from `.claude/handoffs/` to `docs/handoffs/`.

- [ ] **Step 5: Verify skill files have no stale references**

Run: `grep -r '\.claude/handoffs' packages/plugins/handoff/skills/`
Expected: No matches.

Run: `grep -r '\.archive' packages/plugins/handoff/skills/`
Expected: Only the legacy fallback mention in load/SKILL.md.

---

### Task 9: Update reference docs

**Files:**
- Modify: `references/handoff-contract.md`
- Modify: `references/format-reference.md`

- [ ] **Step 1: Update handoff-contract.md**

**Path replacements:**
- `<project_root>/.claude/handoffs/.archive/` → `<project_root>/docs/handoffs/archive/`
- `<project_root>/.claude/handoffs/` → `<project_root>/docs/handoffs/`

**Retention table (lines 55-59):** Replace:
```markdown
| Location | Format | Retention |
|----------|--------|-----------|
| `<project_root>/docs/handoffs/` | `YYYY-MM-DD_HH-MM_<slug>.md` | No auto-prune |
| `<project_root>/docs/handoffs/archive/` | Same | No auto-prune |
| `~/.claude/.session-state/handoff-<UUID>` | Plain text (path) | 24 hours |
```

**Project Root section (line 69):** Change to:
```
The full project root path is used for storage resolution — handoff files live at `<project_root>/docs/handoffs/`.
```

**Write Permission section (line 77):** Change to:
```
If `<project_root>/docs/handoffs/` is not writable (or cannot be created), **STOP** and ask: "Can't write to <project_root>/docs/handoffs/. Where should I save this?"
```

- [ ] **Step 2: Update format-reference.md**

**Storage section (lines 58-62):**
```markdown
**Location:** `<project_root>/docs/handoffs/`

**Filename:** `YYYY-MM-DD_HH-MM_<title-slug>.md`

**Archive:** `<project_root>/docs/handoffs/archive/`
```

**Retention table (lines 66-70):**
```markdown
| Location | Retention |
|----------|-----------|
| Active handoffs (`<project_root>/docs/handoffs/`) | No auto-prune |
| Archived handoffs (`<project_root>/docs/handoffs/archive/`) | No auto-prune |
| State files (`~/.claude/.session-state/handoff-*`) | 24 hours |
```

**Example resumed_from (line 509):**
```
resumed_from: <project_root>/docs/handoffs/archive/2026-01-15_14-30_rate-limiting-system-architecture-and-initial-implementation.md
```

- [ ] **Step 3: Verify no stale references**

Run: `grep -r '\.claude/handoffs' packages/plugins/handoff/references/`
Expected: No matches.

Run: `grep -r '\.archive' packages/plugins/handoff/references/`
Expected: No matches.

Run: `grep -rE '30.day|90.day' packages/plugins/handoff/references/`
Expected: No matches (or only the state file 24-hour reference).

---

### Task 10: Update plugin docs

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README.md**

**Line 30 (hooks description):** Replace:
```
| **SessionStart** | `cleanup.py` | Silently prunes state files >24h. Always exits 0. |
```

**Lines 38 (save description):** Replace `.claude/handoffs/` with `docs/handoffs/`.

**Lines 50 (hooks table):** Replace:
```
| **SessionStart** | `cleanup.py` | Silently prunes state files >24h. Always exits 0. |
```

**Lines 74-82 (storage table):** Replace:
```markdown
| `<project_root>/docs/handoffs/` | Active handoffs and checkpoints | No auto-prune (git-tracked) |
| `<project_root>/docs/handoffs/archive/` | Archived handoffs (moved by `/load`) | No auto-prune (git-tracked) |
| `~/.claude/.session-state/handoff-<UUID>` | Chain protocol state files | 24 hours |
| `docs/tickets/` | Deferred work tickets | Permanent |
| `docs/learnings/learnings.md` | Distilled knowledge entries | Permanent |

Handoff files are git-tracked and auto-committed on create and archive. Use `git log --grep='docs(handoff):'` to view handoff history.
```

**Line 123 (example path):** Replace:
```
                                        (<project_root>/docs/handoffs/2026-03-09_14-30_feature-work.md)
```

**Lines 187-188 (architecture diagram):** Replace:
```
│  Active:  <project_root>/docs/handoffs/         │
│  Archive: <project_root>/docs/handoffs/archive/  │
```

**Add `auto_commit.py` to scripts table (line 57 area):**
```
| `auto_commit.py` | Narrow-scope git commit for handoff files | `/save`, `/load`, `/quicksave` skills |
```

**Line 273 (test count):** Update test count after all changes are complete.

- [ ] **Step 2: Update CHANGELOG.md**

Add new entry under `## [Unreleased]` at the top (before the existing Changed entry):

```markdown
### Changed
- **BREAKING:** Handoff storage moved from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`. Handoffs are now git-tracked and auto-committed. Archive renamed from `.archive/` to `archive/`. No auto-pruning — git history manages lifecycle.
- Cleanup hook (`cleanup.py`) no longer prunes handoff files — only session-state files (24h TTL)
- `is_handoff_path()` now matches `docs/handoffs/` (active and archived) instead of `.claude/handoffs/`
- `search.py` and `triage.py` check legacy `.claude/handoffs/` location as fallback

### Added
- `auto_commit.py` — testable git commit logic for handoff state changes
- `get_legacy_handoffs_dir()` in `project_paths.py` for fallback discovery
- `Bash` added to `allowed-tools` for save, load, quicksave skills
- Legacy fallback warning when handoffs found at old location
```

Remove the existing `### Changed` line about the previous migration (the `.claude/handoffs/` move):
```
- **BREAKING:** Handoff storage moved from global `~/.claude/handoffs/<project>/` to project-local `<project_root>/.claude/handoffs/`.
```

Replace with the new entry above (this supersedes it).

- [ ] **Step 3: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest tests/ -v`
Expected: All pass.

---

### Task 11: Update external files

**Files:**
- Modify: `<repo>/.gitignore`
- Modify: `<repo>/.claude/settings.json`
- Modify: `<repo>/.claude/hooks/test_require_gitflow.py`
- Modify: `<repo>/.claude/skills/changelog/SKILL.md`
- Modify: `<repo>/.claude/skills/changelog/references/entry-writing.md`

All paths below are relative to repo root (`/Users/jp/Projects/active/claude-code-tool-dev/`).

- [ ] **Step 1: Update .gitignore**

Remove line 39 (`.claude/handoffs/`):
```
# Session artifacts
.claude/handoffs/
```

Replace with:
```
# Session artifacts
```

(Just remove the `.claude/handoffs/` line — the comment can stay or be removed.)

- [ ] **Step 2: Update .claude/settings.json**

Remove `**/.claude/handoffs/**,` from the `GITFLOW_ALLOW_FILES` value. The `**/docs/**` pattern already covers `docs/handoffs/`.

Before:
```
"GITFLOW_ALLOW_FILES": "**/docs/**,...,**/.claude/handoffs/**,**/.claude/notes/**,..."
```

After:
```
"GITFLOW_ALLOW_FILES": "**/docs/**,...,**/.claude/notes/**,..."
```

(Remove the `**/.claude/handoffs/**,` segment, keeping the surrounding commas correct.)

- [ ] **Step 3: Update .claude/hooks/test_require_gitflow.py**

At line 1163-1165, change the test to use `docs/handoffs`:

```python
        """**/docs/handoffs/** should match nested handoff files."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "**/docs/handoffs/**")
        assert require_gitflow.is_file_allowed("/Users/jp/docs/handoffs/proj/file.md") is True
```

Wait — since `**/docs/**` already covers this, this test is actually testing a different pattern. The test should be updated to match whatever the new GITFLOW_ALLOW_FILES uses. Since we're removing `**/.claude/handoffs/**`, this test needs to either:
- Test `**/docs/**` matching handoff paths (but that's already covered by a `**/docs/**` test if one exists)
- Be removed if it's testing a pattern that no longer exists

Actually, looking at the test more carefully: it's testing the `is_file_allowed` function with a specific glob pattern. The test sets `GITFLOW_ALLOW_FILES` to `**/.claude/handoffs/**` and checks that a path under `.claude/handoffs/` matches. After migration, this specific test pattern is no longer used in production. Update the test to reflect the new setup:

```python
        """**/docs/** should match handoff files in docs/handoffs/."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "**/docs/**")
        assert require_gitflow.is_file_allowed("/Users/jp/Projects/myproject/docs/handoffs/file.md") is True
```

- [ ] **Step 4: Update .claude/skills/changelog/SKILL.md line 174**

Change:
```
The handoff archive lives at ~/.claude/handoffs/{project-name}/.archive/. Filenames follow YYYY-MM-DD_HH-MM_<title-slug>.md.
```
To:
```
The handoff archive lives at <project_root>/docs/handoffs/archive/. Filenames follow YYYY-MM-DD_HH-MM_<title-slug>.md.
```

- [ ] **Step 5: Update .claude/skills/changelog/references/entry-writing.md line 55**

Change:
```
ARCHIVE_DIR=~/.claude/handoffs/$PROJECT_NAME/.archive
```
To:
```
ARCHIVE_DIR=$(git rev-parse --show-toplevel)/docs/handoffs/archive
```

---

### Task 12: Verification and commit

- [ ] **Step 1: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest tests/ -v`
Expected: All 344+ tests pass (count may change due to added/removed tests).

- [ ] **Step 2: Verify no stale path references in plugin**

Run:
```bash
grep -r '\.claude/handoffs' packages/plugins/handoff/ --include='*.py' --include='*.md' | grep -v 'legacy' | grep -v 'get_legacy' | grep -v 'CHANGELOG' | grep -v '.archive'
```
Expected: No matches (only legacy fallback references should remain).

- [ ] **Step 3: Verify no stale references in references/**

Run:
```bash
grep -r '\.claude/handoffs' packages/plugins/handoff/references/
grep -r '\.archive' packages/plugins/handoff/references/
grep -rE '30.day|90.day' packages/plugins/handoff/references/
```
Expected: All three return no matches.

- [ ] **Step 4: Verify no stale references in external files**

Run:
```bash
grep '\.claude/handoffs' .gitignore .claude/settings.json
```
Expected: No matches.

- [ ] **Step 5: Lint**

Run: `cd packages/plugins/handoff && uv run ruff check . && uv run ruff format --check .`
Expected: No issues.

- [ ] **Step 6: Commit all changes atomically**

```bash
git add \
  packages/plugins/handoff/scripts/project_paths.py \
  packages/plugins/handoff/scripts/auto_commit.py \
  packages/plugins/handoff/scripts/cleanup.py \
  packages/plugins/handoff/scripts/quality_check.py \
  packages/plugins/handoff/scripts/search.py \
  packages/plugins/handoff/scripts/triage.py \
  packages/plugins/handoff/tests/test_project_paths.py \
  packages/plugins/handoff/tests/test_auto_commit.py \
  packages/plugins/handoff/tests/test_cleanup.py \
  packages/plugins/handoff/tests/test_quality_check.py \
  packages/plugins/handoff/tests/test_search.py \
  packages/plugins/handoff/tests/test_triage.py \
  packages/plugins/handoff/tests/test_distill.py \
  packages/plugins/handoff/skills/save/SKILL.md \
  packages/plugins/handoff/skills/load/SKILL.md \
  packages/plugins/handoff/skills/quicksave/SKILL.md \
  packages/plugins/handoff/skills/distill/SKILL.md \
  packages/plugins/handoff/references/handoff-contract.md \
  packages/plugins/handoff/references/format-reference.md \
  packages/plugins/handoff/README.md \
  packages/plugins/handoff/CHANGELOG.md \
  .gitignore \
  .claude/settings.json \
  .claude/hooks/test_require_gitflow.py \
  .claude/skills/changelog/SKILL.md \
  .claude/skills/changelog/references/entry-writing.md

git commit -m "feat(handoff): migrate storage to docs/handoffs with git tracking

Move handoff storage from .claude/handoffs/ (gitignored) to docs/handoffs/
(git-tracked). Auto-commit on every create and archive operation.

- Update path resolution: docs/handoffs/ primary, .claude/handoffs/ legacy
- Create auto_commit.py for testable narrow-scope git commits
- Strip handoff pruning from cleanup.py (git manages lifecycle)
- Update is_handoff_path() to match docs/handoffs/ pattern
- Add legacy fallback to search.py and triage.py
- Add Bash to allowed-tools for save/load/quicksave skills
- Update contract, format-reference, skills, and external configs
- Remove .claude/handoffs/ from .gitignore and GITFLOW_ALLOW_FILES

BREAKING: Handoff files now live at docs/handoffs/ instead of
.claude/handoffs/. Existing files at the old location are discovered
via legacy fallback in search/triage/load."
```
