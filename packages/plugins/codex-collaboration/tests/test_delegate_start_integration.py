"""Production wiring and end-to-end tests for codex.delegate.start."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from server.control_plane import ControlPlane
from server.delegation_controller import DelegationController
from server.delegation_job_store import DelegationJobStore
from server.execution_runtime_registry import ExecutionRuntimeRegistry
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.mcp_server import McpServer
from server.models import AccountState, OperationJournalEntry, RuntimeHandshake
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

    def close(self) -> None:
        pass


def _make_compat_result() -> object:
    from server.codex_compat import REQUIRED_METHODS

    class _R:
        passed = True
        codex_version = "0.117.0"
        available_methods = REQUIRED_METHODS
        errors: tuple[str, ...] = ()

    return _R()


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
    runtime_registry = ExecutionRuntimeRegistry()
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id="sess-e2e",
        plugin_data_path=plugin_data,
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
                "arguments": {"repo_root": str(repo_root)},
            },
        }
    )

    assert "isError" not in response["result"]
    content = response["result"]["content"][0]["text"]
    payload = json.loads(content)
    assert payload["status"] == "queued"
    assert payload["promotion_state"] == "pending"
    assert payload["base_commit"] == head
    worktree_path = Path(payload["worktree_path"])
    # Worktree was created and exists as a directory.
    assert worktree_path.is_dir()
    assert (worktree_path / "README.md").exists()
    # Job is persisted in the job store.
    persisted_job = job_store.get(payload["job_id"])
    assert persisted_job is not None
    # Execution CollaborationHandle is persisted in the lineage store.
    persisted_handle = lineage_store.get(payload["collaboration_id"])
    assert persisted_handle is not None
    assert persisted_handle.capability_class == "execution"
    assert persisted_handle.runtime_id == payload["runtime_id"]
    # Runtime ownership is held by the in-process registry (live view).
    registry_entry = runtime_registry.lookup(payload["runtime_id"])
    assert registry_entry is not None
    assert registry_entry.job_id == payload["job_id"]
    # All three journal phases are present for THIS job creation (the real
    # dispatch, not the seed).
    request_hash = hashlib.sha256(
        f"{repo_root.resolve()}:{head}".encode("utf-8")
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
    audit = json.loads(
        (plugin_data / "audit" / "events.jsonl").read_text().splitlines()[-1]
    )
    assert audit["action"] == "delegate_start"
    assert audit["job_id"] == payload["job_id"]
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

    # Second call is rejected with Job Busy.
    busy_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root)},
            },
        }
    )
    assert "isError" not in busy_response["result"]
    busy_payload = json.loads(busy_response["result"]["content"][0]["text"])
    assert busy_payload["busy"] is True
    assert busy_payload["active_job_id"] == payload["job_id"]
