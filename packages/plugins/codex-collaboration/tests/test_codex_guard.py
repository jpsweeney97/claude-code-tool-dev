"""Tests for codex_guard.py PreToolUse hook."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "codex_guard.py")


def _load_guard_module():
    spec = importlib.util.spec_from_file_location(
        "test_codex_guard_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_hook(tool_name: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "session_id": "test-session",
        }
    )
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
    )


class TestHookAllowsCleanInput:
    def test_consult_with_clean_objective(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp/repo", "objective": "review the architecture"},
        )
        assert result.returncode == 0

    def test_status_tool_allowed(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.status",
            {"repo_root": "/tmp/repo"},
        )
        assert result.returncode == 0

    def test_non_plugin_tool_ignored(self) -> None:
        result = _run_hook("Read", {"file_path": "/etc/passwd"})
        assert result.returncode == 0

    def test_dialogue_reply_clean(self) -> None:
        """Reply schema: collaboration_id, objective, explicit_paths — no repo_root."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply",
            {"collaboration_id": "c1", "objective": "clean review"},
        )
        assert result.returncode == 0


class TestHookBlocksSecrets:
    def test_aws_key_in_objective_blocks(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": "use AKIAIOSFODNN7EXAMPLE"},
        )
        assert result.returncode == 2
        assert (
            "credential" in result.stderr.lower() or "blocked" in result.stderr.lower()
        )

    def test_openai_key_blocks(self) -> None:
        key = "sk-" + "a" * 40
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": f"key: {key}"},
        )
        assert result.returncode == 2

    def test_placeholder_context_allows(self) -> None:
        key = "sk-" + "a" * 40
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {"repo_root": "/tmp", "objective": f"example format {key}"},
        )
        assert result.returncode == 0

    def test_dialogue_reply_scans_objective(self) -> None:
        """Reply schema has collaboration_id, objective, explicit_paths — no repo_root."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply",
            {
                "collaboration_id": "c1",
                "objective": "AKIAIOSFODNN7EXAMPLE",
            },
        )
        assert result.returncode == 2

    def test_profile_with_credential_blocks(self) -> None:
        """Credential in profile field is caught — profile is a content_field."""
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
            {
                "repo_root": "/tmp",
                "objective": "clean",
                "profile": "AKIAIOSFODNN7EXAMPLE",
            },
        )
        assert result.returncode == 2


class TestHookFailsClosed:
    def test_empty_stdin_blocks(self) -> None:
        """Parse failure on empty input must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input="",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2
        assert (
            "failed to parse" in proc.stderr.lower() or "stdin" in proc.stderr.lower()
        )

    def test_malformed_json_blocks(self) -> None:
        """Invalid JSON must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input="not json",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2

    def test_unknown_plugin_tool_blocks(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.unknown",
            {"repo_root": "/tmp"},
        )
        assert result.returncode == 2
        assert "internal error" in result.stderr.lower()

    def test_missing_tool_input_blocks(self) -> None:
        """Missing tool_input on a plugin tool must fail closed."""
        proc = subprocess.run(
            [sys.executable, SCRIPT],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
                }
            ),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2

    def test_internal_error_in_check_tool_input_blocks(
        self,
        monkeypatch,
        capsys,
    ) -> None:
        module = _load_guard_module()
        import server.consultation_safety as consultation_safety

        def _boom(tool_input: object, policy: object) -> object:
            raise RuntimeError("boom")

        payload = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "mcp__plugin_codex-collaboration_codex-collaboration__codex.consult",
                "tool_input": {"repo_root": "/tmp", "objective": "clean"},
                "session_id": "test-session",
            }
        )

        monkeypatch.setattr(consultation_safety, "check_tool_input", _boom)
        monkeypatch.setattr(module.sys, "stdin", io.StringIO(payload))

        with pytest.raises(SystemExit) as excinfo:
            module.run()

        assert excinfo.value.code == 2
        assert "internal error" in capsys.readouterr().err.lower()


class TestDelegateDecideGuard:
    def test_delegate_decide_clean(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide",
            {
                "job_id": "job-1",
                "request_id": "req-1",
                "decision": "approve",
                "answers": {"q1": {"answers": ["yes"]}},
            },
        )
        assert result.returncode == 0

    def test_delegate_decide_answers_with_secret_block(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide",
            {
                "job_id": "job-1",
                "request_id": "req-1",
                "decision": "approve",
                "answers": {"q1": {"answers": ["sk-" + "a" * 40]}},
            },
        )
        assert result.returncode == 2


class TestDelegatePollGuard:
    def test_delegate_poll_clean(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll",
            {"job_id": "job-1"},
        )
        assert result.returncode == 0


class TestHookEntrypoint:
    def test_keyboard_interrupt_exits_fail_closed(self, monkeypatch, capsys) -> None:
        module = _load_guard_module()

        def _interrupt() -> int:
            raise KeyboardInterrupt

        monkeypatch.setattr(module, "main", _interrupt)

        with pytest.raises(SystemExit) as excinfo:
            module.run()

        assert excinfo.value.code == 2
        assert "interrupted" in capsys.readouterr().err.lower()
