"""Packet 1 Task 18: decide() under the reservation two-phase protocol.

Acceptance tests for the new transactional registry protocol — `validate
→ _build_response_payload → DecisionResolution → reserve → journal-intent
(rollback on failure) → commit_signal (bare) → audit (post-commit, non-
gating) → DelegationDecisionResult`.

Per W4 (Task 14/15/16/17 precedent): use module-local helpers
(`_build_controller`, `_command_approval_request`, `_request_user_input_request`
from `tests.test_delegation_controller`) + built-in pytest fixtures
(`tmp_path`, `monkeypatch`, `caplog`) + `unittest.mock`. Do NOT use the
plan-pseudocode fictional fixtures (`delegation_controller_fixture`,
`app_server_runtime_stub`, `journal_spy`, `audit_event_spy`) — they do
not exist in `tests/conftest.py`.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import pytest

from server.delegation_controller import DelegationController
from server.models import (
    DecisionRejectedResponse,
    DelegationDecisionResult,
    DelegationEscalation,
    JobStatus,
    PendingServerRequest,
    TurnExecutionResult,
)
from server.resolution_registry import DecisionResolution

from tests.test_delegation_controller import (
    _build_controller,
    _command_approval_request,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_parked_command_approval(
    tmp_path: Path,
) -> tuple[DelegationController, Any, Path]:
    """Drive controller.start() to the Parked state on a command_approval
    request and return (controller, control_plane, repo_root). The worker is
    blocked in `registry.wait()`; `start()` has already returned a
    `DelegationEscalation`.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)
    return controller, control_plane, repo_root


# ---------------------------------------------------------------------------
# Test 1 — happy approve, command_approval kind.
# ---------------------------------------------------------------------------


def test_decide_returns_3_field_result_on_success_approve(tmp_path: Path) -> None:
    """decide(approve) on a parked command_approval request returns
    DelegationDecisionResult(decision_accepted=True, job_id, request_id).
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn to complete cleanly so the worker can drain.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DelegationDecisionResult)
    assert result.decision_accepted is True
    assert result.job_id == "job-1"
    assert result.request_id == "42"


# ---------------------------------------------------------------------------
# Test 2 — happy deny, command_approval kind.
# ---------------------------------------------------------------------------


def test_decide_returns_3_field_result_on_success_deny(tmp_path: Path) -> None:
    """decide(deny) on a parked command_approval request returns
    DelegationDecisionResult(decision_accepted=True, job_id, request_id).
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn to complete cleanly so the worker can drain.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="declined",
        notifications=(),
    )

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="deny",
    )

    assert isinstance(result, DelegationDecisionResult)
    assert result.decision_accepted is True
    assert result.job_id == "job-1"
    assert result.request_id == "42"


# ---------------------------------------------------------------------------
# Test 3 — same-rid double-decide → second returns request_already_decided.
# ---------------------------------------------------------------------------


def test_decide_twice_second_returns_request_already_decided(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Second decide() on the same request_id must return
    DecisionRejectedResponse(reason='request_already_decided', ...).

    Per L9 mandate + Round-4 corrected mechanism: wrap
    job_store.update_status_and_promotion AFTER the parked-request setup is
    complete, gating ONLY the resume call where status=='running' (the
    post-`commit_signal` mutation at delegation_controller.py:1166). All
    other update_status_and_promotion calls pass through unblocked. This
    holds the worker BEFORE the status race while letting the initial
    park complete normally. Diagnostically: while the gate is held,
    job.status stays 'needs_escalation' (string literal — JobStatus is a
    typing.Literal, NOT enum), so the second decide's validation chain
    passes job_not_awaiting_decision and reaches reserve(), which returns
    None because the first decide's commit_signal has already moved the
    entry into 'consuming'.
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn to complete cleanly so the worker can drain
    # naturally once the gate is released.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    # Install the wrapper AFTER start() has parked. The wrapper holds the
    # worker at the post-commit_signal job-status mutation (status='running').
    # All other update_status_and_promotion calls pass through.
    job_store = controller._job_store
    real_update_status_and_promotion = job_store.update_status_and_promotion
    gate = threading.Event()  # released at the end to let teardown drain

    def gated_update_status_and_promotion(
        job_id: str,
        *,
        status: JobStatus,
        promotion_state: Any = None,
    ) -> Any:
        if status == "running":
            gate.wait()
        return real_update_status_and_promotion(
            job_id, status=status, promotion_state=promotion_state
        )

    monkeypatch.setattr(
        job_store,
        "update_status_and_promotion",
        gated_update_status_and_promotion,
    )

    # First decide — worker wakes, blocks at the gated wrapper before mutating
    # job.status to 'running'. decide() returns success normally (commit_signal
    # is non-blocking; the gating is on the worker side).
    first = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(first, DelegationDecisionResult)
    assert first.decision_accepted is True

    # Diagnostic: while the gate is held, job.status stays 'needs_escalation'.
    # This is a string comparison — JobStatus is typing.Literal, NOT enum.
    pre_decide_job = job_store.get("job-1")
    assert pre_decide_job is not None
    assert pre_decide_job.status == "needs_escalation"

    # Second decide on the same rid — validation passes (status is still
    # 'needs_escalation') → reserve() returns None (entry is in 'consuming'
    # from the first decide's commit_signal) → reject with
    # request_already_decided.
    second = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(second, DecisionRejectedResponse)
    assert second.reason == "request_already_decided"

    # Release the gate so the worker drains naturally for teardown.
    gate.set()


# ---------------------------------------------------------------------------
# Test 4 — deterministic competing reservation → request_already_decided.
# ---------------------------------------------------------------------------


def test_decide_competing_reservation_returns_request_already_decided(
    tmp_path: Path,
) -> None:
    """When the registry entry is already 'reserved' by a competing call,
    decide()'s reserve() returns None and the response is
    DecisionRejectedResponse(reason='request_already_decided').

    Per L9 + Round-3 prune: the test directly calls `controller._registry.reserve`
    to force the entry out of awaiting. Cleanup MUST `abort_reservation` (which
    only restores 'awaiting' — does NOT wake the worker) and then drive a real
    `controller.decide(approve, ...)` to wake the worker through the production
    path. Direct `commit_signal(competing_token)` is forbidden — it would route
    the test-held fake DecisionResolution payload through the worker's respond.
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn so cleanup can drain naturally.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    # Force the entry out of 'awaiting' by directly reserving it. The token is
    # held by the test; the entry is now in 'reserved' state.
    competing_token = controller._registry.reserve(
        "42",
        DecisionResolution(payload={"decision": "accept"}, kind="command_approval"),
    )
    assert competing_token is not None

    # decide() under reservation contention reaches its own reserve(), which
    # returns None because the entry is in 'reserved' (not 'awaiting').
    rejected = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(rejected, DecisionRejectedResponse)
    assert rejected.reason == "request_already_decided"

    # Cleanup: abort the competing reservation (restores 'awaiting' but does
    # NOT wake the worker), then drive a real decide() through the production
    # path to actually drain the worker.
    controller._registry.abort_reservation(competing_token)
    drain = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(drain, DelegationDecisionResult)


# ---------------------------------------------------------------------------
# Test 5 — write_phase('intent') precedes commit_signal.
# ---------------------------------------------------------------------------


def test_decide_writes_intent_before_commit_signal_ordering(
    tmp_path: Path,
) -> None:
    """The journal `intent` write MUST land before
    `ResolutionRegistry.commit_signal`. Capture call order via spies and
    assert intent_index < commit_index.
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn so the worker can drain.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    call_order: list[str] = []

    real_write_phase = controller._journal.write_phase
    real_commit_signal = controller._registry.commit_signal

    def spy_write_phase(entry: Any, *, session_id: str) -> None:
        if entry.operation == "approval_resolution" and entry.phase == "intent":
            call_order.append(f"intent:{entry.request_id}")
        return real_write_phase(entry, session_id=session_id)

    def spy_commit_signal(token: Any) -> None:
        call_order.append(f"commit_signal:{token.request_id}")
        return real_commit_signal(token)

    controller._journal.write_phase = spy_write_phase  # type: ignore[assignment]
    controller._registry.commit_signal = spy_commit_signal  # type: ignore[assignment]

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(result, DelegationDecisionResult)

    # Both events must have fired exactly once and intent must precede
    # commit_signal.
    assert "intent:42" in call_order
    assert "commit_signal:42" in call_order
    assert call_order.index("intent:42") < call_order.index("commit_signal:42")


# ---------------------------------------------------------------------------
# Test 6 — journal-intent failure → abort_reservation called; entry restored.
# ---------------------------------------------------------------------------


def test_decide_aborts_reservation_on_journal_intent_failure(
    tmp_path: Path,
) -> None:
    """If `journal.write_phase('intent')` raises, decide() MUST call
    `abort_reservation(token)` to restore the entry to 'awaiting' and then
    re-raise the original exception. Verifiable via follow-up `reserve()`
    succeeding (the entry is back in 'awaiting').
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    # Configure the resumed turn so cleanup can drain naturally.
    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    # Sabotage the intent write. We re-attach the original after the failed
    # decide() so the cleanup decide() can drive the production path.
    real_write_phase = controller._journal.write_phase

    def sabotaged_write_phase(entry: Any, *, session_id: str) -> None:
        if entry.operation == "approval_resolution" and entry.phase == "intent":
            raise OSError("journal intent write failed")
        return real_write_phase(entry, session_id=session_id)

    controller._journal.write_phase = sabotaged_write_phase  # type: ignore[assignment]

    with pytest.raises(OSError, match="journal intent write failed"):
        controller.decide(
            job_id="job-1",
            request_id="42",
            decision="approve",
        )

    # Entry should be back in 'awaiting' — verifiable via follow-up reserve().
    follow_up_token = controller._registry.reserve(
        "42",
        DecisionResolution(payload={"decision": "accept"}, kind="command_approval"),
    )
    assert follow_up_token is not None, (
        "entry not back in 'awaiting' after journal-intent failure rollback"
    )
    # Restore the entry so the production drain path succeeds.
    controller._registry.abort_reservation(follow_up_token)

    # Un-sabotage and drive a production decide() to drain the worker.
    controller._journal.write_phase = real_write_phase  # type: ignore[assignment]
    drain = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(drain, DelegationDecisionResult)


# ---------------------------------------------------------------------------
# Test 7 — audit failure post-commit is non-gating; durable side effects.
# ---------------------------------------------------------------------------


def test_decide_audit_event_post_commit_non_gating(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Per L7b: if `journal.append_audit_event` raises post-`commit_signal`,
    decide() MUST log a warning and return success — abort_reservation is
    NOT called. Per L9 test #7 contract: do NOT use a follow-up decide(rid)
    as proof of slot-still-claimed (validation-order race). Use durable,
    non-racing assertions:
      (a) decide() returned success;
      (b) audit warning was logged;
      (c) journal `intent` entry persists in capture (was written before
          audit per L7b ordering, durable regardless of audit failure);
      (d) worker eventually dispatches `session.respond` (verifiable via
          mocked respond capture; proves commit_signal fired and woke the
          worker despite audit failure — the actual non-gating evidence).
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    # Capture intent journal writes for assertion (c).
    intent_entries: list[Any] = []
    real_write_phase = controller._journal.write_phase

    def spy_write_phase(entry: Any, *, session_id: str) -> None:
        if entry.operation == "approval_resolution" and entry.phase == "intent":
            intent_entries.append(entry)
        return real_write_phase(entry, session_id=session_id)

    controller._journal.write_phase = spy_write_phase  # type: ignore[assignment]

    # Sabotage append_audit_event.
    def sabotaged_append_audit_event(event: Any) -> None:
        raise OSError("audit append failed")

    controller._journal.append_audit_event = sabotaged_append_audit_event  # type: ignore[assignment]

    # Capture worker-side respond dispatches for assertion (d).
    respond_calls: list[tuple[str, dict[str, Any]]] = []

    def respond_spy(request_id: str, payload: dict[str, Any]) -> None:
        respond_calls.append((request_id, payload))

    session.respond = respond_spy

    with caplog.at_level(logging.WARNING):
        result = controller.decide(
            job_id="job-1",
            request_id="42",
            decision="approve",
        )

    # (a) success return.
    assert isinstance(result, DelegationDecisionResult)
    assert result.decision_accepted is True

    # (b) audit warning logged.
    audit_warnings = [
        rec for rec in caplog.records if "audit" in rec.message.lower()
    ]
    assert audit_warnings, "expected audit warning in logs"

    # (c) intent entry persisted (written before audit, so survives audit
    # failure).
    assert any(e.request_id == "42" for e in intent_entries), (
        "intent entry must persist even when audit fails"
    )

    # (d) worker eventually dispatched respond. Wait for the worker thread
    # to drain. spawn_worker(...) names the thread "delegation-worker-{job_id}"
    # — locate it via threading.enumerate() and join. This is the actual
    # non-gating evidence: commit_signal fired and woke the worker despite
    # the audit failure.
    #
    # Round-6: prior tests may leak parked daemon threads under the same
    # job_id (job-1 is deterministic across tests in this module). Find
    # at least one matching thread and join the most-recently-started one
    # (this test's spawn). The worker must drain — that's the non-gating
    # evidence. Other leaked threads are from sibling tests and tolerated.
    worker_threads = [
        t for t in threading.enumerate() if t.name == "delegation-worker-job-1"
    ]
    assert worker_threads, (
        f"no worker thread named 'delegation-worker-job-1' found; "
        f"got {[t.name for t in threading.enumerate()]!r}"
    )
    # Most-recently-started thread is THIS test's worker. ident is monotonic.
    this_test_worker = max(worker_threads, key=lambda t: t.ident or 0)
    this_test_worker.join(timeout=10.0)
    assert not this_test_worker.is_alive(), "worker thread did not drain"

    assert any(rid == "42" for rid, _ in respond_calls), (
        "worker did not dispatch respond — commit_signal failed to wake the "
        "worker (audit non-gating evidence missing)"
    )


# ---------------------------------------------------------------------------
# Test 8 — audit action='approve' for approve decisions (L7a regression).
# ---------------------------------------------------------------------------


def test_decide_audit_action_matches_decision_for_approve(
    tmp_path: Path,
) -> None:
    """Per L7a: the new audit at the post-`commit_signal` position MUST set
    `action=decision` (not the old hardcoded `action='approve'`). For
    approve decisions, `AuditEvent.action == 'approve'`.
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="done",
        notifications=(),
    )

    captured_events: list[Any] = []
    real_append = controller._journal.append_audit_event

    def spy_append(event: Any) -> None:
        captured_events.append(event)
        return real_append(event)

    controller._journal.append_audit_event = spy_append  # type: ignore[assignment]

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(result, DelegationDecisionResult)

    decide_audits = [e for e in captured_events if e.request_id == "42"]
    # The decide()-side audit emits with action=decision; for approve, that's
    # "approve".
    assert any(e.action == "approve" for e in decide_audits)


# ---------------------------------------------------------------------------
# Test 9 — audit action='deny' for deny decisions (L7a regression).
# ---------------------------------------------------------------------------


def test_decide_audit_action_matches_decision_for_deny(
    tmp_path: Path,
) -> None:
    """Per L7a: deny audit MUST emit with action='deny' (pre-Packet-1 had
    action='approve' hardcoded for both arms — incidental fix per L7a).
    """
    controller, control_plane, _repo = _seed_parked_command_approval(tmp_path)

    session = control_plane._sessions[0]
    session._server_requests = []
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="completed",
        agent_message="declined",
        notifications=(),
    )

    captured_events: list[Any] = []
    real_append = controller._journal.append_audit_event

    def spy_append(event: Any) -> None:
        captured_events.append(event)
        return real_append(event)

    controller._journal.append_audit_event = spy_append  # type: ignore[assignment]

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="deny",
    )
    assert isinstance(result, DelegationDecisionResult)

    decide_audits = [e for e in captured_events if e.request_id == "42"]
    # The decide()-side audit emits with action=decision; for deny, that's
    # "deny".
    assert any(e.action == "deny" for e in decide_audits)


# ---------------------------------------------------------------------------
# Test 10 — _build_response_payload per (kind, decision) — 6-row binding.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind,decision,answers,expected_payload",
    [
        # approve × command_approval → {"decision": "accept"}
        ("command_approval", "approve", None, {"decision": "accept"}),
        # approve × file_change → {"decision": "accept"}
        ("file_change", "approve", None, {"decision": "accept"}),
        # approve × request_user_input → {"answers": <validated>}
        # Per pinned-version fixture
        # tests/fixtures/codex-app-server/0.117.0/ToolRequestUserInputResponse.json,
        # the App Server wire shape is
        # {"answers": {<qid>: {"answers": [<string>...]}}}.
        (
            "request_user_input",
            "approve",
            {"q1": ("yes",)},
            {"answers": {"q1": {"answers": ["yes"]}}},
        ),
        # deny × command_approval → {"decision": "decline"} (NOT "reject")
        ("command_approval", "deny", None, {"decision": "decline"}),
        # deny × file_change → {"decision": "decline"} (NOT "reject")
        ("file_change", "deny", None, {"decision": "decline"}),
        # deny × request_user_input → {"answers": {}} empty-fallback.
        ("request_user_input", "deny", None, {"answers": {}}),
    ],
)
def test_build_response_payload_per_kind_decision(
    tmp_path: Path,
    kind: str,
    decision: str,
    answers: dict[str, tuple[str, ...]] | None,
    expected_payload: dict[str, Any],
) -> None:
    """Parameterized over the 6 valid (kind, decision) combinations from L4.
    Asserts EXACT payload dict for each. Pins:
      - `decline` (NOT `reject`) for deny on command_approval / file_change
      - `{"answers": {}}` empty-fallback for deny on request_user_input
      - `{"answers": <validated answers dict>}` for approve on
        request_user_input (Path A wire shape per pinned-version fixture).
    """
    controller, _cp, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)

    request = PendingServerRequest(
        request_id="42",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-x",
        kind=kind,  # type: ignore[arg-type]
        requested_scope={},
    )

    payload = controller._build_response_payload(
        decision=decision,
        answers=answers,
        request=request,
    )

    assert payload == expected_payload
