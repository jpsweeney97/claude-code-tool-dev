# Packet 1 — Phase F: Worker

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 15–16
**Scope:** `_WorkerRunner` + `_execute_live_turn` sentinel catch scaffolding. Handler rewrite — all 6 `_WorkerTerminalBranchSignal(reason=...)` raise sites: park, completion, unknown, timeout-interrupt-succeeded, internal-abort, worker-failure.
**Landing invariant:** `_execute_live_turn` runs under the worker thread; handler paths emit correct sentinels at exactly 6 spec-documented raise sites. Sentinel count MUST remain 6 at commit time.
**Note:** Several integration-test bodies in this phase are `pass` stubs under concrete docstrings. See manifest §Pre-Execution Notes for implementer contract.

---

## Task 15: Worker runner + `_execute_live_turn` sentinel catch skeleton

**Files:**
- Create: `packages/plugins/codex-collaboration/server/worker_runner.py`
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (extend `_execute_live_turn` with sentinel catch + worker spawn)
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (extend `_load_or_materialize_inspection` tuple)
- Test: `packages/plugins/codex-collaboration/tests/test_worker_runner.py` (new)

**Spec anchor:** §Worker terminal-branch signaling primitive (lines ~489-567). §Worker sequences (spec lines ~665-719).

This task introduces the **worker thread model**. The worker runs `_execute_live_turn` on a separate thread; the main thread calls `wait_for_parked`. The handler's logic (park vs sync-respond vs sentinel raises) lands in Task 16; this task delivers the thread plumbing and the sentinel catch.

- [ ] **Step 15.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_worker_runner.py`:

```python
"""Packet 1: _WorkerRunner thread entry + _execute_live_turn sentinel catch."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from server.delegation_controller import (
    _WorkerTerminalBranchSignal,
)
from server.worker_runner import _WorkerRunner


def test_worker_runner_exists() -> None:
    assert _WorkerRunner is not None


def test_worker_runner_translates_return_to_announce_parked(
    worker_runner_fixture,
) -> None:
    """Happy-path return: worker_runner's `_execute_live_turn` runs; worker
    reached announce_parked within the handler; no exception; thread exits."""
    # Arrange a controller whose _execute_live_turn returns a DelegationJob
    # or DelegationEscalation synchronously (simulating Packet 1's new model).
    # The runner's job is to catch unexpected exceptions and fire
    # announce_worker_failed.
    pass  # Full integration tests land in Task 17.


def test_execute_live_turn_catches_worker_terminal_branch_signal_post_decide(
    delegation_controller, monkeypatch
) -> None:
    """When the handler raises _WorkerTerminalBranchSignal with a post-decide
    reason, _execute_live_turn returns the stored DelegationJob WITHOUT
    calling _finalize_turn.
    """
    # Use a monkeypatched _server_request_handler that raises the sentinel.
    # Assert _finalize_turn was not invoked (spy).
    pass  # Full coverage in Task 17.


def test_execute_live_turn_reraises_sentinel_as_delegation_start_error_for_pre_capture(
    delegation_controller, monkeypatch
) -> None:
    """Pre-capture sentinel reason 'unknown_kind_interrupt_transport_failure'
    re-raises as DelegationStartError(reason=same) with cause=None.
    """
    pass  # Full coverage in Task 17.


def test_execute_live_turn_sentinel_does_not_double_call_cleanup(
    delegation_controller, monkeypatch
) -> None:
    """_mark_execution_unknown_and_cleanup must not fire from
    _execute_live_turn's sentinel catch — the handler already called it
    (or the inline canceled-cleanup analog).
    """
    pass  # Full coverage in Task 17.


def test_load_or_materialize_inspection_tuple_admits_canceled() -> None:
    """_load_or_materialize_inspection's terminal guard at :873 must admit
    'canceled' (fourth literal) and return None for canceled (no artifacts).
    """
    from server.delegation_controller import DelegationController
    # Unit-test the tuple via introspection of the method's source or
    # by exercising the code path with a canceled job.
    pass  # Exercise via integration fixture below.
```

The above has placeholder bodies for tests that require full worker infrastructure (arriving in Task 16). For Task 15, focus on the testable surface: the sentinel catch scaffolding and the `_load_or_materialize_inspection` tuple expansion. Write a concrete test for just those:

```python
def test_load_or_materialize_inspection_admits_canceled_job(
    delegation_controller,
    simple_job_factory,
) -> None:
    job = simple_job_factory(status="canceled", promotion_state=None)
    result = delegation_controller._load_or_materialize_inspection(job)
    assert result is None


def test_load_or_materialize_inspection_does_not_materialize_for_canceled(
    delegation_controller,
    simple_job_factory,
    artifact_store_spy,
) -> None:
    job = simple_job_factory(status="canceled", promotion_state=None)
    delegation_controller._load_or_materialize_inspection(job)
    assert not artifact_store_spy.materialize_snapshot.called
    assert not artifact_store_spy.reconstruct_from_artifacts.called
```

- [ ] **Step 15.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_worker_runner.py -v -k "load_or_materialize"
```

Expected: FAIL — canceled is not in the tuple guard.

- [ ] **Step 15.3: Create `_WorkerRunner` skeleton in `worker_runner.py`**

Create `packages/plugins/codex-collaboration/server/worker_runner.py`:

```python
"""Worker thread runner for Packet 1's deferred-approval model.

Packet 1 (T-20260423-02). One worker thread per deferred-approval turn.
The worker:
  - Invokes _execute_live_turn (which, post-Task 16, contains the
    rewritten handler that parks on the registry).
  - Translates a normal return (DelegationJob | DelegationEscalation) into
    the appropriate announce_* signal on the capture-ready channel.
  - Translates an unhandled exception into announce_worker_failed.

The worker owns IO-1 (exclusive session ownership) + IO-3 (single-writer
to pending_request_store + its own DelegationJob row).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from .resolution_registry import ResolutionRegistry

if TYPE_CHECKING:
    from .delegation_controller import DelegationController

logger = logging.getLogger(__name__)


class _WorkerRunner:
    """Entry point for the worker thread. Instantiated by DelegationController.start,
    spawned once the committed-start phase completes. The thread's target is
    `self.run`.
    """

    def __init__(
        self,
        *,
        controller: "DelegationController",
        registry: ResolutionRegistry,
        job_id: str,
        collaboration_id: str,
        runtime_id: str,
        worktree_path: Path,
        prompt_text: str,
    ) -> None:
        self._controller = controller
        self._registry = registry
        self._job_id = job_id
        self._collaboration_id = collaboration_id
        self._runtime_id = runtime_id
        self._worktree_path = worktree_path
        self._prompt_text = prompt_text

    def run(self) -> None:
        """Thread target. Runs _execute_live_turn and converts its outcome
        into the appropriate capture-ready signal. Never raises on the
        thread — unhandled exceptions fire announce_worker_failed.
        """
        try:
            result = self._controller._execute_live_turn(
                job_id=self._job_id,
                collaboration_id=self._collaboration_id,
                runtime_id=self._runtime_id,
                worktree_path=self._worktree_path,
                prompt_text=self._prompt_text,
            )
        except Exception as exc:
            logger.exception(
                "Worker runner: unhandled exception in _execute_live_turn"
            )
            self._registry.announce_worker_failed(self._job_id, error=exc)
            return

        # Normal return — translate result into a capture-ready signal IF
        # the handler did not already signal (capture-ready channel is
        # idempotent / resolved-once, so late signals are warning no-ops).
        # Per spec §Capture-ready handshake, the handler emits:
        #   - announce_parked before registry.wait() if it parked
        #   - announce_turn_terminal_without_escalation before return for
        #     kind="unknown"
        # If neither fired, the turn completed without capture.
        #
        # At this layer we only handle the "turn completed without capture"
        # fallthrough — the handler itself is responsible for the three
        # signal cases that happen during the turn.
        self._registry.announce_turn_completed_empty(self._job_id)


def spawn_worker(
    *,
    controller: "DelegationController",
    registry: ResolutionRegistry,
    job_id: str,
    collaboration_id: str,
    runtime_id: str,
    worktree_path: Path,
    prompt_text: str,
) -> threading.Thread:
    """Helper: construct a _WorkerRunner and start a daemon thread."""
    runner = _WorkerRunner(
        controller=controller,
        registry=registry,
        job_id=job_id,
        collaboration_id=collaboration_id,
        runtime_id=runtime_id,
        worktree_path=worktree_path,
        prompt_text=prompt_text,
    )
    thread = threading.Thread(
        target=runner.run, name=f"delegation-worker-{job_id}", daemon=True
    )
    thread.start()
    return thread
```

- [ ] **Step 15.4: Expand `_load_or_materialize_inspection` terminal-status tuple to admit `"canceled"`**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py:873`:

```python
# Before:
# if job.status not in ("completed", "failed", "unknown"):
#     return None

# After:
if job.status not in ("completed", "failed", "canceled", "unknown"):
    return None
# Canceled jobs have no artifacts — the worker was interrupted before
# they could be produced. Return None immediately without calling
# materialize_snapshot / reconstruct_from_artifacts.
if job.status == "canceled":
    return None
```

- [ ] **Step 15.5: Add `_WorkerTerminalBranchSignal` catch clause in `_execute_live_turn`**

Edit `_execute_live_turn` at `delegation_controller.py:722-757`. Replace the single `try/except Exception` around `run_execution_turn` with the sentinel-aware block:

```python
try:
    turn_result = entry.session.run_execution_turn(
        thread_id=entry.thread_id,
        prompt_text=prompt_text,
        sandbox_policy=build_workspace_write_sandbox_policy(worktree_path),
        approval_policy=self._approval_policy,
        server_request_handler=_server_request_handler,
    )
except _WorkerTerminalBranchSignal as signal:
    # Handler already performed branch cleanup. Do NOT call
    # _mark_execution_unknown_and_cleanup (that would double-clean).
    if signal.reason == "unknown_kind_interrupt_transport_failure":
        # Pre-capture terminal transport failure. Surface to main thread
        # via DelegationStartError; the worker runner's generic
        # `except Exception` will catch and fire announce_worker_failed
        # with the explicit reason preserved.
        raise DelegationStartError(
            reason="unknown_kind_interrupt_transport_failure",
            cause=None,
        )
    # Post-decide / post-Parked branches. Job is already in its terminal
    # state. Return the stored job — _finalize_turn is BYPASSED because
    # captured_request and turn_result would be stale / meaningless
    # post-terminalization.
    stored = self._job_store.get(job_id)
    assert stored is not None, (
        f"_execute_live_turn sentinel-catch invariant: job_id={job_id!r} "
        f"stored record missing after sentinel reason={signal.reason!r}"
    )
    return stored
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

- [ ] **Step 15.6: Run focused tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_worker_runner.py::test_load_or_materialize_inspection_admits_canceled_job packages/plugins/codex-collaboration/tests/test_worker_runner.py::test_load_or_materialize_inspection_does_not_materialize_for_canceled -v
```

Expected: PASS.

- [ ] **Step 15.7: Verify the full test suite compiles and existing tests still pass**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -x 2>&1 | tail -50
```

Expected: PASS (with some tests that depend on the un-rewritten handler still green because handler behavior hasn't changed yet).

- [ ] **Step 15.8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/worker_runner.py packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_worker_runner.py
git commit -m "$(cat <<'EOF'
feat(delegate): add _WorkerRunner + sentinel catch scaffolding (T-20260423-02 Task 15)

New file worker_runner.py houses the thread-entry wrapper that converts
_execute_live_turn's return value or unhandled exception into the
appropriate registry capture-ready signal. _execute_live_turn gains the
_WorkerTerminalBranchSignal except clause — pre-capture sentinel
("unknown_kind_interrupt_transport_failure") re-raises as
DelegationStartError; post-decide sentinels return the stored DelegationJob
with _finalize_turn bypassed (job already terminal). Handler raise-sites
land in Task 16.

_load_or_materialize_inspection's terminal tuple expanded to admit
"canceled" and returns None early (no artifacts to materialize).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Handler rewrite — park / sentinel raises across all 6 branches

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (rewrite `_server_request_handler` in `_execute_live_turn`)
- Test: `packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py` (new)

**Spec anchor:** §Worker sequence (lines ~665-719). §Timeout path (cancel-capable kind) (lines ~1010-1093). §Timeout path (non-cancel-capable kind) (lines ~1095-1180). §Dispatch failure path. §Internal abort coordination (lines ~347-438). §Worker terminal-branch signaling primitive — all 6 raise sites.

**Scope:** This is the LARGEST task in the plan. The handler must correctly implement all 6 sentinel raise sites (table in spec §Worker terminal-branch signaling primitive). Each branch requires distinct cleanup + durable writes + sentinel raise.

Because the branches share a common skeleton (register + wait + sequence on wake) but diverge by resolution kind, the handler is structured as:

1. **Capture + classify** (parse → kind check → decide if parkable)
2. **If unknown-kind**: persist audit record, interrupt turn, signal `announce_turn_terminal_without_escalation`, return None from handler (turn exits cleanly; worker runner returns)
3. **If unknown-kind + interrupt fails**: persist audit record, call cleanup, raise `_WorkerTerminalBranchSignal(reason="unknown_kind_interrupt_transport_failure")`
4. **If parkable**: create request record, update parked_request_id, transition to needs_escalation, register registry entry, announce_parked, wait on registry
5. **On wake, branch on resolution type:**
   - `DecisionResolution` with `is_timeout=False` (operator decide): respond → record_response_dispatch → mark_resolved OR record_dispatch_failure → sentinel raise on failure
   - `DecisionResolution` with `is_timeout=True` (timeout): re-read kind from store, branch on kind:
     - `command_approval` / `file_change`: respond(cancel) → record_timeout(succeeded) or record_timeout(failed) + sentinel raise
     - `request_user_input`: interrupt_turn → record_timeout(interrupt_succeeded) + sentinel raise `timeout_interrupt_succeeded`
       OR record_timeout(interrupt_failed with interrupt_error) + sentinel raise `timeout_interrupt_failed`
   - `InternalAbort`: execute internal-abort sequence + sentinel raise `internal_abort`

The handler's logic is linear but long. The full pseudocode is in the spec subsections referenced above — copy the logic faithfully.

Given the length, this task is split into sub-steps by branch. Each sub-step has its own test.

- [ ] **Step 16.1: Write the failing test covering happy-path decide-success**

Create `packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py`:

```python
"""Packet 1: Handler branches for decide-success / timeout / internal-abort / dispatch-failure."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

# Integration fixtures provided by conftest.py — see existing test_delegation_controller.py
# for patterns.


def test_happy_path_decide_approve_success(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """Worker parks → operator decides approve → session.respond succeeds →
    mark_resolved + record_response_dispatch → handler returns None → turn
    completes naturally → _finalize_turn runs with request_snapshot.status
    = 'resolved' and terminal guard sets final_status='completed'.
    """
    # Arrange the App Server stub to emit a command_approval server-request
    # notification mid-turn, then turn/completed after the worker respond()s.
    # Kick off start() on a thread, wait for the Parked signal, call decide,
    # assert poll() reaches status='completed'.
    pass  # flesh out with stubs (large)


def test_timeout_cancel_dispatch_succeeded_for_file_change(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """file_change captured → no operator decide → timer fires →
    session.respond(cancel) succeeds → record_timeout(dispatch_result="succeeded")
    → handler returns None → turn completes naturally → _finalize_turn
    reads request_snapshot.status='canceled' and sets final_status='canceled'.
    """
    pass


def test_timeout_cancel_dispatch_failed_for_command_approval(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """command_approval captured → timer fires → session.respond(cancel)
    raises BrokenPipeError → record_timeout(dispatch_result="failed",
    dispatch_error=<sanitized>) → _mark_execution_unknown_and_cleanup →
    sentinel _WorkerTerminalBranchSignal(reason="timeout_cancel_dispatch_failed") →
    _execute_live_turn bypasses _finalize_turn → poll returns
    job.status='unknown' (OB-1: transport fail = unknown).
    """
    pass


def test_timeout_interrupt_succeeded_for_request_user_input(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """request_user_input captured → timer fires → session.interrupt_turn
    succeeds → record_timeout(interrupt_error=None) → inline cancel-cleanup
    sequence (_persist_job_transition(canceled), _emit_terminal_outcome_if_needed,
    lineage completed, runtime release, session close) → sentinel
    _WorkerTerminalBranchSignal(reason="timeout_interrupt_succeeded") →
    _execute_live_turn bypasses _finalize_turn → poll returns
    job.status='canceled' (verified cancel via interrupt).
    """
    pass


def test_timeout_interrupt_failed_for_request_user_input(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """request_user_input captured → timer fires → session.interrupt_turn
    raises → record_timeout(interrupt_error=<sanitized>) →
    _mark_execution_unknown_and_cleanup → sentinel
    _WorkerTerminalBranchSignal(reason="timeout_interrupt_failed") →
    _execute_live_turn bypasses _finalize_turn → poll returns
    job.status='unknown' (OB-1: unverified cancel = unknown).
    """
    pass


def test_dispatch_failure_on_operator_decide(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """Operator decides approve → session.respond raises BrokenPipeError →
    record_dispatch_failure(action="approve", payload={"decision": "accept"},
    dispatch_error=<sanitized>) → _mark_execution_unknown_and_cleanup →
    sentinel _WorkerTerminalBranchSignal(reason="dispatch_failed") →
    _execute_live_turn bypasses _finalize_turn → poll returns
    job.status='unknown' (OB-1: transport fail = unknown; request.status='canceled').
    """
    pass


def test_internal_abort_on_unknown_kind_poll_projection_abort(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """Parkable capture, worker parks. Main thread's poll observes an
    UnknownKindInEscalationProjection (through tampering or corruption),
    calls signal_internal_abort → worker wakes on InternalAbort →
    record_internal_abort → sentinel _WorkerTerminalBranchSignal(reason="internal_abort")
    → _execute_live_turn bypasses _finalize_turn → poll returns
    job.status='unknown'; PendingServerRequest.internal_abort_reason is set.
    """
    pass


def test_unknown_kind_parse_failure_terminalizes_unknown(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """Parse failure → PendingServerRequest(kind='unknown') created →
    session.interrupt_turn succeeds → _persist_job_transition(unknown) →
    announce_turn_terminal_without_escalation → handler returns None
    from the turn → worker exits cleanly. start() returns a plain
    DelegationJob(status='unknown') per TurnTerminalWithoutEscalation branch.
    """
    pass


def test_unknown_kind_interrupt_transport_failure(
    delegation_controller_fixture,
    app_server_runtime_stub,
) -> None:
    """Parse failure → PendingServerRequest(kind='unknown') created →
    session.interrupt_turn raises BrokenPipeError → cleanup →
    sentinel _WorkerTerminalBranchSignal(reason="unknown_kind_interrupt_transport_failure")
    → _execute_live_turn re-raises as DelegationStartError(reason=same, cause=None)
    → worker runner catches generic Exception, fires announce_worker_failed →
    main-thread WorkerFailed handler sees DelegationStartError and preserves
    the reason → start() raises DelegationStartError(reason=same).
    """
    pass
```

- [ ] **Step 16.2: Run failing tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py -v
```

Expected: FAIL / skipped placeholders — the handler logic doesn't branch this way yet.

- [ ] **Step 16.3: Rewrite `_server_request_handler` with the new branch logic**

Edit `_server_request_handler` inside `_execute_live_turn` at `delegation_controller.py:650-720`. Replace the full function. The new logic:

```python
def _server_request_handler(
    message: dict[str, Any],
) -> dict[str, Any] | None:
    nonlocal \
        captured_request, \
        interrupted_by_unknown, \
        captured_request_parse_failed
    try:
        parsed = parse_pending_server_request(
            message,
            runtime_id=runtime_id,
            collaboration_id=collaboration_id,
        )
    except Exception:
        # --- Unknown-kind parse failure branch ---
        logger.warning(
            "Server request parse failed; creating minimal causal record. "
            "Wire id=%r, method=%r",
            message.get("id"),
            message.get("method", ""),
            exc_info=True,
        )
        wire_id = message.get("id")
        wire_method = message.get("method", "")
        minimal = PendingServerRequest(
            request_id=str(wire_id) if wire_id is not None else self._uuid_factory(),
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
        interrupt_entry = self._runtime_registry.lookup(runtime_id)
        try:
            if interrupt_entry is not None:
                interrupt_entry.session.interrupt_turn(
                    thread_id=interrupt_entry.thread_id,
                    turn_id=None,
                )
        except Exception as interrupt_exc:
            # Unknown-kind interrupt transport failure — pre-capture raise site.
            self._mark_execution_unknown_and_cleanup(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                entry=interrupt_entry,
            )
            raise _WorkerTerminalBranchSignal(
                reason="unknown_kind_interrupt_transport_failure"
            ) from interrupt_exc
        # Interrupt succeeded. Persist terminal unknown and signal.
        self._persist_job_transition(job_id, "unknown")
        self._emit_terminal_outcome_if_needed(job_id)
        try:
            self._lineage_store.update_status(collaboration_id, "unknown")
        except Exception:
            logger.exception("lineage_store.update_status failed")
        registry.announce_turn_terminal_without_escalation(
            job_id,
            status="unknown",
            reason="unknown_kind_parse_failure",
            request_id=minimal.request_id,
        )
        return None  # suppress auto-respond; turn loop exits post-interrupt

    if (
        parsed.kind not in _CANCEL_CAPABLE_KINDS
        and parsed.kind not in _KNOWN_DENIAL_KINDS
    ):
        # Kind outside the Packet 1 parkable/denial set — same old interrupt path.
        # (Kept for defense-in-depth; spec's classification assumes all server-
        # request kinds are one of four literals.)
        if captured_request is None:
            self._pending_request_store.create(parsed)
            captured_request = parsed
        interrupted_by_unknown = True
        interrupt_entry = self._runtime_registry.lookup(runtime_id)
        if interrupt_entry is not None:
            interrupt_entry.session.interrupt_turn(
                thread_id=interrupt_entry.thread_id,
                turn_id=None,
            )
        return None

    # --- Parkable capture ---
    if captured_request is None:
        self._pending_request_store.create(parsed)
        captured_request = parsed

    # Durable writes before handshake signal (spec §Worker sequence):
    self._job_store.update_parked_request(job_id, parsed.request_id)
    self._persist_job_transition(job_id, "needs_escalation")
    registry.register(
        parsed.request_id,
        job_id=job_id,
        timeout_seconds=_APPROVAL_OPERATOR_WINDOW_SECONDS,
    )
    registry.announce_parked(job_id, request_id=parsed.request_id)

    # Block until operator decide, timer, or internal abort.
    resolution = registry.wait(parsed.request_id)

    if isinstance(resolution, InternalAbort):
        # --- Internal abort branch ---
        # Spec §Internal abort coordination — worker wake sequence.
        now = self._journal.timestamp()
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
                operation="approval_resolution",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=now,
                repo_root=self._repo_root_for_journal(job_id),
                job_id=job_id,
                request_id=parsed.request_id,
                decision=None,  # non-operator origin
            ),
            session_id=self._session_id,
        )
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
                operation="approval_resolution",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=self._journal.timestamp(),
                repo_root=self._repo_root_for_journal(job_id),
                job_id=job_id,
                request_id=parsed.request_id,
                runtime_id=runtime_id,
                codex_thread_id=entry.thread_id,
                decision=None,
            ),
            session_id=self._session_id,
        )
        self._pending_request_store.record_internal_abort(
            parsed.request_id, reason=resolution.reason
        )
        self._job_store.update_parked_request(job_id, None)
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
                operation="approval_resolution",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=self._journal.timestamp(),
                repo_root=self._repo_root_for_journal(job_id),
                job_id=job_id,
                request_id=parsed.request_id,
                completion_origin="worker_completed",
            ),
            session_id=self._session_id,
        )
        try:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="system",
                    action="internal_abort",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                    request_id=parsed.request_id,
                )
            )
        except Exception:
            logger.warning("audit internal_abort append failed", exc_info=True)
        registry.discard(parsed.request_id)
        self._mark_execution_unknown_and_cleanup(
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            entry=entry,
        )
        raise _WorkerTerminalBranchSignal(reason="internal_abort")

    # resolution is DecisionResolution from here down.
    if resolution.is_timeout:
        # --- Timeout branches ---
        # _handle_timeout_wake returns True iff the cancel-capable-success
        # sub-branch ran (handler returns None so the turn continues to
        # turn/completed; _finalize_turn terminal guard then maps the
        # canceled snapshot to final_status="canceled"). All other
        # sub-branches raise _WorkerTerminalBranchSignal.
        continue_turn = self._handle_timeout_wake(
            entry=entry,
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            request=parsed,
            registry=registry,
        )
        if continue_turn:
            return None
        raise AssertionError(
            "_handle_timeout_wake invariant: must return True or raise "
            "_WorkerTerminalBranchSignal; neither happened"
        )

    # --- Operator decide branch ---
    decision_action = resolution.payload.get("resolution_action", "approve")
    response_payload = resolution.payload.get("response_payload", {})
    self._job_store.update_status_and_promotion(job_id, status="running", promotion_state=None)
    self._journal.write_phase(
        OperationJournalEntry(
            idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
            operation="approval_resolution",
            phase="dispatched",
            collaboration_id=collaboration_id,
            created_at=self._journal.timestamp(),
            repo_root=self._repo_root_for_journal(job_id),
            job_id=job_id,
            request_id=parsed.request_id,
            runtime_id=runtime_id,
            codex_thread_id=entry.thread_id,
            decision=decision_action,
        ),
        session_id=self._session_id,
    )
    dispatch_at = self._journal.timestamp()
    try:
        entry.session.respond(parsed.request_id, response_payload)
    except Exception as respond_exc:
        # Dispatch-failure branch
        self._pending_request_store.record_dispatch_failure(
            parsed.request_id,
            action=decision_action,
            payload=response_payload,
            dispatch_at=dispatch_at,
            dispatch_error=_sanitize_error_string(respond_exc),
        )
        self._job_store.update_parked_request(job_id, None)
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
                operation="approval_resolution",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=self._journal.timestamp(),
                repo_root=self._repo_root_for_journal(job_id),
                job_id=job_id,
                request_id=parsed.request_id,
                completion_origin="worker_completed",
            ),
            session_id=self._session_id,
        )
        try:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="system",
                    action="dispatch_failed",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                    request_id=parsed.request_id,
                )
            )
        except Exception:
            logger.warning("audit dispatch_failed append failed", exc_info=True)
        registry.discard(parsed.request_id)
        self._mark_execution_unknown_and_cleanup(
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            entry=entry,
        )
        raise _WorkerTerminalBranchSignal(reason="dispatch_failed") from respond_exc

    # Dispatch succeeded.
    self._pending_request_store.record_response_dispatch(
        parsed.request_id,
        action=decision_action,
        payload=response_payload,
        dispatch_at=dispatch_at,
    )
    self._pending_request_store.mark_resolved(
        parsed.request_id, resolved_at=self._journal.timestamp()
    )
    self._job_store.update_parked_request(job_id, None)
    self._journal.write_phase(
        OperationJournalEntry(
            idempotency_key=f"approval_resolution:{job_id}:{parsed.request_id}",
            operation="approval_resolution",
            phase="completed",
            collaboration_id=collaboration_id,
            created_at=self._journal.timestamp(),
            repo_root=self._repo_root_for_journal(job_id),
            job_id=job_id,
            request_id=parsed.request_id,
            completion_origin="worker_completed",
        ),
        session_id=self._session_id,
    )
    registry.discard(parsed.request_id)
    return None  # let the turn continue to turn/completed naturally
```

Add a helper method `_handle_timeout_wake` on the controller (module-scope function or instance method):

```python
def _handle_timeout_wake(
    self,
    *,
    entry: ExecutionRuntimeEntry,
    job_id: str,
    collaboration_id: str,
    runtime_id: str,
    request: PendingServerRequest,
    registry: ResolutionRegistry,
) -> bool:
    """Handle the worker's wake from the registry timer.

    Kind-sensitive dispatch per spec §Kind-sensitive timeout dispatch:
      - command_approval / file_change (cancel-capable) → respond({"decision": "cancel"})
      - request_user_input (non-cancel-capable) → session.interrupt_turn(...) (no respond)

    Return contract:
      - Returns True on cancel-capable-success sub-branch (caller's handler
        returns None so the turn continues to turn/completed; _finalize_turn's
        Captured-Request Terminal Guard maps the canceled snapshot).
      - Raises _WorkerTerminalBranchSignal with a branch-specific reason on
        every other sub-branch (cancel-dispatch-failed, interrupt-succeeded,
        interrupt-failed). The sentinel bypass fires; _finalize_turn is NOT
        invoked.
    """
    now = self._journal.timestamp()
    self._journal.write_phase(
        OperationJournalEntry(
            idempotency_key=f"approval_resolution:{job_id}:{request.request_id}",
            operation="approval_resolution",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=now,
            repo_root=self._repo_root_for_journal(job_id),
            job_id=job_id,
            request_id=request.request_id,
            decision=None,  # non-operator
        ),
        session_id=self._session_id,
    )
    self._job_store.update_status_and_promotion(
        job_id, status="running", promotion_state=None
    )
    self._journal.write_phase(
        OperationJournalEntry(
            idempotency_key=f"approval_resolution:{job_id}:{request.request_id}",
            operation="approval_resolution",
            phase="dispatched",
            collaboration_id=collaboration_id,
            created_at=self._journal.timestamp(),
            repo_root=self._repo_root_for_journal(job_id),
            job_id=job_id,
            request_id=request.request_id,
            runtime_id=runtime_id,
            codex_thread_id=entry.thread_id,
            decision=None,
        ),
        session_id=self._session_id,
    )

    if request.kind in ("command_approval", "file_change"):
        # Cancel-capable: respond({"decision": "cancel"}).
        dispatch_at = self._journal.timestamp()
        try:
            entry.session.respond(request.request_id, {"decision": "cancel"})
        except Exception as respond_exc:
            self._pending_request_store.record_timeout(
                request.request_id,
                response_payload={"decision": "cancel"},
                response_dispatch_at=dispatch_at,
                dispatch_result="failed",
                dispatch_error=_sanitize_error_string(respond_exc),
            )
            self._job_store.update_parked_request(job_id, None)
            self._write_completion_and_audit_timeout(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                request_id=request.request_id,
                dispatch_result="failed",
                dispatch_error=_sanitize_error_string(respond_exc),
            )
            registry.discard(request.request_id)
            self._mark_execution_unknown_and_cleanup(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                entry=entry,
            )
            raise _WorkerTerminalBranchSignal(
                reason="timeout_cancel_dispatch_failed"
            ) from respond_exc
        # Success: record and let turn continue to turn/completed.
        self._pending_request_store.record_timeout(
            request.request_id,
            response_payload={"decision": "cancel"},
            response_dispatch_at=dispatch_at,
            dispatch_result="succeeded",
            dispatch_error=None,
        )
        self._job_store.update_parked_request(job_id, None)
        self._write_completion_and_audit_timeout(
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            request_id=request.request_id,
            dispatch_result="succeeded",
            dispatch_error=None,
        )
        registry.discard(request.request_id)
        # Spec §Timeout path (cancel-capable, success sub-branch): handler
        # returns None to let the turn continue to turn/completed;
        # _finalize_turn's Captured-Request Terminal Guard maps the
        # canceled snapshot to final_status="canceled".
        return True  # caller returns None from the handler

    if request.kind == "request_user_input":
        # Non-cancel-capable: interrupt_turn only. No respond.
        try:
            entry.session.interrupt_turn(
                thread_id=entry.thread_id, turn_id=None
            )
        except Exception as interrupt_exc:
            self._pending_request_store.record_timeout(
                request.request_id,
                response_payload=None,
                response_dispatch_at=None,
                dispatch_result=None,
                dispatch_error=None,
                interrupt_error=_sanitize_error_string(interrupt_exc),
            )
            self._job_store.update_parked_request(job_id, None)
            self._write_completion_and_audit_timeout(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                request_id=request.request_id,
                dispatch_result=None,
                dispatch_error=_sanitize_error_string(interrupt_exc),
            )
            registry.discard(request.request_id)
            self._mark_execution_unknown_and_cleanup(
                job_id=job_id,
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                entry=entry,
            )
            raise _WorkerTerminalBranchSignal(
                reason="timeout_interrupt_failed"
            ) from interrupt_exc
        # Interrupt succeeded.
        self._pending_request_store.record_timeout(
            request.request_id,
            response_payload=None,
            response_dispatch_at=None,
            dispatch_result=None,
            dispatch_error=None,
            interrupt_error=None,
        )
        self._job_store.update_parked_request(job_id, None)
        self._write_completion_and_audit_timeout(
            job_id=job_id,
            collaboration_id=collaboration_id,
            runtime_id=runtime_id,
            request_id=request.request_id,
            dispatch_result=None,
            dispatch_error=None,
        )
        registry.discard(request.request_id)
        # Inline cancel-cleanup sequence (NOT _mark_execution_unknown_and_cleanup):
        self._persist_job_transition(job_id, "canceled")
        self._emit_terminal_outcome_if_needed(job_id)
        try:
            self._lineage_store.update_status(collaboration_id, "completed")
        except Exception:
            logger.exception("lineage_store.update_status on cancel failed")
        try:
            self._runtime_registry.release(runtime_id)
        except Exception:
            logger.exception("runtime_registry.release on cancel failed")
        try:
            entry.session.close()
        except Exception:
            logger.exception("entry.session.close on cancel failed")
        raise _WorkerTerminalBranchSignal(reason="timeout_interrupt_succeeded")

    # Any other kind should not reach here (captured_request.kind filtered
    # upstream). Raise defensively.
    raise AssertionError(
        f"_handle_timeout_wake: unexpected kind={request.kind!r}"
    )


def _write_completion_and_audit_timeout(
    self,
    *,
    job_id: str,
    collaboration_id: str,
    runtime_id: str,
    request_id: str,
    dispatch_result: str | None,
    dispatch_error: str | None,
) -> None:
    self._journal.write_phase(
        OperationJournalEntry(
            idempotency_key=f"approval_resolution:{job_id}:{request_id}",
            operation="approval_resolution",
            phase="completed",
            collaboration_id=collaboration_id,
            created_at=self._journal.timestamp(),
            repo_root=self._repo_root_for_journal(job_id),
            job_id=job_id,
            request_id=request_id,
            completion_origin="worker_completed",
        ),
        session_id=self._session_id,
    )
    try:
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="system",
                action="approval_timeout",
                collaboration_id=collaboration_id,
                runtime_id=runtime_id,
                job_id=job_id,
                request_id=request_id,
            )
        )
    except Exception:
        logger.warning("audit approval_timeout append failed", exc_info=True)
```

Add a helper `_repo_root_for_journal(job_id)` that resolves the lineage handle's repo_root for the journal record (the existing code does this inline — extract into a one-liner for reuse).

Also, update the post-timeout-success branch of the main handler: after `_handle_timeout_wake` returns (only on the cancel-capable-success sub-branch), the handler should `return None` to let the turn proceed to `turn/completed`. If `_handle_timeout_wake` raises, the sentinel propagates up.

```python
# Handler resumption after _handle_timeout_wake (cancel-capable-success only):
self._handle_timeout_wake(...)  # returns on cancel-capable-success, raises otherwise
return None
```

(Adjust the handler code structure above to call `_handle_timeout_wake` as a method and fall through to `return None` only when it returns — otherwise the sentinel propagates.)

- [ ] **Step 16.4: Wire the registry into `_execute_live_turn`**

At the top of `_execute_live_turn`, add:

```python
registry = self._registry  # instance-level ResolutionRegistry, init'd in __init__
```

Update `DelegationController.__init__` to accept/create a `ResolutionRegistry`:

```python
self._registry: ResolutionRegistry = ResolutionRegistry()
```

Add `_APPROVAL_OPERATOR_WINDOW_SECONDS` module-level constant:

```python
_APPROVAL_OPERATOR_WINDOW_SECONDS = 900  # default, configurable via env later
```

- [ ] **Step 16.5: Run integration tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py -v
```

Expected: progressively more PASS as each test body is fleshed out with stubs.

- [ ] **Step 16.6: Run full suite; fix any regressions**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -x 2>&1 | tail -80
```

Expected: existing tests pass. New handler behavior is only exercised by the new integration tests.

- [ ] **Step 16.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py
git commit -m "$(cat <<'EOF'
feat(delegate): rewrite _server_request_handler for async-decide model (T-20260423-02 Task 16)

Handler now parks parkable requests on the registry, waits for operator
decide / timeout / internal abort, and dispatches 6 sentinel raise sites
per spec §Worker terminal-branch signaling primitive:
  - internal_abort
  - dispatch_failed (operator decide, respond() raises)
  - timeout_cancel_dispatch_failed (cancel-capable kinds, respond() raises)
  - timeout_interrupt_failed (non-cancel-capable kind, interrupt raises)
  - timeout_interrupt_succeeded (non-cancel-capable kind, inline cancel cleanup)
  - unknown_kind_interrupt_transport_failure (pre-capture)

Happy paths (decide-success + timeout-cancel-dispatch-succeeded) return
None from the handler, letting the turn continue to turn/completed
naturally; _finalize_turn's Captured-Request Terminal Guard (Task 19)
maps the terminal request state to the correct DelegationJob.status.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase F complete.** The worker runs on its own thread and terminalizes through all 6 sentinel branches. Phase G wires the public APIs (start / decide) into the new model.

---
