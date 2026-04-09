"""Tests for containment_lifecycle.py hook behavior."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from server.containment import (
    active_run_path,
    read_json_file,
    scope_file_path,
    seed_file_path,
    smoke_control_path,
    transcript_done_path,
    transcript_error_path,
    transcript_path,
    write_json_file,
    write_text_file,
)

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "scripts" / "containment_lifecycle.py"
)


def _load_lifecycle_module():
    spec = importlib.util.spec_from_file_location(
        "test_containment_lifecycle_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_lifecycle(
    payload: dict[str, object],
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


def _seed_payload(
    *,
    session_id: str = "session-1",
    run_id: str = "run-1",
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "run_id": run_id,
        "file_anchors": ["/repo/anchor.txt"],
        "scope_directories": ["/repo"],
        "created_at": "2026-04-08T00:00:00Z",
    }


def test_subagent_start_missing_active_run_exits_cleanly(tmp_path: Path) -> None:
    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_start_promotes_seed_to_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    scope = read_json_file(scope_file_path(tmp_path, "run-1"))
    assert scope is not None
    assert scope["agent_id"] == "agent-1"
    assert not seed_file_path(tmp_path, "run-1").exists()


def test_subagent_start_duplicate_scope_is_noop(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-original",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    scope = read_json_file(scope_file_path(tmp_path, "run-1"))
    assert scope is not None
    assert scope["agent_id"] == "agent-original"
    assert seed_file_path(tmp_path, "run-1").exists()
    assert "scope already exists" in result.stderr.lower()


def test_subagent_start_smoke_control_delay_calls_sleep(tmp_path: Path) -> None:
    module = _load_lifecycle_module()
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        smoke_control_path(tmp_path, "run-1"),
        {"start_behavior": "delay", "delay_ms": 125},
    )
    calls: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    module.time.sleep = _fake_sleep
    module.handle_payload(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert calls == [0.125]
    assert scope_file_path(tmp_path, "run-1").exists()


def test_subagent_start_smoke_control_disable_leaves_seed_in_place(
    tmp_path: Path,
) -> None:
    module = _load_lifecycle_module()
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        smoke_control_path(tmp_path, "run-1"),
        {"start_behavior": "disable"},
    )

    module.handle_payload(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert not scope_file_path(tmp_path, "run-1").exists()
    assert seed_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_copies_transcript_and_removes_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )
    source = tmp_path / "agent-transcript.jsonl"
    source.write_text('{"message":"done"}\n', encoding="utf-8")

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "agent_transcript_path": str(source),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_path(tmp_path, "run-1").read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )
    assert transcript_done_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_writes_error_marker_on_copy_failure(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "agent_transcript_path": str(tmp_path / "missing.jsonl"),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_error_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_missing_transcript_path_writes_error_marker(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_error_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_agent_id_mismatch_keeps_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-expected",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-other",
            "agent_transcript_path": str(tmp_path / "missing.jsonl"),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert scope_file_path(tmp_path, "run-1").exists()
    assert not transcript_error_path(tmp_path, "run-1").exists()
