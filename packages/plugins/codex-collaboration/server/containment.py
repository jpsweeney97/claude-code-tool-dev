"""Shared containment helpers for the T4 shakedown lifecycle."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_SHAKEDOWN_DIRNAME = "shakedown"
_STALE_PATTERNS = (
    "active-run-*",
    "seed-*.json",
    "scope-*.json",
    "smoke-control-*.json",
    "ordering-marker-*.json",
    "ordering-result-*.json",
    "transcript-*.done",
    "transcript-*.error",
)


def shakedown_dir(data_dir: Path) -> Path:
    """Return the shakedown state directory under the plugin data root."""

    return data_dir / _SHAKEDOWN_DIRNAME


def active_run_path(data_dir: Path, session_id: str) -> Path:
    """Return the path for the active-run pointer for `session_id`."""

    return shakedown_dir(data_dir) / f"active-run-{session_id}"


def seed_file_path(data_dir: Path, run_id: str) -> Path:
    """Return the path for the seed file for `run_id`."""

    return shakedown_dir(data_dir) / f"seed-{run_id}.json"


def scope_file_path(data_dir: Path, run_id: str) -> Path:
    """Return the path for the scope file for `run_id`."""

    return shakedown_dir(data_dir) / f"scope-{run_id}.json"


def smoke_control_path(data_dir: Path, run_id: str) -> Path:
    """Return the path for the optional smoke-control file for `run_id`."""

    return shakedown_dir(data_dir) / f"smoke-control-{run_id}.json"


def transcript_path(data_dir: Path, run_id: str) -> Path:
    """Return the path for the copied shakedown transcript for `run_id`."""

    return shakedown_dir(data_dir) / f"transcript-{run_id}.jsonl"


def transcript_done_path(data_dir: Path, run_id: str) -> Path:
    """Return the completion marker path for `run_id`."""

    return shakedown_dir(data_dir) / f"transcript-{run_id}.done"


def transcript_error_path(data_dir: Path, run_id: str) -> Path:
    """Return the error marker path for `run_id`."""

    return shakedown_dir(data_dir) / f"transcript-{run_id}.error"


def poll_telemetry_path(data_dir: Path) -> Path:
    """Return the JSONL telemetry path for containment branch coverage."""

    return shakedown_dir(data_dir) / "poll-telemetry.jsonl"


def read_active_run_id(data_dir: Path, session_id: str) -> str | None:
    """Read the current run id for `session_id`, if one is published."""

    path = active_run_path(data_dir, session_id)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def read_active_run_id_strict(data_dir: Path, session_id: str) -> str | None:
    """Return the current run id for `session_id`, or None if no pointer exists.

    Raises ValueError if the pointer exists but is unreadable or empty.
    """

    path = active_run_path(data_dir, session_id)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"read active-run failed: {path.name} unreadable. Got: {exc!r:.100}"
        ) from exc
    if not value:
        raise ValueError(
            f"read active-run failed: {path.name} is empty"
        )
    return value


def read_json_file(path: Path) -> dict[str, Any] | None:
    """Return a JSON object from `path`, or None if missing or malformed."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def read_json_file_strict(path: Path) -> dict[str, Any] | None:
    """Return a JSON object from `path`, or None if the file does not exist.

    Raises ValueError if the file exists but is unreadable or malformed.
    """

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"read state file failed: {path.name} unreadable. Got: {exc!r:.100}"
        ) from exc
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ValueError(
            f"read state file failed: {path.name} malformed. Got: {exc!r:.100}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"read state file failed: {path.name} not a JSON object. "
            f"Got: {type(data).__name__}"
        )
    return data


def write_text_file(path: Path, content: str) -> None:
    """Write text atomically with fsync and replace semantics."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_json_file(path: Path, data: dict[str, Any]) -> None:
    """Write a JSON object atomically with fsync and replace semantics."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append a JSON record to `path` and fsync before returning."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def build_scope_from_seed(seed: dict[str, Any], agent_id: str) -> dict[str, Any]:
    """Return the scope payload derived from a seed file and `agent_id`."""

    session_id = seed.get("session_id")
    run_id = seed.get("run_id")
    file_anchors = seed.get("file_anchors")
    scope_directories = seed.get("scope_directories")
    created_at = seed.get("created_at")
    if not isinstance(session_id, str):
        raise ValueError(f"build_scope_from_seed failed: invalid session_id. Got: {session_id!r:.100}")
    if not isinstance(run_id, str):
        raise ValueError(f"build_scope_from_seed failed: invalid run_id. Got: {run_id!r:.100}")
    if not isinstance(created_at, str):
        raise ValueError(f"build_scope_from_seed failed: invalid created_at. Got: {created_at!r:.100}")
    if not _is_string_list(file_anchors):
        raise ValueError(
            f"build_scope_from_seed failed: invalid file_anchors. Got: {file_anchors!r:.100}"
        )
    if not _is_string_list(scope_directories):
        raise ValueError(
            "build_scope_from_seed failed: invalid scope_directories. "
            f"Got: {scope_directories!r:.100}"
        )
    return {
        "session_id": session_id,
        "run_id": run_id,
        "agent_id": agent_id,
        "file_anchors": list(file_anchors),
        "scope_directories": list(scope_directories),
        "created_at": created_at,
    }


def derive_scope_directories(file_anchors: list[str]) -> list[str]:
    """Return deduplicated parent directories for the given file anchors."""

    directories: list[str] = []
    seen: set[str] = set()
    for anchor in file_anchors:
        resolved_parent = os.path.realpath(str(Path(anchor).expanduser().parent))
        if resolved_parent in seen:
            continue
        seen.add(resolved_parent)
        directories.append(resolved_parent)
    return directories


def is_path_within_scope(
    file_path: str,
    file_anchors: list[str],
    scope_directories: list[str],
    *,
    cwd: str | None = None,
) -> bool:
    """Return True when `file_path` is a file anchor or inside a scope directory."""

    candidate = _resolve_candidate_path(file_path, cwd=cwd)
    anchors = _normalize_paths(file_anchors)
    directories = _normalize_paths(scope_directories)
    if any(candidate == anchor for anchor in anchors):
        return True
    return any(_path_is_within(candidate, directory) for directory in directories)


def select_scope_root(
    file_anchors: list[str],
    scope_directories: list[str],
    query_path: str | None,
    tool_name: str,
    *,
    cwd: str | None = None,
) -> str | None:
    """Select the shallowest matching file anchor or scope directory for Grep/Glob."""

    if query_path is None:
        return None
    candidate = _resolve_candidate_path(query_path, cwd=cwd)
    anchors = _normalize_paths(file_anchors)
    directories = _normalize_paths(scope_directories)
    if tool_name == "Grep":
        matching_anchors = [anchor for anchor in anchors if candidate == anchor]
        if matching_anchors:
            return str(_select_shallowest(matching_anchors))
        matching_directories = [
            directory for directory in directories if _path_is_within(candidate, directory)
        ]
        if matching_directories:
            return str(_select_shallowest(matching_directories))
        return None
    if tool_name == "Glob":
        matching_directories = [
            directory for directory in directories if _path_is_within(candidate, directory)
        ]
        if matching_directories:
            return str(_select_shallowest(matching_directories))
        return None
    raise ValueError(
        f"select_scope_root failed: unsupported tool_name. Got: {tool_name!r:.100}"
    )


def clean_stale_files(shakedown_path: Path, max_age_hours: int = 24) -> None:
    """Remove stale shakedown state files older than `max_age_hours`."""

    if not shakedown_path.exists():
        return
    cutoff = max_age_hours * 3600
    current_time = time.time()
    for pattern in _STALE_PATTERNS:
        for path in shakedown_path.glob(pattern):
            if not path.is_file():
                continue
            try:
                age_seconds = current_time - path.stat().st_mtime
            except OSError:
                continue
            if age_seconds <= cutoff:
                continue
            try:
                path.unlink()
            except OSError:
                continue


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _normalize_paths(values: list[str]) -> list[Path]:
    unique: dict[str, Path] = {}
    for value in values:
        resolved = Path(os.path.realpath(value))
        unique[str(resolved)] = resolved
    return list(unique.values())


def _resolve_candidate_path(path_value: str, *, cwd: str | None) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute() and cwd is not None:
        path = Path(cwd).expanduser() / path
    return Path(os.path.realpath(str(path)))


def _path_is_within(candidate: Path, scope_root: Path) -> bool:
    try:
        candidate.relative_to(scope_root)
        return True
    except ValueError:
        return False


def _select_shallowest(paths: list[Path]) -> Path:
    return min(paths, key=lambda path: (len(path.parts), str(path)))
