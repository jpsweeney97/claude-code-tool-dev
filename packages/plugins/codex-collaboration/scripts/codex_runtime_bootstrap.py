#!/usr/bin/env python3
"""Bootstrap entry point for the codex-collaboration MCP server.

Wires the object graph and starts the stdio JSON-RPC loop. Dialogue
and delegation initialization are deferred until the first tool call
on each surface, at which point the published session identity is read
and pinned.

Launch pattern (from .mcp.json):
  uv run --directory ${CLAUDE_PLUGIN_ROOT} python \
      ${CLAUDE_PLUGIN_ROOT}/scripts/codex_runtime_bootstrap.py

See delivery.md §Plugin Component Structure for the normative location.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

# Ensure the package root is importable when launched via `python scripts/...`
_package_root = Path(__file__).resolve().parent.parent
if str(_package_root) not in sys.path:
    sys.path.insert(0, str(_package_root))

from server.control_plane import ControlPlane  # noqa: E402
from server.delegation_controller import DelegationController  # noqa: E402
from server.delegation_job_store import DelegationJobStore  # noqa: E402
from server.dialogue import DialogueController  # noqa: E402
from server.execution_runtime_registry import ExecutionRuntimeRegistry  # noqa: E402
from server.journal import OperationJournal, default_plugin_data_path  # noqa: E402
from server.lineage_store import LineageStore  # noqa: E402
from server.mcp_server import McpServer  # noqa: E402
from server.pending_request_store import PendingRequestStore  # noqa: E402
from server.turn_store import TurnStore  # noqa: E402
from server.worktree_manager import WorktreeManager  # noqa: E402


def _read_session_id(plugin_data_path: Path) -> str:
    """Read the published session identity from the SessionStart hook.

    Returns the session_id string. Raises RuntimeError if the identity
    file is missing — this means the SessionStart hook has not yet fired
    or CLAUDE_PLUGIN_DATA is misconfigured.
    """
    identity_path = plugin_data_path / "session_id"
    if not identity_path.exists():
        raise RuntimeError(
            "Dialogue init failed: session identity not yet available. "
            "The SessionStart hook may not have fired, or "
            f"CLAUDE_PLUGIN_DATA is misconfigured. Got: {identity_path}"
        )
    session_id = identity_path.read_text(encoding="utf-8").strip()
    if not session_id:
        raise RuntimeError(
            "Dialogue init failed: session identity file is empty. "
            f"Got: {identity_path}"
        )
    return session_id


def _build_dialogue_factory(
    *,
    plugin_data_path: Path,
    control_plane: ControlPlane,
    journal: OperationJournal,
) -> Callable[[], DialogueController]:
    """Return a zero-arg factory that builds a DialogueController on first call.

    The factory reads the published session_id, constructs session-scoped
    stores, and returns a fully initialized DialogueController. The
    McpServer calls this at most once and pins the result.
    """

    def factory() -> DialogueController:
        session_id = _read_session_id(plugin_data_path)
        lineage_store = LineageStore(plugin_data_path, session_id)
        turn_store = TurnStore(plugin_data_path, session_id)
        return DialogueController(
            control_plane=control_plane,
            lineage_store=lineage_store,
            journal=journal,
            session_id=session_id,
            turn_store=turn_store,
        )

    return factory


def _build_delegation_factory(
    *,
    plugin_data_path: Path,
    control_plane: ControlPlane,
    runtime_registry: ExecutionRuntimeRegistry,
    journal: OperationJournal,
) -> Callable[[], DelegationController]:
    """Return a zero-arg factory that builds a DelegationController on first call.

    Reads the published session_id, constructs session-scoped job_store +
    lineage_store, and returns a fully initialized controller wired to the
    shared runtime registry and journal. The McpServer calls this at most
    once and pins the result.

    Why lineage_store is built inside the factory closure: LineageStore is
    session-scoped (it takes session_id at construction). session_id is
    only available after ``_read_session_id`` succeeds, which happens
    inside the factory. The dialogue factory follows the same pattern.
    Both factories write to the same underlying lineage JSONL file for
    a given session_id, so the identity layer is shared naturally.
    """

    def factory() -> DelegationController:
        session_id = _read_session_id(plugin_data_path)
        job_store = DelegationJobStore(plugin_data_path, session_id)
        lineage_store = LineageStore(plugin_data_path, session_id)
        pending_request_store = PendingRequestStore(plugin_data_path, session_id)
        return DelegationController(
            control_plane=control_plane,
            worktree_manager=WorktreeManager(),
            job_store=job_store,
            lineage_store=lineage_store,
            runtime_registry=runtime_registry,
            journal=journal,
            session_id=session_id,
            plugin_data_path=plugin_data_path,
            pending_request_store=pending_request_store,
        )

    return factory


def main() -> None:
    plugin_data_path = default_plugin_data_path()
    journal = OperationJournal(plugin_data_path)

    control_plane = ControlPlane(
        plugin_data_path=plugin_data_path,
        journal=journal,
    )

    runtime_registry = ExecutionRuntimeRegistry()

    server = McpServer(
        control_plane=control_plane,
        dialogue_factory=_build_dialogue_factory(
            plugin_data_path=plugin_data_path,
            control_plane=control_plane,
            journal=journal,
        ),
        delegation_factory=_build_delegation_factory(
            plugin_data_path=plugin_data_path,
            control_plane=control_plane,
            runtime_registry=runtime_registry,
            journal=journal,
        ),
    )
    server.run()


if __name__ == "__main__":
    main()
