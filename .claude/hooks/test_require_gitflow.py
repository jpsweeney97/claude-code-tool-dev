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
if spec is None or spec.loader is None:
    raise ImportError("Could not load require-gitflow.py")
require_gitflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(require_gitflow)

# Import functions for unit testing
suggest_branch_name = require_gitflow.suggest_branch_name
matches_valid_pattern = require_gitflow.matches_valid_pattern
get_protected_branches = require_gitflow.get_protected_branches
is_strict_mode = require_gitflow.is_strict_mode


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


class TestIntegration:
    def test_block_message_includes_file_path(self, temp_git_repo, monkeypatch):
        """Block message should mention the specific file being edited."""
        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo, tool_input={"file_path": "src/auth/login.py"})
        assert result.returncode == 2
        assert "'src/auth/login.py'" in result.stderr

    def test_long_file_path_is_truncated(self, temp_git_repo, monkeypatch):
        """Long file paths should be truncated with ... prefix."""
        monkeypatch.chdir(temp_git_repo)
        long_path = "src/very/deeply/nested/directory/structure/that/goes/on/auth/login.py"
        result = run_hook(temp_git_repo, tool_input={"file_path": long_path})
        assert result.returncode == 2
        assert "..." in result.stderr
        assert "login.py" in result.stderr


class TestFrontmatter:
    def test_timeout_is_seconds_not_milliseconds(self):
        """Timeout should be 5 seconds, not 5000 (which would be 83 minutes)."""
        import re

        hook_path = Path(__file__).parent / "require-gitflow.py"
        content = hook_path.read_text()
        # Extract timeout from frontmatter
        match = re.search(r"# timeout: (\d+)", content)
        assert match, "timeout not found in frontmatter"
        timeout = int(match.group(1))
        assert timeout <= 60, f"timeout {timeout}s is too long (max 60s reasonable)"
        assert timeout >= 1, f"timeout {timeout}s is too short"


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


class TestRegexCompilation:
    def test_patterns_are_precompiled(self):
        """VALID_REGEXES should be compiled Pattern objects."""
        import re
        assert hasattr(require_gitflow, "VALID_REGEXES")
        regexes = require_gitflow.VALID_REGEXES
        assert isinstance(regexes, list)
        assert len(regexes) > 0
        assert all(isinstance(r, re.Pattern) for r in regexes)


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


class TestSubdirectoryDetection:
    def test_operation_detection_from_subdirectory(self, temp_git_repo, monkeypatch):
        """Operation detection should work when invoked from subdirectory."""
        subdir = temp_git_repo / "src" / "deep"
        subdir.mkdir(parents=True)

        subprocess.run(["git", "checkout", "-b", "feature/a"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "conflict.txt").write_text("feature a content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feature a"], cwd=temp_git_repo, capture_output=True, check=True)

        subprocess.run(["git", "checkout", "main"], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", "feature/b"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "conflict.txt").write_text("feature b content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feature b"], cwd=temp_git_repo, capture_output=True, check=True)

        subprocess.run(["git", "merge", "feature/a"], cwd=temp_git_repo, capture_output=True)
        monkeypatch.chdir(subdir)

        result = run_hook(subdir)
        assert result.returncode == 0
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


class TestWorktreeSupport:
    def test_gitdir_file_indirection(self, temp_git_repo, tmp_path, monkeypatch):
        """Operation detection should work in linked worktrees where .git is a file."""
        # Create a feature branch on the main repo to use in worktree
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "file.txt").write_text("feat")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "feat"], cwd=temp_git_repo, capture_output=True, check=True)

        # Create conflicting change on main
        subprocess.run(["git", "checkout", "main"], cwd=temp_git_repo, capture_output=True, check=True)
        (temp_git_repo / "file.txt").write_text("main-change")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "main-change"], cwd=temp_git_repo, capture_output=True, check=True)

        # Now create worktree from feature/test branch
        worktree_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "feature/test"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True
        )

        # Start rebase that will conflict (but don't resolve it)
        subprocess.run(["git", "rebase", "main"], cwd=worktree_path, capture_output=True)

        monkeypatch.chdir(worktree_path)

        result = run_hook(worktree_path)
        assert result.returncode == 2
        assert "rebase" in result.stderr.lower()

    def test_resolve_gitdir_file(self):
        """resolve_git_dir should follow gitdir: file indirection."""
        resolve_git_dir = require_gitflow.resolve_git_dir

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            git_file = Path(tmpdir) / ".git"
            actual_git = Path(tmpdir) / "actual_git_dir"
            actual_git.mkdir()

            git_file.write_text(f"gitdir: {actual_git}\n")

            resolved = resolve_git_dir(str(git_file))
            assert resolved == str(actual_git)


class TestIntegrationFull:
    """Integration tests to lock behavior before refactoring."""

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


class TestNoCommitsYet:
    """Tests for repos with no commits (bootstrapping phase)."""

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
        output = json.loads(result.stdout)
        assert "systemMessage" in output
        assert "no commits" in output["systemMessage"].lower()


class TestLogWarning:
    """Tests for log() function error handling."""

    def test_log_warns_on_write_failure(self, tmp_path, monkeypatch, capsys):
        """log() should warn once (not spam) when file write fails."""
        require_gitflow._log_warning_shown = False
        original_debug = require_gitflow.DEBUG
        require_gitflow.DEBUG = True

        # Use a log file in tmp_path so mkdir succeeds
        test_log = tmp_path / "logs" / "test.log"
        monkeypatch.setattr(require_gitflow, "LOG_FILE", test_log)

        def mock_open(*args, **kwargs):
            raise OSError("Disk full")

        monkeypatch.setattr("builtins.open", mock_open)

        try:
            require_gitflow.log("INFO", "test message 1")
            require_gitflow.log("INFO", "test message 2")

            captured = capsys.readouterr()
            # Should warn once, not twice
            assert captured.err.count("Warning: Could not write to log file") == 1
            assert "Disk full" in captured.err
        finally:
            require_gitflow.DEBUG = original_debug


class TestProtectedBranchUnification:
    """Tests to verify unified protected branch logic."""

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

    def test_main_protected_message_shows(self, temp_git_repo, monkeypatch):
        """Main branch should show main-specific message."""
        monkeypatch.chdir(temp_git_repo)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert "production branch" in result.stderr

    def test_develop_protected_message_shows(self, temp_git_repo, monkeypatch):
        """Develop branch should show develop-specific message."""
        monkeypatch.chdir(temp_git_repo)
        subprocess.run(["git", "checkout", "-b", "develop"], cwd=temp_git_repo, capture_output=True, check=True)
        result = run_hook(temp_git_repo)

        assert result.returncode == 2
        assert "integration branch" in result.stderr


class TestResolveGitDir:
    """Tests for resolve_git_dir() function."""

    def test_resolve_git_dir_logs_on_read_error(self, monkeypatch, tmp_path):
        """resolve_git_dir() should log when gitdir file is unreadable."""
        require_gitflow.DEBUG = True
        logged_messages = []

        def mock_log(level, message):
            logged_messages.append((level, message))

        monkeypatch.setattr(require_gitflow, "log", mock_log)

        # Create a gitdir file that will fail to read
        git_file = tmp_path / ".git"
        git_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8

        result = require_gitflow.resolve_git_dir(str(git_file))

        # Should return original path on error
        assert result == str(git_file)
        # Should have logged
        assert any("Could not resolve git dir" in msg for _, msg in logged_messages)


class TestGitContextInvariants:
    """Tests for GitContext invariant validation."""

    def test_gitcontext_rejects_invalid_states(self):
        """GitContext should reject logically invalid states at construction."""
        GitContext = require_gitflow.GitContext

        # is_repo=False but other fields set
        with pytest.raises(ValueError, match="is_repo=False"):
            GitContext(is_repo=False, branch="main")

        with pytest.raises(ValueError, match="is_repo=False"):
            GitContext(is_repo=False, has_commits=True)

        # is_repo=True but no git_dir
        with pytest.raises(ValueError, match="git_dir is None"):
            GitContext(is_repo=True, git_dir=None)

        # is_detached without has_commits
        with pytest.raises(ValueError, match="is_detached=True requires has_commits"):
            GitContext(is_repo=True, git_dir="/path", is_detached=True, has_commits=False)

        # branch and is_detached both set
        with pytest.raises(ValueError, match="mutually exclusive"):
            GitContext(is_repo=True, git_dir="/path", branch="main", is_detached=True, has_commits=True)

    def test_gitcontext_accepts_valid_states(self):
        """GitContext should accept valid states."""
        GitContext = require_gitflow.GitContext

        # Not a repo
        ctx = GitContext(is_repo=False)
        assert ctx.is_repo is False

        # Repo with branch
        ctx = GitContext(is_repo=True, git_dir="/path", branch="main", has_commits=True)
        assert ctx.branch == "main"

        # Repo with detached HEAD
        ctx = GitContext(is_repo=True, git_dir="/path", is_detached=True, has_commits=True)
        assert ctx.is_detached is True

    def test_gitcontext_is_frozen(self):
        """GitContext should be immutable after construction."""
        GitContext = require_gitflow.GitContext

        ctx = GitContext(is_repo=True, git_dir="/path", branch="main", has_commits=True)

        with pytest.raises(AttributeError):
            ctx.branch = "other"
