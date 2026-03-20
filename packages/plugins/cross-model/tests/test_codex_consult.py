"""Tests for codex_consult consultation adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestParseInput:
    """Phase A: structural parse of input JSON."""

    def test_valid_new_conversation(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "explain this code"}))
        result = _parse_input(f)
        assert result["prompt"] == "explain this code"
        assert result["sandbox"] == "read-only"
        assert result["thread_id"] is None

    def test_valid_resume(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({
            "prompt": "follow up question",
            "thread_id": "thr_abc123",
        }))
        result = _parse_input(f)
        assert result["thread_id"] == "thr_abc123"

    def test_defaults(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))
        result = _parse_input(f)
        assert result["sandbox"] == "read-only"
        assert result["reasoning_effort"] == "xhigh"
        assert result["model"] is None

    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text("not json")
        with pytest.raises(ConsultationError, match="invalid JSON"):
            _parse_input(f)

    def test_missing_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"model": "gpt-5"}))
        with pytest.raises(ConsultationError, match="prompt is required"):
            _parse_input(f)

    def test_non_string_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": ["not", "a", "string"]}))
        with pytest.raises(ConsultationError, match="prompt must be string"):
            _parse_input(f)

    def test_invalid_reasoning_effort_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "reasoning_effort": "ultra"}))
        with pytest.raises(ConsultationError, match="invalid reasoning_effort"):
            _parse_input(f)

    def test_missing_file_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        with pytest.raises(ConsultationError, match="input read failed"):
            _parse_input(tmp_path / "missing.json")


import subprocess


class TestBuildCommand:
    """Build codex exec command for new and resume conversations."""

    def test_new_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="explain this", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert cmd[:3] == ["codex", "exec", "--json"]
        assert "-s" in cmd
        idx = cmd.index("-s")
        assert cmd[idx + 1] == "read-only"
        assert "--" in cmd
        assert cmd[-1] == "explain this"

    def test_resume_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="follow up", thread_id="thr_abc", sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert cmd[:4] == ["codex", "exec", "resume", "thr_abc"]
        assert "--json" in cmd
        assert cmd[-1] == "follow up"

    def test_includes_model_when_set(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model="o3", reasoning_effort="xhigh")
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"

    def test_omits_model_when_none(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "-m" not in cmd

    def test_includes_reasoning_effort(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="high")
        assert "-c" in cmd
        idx = cmd.index("-c")
        assert cmd[idx + 1] == "model_reasoning_effort=high"

    def test_dash_prompt_protected(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="--dangerous-looking", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        dd_idx = cmd.index("--")
        assert cmd[dd_idx + 1] == "--dangerous-looking"

    def test_includes_skip_git_repo_check(self) -> None:
        """Shim runs from plugin cache (non-git dir); codex exec requires this flag."""
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "--skip-git-repo-check" in cmd

    def test_resume_includes_skip_git_repo_check(self) -> None:
        """Resume path also runs from non-git dir."""
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id="thr_abc", sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "--skip-git-repo-check" in cmd

    def test_resume_omits_sandbox_flag(self) -> None:
        """codex exec resume does not accept -s/--sandbox; sandbox is inherited from original session."""
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id="thr_abc", sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "-s" not in cmd, f"resume command should not contain -s flag, got: {cmd}"

    def test_new_conversation_includes_sandbox_flag(self) -> None:
        """New conversations must specify sandbox via -s flag."""
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "-s" in cmd
        idx = cmd.index("-s")
        assert cmd[idx + 1] == "read-only"


class TestCheckCodexVersion:
    """Version check requires >= 0.111.0."""

    def test_valid_version_passes(self) -> None:
        from scripts.codex_consult import _check_codex_version
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.116.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            _check_codex_version()

    def test_old_version_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.100.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="requires codex"):
                _check_codex_version()

    def test_missing_codex_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.side_effect = FileNotFoundError("codex not found")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="codex not found"):
                _check_codex_version()


class TestParseJsonl:
    """JSONL parsing extracts continuation_id, response, usage."""

    def _make_jsonl(self, *events: dict) -> str:
        return "\n".join(json.dumps(e) for e in events)

    def test_extracts_thread_id(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.started"}, {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_last_thread_id_wins(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_old"}, {"type": "thread.started", "thread_id": "thr_new"}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_new"

    def test_extracts_agent_message(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "The answer is 42."}}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["response_text"] == "The answer is 42."

    def test_concatenates_multiple_messages(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 1."}}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 2."}}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert "Part 1." in result["response_text"]
        assert "Part 2." in result["response_text"]

    def test_extracts_token_usage(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}})
        result = _parse_jsonl(stdout)
        assert result["token_usage"] == {"input_tokens": 100, "output_tokens": 50}

    def test_captures_runtime_failures(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.failed", "error": "model overloaded"})
        result = _parse_jsonl(stdout)
        assert "model overloaded" in result["runtime_failures"]

    def test_no_usable_events_errors(self) -> None:
        from scripts.codex_consult import _parse_jsonl, ConsultationError
        with pytest.raises(ConsultationError, match="no usable JSONL events"):
            _parse_jsonl("")

    def test_skips_malformed_lines(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = "not json\n" + json.dumps({"type": "thread.started", "thread_id": "thr_001"}) + "\n" + json.dumps({"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_null_thread_id_on_missing_event(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "turn.started"}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] is None


from unittest.mock import patch, MagicMock
import subprocess as _subprocess


class TestRunSubprocess:
    """Subprocess execution with env propagation and dispatch tracking."""

    @patch("scripts.codex_consult.subprocess")
    def test_propagates_seatbelt_env(self, mock_sub: MagicMock) -> None:
        from scripts.codex_consult import _run_subprocess
        mock_proc = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_sub.Popen.return_value = mock_proc
        mock_sub.TimeoutExpired = _subprocess.TimeoutExpired

        mock_stdout = MagicMock()
        mock_stdout.tell.return_value = 10
        mock_stdout.read.return_value = b'{"type":"turn.completed","usage":{}}'
        mock_stdout.seek = MagicMock()
        mock_stderr = MagicMock()

        with patch("scripts.codex_consult.TemporaryFile", side_effect=[mock_stdout, mock_stderr]):
            mock_stdout.__enter__ = MagicMock(return_value=mock_stdout)
            mock_stdout.__exit__ = MagicMock(return_value=False)
            mock_stderr.__enter__ = MagicMock(return_value=mock_stderr)
            mock_stderr.__exit__ = MagicMock(return_value=False)
            _run_subprocess(["codex", "exec", "--json", "--", "test"])

        call_kwargs = mock_sub.Popen.call_args
        env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
        assert env.get("CODEX_SANDBOX") == "seatbelt"

    def test_dispatch_state_values(self) -> None:
        from scripts.codex_consult import DispatchState
        assert DispatchState.NO_DISPATCH.value == "no_dispatch"
        assert DispatchState.COMPLETE.value == "complete"
        assert DispatchState.DISPATCHED_WITH_TOKEN_UNCERTAIN.value == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult.subprocess")
    def test_timeout_returns_partial_stdout(self, mock_sub: MagicMock) -> None:
        from scripts.codex_consult import _run_subprocess, SubprocessTimeout
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = _subprocess.TimeoutExpired(cmd=["codex"], timeout=300)
        mock_proc.kill = MagicMock()
        mock_sub.Popen.return_value = mock_proc
        mock_sub.TimeoutExpired = _subprocess.TimeoutExpired

        partial_jsonl = '{"type":"thread.started","thread_id":"thr_partial"}\n'
        mock_stdout = MagicMock()
        mock_stdout.tell.return_value = len(partial_jsonl)
        mock_stdout.read.return_value = partial_jsonl.encode()
        mock_stdout.seek = MagicMock()
        mock_stderr = MagicMock()

        with patch("scripts.codex_consult.TemporaryFile", side_effect=[mock_stdout, mock_stderr]):
            mock_stdout.__enter__ = MagicMock(return_value=mock_stdout)
            mock_stdout.__exit__ = MagicMock(return_value=False)
            mock_stderr.__enter__ = MagicMock(return_value=mock_stderr)
            mock_stderr.__exit__ = MagicMock(return_value=False)
            with pytest.raises(SubprocessTimeout) as exc_info:
                _run_subprocess(["codex", "exec", "--json", "--", "test"])
            assert "thr_partial" in exc_info.value.partial_stdout


class TestRun:
    """End-to-end pipeline: input → output."""

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_successful_consultation(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = ('{"type":"thread.started","thread_id":"thr_test"}\n{"type":"item.completed","item":{"type":"agent_message","text":"Hello!"}}\n{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n', 0)
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "hi"}))
        exit_code = run(f)
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "ok"
        assert output["continuation_id"] == "thr_test"
        assert output["response_text"] == "Hello!"
        assert output["dispatched"] is True

    @patch("scripts.codex_consult.check_tool_input")
    def test_credential_blocked(self, mock_safety: MagicMock, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="block", reason="AWS key detected", tier="strict")
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "AKIAIOSFODNN7EXAMPLE"}))
        exit_code = run(f)
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "blocked"
        assert output["dispatched"] is False
        assert "AWS key" in output["error"]

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_surfaces_partial_token(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        partial = '{"type":"thread.started","thread_id":"thr_partial"}\n'
        mock_run.side_effect = SubprocessTimeout(partial)
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))
        exit_code = run(f)
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "timeout_uncertain"
        assert output["continuation_id"] == "thr_partial"
        assert output["dispatch_state"] == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_without_token(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.side_effect = SubprocessTimeout("")
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))
        exit_code = run(f)
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "timeout_uncertain"
        assert output["continuation_id"] is None
        assert output["dispatch_state"] == "dispatched_no_token"

    def test_invalid_input_returns_error(self, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run
        f = tmp_path / "input.json"
        f.write_text("not json")
        exit_code = run(f)
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "error"
        assert output["dispatched"] is False

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_resume_uses_thread_id(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = ('{"type":"thread.started","thread_id":"thr_resumed"}\n{"type":"item.completed","item":{"type":"agent_message","text":"Continued."}}\n{"type":"turn.completed","usage":{}}\n', 0)
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "continue", "thread_id": "thr_original"}))
        exit_code = run(f)
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["continuation_id"] == "thr_resumed"


class TestOutput:
    """Output format validation."""

    def test_all_required_fields_present(self, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run
        f = tmp_path / "input.json"
        f.write_text("not json")
        run(f)
        output = json.loads(capsys.readouterr().out)
        required = {"status", "dispatched", "continuation_id", "response_text", "token_usage", "runtime_failures", "error", "dispatch_state"}
        assert required.issubset(set(output.keys()))


class TestConsult:
    """Programmatic API: consult() — same pipeline as run() without file I/O."""

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_success(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_api"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Response via API."}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n',
            0,
        )
        result = consult(prompt="test prompt")
        assert result["status"] == "ok"
        assert result["dispatched"] is True
        assert result["continuation_id"] == "thr_api"
        assert result["response_text"] == "Response via API."
        assert result["token_usage"] == {"input_tokens": 10, "output_tokens": 5}
        assert result["dispatch_state"] == "complete"
        assert result["error"] is None

    @patch("scripts.codex_consult.check_tool_input")
    def test_credential_block(self, mock_safety: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="block", reason="AWS key", tier="strict")
        result = consult(prompt="AKIAIOSFODNN7EXAMPLE")
        assert result["status"] == "blocked"
        assert result["dispatched"] is False
        assert "AWS key" in result["error"]
        assert result["dispatch_state"] == "no_dispatch"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_with_partial_token(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.side_effect = SubprocessTimeout('{"type":"thread.started","thread_id":"thr_partial"}\n')
        result = consult(prompt="test")
        assert result["status"] == "timeout_uncertain"
        assert result["continuation_id"] == "thr_partial"
        assert result["dispatch_state"] == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_passes_thread_id_to_build_command(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_resumed"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Continued."}}\n'
            '{"type":"turn.completed","usage":{}}\n',
            0,
        )
        result = consult(prompt="continue", thread_id="thr_original")
        assert result["status"] == "ok"
        cmd = mock_run.call_args[0][0]
        assert "resume" in cmd
        assert "thr_original" in cmd

    def test_invalid_reasoning_effort(self) -> None:
        from scripts.codex_consult import consult
        result = consult(prompt="test", reasoning_effort="ultra")
        assert result["status"] == "error"
        assert "reasoning_effort" in result["error"]
        assert result["dispatched"] is False
