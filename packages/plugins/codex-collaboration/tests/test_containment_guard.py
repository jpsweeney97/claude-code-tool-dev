"""Tests for containment_guard.py PreToolUse hook behavior."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from server.containment import (
    active_run_path,
    poll_telemetry_path,
    scope_file_path,
    seed_file_path,
    write_json_file,
    write_text_file,
)

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "scripts" / "containment_guard.py"
)


def _load_guard_module():
    spec = importlib.util.spec_from_file_location(
        "test_containment_guard_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_guard(
    payload: dict[str, Any],
    *,
    data_dir: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_DATA"] = str(data_dir)
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def _make_scope_fixture(tmp_path: Path) -> dict[str, str]:
    repo = tmp_path / "repo"
    scope_dir = repo / "scope"
    nested_dir = scope_dir / "nested"
    scope_dir.mkdir(parents=True)
    nested_dir.mkdir()
    anchor = scope_dir / "anchor.txt"
    sibling = nested_dir / "sibling.txt"
    outside = repo / "outside.txt"
    anchor.write_text("anchor", encoding="utf-8")
    sibling.write_text("sibling", encoding="utf-8")
    outside.write_text("outside", encoding="utf-8")
    return {
        "anchor": str(anchor),
        "outside": str(outside),
        "scope_dir": str(scope_dir),
        "sibling": str(sibling),
    }


def _activate_scope(
    data_dir: Path,
    *,
    session_id: str = "session-1",
    run_id: str = "run-1",
    agent_id: str = "agent-1",
    file_anchors: list[str],
    scope_directories: list[str],
) -> None:
    write_text_file(active_run_path(data_dir, session_id), run_id)
    write_json_file(
        scope_file_path(data_dir, run_id),
        {
            "session_id": session_id,
            "run_id": run_id,
            "agent_id": agent_id,
            "file_anchors": file_anchors,
            "scope_directories": scope_directories,
            "created_at": "2026-04-08T00:00:00Z",
        },
    )


def _seed_scope(
    data_dir: Path,
    *,
    session_id: str = "session-1",
    run_id: str = "run-1",
    file_anchors: list[str],
    scope_directories: list[str],
) -> None:
    write_text_file(active_run_path(data_dir, session_id), run_id)
    write_json_file(
        seed_file_path(data_dir, run_id),
        {
            "session_id": session_id,
            "run_id": run_id,
            "file_anchors": file_anchors,
            "scope_directories": scope_directories,
            "created_at": "2026-04-08T00:00:00Z",
        },
    )


def _payload(
    *,
    tool_name: str,
    tool_input: dict[str, object],
    session_id: str = "session-1",
    agent_id: str | None = "agent-1",
    cwd: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "session_id": session_id,
    }
    if agent_id is not None:
        payload["agent_id"] = agent_id
    if cwd is not None:
        payload["cwd"] = cwd
    return payload


def _read_telemetry(data_dir: Path) -> list[dict[str, Any]]:
    path = poll_telemetry_path(data_dir)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _stdout_json(result: subprocess.CompletedProcess[str]) -> dict[str, Any] | None:
    text = result.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def test_main_thread_passthrough_emits_no_telemetry(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["outside"]},
            agent_id=None,
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert _read_telemetry(tmp_path) == []


def test_no_active_run_pointer_passthrough(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["outside"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert _read_telemetry(tmp_path) == []


def test_agent_id_mismatch_passthrough(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        agent_id="other-agent",
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["outside"]},
            agent_id="agent-1",
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert _read_telemetry(tmp_path) == []


def test_read_allow_anchor_records_branch(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert output["hookSpecificOutput"]["updatedInput"]["file_path"] == os.path.realpath(fixture["anchor"])
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "read_allow_anchor"


def test_read_allow_scope_directory_records_branch(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["sibling"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "read_allow_scope_directory"


def test_read_deny_out_of_scope_returns_deny_json(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["outside"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "read_deny_out_of_scope"


def test_grep_rewrite_preserves_all_fields(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Grep",
            tool_input={
                "pattern": "anchor",
                "path": fixture["anchor"],
                "glob": "*.txt",
                "output_mode": "content",
                "-i": True,
                "multiline": False,
            },
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    updated = output["hookSpecificOutput"]["updatedInput"]
    assert updated == {
        "pattern": "anchor",
        "path": fixture["anchor"],
        "glob": "*.txt",
        "output_mode": "content",
        "-i": True,
        "multiline": False,
    }
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "grep_rewrite_path_targeted"


def test_glob_rewrite_targets_scope_directory(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Glob",
            tool_input={"pattern": "**/*.txt", "path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["updatedInput"]["path"] == fixture["scope_dir"]
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "glob_rewrite_path_targeted"


def test_grep_pathless_deny_lists_scope_directories(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Grep",
            tool_input={"pattern": "anchor"},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert fixture["scope_dir"] in output["hookSpecificOutput"]["permissionDecisionReason"]
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "grep_pathless_deny"


def test_grep_out_of_scope_deny_records_branch(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Grep",
            tool_input={"pattern": "outside", "path": fixture["outside"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "grep_deny_out_of_scope"


def test_glob_pathless_deny_lists_scope_directories(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Glob",
            tool_input={"pattern": "**/*.txt"},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert fixture["scope_dir"] in output["hookSpecificOutput"]["permissionDecisionReason"]
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "glob_pathless_deny"


def test_glob_out_of_scope_deny_records_branch(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Glob",
            tool_input={"pattern": "*.txt", "path": fixture["outside"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "glob_deny_out_of_scope"


def test_poll_success_records_branch(tmp_path: Path) -> None:
    module = _load_guard_module()
    fixture = _make_scope_fixture(tmp_path)
    _seed_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    def _promote_scope() -> None:
        write_json_file(
            scope_file_path(tmp_path, "run-1"),
            {
                "session_id": "session-1",
                "run_id": "run-1",
                "agent_id": "agent-1",
                "file_anchors": [fixture["anchor"]],
                "scope_directories": [fixture["scope_dir"]],
                "created_at": "2026-04-08T00:00:00Z",
            },
        )

    timer = threading.Timer(0.02, _promote_scope)
    timer.start()
    response = module.evaluate_payload(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
        poll_interval_seconds=0.005,
        poll_timeout_seconds=0.1,
    )
    timer.join()

    assert response is not None
    assert response["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "poll_success"


def test_poll_timeout_deny_records_branch(tmp_path: Path) -> None:
    module = _load_guard_module()
    fixture = _make_scope_fixture(tmp_path)
    _seed_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    response = module.evaluate_payload(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
        poll_interval_seconds=0.005,
        poll_timeout_seconds=0.02,
    )

    assert response is not None
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "poll_timeout_deny"


def test_empty_active_run_pointer_denies(tmp_path: Path) -> None:
    """Empty active-run pointer file → deny, not passthrough."""
    fixture = _make_scope_fixture(tmp_path)
    pointer = active_run_path(tmp_path, "session-1")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("", encoding="utf-8")

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "empty" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_malformed_scope_denies_when_active_run(tmp_path: Path) -> None:
    """Corrupt scope file with active-run pointer → deny, not passthrough."""
    fixture = _make_scope_fixture(tmp_path)
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    scope = scope_file_path(tmp_path, "run-1")
    scope.parent.mkdir(parents=True, exist_ok=True)
    scope.write_text("{corrupt", encoding="utf-8")

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_malformed_seed_denies_when_active_run(tmp_path: Path) -> None:
    """Corrupt seed (no scope) with active-run pointer → deny, not passthrough."""
    fixture = _make_scope_fixture(tmp_path)
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    seed = seed_file_path(tmp_path, "run-1")
    seed.parent.mkdir(parents=True, exist_ok=True)
    seed.write_text("{corrupt", encoding="utf-8")

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_parse_failure_passthroughs(tmp_path: Path) -> None:
    """Invalid stdin → passthrough (no deny) when active state unverifiable."""
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_DATA"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input="not valid json",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert "invalid hook payload" in result.stderr


def test_missing_plugin_data_logs_and_passthroughs(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.pop("CLAUDE_PLUGIN_DATA", None)
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(_payload(tool_name="Read", tool_input={"file_path": "/tmp/x"})),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert "CLAUDE_PLUGIN_DATA missing" in result.stderr


def test_invalid_scope_structure_denies_without_passthrough(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            "session_id": "session-1",
            "run_id": "run-1",
            "agent_id": "agent-1",
            "file_anchors": 42,
            "scope_directories": [fixture["scope_dir"]],
            "created_at": "2026-04-08T00:00:00Z",
        },
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "invalid scope file" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_payload_requires_fail_closed_on_invalid_scope_shape(tmp_path: Path) -> None:
    module = _load_guard_module()
    fixture = _make_scope_fixture(tmp_path)
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            "session_id": "session-1",
            "run_id": "run-1",
            "agent_id": "agent-1",
            "file_anchors": 42,
            "scope_directories": [fixture["scope_dir"]],
            "created_at": "2026-04-08T00:00:00Z",
        },
    )

    assert module._payload_requires_fail_closed(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )


def test_payload_requires_fail_closed_false_for_other_agent_scope(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    module = _load_guard_module()
    _activate_scope(
        tmp_path,
        agent_id="other-agent",
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    assert not module._payload_requires_fail_closed(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["outside"]},
            agent_id="agent-1",
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )


def test_payload_requires_fail_closed_true_for_seed_bootstrap(tmp_path: Path) -> None:
    fixture = _make_scope_fixture(tmp_path)
    module = _load_guard_module()
    _seed_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    assert module._payload_requires_fail_closed(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )


def test_main_denies_when_fail_closed_probe_crashes(tmp_path: Path) -> None:
    module = _load_guard_module()
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )
    payload_text = json.dumps(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"]},
            cwd=fixture["scope_dir"],
        )
    )
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    original_stdin = module.sys.stdin
    original_env = os.environ.get("CLAUDE_PLUGIN_DATA")
    module.sys.stdin = io.StringIO(payload_text)
    os.environ["CLAUDE_PLUGIN_DATA"] = str(tmp_path)

    def _raise_eval(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom")

    def _raise_probe(*args: object, **kwargs: object) -> bool:
        raise RuntimeError("probe boom")

    original_evaluate_payload = module.evaluate_payload
    original_fail_closed = module._payload_requires_fail_closed
    module.evaluate_payload = _raise_eval
    module._payload_requires_fail_closed = _raise_probe
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exit_code = module.main()
    finally:
        module.evaluate_payload = original_evaluate_payload
        module._payload_requires_fail_closed = original_fail_closed
        module.sys.stdin = original_stdin
        if original_env is None:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        else:
            os.environ["CLAUDE_PLUGIN_DATA"] = original_env

    assert exit_code == 0
    output = json.loads(stdout_buffer.getvalue())
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "internal error" in output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "fail-closed probe crashed" in stderr_buffer.getvalue()


def test_telemetry_write_failure_preserves_read_allow(tmp_path: Path) -> None:
    """Telemetry append failure does not change Read allow → deny."""
    module = _load_guard_module()
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    def _raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    original = module.append_jsonl
    module.append_jsonl = _raise_oserror
    try:
        response = module.evaluate_payload(
            _payload(
                tool_name="Read",
                tool_input={"file_path": fixture["anchor"]},
                cwd=fixture["scope_dir"],
            ),
            data_dir=tmp_path,
        )
    finally:
        module.append_jsonl = original

    assert response is not None
    assert response["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert response["hookSpecificOutput"]["updatedInput"]["file_path"] == os.path.realpath(
        fixture["anchor"]
    )


def test_glob_rewrite_preserves_all_fields(tmp_path: Path) -> None:
    """Glob rewrite preserves all input fields (not just path)."""
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Glob",
            tool_input={
                "pattern": "**/*.txt",
                "path": fixture["anchor"],
                "head_limit": 50,
            },
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    updated = output["hookSpecificOutput"]["updatedInput"]
    assert updated["pattern"] == "**/*.txt"
    assert updated["path"] == fixture["scope_dir"]
    assert updated["head_limit"] == 50
    assert _read_telemetry(tmp_path)[0]["branch_id"] == "glob_rewrite_path_targeted"


def test_read_allow_returns_updated_input(tmp_path: Path) -> None:
    """Read allow returns updatedInput with canonical file_path."""
    fixture = _make_scope_fixture(tmp_path)
    _activate_scope(
        tmp_path,
        file_anchors=[fixture["anchor"]],
        scope_directories=[fixture["scope_dir"]],
    )

    result = _run_guard(
        _payload(
            tool_name="Read",
            tool_input={"file_path": fixture["anchor"], "limit": 100},
            cwd=fixture["scope_dir"],
        ),
        data_dir=tmp_path,
    )

    output = _stdout_json(result)
    assert result.returncode == 0
    assert output is not None
    assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
    updated = output["hookSpecificOutput"]["updatedInput"]
    assert updated["file_path"] == os.path.realpath(fixture["anchor"])
    assert updated["limit"] == 100
