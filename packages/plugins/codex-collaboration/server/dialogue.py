"""Dialogue controller for codex.dialogue.start, .reply, .read.

Orchestrates dialogue operations by composing ControlPlane (runtime bootstrap),
LineageStore (handle persistence), and OperationJournal (crash-recovery entries).
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Callable, Literal

from .context_assembly import assemble_context_packet
from .control_plane import ControlPlane, load_repo_identity
from .lineage_store import LineageStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    ConsultRequest,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    DialogueTurnSummary,
    OperationJournalEntry,
    OutcomeRecord,
    RepoIdentity,
)
from .journal import OperationJournal
from .prompt_builder import (
    CONSULT_OUTPUT_SCHEMA,
    build_consult_turn_text,
    parse_consult_response,
)
from .turn_store import TurnStore


class CommittedTurnParseError(RuntimeError):
    """Turn dispatched and committed, but response parsing failed.

    The turn is durably recorded (journal completed, TurnStore written, audit
    emitted). Use ``codex.dialogue.read`` to inspect the committed turn.
    Blind retry will create a duplicate follow-up turn, not replay this one.
    """


class CommittedTurnFinalizationError(RuntimeError):
    """Turn committed, but local finalization or inline recovery failed.

    The committed turn may already be readable via ``codex.dialogue.read``.
    Blind retry will create a duplicate follow-up turn, not replay this one.
    """


RepairTurnResult = Literal[
    "unconfirmed",
    "confirmed_unfinalized",
    "confirmed_finalized",
]


def _log_recovery_failure(operation: str, reason: Exception, got: object) -> None:
    print(
        f"codex-collaboration: {operation} failed: {reason}. Got: {got!r:.100}",
        file=sys.stderr,
    )


def _local_metadata_complete_for_completed_turns(
    local_turns: dict[int, int], completed_count: int
) -> bool:
    """True iff local metadata covers every completed remote turn.

    Checks that keys {1, 2, ..., completed_count} are all present.
    Extra local keys beyond completed_count are not rejected — they are
    anomalous but do not affect turn-sequence derivation. This matches
    the prefix-completeness rule enforced by read() (dialogue.py:853)
    and the crash-recovery contract (contracts.md:156-158).

    For completed_count == 0: returns True only if local_turns is empty.
    This is a deliberate tightening beyond read()'s enforcement — stale
    local metadata with zero completed remote turns is anomalous state.
    """
    if completed_count == 0:
        return not local_turns
    return set(range(1, completed_count + 1)).issubset(local_turns.keys())


class DialogueController:
    """Implements codex.dialogue.start, .reply, .read, and crash recovery."""

    def __init__(
        self,
        *,
        control_plane: ControlPlane,
        lineage_store: LineageStore,
        journal: OperationJournal,
        session_id: str,
        turn_store: TurnStore,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._lineage_store = lineage_store
        self._journal = journal
        self._session_id = session_id
        self._turn_store = turn_store
        self._repo_identity_loader = repo_identity_loader or load_repo_identity
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))

    def start(
        self, repo_root: Path, *, profile_name: str | None = None
    ) -> DialogueStartResult:
        """Create a durable dialogue thread and persist handle.

        Spec: contracts.md §Dialogue Start, delivery.md §R2 in-scope.
        No audit event — thread creation is not a trust boundary crossing
        (contracts.md §Audit Event Actions does not define dialogue_start).
        """
        resolved_root = repo_root.resolve()
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        resolved_posture: str | None = None
        resolved_effort: str | None = None
        resolved_turn_budget: int | None = None
        if profile_name is not None:
            from .profiles import resolve_profile

            resolved = resolve_profile(profile_name=profile_name)
            resolved_posture = resolved.posture
            resolved_effort = resolved.effort
            resolved_turn_budget = resolved.turn_budget

        collaboration_id = self._uuid_factory()
        created_at = self._journal.timestamp()

        # Phase 1: intent — journal before dispatch
        idempotency_key = f"{self._session_id}:{collaboration_id}"
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="intent",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        try:
            thread_id = runtime.session.start_thread()
            runtime.thread_count += 1
        except Exception:
            self._control_plane.invalidate_runtime(resolved_root)
            raise

        # Phase 2: dispatched — record outcome correlation data
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="dispatched",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
                codex_thread_id=thread_id,
            ),
            session_id=self._session_id,
        )

        handle = CollaborationHandle(
            collaboration_id=collaboration_id,
            capability_class="advisory",
            runtime_id=runtime.runtime_id,
            codex_thread_id=thread_id,
            claude_session_id=self._session_id,
            repo_root=str(resolved_root),
            created_at=created_at,
            status="active",
            resolved_posture=resolved_posture,
            resolved_effort=resolved_effort,
            resolved_turn_budget=resolved_turn_budget,
        )
        self._lineage_store.create(handle)

        # Phase 3: completed — operation fully confirmed
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="thread_creation",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        return DialogueStartResult(
            collaboration_id=collaboration_id,
            runtime_id=runtime.runtime_id,
            status="active",
            created_at=created_at,
        )

    @staticmethod
    def _committed_turn_error_message(reason: str) -> str:
        return (
            f"{reason}. The turn is durably recorded. Use codex.dialogue.read to "
            "inspect the committed turn. Blind retry will create a duplicate "
            "follow-up turn, not replay this one."
        )

    def _completed_entry(self, entry: OperationJournalEntry) -> OperationJournalEntry:
        return OperationJournalEntry(
            idempotency_key=entry.idempotency_key,
            operation=entry.operation,
            phase="completed",
            collaboration_id=entry.collaboration_id,
            created_at=entry.created_at,
            repo_root=entry.repo_root,
        )

    def _finalize_confirmed_turn(
        self,
        *,
        entry: OperationJournalEntry,
        turn_id: str | None,
        policy_fingerprint: str | None,
        outcome_timestamp: str,
    ) -> None:
        """Persist all local artifacts for a confirmed turn before completion."""

        if entry.context_size is not None and entry.turn_sequence is not None:
            self._turn_store.write(
                entry.collaboration_id,
                turn_sequence=entry.turn_sequence,
                context_size=entry.context_size,
            )

        if entry.runtime_id is not None and turn_id is not None:
            self._journal.append_dialogue_audit_event_once(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="dialogue_turn",
                    collaboration_id=entry.collaboration_id,
                    runtime_id=entry.runtime_id,
                    context_size=entry.context_size,
                    turn_id=turn_id,
                )
            )
            self._journal.append_dialogue_outcome_once(
                OutcomeRecord(
                    outcome_id=self._uuid_factory(),
                    timestamp=outcome_timestamp,
                    outcome_type="dialogue_turn",
                    collaboration_id=entry.collaboration_id,
                    runtime_id=entry.runtime_id,
                    context_size=entry.context_size,
                    turn_id=turn_id,
                    turn_sequence=entry.turn_sequence,
                    policy_fingerprint=policy_fingerprint,
                    repo_root=entry.repo_root,
                )
            )

        self._journal.write_phase(
            self._completed_entry(entry),
            session_id=self._session_id,
        )

    @staticmethod
    def _confirmed_turn_details(
        completed_turns: list[dict[str, object]],
        *,
        turn_sequence: int | None,
        fallback_timestamp: str,
    ) -> tuple[str | None, str]:
        turn_id = None
        if turn_sequence is None:
            return (turn_id, fallback_timestamp)
        turn_index = turn_sequence - 1
        if 0 <= turn_index < len(completed_turns):
            raw_turn = completed_turns[turn_index]
            candidate_turn_id = raw_turn.get("id")
            if isinstance(candidate_turn_id, str) and candidate_turn_id:
                turn_id = candidate_turn_id
            created_at = raw_turn.get("createdAt")
            if isinstance(created_at, str) and created_at:
                return (turn_id, created_at)
        return (turn_id, fallback_timestamp)

    def _resume_handle_inline(
        self,
        *,
        collaboration_id: str,
        repo_root: str,
        codex_thread_id: str,
    ) -> bool:
        """Best-effort inline reattach after repair confirms a committed turn."""

        try:
            runtime = self._control_plane.get_advisory_runtime(Path(repo_root))
            resumed_thread_id = runtime.session.resume_thread(codex_thread_id)
        except Exception as exc:
            _log_recovery_failure("inline_resume_turn", exc, collaboration_id)
            self._lineage_store.update_status(collaboration_id, "unknown")
            return False

        self._lineage_store.update_runtime(
            collaboration_id,
            runtime_id=runtime.runtime_id,
            codex_thread_id=resumed_thread_id,
        )
        self._lineage_store.update_status(collaboration_id, "active")
        return True

    def reply(
        self,
        *,
        collaboration_id: str,
        objective: str,
        user_constraints: tuple[str, ...] = (),
        acceptance_criteria: tuple[str, ...] = (),
        explicit_paths: tuple[Path, ...] = (),
        explicit_snippets: tuple[str, ...] = (),
        task_local_paths: tuple[Path, ...] = (),
        broad_repository_summaries: tuple[str, ...] = (),
        promoted_summaries: tuple[str, ...] = (),
        delegation_summaries: tuple[str, ...] = (),
        supplementary_context: tuple[str, ...] = (),
    ) -> DialogueReplyResult:
        """Continue a dialogue turn on an existing handle.

        Spec: contracts.md §Dialogue Reply, delivery.md §R2 in-scope.
        Context assembly reuse: same pipeline as consultation.

        Write ordering invariant: local finalization MUST complete before the
        journal is marked completed.

        Failure semantics:
        - run_turn() raises: inspect via _best_effort_repair_turn(). If the turn
          is still unconfirmed, re-raise the original dispatch exception after
          quarantining the handle. If the turn is confirmed, surface a
          CommittedTurnFinalizationError instead of a raw dispatch failure.
        - local finalization raises after run_turn() succeeds: leave the
          journal at dispatched, quarantine the handle, and raise
          CommittedTurnFinalizationError.
        - parse_consult_response() raises after completed: raise
          CommittedTurnParseError. Handle stays active.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Reply failed: handle not found. "
                f"Got: collaboration_id={collaboration_id!r:.100}"
            )
        if handle.status != "active":
            raise ValueError(
                f"Reply failed: handle not active. "
                f"Got: status={handle.status!r}, collaboration_id={collaboration_id!r:.100}"
            )

        posture = handle.resolved_posture  # may be None
        effort = handle.resolved_effort  # may be None

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)
        repo_identity = self._repo_identity_loader(resolved_root)

        # Derive turn_sequence from completed turns via thread/read (contracts.md:266).
        # Safe only while the MCP server keeps serialized dispatch for the
        # accepted R1/R2 rollout posture — no concurrent advisory turns to race with.
        turn_sequence = self._next_turn_sequence(handle, runtime)

        # Build consult request for context assembly (reuse same pipeline)
        request = ConsultRequest(
            repo_root=resolved_root,
            objective=objective,
            user_constraints=user_constraints,
            acceptance_criteria=acceptance_criteria,
            explicit_paths=explicit_paths,
            explicit_snippets=explicit_snippets,
            task_local_paths=task_local_paths,
            broad_repository_summaries=broad_repository_summaries,
            promoted_summaries=promoted_summaries,
            delegation_summaries=delegation_summaries,
            supplementary_context=supplementary_context,
        )
        packet = assemble_context_packet(request, repo_identity, profile="advisory")

        # Phase 1: intent — journal before dispatch (turn-dispatch key)
        idempotency_key = (
            f"{runtime.runtime_id}:{handle.codex_thread_id}:{turn_sequence}"
        )
        created_at = self._journal.timestamp()
        intent_entry = OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(resolved_root),
            codex_thread_id=handle.codex_thread_id,
            turn_sequence=turn_sequence,
            runtime_id=runtime.runtime_id,
            context_size=packet.context_size,
        )
        self._journal.write_phase(intent_entry, session_id=self._session_id)

        try:
            turn_result = runtime.session.run_turn(
                thread_id=handle.codex_thread_id,
                prompt_text=build_consult_turn_text(packet.payload, posture=posture),
                output_schema=CONSULT_OUTPUT_SCHEMA,
                effort=effort,
            )
        except Exception as exc:
            self._control_plane.invalidate_runtime(resolved_root)
            repair_result = self._best_effort_repair_turn(intent_entry)
            if repair_result == "unconfirmed":
                self._lineage_store.update_status(collaboration_id, "unknown")
                raise
            if repair_result == "confirmed_unfinalized":
                self._lineage_store.update_status(collaboration_id, "unknown")
                raise CommittedTurnFinalizationError(
                    self._committed_turn_error_message(
                        "Reply turn committed but local finalization failed during repair"
                    )
                ) from exc

            self._resume_handle_inline(
                collaboration_id=collaboration_id,
                repo_root=str(resolved_root),
                codex_thread_id=handle.codex_thread_id,
            )
            raise CommittedTurnFinalizationError(
                self._committed_turn_error_message(
                    "Reply turn committed after a dispatch failure and was finalized by inline repair"
                )
            ) from exc

        # Phase 2: dispatched — turn executed
        dispatched_entry = OperationJournalEntry(
            idempotency_key=idempotency_key,
            operation="turn_dispatch",
            phase="dispatched",
            collaboration_id=collaboration_id,
            created_at=created_at,
            repo_root=str(resolved_root),
            codex_thread_id=handle.codex_thread_id,
            turn_sequence=turn_sequence,
            runtime_id=runtime.runtime_id,
            context_size=packet.context_size,
        )
        self._journal.write_phase(
            dispatched_entry,
            session_id=self._session_id,
        )
        try:
            self._finalize_confirmed_turn(
                entry=dispatched_entry,
                turn_id=turn_result.turn_id,
                policy_fingerprint=runtime.policy_fingerprint,
                outcome_timestamp=self._journal.timestamp(),
            )
        except Exception as exc:
            self._lineage_store.update_status(collaboration_id, "unknown")
            raise CommittedTurnFinalizationError(
                self._committed_turn_error_message(
                    f"Reply turn committed but local finalization failed: {exc}"
                )
            ) from exc

        # Parse projection — all durable state is committed above.
        # If parsing fails, the turn is committed and readable via dialogue.read.
        try:
            position, evidence, uncertainties, follow_up_branches = (
                parse_consult_response(turn_result.agent_message)
            )
        except (ValueError, AttributeError) as exc:
            raise CommittedTurnParseError(
                self._committed_turn_error_message(
                    f"Reply turn committed but response parsing failed: {exc}"
                )
            ) from exc

        return DialogueReplyResult(
            collaboration_id=collaboration_id,
            runtime_id=runtime.runtime_id,
            position=position,
            evidence=evidence,
            uncertainties=uncertainties,
            follow_up_branches=follow_up_branches,
            turn_sequence=turn_sequence,
            context_size=packet.context_size,
        )

    def recover_startup(self) -> None:
        """One-shot startup recovery coordinator.

        Order:
        (1) reconcile unresolved journal entries
        (2) reattach remaining active AND eligible unknown handles

        Per contracts.md:141-151 (crash recovery contract).

        Unknown handles are eligible for reattach if:
        - they have no completed turns (vacuous metadata check), OR
        - all completed turns have corresponding TurnStore metadata

        Rollout boundary: pre-fix dialogues (turns dispatched before TurnStore)
        cannot continue after deployment. The journal is session-bounded, so
        fresh sessions have no pre-fix data. Mid-session code upgrades require
        ending the session and starting fresh. The read() integrity error is the
        enforcement signal if this boundary is violated.

        Session-ID stability is an external wiring contract: the caller must
        ensure this controller receives the same session_id used before the restart.
        This method does not validate session_id — an empty store is valid for
        a new session.
        """
        # Phase 1: reconcile unresolved journal entries
        recovered_cids = set(self.recover_pending_operations())

        # Phase 2: enumerate active and unknown handles for reattach.
        # Skip handles already resumed by phase 1 to avoid double-resume.
        # Quarantine any handle with incomplete TurnStore metadata.
        # Unknown handles are eligible for reattach if metadata is complete
        # (or if they have no completed turns to check).
        active_handles = self._lineage_store.list(status="active")
        unknown_handles = self._lineage_store.list(status="unknown")
        for handle in active_handles + unknown_handles:
            if handle.collaboration_id in recovered_cids:
                continue
            try:
                runtime = self._control_plane.get_advisory_runtime(
                    Path(handle.repo_root)
                )
                thread_data = runtime.session.read_thread(handle.codex_thread_id)

                # Metadata completeness check
                raw_turns = thread_data.get("thread", {}).get("turns", [])
                completed_count = sum(
                    1
                    for t in raw_turns
                    if isinstance(t, dict) and t.get("status") == "completed"
                )
                if completed_count > 0:
                    metadata = self._turn_store.get_all(handle.collaboration_id)
                    if len(metadata) < completed_count:
                        self._lineage_store.update_status(
                            handle.collaboration_id, "unknown"
                        )
                        continue

                resumed_thread_id = runtime.session.resume_thread(
                    handle.codex_thread_id
                )
                self._lineage_store.update_runtime(
                    handle.collaboration_id,
                    runtime_id=runtime.runtime_id,
                    codex_thread_id=resumed_thread_id,
                )
                if handle.status == "unknown":
                    self._lineage_store.update_status(handle.collaboration_id, "active")
            except Exception as exc:
                _log_recovery_failure(
                    "recover_startup",
                    exc,
                    handle.collaboration_id,
                )
                self._lineage_store.update_status(handle.collaboration_id, "unknown")

    def recover_pending_operations(self) -> list[str]:
        """Scan journal for incomplete operations and resolve them deterministically.

        Called on controller startup after crash. Returns collaboration_ids
        of handles that were fully reattached (resume_thread + update_runtime)
        by phase 1. Handles only reconciled (journal resolved, metadata repaired,
        or quarantined) are NOT included — they still need phase-2 reattach.

        Ownership: DialogueController reconciles dialogue journal entries.
        ControlPlane owns advisory runtime restart, thread/resume, and update_runtime.
        """
        unresolved = self._journal.list_unresolved(session_id=self._session_id)
        recovered: list[str] = []
        for entry in unresolved:
            if entry.operation == "thread_creation":
                cid = self._recover_thread_creation(entry)
                if cid:
                    recovered.append(cid)
            elif entry.operation == "turn_dispatch":
                self._recover_turn_dispatch(entry)
        return recovered

    def _recover_thread_creation(self, entry: OperationJournalEntry) -> str | None:
        """Recover a pending thread_creation entry.

        intent: dispatch never happened — resolve as no-op.
        dispatched: thread exists (codex_thread_id in entry) — persist handle if missing.
        """
        if entry.phase == "intent":
            # Dispatch never happened. Resolve as terminal no-op.
            self._journal.write_phase(
                OperationJournalEntry(
                    idempotency_key=entry.idempotency_key,
                    operation=entry.operation,
                    phase="completed",
                    collaboration_id=entry.collaboration_id,
                    created_at=entry.created_at,
                    repo_root=entry.repo_root,
                ),
                session_id=self._session_id,
            )
            return None

        # dispatched: thread was created, codex_thread_id is in the entry.
        # Reattach via thread/read + thread/resume per contracts.md §Crash Recovery (steps 3-4).
        if entry.codex_thread_id is None:
            raise RuntimeError(
                f"Recovery integrity failure: no codex_thread_id in thread_creation entry. "
                f"Got: idempotency_key={entry.idempotency_key!r:.100}"
            )

        existing = self._lineage_store.get(entry.collaboration_id)
        resolved_root = Path(entry.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        # Reattach: read latest state, then resume to bind to live runtime
        runtime.session.read_thread(entry.codex_thread_id)
        resumed_thread_id = runtime.session.resume_thread(entry.codex_thread_id)

        if existing is None:
            # Crash between thread/start and lineage persist — persist now
            handle = CollaborationHandle(
                collaboration_id=entry.collaboration_id,
                capability_class="advisory",
                runtime_id=runtime.runtime_id,
                codex_thread_id=resumed_thread_id,
                claude_session_id=self._session_id,
                repo_root=entry.repo_root,
                created_at=entry.created_at,
                status="active",
            )
            self._lineage_store.create(handle)
        else:
            # Handle exists but may point at stale runtime/thread identity
            self._lineage_store.update_runtime(
                entry.collaboration_id,
                runtime_id=runtime.runtime_id,
                codex_thread_id=resumed_thread_id,
            )

        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=entry.idempotency_key,
                operation=entry.operation,
                phase="completed",
                collaboration_id=entry.collaboration_id,
                created_at=entry.created_at,
                repo_root=entry.repo_root,
            ),
            session_id=self._session_id,
        )
        return entry.collaboration_id

    def _recover_turn_dispatch(self, entry: OperationJournalEntry) -> None:
        """Recover a pending turn_dispatch entry.

        Both intent and dispatched phases verify via thread/read:
        - Confirmed (completed turn at turn_sequence): finalize local state, then
          resolve the journal entry as completed.
        - Unconfirmed: mark handle 'unknown' and leave the terminal phase
          unchanged for later recovery.

        Does NOT silently treat intent as no-op. Absence of evidence is not
        evidence of absence: a crash between run_turn() call and journal write
        leaves an intent record even though dispatch occurred.
        """
        handle = self._lineage_store.get(entry.collaboration_id)
        if handle is None:
            raise RuntimeError(
                f"Recovery integrity failure: no handle for turn_dispatch entry. "
                f"Got: collaboration_id={entry.collaboration_id!r:.100}"
            )
        if entry.codex_thread_id is None:
            raise RuntimeError(
                f"Recovery integrity failure: no codex_thread_id in turn_dispatch entry. "
                f"Got: idempotency_key={entry.idempotency_key!r:.100}"
            )

        try:
            runtime = self._control_plane.get_advisory_runtime(Path(entry.repo_root))
            thread_data = runtime.session.read_thread(entry.codex_thread_id)
            raw_turns = thread_data.get("thread", {}).get("turns", [])
            completed_turns = [
                t
                for t in raw_turns
                if isinstance(t, dict) and t.get("status") == "completed"
            ]
            completed_count = len(completed_turns)
            turn_confirmed = (
                entry.turn_sequence is not None
                and completed_count >= entry.turn_sequence
            )
        except Exception as exc:
            _log_recovery_failure(
                "recover_turn_dispatch",
                exc,
                entry.idempotency_key,
            )
            completed_turns = []
            turn_confirmed = False

        if not turn_confirmed:
            # Outcome uncertain — mark handle 'unknown' per contracts.md §Handle Lifecycle
            self._lineage_store.update_status(entry.collaboration_id, "unknown")
            return

        turn_id, outcome_timestamp = self._confirmed_turn_details(
            completed_turns,
            turn_sequence=entry.turn_sequence,
            fallback_timestamp=entry.created_at,
        )
        try:
            self._finalize_confirmed_turn(
                entry=entry,
                turn_id=turn_id,
                policy_fingerprint=runtime.policy_fingerprint,
                outcome_timestamp=outcome_timestamp,
            )
        except Exception as exc:
            _log_recovery_failure(
                "recover_turn_dispatch",
                exc,
                entry.idempotency_key,
            )
            self._lineage_store.update_status(entry.collaboration_id, "unknown")

    def _next_turn_sequence(
        self,
        handle: CollaborationHandle,
        runtime: object,
    ) -> int:
        """Derive next 1-based turn_sequence from completed turn count.

        dialogue.start does not consume a slot (contracts.md:266).

        First-turn fast path: if TurnStore has no local metadata for this
        collaboration, no turns have ever completed — return 1 without calling
        read_thread(). This avoids racing thread materialization on the App
        Server (thread/start returns before thread/read is ready).

        Subsequent turns: fall back to read_thread() and count completed turns,
        preserving remote-authoritative validation.
        """
        local_turns = self._turn_store.get_all(handle.collaboration_id)
        if not local_turns:
            return 1

        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        raw_turns = thread_data.get("thread", {}).get("turns", [])
        completed_count = sum(
            1
            for t in raw_turns
            if isinstance(t, dict) and t.get("status") == "completed"
        )
        return completed_count + 1

    def _best_effort_repair_turn(
        self, intent_entry: OperationJournalEntry
    ) -> RepairTurnResult:
        """Best-effort inspect and repair a turn after run_turn() failure.

        Called only from reply() exception path.
        Returns a repair result describing whether the turn could be confirmed
        and whether local finalization succeeded. Never raises.
        """
        try:
            runtime = self._control_plane.get_advisory_runtime(
                Path(intent_entry.repo_root)
            )
            thread_data = runtime.session.read_thread(intent_entry.codex_thread_id)
            raw_turns = thread_data.get("thread", {}).get("turns", [])
            completed_turns = [
                t
                for t in raw_turns
                if isinstance(t, dict) and t.get("status") == "completed"
            ]
            completed_count = len(completed_turns)
            turn_confirmed = (
                intent_entry.turn_sequence is not None
                and completed_count >= intent_entry.turn_sequence
            )
        except Exception as exc:
            _log_recovery_failure(
                "best_effort_repair_turn",
                exc,
                intent_entry.idempotency_key,
            )
            return "unconfirmed"

        if not turn_confirmed:
            return "unconfirmed"

        turn_id, outcome_timestamp = self._confirmed_turn_details(
            completed_turns,
            turn_sequence=intent_entry.turn_sequence,
            fallback_timestamp=intent_entry.created_at,
        )
        try:
            self._finalize_confirmed_turn(
                entry=intent_entry,
                turn_id=turn_id,
                policy_fingerprint=runtime.policy_fingerprint,
                outcome_timestamp=outcome_timestamp,
            )
        except Exception as exc:
            _log_recovery_failure(
                "best_effort_repair_turn",
                exc,
                intent_entry.idempotency_key,
            )
            return "confirmed_unfinalized"
        return "confirmed_finalized"

    def read(self, collaboration_id: str) -> DialogueReadResult:
        """Read dialogue state for a given collaboration_id.

        Uses thread/read as the base set of completed turns (per delivery.md:201,218).
        Enriches per-turn context_size from the metadata store via left-join.
        A completed turn with no metadata store entry is an integrity failure.
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Read failed: handle not found. "
                f"Got: collaboration_id={collaboration_id!r:.100}"
            )

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        thread = thread_data.get("thread", {})
        raw_turns = thread.get("turns", [])

        # Load all metadata for this collaboration
        metadata = self._turn_store.get_all(collaboration_id)

        turns: list[DialogueTurnSummary] = []
        seq = 0
        for raw_turn in raw_turns:
            if not isinstance(raw_turn, dict):
                continue
            if raw_turn.get("status") != "completed":
                continue
            seq += 1
            agent_message = self._read_turn_agent_message(raw_turn)
            position = ""
            if isinstance(agent_message, str) and agent_message:
                try:
                    parsed = json.loads(agent_message)
                    position = parsed.get("position", "")
                except (ValueError, AttributeError):
                    position = agent_message[:200]

            # Left-join: metadata store MUST have an entry for every completed turn.
            context_size = metadata.get(seq)
            if context_size is None:
                raise RuntimeError(
                    f"Turn metadata integrity failure: no context_size for "
                    f"collaboration_id={collaboration_id!r:.100}, turn_sequence={seq}. "
                    f"This indicates a write-ordering violation or missing recovery "
                    f"repair. If this dialogue predates the current server version, "
                    f"end the session and start fresh."
                )

            turns.append(
                DialogueTurnSummary(
                    turn_sequence=seq,
                    position=position,
                    context_size=context_size,
                    timestamp=self._read_turn_timestamp(raw_turn),
                )
            )

        return DialogueReadResult(
            collaboration_id=collaboration_id,
            status=handle.status,
            turn_count=len(turns),
            created_at=handle.created_at,
            turns=tuple(turns),
        )

    @staticmethod
    def _read_turn_agent_message(raw_turn: dict[str, object]) -> str:
        """Extract agent message text from legacy or live thread/read turn shapes."""
        agent_message = raw_turn.get("agentMessage")
        if isinstance(agent_message, str):
            return agent_message

        items = raw_turn.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "agentMessage":
                    continue
                text = item.get("text")
                if isinstance(text, str):
                    return text
        return ""

    @staticmethod
    def _read_turn_timestamp(raw_turn: dict[str, object]) -> str:
        """Extract turn timestamp when the runtime exposes one."""
        created_at = raw_turn.get("createdAt")
        if isinstance(created_at, str):
            return created_at

        items = raw_turn.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                nested_created_at = item.get("createdAt")
                if isinstance(nested_created_at, str):
                    return nested_created_at
        return ""
