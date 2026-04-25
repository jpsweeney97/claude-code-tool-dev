"""Controller for codex.delegate.start, codex.delegate.decide, and codex.delegate.poll.

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
# _persist_job_transition(job_id, "running") but before post-turn terminal writes,
# the job is persisted as "running" with no live runtime and no journal
# replay anchor. recover_startup() handles this via orphaned-active-job
# detection (see Step 6.2): any job persisted as "running" or
# "needs_escalation" after a cold restart has no live runtime (the
# registry is fresh) and is marked "unknown".
#
# Turn-dispatch journaling (with its own ``turn_dispatch`` operation and
# idempotency key per recovery-and-journal.md:49) is deferred beyond the
# poll slice. Poll operates on materialized artifacts and does not
# require turn-level replay.

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from .approval_router import parse_pending_server_request
from .delegation_job_store import DelegationJobStore
from .execution_prompt_builder import (
    build_execution_resume_turn_text,
    build_execution_turn_text,
)
from .execution_runtime_registry import ExecutionRuntimeEntry, ExecutionRuntimeRegistry
from .journal import OperationJournal
from .lineage_store import LineageStore
from .models import (
    ArtifactInspectionSnapshot,
    AuditEvent,
    CollaborationHandle,
    DecisionAction,
    DecisionRejectedReason,
    DecisionRejectedResponse,
    DelegationDecisionResult,
    DelegationEscalation,
    DelegationJob,
    DelegationOutcomeRecord,
    DelegationPollResult,
    DelegationTerminalStatus,
    DiscardRejectedResponse,
    DiscardResult,
    JobBusyResponse,
    JobStatus,
    OperationJournalEntry,
    PendingEscalationView,
    PendingServerRequest,
    PollRejectedResponse,
    PromotionRejectedResponse,
    PromotionResult,
    TurnExecutionResult,
)
from .pending_request_store import PendingRequestStore
from .runtime import AppServerRuntimeSession, build_workspace_write_sandbox_policy

logger = logging.getLogger(__name__)

_TERMINAL_STATUS_MAP: dict[str, DelegationTerminalStatus] = {
    "completed": "completed",
    "failed": "failed",
    "canceled": "canceled",
    "unknown": "unknown",
}

_SANITIZE_MESSAGE_CAP = 200
_SANITIZE_TOTAL_CAP = 256


def _sanitize_error_string(exc: BaseException) -> str:
    """Produce a bounded, JSONL-safe forensic string for persistence.

    Format: "<ExceptionClassName>: <bounded, escaped message>". Used by the
    three PendingServerRequest forensic fields (dispatch_error,
    interrupt_error, internal_abort_reason). Per spec §Sanitization rules:
    raw message truncated at 200 chars pre-escape with "..." elision;
    escaping (newlines/tabs via unicode_escape) may inflate this, which
    the 256-char combined cap absorbs. An over-long class name or
    sufficient escape-inflation triggers the cap with a warning log.
    """
    class_name = type(exc).__name__
    raw = str(exc)
    if len(raw) > _SANITIZE_MESSAGE_CAP:
        message = raw[:_SANITIZE_MESSAGE_CAP] + "..."
    else:
        message = raw
    # Escape newlines, tabs, and other control characters so the final string
    # is a single JSONL-safe line. encode/decode(unicode_escape) preserves
    # regular content while quoting control characters as \n, \t, etc.
    message = message.encode("unicode_escape").decode("ascii")
    combined = f"{class_name}: {message}"
    if len(combined) > _SANITIZE_TOTAL_CAP:
        logger.warning(
            "Forensic string exceeded total cap; truncating. class=%r len=%d",
            class_name,
            len(combined),
        )
        combined = combined[:_SANITIZE_TOTAL_CAP]
    return combined


class DelegationStartError(RuntimeError):
    """Raised by start() when the delegation-start sequence cannot produce
    a successful return value. The reason literal is part of the public
    plugin contract — see §DelegationStartError reasons in the spec.

    __str__ contract: "{reason}: {message}" when message is non-empty,
    else "{reason}". This guarantees MCP text-prefix recoverability
    without requiring a boundary change.

    Raise idiom for cases with a chained cause:
        raise DelegationStartError(reason=..., cause=exc) from exc
    so Python's __cause__ chain is preserved alongside the explicit .cause
    field. Duplication is intentional: __cause__ participates in
    tracebacks; .cause is the typed attribute callers can read without
    walking __cause__.
    """

    reason: str
    cause: Exception | None

    def __init__(
        self,
        *,
        reason: str,
        cause: Exception | None = None,
        message: str = "",
    ) -> None:
        if message:
            super().__init__(f"{reason}: {message}")
        else:
            super().__init__(reason)
        self.reason = reason
        self.cause = cause


class UnknownKindInEscalationProjection(Exception):
    """Raised by _project_request_to_view when request.kind is not in
    EscalatableRequestKind. Internal assertion signal — MUST NOT escape the
    controller boundary.

    Subclass of Exception (NOT RuntimeError) so narrower except clauses
    catch it before a generic `except RuntimeError`. Carries only a
    message; the callsite determines the abort reason.
    """

    pass


@dataclass(frozen=True)
class _WorkerTerminalBranchSignal(Exception):
    """Private sentinel raised by the server-request handler to terminalize
    the worker turn after the branch's own cleanup has already run.

    The handler raises this AFTER performing its branch's own cleanup:
      - writing any final approval_resolution.completed record
      - calling update_parked_request(job_id, None)
      - discarding the per-request registry entry
      - calling _mark_execution_unknown_and_cleanup (closes session, marks job)
      (or the timeout-success analog: _persist_job_transition(..., "canceled"))

    Caught in _execute_live_turn's new except clause BEFORE the generic
    except Exception; MUST NOT escape _execute_live_turn as a raw exception
    or be caught by the worker runner — doing so would produce
    announce_worker_failed for a handler-terminalized branch.

    Six call sites with distinct reason literals per spec §Worker
    terminal-branch signaling primitive — see the table at "Where it is
    raised."
    """

    reason: str


class _ControlPlaneLike(Protocol):
    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, AppServerRuntimeSession, str]: ...


class _WorktreeManagerLike(Protocol):
    def create_worktree(
        self, *, repo_root: Path, base_commit: str, worktree_path: Path
    ) -> None: ...

    def remove_worktree(self, *, repo_root: Path, worktree_path: Path) -> None: ...


class _ArtifactStoreLike(Protocol):
    def materialize_snapshot(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot: ...

    def load_snapshot(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None: ...

    def reconstruct_from_artifacts(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None: ...

    def generate_canonical_artifacts(
        self, *, job: DelegationJob, output_dir: Path
    ) -> Any: ...


class _PromotionCallbackLike(Protocol):
    def on_promotion_verified(
        self,
        *,
        repo_root: Path,
        artifact_hash: str,
        job_id: str,
    ) -> bool: ...


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


class CommittedDecisionFinalizationError(RuntimeError):
    """Raised when codex.delegate.decide committed a caller decision but local
    finalization failed.

    Blind retry is unsafe: approve may have already dispatched a follow-up turn,
    and deny may already have terminated the live runtime.
    """


class DelegationController:
    """Implements codex.delegate.start, codex.delegate.decide, and codex.delegate.poll."""

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
        artifact_store: _ArtifactStoreLike,
        approval_policy: str = "untrusted",
        head_commit_resolver: Callable[[Path], str] | None = None,
        uuid_factory: Callable[[], str] | None = None,
        promotion_callback: _PromotionCallbackLike | None = None,
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
        self._artifact_store = artifact_store
        self._approval_policy = approval_policy
        self._head_commit_resolver = head_commit_resolver or _resolve_head_commit
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
        self._promotion_callback = promotion_callback
        self._decided_request_ids: set[str] = set()

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

        # Busy check — max-1 user-attention job per session. Consults THREE sources:
        #   (a) job_store.list_user_attention_required(): any non-terminal job
        #       (in-flight, completed awaiting review, failed/unknown needing
        #       inspection). Wider than list_active() to enforce the singleton
        #       user-attention invariant.
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
        active = self._job_store.list_user_attention_required()
        if active:
            # Last in replay order = most recently created. Matches
            # get_active_delegation_summary() so /delegate (resume via
            # status) and /delegate <objective> (blocked by busy) route
            # the user to the same job in the pre-migration anomaly case.
            existing = active[-1]
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
                promotion_state=None,
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
                    self._persist_job_transition(job_id, "unknown")
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
        self._job_store.update_status_and_promotion(
            job_id, status="running", promotion_state=None
        )

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
            self._persist_job_transition(job_id, "unknown")
        except Exception:
            logger.error(
                "Execution cleanup: failed to mark job %r unknown",
                job_id,
                exc_info=True,
            )
        self._emit_terminal_outcome_if_needed(job_id)
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

    def _emit_terminal_outcome_if_needed(self, job_id: str) -> None:
        """Best-effort emit DelegationOutcomeRecord for a terminal job."""
        try:
            job = self._job_store.get(job_id)
            if job is None:
                return
            terminal = _TERMINAL_STATUS_MAP.get(job.status)
            if terminal is None:
                return
            handle = self._lineage_store.get(job.collaboration_id)
            self._journal.append_delegation_outcome_once(
                DelegationOutcomeRecord(
                    outcome_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    outcome_type="delegation_terminal",
                    collaboration_id=job.collaboration_id,
                    runtime_id=job.runtime_id,
                    job_id=job_id,
                    terminal_status=terminal,
                    base_commit=job.base_commit,
                    repo_root=handle.repo_root if handle is not None else None,
                )
            )
        except Exception as exc:
            logger.warning(
                "Terminal outcome emission failed for job %r: %s: %s",
                job_id,
                type(exc).__name__,
                exc,
                exc_info=True,
            )

    def _persist_job_transition(self, job_id: str, status: JobStatus) -> DelegationJob:
        self._job_store.update_status_and_promotion(
            job_id,
            status=status,
            promotion_state="pending" if status == "completed" else None,
        )
        updated = self._job_store.get(job_id)
        assert updated is not None, (
            f"DelegationJobStore invariant violation: job_id={job_id!r} "
            f"was just updated but get() returned None"
        )
        return updated

    # Plugin-level decisions exposed by codex.delegate.decide.
    _PLUGIN_DECISIONS: tuple[str, ...] = ("approve", "deny")

    def _project_request_to_view(
        self, request: PendingServerRequest
    ) -> PendingEscalationView:
        """Project a PendingServerRequest to the caller-visible PendingEscalationView."""
        return PendingEscalationView(
            request_id=request.request_id,
            kind=request.kind,
            requested_scope=request.requested_scope,
            available_decisions=self._PLUGIN_DECISIONS,
        )

    def _project_pending_escalation(
        self, collaboration_id: str
    ) -> PendingEscalationView | None:
        requests = self._pending_request_store.list_by_collaboration_id(
            collaboration_id
        )
        if not requests:
            return None
        return self._project_request_to_view(requests[-1])

    def _load_or_materialize_inspection(
        self, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None:
        if job.status not in ("completed", "failed", "unknown"):
            return None
        existing = self._artifact_store.load_snapshot(job=job)
        if existing is not None:
            if (
                job.artifact_paths != existing.artifact_paths
                or job.artifact_hash != existing.artifact_hash
            ):
                self._job_store.update_artifacts(
                    job.job_id,
                    artifact_paths=existing.artifact_paths,
                    artifact_hash=existing.artifact_hash,
                )
            return existing
        # No usable cache. If the store already holds a reviewed hash,
        # the job was previously materialized — do not recompute from the
        # worktree (it may have been modified since the original review).
        # Reconstruct from the persisted artifact files instead.
        if job.artifact_hash is not None:
            return self._artifact_store.reconstruct_from_artifacts(job=job)
        snapshot = self._artifact_store.materialize_snapshot(job=job)
        self._job_store.update_artifacts(
            job.job_id,
            artifact_paths=snapshot.artifact_paths,
            artifact_hash=snapshot.artifact_hash,
        )
        return snapshot

    def poll(self, *, job_id: str) -> DelegationPollResult | PollRejectedResponse:
        job = self._job_store.get(job_id)
        if job is None:
            return PollRejectedResponse(
                rejected=True,
                reason="job_not_found",
                detail=f"Delegation poll failed: job not found. Got: {job_id!r:.100}",
                job_id=job_id,
            )

        materialization_failed = False
        try:
            inspection = self._load_or_materialize_inspection(job)
        except (subprocess.CalledProcessError, OSError) as exc:
            logger.warning(
                "poll: artifact materialization failed for job %r: %s",
                job_id,
                exc,
            )
            inspection = None
            materialization_failed = True
        refreshed = self._job_store.get(job_id) or job
        pending_escalation = None
        if refreshed.status == "needs_escalation":
            pending_escalation = self._project_pending_escalation(
                refreshed.collaboration_id
            )

        detail = None
        if refreshed.status == "failed":
            detail = "Delegation execution failed. Inspect artifacts before retrying or discarding."
        elif refreshed.status == "unknown":
            detail = "Delegation outcome could not be confirmed after recovery. Inspect artifacts, then restart or discard."

        if inspection is None and refreshed.artifact_hash is not None:
            detail = "Inspection artifacts unavailable — original artifact files may have been deleted."
        elif inspection is None and materialization_failed:
            detail = "Artifact materialization failed — worktree may have been deleted or is unreachable."

        return DelegationPollResult(
            job=refreshed,
            pending_escalation=pending_escalation,
            inspection=inspection,
            detail=detail,
        )

    def promote(self, *, job_id: str) -> PromotionResult | PromotionRejectedResponse:
        """Apply the reviewed diff from a completed delegation to the primary workspace.

        Entry gates (before numbered prechecks):
          - Job exists
          - status == "completed"
          - promotion_state in {"pending", "prechecks_failed"}
          - artifact_hash present (reviewed)
          - Collaboration handle exists in lineage store

        Prechecks (after entry gates pass):
          1. HEAD == base_commit
          2. git status --porcelain empty (no untracked/modified files)
          3. git diff --cached clean (no staged changes)
          4. Regenerated artifact hash matches the reviewed hash

        On success: applies full.diff, verifies, transitions to "verified".
        On precheck failure: transitions to "prechecks_failed".
        On verification failure: rolls back and transitions to "rolled_back".
        """
        job = self._job_store.get(job_id)
        if job is None:
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_completed",
                detail=f"Promotion failed: job not found. Got: {job_id!r:.100}",
                job_id=job_id,
            )
        if job.status != "completed":
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_completed",
                detail=(
                    "Promotion failed: job not in completed status. "
                    f"Got: status={job.status!r:.100}"
                ),
                job_id=job_id,
            )
        # State-machine gate: only pending and prechecks_failed accept promote.
        if job.promotion_state not in ("pending", "prechecks_failed"):
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_completed",
                detail=(
                    "Promotion failed: job promotion_state is not promotable. "
                    f"Got: promotion_state={job.promotion_state!r:.100}"
                ),
                job_id=job_id,
            )
        # Increment promotion_attempt once before all prechecks.
        new_attempt = (job.promotion_attempt or 0) + 1

        if job.artifact_hash is None:
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_reviewed",
                detail="Promotion failed: no reviewed artifact hash present.",
                job_id=job_id,
            )

        # Resolve the primary workspace from the lineage store.
        handle = self._lineage_store.get(job.collaboration_id)
        if handle is None:
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="job_not_completed",
                detail="Promotion failed: collaboration handle not found.",
                job_id=job_id,
            )
        primary_repo_root = Path(handle.repo_root)

        # Precheck: HEAD == base_commit.
        try:
            current_head = self._head_commit_resolver(primary_repo_root)
        except RuntimeError:
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="head_mismatch",
                detail="Promotion failed: could not resolve HEAD.",
                job_id=job_id,
                expected=job.base_commit,
            )
        if current_head != job.base_commit:
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="head_mismatch",
                detail=(
                    "Promotion failed: HEAD does not match base_commit. "
                    f"Got: HEAD={current_head!r:.40}"
                ),
                job_id=job_id,
                expected=job.base_commit,
                actual=current_head,
            )

        # Precheck: git status --porcelain empty.
        porcelain_result = subprocess.run(
            ["git", "-C", str(primary_repo_root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if porcelain_result.stdout.strip():
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="worktree_dirty",
                detail="Promotion failed: primary workspace has uncommitted changes.",
                job_id=job_id,
            )

        # Precheck: git diff --cached clean.
        index_result = subprocess.run(
            ["git", "-C", str(primary_repo_root), "diff", "--cached", "--exit-code"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if index_result.returncode != 0:
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="prechecks_failed",
                promotion_attempt=new_attempt,
            )
            return PromotionRejectedResponse(
                rejected=True,
                reason="index_dirty",
                detail="Promotion failed: primary workspace index is not clean.",
                job_id=job_id,
            )

        # Precheck: regenerate artifacts and compare hash.
        with tempfile.TemporaryDirectory() as tmp_dir:
            bundle = self._artifact_store.generate_canonical_artifacts(
                job=job,
                output_dir=Path(tmp_dir),
            )
            if bundle.artifact_hash != job.artifact_hash:
                self._job_store.update_promotion_state(
                    job_id,
                    promotion_state="prechecks_failed",
                    promotion_attempt=new_attempt,
                )
                return PromotionRejectedResponse(
                    rejected=True,
                    reason="artifact_hash_mismatch",
                    detail=(
                        "Promotion failed: regenerated artifact hash does not match "
                        "reviewed hash (worktree was modified since review)."
                    ),
                    job_id=job_id,
                    expected=job.artifact_hash,
                    actual=bundle.artifact_hash,
                )

        # All prechecks passed. Write journal intent phase FIRST (WAL ordering).
        # Intent must precede prechecks_passed state so recovery always has a
        # journal entry to process if a crash strands prechecks_passed.
        idempotency_key = f"promotion:{job_id}:{new_attempt}"
        created_at = self._journal.timestamp()
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="promotion",
                phase="intent",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=str(primary_repo_root),
                job_id=job_id,
            ),
            session_id=self._session_id,
        )

        # Record prechecks_passed state (after intent journal entry).
        self._job_store.update_promotion_state(
            job_id,
            promotion_state="prechecks_passed",
            promotion_attempt=new_attempt,
        )

        # Identify new paths: files in the reviewed change set not tracked
        # in the primary workspace. Used for rollback file removal.
        reviewed_changed_files: list[str] = []
        for artifact_path_str in job.artifact_paths:
            artifact_path = Path(artifact_path_str)
            if artifact_path.name == "changed-files.json" and artifact_path.exists():
                try:
                    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                    if isinstance(payload, dict):
                        reviewed_changed_files = list(payload.get("changed_files", []))
                except (ValueError, KeyError, TypeError):
                    pass
                break

        reviewed_paths = set(reviewed_changed_files)
        new_paths = {
            path
            for path in reviewed_paths
            if not _path_is_tracked(primary_repo_root, path)
        }

        # Journal dispatched phase BEFORE apply — WAL semantics.
        # Recovery treats "dispatched" as "mutation may have happened."
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="promotion",
                phase="dispatched",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=str(primary_repo_root),
                job_id=job_id,
            ),
            session_id=self._session_id,
        )

        # Apply the reviewed full.diff.
        full_diff_path = Path(job.artifact_paths[0])
        subprocess.run(
            [
                "git",
                "-C",
                str(primary_repo_root),
                "apply",
                "--binary",
                str(full_diff_path),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )

        # Record applied state — mutation has occurred.
        self._job_store.update_promotion_state(
            job_id,
            promotion_state="applied",
            promotion_attempt=new_attempt,
        )

        # Verify: re-generate artifacts from the primary workspace state
        # and compare hash to the reviewed hash.
        verified = self._verify_promotion(
            job=job,
            primary_repo_root=primary_repo_root,
            reviewed_changed_files=reviewed_changed_files,
        )

        if not verified:
            # Rollback: revert tracked files and remove new untracked files.
            self._job_store.update_promotion_state(
                job_id,
                promotion_state="rollback_needed",
                promotion_attempt=new_attempt,
            )
            subprocess.run(
                ["git", "-C", str(primary_repo_root), "checkout", "--", "."],
                check=True,
                capture_output=True,
                timeout=10,
            )
            for relative_path in sorted(new_paths):
                target = primary_repo_root / relative_path
                if target.exists():
                    target.unlink()

            self._job_store.update_promotion_state(
                job_id,
                promotion_state="rolled_back",
                promotion_attempt=new_attempt,
            )

            # Journal completed phase for rollback.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=idempotency_key,
                    operation="promotion",
                    phase="completed",
                    collaboration_id=job.collaboration_id,
                    created_at=created_at,
                    repo_root=str(primary_repo_root),
                    job_id=job_id,
                ),
                session_id=self._session_id,
            )

            return PromotionRejectedResponse(
                rejected=True,
                reason="artifact_hash_mismatch",
                detail=(
                    "Promotion failed: post-apply verification detected workspace "
                    "mismatch. Rolled back."
                ),
                job_id=job_id,
                expected=job.artifact_hash,
            )

        # Verified. Update state and invoke callback.
        self._job_store.update_promotion_state(
            job_id,
            promotion_state="verified",
            promotion_attempt=new_attempt,
        )

        stale_advisory_context = False
        if self._promotion_callback is not None:
            stale_advisory_context = self._promotion_callback.on_promotion_verified(
                repo_root=primary_repo_root,
                artifact_hash=job.artifact_hash,
                job_id=job_id,
            )

        # Audit event.
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="promote",
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                job_id=job_id,
                decision="approve",
            )
        )

        # Journal completed phase.
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="promotion",
                phase="completed",
                collaboration_id=job.collaboration_id,
                created_at=created_at,
                repo_root=str(primary_repo_root),
                job_id=job_id,
            ),
            session_id=self._session_id,
        )

        # Re-read the job to get the final state.
        final_job = self._job_store.get(job_id) or job
        return PromotionResult(
            job=final_job,
            artifact_hash=job.artifact_hash,
            changed_files=tuple(reviewed_changed_files),
            stale_advisory_context=stale_advisory_context,
        )

    def _verify_promotion(
        self,
        *,
        job: DelegationJob,
        primary_repo_root: Path,
        reviewed_changed_files: list[str],
    ) -> bool:
        """Verify the post-apply state matches the reviewed artifacts.

        Three checks per promotion-protocol.md §Post-Apply Verification:
        1. Byte-compare regenerated full.diff to reviewed full.diff
        2. Compare regenerated changed-file set to reviewed changed-files.json
        3. Porcelain shows only the expected modifications

        Uses ``generate_canonical_artifacts`` on the primary workspace to
        reuse the exact ``_full_diff()`` generation logic (including
        synthetic no-index sections for new files). Compares only the
        applyable subset — ignores ``artifact_hash`` and
        ``test_results_path`` because the canonical review set includes
        execution-side data not present in the primary workspace.
        """
        reviewed_diff = Path(job.artifact_paths[0]).read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # status="completed" is hardcoded: the only way to reach this
            # method is through a completed job, and the hash is not used.
            bundle = self._artifact_store.generate_canonical_artifacts(
                job=DelegationJob(
                    job_id=job.job_id,
                    runtime_id=job.runtime_id,
                    collaboration_id=job.collaboration_id,
                    base_commit=job.base_commit,
                    worktree_path=str(primary_repo_root),
                    promotion_state=job.promotion_state,
                    status="completed",
                    artifact_paths=job.artifact_paths,
                    artifact_hash=job.artifact_hash,
                ),
                output_dir=Path(tmp_dir),
            )

            # 1. Byte-compare full.diff (reuses _full_diff() for new-file handling).
            actual_diff = bundle.full_diff_path.read_text(encoding="utf-8")
            if actual_diff.rstrip() != reviewed_diff.rstrip():
                return False

            # 2. Compare changed-file set.
            if sorted(bundle.changed_files) != sorted(reviewed_changed_files):
                return False

        # 3. Porcelain: only expected modifications.
        # Use rstrip(), not strip() — the leading space is part of the
        # XY status format (e.g., " M README.md" for unstaged changes).
        porcelain_output = subprocess.run(
            ["git", "-C", str(primary_repo_root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.rstrip()
        if porcelain_output:
            expected_paths = set(reviewed_changed_files)
            for entry in porcelain_output.splitlines():
                # Porcelain format: XY<space>path (or XY<space>path -> renamed)
                file_path = entry[3:].split(" -> ")[-1]
                if file_path not in expected_paths:
                    return False
        return True

    def discard(self, *, job_id: str) -> DiscardResult | DiscardRejectedResponse:
        """Discard a delegation job without promoting.

        Allowed when promotion_state in (pending, prechecks_failed), or when
        status in (failed, unknown) and promotion_state is None (pre-mutation).
        Post-mutation states (applied, rollback_needed) are never discardable.
        """
        job = self._job_store.get(job_id)
        if job is None:
            return DiscardRejectedResponse(
                rejected=True,
                reason="job_not_found",
                detail=f"Discard failed: job not found. Got: {job_id!r:.100}",
                job_id=job_id,
            )
        _discardable = job.promotion_state in ("pending", "prechecks_failed") or (
            job.status in ("failed", "unknown") and job.promotion_state is None
        )
        if not _discardable:
            return DiscardRejectedResponse(
                rejected=True,
                reason="job_not_discardable",
                detail=(
                    "Discard failed: job promotion_state is not discardable. "
                    f"Got: promotion_state={job.promotion_state!r:.100}"
                ),
                job_id=job_id,
            )

        self._job_store.update_promotion_state(
            job_id,
            promotion_state="discarded",
        )

        # Audit event.
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="discard",
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                job_id=job_id,
            )
        )

        updated = self._job_store.get(job_id) or job
        return DiscardResult(job=updated)

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

        Called by _execute_live_turn (used by both start and decide).
        Separated so the caller can wrap it in a failure guard.
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
                final_status: JobStatus = "needs_escalation"
            elif turn_result.status == "completed":
                final_status = "completed"
            else:
                final_status = "needs_escalation"

            updated_job = self._persist_job_transition(job_id, final_status)

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
                    pending_escalation=self._project_request_to_view(
                        resolved_request or captured_request
                    ),
                    agent_context=turn_result.agent_message or None,
                )

            # Non-escalation: mark handle completed, release + close and return plain job.
            self._lineage_store.update_status(collaboration_id, "completed")
            self._runtime_registry.release(runtime_id)
            entry.session.close()
            self._emit_terminal_outcome_if_needed(job_id)
            return updated_job

        # No server request captured — clean completion or failure.
        if turn_result.status == "completed":
            no_request_status: JobStatus = "completed"
        elif turn_result.status == "failed":
            no_request_status = "failed"
        else:
            no_request_status = "unknown"

        updated_job = self._persist_job_transition(job_id, no_request_status)
        self._lineage_store.update_status(collaboration_id, "completed")
        self._runtime_registry.release(runtime_id)
        entry.session.close()
        self._emit_terminal_outcome_if_needed(job_id)

        return updated_job

    def _reject_decision(
        self,
        *,
        reason: DecisionRejectedReason,
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
        if request_id in self._decided_request_ids:
            return self._reject_decision(
                reason="request_already_decided",
                detail=(
                    "Delegation decide failed: request was already decided. "
                    f"Got: {request_id!r:.100}"
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
        if (
            request.kind == "request_user_input"
            and decision == "approve"
            and not answers
        ):
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
            try:
                self._persist_job_transition(job_id, "failed")
                self._emit_terminal_outcome_if_needed(job_id)
                self._lineage_store.update_status(job.collaboration_id, "completed")
                self._runtime_registry.release(job.runtime_id)
                entry.session.close()
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
                self._decided_request_ids.add(request_id)
                return DelegationDecisionResult(
                    decision_accepted=True,
                    job_id=job_id,
                    request_id=request_id,
                )
            except Exception as exc:
                raise CommittedDecisionFinalizationError(
                    "Delegation decide committed deny but local finalization failed: "
                    f"{exc}. The deny decision has been audited."
                ) from exc

        prompt_text = build_execution_resume_turn_text(
            pending_request=request,
            answers=answers,
        )
        try:
            self._execute_live_turn(
                job_id=job_id,
                collaboration_id=job.collaboration_id,
                runtime_id=job.runtime_id,
                worktree_path=Path(job.worktree_path),
                prompt_text=prompt_text,
            )
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
            self._decided_request_ids.add(request_id)
            return DelegationDecisionResult(
                decision_accepted=True,
                job_id=job_id,
                request_id=request_id,
            )
        except Exception as exc:
            raise CommittedDecisionFinalizationError(
                "Delegation decide committed but local finalization failed: "
                f"{exc}. Blind retry may duplicate follow-up execution."
            ) from exc

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
                    self._persist_job_transition(entry.job_id, "unknown")

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

        # --- approval_resolution reconciliation ---
        # Close unresolved approval_resolution journal entries left by
        # CommittedDecisionFinalizationError or mid-decide crashes.
        approval_resolution_entries = [
            e for e in unresolved if e.operation == "approval_resolution"
        ]
        by_key_ar: dict[str, OperationJournalEntry] = {}
        for entry in approval_resolution_entries:
            existing = by_key_ar.get(entry.idempotency_key)
            if existing is None or _phase_rank(entry.phase) > _phase_rank(
                existing.phase
            ):
                by_key_ar[entry.idempotency_key] = entry

        for entry in by_key_ar.values():
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
                    completion_origin="recovered_unresolved",
                ),
                session_id=self._session_id,
            )

        # --- promotion reconciliation ---
        # Close unresolved promotion journal entries left by crashes during
        # the promotion lifecycle.
        promotion_entries = [e for e in unresolved if e.operation == "promotion"]
        by_key_pr: dict[str, OperationJournalEntry] = {}
        for entry in promotion_entries:
            existing = by_key_pr.get(entry.idempotency_key)
            if existing is None or _phase_rank(entry.phase) > _phase_rank(
                existing.phase
            ):
                by_key_pr[entry.idempotency_key] = entry

        for entry in by_key_pr.values():
            if entry.phase == "intent":
                # No mutation happened — normalize the job back to pending
                # and close the journal entry. Preserve the attempt counter
                # so the next promote() does not reuse the same idempotency key.
                if entry.job_id is not None:
                    job = self._job_store.get(entry.job_id)
                    if job is not None and job.promotion_state not in (
                        "verified",
                        "discarded",
                        "rolled_back",
                    ):
                        # Parse the attempt from the idempotency key
                        # (format: "promotion:{job_id}:{attempt}").
                        recovered_attempt: int | None = None
                        parts = entry.idempotency_key.rsplit(":", 1)
                        if len(parts) == 2:
                            try:
                                recovered_attempt = int(parts[1])
                            except ValueError:
                                pass
                        self._job_store.update_promotion_state(
                            entry.job_id,
                            promotion_state="pending",
                            **(
                                {"promotion_attempt": recovered_attempt}
                                if recovered_attempt is not None
                                else {}
                            ),
                        )
            elif entry.phase == "dispatched":
                # Mutation may have happened — re-verify in the primary workspace.
                if entry.job_id is not None:
                    job = self._job_store.get(entry.job_id)
                    if job is not None and job.promotion_state not in (
                        "verified",
                        "discarded",
                        "rolled_back",
                    ):
                        primary_repo_root = Path(entry.repo_root)
                        # Load reviewed changed files for both verify and rollback.
                        reviewed_changed_files: list[str] = []
                        for artifact_path_str in job.artifact_paths or ():
                            artifact_path = Path(artifact_path_str)
                            if (
                                artifact_path.name == "changed-files.json"
                                and artifact_path.exists()
                            ):
                                try:
                                    payload = json.loads(
                                        artifact_path.read_text(encoding="utf-8")
                                    )
                                    if isinstance(payload, dict):
                                        reviewed_changed_files = list(
                                            payload.get("changed_files", [])
                                        )
                                except (ValueError, KeyError, TypeError):
                                    pass
                                break
                        verified = self._verify_promotion(
                            job=job,
                            primary_repo_root=primary_repo_root,
                            reviewed_changed_files=reviewed_changed_files,
                        )
                        if verified:
                            self._job_store.update_promotion_state(
                                entry.job_id,
                                promotion_state="verified",
                            )
                        else:
                            # Mutation happened but verification failed — rollback.
                            new_paths = {
                                path
                                for path in reviewed_changed_files
                                if not _path_is_tracked(primary_repo_root, path)
                            }
                            self._job_store.update_promotion_state(
                                entry.job_id,
                                promotion_state="rollback_needed",
                            )
                            try:
                                subprocess.run(
                                    [
                                        "git",
                                        "-C",
                                        str(primary_repo_root),
                                        "checkout",
                                        "--",
                                        ".",
                                    ],
                                    check=True,
                                    capture_output=True,
                                    timeout=10,
                                )
                                for relative_path in sorted(new_paths):
                                    target = primary_repo_root / relative_path
                                    if target.exists():
                                        target.unlink()
                            except subprocess.CalledProcessError:
                                logger.warning(
                                    "Promotion recovery: rollback git checkout failed "
                                    "for job %r — leaving journal unresolved for "
                                    "next recovery attempt",
                                    entry.job_id,
                                )
                                # Do NOT write rolled_back or close the journal.
                                # Leave unresolved so next startup re-enters recovery.
                                continue
                            self._job_store.update_promotion_state(
                                entry.job_id,
                                promotion_state="rolled_back",
                            )

            # Advance journal to completed.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation="promotion",
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                    job_id=entry.job_id,
                ),
                session_id=self._session_id,
            )

        # --- Orphaned active-job reconciliation ---
        # After a cold restart, the runtime registry is fresh: no live
        # runtimes exist. Any job persisted as "running" or
        # "needs_escalation" is orphaned — the runtime subprocess that
        # was serving it is gone. There is no journal replay anchor for
        # the turn window (D2: first turn is intentionally unjournaled),
        # so the only safe terminal state is "unknown".
        #
        # This is separate from the journal-based reconciliation above
        # because the journal entry is already "completed" at this point
        # (job_creation.completed fired before turn dispatch).
        for job in self._job_store.list_active():
            if job.status in ("running", "needs_escalation"):
                self._persist_job_transition(job.job_id, "unknown")
                handle = self._lineage_store.get(job.collaboration_id)
                if handle is not None and handle.status == "active":
                    self._lineage_store.update_status(
                        job.collaboration_id,
                        "unknown",
                    )

        # --- Terminal outcome catch-up (same-session only) ---
        # Sweep all same-session jobs for terminal statuses missing their
        # analytics outcome. Uses list() (all session jobs), NOT
        # list_user_attention_required() — the latter excludes terminal
        # promotion states (verified/discarded/rolled_back) which are
        # still terminal from an outcome-emission perspective.
        # Cross-session abandoned outcomes are structurally unreachable
        # (DelegationJobStore is session-scoped). This is a documented
        # T-07 limitation, not a bug.
        for job in self._job_store.list():
            if job.status in ("completed", "failed", "unknown"):
                self._emit_terminal_outcome_if_needed(job.job_id)

    def get_active_delegation_summary(self) -> tuple[DelegationJob | None, int]:
        """Return the active user-attention-required job and total count.

        Returns (job, count). job is the last in store replay order
        (most recently created). count > 1 is a pre-migration anomaly
        — the widened busy gate prevents new multi-attention states,
        but sessions started before the gate was widened may have
        multiple attention-active jobs.

        Used by codex.status enrichment. Preserves encapsulation —
        callers do not reach into the private job store.
        """
        attention = self._job_store.list_user_attention_required()
        if not attention:
            return None, 0
        # Last in replay order = most recently created (JSONL append order).
        return attention[-1], len(attention)


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


def _path_is_tracked(repo_root: Path, relative_path: str) -> bool:
    """Return True if the path is tracked in the git index."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", relative_path],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _phase_rank(phase: str) -> int:
    """Phase-ordering helper for picking the latest phase per idempotency key."""
    return {"intent": 0, "dispatched": 1, "completed": 2}.get(phase, -1)
