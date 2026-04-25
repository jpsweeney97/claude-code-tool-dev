"""Production wiring and end-to-end tests for codex.delegate.start."""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest

from server.artifact_store import ArtifactStore
from server.control_plane import ControlPlane
from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.mcp_server import McpServer
from server.models import (
    AccountState,
    OperationJournalEntry,
    RuntimeHandshake,
    TurnExecutionResult,
)
from server.pending_request_store import PendingRequestStore
from server.worktree_manager import WorktreeManager


def test_delegation_factory_builds_controller(tmp_path: Path, monkeypatch) -> None:
    # Ensure scripts dir is importable
    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    # Publish a fake session id.
    (plugin_data / "session_id").write_text("sess-smoke-1")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    from server.delegation_controller import DelegationController

    assert isinstance(controller, DelegationController)


def test_delegation_factory_passes_shared_runtime_registry(
    tmp_path: Path, monkeypatch
) -> None:
    """A single registry is shared across controller instances from one factory.

    The registry is constructed in main() and passed into the factory.
    The factory is called at most once per McpServer instance (lazy pin),
    so sharing the registry across callers within one McpServer is the
    correct default — it is the live view of THIS plugin instance.
    """

    scripts_dir = Path(__file__).parent.parent / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    from codex_runtime_bootstrap import _build_delegation_factory  # type: ignore
    from server.control_plane import ControlPlane
    from server.execution_runtime_registry import ExecutionRuntimeRegistry
    from server.journal import OperationJournal

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    (plugin_data / "session_id").write_text("sess-smoke-2")

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(plugin_data_path=plugin_data, journal=journal)
    runtime_registry = ExecutionRuntimeRegistry()

    factory = _build_delegation_factory(
        plugin_data_path=plugin_data,
        control_plane=control_plane,
        runtime_registry=runtime_registry,
        journal=journal,
    )
    controller = factory()

    # The registry the controller received must be the same object main()
    # constructed — otherwise main()'s reference cannot observe registered
    # runtimes later.
    assert controller._runtime_registry is runtime_registry  # type: ignore[attr-defined]


def _init_repo(repo_path: Path) -> str:
    """Init a tmp git repo with one commit. Returns the HEAD SHA."""
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    (repo_path / "README.md").write_text("hello\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return head


class _StubSession:
    def initialize(self) -> RuntimeHandshake:
        return RuntimeHandshake(
            codex_home="/fake",
            platform_family="unix",
            platform_os="darwin",
            user_agent="codex/stub",
        )

    def read_account(self) -> AccountState:
        return AccountState(
            auth_status="authenticated",
            account_type="stub",
            requires_openai_auth=False,
        )

    def start_thread(self) -> str:
        return "thr-exec-stub"

    def run_execution_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        sandbox_policy: dict[str, Any],
        approval_policy: str = "on-request",
        output_schema: dict[str, Any] | None = None,
        effort: str | None = None,
        server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None]
        | None = None,
    ) -> TurnExecutionResult:
        return TurnExecutionResult(
            turn_id="turn-stub",
            status="completed",
            agent_message="Stub done.",
            notifications=(),
        )

    def interrupt_turn(self, *, thread_id: str, turn_id: str | None) -> None:
        pass

    def close(self) -> None:
        pass


class _ConfigurableStubSession(_StubSession):
    """_StubSession extended with configurable server requests and turn result.

    Mirrors _FakeSession from test_delegation_controller.py but layered on
    top of _StubSession so all lifecycle methods are inherited.
    """

    def __init__(
        self,
        *,
        server_requests: list[dict[str, Any]] | None = None,
        turn_result: TurnExecutionResult | None = None,
    ) -> None:
        self._server_requests: list[dict[str, Any]] = server_requests or []
        self._interrupted = False
        self._turn_result = turn_result or TurnExecutionResult(
            turn_id="turn-stub",
            status="completed",
            agent_message="Stub done.",
            notifications=(),
        )

    def run_execution_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        sandbox_policy: dict[str, Any],
        approval_policy: str = "on-request",
        output_schema: dict[str, Any] | None = None,
        effort: str | None = None,
        server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None]
        | None = None,
    ) -> TurnExecutionResult:
        for req in self._server_requests:
            if server_request_handler is not None:
                server_request_handler(req)
        if self._interrupted:
            return TurnExecutionResult(
                turn_id=self._turn_result.turn_id,
                status="interrupted",
                agent_message=self._turn_result.agent_message,
                notifications=self._turn_result.notifications,
            )
        return self._turn_result

    def interrupt_turn(self, *, thread_id: str, turn_id: str | None) -> None:
        self._interrupted = True


def _make_compat_result() -> object:
    from server.codex_compat import REQUIRED_METHODS

    class _R:
        passed = True
        codex_version = "0.117.0"
        available_methods = REQUIRED_METHODS
        errors: tuple[str, ...] = ()

    return _R()


def _build_e2e_setup(
    tmp_path: Path,
    *,
    session_factory: Callable[[], _StubSession] | None = None,
) -> tuple[McpServer, DelegationJobStore, PendingRequestStore, OperationJournal, Path]:
    """Build a full integration stack: ControlPlane + DelegationController + McpServer.

    Returns (server, job_store, pending_request_store, journal, plugin_data).
    The caller is responsible for initialising the git repo via _init_repo.
    """
    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()
    (plugin_data / "session_id").write_text("sess-e2e-esc")

    journal = OperationJournal(plugin_data)

    stub_factory = session_factory or (lambda _: _StubSession())
    control_plane = ControlPlane(
        plugin_data_path=plugin_data,
        journal=journal,
        runtime_factory=lambda _: stub_factory(),  # type: ignore[arg-type]
        compat_checker=_make_compat_result,
    )

    job_store = DelegationJobStore(plugin_data, "sess-e2e-esc")
    lineage_store = LineageStore(plugin_data, "sess-e2e-esc")
    pending_request_store = PendingRequestStore(plugin_data, "sess-e2e-esc")
    runtime_registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id="sess-e2e-esc",
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
    )

    server = McpServer(
        control_plane=control_plane,
        delegation_factory=lambda: controller,
    )
    return server, job_store, pending_request_store, journal, plugin_data


def test_delegate_start_end_to_end_through_mcp_dispatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    head = _init_repo(repo_root)

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(
        plugin_data_path=plugin_data,
        journal=journal,
        runtime_factory=lambda _: _StubSession(),  # type: ignore[arg-type]
        compat_checker=_make_compat_result,
    )
    job_store = DelegationJobStore(plugin_data, "sess-e2e")
    lineage_store = LineageStore(plugin_data, "sess-e2e")
    pending_request_store = PendingRequestStore(plugin_data, "sess-e2e")
    runtime_registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id="sess-e2e",
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
    )

    # SEED (load-bearing proof of AC 4 consumer wiring): simulate a prior
    # session that crashed between journal.write_phase(dispatched) and any
    # durable local write. The seeded entry is at ``dispatched`` phase for
    # a DISTINCT idempotency key from the upcoming real dispatch so the two
    # do not interfere. No handle / job persisted — this is the
    # register-failure-or-crash-before-first-durable-write shape from AC 4.
    #
    # This seed is the exact state the lazy-factory recovery wiring must
    # reconcile. If the test bypassed the factory path (direct-controller
    # injection), ``_ensure_delegation_controller()`` would never run,
    # ``recover_startup()`` would never be called, the seed would stay
    # unresolved, and the post-dispatch assertion on ``post_unresolved_seeds``
    # below would fail — proving the factory-path wiring is genuinely
    # load-bearing, not merely declared.
    seeded_key = "sess-e2e:seeded-leftover-hash"
    seeded_created_at = journal.timestamp()
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=seeded_key,
            operation="job_creation",
            phase="intent",
            collaboration_id="collab-seeded",
            created_at=seeded_created_at,
            repo_root=str(repo_root.resolve()),
            job_id="job-seeded",
        ),
        session_id="sess-e2e",
    )
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key=seeded_key,
            operation="job_creation",
            phase="dispatched",
            collaboration_id="collab-seeded",
            created_at=seeded_created_at,
            repo_root=str(repo_root.resolve()),
            job_id="job-seeded",
            runtime_id="rt-seeded",
            codex_thread_id="thr-seeded",
        ),
        session_id="sess-e2e",
    )
    # Sanity-check the seed IS unresolved before dispatch — invariant for
    # the proof shape. If this fails, the seed setup is wrong and the
    # downstream reconciliation assertion is meaningless.
    pre_unresolved_seeds = [
        e
        for e in journal.list_unresolved(session_id="sess-e2e")
        if e.operation == "job_creation" and e.idempotency_key == seeded_key
    ]
    assert len(pre_unresolved_seeds) == 1
    assert pre_unresolved_seeds[0].phase == "dispatched"

    class _MinimalCP:
        def codex_status(self, repo_root: Path) -> dict:
            return {}

        def codex_consult(self, request: object) -> object:
            raise NotImplementedError

    # Wire through the lazy-factory path (NOT direct controller injection) so
    # the first dispatch exercises _ensure_delegation_controller() →
    # controller.recover_startup() → pin. This is the production entry seam;
    # direct injection would skip recover_startup() on the lazy path and
    # leave the seeded entry unresolved.
    server = McpServer(
        control_plane=_MinimalCP(),
        delegation_factory=lambda: controller,
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "E2E test"},
            },
        }
    )

    assert "isError" not in response["result"]
    content = response["result"]["content"][0]["text"]
    payload = json.loads(content)
    # After turn dispatch (no server requests), job completes fully.
    assert payload["status"] == "completed"
    assert payload["promotion_state"] == "pending"
    assert payload["base_commit"] == head
    worktree_path = Path(payload["worktree_path"])
    # Worktree was created and exists as a directory.
    assert worktree_path.is_dir()
    assert (worktree_path / "README.md").exists()
    # Job is persisted in the job store.
    persisted_job = job_store.get(payload["job_id"])
    assert persisted_job is not None
    assert persisted_job.status == "completed"
    # Execution CollaborationHandle is persisted in the lineage store.
    persisted_handle = lineage_store.get(payload["collaboration_id"])
    assert persisted_handle is not None
    assert persisted_handle.capability_class == "execution"
    assert persisted_handle.runtime_id == payload["runtime_id"]
    # Runtime released and session closed after clean completion.
    registry_entry = runtime_registry.lookup(payload["runtime_id"])
    assert registry_entry is None
    # All three journal phases are present for THIS job creation (the real
    # dispatch, not the seed).
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:{head}:E2E test".encode("utf-8")
    ).hexdigest()
    key = f"sess-e2e:{request_hash}"
    terminal = journal.check_idempotency(key, session_id="sess-e2e")
    assert terminal is not None
    assert terminal.phase == "completed"
    assert terminal.operation == "job_creation"
    assert terminal.job_id == payload["job_id"]
    records = [
        json.loads(line)
        for line in journal._operations_path("sess-e2e").read_text().splitlines()
        if line.strip()
    ]
    phases = [r["phase"] for r in records if r["idempotency_key"] == key]
    assert phases == ["intent", "dispatched", "completed"]
    # Audit event was emitted with delegate_start.
    audit_lines = [
        json.loads(line)
        for line in (plugin_data / "audit" / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    delegate_start_events = [e for e in audit_lines if e["action"] == "delegate_start"]
    assert len(delegate_start_events) == 1
    assert delegate_start_events[0]["job_id"] == payload["job_id"]
    # LOAD-BEARING AC 4 PROOF: the seeded unresolved ``dispatched`` entry
    # that existed BEFORE the first dispatch has been reconciled by
    # ``recover_startup()`` running inside ``_ensure_delegation_controller()``
    # on the lazy factory path. The seed key no longer appears in
    # ``list_unresolved()`` and its terminal phase is ``completed``. If the
    # factory path ever regresses (e.g., a refactor drops the recover_startup
    # call from _ensure_delegation_controller), these two assertions fail and
    # the "end-to-end" label stops being a lie. The separate retry-ordering
    # invariant (no pin when recovery fails) is proven by Task 8's
    # test_ensure_delegation_controller_does_not_pin_on_recovery_failure,
    # not by this integration test.
    post_unresolved_seeds = [
        e
        for e in journal.list_unresolved(session_id="sess-e2e")
        if e.operation == "job_creation" and e.idempotency_key == seeded_key
    ]
    assert post_unresolved_seeds == []
    seeded_terminal = journal.check_idempotency(seeded_key, session_id="sess-e2e")
    assert seeded_terminal is not None
    assert seeded_terminal.phase == "completed"

    # After a clean completion, the job is attention-active (completed/pending)
    # — a second start is rejected until the user promotes or discards. This
    # verifies the singleton user-attention invariant: runtime and journal
    # sources are cleared (the runtime was released and journal resolved), but
    # the job store retains the completed job until the user acts on it.
    second_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "E2E second"},
            },
        }
    )
    assert "isError" not in second_response["result"]
    second_payload = json.loads(second_response["result"]["content"][0]["text"])
    assert second_payload["busy"] is True
    assert second_payload["active_job_id"] == payload["job_id"]


# -----------------------------------------------------------------------------
# Escalation E2E tests — verify full capture path through MCP dispatch.
# -----------------------------------------------------------------------------


def _command_approval_request_msg(
    *,
    request_id: int | str = 42,
    item_id: str = "item-1",
    thread_id: str = "thr-exec-stub",
    turn_id: str = "turn-stub",
) -> dict[str, Any]:
    """Build a fake command_approval server request for integration tests."""
    return {
        "id": request_id,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "command": "rm -rf /",
        },
    }


def _permissions_request_msg(
    *,
    request_id: int | str = 99,
    item_id: str = "item-p",
    thread_id: str = "thr-exec-stub",
    turn_id: str = "turn-stub",
) -> dict[str, Any]:
    """Build a fake unknown-kind (permissions) server request for integration tests."""
    return {
        "id": request_id,
        "method": "item/permissions/requestApproval",
        "params": {
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
            "scope": "network",
        },
    }


def test_e2e_command_approval_produces_escalation(tmp_path: Path) -> None:
    """Full path: start → turn dispatch → command approval → cancel → DelegationEscalation."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    session = _ConfigurableStubSession(
        server_requests=[_command_approval_request_msg()],
    )
    server, job_store, prs, journal, plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: session,
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )

    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])

    # Top-level escalation flag set.
    assert payload["escalated"] is True

    # Job landed in needs_escalation.
    assert payload["job"]["status"] == "needs_escalation"

    # Pending escalation projected with correct kind (internal IDs stripped).
    assert payload["pending_escalation"]["kind"] == "command_approval"
    assert payload["pending_escalation"]["request_id"] == "42"

    # agent_context captured (may be None but key must be present).
    assert "agent_context" in payload

    # Store confirms resolved status matches the returned object.
    stored = prs.get("42")
    assert stored is not None
    assert stored.status == "resolved"

    # Escalation audit event emitted.
    audit_lines = [
        json.loads(line)
        for line in (plugin_data / "audit" / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    escalation_events = [e for e in audit_lines if e.get("action") == "escalate"]
    assert len(escalation_events) == 1
    assert escalation_events[0]["request_id"] == "42"

    # Job persisted with needs_escalation status.
    job_id = payload["job"]["job_id"]
    persisted_job = job_store.get(job_id)
    assert persisted_job is not None
    assert persisted_job.status == "needs_escalation"


def test_e2e_unknown_request_kind_interrupts_and_escalates(tmp_path: Path) -> None:
    """Unknown request kind (permissions) → turn interrupt → needs_escalation."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    session = _ConfigurableStubSession(
        server_requests=[_permissions_request_msg()],
    )
    server, job_store, prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: session,
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Deploy"},
            },
        }
    )

    assert "isError" not in response["result"]
    payload = json.loads(response["result"]["content"][0]["text"])

    assert payload["escalated"] is True
    assert payload["job"]["status"] == "needs_escalation"
    assert payload["pending_escalation"]["kind"] == "unknown"
    assert payload["pending_escalation"]["request_id"] == "99"

    # Pending request persisted (unknown kind → status resolved, D4 rule for
    # successful parse with unknown kind).
    stored = prs.get("99")
    assert stored is not None
    assert stored.status == "resolved"

    # Job persisted in needs_escalation.
    persisted_job = job_store.get(payload["job"]["job_id"])
    assert persisted_job is not None
    assert persisted_job.status == "needs_escalation"


def test_e2e_busy_gate_blocks_when_job_needs_escalation(tmp_path: Path) -> None:
    """A job in needs_escalation is still active → busy gate blocks second start."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    session = _ConfigurableStubSession(
        server_requests=[_command_approval_request_msg(request_id=55)],
    )
    server, job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: session,
    )

    # First start produces an escalation (needs_escalation = active).
    first_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {
                    "repo_root": str(repo_root),
                    "objective": "First job",
                },
            },
        }
    )
    first_payload = json.loads(first_response["result"]["content"][0]["text"])
    assert first_payload["escalated"] is True
    assert first_payload["job"]["status"] == "needs_escalation"

    # Second start on the same repo is rejected by the busy gate.
    second_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {
                    "repo_root": str(repo_root),
                    "objective": "Second job",
                },
            },
        }
    )

    assert "isError" not in second_response["result"]
    second_payload = json.loads(second_response["result"]["content"][0]["text"])

    # Busy gate fires: response carries busy=True and the active job details.
    assert second_payload["busy"] is True
    assert second_payload["active_job_id"] == first_payload["job"]["job_id"]
    assert second_payload["active_job_status"] == "needs_escalation"


def test_delegate_poll_completed_job_materializes_snapshot_through_mcp(
    tmp_path: Path,
) -> None:
    """Poll a completed job → materializes inspection artifacts through MCP dispatch."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _StubSession(),
    )

    # Start a job — completes immediately since _StubSession returns "completed".
    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {
                    "repo_root": str(repo_root),
                    "objective": "Build feature",
                },
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["status"] == "completed"
    job_id = start_payload["job_id"]

    # Create a change in the worktree so artifact materialization produces content.
    worktree_path = Path(start_payload["worktree_path"])
    (worktree_path / "new_file.py").write_text("# new\n")
    subprocess.run(
        ["git", "-C", str(worktree_path), "add", "new_file.py"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(worktree_path), "commit", "-m", "add feature"],
        check=True,
        capture_output=True,
    )

    # Poll the completed job.
    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": job_id},
            },
        }
    )

    assert "isError" not in poll_response["result"]
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])

    assert poll_payload["job"]["promotion_state"] == "pending"
    assert poll_payload["inspection"]["artifact_hash"] is not None
    assert len(poll_payload["inspection"]["artifact_paths"]) == 3


def test_delegate_poll_needs_escalation_returns_projected_request(
    tmp_path: Path,
) -> None:
    """Poll a needs_escalation job → returns pending_escalation view without codex_thread_id."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    session = _ConfigurableStubSession(
        server_requests=[_command_approval_request_msg(request_id=42)],
    )
    server, _job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: session,
    )

    # Start a job — escalates due to server request.
    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["escalated"] is True
    job_id = start_payload["job"]["job_id"]

    # Poll the escalated job.
    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": job_id},
            },
        }
    )

    assert "isError" not in poll_response["result"]
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])

    assert poll_payload["pending_escalation"]["request_id"] == "42"
    assert poll_payload["pending_escalation"]["available_decisions"] == [
        "approve",
        "deny",
    ]
    # codex_thread_id must NOT be in the response (PendingEscalationView strips it).
    assert "codex_thread_id" not in json.dumps(poll_payload["pending_escalation"])


def test_delegate_decide_approve_end_to_end_through_mcp_dispatch(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, pending_request_store, journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["job"]["status"] == "needs_escalation"

    controller = server._ensure_delegation_controller()
    entry = controller._runtime_registry.lookup(start_payload["job"]["runtime_id"])
    assert entry is not None
    stub = entry.session
    stub._server_requests = []
    stub._turn_result = TurnExecutionResult(
        turn_id="turn-stub-2",
        status="completed",
        agent_message="Follow-up done.",
        notifications=(),
    )

    decide_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": start_payload["job"]["job_id"],
                    "request_id": start_payload["pending_escalation"]["request_id"],
                    "decision": "approve",
                },
            },
        }
    )

    decide_payload = json.loads(decide_response["result"]["content"][0]["text"])
    # Packet 1 (T-20260423-02): decide response is the 3-field shape.
    assert set(decide_payload.keys()) == {"decision_accepted", "job_id", "request_id"}
    assert decide_payload["decision_accepted"] is True
    # Post-dispatch job state observed via poll(), not decide() result.
    job_id = start_payload["job"]["job_id"]
    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": job_id},
            },
        }
    )
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])
    assert poll_payload["job"]["status"] == "completed"


def test_delegate_decide_deny_end_to_end_through_mcp_dispatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, pending_request_store, journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])

    decide_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": start_payload["job"]["job_id"],
                    "request_id": start_payload["pending_escalation"]["request_id"],
                    "decision": "deny",
                },
            },
        }
    )

    decide_payload = json.loads(decide_response["result"]["content"][0]["text"])
    # Packet 1 (T-20260423-02): decide response is the 3-field shape.
    assert set(decide_payload.keys()) == {"decision_accepted", "job_id", "request_id"}
    assert decide_payload["decision_accepted"] is True
    # Post-dispatch job state observed via poll(), not decide() result.
    job_id = start_payload["job"]["job_id"]
    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": job_id},
            },
        }
    )
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])
    assert poll_payload["job"]["status"] == "failed"


# ---------------------------------------------------------------------------
# MCP-boundary contract: pending_escalation projection
# ---------------------------------------------------------------------------

# Internal IDs that must NEVER appear in caller-visible escalation payloads.
_INTERNAL_IDS = frozenset(
    {
        "codex_thread_id",
        "codex_turn_id",
        "item_id",
        "runtime_id",
        "collaboration_id",
        "status",
    }
)


def _assert_no_internal_ids(payload: dict[str, Any], key: str) -> None:
    """Assert that payload[key] contains no internal PendingServerRequest fields."""
    serialized = json.dumps(payload[key])
    for field in _INTERNAL_IDS:
        assert field not in serialized, (
            f"Internal field {field!r} leaked into caller-visible {key!r} payload"
        )


def test_start_escalation_uses_pending_escalation_key(tmp_path: Path) -> None:
    """codex.delegate.start escalation must use 'pending_escalation', not 'pending_request'."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    session = _ConfigurableStubSession(
        server_requests=[_command_approval_request_msg()],
    )
    server, _job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: session,
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["escalated"] is True

    # New contract: caller-visible key is "pending_escalation".
    assert "pending_escalation" in payload, "start must use 'pending_escalation' key"
    assert "pending_request" not in payload, "start must not use 'pending_request' key"

    # Projected fields present.
    esc = payload["pending_escalation"]
    assert esc["request_id"] == "42"
    assert esc["kind"] == "command_approval"
    assert "available_decisions" in esc

    # No internal IDs leaked.
    _assert_no_internal_ids(payload, "pending_escalation")


def test_decide_reescalation_uses_pending_escalation_key(tmp_path: Path) -> None:
    """codex.delegate.decide re-escalation must use 'pending_escalation', not 'pending_request'."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, _job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    # Start → escalation.
    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    job_id = start_payload["job"]["job_id"]

    # Wire up re-escalation on the resume turn.
    controller = server._ensure_delegation_controller()
    entry = controller._runtime_registry.lookup(start_payload["job"]["runtime_id"])
    assert entry is not None
    stub = entry.session
    stub._server_requests = [_permissions_request_msg(request_id=99)]
    stub._turn_result = TurnExecutionResult(
        turn_id="turn-stub-2",
        status="interrupted",
        agent_message="Need another approval.",
        notifications=(),
    )

    # Extract request_id from the start escalation payload.
    # After projection, this comes from pending_escalation (not pending_request).
    start_esc = start_payload.get("pending_escalation") or start_payload.get(
        "pending_request"
    )
    assert start_esc is not None

    decide_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.decide",
                "arguments": {
                    "job_id": job_id,
                    "request_id": start_esc["request_id"],
                    "decision": "approve",
                },
            },
        }
    )

    decide_payload = json.loads(decide_response["result"]["content"][0]["text"])
    # Packet 1 (T-20260423-02): decide response is the 3-field shape only.
    assert set(decide_payload.keys()) == {"decision_accepted", "job_id", "request_id"}
    assert decide_payload["decision_accepted"] is True
    assert "pending_escalation" not in decide_payload
    assert "pending_request" not in decide_payload

    # Re-escalation is observable via poll(), not decide() (Packet 1).
    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": job_id},
            },
        }
    )
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])
    assert "pending_escalation" in poll_payload, (
        "poll must use 'pending_escalation' key"
    )
    assert "pending_request" not in poll_payload, (
        "poll must not use 'pending_request' key"
    )

    esc = poll_payload["pending_escalation"]
    assert esc["request_id"] == "99"
    assert esc["kind"] == "unknown"
    assert "available_decisions" in esc

    # No internal IDs leaked.
    _assert_no_internal_ids(poll_payload, "pending_escalation")


# -----------------------------------------------------------------------------
# codex.status active_delegation enrichment tests
# -----------------------------------------------------------------------------


def _build_status_test_server(
    tmp_path: Path,
) -> tuple[McpServer, DelegationController, DelegationJobStore, Path]:
    """Build an McpServer wired through the delegation factory path for status enrichment tests."""
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    plugin_data = tmp_path / "pd"
    plugin_data.mkdir()

    journal = OperationJournal(plugin_data)
    control_plane = ControlPlane(
        plugin_data_path=plugin_data,
        journal=journal,
        runtime_factory=lambda _: _StubSession(),  # type: ignore[arg-type]
        compat_checker=_make_compat_result,
    )
    job_store = DelegationJobStore(plugin_data, "sess-status")
    lineage_store = LineageStore(plugin_data, "sess-status")
    pending_request_store = PendingRequestStore(plugin_data, "sess-status")
    runtime_registry = ExecutionRuntimeRegistry()
    artifact_store = ArtifactStore(plugin_data, timestamp_factory=journal.timestamp)
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id="sess-status",
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
    )

    class _StatusCP:
        def codex_status(self, repo_root: Path) -> dict:
            return {
                "auth_status": "authenticated",
                "errors": [],
                "active_delegation": None,
            }

        def codex_consult(self, request: object) -> object:
            raise NotImplementedError

    server = McpServer(
        control_plane=_StatusCP(),
        delegation_factory=lambda: controller,
    )
    return server, controller, job_store, repo_root


def _status_call(server: McpServer, repo_root: Path) -> dict:
    """Call codex.status through the MCP server and return the parsed result."""
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.status",
                "arguments": {"repo_root": str(repo_root)},
            },
        }
    )
    return json.loads(response["result"]["content"][0]["text"])


def _start_call(server: McpServer, repo_root: Path, objective: str = "test") -> dict:
    """Call codex.delegate.start through the MCP server and return the parsed result."""
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": objective},
            },
        }
    )
    return json.loads(response["result"]["content"][0]["text"])


def _discard_call(server: McpServer, job_id: str) -> dict:
    """Call codex.delegate.discard through the MCP server and return the parsed result."""
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.discard",
                "arguments": {"job_id": job_id},
            },
        }
    )
    return json.loads(response["result"]["content"][0]["text"])


def test_status_active_delegation_null_when_no_jobs(tmp_path: Path) -> None:
    """codex.status returns active_delegation=null when no delegation exists."""
    server, _ctrl, _store, repo_root = _build_status_test_server(tmp_path)
    result = _status_call(server, repo_root)
    assert result["active_delegation"] is None


def test_status_active_delegation_populated_after_start(tmp_path: Path) -> None:
    """codex.status returns active_delegation after a delegation job starts."""
    server, _ctrl, _store, repo_root = _build_status_test_server(tmp_path)
    start_result = _start_call(server, repo_root, "test objective")
    job_id = start_result["job_id"]

    status = _status_call(server, repo_root)
    assert status["active_delegation"] is not None
    assert status["active_delegation"]["job_id"] == job_id


def test_status_active_delegation_null_after_discard(tmp_path: Path) -> None:
    """codex.status returns active_delegation=null after job is discarded."""
    server, _ctrl, _store, repo_root = _build_status_test_server(tmp_path)
    start_result = _start_call(server, repo_root, "test objective")
    job_id = start_result["job_id"]

    _discard_call(server, job_id)

    status = _status_call(server, repo_root)
    assert status["active_delegation"] is None


def test_status_active_delegation_includes_required_fields(tmp_path: Path) -> None:
    """active_delegation contains the required shape fields."""
    server, _ctrl, _store, repo_root = _build_status_test_server(tmp_path)
    _start_call(server, repo_root, "test objective")

    status = _status_call(server, repo_root)
    ad = status["active_delegation"]
    assert ad is not None
    for field in (
        "job_id",
        "status",
        "promotion_state",
        "base_commit",
        "artifact_hash",
        "artifact_paths",
        "attention_job_count",
    ):
        assert field in ad, f"active_delegation missing field: {field}"
    assert ad["attention_job_count"] == 1


def test_status_delegation_status_error_when_factory_fails(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """When _ensure_delegation_controller() fails, active_delegation is null,
    delegation_status_error contains a diagnostic, and the full traceback is
    logged server-side."""

    def failing_factory():
        raise RuntimeError("factory recovery failed")

    class _StatusCP:
        def codex_status(self, repo_root: Path) -> dict:
            return {
                "auth_status": "authenticated",
                "errors": [],
                "active_delegation": None,
            }

        def codex_consult(self, request: object) -> object:
            raise NotImplementedError

    server = McpServer(
        control_plane=_StatusCP(),
        delegation_factory=failing_factory,
    )
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    with caplog.at_level(
        logging.WARNING, logger="codex_collaboration.server.mcp_server"
    ):
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "codex.status",
                    "arguments": {"repo_root": str(repo_root)},
                },
            }
        )
    result = json.loads(response["result"]["content"][0]["text"])
    assert result["active_delegation"] is None
    assert "delegation_status_error" in result
    assert "factory recovery failed" in result["delegation_status_error"]
    # CRITICAL: global errors must NOT be polluted — existing status consumers
    # (consult, dialogue) treat non-empty errors as blocking.
    assert result["errors"] == []
    # Verify server-side logging captures the full exception for debuggability.
    assert any("factory recovery failed" in r.message for r in caplog.records)
    assert any(
        r.exc_info is not None
        for r in caplog.records
        if "factory recovery" in r.message
    )


def test_status_active_delegation_attention_count_gt_1(tmp_path: Path) -> None:
    """When multiple attention-active jobs exist (pre-migration anomaly),
    attention_job_count > 1 is surfaced in active_delegation."""
    server, _ctrl, job_store, repo_root = _build_status_test_server(tmp_path)

    # Start a job normally (it completes with promotion_state=pending).
    _start_call(server, repo_root, "first objective")

    # Simulate pre-migration anomaly: manually create a second attention-active
    # job in the store (bypassing the busy gate which would reject it).
    from server.models import DelegationJob

    second_job = DelegationJob(
        job_id="anomaly-job",
        runtime_id="rt-anomaly",
        collaboration_id="collab-anomaly",
        base_commit="abc123",
        worktree_path="/tmp/anomaly",
        status="completed",
        promotion_state="pending",
    )
    job_store.create(second_job)

    status = _status_call(server, repo_root)
    ad = status["active_delegation"]
    assert ad is not None
    assert ad["attention_job_count"] == 2
    # Last in replay order should be the anomaly job (most recently created).
    assert ad["job_id"] == "anomaly-job"
