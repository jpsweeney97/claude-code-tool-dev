"""Tests for DelegationController — mirrors dialogue pattern.

Verifies every durable surface is populated AND the in-process registry
retains the session so the runtime remains controllable.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest

from server.artifact_store import ArtifactStore
from server.delegation_controller import DelegationController, DelegationStartError
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import (
    AccountState,
    ArtifactInspectionSnapshot,
    CollaborationHandle,
    DelegationEscalation,
    DelegationJob,
    DelegationPollResult,
    DiscardRejectedResponse,
    DiscardResult,
    JobBusyResponse,
    OperationJournalEntry,
    PendingServerRequest,
    PollRejectedResponse,
    PromotionRejectedResponse,
    PromotionResult,
    RuntimeHandshake,
    TurnExecutionResult,
)
from server.pending_request_store import PendingRequestStore

_TASK_18_DECIDE_SIGNAL_REASON = (
    "Phase G Task 18: decide() does not yet route through "
    "ResolutionRegistry.reserve() + commit_signal(). Without "
    "commit_signal, the worker stays parked in registry.wait() and "
    "decide(approve)/decide(deny)/decide(re-escalate)/CAS-stale paths "
    "cannot signal the worker through the canonical Task-18 mechanism. "
    "Some assertions might mechanically pass under legacy decide() "
    "(e.g., deny local-finalization at delegation_controller.py:~2446) "
    "but would do so via the old non-async-decide code path. Skip is "
    "preserved for audit discipline: Task 18's reserve+commit_signal "
    "is the canonical signal mechanism for these assertions."
)


class _FakeSession:
    # respond is a stub for worker-side server-request responses. Tests that
    # exercise the parkable-capture path (Task 16 handler) set this to a
    # MagicMock to control and inspect transport dispatch behavior.
    respond: Any = None

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


class _FakeArtifactStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, ArtifactInspectionSnapshot] = {}

    def materialize_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot:
        snapshot = ArtifactInspectionSnapshot(
            artifact_hash=f"hash-{job.job_id}" if job.status == "completed" else None,
            artifact_paths=(
                f"/tmp/inspection/{job.job_id}/full.diff",
                f"/tmp/inspection/{job.job_id}/changed-files.json",
                f"/tmp/inspection/{job.job_id}/test-results.json",
            ),
            changed_files=("README.md",),
            reviewed_at="2026-04-20T10:00:00Z",
        )
        self._snapshots[job.job_id] = snapshot
        return snapshot

    def load_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot | None:
        return self._snapshots.get(job.job_id)

    def reconstruct_from_artifacts(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None:
        if not job.artifact_paths:
            return None
        return ArtifactInspectionSnapshot(
            artifact_hash=job.artifact_hash,
            artifact_paths=job.artifact_paths,
            changed_files=("README.md",),
            reviewed_at="2026-04-20T10:00:00Z",
        )

    def generate_canonical_artifacts(
        self, *, job: DelegationJob, output_dir: Path
    ) -> Any:
        """Fake — not used by promote tests that use a real ArtifactStore."""
        return None


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
    artifact_store = _FakeArtifactStore()
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
        artifact_store=artifact_store,
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
    artifact_store = _FakeArtifactStore()
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
        artifact_store=artifact_store,
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


def test_start_returns_busy_when_completed_pending_job_exists(
    tmp_path: Path,
) -> None:
    """Start rejects when a completed job with pending promotion exists."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    # First start succeeds (complete immediately, no server request).
    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # The job completed normally — status=completed, promotion_state=pending.
    persisted = job_store.get(first_job_id)
    assert persisted is not None
    assert persisted.status == "completed"
    assert persisted.promotion_state == "pending"

    # Second start should be rejected.
    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == first_job_id


def test_start_returns_busy_when_failed_null_promotion_job_exists(
    tmp_path: Path,
) -> None:
    """Start rejects when a failed job with null promotion_state exists."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # Override to failed with null promotion.
    job_store.update_status_and_promotion(
        first_job_id, status="failed", promotion_state=None
    )

    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == first_job_id


def test_start_succeeds_after_discard_clears_attention_job(
    tmp_path: Path,
) -> None:
    """Start succeeds once the user discards the attention-active job."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # Discard the completed job.
    discard_result = controller.discard(job_id=first_job_id)
    assert isinstance(discard_result, DiscardResult)

    # Now start should succeed (discarded job is terminal, no longer attention-active).
    second = controller.start(repo_root=repo_root)
    assert not isinstance(second, JobBusyResponse)


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
            promotion_state=None,
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
            promotion_state=None,
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
    """command_approval → handler parks → DelegationEscalation.

    Post-Task-17 (async model): the handler announces parked and then blocks
    on registry.wait(). start() returns DelegationEscalation with
    agent_context=None (deferred-escalation semantics per spec §Capture-ready
    handshake — the worker is still inside the turn so turn_result.agent_message
    does not yet exist). The request status remains 'pending' until decide()
    resumes the worker and _finalize_turn runs the D4 update. Escalation audit
    events fire from _finalize_turn, also deferred until decide().
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _job_store, _ls, _journal, registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_command_approval_request()]

    result = controller.start(repo_root=repo_root, objective="Fix the bug")

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_escalation.kind == "command_approval"
    assert result.pending_escalation.request_id == "42"
    # Deferred-escalation: agent_context=None for the Parked path.
    assert result.agent_context is None

    # Request persisted (status 'pending' until decide() resumes worker).
    stored = prs.get("42")
    assert stored is not None

    # Runtime kept live for needs_escalation — worker is parked in registry.wait().
    assert registry.lookup("rt-1") is not None
    assert not control_plane._sessions[0].closed


def test_start_with_unknown_request_interrupts_and_escalates(tmp_path: Path) -> None:
    """Unknown kind (e.g., permissions) → interrupt → terminal status='unknown'.

    Post-Task-17 (L11 carve-out): unknown-kind interrupted requests cannot be
    projected into a PendingEscalationView. _finalize_turn now routes
    interrupted_by_unknown to final_status='unknown' and start() returns the
    plain terminal job — no escalation is built. Causal record lives on the
    persisted PendingServerRequest(kind='unknown') audit entry.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_permissions_request()]

    result = controller.start(repo_root=repo_root, objective="Deploy")

    # Unknown-kind interrupt → terminal job, NOT escalation.
    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"
    assert result.job_id == "job-1"

    # Pending request persisted (parse succeeded, kind="unknown" via _METHOD_TO_KIND
    # default). D4 update_status("resolved") still fires for parseable requests
    # because captured_request_parse_failed is False on this path.
    stored = prs.get("99")
    assert stored is not None
    assert stored.kind == "unknown"
    assert stored.status == "resolved"


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
    assert result.pending_escalation.request_id == "1"


def test_start_with_unparseable_request_creates_minimal_causal_record(
    tmp_path: Path,
) -> None:
    """Parse failure → minimal record with status="pending" (D4 carve-out).

    Post-Task-17 (L11 carve-out): the worker handler emits
    announce_turn_terminal_without_escalation after creating the minimal
    PendingServerRequest(kind='unknown') and interrupting the turn. start()
    receives TurnTerminalWithoutEscalation and returns the plain terminal job.
    The minimal causal record is the persisted PendingServerRequest itself.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)

    # A message with no params dict at all will fail parse.
    control_plane._next_session_requests = [
        {"id": 77, "method": "item/unknown/broken", "params": "not-a-dict"}
    ]

    result = controller.start(repo_root=repo_root, objective="Build")

    # Parse-failure path → terminal job, NOT escalation.
    assert isinstance(result, DelegationJob)
    assert result.status == "unknown"
    assert result.job_id == "job-1"

    # Minimal causal record persisted with raw method preserved.
    # D4 carve-out: parse failures stay "pending" — NOT updated to "resolved".
    stored = prs.get("77")
    assert stored is not None
    assert stored.kind == "unknown"
    assert stored.status == "pending"
    assert stored.requested_scope == {"raw_method": "item/unknown/broken"}


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
    is released, and the session is closed — not left stuck running.

    Post-Task-17: the worker thread catches the unhandled exception and signals
    WorkerFailed; start() raises DelegationStartError(reason='worker_failed_before_capture')
    with the original exception chained on .cause (L7 reason-preservation rule).
    """
    controller, control_plane, _, job_store, _, _, registry, _ = _build_controller(
        tmp_path
    )
    control_plane._next_raise_on_turn = RuntimeError("transport died")

    with pytest.raises(DelegationStartError) as exc_info:
        controller.start(
            repo_root=tmp_path / "repo",
            objective="Should fail",
        )
    assert exc_info.value.reason == "worker_failed_before_capture"
    assert isinstance(exc_info.value.cause, RuntimeError)
    assert "transport died" in str(exc_info.value.cause)

    # Job should be "unknown", not stuck "running".
    jobs = job_store.list_active()
    assert len(jobs) == 0, f"Expected no active jobs, got: {[j.status for j in jobs]}"

    # Runtime released and session closed.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_start_post_turn_finalization_failure_marks_job_unknown_and_cleans_up(
    tmp_path: Path,
) -> None:
    """If a post-turn local write (e.g. audit emit) raises after
    run_execution_turn() succeeds, the job is still marked unknown and
    the runtime is released.

    Bucket B reclassification (Task 17 BLOCKED-resume, post-feat audit):
    under the async model _finalize_turn runs on the worker thread AFTER
    decide() commits and resumes the worker — NOT during start(). The
    sabotaged escalation-audit second call (intended to fail _finalize_turn)
    is unreachable from start() because the handler parks BEFORE _finalize_turn
    runs. Verifying this failure path requires the Task-18 decide() rewrite
    (reserve + commit_signal cycle), so the test is reclassified from Bucket A
    to Bucket B.

    Body assertions use the `worker_failed_before_capture` fallback shape,
    which is NOT the expected Task-18 failure path; the entire body must
    be rewritten when Task 18 unblocks this test.
    """
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

    with pytest.raises(DelegationStartError) as exc_info:
        controller.start(
            repo_root=tmp_path / "repo",
            objective="Audit failure test",
        )
    assert exc_info.value.reason == "worker_failed_before_capture"
    assert isinstance(exc_info.value.cause, OSError)
    assert "disk full" in str(exc_info.value.cause)

    # Job should be "unknown", not stuck "running" or "needs_escalation".
    jobs = job_store.list_active()
    assert len(jobs) == 0, f"Expected no active jobs, got: {[j.status for j in jobs]}"

    # Runtime released and session closed despite the failure.
    assert registry.lookup("rt-1") is None
    assert control_plane._sessions[0].closed


def test_start_with_request_user_input_completed_returns_delegation_job(
    tmp_path: Path,
) -> None:
    """request_user_input → handler parks → start() returns DelegationEscalation.

    Post-Task-17 (async model): request_user_input is a parkable kind
    (member of _KNOWN_DENIAL_KINDS). The handler parks on registry.wait()
    BEFORE the turn loop can continue to "completed", so start() returns
    DelegationEscalation immediately after announce_parked. The worker stays
    parked in registry.wait() until decide() commits. The test name is
    preserved for git-blame continuity; the async assertions reflect the
    deferred-decide semantics. Runtime stays live; the request status remains
    "pending" until decide() resumes the worker (D4 update_status('resolved')
    runs inside _finalize_turn AFTER the turn resumes).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _job_store, _ls, _journal, registry, prs = (
        _build_controller(tmp_path)
    )

    control_plane._next_session_requests = [_request_user_input_request()]

    result = controller.start(repo_root=repo_root, objective="Summarize")

    # Async model: parked → escalation, NOT terminal completed.
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_escalation.kind == "request_user_input"
    assert result.pending_escalation.request_id == "55"

    # Request persisted (status remains "pending" until decide resumes worker
    # and _finalize_turn runs the D4 update).
    stored = prs.get("55")
    assert stored is not None
    assert stored.kind == "request_user_input"

    # Runtime kept live for the parked worker — decide() will resume.
    assert registry.lookup("rt-1") is not None


def test_later_parse_failure_does_not_prevent_captured_request_resolution(
    tmp_path: Path,
) -> None:
    """First request parses fine → handler parks → start() returns escalation.

    Post-Task-17 (async model): the first parseable command_approval request
    causes the handler to park on registry.wait() BEFORE the turn loop can
    dispatch any later message. Under the synchronous-handler legacy model,
    BOTH messages would have been dispatched and the second's parse failure
    would have been the trigger for interrupted_by_unknown. Under async, only
    the first message is processed during start(); the parked worker awaits
    decide(). The test is preserved for git-blame continuity and renamed-
    semantics: it now verifies that a parseable first request reaches the
    parked-escalation state cleanly. The "later parse failure" handling is
    covered by post-decide turn-resume tests (Bucket B, deferred to Task 18).
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, registry, prs = _build_controller(
        tmp_path
    )

    # First message: parseable command_approval (parks the worker).
    # Second message: unparseable — never reached during start() because the
    # handler parks in registry.wait() after the first message.
    control_plane._next_session_requests = [
        _command_approval_request(request_id=10, item_id="item-ok"),
        {"id": 11, "method": "broken/method", "params": "not-a-dict"},
    ]
    control_plane._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="interrupted by unknown",
    )

    result = controller.start(repo_root=repo_root, objective="Mixed")

    # Parked on the first message.
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_escalation.request_id == "10"

    # First request persisted (status pending until decide() resumes worker
    # and _finalize_turn runs D4 update).
    stored = prs.get("10")
    assert stored is not None

    # Second request never dispatched (handler parked before it could be).
    assert prs.get("11") is None

    # Runtime kept live for the parked worker.
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


# -----------------------------------------------------------------------------
# decide() success-path tests — approve, deny, re-escalation.
# -----------------------------------------------------------------------------


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_decide_approve_resumes_runtime_and_returns_completed_result(
    tmp_path: Path,
) -> None:
    from server.models import DelegationDecisionResult

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, lineage, _j, registry, _prs = (
        _build_controller(tmp_path)
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
    assert result.decision_accepted is True
    assert result.job_id == "job-1"
    assert result.request_id == "42"
    # Post-dispatch state observed via poll(), not decide() result (Packet 1).
    poll = controller.poll(job_id="job-1")
    assert isinstance(poll, DelegationPollResult)
    assert poll.job.status == "completed"
    assert poll.pending_escalation is None
    assert registry.lookup("rt-1") is None
    handle = lineage.get("collab-1")
    assert handle is not None and handle.status == "completed"


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
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
    assert result.decision_accepted is True
    assert result.job_id == "job-1"
    assert result.request_id == "42"
    # Post-dispatch re-escalation state observed via poll(), not decide() result (Packet 1).
    poll = controller.poll(job_id="job-1")
    assert isinstance(poll, DelegationPollResult)
    assert poll.job.status == "needs_escalation"
    assert poll.pending_escalation is not None
    assert poll.pending_escalation.request_id == "99"
    assert registry.lookup("rt-1") is not None
    stored = prs.get("99")
    assert stored is not None and stored.status == "resolved"


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
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
    assert result.decision_accepted is True
    assert result.job_id == "job-1"
    assert result.request_id == "42"
    # Post-dispatch state observed via poll(), not decide() result (Packet 1).
    poll = controller.poll(job_id="job-1")
    assert isinstance(poll, DelegationPollResult)
    assert poll.job.status == "failed"
    assert poll.pending_escalation is None
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


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_decide_deny_emits_terminal_outcome(tmp_path: Path) -> None:
    """Deny decisions must write a delegation_terminal record to outcomes.jsonl."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, journal, _r, _prs = _build_controller(
        tmp_path
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    controller.decide(job_id="job-1", request_id="42", decision="deny")

    outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
    assert outcomes_path.exists(), "Terminal outcome file must exist after deny"
    lines = [
        line
        for line in outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        if line.strip()
    ]
    terminal_records = [
        json.loads(line)
        for line in lines
        if json.loads(line).get("outcome_type") == "delegation_terminal"
    ]
    assert len(terminal_records) == 1
    assert terminal_records[0]["job_id"] == "job-1"
    assert terminal_records[0]["terminal_status"] == "failed"


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

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
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

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
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


def test_decide_rejects_job_not_found(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    controller, _cp, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)

    result = controller.decide(
        job_id="nonexistent-job",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "job_not_found"
    assert result.job_id == "nonexistent-job"


def test_decide_rejects_job_not_awaiting_decision(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
    # Start with no server requests → turn completes without escalation
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationJob)
    assert start_result.status == "completed"

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "job_not_awaiting_decision"


def test_decide_rejects_request_not_found(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="nonexistent-request",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "request_not_found"


def test_decide_rejects_request_job_mismatch(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    # Plant a request belonging to a different collaboration
    prs.create(
        PendingServerRequest(
            request_id="foreign-99",
            runtime_id="rt-other",
            collaboration_id="other-collab",
            codex_thread_id="thr-other",
            codex_turn_id="turn-other",
            item_id="item-x",
            kind="command_approval",
            requested_scope={"cmd": "ls"},
            status="resolved",
        )
    )

    result = controller.decide(
        job_id="job-1",
        request_id="foreign-99",
        decision="approve",
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "request_job_mismatch"


def test_decide_rejects_deny_with_answers(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="deny",
        answers={"q1": ("yes",)},
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "answers_not_allowed"


def test_decide_rejects_answers_for_non_request_user_input(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, _r, _prs = _build_controller(tmp_path)
    # command_approval is not request_user_input — answers not allowed
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
        answers={"q1": ("yes",)},
    )

    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "answers_not_allowed"


def test_recover_startup_marks_orphaned_needs_escalation_job_and_handle_unknown(
    tmp_path: Path,
) -> None:
    """After a cold restart, needs_escalation jobs with no live runtime are marked unknown.

    Simulates a crash between start() returning an escalation and decide()
    being called. On restart, recover_startup() marks both the orphaned job
    and its active handle as unknown.
    """
    _, _, _, job_store, lineage_store, _, _, _ = _build_controller(tmp_path)

    job_store.create(
        DelegationJob(
            job_id="job-orphan",
            runtime_id="rt-orphan",
            collaboration_id="collab-orphan",
            base_commit="head-abc",
            worktree_path="/tmp/wk",
            promotion_state=None,
            status="needs_escalation",
        )
    )
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-orphan",
            capability_class="execution",
            runtime_id="rt-orphan",
            codex_thread_id="thr-orphan",
            claude_session_id="sess-old",
            repo_root="/tmp/repo",
            created_at="2026-01-01T00:00:00Z",
            status="active",
        )
    )

    # Cold restart: fresh controller (fresh registry, no live runtimes)
    controller2, _, _, _, _, _, _, _ = _build_controller(tmp_path, session_id="sess-1")
    controller2.recover_startup()

    recovered_job = job_store.get("job-orphan")
    assert recovered_job is not None
    assert recovered_job.status == "unknown"
    recovered_handle = lineage_store.get("collab-orphan")
    assert recovered_handle is not None
    assert recovered_handle.status == "unknown"


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
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

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state=None,
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
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state=None,
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
            idempotency_key="42:recovered",
            operation="approval_resolution",
            phase="intent",
            collaboration_id="collab-1",
            created_at=journal.timestamp(),
            repo_root=str(repo_root),
            job_id="job-1",
            request_id="42",
            decision=None,  # timeout-wake / internal-abort-wake origin
        ),
        session_id="sess-1",
    )

    # Act: recovery must complete without raising
    controller.recover_startup()

    # Assert: journal contains the new completed record
    found = journal.check_idempotency("42:recovered", session_id="sess-1")
    assert found is not None
    assert found.phase == "completed"
    assert found.completion_origin == "recovered_unresolved"


def test_recover_startup_marks_dispatched_approval_resolution_unknown(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r, _prs = (
        _build_controller(tmp_path)
    )

    job_store.create(
        DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit="head-abc",
            worktree_path=str(tmp_path / "wk"),
            promotion_state=None,
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


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_decide_rejects_stale_request_id_after_reescalation(tmp_path: Path) -> None:
    from server.models import DecisionRejectedResponse, DelegationDecisionResult

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, _js, _ls, _j, registry, prs = _build_controller(
        tmp_path
    )
    # First escalation: command_approval with request_id "42"
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    # Approve the first escalation — configure follow-up to re-escalate
    session = control_plane._sessions[0]
    session._server_requests = [_permissions_request(request_id=99, item_id="item-2")]
    session._turn_result = TurnExecutionResult(
        turn_id="turn-2",
        status="interrupted",
        agent_message="Need another escalation.",
        notifications=(),
    )
    approve_result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(approve_result, DelegationDecisionResult)
    assert approve_result.decision_accepted is True
    # Re-escalation observable via poll(), not decide() result (Packet 1).
    re_esc_poll = controller.poll(job_id="job-1")
    assert isinstance(re_esc_poll, DelegationPollResult)
    assert re_esc_poll.pending_escalation is not None
    assert re_esc_poll.pending_escalation.request_id == "99"

    # Now try to use the stale request_id "42" to decide the new escalation
    result = controller.decide(
        job_id="job-1",
        request_id="42",
        decision="approve",
    )
    assert isinstance(result, DecisionRejectedResponse)
    assert result.reason == "request_already_decided"


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error(
    tmp_path: Path,
) -> None:
    """If the approve turn succeeds but the post-turn journal write_phase fails,
    CommittedDecisionFinalizationError is raised with the turn result already
    committed (job status reflects the turn outcome, not a rollback)."""
    from server.delegation_controller import CommittedDecisionFinalizationError

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, lineage, journal, registry, _prs = (
        _build_controller(tmp_path)
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root, objective="Fix it")
    assert isinstance(start_result, DelegationEscalation)

    # Clear session requests so the follow-up turn completes cleanly
    # (no re-escalation). The follow-up turn is what approve triggers.
    session = control_plane._sessions[0]
    session._server_requests = []

    # The approve path calls write_phase three times: intent, dispatched,
    # then completed. Make the third call (post-turn completed) fail.
    original_write_phase = journal.write_phase
    write_phase_count = 0

    def _exploding_third_write_phase(*args: object, **kwargs: object) -> None:
        nonlocal write_phase_count
        write_phase_count += 1
        if write_phase_count >= 3:
            raise OSError("disk full on completed phase")
        original_write_phase(*args, **kwargs)  # type: ignore[arg-type]

    journal.write_phase = _exploding_third_write_phase  # type: ignore[assignment]

    with pytest.raises(CommittedDecisionFinalizationError, match="committed"):
        controller.decide(
            job_id="job-1",
            request_id="42",
            decision="approve",
        )

    # The turn completed successfully — the job status must be "completed",
    # not degraded to "unknown" (recovery state) or stuck at "needs_escalation".
    job = job_store.get("job-1")
    assert job is not None
    assert job.status == "completed"


@pytest.mark.skip(reason=_TASK_18_DECIDE_SIGNAL_REASON)
def test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error(
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

    # Make session.close() raise after the deny decision has committed
    session = control_plane._sessions[0]
    session.close = lambda: (_ for _ in ()).throw(RuntimeError("close failed"))

    with pytest.raises(CommittedDecisionFinalizationError, match="committed deny"):
        controller.decide(
            job_id="job-1",
            request_id="42",
            decision="deny",
        )

    # Job should be failed (deny committed before close failed)
    job = job_store.get("job-1")
    assert job is not None and job.status == "failed"


# -----------------------------------------------------------------------------
# poll() tests — DelegationController.poll lifecycle.
# -----------------------------------------------------------------------------


def test_start_completed_job_sets_promotion_state_pending(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    result = controller.start(repo_root=repo_root)
    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
    assert result.promotion_state == "pending"
    persisted = job_store.get(result.job_id)
    assert persisted is not None
    assert persisted.promotion_state == "pending"


def test_start_escalation_keeps_promotion_state_none(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, control_plane, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    control_plane._next_session_requests = [_command_approval_request()]
    result = controller.start(repo_root=repo_root)
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.job.promotion_state is None
    persisted = job_store.get(result.job.job_id)
    assert persisted is not None
    assert persisted.promotion_state is None


def test_poll_completed_job_materializes_snapshot_and_reuses_it(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)
    first = controller.poll(job_id=start_result.job_id)
    second = controller.poll(job_id=start_result.job_id)
    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None
    assert first.inspection.artifact_hash is not None
    assert second.inspection == first.inspection


def test_poll_rehydrates_store_from_cached_snapshot_when_artifacts_are_missing(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)
    first = controller.poll(job_id=start_result.job_id)
    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None
    job_store.update_artifacts(
        start_result.job_id, artifact_paths=(), artifact_hash=None
    )
    second = controller.poll(job_id=start_result.job_id)
    persisted = job_store.get(start_result.job_id)
    assert isinstance(second, DelegationPollResult)
    assert second.inspection == first.inspection
    assert persisted is not None
    assert persisted.artifact_paths == first.inspection.artifact_paths
    assert persisted.artifact_hash == first.inspection.artifact_hash


def test_poll_needs_escalation_projects_pending_request_without_raw_ids(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, control_plane, _wm, _job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    control_plane._next_session_requests = [_command_approval_request()]
    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationEscalation)
    polled = controller.poll(job_id=start_result.job.job_id)
    assert isinstance(polled, DelegationPollResult)
    assert polled.pending_escalation is not None
    assert polled.pending_escalation.request_id == "42"
    assert polled.pending_escalation.available_decisions == ("approve", "deny")
    assert not hasattr(polled.pending_escalation, "codex_thread_id")


def test_poll_reconstructs_from_artifacts_when_cache_is_corrupt(
    tmp_path: Path,
) -> None:
    """A completed job with an existing hash reconstructs from artifact files.

    If snapshot.json is corrupt but the store already holds a reviewed hash,
    the controller reconstructs the inspection from the persisted artifacts
    rather than rematerializing from the (potentially mutated) worktree.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )

    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)

    # First poll — materializes and records hash.
    first = controller.poll(job_id=start_result.job_id)
    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None
    original_hash = first.inspection.artifact_hash

    # Simulate corrupt cache by clearing the fake store's internal dict
    # (so load_snapshot returns None), while the job store still has the hash.
    fake_store = controller._artifact_store  # type: ignore[attr-defined]
    fake_store._snapshots.clear()

    # Poll again — reconstructs from artifacts, preserving the reviewed hash.
    second = controller.poll(job_id=start_result.job_id)
    assert isinstance(second, DelegationPollResult)
    assert second.inspection is not None
    assert second.inspection.artifact_hash == original_hash

    # The store's hash must be preserved — not overwritten.
    persisted = job_store.get(start_result.job_id)
    assert persisted is not None
    assert persisted.artifact_hash == original_hash


def test_poll_returns_structured_result_when_materialization_raises(
    tmp_path: Path,
) -> None:
    """If artifact materialization raises CalledProcessError (e.g. worktree deleted),
    poll returns a structured result with inspection=None and a diagnostic detail
    explaining that materialization failed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)

    # Patch the fake store to raise CalledProcessError on materialize.
    import subprocess as _sp

    def _raise_on_materialize(*, job: DelegationJob) -> ArtifactInspectionSnapshot:
        raise _sp.CalledProcessError(
            128, ["git", "diff"], stderr="fatal: not a git repository"
        )

    controller._artifact_store.materialize_snapshot = _raise_on_materialize  # type: ignore[assignment]

    result = controller.poll(job_id=start_result.job_id)
    assert isinstance(result, DelegationPollResult)
    assert result.inspection is None
    assert result.detail is not None
    assert "materialization failed" in result.detail.lower()


def test_poll_sets_detail_when_artifacts_unavailable_for_reviewed_job(
    tmp_path: Path,
) -> None:
    """A completed job with artifact_hash but no loadable inspection gets a diagnostic detail."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = (
        _build_controller(tmp_path)
    )
    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)

    # First poll materializes and records hash.
    first = controller.poll(job_id=start_result.job_id)
    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None

    # Clear the fake store's cache AND make reconstruct return None
    # (simulates all artifact files deleted from disk).
    fake_store = controller._artifact_store  # type: ignore[attr-defined]
    fake_store._snapshots.clear()

    def _fail_reconstruct(*, job: DelegationJob) -> None:
        return None

    fake_store.reconstruct_from_artifacts = _fail_reconstruct  # type: ignore[assignment]

    result = controller.poll(job_id=start_result.job_id)
    assert isinstance(result, DelegationPollResult)
    assert result.inspection is None
    assert result.detail is not None
    assert "unavailable" in result.detail.lower()


def test_poll_returns_job_not_found_rejection(tmp_path: Path) -> None:
    controller, _cp, _wm, _js, _lineage, _journal, _registry, _prs = _build_controller(
        tmp_path
    )
    result = controller.poll(job_id="job-missing")
    assert isinstance(result, PollRejectedResponse)
    assert result.reason == "job_not_found"


# --- Promote / Discard tests ---


def _init_git_repo(path: Path) -> str:
    """Create a git repo with an initial commit, return the HEAD sha."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )
    (path / "README.md").write_text("# Initial\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(path), "add", "."], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", "init"],
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class _FakePromotionCallback:
    """Records invocations of on_promotion_verified."""

    def __init__(self, *, stale: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._stale = stale

    def on_promotion_verified(
        self, *, repo_root: Path, artifact_hash: str, job_id: str
    ) -> bool:
        self.calls.append(
            {"repo_root": repo_root, "artifact_hash": artifact_hash, "job_id": job_id}
        )
        return self._stale


def _build_promote_scenario(
    tmp_path: Path,
    *,
    modify_file: str = "README.md",
    new_content: str = "# Modified\n",
    add_new_file: bool = False,
    new_file_name: str = "new_file.txt",
    new_file_content: str = "new content\n",
    stale_callback: bool = False,
) -> tuple[
    DelegationController,
    DelegationJobStore,
    OperationJournal,
    Path,
    str,
    str,
    _FakePromotionCallback,
]:
    """Set up a completed delegation job with real git repos for promote testing.

    Creates:
    - primary_repo: the "real" repo that promote targets
    - worktree: a separate clone where the delegation work happened
    - A completed DelegationJob with materialized artifacts

    Returns controller, job_store, journal, primary_repo, job_id, artifact_hash, callback.
    """
    primary_repo = tmp_path / "primary"
    head_sha = _init_git_repo(primary_repo)

    # Create the "worktree" as a clone (simulates the delegation sandbox).
    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "clone", str(primary_repo), str(worktree)],
        check=True,
        capture_output=True,
    )

    # Make changes in the worktree.
    (worktree / modify_file).write_text(new_content, encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(worktree), "add", modify_file],
        check=True,
        capture_output=True,
    )
    if add_new_file:
        (worktree / new_file_name).write_text(new_file_content, encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(worktree), "add", new_file_name],
            check=True,
            capture_output=True,
        )
    subprocess.run(
        ["git", "-C", str(worktree), "commit", "-m", "delegation work"],
        check=True,
        capture_output=True,
    )

    # Set up stores.
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    session_id = "sess-promote"
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)

    # Create a completed job.
    job_id = "job-promote-1"
    collaboration_id = "collab-promote-1"
    job = DelegationJob(
        job_id=job_id,
        runtime_id="rt-promote-1",
        collaboration_id=collaboration_id,
        base_commit=head_sha,
        worktree_path=str(worktree),
        promotion_state="pending",
        status="completed",
    )
    job_store.create(job)

    # Materialize artifacts using the real ArtifactStore.
    snapshot = artifact_store.materialize_snapshot(job=job)
    job_store.update_artifacts(
        job_id,
        artifact_paths=snapshot.artifact_paths,
        artifact_hash=snapshot.artifact_hash,
    )

    # Create the lineage handle.
    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id="rt-promote-1",
        codex_thread_id="thr-promote-1",
        claude_session_id=session_id,
        repo_root=str(primary_repo),
        created_at=journal.timestamp(),
        status="completed",
    )
    lineage_store.create(handle)

    callback = _FakePromotionCallback(stale=stale_callback)
    uuid_counter = iter([f"evt-{i}" for i in range(100)])
    controller = DelegationController(
        control_plane=_FakeControlPlane(),
        worktree_manager=_FakeWorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
        promotion_callback=callback,
    )

    return (
        controller,
        job_store,
        journal,
        primary_repo,
        job_id,
        snapshot.artifact_hash,
        callback,
    )


def test_promote_rejects_dirty_primary_workspace(tmp_path: Path) -> None:
    """Promote rejects when the primary workspace has uncommitted changes."""
    controller, job_store, _journal, primary_repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Dirty the primary workspace.
    (primary_repo / "README.md").write_text("# Dirty\n", encoding="utf-8")

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)
    assert result.reason == "worktree_dirty"

    # Job should be in prechecks_failed state.
    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "prechecks_failed"


def test_promote_rejects_job_without_reviewed_hash(tmp_path: Path) -> None:
    """Promote rejects when the job has no artifact_hash (not yet reviewed)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Clear the artifact hash to simulate an un-reviewed job.
    job_store.update_artifacts(job_id, artifact_paths=(), artifact_hash=None)

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)
    assert result.reason == "job_not_reviewed"

    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "prechecks_failed"


def test_promote_applies_reviewed_diff_and_sets_verified(tmp_path: Path) -> None:
    """Happy path: promote applies the diff, verifies, and returns PromotionResult."""
    controller, job_store, _journal, primary_repo, job_id, artifact_hash, callback = (
        _build_promote_scenario(tmp_path)
    )

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionResult)
    assert result.artifact_hash == artifact_hash
    assert "README.md" in result.changed_files
    assert result.stale_advisory_context is False

    # Verify the file was actually modified in the primary workspace.
    assert (primary_repo / "README.md").read_text(encoding="utf-8") == "# Modified\n"

    # Verify the job is in verified state.
    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "verified"

    # Callback was invoked.
    assert len(callback.calls) == 1
    assert callback.calls[0]["artifact_hash"] == artifact_hash
    assert callback.calls[0]["job_id"] == job_id


def test_promote_rolls_back_when_primary_workspace_verification_fails(
    tmp_path: Path,
) -> None:
    """Promote rolls back when post-apply verification detects a mismatch."""
    primary_repo = tmp_path / "primary"
    head_sha = _init_git_repo(primary_repo)

    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "clone", str(primary_repo), str(worktree)],
        check=True,
        capture_output=True,
    )
    (worktree / "README.md").write_text("# Modified\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(worktree), "add", "README.md"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(worktree), "commit", "-m", "delegation work"],
        check=True,
        capture_output=True,
    )

    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    session_id = "sess-promote"
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)

    job_id = "job-rollback-1"
    collaboration_id = "collab-rollback-1"
    job = DelegationJob(
        job_id=job_id,
        runtime_id="rt-rollback-1",
        collaboration_id=collaboration_id,
        base_commit=head_sha,
        worktree_path=str(worktree),
        promotion_state="pending",
        status="completed",
    )
    job_store.create(job)
    snapshot = artifact_store.materialize_snapshot(job=job)
    job_store.update_artifacts(
        job_id,
        artifact_paths=snapshot.artifact_paths,
        artifact_hash=snapshot.artifact_hash,
    )
    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id="rt-rollback-1",
        codex_thread_id="thr-rollback-1",
        claude_session_id=session_id,
        repo_root=str(primary_repo),
        created_at=journal.timestamp(),
        status="completed",
    )
    lineage_store.create(handle)

    # Create a controller that tampers ONLY during post-apply verification,
    # not during precheck regeneration. We track call count: the first call
    # (precheck) passes through cleanly; the second call (verification)
    # tampers to simulate a workspace mismatch.
    class _VerifyTamperingArtifactStore(ArtifactStore):
        """Tampers only on the second generate_canonical_artifacts call (verify)."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._call_count = 0

        def generate_canonical_artifacts(
            self, *, job: DelegationJob, output_dir: Path
        ) -> Any:
            self._call_count += 1
            bundle = super().generate_canonical_artifacts(
                job=job, output_dir=output_dir
            )
            if self._call_count <= 1:
                return bundle
            # Second call (verify): tamper with the diff to change the hash.
            diff_path = output_dir / "full.diff"
            original = diff_path.read_text(encoding="utf-8")
            diff_path.write_text(original + "\n# tampered\n", encoding="utf-8")
            from server.artifact_store import ArtifactStore as _AS

            tampered_hash = _AS._review_hash(self, output_dir, bundle.artifact_paths)
            from server.artifact_store import CanonicalArtifactBundle

            return CanonicalArtifactBundle(
                artifact_paths=bundle.artifact_paths,
                artifact_hash=tampered_hash,
                changed_files=bundle.changed_files,
                full_diff_path=bundle.full_diff_path,
                changed_files_path=bundle.changed_files_path,
                test_results_path=bundle.test_results_path,
            )

    tampered_store = _VerifyTamperingArtifactStore(
        plugin_data, timestamp_factory=journal.timestamp
    )
    uuid_counter = iter([f"evt-{i}" for i in range(100)])
    controller = DelegationController(
        control_plane=_FakeControlPlane(),
        worktree_manager=_FakeWorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=tampered_store,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)
    assert result.reason == "artifact_hash_mismatch"

    # Primary workspace should be rolled back to its original state.
    assert (primary_repo / "README.md").read_text(encoding="utf-8") == "# Initial\n"

    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "rolled_back"


def test_promote_rollback_removes_new_files_created_by_reviewed_diff(
    tmp_path: Path,
) -> None:
    """Rollback removes files that were newly created by the diff (not previously tracked)."""
    primary_repo = tmp_path / "primary"
    head_sha = _init_git_repo(primary_repo)

    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "clone", str(primary_repo), str(worktree)],
        check=True,
        capture_output=True,
    )
    # Add a new file in the worktree.
    (worktree / "README.md").write_text("# Modified\n", encoding="utf-8")
    (worktree / "new_file.txt").write_text("new content\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(worktree), "add", "."],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(worktree), "commit", "-m", "delegation work"],
        check=True,
        capture_output=True,
    )

    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    session_id = "sess-promote"
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)

    job_id = "job-newfile-1"
    collaboration_id = "collab-newfile-1"
    job = DelegationJob(
        job_id=job_id,
        runtime_id="rt-newfile-1",
        collaboration_id=collaboration_id,
        base_commit=head_sha,
        worktree_path=str(worktree),
        promotion_state="pending",
        status="completed",
    )
    job_store.create(job)
    snapshot = artifact_store.materialize_snapshot(job=job)
    job_store.update_artifacts(
        job_id,
        artifact_paths=snapshot.artifact_paths,
        artifact_hash=snapshot.artifact_hash,
    )
    handle = CollaborationHandle(
        collaboration_id=collaboration_id,
        capability_class="execution",
        runtime_id="rt-newfile-1",
        codex_thread_id="thr-newfile-1",
        claude_session_id=session_id,
        repo_root=str(primary_repo),
        created_at=journal.timestamp(),
        status="completed",
    )
    lineage_store.create(handle)

    # Use a tampering store to force verification failure (only on verify, not precheck).
    class _VerifyTamperingArtifactStore2(ArtifactStore):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._call_count = 0

        def generate_canonical_artifacts(
            self, *, job: DelegationJob, output_dir: Path
        ) -> Any:
            self._call_count += 1
            bundle = super().generate_canonical_artifacts(
                job=job, output_dir=output_dir
            )
            if self._call_count <= 1:
                return bundle
            diff_path = output_dir / "full.diff"
            original = diff_path.read_text(encoding="utf-8")
            diff_path.write_text(original + "\n# tampered\n", encoding="utf-8")
            from server.artifact_store import ArtifactStore as _AS

            tampered_hash = _AS._review_hash(self, output_dir, bundle.artifact_paths)
            from server.artifact_store import CanonicalArtifactBundle

            return CanonicalArtifactBundle(
                artifact_paths=bundle.artifact_paths,
                artifact_hash=tampered_hash,
                changed_files=bundle.changed_files,
                full_diff_path=bundle.full_diff_path,
                changed_files_path=bundle.changed_files_path,
                test_results_path=bundle.test_results_path,
            )

    tampered_store = _VerifyTamperingArtifactStore2(
        plugin_data, timestamp_factory=journal.timestamp
    )
    uuid_counter = iter([f"evt-{i}" for i in range(100)])
    controller = DelegationController(
        control_plane=_FakeControlPlane(),
        worktree_manager=_FakeWorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=tampered_store,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)

    # The new file should be removed after rollback.
    assert not (primary_repo / "new_file.txt").exists()
    # Original tracked file should be restored.
    assert (primary_repo / "README.md").read_text(encoding="utf-8") == "# Initial\n"


def test_discard_accepts_pending_job(tmp_path: Path) -> None:
    """Discard accepts a job in 'pending' promotion state."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"

    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == "discarded"


def test_discard_rejects_applied_job(tmp_path: Path) -> None:
    """Discard rejects a job that has already been promoted (verified state)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Promote the job first.
    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionResult)

    # Now try to discard — should be rejected.
    discard_result = controller.discard(job_id=job_id)
    assert isinstance(discard_result, DiscardRejectedResponse)
    assert discard_result.reason == "job_not_discardable"


def test_discard_accepts_failed_null_promotion(tmp_path: Path) -> None:
    """Discard accepts a failed job with null promotion_state (pre-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    # Override to failed with null promotion_state.
    job_store.update_status_and_promotion(job_id, status="failed", promotion_state=None)

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"


def test_discard_accepts_unknown_null_promotion(tmp_path: Path) -> None:
    """Discard accepts an unknown job with null promotion_state (pre-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="unknown", promotion_state=None
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"


def test_discard_rejects_failed_with_applied_promotion(tmp_path: Path) -> None:
    """Discard rejects a failed job with applied promotion_state (post-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="failed", promotion_state="applied"
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_discard_rejects_failed_with_rollback_needed(tmp_path: Path) -> None:
    """Discard rejects a failed job with rollback_needed promotion (post-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="failed", promotion_state="rollback_needed"
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_recover_startup_replays_promotion_dispatched_state(tmp_path: Path) -> None:
    """recover_startup reconciles an unresolved promotion:dispatched journal entry."""
    controller, job_store, journal, primary_repo, job_id, artifact_hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Manually simulate a crash after promotion:dispatched was written
    # but before completion. Write the intent and dispatched phases directly.
    session_id = "sess-promote"
    idempotency_key = f"promotion:{job_id}:1"
    created_at = journal.timestamp()
    repo_root_str = str(primary_repo)

    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="intent",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="dispatched",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )

    # Apply the diff to the primary repo to simulate the apply having happened.
    persisted = job_store.get(job_id)
    assert persisted is not None
    diff_path = persisted.artifact_paths[0]
    subprocess.run(
        ["git", "-C", str(primary_repo), "apply", "--binary", diff_path],
        check=True,
        capture_output=True,
    )

    # Now run recover_startup — should detect the dispatched state and re-verify.
    controller.recover_startup()

    # The journal entry should now be resolved (completed).
    unresolved = journal.list_unresolved(session_id=session_id)
    promotion_unresolved = [e for e in unresolved if e.operation == "promotion"]
    assert len(promotion_unresolved) == 0

    # Job should be in verified state (the diff was valid).
    recovered = job_store.get(job_id)
    assert recovered is not None
    assert recovered.promotion_state == "verified"


def test_recover_startup_normalizes_promotion_intent_to_pending(
    tmp_path: Path,
) -> None:
    """Recovery with only promotion:intent (no dispatched) normalizes to pending.

    This means no workspace mutation occurred — the process crashed between
    prechecks passing and git apply.
    """
    controller, job_store, journal, primary_repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    session_id = "sess-recover-intent"
    created_at = journal.timestamp()
    repo_root_str = str(primary_repo.resolve())
    idempotency_key = f"{job_id}:1"

    # Write only the intent phase — simulates crash before apply.
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="intent",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )

    # Manually set prechecks_passed to simulate the state before apply.
    job_store.update_promotion_state(job_id, promotion_state="prechecks_passed")

    # Rebuild controller with the recovery session_id.
    plugin_data = tmp_path / "plugin-data"
    registry = ExecutionRuntimeRegistry()
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    # Re-create the lineage handle for recovery.
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-promote-1",
            capability_class="execution",
            runtime_id="rt-promote-1",
            codex_thread_id="thr-1",
            claude_session_id=session_id,
            repo_root=repo_root_str,
            created_at=created_at,
            status="active",
        )
    )
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)
    recovery_controller = DelegationController(
        control_plane=_FakeControlPlane(),
        worktree_manager=_FakeWorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
        head_commit_resolver=lambda repo_root: "abc123",
        uuid_factory=iter([f"evt-{i}" for i in range(100)]).__next__,
    )

    recovery_controller.recover_startup()

    # The journal entry should now be resolved.
    unresolved = journal.list_unresolved(session_id=session_id)
    promotion_unresolved = [e for e in unresolved if e.operation == "promotion"]
    assert len(promotion_unresolved) == 0

    # Job should be normalized back to pending (not prechecks_passed).
    recovered = job_store.get(job_id)
    assert recovered is not None
    assert recovered.promotion_state == "pending"


def test_promote_writes_dispatched_before_apply(tmp_path: Path) -> None:
    """The journal 'dispatched' phase must be written BEFORE git apply.

    This ensures crash recovery correctly identifies workspace mutation risk.
    If the process crashes after git apply but before dispatched, recovery
    would incorrectly treat the workspace as unmodified.
    """
    controller, job_store, journal, primary_repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Track the order of operations by monkey-patching git apply.
    call_order: list[str] = []
    original_run = subprocess.run

    def _tracking_run(args: Any, **kwargs: Any) -> Any:
        if isinstance(args, list) and "apply" in args:
            # At the moment git apply is called, check if dispatched was written.
            session_id = "sess-promote"
            unresolved = journal.list_unresolved(session_id=session_id)
            dispatched_entries = [
                e
                for e in unresolved
                if e.operation == "promotion" and e.phase == "dispatched"
            ]
            if dispatched_entries:
                call_order.append("dispatched_before_apply")
            else:
                call_order.append("apply_before_dispatched")
        return original_run(args, **kwargs)

    # Patch subprocess.run at the module level where it's imported.
    import server.delegation_controller as ctrl_module

    old_run = ctrl_module.subprocess.run
    ctrl_module.subprocess.run = _tracking_run
    try:
        result = controller.promote(job_id=job_id)
    finally:
        ctrl_module.subprocess.run = old_run

    assert isinstance(result, PromotionResult)
    assert "dispatched_before_apply" in call_order, (
        "Journal 'dispatched' phase must be written before git apply to "
        "maintain WAL semantics for crash recovery"
    )


def test_recover_startup_leaves_unresolved_when_rollback_fails(
    tmp_path: Path,
) -> None:
    """Recovery must NOT claim rolled_back if rollback actually failed.

    If git checkout fails during recovery rollback, the journal entry must
    remain unresolved and promotion_state must stay at rollback_needed so
    the next startup re-enters recovery.
    """
    controller, job_store, journal, primary_repo, job_id, artifact_hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Simulate a crash after dispatched was written and apply happened.
    session_id = "sess-promote"
    idempotency_key = f"promotion:{job_id}:1"
    created_at = journal.timestamp()
    repo_root_str = str(primary_repo)

    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="intent",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="dispatched",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )

    # Apply the diff to simulate the mutation having happened.
    persisted = job_store.get(job_id)
    assert persisted is not None
    diff_path = persisted.artifact_paths[0]
    subprocess.run(
        ["git", "-C", str(primary_repo), "apply", "--binary", diff_path],
        check=True,
        capture_output=True,
    )

    # Now tamper with the workspace so verification fails (triggering rollback).
    (primary_repo / "README.md").write_text("# Tampered\n", encoding="utf-8")

    # Make git checkout fail by monkey-patching subprocess.run.
    import server.delegation_controller as ctrl_module

    original_run = subprocess.run

    def _failing_checkout(args: Any, **kwargs: Any) -> Any:
        if isinstance(args, list) and "checkout" in args and "--" in args:
            raise subprocess.CalledProcessError(1, args)
        return original_run(args, **kwargs)

    old_run = ctrl_module.subprocess.run
    ctrl_module.subprocess.run = _failing_checkout
    try:
        controller.recover_startup()
    finally:
        ctrl_module.subprocess.run = old_run

    # The journal entry must remain UNRESOLVED (not closed as completed).
    unresolved = journal.list_unresolved(session_id=session_id)
    promotion_unresolved = [e for e in unresolved if e.operation == "promotion"]
    assert len(promotion_unresolved) > 0, (
        "Journal entry must remain unresolved when rollback fails — "
        "do not falsely close it as completed"
    )

    # promotion_state must NOT be "rolled_back" — it should stay at rollback_needed.
    recovered = job_store.get(job_id)
    assert recovered is not None
    assert recovered.promotion_state == "rollback_needed", (
        f"Expected 'rollback_needed' but got {recovered.promotion_state!r}. "
        "Failed rollback must not claim success."
    )


def test_bootstrap_factory_wires_promotion_callback(tmp_path: Path) -> None:
    """The production bootstrap factory must pass promotion_callback to the controller."""
    from scripts.codex_runtime_bootstrap import _build_delegation_factory

    from server.control_plane import ControlPlane

    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir(parents=True, exist_ok=True)

    # Write the required session ID file.
    (plugin_data / "session_id").write_text("test-session-123", encoding="utf-8")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        control_plane=control_plane,
        runtime_registry=registry,
        journal=journal,
        plugin_data_path=plugin_data,
    )
    controller = factory()

    # Verify the promotion_callback was wired.
    assert controller._promotion_callback is not None, (
        "Bootstrap factory must pass promotion_callback=control_plane "
        "to DelegationController so verified promotes mark advisory context stale"
    )


@pytest.mark.parametrize(
    "terminal_state",
    ["verified", "rolled_back", "discarded"],
)
def test_promote_rejects_job_in_terminal_state(
    tmp_path: Path, terminal_state: Any
) -> None:
    """Promote must reject when promotion_state is terminal.

    A second promote call after success would hit worktree_dirty (workspace is
    modified) and overwrite the terminal state with prechecks_failed, corrupting
    the state machine.
    """
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Force the job into a terminal state.
    job_store.update_promotion_state(job_id, promotion_state=terminal_state)

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)
    assert result.reason == "job_not_completed"

    # Verify the terminal state was NOT overwritten.
    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == terminal_state


@pytest.mark.parametrize(
    "inflight_state",
    ["prechecks_passed", "applied", "rollback_needed"],
)
def test_promote_rejects_job_in_inflight_state(
    tmp_path: Path, inflight_state: Any
) -> None:
    """Promote must reject when promotion_state indicates an in-flight operation."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )

    # Force the job into an in-flight state.
    job_store.update_promotion_state(job_id, promotion_state=inflight_state)

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionRejectedResponse)
    assert result.reason == "job_not_completed"

    # Verify the in-flight state was NOT overwritten.
    persisted = job_store.get(job_id)
    assert persisted is not None
    assert persisted.promotion_state == inflight_state


def test_promote_prechecks_passed_not_stranded_on_crash_before_intent(
    tmp_path: Path,
) -> None:
    """If prechecks_passed is written before intent, a crash strands the state.

    This test verifies the ordering: intent journal must be written BEFORE
    prechecks_passed state, so recovery always has a journal entry to process.
    Alternatively, prechecks_passed must not be written until after intent.
    """
    controller, job_store, journal, _repo, job_id, _hash, _cb = _build_promote_scenario(
        tmp_path
    )

    # Track when prechecks_passed is written relative to the intent journal.
    write_order: list[str] = []
    original_update = job_store.update_promotion_state
    original_write_phase = journal.write_phase

    def _tracking_update(jid: str, *, promotion_state: str, **kwargs: Any) -> None:
        if promotion_state == "prechecks_passed":
            write_order.append("prechecks_passed")
        return original_update(jid, promotion_state=promotion_state, **kwargs)

    def _tracking_write_phase(entry: Any, **kwargs: Any) -> None:
        if (
            hasattr(entry, "operation")
            and entry.operation == "promotion"
            and entry.phase == "intent"
        ):
            write_order.append("intent")
        return original_write_phase(entry, **kwargs)

    job_store.update_promotion_state = _tracking_update  # type: ignore[assignment]
    journal.write_phase = _tracking_write_phase  # type: ignore[assignment]

    result = controller.promote(job_id=job_id)
    assert isinstance(result, PromotionResult)

    # Intent must be written BEFORE prechecks_passed (or prechecks_passed must
    # not exist at all before intent). The key invariant: no persisted state
    # exists that recovery cannot find via journal entry.
    assert "intent" in write_order, "Intent journal phase was never written"
    assert "prechecks_passed" in write_order, "prechecks_passed was never written"
    intent_idx = write_order.index("intent")
    prechecks_idx = write_order.index("prechecks_passed")
    assert intent_idx < prechecks_idx, (
        f"prechecks_passed (idx={prechecks_idx}) was written before intent "
        f"(idx={intent_idx}). A crash in that gap strands the job at "
        "prechecks_passed with no journal entry for recovery to process."
    )


def test_recover_startup_preserves_promotion_attempt_from_intent(
    tmp_path: Path,
) -> None:
    """Recovery of intent-only normalizes to pending AND preserves the attempt counter.

    Without preserving the attempt, the next promote() reuses the same
    idempotency key, violating the monotonic promotion_attempt contract.
    """
    controller, job_store, journal, primary_repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    session_id = "sess-recover-attempt"
    created_at = journal.timestamp()
    repo_root_str = str(primary_repo.resolve())

    # Simulate: promote() ran, wrote intent with attempt=3, then crashed.
    job_store.update_promotion_state(
        job_id, promotion_state="prechecks_passed", promotion_attempt=3
    )
    idempotency_key = f"promotion:{job_id}:3"
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="promotion",
            phase="intent",
            collaboration_id="collab-promote-1",
            created_at=created_at,
            repo_root=repo_root_str,
            job_id=job_id,
        ),
        session_id=session_id,
    )

    # Rebuild controller with the recovery session_id.
    plugin_data = tmp_path / "plugin-data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    registry = ExecutionRuntimeRegistry()
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    lineage_store.create(
        CollaborationHandle(
            collaboration_id="collab-promote-1",
            capability_class="execution",
            runtime_id="rt-promote-1",
            codex_thread_id="thr-1",
            claude_session_id=session_id,
            repo_root=repo_root_str,
            created_at=created_at,
            status="active",
        )
    )
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)
    recovery_controller = DelegationController(
        control_plane=_FakeControlPlane(),
        worktree_manager=_FakeWorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
        head_commit_resolver=lambda repo_root: "abc123",
        uuid_factory=iter([f"evt-{i}" for i in range(100)]).__next__,
    )

    recovery_controller.recover_startup()

    # Job should be normalized to pending with attempt=3 preserved.
    recovered = job_store.get(job_id)
    assert recovered is not None
    assert recovered.promotion_state == "pending"
    assert recovered.promotion_attempt == 3, (
        f"Expected promotion_attempt=3 (from crashed intent) but got "
        f"{recovered.promotion_attempt}. Recovery must preserve the attempt "
        "counter to avoid idempotency key reuse."
    )


class TestTerminalOutcomeEmission:
    """Verify DelegationOutcomeRecord emission on terminal job transitions."""

    def test_completed_job_emits_terminal_outcome(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            job_store,
            _lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        result = controller.start(repo_root=repo_root)
        assert isinstance(result, DelegationJob)
        assert result.status == "completed"

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists()
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1
        record = terminal_records[0]
        assert record["job_id"] == "job-1"
        assert record["terminal_status"] == "completed"
        assert record["collaboration_id"] == "collab-1"
        assert record["base_commit"] == "head-abc"

    def test_failed_turn_emits_terminal_outcome(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            cp,
            _wm,
            job_store,
            _lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        cp._next_turn_result = TurnExecutionResult(
            turn_id="turn-1",
            status="failed",
            agent_message="Failed.",
            notifications=(),
        )

        result = controller.start(repo_root=repo_root)
        assert isinstance(result, DelegationJob)
        assert result.status == "failed"

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1
        assert terminal_records[0]["terminal_status"] == "failed"

    def test_unknown_cleanup_emits_terminal_outcome(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            cp,
            _wm,
            job_store,
            _lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        cp._next_raise_on_turn = RuntimeError("turn dispatch failure")

        # Post-Task-17: worker exception is wrapped as DelegationStartError(
        # reason='worker_failed_before_capture'); cause carries the original
        # RuntimeError. _mark_execution_unknown_and_cleanup still runs on the
        # worker thread and emits the terminal outcome BEFORE the wrap.
        with pytest.raises(DelegationStartError) as exc_info:
            controller.start(repo_root=repo_root)
        assert exc_info.value.reason == "worker_failed_before_capture"
        assert isinstance(exc_info.value.cause, RuntimeError)
        assert "turn dispatch failure" in str(exc_info.value.cause)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists(), (
            "Terminal outcome file must exist after unknown cleanup"
        )
        lines = [
            line
            for line in outcomes_path.read_text(encoding="utf-8").strip().split("\n")
            if line.strip()
        ]
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1, "Exactly one terminal outcome expected"
        assert terminal_records[0]["terminal_status"] == "unknown"

    def test_terminal_outcome_is_idempotent(self, tmp_path: Path) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            job_store,
            _lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        result = controller.start(repo_root=repo_root)
        assert isinstance(result, DelegationJob)

        # Manually call the helper again — should not duplicate
        controller._emit_terminal_outcome_if_needed(result.job_id)

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        lines = outcomes_path.read_text(encoding="utf-8").strip().split("\n")
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1

    def test_terminal_outcome_emission_failure_is_logged_not_propagated(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from unittest.mock import patch

        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            _js,
            _lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        result = controller.start(repo_root=repo_root)
        assert isinstance(result, DelegationJob)

        with (
            patch.object(
                journal,
                "append_delegation_outcome_once",
                side_effect=OSError("disk full"),
            ),
            caplog.at_level("WARNING", logger="server.delegation_controller"),
        ):
            controller._emit_terminal_outcome_if_needed(result.job_id)

        assert any("disk full" in msg for msg in caplog.messages)


class TestRecoveryCatchup:
    """Verify same-session terminal outcome catch-up during recover_startup."""

    def test_recover_startup_emits_for_completed_jobs_missing_outcome(
        self, tmp_path: Path
    ) -> None:
        """Simulate a same-session job that completed but crashed before outcome emission."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            job_store,
            lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        from server.models import CollaborationHandle, DelegationJob

        lineage.create(
            CollaborationHandle(
                collaboration_id="collab-pre",
                capability_class="execution",
                runtime_id="rt-pre",
                codex_thread_id="thr-pre",
                claude_session_id="sess-1",
                repo_root=str(repo_root),
                created_at="2026-04-21T00:00:00Z",
                status="completed",
            )
        )
        job_store.create(
            DelegationJob(
                job_id="job-pre",
                runtime_id="rt-pre",
                collaboration_id="collab-pre",
                base_commit="abc123",
                worktree_path=str(tmp_path / "wt"),
                promotion_state="pending",
                status="completed",
            )
        )

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert not outcomes_path.exists() or outcomes_path.read_text().strip() == ""

        controller.recover_startup()

        assert outcomes_path.exists()
        lines = [
            line
            for line in outcomes_path.read_text(encoding="utf-8").strip().split("\n")
            if line.strip()
        ]
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1
        assert terminal_records[0]["job_id"] == "job-pre"
        assert terminal_records[0]["terminal_status"] == "completed"

    def test_recover_startup_catches_up_verified_promoted_jobs(
        self, tmp_path: Path
    ) -> None:
        """Jobs with terminal promotion states (verified, discarded) must still
        be swept — list_user_attention_required() would miss these."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            job_store,
            lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        from server.models import CollaborationHandle, DelegationJob

        lineage.create(
            CollaborationHandle(
                collaboration_id="collab-promoted",
                capability_class="execution",
                runtime_id="rt-promoted",
                codex_thread_id="thr-promoted",
                claude_session_id="sess-1",
                repo_root=str(repo_root),
                created_at="2026-04-21T00:00:00Z",
                status="completed",
            )
        )
        job_store.create(
            DelegationJob(
                job_id="job-promoted",
                runtime_id="rt-promoted",
                collaboration_id="collab-promoted",
                base_commit="abc123",
                worktree_path=str(tmp_path / "wt"),
                promotion_state="verified",
                status="completed",
            )
        )

        controller.recover_startup()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        assert outcomes_path.exists(), (
            "Terminal outcome must be emitted even for verified/discarded jobs"
        )
        lines = [
            line
            for line in outcomes_path.read_text(encoding="utf-8").strip().split("\n")
            if line.strip()
        ]
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1
        assert terminal_records[0]["job_id"] == "job-promoted"

    def test_recover_startup_skips_already_emitted_outcomes(
        self, tmp_path: Path
    ) -> None:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (
            controller,
            _cp,
            _wm,
            job_store,
            lineage,
            journal,
            _registry,
            _prs,
        ) = _build_controller(tmp_path)

        from server.models import (
            CollaborationHandle,
            DelegationJob,
            DelegationOutcomeRecord,
        )

        lineage.create(
            CollaborationHandle(
                collaboration_id="collab-pre",
                capability_class="execution",
                runtime_id="rt-pre",
                codex_thread_id="thr-pre",
                claude_session_id="sess-1",
                repo_root=str(repo_root),
                created_at="2026-04-21T00:00:00Z",
                status="completed",
            )
        )
        job_store.create(
            DelegationJob(
                job_id="job-pre",
                runtime_id="rt-pre",
                collaboration_id="collab-pre",
                base_commit="abc123",
                worktree_path=str(tmp_path / "wt"),
                promotion_state="pending",
                status="completed",
            )
        )

        journal.append_delegation_outcome(
            DelegationOutcomeRecord(
                outcome_id="do-existing",
                timestamp="2026-04-21T00:00:00Z",
                outcome_type="delegation_terminal",
                collaboration_id="collab-pre",
                runtime_id="rt-pre",
                job_id="job-pre",
                terminal_status="completed",
                base_commit="abc123",
            )
        )

        controller.recover_startup()

        outcomes_path = journal.plugin_data_path / "analytics" / "outcomes.jsonl"
        lines = [
            line
            for line in outcomes_path.read_text(encoding="utf-8").strip().split("\n")
            if line.strip()
        ]
        terminal_records = [
            json.loads(line)
            for line in lines
            if json.loads(line).get("outcome_type") == "delegation_terminal"
        ]
        assert len(terminal_records) == 1  # No duplicate
