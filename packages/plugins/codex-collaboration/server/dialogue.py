"""Dialogue controller for codex.dialogue.start, .reply, .read.

Orchestrates dialogue operations by composing ControlPlane (runtime bootstrap),
LineageStore (handle persistence), and OperationJournal (crash-recovery entries).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Callable

from .control_plane import ControlPlane, load_repo_identity
from .lineage_store import LineageStore
from .models import (
    CollaborationHandle,
    DialogueStartResult,
    OperationJournalEntry,
    RepoIdentity,
)
from .journal import OperationJournal


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
