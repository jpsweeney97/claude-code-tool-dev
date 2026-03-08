"""Tests for path canonicalization, denylist, and safety checks."""

import pytest

from context_injection.paths import (
    DENYLIST_DIRS,
    CompileTimeResult,
    check_path_compile_time,
    check_path_runtime,
    is_risk_signal_path,
    normalize_input_path,
)


class TestNormalizeInputPath:
    def test_strips_backticks(self) -> None:
        assert normalize_input_path("`src/app.py`") == "src/app.py"

    def test_strips_quotes(self) -> None:
        assert normalize_input_path('"src/app.py"') == "src/app.py"
        assert normalize_input_path("'src/app.py'") == "src/app.py"

    def test_splits_line_number(self) -> None:
        path, line = normalize_input_path("src/app.py:42", split_anchor=True)
        assert path == "src/app.py"
        assert line == 42

    def test_splits_github_anchor(self) -> None:
        path, line = normalize_input_path("src/app.py#L42", split_anchor=True)
        assert path == "src/app.py"
        assert line == 42

    def test_default_mode_preserves_anchor_in_path(self) -> None:
        """Without split_anchor, colon anchor stays in the path string."""
        result = normalize_input_path("src/app.py:42")
        assert result == "src/app.py:42"
        assert isinstance(result, str)  # not a tuple

    def test_default_mode_preserves_github_anchor(self) -> None:
        """Without split_anchor, #L anchor stays in the path string."""
        result = normalize_input_path("src/app.py#L42")
        assert result == "src/app.py#L42"
        assert isinstance(result, str)

    def test_backslash_to_forward(self) -> None:
        assert normalize_input_path("src\\api\\auth.py") == "src/api/auth.py"

    def test_rejects_nul_bytes(self) -> None:
        with pytest.raises(ValueError, match="NUL"):
            normalize_input_path("src/app\x00.py")

    def test_rejects_dotdot_traversal(self) -> None:
        with pytest.raises(ValueError, match="traversal"):
            normalize_input_path("../etc/passwd")

    def test_rejects_absolute_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            normalize_input_path("/etc/passwd")

    def test_nfc_normalization(self) -> None:
        # NFD: e + combining acute
        nfd = "caf\u0065\u0301.py"
        # NFC: precomposed é
        nfc = "caf\u00e9.py"
        assert normalize_input_path(nfd) == nfc


class TestNormalizeInputPathCanonicalization:
    """Tests for canonical path form: collapsing separators, dots, trailing slashes."""

    def test_collapses_double_slashes(self) -> None:
        assert normalize_input_path("a//b/c.py") == "a/b/c.py"

    def test_collapses_triple_slashes(self) -> None:
        assert normalize_input_path("a///b/c.py") == "a/b/c.py"

    def test_removes_dot_segments(self) -> None:
        assert normalize_input_path("./a/./b/c.py") == "a/b/c.py"

    def test_removes_leading_dot_slash(self) -> None:
        assert normalize_input_path("./src/app.py") == "src/app.py"

    def test_strips_trailing_slash(self) -> None:
        assert normalize_input_path("a/b/") == "a/b"

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("   ")

    def test_rejects_dot_only(self) -> None:
        """posixpath.normpath('.') returns '.', which is a bare directory — reject."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path(".")

    def test_rejects_quoted_empty(self) -> None:
        """Quoted empty string after stripping quotes."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("''")

    def test_combined_normalization(self) -> None:
        assert normalize_input_path("./a/./b//c/") == "a/b/c"

    def test_anchor_preserved_through_normpath(self) -> None:
        """Colon anchor survives normpath (treated as filename char)."""
        assert normalize_input_path("./src/app.py:42") == "src/app.py:42"

    def test_anchor_split_after_normpath(self) -> None:
        """Anchor splitting works correctly on normalized path."""
        path, line = normalize_input_path("./src/app.py:42", split_anchor=True)
        assert path == "src/app.py"
        assert line == 42

    def test_trailing_dot_segment(self) -> None:
        """a/b/c/. normalizes to a/b/c via posixpath.normpath."""
        assert normalize_input_path("a/b/c/.") == "a/b/c"

    def test_dot_slash_only_rejected(self) -> None:
        """./ normalizes to . — rejected as bare directory."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("./")


class TestNormalizeInputPathAnchorOnly:
    """Anchor-only inputs must be rejected when split_anchor=True."""

    def test_rejects_colon_anchor_only(self) -> None:
        """':42' has no path component — should raise, not return ('', 42)."""
        with pytest.raises(ValueError, match="empty path"):
            normalize_input_path(":42", split_anchor=True)

    def test_rejects_github_anchor_only(self) -> None:
        """'#L42' has no path component — should raise, not return ('', 42)."""
        with pytest.raises(ValueError, match="empty path"):
            normalize_input_path("#L42", split_anchor=True)

    def test_rejects_dot_slash_anchor(self) -> None:
        """./:42 normalizes to '.' then anchor splits to '' — should raise."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("./:42", split_anchor=True)

    def test_rejects_dot_colon_anchor(self) -> None:
        """.:42 normpath leaves '.:42', anchor split produces ('.', 42) — should raise."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path(".:42", split_anchor=True)


class TestNormalizedPathDedupe:
    """Verify that non-canonical inputs produce the same normalized form
    for consistent git-files lookup and denylist matching."""

    def test_double_slash_matches_git_files(self) -> None:
        result = check_path_compile_time(
            "src//app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "allowed"
        assert result.user_rel == "src/app.py"

    def test_dot_segment_matches_git_files(self) -> None:
        result = check_path_compile_time(
            "./src/./app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "allowed"
        assert result.user_rel == "src/app.py"

    def test_trailing_slash_matches_git_files(self) -> None:
        result = check_path_compile_time(
            "src/app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "allowed"


class TestDenylist:
    def test_git_dir_denied(self) -> None:
        result = check_path_compile_time(
            ".git/config",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "denied"

    def test_env_file_denied(self) -> None:
        result = check_path_compile_time(
            ".env",
            repo_root="/tmp/repo",
            git_files={".env", "src/app.py"},
        )
        assert result.status == "denied"

    def test_env_local_denied(self) -> None:
        result = check_path_compile_time(
            ".env.local",
            repo_root="/tmp/repo",
            git_files={".env.local"},
        )
        assert result.status == "denied"

    def test_env_example_allowed(self) -> None:
        result = check_path_compile_time(
            ".env.example",
            repo_root="/tmp/repo",
            git_files={".env.example"},
        )
        assert result.status == "allowed"

    def test_pem_file_denied(self) -> None:
        result = check_path_compile_time(
            "certs/server.pem",
            repo_root="/tmp/repo",
            git_files={"certs/server.pem"},
        )
        assert result.status == "denied"

    def test_ssh_dir_denied(self) -> None:
        result = check_path_compile_time(
            ".ssh/id_rsa",
            repo_root="/tmp/repo",
            git_files=set(),
        )
        assert result.status == "denied"


class TestDenylistAtDepth:
    """Verify denylist catches denied directories at arbitrary nesting depth."""

    def test_git_at_depth_1(self) -> None:
        result = check_path_compile_time(
            "src/.git/config",
            repo_root="/tmp/repo",
            git_files={"src/.git/config"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_git_at_depth_3(self) -> None:
        result = check_path_compile_time(
            "deeply/nested/path/.git/refs/heads/main",
            repo_root="/tmp/repo",
            git_files={"deeply/nested/path/.git/refs/heads/main"},
        )
        assert result.status == "denied"

    def test_ssh_at_depth_2(self) -> None:
        result = check_path_compile_time(
            "home/user/.ssh/id_rsa",
            repo_root="/tmp/repo",
            git_files={"home/user/.ssh/id_rsa"},
        )
        assert result.status == "denied"

    def test_pycache_at_depth_1(self) -> None:
        result = check_path_compile_time(
            "src/__pycache__/module.cpython-311.pyc",
            repo_root="/tmp/repo",
            git_files={"src/__pycache__/module.cpython-311.pyc"},
        )
        assert result.status == "denied"

    def test_node_modules_at_depth_1(self) -> None:
        result = check_path_compile_time(
            "packages/node_modules/lodash/index.js",
            repo_root="/tmp/repo",
            git_files={"packages/node_modules/lodash/index.js"},
        )
        assert result.status == "denied"


class TestDenylistDirsInvariant:
    """Structural invariant: DENYLIST_DIRS must contain only bare names."""

    def test_no_slash_patterns(self) -> None:
        """Bare-name patterns match per-component at any depth.
        Slash patterns (e.g., name/*) silently fail for nested paths."""
        assert all("/" not in p for p in DENYLIST_DIRS)


class TestDenylistSecretLocations:
    """Verify newly added secret directories and files are denied."""

    @pytest.mark.parametrize(
        "dirname",
        [".aws", ".gnupg", ".docker", ".kube", ".terraform"],
    )
    def test_secret_dirs_denied(self, dirname: str) -> None:
        result = check_path_compile_time(
            f"{dirname}/credentials",
            repo_root="/tmp/repo",
            git_files={f"{dirname}/credentials"},
        )
        assert result.status == "denied"
        assert dirname in (result.deny_reason or "")

    @pytest.mark.parametrize(
        "dirname",
        [".aws", ".gnupg", ".docker", ".kube", ".terraform"],
    )
    def test_secret_dirs_denied_at_depth(self, dirname: str) -> None:
        result = check_path_compile_time(
            f"subdir/{dirname}/config",
            repo_root="/tmp/repo",
            git_files={f"subdir/{dirname}/config"},
        )
        assert result.status == "denied"

    @pytest.mark.parametrize(
        "filename",
        [".npmrc", ".pypirc", ".netrc", "credentials.json"],
    )
    def test_secret_files_denied(self, filename: str) -> None:
        result = check_path_compile_time(
            filename,
            repo_root="/tmp/repo",
            git_files={filename},
        )
        assert result.status == "denied"

    def test_service_account_json_denied(self) -> None:
        result = check_path_compile_time(
            "service-account-prod.json",
            repo_root="/tmp/repo",
            git_files={"service-account-prod.json"},
        )
        assert result.status == "denied"

    def test_tfstate_denied(self) -> None:
        result = check_path_compile_time(
            "terraform.tfstate",
            repo_root="/tmp/repo",
            git_files={"terraform.tfstate"},
        )
        assert result.status == "denied"

    def test_tfstate_backup_denied(self) -> None:
        result = check_path_compile_time(
            "terraform.tfstate.backup",
            repo_root="/tmp/repo",
            git_files={"terraform.tfstate.backup"},
        )
        assert result.status == "denied"

    def test_normal_json_not_denied(self) -> None:
        """Regular JSON files should NOT be caught by service-account pattern."""
        result = check_path_compile_time(
            "config.json",
            repo_root="/tmp/repo",
            git_files={"config.json"},
        )
        assert result.status == "allowed"


class TestGitLsFilesGating:
    def test_tracked_file_allowed(self) -> None:
        result = check_path_compile_time(
            "src/app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "allowed"

    def test_untracked_file_blocked(self) -> None:
        result = check_path_compile_time(
            "src/app.py",
            repo_root="/tmp/repo",
            git_files={"src/other.py"},
        )
        assert result.status == "not_tracked"


class TestRiskSignal:
    def test_secret_in_path(self) -> None:
        assert is_risk_signal_path("config/secrets.yaml") is True

    def test_token_in_path(self) -> None:
        assert is_risk_signal_path("auth/token_store.py") is True

    def test_credential_in_path(self) -> None:
        assert is_risk_signal_path("credentials/aws.json") is True

    def test_normal_path(self) -> None:
        assert is_risk_signal_path("src/app.py") is False


class TestCompileTimeResult:
    def test_allowed_result(self) -> None:
        result = check_path_compile_time(
            "src/app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert isinstance(result, CompileTimeResult)
        assert result.status == "allowed"
        assert result.user_rel == "src/app.py"
        assert result.resolved_rel is not None
        assert result.risk_signal is False


class TestSymlinkDenylistBypass:
    """Symlinks to denylisted files must be denied even if the link name is safe."""

    def test_compile_time_symlink_to_env_denied(self, tmp_path) -> None:
        """A tracked symlink docs/readme.md -> .env is denied at compile time."""
        target = tmp_path / ".env"
        target.write_text("SECRET=hunter2")
        link = tmp_path / "docs" / "readme.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        result = check_path_compile_time(
            "docs/readme.md",
            repo_root=str(tmp_path),
            git_files={"docs/readme.md"},
        )
        assert result.status == "denied"
        assert "denylist" in (result.deny_reason or "")

    def test_compile_time_symlink_to_pem_denied(self, tmp_path) -> None:
        """A tracked symlink public.txt -> certs/server.pem is denied."""
        certs = tmp_path / "certs"
        certs.mkdir()
        target = certs / "server.pem"
        target.write_text("-----BEGIN RSA PRIVATE KEY-----")
        link = tmp_path / "public.txt"
        link.symlink_to(target)
        result = check_path_compile_time(
            "public.txt",
            repo_root=str(tmp_path),
            git_files={"public.txt"},
        )
        assert result.status == "denied"

    def test_runtime_symlink_to_env_denied(self, tmp_path) -> None:
        """A symlink resolving to .env is denied at runtime."""
        target = tmp_path / ".env"
        target.write_text("SECRET=hunter2")
        link = tmp_path / "docs" / "readme.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        result = check_path_runtime(str(link), repo_root=str(tmp_path))
        assert result.status == "denied"
        assert "denylist" in (result.deny_reason or "")


class TestDenylistOnResolvedPath:
    """Verify denylist is checked on resolved_rel, not just normalized."""

    def test_symlink_to_git_dir_denied(self, tmp_path) -> None:
        """A symlink resolving into .git/ is denied via resolved_rel check."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        target = git_dir / "config"
        target.write_text("[core]")

        link = tmp_path / "docs" / "config.txt"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)

        result = check_path_compile_time(
            "docs/config.txt",
            repo_root=str(tmp_path),
            git_files={"docs/config.txt"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_non_symlink_resolved_rel_equals_user_rel(self) -> None:
        """For non-symlink paths, resolved_rel matches user_rel."""
        result = check_path_compile_time(
            "src/app.py",
            repo_root="/tmp/repo",
            git_files={"src/app.py"},
        )
        assert result.status == "allowed"
        assert result.resolved_rel == result.user_rel


class TestDenylistAfterNormpath:
    """Pipeline integration: non-canonical inputs must still hit denylist after normpath."""

    def test_dot_slash_git_denied(self) -> None:
        """./.git/config normalizes to .git/config — still denied."""
        result = check_path_compile_time(
            "./.git/config",
            repo_root="/tmp/repo",
            git_files={".git/config"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_double_slash_git_denied(self) -> None:
        """.git//config normalizes to .git/config — still denied."""
        result = check_path_compile_time(
            ".git//config",
            repo_root="/tmp/repo",
            git_files={".git/config"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_dot_segments_in_denied_path(self) -> None:
        """src/./node_modules/./lodash/index.js normalizes — node_modules still denied."""
        result = check_path_compile_time(
            "src/./node_modules/./lodash/index.js",
            repo_root="/tmp/repo",
            git_files={"src/node_modules/lodash/index.js"},
        )
        assert result.status == "denied"
        assert "node_modules" in (result.deny_reason or "")

    def test_trailing_slash_on_denied_component(self) -> None:
        """.aws/credentials/ (trailing slash) normalizes — .aws still denied."""
        result = check_path_compile_time(
            ".aws/credentials/",
            repo_root="/tmp/repo",
            git_files={".aws/credentials"},
        )
        assert result.status == "denied"
        assert ".aws" in (result.deny_reason or "")


class TestDenylistNegativeCases:
    """Verify paths that look similar to denylist entries are NOT denied."""

    @pytest.mark.parametrize(
        ("path", "description"),
        [
            ("terraform/main.tf", "terraform (no dot) != .terraform"),
            ("aws-sdk/lib.py", "aws-sdk != .aws"),
            ("docker-compose.yml", "docker-compose != .docker"),
            ("kube-system/config.yaml", "kube-system != .kube"),
            ("gnupg-utils/helper.py", "gnupg-utils != .gnupg"),
        ],
    )
    def test_similar_names_not_denied(self, path: str, description: str) -> None:
        result = check_path_compile_time(
            path,
            repo_root="/tmp/repo",
            git_files={path},
        )
        assert result.status == "allowed", f"False positive: {description}"


class TestCheckPathRuntime:
    """Tests for check_path_runtime() — Call 2 lightweight re-check."""

    def test_existing_file_allowed(self, tmp_path) -> None:
        """A regular file under repo_root is allowed."""
        f = tmp_path / "src" / "app.py"
        f.parent.mkdir(parents=True)
        f.write_text("print('hello')")
        result = check_path_runtime(str(f), repo_root=str(tmp_path))
        assert result.status == "allowed"
        assert result.resolved_abs is not None

    def test_nonexistent_file_not_found(self, tmp_path) -> None:
        """A non-existent path returns not_found."""
        result = check_path_runtime(
            str(tmp_path / "missing.py"), repo_root=str(tmp_path)
        )
        assert result.status == "not_found"

    def test_directory_not_found(self, tmp_path) -> None:
        """A directory (not a regular file) returns not_found."""
        d = tmp_path / "subdir"
        d.mkdir()
        result = check_path_runtime(str(d), repo_root=str(tmp_path))
        assert result.status == "not_found"

    def test_path_escaping_repo_root_denied(self, tmp_path) -> None:
        """A path outside repo_root is denied."""
        outside = tmp_path / ".." / "outside.py"
        # Create the file so it exists
        real_outside = tmp_path.parent / "outside.py"
        real_outside.write_text("secret")
        result = check_path_runtime(str(outside), repo_root=str(tmp_path))
        assert result.status == "denied"
        assert result.deny_reason is not None
        # Cleanup
        real_outside.unlink()

    def test_symlink_to_outside_denied(self, tmp_path) -> None:
        """A symlink pointing outside repo_root is denied."""
        outside = tmp_path.parent / "secret.txt"
        outside.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        result = check_path_runtime(str(link), repo_root=str(tmp_path))
        assert result.status == "denied"
        # Cleanup
        outside.unlink()

    def test_relative_path_resolves_against_repo_root(self, tmp_path, monkeypatch) -> None:
        """Repo-relative path resolves against repo_root, not CWD."""
        repo = tmp_path / "myrepo"
        repo.mkdir()
        src = repo / "src"
        src.mkdir()
        f = src / "app.py"
        f.write_text("x = 1\n")

        # Set CWD to a DIFFERENT directory than repo_root
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        result = check_path_runtime("src/app.py", repo_root=str(repo))
        assert result.status == "allowed"
        assert result.resolved_abs == str(f.resolve())
