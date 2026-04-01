"""Tests for lineage store persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from server.lineage_store import LineageStore
from server.models import CollaborationHandle


def _make_handle(
    collaboration_id: str = "collab-1",
    runtime_id: str = "rt-1",
    thread_id: str = "thr-1",
    session_id: str = "sess-1",
    repo_root: str = "/repo",
    status: str = "active",
) -> CollaborationHandle:
    return CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="advisory",
        runtime_id=runtime_id,
        codex_thread_id=thread_id,
        claude_session_id=session_id,
        repo_root=repo_root,
        created_at="2026-03-28T00:00:00Z",
        status=status,
    )


class TestCreateAndGet:
    def test_create_then_get_returns_handle(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        handle = _make_handle()
        store.create(handle)
        retrieved = store.get("collab-1")
        assert retrieved is not None
        assert retrieved.collaboration_id == "collab-1"
        assert retrieved.codex_thread_id == "thr-1"

    def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        assert store.get("nonexistent") is None

    def test_create_writes_to_jsonl_file(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        assert store_path.exists()
        lines = store_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["op"] == "create"
        assert record["collaboration_id"] == "collab-1"

    def test_create_uses_fsync(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fsynced_fds: list[int] = []
        original_fsync = os.fsync

        def tracking_fsync(fd: int) -> None:
            fsynced_fds.append(fd)
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", tracking_fsync)
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        assert len(fsynced_fds) == 1


class TestCrashRecovery:
    def test_incomplete_trailing_record_discarded(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        # Simulate crash mid-write: append incomplete JSON
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write('{"op": "create", "collaboration_id": "collab-2", "capabilit')
        # Reload and verify only first handle survives
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1") is not None
        assert store2.get("collab-2") is None

    def test_empty_trailing_lines_ignored(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write("\n\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1") is not None

    def test_survives_reload_after_create(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        # Simulate process restart: new LineageStore instance
        store2 = LineageStore(tmp_path, "sess-1")
        retrieved = store2.get("collab-1")
        assert retrieved is not None
        assert retrieved.runtime_id == "rt-1"


class TestList:
    def test_list_all_handles(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle(collaboration_id="collab-1"))
        store.create(_make_handle(collaboration_id="collab-2", thread_id="thr-2"))
        handles = store.list()
        assert len(handles) == 2

    def test_list_filters_by_repo_root(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle(collaboration_id="c1", repo_root="/repo-a"))
        store.create(_make_handle(collaboration_id="c2", repo_root="/repo-b"))
        handles = store.list(repo_root="/repo-a")
        assert len(handles) == 1
        assert handles[0].collaboration_id == "c1"

    def test_list_filters_by_status(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle(collaboration_id="c1", status="active"))
        store.create(_make_handle(collaboration_id="c2", status="completed"))
        handles = store.list(status="active")
        assert len(handles) == 1
        assert handles[0].collaboration_id == "c1"


class TestUpdateStatus:
    def test_update_status_changes_handle(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store.update_status("collab-1", "completed")
        handle = store.get("collab-1")
        assert handle is not None
        assert handle.status == "completed"

    def test_update_status_survives_reload(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store.update_status("collab-1", "crashed")
        store2 = LineageStore(tmp_path, "sess-1")
        handle = store2.get("collab-1")
        assert handle is not None
        assert handle.status == "crashed"


class TestUpdateRuntime:
    def test_update_runtime_remaps_runtime_id(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store.update_runtime("collab-1", runtime_id="rt-2")
        handle = store.get("collab-1")
        assert handle is not None
        assert handle.runtime_id == "rt-2"
        assert handle.codex_thread_id == "thr-1"  # unchanged

    def test_update_runtime_also_remaps_thread_id(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store.update_runtime("collab-1", runtime_id="rt-2", codex_thread_id="thr-2")
        handle = store.get("collab-1")
        assert handle is not None
        assert handle.runtime_id == "rt-2"
        assert handle.codex_thread_id == "thr-2"


class TestCleanup:
    def test_cleanup_removes_session_directory(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        session_dir = tmp_path / "lineage" / "sess-1"
        assert session_dir.exists()
        store.cleanup()
        assert not session_dir.exists()

    def test_cleanup_is_safe_when_no_data(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.cleanup()  # no error


class TestReplayHardening:
    """I4 regression: unknown ops and schema violations must be diagnosed."""

    def test_unknown_op_does_not_crash(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "future_op",
                        "collaboration_id": "collab-1",
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        # Unknown op skipped; original handle survives
        assert store2.get("collab-1") is not None

    def test_missing_op_does_not_crash(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"collaboration_id": "collab-1"}) + "\n")
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1") is not None

    def test_create_missing_required_field_skipped(self, tmp_path: Path) -> None:
        """Create op missing a required field is a schema violation."""
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "create",
                        "collaboration_id": "collab-bad",
                        # missing capability_class and other required fields
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None

    def test_update_status_wrong_type_skipped(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "update_status",
                        "collaboration_id": "collab-1",
                        "status": 123,  # wrong type
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        # Status unchanged — bad record skipped
        assert store2.get("collab-1").status == "active"

    def test_check_health_reports_unknown_op(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "future_op",
                        "collaboration_id": "collab-1",
                    }
                )
                + "\n"
            )
        diags = store.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "unknown_operation"

    def test_check_health_clean_file(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        diags = store.check_health()
        assert diags.diagnostics == ()

    def test_create_invalid_status_diagnosed_and_skipped(self, tmp_path: Path) -> None:
        """Unknown status literal is a schema violation — intentionally tighter
        than the extra-field policy. See compatibility decision in callback."""
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "create",
                        "collaboration_id": "collab-bad",
                        "capability_class": "advisory",
                        "runtime_id": "rt-1",
                        "codex_thread_id": "thread-1",
                        "claude_session_id": "sess-1",
                        "repo_root": "/repo",
                        "created_at": "2026-01-01T00:00:00Z",
                        "status": "banana",
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "status" in diags.diagnostics[0].detail

    def test_create_invalid_capability_class_diagnosed_and_skipped(
        self, tmp_path: Path
    ) -> None:
        """Unknown capability_class is a schema violation — intentionally tighter
        than the extra-field policy. See compatibility decision in callback."""
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "create",
                        "collaboration_id": "collab-bad",
                        "capability_class": "banana",
                        "runtime_id": "rt-1",
                        "codex_thread_id": "thread-1",
                        "claude_session_id": "sess-1",
                        "repo_root": "/repo",
                        "created_at": "2026-01-01T00:00:00Z",
                        "status": "active",
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-bad") is None
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "capability_class" in diags.diagnostics[0].detail

    def test_update_status_invalid_literal_diagnosed_and_skipped(
        self, tmp_path: Path
    ) -> None:
        """Unknown status literal on update_status is a schema violation."""
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "update_status",
                        "collaboration_id": "collab-1",
                        "status": "banana",
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").status == "active"
        diags = store2.check_health()
        assert len(diags.diagnostics) == 1
        assert diags.diagnostics[0].label == "schema_violation"
        assert "status" in diags.diagnostics[0].detail

    def test_update_runtime_wrong_type_runtime_id_skipped(self, tmp_path: Path) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "update_runtime",
                        "collaboration_id": "collab-1",
                        "runtime_id": 123,
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").runtime_id == "rt-1"

    def test_update_runtime_wrong_type_codex_thread_id_skipped(
        self, tmp_path: Path
    ) -> None:
        store = LineageStore(tmp_path, "sess-1")
        store.create(_make_handle())
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "update_runtime",
                        "collaboration_id": "collab-1",
                        "runtime_id": "rt-2",
                        "codex_thread_id": 123,
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        assert store2.get("collab-1").codex_thread_id == "thr-1"

    def test_create_extra_field_ignored(self, tmp_path: Path) -> None:
        """Forward-compat: extra fields on create are silently ignored.
        Shared policy per design spec §Extra-Field Policy."""
        store_path = tmp_path / "lineage" / "sess-1" / "handles.jsonl"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "op": "create",
                        "collaboration_id": "collab-1",
                        "capability_class": "advisory",
                        "runtime_id": "rt-1",
                        "codex_thread_id": "thread-1",
                        "claude_session_id": "sess-1",
                        "repo_root": "/repo",
                        "created_at": "2026-01-01T00:00:00Z",
                        "status": "active",
                        "future_field": "some_value",
                    }
                )
                + "\n"
            )
        store2 = LineageStore(tmp_path, "sess-1")
        handle = store2.get("collab-1")
        assert handle is not None
        assert handle.collaboration_id == "collab-1"
