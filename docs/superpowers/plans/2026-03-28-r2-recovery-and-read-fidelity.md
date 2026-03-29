# R2 Recovery and Read Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix four findings from post-R2 review: dead recovery path, intent-phase turn loss, missing lifecycle guard, and bogus `context_size` in `dialogue.read`.

**Architecture:** Add `context_size` to the journal intent entry so recovery has it. Add a crash-safe per-turn metadata store so `read()` can return real `context_size` values. Enforce write ordering: metadata store write BEFORE journal `completed`, so any crash that loses the store also leaves the journal unresolved for recovery. Fix intent-phase turn recovery to verify via `thread/read` and mark `unknown` on ambiguity. Add lifecycle guard to `reply()`. Wire a startup recovery coordinator that reconciles journals then reattaches active handles.

**Tech Stack:** Python 3.12, pytest, frozen dataclasses, append-only JSONL with fsync

**Baseline:** 158 tests passing on branch `feature/codex-collaboration-r2-dialogue`. All changes in `packages/plugins/codex-collaboration/`.

**Spec references:**
- contracts.md:132-139 — Handle lifecycle state machine
- contracts.md:141-151 — Crash recovery contract (reattach steps)
- contracts.md:269-279 — Dialogue Read response shape (`context_size: integer`)
- recovery-and-journal.md:33-39 — Write ordering: journal before dispatch
- recovery-and-journal.md:53-57 — Session scope: journal is session-bounded
- delivery.md:201,218 — `codex.dialogue.read` uses lineage + Codex `thread/read`

**Key invariants:**
1. The metadata store write MUST happen before journal `completed`. If this ordering is violated, a crash can leave a terminally-completed journal entry with no metadata store record — an unrecoverable integrity hole.
2. `context_size` in contracts.md §Dialogue Read is `integer`, not nullable. A missing store entry for a completed turn is an integrity failure — `read()` raises `RuntimeError`, unconditionally.
3. **Metadata completeness enforcement** operates at three levels with different scopes:
   - **Startup quarantine (after restart):** `recover_startup()` quarantines any active handle whose completed turn count (from `thread/read`) exceeds its TurnStore entry count as `unknown`. Catches both legacy dialogues and post-fix corruption. `reply()` rejects `unknown` handles via the lifecycle guard.
   - **`read()` integrity check (live process):** Raises unconditionally on missing TurnStore entries. This is the detection path within a running process — it fires before a `read()` consumer sees bad data, but it does not prevent a prior `reply()` from dispatching against the same handle.
   - **Write-ordering invariant (prevention):** The TurnStore write uses fsync and occurs before journal `completed`. A failed store write propagates as an exception from `reply()`, halting the operation. In-process metadata loss without a process crash is unlikely but not structurally prevented — `reply()` does not perform a completeness preflight.

   The system cannot distinguish legacy from corruption without a rollout marker. `unknown` is the correct disposition for both per contracts.md §Handle Lifecycle.
4. Session-ID stability across in-session restarts is an external wiring contract. This plan does not validate it — there is no production composition root in this repo. The coordinator documents the contract.
5. `_recover_turn_dispatch` raises on missing handle or thread_id. These are integrity violations, not recoverable states — silent terminalization erases in-flight evidence.
6. Phase 1 (journal reconciliation) returns a skip set of collaboration_ids it already resumed. Phase 2 (bulk reattach) excludes these to avoid double-resume churn.

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `server/turn_store.py` | Crash-safe per-turn metadata store (append-only JSONL, keyed by `collaboration_id:turn_sequence`) |
| `tests/test_turn_store.py` | Unit tests for turn store CRUD, crash recovery, replay |
| `tests/test_recovery_coordinator.py` | Tests for startup recovery: journal reconciliation + active-handle reattach |

### Modified Files

| File | Changes |
|------|---------|
| `server/models.py:222-239` | Add `context_size: int \| None = None` to `OperationJournalEntry` |
| `server/dialogue.py:132-267` | `reply()`: write metadata store before journal completed; add lifecycle guard |
| `server/dialogue.py:355-410` | `_recover_turn_dispatch()`: both phases verify via `thread/read`; repair metadata store on confirm; `unknown` on unconfirmed |
| `server/dialogue.py:430-484` | `read()`: use `thread/read` as base set, left-join metadata store for `context_size` |
| `server/dialogue.py:32-51` | Constructor: accept `turn_store` parameter |
| `server/dialogue.py:269-287` | `recover_pending_operations()`: no structural change, but `_recover_turn_dispatch` behavior changes |
| `server/mcp_server.py:78-89,107-120` | Add `startup()` method; call it at top of `run()`; accept `turn_store` in constructor |
| `tests/test_dialogue.py:21-51` | Update `_build_dialogue_stack` to wire `TurnStore` |
| `tests/test_dialogue.py:105-197` | Update reply tests for metadata store; add lifecycle guard tests |
| `tests/test_dialogue.py:199-372` | Update recovery tests for new intent-phase behavior |
| `tests/test_dialogue.py:378-431` | Update read tests for `context_size` enrichment and integrity check |
| `tests/test_dialogue_integration.py:22-50` | Update `_full_stack` to wire `TurnStore` |
| `tests/test_dialogue_integration.py` | Add integration tests for recovery coordinator and crash window |
| `tests/test_mcp_server.py:50-81,84-89` | Update `FakeDialogueController` and server construction for `startup()` |

---

## Task 1: Add `context_size` to `OperationJournalEntry`

**Files:**
- Modify: `server/models.py:222-239`
- Test: `tests/test_models_r2.py`

- [ ] **Step 1: Write failing test — `context_size` field exists on `OperationJournalEntry`**

In `tests/test_models_r2.py`, add a test to the existing `OperationJournalEntry` test class:

```python
def test_operation_journal_entry_has_context_size_field(self) -> None:
    entry = OperationJournalEntry(
        idempotency_key="rt-1:thr-1:1",
        operation="turn_dispatch",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
        codex_thread_id="thr-1",
        turn_sequence=1,
        runtime_id="rt-1",
        context_size=4096,
    )
    assert entry.context_size == 4096


def test_operation_journal_entry_context_size_defaults_to_none(self) -> None:
    entry = OperationJournalEntry(
        idempotency_key="sess-1:collab-1",
        operation="thread_creation",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-03-28T00:00:00Z",
        repo_root="/repo",
    )
    assert entry.context_size is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --package codex-collaboration pytest tests/test_models_r2.py -v -k "context_size"`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'context_size'`

- [ ] **Step 3: Add `context_size` field to `OperationJournalEntry`**

In `server/models.py`, add after line 239 (`runtime_id` field):

```python
    context_size: int | None = None  # turn_dispatch only, set at intent (pre-dispatch)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --package codex-collaboration pytest tests/test_models_r2.py -v -k "context_size"`
Expected: 2 PASSED

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: 160 passed (158 existing + 2 new)

- [ ] **Step 6: Commit**

```bash
git add server/models.py tests/test_models_r2.py
git commit -m "feat(codex-collaboration): add context_size to OperationJournalEntry for pre-dispatch recovery"
```

---

## Task 2: Create crash-safe per-turn metadata store

**Files:**
- Create: `server/turn_store.py`
- Create: `tests/test_turn_store.py`

The store persists `context_size` per `(collaboration_id, turn_sequence)`. Append-only JSONL with fsync, same crash-safety pattern as `lineage_store.py`. On read, replays the log — last record per key wins. Incomplete trailing records discarded on load.

- [ ] **Step 1: Write failing tests for TurnStore**

Create `tests/test_turn_store.py`:

```python
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

    def test_write_uses_fsync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest tests/test_turn_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'server.turn_store'`

- [ ] **Step 3: Implement TurnStore**

Create `server/turn_store.py`:

```python
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

    def _replay(self) -> dict[str, int]:
        """Replay JSONL log. Last record per key wins."""
        if not self._store_path.exists():
            return {}
        entries: dict[str, int] = {}
        with self._store_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = f"{record['collaboration_id']}:{record['turn_sequence']}"
                entries[key] = record["context_size"]
        return entries
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package codex-collaboration pytest tests/test_turn_store.py -v`
Expected: 11 PASSED

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: 171 passed (160 + 11 new)

- [ ] **Step 6: Commit**

```bash
git add server/turn_store.py tests/test_turn_store.py
git commit -m "feat(codex-collaboration): add crash-safe per-turn metadata store"
```

---

## Task 3: Wire TurnStore into DialogueController and update `reply()` write ordering

This task changes the `reply()` write sequence so the metadata store write happens BEFORE journal `completed`. It also adds `context_size` to the journal intent entry.

**Files:**
- Modify: `server/dialogue.py:32-51` (constructor)
- Modify: `server/dialogue.py:132-267` (`reply()` method)
- Modify: `tests/test_dialogue.py:1-51` (imports and `_build_dialogue_stack`)
- Modify: `tests/test_dialogue_integration.py:1-50` (imports and `_full_stack`)

- [ ] **Step 1: Write failing test — `reply()` writes to turn store before journal completed**

In `tests/test_dialogue.py`, add to `TestDialogueReply`:

```python
def test_reply_persists_context_size_in_turn_store(self, tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    controller, _, _, _, turn_store = _build_dialogue_stack(tmp_path)
    start_result = controller.start(tmp_path)

    reply_result = controller.reply(
        collaboration_id=start_result.collaboration_id,
        objective="Review focus.py",
        explicit_paths=(Path("focus.py"),),
    )

    stored = turn_store.get(start_result.collaboration_id, turn_sequence=1)
    assert stored is not None
    assert stored == reply_result.context_size
    assert stored > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestDialogueReply::test_reply_persists_context_size_in_turn_store -v`
Expected: FAIL (either `_build_dialogue_stack` doesn't return `turn_store`, or `TurnStore` not wired)

- [ ] **Step 3: Write failing test — journal intent carries `context_size`**

In `tests/test_dialogue.py`, add to `TestDialogueReply`:

```python
def test_reply_journal_intent_carries_context_size(self, tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")

    class CrashAfterIntent(FakeRuntimeSession):
        """Crash after intent is written but before run_turn executes."""
        def run_turn(self, **kwargs: object) -> object:
            raise RuntimeError("crash after intent")

    session = CrashAfterIntent()
    controller, _, _, journal, _ = _build_dialogue_stack(tmp_path, session=session)
    start_result = controller.start(tmp_path)

    with pytest.raises(RuntimeError, match="crash after intent"):
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )

    # Intent entry should carry context_size (non-None, > 0)
    unresolved = journal.list_unresolved(session_id="sess-1")
    turn_intents = [e for e in unresolved if e.operation == "turn_dispatch"]
    assert len(turn_intents) == 1
    assert turn_intents[0].context_size is not None
    assert turn_intents[0].context_size > 0
```

- [ ] **Step 4: Write failing test — metadata store write ordering (crash after store, before completed)**

In `tests/test_dialogue_integration.py`, add a new test class:

```python
class TestTurnStoreWriteOrdering:
    """The metadata store write must land before journal completed.
    A crash in that window must leave the journal unresolved so recovery can repair."""

    def test_crash_after_store_write_before_completed_is_recoverable(
        self, tmp_path: Path
    ) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class CrashAfterDispatchedPhase(FakeRuntimeSession):
            """Let run_turn succeed, then crash when the THIRD journal write
            (completed phase for turn_dispatch) would happen.

            We simulate this by tracking run_turn calls and making the second
            call to journal.write_phase after run_turn raise."""
            pass

        # For this test we directly verify the state after a partial reply.
        # Simulate: intent written, run_turn succeeds, dispatched written,
        # store written, then crash before completed.
        session = FakeRuntimeSession()
        controller, plane, store, journal, session = _full_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # Perform a normal reply to establish one completed turn
        r1 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert r1.turn_sequence == 1

        # Now manually simulate a partial second reply:
        # Write intent + dispatched + store entry, but NOT completed
        from server.models import OperationJournalEntry
        from server.turn_store import TurnStore

        turn_store = TurnStore(tmp_path / "plugin-data", "sess-1")
        idem_key = f"rt-1:thr-start:2"
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idem_key,
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:02:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=2,
                runtime_id="rt-1",
                context_size=5000,
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idem_key,
                operation="turn_dispatch",
                phase="dispatched",
                collaboration_id=start.collaboration_id,
                created_at="2026-03-28T00:02:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=2,
                runtime_id="rt-1",
                context_size=5000,
            ),
            session_id="sess-1",
        )
        # Store write landed (before completed)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=5000)

        # Journal is unresolved (dispatched, not completed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 1
        assert unresolved[0].idempotency_key == idem_key

        # Configure thread/read to confirm 2 completed turns
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                    {"id": "t2", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }

        # Recovery confirms the turn and resolves the journal
        controller.recover_pending_operations()
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

        # Store entry survived — read can use it
        assert turn_store.get(start.collaboration_id, turn_sequence=2) == 5000
```

- [ ] **Step 5: Update `_build_dialogue_stack` and `_full_stack` to wire TurnStore**

In `tests/test_dialogue.py`, update imports and helper:

```python
# Add import at top:
from server.turn_store import TurnStore

# Update _build_dialogue_stack return type and body:
def _build_dialogue_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
    session_id: str = "sess-1",
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, TurnStore]:
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
    turn_store = TurnStore(plugin_data, session_id)
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id=session_id,
        turn_store=turn_store,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{session_id}", *(f"id-{i}" for i in range(100)))).__next__,
    )
    return controller, plane, store, journal, turn_store
```

Update ALL existing callers in `tests/test_dialogue.py` that unpack the result of `_build_dialogue_stack`. Every call site currently unpacks 4 values — change to 5:

```python
# Old pattern (throughout the file):
controller, _, _, _ = _build_dialogue_stack(tmp_path)
controller, _, store, _ = _build_dialogue_stack(tmp_path)
controller, _, _, journal = _build_dialogue_stack(tmp_path)
controller, _, store, journal = _build_dialogue_stack(tmp_path)

# New pattern:
controller, _, _, _, _ = _build_dialogue_stack(tmp_path)
controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
controller, _, store, journal, _ = _build_dialogue_stack(tmp_path)
```

In `tests/test_dialogue_integration.py`, update imports and `_full_stack`:

```python
# Add import at top:
from server.turn_store import TurnStore

# Update _full_stack return type:
def _full_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, FakeRuntimeSession]:
    # ... existing body unchanged until after store = LineageStore(...)
    store = LineageStore(plugin_data, "sess-1")
    turn_store = TurnStore(plugin_data, "sess-1")
    # ... update DialogueController construction:
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id="sess-1",
        turn_store=turn_store,
        repo_identity_loader=_repo_identity,
        uuid_factory=lambda: next(dialogue_uuids),
    )
    return controller, plane, store, journal, session
```

Note: `_full_stack` return type stays the same (it doesn't expose `turn_store`). The `TurnStore` is wired internally. Tests that need direct access to the `TurnStore` should construct it separately using the same `plugin_data` and `session_id`.

- [ ] **Step 6: Update `DialogueController.__init__` to accept `turn_store`**

In `server/dialogue.py`, update the constructor:

```python
# Add import at top:
from .turn_store import TurnStore

# Update __init__ signature and body:
class DialogueController:
    """Implements codex.dialogue.start, .reply, .read, and crash recovery."""

    def __init__(
        self,
        *,
        control_plane: ControlPlane,
        lineage_store: LineageStore,
        journal: OperationJournal,
        session_id: str,
        turn_store: TurnStore,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._lineage_store = lineage_store
        self._journal = journal
        self._session_id = session_id
        self._turn_store = turn_store
        self._repo_identity_loader = repo_identity_loader or load_repo_identity
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
```

- [ ] **Step 7: Update `reply()` — add `context_size` to intent entry and write store before completed**

In `server/dialogue.py`, modify `reply()`. The new write sequence is:

1. Assemble packet (context_size known)
2. Intent journal entry **with context_size**
3. `run_turn()`
4. Dispatched journal entry
5. **Metadata store write**
6. Completed journal entry
7. Audit event

Replace the `reply()` method body (lines 132-267). The full updated method:

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

        Write ordering invariant: metadata store write MUST happen before
        journal completed. See plan doc §Key invariants.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Reply failed: handle not found. "
                f"Got: collaboration_id={collaboration_id!r:.100}"
            )
        if handle.status != "active":
            raise ValueError(
                f"Reply failed: handle not active. "
                f"Got: status={handle.status!r}, collaboration_id={collaboration_id!r:.100}"
            )

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)
        repo_identity = self._repo_identity_loader(resolved_root)

        turn_sequence = self._next_turn_sequence(handle, runtime)

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

        # Phase 1: intent — journal before dispatch, WITH context_size
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
                context_size=packet.context_size,
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
                context_size=packet.context_size,
            ),
            session_id=self._session_id,
        )

        position, evidence, uncertainties, follow_up_branches = parse_consult_response(
            turn_result.agent_message
        )

        # Metadata store: MUST write before journal completed
        self._turn_store.write(
            collaboration_id,
            turn_sequence=turn_sequence,
            context_size=packet.context_size,
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

        # Audit event
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
```

- [ ] **Step 8: Run the new tests**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestDialogueReply::test_reply_persists_context_size_in_turn_store tests/test_dialogue.py::TestDialogueReply::test_reply_journal_intent_carries_context_size -v`
Expected: 2 PASSED

- [ ] **Step 9: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing (existing + new tests). Some existing tests may need the unpacking fix from Step 5.

- [ ] **Step 10: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py tests/test_dialogue_integration.py
git commit -m "feat(codex-collaboration): wire TurnStore into reply() with correct write ordering"
```

---

## Task 4: Fix `_recover_turn_dispatch()` — verify both phases via `thread/read`

**Files:**
- Modify: `server/dialogue.py:355-410` (`_recover_turn_dispatch`)
- Modify: `tests/test_dialogue.py:199-372` (recovery tests)

The current code treats intent-phase `turn_dispatch` as a no-op. The fix: both `intent` and `dispatched` phases verify via `thread/read`. Confirmed → resolve + repair metadata store. Unconfirmed → mark handle `unknown`.

- [ ] **Step 1: Write failing test — intent-phase verifies via `thread/read` and marks `unknown` when unconfirmed**

In `tests/test_dialogue.py`, modify the existing `test_recover_intent_only_turn_dispatch` test to assert `unknown` status:

```python
def test_recover_intent_only_turn_dispatch_marks_unknown(self, tmp_path: Path) -> None:
    """Crash before run_turn. Intent-only turn_dispatch: thread/read check
    does not confirm the turn. Handle marked 'unknown' (ambiguous, not no-op)."""
    session = FakeRuntimeSession()
    # thread/read shows no completed turns at turn_sequence=1
    session.read_thread_response = {
        "thread": {"id": "thr-start", "turns": []},
    }
    controller, _, store, journal, _ = _build_dialogue_stack(tmp_path, session=session)
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
            context_size=4096,
        ),
        session_id="sess-1",
    )

    controller.recover_pending_operations()

    unresolved = journal.list_unresolved(session_id="sess-1")
    assert len(unresolved) == 0
    handle = store.get(start.collaboration_id)
    assert handle.status == "unknown"
```

- [ ] **Step 2: Write failing test — intent-phase confirmed via `thread/read` repairs metadata store**

```python
def test_recover_intent_turn_dispatch_confirmed_repairs_store(self, tmp_path: Path) -> None:
    """Intent-phase turn_dispatch but thread/read confirms the turn completed.
    Recovery resolves the journal and repairs the metadata store."""
    session = FakeRuntimeSession()
    session.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": "2026-03-28T00:01:30Z"},
            ],
        },
    }
    controller, _, store, journal, turn_store = _build_dialogue_stack(tmp_path, session=session)
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
            context_size=4096,
        ),
        session_id="sess-1",
    )

    controller.recover_pending_operations()

    unresolved = journal.list_unresolved(session_id="sess-1")
    assert len(unresolved) == 0
    handle = store.get(start.collaboration_id)
    assert handle.status == "active"
    # Metadata store repaired with context_size from journal intent
    assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096
```

- [ ] **Step 3: Write failing test — dispatched-phase confirmed repairs metadata store**

```python
def test_recover_dispatched_turn_dispatch_confirmed_repairs_store(
    self, tmp_path: Path
) -> None:
    """Dispatched-phase turn_dispatch, turn confirmed. Recovery resolves and repairs store."""
    session = FakeRuntimeSession()
    session.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
            ],
        },
    }
    controller, _, store, journal, turn_store = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)

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
            context_size=4096,
        ),
        session_id="sess-1",
    )

    controller.recover_pending_operations()

    unresolved = journal.list_unresolved(session_id="sess-1")
    assert len(unresolved) == 0
    assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096
```

- [ ] **Step 4: Run new tests to verify they fail**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestRecoverPendingOperations -v -k "intent_only or intent_turn or dispatched_turn_dispatch_confirmed_repairs"`
Expected: FAIL (intent test expects `unknown` but gets `active`; store repair tests fail)

- [ ] **Step 5: Implement unified recovery for `_recover_turn_dispatch`**

Replace `_recover_turn_dispatch` in `server/dialogue.py`:

```python
    def _recover_turn_dispatch(self, entry: OperationJournalEntry) -> None:
        """Recover a pending turn_dispatch entry.

        Both intent and dispatched phases verify via thread/read:
        - Confirmed (completed turn at turn_sequence): resolve journal, repair metadata store.
        - Unconfirmed: mark handle 'unknown' (ambiguous — dispatch may or may not have happened).

        Does NOT silently treat intent as no-op. Absence of evidence is not
        evidence of absence: a crash between run_turn() call and journal write
        leaves an intent record even though dispatch occurred.
        """
        handle = self._lineage_store.get(entry.collaboration_id)
        if handle is None:
            raise RuntimeError(
                f"Recovery integrity failure: no handle for turn_dispatch entry. "
                f"Got: collaboration_id={entry.collaboration_id!r:.100}"
            )
        if entry.codex_thread_id is None:
            raise RuntimeError(
                f"Recovery integrity failure: no codex_thread_id in turn_dispatch entry. "
                f"Got: idempotency_key={entry.idempotency_key!r:.100}"
            )

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

        if turn_confirmed:
            # Repair metadata store if entry has context_size
            if entry.context_size is not None and entry.turn_sequence is not None:
                self._turn_store.write(
                    entry.collaboration_id,
                    turn_sequence=entry.turn_sequence,
                    context_size=entry.context_size,
                )
        else:
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

- [ ] **Step 6: Remove the old `test_recover_intent_only_turn_dispatch` test**

The old test at `tests/test_dialogue.py` asserts `handle.status == "active"` after intent-only recovery. This is now incorrect — the handle should be `unknown`. Delete the old test; the new `test_recover_intent_only_turn_dispatch_marks_unknown` replaces it.

- [ ] **Step 7: Run all recovery tests**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestRecoverPendingOperations -v`
Expected: All PASSED

- [ ] **Step 8: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 9: Update integration test for turn dispatch crash and recovery**

The existing `TestJournalIdempotency::test_turn_dispatch_crash_and_recovery` (test_dialogue_integration.py:192-237) asserts `handle.status == "active"` after intent-only recovery. Update to expect `unknown`:

In `tests/test_dialogue_integration.py`, update lines 236-237:

```python
        # Old:
        # handle = store.get(start.collaboration_id)
        # assert handle.status == "active"

        # New: intent-only turn_dispatch with no thread/read confirmation → unknown
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"
```

- [ ] **Step 10: Run full suite again**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 11: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py tests/test_dialogue_integration.py
git commit -m "fix(codex-collaboration): intent-phase turn recovery verifies via thread/read, marks unknown on ambiguity"
```

---

## Task 5: Add `reply()` lifecycle guard

**Files:**
- Modify: `server/dialogue.py:132-167` (already done in Task 3 — the guard is in the updated `reply()`)
- Modify: `tests/test_dialogue.py`

The lifecycle guard was included in Task 3's `reply()` rewrite. This task adds the tests that prove it works.

- [ ] **Step 1: Write failing tests for lifecycle guard**

In `tests/test_dialogue.py`, add to `TestDialogueReply`:

```python
def test_reply_rejects_completed_handle(self, tmp_path: Path) -> None:
    controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
    start = controller.start(tmp_path)
    store.update_status(start.collaboration_id, "completed")
    with pytest.raises(ValueError, match="handle not active"):
        controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Should fail",
        )

def test_reply_rejects_unknown_handle(self, tmp_path: Path) -> None:
    controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
    start = controller.start(tmp_path)
    store.update_status(start.collaboration_id, "unknown")
    with pytest.raises(ValueError, match="handle not active"):
        controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Should fail",
        )

def test_reply_rejects_crashed_handle(self, tmp_path: Path) -> None:
    controller, _, store, _, _ = _build_dialogue_stack(tmp_path)
    start = controller.start(tmp_path)
    store.update_status(start.collaboration_id, "crashed")
    with pytest.raises(ValueError, match="handle not active"):
        controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Should fail",
        )
```

- [ ] **Step 2: Write test that `read()` still works on non-active handles**

```python
# In TestDialogueRead, add:
def test_read_works_on_unknown_handle(self, tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    session.read_thread_response = {"thread": {"id": "thr-start", "turns": []}}
    controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)
    store.update_status(start.collaboration_id, "unknown")

    read_result = controller.read(start.collaboration_id)
    assert read_result.status == "unknown"

def test_read_works_on_completed_handle(self, tmp_path: Path) -> None:
    session = FakeRuntimeSession()
    session.read_thread_response = {"thread": {"id": "thr-start", "turns": []}}
    controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)
    store.update_status(start.collaboration_id, "completed")

    read_result = controller.read(start.collaboration_id)
    assert read_result.status == "completed"
```

- [ ] **Step 3: Run new tests**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py -v -k "rejects_completed or rejects_unknown or rejects_crashed or read_works_on"`
Expected: All PASSED (guard already implemented in Task 3)

- [ ] **Step 4: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 5: Commit**

```bash
git add tests/test_dialogue.py
git commit -m "test(codex-collaboration): add lifecycle guard and read-on-non-active tests"
```

---

## Task 6: Update `read()` to enrich from metadata store

**Files:**
- Modify: `server/dialogue.py:430-484` (`read()` method)
- Modify: `tests/test_dialogue.py` (read tests)
- Modify: `tests/test_dialogue_integration.py` (end-to-end read test)

`read()` continues to use `thread/read` as the base set of completed turns (per delivery.md:201,218). Per-turn `context_size` is enriched from the metadata store via left-join on `turn_sequence`. A completed turn with no metadata store entry is an integrity failure — raises `RuntimeError`.

- [ ] **Step 1: Write failing test — `read()` returns real context_size**

```python
# In TestDialogueRead, add:
def test_read_returns_real_context_size_from_store(self, tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    controller, _, _, _, turn_store = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)

    reply_result = controller.reply(
        collaboration_id=start.collaboration_id,
        objective="First turn",
        explicit_paths=(Path("focus.py"),),
    )

    # Configure thread/read to match the completed turn
    session.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "turn-1",
                    "status": "completed",
                    "agentMessage": '{"position":"Pos","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                    "createdAt": "2026-03-28T00:01:00Z",
                },
            ],
        },
    }

    read_result = controller.read(start.collaboration_id)
    assert read_result.turn_count == 1
    assert len(read_result.turns) == 1
    assert read_result.turns[0].context_size == reply_result.context_size
    assert read_result.turns[0].context_size > 0
```

- [ ] **Step 2: Write failing test — missing metadata triggers integrity error**

```python
def test_read_raises_on_missing_metadata_for_post_fix_turn(self, tmp_path: Path) -> None:
    """In a post-fix session (some turns have metadata), a completed turn
    with no metadata store entry is an integrity failure."""
    session = FakeRuntimeSession()
    session.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "turn-1",
                    "status": "completed",
                    "agentMessage": '{"position":"Pos","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                    "createdAt": "2026-03-28T00:01:00Z",
                },
                {
                    "id": "turn-2",
                    "status": "completed",
                    "agentMessage": '{"position":"Pos2","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                    "createdAt": "2026-03-28T00:02:00Z",
                },
            ],
        },
    }
    controller, _, _, _, turn_store = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)

    # Write metadata for turn 1 but NOT turn 2 — partial metadata = post-fix session
    turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

    with pytest.raises(RuntimeError, match="Turn metadata integrity"):
        controller.read(start.collaboration_id)

def test_read_raises_on_pre_fix_turn_without_metadata(self, tmp_path: Path) -> None:
    """A pre-fix turn (no TurnStore entry) triggers the same integrity error.
    The rollout boundary is enforced by read() — pre-fix dialogues cannot
    continue after deployment without restarting the session."""
    session = FakeRuntimeSession()
    session.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "turn-1",
                    "status": "completed",
                    "agentMessage": '{"position":"Legacy","evidence":[],"uncertainties":[],"follow_up_branches":[]}',
                    "createdAt": "2026-03-28T00:01:00Z",
                },
            ],
        },
    }
    # Create handle but do NOT write to turn store (simulates pre-fix turn)
    controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
    start = controller.start(tmp_path)

    with pytest.raises(RuntimeError, match="Turn metadata integrity"):
        controller.read(start.collaboration_id)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestDialogueRead -v -k "real_context_size or missing_metadata"`
Expected: FAIL (current `read()` still hard-codes `context_size = 0`)

- [ ] **Step 4: Implement updated `read()`**

Replace `read()` in `server/dialogue.py`:

```python
    def read(self, collaboration_id: str) -> DialogueReadResult:
        """Read dialogue state for a given collaboration_id.

        Uses thread/read as the base set of completed turns (per delivery.md:201,218).
        Enriches per-turn context_size from the metadata store via left-join.
        A completed turn with no metadata store entry is an integrity failure.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Read failed: handle not found. "
                f"Got: collaboration_id={collaboration_id!r:.100}"
            )

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        thread = thread_data.get("thread", {})
        raw_turns = thread.get("turns", [])

        # Load all metadata for this collaboration
        metadata = self._turn_store.get_all(collaboration_id)

        turns: list[DialogueTurnSummary] = []
        seq = 0
        for raw_turn in raw_turns:
            if not isinstance(raw_turn, dict):
                continue
            if raw_turn.get("status") != "completed":
                continue
            seq += 1
            agent_message = raw_turn.get("agentMessage", "")
            position = ""
            if isinstance(agent_message, str) and agent_message:
                try:
                    parsed = json.loads(agent_message)
                    position = parsed.get("position", "")
                except (ValueError, AttributeError):
                    position = agent_message[:200]

            # Left-join: metadata store MUST have an entry for every completed turn.
            # This is unconditional — no fallback to 0. A missing entry is always
            # an integrity failure (write-ordering violation, missing recovery repair,
            # or pre-fix dialogue continued across the rollout boundary).
            context_size = metadata.get(seq)
            if context_size is None:
                raise RuntimeError(
                    f"Turn metadata integrity failure: no context_size for "
                    f"collaboration_id={collaboration_id!r:.100}, turn_sequence={seq}. "
                    f"This indicates a write-ordering violation or missing recovery "
                    f"repair. If this dialogue predates the current server version, "
                    f"end the session and start fresh."
                )

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

- [ ] **Step 5: Run the new tests**

Run: `uv run --package codex-collaboration pytest tests/test_dialogue.py::TestDialogueRead -v`
Expected: All PASSED

- [ ] **Step 6: Update existing `test_read_includes_turn_history`**

The existing test (test_dialogue.py:397-427) calls `reply()` (which now writes to the turn store) and then `read()`. It should now assert real `context_size`:

```python
def test_read_includes_turn_history(self, tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
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
    controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
    start_result = controller.start(tmp_path)
    reply_result = controller.reply(
        collaboration_id=start_result.collaboration_id,
        objective="First turn",
        explicit_paths=(Path("focus.py"),),
    )

    read_result = controller.read(start_result.collaboration_id)

    assert read_result.turn_count >= 1
    assert len(read_result.turns) >= 1
    # context_size is now real, not 0
    assert read_result.turns[0].context_size == reply_result.context_size
```

- [ ] **Step 7: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 8: Commit**

```bash
git add server/dialogue.py tests/test_dialogue.py
git commit -m "fix(codex-collaboration): read() enriches context_size from metadata store, raises on integrity failure"
```

---

## Task 7: Add startup recovery coordinator

**Files:**
- Modify: `server/dialogue.py` (add `recover_startup` method)
- Create: `tests/test_recovery_coordinator.py`

The coordinator runs once at startup. Order: (1) reconcile unresolved journal entries, (2) enumerate remaining `active` handles, (3) reattach each via `thread/read` → `thread/resume` → `update_runtime`.

Per contracts.md:141-151, this satisfies the crash recovery contract.

Session-ID stability is an external wiring contract. The coordinator documents it but does not validate it (an empty store is valid for a new session).

- [ ] **Step 1: Write failing test — startup reattaches active handles with clean journal**

Create `tests/test_recovery_coordinator.py`:

```python
"""Tests for the startup recovery coordinator."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.turn_store import TurnStore

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _recovery_stack(
    tmp_path: Path,
    *,
    session: FakeRuntimeSession | None = None,
) -> tuple[DialogueController, ControlPlane, LineageStore, OperationJournal, TurnStore, FakeRuntimeSession]:
    """Wire a stack for recovery testing. Returns all components."""
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
    turn_store = TurnStore(plugin_data, "sess-1")
    controller = DialogueController(
        control_plane=plane,
        lineage_store=store,
        journal=journal,
        session_id="sess-1",
        turn_store=turn_store,
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"collab-{i}" for i in range(100))).__next__,
    )
    return controller, plane, store, journal, turn_store, session


class TestStartupRecoveryCoordinator:
    def test_reattaches_active_handle_with_clean_journal(self, tmp_path: Path) -> None:
        """An active handle with no unresolved journal entries still needs
        reattachment after restart (new runtime, stale thread binding)."""
        session = FakeRuntimeSession()
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        # Create a dialogue normally (all journal phases complete)
        start = controller.start(tmp_path)
        assert store.get(start.collaboration_id).status == "active"
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0

        # Now simulate startup recovery
        controller.recover_startup()

        # Handle should be reattached: runtime_id updated, thread resumed
        handle = store.get(start.collaboration_id)
        assert handle is not None
        assert handle.codex_thread_id == "thr-start-resumed"

    def test_journal_reconciled_before_reattach(self, tmp_path: Path) -> None:
        """Unresolved journal entries resolved first, then remaining active handles reattached."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        # Create two dialogues
        start1 = controller.start(tmp_path)
        # Reset thread response so start2 works
        session.read_thread_response = None
        start2 = controller.start(tmp_path)

        # Make start1 have an unresolved turn_dispatch (will be marked unknown)
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="rt-1:thr-start:1",
                operation="turn_dispatch",
                phase="intent",
                collaboration_id=start1.collaboration_id,
                created_at="2026-03-28T00:01:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-start",
                turn_sequence=1,
                runtime_id="rt-1",
                context_size=4096,
            ),
            session_id="sess-1",
        )

        # Set thread/read to return no turns (unconfirmed intent)
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }

        controller.recover_startup()

        # start1: journal reconciled, intent unconfirmed → unknown (NOT reattached)
        h1 = store.get(start1.collaboration_id)
        assert h1.status == "unknown"

        # start2: clean journal, still active → reattached
        h2 = store.get(start2.collaboration_id)
        assert h2.status == "active"
        assert h2.codex_thread_id == "thr-start-resumed"

    def test_does_not_double_resume_handles_from_phase_1(self, tmp_path: Path) -> None:
        """Handles recovered by journal reconciliation (phase 1) are skipped
        during bulk reattach (phase 3) to avoid double-resume churn."""
        from server.models import OperationJournalEntry

        session = FakeRuntimeSession()
        controller, _, store, journal, _, session = _recovery_stack(tmp_path, session=session)

        # Write an unresolved thread_creation dispatched entry
        # Phase 1 will recover this → calls resume_thread → handle becomes active
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-recovered",
                operation="thread_creation",
                phase="intent",
                collaboration_id="collab-recovered",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
            ),
            session_id="sess-1",
        )
        journal.write_phase(
            OperationJournalEntry(
                idempotency_key="sess-1:collab-recovered",
                operation="thread_creation",
                phase="dispatched",
                collaboration_id="collab-recovered",
                created_at="2026-03-28T00:00:00Z",
                repo_root=str(tmp_path.resolve()),
                codex_thread_id="thr-recovered",
            ),
            session_id="sess-1",
        )

        # Track resume_thread calls to verify no double-resume
        resume_calls: list[str] = []
        original_resume = session.resume_thread

        def tracking_resume(thread_id: str) -> str:
            resume_calls.append(thread_id)
            return original_resume(thread_id)

        session.resume_thread = tracking_resume

        controller.recover_startup()

        # resume_thread called exactly once for the recovered handle,
        # NOT twice (once by phase 1 recovery + once by phase 3 reattach)
        recovered_resumes = [c for c in resume_calls if c == "thr-recovered"]
        assert len(recovered_resumes) == 1

    def test_quarantines_pre_fix_handle_with_completed_turns(self, tmp_path: Path) -> None:
        """Active handle with completed turns but no TurnStore entries is
        quarantined as unknown during startup. This enforces the rollout
        boundary — prevents reply() from creating mixed-era dialogues."""
        session = FakeRuntimeSession()
        # thread/read shows 1 completed turn (from a pre-fix reply)
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        # Create a dialogue (handle is active, journal is clean)
        start = controller.start(tmp_path)
        assert store.get(start.collaboration_id).status == "active"

        # TurnStore is empty — simulates pre-fix dialogue with completed turns
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is None

        controller.recover_startup()

        # Handle quarantined as unknown — reply() will reject it
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_quarantines_post_fix_handle_with_missing_metadata(self, tmp_path: Path) -> None:
        """A post-fix handle with some TurnStore entries but fewer than completed
        turns is also quarantined. The system cannot distinguish this from a legacy
        handle — both result in unknown status."""
        session = FakeRuntimeSession()
        # thread/read shows 2 completed turns
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                    {"id": "t2", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)

        # Write metadata for turn 1 only — simulates post-fix corruption
        # (turn 2 completed but store write was lost)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        controller.recover_startup()

        # Handle quarantined — same treatment as legacy
        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_does_not_quarantine_handle_with_no_completed_turns(self, tmp_path: Path) -> None:
        """Active handle with zero completed turns (just started, no replies yet)
        should be reattached normally, not quarantined."""
        session = FakeRuntimeSession()
        # thread/read shows no completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)

        controller.recover_startup()

        # Handle reattached — not quarantined
        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start-resumed"

    def test_no_op_when_no_handles_or_journal(self, tmp_path: Path) -> None:
        """Startup recovery is safe on a fresh session with no data."""
        controller, _, _, _, _, _ = _recovery_stack(tmp_path)
        controller.recover_startup()  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest tests/test_recovery_coordinator.py -v`
Expected: FAIL with `AttributeError: 'DialogueController' has no attribute 'recover_startup'`

- [ ] **Step 3: Implement `recover_startup` on `DialogueController`**

In `server/dialogue.py`, add after `recover_pending_operations`:

```python
    def recover_startup(self) -> None:
        """One-shot startup recovery coordinator.

        Order:
        (1) reconcile unresolved journal entries
        (2) reattach remaining active handles not already touched by phase 1

        Per contracts.md:141-151 (crash recovery contract).

        Rollout boundary: pre-fix dialogues (turns dispatched before TurnStore)
        cannot continue after deployment. The journal is session-bounded, so
        fresh sessions have no pre-fix data. Mid-session code upgrades require
        ending the session and starting fresh. The read() integrity error is the
        enforcement signal if this boundary is violated.

        Session-ID stability is an external wiring contract: the caller must
        ensure this controller receives the same session_id used before the restart.
        This method does not validate session_id — an empty store is valid for
        a new session.
        """
        # Phase 1: reconcile unresolved journal entries
        # (may mark some handles unknown, may create/resume handles from thread_creation recovery)
        # Returns collaboration_ids of handles already resumed — skip in phase 2.
        recovered_cids = set(self.recover_pending_operations())

        # Phase 2: enumerate remaining active handles and reattach.
        # Skip handles already resumed by phase 1 to avoid double-resume
        # (thread/resume may yield a new identity on each call).
        # Quarantine any handle with incomplete TurnStore metadata (completed
        # turns without store entries). Covers both legacy dialogues and post-fix
        # corruption — the system cannot distinguish them without a rollout marker.
        active_handles = self._lineage_store.list(status="active")
        for handle in active_handles:
            if handle.collaboration_id in recovered_cids:
                continue
            try:
                runtime = self._control_plane.get_advisory_runtime(
                    Path(handle.repo_root)
                )
                thread_data = runtime.session.read_thread(handle.codex_thread_id)

                # Metadata completeness check: if this handle has completed turns
                # but the TurnStore is missing entries, quarantine as unknown.
                # Catches both legacy dialogues and post-fix corruption.
                raw_turns = thread_data.get("thread", {}).get("turns", [])
                completed_count = sum(
                    1 for t in raw_turns
                    if isinstance(t, dict) and t.get("status") == "completed"
                )
                if completed_count > 0:
                    metadata = self._turn_store.get_all(handle.collaboration_id)
                    if len(metadata) < completed_count:
                        self._lineage_store.update_status(
                            handle.collaboration_id, "unknown"
                        )
                        continue

                resumed_thread_id = runtime.session.resume_thread(
                    handle.codex_thread_id
                )
                self._lineage_store.update_runtime(
                    handle.collaboration_id,
                    runtime_id=runtime.runtime_id,
                    codex_thread_id=resumed_thread_id,
                )
            except Exception:
                # Reattach failure — mark handle unknown rather than leaving stale binding
                self._lineage_store.update_status(
                    handle.collaboration_id, "unknown"
                )
```

- [ ] **Step 4: Run the coordinator tests**

Run: `uv run --package codex-collaboration pytest tests/test_recovery_coordinator.py -v`
Expected: All PASSED

- [ ] **Step 5: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 6: Commit**

```bash
git add server/dialogue.py tests/test_recovery_coordinator.py
git commit -m "feat(codex-collaboration): add startup recovery coordinator — journal reconciliation then active-handle reattach"
```

---

## Task 8: Wire startup recovery into MCP server

**Files:**
- Modify: `server/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

Add a `startup()` method to `McpServer` that calls `recover_startup()` on the dialogue controller. Call it at the top of `run()`, before entering the request loop. Guard with a one-shot flag.

- [ ] **Step 1: Write failing test — startup called before request processing**

In `tests/test_mcp_server.py`, update `FakeDialogueController` and add tests:

```python
class FakeDialogueController:
    def __init__(self) -> None:
        self.startup_called = False

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

    def recover_startup(self) -> None:
        self.startup_called = True


class TestStartup:
    def test_startup_calls_recover_startup(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.startup()
        assert controller.startup_called is True

    def test_startup_is_idempotent(self) -> None:
        controller = FakeDialogueController()
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=controller,
        )
        server.startup()
        server.startup()  # second call should be a no-op
        assert controller.startup_called is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest tests/test_mcp_server.py::TestStartup -v`
Expected: FAIL with `AttributeError: 'McpServer' object has no attribute 'startup'`

- [ ] **Step 3: Implement `startup()` on `McpServer` and call from `run()`**

In `server/mcp_server.py`, update `McpServer`:

```python
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
        self._recovery_completed = False

    def startup(self) -> None:
        """One-shot startup recovery. Idempotent — second call is a no-op."""
        if self._recovery_completed:
            return
        self._dialogue_controller.recover_startup()
        self._recovery_completed = True

    def run(self) -> None:
        """Main loop: run startup recovery, then read JSON-RPC from stdin."""
        self.startup()
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

    # ... rest unchanged
```

- [ ] **Step 4: Run new tests**

Run: `uv run --package codex-collaboration pytest tests/test_mcp_server.py::TestStartup -v`
Expected: 2 PASSED

- [ ] **Step 5: Run full suite**

Run: `uv run --package codex-collaboration pytest tests/ -q --tb=short`
Expected: All passing

- [ ] **Step 6: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(codex-collaboration): wire startup recovery into MCP server pre-loop"
```

---

## Non-Negotiable Checkpoints

After all 8 tasks, verify these tests pass — they prove the four original findings and review corrections are fixed:

| Finding | Test | What it proves |
|---------|------|---------------|
| P1: Dead recovery path | `test_reattaches_active_handle_with_clean_journal` | Startup recovery reattaches active handles even with clean journal |
| P1: Intent turn loss | `test_recover_intent_only_turn_dispatch_marks_unknown` | Intent-phase recovery marks `unknown`, not silent no-op |
| P2: Missing lifecycle guard | `test_reply_rejects_unknown_handle` + `test_read_works_on_unknown_handle` | `reply()` rejects, `read()` allows non-active handles |
| P2: Bogus context_size | `test_read_returns_real_context_size_from_store` + `test_read_raises_on_missing_metadata_for_post_fix_turn` | Real values from store, unconditional integrity failure on missing |
| Review: No double-resume | `test_does_not_double_resume_handles_from_phase_1` | Phase 1 recovered handles skipped in phase 2 |
| Review: Metadata quarantine | `test_quarantines_pre_fix_handle_with_completed_turns` + `test_quarantines_post_fix_handle_with_missing_metadata` | Startup quarantines any handle with incomplete metadata (legacy or corruption) |
| Review: Read defense-in-depth | `test_read_raises_on_pre_fix_turn_without_metadata` + `test_read_raises_on_missing_metadata_for_post_fix_turn` | `read()` catches missing metadata unconditionally |
| Review: Write ordering | `test_crash_after_store_write_before_completed_is_recoverable` | Crash between store write and journal completed is recoverable |

Run the explicit verification:

```bash
uv run --package codex-collaboration pytest tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_reattaches_active_handle_with_clean_journal tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_does_not_double_resume_handles_from_phase_1 tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_quarantines_pre_fix_handle_with_completed_turns tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_quarantines_post_fix_handle_with_missing_metadata tests/test_dialogue.py::TestRecoverPendingOperations::test_recover_intent_only_turn_dispatch_marks_unknown tests/test_dialogue.py::TestDialogueReply::test_reply_rejects_unknown_handle tests/test_dialogue.py::TestDialogueRead::test_read_works_on_unknown_handle tests/test_dialogue.py::TestDialogueRead::test_read_returns_real_context_size_from_store tests/test_dialogue.py::TestDialogueRead::test_read_raises_on_missing_metadata_for_post_fix_turn tests/test_dialogue.py::TestDialogueRead::test_read_raises_on_pre_fix_turn_without_metadata tests/test_dialogue_integration.py::TestTurnStoreWriteOrdering::test_crash_after_store_write_before_completed_is_recoverable -v
```

Expected: 11 PASSED, 0 FAILED.

---

## Dependency Graph

```
Task 1 (journal model) ─┐
                         ├─→ Task 3 (wire + write ordering) ─→ Task 4 (recovery fix) ─→ Task 7 (coordinator) ─→ Task 8 (MCP wiring)
Task 2 (turn store) ────┘         │
                                  ├─→ Task 5 (lifecycle guard) [parallel with 4]
                                  └─→ Task 6 (read update) [parallel with 4, 5]
```

Tasks 1 and 2 are independent foundations — can run in parallel.
Task 3 requires both 1 and 2.
Tasks 4, 5, 6 all require 3 and can partially parallelize.
Task 7 requires 4.
Task 8 requires 7.
