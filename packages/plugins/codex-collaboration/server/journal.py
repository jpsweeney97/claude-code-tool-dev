"""Minimal operation journal and audit log support for R1."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from typing import Any, Callable

from .models import (
    AuditEvent,
    OperationJournalEntry,
    OutcomeRecord,
    StaleAdvisoryContextMarker,
)
from .replay import ReplayDiagnostics, SchemaViolation, replay_jsonl


def default_plugin_data_path() -> Path:
    """Resolve the plugin data root.

    Falls back to a local temp-style directory when CLAUDE_PLUGIN_DATA is not
    present, which keeps tests self-contained.
    """

    env_value = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path("/tmp/codex-collaboration").resolve()


_VALID_OPERATIONS = frozenset(("thread_creation", "turn_dispatch", "job_creation"))
_VALID_PHASES = frozenset(("intent", "dispatched", "completed"))
_JOURNAL_REQUIRED_STR = (
    "idempotency_key",
    "operation",
    "phase",
    "collaboration_id",
    "created_at",
    "repo_root",
)
_JOURNAL_OPTIONAL_STR = ("codex_thread_id", "runtime_id", "job_id")
_JOURNAL_OPTIONAL_INT = ("turn_sequence", "context_size")


def _journal_callback(
    record: dict[str, Any],
) -> tuple[str, OperationJournalEntry]:
    """Validate all fields and construct a journal entry."""
    for name in _JOURNAL_REQUIRED_STR:
        if not isinstance(record.get(name), str):
            raise SchemaViolation(f"{name} missing or not a string")
    if record["operation"] not in _VALID_OPERATIONS:
        raise SchemaViolation(f"unknown operation value: {record['operation']!r}")
    if record["phase"] not in _VALID_PHASES:
        raise SchemaViolation(f"unknown phase value: {record['phase']!r}")
    for name in _JOURNAL_OPTIONAL_STR:
        val = record.get(name)
        if val is not None and not isinstance(val, str):
            raise SchemaViolation(f"{name} is not a string")
    for name in _JOURNAL_OPTIONAL_INT:
        val = record.get(name)
        if val is not None and type(val) is not int:
            raise SchemaViolation(f"{name} is not an int")
    # Per-operation+phase conditional requirements.
    # Recovery (dialogue.py:446-592) relies on these fields existing for
    # specific operation+phase combinations. Without enforcement, type-valid
    # but incomplete records survive to recovery and crash with RuntimeError.
    #
    # Completed phase is excluded: production writers (dialogue.py:300-309,
    # :588-595, :688-695) emit completed as a minimal resolution marker
    # without codex_thread_id or turn_sequence. Requiring those fields
    # would reject every completed record written by production code.
    op = record["operation"]
    phase = record["phase"]
    if op == "turn_dispatch" and phase in ("intent", "dispatched"):
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                f"turn_dispatch at {phase} requires codex_thread_id (string)"
            )
        if phase == "dispatched":
            ts = record.get("turn_sequence")
            if ts is None or type(ts) is not int:
                raise SchemaViolation(
                    f"turn_dispatch at {phase} requires turn_sequence (int)"
                )
    elif op == "thread_creation" and phase == "dispatched":
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                "thread_creation at dispatched requires codex_thread_id (string)"
            )
    elif op == "job_creation" and phase == "intent":
        if not isinstance(record.get("job_id"), str):
            raise SchemaViolation(
                "job_creation at intent requires job_id (string)"
            )
    elif op == "job_creation" and phase == "dispatched":
        if not isinstance(record.get("job_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires job_id (string)"
            )
        if not isinstance(record.get("runtime_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires runtime_id (string)"
            )
        if not isinstance(record.get("codex_thread_id"), str):
            raise SchemaViolation(
                "job_creation at dispatched requires codex_thread_id (string)"
            )
    # Compatibility decision: runtime_id on turn_dispatch is NOT required.
    # Missing runtime_id suppresses audit event emission (dialogue.py:592,689)
    # but does not crash recovery. Requiring it would reject records from
    # older writers that may not persist runtime_id on all turn_dispatch
    # entries. This is a data-quality gap, not a correctness failure.
    entry = OperationJournalEntry(
        idempotency_key=record["idempotency_key"],
        operation=record["operation"],
        phase=record["phase"],
        collaboration_id=record["collaboration_id"],
        created_at=record["created_at"],
        repo_root=record["repo_root"],
        codex_thread_id=record.get("codex_thread_id"),
        turn_sequence=record.get("turn_sequence"),
        runtime_id=record.get("runtime_id"),
        context_size=record.get("context_size"),
        job_id=record.get("job_id"),
    )
    return (entry.idempotency_key, entry)


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
        self._analytics_dir = self._plugin_data_path / "analytics"
        self._outcomes_path = self._analytics_dir / "outcomes.jsonl"
        self._analytics_dir.mkdir(parents=True, exist_ok=True)

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

    def append_dialogue_audit_event_once(self, event: AuditEvent) -> None:
        """Append a dialogue audit event unless the logical record already exists."""

        if self._jsonl_contains(
            self._audit_path,
            lambda record: (
                record.get("action") == event.action
                and record.get("collaboration_id") == event.collaboration_id
                and record.get("turn_id") == event.turn_id
            ),
        ):
            return
        self.append_audit_event(event)

    def append_outcome(self, record: OutcomeRecord) -> None:
        """Append an analytics outcome record as JSONL."""

        with self._outcomes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def append_dialogue_outcome_once(self, record: OutcomeRecord) -> None:
        """Append a dialogue outcome unless the logical record already exists."""

        if self._jsonl_contains(
            self._outcomes_path,
            lambda existing: (
                existing.get("outcome_type") == record.outcome_type
                and existing.get("collaboration_id") == record.collaboration_id
                and existing.get("turn_id") == record.turn_id
            ),
        ):
            return
        self.append_outcome(record)

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
        return [entry for entry in terminal.values() if entry.phase != "completed"]

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
        remaining = [entry for entry in terminal.values() if entry.phase != "completed"]
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
        results, _ = replay_jsonl(path, _journal_callback)
        return dict(results)

    def check_health(self, *, session_id: str) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        path = self._operations_path(session_id)
        _, diagnostics = replay_jsonl(path, _journal_callback)
        return diagnostics

    def _operations_path(self, session_id: str) -> Path:
        return self._journal_dir / "operations" / f"{session_id}.jsonl"

    @staticmethod
    def _jsonl_contains(
        path: Path, predicate: Callable[[dict[str, Any]], bool]
    ) -> bool:
        if not path.exists():
            return False
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and predicate(record):
                    return True
        return False

    def timestamp(self) -> str:
        """Return the current UTC timestamp as ISO 8601."""

        return (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )

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
