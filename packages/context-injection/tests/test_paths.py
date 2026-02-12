"""Tests for path canonicalization, denylist, and safety checks."""

import pytest

from context_injection.paths import (
    CompileTimeResult,
    check_path_compile_time,
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
