# AC6 Analytics Emission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add analytics outcome recording to codex-collaboration's consult and dialogue flows, using a separate JSONL file and shared journal helper — not by expanding the existing trust-boundary `AuditEvent`.

**Architecture:** A new `OutcomeRecord` frozen dataclass in `models.py` captures structured outcome data already available at each success emission site. `OperationJournal` gains an `analytics/outcomes.jsonl` path and an `append_outcome()` method parallel to `append_audit_event()`. Four emission sites (1 consult, 3 dialogue) each construct and append an `OutcomeRecord` alongside the existing `AuditEvent`. Tests verify the JSONL file contents, field shapes, and per-site emission guards.

**Tech Stack:** Python 3.12, dataclasses, `json` stdlib, pytest

---

## File Structure

| File | Responsibility |
|------|---------------|
| `server/models.py` | `OutcomeRecord` frozen dataclass |
| `server/journal.py` | `analytics/outcomes.jsonl` path, `append_outcome()` method |
| `server/control_plane.py` | Consult outcome emission after audit event |
| `server/dialogue.py` | Dialogue outcome emission at 3 success sites |
| `tests/test_control_plane.py` | Consult outcome assertions |
| `tests/test_dialogue.py` | Dialogue outcome assertions (normal, recovery, repair) |

All paths are relative to `packages/plugins/codex-collaboration/`.

## Background: Emission Sites

Four existing code paths emit `AuditEvent` on success. Each will also emit an `OutcomeRecord`:

| # | File:Line | Action | Guard | Available Data |
|---|-----------|--------|-------|----------------|
| 1 | `control_plane.py:192` | `consult` | Always (success path) | `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `policy_fingerprint`, `repo_root` |
| 2 | `dialogue.py:307` | `dialogue_turn` | Always (normal reply success) | `collaboration_id`, `runtime_id`, `context_size`, `turn_id`, `turn_sequence`, `resolved_root`, `runtime.policy_fingerprint` |
| 3 | `dialogue.py:592` | `dialogue_turn` | `turn_id is not None and entry.runtime_id is not None` | Same as #2, plus `entry.repo_root`; `runtime.policy_fingerprint` via bootstrapped runtime |
| 4 | `dialogue.py:689` | `dialogue_turn` | `turn_id is not None and intent_entry.runtime_id is not None` | Same as #2, plus `intent_entry.repo_root`; `runtime.policy_fingerprint` via bootstrapped runtime |

## Background: Test Patterns

The existing test patterns use:
- `FakeRuntimeSession` from `tests/test_control_plane.py` — shared test double
- `_build_dialogue_stack()` from `tests/test_dialogue.py` — wires up full dialogue stack with test doubles
- Audit assertions read `plugin_data / "audit" / "events.jsonl"`, parse each line as JSON, filter by `action` field
- The same pattern applies to `analytics / "outcomes.jsonl"`

---

### Task 0: Create Feature Branch

All implementation work must happen on a feature branch off `main` (enforced by PreToolUse gitflow hook — edits on `main` are blocked).

- [ ] **Step 1: Create and switch to the feature branch**

```bash
git checkout main
git checkout -b feature/ac6-analytics-emission
```

- [ ] **Step 2: Verify**

```bash
git branch --show-current
```
Expected: `feature/ac6-analytics-emission`

---

### Task 1: OutcomeRecord Model

**Files:**
- Modify: `server/models.py:141-157` (after `AuditEvent`)

- [ ] **Step 1: Write the failing test**

Create `tests/test_outcome_record.py`:

```python
"""Tests for OutcomeRecord model."""

from __future__ import annotations

from dataclasses import asdict

from server.models import OutcomeRecord


class TestOutcomeRecord:
    def test_consult_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
        )
        assert record.outcome_type == "consult"
        assert record.context_size == 4096
        assert record.turn_sequence is None
        assert record.policy_fingerprint is None
        assert record.repo_root is None

    def test_dialogue_outcome_fields(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-2",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=2048,
            turn_id="turn-2",
            turn_sequence=3,
        )
        assert record.outcome_type == "dialogue_turn"
        assert record.turn_sequence == 3

    def test_frozen(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-3",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=1024,
            turn_id="turn-3",
        )
        import pytest
        with pytest.raises(AttributeError):
            record.outcome_type = "dialogue_turn"  # type: ignore[misc]

    def test_context_size_nullable(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-5",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="dialogue_turn",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=None,
            turn_id="turn-5",
            turn_sequence=1,
        )
        assert record.context_size is None
        d = asdict(record)
        assert d["context_size"] is None

    def test_asdict_roundtrip(self) -> None:
        record = OutcomeRecord(
            outcome_id="o-4",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-4",
            policy_fingerprint="abc123",
            repo_root="/tmp/repo",
        )
        d = asdict(record)
        assert d["outcome_id"] == "o-4"
        assert d["outcome_type"] == "consult"
        assert d["policy_fingerprint"] == "abc123"
        assert d["repo_root"] == "/tmp/repo"
        assert d["turn_sequence"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_outcome_record.py -v`
Expected: FAIL with `ImportError: cannot import name 'OutcomeRecord' from 'server.models'`

- [ ] **Step 3: Write minimal implementation**

Add to `server/models.py` after the `AuditEvent` class (after line 157):

```python
@dataclass(frozen=True)
class OutcomeRecord:
    """Analytics outcome record for consult and dialogue success paths.

    Separate from AuditEvent (trust-boundary record). Persisted to
    analytics/outcomes.jsonl via OperationJournal.append_outcome().
    """

    outcome_id: str
    timestamp: str
    outcome_type: Literal["consult", "dialogue_turn"]
    collaboration_id: str
    runtime_id: str
    context_size: int | None
    turn_id: str
    turn_sequence: int | None = None
    policy_fingerprint: str | None = None
    repo_root: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_outcome_record.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/tests/test_outcome_record.py
git commit -m "feat: add OutcomeRecord model for analytics emission (AC6)"
```

---

### Task 2: Journal Persistence Path

**Files:**
- Modify: `server/journal.py:110-121` (constructor), `server/journal.py:155-159` (after `append_audit_event`)

- [ ] **Step 1: Write the failing test**

In `tests/test_outcome_record.py`, add these imports to the **top of the file** (in the existing import block, after `from dataclasses import asdict`):

```python
import json
from pathlib import Path
```

And add this import after the existing `from server.models import OutcomeRecord` line:

```python
from server.journal import OperationJournal
```

Then **append** the following test class at the end of the file:

```python
class TestOutcomeJournalPersistence:
    def test_append_outcome_creates_file_and_writes_jsonl(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        record = OutcomeRecord(
            outcome_id="o-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="consult",
            collaboration_id="collab-1",
            runtime_id="rt-1",
            context_size=4096,
            turn_id="turn-1",
            policy_fingerprint="fp-abc",
            repo_root="/tmp/repo",
        )
        journal.append_outcome(record)

        outcomes_path = tmp_path / "plugin-data" / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        line = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
        assert line["outcome_id"] == "o-1"
        assert line["outcome_type"] == "consult"
        assert line["context_size"] == 4096
        assert line["policy_fingerprint"] == "fp-abc"

    def test_append_outcome_appends_multiple_records(self, tmp_path: Path) -> None:
        journal = OperationJournal(tmp_path / "plugin-data")
        for i in range(3):
            journal.append_outcome(
                OutcomeRecord(
                    outcome_id=f"o-{i}",
                    timestamp="2026-04-01T00:00:00Z",
                    outcome_type="dialogue_turn",
                    collaboration_id=f"collab-{i}",
                    runtime_id="rt-1",
                    context_size=1024 * (i + 1),
                    turn_id=f"turn-{i}",
                    turn_sequence=i + 1,
                )
            )

        outcomes_path = tmp_path / "plugin-data" / "analytics" / "outcomes.jsonl"
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        records = [json.loads(line) for line in lines]
        assert records[0]["outcome_id"] == "o-0"
        assert records[2]["context_size"] == 3072
        assert records[1]["turn_sequence"] == 2

    def test_analytics_directory_created_on_init(self, tmp_path: Path) -> None:
        plugin_data = tmp_path / "plugin-data"
        OperationJournal(plugin_data)
        assert (plugin_data / "analytics").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_outcome_record.py::TestOutcomeJournalPersistence -v`
Expected: FAIL — `AttributeError: 'OperationJournal' object has no attribute 'append_outcome'` or `AssertionError` for directory check

- [ ] **Step 3: Write minimal implementation**

In `server/journal.py`, make three changes:

**3a.** Add `OutcomeRecord` to the import line (line 13):

Change:
```python
from .models import AuditEvent, OperationJournalEntry, StaleAdvisoryContextMarker
```
To:
```python
from .models import AuditEvent, OperationJournalEntry, OutcomeRecord, StaleAdvisoryContextMarker
```

**3b.** Add analytics path setup to `__init__` (after line 120, `self._audit_dir.mkdir(...)`):

```python
        self._analytics_dir = self._plugin_data_path / "analytics"
        self._outcomes_path = self._analytics_dir / "outcomes.jsonl"
        self._analytics_dir.mkdir(parents=True, exist_ok=True)
```

**3c.** Add `append_outcome` method after `append_audit_event` (after line 159):

```python
    def append_outcome(self, record: OutcomeRecord) -> None:
        """Append an analytics outcome record as JSONL."""

        with self._outcomes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_outcome_record.py -v`
Expected: 8 passed (5 model + 3 journal)

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All existing tests pass (430+)

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/journal.py packages/plugins/codex-collaboration/tests/test_outcome_record.py
git commit -m "feat: add analytics outcome persistence path to OperationJournal (AC6)"
```

---

### Task 3: Consult Outcome Emission

**Files:**
- Modify: `server/control_plane.py:188-205` (after audit emission)
- Modify: `tests/test_control_plane.py:244-278` (existing consult test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_control_plane.py` after `test_codex_consult_returns_structured_result_and_audits_context_size`:

```python
def test_codex_consult_emits_outcome_record(tmp_path: Path) -> None:
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")
    session = FakeRuntimeSession()
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
        journal=journal,
    )

    result = plane.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Review focus.py",
            explicit_paths=(Path("focus.py"),),
        )
    )

    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    assert outcomes_path.exists()
    record = json.loads(outcomes_path.read_text(encoding="utf-8").strip())
    assert record["outcome_type"] == "consult"
    assert record["collaboration_id"] == "collab-1"
    assert record["runtime_id"] == "runtime-1"
    assert record["context_size"] == result.context_size
    assert record["turn_id"] is not None
    assert record["policy_fingerprint"] is not None
    assert record["repo_root"] == str(tmp_path.resolve())
    assert record["turn_sequence"] is None
```

Also add a negative test:

```python
def test_codex_consult_failure_does_not_emit_outcome(tmp_path: Path) -> None:
    session = FakeRuntimeSession(run_turn_error=RuntimeError("turn boom"))
    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)
    plane = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        journal=journal,
    )

    with pytest.raises(RuntimeError, match="turn boom"):
        plane.codex_consult(
            ConsultRequest(repo_root=tmp_path, objective="Should fail")
        )

    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    assert not outcomes_path.exists() or outcomes_path.read_text(encoding="utf-8").strip() == ""
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py::test_codex_consult_emits_outcome_record tests/test_control_plane.py::test_codex_consult_failure_does_not_emit_outcome -v`
Expected: `test_codex_consult_emits_outcome_record` FAIL (no outcomes.jsonl written); `test_codex_consult_failure_does_not_emit_outcome` PASS (failure path already doesn't write)

- [ ] **Step 3: Write minimal implementation**

In `server/control_plane.py`:

**3a.** Add `OutcomeRecord` to the import (line 23):

Change:
```python
from .models import (
    AdvisoryRuntimeState,
    AuditEvent,
    ConsultRequest,
    ConsultResult,
    RepoIdentity,
)
```
To:
```python
from .models import (
    AdvisoryRuntimeState,
    AuditEvent,
    ConsultRequest,
    ConsultResult,
    OutcomeRecord,
    RepoIdentity,
)
```

**3b.** Add outcome emission after the audit event block (after line 205, before the `return ConsultResult(...)` at line 206):

```python
        self._journal.append_outcome(
            OutcomeRecord(
                outcome_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                outcome_type="consult",
                collaboration_id=collaboration_id,
                runtime_id=runtime.runtime_id,
                context_size=packet.context_size,
                turn_id=turn_result.turn_id,
                policy_fingerprint=runtime.policy_fingerprint,
                repo_root=str(resolved_root),
            )
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_control_plane.py -v`
Expected: All pass

- [ ] **Step 5: Update uuid_factory iterators in all existing consult tests that reach outcome emission**

Adding outcome emission consumes one extra UUID per successful consult. Five tests use finite UUID iterators and reach the success path:

**5a.** `test_codex_consult_returns_structured_result_and_audits_context_size` (line 256):
```python
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
```

**5b.** `test_codex_consult_clears_stale_marker_on_success` (line 337):
```python
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
```

**5c.** `test_codex_consult_invalidates_cached_runtime_after_turn_failure` (line 365) — first consult fails (no outcome emitted), second succeeds. Add outcome UUID after the second event UUID:
```python
        uuid_factory=iter(
            ("runtime-1", "runtime-2", "collab-2", "event-2", "outcome-2")
        ).__next__,
```

**5d.** `test_codex_consult_invalidates_cached_runtime_after_parse_failure` (line 402) — first consult fails at parse. In `control_plane.py`, `parse_consult_response()` (line 182) runs BEFORE audit/outcome emission (lines 192+), so the first consult consumes only `runtime-1` (parse raises before collab/event/outcome UUIDs). The second consult succeeds and consumes `runtime-2`, `collab-2`, `event-2`, `outcome-2`:
```python
        uuid_factory=iter(
            ("runtime-1", "runtime-2", "collab-2", "event-2", "outcome-2")
        ).__next__,
```

**5e.** `test_codex_consult_revalidates_cached_runtime_auth_before_reuse` (line 438) — first consult succeeds, second fails at auth (no outcome). Add outcome UUID after the first event:
```python
        uuid_factory=iter(("runtime-1", "collab-1", "event-1", "outcome-1")).__next__,
```

- [ ] **Step 6: Run full test suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/control_plane.py packages/plugins/codex-collaboration/tests/test_control_plane.py
git commit -m "feat: emit consult outcome record in analytics path (AC6)"
```

---

### Task 4: Dialogue Normal Reply Outcome Emission

**Files:**
- Modify: `server/dialogue.py:304-318` (after audit emission in `reply()`)
- Modify: `tests/test_dialogue.py:162-179` (near existing audit test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_dialogue.py` in `class TestDialogueReply`, after `test_reply_emits_dialogue_turn_audit_event`:

```python
    def test_reply_emits_outcome_record(self, tmp_path: Path) -> None:
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        controller, _, _, journal, _ = _build_dialogue_stack(tmp_path)
        start_result = controller.start(tmp_path)
        controller.reply(
            collaboration_id=start_result.collaboration_id,
            objective="Test turn",
            explicit_paths=(Path("focus.py"),),
        )
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start_result.collaboration_id
        assert dialogue_outcomes[0]["turn_id"] is not None
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] > 0
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueReply::test_reply_emits_outcome_record -v`
Expected: FAIL — outcomes.jsonl not written or empty

- [ ] **Step 3: Write minimal implementation**

In `server/dialogue.py`:

**3a.** Add `OutcomeRecord` to the import (line 19):

Change:
```python
from .models import (
    AuditEvent,
    CollaborationHandle,
    ConsultRequest,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
    OperationJournalEntry,
    RepoIdentity,
)
```
To:
```python
from .models import (
    AuditEvent,
    CollaborationHandle,
    ConsultRequest,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
    OperationJournalEntry,
    OutcomeRecord,
    RepoIdentity,
)
```

**3b.** Add outcome emission after the audit event block in `reply()` (after line 318, before the `# Parse projection` comment at line 320):

```python
        self._journal.append_outcome(
            OutcomeRecord(
                outcome_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                outcome_type="dialogue_turn",
                collaboration_id=collaboration_id,
                runtime_id=runtime.runtime_id,
                context_size=packet.context_size,
                turn_id=turn_result.turn_id,
                turn_sequence=turn_sequence,
                policy_fingerprint=runtime.policy_fingerprint,
                repo_root=str(resolved_root),
            )
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestDialogueReply::test_reply_emits_outcome_record -v`
Expected: PASS

- [ ] **Step 5: Extend parse-failure durability test to assert outcome emission**

The existing test `TestCommittedTurnParseError.test_completes_journal_writes_store_and_emits_audit` (line 1300) verifies that journal, TurnStore, and audit emission all complete before parsing. Since `append_outcome()` sits in the same pre-parse block, add an outcome assertion to lock that invariant.

Add to `tests/test_dialogue.py` at the end of `test_completes_journal_writes_store_and_emits_audit` (after the audit assertion at line 1335):

```python
        # Outcome record emitted (before parse)
        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        outcome_lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        outcome_records = [json.loads(line) for line in outcome_lines]
        dialogue_outcomes = [r for r in outcome_records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start.collaboration_id
```

- [ ] **Step 6: Run parse-failure test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestCommittedTurnParseError::test_completes_journal_writes_store_and_emits_audit -v`
Expected: PASS (outcome emission is in the pre-parse block alongside audit)

- [ ] **Step 7: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat: emit dialogue_turn outcome on normal reply success (AC6)"
```

---

### Task 5: Recovery Path Outcome Emission

**Files:**
- Modify: `server/dialogue.py:592-604` (in `_recover_turn_dispatch`, after audit emission)
- Modify: `tests/test_dialogue.py` (near existing recovery tests)

The recovery path at `dialogue.py:592` already guards audit emission with `if turn_id is not None and entry.runtime_id is not None`. The outcome emission uses the same guard.

- [ ] **Step 1: Write the failing test**

Find the test class that covers startup recovery. Add a new test. Based on the existing `TestBestEffortRepairTurn.test_emits_dialogue_turn_audit_when_turn_confirmed` pattern, add a recovery-specific test.

First, find where `_recover_turn_dispatch` is tested. It is exercised via `controller.recover_pending_operations()`. Add this test to `tests/test_dialogue.py`:

```python
class TestRecoveryOutcomeEmission:
    def test_recovery_confirmed_emits_outcome_record(self, tmp_path: Path) -> None:
        """Startup recovery that confirms a turn also emits an outcome record."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "recovered-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-01T00:00:00Z",
                    },
                ],
            },
        }
        controller, _, _, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        # Simulate: an unresolved turn_dispatch entry left by a crashed session
        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller.recover_pending_operations()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["collaboration_id"] == start.collaboration_id
        assert dialogue_outcomes[0]["turn_id"] == "recovered-turn-1"
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] == 4096
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None

    def test_recovery_unconfirmed_does_not_emit_outcome(self, tmp_path: Path) -> None:
        """Recovery that cannot confirm the turn does NOT emit an outcome."""
        focus = tmp_path / "focus.py"
        focus.write_text("print('focus')\n", encoding="utf-8")
        session = FakeRuntimeSession()
        # thread/read shows no completed turns — turn unconfirmed
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
        }
        controller, _, _, journal, _ = _build_dialogue_stack(
            tmp_path, session=session
        )
        start = controller.start(tmp_path)

        intent_entry = OperationJournalEntry(
            idempotency_key="rt-sess-1:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller.recover_pending_operations()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        if outcomes_path.exists():
            content = outcomes_path.read_text(encoding="utf-8").strip()
            if content:
                records = [json.loads(line) for line in content.split("\n")]
                dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
                assert len(dialogue_outcomes) == 0
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoveryOutcomeEmission -v`
Expected: `test_recovery_confirmed_emits_outcome_record` FAIL; `test_recovery_unconfirmed_does_not_emit_outcome` PASS

- [ ] **Step 3: Write minimal implementation**

In `server/dialogue.py`, inside `_recover_turn_dispatch`, add outcome emission after the audit event block (after line 604, inside the `if turn_id is not None and entry.runtime_id is not None:` guard):

Change lines 592-604 from:
```python
        if turn_id is not None and entry.runtime_id is not None:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="dialogue_turn",
                    collaboration_id=entry.collaboration_id,
                    runtime_id=entry.runtime_id,
                    context_size=entry.context_size,
                    turn_id=turn_id,
                )
            )
```
To:
```python
        if turn_id is not None and entry.runtime_id is not None:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="dialogue_turn",
                    collaboration_id=entry.collaboration_id,
                    runtime_id=entry.runtime_id,
                    context_size=entry.context_size,
                    turn_id=turn_id,
                )
            )
            self._journal.append_outcome(
                OutcomeRecord(
                    outcome_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    outcome_type="dialogue_turn",
                    collaboration_id=entry.collaboration_id,
                    runtime_id=entry.runtime_id,
                    context_size=entry.context_size,
                    turn_id=turn_id,
                    turn_sequence=entry.turn_sequence,
                    policy_fingerprint=runtime.policy_fingerprint,
                    repo_root=entry.repo_root,
                )
            )
```

Note: `entry.context_size` is `int | None` on `OperationJournalEntry` and `int | None` on `OutcomeRecord` — the types match. `runtime` is the bootstrapped runtime from line 541. `entry.repo_root` is always a string (required field on `OperationJournalEntry`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestRecoveryOutcomeEmission -v`
Expected: 2 passed

- [ ] **Step 5: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat: emit outcome record on recovery-confirmed dialogue turn (AC6)"
```

---

### Task 6: Best-Effort Repair Path Outcome Emission

**Files:**
- Modify: `server/dialogue.py:689-701` (in `_best_effort_repair_turn`, after audit emission)
- Modify: `tests/test_dialogue.py` (extend `TestBestEffortRepairTurn`)

This is the inline repair path — same guard pattern as recovery.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_dialogue.py` in `class TestBestEffortRepairTurn`:

```python
    def test_emits_outcome_record_when_turn_confirmed(
        self, tmp_path: Path
    ) -> None:
        """Confirmed inline repair must also emit an outcome record."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {
                "id": "thr-start",
                "turns": [
                    {
                        "id": "repaired-turn-1",
                        "status": "completed",
                        "agentMessage": "",
                        "createdAt": "2026-04-01T00:00:00Z",
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
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
        assert len(dialogue_outcomes) == 1
        assert dialogue_outcomes[0]["turn_id"] == "repaired-turn-1"
        assert dialogue_outcomes[0]["turn_sequence"] == 1
        assert dialogue_outcomes[0]["context_size"] == 4096
        assert dialogue_outcomes[0]["repo_root"] == str(tmp_path.resolve())
        assert dialogue_outcomes[0]["policy_fingerprint"] is not None

    def test_does_not_emit_outcome_when_turn_unconfirmed(
        self, tmp_path: Path
    ) -> None:
        """Unconfirmed repair must NOT emit an outcome record."""
        session = FakeRuntimeSession()
        session.read_thread_response = {
            "thread": {"id": "thr-start", "turns": []},
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
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="rt-sess-1",
            context_size=4096,
        )
        journal.write_phase(intent_entry, session_id="sess-1")

        controller._best_effort_repair_turn(intent_entry)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        if outcomes_path.exists():
            content = outcomes_path.read_text(encoding="utf-8").strip()
            if content:
                records = [json.loads(line) for line in content.split("\n")]
                dialogue_outcomes = [r for r in records if r["outcome_type"] == "dialogue_turn"]
                assert len(dialogue_outcomes) == 0
```

- [ ] **Step 2: Run tests to verify failures**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestBestEffortRepairTurn::test_emits_outcome_record_when_turn_confirmed tests/test_dialogue.py::TestBestEffortRepairTurn::test_does_not_emit_outcome_when_turn_unconfirmed -v`
Expected: `test_emits_outcome_record_when_turn_confirmed` FAIL; `test_does_not_emit_outcome_when_turn_unconfirmed` PASS

- [ ] **Step 3: Write minimal implementation**

In `server/dialogue.py`, inside `_best_effort_repair_turn`, add outcome emission after the audit event block (after line 701, inside the `if turn_id is not None and intent_entry.runtime_id is not None:` guard):

Change lines 689-701 from:
```python
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
To:
```python
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
            self._journal.append_outcome(
                OutcomeRecord(
                    outcome_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    outcome_type="dialogue_turn",
                    collaboration_id=intent_entry.collaboration_id,
                    runtime_id=intent_entry.runtime_id,
                    context_size=intent_entry.context_size,
                    turn_id=turn_id,
                    turn_sequence=intent_entry.turn_sequence,
                    policy_fingerprint=runtime.policy_fingerprint,
                    repo_root=intent_entry.repo_root,
                )
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_dialogue.py::TestBestEffortRepairTurn -v`
Expected: All pass (existing + 2 new)

- [ ] **Step 5: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_dialogue.py
git commit -m "feat: emit outcome record on best-effort repair confirmed turn (AC6)"
```

---

### Task 7: Shape Consistency Test

**Files:**
- Create: `tests/test_outcome_shape_consistency.py`

This test verifies that all emission sites serialize the same JSON shape, preventing field drift between the consult, normal reply, recovery, and repair paths.

- [ ] **Step 1: Write the test**

```python
"""Shape consistency test for OutcomeRecord emission across all paths."""

from __future__ import annotations

import json
from pathlib import Path

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import ConsultRequest, OperationJournalEntry
from server.turn_store import TurnStore

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _collect_outcomes(plugin_data: Path) -> list[dict]:
    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    if not outcomes_path.exists():
        return []
    content = outcomes_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return [json.loads(line) for line in content.split("\n")]


def test_all_outcome_records_share_same_keys(tmp_path: Path) -> None:
    """Consult, normal reply, recovery, and repair all produce the same key set."""
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)

    # 1. Consult outcome
    session_consult = FakeRuntimeSession()
    plane_consult = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_consult,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter(
            (f"uuid-{i}" for i in range(100))
        ).__next__,
        journal=journal,
    )
    plane_consult.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Test",
            explicit_paths=(Path("focus.py"),),
        )
    )

    # 2. Normal dialogue reply outcome
    session_dialogue = FakeRuntimeSession()
    plane_dialogue = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_dialogue,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 200.0,
        uuid_factory=iter(
            (f"d-uuid-{i}" for i in range(100))
        ).__next__,
        journal=journal,
    )
    store = LineageStore(plugin_data, "sess-shape")
    turn_store = TurnStore(plugin_data, "sess-shape")
    controller = DialogueController(
        control_plane=plane_dialogue,
        lineage_store=store,
        journal=journal,
        session_id="sess-shape",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(
            (f"dc-uuid-{i}" for i in range(100))
        ).__next__,
        turn_store=turn_store,
    )
    start = controller.start(tmp_path)
    controller.reply(
        collaboration_id=start.collaboration_id,
        objective="Test turn",
        explicit_paths=(Path("focus.py"),),
    )

    # 3. Recovery outcome
    session_recovery = FakeRuntimeSession()
    session_recovery.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "recovered-turn",
                    "status": "completed",
                    "agentMessage": "",
                    "createdAt": "",
                },
            ],
        },
    }
    plane_recovery = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_recovery,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 300.0,
        uuid_factory=iter(
            (f"r-uuid-{i}" for i in range(100))
        ).__next__,
        journal=journal,
    )
    store_r = LineageStore(plugin_data, "sess-recovery")
    turn_store_r = TurnStore(plugin_data, "sess-recovery")
    controller_r = DialogueController(
        control_plane=plane_recovery,
        lineage_store=store_r,
        journal=journal,
        session_id="sess-recovery",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(
            (f"rc-uuid-{i}" for i in range(100))
        ).__next__,
        turn_store=turn_store_r,
    )
    start_r = controller_r.start(tmp_path)
    # Write an unresolved turn_dispatch for recovery to pick up
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="r-uuid-0:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start_r.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="r-uuid-0",
            context_size=2048,
        ),
        session_id="sess-recovery",
    )
    controller_r.recover_pending_operations()

    # 4. Best-effort repair outcome
    session_repair = FakeRuntimeSession()
    session_repair.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "repaired-turn",
                    "status": "completed",
                    "agentMessage": "",
                    "createdAt": "",
                },
            ],
        },
    }
    plane_repair = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_repair,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 400.0,
        uuid_factory=iter(
            (f"rp-uuid-{i}" for i in range(100))
        ).__next__,
        journal=journal,
    )
    store_rp = LineageStore(plugin_data, "sess-repair")
    turn_store_rp = TurnStore(plugin_data, "sess-repair")
    controller_rp = DialogueController(
        control_plane=plane_repair,
        lineage_store=store_rp,
        journal=journal,
        session_id="sess-repair",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter(
            (f"rpc-uuid-{i}" for i in range(100))
        ).__next__,
        turn_store=turn_store_rp,
    )
    start_rp = controller_rp.start(tmp_path)
    store_rp.update_status(start_rp.collaboration_id, "unknown")
    intent_entry_rp = OperationJournalEntry(
        idempotency_key="rp-uuid-0:thr-start:1",
        operation="turn_dispatch",
        phase="intent",
        collaboration_id=start_rp.collaboration_id,
        created_at="2026-04-01T00:00:00Z",
        repo_root=str(tmp_path.resolve()),
        codex_thread_id="thr-start",
        turn_sequence=1,
        runtime_id="rp-uuid-0",
        context_size=1024,
    )
    journal.write_phase(intent_entry_rp, session_id="sess-repair")
    controller_rp._best_effort_repair_turn(intent_entry_rp)

    # Collect all outcomes and verify key consistency
    outcomes = _collect_outcomes(plugin_data)
    assert len(outcomes) >= 4, f"Expected at least 4 outcomes, got {len(outcomes)}"

    # All records must have exactly the same set of keys
    key_sets = [frozenset(r.keys()) for r in outcomes]
    assert len(set(key_sets)) == 1, (
        f"Outcome records have inconsistent keys. "
        f"Key sets: {[sorted(ks) for ks in key_sets]}"
    )
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd packages/plugins/codex-collaboration && uv run pytest tests/test_outcome_shape_consistency.py -v`
Expected: PASS (all emission sites now implemented)

- [ ] **Step 3: Run full suite**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_outcome_shape_consistency.py
git commit -m "test: verify outcome record shape consistency across all emission paths (AC6)"
```

---

### Task 8: Lint and Final Verification

- [ ] **Step 1: Lint all modified source and test files**

Run: `cd packages/plugins/codex-collaboration && uv run ruff check server/models.py server/journal.py server/control_plane.py server/dialogue.py tests/test_outcome_record.py tests/test_control_plane.py tests/test_dialogue.py tests/test_outcome_shape_consistency.py && uv run ruff format --check server/models.py server/journal.py server/control_plane.py server/dialogue.py tests/test_outcome_record.py tests/test_control_plane.py tests/test_dialogue.py tests/test_outcome_shape_consistency.py`
Expected: Clean

- [ ] **Step 2: Format only target files if needed**

Run: `cd packages/plugins/codex-collaboration && uv run ruff format server/models.py server/journal.py server/control_plane.py server/dialogue.py tests/test_outcome_record.py tests/test_control_plane.py tests/test_dialogue.py tests/test_outcome_shape_consistency.py`

Do NOT run `ruff format .` — this will reformat ~28 non-target files (known divergence in this plugin, documented in prior handoffs).

- [ ] **Step 3: Run full test suite one final time**

Run: `cd packages/plugins/codex-collaboration && uv run pytest -v`
Expected: All pass (430 existing + ~14 new)

- [ ] **Step 4: Smoke-test outcome emission end-to-end**

Run: `cd packages/plugins/codex-collaboration && uv run python -c "
import json, tempfile
from pathlib import Path
from server.journal import OperationJournal
from server.models import OutcomeRecord
d = Path(tempfile.mkdtemp())
j = OperationJournal(d)
j.append_outcome(OutcomeRecord(
    outcome_id='smoke-1', timestamp='2026-04-01T00:00:00Z',
    outcome_type='consult', collaboration_id='c-1', runtime_id='r-1',
    context_size=1024, turn_id='t-1',
))
p = d / 'analytics' / 'outcomes.jsonl'
assert p.exists(), 'outcomes.jsonl not created'
r = json.loads(p.read_text().strip())
assert r['outcome_type'] == 'consult', f'wrong outcome_type: {r[\"outcome_type\"]}'
print(f'PASS: {p} contains valid outcome record')
"`
Expected: `PASS: /tmp/.../analytics/outcomes.jsonl contains valid outcome record`

- [ ] **Step 5: Commit formatting fixes if any**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/journal.py packages/plugins/codex-collaboration/server/control_plane.py packages/plugins/codex-collaboration/server/dialogue.py packages/plugins/codex-collaboration/tests/test_outcome_record.py packages/plugins/codex-collaboration/tests/test_control_plane.py packages/plugins/codex-collaboration/tests/test_dialogue.py packages/plugins/codex-collaboration/tests/test_outcome_shape_consistency.py
git commit -m "style: apply ruff formatting to AC6 analytics emission files"
```

(Skip this commit if step 1 was clean.)

---

## Verification Checklist

| Check | Task |
|-------|------|
| `OutcomeRecord` is frozen and separate from `AuditEvent` | Task 1 |
| `analytics/` directory created on journal init; `outcomes.jsonl` created on first append | Task 2 |
| `append_outcome()` writes sorted-key JSONL | Task 2 |
| Consult success emits one outcome record | Task 3 |
| Consult failure does NOT emit outcome | Task 3 |
| Normal dialogue reply emits one outcome record | Task 4 |
| Parse-failure reply still emits outcome (pre-parse durability) | Task 4 |
| Recovery-confirmed turn emits one outcome record | Task 5 |
| Recovery-unconfirmed turn does NOT emit outcome | Task 5 |
| Best-effort repair confirmed emits one outcome record | Task 6 |
| Best-effort repair unconfirmed does NOT emit outcome | Task 6 |
| All emission sites produce same JSON key set | Task 7 |
| Lint clean on all modified files | Task 8 |
| Full suite passes with no regressions | Task 8 |

## Gotchas

- **uuid_factory exhaustion:** Adding outcome emission consumes one extra UUID per success path. Any test that uses a finite UUID iterator must add entries. Task 3 step 5 patches all five affected tests in `test_control_plane.py`; dialogue tests use `range(100)` iterators so they have headroom.
- **context_size nullable:** Both `OperationJournalEntry.context_size` and `OutcomeRecord.context_size` are `int | None`. Recovery/repair paths pass `entry.context_size` through directly — no coercion to 0. A `None` context_size in the outcome means the size was not available at recovery time (data-quality gap, not fabrication).
- **Ruff formatting artifacts:** Format only target files. Never `ruff format .` in this plugin directory.
