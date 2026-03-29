"""Dialogue controller for codex.dialogue.start, .reply, .read.

Orchestrates dialogue operations by composing ControlPlane (runtime bootstrap),
LineageStore (handle persistence), and OperationJournal (crash-recovery entries).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Callable

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
    RepoIdentity,
)
from .journal import OperationJournal
from .prompt_builder import CONSULT_OUTPUT_SCHEMA, build_consult_turn_text, parse_consult_response
from .turn_store import TurnStore


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

    def start(self, repo_root: Path) -> DialogueStartResult:
        """Create a durable dialogue thread and persist handle.

        Spec: contracts.md §Dialogue Start, delivery.md §R2 in-scope.
        No audit event — thread creation is not a trust boundary crossing
        (contracts.md §Audit Event Actions does not define dialogue_start).
        """
        resolved_root = repo_root.resolve()
        runtime = self._control_plane.get_advisory_runtime(resolved_root)

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

        Write ordering invariant: metadata store write MUST happen before
        journal completed. See plan doc §Key invariants.
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

        resolved_root = Path(handle.repo_root)
        runtime = self._control_plane.get_advisory_runtime(resolved_root)
        repo_identity = self._repo_identity_loader(resolved_root)

        # Derive turn_sequence from completed turns via thread/read (contracts.md:266).
        # Safe under MCP serialization invariant — no concurrent turns to race with.
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
        idempotency_key = f"{runtime.runtime_id}:{handle.codex_thread_id}:{turn_sequence}"
        created_at = self._journal.timestamp()
        self._journal.write_phase(
            OperationJournalEntry(
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
            ),
            session_id=self._session_id,
        )

        try:
            turn_result = runtime.session.run_turn(
                thread_id=handle.codex_thread_id,
                prompt_text=build_consult_turn_text(packet.payload),
                output_schema=CONSULT_OUTPUT_SCHEMA,
            )
        except Exception:
            self._control_plane.invalidate_runtime(resolved_root)
            raise

        # Phase 2: dispatched — turn executed
        self._journal.write_phase(
            OperationJournalEntry(
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
            ),
            session_id=self._session_id,
        )

        position, evidence, uncertainties, follow_up_branches = parse_consult_response(
            turn_result.agent_message
        )

        # Metadata store: MUST write before journal completed
        self._turn_store.write(
            collaboration_id,
            turn_sequence=turn_sequence,
            context_size=packet.context_size,
        )

        # Phase 3: completed
        self._journal.write_phase(
            OperationJournalEntry(
                idempotency_key=idempotency_key,
                operation="turn_dispatch",
                phase="completed",
                collaboration_id=collaboration_id,
                created_at=created_at,
                repo_root=str(resolved_root),
            ),
            session_id=self._session_id,
        )

        # Audit event (dialogue_turn per contracts.md §Audit Event Actions)
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="dialogue_turn",
                collaboration_id=collaboration_id,
                runtime_id=runtime.runtime_id,
                context_size=packet.context_size,
                turn_id=turn_result.turn_id,
            )
        )

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

    def recover_pending_operations(self) -> list[str]:
        """Scan journal for incomplete operations and resolve them deterministically.

        Called on controller startup after crash. Returns collaboration_ids
        of handles that were recovered or affected.

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
        existing = self._lineage_store.get(entry.collaboration_id)
        if entry.codex_thread_id is not None:
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
        - Confirmed (completed turn at turn_sequence): resolve journal, repair metadata store.
        - Unconfirmed: mark handle 'unknown' (ambiguous — dispatch may or may not have happened).

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
            completed_count = sum(
                1 for t in raw_turns
                if isinstance(t, dict) and t.get("status") == "completed"
            )
            turn_confirmed = (
                entry.turn_sequence is not None
                and completed_count >= entry.turn_sequence
            )
        except Exception:
            turn_confirmed = False

        if turn_confirmed:
            # Repair metadata store if entry has context_size
            if entry.context_size is not None and entry.turn_sequence is not None:
                self._turn_store.write(
                    entry.collaboration_id,
                    turn_sequence=entry.turn_sequence,
                    context_size=entry.context_size,
                )
        else:
            # Outcome uncertain — mark handle 'unknown' per contracts.md §Handle Lifecycle
            self._lineage_store.update_status(entry.collaboration_id, "unknown")

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

    def _next_turn_sequence(
        self,
        handle: CollaborationHandle,
        runtime: object,
    ) -> int:
        """Derive next 1-based turn_sequence from completed turn count via thread/read.

        dialogue.start does not consume a slot (contracts.md:266).
        Counts only turns with status 'completed' to avoid overcounting interrupted turns.
        """
        thread_data = runtime.session.read_thread(handle.codex_thread_id)
        raw_turns = thread_data.get("thread", {}).get("turns", [])
        completed_count = sum(
            1 for t in raw_turns
            if isinstance(t, dict) and t.get("status") == "completed"
        )
        return completed_count + 1

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
            agent_message = raw_turn.get("agentMessage", "")
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
                    timestamp=str(raw_turn.get("createdAt", "")),
                )
            )

        return DialogueReadResult(
            collaboration_id=collaboration_id,
            status=handle.status,
            turn_count=len(turns),
            created_at=handle.created_at,
            turns=tuple(turns),
        )
