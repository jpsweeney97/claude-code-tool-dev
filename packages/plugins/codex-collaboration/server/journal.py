"""Minimal operation journal and audit log support for R1."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import AuditEvent, StaleAdvisoryContextMarker


def default_plugin_data_path() -> Path:
    """Resolve the plugin data root.

    Falls back to a local temp-style directory when CLAUDE_PLUGIN_DATA is not
    present, which keeps tests self-contained.
    """

    env_value = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path("/tmp/codex-collaboration").resolve()


class OperationJournal:
    """Session-bounded journal for stale advisory context markers."""

    def __init__(self, plugin_data_path: Path | None = None) -> None:
        self._plugin_data_path = plugin_data_path or default_plugin_data_path()
        self._journal_dir = self._plugin_data_path / "journal"
        self._markers_path = self._journal_dir / "stale_advisory_context.json"
        self._audit_dir = self._plugin_data_path / "audit"
        self._audit_path = self._audit_dir / "events.jsonl"
        self._journal_dir.mkdir(parents=True, exist_ok=True)
        self._audit_dir.mkdir(parents=True, exist_ok=True)

    @property
    def plugin_data_path(self) -> Path:
        return self._plugin_data_path

    def load_stale_marker(self, repo_root: Path) -> StaleAdvisoryContextMarker | None:
        """Return the persisted stale marker for `repo_root`, if present."""

        markers = self._read_markers()
        record = markers.get(_normalize_repo_root_key(repo_root))
        if record is None:
            return None
        return StaleAdvisoryContextMarker(**record)

    def write_stale_marker(self, marker: StaleAdvisoryContextMarker) -> None:
        """Persist or replace a stale marker for its repo root."""

        markers = self._read_markers()
        normalized_repo_root = _normalize_repo_root_key(marker.repo_root)
        normalized_marker = StaleAdvisoryContextMarker(
            repo_root=normalized_repo_root,
            promoted_head=marker.promoted_head,
            recorded_at=marker.recorded_at,
        )
        markers[normalized_repo_root] = asdict(normalized_marker)
        self._write_markers(markers)

    def clear_stale_marker(self, repo_root: Path) -> None:
        """Clear the stale marker for `repo_root` without deleting journal files."""

        markers = self._read_markers()
        markers.pop(_normalize_repo_root_key(repo_root), None)
        self._write_markers(markers)

    def append_audit_event(self, event: AuditEvent) -> None:
        """Append an audit event as JSONL."""

        with self._audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")

    def timestamp(self) -> str:
        """Return the current UTC timestamp as ISO 8601."""

        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _read_markers(self) -> dict[str, dict[str, str]]:
        if not self._markers_path.exists():
            return {}
        with self._markers_path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(
                "Operation journal read failed: stale marker file is not an object. "
                f"Got: {loaded!r:.100}"
            )
        return loaded

    def _write_markers(self, markers: dict[str, dict[str, str]]) -> None:
        with self._markers_path.open("w", encoding="utf-8") as handle:
            json.dump(markers, handle, indent=2, sort_keys=True)
            handle.write("\n")


def _normalize_repo_root_key(repo_root: Path | str) -> str:
    """Canonicalize repo-root keys so read/write/clear use the same lookup."""

    return Path(repo_root).expanduser().resolve().as_posix()
