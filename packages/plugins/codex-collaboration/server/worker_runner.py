"""Worker thread runner for Packet 1's deferred-approval model.

Packet 1 (T-20260423-02). One worker thread per deferred-approval turn.
The worker:
  - Invokes _execute_live_turn (which, post-Task 16, contains the
    rewritten handler that parks on the registry).
  - Emits announce_turn_completed_empty as a fallthrough if the handler
    did not already signal during the turn. The handler itself emits
    announce_parked / announce_turn_terminal_without_escalation during
    the turn; the worker runner emits announce_worker_failed only on
    unhandled exceptions.

The worker owns IO-1 (exclusive session ownership) + IO-3 (single-writer
to pending_request_store + its own DelegationJob row).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from .resolution_registry import ResolutionRegistry

if TYPE_CHECKING:
    from .delegation_controller import DelegationController

logger = logging.getLogger(__name__)


class _WorkerRunner:
    """Entry point for the worker thread. Instantiated by DelegationController.start,
    spawned once the committed-start phase completes. The thread's target is
    `self.run`.
    """

    def __init__(
        self,
        *,
        controller: "DelegationController",
        registry: ResolutionRegistry,
        job_id: str,
        collaboration_id: str,
        runtime_id: str,
        worktree_path: Path,
        prompt_text: str,
    ) -> None:
        self._controller = controller
        self._registry = registry
        self._job_id = job_id
        self._collaboration_id = collaboration_id
        self._runtime_id = runtime_id
        self._worktree_path = worktree_path
        self._prompt_text = prompt_text

    def run(self) -> None:
        """Thread target. Runs _execute_live_turn and converts its outcome
        into the appropriate capture-ready signal. Never raises on the
        thread — unhandled exceptions fire announce_worker_failed.
        """
        try:
            self._controller._execute_live_turn(
                job_id=self._job_id,
                collaboration_id=self._collaboration_id,
                runtime_id=self._runtime_id,
                worktree_path=self._worktree_path,
                prompt_text=self._prompt_text,
            )
        except Exception as exc:
            logger.exception(
                "Worker runner: unhandled exception in _execute_live_turn"
            )
            self._registry.announce_worker_failed(self._job_id, error=exc)
            return

        # Normal return — translate result into a capture-ready signal IF
        # the handler did not already signal (capture-ready channel is
        # idempotent / resolved-once, so late signals are warning no-ops).
        # Per spec §Capture-ready handshake, the handler emits:
        #   - announce_parked before registry.wait() if it parked
        #   - announce_turn_terminal_without_escalation before return for
        #     kind="unknown"
        # If neither fired, the turn completed without capture.
        #
        # At this layer we only handle the "turn completed without capture"
        # fallthrough — the handler itself is responsible for the three
        # signal cases that happen during the turn.
        self._registry.announce_turn_completed_empty(self._job_id)


def spawn_worker(
    *,
    controller: "DelegationController",
    registry: ResolutionRegistry,
    job_id: str,
    collaboration_id: str,
    runtime_id: str,
    worktree_path: Path,
    prompt_text: str,
) -> threading.Thread:
    """Helper: construct a _WorkerRunner and start a daemon thread."""
    runner = _WorkerRunner(
        controller=controller,
        registry=registry,
        job_id=job_id,
        collaboration_id=collaboration_id,
        runtime_id=runtime_id,
        worktree_path=worktree_path,
        prompt_text=prompt_text,
    )
    thread = threading.Thread(
        target=runner.run, name=f"delegation-worker-{job_id}", daemon=True
    )
    thread.start()
    return thread
