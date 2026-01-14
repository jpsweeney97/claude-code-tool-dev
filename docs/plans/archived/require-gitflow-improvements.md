# require-gitflow.py Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve the require-gitflow.py hook with bug fixes, better UX, performance optimization, and comprehensive tests.

**Architecture:** Seven incremental improvements applied via TDD. Each improvement is independent except unit tests which verify all changes. Git context caching restructures internal functions but maintains the same public interface and behavior.

**Tech Stack:** Python 3.12, pytest, subprocess, dataclasses, regex

**Source:** Design document at `docs/plans/require-gitflow-improvements.md` (original analysis)

---

## Task 1: Create Test File Scaffold

**Files:**
- Create: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the test file with imports and fixtures**

```python
"""Unit tests for require-gitflow.py hook."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import hyphenated module using importlib
spec = importlib.util.spec_from_file_location(
    "require_gitflow",
    Path(__file__).parent / "require-gitflow.py"
)
require_gitflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(require_gitflow)

# Import functions for unit testing
suggest_branch_name = require_gitflow.suggest_branch_name
matches_valid_pattern = require_gitflow.matches_valid_pattern
get_protected_branches = require_gitflow.get_protected_branches
is_strict_mode = require_gitflow.is_strict_mode


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository on 'main' branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    (repo / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)
    return repo


def run_hook(cwd, tool_name="Edit", tool_input=None):
    """Helper to run the hook script with given input."""
    if tool_input is None:
        tool_input = {"file_path": "test.py"}
    input_data = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    return subprocess.run(
        [sys.executable, str(Path(__file__).parent / "require-gitflow.py")],
        input=input_data,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
```

**Step 2: Run test to verify imports work**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v --collect-only`
Expected: Collection shows fixtures, no import errors

**Step 3: Commit**

```bash
git add .claude/hooks/test_require_gitflow.py
git commit -m "test(gitflow): add test scaffold with fixtures"
```

---

## Task 2: Fix Frontmatter Timeout Bug

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:5`

**Step 1: Write the failing test**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestFrontmatter:
    def test_timeout_is_seconds_not_milliseconds(self):
        """Timeout should be 5 seconds, not 5000 (which would be 83 minutes)."""
        hook_path = Path(__file__).parent / "require-gitflow.py"
        content = hook_path.read_text()
        # Extract timeout from frontmatter
        import re
        match = re.search(r"# timeout: (\d+)", content)
        assert match, "timeout not found in frontmatter"
        timeout = int(match.group(1))
        assert timeout <= 60, f"timeout {timeout}s is too long (max 60s reasonable)"
        assert timeout >= 1, f"timeout {timeout}s is too short"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFrontmatter -v`
Expected: FAIL with "timeout 5000s is too long"

**Step 3: Fix the frontmatter**

In `.claude/hooks/require-gitflow.py`, change line 5:

```python
# timeout: 5
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFrontmatter -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(gitflow): correct timeout from 5000ms to 5s"
```

---

## Task 3: Add Case-Insensitive Branch Matching

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:79-81`
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing tests**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestMatchesValidPattern:
    @pytest.mark.parametrize("branch", [
        "feature/new-login",
        "feat/add-button",
        "release/1.0.0",
        "hotfix/critical-bug",
        "fix/null-pointer",
        "docs/readme-update",
        "refactor/cleanup",
        "dependabot/npm_and_yarn/lodash-4.17.21",
        "spike/new-architecture",
    ])
    def test_valid_patterns_lowercase(self, branch):
        assert matches_valid_pattern(branch)

    @pytest.mark.parametrize("branch", [
        "Feature/MixedCase",
        "FEATURE/UPPERCASE",
        "FIX/Bug-123",
        "Hotfix/Critical",
        "Release/1.0.0",
    ])
    def test_valid_patterns_case_insensitive(self, branch):
        """Branch patterns should match regardless of case."""
        assert matches_valid_pattern(branch)

    @pytest.mark.parametrize("branch", [
        "main",
        "master",
        "develop",
        "random-branch",
        "my-feature",
        "feature",  # Missing description
    ])
    def test_invalid_patterns(self, branch):
        assert not matches_valid_pattern(branch)
```

**Step 2: Run tests to verify case-insensitive tests fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestMatchesValidPattern::test_valid_patterns_case_insensitive -v`
Expected: FAIL (Feature/MixedCase etc. don't match)

**Step 3: Fix matches_valid_pattern to be case-insensitive**

In `.claude/hooks/require-gitflow.py`, update the function:

```python
def matches_valid_pattern(branch: str) -> bool:
    """Check if branch name matches any valid GitFlow pattern (case-insensitive)."""
    return any(re.match(pattern, branch.lower()) for pattern in VALID_PATTERNS)
```

**Step 4: Run all pattern tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestMatchesValidPattern -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(gitflow): make branch pattern matching case-insensitive"
```

---

## Task 4: Add File Path to Block Messages

**Files:**
- Modify: `.claude/hooks/require-gitflow.py` (add helper, update messages)
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestIntegration:
    def test_block_message_includes_file_path(self, temp_git_repo, monkeypatch):
        """Block message should mention the specific file being edited."""
        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo, tool_input={"file_path": "src/auth/login.py"})
        assert result.returncode == 2
        assert "src/auth/login.py" in result.stderr or "login.py" in result.stderr
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestIntegration::test_block_message_includes_file_path -v`
Expected: FAIL (file path not in error message)

**Step 3: Add file context helper and update messages**

In `.claude/hooks/require-gitflow.py`, add after line 37 (after imports):

```python
MAX_PATH_DISPLAY_LEN = 50


def get_file_context(tool_input: dict) -> str:
    """Extract file path from tool input for context in messages."""
    file_path = tool_input.get("file_path", "")
    if file_path:
        if len(file_path) > MAX_PATH_DISPLAY_LEN:
            file_path = "..." + file_path[-(MAX_PATH_DISPLAY_LEN - 3) :]
        return f"'{file_path}'"
    return "files"
```

Update `BLOCK_MESSAGE_MAIN` (around line 84):

```python
BLOCK_MESSAGE_MAIN = """Cannot edit {file} on '{branch}' — this is the production branch.

GitFlow requires working branches:

  For new features (branch from develop):
    git checkout develop
    git checkout -b feature/<name>

  For emergency fixes (branch from main):
    git checkout -b hotfix/<name>"""
```

Update `BLOCK_MESSAGE_DEVELOP`:

```python
BLOCK_MESSAGE_DEVELOP = """Cannot edit {file} on '{branch}' — this is the integration branch.

GitFlow requires working branches:

  For new features:
    git checkout -b feature/<name>

  For release preparation:
    git checkout -b release/<version>

  For bug fixes:
    git checkout -b fix/<name>"""
```

Update `main()` to extract file context and pass to messages (around line 337-348):

```python
        # Get file context for error messages
        tool_input = data.get("tool_input", {})
        file_context = get_file_context(tool_input)

        if branch_lower in {"main", "master"}:
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower == "develop":
            print(BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower in protected:
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestIntegration::test_block_message_includes_file_path -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): include file path in block messages"
```

---

## Task 5: Add Bypass Environment Variable

**Files:**
- Modify: `.claude/hooks/require-gitflow.py`
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing tests**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestBypass:
    def test_bypass_allows_edit_on_main(self, temp_git_repo, monkeypatch):
        """GITFLOW_BYPASS=1 should allow edits on protected branches."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_BYPASS", "1")
        result = run_hook(temp_git_repo)
        assert result.returncode == 0

    def test_bypass_shows_warning(self, temp_git_repo, monkeypatch):
        """Bypass should output a warning via systemMessage."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_BYPASS", "1")
        result = run_hook(temp_git_repo)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "Warning" in output.get("systemMessage", "")
        assert "bypassed" in output.get("systemMessage", "").lower()

    def test_bypass_disabled_by_default(self, temp_git_repo, monkeypatch):
        """Without GITFLOW_BYPASS, main branch should be blocked."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.delenv("GITFLOW_BYPASS", raising=False)
        result = run_hook(temp_git_repo)
        assert result.returncode == 2
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBypass -v`
Expected: FAIL (bypass not implemented)

**Step 3: Implement bypass check**

In `.claude/hooks/require-gitflow.py`, add after the imports (around line 37):

```python
BYPASS_ENV = "GITFLOW_BYPASS"


def check_bypass() -> bool:
    """Check if bypass is enabled. Returns True if should skip all checks."""
    bypass = os.environ.get(BYPASS_ENV, "").strip()
    if bypass == "1":
        output = {
            "systemMessage": (
                f"Warning: GitFlow enforcement bypassed via {BYPASS_ENV}=1\n"
                "All branch protection checks are disabled for this session."
            )
        }
        print(json.dumps(output))
        return True
    return False
```

In `main()`, add bypass check right after parsing JSON (around line 280):

```python
def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")

        # Only check Edit and Write tools
        if tool_name not in ("Edit", "Write"):
            sys.exit(0)

        # Check bypass FIRST (before any git operations)
        if check_bypass():
            sys.exit(0)

        # Not a git repo - allow (untracked project)
        ...
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBypass -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): add GITFLOW_BYPASS env var for emergency use"
```

---

## Task 6: Add Debug Logging

**Files:**
- Modify: `.claude/hooks/require-gitflow.py`
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestDebugLogging:
    def test_debug_mode_outputs_to_stderr(self, temp_git_repo, monkeypatch):
        """GITFLOW_DEBUG=1 should output debug info to stderr."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_DEBUG", "1")
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)
        assert result.returncode == 0
        assert "[GITFLOW]" in result.stderr

    def test_debug_mode_disabled_by_default(self, temp_git_repo, monkeypatch):
        """Without GITFLOW_DEBUG, stderr should be empty on success."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.delenv("GITFLOW_DEBUG", raising=False)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)
        assert result.returncode == 0
        assert "[GITFLOW]" not in result.stderr
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestDebugLogging -v`
Expected: FAIL (debug output not implemented)

**Step 3: Implement debug logging**

In `.claude/hooks/require-gitflow.py`, add after imports (around line 37):

```python
from datetime import datetime
from pathlib import Path

DEBUG = os.environ.get("GITFLOW_DEBUG", "") == "1"
LOG_FILE = Path.home() / ".claude/logs/gitflow-hook.log"


def log(level: str, message: str) -> None:
    """Log message to stderr (if debug) and log file."""
    if not DEBUG and level == "DEBUG":
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {message}"

    if DEBUG:
        print(f"[GITFLOW] {message}", file=sys.stderr)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # Fail silently
```

Add logging calls throughout `main()`:

After parsing JSON:
```python
        log("DEBUG", f"Hook invoked: tool={tool_name}")
```

After getting file context:
```python
        log("DEBUG", f"Checking edit to: {tool_input.get('file_path', 'unknown')}")
```

When blocking on protected branch:
```python
        if branch_lower in {"main", "master"}:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            ...
```

When allowing valid pattern:
```python
        if matches_valid_pattern(branch):
            log("DEBUG", f"Branch {branch} matches valid pattern, allowing")
            sys.exit(0)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestDebugLogging -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): add GITFLOW_DEBUG env var for troubleshooting"
```

---

## Task 7: Implement Git Context Caching

**Files:**
- Modify: `.claude/hooks/require-gitflow.py`
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestGitContext:
    def test_git_context_dataclass_exists(self):
        """GitContext dataclass should be defined."""
        assert hasattr(require_gitflow, "GitContext")

    def test_get_git_context_returns_context(self, temp_git_repo, monkeypatch):
        """get_git_context should return populated GitContext."""
        monkeypatch.chdir(temp_git_repo)
        get_git_context = require_gitflow.get_git_context
        ctx = get_git_context()
        assert ctx.is_repo is True
        assert ctx.has_commits is True
        assert ctx.branch == "main"
        assert ctx.is_detached is False

    def test_git_context_on_feature_branch(self, temp_git_repo, monkeypatch):
        """GitContext should report correct branch name."""
        monkeypatch.chdir(temp_git_repo)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_git_repo, capture_output=True)
        get_git_context = require_gitflow.get_git_context
        ctx = get_git_context()
        assert ctx.branch == "feature/test"

    def test_git_context_not_a_repo(self, tmp_path, monkeypatch):
        """GitContext should report is_repo=False outside git repo."""
        monkeypatch.chdir(tmp_path)
        get_git_context = require_gitflow.get_git_context
        ctx = get_git_context()
        assert ctx.is_repo is False
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitContext -v`
Expected: FAIL (GitContext not defined)

**Step 3: Implement GitContext dataclass and get_git_context**

In `.claude/hooks/require-gitflow.py`, add after imports:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitContext:
    """Cached git repository context."""
    is_repo: bool = False
    has_commits: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None
    is_detached: bool = False


def get_git_context() -> GitContext:
    """
    Gather all git context in minimal subprocess calls.

    Reduces 5 subprocess calls to 2-3 by combining checks.
    """
    ctx = GitContext()

    # Call 1: Is this a git repo?
    success, git_dir = run_git("rev-parse", "--git-dir")
    if not success:
        return ctx  # Not a git repo

    ctx.is_repo = True
    ctx.git_dir = git_dir.strip()

    # Call 2: Check for commits and get branch name
    # symbolic-ref fails on detached HEAD or no commits
    success, branch = run_git("symbolic-ref", "--short", "HEAD")
    if success and branch:
        ctx.branch = branch.strip()
        ctx.is_detached = False
        ctx.has_commits = True
    else:
        # Could be detached HEAD or no commits - check HEAD exists
        head_exists, _ = run_git("rev-parse", "--verify", "HEAD")
        ctx.has_commits = head_exists
        ctx.is_detached = head_exists  # If HEAD exists but no symbolic-ref, it's detached

    return ctx
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitContext -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): add GitContext dataclass for context caching"
```

---

## Task 8: Refactor main() to Use GitContext

**Files:**
- Modify: `.claude/hooks/require-gitflow.py`
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write integration tests to ensure behavior unchanged**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestIntegrationFull:
    def test_main_branch_blocks(self, temp_git_repo, monkeypatch):
        """Edit on main should be blocked."""
        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)
        assert result.returncode == 2
        assert "Cannot edit" in result.stderr

    def test_feature_branch_allows(self, temp_git_repo, monkeypatch):
        """Edit on feature branch should be allowed."""
        monkeypatch.chdir(temp_git_repo)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)
        assert result.returncode == 0

    def test_non_edit_tools_ignored(self, temp_git_repo, monkeypatch):
        """Non-Edit/Write tools should be allowed regardless of branch."""
        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo, tool_name="Bash", tool_input={"command": "ls"})
        assert result.returncode == 0

    def test_case_insensitive_branch_matching(self, temp_git_repo, monkeypatch):
        """Feature/MixedCase should be valid."""
        monkeypatch.chdir(temp_git_repo)
        subprocess.run(["git", "checkout", "-b", "Feature/MixedCase"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)
        assert result.returncode == 0

    def test_detached_head_warns_but_allows(self, temp_git_repo, monkeypatch):
        """Detached HEAD should warn but allow."""
        monkeypatch.chdir(temp_git_repo)
        subprocess.run(["git", "checkout", "HEAD~0"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "detached" in output.get("systemMessage", "").lower()

    def test_not_a_git_repo_allows(self, tmp_path, monkeypatch):
        """Non-git directory should allow edits."""
        monkeypatch.chdir(tmp_path)
        result = run_hook(tmp_path)
        assert result.returncode == 0
```

**Step 2: Run tests to verify current behavior**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestIntegrationFull -v`
Expected: All PASS (existing behavior)

**Step 3: Refactor main() to use GitContext**

Update `get_git_operation_state` signature:

```python
def get_git_operation_state(git_dir: str | None) -> str | None:
    """
    Detect if a git operation is in progress.

    Args:
        git_dir: Path to .git directory (from GitContext)

    Returns:
        'rebase' | 'merge' | 'cherry-pick' | 'bisect' | None
    """
    if not git_dir:
        return None

    # Check for various in-progress operations (unchanged logic)
    ...
```

Refactor `main()` to use GitContext:

```python
def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only check Edit and Write tools
        if tool_name not in ("Edit", "Write"):
            sys.exit(0)

        log("DEBUG", f"Hook invoked: tool={tool_name}")

        # Check bypass FIRST (before any git operations)
        if check_bypass():
            sys.exit(0)

        # Gather git context (2-3 subprocess calls instead of 5)
        ctx = get_git_context()

        # Not a git repo - allow (untracked project)
        if not ctx.is_repo:
            log("DEBUG", "Not a git repo, allowing")
            sys.exit(0)

        # New repo with no commits - allow (bootstrapping)
        if not ctx.has_commits:
            log("DEBUG", "No commits yet, allowing")
            sys.exit(0)

        # Get file context for error messages
        file_context = get_file_context(tool_input)
        log("DEBUG", f"Checking edit to: {tool_input.get('file_path', 'unknown')}")

        # Check for in-progress git operations FIRST
        operation = get_git_operation_state(ctx.git_dir)

        if operation == "rebase":
            log("INFO", "BLOCKED: Edit during rebase")
            print(BLOCK_MESSAGE_REBASE, file=sys.stderr)
            sys.exit(2)

        if operation == "bisect":
            log("INFO", "BLOCKED: Edit during bisect")
            print(BLOCK_MESSAGE_BISECT, file=sys.stderr)
            sys.exit(2)

        if operation == "merge":
            output = {"systemMessage": WARN_MESSAGE_MERGE}
            print(json.dumps(output))
            sys.exit(0)

        if operation == "cherry-pick":
            output = {"systemMessage": WARN_MESSAGE_CHERRY_PICK}
            print(json.dumps(output))
            sys.exit(0)

        # Check for detached HEAD
        if ctx.is_detached:
            log("DEBUG", "Detached HEAD, warning but allowing")
            output = {"systemMessage": WARN_MESSAGE_DETACHED}
            print(json.dumps(output))
            sys.exit(0)

        # Get current branch from context
        branch = ctx.branch

        # Couldn't determine branch - allow (unexpected state, fail open)
        if branch is None:
            log("DEBUG", "Could not determine branch, allowing")
            sys.exit(0)

        # Check if on protected branch (case-insensitive)
        protected = get_protected_branches()
        branch_lower = branch.lower()

        if branch_lower in {"main", "master"}:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower == "develop":
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            print(BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower in protected:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        # Check if matches valid GitFlow pattern
        if matches_valid_pattern(branch):
            log("DEBUG", f"Branch {branch} matches valid pattern, allowing")
            sys.exit(0)

        # Non-standard branch name
        suggested = suggest_branch_name(branch)

        if is_strict_mode():
            log("INFO", f"BLOCKED: Non-standard branch {branch} (strict mode)")
            print(
                BLOCK_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested),
                file=sys.stderr,
            )
            sys.exit(2)

        # Permissive mode: warn but allow
        log("DEBUG", f"Non-standard branch {branch}, warning but allowing")
        output = {
            "systemMessage": WARN_MESSAGE_NONSTANDARD.format(
                branch=branch, suggested=suggested
            ),
        }
        print(json.dumps(output))
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)
```

Remove now-unused functions: `is_git_repo()`, `has_commits()`, `is_detached_head()`, `get_git_dir()`, `get_current_branch()`.

**Step 4: Run all tests to verify behavior unchanged**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "refactor(gitflow): use GitContext to reduce subprocess calls"
```

---

## Task 9: Update Docstring

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:7-31`

**Step 1: Update the module docstring**

Replace the docstring at the top of `.claude/hooks/require-gitflow.py`:

```python
"""
Enforce GitFlow branching workflow before editing files.

Behavior:
  - BLOCK on protected branches (main, master, develop)
  - BLOCK/WARN based on git operation state (rebase, merge, cherry-pick, bisect)
  - ALLOW on valid GitFlow working branches (feature/*, release/*, etc.)
  - WARN but ALLOW on non-standard branch names (permissive mode)

Git operation handling:
  - rebase:      BLOCK — edits during rebase are risky
  - merge:       ALLOW — conflict resolution requires edits
  - cherry-pick: WARN  — may need edits for conflicts
  - bisect:      BLOCK — edits lost on next bisect step
  - detached:    WARN  — user explicitly checked out a commit

Configuration (environment variables):
  PROTECTED_BRANCHES    Comma-separated protected branches (default: main,master,develop)
  GITFLOW_STRICT        Set to "1" to block non-standard branch names (default: permissive)
  GITFLOW_BYPASS        Set to "1" to bypass all checks (emergency use only)
  GITFLOW_DEBUG         Set to "1" for debug output to stderr and log file

Log file: ~/.claude/logs/gitflow-hook.log

Exit codes:
  0 - Allow (valid branch or permissive warning)
  1 - Error (non-blocking)
  2 - Block (protected branch, rebase, or bisect)
"""
```

**Step 2: Run tests to ensure nothing broke**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add .claude/hooks/require-gitflow.py
git commit -m "docs(gitflow): update docstring with new env vars"
```

---

## Task 10: Add Remaining Unit Tests

**Files:**
- Modify: `.claude/hooks/test_require_gitflow.py`

**Step 1: Add tests for helper functions**

Add to `.claude/hooks/test_require_gitflow.py`:

```python
class TestSuggestBranchName:
    def test_simple_name(self):
        assert suggest_branch_name("my-feature") == "feature/my-feature"

    def test_spaces_converted(self):
        assert suggest_branch_name("My Feature Name") == "feature/my-feature-name"

    def test_uppercase_lowercased(self):
        assert suggest_branch_name("UPPERCASE") == "feature/uppercase"

    def test_empty_string(self):
        assert suggest_branch_name("") == "feature/my-feature"

    def test_only_dashes(self):
        assert suggest_branch_name("---") == "feature/my-feature"


class TestGetProtectedBranches:
    def test_default_branches(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PROTECTED_BRANCHES", None)
            result = get_protected_branches()
            assert result == {"main", "master", "develop"}

    def test_custom_branches(self):
        with patch.dict(os.environ, {"PROTECTED_BRANCHES": "main,staging"}):
            result = get_protected_branches()
            assert result == {"main", "staging"}


class TestIsStrictMode:
    def test_strict_enabled(self):
        with patch.dict(os.environ, {"GITFLOW_STRICT": "1"}):
            assert is_strict_mode() is True

    def test_strict_disabled(self):
        with patch.dict(os.environ, {"GITFLOW_STRICT": "0"}):
            assert is_strict_mode() is False

    def test_strict_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITFLOW_STRICT", None)
            assert is_strict_mode() is False


class TestGetFileContext:
    def test_normal_path(self):
        get_file_context = require_gitflow.get_file_context
        assert get_file_context({"file_path": "src/main.py"}) == "'src/main.py'"

    def test_long_path_truncated(self):
        get_file_context = require_gitflow.get_file_context
        long_path = "a" * 100 + "/file.py"
        result = get_file_context({"file_path": long_path})
        assert result.startswith("'...")
        assert len(result) <= 53  # 50 chars + quotes + ellipsis

    def test_no_path(self):
        get_file_context = require_gitflow.get_file_context
        assert get_file_context({}) == "files"
```

**Step 2: Run all tests**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add .claude/hooks/test_require_gitflow.py
git commit -m "test(gitflow): add comprehensive unit tests"
```

---

## Task 11: Final Verification

**Files:**
- None (verification only)

**Step 1: Run full test suite**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v --tb=short`
Expected: All tests PASS

**Step 2: Run hook manually to verify output**

```bash
cd /tmp && mkdir test-repo && cd test-repo
git init -b main
git config user.email "test@test.com"
git config user.name "Test"
echo "test" > file.txt && git add . && git commit -m "init"

# Test block on main
echo '{"tool_name": "Edit", "tool_input": {"file_path": "src/auth.py"}}' | python ~/.local/share/claude-code-tool-dev/.claude/hooks/require-gitflow.py
# Expected: exit 2, stderr contains "src/auth.py"

# Test allow on feature branch
git checkout -b feature/test
echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}' | python ~/.local/share/claude-code-tool-dev/.claude/hooks/require-gitflow.py
# Expected: exit 0

# Test bypass
git checkout main
GITFLOW_BYPASS=1 echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}' | python ~/.local/share/claude-code-tool-dev/.claude/hooks/require-gitflow.py
# Expected: exit 0, stdout contains systemMessage with "Warning"

# Cleanup
cd /tmp && rm -rf test-repo
```

**Step 3: Sync settings and test in Claude Code**

Run: `uv run scripts/sync-settings`

Start a new Claude Code session and test on main branch — should be blocked with file path in message.

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(gitflow): address any issues found in verification"
```

---

## Summary

| Task | Description | Commit Message |
|------|-------------|----------------|
| 1 | Test scaffold | `test(gitflow): add test scaffold with fixtures` |
| 2 | Fix timeout | `fix(gitflow): correct timeout from 5000ms to 5s` |
| 3 | Case-insensitive | `fix(gitflow): make branch pattern matching case-insensitive` |
| 4 | File path in messages | `feat(gitflow): include file path in block messages` |
| 5 | Bypass env var | `feat(gitflow): add GITFLOW_BYPASS env var for emergency use` |
| 6 | Debug logging | `feat(gitflow): add GITFLOW_DEBUG env var for troubleshooting` |
| 7 | GitContext dataclass | `feat(gitflow): add GitContext dataclass for context caching` |
| 8 | Refactor main() | `refactor(gitflow): use GitContext to reduce subprocess calls` |
| 9 | Update docstring | `docs(gitflow): update docstring with new env vars` |
| 10 | Remaining tests | `test(gitflow): add comprehensive unit tests` |
| 11 | Final verification | (verification only) |
