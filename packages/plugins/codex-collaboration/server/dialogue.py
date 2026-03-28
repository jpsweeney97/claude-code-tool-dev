"""Dialogue controller for codex.dialogue.start, .reply, .read.

Orchestrates dialogue operations by composing ControlPlane (runtime bootstrap),
LineageStore (handle persistence), and OperationJournal (crash-recovery entries).
"""

from __future__ import annotations

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
    DialogueReplyResult,
    DialogueStartResult,
    OperationJournalEntry,
    RepoIdentity,
)
from .journal import OperationJournal
from .prompt_builder import CONSULT_OUTPUT_SCHEMA, build_consult_turn_text, parse_consult_response


class DialogueController:
    """Implements codex.dialogue.start, .reply, .read, and crash recovery."""

    def __init__(
        self,
        *,
        control_plane: ControlPlane,
        lineage_store: LineageStore,
        journal: OperationJournal,
        session_id: str,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._lineage_store = lineage_store
        self._journal = journal
        self._session_id = session_id
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
        """
        handle = self._lineage_store.get(collaboration_id)
        if handle is None:
            raise ValueError(
                f"Handle not found for reply: no handle with collaboration_id. "
                f"Got: {collaboration_id!r:.100}"
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
            ),
            session_id=self._session_id,
        )

        position, evidence, uncertainties, follow_up_branches = parse_consult_response(
            turn_result.agent_message
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
