"""Shared containment helpers for the T4 shakedown lifecycle."""

from __future__ import annotations

import fnmatch
import json
import os
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from stat import S_ISDIR, S_ISREG

_SHAKEDOWN_DIRNAME = "shakedown"
_STALE_PATTERNS = (
    "active-run-*",
    "seed-*.json",
    "scope-*.json",
    "metadata-*.json",
    "transcript-*.jsonl",
    "smoke-control-*.json",
    "ordering-marker-*.json",
    "ordering-result-*.json",
    "inspection-*.md",
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


@dataclass(frozen=True)
class CleanStaleResult:
    """Outcome of a :func:`clean_stale_files` sweep.

    Attributes:
        removed: Paths that were successfully unlinked.
        skipped_fresh: Paths under the age cutoff that were left in place.
        failed_stat: ``(path, error_repr)`` pairs where ``stat()`` raised
            ``OSError`` on an individual file. These files could not be
            checked for age and were not attempted for deletion.
        failed_unlink: ``(path, error_repr)`` pairs where ``unlink()`` raised
            ``OSError`` after a successful stat. The file is still on disk.

    Root-level access failures (an absent-but-existing root entry, an
    unreadable root, a dangling symlink root, or a root path that is not
    a directory) are raised rather than captured here, because they
    indicate a global abort condition rather than a per-file outcome.
    """

    removed: tuple[Path, ...]
    skipped_fresh: tuple[Path, ...]
    failed_stat: tuple[tuple[Path, str], ...]
    failed_unlink: tuple[tuple[Path, str], ...]

    @property
    def had_errors(self) -> bool:
        """Return True when any per-file stat or unlink call failed."""

        return bool(self.failed_stat or self.failed_unlink)

    def report(self, prefix: str = "") -> str:
        """Return an operator-facing multi-line report of the sweep.

        Args:
            prefix: Optional string prepended to *every* line, so that
                multi-line reports retain caller attribution when
                aggregated with other log output. Defaults to empty
                (suitable when the report is printed in an unambiguous
                single-source context such as the standalone CLI wrapper).

        Returns:
            A string whose first line is a terse count summary
            ("removed=N, fresh=N, ...") and whose remaining lines are
            one entry per failure, each rendered as
            ``  failed_stat <path>: <error_repr>`` or
            ``  failed_unlink <path>: <error_repr>``. Every line is
            prefixed with ``prefix``. Designed for printing to stderr.
        """

        parts = [
            f"removed={len(self.removed)}",
            f"fresh={len(self.skipped_fresh)}",
        ]
        if self.failed_stat:
            parts.append(f"failed_stat={len(self.failed_stat)}")
        if self.failed_unlink:
            parts.append(f"failed_unlink={len(self.failed_unlink)}")
        lines = [prefix + "clean_stale_files: " + ", ".join(parts)]
        for path, error in self.failed_stat:
            lines.append(f"{prefix}  failed_stat {path}: {error}")
        for path, error in self.failed_unlink:
            lines.append(f"{prefix}  failed_unlink {path}: {error}")
        return "\n".join(lines)


def clean_stale_files(
    shakedown_path: Path, max_age_hours: int = 24
) -> CleanStaleResult:
    """Remove stale shakedown state files older than ``max_age_hours``.

    Returns a :class:`CleanStaleResult` describing what was removed, what was
    skipped because it was still fresh, and any per-file ``stat()`` or
    ``unlink()`` failures encountered during the sweep. Per-file errors do
    not abort the run. Concurrent-deletion races after ``os.listdir()``
    are ignored because the stale file is already gone.

    Root-level handling uses a **three-stage check** to distinguish a
    legitimate first-run absence from every corruption mode:

    - Stage 1 (``lstat``): ``FileNotFoundError`` means the path entry does
      not exist at the filesystem level — the legitimate first-run state.
      Returns an empty :class:`CleanStaleResult`. Any other ``OSError``
      (permission denied on the parent, stale NFS handle, etc.) is
      re-raised with an explicit ``"cannot lstat"`` context message.
    - Stage 2 (``stat``): Follows symlinks and validates the resolved
      target. A dangling symlink raises ``FileNotFoundError`` *from this
      call* (not Stage 1), re-raised as ``OSError`` with a
      ``"possible broken symlink"`` context message. A non-directory
      target (``S_ISDIR`` false) raises ``NotADirectoryError``.
    - Stage 3 (``os.listdir``): Enumerates candidate entries. A
      ``chmod 0o000`` directory passes Stage 2 (``stat`` on a directory
      only needs execute permission on the parent, so mode ``0o40000``
      still comes back with ``S_ISDIR`` true), but ``os.listdir`` raises
      ``PermissionError`` when it actually tries to read the directory
      contents. Re-raised with a ``"cannot enumerate"`` context message.
      This stage is necessary because the stdlib ``Path.glob()`` helper
      would silently return ``[]`` on the same input, which would mask
      the failure as a clean empty result.

    Stages 1 and 2 run without touching directory contents; Stage 3 is
    the first operation that requires the directory's read bit. Any
    earlier "stat succeeded" signal does not imply listability.

    Raises:
        OSError: If the shakedown root exists but cannot be stat-ed or
            cannot be enumerated. Covers three distinct failure classes:
            lstat failure on an existing entry, stat failure after
            lstat succeeds (dangling symlink or similar), and
            ``os.listdir`` failure after stat succeeds (unreadable
            directory contents). Matches the "Explicit over Silent"
            tenet.
        NotADirectoryError: If the shakedown root (after symlink
            resolution) is not a directory. Subclass of ``OSError``.
    """

    removed: list[Path] = []
    skipped_fresh: list[Path] = []
    failed_stat: list[tuple[Path, str]] = []
    failed_unlink: list[tuple[Path, str]] = []

    # Stage 1: lstat() without following symlinks. Distinguishes true
    # filesystem absence from a dangling-symlink corruption state.
    try:
        shakedown_path.lstat()
    except FileNotFoundError:
        return CleanStaleResult(
            removed=tuple(removed),
            skipped_fresh=tuple(skipped_fresh),
            failed_stat=tuple(failed_stat),
            failed_unlink=tuple(failed_unlink),
        )
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: cannot lstat shakedown root. "
            f"Got: {exc!r:.100}"
        ) from exc

    # Stage 2: stat() follows symlinks and validates the resolved target.
    try:
        root_stat = shakedown_path.stat()
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: shakedown root is unreadable "
            f"(possible broken symlink). Got: {exc!r:.100}"
        ) from exc

    if not S_ISDIR(root_stat.st_mode):
        raise NotADirectoryError(
            f"clean_stale_files failed: shakedown root is not a directory. "
            f"Got: {str(shakedown_path)!r:.100}"
        )

    # Stage 3: enumerate candidates with os.listdir. Path.glob silently
    # returns [] on directories we cannot read (verified on Python 3.14:
    # chmod 0o000 on a directory makes root.glob("seed-*.json") return []
    # with no exception). os.listdir raises PermissionError loudly on
    # the same input. This stage is necessary because stat() on an
    # unreadable directory succeeds with mode 0o40000 — the two-stage
    # root check above cannot detect this class.
    try:
        entry_names = os.listdir(shakedown_path)
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: cannot enumerate shakedown root. "
            f"Got: {exc!r:.100}"
        ) from exc

    candidates = [
        shakedown_path / name
        for name in entry_names
        if any(fnmatch.fnmatch(name, pattern) for pattern in _STALE_PATTERNS)
    ]

    cutoff = max_age_hours * 3600
    current_time = time.time()
    for path in candidates:
        try:
            stat_result = path.stat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            failed_stat.append((path, f"{exc!r:.100}"))
            continue
        if not S_ISREG(stat_result.st_mode):
            continue
        age_seconds = current_time - stat_result.st_mtime
        if age_seconds <= cutoff:
            skipped_fresh.append(path)
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            failed_unlink.append((path, f"{exc!r:.100}"))
            continue
        removed.append(path)

    return CleanStaleResult(
        removed=tuple(removed),
        skipped_fresh=tuple(skipped_fresh),
        failed_stat=tuple(failed_stat),
        failed_unlink=tuple(failed_unlink),
    )


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
