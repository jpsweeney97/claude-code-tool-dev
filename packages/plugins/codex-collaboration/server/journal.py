"""Minimal operation journal and audit log support for R1."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import AuditEvent, OperationJournalEntry, StaleAdvisoryContextMarker


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

    def write_phase(self, entry: OperationJournalEntry, *, session_id: str) -> None:
        """Append a phased journal record with fsync."""
        path = self._operations_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def list_unresolved(self, *, session_id: str) -> list[OperationJournalEntry]:
        """Return entries whose terminal phase is not 'completed'.

        Replays the full log, grouping by idempotency_key, and returns only
        the terminal-phase record for keys that are not yet completed.
        """
        terminal = self._terminal_phases(session_id)
        return [
            entry for entry in terminal.values()
            if entry.phase != "completed"
        ]

    def check_idempotency(
        self, key: str, *, session_id: str
    ) -> OperationJournalEntry | None:
        """Return the terminal-phase record for this key, or None."""
        terminal = self._terminal_phases(session_id)
        return terminal.get(key)

    def compact(self, *, session_id: str) -> None:
        """Atomic rewrite: keep only unresolved keys, each as its terminal record.

        Completed keys are removed entirely. Stale intent/dispatched rows for
        unresolved keys are collapsed to a single terminal-phase record.
        Uses temp-file-rename with fsync for crash safety.
        """
        path = self._operations_path(session_id)
        if not path.exists():
            return
        terminal = self._terminal_phases(session_id)
        remaining = [
            entry for entry in terminal.values()
            if entry.phase != "completed"
        ]
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for entry in remaining:
                handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        tmp.rename(path)

    def _terminal_phases(self, session_id: str) -> dict[str, OperationJournalEntry]:
        """Replay the log and return the last record per idempotency key."""
        path = self._operations_path(session_id)
        if not path.exists():
            return {}
        terminal: dict[str, OperationJournalEntry] = {}
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                entry = OperationJournalEntry(**record)
                terminal[entry.idempotency_key] = entry
        return terminal

    def _operations_path(self, session_id: str) -> Path:
        return self._journal_dir / "operations" / f"{session_id}.jsonl"

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
