"""Tests for per-turn metadata store."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from server.turn_store import TurnStore


class TestWriteAndGet:
    def test_write_then_get_returns_context_size(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        assert store.get("collab-1", turn_sequence=1) == 4096

    def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        assert store.get("collab-1", turn_sequence=1) is None

    def test_write_multiple_turns(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store.write("collab-1", turn_sequence=2, context_size=8192)
        assert store.get("collab-1", turn_sequence=1) == 4096
        assert store.get("collab-1", turn_sequence=2) == 8192

    def test_write_multiple_collaborations(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store.write("collab-2", turn_sequence=1, context_size=2048)
        assert store.get("collab-1", turn_sequence=1) == 4096
        assert store.get("collab-2", turn_sequence=1) == 2048

    def test_overwrite_same_key(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store.write("collab-1", turn_sequence=1, context_size=5000)
        assert store.get("collab-1", turn_sequence=1) == 5000

    def test_write_uses_fsync(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fsynced_fds: list[int] = []
        original_fsync = os.fsync

        def tracking_fsync(fd: int) -> None:
            fsynced_fds.append(fd)
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", tracking_fsync)
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        assert len(fsynced_fds) == 1


class TestCrashRecovery:
    def test_incomplete_trailing_record_discarded(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write('{"collaboration_id": "collab-1", "turn_seque')
        store2 = TurnStore(tmp_path, "sess-1")
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_survives_reload(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store2 = TurnStore(tmp_path, "sess-1")
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_empty_file_returns_none(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        assert store.get("collab-1", turn_sequence=1) is None


class TestGetAll:
    def test_get_all_for_collaboration(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store.write("collab-1", turn_sequence=2, context_size=8192)
        store.write("collab-2", turn_sequence=1, context_size=2048)
        result = store.get_all("collab-1")
        assert result == {1: 4096, 2: 8192}

    def test_get_all_empty(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        assert store.get_all("collab-1") == {}


class TestReplayHardening:
    """I2 regression: malformed records must not crash replay."""

    def test_malformed_record_does_not_crash(self, tmp_path: Path) -> None:
        """I2: a record missing required fields must not crash replay."""
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"bad": "record"}) + "\n")
        store2 = TurnStore(tmp_path, "sess-1")
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_wrong_type_does_not_crash(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "collaboration_id": "collab-1",
                        "turn_sequence": "not-an-int",
                        "context_size": 100,
                    }
                )
                + "\n"
            )
        store2 = TurnStore(tmp_path, "sess-1")
        # Valid record survives; malformed record skipped
        assert store2.get("collab-1", turn_sequence=1) == 4096

    def test_bool_as_int_rejected(self, tmp_path: Path) -> None:
        """type(True) is bool, not int — must not pass integer validation."""
        store = TurnStore(tmp_path, "sess-1")
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "collaboration_id": "collab-1",
                        "turn_sequence": True,
                        "context_size": 4096,
                    }
                )
                + "\n"
            )
        assert store.get("collab-1", turn_sequence=1) is None

    def test_check_health_returns_diagnostics(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"bad": "record"}) + "\n")
        diags = store.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        diags = store.check_health()
        assert diags.diagnostics == ()
        assert diags.has_warnings is False
