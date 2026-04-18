"""In-process live-ownership registry for execution runtimes.

Solves the orphan-runtime problem WITHIN a live control-plane process.
Does NOT provide crash durability — if the control plane dies, the registry
is lost. Crash recovery is handled by replaying:

    LineageStore        -> CollaborationHandle records (identity/routing)
    DelegationJobStore  -> DelegationJob records (job lifecycle)
    OperationJournal    -> job_creation phase records (replay safety)

Keep this file small on purpose. It is not a control plane; it is a table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionRuntimeEntry:
    """Live-ownership record for one execution runtime."""

    runtime_id: str
    session: Any  # AppServerRuntimeSession — Any to avoid import cycle
    thread_id: str
    job_id: str


class ExecutionRuntimeRegistry:
    """In-process registry mapping runtime_id -> live session/thread/job."""

    def __init__(self) -> None:
        self._entries: dict[str, ExecutionRuntimeEntry] = {}

    def register(
        self,
        *,
        runtime_id: str,
        session: Any,
        thread_id: str,
        job_id: str,
    ) -> None:
        """Register a live runtime. Rejects duplicate runtime_id.

        The controller calls this as the FIRST committed-start write,
        IMMEDIATELY after ``journal.write_phase(dispatched)`` and BEFORE
        any other durable local write (lineage, job, audit, journal-completed).
        Rationale: the runtime subprocess is already live by this point, and
        the in-process registry is what makes it reachable for later turn
        dispatch, close, and crash-to-``unknown`` paths. If any subsequent
        local write fails without the runtime having been registered first,
        the subprocess is unreachable and the busy gate's registry branch
        cannot block a same-session retry — recreating the orphan-runtime
        bug. See ``DelegationController.start`` docstring and the
        ``Write ordering invariant`` block for the full rationale.

        A duplicate here indicates a programming error (two callers thinking
        they own the same ``runtime_id``). Runtime ids are uuid-generated so
        collision is structurally impossible in practice; the error surface
        is retained for test monkeypatching and defensive correctness.
        """

        if runtime_id in self._entries:
            raise RuntimeError(
                "ExecutionRuntimeRegistry.register failed: runtime_id already "
                f"registered. Got: {runtime_id!r:.100}"
            )
        self._entries[runtime_id] = ExecutionRuntimeEntry(
            runtime_id=runtime_id,
            session=session,
            thread_id=thread_id,
            job_id=job_id,
        )

    def lookup(self, runtime_id: str) -> ExecutionRuntimeEntry | None:
        """Return the entry for a live runtime, or None if not registered."""

        return self._entries.get(runtime_id)

    def release(self, runtime_id: str) -> ExecutionRuntimeEntry | None:
        """Remove and return the entry for a runtime, or None if not registered.

        The caller is responsible for any session teardown. This method is
        intentionally tear-down-agnostic so the v1 slice does not depend on
        a stable ``session.close()`` contract. Follow-up slices add teardown
        wiring alongside poll/promote.
        """

        return self._entries.pop(runtime_id, None)

    def active_runtime_ids(self) -> tuple[str, ...]:
        """Snapshot of currently-registered runtime ids."""

        return tuple(self._entries.keys())
