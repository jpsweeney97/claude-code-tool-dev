# T-06 Decide Opening Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first `codex.delegate.decide` slice so live same-session `needs_escalation` jobs can be approved or denied through the MCP surface, with typed rejections, retained-runtime reuse on approve, and clean terminal lifecycle handling on deny.

**Architecture:** `codex.delegate.decide` is a plugin-side escalation consumer, not a late reply to the original App Server request. The controller validates a live `needs_escalation` job, journals the approval-resolution attempt, emits the approval audit record, then either resumes the retained execution runtime with a follow-up turn on approve or terminates the job on deny. The opening slice stays deliberately narrow: no `poll`, no promotion, no worktree cleanup policy, and no cross-session runtime recovery; if the runtime is missing after restart, recovery marks the job `unknown` instead of trying to reattach it.

**Tech Stack:** Python 3.11+, pytest, append-only JSONL stores, MCP JSON-RPC tool dispatch, existing execution runtime/session wrappers.

---

## Scope Lock

### In scope

1. Add `codex.delegate.decide` to the MCP surface with a typed request schema:
   - `job_id: str`
   - `request_id: str`
   - `decision: "approve" | "deny"`
   - optional `answers` object for `request_user_input` approvals only
2. Pin the caller-facing `codex.delegate.decide` contract in `contracts.md`:
   - success result shape
   - typed rejection shape
   - same-session-live-runtime limitation
3. Implement `DelegationController.decide()` for jobs already in `needs_escalation`.
4. Reuse the retained live runtime on approve by dispatching a follow-up execution turn in the same thread.
5. Terminate the job cleanly on deny with `job.status = "failed"`.
6. Add a narrow approval-resolution journal operation keyed by `request_id + decision` so decision-time crashes reconcile to `unknown` instead of silently duplicating work.
7. Emit the audit event required by `recovery-and-journal.md` / `contracts.md` for approval resolution (`action: "approve"` with `decision`).
8. Close the direct lifecycle gaps this slice needs:
   - terminal execution handles move to `completed`
   - escalation paths keep handles active
   - same-session cleanup releases the runtime registry entry and closes the session on terminal paths
9. Add PreToolUse safety policy coverage for the new MCP tool input.

### Explicitly out of scope

1. `codex.delegate.poll`
2. `codex.delegate.promote`
3. Artifact hashing, rollback, and stale advisory context markers
4. `/delegate` skill UX
5. Cross-session runtime reattach, runtime inspection, or restart-from-brief
6. Worktree cleanup TTL policy
7. Session-scoped approval widening (`acceptForSession`, exec-policy amendments, network-policy amendments)
8. A generic “discard” action

### Design locks for this opening slice

1. **Plugin-side decision, not wire replay.** `PendingServerRequest.status` stays wire lifecycle. `codex.delegate.decide` acts on `DelegationJob.status` plus the stored causal request record; it does not attempt to reopen the original App Server request.
2. **Approve reuses the live runtime.** Approval dispatches a new follow-up turn in the existing execution thread.
3. **Deny is terminal and maps to `failed`.** A denied escalation did not accomplish the delegated work.
4. **Same-session only.** Missing runtime on `decide` is a typed rejection, not a recovery flow.
5. **No hidden poll scope.** The slice resolves a known `job_id + request_id` pair directly; it does not add job enumeration or inspection surfaces.

---

## File Structure

### Modified production files

| Path | Responsibility in this slice |
|---|---|
| `docs/superpowers/specs/codex-collaboration/contracts.md` | Pin the `codex.delegate.decide` success + rejection contract and the opening-slice same-session constraint. |
| `packages/plugins/codex-collaboration/server/models.py` | Add decide result/rejection types, decision literals, `AuditEvent.decision`, and approval-resolution journal fields. |
| `packages/plugins/codex-collaboration/server/journal.py` | Accept and replay the new `approval_resolution` journal operation. |
| `packages/plugins/codex-collaboration/server/execution_prompt_builder.py` | Build the follow-up execution prompt used after approve. |
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | Extract reusable execution-turn logic, fix terminal handle lifecycle, implement `decide()`, and reconcile unresolved approval-resolution records on startup. |
| `packages/plugins/codex-collaboration/server/mcp_server.py` | Register and dispatch `codex.delegate.decide`. |
| `packages/plugins/codex-collaboration/server/consultation_safety.py` | Add the PreToolUse scan policy for `codex.delegate.decide`. |
| `packages/plugins/codex-collaboration/server/__init__.py` | Export the new decide result/rejection types if they are public. |

### Modified test files

| Path | Coverage added |
|---|---|
| `packages/plugins/codex-collaboration/tests/test_models_r2.py` | Decide dataclasses, audit decision field, journal-entry shape. |
| `packages/plugins/codex-collaboration/tests/test_journal.py` | Approval-resolution journal round-trip and validator requirements. |
| `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py` | Resume prompt content for approve and optional answers. |
| `packages/plugins/codex-collaboration/tests/test_delegation_controller.py` | Shared execution helper behavior, handle lifecycle, decide success paths, decide rejections, and approval-resolution recovery. |
| `packages/plugins/codex-collaboration/tests/test_mcp_server.py` | Tool definition, dispatch wiring, and serialization for `codex.delegate.decide`. |
| `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py` | End-to-end `start -> escalate -> decide` approve/deny flows through MCP. |
| `packages/plugins/codex-collaboration/tests/test_consultation_safety.py` | Policy routing for the new tool. |
| `packages/plugins/codex-collaboration/tests/test_codex_guard.py` | Hook guard behavior for clean and secret-bearing `codex.delegate.decide` inputs. |

### No new production modules

Keep the opening slice inside the existing execution-domain files. The refactor belongs in `delegation_controller.py`; do not introduce a new “decision manager” module just to move code around.

---

## Acceptance Coverage For This Plan

| Opening-slice requirement | Planned implementation |
|---|---|
| Live `needs_escalation` jobs can be approved | Task 4 adds `DelegationController.decide()` approve path that dispatches a follow-up turn in the retained runtime. |
| Live `needs_escalation` jobs can be denied | Task 4 sets `job.status = "failed"`, marks the execution handle completed, releases the runtime, and returns a typed decide result. |
| Invalid decide attempts are typed rejections | Tasks 1 and 5 add `DecisionRejectedResponse` plus controller validation tests. |
| Same-session-only boundary is enforced | Task 5 returns `runtime_unavailable` when the registry entry is gone and reconciles unresolved approval-resolution records to `unknown` on startup. |
| No ticket-scope creep into poll/promote | Scope lock + tasks avoid any job listing, artifact hash, rollback, or worktree cleanup behavior. |

---

## Pre-Flight

- [ ] **Step P1: Re-anchor on live `main`**

Run:
```bash
git branch --show-current
git rev-parse --short HEAD
git status --short --branch
```

Expected:
- branch is `main`
- `HEAD` is still `271f23aa` or a consciously-reviewed newer mainline commit
- only known local drift is the existing untracked file `docs/plans/2026-04-19-t05-pending-request-capture-slice.md`

If `main` moved, read the landed diff first and adjust file references before editing.

- [ ] **Step P2: Confirm the current delegation baseline is green**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py -q
```

Expected: PASS on the current T-05 execution + escalation substrate.

If baseline is red, stop and fix that first. Do not layer T-06 planning assumptions on a broken T-05 base.

---

### Task 1: Pin The Decide Contract And Approval-Resolution Journal Vocabulary

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/contracts.md`
- Modify: `packages/plugins/codex-collaboration/server/models.py`
- Modify: `packages/plugins/codex-collaboration/server/journal.py`
- Test: `packages/plugins/codex-collaboration/tests/test_models_r2.py`
- Test: `packages/plugins/codex-collaboration/tests/test_journal.py`

- [ ] **Step 1.1: Write the failing model and journal tests**

Append to `packages/plugins/codex-collaboration/tests/test_models_r2.py`:

```python
def test_delegation_decision_result_shape() -> None:
    from server.models import (
        DelegationDecisionResult,
        DelegationJob,
        PendingServerRequest,
    )

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="completed",
    )
    request = PendingServerRequest(
        request_id="req-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind="command_approval",
        requested_scope={"command": "make test"},
        status="resolved",
    )

    result = DelegationDecisionResult(
        job=job,
        decision="approve",
        resumed=True,
        pending_request=request,
        agent_context="Need approval",
    )

    assert result.job.job_id == "job-1"
    assert result.decision == "approve"
    assert result.resumed is True
    assert result.pending_request is request


def test_decision_rejected_response_shape() -> None:
    from server.models import DecisionRejectedResponse

    rejected = DecisionRejectedResponse(
        rejected=True,
        reason="runtime_unavailable",
        detail="Delegation decide failed: runtime unavailable. Got: 'rt-1'",
        job_id="job-1",
        request_id="req-1",
    )

    assert rejected.rejected is True
    assert rejected.reason == "runtime_unavailable"
    assert rejected.job_id == "job-1"
    assert rejected.request_id == "req-1"


def test_audit_event_supports_decision_field() -> None:
    from server.models import AuditEvent

    event = AuditEvent(
        event_id="evt-1",
        timestamp="2026-04-19T00:00:00Z",
        actor="claude",
        action="approve",
        collaboration_id="collab-1",
        runtime_id="rt-1",
        job_id="job-1",
        request_id="req-1",
        decision="deny",
    )

    assert event.action == "approve"
    assert event.decision == "deny"


def test_operation_journal_entry_supports_approval_resolution_fields() -> None:
    from server.models import OperationJournalEntry

    entry = OperationJournalEntry(
        idempotency_key="req-1:approve",
        operation="approval_resolution",
        phase="intent",
        collaboration_id="collab-1",
        created_at="2026-04-19T00:00:00Z",
        repo_root="/repo",
        job_id="job-1",
        request_id="req-1",
        decision="approve",
    )

    assert entry.operation == "approval_resolution"
    assert entry.request_id == "req-1"
    assert entry.decision == "approve"
```

Append to `packages/plugins/codex-collaboration/tests/test_journal.py`:

```python
def test_approval_resolution_round_trips_as_unresolved_terminal_record(
    tmp_path: Path,
) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="req-1:approve",
            operation="approval_resolution",
            phase="intent",
            collaboration_id="collab-1",
            created_at="2026-04-19T00:00:00Z",
            repo_root="/repo",
            job_id="job-1",
            request_id="req-1",
            decision="approve",
        ),
        session_id="sess-1",
    )

    unresolved = journal.list_unresolved(session_id="sess-1")
    assert len(unresolved) == 1
    assert unresolved[0].operation == "approval_resolution"
    assert unresolved[0].request_id == "req-1"
    assert unresolved[0].decision == "approve"


def test_check_health_reports_missing_request_id_for_approval_resolution(
    tmp_path: Path,
) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    path = journal._operations_path("sess-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "idempotency_key": "req-1:approve",
                "operation": "approval_resolution",
                "phase": "intent",
                "collaboration_id": "collab-1",
                "created_at": "2026-04-19T00:00:00Z",
                "repo_root": "/repo",
                "job_id": "job-1",
                "decision": "approve",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    diagnostics = journal.check_health(session_id="sess-1")
    assert len(diagnostics.schema_violations) == 1
    assert "request_id" in diagnostics.schema_violations[0].detail
```

- [ ] **Step 1.2: Run the targeted tests and verify they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_journal.py -q
```

Expected: FAIL because the decide dataclasses, `AuditEvent.decision`, and the `approval_resolution` journal vocabulary do not exist yet.

- [ ] **Step 1.3: Add the contract text and model types**

Update `docs/superpowers/specs/codex-collaboration/contracts.md` by adding this typed-response section after `### Job Busy`:

```markdown
### Decision Rejection

Returned by `codex.delegate.decide` when the caller asks to resolve an escalation
that cannot be handled under the opening-slice constraints.

| Field | Type | Description |
|---|---|---|
| `rejected` | boolean | Always `true` |
| `reason` | enum | `invalid_decision`, `job_not_found`, `job_not_awaiting_decision`, `request_not_found`, `request_job_mismatch`, `runtime_unavailable`, `answers_required`, `answers_not_allowed` |
| `detail` | string | Human-readable explanation |
| `job_id` | string? | Rejected job id when known |
| `request_id` | string? | Rejected request id when known |

### Decide Result

Returned by `codex.delegate.decide` on success.

| Field | Type | Description |
|---|---|---|
| `job` | [DelegationJob](#delegationjob) | Updated job after the decision path finished |
| `decision` | enum | `approve` or `deny` |
| `resumed` | boolean | `true` only when approve dispatched a follow-up turn |
| `pending_request` | [PendingServerRequest](#pendingserverrequest)? | Present only when the resumed turn hit another escalation |
| `agent_context` | string? | Best-effort agent message from the resumed turn when present |
```

Update `packages/plugins/codex-collaboration/server/models.py`:

```python
DecisionAction = Literal["approve", "deny"]
DecisionRejectedReason = Literal[
    "invalid_decision",
    "job_not_found",
    "job_not_awaiting_decision",
    "request_not_found",
    "request_job_mismatch",
    "runtime_unavailable",
    "answers_required",
    "answers_not_allowed",
]
```

Add these dataclasses below `DelegationEscalation`:

```python
@dataclass(frozen=True)
class DelegationDecisionResult:
    """Returned by codex.delegate.decide after approve or deny."""

    job: DelegationJob
    decision: DecisionAction
    resumed: bool
    pending_request: PendingServerRequest | None = None
    agent_context: str | None = None


@dataclass(frozen=True)
class DecisionRejectedResponse:
    """Typed rejection returned by codex.delegate.decide."""

    rejected: bool
    reason: DecisionRejectedReason
    detail: str
    job_id: str | None = None
    request_id: str | None = None
```

Extend `AuditEvent`:

```python
    decision: str | None = None
```

Extend `OperationJournalEntry`:

```python
    operation: Literal[
        "thread_creation",
        "turn_dispatch",
        "job_creation",
        "approval_resolution",
    ]
    request_id: str | None = None
    decision: str | None = None
```

- [ ] **Step 1.4: Teach the journal validator about `approval_resolution`**

Update `packages/plugins/codex-collaboration/server/journal.py`:

```python
_VALID_OPERATIONS = frozenset(
    ("thread_creation", "turn_dispatch", "job_creation", "approval_resolution")
)
_JOURNAL_OPTIONAL_STR = ("codex_thread_id", "runtime_id", "job_id", "request_id", "decision")
```

Add this conditional validation branch inside `_journal_callback`:

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
        if not isinstance(record.get("decision"), str):
            raise SchemaViolation(
                "approval_resolution at intent requires decision (string)"
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
        if not isinstance(record.get("decision"), str):
            raise SchemaViolation(
                "approval_resolution at dispatched requires decision (string)"
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

And pass the extra fields into `OperationJournalEntry`:

```python
        request_id=record.get("request_id"),
        decision=record.get("decision"),
```

- [ ] **Step 1.5: Re-run the targeted tests**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_journal.py -q
```

Expected: PASS.

- [ ] **Step 1.6: Commit**

```bash
git add \
  docs/superpowers/specs/codex-collaboration/contracts.md \
  packages/plugins/codex-collaboration/server/models.py \
  packages/plugins/codex-collaboration/server/journal.py \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_journal.py
git commit -m "feat(t20260330-06): pin decide contract and journal vocabulary"
```

---

### Task 2: Build The Resume Prompt For Approve

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/execution_prompt_builder.py`
- Test: `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py`

- [ ] **Step 2.1: Write the failing prompt-builder tests**

Append to `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py`:

```python
from server.models import PendingServerRequest


def test_build_execution_resume_turn_text_includes_request_context() -> None:
    from server.execution_prompt_builder import build_execution_resume_turn_text

    request = PendingServerRequest(
        request_id="req-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind="command_approval",
        requested_scope={"command": "make test", "cwd": "/repo"},
        status="resolved",
    )

    result = build_execution_resume_turn_text(
        pending_request=request,
        answers=None,
    )

    assert "req-1" in result
    assert "command_approval" in result
    assert "make test" in result
    assert "already been resolved at the wire layer" in result


def test_build_execution_resume_turn_text_includes_answers_when_present() -> None:
    from server.execution_prompt_builder import build_execution_resume_turn_text

    request = PendingServerRequest(
        request_id="req-2",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-2",
        kind="request_user_input",
        requested_scope={"questions": [{"id": "q1"}]},
        status="resolved",
    )

    result = build_execution_resume_turn_text(
        pending_request=request,
        answers={"q1": ("yes", "ship it")},
    )

    assert "request_user_input" in result
    assert "q1" in result
    assert "ship it" in result
```

- [ ] **Step 2.2: Run the prompt-builder tests and verify they fail**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py -q
```

Expected: FAIL because `build_execution_resume_turn_text` does not exist yet.

- [ ] **Step 2.3: Add the resume prompt builder**

Update `packages/plugins/codex-collaboration/server/execution_prompt_builder.py`:

```python
import json

from .models import PendingServerRequest
```

Add this function below `build_execution_turn_text`:

```python
def build_execution_resume_turn_text(
    *,
    pending_request: PendingServerRequest,
    answers: dict[str, tuple[str, ...]] | None,
) -> str:
    """Build the follow-up prompt used after Claude approves an escalation."""

    requested_scope = json.dumps(
        pending_request.requested_scope,
        indent=2,
        sort_keys=True,
    )
    lines = [
        "Continue the existing isolated delegation thread.",
        "The earlier server request has already been resolved at the wire layer.",
        "Do not re-ask for the same approval; treat the caller decision below as authoritative.",
        "",
        f"Escalation kind: {pending_request.kind}",
        f"Request id: {pending_request.request_id}",
        "Captured request scope:",
        requested_scope,
    ]
    if answers:
        answer_payload = json.dumps(
            {key: {"answers": list(value)} for key, value in answers.items()},
            indent=2,
            sort_keys=True,
        )
        lines.extend(
            [
                "",
                "Caller-supplied answers:",
                answer_payload,
            ]
        )
    return "\n".join(lines)
```

- [ ] **Step 2.4: Re-run the prompt-builder tests**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py -q
```

Expected: PASS.

- [ ] **Step 2.5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/execution_prompt_builder.py \
  packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py
git commit -m "feat(t20260330-06): add execution resume prompt builder"
```

---

### Task 3: Extract A Reusable Execution-Turn Helper And Close Terminal Handle Lifecycle

This is the highest-risk mechanical refactor in the packet. Keep it in its own commit, preserve behavior byte-for-byte outside the explicit lifecycle fixes below, and do not start Task 4 until the full controller suite is green again.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

- [ ] **Step 3.1: Write the failing lifecycle tests**

Append to `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
def test_start_completed_job_marks_execution_handle_completed(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, lineage, _j, _r, _prs = _build_controller(tmp_path)

    result = controller.start(repo_root=repo_root, objective="Finish cleanly")

    assert isinstance(result, DelegationJob)
    handle = lineage.get("collab-1")
    assert handle is not None
    assert handle.status == "completed"


def test_start_escalation_keeps_execution_handle_active(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, lineage, _j, _r, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]

    result = controller.start(repo_root=repo_root, objective="Need approval")

    assert isinstance(result, DelegationEscalation)
    handle = lineage.get("collab-1")
    assert handle is not None
    assert handle.status == "active"
```

- [ ] **Step 3.1b: Harden the multi-turn test fixture before decide tests depend on it**

In `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`, update `_FakeSession.run_execution_turn()` so interrupt state is per-turn instead of leaking across turns:

```python
    def run_execution_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        sandbox_policy: dict[str, Any],
        approval_policy: str = "on-request",
        output_schema: dict[str, Any] | None = None,
        effort: str | None = None,
        server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None]
        | None = None,
    ) -> TurnExecutionResult:
        """Simulate run_execution_turn by dispatching fake server requests."""
        if self._raise_on_turn is not None:
            raise self._raise_on_turn
        self._interrupted = False
        for req in self._server_requests:
            if server_request_handler is not None:
                server_request_handler(req)
        if self._interrupted:
            return TurnExecutionResult(
                turn_id=self._turn_result.turn_id,
                status="interrupted",
                agent_message=self._turn_result.agent_message,
                notifications=self._turn_result.notifications,
            )
        return self._turn_result
```

Also extend `_build_controller()`'s `uuid_counter` pool so multi-turn decide tests use semantically clear audit ids:

```python
    uuid_counter = iter(
        [
            "job-1",
            "collab-1",
            "delegate-start-evt-1",
            "escalation-evt-1",
            "decision-evt-1",
            "re-escalation-evt-1",
            "job-2",
            "collab-2",
            "delegate-start-evt-2",
            "escalation-evt-2",
        ]
    )
```

- [ ] **Step 3.2: Run the lifecycle tests and verify they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_start_completed_job_marks_execution_handle_completed \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_start_escalation_keeps_execution_handle_active -q
```

Expected: FAIL because terminal execution handles still stay `active`.

- [ ] **Step 3.3: Extract the shared execution-turn helper and fix terminal handle transitions**

Update `packages/plugins/codex-collaboration/server/delegation_controller.py` by extracting the turn-dispatch block from `start()` into a helper:

```python
    def _execute_live_turn(
        self,
        *,
        job_id: str,
        collaboration_id: str,
        runtime_id: str,
        worktree_path: Path,
        prompt_text: str,
    ) -> DelegationJob | DelegationEscalation:
        self._job_store.update_status(job_id, "running")

        captured_request: PendingServerRequest | None = None
        interrupted_by_unknown = False
        captured_request_parse_failed = False
        _CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})
        _KNOWN_DENIAL_KINDS = frozenset({"request_user_input"})
        entry = self._runtime_registry.lookup(runtime_id)
        assert entry is not None, (
            f"ExecutionRuntimeRegistry invariant violation: runtime_id={runtime_id!r} "
            "not found during live turn execution"
        )

        def _server_request_handler(
            message: dict[str, Any],
        ) -> dict[str, Any] | None:
            nonlocal captured_request, interrupted_by_unknown, captured_request_parse_failed
            try:
                parsed = parse_pending_server_request(
                    message,
                    runtime_id=runtime_id,
                    collaboration_id=collaboration_id,
                )
            except Exception:
                logger.warning(
                    "Server request parse failed; creating minimal causal record "
                    "(D4 carve-out). Wire id=%r, method=%r",
                    message.get("id"),
                    message.get("method", ""),
                    exc_info=True,
                )
                wire_id = message.get("id")
                wire_method = message.get("method", "")
                minimal = PendingServerRequest(
                    request_id=str(wire_id)
                    if wire_id is not None
                    else self._uuid_factory(),
                    runtime_id=runtime_id,
                    collaboration_id=collaboration_id,
                    codex_thread_id="",
                    codex_turn_id="",
                    item_id="",
                    kind="unknown",
                    requested_scope={"raw_method": wire_method},
                )
                if captured_request is None:
                    self._pending_request_store.create(minimal)
                    captured_request = minimal
                    captured_request_parse_failed = True
                interrupted_by_unknown = True
                entry = self._runtime_registry.lookup(runtime_id)
                if entry is not None:
                    entry.session.interrupt_turn(
                        thread_id=entry.thread_id,
                        turn_id=None,
                    )
                return None

            if (
                parsed.kind not in _CANCEL_CAPABLE_KINDS
                and parsed.kind not in _KNOWN_DENIAL_KINDS
            ):
                if captured_request is None:
                    self._pending_request_store.create(parsed)
                    captured_request = parsed
                interrupted_by_unknown = True
                entry = self._runtime_registry.lookup(runtime_id)
                if entry is not None:
                    entry.session.interrupt_turn(
                        thread_id=entry.thread_id,
                        turn_id=None,
                    )
                return None

            if captured_request is None:
                self._pending_request_store.create(parsed)
                captured_request = parsed

            if parsed.kind in _CANCEL_CAPABLE_KINDS:
                return {"decision": "cancel"}
            return {"answers": {}}

        try:
            turn_result = entry.session.run_execution_turn(
                thread_id=entry.thread_id,
                prompt_text=prompt_text,
                sandbox_policy=build_workspace_write_sandbox_policy(worktree_path),
                approval_policy=self._approval_policy,
                server_request_handler=_server_request_handler,
            )
        except Exception:
            self._mark_execution_unknown_and_cleanup(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                entry=entry,
            )
            raise

        try:
            return self._finalize_turn(
                job_id=job_id,
                runtime_id=runtime_id,
                collaboration_id=collaboration_id,
                entry=entry,
                turn_result=turn_result,
                captured_request=captured_request,
                interrupted_by_unknown=interrupted_by_unknown,
                captured_request_parse_failed=captured_request_parse_failed,
            )
        except Exception:
            self._mark_execution_unknown_and_cleanup(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                entry=entry,
            )
            raise
```

Add a dedicated cleanup helper so the failure path is not duplicated:

```python
    def _mark_execution_unknown_and_cleanup(
        self,
        *,
        job_id: str,
        collaboration_id: str,
        runtime_id: str,
        entry: ExecutionRuntimeEntry,
    ) -> None:
        try:
            self._job_store.update_status(job_id, "unknown")
        except Exception:
            logger.error(
                "Execution cleanup: failed to mark job %r unknown",
                job_id,
                exc_info=True,
            )
        try:
            self._lineage_store.update_status(collaboration_id, "unknown")
        except Exception:
            logger.error(
                "Execution cleanup: failed to mark handle %r unknown",
                collaboration_id,
                exc_info=True,
            )
        try:
            self._runtime_registry.release(runtime_id)
        except Exception:
            logger.error(
                "Execution cleanup: failed to release runtime %r",
                runtime_id,
                exc_info=True,
            )
        try:
            entry.session.close()
        except Exception:
            logger.error(
                "Execution cleanup: failed to close runtime %r",
                runtime_id,
                exc_info=True,
            )
```

Update `_finalize_turn()` terminal branches so execution handles close cleanly.

In the captured-request non-escalation branch, replace the existing:

```python
            # Non-escalation: release + close and return plain job.
            self._runtime_registry.release(runtime_id)
            entry.session.close()
            return updated_job
```

with:

```python
            self._lineage_store.update_status(collaboration_id, "completed")
            self._runtime_registry.release(runtime_id)
            entry.session.close()
            return updated_job
```

In the no-captured-request terminal branch, replace the existing:

```python
        self._job_store.update_status(job_id, final_status)
        self._runtime_registry.release(runtime_id)
        entry.session.close()
```

with:

```python
        self._job_store.update_status(job_id, final_status)
        self._lineage_store.update_status(collaboration_id, "completed")
        self._runtime_registry.release(runtime_id)
        entry.session.close()
```

Finally, make `start()` call `_execute_live_turn()` instead of inlining the turn block:

```python
        prompt_text = build_execution_turn_text(
            objective=objective,
            worktree_path=str(worktree_path),
        )
        return self._execute_live_turn(
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            worktree_path=worktree_path,
            prompt_text=prompt_text,
        )
```

- [ ] **Step 3.4: Run the lifecycle tests plus the existing controller suite**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q
```

Expected: PASS. The two new handle-lifecycle tests should now pass without regressing the T-05 escalation tests.

- [ ] **Step 3.5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "refactor(t20260330-06): share execution turn path and close terminal handles"
```

---

### Task 4: Implement `DelegationController.decide()` Success Paths

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

- [ ] **Step 4.1: Write the failing approve/deny success-path tests**

Append to `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
def test_decide_approve_resumes_runtime_and_returns_completed_result(
    tmp_path: Path,
) -> None:
    from server.models import DelegationDecisionResult

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, lineage, _j, registry, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="Approved work finished.",
        notifications=(),
    )

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DelegationDecisionResult)
    assert result.decision == "approve"
    assert result.resumed is True
    assert result.pending_request is None
    assert result.job.status == "completed"
    assert registry.lookup("rt-1") is None
    handle = lineage.get("collab-1")
    assert handle is not None and handle.status == "completed"


def test_decide_approve_can_reescalate_with_new_pending_request(tmp_path: Path) -> None:
    from server.models import DelegationDecisionResult

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, registry, prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    session = control_plane._sessions[0]
    session._server_requests = [_permissions_request(request_id=99, item_id="item-2")]
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="interrupted",
        agent_message="Need another escalation.",
        notifications=(),
    )

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DelegationDecisionResult)
    assert result.decision == "approve"
    assert result.resumed is True
    assert result.pending_request is not None
    assert result.pending_request.request_id == "99"
    assert result.job.status == "needs_escalation"
    assert registry.lookup("rt-1") is not None
    stored = prs.get("99")
    assert stored is not None and stored.status == "resolved"


def test_decide_deny_marks_job_failed_and_closes_runtime(tmp_path: Path) -> None:
    from server.models import DelegationDecisionResult

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, lineage, journal, registry, _prs = (
        _build_controller(tmp_path)
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="deny",
    )

    assert isinstance(result, DelegationDecisionResult)
    assert result.decision == "deny"
    assert result.resumed is False
    assert result.pending_request is None
    assert result.job.status == "failed"
    assert job_store.get("job-1") is not None
    assert registry.lookup("rt-1") is None
    handle = lineage.get("collab-1")
    assert handle is not None and handle.status == "completed"

    events_path = journal.plugin_data_path / "audit" / "events.jsonl"
    lines = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]
    approval_events = [e for e in lines if e.get("action") == "approve"]
    assert len(approval_events) == 1
    assert approval_events[0]["decision"] == "deny"
    assert approval_events[0]["request_id"] == "42"
```

- [ ] **Step 4.2: Run the new success-path tests and verify they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_decide_approve_resumes_runtime_and_returns_completed_result \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_decide_approve_can_reescalate_with_new_pending_request \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py::test_decide_deny_marks_job_failed_and_closes_runtime -q
```

Expected: FAIL because `DelegationController.decide()` does not exist yet.

- [ ] **Step 4.3: Add `CommittedDecisionFinalizationError` and implement `decide()`**

In `packages/plugins/codex-collaboration/server/delegation_controller.py`, add:

```python
class CommittedDecisionFinalizationError(RuntimeError):
    """Raised when codex.delegate.decide committed a caller decision but local
    finalization failed.

    Blind retry is unsafe: approve may have already dispatched a follow-up turn,
    and deny may already have terminated the live runtime.
    """
```

Add `DelegationDecisionResult`, `DecisionAction`, and `DecisionRejectedResponse`
to the import list.

Add this helper inside `DelegationController`:

```python
    def _reject_decision(
        self,
        *,
        reason: str,
        detail: str,
        job_id: str | None,
        request_id: str | None,
    ) -> DecisionRejectedResponse:
        return DecisionRejectedResponse(
            rejected=True,
            reason=reason,
            detail=detail,
            job_id=job_id,
            request_id=request_id,
        )
```

Then add `decide()`:

```python
    def decide(
        self,
        *,
        job_id: str,
        request_id: str,
        decision: DecisionAction | str,
        answers: dict[str, tuple[str, ...]] | None = None,
    ) -> DelegationDecisionResult | DecisionRejectedResponse:
        if decision not in ("approve", "deny"):
            return self._reject_decision(
                reason="invalid_decision",
                detail=(
                    "Delegation decide failed: invalid decision. "
                    f"Got: {decision!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )
        job = self._job_store.get(job_id)
        if job is None:
            return self._reject_decision(
                reason="job_not_found",
                detail=f"Delegation decide failed: job not found. Got: {job_id!r:.100}",
                job_id=job_id,
                request_id=request_id,
            )
        if job.status != "needs_escalation":
            return self._reject_decision(
                reason="job_not_awaiting_decision",
                detail=(
                    "Delegation decide failed: job not awaiting decision. "
                    f"Got: status={job.status!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )

        request = self._pending_request_store.get(request_id)
        if request is None:
            return self._reject_decision(
                reason="request_not_found",
                detail=(
                    "Delegation decide failed: request not found. "
                    f"Got: {request_id!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )
        if request.collaboration_id != job.collaboration_id:
            return self._reject_decision(
                reason="request_job_mismatch",
                detail=(
                    "Delegation decide failed: request does not belong to job. "
                    f"Got: request_id={request_id!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )
        if decision == "deny" and answers:
            return self._reject_decision(
                reason="answers_not_allowed",
                detail="Delegation decide failed: deny does not accept answers. Got: 'answers'",
                job_id=job_id,
                request_id=request_id,
            )
        if request.kind == "request_user_input" and decision == "approve" and not answers:
            return self._reject_decision(
                reason="answers_required",
                detail=(
                    "Delegation decide failed: request_user_input approval requires answers. "
                    f"Got: {request_id!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )
        if request.kind != "request_user_input" and answers:
            return self._reject_decision(
                reason="answers_not_allowed",
                detail=(
                    "Delegation decide failed: answers are only valid for request_user_input. "
                    f"Got: kind={request.kind!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )

        handle = self._lineage_store.get(job.collaboration_id)
        entry = self._runtime_registry.lookup(job.runtime_id)
        if handle is None or entry is None:
            return self._reject_decision(
                reason="runtime_unavailable",
                detail=(
                    "Delegation decide failed: runtime unavailable for same-session decision. "
                    f"Got: runtime_id={job.runtime_id!r:.100}"
                ),
                job_id=job_id,
                request_id=request_id,
            )

        idempotency_key = f"{request_id}:{decision}"
        created_at = self._journal.timestamp()
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="approval_resolution",
                phase="intent",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=handle.repo_root,
                job_id=job_id,
                request_id=request_id,
                decision=decision,
            ),
            session_id=self._session_id,
        )
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="approve",
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                job_id=job_id,
                request_id=request_id,
                decision=decision,
            )
        )
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="approval_resolution",
                phase="dispatched",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=handle.repo_root,
                codex_thread_id=handle.codex_thread_id,
                runtime_id=job.runtime_id,
                job_id=job_id,
                request_id=request_id,
                decision=decision,
            ),
            session_id=self._session_id,
        )

        if decision == "deny":
            self._job_store.update_status(job_id, "failed")
            self._lineage_store.update_status(job.collaboration_id, "completed")
            self._runtime_registry.release(job.runtime_id)
            entry.session.close()
            updated_job = self._job_store.get(job_id)
            assert updated_job is not None
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=idempotency_key,
                    operation="approval_resolution",
                    phase="completed",
                    collaboration_id=job.collaboration_id,
                    created_at=created_at,
                    repo_root=handle.repo_root,
                    job_id=job_id,
                    request_id=request_id,
                    decision=decision,
                ),
                session_id=self._session_id,
            )
            return DelegationDecisionResult(
                job=updated_job,
                decision="deny",
                resumed=False,
            )

        prompt_text = build_execution_resume_turn_text(
            pending_request=request,
            answers=answers,
        )
        try:
            follow_up = self._execute_live_turn(
                job_id=job_id,
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                worktree_path=Path(job.worktree_path),
                prompt_text=prompt_text,
            )
        except Exception as exc:
            raise CommittedDecisionFinalizationError(
                "Delegation decide committed but local finalization failed: "
                f"{exc}. Blind retry may duplicate follow-up execution."
            ) from exc

        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="approval_resolution",
                phase="completed",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=handle.repo_root,
                job_id=job_id,
                request_id=request_id,
                decision=decision,
            ),
            session_id=self._session_id,
        )
        if isinstance(follow_up, DelegationEscalation):
            return DelegationDecisionResult(
                job=follow_up.job,
                decision="approve",
                resumed=True,
                pending_request=follow_up.pending_request,
                agent_context=follow_up.agent_context,
            )
        return DelegationDecisionResult(
            job=follow_up,
            decision="approve",
            resumed=True,
        )
```

- [ ] **Step 4.4: Run the controller suite**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q
```

Expected: PASS on the new approve/deny success paths plus the existing T-05 behavior.

- [ ] **Step 4.5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-06): implement same-session decide success paths"
```

---

### Task 5: Add Decide Rejections, Safety Policy, And Recovery

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Modify: `packages/plugins/codex-collaboration/server/consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`
- Test: `packages/plugins/codex-collaboration/tests/test_consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_codex_guard.py`

- [ ] **Step 5.1: Write the failing rejection and recovery tests**

Append to `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
def test_decide_rejects_when_runtime_is_missing(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, registry, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    registry.release("rt-1")

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.rejected is True
    assert result.reason == "runtime_unavailable"


def test_decide_rejects_invalid_decision_value(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="later",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.rejected is True
    assert result.reason == "invalid_decision"


def test_decide_request_user_input_requires_answers(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_request_user_input_request()]
    control_plane._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Need input",
        notifications=(),
    )
    start_result = controller.start(repo_root=repo_root, objective="Ask user")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="55",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.rejected is True
    assert result.reason == "answers_required"


def test_decide_approve_turn_failure_raises_committed_decision_finalization_error(
    tmp_path: Path,
) -> None:
    from server.delegation_controller import CommittedDecisionFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, lineage, journal, registry, _prs = (
        _build_controller(tmp_path)
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    session = control_plane._sessions[0]
    session._raise_on_turn = RuntimeError("transport died during decide")

    with pytest.raises(CommittedDecisionFinalizationError, match="committed"):
        controller.decide(
            job_id="job-1",
            request_id="42",
            decision="approve",
        )

    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    handle = lineage.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    assert registry.lookup("rt-1") is None

    unresolved = [
        e
        for e in journal.list_unresolved(session_id="sess-1")
        if e.operation == "approval_resolution"
    ]
    assert len(unresolved) == 1
    assert unresolved[0].phase == "dispatched"


def test_recover_startup_marks_intent_only_approval_resolution_unknown(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = _build_controller(
        tmp_path
    )

    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state="pending",
            status="needs_escalation",
        )
    )
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-1",
            capability_class="execution",
            runtime_id="rt-1",
            codex_thread_id="thr-1",
            claude_session_id="sess-1",
            repo_root=str(repo_root),
            created_at=journal.timestamp(),
            status="active",
        )
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="42:approve",
            operation="approval_resolution",
            phase="intent",
            collaboration_id="collab-1",
            created_at=journal.timestamp(),
            repo_root=str(repo_root),
            job_id="job-1",
            request_id="42",
            decision="approve",
        ),
        session_id="sess-1",
    )

    controller.recover_startup()

    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    assert journal.list_unresolved(session_id="sess-1") == []


def test_recover_startup_marks_dispatched_approval_resolution_unknown(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = _build_controller(
        tmp_path
    )

    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state="pending",
            status="needs_escalation",
        )
    )
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-1",
            capability_class="execution",
            runtime_id="rt-1",
            codex_thread_id="thr-1",
            claude_session_id="sess-1",
            repo_root=str(repo_root),
            created_at=journal.timestamp(),
            status="active",
        )
    )
    created_at = journal.timestamp()
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="42:approve",
            operation="approval_resolution",
            phase="intent",
            collaboration_id="collab-1",
            created_at=created_at,
            repo_root=str(repo_root),
            job_id="job-1",
            request_id="42",
            decision="approve",
        ),
        session_id="sess-1",
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="42:approve",
            operation="approval_resolution",
            phase="dispatched",
            collaboration_id="collab-1",
            created_at=created_at,
            repo_root=str(repo_root),
            codex_thread_id="thr-1",
            runtime_id="rt-1",
            job_id="job-1",
            request_id="42",
            decision="approve",
        ),
        session_id="sess-1",
    )

    controller.recover_startup()

    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    assert journal.list_unresolved(session_id="sess-1") == []
```

Append to `packages/plugins/codex-collaboration/tests/test_consultation_safety.py` and add `DELEGATE_DECIDE_POLICY` to the existing import list:

```python
from server.consultation_safety import DELEGATE_DECIDE_POLICY


def test_delegate_decide_returns_decide_policy() -> None:
    policy = policy_for_tool(
        "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide"
    )
    assert policy is DELEGATE_DECIDE_POLICY


def test_delegate_decide_answers_field_is_scanned() -> None:
    verdict = check_tool_input(
        {
            "job_id": "job-1",
            "request_id": "req-1",
            "decision": "approve",
            "answers": {"q1": {"answers": ["sk-" + "a" * 40]}},
        },
        DELEGATE_DECIDE_POLICY,
    )
    assert verdict.action == "block"
```

Append this new class to `packages/plugins/codex-collaboration/tests/test_codex_guard.py`:

```python
class TestDelegateDecideGuard:
    def test_delegate_decide_clean(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide",
            {
                "job_id": "job-1",
                "request_id": "req-1",
                "decision": "approve",
                "answers": {"q1": {"answers": ["yes"]}},
            },
        )
        assert result.returncode == 0

    def test_delegate_decide_answers_with_secret_block(self) -> None:
        result = _run_hook(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide",
            {
                "job_id": "job-1",
                "request_id": "req-1",
                "decision": "approve",
                "answers": {"q1": {"answers": ["sk-" + "a" * 40]}},
            },
        )
        assert result.returncode == 2
```

- [ ] **Step 5.2: Run the targeted tests and verify they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py -q
```

Expected: FAIL because the runtime-missing rejection, approval-resolution recovery, and guard-policy routing are not implemented yet.

- [ ] **Step 5.3: Reconcile unresolved `approval_resolution` entries and orphaned active jobs on startup**

Extend `DelegationController.recover_startup()` in `packages/plugins/codex-collaboration/server/delegation_controller.py` with a second operation branch after `job_creation` reconciliation:

```python
        approval_resolution_entries = [
            e for e in unresolved if e.operation == "approval_resolution"
        ]
        by_key = {}
        for entry in approval_resolution_entries:
            existing = by_key.get(entry.idempotency_key)
            if existing is None or _phase_rank(entry.phase) > _phase_rank(existing.phase):
                by_key[entry.idempotency_key] = entry

        for entry in by_key.values():
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation="approval_resolution",
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                    job_id=entry.job_id,
                    request_id=entry.request_id,
                    decision=entry.decision,
                ),
                session_id=self._session_id,
            )

        # Same-session-only startup reconciliation: after restart the runtime
        # registry is fresh, so any active execution job is orphaned and cannot
        # be decided or resumed. Demote these to unknown exactly once here.
        for job in self._job_store.list_active():
            if job.status in ("running", "needs_escalation"):
                self._job_store.update_status(job.job_id, "unknown")
                handle = self._lineage_store.get(job.collaboration_id)
                if handle is not None and handle.status == "active":
                    self._lineage_store.update_status(
                        job.collaboration_id,
                        "unknown",
                    )
```

- [ ] **Step 5.4: Add the decide tool-input scan policy**

Update `packages/plugins/codex-collaboration/server/consultation_safety.py`:

```python
DELEGATE_DECIDE_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"job_id", "request_id", "decision"}),
    content_fields=frozenset({"answers"}),
)
```

Add it to `_TOOL_POLICY_MAP`:

```python
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide": DELEGATE_DECIDE_POLICY,
```

- [ ] **Step 5.5: Re-run the targeted tests**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py -q
```

Expected: PASS.

- [ ] **Step 5.6: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/delegation_controller.py \
  packages/plugins/codex-collaboration/server/consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py
git commit -m "feat(t20260330-06): add decide recovery and safety policy"
```

---

### Task 6: Expose `codex.delegate.decide` Through MCP And Prove It End-To-End

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py`
- Modify: `packages/plugins/codex-collaboration/server/__init__.py`
- Test: `packages/plugins/codex-collaboration/tests/test_mcp_server.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`

- [ ] **Step 6.1: Write the failing MCP and integration tests**

Append to `packages/plugins/codex-collaboration/tests/test_mcp_server.py`:

```python
class FakeDelegationController:
    def __init__(self) -> None:
        self.startup_called = False
        self.last_decide_args: dict[str, object] | None = None

    def recover_startup(self) -> None:
        self.startup_called = True

    def start(self, **kwargs: object) -> object:
        from server.models import DelegationJob

        return DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="abc123",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="completed",
        )

    def decide(
        self,
        *,
        job_id: str,
        request_id: str,
        decision: str,
        answers: dict[str, tuple[str, ...]] | None = None,
    ) -> object:
        from server.models import DelegationDecisionResult, DelegationJob

        self.last_decide_args = {
            "job_id": job_id,
            "request_id": request_id,
            "decision": decision,
            "answers": answers,
        }
        return DelegationDecisionResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="pending",
                status="completed",
            ),
            decision=decision,
            resumed=(decision == "approve"),
        )


def test_delegate_decide_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.decide" in tool_names


def test_handle_tools_call_delegate_decide() -> None:
    controller = FakeDelegationController()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": "job-1",
                    "request_id": "req-1",
                    "decision": "approve",
                    "answers": {"q1": {"answers": ["yes"]}},
                },
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["decision"] == "approve"
    assert payload["resumed"] is True
    assert controller.last_decide_args == {
        "job_id": "job-1",
        "request_id": "req-1",
        "decision": "approve",
        "answers": {"q1": ("yes",)},
    }
```

Append to `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`:

```python
def test_delegate_decide_approve_end_to_end_through_mcp_dispatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, pending_request_store, journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["job"]["status"] == "needs_escalation"

    controller = server._ensure_delegation_controller()
    entry = controller._runtime_registry.lookup(start_payload["job"]["runtime_id"])
    assert entry is not None
    stub = entry.session
    stub._server_requests = []
    stub._turn_result = TurnExecutionResult(
        turn_id="turn-stub-2",
        status="completed",
        agent_message="Follow-up done.",
        notifications=(),
    )

    decide_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": start_payload["job"]["job_id"],
                    "request_id": start_payload["pending_request"]["request_id"],
                    "decision": "approve",
                },
            },
        }
    )

    decide_payload = json.loads(decide_response["result"]["content"][0]["text"])
    assert decide_payload["decision"] == "approve"
    assert decide_payload["resumed"] is True
    assert decide_payload["job"]["status"] == "completed"


def test_delegate_decide_deny_end_to_end_through_mcp_dispatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, pending_request_store, journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])

    decide_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": start_payload["job"]["job_id"],
                    "request_id": start_payload["pending_request"]["request_id"],
                    "decision": "deny",
                },
            },
        }
    )

    decide_payload = json.loads(decide_response["result"]["content"][0]["text"])
    assert decide_payload["decision"] == "deny"
    assert decide_payload["resumed"] is False
    assert decide_payload["job"]["status"] == "failed"
```

- [ ] **Step 6.2: Run the new tests and verify they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py -q
```

Expected: FAIL because the tool is not yet registered or serialized.

- [ ] **Step 6.3: Add the MCP tool definition, dispatch, and public exports**

Update `packages/plugins/codex-collaboration/server/mcp_server.py` by adding this tool definition after `codex.delegate.start`:

```python
    {
        "name": "codex.delegate.decide",
        "description": "Resolve a live same-session delegation escalation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "request_id": {"type": "string"},
                "decision": {
                    "type": "string",
                    "enum": ["approve", "deny"],
                },
                "answers": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "answers": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["answers"],
                    },
                },
            },
            "required": ["job_id", "request_id", "decision"],
        },
    },
```

Add the dispatch branch:

```python
        if name == "codex.delegate.decide":
            from .models import DelegationDecisionResult

            controller = self._ensure_delegation_controller()
            raw_answers = arguments.get("answers")
            answers = None
            if isinstance(raw_answers, dict):
                normalized: dict[str, tuple[str, ...]] = {}
                for key, value in raw_answers.items():
                    if not isinstance(key, str) or not isinstance(value, dict):
                        continue
                    raw_list = value.get("answers", ())
                    if isinstance(raw_list, list) and all(isinstance(item, str) for item in raw_list):
                        normalized[key] = tuple(raw_list)
                answers = normalized

            result = controller.decide(
                job_id=arguments["job_id"],
                request_id=arguments["request_id"],
                decision=arguments["decision"],
                answers=answers,
            )
            if isinstance(result, DelegationDecisionResult):
                payload = {
                    "job": asdict(result.job),
                    "decision": result.decision,
                    "resumed": result.resumed,
                }
                if result.pending_request is not None:
                    payload["pending_request"] = asdict(result.pending_request)
                if result.agent_context is not None:
                    payload["agent_context"] = result.agent_context
                return payload
            return asdict(result)
```

Update `packages/plugins/codex-collaboration/server/__init__.py` exports:

```python
    DecisionRejectedResponse,
    DelegationDecisionResult,
```

- [ ] **Step 6.4: Re-run the targeted integration suite**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py -q
```

Expected: PASS.

- [ ] **Step 6.5: Run the broad package-local verification pass**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/ -q
ruff check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests
```

Expected:
- full package test suite passes
- `ruff check` passes with no new violations

If the broad suite exposes unrelated historical failures, stop and separate them from the T-06 slice before landing.

- [ ] **Step 6.6: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/mcp_server.py \
  packages/plugins/codex-collaboration/server/__init__.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "feat(t20260330-06): expose codex.delegate.decide through MCP"
```

---

## Risks And Known Deferrals

| Risk / Deferral | Why deferred | Trigger that reopens it |
|---|---|---|
| **Cross-session restart demotes active execution jobs to `unknown`.** | The opening slice is same-session only. Startup reconciliation closes unresolved decision journals and marks orphaned `running` / `needs_escalation` jobs `unknown` instead of preserving an unresolvable zombie state. | `codex.delegate.poll` or a later restart/inspection slice. |
| **Follow-up execution turns are still not inspectable by callers.** | This slice resolves a known escalation directly; it does not add polling or history surfaces. | `codex.delegate.poll`. |
| **No discard action.** | Deny is the only terminal non-approve decision in the opening slice. | If the user needs “keep artifacts but stop now” without classifying the job as failed. |
| **Request-user-input answers are injected through the follow-up prompt, not replayed to the old wire request.** | This preserves the design lock that decide is plugin-side, not wire replay. | If the App Server later requires first-class answer replay to preserve correctness. |
| **`codex.delegate.start` still has no dedicated PreToolUse scan policy in this packet.** | This plan adds `DELEGATE_DECIDE_POLICY` only. The existing start-surface guard gap predates T-06 and is intentionally left out of scope here to avoid scope creep. | A separate hardening pass on the execution-domain hook guard. |
| **The existing untracked plan file `docs/plans/2026-04-19-t05-pending-request-capture-slice.md` can still be staged accidentally.** | It predates this slice and remains outside the repo index. | Any commit step in this plan — check `git status` before `git add`. |

---

## Final Check

Before handing this to an implementation worker, skim the plan and confirm:

1. Every step names an exact file path.
2. The only new public tool is `codex.delegate.decide`.
3. No task quietly adds `poll`, `promote`, `/delegate`, artifact hash, rollback, or worktree cleanup.
4. The success contract is consistent everywhere:
   - approve -> `DelegationDecisionResult(resumed=True, pending_request optional)`
   - deny -> `DelegationDecisionResult(resumed=False, job.status="failed")`
   - invalid attempt -> `DecisionRejectedResponse`
