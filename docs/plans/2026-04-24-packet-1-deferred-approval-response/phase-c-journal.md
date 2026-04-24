# Packet 1 — Phase C: Journal

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 10
**Scope:** `OperationJournalEntry.completion_origin` field + journal validator relaxation (admit `decision=None` on `intent` and `dispatched` phases) + recovery read-side audit (step 10.7a).
**Landing invariant:** Journal validator admits `decision=None`; `completion_origin` field round-trips; recovery tolerates orphaned intent with null decision without crashing.

---

## Task 10: OperationJournalEntry.completion_origin + journal validator relaxation

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py` (add `completion_origin` field to `OperationJournalEntry`)
- Modify: `packages/plugins/codex-collaboration/server/journal.py` (relax `decision` check at intent/dispatched; serialize + replay new field)
- Test: `packages/plugins/codex-collaboration/tests/test_journal_completion_origin.py` (new)

**Spec anchor:** §OperationJournalEntry (addition) (spec lines ~1438-1449). §Journal validator relaxation (spec lines ~2184-2215).

- [ ] **Step 10.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_journal_completion_origin.py`:

```python
"""Packet 1: OperationJournalEntry.completion_origin + decision=None relaxation."""

from __future__ import annotations

import pytest

from server.journal import OperationJournal, SchemaViolation
from server.models import OperationJournalEntry


def test_completion_origin_field_exists_with_default_none() -> None:
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="2026-04-24T12:00:00Z",
        repo_root="/tmp",
    )
    assert entry.completion_origin is None


def test_intent_accepts_decision_none(tmp_path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="intent",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=None,  # timeout-wake / internal-abort-wake
    )
    journal.write_phase(entry, session_id="s1")


def test_dispatched_accepts_decision_none(tmp_path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="dispatched",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=None,
        runtime_id="rt1",
        codex_thread_id="t1",
    )
    journal.write_phase(entry, session_id="s1")


def test_decision_non_string_non_none_still_rejected(tmp_path) -> None:
    """Only None is permitted; a non-string non-None (e.g., dict, int) is
    still a schema violation per the narrow relaxation."""
    journal = OperationJournal(plugin_data_path=tmp_path)
    # Replay a hand-crafted bad record to hit the validator.
    bad = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="intent",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision=42,  # not a string, not None — invalid
    )
    with pytest.raises(SchemaViolation):
        journal.write_phase(bad, session_id="s1")


def test_completion_origin_worker_completed_round_trip(tmp_path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin="worker_completed",
    )
    journal.write_phase(entry, session_id="s1")
    # Replay and assert field round-trips.
    replay = journal.replay_jsonl(session_id="s1")
    found = [e for e in replay if e.idempotency_key == "k1" and e.phase == "completed"]
    assert len(found) == 1
    assert found[0].completion_origin == "worker_completed"


def test_completion_origin_recovered_unresolved_round_trip(tmp_path) -> None:
    journal = OperationJournal(plugin_data_path=tmp_path)
    entry = OperationJournalEntry(
        idempotency_key="k1",
        operation="approval_resolution",
        phase="completed",
        collaboration_id="c1",
        created_at="t",
        repo_root="/tmp",
        job_id="j1",
        request_id="r1",
        decision="approve",
        completion_origin="recovered_unresolved",
    )
    journal.write_phase(entry, session_id="s1")
    replay = journal.replay_jsonl(session_id="s1")
    found = [e for e in replay if e.idempotency_key == "k1" and e.phase == "completed"]
    assert len(found) == 1
    assert found[0].completion_origin == "recovered_unresolved"


def test_legacy_records_without_field_replay_as_none(tmp_path) -> None:
    """Pre-Packet-1 records without completion_origin replay with None."""
    import json
    journal = OperationJournal(plugin_data_path=tmp_path)
    # Hand-write a legacy record.
    session_dir = tmp_path / "journal" / "s1"
    session_dir.mkdir(parents=True)
    legacy = {
        "idempotency_key": "k1",
        "operation": "approval_resolution",
        "phase": "completed",
        "collaboration_id": "c1",
        "created_at": "t",
        "repo_root": "/tmp",
        "job_id": "j1",
        "request_id": "r1",
        "decision": "approve",
    }
    (session_dir / "journal.jsonl").write_text(
        json.dumps(legacy, sort_keys=True) + "\n", encoding="utf-8"
    )
    replay = journal.replay_jsonl(session_id="s1")
    assert len(replay) == 1
    assert replay[0].completion_origin is None
```

- [ ] **Step 10.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_journal_completion_origin.py -v
```

Expected: FAIL — field/validator changes absent. Some tests fail at dataclass-construction (missing field), others at schema validation.

- [ ] **Step 10.3: Add `completion_origin` field to `OperationJournalEntry`**

Edit `packages/plugins/codex-collaboration/server/models.py:337-364` (the `OperationJournalEntry` dataclass). Add the field at the end:

```python
@dataclass(frozen=True)
class OperationJournalEntry:
    """..."""
    idempotency_key: str
    operation: Literal[
        "thread_creation",
        "turn_dispatch",
        "job_creation",
        "approval_resolution",
        "promotion",
    ]
    phase: Literal["intent", "dispatched", "completed"]
    collaboration_id: str
    created_at: str
    repo_root: str
    codex_thread_id: str | None = None
    turn_sequence: int | None = None
    runtime_id: str | None = None
    context_size: int | None = None
    job_id: str | None = None
    request_id: str | None = None
    decision: str | None = None
    # Packet 1: narrow provenance annotation on phase="completed" records.
    # "worker_completed" = worker wrote the completed record.
    # "recovered_unresolved" = cold-start recovery wrote the completed record
    #   to close an orphaned unresolved operation.
    # None = legacy record (pre-Packet-1) — back-compat read semantics.
    completion_origin: Literal["worker_completed", "recovered_unresolved"] | None = None
```

- [ ] **Step 10.4: Relax the journal `decision` schema check**

Edit `packages/plugins/codex-collaboration/server/journal.py:124-157` (the `approval_resolution` intent/dispatched schema blocks). Change both from `isinstance(..., str)` to "None-or-string":

```python
elif op == "approval_resolution" and phase == "intent":
    if not isinstance(record.get("job_id"), str):
        raise SchemaViolation(
            "approval_resolution at intent requires job_id (string)"
        )
    if not isinstance(record.get("request_id"), str):
        raise SchemaViolation(
            "approval_resolution at intent requires request_id (string)"
        )
    decision = record.get("decision")
    if decision is not None and not isinstance(decision, str):
        raise SchemaViolation(
            "approval_resolution at intent requires decision to be a string or None"
        )

elif op == "approval_resolution" and phase == "dispatched":
    if not isinstance(record.get("job_id"), str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires job_id (string)"
        )
    if not isinstance(record.get("request_id"), str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires request_id (string)"
        )
    decision = record.get("decision")
    if decision is not None and not isinstance(decision, str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires decision to be a string or None"
        )
    if not isinstance(record.get("runtime_id"), str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires runtime_id (string)"
        )
    if not isinstance(record.get("codex_thread_id"), str):
        raise SchemaViolation(
            "approval_resolution at dispatched requires codex_thread_id (string)"
        )
```

- [ ] **Step 10.5: Add `completion_origin` to the `OperationJournalEntry` construction in `replay_jsonl`**

In the same file (`journal.py`), locate the `entry = OperationJournalEntry(...)` construction (around `:166-179` in the current file). Add the new field:

```python
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
    request_id=record.get("request_id"),
    decision=record.get("decision"),
    completion_origin=record.get("completion_origin"),
)
```

Verify that `write_phase` serializes the field — locate the `asdict` or manual serialization in `write_phase` and ensure `completion_origin` is included. If the current serialization uses `asdict(entry)`, no change is needed; if it enumerates fields explicitly, add `"completion_origin": entry.completion_origin` to the dict.

- [ ] **Step 10.6: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_journal_completion_origin.py -v
```

Expected: 7 PASS.

- [ ] **Step 10.7: Verify existing journal tests still pass**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_journal.py -v
```

Expected: all PASS. If any prior test asserts "decision is required on intent" and now fails, that test's expectation is now stale per §Journal validator relaxation — update the assertion to match the new None-or-string rule.

- [ ] **Step 10.7a: Audit recovery read-side for `decision=None` handling**

Per spec §Journal validator relaxation: "Recovery code at `delegation_controller.py:1856-1884` must also accept None when reading journal intent records."

Read the current recovery code:

```bash
sed -n '1856,1884p' /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/delegation_controller.py
```

Inspect the logic for any `assert decision is not None` or `if not decision:` checks that would now be incorrect. If the recovery writes a `phase="completed"` record that carries `decision` over from the intent record, ensure it accepts `decision=None` (either by explicit handling or by not asserting).

Common fix shape:

```python
# Before (if present):
# decision = intent_record.decision
# assert isinstance(decision, str), "recovery: intent must carry string decision"

# After:
decision = intent_record.decision  # may be None for non-operator origins
# No assert — None is valid for timeout-wake / internal-abort-wake origins.
```

Add a test that exercises this path:

```python
# Lives in tests/test_delegation_controller.py (flat layout — no tests/
# subdirectory exists in this project). Place immediately after
# test_recover_startup_marks_intent_only_approval_resolution_unknown at :2129.
def test_recover_startup_closes_orphaned_none_decision_intent(
    tmp_path: Path,
) -> None:
    """Recovery must close an orphaned approval_resolution.intent with
    decision=None (timeout-wake or internal-abort-wake origin) by
    writing a phase='completed' record with
    completion_origin='recovered_unresolved', WITHOUT raising.

    This is the decision=None mirror of the existing sibling test at
    tests/test_delegation_controller.py:2129
    (test_recover_startup_marks_intent_only_approval_resolution_unknown),
    which covers the operator-origin case (decision='approve',
    recovered as job.status='unknown'). For decision=None
    (non-operator origin), Packet 1 closes the record explicitly
    as completion_origin='recovered_unresolved' instead of
    marking unknown.

    Concrete arrange/act/assert:
    1. Arrange — use the same _build_controller(tmp_path) helper
       the sibling test uses. Create the matching DelegationJob
       (status='needs_escalation') + CollaborationHandle
       (status='active'). Then write the orphaned intent via
       journal.write_phase:

           journal.write_phase(
               OperationJournalEntry(
                   idempotency_key="42:recovered",
                   operation="approval_resolution",
                   phase="intent",
                   collaboration_id="collab-1",
                   created_at=journal.timestamp(),
                   repo_root=str(repo_root),
                   job_id="job-1",
                   request_id="42",
                   decision=None,             # <-- the case under test
               ),
               session_id="sess-1",
           )

       NOTE: Before Step 10.4 relaxes the validator, this write
       itself would fail at the isinstance(decision, str) assertion
       in journal.py's approval_resolution schema. The test
       therefore only becomes executable after Step 10.4 lands.
    2. Act — controller.recover_startup() (no args, mirrors the
       sibling test exactly).
    3. Assert:
         - Recovery completes without raising.
         - The journal now contains a NEW approval_resolution
           record with phase='completed', request_id='42', and
           completion_origin='recovered_unresolved'.
         - The original intent record is still present
           (journal is append-only).
    """
    pytest.fail(
        "Task 10 Step 10.7a: implementer must author the body per "
        "the docstring above. This pytest.fail guard prevents a "
        "vacuous PASS from satisfying the Step 10.7a pytest run. "
        "The new test lives in tests/test_delegation_controller.py "
        "alongside the existing "
        "test_recover_startup_marks_intent_only_approval_resolution_unknown "
        "sibling at line 2129. Remove this pytest.fail once the "
        "arrange/act/assert is wired using _build_controller."
    )
```

Run (selects the new test by pytest node ID, avoiding the full-file run):

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_recover_startup_closes_orphaned_none_decision_intent -v
```

Expected: all PASS. If recovery chokes on None, fix by relaxing the guard.

- [ ] **Step 10.8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/journal.py packages/plugins/codex-collaboration/tests/test_journal_completion_origin.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "$(cat <<'EOF'
feat(delegate): add completion_origin + relax decision=None on journal (T-20260423-02 Task 10)

OperationJournalEntry gains completion_origin: Literal["worker_completed",
"recovered_unresolved"] | None, defaulting to None for back-compat. Journal
schema for approval_resolution intent/dispatched now permits
decision=None — semantically "non-operator-origin resolution" (timeout-wake
or internal-abort-wake). decision=None remains rejected on other operations;
DecisionAction literal itself is unchanged (still "approve" | "deny").

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase C complete.** Journal schema now admits `decision=None` on `intent`/`dispatched` phases and round-trips `completion_origin`; the recovery read-side tolerates orphaned intent with null decision. Store layer (Phase B) + journal (Phase C) together can represent the full Packet 1 request/job/operation state. Phase D follows with the `ResolutionRegistry` coordination primitive.

---

