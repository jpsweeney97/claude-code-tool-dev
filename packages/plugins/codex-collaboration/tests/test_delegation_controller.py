"""Tests for DelegationController — mirrors dialogue pattern.

Verifies every durable surface is populated AND the in-process registry
retains the session so the runtime remains controllable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import (
    AccountState,
    CollaborationHandle,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
    RuntimeHandshake,
)


class _FakeSession:
    def __init__(self, thread_id: str = "thr-1") -> None:
        self._thread_id = thread_id
        self.closed = False

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

    def close(self) -> None:
        self.closed = True


class _FakeControlPlane:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self._next_runtime_id = 0
        self._sessions: list[_FakeSession] = []

    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, _FakeSession, str]:
        self.calls.append(worktree_path)
        self._next_runtime_id += 1
        session = _FakeSession(thread_id=f"thr-{self._next_runtime_id}")
        self._sessions.append(session)
        return f"rt-{self._next_runtime_id}", session, session._thread_id


class _FakeWorktreeManager:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str, Path]] = []

    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None:
        self.calls.append((repo_root, base_commit, worktree_path))
        worktree_path.mkdir(parents=True, exist_ok=True)


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
]:
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    control_plane = _FakeControlPlane()
    worktree_manager = _FakeWorktreeManager()
    registry = ExecutionRuntimeRegistry()
    uuid_counter = iter(
        ["job-1", "collab-1", "evt-1", "job-2", "collab-2", "evt-2"]
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
    ) = _build_controller(tmp_path)

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, DelegationJob)
    assert result.job_id == "job-1"
    assert result.base_commit == "head-abc"
    assert result.status == "queued"
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

    controller, _cp, _wm, _js, lineage, _j, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    handle = lineage.get("collab-1")
    assert isinstance(handle, CollaborationHandle)
    assert handle.capability_class == "execution"
    assert handle.runtime_id == "rt-1"
    assert handle.codex_thread_id == "thr-1"
    assert handle.claude_session_id == "sess-1"
    assert handle.status == "active"


def test_start_writes_three_phase_journal_records(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    # Idempotency key is claude_session_id + delegation_request_hash.
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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
    ) = _build_controller(tmp_path)

    controller.start(repo_root=repo_root)

    entry = registry.lookup("rt-1")
    assert entry is not None
    assert entry.job_id == "job-1"
    assert entry.thread_id == "thr-1"
    # The registered session is the SAME object the control plane returned.
    assert entry.session is control_plane._sessions[0]


def test_start_emits_delegate_start_audit_event(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

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

    controller, _cp, worktree_manager, _js, _ls, _j, _r = _build_controller(tmp_path)

    controller.start(repo_root=repo_root, base_commit="explicit-sha")

    assert worktree_manager.calls[0][1] == "explicit-sha"


def test_start_returns_busy_response_when_active_job_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, _j, _r = _build_controller(tmp_path)

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)

    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == "job-1"
    assert second.active_job_status == "queued"
    # The rejected second call must NOT have triggered side effects.
    # Worktree and runtime counts stay at 1 (from the first, successful call).
    assert len(_wm.calls) == 1
    assert len(_cp.calls) == 1


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

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("lineage_store.create boom")

    monkeypatch.setattr(lineage_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("job_store.create boom")

    monkeypatch.setattr(job_store, "create", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
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
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise OSError("audit boom")

    monkeypatch.setattr(journal, "append_audit_event", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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

    controller, _cp, _wm, job_store, lineage_store, journal, registry = (
        _build_controller(tmp_path)
    )

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("registry.register boom")

    monkeypatch.setattr(registry, "register", _boom)

    with pytest.raises(CommittedStartFinalizationError, match="start committed"):
        controller.start(repo_root=repo_root)

    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:head-abc".encode("utf-8")
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

    controller, _cp, _wm, _job_store, _lineage_store, _journal, registry = (
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

    controller, _cp, _wm, _job_store, _lineage_store, journal, _registry = (
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
    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

    before = journal.list_unresolved(session_id="sess-1")
    assert before == []

    controller.recover_startup()

    after = journal.list_unresolved(session_id="sess-1")
    assert after == []


def test_recover_startup_closes_intent_only_as_noop(tmp_path: Path) -> None:
    """intent-only → write completed, no durable changes."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
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


def test_recover_startup_marks_dispatched_handle_and_job_unknown(tmp_path: Path) -> None:
    """intent + dispatched with persisted handle + job → mark both unknown, close journal."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
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


def test_recover_startup_closes_dispatched_without_persisted_state(tmp_path: Path) -> None:
    """intent + dispatched but no handle/job persisted → write completed, no mark needed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
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

    controller, _cp, _wm, job_store, lineage_store, journal, _r = _build_controller(
        tmp_path
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


def test_recover_startup_idempotent_second_call_is_noop(tmp_path: Path) -> None:
    """Second recover_startup after the first has reconciled finds nothing to do."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, _cp, _wm, _js, _ls, journal, _r = _build_controller(tmp_path)

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
