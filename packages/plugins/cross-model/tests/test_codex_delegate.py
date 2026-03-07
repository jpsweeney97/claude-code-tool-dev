"""Tests for codex_delegate adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestResolveRepoRoot:
    """Pipeline step 1: resolve repo root."""

    def test_returns_toplevel_path(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _resolve_repo_root
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(
                returncode=0, stdout=str(tmp_path) + "\n"
            )
            assert _resolve_repo_root() == tmp_path

    def test_raises_on_not_git_repo(self) -> None:
        from scripts.codex_delegate import _resolve_repo_root, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=128, stdout="", stderr="not a git repo")
            with pytest.raises(DelegationError, match="not a git repository"):
                _resolve_repo_root()


class TestParseInput:
    """F1+F8: Phase A parse (_parse_input) — structural only."""

    def test_valid_minimal_input(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "fix the test"}))
        result = _parse_input(f)
        assert result["prompt"] == "fix the test"
        assert result["sandbox"] == "workspace-write"  # default

    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input, DelegationError
        f = tmp_path / "input.json"
        f.write_text("not json at all")
        with pytest.raises(DelegationError, match="invalid JSON"):
            _parse_input(f)

    def test_returns_raw_keys(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "bogus": True}))
        result = _parse_input(f)
        assert "bogus" in result["_raw_keys"]

    def test_empty_string_model_normalized_to_none(self, tmp_path: Path) -> None:
        """R6-B5: model='' should be normalized to None in Phase A."""
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "model": ""}))
        result = _parse_input(f)
        assert result["model"] is None

    def test_falsy_non_string_model_preserved_for_phase_b(self, tmp_path: Path) -> None:
        """Falsy non-string model values (0, False) pass through to Phase B type check."""
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        for falsy_val in [0, False]:
            f.write_text(json.dumps({"prompt": "test", "model": falsy_val}))
            result = _parse_input(f)
            assert result["model"] is not None, f"model={falsy_val!r} was incorrectly normalized to None"


class TestValidateInput:
    """F1+F8: Phase B validate (_validate_input) — field validation."""

    def test_missing_prompt_errors(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": None, "sandbox": "workspace-write",
                  "reasoning_effort": "high", "full_auto": False, "_raw_keys": {"sandbox"}}
        with pytest.raises(DelegationError, match="prompt required"):
            _validate_input(parsed)

    def test_danger_full_access_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "danger-full-access",
                  "reasoning_effort": "high", "full_auto": False, "_raw_keys": {"prompt", "sandbox"}}
        with pytest.raises(DelegationError, match="not supported"):
            _validate_input(parsed)

    def test_full_auto_read_only_conflict(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "read-only",
                  "reasoning_effort": "high", "full_auto": True,
                  "_raw_keys": {"prompt", "sandbox", "full_auto"}}
        with pytest.raises(DelegationError, match="mutually exclusive"):
            _validate_input(parsed)

    def test_unknown_field_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "workspace-write",
                  "reasoning_effort": "high", "full_auto": False,
                  "_raw_keys": {"prompt", "bogus_field"}}
        with pytest.raises(DelegationError, match="unknown field"):
            _validate_input(parsed)


class TestCredentialScan:
    """Step 4: credential scan (between Phase A and Phase B in run())."""

    def test_credential_in_prompt_blocked(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input, CredentialBlockError
        from scripts.credential_scan import scan_text
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "use key AKIAIOSFODNN7EXAMPLE"}))
        phase_a = _parse_input(f)
        result = scan_text(phase_a["prompt"])
        assert result.action == "block"

    @patch("scripts.codex_delegate.scan_text", side_effect=RuntimeError("regex engine failure"))
    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_scanner_error_blocks_not_errors(
        self, mock_sub: MagicMock, mock_log: MagicMock, mock_scan: MagicMock, tmp_path: Path,
    ) -> None:
        """B1+B17: Scanner exceptions produce status=blocked/exit 0 (governance rule 4)."""
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "fix the tests"}))
        exit_code = run(f)
        assert exit_code == 0  # blocked, not error


class TestVersionCheck:
    """Pipeline step 6: CLI version check."""

    def test_valid_version_passes(self) -> None:
        from scripts.codex_delegate import _check_codex_version
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.111.0\n")
            _check_codex_version()

    def test_old_version_fails(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.110.0\n")
            with pytest.raises(DelegationError, match="< 0.111.0"):
                _check_codex_version()

    def test_codex_not_found(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.side_effect = FileNotFoundError
            with pytest.raises(DelegationError, match="not found"):
                _check_codex_version()

    def test_unparseable_version(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex dev-build\n")
            with pytest.raises(DelegationError, match="cannot parse"):
                _check_codex_version()

    def test_version_timeout(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.side_effect = subprocess.TimeoutExpired(cmd=["codex"], timeout=10)
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(DelegationError, match="timed out"):
                _check_codex_version()

    def test_nonzero_returncode(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=1, stdout="codex 0.111.0\n")
            with pytest.raises(DelegationError, match="non-zero"):
                _check_codex_version()


class TestCleanTreeGate:
    """Pipeline step 7: clean-tree gate."""

    def test_clean_tree_passes(self) -> None:
        from scripts.codex_delegate import _check_clean_tree
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="")
            _check_clean_tree()

    def test_dirty_tree_blocked(self) -> None:
        from scripts.codex_delegate import _check_clean_tree, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=" M src/main.py\0")
            with pytest.raises(GateBlockError, match="dirty"):
                _check_clean_tree()


class TestSecretFileGate:
    """Pipeline step 8: readable-secret-file gate (F5: clean pathspec split)."""

    def test_no_secrets_passes(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="")
            _check_secret_files()

    def test_env_file_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_env_example_exempt(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.example\n")
            _check_secret_files()

    def test_env_sample_exempt(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.sample\n")
            _check_secret_files()

    def test_env_template_exempt(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.template\n")
            _check_secret_files()

    def test_pem_file_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="certs/server.pem\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_key_file_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="id_rsa.key\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_env_production_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.production\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()


class TestBuildCommand:
    """Pipeline step 9: build codex exec command."""

    def test_minimal_command(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        output_file = tmp_path / "output.txt"
        cmd = _build_command(
            prompt="fix tests", sandbox="workspace-write", model=None,
            reasoning_effort="high", full_auto=False, output_file=output_file,
        )
        assert cmd[0] == "codex"
        assert "exec" in cmd
        assert "--json" in cmd
        assert "-o" in cmd
        assert "-s" in cmd
        assert "workspace-write" in cmd

    def test_full_auto_flag(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        cmd = _build_command("fix", "workspace-write", None, "high", True, tmp_path / "o.txt")
        assert "--full-auto" in cmd

    def test_model_flag(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        cmd = _build_command("fix", "workspace-write", "o3", "high", False, tmp_path / "o.txt")
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"

    def test_double_dash_before_prompt(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        cmd = _build_command("-fix the thing", "workspace-write", None, "high", False, tmp_path / "o.txt")
        dash_idx = cmd.index("--")
        assert cmd[dash_idx + 1] == "-fix the thing"


class TestParseJsonlEvents:
    """Pipeline steps 11-12: JSONL parsing."""

    def test_extracts_thread_id(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = '{"type":"thread.started","thread_id":"abc-123"}\n'
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "abc-123"

    def test_extracts_commands(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = '{"type":"item.completed","item":{"type":"command_execution","command":"ls","exit_code":0}}\n'
        result = _parse_jsonl(lines)
        assert len(result["commands_run"]) == 1
        assert result["commands_run"][0]["command"] == "ls"

    def test_skips_malformed_lines(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = 'not json\n{"type":"thread.started","thread_id":"abc"}\n'
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "abc"

    def test_zero_usable_events_errors(self) -> None:
        from scripts.codex_delegate import _parse_jsonl, DelegationError
        with pytest.raises(DelegationError, match="no usable JSONL"):
            _parse_jsonl("not json\nalso not json\n")

    def test_unknown_event_types_not_counted(self) -> None:
        from scripts.codex_delegate import _parse_jsonl, DelegationError
        lines = '{"type":"unknown.event","data":"foo"}\n{"type":"custom.thing"}\n'
        with pytest.raises(DelegationError, match="no usable JSONL"):
            _parse_jsonl(lines)


class TestRunOrchestrator:
    """F4: run() orchestrator tests."""

    def _write_input(self, tmp_path: Path, data: dict) -> Path:
        f = tmp_path / "input.json"
        f.write_text(json.dumps(data))
        return f

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_credential_block_emits_analytics(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")
        f = self._write_input(tmp_path, {"prompt": "use key AKIAIOSFODNN7EXAMPLE"})
        exit_code = run(f)
        assert exit_code == 0
        assert mock_log.called

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_gate_block_emits_analytics(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=" M dirty.py\0"),
        ]
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        exit_code = run(f)
        assert exit_code == 0
        assert mock_log.called

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_subprocess_timeout(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_sub.PIPE = subprocess.PIPE
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["codex"], timeout=600)
        mock_sub.Popen.return_value = mock_proc
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        exit_code = run(f)
        assert exit_code == 1
        mock_proc.kill.assert_called_once()
        mock_proc.wait.assert_called_once()

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_finally_cleans_output_file(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=128, stdout="", stderr="not a git repo")
        f = self._write_input(tmp_path, {"prompt": "test"})
        run(f)
        assert f.exists()

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_success_path(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        output_file = tmp_path / "codex_output.txt"
        output_file.write_text("Summary of changes made.")
        jsonl_output = (
            '{"type":"thread.started","thread_id":"t-123"}\n'
            '{"type":"item.completed","item":{"type":"command_execution","command":"ls","exit_code":0}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":50}}\n'
        )
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_sub.PIPE = subprocess.PIPE
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (jsonl_output, "")
        mock_proc.returncode = 0
        mock_sub.Popen.return_value = mock_proc
        f = self._write_input(tmp_path, {"prompt": "fix the tests"})
        fd = os.open(str(output_file), os.O_RDWR)
        with patch("scripts.codex_delegate.tempfile") as mock_tmp:
            mock_tmp.mkstemp.return_value = (fd, str(output_file))
            exit_code = run(f)
        assert exit_code == 0
        assert mock_log.called
        log_event = mock_log.call_args[0][0]
        assert log_event["dispatched"] is True
        assert log_event["thread_id"] == "t-123"
        assert log_event["commands_run_count"] == 1

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_success_path_dispatched_in_stdout(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_delegate import run
        output_file = tmp_path / "codex_output.txt"
        output_file.write_text("Summary.")
        jsonl_output = '{"type":"thread.started","thread_id":"t-1"}\n{"type":"turn.completed","usage":{}}\n'
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_sub.PIPE = subprocess.PIPE
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (jsonl_output, "")
        mock_proc.returncode = 0
        mock_sub.Popen.return_value = mock_proc
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        fd = os.open(str(output_file), os.O_RDWR)
        with patch("scripts.codex_delegate.tempfile") as mock_tmp:
            mock_tmp.mkstemp.return_value = (fd, str(output_file))
            run(f)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["dispatched"] is True

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_error_dispatched_false_in_stdout(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=128, stdout="", stderr="not git")
        f = self._write_input(tmp_path, {"prompt": "test"})
        run(f)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["dispatched"] is False


class TestValidateInputTypeChecks:
    """R5-B3: isinstance checks prevent TypeError on non-string enum values."""

    def test_sandbox_list_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": [],
                  "reasoning_effort": "high", "full_auto": False, "_raw_keys": {"prompt"}}
        with pytest.raises(DelegationError, match="invalid sandbox"):
            _validate_input(parsed)

    def test_reasoning_effort_int_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "workspace-write",
                  "reasoning_effort": 123, "full_auto": False, "_raw_keys": {"prompt"}}
        with pytest.raises(DelegationError, match="invalid reasoning_effort"):
            _validate_input(parsed)

    def test_model_int_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "workspace-write",
                  "reasoning_effort": "high", "full_auto": False,
                  "model": 123, "_raw_keys": {"prompt", "model"}}
        with pytest.raises(DelegationError, match="invalid model"):
            _validate_input(parsed)


class TestStep10ErrorShapes:
    """R5-B4: Step 10 timeout/spawn produce pinned error messages."""

    def _write_input(self, tmp_path: Path, data: dict) -> Path:
        f = tmp_path / "input.json"
        f.write_text(json.dumps(data))
        return f

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_timeout_error_shape(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_sub.PIPE = subprocess.PIPE
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["codex"], timeout=600)
        mock_sub.Popen.return_value = mock_proc
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        run(f)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["error"] == "exec failed: process timeout"
        assert output["dispatched"] is True

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_spawn_error_shape(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        mock_sub.PIPE = subprocess.PIPE
        mock_sub.Popen.side_effect = FileNotFoundError("codex not found")
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        run(f)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "subprocess spawn error" in output["error"]
        assert "dispatched" in output


class TestEmitAnalyticsInvariants:
    """R5-B5: termination_reason derivation hierarchy."""

    def test_not_dispatched_no_blocked_by_is_error(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test", "sandbox": "workspace-write"},
                            parsed=None, exit_code=0, blocked_by=None, dispatched=False)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "error"

    def test_not_dispatched_no_blocked_by_exit_none_is_error(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"}, parsed=None,
                            exit_code=None, blocked_by=None, dispatched=False)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "error"

    def test_dispatched_exit_zero_is_complete(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"},
                            parsed={"thread_id": "t", "commands_run": []},
                            exit_code=0, blocked_by=None, dispatched=True)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "complete"

    def test_blocked_by_overrides_dispatched(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"}, parsed=None,
                            exit_code=0, blocked_by="credential", dispatched=False)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "blocked"

    def test_dispatched_nonzero_exit_is_error(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"},
                            parsed={"thread_id": None, "commands_run": []},
                            exit_code=1, blocked_by=None, dispatched=True)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "error"

    def test_dispatched_exit_none_is_error(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"},
                            parsed={"thread_id": None, "commands_run": []},
                            exit_code=None, blocked_by=None, dispatched=True)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "error"

    def test_git_error_gate_does_not_set_block_flags(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"}, parsed=None,
                            exit_code=None, blocked_by="git_error", dispatched=False)
            event = mock_log.call_args[0][0]
            assert event["termination_reason"] == "blocked"
            assert event["dirty_tree_blocked"] is False
            assert event["readable_secret_file_blocked"] is False
            assert event["credential_blocked"] is False

    def test_partial_parsed_dict_no_keyerror(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(phase_a={"prompt": "test"},
                            parsed={"commands_run": [{"command": "ls", "exit_code": 0}]},
                            exit_code=1, blocked_by=None, dispatched=True)
            event = mock_log.call_args[0][0]
            assert event["thread_id"] is None
            assert event["commands_run_count"] == 1


class TestSchemaParity:
    """R5-I1: Reader/emitter parity guard."""

    def test_emitter_fields_match_reader_required_fields(self) -> None:
        from scripts.codex_delegate import _emit_analytics
        from scripts.read_events import _REQUIRED_FIELDS
        with patch("scripts.codex_delegate.append_log", return_value=True) as mock_log:
            _emit_analytics(
                phase_a={"prompt": "t", "sandbox": "workspace-write",
                          "model": None, "reasoning_effort": "high", "full_auto": False},
                parsed={"thread_id": "t-1", "commands_run": [{"command": "ls", "exit_code": 0}]},
                exit_code=0, blocked_by=None, dispatched=True,
            )
            event = mock_log.call_args[0][0]
            emitted_fields = set(event.keys())
            required_fields = set(_REQUIRED_FIELDS["delegation_outcome"])
            assert emitted_fields == required_fields, (
                f"Mismatch: emitted-only={emitted_fields - required_fields}, "
                f"required-only={required_fields - emitted_fields}"
            )


class TestParseJsonlDeferredCoverage:
    """D1-D4: Deferred parser hardening tests."""

    def test_thread_started_first_wins(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"first"}\n'
            '{"type":"thread.started","thread_id":"second"}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "first"

    def test_summary_from_output_file_over_agent_message(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"from agent"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        result = _parse_jsonl(lines)
        assert result["summary"] == "from agent"

    def test_multi_turn_completed_keeps_last(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":50}}\n'
        )
        result = _parse_jsonl(lines)
        assert result["token_usage"]["input_tokens"] == 100

    def test_turn_started_event_ignored(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "t"

    def test_only_turn_started_does_not_raise(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = '{"type":"turn.started"}\n'
        result = _parse_jsonl(lines)
        assert result["thread_id"] is None
        assert result["commands_run"] == []

    def test_non_dict_item_skipped(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"item.completed","item":"not-a-dict"}\n'
        )
        result = _parse_jsonl(lines)
        assert result["commands_run"] == []

    def test_non_dict_usage_skipped(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = (
            '{"type":"thread.started","thread_id":"t"}\n'
            '{"type":"turn.completed","usage":"not-a-dict"}\n'
        )
        result = _parse_jsonl(lines)
        assert result["token_usage"] is None


class TestOutputSchemaEnforcement:
    """R7-8: _output() validates all required fields are present."""

    def test_output_with_all_fields(self) -> None:
        from scripts.codex_delegate import _output
        result = json.loads(_output(
            "ok", dispatched=True, thread_id="t", summary=None,
            commands_run=[], exit_code=0, token_usage=None,
            runtime_failures=[], blocked_paths=[], error=None,
        ))
        assert result["status"] == "ok"

    def test_output_missing_field_asserts(self) -> None:
        from scripts.codex_delegate import _output
        with pytest.raises(AssertionError, match="missing fields"):
            _output("ok", dispatched=True)


class TestNonStringPromptRejection:
    """R7-29: Non-string prompt rejected before credential scan."""

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_list_prompt_rejected_before_scan(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": ["AKIAIOSFODNN7EXAMPLE", "fix tests"]}))
        exit_code = run(f)
        assert exit_code == 1
