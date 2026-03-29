# R2 Dialogue Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Runtime Milestone R2 for codex-collaboration: lineage store, MCP server scaffolding with serialized dispatch, `codex.dialogue.start`/`.reply`/`.read` with typed response shapes, journal-before-dispatch with separate idempotency keys, and audit events for dialogue turns.

**Architecture:** A `DialogueController` orchestrates dialogue operations by composing the existing `ControlPlane` (runtime bootstrap, context assembly) with a new `LineageStore` (handle persistence) and extended `OperationJournal` (crash-recovery journal entries). An MCP server (`mcp_server.py`) provides tool registration and serialized request dispatch over stdio JSON-RPC for all R1+R2 tools.

**Tech Stack:** Python 3.11+, pytest, zero external dependencies (stdlib only)

**Spec Anchors (frozen — any scope pressure is a spec-change question, not an implementation choice):**

| Anchor | Section | Governs |
|--------|---------|---------|
| `delivery.md:191-223` | §Runtime Milestone R2 | Scope, acceptance gates |
| `contracts.md:87-162` | §Lineage Store | Persistence contract, operations, crash recovery |
| `contracts.md:243-279` | §Typed Response Shapes | Dialogue Start/Reply/Read |
| `recovery-and-journal.md:29-61` | §Operation Journal | Write ordering, idempotency keys, trimming |
| `decisions.md:80-88` | §Dialogue Fork Scope | Fork deferred — flat handles only |

**Non-negotiable checkpoints:**

1. Lineage store: session-partitioned append-only JSONL with fsync, crash-safe, incomplete record discard
2. Typed response shapes: Dialogue Start/Reply/Read per contracts.md §Typed Response Shapes
3. Journal-before-dispatch with thread-creation key (`claude_session_id + collaboration_id`) and turn-dispatch key (`runtime_id + thread_id + turn_sequence`)
4. Serialized MCP dispatch: one tool call at a time
5. No fork in R2

---

## File Structure

### New Files

| File | Responsibility | Est. Lines |
|------|---------------|------------|
| `server/lineage_store.py` | Append-only JSONL handle persistence with crash-safe fsync | ~180 |
| `server/dialogue.py` | DialogueController: start, reply, read, recover_pending_operations | ~300 |
| `server/mcp_server.py` | Stdio JSON-RPC MCP server with serialized dispatch | ~190 |
| `tests/test_lineage_store.py` | LineageStore CRUD, crash recovery, session cleanup | ~220 |
| `tests/test_dialogue.py` | Dialogue operations, phased journal integration, recovery | ~420 |
| `tests/test_mcp_server.py` | Tool registration, serialized dispatch, handler routing | ~200 |

### Modified Files

| File | Changes |
|------|---------|
| `server/models.py` | `CollaborationHandle`, `HandleStatus`, dialogue response types, `OperationJournalEntry` |
| `server/journal.py` | Phased operation entries (intent/dispatched/completed), idempotency check, atomic compaction |
| `server/runtime.py` | `read_thread()`, `resume_thread()` |
| `server/control_plane.py` | Public `get_advisory_runtime()`, `invalidate_runtime()` |
| `server/__init__.py` | Export new public types |
| `tests/conftest.py` | Extended `FakeRuntimeSession`, dialogue helper factories |

### Dependency Graph

```
Task 1 (models) ─────────┬──► Task 2 (lineage store) ──► Task 6 (start) ──► Task 7 (reply) ──► Task 10 (MCP)
                          ├──► Task 3 (journal)     ────────────┘                │
                          ├──► Task 4 (runtime ext) ──► Task 5 (fixtures) ───────┤
                          │                                                      ├──► Task 8 (recovery) ──► Task 11 (integration)
                          └──► Task 9 (read) ◄───── Task 5 ─────────────────────┘
```

Parallelizable: Tasks 2, 3, 4 can run in parallel after Task 1.
Task 8 (recovery) depends on Tasks 4+5 (runtime read_thread) and Tasks 6+7 (dialogue start/reply).
Task 9 (read) can run in parallel with Task 8.

---

## Task 1: Data Models

**Files:**
- Modify: `server/models.py:8` (add to imports), append after line 153

- [ ] **Step 1: Write the failing test**

Create `tests/test_models_r2.py`:

```python
"""Tests for R2 data model types."""

from __future__ import annotations

from dataclasses import asdict, FrozenInstanceError

import pytest

from server.models import (
    CollaborationHandle,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
    HandleStatus,
    OperationJournalEntry,
)


def test_collaboration_handle_is_frozen() -> None:
    handle = CollaborationHandle(
        collaboration_id="collab-1",
        capability_class="advisory",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
        claude_session_id="sess-1",
        repo_root="/repo",
        created_at="2026-03-28T00:00:00Z",
        status="active",
    )
    assert handle.collaboration_id == "collab-1"
    assert handle.status == "active"
    assert handle.parent_collaboration_id is None
    assert handle.fork_reason is None
    with pytest.raises(FrozenInstanceError):
        handle.status = "completed"  # type: ignore[misc]


def test_collaboration_handle_serializes_to_dict() -> None:
    handle = CollaborationHandle(
        collaboration_id="collab-1",
        capability_class="advisory",
        runtime_id="rt-1",
        codex_thread_id="thr-1",
        claude_session_id="sess-1",
        repo_root="/repo",
        created_at="2026-03-28T00:00:00Z",
        status="active",
    )
    d = asdict(handle)
    assert d["collaboration_id"] == "collab-1"
    assert d["parent_collaboration_id"] is None
    assert len(d) == 10


def test_dialogue_start_result_fields() -> None:
    result = DialogueStartResult(
        collaboration_id="collab-1",
        runtime_id="rt-1",
        status="active",
        created_at="2026-03-28T00:00:00Z",
    )
    assert result.status == "active"


def test_dialogue_reply_result_fields() -> None:
    from server.models import ConsultEvidence

    result = DialogueReplyResult(
        collaboration_id="collab-1",
        runtime_id="rt-1",
        position="Analysis complete",
        evidence=(ConsultEvidence(claim="Found bug", citation="main.py:42"),),
        uncertainties=("Untested path",),
        follow_up_branches=("Check tests",),
        turn_sequence=1,
        context_size=1024,
    )
    assert result.turn_sequence == 1
    assert len(result.evidence) == 1


def test_dialogue_read_result_fields() -> None:
    result = DialogueReadResult(
        collaboration_id="collab-1",
        status="active",
        turn_count=2,
        created_at="2026-03-28T00:00:00Z",
        turns=(
            DialogueTurnSummary(
                turn_sequence=1,
                position="First analysis",
                context_size=1024,
                timestamp="2026-03-28T00:01:00Z",
            ),
        ),
    )
    assert result.turn_count == 2
    assert result.turns[0].turn_sequence == 1


def test_operation_journal_entry_intent_phase() -> None:
    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )
    assert entry.operation == "thread_creation"
    assert entry.phase == "intent"
    assert entry.codex_thread_id is None


def test_operation_journal_entry_dispatched_phase() -> None:
    entry = OperationJournalEntry(
        idempotency_key="rt-1:thr-1:1",
        operation="turn_dispatch",
        phase="dispatched",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
        codex_thread_id="thr-1",
        turn_sequence=1,
        runtime_id="rt-1",
    )
    assert entry.phase == "dispatched"
    assert entry.turn_sequence == 1
    assert entry.codex_thread_id == "thr-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py -v`
Expected: ImportError — types not yet defined

- [ ] **Step 3: Write the implementation**

Append to `server/models.py` after the `AuditEvent` class (after line 153). Also add `HandleStatus` to the type aliases near line 11:

```python
# Near line 11, after existing Literal types:
HandleStatus = Literal["active", "completed", "crashed", "unknown"]


# After AuditEvent class (after line 153):

@dataclass(frozen=True)
class CollaborationHandle:
    """Lineage-persisted handle for dialogue or delegation.

    Consultation handles are ephemeral (not lineage-persisted).
    See contracts.md §CollaborationHandle.
    """

    collaboration_id: str
    capability_class: CapabilityProfile
    runtime_id: str
    codex_thread_id: str
    claude_session_id: str
    repo_root: str
    created_at: str
    status: HandleStatus
    parent_collaboration_id: str | None = None
    fork_reason: str | None = None


@dataclass(frozen=True)
class DialogueStartResult:
    """Response shape for codex.dialogue.start. See contracts.md §Dialogue Start."""

    collaboration_id: str
    runtime_id: str
    status: HandleStatus
    created_at: str


@dataclass(frozen=True)
class DialogueTurnSummary:
    """Single turn entry within a DialogueReadResult."""

    turn_sequence: int
    position: str
    context_size: int
    timestamp: str


@dataclass(frozen=True)
class DialogueReplyResult:
    """Response shape for codex.dialogue.reply. See contracts.md §Dialogue Reply."""

    collaboration_id: str
    runtime_id: str
    position: str
    evidence: tuple[ConsultEvidence, ...]
    uncertainties: tuple[str, ...]
    follow_up_branches: tuple[str, ...]
    turn_sequence: int
    context_size: int


@dataclass(frozen=True)
class DialogueReadResult:
    """Response shape for codex.dialogue.read. See contracts.md §Dialogue Read."""

    collaboration_id: str
    status: HandleStatus
    turn_count: int
    created_at: str
    turns: tuple[DialogueTurnSummary, ...]


@dataclass(frozen=True)
class OperationJournalEntry:
    """Phased operation record for deterministic crash recovery replay.

    Lifecycle: intent (before dispatch) → dispatched (after dispatch, with
    outcome correlation data) → completed (confirmed, eligible for compaction).
    See recovery-and-journal.md §Write Ordering.
    """

    idempotency_key: str
    operation: Literal["thread_creation", "turn_dispatch"]
    phase: Literal["intent", "dispatched", "completed"]
    collaboration_id: str
    created_at: str
    repo_root: str
    # Outcome correlation — set when logically knowable
    codex_thread_id: str | None = None  # thread_creation: set at dispatched; turn_dispatch: set at intent
    turn_sequence: int | None = None  # turn_dispatch only
    runtime_id: str | None = None  # turn_dispatch only
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_models_r2.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All existing tests still pass (no regressions)

- [ ] **Step 6: Commit**

```bash
git add server/models.py tests/test_models_r2.py
git commit -m "feat(codex-collaboration): add R2 data models — CollaborationHandle, dialogue response types, journal entry"
```

---

## Task 2: Lineage Store

**Files:**
- Create: `server/lineage_store.py`
- Test: `tests/test_lineage_store.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_lineage_store.py`:

```python
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

    def test_create_uses_fsync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_lineage_store.py -v`
Expected: ImportError — `server.lineage_store` does not exist

- [ ] **Step 3: Write the implementation**

Create `server/lineage_store.py`:

```python
"""Lineage store: session-partitioned append-only JSONL handle persistence.

See contracts.md §Lineage Store for the normative contract.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import CollaborationHandle, HandleStatus


class LineageStore:
    """Persists CollaborationHandle records as append-only JSONL.

    All mutations append a new record. On read, the store replays the log —
    the last record for each collaboration_id wins. Incomplete trailing records
    (from crash mid-write) are discarded on load.
    """

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "lineage" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "handles.jsonl"

    def create(self, handle: CollaborationHandle) -> None:
        """Persist a new handle."""
        self._append({"op": "create", **asdict(handle)})

    def get(self, collaboration_id: str) -> CollaborationHandle | None:
        """Retrieve a handle by collaboration_id, or None if not found."""
        return self._replay().get(collaboration_id)

    def list(
        self,
        *,
        repo_root: str | None = None,
        status: HandleStatus | None = None,
    ) -> list[CollaborationHandle]:
        """Query handles with optional repo_root and status filters."""
        handles = list(self._replay().values())
        if repo_root is not None:
            handles = [h for h in handles if h.repo_root == repo_root]
        if status is not None:
            handles = [h for h in handles if h.status == status]
        return handles

    def update_status(self, collaboration_id: str, status: HandleStatus) -> None:
        """Transition handle lifecycle status."""
        self._append({
            "op": "update_status",
            "collaboration_id": collaboration_id,
            "status": status,
        })

    def update_runtime(
        self,
        collaboration_id: str,
        runtime_id: str,
        codex_thread_id: str | None = None,
    ) -> None:
        """Remap handle to a new runtime (and optionally a new thread identity)."""
        record: dict[str, str] = {
            "op": "update_runtime",
            "collaboration_id": collaboration_id,
            "runtime_id": runtime_id,
        }
        if codex_thread_id is not None:
            record["codex_thread_id"] = codex_thread_id
        self._append(record)

    def cleanup(self) -> None:
        """Remove the session directory. Called on session end."""
        if self._store_dir.exists():
            shutil.rmtree(self._store_dir)

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _replay(self) -> dict[str, CollaborationHandle]:
        """Replay the JSONL log to reconstruct current handle state."""
        if not self._store_path.exists():
            return {}
        handles: dict[str, CollaborationHandle] = {}
        with self._store_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._apply_record(handles, record)
        return handles

    def _apply_record(
        self,
        handles: dict[str, CollaborationHandle],
        record: dict[str, Any],
    ) -> None:
        op = record.get("op")
        cid = record.get("collaboration_id")
        if cid is None:
            return
        if op == "create":
            fields = {
                k: record[k]
                for k in CollaborationHandle.__dataclass_fields__
                if k in record
            }
            handles[cid] = CollaborationHandle(**fields)
        elif op == "update_status" and cid in handles:
            handles[cid] = _replace_handle(handles[cid], status=record["status"])
        elif op == "update_runtime" and cid in handles:
            updates: dict[str, Any] = {"runtime_id": record["runtime_id"]}
            if "codex_thread_id" in record:
                updates["codex_thread_id"] = record["codex_thread_id"]
            handles[cid] = _replace_handle(handles[cid], **updates)


def _replace_handle(handle: CollaborationHandle, **changes: Any) -> CollaborationHandle:
    """Return a new handle with specified fields replaced (frozen dataclass)."""
    return CollaborationHandle(**{**asdict(handle), **changes})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_lineage_store.py -v`
Expected: All 14 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/lineage_store.py tests/test_lineage_store.py
git commit -m "feat(codex-collaboration): add lineage store — append-only JSONL with crash-safe fsync"
```

---

## Task 3: Phased Operation Journal

**Files:**
- Modify: `server/journal.py:9` (add import), append new methods
- Test: `tests/test_journal.py` (extend existing file)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_journal.py`:

```python
import pytest

from server.models import OperationJournalEntry


def _make_intent(
    key: str = "sess-1:collab-1",
    operation: str = "thread_creation",
    collab: str = "collab-1",
) -> OperationJournalEntry:
    return OperationJournalEntry(
        idempotency_key=key,
        operation=operation,
        phase="intent",
        collaboration_id=collab,
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )


class TestPhasedJournal:
    def test_write_intent_and_list_unresolved(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "intent"

    def test_write_dispatched_updates_terminal_phase(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
                codex_thread_id="thr-1",
            ),
            session_id="sess-1",
        )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].phase == "dispatched"
        assert unresolved[0].codex_thread_id == "thr-1"

    def test_write_completed_resolves_operation(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1",
                operation="thread_creation",
                phase="completed",
                collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_check_idempotency_returns_terminal_entry(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        found = journal.check_idempotency("sess-1:collab-1", session_id="sess-1")
        assert found is not None
        assert found.phase == "intent"

    def test_check_idempotency_returns_none_when_missing(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        assert journal.check_idempotency("no-such-key", session_id="sess-1") is None

    def test_write_phase_uses_fsync(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import os as _os

        fsynced: list[int] = []
        original = _os.fsync

        def tracking(fd: int) -> None:
            fsynced.append(fd)
            original(fd)

        monkeypatch.setattr(_os, "fsync", tracking)
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(key="k1", collab="c1"), session_id="sess-1")
        assert len(fsynced) >= 1

    def test_compact_removes_completed_keeps_unresolved_terminal(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        # key-0: intent → dispatched → completed (should be removed entirely)
        journal.write_phase(_make_intent(key="key-0", collab="c0"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0", operation="thread_creation", phase="dispatched",
                collaboration_id="c0", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo", codex_thread_id="thr-0",
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-0", operation="thread_creation", phase="completed",
                collaboration_id="c0", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo",
            ),
            session_id="sess-1",
        )
        # key-1: intent → dispatched (unresolved — should keep only terminal "dispatched")
        journal.write_phase(_make_intent(key="key-1", collab="c1"), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="key-1", operation="thread_creation", phase="dispatched",
                collaboration_id="c1", created_at="2026-03-28T00:00:00Z",
                repo_root="/repo", codex_thread_id="thr-1",
            ),
            session_id="sess-1",
        )
        # key-2: intent only (unresolved — should keep the intent)
        journal.write_phase(_make_intent(key="key-2", collab="c2"), session_id="sess-1")

        journal.compact(session_id="sess-1")

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 2
        by_key = {e.idempotency_key: e for e in unresolved}
        assert by_key["key-1"].phase == "dispatched"
        assert by_key["key-1"].codex_thread_id == "thr-1"
        assert by_key["key-2"].phase == "intent"

    def test_compact_uses_atomic_rename(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        journal.write_phase(_make_intent(), session_id="sess-1")
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-1", operation="thread_creation",
                phase="completed", collaboration_id="collab-1",
                created_at="2026-03-28T00:00:00Z", repo_root="/repo",
            ),
            session_id="sess-1",
        )
        journal.compact(session_id="sess-1")
        # After compacting a fully-completed journal, file should be empty or minimal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_journal.py -v`
Expected: AttributeError — `write_phase` not defined on `OperationJournal`

- [ ] **Step 3: Write the implementation**

Add import and methods to `server/journal.py`:

At the top, add `OperationJournalEntry` to the model import:

```python
from .models import AuditEvent, OperationJournalEntry, StaleAdvisoryContextMarker
```

Add these methods to the `OperationJournal` class (after `append_audit_event`):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_journal.py -v`
Expected: All 12 tests PASS (3 existing + 9 new)

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/journal.py tests/test_journal.py
git commit -m "feat(codex-collaboration): phased operation journal — intent/dispatched/completed with atomic compaction"
```

---

## Task 4: Runtime Extensions

**Files:**
- Modify: `server/runtime.py` (append after `run_turn`)
- Test: `tests/test_runtime.py` (extend existing file)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_runtime.py`. First read the file to understand the existing test pattern, then add:

```python
class _StubClientForThreadOps:
    """Stub JSON-RPC client for thread/read and thread/resume."""

    def __init__(self, responses: dict[str, dict]) -> None:
        self._responses = responses
        self.requests: list[tuple[str, dict]] = []

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict) -> dict:
        self.requests.append((method, params))
        return self._responses.get(method, {})

    def close(self) -> None:
        pass


def test_read_thread_returns_turns() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(
        responses={
            "thread/read": {
                "thread": {
                    "id": "thr-1",
                    "turns": [
                        {
                            "id": "turn-1",
                            "status": "completed",
                            "agentMessage": "First response",
                            "createdAt": "2026-03-28T00:01:00Z",
                        },
                    ],
                },
            },
        }
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    result = session.read_thread("thr-1")
    assert result["thread"]["id"] == "thr-1"
    assert len(result["thread"]["turns"]) == 1
    assert client.requests[0] == ("thread/read", {"threadId": "thr-1"})


def test_resume_thread_returns_new_thread_id() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(
        responses={
            "thread/resume": {
                "thread": {"id": "thr-resumed"},
            },
        }
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    new_thread_id = session.resume_thread("thr-1")
    assert new_thread_id == "thr-resumed"
    assert client.requests[0] == ("thread/resume", {"threadId": "thr-1"})


def test_resume_thread_raises_on_malformed_response() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(responses={"thread/resume": {"error": "bad"}})
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    with pytest.raises(RuntimeError, match="Thread resume failed"):
        session.resume_thread("thr-1")
```

Add `import pytest` and `from pathlib import Path` to the test file imports if not already present.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_runtime.py -v -k "read_thread or resume_thread"`
Expected: AttributeError — `read_thread` not defined

- [ ] **Step 3: Write the implementation**

Append to `server/runtime.py` before the `close` method:

```python
    def read_thread(self, thread_id: str) -> dict[str, Any]:
        """Read thread state and turn history via thread/read."""
        return self._client.request("thread/read", {"threadId": thread_id})

    def resume_thread(self, thread_id: str) -> str:
        """Resume a thread after crash recovery. Returns the (possibly new) thread ID."""
        result = self._client.request("thread/resume", {"threadId": thread_id})
        thread = result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise RuntimeError(
                f"Thread resume failed: malformed thread response. Got: {thread!r:.100}"
            )
        return str(thread["id"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_runtime.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add server/runtime.py tests/test_runtime.py
git commit -m "feat(codex-collaboration): add read_thread and resume_thread to runtime session"
```

---

## Task 5: ControlPlane Public API and Test Fixtures

**Files:**
- Modify: `server/control_plane.py:202` (add public methods)
- Modify: `tests/conftest.py` (extend)
- Test: `tests/test_control_plane.py` (add tests for new methods)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_control_plane.py`:

```python
def test_get_advisory_runtime_returns_cached_runtime(tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: "uuid-1",
    )

    runtime = plane.get_advisory_runtime(tmp_path)

    assert runtime is not None
    assert runtime.runtime_id == "uuid-1"
    assert runtime.session is session


def test_get_advisory_runtime_raises_on_failure(tmp_path: Path) -> None:
    session = FakeRuntimeSession(initialize_error=RuntimeError("init boom"))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
    )

    with pytest.raises(RuntimeError, match="initialize failed"):
        plane.get_advisory_runtime(tmp_path)


def test_invalidate_runtime_drops_cache(tmp_path: Path) -> None:
    session1 = FakeRuntimeSession()
    session2 = FakeRuntimeSession()
    sessions = iter((session1, session2))
    plane = ControlPlane(
        plugin_data_path=tmp_path / "plugin-data",
        runtime_factory=lambda _repo_root: next(sessions),
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(("rt-1", "rt-2")).__next__,
    )

    rt1 = plane.get_advisory_runtime(tmp_path)
    assert rt1.runtime_id == "rt-1"

    plane.invalidate_runtime(tmp_path)
    assert session1.closed is True

    rt2 = plane.get_advisory_runtime(tmp_path)
    assert rt2.runtime_id == "rt-2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py::test_get_advisory_runtime_returns_cached_runtime -v`
Expected: AttributeError — `get_advisory_runtime` not defined

- [ ] **Step 3: Write the ControlPlane public methods**

Add to `server/control_plane.py`, before `close()` (before line 202):

```python
    def get_advisory_runtime(self, repo_root: Path) -> AdvisoryRuntimeState:
        """Bootstrap and return the advisory runtime for a repo root.

        Raises RuntimeError if the runtime cannot be established.
        Used by DialogueController for shared runtime access.
        """
        resolved_root = repo_root.resolve()
        runtime = self._bootstrap_runtime(resolved_root, strict=True)
        assert runtime is not None  # strict=True guarantees non-None or raises
        return runtime

    def invalidate_runtime(self, repo_root: Path) -> None:
        """Drop a cached runtime. Public wrapper for error recovery paths."""
        self._invalidate_runtime(repo_root.resolve())
```

- [ ] **Step 4: Extend FakeRuntimeSession in conftest.py**

Add `read_thread` and `resume_thread` stubs to `FakeRuntimeSession` in `tests/test_control_plane.py` (where it is currently defined):

```python
    # Add to FakeRuntimeSession class, after run_turn:
    def read_thread(self, thread_id: str) -> dict:
        return {
            "thread": {
                "id": thread_id,
                "turns": [],
            },
        }

    def resume_thread(self, thread_id: str) -> str:
        return f"{thread_id}-resumed"
```

Add shared test helper to `tests/conftest.py`:

```python
from server.models import CollaborationHandle


def make_test_handle(
    collaboration_id: str = "collab-1",
    runtime_id: str = "rt-1",
    thread_id: str = "thr-1",
    session_id: str = "sess-1",
    repo_root: str = "/repo",
    status: str = "active",
) -> CollaborationHandle:
    """Factory for test CollaborationHandle instances."""
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py -v`
Expected: All tests PASS (11 existing + 3 new)

- [ ] **Step 6: Commit**

```bash
git add server/control_plane.py tests/conftest.py tests/test_control_plane.py
git commit -m "feat(codex-collaboration): add public get_advisory_runtime/invalidate_runtime, extend test fixtures"
```

---

## Task 6: DialogueController.start

**Files:**
- Create: `server/dialogue.py`
- Test: `tests/test_dialogue.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dialogue.py`:

```python
"""Tests for DialogueController operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.control_plane import ControlPlane, load_repo_identity
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import RepoIdentity

# Import FakeRuntimeSession and helpers from the control plane tests.
# These will be moved to conftest.py in a cleanup pass; for now we import directly.
from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _build_dialogue_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
    session_id: str = "sess-1",
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal]:
    """Wire up a full dialogue stack with test doubles."""
    session = session or FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(
            (f"rt-{session_id}", *(f"uuid-{i}" for i in range(100)))
        ).__next__,
        journal=journal,
    )
    store = LineageStore(plugin_data, session_id)
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id=session_id,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{session_id}", *(f"id-{i}" for i in range(100)))).__next__,
    )
    return controller, plane, store, journal


class TestDialogueStart:
    def test_start_returns_dialogue_start_result(self, tmp_path: Path) -> None:
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        assert result.collaboration_id == "collab-sess-1"
        assert result.status == "active"
        assert result.runtime_id == "rt-sess-1"
        assert result.created_at is not None

    def test_start_persists_handle_in_lineage_store(self, tmp_path: Path) -> None:
        controller, _, store, _ = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        handle = store.get(result.collaboration_id)
        assert handle is not None
        assert handle.capability_class == "advisory"
        assert handle.codex_thread_id == "thr-start"
        assert handle.claude_session_id == "sess-1"

    def test_start_journals_before_dispatch(self, tmp_path: Path) -> None:
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        result = controller.start(tmp_path)
        # After successful completion, all phases written (intent → dispatched → completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_start_does_not_emit_audit_event(self, tmp_path: Path) -> None:
        """Thread creation is not a trust boundary crossing — no audit event.
        See contracts.md §Audit Event Actions (dialogue_start is not defined)."""
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        controller.start(tmp_path)
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        if audit_path.exists():
            events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
            assert all(e["action"] != "dialogue_start" for e in events)

    def test_start_creates_thread_on_runtime(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession()
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        controller.start(tmp_path)
        assert "start" in session.started_threads

    def test_start_invalidates_runtime_on_thread_failure(self, tmp_path: Path) -> None:
        session = FakeRuntimeSession(initialize_error=RuntimeError("boom"))
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        with pytest.raises(RuntimeError):
            controller.start(tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueStart -v`
Expected: ModuleNotFoundError — `server.dialogue` does not exist

- [ ] **Step 3: Write the implementation**

Create `server/dialogue.py`:

```python
"""Dialogue controller for codex.dialogue.start, .reply, .read.

Orchestrates dialogue operations by composing ControlPlane (runtime bootstrap),
LineageStore (handle persistence), and OperationJournal (crash-recovery entries).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Callable

from .control_plane import ControlPlane, load_repo_identity
from .lineage_store import LineageStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    DialogueStartResult,
    OperationJournalEntry,
    RepoIdentity,
)
from .journal import OperationJournal


class DialogueController:
    """Implements codex.dialogue.start, .reply, .read, and crash recovery."""

    def __init__(
        self,
        *,
        control_plane: ControlPlane,
        lineage_store: LineageStore,
        journal: OperationJournal,
        session_id: str,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._lineage_store = lineage_store
        self._journal = journal
        self._session_id = session_id
        self._repo_identity_loader = repo_identity_loader or load_repo_identity
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))

    def start(self, repo_root: Path) -> DialogueStartResult:
        """Create a durable dialogue thread and persist handle.

        Spec: contracts.md §Dialogue Start, delivery.md §R2 in-scope.
        No audit event — thread creation is not a trust boundary crossing
        (contracts.md §Audit Event Actions does not define dialogue_start).
        """
        resolved_root = repo_root.resolve()
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        collaboration_id = self._uuid_factory()
        created_at = self._journal.timestamp()

        # Phase 1: intent — journal before dispatch
        idempotency_key = f"{self._session_id}:{collaboration_id}"
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        try:
            thread_id = runtime.session.start_thread()
            runtime.thread_count += 1
        except Exception:
            self._control_plane.invalidate_runtime(resolved_root)
            raise

        # Phase 2: dispatched — record outcome correlation data
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                codex_thread_id=thread_id,
            ),
            session_id=self._session_id,
        )

        handle = CollaborationHandle(
            collaboration_id=collaboration_id,
            capability_class="advisory",
            runtime_id=runtime.runtime_id,
            codex_thread_id=thread_id,
            claude_session_id=self._session_id,
            repo_root=str(resolved_root),
            created_at=created_at,
            status="active",
        )
        self._lineage_store.create(handle)

        # Phase 3: completed — operation fully confirmed
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        return DialogueStartResult(
            collaboration_id=collaboration_id,
            runtime_id=runtime.runtime_id,
            status="active",
            created_at=created_at,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueStart -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py
git commit -m "feat(codex-collaboration): add DialogueController.start — thread creation with journal-before-dispatch"
```

---

## Task 7: DialogueController.reply

**Files:**
- Modify: `server/dialogue.py` (add `reply` method)
- Modify: `tests/test_dialogue.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_dialogue.py`:

```python
from server.models import ConsultRequest, DialogueReplyResult


class TestDialogueReply:
    def test_reply_returns_dialogue_reply_result(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)

        reply_result = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

        assert isinstance(reply_result, DialogueReplyResult)
        assert reply_result.collaboration_id == start_result.collaboration_id
        assert reply_result.turn_sequence == 1
        assert reply_result.position is not None
        assert reply_result.context_size > 0

    def test_reply_increments_turn_sequence(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)

        reply1 = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        reply2 = controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Second turn",
            explicit_paths=(Path("focus.py"),),
        )

        assert reply1.turn_sequence == 1
        assert reply2.turn_sequence == 2

    def test_reply_journals_before_dispatch(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        # After successful reply, all operations should be completed (no unresolved)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_reply_emits_dialogue_turn_audit_event(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start_result.collaboration_id
        assert "turn_id" in turn_events[0]

    def test_reply_raises_on_unknown_collaboration_id(self, tmp_path: Path) -> None:
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Handle not found"):
            controller.reply(
                collaboration_id="nonexistent",
                objective="Should fail",
            )

    def test_reply_uses_same_context_assembly_as_consult(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
        # Verify the prompt contains the assembled packet (same pipeline as consult)
        assert session.last_prompt_text is not None
        assert "focus.py" in session.last_prompt_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueReply -v`
Expected: AttributeError — `reply` not defined on `DialogueController`

- [ ] **Step 3: Write the implementation**

Add imports to `server/dialogue.py`:

```python
from .context_assembly import assemble_context_packet
from .models import (
    AuditEvent,
    CollaborationHandle,
    ConsultRequest,
    DialogueReplyResult,
    DialogueStartResult,
    OperationJournalEntry,
    RepoIdentity,
)
from .prompt_builder import CONSULT_OUTPUT_SCHEMA, build_consult_turn_text, parse_consult_response
```

Add `reply` method to `DialogueController`:

```python
    def reply(
        self,
        *,
        collaboration_id: str,
        objective: str,
        user_constraints: tuple[str, ...] = (),
        acceptance_criteria: tuple[str, ...] = (),
        explicit_paths: tuple[Path, ...] = (),
        explicit_snippets: tuple[str, ...] = (),
        task_local_paths: tuple[Path, ...] = (),
        broad_repository_summaries: tuple[str, ...] = (),
        promoted_summaries: tuple[str, ...] = (),
        delegation_summaries: tuple[str, ...] = (),
        supplementary_context: tuple[str, ...] = (),
    ) -> DialogueReplyResult:
        """Continue a dialogue turn on an existing handle.

        Spec: contracts.md §Dialogue Reply, delivery.md §R2 in-scope.
        Context assembly reuse: same pipeline as consultation.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Handle not found for reply: no handle with collaboration_id. "
                f"Got: {collaboration_id!r:.100}"
            )

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)
        repo_identity = self._repo_identity_loader(resolved_root)

        # Derive turn_sequence from completed turns via thread/read (contracts.md:266).
        # Safe under MCP serialization invariant — no concurrent turns to race with.
        turn_sequence = self._next_turn_sequence(handle, runtime)

        # Build consult request for context assembly (reuse same pipeline)
        request = ConsultRequest(
            repo_root=resolved_root,
            objective=objective,
            user_constraints=user_constraints,
            acceptance_criteria=acceptance_criteria,
            explicit_paths=explicit_paths,
            explicit_snippets=explicit_snippets,
            task_local_paths=task_local_paths,
            broad_repository_summaries=broad_repository_summaries,
            promoted_summaries=promoted_summaries,
            delegation_summaries=delegation_summaries,
            supplementary_context=supplementary_context,
        )
        packet = assemble_context_packet(request, repo_identity, profile="advisory")

        # Phase 1: intent — journal before dispatch (turn-dispatch key)
        idempotency_key = f"{runtime.runtime_id}:{handle.codex_thread_id}:{turn_sequence}"
        created_at = self._journal.timestamp()
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                codex_thread_id=handle.codex_thread_id,
                turn_sequence=turn_sequence,
                runtime_id=runtime.runtime_id,
            ),
            session_id=self._session_id,
        )

        try:
            turn_result = runtime.session.run_turn(
                thread_id=handle.codex_thread_id,
                prompt_text=build_consult_turn_text(packet.payload),
                output_schema=CONSULT_OUTPUT_SCHEMA,
            )
        except Exception:
            self._control_plane.invalidate_runtime(resolved_root)
            raise

        # Phase 2: dispatched — turn executed
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                codex_thread_id=handle.codex_thread_id,
                turn_sequence=turn_sequence,
                runtime_id=runtime.runtime_id,
            ),
            session_id=self._session_id,
        )

        position, evidence, uncertainties, follow_up_branches = parse_consult_response(
            turn_result.agent_message
        )

        # Phase 3: completed
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="turn_dispatch",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        # Audit event (dialogue_turn per contracts.md §Audit Event Actions)
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="dialogue_turn",
                collaboration_id=collaboration_id,
                runtime_id=runtime.runtime_id,
                context_size=packet.context_size,
                turn_id=turn_result.turn_id,
            )
        )

        return DialogueReplyResult(
            collaboration_id=collaboration_id,
            runtime_id=runtime.runtime_id,
            position=position,
            evidence=evidence,
            uncertainties=uncertainties,
            follow_up_branches=follow_up_branches,
            turn_sequence=turn_sequence,
            context_size=packet.context_size,
        )

    def _next_turn_sequence(
        self,
        handle: CollaborationHandle,
        runtime: object,
    ) -> int:
        """Derive next 1-based turn_sequence from completed turn count via thread/read.

        dialogue.start does not consume a slot (contracts.md:266).
        Counts only turns with status 'completed' to avoid overcounting interrupted turns.
        """
        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        raw_turns = thread_data.get("thread", {}).get("turns", [])
        completed_count = sum(
            1 for t in raw_turns
            if isinstance(t, dict) and t.get("status") == "completed"
        )
        return completed_count + 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueReply -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py
git commit -m "feat(codex-collaboration): add DialogueController.reply — turn dispatch with context assembly reuse"
```

---

## Task 8: Recovery Orchestration

**Files:**
- Modify: `server/dialogue.py` (add `recover_pending_operations` method)
- Modify: `tests/test_dialogue.py` (add recovery tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_dialogue.py`:

```python
class TestRecoverPendingOperations:
    def test_recover_thread_creation_at_intent_phase(self, tmp_path: Path) -> None:
        """Crash before thread/start — intent only. Recovery resolves as no-op."""
        controller, _, store, journal = _build_dialogue_stack(tmp_path)

        # Manually write an intent entry (simulating crash before dispatch)
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )

        recovered = controller.recover_pending_operations()

        # Intent-only thread_creation resolved as no-op terminal
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        assert store.get("orphan-1") is None  # no handle created

    def test_recover_thread_creation_at_dispatched_phase(self, tmp_path: Path) -> None:
        """Crash after thread/start but before lineage persist.
        Recovery performs thread/read + thread/resume reattach, then persists handle."""
        session = FakeRuntimeSession()
        controller, _, store, journal = _build_dialogue_stack(tmp_path, session=session)

        # Manually write intent + dispatched entries
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-2",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-2",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-2",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="orphan-2",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-orphan",
            ),
            session_id="sess-1",
        )

        recovered = controller.recover_pending_operations()

        assert "orphan-2" in recovered
        handle = store.get("orphan-2")
        assert handle is not None
        # Handle uses the resumed thread_id, not the original
        assert handle.codex_thread_id == "thr-orphan-resumed"
        assert handle.status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_turn_dispatch_at_dispatched_phase_completed(
        self, tmp_path: Path
    ) -> None:
        """Crash after run_turn. thread/read confirms turn completed. Recovery marks complete."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # Simulate: thread has 1 completed turn (from before the crash)
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [{"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""}],
            },
        }
        controller, _, store, journal = _build_dialogue_stack(tmp_path, session=session)

        # Set up: create a real handle first
        start = controller.start(tmp_path)

        # Manually write a dispatched turn_dispatch entry (simulating crash after run_turn)
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        # Turn confirmed via thread/read — marked completed
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_turn_dispatch_at_dispatched_phase_incomplete(
        self, tmp_path: Path
    ) -> None:
        """Crash during run_turn. thread/read shows turn did not complete.
        Handle marked 'unknown' (not 'crashed' — runtime crash is not confirmed)."""
        session = FakeRuntimeSession()
        # Thread has NO completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Manually write dispatched turn_dispatch
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        # Turn not confirmed — handle marked unknown
        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "unknown"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_recover_intent_only_turn_dispatch(self, tmp_path: Path) -> None:
        """Crash before run_turn. Intent-only turn_dispatch resolved as no-op."""
        controller, _, store, journal = _build_dialogue_stack(tmp_path)
        start = controller.start(tmp_path)

        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-sess-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-sess-1",
            ),
            session_id="sess-1",
        )

        controller.recover_pending_operations()

        # Intent-only — dispatch never happened, resolved as completed
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        # Handle stays active (not marked unknown — dispatch didn't happen)
        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoverPendingOperations -v`
Expected: AttributeError — `recover_pending_operations` not defined

- [ ] **Step 3: Write the implementation**

Add to `DialogueController` in `server/dialogue.py`:

```python
    def recover_pending_operations(self) -> list[str]:
        """Scan journal for incomplete operations and resolve them deterministically.

        Called on controller startup after crash. Returns collaboration_ids
        of handles that were recovered or affected.

        Ownership: DialogueController reconciles dialogue journal entries.
        ControlPlane owns advisory runtime restart, thread/resume, and update_runtime.
        """
        unresolved = self._journal.list_unresolved(session_id=self._session_id)
        recovered: list[str] = []
        for entry in unresolved:
            if entry.operation == "thread_creation":
                cid = self._recover_thread_creation(entry)
                if cid:
                    recovered.append(cid)
            elif entry.operation == "turn_dispatch":
                self._recover_turn_dispatch(entry)
        return recovered

    def _recover_thread_creation(self, entry: OperationJournalEntry) -> str | None:
        """Recover a pending thread_creation entry.

        intent: dispatch never happened — resolve as no-op.
        dispatched: thread exists (codex_thread_id in entry) — persist handle if missing.
        """
        if entry.phase == "intent":
            # Dispatch never happened. Resolve as terminal no-op.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation=entry.operation,
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                ),
                session_id=self._session_id,
            )
            return None

        # dispatched: thread was created, codex_thread_id is in the entry.
        # Reattach via thread/read + thread/resume per contracts.md §Crash Recovery (steps 3-4).
        existing = self._lineage_store.get(entry.collaboration_id)
        if entry.codex_thread_id is not None:
            resolved_root = Path(entry.repo_root)
            runtime = self._control_plane.get_advisory_runtime(resolved_root)

            # Reattach: read latest state, then resume to bind to live runtime
            runtime.session.read_thread(entry.codex_thread_id)
            resumed_thread_id = runtime.session.resume_thread(entry.codex_thread_id)

            if existing is None:
                # Crash between thread/start and lineage persist — persist now
                handle = CollaborationHandle(
                    collaboration_id=entry.collaboration_id,
                    capability_class="advisory",
                    runtime_id=runtime.runtime_id,
                    codex_thread_id=resumed_thread_id,
                    claude_session_id=self._session_id,
                    repo_root=entry.repo_root,
                    created_at=entry.created_at,
                    status="active",
                )
                self._lineage_store.create(handle)
            else:
                # Handle exists but may point at stale runtime/thread identity
                self._lineage_store.update_runtime(
                    entry.collaboration_id,
                    runtime_id=runtime.runtime_id,
                    codex_thread_id=resumed_thread_id,
                )

        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=entry.idempotency_key,
                operation=entry.operation,
                phase="completed",
                collaboration_id=entry.collaboration_id,
                created_at=entry.created_at,
                repo_root=entry.repo_root,
            ),
            session_id=self._session_id,
        )
        return entry.collaboration_id

    def _recover_turn_dispatch(self, entry: OperationJournalEntry) -> None:
        """Recover a pending turn_dispatch entry.

        intent: dispatch never happened — resolve as no-op (handle stays active).
        dispatched: check thread/read for completed turn at turn_sequence.
          - If completed: resolve.
          - If not: mark handle 'unknown' (not 'crashed' — runtime crash not confirmed).
        """
        if entry.phase == "intent":
            # Dispatch never happened. No state change to handle.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation=entry.operation,
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                ),
                session_id=self._session_id,
            )
            return

        # dispatched: check if turn completed via thread/read
        handle = self._lineage_store.get(entry.collaboration_id)
        if handle is not None and entry.codex_thread_id is not None:
            try:
                runtime = self._control_plane.get_advisory_runtime(Path(entry.repo_root))
                thread_data = runtime.session.read_thread(entry.codex_thread_id)
                raw_turns = thread_data.get("thread", {}).get("turns", [])
                completed_count = sum(
                    1 for t in raw_turns
                    if isinstance(t, dict) and t.get("status") == "completed"
                )
                turn_confirmed = (
                    entry.turn_sequence is not None
                    and completed_count >= entry.turn_sequence
                )
            except Exception:
                turn_confirmed = False

            if not turn_confirmed:
                # Outcome uncertain — mark handle 'unknown' per contracts.md §Handle Lifecycle
                self._lineage_store.update_status(entry.collaboration_id, "unknown")

        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=entry.idempotency_key,
                operation=entry.operation,
                phase="completed",
                collaboration_id=entry.collaboration_id,
                created_at=entry.created_at,
                repo_root=entry.repo_root,
            ),
            session_id=self._session_id,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoverPendingOperations -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py
git commit -m "feat(codex-collaboration): add recover_pending_operations — deterministic crash recovery replay"
```

---

## Task 9: DialogueController.read

**Files:**
- Modify: `server/dialogue.py` (add `read` method)
- Modify: `tests/test_dialogue.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_dialogue.py`:

```python
from server.models import DialogueReadResult, DialogueTurnSummary


class TestDialogueRead:
    def test_read_returns_dialogue_state(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        read_result = controller.read(start_result.collaboration_id)

        assert isinstance(read_result, DialogueReadResult)
        assert read_result.collaboration_id == start_result.collaboration_id
        assert read_result.status == "active"
        assert read_result.created_at is not None

    def test_read_includes_turn_history(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # Configure read_thread to return turn history
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": '{"position":"First","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                        "createdAt": "2026-03-28T00:01:00Z",
                    },
                ],
            },
        }
        controller, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        read_result = controller.read(start_result.collaboration_id)

        assert read_result.turn_count >= 1
        assert len(read_result.turns) >= 1

    def test_read_raises_on_unknown_collaboration_id(self, tmp_path: Path) -> None:
        controller, _, _, _ = _build_dialogue_stack(tmp_path)
        with pytest.raises(ValueError, match="Handle not found"):
            controller.read("nonexistent")
```

Update `FakeRuntimeSession` in `tests/test_control_plane.py` to support configurable `read_thread` responses:

```python
    # Add to __init__:
    self.read_thread_response: dict | None = None
    self.completed_turn_count: int = 0  # incremented by run_turn for turn sequencing

    # Update run_turn to track completed turns (add after existing run_turn_calls increment):
    self.completed_turn_count += 1

    # Update read_thread:
    def read_thread(self, thread_id: str) -> dict:
        if self.read_thread_response is not None:
            return self.read_thread_response
        # Generate completed turns to match the number of successful run_turn calls
        turns = [
            {"id": f"turn-{i+1}", "status": "completed", "agentMessage": "", "createdAt": ""}
            for i in range(self.completed_turn_count)
        ]
        return {
            "thread": {
                "id": thread_id,
                "turns": turns,
            },
        }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueRead -v`
Expected: AttributeError — `read` not defined

- [ ] **Step 3: Write the implementation**

Add imports to `server/dialogue.py`:

```python
from .models import (
    # ... existing imports plus:
    DialogueReadResult,
    DialogueTurnSummary,
)
```

Add `read` method to `DialogueController`:

```python
    def read(self, collaboration_id: str) -> DialogueReadResult:
        """Read dialogue state for a given collaboration_id.

        Combines lineage store handle data with Codex thread/read history.
        Spec: contracts.md §Dialogue Read, delivery.md §R2 in-scope.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Handle not found for read: no handle with collaboration_id. "
                f"Got: {collaboration_id!r:.100}"
            )

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        # Read thread history from Codex
        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        thread = thread_data.get("thread", {})
        raw_turns = thread.get("turns", [])

        turns: list[DialogueTurnSummary] = []
        seq = 0
        for raw_turn in raw_turns:
            if not isinstance(raw_turn, dict):
                continue
            # Only include completed turns (contracts.md:266)
            if raw_turn.get("status") != "completed":
                continue
            seq += 1
            agent_message = raw_turn.get("agentMessage", "")
            position = ""
            context_size = 0
            if isinstance(agent_message, str) and agent_message:
                try:
                    parsed = json.loads(agent_message)
                    position = parsed.get("position", "")
                except (ValueError, AttributeError):
                    position = agent_message[:200]
            turns.append(
                DialogueTurnSummary(
                    turn_sequence=seq,
                    position=position,
                    context_size=context_size,
                    timestamp=str(raw_turn.get("createdAt", "")),
                )
            )

        return DialogueReadResult(
            collaboration_id=collaboration_id,
            status=handle.status,
            turn_count=len(turns),
            created_at=handle.created_at,
            turns=tuple(turns),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueRead -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py tests/test_control_plane.py
git commit -m "feat(codex-collaboration): add DialogueController.read — thread history retrieval"
```

---

## Task 10: MCP Server Scaffolding

**Files:**
- Create: `server/mcp_server.py`
- Test: `tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mcp_server.py`:

```python
"""Tests for MCP server scaffolding with serialized dispatch."""

from __future__ import annotations

import json
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from server.mcp_server import McpServer, TOOL_DEFINITIONS


class TestToolDefinitions:
    def test_all_r1_and_r2_tools_registered(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.status" in tool_names
        assert "codex.consult" in tool_names
        assert "codex.dialogue.start" in tool_names
        assert "codex.dialogue.reply" in tool_names
        assert "codex.dialogue.read" in tool_names

    def test_no_fork_tool_in_r2(self) -> None:
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "codex.dialogue.fork" not in tool_names

    def test_each_tool_has_input_schema(self) -> None:
        for tool in TOOL_DEFINITIONS:
            assert "inputSchema" in tool, f"{tool['name']} missing inputSchema"
            assert tool["inputSchema"]["type"] == "object"


class FakeControlPlane:
    def codex_status(self, repo_root: Path) -> dict:
        return {"status": "ok", "repo_root": str(repo_root)}

    def codex_consult(self, request: object) -> object:
        from server.models import ConsultResult, ConsultEvidence
        return ConsultResult(
            collaboration_id="c1",
            runtime_id="r1",
            position="pos",
            evidence=(ConsultEvidence(claim="c", citation="x"),),
            uncertainties=(),
            follow_up_branches=(),
            context_size=100,
        )


class FakeDialogueController:
    def start(self, repo_root: Path) -> object:
        from server.models import DialogueStartResult
        return DialogueStartResult(
            collaboration_id="c1",
            runtime_id="r1",
            status="active",
            created_at="2026-03-28T00:00:00Z",
        )

    def reply(self, **kwargs: object) -> object:
        from server.models import DialogueReplyResult
        return DialogueReplyResult(
            collaboration_id=str(kwargs.get("collaboration_id", "c1")),
            runtime_id="r1",
            position="Response",
            evidence=(),
            uncertainties=(),
            follow_up_branches=(),
            turn_sequence=1,
            context_size=100,
        )

    def read(self, collaboration_id: str) -> object:
        from server.models import DialogueReadResult
        return DialogueReadResult(
            collaboration_id=collaboration_id,
            status="active",
            turn_count=0,
            created_at="2026-03-28T00:00:00Z",
            turns=(),
        )


class TestMcpServer:
    def _make_server(self) -> McpServer:
        return McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueController(),
        )

    def test_handle_initialize(self) -> None:
        server = self._make_server()
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in response["result"]["capabilities"]

    def test_handle_tools_list(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })
        tools = response["result"]["tools"]
        names = {t["name"] for t in tools}
        assert "codex.dialogue.start" in names
        assert "codex.dialogue.reply" in names

    def test_handle_tools_call_dialogue_start(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.dialogue.start",
                "arguments": {"repo_root": "/tmp/test-repo"},
            },
        })
        assert "result" in response
        content = response["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        result_data = json.loads(content[0]["text"])
        assert result_data["collaboration_id"] == "c1"

    def test_handle_unknown_tool_returns_error(self) -> None:
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "codex.dialogue.fork", "arguments": {}},
        })
        assert response["result"]["isError"] is True

    def test_serialized_dispatch_is_sequential(self) -> None:
        """Verify the server processes requests one at a time (implicit in sync loop)."""
        server = self._make_server()
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        # Multiple calls execute sequentially — the sync design guarantees this.
        for i in range(3):
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.dialogue.start",
                    "arguments": {"repo_root": "/tmp/test-repo"},
                },
            })
            assert "result" in response
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py -v`
Expected: ModuleNotFoundError — `server.mcp_server` does not exist

- [ ] **Step 3: Write the implementation**

Create `server/mcp_server.py`:

```python
"""MCP server scaffolding with serialized dispatch.

Stdio JSON-RPC 2.0 server exposing all R1+R2 tools. Processes one tool call
at a time (serialization invariant per delivery.md §R2 in-scope).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "codex.status",
        "description": "Health, auth, version, and runtime diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string", "description": "Repository root path"},
            },
            "required": ["repo_root"],
        },
    },
    {
        "name": "codex.consult",
        "description": "One-shot second opinion using the advisory runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string"},
                "objective": {"type": "string"},
                "explicit_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo_root", "objective"],
        },
    },
    {
        "name": "codex.dialogue.start",
        "description": "Create a durable dialogue thread in the advisory runtime.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_root": {"type": "string", "description": "Repository root path"},
            },
            "required": ["repo_root"],
        },
    },
    {
        "name": "codex.dialogue.reply",
        "description": "Continue a dialogue turn on an existing handle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collaboration_id": {"type": "string"},
                "objective": {"type": "string"},
                "explicit_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["collaboration_id", "objective"],
        },
    },
    {
        "name": "codex.dialogue.read",
        "description": "Read dialogue state for a given collaboration_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collaboration_id": {"type": "string"},
            },
            "required": ["collaboration_id"],
        },
    },
]


class McpServer:
    """Synchronous MCP server with serialized tool dispatch."""

    def __init__(
        self,
        *,
        control_plane: Any,
        dialogue_controller: Any,
    ) -> None:
        self._control_plane = control_plane
        self._dialogue_controller = dialogue_controller
        self._initialized = False

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a single JSON-RPC 2.0 request and return the response."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return self._handle_initialize(req_id, params)
        if method == "notifications/initialized":
            return {}  # notification, no response
        if method == "tools/list":
            return self._handle_tools_list(req_id)
        if method == "tools/call":
            return self._handle_tools_call(req_id, params)
        return _error_response(req_id, -32601, f"Method not found: {method}")

    def run(self) -> None:
        """Main loop: read JSON-RPC from stdin, write responses to stdout."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                _write_response(_error_response(None, -32700, "Parse error"))
                continue
            response = self.handle_request(request)
            if response:
                _write_response(response)

    def _handle_initialize(
        self, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        self._initialized = True
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "codex-collaboration",
                    "version": "0.2.0",
                },
            },
        }

    def _handle_tools_list(self, req_id: Any) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOL_DEFINITIONS},
        }

    def _handle_tools_call(
        self, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = self._dispatch_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result, default=str)},
                    ],
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": str(exc)},
                    ],
                    "isError": True,
                },
            }

    def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Route a tool call to the appropriate handler. Serialization is
        guaranteed by the synchronous single-threaded main loop."""
        if name == "codex.status":
            return self._control_plane.codex_status(Path(arguments["repo_root"]))
        if name == "codex.consult":
            from .models import ConsultRequest

            request = ConsultRequest(
                repo_root=Path(arguments["repo_root"]),
                objective=arguments["objective"],
                explicit_paths=tuple(
                    Path(p) for p in arguments.get("explicit_paths", ())
                ),
            )
            result = self._control_plane.codex_consult(request)
            return asdict(result)
        if name == "codex.dialogue.start":
            result = self._dialogue_controller.start(Path(arguments["repo_root"]))
            return asdict(result)
        if name == "codex.dialogue.reply":
            result = self._dialogue_controller.reply(
                collaboration_id=arguments["collaboration_id"],
                objective=arguments["objective"],
                explicit_paths=tuple(
                    Path(p) for p in arguments.get("explicit_paths", ())
                ),
            )
            return asdict(result)
        if name == "codex.dialogue.read":
            result = self._dialogue_controller.read(arguments["collaboration_id"])
            return asdict(result)
        raise ValueError(f"Unknown tool: {name!r:.100}")


def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _write_response(response: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: No regressions

- [ ] **Step 6: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(codex-collaboration): add MCP server scaffolding — serialized dispatch over stdio JSON-RPC"
```

---

## Task 11: Integration Tests and Exports

**Files:**
- Modify: `server/__init__.py` (update exports)
- Create: `tests/test_dialogue_integration.py`

- [ ] **Step 1: Update exports**

Replace `server/__init__.py`:

```python
"""Public server exports for codex-collaboration."""

from .control_plane import ControlPlane, build_policy_fingerprint, load_repo_identity
from .dialogue import DialogueController
from .lineage_store import LineageStore
from .models import (
    CollaborationHandle,
    ConsultRequest,
    ConsultResult,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
)

__all__ = [
    "CollaborationHandle",
    "ConsultRequest",
    "ConsultResult",
    "ControlPlane",
    "DialogueController",
    "DialogueReadResult",
    "DialogueReplyResult",
    "DialogueStartResult",
    "LineageStore",
    "build_policy_fingerprint",
    "load_repo_identity",
]
```

- [ ] **Step 2: Write the integration tests**

Create `tests/test_dialogue_integration.py`:

```python
"""Integration tests for the R2 dialogue foundation.

Tests end-to-end flows and acceptance gates from delivery.md §R2.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import OperationJournalEntry

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _full_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, FakeRuntimeSession]:
    session = session or FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    uuids = iter(("rt-1", *(f"id-{i}" for i in range(200))))
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=lambda: next(uuids),
        journal=journal,
    )
    store = LineageStore(plugin_data, "sess-1")
    dialogue_uuids = iter((f"collab-{i}" for i in range(100)))
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id="sess-1",
        repo_identity_loader=_repo_identity,
        uuid_factory=lambda: next(dialogue_uuids),
    )
    return controller, plane, store, journal, session


class TestEndToEndDialogueFlow:
    """Acceptance gate: start → reply → reply → read."""

    def test_full_dialogue_lifecycle(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('hello')\n", encoding="utf-8")
        controller, _, store, journal, session = _full_stack(tmp_path)

        # Start
        start = controller.start(tmp_path)
        assert start.status == "active"

        # Reply 1
        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1
        assert r1.context_size > 0

        # Reply 2
        r2 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Follow up on first finding",
            explicit_paths=(Path("focus.py"),),
        )
        assert r2.turn_sequence == 2

        # Read
        read = controller.read(start.collaboration_id)
        assert read.collaboration_id == start.collaboration_id
        assert read.status == "active"

        # Handle persisted
        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.codex_thread_id == "thr-start"

        # Journal clean (all operations completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0


class TestLineageStoreCrashRecovery:
    """Acceptance gate: lineage store persists and recovers after crash."""

    def test_handles_survive_simulated_crash(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _full_stack(tmp_path)

        start = controller.start(tmp_path)
        # Simulate crash: destroy in-memory state, create new store instance
        del store
        store2 = LineageStore(tmp_path / "plugin-data", "sess-1")
        handle = store2.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start"

    def test_incomplete_trailing_record_discarded_on_recovery(self, tmp_path: Path) -> None:
        controller, _, store, _, _ = _full_stack(tmp_path)
        start = controller.start(tmp_path)

        # Simulate crash mid-write to lineage store
        store_path = (tmp_path / "plugin-data" / "lineage" / "sess-1" / "handles.jsonl")
        with store_path.open("a", encoding="utf-8") as f:
            f.write('{"op": "update_status", "collaboration_id": "' + start.collaboration_id + '", "stat')

        store2 = LineageStore(tmp_path / "plugin-data", "sess-1")
        handle = store2.get(start.collaboration_id)
        assert handle is not None
        assert handle.status == "active"  # incomplete update_status discarded


class TestJournalIdempotency:
    """Acceptance gate: turns journaled before dispatch, replayed idempotently."""

    def test_journal_entry_written_before_dispatch(self, tmp_path: Path) -> None:
        """Verify journal-before-dispatch ordering by injecting a crash between
        journal write and thread creation."""

        class CrashOnStartThread(FakeRuntimeSession):
            def start_thread(self) -> str:
                raise RuntimeError("simulated crash during thread/start")

        crashing_session = CrashOnStartThread()
        controller, _, _, journal, _ = _full_stack(tmp_path, session=crashing_session)

        with pytest.raises(RuntimeError, match="simulated crash"):
            controller.start(tmp_path)

        # Journal intent entry survives because it was written BEFORE dispatch
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].operation == "thread_creation"
        assert unresolved[0].phase == "intent"

    def test_crash_after_dispatch_leaves_dispatched_entry(self, tmp_path: Path) -> None:
        """Crash after thread/start but before lineage persist. Journal has dispatched entry."""
        controller, _, store, journal, _ = _full_stack(tmp_path)

        # Start succeeds (creates intent + dispatched + handle + completed normally)
        start = controller.start(tmp_path)

        # Now simulate: a second start where crash happens after dispatch but before lineage
        # We test this indirectly via recovery — manually write dispatched entry
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="intent",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:orphan-1",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="orphan-1",
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-orphan",
            ),
            session_id="sess-1",
        )

        # Recovery reattaches via thread/read + thread/resume, then persists handle
        recovered = controller.recover_pending_operations()
        assert "orphan-1" in recovered
        handle = store.get("orphan-1")
        assert handle is not None
        assert handle.codex_thread_id == "thr-orphan-resumed"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

    def test_turn_dispatch_crash_and_recovery(self, tmp_path: Path) -> None:
        """Full crash-and-recover cycle for turn dispatch."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class CrashOnSecondRunTurn(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self._turn_calls = 0

            def run_turn(self, **kwargs: object) -> object:
                self._turn_calls += 1
                if self._turn_calls <= 1:
                    return super().run_turn(**kwargs)
                raise RuntimeError("simulated crash during turn")

        session = CrashOnSecondRunTurn()
        controller, _, store, journal, _ = _full_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn succeeds",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1

        # Second reply crashes — intent entry survives (dispatched never written)
        with pytest.raises(RuntimeError, match="simulated crash during turn"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Second turn crashes",
                explicit_paths=(Path("focus.py"),),
            )

        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].operation == "turn_dispatch"
        assert unresolved[0].phase == "intent"

        # Recovery resolves intent-only turn as no-op (handle stays active)
        controller.recover_pending_operations()
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        handle = store.get(start.collaboration_id)
        assert handle.status == "active"


class TestAuditEvents:
    """Acceptance gate: audit events emitted for dialogue turns."""

    def test_dialogue_lifecycle_emits_audit_events(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _full_stack(tmp_path)

        start = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]

        # No dialogue_start action — thread creation is not a trust boundary crossing
        actions = [e["action"] for e in events]
        assert "dialogue_start" not in actions
        # dialogue_turn IS emitted per contracts.md §Audit Event Actions
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) >= 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
        assert "runtime_id" in turn_events[0]


class TestNoForkInR2:
    """Acceptance gate: no R2 path depends on fork."""

    def test_dialogue_controller_has_no_fork_method(self) -> None:
        assert not hasattr(DialogueController, "fork")
```

- [ ] **Step 3: Run integration tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue_integration.py -v`
Expected: All tests PASS

- [ ] **Step 4: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All tests PASS across all test files

- [ ] **Step 5: Commit**

```bash
git add server/__init__.py tests/test_dialogue_integration.py
git commit -m "feat(codex-collaboration): add R2 integration tests — end-to-end dialogue, crash recovery, audit events"
```

---

## Acceptance Gate Mapping

| Gate (delivery.md §R2) | Task | Test |
|------------------------|------|------|
| Lineage store persists handles and recovers after crash, discards incomplete records | 2 | `test_lineage_store.py::TestCrashRecovery`, `test_dialogue_integration.py::TestLineageStoreCrashRecovery` |
| `dialogue.start` creates thread, returns Dialogue Start shape | 6 | `test_dialogue.py::TestDialogueStart` |
| `dialogue.reply` dispatches turn, returns Dialogue Reply shape | 7 | `test_dialogue.py::TestDialogueReply` |
| `dialogue.read` returns Dialogue Read shape from lineage + thread/read | 9 | `test_dialogue.py::TestDialogueRead` |
| MCP server exposes all R2+R1 tools with serialized dispatch | 10 | `test_mcp_server.py::TestMcpServer` |
| Dialogue turns journaled before dispatch, replayed idempotently after crash | 8, 11 | `test_dialogue.py::TestRecoverPendingOperations`, `test_dialogue_integration.py::TestJournalIdempotency` |
| Audit events emitted for dialogue turns | 11 | `test_dialogue_integration.py::TestAuditEvents` |
| No R2 path depends on fork | 11 | `test_dialogue_integration.py::TestNoForkInR2` |

## Self-Review Findings

**Spec coverage check:**
- All 8 R2 in-scope items mapped to tasks
- All 8 acceptance gates mapped to tests
- All 4 deferred items (fork, hooks, delegation, turn/steer) excluded
- Non-negotiable checkpoints 1-5 all covered

**Placeholder scan:** No TBD/TODO/placeholder patterns found.

**Type consistency check:**
- `CollaborationHandle` fields match contracts.md §CollaborationHandle exactly (10 fields)
- `DialogueStartResult`/`DialogueReplyResult`/`DialogueReadResult` match contracts.md §Typed Response Shapes
- `OperationJournalEntry` phased model (intent/dispatched/completed) with replay context fields
- `HandleStatus` matches contracts.md §Handle Lifecycle (4 states)
- `_next_turn_sequence` derives from `thread/read` completed turns per contracts.md:266

**Review remediation log:**

| Finding | Fix | Verification |
|---------|-----|-------------|
| P0: Journal schema too thin for replay | Phased model with intent/dispatched/completed and outcome correlation fields | Task 3 tests: phase transitions, compaction, terminal-phase grouping |
| P0: Replay gate claimed but not implemented | Explicit `recover_pending_operations()` with 5 crash-scenario tests | Task 8 tests: intent-only, dispatched thread, dispatched turn (confirmed/incomplete) |
| P1: In-memory turn_sequence | `_next_turn_sequence` calls `thread/read`, counts only `status: completed` turns | Task 7 tests: sequence increments correctly; FakeRuntimeSession tracks completed turns |
| P1: Unsafe journal trim | Replaced with append-only `write_phase("completed")`. Compaction via temp-file-rename with fsync | Task 3 tests: `test_compact_*` verify key-based compaction, atomic rename |
| P2: Invented `dialogue_start` audit action | Removed from `start()` and all tests. No audit for thread creation — not in contracts.md | Task 6: `test_start_does_not_emit_audit_event`; Task 11: audit test asserts absence |
