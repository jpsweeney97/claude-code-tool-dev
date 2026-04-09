#!/usr/bin/env python3
"""PreToolUse containment guard for T4 Read, Grep, and Glob confinement."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add package root to sys.path for server imports.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from server.containment import (  # noqa: E402
    append_jsonl,
    is_path_within_scope,
    poll_telemetry_path,
    read_active_run_id,
    read_active_run_id_strict,
    read_json_file,
    read_json_file_strict,
    scope_file_path,
    seed_file_path,
    select_scope_root,
)

_GUARDED_TOOLS = frozenset(("Read", "Grep", "Glob"))
_POLL_INTERVAL_SECONDS = 0.1
_POLL_TIMEOUT_SECONDS = 2.0


def _plugin_data_from_env() -> Path | None:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not plugin_data:
        return None
    return Path(plugin_data).expanduser().resolve()


def evaluate_payload(
    payload: dict[str, Any],
    *,
    data_dir: Path,
    poll_interval_seconds: float = _POLL_INTERVAL_SECONDS,
    poll_timeout_seconds: float = _POLL_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Return hook JSON output, or None for passthrough."""

    tool_name = payload.get("tool_name")
    if tool_name not in _GUARDED_TOOLS:
        return None

    agent_id = payload.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return None

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return _deny("containment-guard: missing session_id for subagent tool call")

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return _deny("containment-guard: missing or invalid tool_input")

    cwd = payload.get("cwd")
    resolved_cwd = cwd if isinstance(cwd, str) and cwd else None

    try:
        run_id = read_active_run_id_strict(data_dir, session_id)
    except ValueError as exc:
        return _deny(f"containment-guard: {exc}")
    if run_id is None:
        return None

    # Active run exists. Corrupt state → deny, not passthrough.
    try:
        scope = read_json_file_strict(scope_file_path(data_dir, run_id))
    except ValueError as exc:
        return _deny(f"containment-guard: {exc}")

    if scope is None:
        try:
            seed = read_json_file_strict(seed_file_path(data_dir, run_id))
        except ValueError as exc:
            return _deny(f"containment-guard: {exc}")
        if seed is None:
            return None
        try:
            scope = _poll_for_scope(
                data_dir=data_dir,
                run_id=run_id,
                poll_interval_seconds=poll_interval_seconds,
                poll_timeout_seconds=poll_timeout_seconds,
            )
        except ValueError as exc:
            return _deny(f"containment-guard: {exc}")
        if scope is None:
            _try_append_branch_telemetry(
                data_dir=data_dir,
                branch_id="poll_timeout_deny",
                payload=payload,
                run_id=run_id,
                decision="deny",
                query_path=_query_path_for_tool(tool_name, tool_input),
                rewritten_path=None,
            )
            return _deny(
                "Containment scope not established within 2s — "
                "SubagentStart may have failed or ordering gap exceeds poll window."
            )
        if scope.get("agent_id") != agent_id:
            return None
        return _enforce_active_scope(
            payload=payload,
            data_dir=data_dir,
            run_id=run_id,
            scope=scope,
            tool_name=tool_name,
            tool_input=tool_input,
            cwd=resolved_cwd,
            poll_succeeded=True,
        )

    if scope.get("agent_id") != agent_id:
        return None

    return _enforce_active_scope(
        payload=payload,
        data_dir=data_dir,
        run_id=run_id,
        scope=scope,
        tool_name=tool_name,
        tool_input=tool_input,
        cwd=resolved_cwd,
        poll_succeeded=False,
    )


def _enforce_active_scope(
    *,
    payload: dict[str, Any],
    data_dir: Path,
    run_id: str,
    scope: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    cwd: str | None,
    poll_succeeded: bool,
) -> dict[str, Any] | None:
    file_anchors = scope.get("file_anchors")
    scope_directories = scope.get("scope_directories")
    if not _is_string_list(file_anchors) or not _is_string_list(scope_directories):
        raise ValueError(
            "containment-guard failed: invalid scope file. "
            f"Got: {scope!r:.100}"
        )

    if tool_name == "Read":
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return _deny("containment-guard: missing file_path for Read")
        in_scope = is_path_within_scope(
            file_path,
            list(file_anchors),
            list(scope_directories),
            cwd=cwd,
        )
        if not in_scope:
            _try_append_branch_telemetry(
                data_dir=data_dir,
                branch_id="read_deny_out_of_scope",
                payload=payload,
                run_id=run_id,
                decision="deny",
                query_path=file_path,
                rewritten_path=None,
            )
            return _deny(
                "Requested Read path is outside the shakedown scope. "
                f"Reissue under one of: {_format_scope_directories(list(scope_directories))}"
            )
        resolved_path = _resolve_query_path(file_path, cwd=cwd)
        decision = _allow({**tool_input, "file_path": resolved_path})
        try:
            branch_id = "poll_success" if poll_succeeded else _read_allow_branch_id(
                file_path,
                list(file_anchors),
                cwd=cwd,
            )
        except Exception:
            branch_id = "read_allow_unknown"
        _try_append_branch_telemetry(
            data_dir=data_dir,
            branch_id=branch_id,
            payload=payload,
            run_id=run_id,
            decision="allow",
            query_path=file_path,
            rewritten_path=resolved_path,
        )
        return decision

    if tool_name == "Grep":
        path_value = tool_input.get("path")
        if path_value is None:
            _try_append_branch_telemetry(
                data_dir=data_dir,
                branch_id="grep_pathless_deny",
                payload=payload,
                run_id=run_id,
                decision="deny",
                query_path=None,
                rewritten_path=None,
            )
            return _deny(_pathless_reason("Grep", list(scope_directories)))
        if not isinstance(path_value, str) or not path_value:
            return _deny("containment-guard: invalid path for Grep")
        rewritten = select_scope_root(
            list(file_anchors),
            list(scope_directories),
            path_value,
            tool_name,
            cwd=cwd,
        )
        if rewritten is None:
            return _deny(_out_of_scope_reason("Grep", list(scope_directories)))
        decision = _allow({**tool_input, "path": rewritten})
        branch_id = "poll_success" if poll_succeeded else "grep_rewrite_path_targeted"
        _try_append_branch_telemetry(
            data_dir=data_dir,
            branch_id=branch_id,
            payload=payload,
            run_id=run_id,
            decision="allow",
            query_path=path_value,
            rewritten_path=rewritten,
        )
        return decision

    path_value = tool_input.get("path")
    if path_value is None:
        _try_append_branch_telemetry(
            data_dir=data_dir,
            branch_id="glob_pathless_deny",
            payload=payload,
            run_id=run_id,
            decision="deny",
            query_path=None,
            rewritten_path=None,
        )
        return _deny(_pathless_reason("Glob", list(scope_directories)))
    if not isinstance(path_value, str) or not path_value:
        return _deny("containment-guard: invalid path for Glob")
    rewritten = select_scope_root(
        list(file_anchors),
        list(scope_directories),
        path_value,
        tool_name,
        cwd=cwd,
    )
    if rewritten is None:
        return _deny(_out_of_scope_reason("Glob", list(scope_directories)))
    decision = _allow({**tool_input, "path": rewritten})
    branch_id = "poll_success" if poll_succeeded else "glob_rewrite_path_targeted"
    _try_append_branch_telemetry(
        data_dir=data_dir,
        branch_id=branch_id,
        payload=payload,
        run_id=run_id,
        decision="allow",
        query_path=path_value,
        rewritten_path=rewritten,
    )
    return decision


def _poll_for_scope(
    *,
    data_dir: Path,
    run_id: str,
    poll_interval_seconds: float,
    poll_timeout_seconds: float,
) -> dict[str, Any] | None:
    deadline = time.monotonic() + poll_timeout_seconds
    scope_path = scope_file_path(data_dir, run_id)
    while True:
        scope = read_json_file_strict(scope_path)
        if scope is not None:
            return scope
        if time.monotonic() >= deadline:
            return None
        time.sleep(poll_interval_seconds)


def _append_branch_telemetry(
    *,
    data_dir: Path,
    branch_id: str,
    payload: dict[str, Any],
    run_id: str,
    decision: str,
    query_path: str | None,
    rewritten_path: str | None,
) -> None:
    append_jsonl(
        poll_telemetry_path(data_dir),
        {
            "agent_id": payload.get("agent_id"),
            "branch_id": branch_id,
            "decision": decision,
            "query_path": query_path,
            "recorded_at": _timestamp(),
            "rewritten_path": rewritten_path,
            "run_id": run_id,
            "session_id": payload.get("session_id"),
            "tool_name": payload.get("tool_name"),
        },
    )


def _try_append_branch_telemetry(**kwargs: Any) -> None:
    """Best-effort telemetry — never affects authorization decisions."""
    try:
        _append_branch_telemetry(**kwargs)
    except Exception:
        pass


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _allow(updated_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated_input,
        }
    }


def _read_allow_branch_id(
    file_path: str,
    file_anchors: list[str],
    *,
    cwd: str | None,
) -> str:
    resolved_path = _resolve_query_path(file_path, cwd=cwd)
    resolved_anchors = {_resolve_query_path(anchor, cwd=None) for anchor in file_anchors}
    if resolved_path in resolved_anchors:
        return "read_allow_anchor"
    return "read_allow_scope_directory"


def _resolve_query_path(path_value: str, *, cwd: str | None) -> str:
    path = Path(path_value).expanduser()
    if not path.is_absolute() and cwd is not None:
        path = Path(cwd).expanduser() / path
    return str(Path(os.path.realpath(str(path))))


def _query_path_for_tool(
    tool_name: str,
    tool_input: dict[str, Any],
) -> str | None:
    if tool_name == "Read":
        value = tool_input.get("file_path")
        return value if isinstance(value, str) else None
    value = tool_input.get("path")
    return value if isinstance(value, str) else None


def _pathless_reason(tool_name: str, scope_directories: list[str]) -> str:
    return (
        f"{tool_name} requires an explicit path under the shakedown scope. "
        "Reissue with `path` set to one of: "
        f"{_format_scope_directories(scope_directories)}"
    )


def _out_of_scope_reason(tool_name: str, scope_directories: list[str]) -> str:
    return (
        f"{tool_name} path is outside the shakedown scope. "
        "Reissue under one of: "
        f"{_format_scope_directories(scope_directories)}"
    )


def _format_scope_directories(scope_directories: list[str]) -> str:
    return ", ".join(scope_directories)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _payload_requires_fail_closed(payload: dict[str, Any], *, data_dir: Path) -> bool:
    agent_id = payload.get("agent_id")
    session_id = payload.get("session_id")
    if not isinstance(agent_id, str) or not agent_id:
        return False
    if not isinstance(session_id, str) or not session_id:
        return True
    run_id = read_active_run_id(data_dir, session_id)
    if run_id is None:
        return False
    scope = read_json_file(scope_file_path(data_dir, run_id))
    if scope is not None and scope.get("agent_id") == agent_id:
        return True
    seed = read_json_file(seed_file_path(data_dir, run_id))
    return seed is not None


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
        response = evaluate_payload(payload, data_dir=data_dir)
    except Exception as exc:
        if _payload_requires_fail_closed(payload, data_dir=data_dir):
            print(
                json.dumps(
                    _deny(f"containment-guard: internal error ({exc})"),
                )
            )
        return 0
    if response is not None:
        print(json.dumps(response))
    return 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(json.dumps(_deny("containment-guard: interrupted")))
        sys.exit(0)


if __name__ == "__main__":
    run()
