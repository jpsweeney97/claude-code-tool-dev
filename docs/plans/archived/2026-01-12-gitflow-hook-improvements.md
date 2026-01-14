# GitFlow Hook Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the require-gitflow.py hook with file allowlisting, additional git state detection, configurable logging, and improved testability through extracted decision logic.

**Architecture:** Add new environment variable configurations (GITFLOW_ALLOW_FILES, GITFLOW_LOG_FILE), extend GitContext dataclass with bare repo detection, extract decision logic into pure function for unit testing, and add comprehensive integration tests for git operation states.

**Tech Stack:** Python 3.12, pytest, subprocess for git operations, pathlib for glob matching

---

## Task 1: Configurable Log Path

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:49-50`
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test**

Add to `test_require_gitflow.py`:

```python
class TestConfigurableLogPath:
    def test_default_log_path(self):
        """Default log path should be ~/.claude/logs/gitflow-hook.log."""
        # Reimport to get fresh module state
        import importlib
        spec = importlib.util.spec_from_file_location(
            "require_gitflow_fresh",
            Path(__file__).parent / "require-gitflow.py"
        )
        fresh_module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITFLOW_LOG_FILE", None)
            spec.loader.exec_module(fresh_module)
            assert fresh_module.LOG_FILE == Path.home() / ".claude/logs/gitflow-hook.log"

    def test_custom_log_path(self, tmp_path):
        """GITFLOW_LOG_FILE should override default path."""
        custom_path = tmp_path / "custom.log"
        with patch.dict(os.environ, {"GITFLOW_LOG_FILE": str(custom_path)}):
            result = require_gitflow.get_log_file()
            assert result == custom_path

    def test_empty_env_uses_default(self):
        """Empty GITFLOW_LOG_FILE should use default."""
        with patch.dict(os.environ, {"GITFLOW_LOG_FILE": ""}):
            result = require_gitflow.get_log_file()
            assert result == Path.home() / ".claude/logs/gitflow-hook.log"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestConfigurableLogPath -v`
Expected: FAIL with "AttributeError: module has no attribute 'get_log_file'"

**Step 3: Write minimal implementation**

In `require-gitflow.py`, replace lines 49-50:

```python
def get_log_file() -> Path:
    """Get log file path from environment or default."""
    env_path = os.environ.get("GITFLOW_LOG_FILE", "").strip()
    if env_path:
        return Path(env_path)
    return Path.home() / ".claude/logs/gitflow-hook.log"


LOG_FILE = get_log_file()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestConfigurableLogPath -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): add configurable log path via GITFLOW_LOG_FILE"
```

---

## Task 2: Bare Repository Detection

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:313-345` (GitContext dataclass)
- Modify: `.claude/hooks/require-gitflow.py:347-400` (get_git_context function)
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing test for GitContext**

```python
class TestBareRepoDetection:
    def test_git_context_has_is_bare_field(self):
        """GitContext should have is_bare field."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", is_bare=True)
        assert ctx.is_bare is True

    def test_git_context_is_bare_default_false(self):
        """is_bare should default to False."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="main")
        assert ctx.is_bare is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBareRepoDetection::test_git_context_has_is_bare_field -v`
Expected: FAIL with "TypeError: unexpected keyword argument 'is_bare'"

**Step 3: Add is_bare to GitContext dataclass**

In `require-gitflow.py`, update GitContext:

```python
@dataclass(frozen=True)
class GitContext:
    """
    Cached git repository context.

    Invariants:
    - is_repo=False implies all other fields are at defaults
    - is_repo=True implies git_dir is not None
    - branch and is_detached are mutually exclusive
    - is_detached requires has_commits=True
    - is_bare=True implies is_repo=True
    """

    is_repo: bool = False
    is_bare: bool = False
    has_commits: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None
    is_detached: bool = False

    def __post_init__(self) -> None:
        if not self.is_repo:
            if self.has_commits or self.git_dir or self.branch or self.is_detached or self.is_bare:
                raise ValueError(
                    f"GitContext invariant violated: is_repo=False but other fields set: "
                    f"has_commits={self.has_commits}, git_dir={self.git_dir!r}, "
                    f"branch={self.branch!r}, is_detached={self.is_detached}, is_bare={self.is_bare}"
                )
        elif self.git_dir is None:
            raise ValueError("GitContext invariant violated: is_repo=True but git_dir is None")
        if self.is_detached and not self.has_commits:
            raise ValueError("GitContext invariant violated: is_detached=True requires has_commits=True")
        if self.branch is not None and self.is_detached:
            raise ValueError("GitContext invariant violated: branch and is_detached are mutually exclusive")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBareRepoDetection -v`
Expected: PASS

**Step 5: Write test for bare repo detection in get_git_context**

```python
    def test_get_git_context_detects_bare_repo(self, tmp_path, monkeypatch):
        """get_git_context should detect bare repositories."""
        bare_repo = tmp_path / "bare.git"
        subprocess.run(["git", "init", "--bare", str(bare_repo)], capture_output=True, check=True)

        monkeypatch.chdir(bare_repo)
        ctx = require_gitflow.get_git_context()

        assert ctx.is_repo is True
        assert ctx.is_bare is True

    def test_get_git_context_normal_repo_not_bare(self, temp_git_repo, monkeypatch):
        """Normal repos should have is_bare=False."""
        monkeypatch.chdir(temp_git_repo)
        ctx = require_gitflow.get_git_context()
        assert ctx.is_bare is False
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBareRepoDetection::test_get_git_context_detects_bare_repo -v`
Expected: FAIL with assertion error (is_bare will be False)

**Step 7: Implement bare detection in get_git_context**

In `get_git_context()`, after resolving git_dir and before checking commits:

```python
def get_git_context() -> GitContext:
    """Gather all git context in minimal subprocess calls."""
    # Call 1: Is this a git repo?
    success, git_dir = run_git("rev-parse", "--absolute-git-dir")
    if not success:
        success, git_dir = run_git("rev-parse", "--git-dir")
        if not success:
            return GitContext()

        if not os.path.isabs(git_dir):
            toplevel_ok, toplevel = run_git("rev-parse", "--show-toplevel")
            if toplevel_ok and toplevel:
                git_dir = os.path.join(toplevel.strip(), git_dir.strip())
            else:
                git_dir = os.path.abspath(git_dir.strip())

    resolved_git_dir = resolve_git_dir(git_dir.strip())

    # Check if bare repo BEFORE other checks
    success, is_bare_output = run_git("rev-parse", "--is-bare-repository")
    is_bare = success and is_bare_output.strip().lower() == "true"

    if is_bare:
        return GitContext(is_repo=True, is_bare=True, git_dir=resolved_git_dir)

    # Rest of existing logic for non-bare repos...
    commits_exist, _ = run_git("rev-parse", "--verify", "HEAD")
    success, branch_output = run_git("symbolic-ref", "--short", "HEAD")

    if success and branch_output:
        return GitContext(
            is_repo=True,
            git_dir=resolved_git_dir,
            has_commits=commits_exist,
            branch=branch_output.strip(),
            is_detached=False,
        )
    else:
        return GitContext(
            is_repo=True,
            git_dir=resolved_git_dir,
            has_commits=commits_exist,
            branch=None,
            is_detached=commits_exist,
        )
```

**Step 8: Run test to verify it passes**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBareRepoDetection -v`
Expected: PASS

**Step 9: Write integration test for bare repo allowing edits**

```python
    def test_bare_repo_allows_edits(self, tmp_path, monkeypatch):
        """Bare repos should allow edits (exit 0)."""
        bare_repo = tmp_path / "bare.git"
        subprocess.run(["git", "init", "--bare", str(bare_repo)], capture_output=True, check=True)

        monkeypatch.chdir(bare_repo)
        result = run_hook(bare_repo)

        assert result.returncode == 0
```

**Step 10: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestBareRepoDetection::test_bare_repo_allows_edits -v`
Expected: May fail depending on current main() behavior

**Step 11: Add bare repo handling to main()**

In `main()`, after the `ctx = get_git_context()` line (~line 456), add:

```python
        # Bare repo - allow (no working tree, edits are meaningless)
        if ctx.is_bare:
            log("DEBUG", "Bare repository, skipping checks")
            sys.exit(0)
```

**Step 12: Run all tests to verify nothing broke**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 13: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): detect and skip checks for bare repositories"
```

---

## Task 3: File Allowlist

**Files:**
- Modify: `.claude/hooks/require-gitflow.py` (add functions after get_protected_branches)
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write the failing unit tests**

```python
class TestFileAllowlist:
    def test_get_allowed_file_patterns_empty_by_default(self):
        """No patterns when GITFLOW_ALLOW_FILES is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITFLOW_ALLOW_FILES", None)
            result = require_gitflow.get_allowed_file_patterns()
            assert result == []

    def test_get_allowed_file_patterns_single(self, monkeypatch):
        """Single pattern parsing."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "package-lock.json")
        result = require_gitflow.get_allowed_file_patterns()
        assert result == ["package-lock.json"]

    def test_get_allowed_file_patterns_multiple(self, monkeypatch):
        """Multiple comma-separated patterns."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock, *.generated.*, version.txt")
        result = require_gitflow.get_allowed_file_patterns()
        assert result == ["*.lock", "*.generated.*", "version.txt"]

    def test_is_file_allowed_no_patterns(self):
        """No match when no patterns configured."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITFLOW_ALLOW_FILES", None)
            assert require_gitflow.is_file_allowed("any-file.py") is False

    def test_is_file_allowed_exact_match(self, monkeypatch):
        """Exact filename match."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "package-lock.json")
        assert require_gitflow.is_file_allowed("package-lock.json") is True
        assert require_gitflow.is_file_allowed("other.json") is False

    def test_is_file_allowed_glob_pattern(self, monkeypatch):
        """Glob pattern matching."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock")
        assert require_gitflow.is_file_allowed("package.lock") is True
        assert require_gitflow.is_file_allowed("yarn.lock") is True
        assert require_gitflow.is_file_allowed("package.json") is False

    def test_is_file_allowed_path_with_directory(self, monkeypatch):
        """Pattern should match against full path."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock")
        assert require_gitflow.is_file_allowed("src/deps/package.lock") is True
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFileAllowlist -v`
Expected: FAIL with "AttributeError: module has no attribute 'get_allowed_file_patterns'"

**Step 3: Implement allowlist functions**

Add after `get_protected_branches()` in require-gitflow.py:

```python
def get_allowed_file_patterns() -> list[str]:
    """Get file patterns that bypass protected branch checks."""
    env_value = os.environ.get("GITFLOW_ALLOW_FILES", "")
    return [p.strip() for p in env_value.split(",") if p.strip()]


def is_file_allowed(file_path: str) -> bool:
    """Check if file matches any allowlist pattern."""
    patterns = get_allowed_file_patterns()
    if not patterns:
        return False
    path = Path(file_path)
    return any(path.match(pattern) for pattern in patterns)
```

**Step 4: Run unit tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFileAllowlist -v`
Expected: PASS

**Step 5: Write integration test**

```python
    def test_allowlist_bypasses_protected_branch(self, temp_git_repo, monkeypatch):
        """Allowed files can be edited on protected main branch."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock")
        result = run_hook(temp_git_repo, tool_input={"file_path": "package.lock"})
        assert result.returncode == 0

    def test_non_matching_file_still_blocked(self, temp_git_repo, monkeypatch):
        """Non-matching files still blocked on protected branch."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock")
        result = run_hook(temp_git_repo, tool_input={"file_path": "src/main.py"})
        assert result.returncode == 2
```

**Step 6: Run integration test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFileAllowlist::test_allowlist_bypasses_protected_branch -v`
Expected: FAIL (returncode == 2 instead of 0)

**Step 7: Add allowlist check to main()**

In `main()`, after the no-commits check and before operation checks (~line 476), add:

```python
        # Check file allowlist (before protected branch checks)
        file_path = tool_input.get("file_path", "")
        if is_file_allowed(file_path):
            log("DEBUG", f"File matches allowlist, bypassing protection: {file_path}")
            sys.exit(0)
```

**Step 8: Run integration tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestFileAllowlist -v`
Expected: PASS

**Step 9: Run all tests**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 10: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): add file allowlist via GITFLOW_ALLOW_FILES"
```

---

## Task 4: Stash Conflict Detection

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:402-436` (get_git_operation_state)
- Modify: `.claude/hooks/require-gitflow.py` (add WARN_MESSAGE_STASH)
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write unit test for stash-apply detection**

```python
class TestStashConflictDetection:
    def test_get_git_operation_state_detects_stash_apply(self, tmp_path):
        """AUTO_MERGE file indicates stash-apply conflict."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "AUTO_MERGE").touch()

        result = require_gitflow.get_git_operation_state(str(git_dir))
        assert result == "stash-apply"

    def test_merge_takes_precedence_over_auto_merge(self, tmp_path):
        """MERGE_HEAD should take precedence over AUTO_MERGE."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "MERGE_HEAD").touch()
        (git_dir / "AUTO_MERGE").touch()

        result = require_gitflow.get_git_operation_state(str(git_dir))
        assert result == "merge"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestStashConflictDetection::test_get_git_operation_state_detects_stash_apply -v`
Expected: FAIL (returns None instead of "stash-apply")

**Step 3: Add stash-apply detection to get_git_operation_state**

In `get_git_operation_state()`, add AFTER the merge check but BEFORE returning None:

```python
def get_git_operation_state(git_dir: str | None) -> str | None:
    """Detect if a git operation is in progress."""
    if not git_dir:
        return None

    # Rebase (interactive or regular)
    if os.path.exists(os.path.join(git_dir, "rebase-merge")):
        return "rebase"
    if os.path.exists(os.path.join(git_dir, "rebase-apply")):
        return "rebase"

    # Merge
    if os.path.exists(os.path.join(git_dir, "MERGE_HEAD")):
        return "merge"

    # Cherry-pick
    if os.path.exists(os.path.join(git_dir, "CHERRY_PICK_HEAD")):
        return "cherry-pick"

    # Bisect
    if os.path.exists(os.path.join(git_dir, "BISECT_LOG")):
        return "bisect"

    # Stash apply conflict (AUTO_MERGE exists without merge in progress)
    if os.path.exists(os.path.join(git_dir, "AUTO_MERGE")):
        return "stash-apply"

    return None
```

**Step 4: Run unit tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestStashConflictDetection -v`
Expected: PASS

**Step 5: Add warning message**

Add after `WARN_MESSAGE_DETACHED`:

```python
WARN_MESSAGE_STASH = """You're resolving a stash apply conflict.

Edits are expected during stash conflict resolution. After resolving:
  git add <resolved-files>
  git stash drop               # if you used 'stash pop'

To abort:
  git checkout -- <conflicted-files>
  git stash                    # your changes are still in the stash"""
```

**Step 6: Add stash-apply handling to main()**

In `main()`, after the cherry-pick handling (~line 497), add:

```python
        if operation == "stash-apply":
            log("INFO", "Stash-apply conflict detected, allowing edits")
            output = {"systemMessage": WARN_MESSAGE_STASH}
            print(json.dumps(output))
            sys.exit(0)
```

**Step 7: Write integration test**

```python
    def test_stash_apply_conflict_warns(self, temp_git_repo, monkeypatch):
        """Stash apply with conflict should warn but allow edits."""
        # Create and stash a change
        (temp_git_repo / "file.txt").write_text("stashed change")
        subprocess.run(["git", "stash"], cwd=temp_git_repo, capture_output=True, check=True)

        # Create conflicting committed change
        (temp_git_repo / "file.txt").write_text("committed change")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "conflict"], cwd=temp_git_repo, capture_output=True, check=True)

        # Switch to feature branch and pop stash (will conflict)
        subprocess.run(["git", "checkout", "-b", "feature/stash-test"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "stash", "pop"], cwd=temp_git_repo, capture_output=True)

        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "stash" in output.get("systemMessage", "").lower()
```

**Step 8: Run integration test**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestStashConflictDetection::test_stash_apply_conflict_warns -v`
Expected: PASS

**Step 9: Run all tests**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 10: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): detect and warn on stash apply conflicts"
```

---

## Task 5: Integration Tests for Git Operations

**Files:**
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write rebase integration test**

```python
class TestGitOperationStates:
    """Integration tests for git operation state detection and handling."""

    def test_rebase_in_progress_blocks(self, temp_git_repo, monkeypatch):
        """Rebase in progress should block edits with exit 2."""
        # Create divergent history
        subprocess.run(["git", "checkout", "-b", "feature/rebase-test"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "file.txt").write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feature commit"], cwd=temp_git_repo, capture_output=True, check=True)

        subprocess.run(["git", "checkout", "main"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "file.txt").write_text("main content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "main commit"], cwd=temp_git_repo, capture_output=True, check=True)

        # Start rebase (will conflict)
        subprocess.run(["git", "checkout", "feature/rebase-test"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "rebase", "main"], cwd=temp_git_repo, capture_output=True)

        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert "rebase" in result.stderr.lower()
```

**Step 2: Run test to verify it passes (existing functionality)**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitOperationStates::test_rebase_in_progress_blocks -v`
Expected: PASS

**Step 3: Write bisect integration test**

```python
    def test_bisect_in_progress_blocks(self, temp_git_repo, monkeypatch):
        """Bisect in progress should block edits with exit 2."""
        # Create multiple commits for bisect
        for i in range(5):
            (temp_git_repo / "file.txt").write_text(f"commit {i}")
            subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", f"commit {i}"], cwd=temp_git_repo, capture_output=True, check=True)

        # Start bisect
        subprocess.run(["git", "bisect", "start"], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "bisect", "bad", "HEAD"], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "bisect", "good", "HEAD~4"], cwd=temp_git_repo, capture_output=True, check=True)

        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert "bisect" in result.stderr.lower()
```

**Step 4: Run bisect test**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitOperationStates::test_bisect_in_progress_blocks -v`
Expected: PASS

**Step 5: Write cherry-pick integration test**

```python
    def test_cherry_pick_conflict_warns(self, temp_git_repo, monkeypatch):
        """Cherry-pick with conflict should warn but allow edits (exit 0)."""
        # Create commit on feature branch
        subprocess.run(["git", "checkout", "-b", "feature/cp-source"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "new.txt").write_text("source content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add new file"], cwd=temp_git_repo, capture_output=True, check=True)
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=temp_git_repo, capture_output=True, text=True).stdout.strip()

        # Create conflicting commit on another branch
        subprocess.run(["git", "checkout", "main"], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", "feature/cp-target"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "new.txt").write_text("target content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "different content"], cwd=temp_git_repo, capture_output=True, check=True)

        # Cherry-pick (will conflict)
        subprocess.run(["git", "cherry-pick", commit], cwd=temp_git_repo, capture_output=True)

        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "cherry-pick" in output.get("systemMessage", "").lower()
```

**Step 6: Run cherry-pick test**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitOperationStates::test_cherry_pick_conflict_warns -v`
Expected: PASS

**Step 7: Run all git operation tests**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestGitOperationStates -v`
Expected: All PASS

**Step 8: Run full test suite**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 9: Commit**

```bash
git add .claude/hooks/test_require_gitflow.py
git commit -m "test(gitflow): add integration tests for rebase/bisect/cherry-pick states"
```

---

## Task 6: Extract Decision Logic

**Files:**
- Modify: `.claude/hooks/require-gitflow.py` (add Decision enum, HookDecision dataclass, evaluate_gitflow_rules function)
- Modify: `.claude/hooks/require-gitflow.py` (refactor main())
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Add Decision enum and HookDecision dataclass**

Add after GitContext dataclass:

```python
from enum import Enum


class Decision(Enum):
    """Decision types for gitflow evaluation."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True)
class HookDecision:
    """Result of evaluating gitflow rules."""
    decision: Decision
    message: str | None = None
    exit_code: int = 0
    output_json: dict | None = None
```

**Step 2: Write failing tests for evaluate_gitflow_rules**

```python
class TestEvaluateGitflowRules:
    """Unit tests for the extracted decision logic."""

    def test_not_a_repo_allows(self):
        """Not a git repo should allow."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=False)
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", None)
        assert decision.decision == require_gitflow.Decision.ALLOW
        assert decision.exit_code == 0

    def test_bare_repo_allows(self):
        """Bare repo should allow."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, is_bare=True, git_dir="/path")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", None)
        assert decision.decision == require_gitflow.Decision.ALLOW

    def test_rebase_blocks(self):
        """Rebase in progress should block."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="feature/x")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", "rebase")
        assert decision.decision == require_gitflow.Decision.BLOCK
        assert decision.exit_code == 2
        assert "rebase" in decision.message.lower()

    def test_bisect_blocks(self):
        """Bisect in progress should block."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="feature/x")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", "bisect")
        assert decision.decision == require_gitflow.Decision.BLOCK
        assert decision.exit_code == 2

    def test_merge_warns(self):
        """Merge in progress should warn but allow."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="feature/x")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", "merge")
        assert decision.decision == require_gitflow.Decision.WARN
        assert decision.exit_code == 0
        assert decision.output_json is not None

    def test_protected_branch_blocks(self):
        """Protected branch should block."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="main")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", None)
        assert decision.decision == require_gitflow.Decision.BLOCK
        assert decision.exit_code == 2

    def test_feature_branch_allows(self):
        """Feature branch should allow."""
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="feature/test")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "test.py", None)
        assert decision.decision == require_gitflow.Decision.ALLOW

    def test_allowlisted_file_on_protected_allows(self, monkeypatch):
        """Allowlisted file on protected branch should allow."""
        monkeypatch.setenv("GITFLOW_ALLOW_FILES", "*.lock")
        GitContext = require_gitflow.GitContext
        ctx = GitContext(is_repo=True, git_dir="/path", has_commits=True, branch="main")
        decision = require_gitflow.evaluate_gitflow_rules(ctx, "package.lock", None)
        assert decision.decision == require_gitflow.Decision.ALLOW
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestEvaluateGitflowRules -v`
Expected: FAIL with "AttributeError: module has no attribute 'evaluate_gitflow_rules'"

**Step 4: Implement evaluate_gitflow_rules function**

Add after HookDecision dataclass:

```python
def evaluate_gitflow_rules(
    ctx: GitContext,
    file_path: str,
    operation: str | None,
) -> HookDecision:
    """
    Evaluate gitflow rules and return decision.

    Pure function - no side effects, no I/O.
    """
    # Not a repo
    if not ctx.is_repo:
        return HookDecision(Decision.ALLOW)

    # Bare repo
    if ctx.is_bare:
        return HookDecision(Decision.ALLOW)

    # No commits yet
    if not ctx.has_commits:
        return HookDecision(
            Decision.ALLOW,
            output_json={
                "systemMessage": "Note: This repository has no commits yet. GitFlow checks are bypassed during initial setup."
            }
        )

    # File allowlist check
    if is_file_allowed(file_path):
        return HookDecision(Decision.ALLOW)

    # Operation checks
    if operation == "rebase":
        return HookDecision(Decision.BLOCK, BLOCK_MESSAGE_REBASE, exit_code=2)
    if operation == "bisect":
        return HookDecision(Decision.BLOCK, BLOCK_MESSAGE_BISECT, exit_code=2)
    if operation == "merge":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_MERGE})
    if operation == "cherry-pick":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_CHERRY_PICK})
    if operation == "stash-apply":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_STASH})

    # Detached HEAD
    if ctx.is_detached:
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_DETACHED})

    # Branch checks
    branch = ctx.branch
    if branch is None:
        return HookDecision(Decision.ALLOW)

    protected = get_protected_branches()
    branch_lower = branch.lower()

    if branch_lower in protected:
        file_context = get_file_context({"file_path": file_path})
        if branch_lower in {"main", "master"}:
            msg = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)
        elif branch_lower == "develop":
            msg = BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context)
        else:
            msg = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)
        return HookDecision(Decision.BLOCK, msg, exit_code=2)

    if matches_valid_pattern(branch):
        return HookDecision(Decision.ALLOW)

    # Non-standard branch
    suggested = suggest_branch_name(branch)
    if is_strict_mode():
        return HookDecision(
            Decision.BLOCK,
            BLOCK_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested),
            exit_code=2
        )

    return HookDecision(
        Decision.WARN,
        output_json={
            "systemMessage": WARN_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested)
        }
    )
```

**Step 5: Run unit tests to verify they pass**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py::TestEvaluateGitflowRules -v`
Expected: PASS

**Step 6: Refactor main() to use evaluate_gitflow_rules**

Replace the decision logic in main() with:

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

        # Gather git context
        ctx = get_git_context()
        file_path = tool_input.get("file_path", "")
        operation = get_git_operation_state(ctx.git_dir) if ctx.is_repo else None

        log("DEBUG", f"Checking edit to: {file_path}")

        # Evaluate gitflow rules
        decision = evaluate_gitflow_rules(ctx, file_path, operation)

        # Log decision
        log("DEBUG", f"Decision: {decision.decision.value}")

        # Execute decision
        if decision.output_json:
            print(json.dumps(decision.output_json))

        if decision.message and decision.decision == Decision.BLOCK:
            log("INFO", f"BLOCKED: {decision.message[:50]}...")
            print(decision.message, file=sys.stderr)

        sys.exit(decision.exit_code)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        import traceback

        tool_info = (
            f"tool={data.get('tool_name', 'unknown')}" if "data" in dir() else "before parsing"
        )
        log("ERROR", f"Unexpected error ({tool_info}): {type(e).__name__}: {e}")
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print(f"Hook error ({tool_info}): {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
```

**Step 7: Run all tests to verify refactoring is correct**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "refactor(gitflow): extract decision logic to evaluate_gitflow_rules"
```

---

## Task 7: Update Module Docstring

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:7-35` (docstring)

**Step 1: Update docstring with new env vars**

```python
"""
Enforce GitFlow branching workflow before editing files.

Behavior:
  - BLOCK on protected branches (main, master, develop)
  - BLOCK/WARN based on git operation state (rebase, merge, cherry-pick, bisect, stash-apply)
  - ALLOW on valid GitFlow working branches (feature/*, release/*, etc.)
  - WARN but ALLOW on non-standard branch names (permissive mode)
  - ALLOW bare repositories (no working tree)

Git operation handling:
  - rebase:      BLOCK — edits during rebase are risky
  - merge:       ALLOW — conflict resolution requires edits
  - cherry-pick: WARN  — may need edits for conflicts
  - bisect:      BLOCK — edits lost on next bisect step
  - stash-apply: WARN  — may need edits for conflict resolution
  - detached:    WARN  — user explicitly checked out a commit

Configuration (environment variables):
  PROTECTED_BRANCHES    Comma-separated protected branches (default: main,master,develop)
  GITFLOW_STRICT        Set to "1" to block non-standard branch names (default: permissive)
  GITFLOW_BYPASS        Set to "1" to bypass all checks (emergency use only)
  GITFLOW_DEBUG         Set to "1" for debug output to stderr and log file
  GITFLOW_LOG_FILE      Custom path for log file (default: ~/.claude/logs/gitflow-hook.log)
  GITFLOW_ALLOW_FILES   Comma-separated glob patterns for files to allow on protected branches

Log file: ~/.claude/logs/gitflow-hook.log (or GITFLOW_LOG_FILE)

Exit codes:
  0 - Allow (valid branch, allowlisted file, or permissive warning)
  1 - Error (non-blocking)
  2 - Block (protected branch, rebase, or bisect)
"""
```

**Step 2: Commit**

```bash
git add .claude/hooks/require-gitflow.py
git commit -m "docs(gitflow): update docstring with new env vars and behaviors"
```

---

## Task 8: Final Verification

**Step 1: Run full test suite**

Run: `uv run pytest .claude/hooks/test_require_gitflow.py -v --tb=short`
Expected: All PASS

**Step 2: Test manually with debug output**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
export GITFLOW_DEBUG=1
echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}' | python .claude/hooks/require-gitflow.py
echo "Exit code: $?"
```

**Step 3: Test file allowlist manually**

```bash
export GITFLOW_ALLOW_FILES="*.lock"
echo '{"tool_name": "Edit", "tool_input": {"file_path": "package.lock"}}' | python .claude/hooks/require-gitflow.py
echo "Exit code: $?"  # Should be 0
```

**Step 4: Sync settings**

Run: `uv run scripts/sync-settings`

**Step 5: Commit any remaining changes**

```bash
git add -A
git status
# If any unstaged changes:
git commit -m "chore(gitflow): final cleanup"
```

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `.claude/hooks/require-gitflow.py` | Modify | All 6 improvements |
| `.claude/hooks/test_require_gitflow.py` | Modify | New test classes for all improvements |
| `docs/plans/2026-01-12-gitflow-hook-improvements.md` | Create | This plan document |

---

## New Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GITFLOW_LOG_FILE` | path | `~/.claude/logs/gitflow-hook.log` | Custom log file path |
| `GITFLOW_ALLOW_FILES` | glob patterns | empty | Files to allow on protected branches |

---

## Verification Commands

```bash
# Run all tests
uv run pytest .claude/hooks/test_require_gitflow.py -v

# Run specific test class
uv run pytest .claude/hooks/test_require_gitflow.py::TestFileAllowlist -v

# Run with coverage
uv run pytest .claude/hooks/test_require_gitflow.py --cov=.claude/hooks/require-gitflow --cov-report=term-missing

# Manual test
echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}' | python .claude/hooks/require-gitflow.py
```
