# require-gitflow.py Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 6 issues in require-gitflow.py identified during code review, focusing on git_dir path resolution bug and improving robustness.

**Architecture:** Fix critical path resolution bug first, then add worktree support, then batch cleanup items (regex precompilation, unified protected-branch logic, improved messaging).

**Tech Stack:** Python 3.12, pytest, subprocess, dataclasses

---

## Task 1: Fix git_dir Relative Path Bug

The critical bug: `git rev-parse --git-dir` returns `.git` (relative) when run from repo root. If the hook's working directory differs from the repo root, `os.path.exists(os.path.join(git_dir, ...))` fails silently.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:283-312` (get_git_context function)
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write failing test for subdirectory detection**

Add to `test_require_gitflow.py`:

```python
class TestSubdirectoryDetection:
    def test_operation_detection_from_subdirectory(self, temp_git_repo, monkeypatch):
        """Operation detection should work when invoked from subdirectory."""
        # Create subdirectory
        subdir = temp_git_repo / "src" / "deep"
        subdir.mkdir(parents=True)

        # Start a merge that will conflict
        subprocess.run(["git", "checkout", "-b", "feature/a"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "conflict.txt").write_text("feature a content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feature a"], cwd=temp_git_repo, capture_output=True, check=True)

        subprocess.run(["git", "checkout", "main"], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", "feature/b"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "conflict.txt").write_text("feature b content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feature b"], cwd=temp_git_repo, capture_output=True, check=True)

        # Merge that creates conflict
        subprocess.run(["git", "merge", "feature/a"], cwd=temp_git_repo, capture_output=True)

        # Change to subdirectory and run hook
        monkeypatch.chdir(subdir)

        # Hook should detect merge-in-progress even from subdirectory
        result = run_hook(subdir)
        assert result.returncode == 0  # Merge allows edits
        output = json.loads(result.stdout)
        assert "merge" in output.get("systemMessage", "").lower()

    def test_git_context_from_subdirectory(self, temp_git_repo, monkeypatch):
        """GitContext.git_dir should be absolute path even from subdirectory."""
        subdir = temp_git_repo / "src" / "nested"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        get_git_context = require_gitflow.get_git_context
        ctx = get_git_context()

        assert ctx.is_repo is True
        assert ctx.git_dir is not None
        assert os.path.isabs(ctx.git_dir), f"git_dir should be absolute, got: {ctx.git_dir}"
        assert os.path.isdir(ctx.git_dir), f"git_dir should exist: {ctx.git_dir}"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestSubdirectoryDetection -v
```

Expected: FAIL - git_dir is `.git` not absolute path

**Step 3: Fix get_git_context to resolve absolute path**

Modify `get_git_context()` in `require-gitflow.py`:

```python
def get_git_context() -> GitContext:
    """
    Gather all git context in minimal subprocess calls.

    Reduces 5 subprocess calls to 2-3 by combining checks.
    """
    ctx = GitContext()

    # Call 1: Get git directory as absolute path
    # Use --absolute-git-dir if available (Git 2.13+), fallback to manual resolution
    success, git_dir = run_git("rev-parse", "--absolute-git-dir")
    if not success:
        # Fallback for older Git: get git-dir and toplevel, then resolve
        success, git_dir = run_git("rev-parse", "--git-dir")
        if not success:
            return ctx  # Not a git repo

        # If relative (e.g., ".git"), resolve against repo root
        if not os.path.isabs(git_dir):
            toplevel_ok, toplevel = run_git("rev-parse", "--show-toplevel")
            if toplevel_ok and toplevel:
                git_dir = os.path.join(toplevel.strip(), git_dir.strip())
            else:
                # Last resort: resolve against cwd
                git_dir = os.path.abspath(git_dir.strip())

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

**Step 4: Run tests to verify fix**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestSubdirectoryDetection -v
uv run pytest .claude/hooks/test_require_gitflow.py -v  # All tests
```

Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "fix(gitflow): resolve git_dir to absolute path for subdirectory support"
```

---

## Task 2: Handle Worktrees and Submodules (gitdir file indirection)

In linked worktrees and submodules, `.git` is a file containing `gitdir: /path/to/actual/.git`. The current code treats it as a directory.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:315-349` (get_git_operation_state function)
- Test: `.claude/hooks/test_require_gitflow.py`

**Step 1: Write failing test for worktree gitdir file**

```python
class TestWorktreeSupport:
    def test_gitdir_file_indirection(self, temp_git_repo, tmp_path, monkeypatch):
        """Operation detection should work in linked worktrees where .git is a file."""
        # Create a worktree
        worktree_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", "feature/worktree"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True
        )

        # Start a rebase in the worktree
        (worktree_path / "new.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=worktree_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "new"], cwd=worktree_path, capture_output=True, check=True)

        # Create conflict for rebase
        subprocess.run(["git", "checkout", "main"], cwd=worktree_path, capture_output=True)
        (worktree_path / "new.txt").write_text("conflicting")
        subprocess.run(["git", "add", "."], cwd=worktree_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "conflict"], cwd=worktree_path, capture_output=True, check=True)

        subprocess.run(["git", "checkout", "feature/worktree"], cwd=worktree_path, capture_output=True)
        subprocess.run(["git", "rebase", "main"], cwd=worktree_path, capture_output=True)  # Will conflict

        monkeypatch.chdir(worktree_path)

        # Hook should detect rebase in worktree
        result = run_hook(worktree_path)
        assert result.returncode == 2  # Rebase blocks
        assert "rebase" in result.stderr.lower()

    def test_resolve_gitdir_file(self):
        """resolve_git_dir should follow gitdir: file indirection."""
        resolve_git_dir = require_gitflow.resolve_git_dir

        # Mock a gitdir file
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            git_file = Path(tmpdir) / ".git"
            actual_git = Path(tmpdir) / "actual_git_dir"
            actual_git.mkdir()

            git_file.write_text(f"gitdir: {actual_git}\n")

            resolved = resolve_git_dir(str(git_file))
            assert resolved == str(actual_git)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestWorktreeSupport -v
```

Expected: FAIL - no resolve_git_dir function, worktree detection fails

**Step 3: Add resolve_git_dir helper and update get_git_operation_state**

Add after `run_git()`:

```python
def resolve_git_dir(git_dir: str) -> str:
    """
    Resolve git directory, following gitdir file indirection.

    In linked worktrees and some submodules, .git is a file containing:
        gitdir: /path/to/actual/.git/worktrees/name

    This function follows that indirection.
    """
    git_path = Path(git_dir)

    # If it's a file, read the gitdir: pointer
    if git_path.is_file():
        try:
            content = git_path.read_text().strip()
            if content.startswith("gitdir:"):
                pointed_path = content[7:].strip()
                # Could be relative or absolute
                if not os.path.isabs(pointed_path):
                    pointed_path = str(git_path.parent / pointed_path)
                return os.path.normpath(pointed_path)
        except Exception:
            pass

    return git_dir
```

Update `get_git_context()` to use it:

```python
    # After resolving git_dir to absolute path, resolve gitdir file indirection
    ctx.git_dir = resolve_git_dir(git_dir.strip())
```

**Step 4: Run tests**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestWorktreeSupport -v
uv run pytest .claude/hooks/test_require_gitflow.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): support worktrees and submodules via gitdir file indirection"
```

---

## Task 3: Precompile Regex Patterns

Minor optimization: compile patterns once at module load instead of on each `matches_valid_pattern()` call.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:97-140`

**Step 1: Write test for compiled patterns**

```python
class TestRegexCompilation:
    def test_patterns_are_precompiled(self):
        """VALID_REGEXES should be compiled Pattern objects."""
        import re
        assert hasattr(require_gitflow, "VALID_REGEXES")
        regexes = require_gitflow.VALID_REGEXES
        assert isinstance(regexes, list)
        assert len(regexes) > 0
        assert all(isinstance(r, re.Pattern) for r in regexes)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestRegexCompilation -v
```

Expected: FAIL - no VALID_REGEXES attribute

**Step 3: Precompile patterns**

Replace the VALID_PATTERNS block:

```python
# Valid GitFlow working branch patterns (regex)
VALID_PATTERNS = [
    # GitFlow core
    r"^feature/.+",
    r"^feat/.+",
    r"^release/.+",
    r"^hotfix/.+",
    # Bug fixes
    r"^fix/.+",
    r"^bugfix/.+",
    # Conventional Commits aligned
    r"^docs/.+",
    r"^style/.+",
    r"^refactor/.+",
    r"^perf/.+",
    r"^test/.+",
    r"^build/.+",
    r"^ci/.+",
    r"^chore/.+",
    # Automation (dependency bots)
    r"^dependabot/.+",
    r"^renovate/.+",
    r"^deps/.+",
    # Exploratory
    r"^spike/.+",
    r"^experiment/.+",
    r"^poc/.+",
]

# Precompile patterns for performance (case-insensitive)
VALID_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in VALID_PATTERNS]


def matches_valid_pattern(branch: str) -> bool:
    """Check if branch name matches any valid GitFlow pattern."""
    return any(regex.match(branch) for regex in VALID_REGEXES)
```

**Step 4: Run tests**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py -v
```

Expected: All PASS (including new test and existing pattern tests)

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "perf(gitflow): precompile regex patterns at module load"
```

---

## Task 4: Unify Protected Branch Logic

Currently main/master/develop are special-cased, then protected branches checked separately. Unify into single check with per-branch message selection.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:423-441`

**Step 1: Write test to verify unified behavior**

```python
class TestProtectedBranchUnification:
    def test_custom_protected_includes_develop_behavior(self, temp_git_repo, monkeypatch):
        """Custom protected branch should use appropriate message."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("PROTECTED_BRANCHES", "main,staging,production")

        subprocess.run(["git", "checkout", "-b", "staging"], cwd=temp_git_repo, capture_output=True, check=True)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert "Cannot edit" in result.stderr

    def test_develop_in_custom_protected_not_duplicate_check(self, temp_git_repo, monkeypatch):
        """Adding develop to PROTECTED_BRANCHES shouldn't cause double-blocking."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("PROTECTED_BRANCHES", "main,develop")

        subprocess.run(["git", "checkout", "-b", "develop"], cwd=temp_git_repo, capture_output=True, check=True)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        # Should only hit the check once (develop-specific message)
        assert "integration branch" in result.stderr
```

**Step 2: Run test to verify current behavior**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestProtectedBranchUnification -v
```

Expected: Should pass with current code (this is a refactor, not behavior change)

**Step 3: Refactor to unified logic**

Replace the protected branch checks with:

```python
        # Check if on protected branch (case-insensitive)
        protected = get_protected_branches()
        branch_lower = branch.lower()

        if branch_lower in protected:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")

            # Select message based on branch type
            if branch_lower in {"main", "master"}:
                message = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)
            elif branch_lower == "develop":
                message = BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context)
            else:
                # Custom protected branch - use main template
                message = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)

            print(message, file=sys.stderr)
            sys.exit(2)
```

**Step 4: Run all tests**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "refactor(gitflow): unify protected branch checking logic"
```

---

## Task 5: Improve "No Commits Yet" Messaging

Add explicit log and optional warning for repos with no commits.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:376-379`

**Step 1: Write test for no-commits behavior**

```python
class TestNoCommitsYet:
    def test_no_commits_allows_with_log(self, tmp_path, monkeypatch):
        """Repo with no commits should allow edits and log explicitly."""
        repo = tmp_path / "empty_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

        monkeypatch.chdir(repo)
        monkeypatch.setenv("GITFLOW_DEBUG", "1")

        result = run_hook(repo)
        assert result.returncode == 0
        assert "no commits" in result.stderr.lower()

    def test_no_commits_returns_system_message(self, tmp_path, monkeypatch):
        """No-commits state should return a systemMessage."""
        repo = tmp_path / "empty_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

        monkeypatch.chdir(repo)

        result = run_hook(repo)
        assert result.returncode == 0
        if result.stdout.strip():
            output = json.loads(result.stdout)
            # Optional: could have a message
```

**Step 2: Run tests**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py::TestNoCommitsYet -v
```

**Step 3: Improve no-commits handling**

```python
        # New repo with no commits - allow (bootstrapping)
        if not ctx.has_commits:
            log("INFO", "Repository has no commits yet - allowing edits for bootstrapping")
            output = {
                "systemMessage": "Note: This repository has no commits yet. GitFlow checks are bypassed during initial setup."
            }
            print(json.dumps(output))
            sys.exit(0)
```

**Step 4: Run all tests**

```bash
uv run pytest .claude/hooks/test_require_gitflow.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add .claude/hooks/require-gitflow.py .claude/hooks/test_require_gitflow.py
git commit -m "feat(gitflow): improve messaging for repos with no commits"
```

---

## Task 6: JSON systemMessage in Strict Mode

Currently strict mode only prints to stderr. Add JSON systemMessage output (while still exiting 2) for consistent UI.

**Files:**
- Modify: `.claude/hooks/require-gitflow.py:451-456`

**Step 1: Write test for strict mode JSON**

```python
class TestStrictModeOutput:
    def test_strict_mode_includes_system_message(self, temp_git_repo, monkeypatch):
        """Strict mode should output JSON systemMessage even when blocking."""
        monkeypatch.chdir(temp_git_repo)
        monkeypatch.setenv("GITFLOW_STRICT", "1")

        subprocess.run(["git", "checkout", "-b", "random-branch"], cwd=temp_git_repo, capture_output=True)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert result.stderr  # Still has stderr message
        # Note: JSON on stdout is ignored at exit 2, but we output for potential future use
```

Actually, reviewing the hook rules: "On exit 2, JSON in stdout is ignored." So adding JSON output at exit 2 provides no benefit - it's ignored.

**Step 1 (Revised): Document the limitation**

The hook spec says JSON on stdout is ignored at exit 2. We cannot provide systemMessage when blocking. This is a limitation of the hook contract, not something we can fix in this hook.

**Step 2: Add comment documenting this**

```python
        if is_strict_mode():
            log("INFO", f"BLOCKED: Non-standard branch {branch} (strict mode)")
            # Note: JSON systemMessage cannot be used here because exit 2 ignores stdout.
            # The hook contract only processes stdout JSON on exit 0.
            print(
                BLOCK_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested),
                file=sys.stderr,
            )
            sys.exit(2)
```

**Step 3: Commit**

```bash
git add .claude/hooks/require-gitflow.py
git commit -m "docs(gitflow): document JSON limitation in strict mode blocking"
```

---

## Summary

| Task | Type | Description |
|------|------|-------------|
| 1 | Bug fix | Resolve git_dir to absolute path |
| 2 | Feature | Support worktrees via gitdir file indirection |
| 3 | Perf | Precompile regex patterns |
| 4 | Refactor | Unify protected branch logic |
| 5 | Feature | Improve no-commits messaging |
| 6 | Docs | Document JSON limitation in strict mode |

After all tasks complete:

```bash
uv run pytest .claude/hooks/test_require_gitflow.py -v  # Verify all tests pass
uv run scripts/promote hook require-gitflow            # Promote to production
uv run scripts/sync-settings                           # Update hook registration
```
