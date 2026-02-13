"""Tests for path canonicalization, denylist, and safety checks."""

import pytest

from context_injection.paths import (
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
