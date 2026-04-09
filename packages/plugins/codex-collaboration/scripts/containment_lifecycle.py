#!/usr/bin/env python3
"""Subagent lifecycle hook for T4 containment state transitions."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# Add package root to sys.path for server imports.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from server.containment import (  # noqa: E402
    build_scope_from_seed,
    clean_stale_files,
    read_active_run_id,
    read_json_file,
    scope_file_path,
    seed_file_path,
    shakedown_dir,
    smoke_control_path,
    transcript_done_path,
    transcript_error_path,
    transcript_path,
    write_json_file,
    write_text_file,
)


def _plugin_data_from_env() -> Path | None:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not plugin_data:
        return None
    return Path(plugin_data).expanduser().resolve()


def handle_payload(payload: dict[str, Any], *, data_dir: Path) -> None:
    """Dispatch lifecycle behavior based on `hook_event_name`."""

    event_name = payload.get("hook_event_name")
    if event_name == "SubagentStart":
        _handle_subagent_start(payload, data_dir=data_dir)
        return
    if event_name == "SubagentStop":
        _handle_subagent_stop(payload, data_dir=data_dir)
        return
    print(
        "containment-lifecycle: unsupported hook_event_name. "
        f"Got: {event_name!r:.100}",
        file=sys.stderr,
    )


def _handle_subagent_start(payload: dict[str, Any], *, data_dir: Path) -> None:
    session_id = payload.get("session_id")
    agent_id = payload.get("agent_id")
    if not isinstance(session_id, str) or not isinstance(agent_id, str):
        return

    clean_stale_files(shakedown_dir(data_dir))
    run_id = read_active_run_id(data_dir, session_id)
    if run_id is None:
        return

    seed = read_json_file(seed_file_path(data_dir, run_id))
    if seed is None:
        return

    scope_path = scope_file_path(data_dir, run_id)
    if scope_path.exists():
        print(
            "containment-lifecycle: scope already exists for run. "
            f"Got: {run_id!r:.100}",
            file=sys.stderr,
        )
        return

    smoke_control = read_json_file(smoke_control_path(data_dir, run_id)) or {}
    start_behavior = smoke_control.get("start_behavior", "normal")
    if start_behavior == "delay":
        delay_ms = smoke_control.get("delay_ms", 0)
        if isinstance(delay_ms, (int, float)) and delay_ms > 0:
            time.sleep(float(delay_ms) / 1000.0)
    elif start_behavior == "disable":
        return
    elif start_behavior != "normal":
        print(
            "containment-lifecycle: invalid smoke-control start_behavior. "
            f"Got: {start_behavior!r:.100}",
            file=sys.stderr,
        )
        return

    scope = build_scope_from_seed(seed, agent_id)
    write_json_file(scope_path, scope)
    try:
        seed_file_path(data_dir, run_id).unlink()
    except FileNotFoundError:
        return


def _handle_subagent_stop(payload: dict[str, Any], *, data_dir: Path) -> None:
    session_id = payload.get("session_id")
    agent_id = payload.get("agent_id")
    if not isinstance(session_id, str) or not isinstance(agent_id, str):
        return

    run_id = read_active_run_id(data_dir, session_id)
    if run_id is None:
        return

    scope_path = scope_file_path(data_dir, run_id)
    scope = read_json_file(scope_path)
    if scope is None:
        return
    if scope.get("agent_id") != agent_id:
        return

    try:
        transcript_source = payload.get("agent_transcript_path")
        if not isinstance(transcript_source, str) or not transcript_source:
            raise ValueError(
                "copy transcript failed: missing agent_transcript_path. "
                f"Got: {transcript_source!r:.100}"
            )
        _copy_file_atomic(
            source=Path(transcript_source).expanduser(),
            destination=transcript_path(data_dir, run_id),
        )
        write_text_file(transcript_done_path(data_dir, run_id), "")
    except Exception as exc:
        write_text_file(transcript_error_path(data_dir, run_id), str(exc))
    finally:
        try:
            scope_path.unlink()
        except FileNotFoundError:
            pass


def _copy_file_atomic(*, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, tmp)
    os.replace(tmp, destination)


def main() -> int:
    data_dir = _plugin_data_from_env()
    if data_dir is None:
        return 0
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        handle_payload(payload, data_dir=data_dir)
    except Exception as exc:
        print(
            f"containment-lifecycle: internal error ({exc})",
            file=sys.stderr,
        )
    return 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    run()
