"""Controller for codex.delegate.start.

Mirrors dialogue.py::DialogueController.start three-phase discipline. Flow:

    --- Committed-start phase ---
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

    --- First-turn dispatch + capture ---
    update job status to "running"
    dispatch first execution turn with three-strategy server request handler
    post-turn status derivation (completed / needs_escalation / failed / unknown)
    if needs_escalation: emit escalation audit, return DelegationEscalation
        (runtime kept live for decide)
    if terminal: release runtime, close session, return DelegationJob
"""

# Execution-turn journaling deferral (T-05 pending-request capture slice):
#
# The first execution turn dispatched inside start() is intentionally
# unjournaled. job_creation.completed means "all durable start writes
# landed," not "turn finished." Turn dispatch happens AFTER the journal
# is terminal.
#
# Crash recovery for the first-turn window:
#
# After job_creation.completed, the journal entry IS resolved —
# list_unresolved() will NOT return it. If the process crashes after
# update_status(job_id, "running") but before post-turn terminal writes,
# the job is persisted as "running" with no live runtime and no journal
# replay anchor. recover_startup() handles this via orphaned-running-job
# detection (see Step 6.2): any job persisted as "running" after a cold
# restart has no live runtime (the registry is fresh) and is marked
# "unknown".
#
# Turn-dispatch journaling (with its own ``turn_dispatch`` operation and
# idempotency key per recovery-and-journal.md:49) lands with T-06
# (codex.delegate.poll), where multi-turn dispatch and replay become
# real requirements.

from __future__ import annotations

import hashlib
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable, Protocol

from .approval_router import parse_pending_server_request
from .delegation_job_store import DelegationJobStore
from .execution_prompt_builder import build_execution_turn_text
from .execution_runtime_registry import ExecutionRuntimeEntry, ExecutionRuntimeRegistry
from .journal import OperationJournal
from .lineage_store import LineageStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    DelegationEscalation,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
    PendingServerRequest,
    TurnExecutionResult,
)
from .pending_request_store import PendingRequestStore
from .runtime import AppServerRuntimeSession, build_workspace_write_sandbox_policy

logger = logging.getLogger(__name__)


class _ControlPlaneLike(Protocol):
    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, AppServerRuntimeSession, str]: ...


class _WorktreeManagerLike(Protocol):
    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None: ...

    def remove_worktree(self, *, repo_root: Path, worktree_path: Path) -> None: ...


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


def _delegation_request_hash(repo_root: Path, base_commit: str, objective: str) -> str:
    """Recovery-contract idempotency component — hash of the delegation request.

    Per recovery-and-journal.md:47, the ``job_creation`` idempotency key is
    ``claude_session_id + delegation_request_hash``. The request is fully
    characterized by the resolved repo_root + base_commit + objective in v1.

    When the MCP surface later accepts additional inputs (e.g., a delegation
    brief or profile override), they must be included in the hash so replay
    recognizes the full request shape.
    """
    payload = f"{repo_root}:{base_commit}:{objective}".encode("utf-8")
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
        pending_request_store: PendingRequestStore,
        approval_policy: str = "untrusted",
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
        self._pending_request_store = pending_request_store
        self._approval_policy = approval_policy
        self._head_commit_resolver = head_commit_resolver or _resolve_head_commit
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))

    def start(
        self,
        *,
        repo_root: Path,
        base_commit: str | None = None,
        objective: str = "",
    ) -> DelegationJob | DelegationEscalation | JobBusyResponse:
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
        request_hash = _delegation_request_hash(resolved_root, resolved_base, objective)
        idempotency_key = f"{self._session_id}:{request_hash}"
        created_at = self._journal.timestamp()
        worktree_path = (
            self._plugin_data_path / "runtimes" / "delegation" / job_id / "worktree"
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
        try:
            runtime_id, session, thread_id = (
                self._control_plane.start_execution_runtime(worktree_path)
            )
        except Exception:
            # Bootstrap failed before dispatched — no handle, job, or registry
            # entry was persisted. Remove the worktree so there is no untracked
            # directory that a later cleanup slice cannot discover.
            self._worktree_manager.remove_worktree(
                repo_root=resolved_root, worktree_path=worktree_path
            )
            raise

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
                    # Best-effort — reconciliation will close it.
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

        # ------------------------------------------------------------------
        # Turn dispatch + capture loop.
        #
        # The first execution turn is intentionally unjournaled (see module
        # docstring). Crash recovery for the first-turn window uses orphaned-
        # running-job detection in recover_startup().
        # ------------------------------------------------------------------
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

    def _finalize_turn(
        self,
        *,
        job_id: str,
        runtime_id: str,
        collaboration_id: str,
        entry: ExecutionRuntimeEntry,
        turn_result: TurnExecutionResult,
        captured_request: PendingServerRequest | None,
        interrupted_by_unknown: bool,
        captured_request_parse_failed: bool,
    ) -> DelegationJob | DelegationEscalation:
        """Post-turn status derivation, audit, and cleanup.

        Extracted from start() so the caller can wrap it in a failure guard.
        """
        _CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})

        if captured_request is not None:
            # D6 diagnostic — only when we have a parseable request with
            # wire-correlated IDs.
            if not captured_request_parse_failed:
                _verify_post_turn_signals(
                    notifications=turn_result.notifications,
                    request_id=captured_request.request_id,
                    item_id=captured_request.item_id,
                )
                # D4: mark wire request resolved (parse failures stay pending).
                self._pending_request_store.update_status(
                    captured_request.request_id, "resolved"
                )

            # Job status derivation.
            if captured_request.kind in _CANCEL_CAPABLE_KINDS or interrupted_by_unknown:
                final_status = "needs_escalation"
            elif turn_result.status == "completed":
                final_status = "completed"
            else:
                final_status = "needs_escalation"

            self._job_store.update_status(job_id, final_status)

            updated_job = self._job_store.get(job_id)
            assert updated_job is not None, (
                f"DelegationJobStore invariant violation: job_id={job_id!r} "
                f"was just updated but get() returned None"
            )

            if final_status == "needs_escalation":
                # Audit event for escalation.
                self._journal.append_audit_event(
                    AuditEvent(
                        event_id=self._uuid_factory(),
                        timestamp=self._journal.timestamp(),
                        actor="claude",
                        action="escalate",
                        collaboration_id=collaboration_id,
                        runtime_id=runtime_id,
                        job_id=job_id,
                        request_id=captured_request.request_id,
                    )
                )

                # Re-read the request from the store so the returned object
                # reflects the authoritative status (e.g., "resolved" after D4).
                resolved_request = self._pending_request_store.get(
                    captured_request.request_id
                )

                # Keep runtime live — decide will reuse it.
                return DelegationEscalation(
                    job=updated_job,
                    pending_request=resolved_request or captured_request,
                    agent_context=turn_result.agent_message or None,
                )

            # Non-escalation: mark handle completed, release + close and return plain job.
            self._lineage_store.update_status(collaboration_id, "completed")
            self._runtime_registry.release(runtime_id)
            entry.session.close()
            return updated_job

        # No server request captured — clean completion or failure.
        if turn_result.status == "completed":
            final_status = "completed"
        elif turn_result.status == "failed":
            final_status = "failed"
        else:
            final_status = "unknown"

        self._job_store.update_status(job_id, final_status)
        self._lineage_store.update_status(collaboration_id, "completed")
        self._runtime_registry.release(runtime_id)
        entry.session.close()

        updated_job = self._job_store.get(job_id)
        assert updated_job is not None, (
            f"DelegationJobStore invariant violation: job_id={job_id!r} "
            f"was just updated but get() returned None"
        )
        return updated_job

    def recover_startup(self) -> None:
        """Consume unresolved job_creation journal records into durable terminal state.

        Mirrors dialogue.py:522 recover_startup — but reconcile-only. Unlike
        dialogue (which can reattach persistent codex_thread_ids to new runtime
        sessions), delegation runtimes are subprocess-anchored to a worktree and
        cannot be rejoined across restart. The only recovery this does is close
        unresolved journal records and mark any partially-persisted handle / job
        as ``unknown`` so poll/discard/promote slices can operate on terminal
        durable state.

        Reconciliation contract (by journal phase):

        - ``intent`` only: no side effects committed yet; advance to ``completed``.
        - ``dispatched`` + no persisted handle/job: runtime subprocess is dead;
          advance journal to ``completed``.
        - ``dispatched`` + persisted handle and/or job: mark each persisted record
          ``unknown`` (if not already); advance journal to ``completed``.

        Idempotent: a second call after the first has reconciled finds no
        unresolved entries and is a clean no-op.

        Called from mcp_server.py's session init path, mirroring the
        ``self._dialogue_controller.recover_startup()`` call.
        """
        unresolved = self._journal.list_unresolved(session_id=self._session_id)
        job_creation_entries = [e for e in unresolved if e.operation == "job_creation"]
        # Group by idempotency_key and pick the latest phase per key.
        by_key: dict[str, OperationJournalEntry] = {}
        for entry in job_creation_entries:
            existing = by_key.get(entry.idempotency_key)
            if existing is None or _phase_rank(entry.phase) > _phase_rank(
                existing.phase
            ):
                by_key[entry.idempotency_key] = entry

        for entry in by_key.values():
            # Mark durable records unknown if they exist AND are not already
            # in a terminal state.
            if entry.collaboration_id is not None:
                handle = self._lineage_store.get(entry.collaboration_id)
                if handle is not None and handle.status == "active":
                    self._lineage_store.update_status(entry.collaboration_id, "unknown")
            if entry.job_id is not None:
                job = self._job_store.get(entry.job_id)
                if job is not None and job.status in ("queued", "running"):
                    self._job_store.update_status(entry.job_id, "unknown")

            # Advance the journal to completed — this is the terminal phase
            # per recovery-and-journal.md, and it causes list_unresolved to
            # stop returning this key. Physical compaction via
            # OperationJournal.compact() is a separate operation not invoked
            # in this slice (recovery-and-journal.md:59 describes the
            # "near-empty" steady state but does not require eager trimming).
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation="job_creation",
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                    job_id=entry.job_id,
                ),
                session_id=self._session_id,
            )

        # --- Orphaned-running-job reconciliation ---
        # After a cold restart, the runtime registry is fresh: no live
        # runtimes exist. Any job persisted as "running" is orphaned —
        # the first-turn window crashed after update_status(job_id,
        # "running") but before post-turn terminal writes. There is no
        # journal replay anchor (D2: first turn is intentionally
        # unjournaled), so the only safe terminal state is "unknown".
        #
        # This is separate from the journal-based reconciliation above
        # because the journal entry is already "completed" at this point
        # (job_creation.completed fired before turn dispatch).
        for job in self._job_store.list_active():
            if job.status == "running":
                self._job_store.update_status(job.job_id, "unknown")


def _verify_post_turn_signals(
    *,
    notifications: tuple[dict[str, Any], ...],
    request_id: str,
    item_id: str,
) -> None:
    """D6 diagnostic: check serverRequest/resolved + item/completed."""
    seen_resolved = False
    seen_item_completed = False
    for notification in notifications:
        method = notification.get("method")
        params = notification.get("params", {})
        if not isinstance(params, dict):
            continue
        if method == "serverRequest/resolved":
            raw_request_id = params.get("requestId")
            if raw_request_id is not None and str(raw_request_id) == request_id:
                seen_resolved = True
        if method == "item/completed" and isinstance(params.get("item"), dict):
            if params["item"].get("id") == item_id:
                seen_item_completed = True
    if not seen_resolved:
        logger.warning(
            "D6 signal missing: serverRequest/resolved not seen for request_id=%r after turn/completed",
            request_id,
        )
    if not seen_item_completed:
        logger.warning(
            "D6 signal missing: item/completed not seen for item_id=%r after turn/completed",
            item_id,
        )


def _phase_rank(phase: str) -> int:
    """Phase-ordering helper for picking the latest phase per idempotency key."""
    return {"intent": 0, "dispatched": 1, "completed": 2}.get(phase, -1)
