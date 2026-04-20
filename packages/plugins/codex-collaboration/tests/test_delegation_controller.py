"""Tests for DelegationController — mirrors dialogue pattern.

Verifies every durable surface is populated AND the in-process registry
retains the session so the runtime remains controllable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import (
    AccountState,
    CollaborationHandle,
    DelegationEscalation,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
    RuntimeHandshake,
    TurnExecutionResult,
)
from server.pending_request_store import PendingRequestStore


class _FakeSession:
    def __init__(self, thread_id: str = "thr-1") -> None:
        self._thread_id = thread_id
        self.closed = False
        self._interrupted = False
        self._raise_on_turn: Exception | None = None
        # Configurable server requests and turn result for capture loop tests.
        self._server_requests: list[dict[str, Any]] = []
        self._turn_result: TurnExecutionResult = TurnExecutionResult(
            turn_id="turn-1",
            status="completed",
            agent_message="Done.",
            notifications=(),
        )

    def initialize(self) -> RuntimeHandshake:
        return RuntimeHandshake(
            codex_home="/h",
            platform_family="u",
            platform_os="d",
            user_agent="codex/test",
        )

    def read_account(self) -> AccountState:
        return AccountState(
            auth_status="authenticated",
            account_type="t",
            requires_openai_auth=False,
        )

    def start_thread(self) -> str:
        return self._thread_id

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

    def interrupt_turn(self, *, thread_id: str, turn_id: str | None) -> None:
        self._interrupted = True

    def close(self) -> None:
        self.closed = True


class _FakeControlPlane:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self._next_runtime_id = 0
        self._sessions: list[_FakeSession] = []
        # Pre-configure server requests and turn result for the next session.
        self._next_session_requests: list[dict[str, Any]] = []
        self._next_turn_result: TurnExecutionResult | None = None
        self._next_raise_on_turn: Exception | None = None

    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, _FakeSession, str]:
        self.calls.append(worktree_path)
        self._next_runtime_id += 1
        session = _FakeSession(thread_id=f"thr-{self._next_runtime_id}")
        session._server_requests = list(self._next_session_requests)
        if self._next_turn_result is not None:
            session._turn_result = self._next_turn_result
        session._raise_on_turn = self._next_raise_on_turn
        self._sessions.append(session)
        return f"rt-{self._next_runtime_id}", session, session._thread_id


class _FakeWorktreeManager:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str, Path]] = []
        self.remove_calls: list[tuple[Path, Path]] = []

    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None:
        self.calls.append((repo_root, base_commit, worktree_path))
        worktree_path.mkdir(parents=True, exist_ok=True)

    def remove_worktree(self, *, repo_root: Path, worktree_path: Path) -> None:
        self.remove_calls.append((repo_root, worktree_path))
        if worktree_path.exists():
            import shutil

            shutil.rmtree(worktree_path)
        # Mirror real WorktreeManager: clean up empty parent.
        parent = worktree_path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()


def _build_controller(
    tmp_path: Path,
    *,
    head_sha: str = "head-abc",
    session_id: str = "sess-1",
) -> tuple[
    DelegationController,
    _FakeControlPlane,
    _FakeWorktreeManager,
    DelegationJobStore,
    LineageStore,
    OperationJournal,
    ExecutionRuntimeRegistry,
    PendingRequestStore,
]:
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    control_plane = _FakeControlPlane()
    worktree_manager = _FakeWorktreeManager()
    registry = ExecutionRuntimeRegistry()
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
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )
    return (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        lineage_store,
        journal,
        registry,
        pending_request_store,
    )


def test_start_creates_worktree_runtime_and_persists_job(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        _lineage,
        _journal,
        _registry,
        _prs,
    ) = _build_controller(tmp_path)

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-1"
    assert result.base_commit == "head-abc"
    # After the turn dispatch (no server requests), status is "completed".
    assert result.status == "completed"
    assert result.promotion_state == "pending"
    # Worktree was created under the plugin data dir at the job's path.
    assert len(worktree_manager.calls) == 1
    recorded_repo, recorded_commit, recorded_wk = worktree_manager.calls[0]
    assert recorded_repo == repo_root
    assert recorded_commit == "head-abc"
    assert str(recorded_wk).endswith("/runtimes/delegation/job-1/worktree")
    # The controller bootstrapped exactly one runtime against that worktree.
    assert control_plane.calls == [recorded_wk]
    # Job is persisted.
    persisted = job_store.get("job-1")
    assert persisted is not None
    assert persisted.runtime_id == "rt-1"
    assert persisted.worktree_path == str(recorded_wk)


def test_start_persists_execution_collaboration_handle(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, lineage, _j, _r, _prs = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    handle = lineage.get("collab-1")
    assert isinstance(handle, CollaborationHandle)
    assert handle.capability_class == "execution"
    assert handle.runtime_id == "rt-1"
    assert handle.codex_thread_id == "thr-1"
    assert handle.claude_session_id == "sess-1"
    # Terminal completion: handle transitions to "completed" when the job
    # completes without escalation.
    assert handle.status == "completed"


def test_start_writes_three_phase_journal_records(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r, _prs = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    # Idempotency key is claude_session_id + delegation_request_hash.
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    key = f"sess-1:{request_hash}"

    terminal = journal.check_idempotency(key, session_id="sess-1")
    assert terminal is not None, "terminal phase should be completed"
    assert terminal.phase == "completed"
    assert terminal.operation == "job_creation"
    assert terminal.job_id == "job-1"

    # Inspect the raw journal file for all three phases.
    path = journal._operations_path("sess-1")
    records = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert phases == ["intent", "dispatched", "completed"]


def test_start_registers_runtime_ownership(tmp_path: Path) -> None:
    """After clean completion (no server requests), the runtime was registered
    during the committed-start phase and then released+closed during terminal
    cleanup. Verify the session IS closed and the registry IS empty.
    For needs_escalation scenarios, see test_start_with_command_approval_returns_escalation.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    (
        controller,
        control_plane,
        _wm,
        _js,
        _ls,
        _j,
        registry,
        _prs,
    ) = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    # After clean completion, the runtime was released and session closed.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


def test_start_emits_delegate_start_audit_event(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r, _prs = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    events_path = journal.plugin_data_path / "audit" / "events.jsonl"
    assert events_path.exists()

    lines = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]
    delegate_events = [e for e in lines if e.get("action") == "delegate_start"]
    assert len(delegate_events) == 1
    event = delegate_events[0]
    assert event["actor"] == "claude"
    assert event["collaboration_id"] == "collab-1"
    assert event["job_id"] == "job-1"
    assert event["runtime_id"] == "rt-1"


def test_start_uses_caller_provided_base_commit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, worktree_manager, _js, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    controller.start(repo_root=repo_root, base_commit="explicit-sha")

    assert worktree_manager.calls[0][1] == "explicit-sha"


def test_start_returns_busy_response_when_active_job_exists(tmp_path: Path) -> None:
    """Second start() is rejected when the first produced a needs_escalation job."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)

    # Configure the first start to hit a command_approval server request,
    # which produces needs_escalation (an active status).
    control_plane._next_session_requests = [
        {
            "id": 42,
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "rm -rf /",
            },
        }
    ]

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationEscalation)
    assert first.job.status == "needs_escalation"

    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == "job-1"
    assert second.active_job_status == "needs_escalation"
    # The rejected second call must NOT have triggered side effects.
    # Worktree and runtime counts stay at 1 (from the first, successful call).
    assert len(_wm.calls) == 1
    assert len(control_plane.calls) == 1


def test_start_does_not_persist_durable_state_on_bootstrap_failure(
    tmp_path: Path,
) -> None:
    """If runtime bootstrap raises, no durable state remains and no audit emitted.

    The journal may record an ``intent`` phase (that is correct per the journal-
    before-dispatch contract), but no ``dispatched`` / ``completed`` phase, no
    handle in lineage, no job in job store, no registry entry, no audit event.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, "sess-1")
    lineage_store = LineageStore(plugin_data, "sess-1")
    journal = OperationJournal(plugin_data)
    registry = ExecutionRuntimeRegistry()
    worktree_manager = _FakeWorktreeManager()

    class _FailingControlPlane:
        def start_execution_runtime(self, worktree_path: Path) -> tuple:
            raise RuntimeError("Execution runtime bootstrap failed: test forced")

    pending_request_store = PendingRequestStore(plugin_data, "sess-1")
    uuid_counter = iter(["job-1", "collab-1", "evt-1"])
    controller = DelegationController(
        control_plane=_FailingControlPlane(),  # type: ignore[arg-type]
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id="sess-1",
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        head_commit_resolver=lambda _: "head-abc",
        uuid_factory=lambda: next(uuid_counter),
    )

    with pytest.raises(RuntimeError, match="Execution runtime bootstrap failed"):
        controller.start(repo_root=repo_root)

    assert job_store.get("job-1") is None
    assert lineage_store.get("collab-1") is None
    assert registry.lookup("rt-1") is None
    audit_path = journal.plugin_data_path / "audit" / "events.jsonl"
    if audit_path.exists():
        content = audit_path.read_text()
        assert "delegate_start" not in content
    # Worktree must be cleaned up — no untracked directory left behind.
    assert len(worktree_manager.remove_calls) == 1
    _, removed_path = worktree_manager.remove_calls[0]
    assert not removed_path.exists()
    # Per-job parent directory must also be gone (not just the worktree leaf).
    assert not removed_path.parent.exists()


# -----------------------------------------------------------------------------
# Committed-start failure semantics — post-dispatched local-write failures.
#
# Each of these tests verifies that when a write after the ``dispatched`` journal
# phase fails, the controller: (1) does NOT write the ``completed`` journal phase
# (leaves it for startup reconciliation), (2) best-effort marks persisted handle
# and/or job as ``unknown``, and (3) raises CommittedStartFinalizationError with
# caller-facing no-retry guidance.
# -----------------------------------------------------------------------------


def _assert_dispatched_but_not_completed(
    journal: OperationJournal, session_id: str, request_hash: str
) -> None:
    """Helper: assert journal has intent + dispatched but NOT completed for job."""
    key = f"{session_id}:{request_hash}"
    path = journal._operations_path(session_id)
    records = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert "intent" in phases
    assert "dispatched" in phases
    assert "completed" not in phases, (
        "journal must stay at dispatched for startup reconciliation to close it"
    )


def test_start_raises_committed_start_finalization_error_on_lineage_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LineageStore.create failure after dispatched: partial state, no completed."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("lineage_store.create boom")

    monkeypatch.setattr(lineage_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Registry HAS the entry — register goes FIRST in the try block, before
    # lineage. The runtime subprocess is reachable in-process for the rest
    # of the session and the busy gate's registry consultation blocks retry.
    assert registry.lookup("rt-1") is not None
    # Nothing persisted downstream of the failure.
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_start_raises_committed_start_finalization_error_on_job_store_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DelegationJobStore.create failure after dispatched: handle marked unknown."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("job_store.create boom")

    monkeypatch.setattr(job_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Registry HAS the entry — register goes FIRST in the try block.
    assert registry.lookup("rt-1") is not None
    # Handle WAS written before the failure — must be marked unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None
    assert handle.status == "unknown"
    # Job was NOT written.
    assert job_store.get("job-1") is None


def test_start_raises_committed_start_finalization_error_on_journal_completed_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """journal.write_phase(completed) failure: handle + job marked unknown."""

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    # Let intent + dispatched succeed; fail on the completed phase.
    real_write_phase = journal.write_phase
    calls: list[str] = []

    def _selective_boom(entry: OperationJournalEntry, *, session_id: str) -> None:
        calls.append(entry.phase)
        if entry.phase == "completed":
            raise OSError("journal.write_phase(completed) boom")
        real_write_phase(entry, session_id=session_id)

    monkeypatch.setattr(journal, "write_phase", _selective_boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    assert calls == ["intent", "dispatched", "completed"]
    # No completed in the file either — the selective_boom ensured it.
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Both handle and job were written before the failure — both must be unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Registry registration happens before the completed phase — entry present.
    assert registry.lookup("rt-1") is not None


def test_start_raises_committed_start_finalization_error_on_audit_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """journal.append_audit_event failure: handle + job marked unknown, journal at dispatched.

    Flow order in Step 6.3 places append_audit_event BEFORE journal.write_phase(completed)
    so the journal-at-dispatched invariant holds for all five committed-start failure modes
    (register / lineage / job / audit / journal-completed).
    """

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("audit boom")

    monkeypatch.setattr(journal, "append_audit_event", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Handle, job, and registry entry were all created before the audit failure.
    # All must be marked unknown (or released in the registry's case — see policy note below).
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Registry entry stays (runtime subprocess is live; releasing it would leak
    # the subprocess). Recovery policy: the unknown status on handle+job is the
    # authoritative signal; the live runtime remains reachable via registry.lookup
    # for a subsequent teardown pass in poll/promote slices.
    assert registry.lookup("rt-1") is not None


def test_start_raises_committed_start_finalization_error_on_register_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ExecutionRuntimeRegistry.register failure: no entry, no handle, no job.

    Register is the FIRST committed-start write — if it raises, no other
    durable state has been touched yet. The runtime subprocess is live but
    unreachable from the in-process registry; the journal is at dispatched
    so reconciliation will close it on next session init. The subprocess
    leaks until the parent process exits (no entry to release; teardown via
    subprocess discovery is out of scope).
    """

    from server.delegation_controller import CommittedStartFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("registry.register boom")

    monkeypatch.setattr(registry, "register", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc:".encode("utf-8")
    ).hexdigest()
    _assert_dispatched_but_not_completed(journal, "sess-1", request_hash)
    # Register itself failed — no entry, and downstream writes never started.
    assert registry.lookup("rt-1") is None
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


# -----------------------------------------------------------------------------
# Busy-gate widening: the gate consults THREE sources (job_store, registry,
# unresolved job_creation journal entries). The two tests below cover the new
# sources; existing tests already cover the job_store-only case.
# -----------------------------------------------------------------------------


def test_start_returns_busy_when_registry_has_entry_but_job_store_empty(
    tmp_path: Path,
) -> None:
    """Same-session retry after committed-start lineage failure: registry-based busy.

    Simulates the post-lineage-failure state directly: a registered runtime
    with no DelegationJob in the store. The busy gate must consult the
    registry and reject the second start, otherwise blind retry would spawn
    a duplicate runtime subprocess.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _job_store, _lineage_store, _journal, registry, _prs = (
        _build_controller(tmp_path)
    )

    fake_session = object()
    registry.register(
        runtime_id="rt-prior",
        session=fake_session,
        thread_id="thread-prior",
        job_id="job-prior",
    )

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, JobBusyResponse)
    assert result.busy is True
    assert result.active_job_id == "job-prior"
    # The rejected call must NOT have triggered side effects.
    assert _wm.calls == []
    assert _cp.calls == []


def test_start_returns_busy_when_unresolved_journal_entry_present(
    tmp_path: Path,
) -> None:
    """Cross-session committed-start residue: journal-based busy.

    Simulates a fresh session where the in-process registry is empty but the
    journal still has a dispatched job_creation record from a prior process.
    The busy gate must consult unresolved journal entries (filtered by
    operation == "job_creation") and reject the second start until
    recover_startup() reconciles it.
    """

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _job_store, _lineage_store, journal, _registry, _prs = (
        _build_controller(tmp_path)
    )

    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="sess-1:prior-hash",
            operation="job_creation",
            phase="intent",
            collaboration_id="collab-prior",
            created_at="2026-01-01T00:00:00Z",
            repo_root=str(repo_root.resolve()),
            job_id="job-prior",
        ),
        session_id="sess-1",
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="sess-1:prior-hash",
            operation="job_creation",
            phase="dispatched",
            collaboration_id="collab-prior",
            created_at="2026-01-01T00:00:00Z",
            repo_root=str(repo_root.resolve()),
            job_id="job-prior",
            runtime_id="rt-prior",
            codex_thread_id="thread-prior",
        ),
        session_id="sess-1",
    )

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, JobBusyResponse)
    assert result.busy is True
    assert result.active_job_id == "job-prior"
    # The rejected call must NOT have triggered side effects.
    assert _wm.calls == []
    assert _cp.calls == []


# -----------------------------------------------------------------------------
# Startup reconciliation — DelegationController.recover_startup() consumes
# unresolved job_creation journal entries and closes them into durable state.
# -----------------------------------------------------------------------------


def _write_unresolved_intent(
    journal: OperationJournal,
    session_id: str,
    *,
    idempotency_key: str,
    collaboration_id: str,
    job_id: str,
    repo_root: Path,
) -> None:
    """Seed the journal with an intent-only job_creation entry (simulates a crash
    after intent but before dispatch side effects)."""
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=journal.timestamp(),
            repo_root=str(repo_root),
            job_id=job_id,
        ),
        session_id=session_id,
    )


def _write_unresolved_dispatched(
    journal: OperationJournal,
    session_id: str,
    *,
    idempotency_key: str,
    collaboration_id: str,
    job_id: str,
    runtime_id: str,
    thread_id: str,
    repo_root: Path,
) -> None:
    """Seed the journal with intent + dispatched (simulates a crash during
    committed-start finalization)."""
    created_at = journal.timestamp()
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(repo_root),
            job_id=job_id,
        ),
        session_id=session_id,
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="job_creation",
            phase="dispatched",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(repo_root),
            job_id=job_id,
            runtime_id=runtime_id,
            codex_thread_id=thread_id,
        ),
        session_id=session_id,
    )


def test_recover_startup_noop_on_fresh_session(tmp_path: Path) -> None:
    """No unresolved entries → no durable changes, no journal writes."""
    controller, _cp, _wm, _js, _ls, journal, _r, _prs = _build_controller(tmp_path)

    before = journal.list_unresolved(session_id="sess-1")
    assert before == []

    controller.recover_startup()

    after = journal.list_unresolved(session_id="sess-1")
    assert after == []


def test_recover_startup_closes_intent_only_as_noop(tmp_path: Path) -> None:
    """intent-only → write completed, no durable changes."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    _write_unresolved_intent(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        repo_root=repo_root,
    )

    # No handle / job persisted (crash before dispatch side effects).
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None

    controller.recover_startup()

    # Journal advanced to completed; unresolved list empty after reconciliation.
    assert journal.list_unresolved(session_id="sess-1") == []
    # Still no durable handle / job (nothing was there to reconcile).
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_recover_startup_marks_dispatched_handle_and_job_unknown(
    tmp_path: Path,
) -> None:
    """intent + dispatched with persisted handle + job → mark both unknown, close journal."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    # Seed: intent + dispatched journal + persisted active handle + persisted queued job.
    _write_unresolved_dispatched(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        runtime_id="rt-1",
        thread_id="thr-1",
        repo_root=repo_root,
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
    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state="pending",
            status="queued",
        )
    )

    controller.recover_startup()

    # Both stores advanced to unknown.
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    job = job_store.get("job-1")
    assert job is not None and job.status == "unknown"
    # Journal record closed.
    assert journal.list_unresolved(session_id="sess-1") == []


def test_recover_startup_closes_dispatched_without_persisted_state(
    tmp_path: Path,
) -> None:
    """intent + dispatched but no handle/job persisted → write completed, no mark needed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    _write_unresolved_dispatched(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        runtime_id="rt-1",
        thread_id="thr-1",
        repo_root=repo_root,
    )
    # Intentionally NO lineage_store.create / job_store.create — simulates crash
    # between journal.write_phase(dispatched) and lineage_store.create.

    controller.recover_startup()

    # No durable records to advance, but journal is closed.
    assert journal.list_unresolved(session_id="sess-1") == []
    assert lineage_store.get("collab-1") is None
    assert job_store.get("job-1") is None


def test_recover_startup_does_not_downgrade_handle_already_unknown(
    tmp_path: Path,
) -> None:
    """Row 5 of reconciliation contract: handle already unknown (same-session
    committed-start failure) → no change, write completed. Exercises the
    negation of the ``handle.status == "active"`` guard — a handle that was
    best-effort marked unknown by Task 6's CommittedStartFinalizationError
    path must not be re-touched by reconciliation.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    _write_unresolved_dispatched(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        runtime_id="rt-1",
        thread_id="thr-1",
        repo_root=repo_root,
    )
    # Handle persisted directly in the "unknown" state — simulates the state
    # left behind after a same-session CommittedStartFinalizationError best-
    # effort marked it. Job store intentionally empty (register/lineage failed
    # before job.create in the committed-start order).
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-1",
            capability_class="execution",
            runtime_id="rt-1",
            codex_thread_id="thr-1",
            claude_session_id="sess-1",
            repo_root=str(repo_root),
            created_at=journal.timestamp(),
            status="unknown",
        )
    )

    controller.recover_startup()

    # Handle stays unknown (guard skips non-active); journal closed.
    handle = lineage_store.get("collab-1")
    assert handle is not None and handle.status == "unknown"
    assert job_store.get("job-1") is None
    assert journal.list_unresolved(session_id="sess-1") == []


def test_start_accepts_objective_parameter(tmp_path: Path) -> None:
    """start() accepts an objective parameter without error."""
    controller, _, _, _, _, _, _, _ = _build_controller(tmp_path)
    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Fix the login bug",
    )
    assert not isinstance(result, JobBusyResponse)


def test_delegation_request_hash_includes_objective(tmp_path: Path) -> None:
    """Objective is a component of the idempotency hash."""
    from server.delegation_controller import _delegation_request_hash

    repo_root = (tmp_path / "repo").resolve()
    hash_a = _delegation_request_hash(repo_root, "head-abc", "Fix bug A")
    hash_b = _delegation_request_hash(repo_root, "head-abc", "Fix bug B")
    hash_no_obj = _delegation_request_hash(repo_root, "head-abc", "")
    assert hash_a != hash_b, "Different objectives must produce different hashes"
    assert hash_a != hash_no_obj, "Objective vs no-objective must differ"


def test_recover_startup_marks_orphaned_running_jobs_unknown(
    tmp_path: Path,
) -> None:
    """After a cold restart, running jobs with no live runtime are marked unknown.

    Simulates the crash-during-turn window: job is created and set to "running"
    by start(), then the process crashes before post-turn terminal writes. On
    restart, recover_startup() marks the orphaned running job as "unknown".
    """
    _, _, _, job_store, _, _, _, _ = _build_controller(tmp_path)

    # Directly create a job in the store to simulate a crash mid-turn.
    job_store.create(
        DelegationJob(
            job_id="job-orphan",
            runtime_id="rt-orphan",
            collaboration_id="collab-orphan",
            base_commit="head-abc",
            worktree_path="/tmp/wk",
            promotion_state="pending",
            status="running",
        )
    )

    # Cold restart: fresh controller (fresh registry, no live runtimes)
    controller2, _, _, _, _, _, _, _ = _build_controller(tmp_path, session_id="sess-1")
    controller2.recover_startup()

    recovered = job_store.get("job-orphan")
    assert recovered is not None
    assert recovered.status == "unknown"


def test_recover_startup_idempotent_second_call_is_noop(tmp_path: Path) -> None:
    """Second recover_startup after the first has reconciled finds nothing to do."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r, _prs = _build_controller(tmp_path)

    _write_unresolved_intent(
        journal,
        "sess-1",
        idempotency_key="sess-1:hash-abc",
        collaboration_id="collab-1",
        job_id="job-1",
        repo_root=repo_root,
    )

    controller.recover_startup()
    assert journal.list_unresolved(session_id="sess-1") == []

    # Second call should be a clean no-op.
    controller.recover_startup()
    assert journal.list_unresolved(session_id="sess-1") == []


# -----------------------------------------------------------------------------
# Capture loop tests — turn dispatch + three-strategy handler + job transitions.
# -----------------------------------------------------------------------------


def _command_approval_request(
    *,
    request_id: int | str = 42,
    item_id: str = "item-1",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    """Build a fake command_approval server request message."""
    return {
        "id": request_id,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "command": "rm -rf /",
        },
    }


def _request_user_input_request(
    *,
    request_id: int | str = 55,
    item_id: str = "item-u",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    """Build a fake request_user_input server request."""
    return {
        "id": request_id,
        "method": "item/tool/requestUserInput",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "questions": [],
        },
    }


def _permissions_request(
    *,
    request_id: int | str = 99,
    item_id: str = "item-p",
    thread_id: str = "thr-1",
    turn_id: str = "turn-1",
) -> dict[str, Any]:
    """Build a fake unknown-kind server request (permissions)."""
    return {
        "id": request_id,
        "method": "item/permissions/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "scope": "network",
        },
    }


def test_start_with_command_approval_returns_escalation(tmp_path: Path) -> None:
    """command_approval → cancel response → DelegationEscalation with needs_escalation."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, journal, registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_command_approval_request()]

    result = controller.start(repo_root=repo_root, objective="Fix the bug")

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "command_approval"
    assert result.pending_request.request_id == "42"
    assert result.agent_context is not None

    # Pending request was persisted and resolved (D4).
    stored = prs.get("42")
    assert stored is not None
    assert stored.status == "resolved"

    # Escalation audit event emitted.
    events_path = journal.plugin_data_path / "audit" / "events.jsonl"
    lines = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]
    escalation_events = [e for e in lines if e.get("action") == "escalate"]
    assert len(escalation_events) == 1
    assert escalation_events[0]["request_id"] == "42"

    # Runtime kept live for needs_escalation — NOT released, NOT closed.
    assert registry.lookup("rt-1") is not None
    assert not control_plane._sessions[0].closed


def test_start_with_unknown_request_interrupts_and_escalates(tmp_path: Path) -> None:
    """Unknown kind (e.g., permissions) → interrupt → needs_escalation."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_permissions_request()]

    result = controller.start(repo_root=repo_root, objective="Deploy")

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "unknown"
    assert result.pending_request.request_id == "99"

    # Pending request persisted and resolved (D4 — parse succeeded, kind unknown).
    stored = prs.get("99")
    assert stored is not None
    assert stored.status == "resolved"

    # Runtime kept live.
    assert registry.lookup("rt-1") is not None


def test_start_with_two_requests_responds_to_both(tmp_path: Path) -> None:
    """Second request gets a response but is NOT separately persisted."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)

    control_plane._next_session_requests = [
        _command_approval_request(request_id=1, item_id="item-a"),
        _command_approval_request(request_id=2, item_id="item-b"),
    ]

    result = controller.start(repo_root=repo_root, objective="Fix")

    assert isinstance(result, DelegationEscalation)
    # Only the FIRST request is persisted.
    assert prs.get("1") is not None
    assert prs.get("2") is None
    # The escalation refers to the first request.
    assert result.pending_request.request_id == "1"


def test_start_with_unparseable_request_creates_minimal_causal_record(
    tmp_path: Path,
) -> None:
    """Parse failure → minimal record with status="pending" (D4 carve-out)."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)

    # A message with no params dict at all will fail parse.
    control_plane._next_session_requests = [
        {"id": 77, "method": "item/unknown/broken", "params": "not-a-dict"}
    ]

    result = controller.start(repo_root=repo_root, objective="Build")

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "unknown"
    assert result.pending_request.request_id == "77"
    assert result.pending_request.requested_scope == {
        "raw_method": "item/unknown/broken"
    }

    # D4 carve-out: parse failures stay "pending" — NOT updated to "resolved".
    stored = prs.get("77")
    assert stored is not None
    assert stored.status == "pending"


def test_start_with_no_server_requests_returns_delegation_job(tmp_path: Path) -> None:
    """Clean completion (no server requests) → DelegationJob, runtime released and closed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, registry, _prs = (
        _build_controller(tmp_path)
    )

    # No server requests configured — clean turn completion.
    result = controller.start(repo_root=repo_root, objective="Refactor")

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
    assert result.job_id == "job-1"

    # Runtime released and session closed.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


def test_start_turn_dispatch_failure_marks_job_unknown_and_cleans_up(
    tmp_path: Path,
) -> None:
    """If run_execution_turn() raises, the job is marked unknown, the runtime
    is released, and the session is closed — not left stuck running."""
    controller, control_plane, _, job_store, _, _, registry, _ = _build_controller(
        tmp_path
    )
    control_plane._next_raise_on_turn = RuntimeError("transport died")

    with pytest.raises(RuntimeError, match="transport died"):
        controller.start(
            repo_root=tmp_path / "repo",
            objective="Should fail",
        )

    # Job should be "unknown", not stuck "running".
    jobs = job_store.list_active()
    assert len(jobs) == 0, f"Expected no active jobs, got: {[j.status for j in jobs]}"

    # Runtime released and session closed.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


def test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up(
    tmp_path: Path,
) -> None:
    """If a post-turn local write (e.g. audit emit) raises after
    run_execution_turn() succeeds, the job is still marked unknown and
    the runtime is released."""
    controller, control_plane, _, job_store, _, journal, registry, _ = (
        _build_controller(tmp_path)
    )

    # Configure a command-approval request so the capture path fires.
    control_plane._next_session_requests = [
        {
            "id": "req-1",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "make build",
                "cwd": "/repo",
            },
        },
    ]
    control_plane._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="was building",
    )

    # Sabotage the audit emit so _finalize_turn raises after the turn
    # has already completed successfully. The first call (delegate_start
    # audit in committed-start phase) must succeed; only the second call
    # (escalation audit in _finalize_turn) should fail.
    original_append = journal.append_audit_event
    call_count = 0

    def _exploding_audit_on_second(event: Any) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise OSError("disk full")
        original_append(event)

    journal.append_audit_event = _exploding_audit_on_second  # type: ignore[assignment]

    with pytest.raises(OSError, match="disk full"):
        controller.start(
            repo_root=tmp_path / "repo",
            objective="Audit failure test",
        )

    # Job should be "unknown", not stuck "running" or "needs_escalation".
    jobs = job_store.list_active()
    assert len(jobs) == 0, f"Expected no active jobs, got: {[j.status for j in jobs]}"

    # Runtime released and session closed despite the failure.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


def test_start_with_request_user_input_completed_returns_delegation_job(
    tmp_path: Path,
) -> None:
    """request_user_input + completed turn → DelegationJob, not DelegationEscalation.

    When a no-cancel known kind (request_user_input) is captured but the turn
    completes normally, the job is completed — not escalated. The runtime is
    released, the session is closed, the pending request is resolved, and no
    escalation audit event is emitted.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, journal, registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_request_user_input_request()]

    result = controller.start(repo_root=repo_root, objective="Summarize")

    # Returns a plain DelegationJob, not a DelegationEscalation.
    assert isinstance(result, DelegationJob)
    assert result.status == "completed"

    # Pending request was persisted and resolved (D4).
    stored = prs.get("55")
    assert stored is not None
    assert stored.status == "resolved"

    # Runtime released and session closed — not kept live.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed

    # No escalation audit event emitted.
    events_path = journal.plugin_data_path / "audit" / "events.jsonl"
    lines = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]
    escalation_events = [e for e in lines if e.get("action") == "escalate"]
    assert len(escalation_events) == 0


def test_later_parse_failure_does_not_prevent_captured_request_resolution(
    tmp_path: Path,
) -> None:
    """First request parses fine, second message fails parse → first resolved.

    The captured_request_parse_failed flag should only apply to the captured
    (first) request. A later malformed message should still trigger
    interrupted_by_unknown (escalation), but the successfully-parsed first
    request must still be marked resolved.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, registry, prs = (
        _build_controller(tmp_path)
    )

    # First message: parseable command_approval. Second: unparseable.
    control_plane._next_session_requests = [
        _command_approval_request(request_id=10, item_id="item-ok"),
        {"id": 11, "method": "broken/method", "params": "not-a-dict"},
    ]
    # The second message triggers interrupt, so the turn ends interrupted.
    control_plane._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="interrupted by unknown",
    )

    result = controller.start(repo_root=repo_root, objective="Mixed")

    # Should escalate (interrupted_by_unknown from the second message).
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"

    # The FIRST request (successfully parsed) must be resolved — not left
    # pending due to a later message's parse failure.
    stored = prs.get("10")
    assert stored is not None
    assert stored.status == "resolved"

    # Only the first request was persisted (first-capture semantics).
    assert prs.get("11") is None

    # Runtime kept live for escalation.
    assert registry.lookup("rt-1") is not None


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
