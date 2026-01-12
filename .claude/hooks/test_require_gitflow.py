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
