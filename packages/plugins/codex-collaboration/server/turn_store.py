"""Per-turn metadata store: session-partitioned append-only JSONL.

Persists context_size per (collaboration_id, turn_sequence) for dialogue.read
enrichment. Crash-safe: append-only with fsync, incomplete trailing records
discarded on replay.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .replay import ReplayDiagnostics, SchemaViolation, replay_jsonl


def _turn_callback(record: dict[str, Any]) -> tuple[str, int]:
    """Validate and extract turn metadata from a JSONL record."""
    cid = record.get("collaboration_id")
    if not isinstance(cid, str):
        raise SchemaViolation("missing or non-string collaboration_id")
    seq = record.get("turn_sequence")
    if type(seq) is not int:
        raise SchemaViolation("missing or non-int turn_sequence")
    size = record.get("context_size")
    if type(size) is not int:
        raise SchemaViolation("missing or non-int context_size")
    return (f"{cid}:{seq}", size)


class TurnStore:
    """Append-only JSONL store for per-turn context_size."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "turns" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "turn_metadata.jsonl"

    def write(
        self,
        collaboration_id: str,
        *,
        turn_sequence: int,
        context_size: int,
    ) -> None:
        """Persist context_size for a turn. Idempotent — last write wins on replay."""
        record = {
            "collaboration_id": collaboration_id,
            "turn_sequence": turn_sequence,
            "context_size": context_size,
        }
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def get(self, collaboration_id: str, *, turn_sequence: int) -> int | None:
        """Return context_size for a specific turn, or None if not found."""
        all_turns = self._replay()
        return all_turns.get(f"{collaboration_id}:{turn_sequence}")

    def get_all(self, collaboration_id: str) -> dict[int, int]:
        """Return {turn_sequence: context_size} for all turns in a collaboration."""
        all_turns = self._replay()
        prefix = f"{collaboration_id}:"
        return {
            int(key.split(":", 1)[1]): value
            for key, value in all_turns.items()
            if key.startswith(prefix)
        }

    def check_health(self) -> ReplayDiagnostics:
        """Replay and return diagnostics. Test and diagnostic support only."""
        _, diagnostics = replay_jsonl(self._store_path, _turn_callback)
        return diagnostics

    def _replay(self) -> dict[str, int]:
        """Replay JSONL log. Last record per key wins."""
        results, _ = replay_jsonl(self._store_path, _turn_callback)
        return dict(results)
