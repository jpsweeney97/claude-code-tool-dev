"""Controller for codex.delegate.start.

Mirrors dialogue.py::DialogueController.start three-phase discipline. Flow:

    busy check (job_store.list_active + registry.active_runtime_ids
        + unresolved job_creation journal entries)
    resolve base commit
    compute idempotency key (claude_session_id + delegation_request_hash)
    journal Phase 1: intent (before any side effects)
    create worktree
    bootstrap execution runtime
    journal Phase 2: dispatched (runtime_id + codex_thread_id recorded)
    register runtime ownership in ExecutionRuntimeRegistry (FIRST committed-start
        write — establishes in-process ownership before any fallible local write)
    persist CollaborationHandle in LineageStore (identity/routing)
    persist DelegationJob in DelegationJobStore (job lifecycle)
    emit delegate_start audit event (BEFORE journal completed; "journal at
        dispatched" is the universal terminal state for committed-start failures)
    journal Phase 3: completed (terminal write)

This slice does NOT dispatch execution turns. The controller stops at
journal.write_phase(completed). Callers receive a queued job record with
a live runtime whose session is retained by the registry so follow-up
turn dispatch can find it via ExecutionRuntimeRegistry.lookup(runtime_id).
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from pathlib import Path
from typing import Callable, Protocol

from .delegation_job_store import DelegationJobStore
from .execution_runtime_registry import ExecutionRuntimeRegistry
from .journal import OperationJournal
from .lineage_store import LineageStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
)
from .runtime import AppServerRuntimeSession


class _ControlPlaneLike(Protocol):
    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, AppServerRuntimeSession, str]:
        ...


class _WorktreeManagerLike(Protocol):
    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None:
        ...


def _resolve_head_commit(repo_root: Path) -> str:
    """Default head-commit resolver — `git rev-parse HEAD` in repo_root."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Delegation start failed: could not resolve HEAD. "
            f"Got: {(exc.stderr or exc.stdout).strip()!r:.200}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Delegation start failed: git rev-parse HEAD timed out. "
            f"Got: {repo_root!r:.100}"
        ) from exc
    return result.stdout.strip()


def _delegation_request_hash(repo_root: Path, base_commit: str) -> str:
    """Recovery-contract idempotency component — hash of the delegation request.

    Per recovery-and-journal.md:47, the ``job_creation`` idempotency key is
    ``claude_session_id + delegation_request_hash``. The request is fully
    characterized by the resolved repo_root + base_commit pair in v1.
    """

    payload = f"{repo_root}:{base_commit}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class CommittedStartFinalizationError(RuntimeError):
    """Raised when a delegation start has committed side effects (worktree + runtime
    are live, journal-dispatched is written) but a local durable write afterwards
    fails (lineage persist, job persist, audit emit, or journal-completed write).

    Mirrors dialogue.py::CommittedTurnFinalizationError. The caller MUST NOT blindly
    retry: the worktree is live, a runtime subprocess is running, and any partially
    persisted handle or job record has been best-effort marked ``unknown``. Retrying
    ``codex.delegate.start`` will produce a duplicate job record for the same
    (repo_root, base_commit) pair because the idempotency replay path only recognizes
    a ``completed`` journal phase as terminal — which is exactly the phase this error
    guarantees was NOT written.

    Recovery path: on next session init, DelegationController.recover_startup()
    reads the unresolved job_creation journal entries (they sit at ``dispatched``)
    and advances them to ``completed`` so they are no longer returned by
    ``list_unresolved()``. Physical compaction via ``OperationJournal.compact()``
    is not invoked here. For lineage / job / audit / journal-completed failures,
    the handle and job are already best-effort marked ``unknown`` before the
    error is raised, and the registry entry is retained for the rest of the
    session; reconciliation just confirms the journal advance. For the
    ``runtime_registry.register`` failure case, no handle / job / registry
    entry was ever persisted, so reconciliation only advances the journal.
    The runtime subprocess is not reattached in any case — promote/discard
    is the caller's responsibility on the durable ``unknown`` record (or,
    for the register-failure case, no durable record at all) via future slices.
    """


class DelegationController:
    """Implements codex.delegate.start."""

    def __init__(
        self,
        *,
        control_plane: _ControlPlaneLike,
        worktree_manager: _WorktreeManagerLike,
        job_store: DelegationJobStore,
        lineage_store: LineageStore,
        runtime_registry: ExecutionRuntimeRegistry,
        journal: OperationJournal,
        session_id: str,
        plugin_data_path: Path,
        head_commit_resolver: Callable[[Path], str] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._worktree_manager = worktree_manager
        self._job_store = job_store
        self._lineage_store = lineage_store
        self._runtime_registry = runtime_registry
        self._journal = journal
        self._session_id = session_id
        self._plugin_data_path = plugin_data_path
        self._head_commit_resolver = head_commit_resolver or _resolve_head_commit
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))

    def start(
        self,
        *,
        repo_root: Path,
        base_commit: str | None = None,
    ) -> DelegationJob | JobBusyResponse:
        """Start a delegation job. Returns the job, or JobBusyResponse if busy.

        Write ordering invariant:
          1. ``runtime_registry.register`` is the FIRST committed-start write
             (immediately after ``dispatched``) so the runtime is controllable
             in-process for any subsequent failure path. Without this, a
             failure in lineage / job / audit / completed would leave a live
             subprocess with no in-process owner and the busy gate would
             clear → same-session retry would spawn a duplicate.
          2. ``journal.write_phase(completed)`` is the LAST write. If any step
             between ``dispatched`` and ``completed`` fails, the journal stays
             at ``dispatched`` and startup reconciliation (recover_startup)
             will close the record on next session init.
          3. Audit emission happens BEFORE the completed phase so an audit
             failure leaves the journal unreconciled rather than
             terminal-but-inconsistent.

        Failure semantics (mirrors dialogue.py:361-373 committed-turn finalization,
        adapted for delegation's wider blast radius — 4-5 post-``dispatched`` local
        writes vs dialogue's 1):

        - ``worktree_manager.create_worktree`` or ``control_plane.start_execution_runtime``
          raises (before ``dispatched``): raw exception propagates. Journal may have
          an ``intent`` phase; no durable state beyond that. Covered by
          test_start_does_not_persist_durable_state_on_bootstrap_failure.

        - ``runtime_registry.register`` raises (after ``dispatched``, BEFORE any
          other committed-start write): the runtime subprocess is live but the
          in-process ownership table never received the entry. The journal is at
          ``dispatched``; no handle, job, or registry entry exists. The controller
          raises CommittedStartFinalizationError with no-retry guidance.
          Reconciliation on next session init advances the journal to ``completed``;
          the runtime subprocess is unreachable from the registry and will leak
          until the parent process exits (no in-process entry to release; teardown
          via subprocess discovery is out of scope for this slice). Structurally
          rare: register rejects only on duplicate ``runtime_id``, and ``runtime_id``
          is uuid-generated. Covered by
          test_start_raises_committed_start_finalization_error_on_register_failure.

        - ``lineage_store.create`` / ``job_store.create`` / ``journal.append_audit_event``
          / ``journal.write_phase(completed)`` raises (after ``dispatched`` AND
          successful ``register``): the start has committed — a runtime subprocess
          is live AND registered. The controller best-effort marks any already-persisted
          ``CollaborationHandle`` and ``DelegationJob`` with ``status="unknown"``,
          leaves the journal at ``dispatched`` (does NOT write ``completed``),
          retains the registry entry (the runtime stays controllable in-process for
          the rest of the session; releasing it would leak the subprocess), and
          raises CommittedStartFinalizationError with no-retry guidance. The busy
          gate consults ``registry.active_runtime_ids()`` (alongside the job store
          and unresolved journal entries) so any same-session retry is rejected.
          Recovery is deferred to DelegationController.recover_startup() on the
          next session init for the durable side.
        """

        # Busy check — max-1 concurrent job per session. Consults THREE sources:
        #   (a) job_store.list_active(): healthy queued/running/needs_escalation jobs
        #   (b) registry.active_runtime_ids(): in-process live ownership; catches
        #       same-session retry after a committed-start failure that left a
        #       registered runtime without a queued job (e.g., lineage_store.create
        #       failed AFTER the registry registration that always happens FIRST
        #       post-dispatched).
        #   (c) unresolved job_creation journal entries: catches the cross-session
        #       case where the in-process registry is fresh but the journal still
        #       has a dispatched record awaiting recover_startup() reconciliation.
        # Filter (c) in the controller — journal.list_unresolved() does not take
        # an operation parameter; we filter on entry.operation == "job_creation".
        active = self._job_store.list_active()
        if active:
            existing = active[0]
            return JobBusyResponse(
                busy=True,
                active_job_id=existing.job_id,
                active_job_status=existing.status,
                detail=(
                    "Another delegation is in flight (job_store). "
                    f"active_job_id={existing.job_id!r} "
                    f"status={existing.status!r}"
                ),
            )
        active_runtime_ids = self._runtime_registry.active_runtime_ids()
        if active_runtime_ids:
            rt_id = next(iter(active_runtime_ids))
            entry = self._runtime_registry.lookup(rt_id)
            # Invariant: rt_id came from active_runtime_ids(); lookup() on
            # that id cannot return None (both reads are against the same
            # in-process dict). Assert to document the invariant and fail
            # loud on corruption rather than encode an impossible None into
            # JobBusyResponse.active_job_id (declared ``str``).
            assert entry is not None, (
                f"ExecutionRuntimeRegistry invariant violation: "
                f"runtime_id={rt_id!r} in active_runtime_ids() but "
                f"lookup() returned None"
            )
            return JobBusyResponse(
                busy=True,
                active_job_id=entry.job_id,
                active_job_status="unknown",
                detail=(
                    "Another delegation runtime is registered in-process "
                    "(committed-start failure pending reconciliation). "
                    f"active_runtime_id={rt_id!r} job_id={entry.job_id!r}"
                ),
            )
        unresolved = [
            e
            for e in self._journal.list_unresolved(session_id=self._session_id)
            if e.operation == "job_creation"
        ]
        if unresolved:
            earliest = unresolved[0]
            # Invariant: the journal validator requires ``job_id`` on every
            # ``job_creation`` entry at both ``intent`` and ``dispatched``
            # phases (Task 1 per-phase validator extension). The
            # ``OperationJournalEntry.job_id`` field is declared
            # ``str | None`` for compatibility with non-job_creation ops,
            # but for this branch it is always present. Assert to document
            # the invariant and preserve the typed
            # ``JobBusyResponse.active_job_id`` (declared ``str``).
            assert earliest.job_id is not None, (
                f"OperationJournal invariant violation: job_creation entry "
                f"at phase={earliest.phase!r} has job_id=None "
                f"(idempotency_key={earliest.idempotency_key!r})"
            )
            return JobBusyResponse(
                busy=True,
                active_job_id=earliest.job_id,
                active_job_status="unknown",
                detail=(
                    "Unresolved job_creation journal entries present "
                    "(awaiting recover_startup reconciliation). "
                    f"job_id={earliest.job_id!r}"
                ),
            )

        # Resolve inputs and compute identifiers.
        resolved_root = repo_root.resolve()
        resolved_base = base_commit or self._head_commit_resolver(resolved_root)
        job_id = self._uuid_factory()
        collaboration_id = self._uuid_factory()
        request_hash = _delegation_request_hash(resolved_root, resolved_base)
        idempotency_key = f"{self._session_id}:{request_hash}"
        created_at = self._journal.timestamp()
        worktree_path = (
            self._plugin_data_path
            / "runtimes"
            / "delegation"
            / job_id
            / "worktree"
        )

        # Phase 1: journal intent BEFORE any side effects.
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="job_creation",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                job_id=job_id,
            ),
            session_id=self._session_id,
        )

        # Side effects: worktree + runtime bootstrap + thread.
        self._worktree_manager.create_worktree(
            repo_root=resolved_root,
            base_commit=resolved_base,
            worktree_path=worktree_path,
        )
        runtime_id, session, thread_id = (
            self._control_plane.start_execution_runtime(worktree_path)
        )

        # Phase 2: journal dispatched with outcome correlation.
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="job_creation",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                job_id=job_id,
                runtime_id=runtime_id,
                codex_thread_id=thread_id,
            ),
            session_id=self._session_id,
        )

        # ------------------------------------------------------------------
        # Committed-start phase: worktree + runtime are live, journal records
        # dispatched. Every write below is wrapped so that any failure leaves
        # the journal at ``dispatched`` (NOT ``completed``), and any
        # partially-persisted durable state is best-effort marked unknown.
        # ORDER MATTERS:
        #   1. runtime_registry.register goes FIRST so the runtime is
        #      controllable in-process from the moment the journal records
        #      dispatched. Without this, a subsequent failure (lineage / job
        #      / audit / completed) would leave a live subprocess with no
        #      in-process owner and the busy gate would clear → same-session
        #      retry would spawn a second runtime.
        #   2. journal.write_phase(completed) goes LAST so "journal at
        #      dispatched" is the universal terminal state for any
        #      committed-start failure (recovery just advances to completed).
        #   3. audit emission comes BEFORE completed so an audit failure
        #      still leaves the journal unreconciled rather than
        #      terminal-but-inconsistent.
        # ------------------------------------------------------------------
        handle_persisted = False
        job_persisted = False
        try:
            # Register live ownership FIRST — keeps the runtime controllable
            # in-process for the rest of the session, so any subsequent
            # committed-start failure does not leave an orphan subprocess.
            # Not a crash-durability layer; recovery uses the three durable
            # stores. If register itself raises, the catch block runs with
            # both _persisted flags False (no stores were touched) and the
            # subprocess leaks until the parent process exits — see the
            # register-failure failure-mode bullet in the start() docstring.
            self._runtime_registry.register(
                runtime_id=runtime_id,
                session=session,
                thread_id=thread_id,
                job_id=job_id,
            )

            # Persist identity — CollaborationHandle in the lineage store.
            handle = CollaborationHandle(
                collaboration_id=collaboration_id,
                capability_class="execution",
                runtime_id=runtime_id,
                codex_thread_id=thread_id,
                claude_session_id=self._session_id,
                repo_root=str(resolved_root),
                created_at=created_at,
                status="active",
            )
            self._lineage_store.create(handle)
            handle_persisted = True

            # Persist job lifecycle — DelegationJob in the job store.
            job = DelegationJob(
                job_id=job_id,
                runtime_id=runtime_id,
                collaboration_id=collaboration_id,
                base_commit=resolved_base,
                worktree_path=str(worktree_path),
                promotion_state="pending",
                status="queued",
            )
            self._job_store.create(job)
            job_persisted = True

            # Audit emission BEFORE journal completed — see ORDER MATTERS
            # note above. Crosses a trust/capability boundary per
            # recovery-and-journal.md Write Triggers.
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="delegate_start",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                )
            )

            # Phase 3: journal completed — terminal write. After this line
            # the operation is replay-safe: a later recover_startup() will
            # see a ``completed`` record and treat it as no-op.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=idempotency_key,
                    operation="job_creation",
                    phase="completed",
                    collaboration_id=collaboration_id,
                    created_at=created_at,
                    repo_root=str(resolved_root),
                    job_id=job_id,
                ),
                session_id=self._session_id,
            )
        except Exception as exc:
            # Committed-start finalization failure. The runtime subprocess is
            # live and the journal is at ``dispatched``. Best-effort mark any
            # persisted durable records as ``unknown``; leave the journal
            # unresolved for startup reconciliation to close on next session
            # init. If register succeeded (the common case), the registry entry
            # stays so the runtime remains reachable for a later teardown pass
            # (poll/promote slices) AND so the busy gate's registry consultation
            # blocks same-session retry. If register itself raised, there is no
            # entry to retain — the subprocess will leak until the parent
            # process exits.
            if handle_persisted:
                try:
                    self._lineage_store.update_status(collaboration_id, "unknown")
                except Exception:
                    # Best-effort — reconciliation will close it.
                    pass
            if job_persisted:
                try:
                    self._job_store.update_status(job_id, "unknown")
                except Exception:
                    pass
            raise CommittedStartFinalizationError(
                "Delegation start committed but local finalization failed: "
                f"{exc}. The runtime is live at runtime_id={runtime_id!r} with "
                f"job_id={job_id!r}. The operation journal is at phase "
                f"``dispatched``; startup reconciliation will mark the job "
                f"and handle ``unknown`` on next session init (or, if registry "
                f"registration was the failure, will simply advance the journal "
                f"with no durable identity to mark). Blind retry of "
                f"codex.delegate.start will create a duplicate job for the "
                f"same (repo_root, base_commit) pair — the idempotency replay "
                f"path only recognizes a ``completed`` journal phase as "
                f"terminal, which is exactly the phase that was NOT written."
            ) from exc
        return job
