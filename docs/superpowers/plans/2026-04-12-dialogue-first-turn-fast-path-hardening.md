# Dialogue First-Turn Fast Path Hardening Implementation Plan

> **For agentic workers:** Recommended: use superpowers:subagent-driven-development or superpowers:executing-plans for task isolation. Inline execution is also viable. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden `_next_turn_sequence()` to distinguish "genuinely empty TurnStore" from "metadata unreadable or structurally suspect," and bring `_next_turn_sequence()` and `recover_startup()` to the same prefix-completeness standard enforced by `read()`.

**Architecture:** Add `TurnStore.get_all_checked()` for single-pass metadata+diagnostics retrieval. Add `_local_metadata_complete_for_completed_turns()` helper for shared prefix-completeness validation. Rewrite `_next_turn_sequence()` with three-phase trust policy (fast path → remote read → consistency check). Restructure `recover_startup()` to use the same helper unconditionally.

**Tech Stack:** Python 3.14, pytest, codex-collaboration plugin internals

**Branch:** `fix/t02-dialogue-first-turn-hardening` (already created from `main`)

**Spec:** `docs/superpowers/specs/2026-04-12-dialogue-first-turn-fast-path-hardening-design.md`

**Ticket:** T-20260410-02

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `packages/plugins/codex-collaboration/server/turn_store.py` | Modify | Add `get_all_checked()` method (~12 lines) |
| `packages/plugins/codex-collaboration/server/dialogue.py` | Modify | Add `_local_metadata_complete_for_completed_turns()` (~10 lines), rewrite `_next_turn_sequence()` (~40 lines), restructure `recover_startup()` metadata check (~5 lines) |
| `packages/plugins/codex-collaboration/tests/test_turn_store.py` | Modify | Add 3 tests for `get_all_checked()` |
| `packages/plugins/codex-collaboration/tests/test_dialogue.py` | Modify | Add 12 tests for hardened `_next_turn_sequence()` and `recover_startup()` |

No new files. All changes are modifications to existing files.

**Branch base:** `d5aa4038` (commit where `fix/t02-dialogue-first-turn-hardening` was created from `main`)

---

### Task 0: Commit spec, contract, and plan docs

**Prerequisite — must complete before any implementation task.**

**Files:**
- Stage: `docs/superpowers/specs/2026-04-12-dialogue-first-turn-fast-path-hardening-design.md`
- Stage: `docs/superpowers/specs/codex-collaboration/contracts.md`
- Stage: `docs/superpowers/plans/2026-04-12-dialogue-first-turn-fast-path-hardening.md`

- [ ] **Step 1: Commit the revised spec, contract, and plan**

```bash
git add docs/superpowers/specs/2026-04-12-dialogue-first-turn-fast-path-hardening-design.md \
       docs/superpowers/specs/codex-collaboration/contracts.md \
       docs/superpowers/plans/2026-04-12-dialogue-first-turn-fast-path-hardening.md
git commit -m "docs(spec): revise fast-path hardening design — prefix-completeness, contract update

Spec: relax invariant to prefix-completeness, label zero-turn check as
deliberate tightening, remove path-mismatch overclaim, add preconditions.
Contract: rewrite eligibility as explicit if/else on completed_count.
Plan: 7-task implementation plan with complete code (Task 0 docs + Tasks 1-6).

Ref: T-20260410-02"
```

- [ ] **Step 2: Verify the commit is on the feature branch**

Run: `git log --oneline d5aa4038..HEAD`

Expected: 1 commit (the docs commit just created)

---

### Task 1: `TurnStore.get_all_checked()` — test and implement

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_turn_store.py`
- Modify: `packages/plugins/codex-collaboration/server/turn_store.py:72` (after `get_all`)

- [ ] **Step 1: Write the three `get_all_checked()` tests**

Add a new test class at the end of `tests/test_turn_store.py`:

```python
class TestGetAllChecked:
    def test_clean_store_returns_metadata_and_empty_diagnostics(
        self, tmp_path: Path
    ) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store.write("collab-1", turn_sequence=2, context_size=8192)
        metadata, diagnostics = store.get_all_checked("collab-1")
        assert metadata == {1: 4096, 2: 8192}
        assert diagnostics.diagnostics == ()

    def test_corrupt_jsonl_returns_partial_results_and_diagnostics(
        self, tmp_path: Path
    ) -> None:
        store = TurnStore(tmp_path, "sess-1")
        store.write("collab-1", turn_sequence=1, context_size=4096)
        store_path = tmp_path / "turns" / "sess-1" / "turn_metadata.jsonl"
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")
        store.write("collab-1", turn_sequence=2, context_size=8192)
        metadata, diagnostics = store.get_all_checked("collab-1")
        assert metadata == {1: 4096, 2: 8192}
        assert len(diagnostics.diagnostics) == 1
        assert diagnostics.diagnostics[0].label == "mid_file_corruption"

    def test_empty_store_returns_empty_metadata_and_empty_diagnostics(
        self, tmp_path: Path
    ) -> None:
        store = TurnStore(tmp_path, "sess-1")
        metadata, diagnostics = store.get_all_checked("collab-1")
        assert metadata == {}
        assert diagnostics.diagnostics == ()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_turn_store.py::TestGetAllChecked -v`

Expected: FAIL — `AttributeError: 'TurnStore' object has no attribute 'get_all_checked'`

- [ ] **Step 3: Implement `get_all_checked()`**

Add this method to `TurnStore` in `server/turn_store.py`, between `get_all()` (line 71) and `check_health()` (line 73):

```python
    def get_all_checked(
        self, collaboration_id: str
    ) -> tuple[dict[int, int], ReplayDiagnostics]:
        """Return {turn_sequence: context_size} and replay diagnostics in one pass.

        Diagnostics are file-global (session-wide JSONL), not collaboration-scoped.
        A corrupt line from an unrelated collaboration appears in the diagnostics.
        Callers should treat any diagnostic as reason to distrust an otherwise-empty
        result for this collaboration. See the design spec for the blast-radius
        rationale.
        """
        all_turns, diagnostics = replay_jsonl(self._store_path, _turn_callback)
        prefix = f"{collaboration_id}:"
        filtered = {
            int(key.split(":", 1)[1]): value
            for key, value in dict(all_turns).items()
            if key.startswith(prefix)
        }
        return filtered, diagnostics
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_turn_store.py::TestGetAllChecked -v`

Expected: 3 passed

- [ ] **Step 5: Run full turn_store test suite to check for regressions**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_turn_store.py -v`

Expected: All tests pass (existing + 3 new)

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/turn_store.py packages/plugins/codex-collaboration/tests/test_turn_store.py
git commit -m "feat(turn-store): add get_all_checked() for single-pass metadata+diagnostics

Additive API — existing get_all(), get(), and check_health() unchanged.
Returns (filtered_metadata, ReplayDiagnostics) in one replay pass.

File-global diagnostics contract documented in docstring: corruption
from any collaboration in the session-wide JSONL appears in the
diagnostics. Callers treat any diagnostic as reason to distrust
an otherwise-empty result.

Ref: T-20260410-02"
```

---

### Task 2: `_local_metadata_complete_for_completed_turns()` — helper function

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/dialogue.py:68` (after `_log_recovery_failure`)

This is a pure function with no dependencies beyond its arguments. It does not need its own test file — it will be exercised through the `_next_turn_sequence()` and `recover_startup()` behavioral tests in Tasks 3-5.

- [ ] **Step 1: Add the helper function**

Add after `_log_recovery_failure()` (line 67) in `server/dialogue.py`:

```python
def _local_metadata_complete_for_completed_turns(
    local_turns: dict[int, int], completed_count: int
) -> bool:
    """True iff local metadata covers every completed remote turn.

    Checks that keys {1, 2, ..., completed_count} are all present.
    Extra local keys beyond completed_count are not rejected — they are
    anomalous but do not affect turn-sequence derivation. This matches
    the prefix-completeness rule enforced by read() (dialogue.py:853)
    and the crash-recovery contract (contracts.md:156-158).

    For completed_count == 0: returns True only if local_turns is empty.
    This is a deliberate tightening beyond read()'s enforcement — stale
    local metadata with zero completed remote turns is anomalous state.
    """
    if completed_count == 0:
        return not local_turns
    return set(range(1, completed_count + 1)).issubset(local_turns.keys())
```

- [ ] **Step 2: Run existing tests to verify no regressions**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py -x -q`

Expected: All existing tests pass (adding the function doesn't change behavior yet)

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py
git commit -m "feat(dialogue): add _local_metadata_complete_for_completed_turns helper

Pure function encoding prefix-completeness: keys {1..completed_count}
must all be present. Extra keys tolerated. Zero-turn case rejects stale
local metadata (deliberate tightening beyond read() — see spec §2).

Ref: T-20260410-02"
```

---

### Task 3: Rewrite `_next_turn_sequence()` — three-phase trust policy

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/dialogue.py:725-753`

- [ ] **Step 1: Rewrite `_next_turn_sequence()`**

Replace the current method body at `dialogue.py:725-753` (line numbers will have shifted after Task 2 — find the method by name). The method signature stays the same. Replace from the docstring through `return completed_count + 1`:

```python
    def _next_turn_sequence(
        self,
        handle: CollaborationHandle,
        runtime: object,
    ) -> int:
        """Derive next 1-based turn_sequence from completed turn count.

        dialogue.start does not consume a slot (contracts.md:266).

        Three-phase trust policy:
        1. Fast path: empty TurnStore + no replay diagnostics → return 1
        2. Remote read: all other states require read_thread()
        3. Consistency: validate local metadata against remote completed count
        """
        collaboration_id = handle.collaboration_id
        local_turns, diagnostics = self._turn_store.get_all_checked(collaboration_id)

        # Phase 1: local-only fast path
        if not local_turns and not diagnostics.diagnostics:
            return 1

        # Phase 2: remote read (all non-fast-path states)
        try:
            thread_data = runtime.session.read_thread(handle.codex_thread_id)
        except Exception as exc:
            if not local_turns:
                diag_labels = ", ".join(
                    sorted({d.label for d in diagnostics.diagnostics})
                )
                raise RuntimeError(
                    f"Turn sequence derivation failed: session turn metadata "
                    f"file has replay diagnostics "
                    f"(diagnostics={diag_labels}), and remote thread read "
                    f"failed. Got: collaboration_id={collaboration_id!r:.100}"
                ) from exc
            raise RuntimeError(
                f"Turn sequence derivation failed: cannot validate local "
                f"turn metadata (sequences={sorted(local_turns.keys())}) "
                f"against remote, remote thread read failed. "
                f"Got: collaboration_id={collaboration_id!r:.100}"
            ) from exc

        raw_turns = thread_data.get("thread", {}).get("turns", [])
        completed_count = sum(
            1
            for t in raw_turns
            if isinstance(t, dict) and t.get("status") == "completed"
        )

        # Phase 3: remote/local consistency
        if not _local_metadata_complete_for_completed_turns(
            local_turns, completed_count
        ):
            self._lineage_store.update_status(collaboration_id, "unknown")
            raise RuntimeError(
                f"Turn sequence derivation failed: local turn metadata "
                f"incomplete for completed remote turns. "
                f"Required sequences "
                f"{list(range(1, completed_count + 1))}, "
                f"present {sorted(local_turns.keys())}. "
                f"Got: collaboration_id={collaboration_id!r:.100}, "
                f"completed_count={completed_count}, "
                f"actual_sequences={sorted(local_turns.keys())}"
            )

        if len(local_turns) > completed_count:
            print(
                f"codex-collaboration: _next_turn_sequence anomaly: extra "
                f"local turn metadata beyond completed count. "
                f"collaboration_id={collaboration_id!r:.100}, "
                f"completed_count={completed_count}, "
                f"local_sequences={sorted(local_turns.keys())}",
                file=sys.stderr,
            )

        return completed_count + 1
```

- [ ] **Step 2: Run existing fast-path tests to verify they still pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestFirstTurnFastPath -v`

Expected: 2 passed — the existing happy-path and second-reply tests must not regress

- [ ] **Step 3: Run full dialogue test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py -x -q`

Expected: All existing tests pass

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py
git commit -m "feat(dialogue): rewrite _next_turn_sequence with three-phase trust policy

Phase 1: empty TurnStore + no diagnostics → fast path return 1
Phase 2: all other states require read_thread()
Phase 3: validate local metadata prefix-completeness against remote

Raises RuntimeError on remote read failure (with causal chain) and on
local/remote inconsistency (quarantines handle as 'unknown' first).
Emits stderr diagnostic for anomalous-but-prefix-complete extra keys.

Ref: T-20260410-02"
```

---

### Task 4: `_next_turn_sequence()` hardening tests

**Files:**
- Modify: `packages/plugins/codex-collaboration/tests/test_dialogue.py`

All new tests go inside the existing `TestFirstTurnFastPath` class (after line 1909).

- [ ] **Step 1: Write the corruption + remote success tests**

Add these tests after `test_second_reply_uses_read_thread` inside `TestFirstTurnFastPath`:

```python
    def test_empty_plus_diagnostics_remote_zero_completed(
        self, tmp_path: Path
    ) -> None:
        """Corrupt JSONL + remote confirms 0 completed → turn_sequence=1."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return {"thread": {"id": thread_id, "turns": []}}

        session = TrackingSession()
        controller, _, _, _, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Corrupt the JSONL to produce diagnostics without valid records
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 1
        assert session.read_thread_calls == 1, (
            "Diagnostics should force remote validation even with empty local metadata"
        )

    def test_empty_plus_diagnostics_remote_two_completed(
        self, tmp_path: Path
    ) -> None:
        """Corrupt JSONL + remote says 2 completed → integrity error, handle unknown."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        with pytest.raises(RuntimeError, match="incomplete for completed remote"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_empty_plus_diagnostics_remote_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Corrupt JSONL + read_thread raises → error mentions diagnostics."""
        session = FakeRuntimeSession()
        controller, _, _, _, _ = _build_dialogue_stack(tmp_path, session=session)
        start = controller.start(tmp_path)

        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write("not valid json\n")

        monkeypatch.setattr(
            session, "read_thread", lambda _tid: (_ for _ in ()).throw(RuntimeError("remote boom"))
        )

        with pytest.raises(RuntimeError, match="session turn metadata file has replay diagnostics") as exc_info:
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert exc_info.value.__cause__ is not None
```

- [ ] **Step 2: Run the new tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestFirstTurnFastPath::test_empty_plus_diagnostics_remote_zero_completed tests/test_dialogue.py::TestFirstTurnFastPath::test_empty_plus_diagnostics_remote_two_completed tests/test_dialogue.py::TestFirstTurnFastPath::test_empty_plus_diagnostics_remote_fails -v`

Expected: 3 passed

- [ ] **Step 3: Write the gap, partial-tail, and non-empty remote-fail tests**

Add these tests inside `TestFirstTurnFastPath`:

```python
    def test_gap_metadata_integrity_error(self, tmp_path: Path) -> None:
        """Gap {2} with remote 2 completed → integrity error."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=4096)

        with pytest.raises(RuntimeError, match="Required.*\\[1, 2\\].*present.*\\[2\\]"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_partial_tail_integrity_error(self, tmp_path: Path) -> None:
        """Partial tail {1} with remote 2 completed → integrity error."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        with pytest.raises(RuntimeError, match="Required.*\\[1, 2\\].*present.*\\[1\\]"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_nonempty_local_remote_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-empty local + read_thread raises → error mentions sequences."""
        session = FakeRuntimeSession()
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)

        monkeypatch.setattr(
            session, "read_thread", lambda _tid: (_ for _ in ()).throw(RuntimeError("remote boom"))
        )

        with pytest.raises(RuntimeError, match="cannot validate local turn metadata.*sequences=\\[1\\]") as exc_info:
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="Next turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert exc_info.value.__cause__ is not None
```

- [ ] **Step 4: Run the new tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestFirstTurnFastPath::test_gap_metadata_integrity_error tests/test_dialogue.py::TestFirstTurnFastPath::test_partial_tail_integrity_error tests/test_dialogue.py::TestFirstTurnFastPath::test_nonempty_local_remote_fails -v`

Expected: 3 passed

- [ ] **Step 5: Write the extra-local and file-global blast radius tests**

Add these tests inside `TestFirstTurnFastPath`:

```python
    def test_extra_local_keys_prefix_complete(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Extra local {1,2,3} with remote 2 completed → succeeds, warns on stderr."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=8192)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="Next turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 3
        stderr = capsys.readouterr().err
        assert "extra local turn metadata beyond completed count" in stderr

    def test_zero_turn_stale_metadata_integrity_error(
        self, tmp_path: Path
    ) -> None:
        """Stale local {1} + remote 0 completed → integrity error (zero-turn tightening).

        Proves the reply path applies the same zero-turn stale metadata
        rejection as recover_startup(). Without this, a buggy implementation
        could allow stale metadata through on the reply path while correctly
        rejecting it on recovery.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=500)

        with pytest.raises(RuntimeError, match="incomplete for completed remote"):
            controller.reply(
                collaboration_id=start.collaboration_id,
                objective="First turn",
                explicit_paths=(Path(tmp_path / "focus.py"),),
            )
        assert store.get(start.collaboration_id).status == "unknown"

    def test_unrelated_collaboration_corruption_disables_fast_path(
        self, tmp_path: Path
    ) -> None:
        """Corrupt JSONL from collab-B disables fast path for collab-A (file-global)."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")

        class TrackingSession(FakeRuntimeSession):
            def __init__(self) -> None:
                super().__init__()
                self.read_thread_calls: int = 0

            def read_thread(self, thread_id: str) -> dict:
                self.read_thread_calls += 1
                return {"thread": {"id": thread_id, "turns": []}}

        session = TrackingSession()
        controller, _, _, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Write valid metadata for a DIFFERENT collaboration, then corrupt
        turn_store.write("other-collab", turn_sequence=1, context_size=1000)
        store_path = (
            tmp_path / "plugin-data" / "turns" / "sess-1" / "turn_metadata.jsonl"
        )
        with store_path.open("a", encoding="utf-8") as f:
            f.write("corrupted line from other collab\n")

        reply = controller.reply(
            collaboration_id=start.collaboration_id,
            objective="First turn",
            explicit_paths=(Path("focus.py"),),
        )
        assert reply.turn_sequence == 1
        assert session.read_thread_calls == 1, (
            "File-global diagnostics should force remote validation "
            "even though this collaboration has no corrupt records"
        )
```

- [ ] **Step 6: Run the new tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestFirstTurnFastPath::test_zero_turn_stale_metadata_integrity_error tests/test_dialogue.py::TestFirstTurnFastPath::test_extra_local_keys_prefix_complete tests/test_dialogue.py::TestFirstTurnFastPath::test_unrelated_collaboration_corruption_disables_fast_path -v`

Expected: 3 passed

- [ ] **Step 7: Run the full `TestFirstTurnFastPath` class**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestFirstTurnFastPath -v`

Expected: 11 passed (2 existing + 9 new)

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "test(dialogue): add _next_turn_sequence hardening tests

9 new tests in TestFirstTurnFastPath:
- Empty + diagnostics + remote 0/2/fail (3 tests)
- Gap, partial tail, non-empty remote fail (3 tests)
- Zero-turn stale metadata integrity error (1 test)
- Extra local keys prefix-complete with stderr warning (1 test)
- File-global blast radius: unrelated collab corruption (1 test)

Ref: T-20260410-02"
```

---

### Task 5: Restructure `recover_startup()` + recovery tests

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/dialogue.py:533-539`
- Test: `packages/plugins/codex-collaboration/tests/test_dialogue.py`

- [ ] **Step 1: Write the three recovery tests**

Add a new test class after `TestFirstTurnFastPath` in `tests/test_dialogue.py`:

```python
class TestRecoverStartupMetadataCompleteness:
    """recover_startup() must quarantine handles with incomplete local metadata
    and allow reattach for prefix-complete metadata (including extra keys)."""

    def test_gapped_metadata_quarantines_handle(self, tmp_path: Path) -> None:
        """Handle with {1, 3} metadata vs remote 2 completed → quarantine.

        Cardinality-matching gap: len(metadata) == completed_count == 2,
        so the old ``len(metadata) < completed_count`` check passes.
        Only the prefix-completeness check catches the gap (key 2 missing).
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Pre-populate gapped metadata: keys {1, 3}, missing key 2
        # len == 2 == completed_count, so old cardinality check misses this
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_zero_turn_stale_metadata_quarantines_handle(
        self, tmp_path: Path
    ) -> None:
        """Handle with stale local metadata + remote 0 completed → quarantine."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Pre-populate stale metadata for a turn the remote never completed
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=500)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status == "unknown"

    def test_extra_local_keys_allows_reattach(self, tmp_path: Path) -> None:
        """Handle with {1, 2, 3} metadata vs remote 2 completed → reattach allowed.

        Proves recover_startup() applies prefix-completeness, not exact-key
        equality. Extra local keys beyond completed_count are tolerated.
        Without this, a buggy implementation could reject extra keys in
        recovery while accepting them in reply.
        """
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {"id": "turn-1", "status": "completed"},
                    {"id": "turn-2", "status": "completed"},
                ],
            },
        }
        controller, _, store, _, turn_store = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)
        turn_store.write(start.collaboration_id, turn_sequence=1, context_size=4096)
        turn_store.write(start.collaboration_id, turn_sequence=2, context_size=8192)
        turn_store.write(start.collaboration_id, turn_sequence=3, context_size=2048)

        controller.recover_startup()

        handle = store.get(start.collaboration_id)
        assert handle.status != "unknown", (
            "Extra local keys beyond completed_count should not quarantine — "
            "prefix {1, 2} is complete for completed_count=2"
        )
```

- [ ] **Step 2: Run tests to verify failures on old code**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoverStartupMetadataCompleteness -v`

Expected: 2 FAIL (gapped-metadata and zero-turn tests) and 1 PASS (extra-local-keys — old code also allows reattach for `len(metadata) >= completed_count`) — the gapped-metadata test fails because old code uses `len(metadata) < completed_count` (2 < 2 is False, so the gap is missed), and the zero-turn test fails because old code skips the check when `completed_count == 0`

- [ ] **Step 3: Restructure `recover_startup()` metadata check**

In `server/dialogue.py`, find the metadata check inside `recover_startup()` (currently at lines 533-539, but shifted by Task 2 additions). Replace this block:

```python
                if completed_count > 0:
                    metadata = self._turn_store.get_all(handle.collaboration_id)
                    if len(metadata) < completed_count:
                        self._lineage_store.update_status(
                            handle.collaboration_id, "unknown"
                        )
                        continue
```

With:

```python
                metadata = self._turn_store.get_all(handle.collaboration_id)
                if not _local_metadata_complete_for_completed_turns(
                    metadata, completed_count
                ):
                    self._lineage_store.update_status(
                        handle.collaboration_id, "unknown"
                    )
                    continue
```

- [ ] **Step 4: Update `recover_startup()` docstring and phase-2 comments**

The current docstring at `dialogue.py:492-495` says:

```
        Unknown handles are eligible for reattach if:
        - they have no completed turns (vacuous metadata check), OR
        - all completed turns have corresponding TurnStore metadata
```

Replace with:

```
        Unknown handles are eligible for reattach if their local TurnStore
        metadata passes prefix-completeness:
        - if completed_count == 0: the TurnStore must have no metadata
          for this collaboration (deliberate tightening — see contracts.md)
        - if completed_count > 0: metadata keys {1..completed_count}
          must all be present (extra keys beyond completed_count tolerated)
```

The current phase-2 comment at `dialogue.py:512-514` says:

```
        # Quarantine any handle with incomplete TurnStore metadata.
        # Unknown handles are eligible for reattach if metadata is complete
        # (or if they have no completed turns to check).
```

Replace with:

```
        # Quarantine any handle that fails prefix-completeness:
        # - completed_count == 0: no stale local metadata allowed
        # - completed_count > 0: keys {1..completed_count} all present
        # Uses the same _local_metadata_complete_for_completed_turns()
        # helper as _next_turn_sequence() for reply/recovery symmetry.
```

- [ ] **Step 5: Run the recovery tests**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoverStartupMetadataCompleteness -v`

Expected: 3 passed

- [ ] **Step 6: Run the full dialogue test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py -x -q`

Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat(dialogue): restructure recover_startup metadata check

Move metadata completeness check outside 'if completed_count > 0'
guard. Now uses shared _local_metadata_complete_for_completed_turns()
for the same prefix-completeness invariant as _next_turn_sequence().
Update recover_startup() docstring and phase-2 comments to match
the if/else contract form (no more vacuous OR-branches).

Catches: gapped metadata, zero-turn stale metadata (deliberate
tightening — contracts.md updated). Aligns recovery with reply path.
Tests: gapped quarantine, zero-turn quarantine, extra-key acceptance.

Ref: T-20260410-02"
```

---

### Task 6: Final verification and lint

**Files:** None (verification only)

- [ ] **Step 1: Run the full package test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`

Expected: All tests pass (existing baseline + 15 new tests: 3 turn_store + 9 fast-path + 3 recovery)

- [ ] **Step 2: Run ruff check**

Run: `cd packages/plugins/codex-collaboration && uv run ruff check server/ tests/`

Expected: No errors

- [ ] **Step 3: Run ruff format check**

Run: `cd packages/plugins/codex-collaboration && uv run ruff format --check server/ tests/`

Expected: No reformatting needed (or run `ruff format` to fix)

- [ ] **Step 4: Verify commit log on branch**

Run: `git log --oneline d5aa4038..HEAD`

Expected: 6 commits — 1 docs (Task 0) + 5 implementation (Tasks 1-5):
1. `docs(spec): revise fast-path hardening design ...`
2. `feat(turn-store): add get_all_checked ...`
3. `feat(dialogue): add _local_metadata_complete_for_completed_turns ...`
4. `feat(dialogue): rewrite _next_turn_sequence ...`
5. `test(dialogue): add _next_turn_sequence hardening tests`
6. `feat(dialogue): restructure recover_startup metadata check ...`

- [ ] **Step 5: Verify ticket acceptance criteria**

Cross-reference against ticket T-20260410-02 acceptance criteria:
- ✅ Empty TurnStore + corruption diagnostics → don't trust fast path (tests: `test_empty_plus_diagnostics_*`)
- ✅ Regression test: turn 1 succeeds without `read_thread` on healthy path (existing: `test_first_reply_skips_read_thread`)
- ✅ Regression test: turn 1 `read_thread` failure not masked by fast path (test: `test_empty_plus_diagnostics_remote_fails`)
- ✅ Regression test: partial/gapped/inconsistent turn metadata handled (tests: `test_gap_*`, `test_partial_tail_*`, `test_extra_local_*`)
- ✅ Reply/recovery symmetry: zero-turn stale metadata rejected on both paths (`test_zero_turn_stale_metadata_*`)
- ✅ Reply/recovery symmetry: extra-key prefix-complete accepted on both paths (`test_extra_local_keys_*`)
- ✅ Error messages distinguish local metadata ambiguity from remote thread-read failure (tests check error message patterns)
- ✅ `recover_startup()` docstring/comments updated to match if/else contract form
