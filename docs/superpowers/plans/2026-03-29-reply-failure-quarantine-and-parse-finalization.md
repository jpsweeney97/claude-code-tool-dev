# Conservative `run_turn` Quarantine + Durable Parse-Failure Finalization

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two `reply()` failure windows so that (1) a `run_turn()` exception quarantines the handle and best-effort repairs metadata/journal/audit inline when the turn can be confirmed, and (2) a `parse_consult_response()` exception finalizes all durable state before raising a dedicated error.

**Architecture:** Two distinct error-handling branches in `reply()`, each with different semantics. The `run_turn` branch quarantines (handle → `unknown`, best-effort inspect/repair, re-raise). If the turn is confirmed, the inline repair writes TurnStore metadata, resolves the journal entry, and attempts to emit the corresponding `dialogue_turn` audit event when a usable string `turn_id` can be recovered from `thread/read`. The parse branch finalizes (TurnStore + journal + audit committed, handle stays `active`, raise `CommittedTurnParseError`). Startup recovery is extended to reattach eligible `unknown` handles under the Option C predicate: zero completed turns OR complete TurnStore metadata for all completed turns, plus successful `read_thread` + `resume_thread`. No changes to `_recover_turn_dispatch()`.

**Tech Stack:** Python 3.12, pytest, dataclasses, JSONL append-only stores.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `server/dialogue.py` | Modify | Add `CommittedTurnParseError`, add `_best_effort_repair_turn()`, rewrite `reply()` exception handling, extend `recover_startup()` phase 2 |
| `tests/test_dialogue.py` | Modify | Add 11 tests: 4 for `_best_effort_repair_turn`, 3 for `run_turn` failure, 4 for parse failure |
| `tests/test_recovery_coordinator.py` | Modify | Add 4 tests: startup reattach of `unknown` handles |
| `tests/test_mcp_server.py` | Modify | Add 1 test: MCP surfaces `CommittedTurnParseError` guidance |
| `docs/superpowers/specs/codex-collaboration/contracts.md` | Modify | Update §Crash Recovery Contract to document `active + eligible unknown` enumeration and the Option C eligibility predicate |

No new files. No changes to models, journal, lineage_store, turn_store, control_plane, prompt_builder, or `_recover_turn_dispatch()`.

**Out of scope for this patch:**
- Retrofitting `_recover_turn_dispatch()` to emit `dialogue_turn` audit events on confirmed startup recovery. That pre-existing audit asymmetry should be tracked as separate follow-up work.
- Adding `quarantine_reason` or other provenance fields to `CollaborationHandle`. This plan intentionally uses Option C instead.

---

## Key Invariants

**Turn confirmation rule** (used in `_best_effort_repair_turn` and existing `_recover_turn_dispatch`):
```python
turn_confirmed = (
    turn_sequence is not None
    and completed_count >= turn_sequence
)
```

**Write-ordering invariant** (reordered but preserved):
```
intent → run_turn → dispatched → TurnStore.write → completed → audit → parse
```

TurnStore write MUST happen between `dispatched` and `completed` journal phases. Moving parse after audit does not violate this — parse is a projection step that consumes the committed turn data.

**Audit invariant** (new in this patch): the normal `reply()` success path MUST emit `dialogue_turn`. `_best_effort_repair_turn()` should also emit the matching `dialogue_turn` audit event when it can recover a usable string `turn_id` from `thread/read`; because the helper is best-effort cleanup, malformed or missing turn identifiers are treated as audit-repair misses rather than hard failures. This plan does NOT retrofit `_recover_turn_dispatch()`; that pre-existing asymmetry remains follow-up work.

**Lifecycle guard** (existing, unchanged): `reply()` rejects handles where `status != "active"`. After quarantine, same-session retries are blocked.

**Unknown reattach eligibility** (Option C, chosen scope): startup may reattach an `unknown` handle only if it has zero completed turns OR complete TurnStore metadata for all completed turns, and only after successful `read_thread` + `resume_thread`. Future producers of `unknown` MUST be compatible with this predicate or add stronger provenance before shipping.

---

## Task 1: Add `CommittedTurnParseError` exception class

**Files:**
- Modify: `server/dialogue.py:1-31` (imports and module top-level)

This is a standalone exception class with no dependencies. Tests in later tasks verify its behavior.

- [ ] **Step 1: Add the exception class after imports**

Add at `server/dialogue.py` between the `TurnStore` import (line 30) and the `DialogueController` class (line 33):

```python
class CommittedTurnParseError(RuntimeError):
    """Turn dispatched and committed, but response parsing failed.

    The turn is durably recorded (journal completed, TurnStore written, audit
    emitted). Use ``codex.dialogue.read`` to inspect the committed turn.
    Blind retry will create a duplicate follow-up turn, not replay this one.
    """
```

- [ ] **Step 2: Verify import resolves**

Run: `cd packages/plugins/codex-collaboration && uv run python -c "from server.dialogue import CommittedTurnParseError; print(CommittedTurnParseError.__mro__)"`
Expected: prints `(<class 'server.dialogue.CommittedTurnParseError'>, <class 'RuntimeError'>, ...)`

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py
git commit -m "feat(codex-collaboration): add CommittedTurnParseError exception class"
```

---

## Task 2: Add `_best_effort_repair_turn()` helper

**Files:**
- Modify: `server/dialogue.py` (add method to `DialogueController`)
- Test: `tests/test_dialogue.py`

This is the reply-scoped inline repair helper. It attempts to inspect the thread via a fresh runtime and, if the turn is confirmed, writes TurnStore metadata, resolves the journal entry, and attempts to emit the matching `dialogue_turn` audit event when a usable string `turn_id` can be recovered from `thread/read`. It does NOT reactivate the handle.

- [ ] **Step 1: Write the failing test — repair succeeds when turn is confirmed**

Add to `tests/test_dialogue.py` in a new class after `TestDialogueRead`:

```python
class TestBestEffortRepairTurn:
    def test_repairs_metadata_and_journal_when_turn_confirmed(self, tmp_path: Path) -> None:
        """Fresh runtime confirms the turn completed. Repair writes TurnStore
        metadata and resolves the journal entry. Handle status is not changed."""
        session = FakeRuntimeSession()
        # After repair bootstraps a fresh runtime, thread/read shows 1 completed turn
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        # Simulate: handle already marked unknown by reply() exception path
        store.update_status(start.collaboration_id, "unknown")

        # Build the intent entry that reply() would have created
        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        # Write the intent to journal (simulating what reply() does before run_turn)
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        # Journal resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        assert len(unresolved) == 0
        # TurnStore repaired
        assert turn_store.get(start.collaboration_id, turn_sequence=1) == 4096
        # Handle NOT reactivated — stays unknown
        assert store.get(start.collaboration_id).status == "unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestBestEffortRepairTurn::test_repairs_metadata_and_journal_when_turn_confirmed -v`
Expected: FAIL with `AttributeError: 'DialogueController' object has no attribute '_best_effort_repair_turn'`

- [ ] **Step 3: Write the failing test — repair emits `dialogue_turn` audit when turn is confirmed**

Add to `TestBestEffortRepairTurn`:

```python
    def test_emits_dialogue_turn_audit_when_turn_confirmed(self, tmp_path: Path) -> None:
        """Confirmed inline repair must also emit the required dialogue_turn audit."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-03-29T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
        assert turn_events[0]["runtime_id"] == "rt-sess-1"
        assert turn_events[0]["turn_id"] == "turn-1"
        assert turn_events[0]["context_size"] == 4096
```

- [ ] **Step 4: Write the failing test — repair is no-op when turn unconfirmed**

Add to `TestBestEffortRepairTurn`:

```python
    def test_leaves_journal_unresolved_when_turn_not_confirmed(self, tmp_path: Path) -> None:
        """Thread/read shows zero completed turns. Repair leaves journal unresolved
        for later startup recovery. Handle status is not changed."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        # Journal stays unresolved — startup recovery will handle it
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
        # No TurnStore write
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is None
```

- [ ] **Step 5: Write the failing test — repair swallows exceptions silently**

Add to `TestBestEffortRepairTurn`:

```python
    def test_swallows_exception_when_inspection_fails(self, tmp_path: Path) -> None:
        """If get_advisory_runtime or read_thread raises, the repair silently
        gives up. Journal stays unresolved. No exception escapes."""
        session = FakeRuntimeSession(
            initialize_error=RuntimeError("codex down")
        )
        controller, plane, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        # Manually create a handle (start() would fail with initialize_error)
        from server.models import CollaborationHandle
        handle = CollaborationHandle(
            collaboration_id="collab-sess-1",
            capability_class="advisory",
            runtime_id="rt-old",
            codex_thread_id="thr-start",
            claude_session_id="sess-1",
            repo_root=str(tmp_path.resolve()),
            created_at="2026-03-29T00:00:00Z",
            status="unknown",
        )
        store.create(handle)

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-old:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id="collab-sess-1",
            created_at="2026-03-29T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-old",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        # Invalidate the runtime so get_advisory_runtime has to bootstrap fresh
        # The fresh bootstrap will hit initialize_error
        plane.invalidate_runtime(tmp_path.resolve())

        # Must not raise
        controller._best_effort_repair_turn(intent_entry)

        # Journal stays unresolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
```

- [ ] **Step 6: Run all four tests to verify they fail**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestBestEffortRepairTurn -v`
Expected: all 4 FAIL with `AttributeError: '_best_effort_repair_turn'`

- [ ] **Step 7: Implement `_best_effort_repair_turn`**

Add to `DialogueController` in `server/dialogue.py`, after `_next_turn_sequence` (after line 516) and before `read` (line 518):

```python
    def _best_effort_repair_turn(
        self, intent_entry: OperationJournalEntry
    ) -> None:
        """Best-effort inspect and repair a turn after run_turn() failure.

        Called only from reply() exception path. Does NOT reactivate the handle.
        If inspection confirms the turn completed, writes TurnStore metadata,
        resolves the journal entry, and attempts to emit the matching
        dialogue_turn audit event when a usable string turn_id can be
        recovered from thread/read. Otherwise leaves the entry unresolved
        for startup recovery.

        All exceptions are swallowed — this is best-effort cleanup.
        """
        try:
            runtime = self._control_plane.get_advisory_runtime(
                Path(intent_entry.repo_root)
            )
            thread_data = runtime.session.read_thread(intent_entry.codex_thread_id)
            raw_turns = thread_data.get("thread", {}).get("turns", [])
            completed_turns = [
                t for t in raw_turns
                if isinstance(t, dict) and t.get("status") == "completed"
            ]
            completed_count = len(completed_turns)
            turn_confirmed = (
                intent_entry.turn_sequence is not None
                and completed_count >= intent_entry.turn_sequence
            )
        except Exception:
            return

        if not turn_confirmed:
            return

        turn_id = None
        if intent_entry.turn_sequence is not None:
            turn_index = intent_entry.turn_sequence - 1
            if 0 <= turn_index < len(completed_turns):
                candidate_turn_id = completed_turns[turn_index].get("id")
                if isinstance(candidate_turn_id, str) and candidate_turn_id:
                    turn_id = candidate_turn_id

        if intent_entry.context_size is not None and intent_entry.turn_sequence is not None:
            self._turn_store.write(
                intent_entry.collaboration_id,
                turn_sequence=intent_entry.turn_sequence,
                context_size=intent_entry.context_size,
            )
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=intent_entry.idempotency_key,
                operation=intent_entry.operation,
                phase="completed",
                collaboration_id=intent_entry.collaboration_id,
                created_at=intent_entry.created_at,
                repo_root=intent_entry.repo_root,
            ),
            session_id=self._session_id,
        )
        if turn_id is not None and intent_entry.runtime_id is not None:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="dialogue_turn",
                    collaboration_id=intent_entry.collaboration_id,
                    runtime_id=intent_entry.runtime_id,
                    context_size=intent_entry.context_size,
                    turn_id=turn_id,
                )
            )
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestBestEffortRepairTurn -v`
Expected: 4 passed

- [ ] **Step 9: Run full suite to verify no regressions**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all tests pass (193 existing + 4 new = 197)

- [ ] **Step 10: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat(codex-collaboration): add _best_effort_repair_turn helper for reply-time inspection"
```

---

## Task 3: Rewrite `reply()` run_turn exception path

**Files:**
- Modify: `server/dialogue.py:194-221` (the intent write + run_turn + except block)
- Test: `tests/test_dialogue.py`

The current exception path (lines 219-221) only invalidates the runtime and re-raises. The new path also quarantines the handle and calls `_best_effort_repair_turn`.

- [ ] **Step 1: Write the failing test — quarantine and block retry**

Add to `tests/test_dialogue.py` in a new class after `TestBestEffortRepairTurn`:

```python
class TestReplyRunTurnFailure:
    def test_marks_handle_unknown_and_blocks_retry(self, tmp_path: Path) -> None:
        """run_turn raises → handle quarantined → second reply rejected."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(run_turn_error=RuntimeError("dispatch failed"))
        # After quarantine, best-effort repair sees no completed turns
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="dispatch failed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle is now unknown
        assert store.get(start.collaboration_id).status == "unknown"

        # Second reply blocked by lifecycle guard
        with pytest.raises(ValueError, match="handle not active"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should be rejected",
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyRunTurnFailure::test_marks_handle_unknown_and_blocks_retry -v`
Expected: FAIL — handle status is still `active` after the exception (current code doesn't quarantine)

- [ ] **Step 3: Write the failing test — repairs metadata when turn confirmed**

```python
    def test_repairs_metadata_when_completed_turn_is_visible(self, tmp_path: Path) -> None:
        """run_turn raises, but fresh runtime shows the turn completed.
        TurnStore repaired, journal resolved, handle stays unknown, read() works."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class FailThenSucceedSession(FakeRuntimeSession):
            """First run_turn raises, but read_thread shows the turn completed."""
            def __init__(self) -> None:
                super().__init__()
                self._run_turn_failed = False

            def run_turn(self, **kwargs: object) -> object:
                if not self._run_turn_failed:
                    self._run_turn_failed = True
                    # Simulate: Codex processed the turn but connection dropped
                    self.completed_turn_count += 1
                    raise RuntimeError("connection lost after dispatch")
                return super().run_turn(**kwargs)

        session = FailThenSucceedSession()
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="connection lost after dispatch"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle quarantined
        assert store.get(start.collaboration_id).status == "unknown"
        # But metadata repaired (turn was confirmed via thread/read)
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is not None
        # Journal resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 0

        # read() works without integrity error
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        read_result = controller.read(start.collaboration_id)
        assert read_result.turn_count == 1
```

- [ ] **Step 4: Write the failing test — preserves original exception when repair fails**

```python
    def test_preserves_original_exception_when_inspection_fails(self, tmp_path: Path) -> None:
        """run_turn raises and best-effort repair also fails.
        Original exception is re-raised, handle is unknown, journal unresolved."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class AlwaysFailSession(FakeRuntimeSession):
            """run_turn fails, and subsequent initialize (for fresh runtime) also fails."""
            _run_turn_raised = False

            def run_turn(self, **kwargs: object) -> object:
                self._run_turn_raised = True
                raise RuntimeError("original dispatch error")

            def initialize(self) -> object:
                if self._run_turn_raised:
                    # Fresh runtime bootstrap also fails
                    raise RuntimeError("codex unreachable")
                return super().initialize()

        session = AlwaysFailSession()
        controller, _, store, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(RuntimeError, match="original dispatch error"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Should fail",
                explicit_paths=(Path("focus.py"),),
            )

        # Handle quarantined
        assert store.get(start.collaboration_id).status == "unknown"
        # Journal unresolved (repair failed)
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 1
```

- [ ] **Step 5: Run all three to verify they fail**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyRunTurnFailure -v`
Expected: first test fails (handle still `active`), other two fail similarly

- [ ] **Step 6: Rewrite the `reply()` intent + run_turn + exception path**

In `server/dialogue.py`, replace lines 194-221 (from `# Phase 1: intent` through the `except Exception` block) with:

```python
        # Phase 1: intent — journal before dispatch (turn-dispatch key)
        idempotency_key = f"{runtime.runtime_id}:{handle.codex_thread_id}:{turn_sequence}"
        created_at = self._journal.timestamp()
        intent_entry = OperationJournalEntry(
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
        )
        self._journal.write_phase(intent_entry, session_id=self._session_id)

        try:
            turn_result = runtime.session.run_turn(
                thread_id=handle.codex_thread_id,
                prompt_text=build_consult_turn_text(packet.payload),
                output_schema=CONSULT_OUTPUT_SCHEMA,
            )
        except Exception:
            self._control_plane.invalidate_runtime(resolved_root)
            self._lineage_store.update_status(collaboration_id, "unknown")
            self._best_effort_repair_turn(intent_entry)
            raise
```

- [ ] **Step 7: Run the three new tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyRunTurnFailure -v`
Expected: 3 passed

- [ ] **Step 8: Run existing `test_reply_journal_intent_carries_context_size` to check compat**

This existing test uses a `CrashAfterIntent` session that raises from `run_turn`. It currently checks that the journal has an unresolved intent with `context_size`. With the new code, the `run_turn` exception path now also marks the handle `unknown` and attempts best-effort repair. The repair will see no completed turns (the crash happened before dispatch), so the journal entry stays unresolved. The test should still pass.

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueReply::test_reply_journal_intent_carries_context_size -v`
Expected: PASS

- [ ] **Step 9: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all tests pass (197 existing + 3 new = 200)

- [ ] **Step 10: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat(codex-collaboration): quarantine handle and best-effort repair on run_turn failure"
```

---

## Task 4: Reorder `reply()` success path and add parse-failure handling

**Files:**
- Modify: `server/dialogue.py:223-287` (dispatched → parse → TurnStore → completed → audit → return)
- Test: `tests/test_dialogue.py`

Reorder the success path so all durable writes (journal, TurnStore, audit) happen before the fallible `parse_consult_response()` call. Add a try/except around parse that raises `CommittedTurnParseError`.

- [ ] **Step 1: Write the failing test — parse failure raises CommittedTurnParseError**

Add to `tests/test_dialogue.py` in a new class:

```python
from server.dialogue import CommittedTurnParseError


class TestReplyParseFailure:
    def test_raises_committed_turn_parse_error_and_leaves_handle_active(
        self, tmp_path: Path
    ) -> None:
        """Malformed agent message → CommittedTurnParseError; handle stays active."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError, match="turn committed"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        assert store.get(start.collaboration_id).status == "active"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyParseFailure::test_raises_committed_turn_parse_error_and_leaves_handle_active -v`
Expected: FAIL — currently raises `ValueError` from `parse_consult_response`, not `CommittedTurnParseError`

- [ ] **Step 3: Write the failing test — journal resolved, TurnStore written, audit emitted**

```python
    def test_completes_journal_writes_store_and_emits_audit(self, tmp_path: Path) -> None:
        """Parse failure still finalizes all durable state."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, store, journal, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Journal fully resolved
        unresolved = journal.list_unresolved(session_id="sess-1")
        turn_entries = [e for e in unresolved if e.operation == "turn_dispatch"]
        assert len(turn_entries) == 0

        # TurnStore has metadata
        assert turn_store.get(start.collaboration_id, turn_sequence=1) is not None

        # Audit event emitted
        audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
        events = [json.loads(line) for line in audit_path.read_text().strip().split("\n")]
        turn_events = [e for e in events if e["action"] == "dialogue_turn"]
        assert len(turn_events) == 1
        assert turn_events[0]["collaboration_id"] == start.collaboration_id
```

- [ ] **Step 4: Write the failing test — read() works after parse failure**

```python
    def test_read_returns_fallback_position_without_integrity_error(
        self, tmp_path: Path
    ) -> None:
        """After parse failure, read() uses the raw-message fallback and does not
        raise a metadata integrity error."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        session = FakeRuntimeSession(agent_message="not valid json {{{{")
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Review focus.py",
                explicit_paths=(Path("focus.py"),),
            )

        # Configure read_thread with the committed turn's malformed message
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "turn-1",
                        "status": "completed",
                        "agentMessage": "not valid json {{{{",
                        "createdAt": "2026-03-29T00:00:00Z",
                    },
                ],
            },
        }

        # read() should NOT raise RuntimeError — it uses the raw-message fallback
        read_result = controller.read(start.collaboration_id)
        assert read_result.turn_count == 1
        # Fallback position is agent_message[:200]
        assert read_result.turns[0].position == "not valid json {{{{"
```

- [ ] **Step 5: Write the failing test — follow-up reply uses next turn_sequence**

```python
    def test_follow_up_reply_uses_next_turn_sequence(self, tmp_path: Path) -> None:
        """First reply commits but fails parsing. Second reply succeeds at turn 2."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class MalformedThenValidSession(FakeRuntimeSession):
            """First run_turn returns malformed JSON, second returns valid."""
            def __init__(self) -> None:
                super().__init__()
                self._first_call = True

            def run_turn(self, **kwargs: object) -> object:
                if self._first_call:
                    self._first_call = False
                    self.run_turn_calls += 1
                    self.completed_turn_count += 1
                    from server.models import TurnExecutionResult
                    return TurnExecutionResult(
                        turn_id="turn-1",
                        agent_message="not valid json {{{{",
                    )
                return super().run_turn(**kwargs)

        session = MalformedThenValidSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        # First reply: commits but parse fails
        with pytest.raises(CommittedTurnParseError):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path("focus.py"),),
            )

        # Second reply: should be turn_sequence=2
        reply2 = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Second turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply2.turn_sequence == 2
```

- [ ] **Step 6: Run all four parse-failure tests to verify they fail**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyParseFailure -v`
Expected: all 4 FAIL — first raises `ValueError` not `CommittedTurnParseError`, others depend on reorder

- [ ] **Step 7: Rewrite the `reply()` success path**

In `server/dialogue.py`, replace the block from `# Phase 2: dispatched` (line 223) through the `return DialogueReplyResult(...)` (line 287). The new code:

```python
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

        # Parse projection — all durable state is committed above.
        # If parsing fails, the turn is committed and readable via dialogue.read.
        try:
            position, evidence, uncertainties, follow_up_branches = (
                parse_consult_response(turn_result.agent_message)
            )
        except (ValueError, AttributeError) as exc:
            raise CommittedTurnParseError(
                f"Reply turn committed but response parsing failed: {exc}. "
                f"The turn is durably recorded. Use codex.dialogue.read to "
                f"inspect the committed turn. Blind retry will create a "
                f"duplicate follow-up turn, not replay this one."
            ) from exc

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

- [ ] **Step 8: Run parse-failure tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestReplyParseFailure -v`
Expected: 4 passed

- [ ] **Step 9: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all tests pass (200 existing + 4 new = 204)

- [ ] **Step 10: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat(codex-collaboration): reorder reply success path and add CommittedTurnParseError handling"
```

---

## Task 5: Extend `recover_startup()` to reattach eligible `unknown` handles

**Files:**
- Modify: `server/dialogue.py:289-350` (`recover_startup()`)
- Test: `tests/test_recovery_coordinator.py`

Currently phase 2 only lists `active` handles. Extend it to also list `unknown` handles and apply the same reattachment logic: metadata completeness check, then read_thread + resume_thread.

This plan intentionally uses **Option C** for `unknown` eligibility. Reattach eligibility is defined by the metadata-completeness predicate and successful reattach, not by a new provenance field. Future producers of `unknown` MUST be compatible with this predicate or introduce stronger provenance before shipping.

- [ ] **Step 1: Write the failing test — unknown handle with no turns is reattached**

Add to `tests/test_recovery_coordinator.py` in `TestStartupRecoveryCoordinator`:

```python
    def test_reattaches_unknown_handle_with_no_completed_turns(self, tmp_path: Path) -> None:
        """Unknown handle with zero completed turns: eligible for reattach.
        No metadata completeness check needed."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, _, session = _recovery_stack(tmp_path, session=session)

        start = controller.start(tmp_path)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start-resumed"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_reattaches_unknown_handle_with_no_completed_turns -v`
Expected: FAIL — handle stays `unknown` (phase 2 only lists `active`)

- [ ] **Step 3: Write the failing test — unknown handle with complete metadata is reattached**

```python
    def test_reattaches_unknown_handle_with_complete_metadata(self, tmp_path: Path) -> None:
        """Unknown handle with completed turns and complete TurnStore metadata:
        eligible for reattach, restored to active."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, _, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        # Write complete metadata, then mark unknown
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "active"
        assert handle.codex_thread_id == "thr-start-resumed"
```

- [ ] **Step 4: Write the failing test — unknown handle with incomplete metadata stays unknown**

```python
    def test_keeps_unknown_handle_unknown_when_metadata_incomplete(self, tmp_path: Path) -> None:
        """Unknown handle with completed turns but missing TurnStore entries:
        not eligible for reattach, stays unknown."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "t1", "status": "completed", "agentMessage": "", "createdAt": ""},
                    {"id": "t2", "status": "completed", "agentMessage": "", "createdAt": ""},
                ],
            },
        }
        controller, _, store, _, turn_store, session = _recovery_stack(
            tmp_path, session=session
        )

        start = controller.start(tmp_path)
        # Only 1 of 2 metadata entries — incomplete
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        store.update_status(start.collaboration_id, "unknown")

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"
```

- [ ] **Step 5: Write the failing test — unknown handle stays unknown when reattach fails**

```python
    def test_keeps_unknown_handle_unknown_when_reattach_fails(self, tmp_path: Path) -> None:
        """Unknown handle where read_thread or resume_thread raises:
        stays unknown. Exception does not propagate."""
        session = FakeRuntimeSession(
            initialize_error=RuntimeError("codex unreachable")
        )
        controller, _, store, _, _, session = _recovery_stack(tmp_path, session=session)

        # Manually create an unknown handle (can't use start() with initialize_error)
        from server.models import CollaborationHandle
        handle = CollaborationHandle(
            collaboration_id="collab-0",
            capability_class="advisory",
            runtime_id="rt-old",
            codex_thread_id="thr-start",
            claude_session_id="sess-1",
            repo_root=str(tmp_path.resolve()),
            created_at="2026-03-29T00:00:00Z",
            status="unknown",
        )
        store.create(handle)

        # Should not raise
        controller.recover_startup()

        assert store.get("collab-0").status == "unknown"
```

- [ ] **Step 6: Run all four new startup tests to verify they fail**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_reattaches_unknown_handle_with_no_completed_turns tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_reattaches_unknown_handle_with_complete_metadata tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_keeps_unknown_handle_unknown_when_metadata_incomplete tests/test_recovery_coordinator.py::TestStartupRecoveryCoordinator::test_keeps_unknown_handle_unknown_when_reattach_fails -v`
Expected: first two FAIL (unknown not listed), last two may pass (exception path already quarantines, metadata check may not apply). Verify actual failures.

- [ ] **Step 7: Extend `recover_startup()` phase 2**

In `server/dialogue.py`, replace lines 312-350 (from `# Phase 2:` to end of `recover_startup`) with:

```python
        # Phase 2: enumerate active and unknown handles for reattach.
        # Skip handles already resumed by phase 1 to avoid double-resume.
        # Quarantine any handle with incomplete TurnStore metadata.
        # Unknown handles are eligible for reattach if metadata is complete
        # (or if they have no completed turns to check).
        active_handles = self._lineage_store.list(status="active")
        unknown_handles = self._lineage_store.list(status="unknown")
        for handle in active_handles + unknown_handles:
            if handle.collaboration_id in recovered_cids:
                continue
            try:
                runtime = self._control_plane.get_advisory_runtime(
                    Path(handle.repo_root)
                )
                thread_data = runtime.session.read_thread(handle.codex_thread_id)

                # Metadata completeness check
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
                if handle.status == "unknown":
                    self._lineage_store.update_status(
                        handle.collaboration_id, "active"
                    )
            except Exception:
                self._lineage_store.update_status(
                    handle.collaboration_id, "unknown"
                )
```

- [ ] **Step 8: Update the `recover_startup()` docstring**

Replace the existing docstring (lines 290-308) with:

```python
        """One-shot startup recovery coordinator.

        Order:
        (1) reconcile unresolved journal entries
        (2) reattach remaining active AND eligible unknown handles

        Per contracts.md:141-151 (crash recovery contract).

        Unknown handles are eligible for reattach if:
        - they have no completed turns (vacuous metadata check), OR
        - all completed turns have corresponding TurnStore metadata

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
```

- [ ] **Step 9: Update `contracts.md` §Crash Recovery Contract**

Modify `docs/superpowers/specs/codex-collaboration/contracts.md:141-151` so it matches the new startup behavior.

Replace:

```markdown
2. The control plane reads all handles with `status: active` from the lineage store for the current session and repo root.
3. For each active handle, the control plane uses Codex `thread/read` on the handle's `codex_thread_id` to recover the latest completed state, then `thread/resume` to reattach the thread in the replacement runtime.
4. The control plane calls `update_runtime` on each recovered handle to point to the new runtime instance. If `thread/resume` yields a new thread identity, the handle's `codex_thread_id` must also be updated.
5. Pending server requests associated with crashed handles are marked canceled.
6. Claude may continue from the last completed turn. Forking from the interrupted snapshot requires `codex.dialogue.fork` to be in scope.
```

With:

```markdown
2. The control plane reads all handles with `status: active` and all eligible handles with `status: unknown` from the lineage store for the current session and repo root.
3. Eligibility for an `unknown` handle is:
   - zero completed turns, OR
   - complete TurnStore metadata for every completed turn,
   and in either case successful `thread/read` followed by `thread/resume`.
4. For each enumerated handle, the control plane uses Codex `thread/read` on the handle's `codex_thread_id` to recover the latest completed state, then `thread/resume` to reattach the thread in the replacement runtime.
5. The control plane calls `update_runtime` on each recovered handle to point to the new runtime instance. If `thread/resume` yields a new thread identity, the handle's `codex_thread_id` must also be updated.
6. Pending server requests associated with crashed handles are marked canceled.
7. Claude may continue from the last completed turn. Forking from the interrupted snapshot requires `codex.dialogue.fork` to be in scope.
```

Add one sentence immediately after the numbered list:

```markdown
Future producers of `status: unknown` must either be compatible with this eligibility predicate or introduce stronger provenance before they can participate in startup reattach.
```

- [ ] **Step 10: Run all new startup tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_recovery_coordinator.py -v`
Expected: all tests pass (7 existing + 4 new = 11)

- [ ] **Step 11: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all tests pass (204 existing + 4 new = 208)

- [ ] **Step 12: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py docs/superpowers/specs/codex-collaboration/contracts.md
git commit -m "feat(codex-collaboration): extend startup recovery to reattach eligible unknown handles"
```

---

## Task 6: Add MCP-level test for `CommittedTurnParseError` guidance

**Files:**
- Modify: `tests/test_mcp_server.py`

Verify that when the dialogue controller raises `CommittedTurnParseError`, the MCP error text contains the guidance message.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_mcp_server.py`. First, update `FakeDialogueController.reply` to support raising:

```python
from server.dialogue import CommittedTurnParseError


class FakeDialogueControllerWithParseError:
    """Dialogue controller that raises CommittedTurnParseError on reply."""
    def __init__(self) -> None:
        self.startup_called = False

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(self, repo_root: Path) -> object:
        from server.models import DialogueStartResult
        return DialogueStartResult(
            collaboration_id="c1",
            runtime_id="r1",
            status="active",
            created_at="2026-03-28T00:00:00Z",
        )

    def reply(self, **kwargs: object) -> object:
        raise CommittedTurnParseError(
            "Reply turn committed but response parsing failed: bad json. "
            "The turn is durably recorded. Use codex.dialogue.read to "
            "inspect the committed turn. Blind retry will create a "
            "duplicate follow-up turn, not replay this one."
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
```

Then add the test class:

```python
class TestCommittedTurnParseErrorSurfacing:
    def test_mcp_surfaces_committed_turn_parse_guidance(self) -> None:
        """MCP error text contains both 'turn committed' and 'codex.dialogue.read'."""
        server = McpServer(
            control_plane=FakeControlPlane(),
            dialogue_controller=FakeDialogueControllerWithParseError(),
        )
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.dialogue.reply",
                "arguments": {
                    "collaboration_id": "c1",
                    "objective": "test",
                },
            },
        })

        assert response["result"]["isError"] is True
        error_text = response["result"]["content"][0]["text"]
        assert "turn committed" in error_text.lower()
        assert "codex.dialogue.read" in error_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py::TestCommittedTurnParseErrorSurfacing -v`
Expected: FAIL — `CommittedTurnParseError` does not exist yet in the test module's import (it was added in Task 1, so this should actually pass if Tasks 1-4 are done). If import fails, verify Task 1 is committed.

- [ ] **Step 3: Run to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_mcp_server.py::TestCommittedTurnParseErrorSurfacing -v`
Expected: PASS (the MCP `_handle_tools_call` catches all exceptions and puts `str(exc)` in the error text)

- [ ] **Step 4: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all tests pass (208 existing + 1 new = 209)

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_mcp_server.py
git commit -m "test(codex-collaboration): verify MCP surfaces CommittedTurnParseError guidance"
```

---

## Task 7: Update `reply()` docstring

**Files:**
- Modify: `server/dialogue.py:150-157` (the `reply()` docstring)

The docstring currently describes only the write-ordering invariant. Update it to document the two failure branches.

- [ ] **Step 1: Replace the docstring**

Replace lines 150-157 of `server/dialogue.py` with:

```python
        """Continue a dialogue turn on an existing handle.

        Spec: contracts.md §Dialogue Reply, delivery.md §R2 in-scope.
        Context assembly reuse: same pipeline as consultation.

        Write ordering invariant: metadata store write MUST happen before
        journal completed. See plan doc §Key invariants.

        Failure semantics:
        - run_turn() raises: handle quarantined to 'unknown', best-effort
          metadata/journal/audit repair via _best_effort_repair_turn(),
          original exception re-raised. Handle is NOT reactivated inline;
          startup recovery handles eligible unknown handles.
        - parse_consult_response() raises: all durable state (TurnStore,
          journal, audit) is committed before parsing. Raises
          CommittedTurnParseError. Handle stays 'active'.
        """
```

- [ ] **Step 2: Run full suite to verify no regressions**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: all 209 tests pass

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py
git commit -m "docs(codex-collaboration): document reply() failure semantics in docstring"
```

---

## Non-Negotiable Checkpoint Gate

After all 7 tasks, run these exact commands to verify the patch:

```bash
cd packages/plugins/codex-collaboration

# 1. All tests pass
uv run pytest -v

# 2. New tests exist and pass (16 total)
uv run pytest -v -k "TestBestEffortRepairTurn or TestReplyRunTurnFailure or TestReplyParseFailure or test_reattaches_unknown_handle or test_keeps_unknown_handle_unknown_when_metadata_incomplete or test_keeps_unknown_handle_unknown_when_reattach_fails or TestCommittedTurnParseErrorSurfacing"

# 3. Existing recovery tests still pass
uv run pytest tests/test_recovery_coordinator.py -v
uv run pytest tests/test_dialogue.py::TestRecoverPendingOperations -v

# 4. Existing lifecycle guard tests still pass
uv run pytest tests/test_dialogue.py -k "rejects_completed or rejects_unknown or rejects_crashed" -v
```

**Expected:** 209 total tests, 16 new, 0 failures.
