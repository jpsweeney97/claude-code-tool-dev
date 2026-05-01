from __future__ import annotations

import os
from pathlib import Path

import pytest

from server.runtime import (
    AppServerRuntimeSession,
    _resolve_worktree_gitdir,
    build_workspace_write_sandbox_policy,
)


class _StubClient:
    def __init__(self, response: dict[str, object]) -> None:
        self._response = response

    def request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        assert method == "account/read"
        assert params == {"refreshToken": False}
        return self._response


def test_read_account_treats_no_auth_required_as_available(tmp_path: Path) -> None:
    session = AppServerRuntimeSession(repo_root=tmp_path)
    session._client = _StubClient(  # type: ignore[assignment]
        {"account": None, "requiresOpenaiAuth": False}
    )

    account_state = session.read_account()

    assert account_state.auth_status == "authenticated"
    assert account_state.requires_openai_auth is False


class _StubClientForThreadOps:
    """Stub JSON-RPC client for thread/read and thread/resume."""

    def __init__(self, responses: dict[str, dict]) -> None:
        self._responses = responses
        self.requests: list[tuple[str, dict]] = []

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict) -> dict:
        self.requests.append((method, params))
        return self._responses.get(method, {})

    def close(self) -> None:
        pass


def test_read_thread_returns_turns() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(
        responses={
            "thread/read": {
                "thread": {
                    "id": "thr-1",
                    "turns": [
                        {
                            "id": "turn-1",
                            "status": "completed",
                            "agentMessage": "First response",
                            "createdAt": "2026-03-28T00:01:00Z",
                        },
                    ],
                },
            },
        }
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    result = session.read_thread("thr-1")
    assert result["thread"]["id"] == "thr-1"
    assert len(result["thread"]["turns"]) == 1
    assert client.requests[0] == (
        "thread/read",
        {"threadId": "thr-1", "includeTurns": True},
    )


def test_resume_thread_returns_thread_id_from_response() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(
        responses={
            "thread/resume": {
                "thread": {"id": "thr-1"},
            },
        }
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    resumed_thread_id = session.resume_thread("thr-1")
    assert resumed_thread_id == "thr-1"
    assert client.requests[0] == ("thread/resume", {"threadId": "thr-1"})


def test_resume_thread_raises_on_malformed_response() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(responses={"thread/resume": {"error": "bad"}})
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    with pytest.raises(RuntimeError, match="Thread resume failed"):
        session.resume_thread("thr-1")


class _StubClientForTurnStart:
    """Stub that captures turn/start parameters."""

    def __init__(self) -> None:
        self.last_method: str | None = None
        self.last_params: dict | None = None

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        if method == "turn/start":
            self.last_method = method
            self.last_params = dict(params)
            return {"turn": {"id": "turn-1"}}
        if method == "thread/read":
            return {"thread": {"id": "thr-1", "turns": []}}
        return {}

    def next_notification(self, timeout: float = 60.0) -> dict:
        return {
            "method": "turn/completed",
            "params": {
                "turnId": "turn-1",
                "turn": {"id": "turn-1", "status": "completed"},
                "agentMessage": "done",
            },
        }

    def close(self) -> None:
        pass


class TestRunTurnEffort:
    def test_effort_included_when_provided(self, tmp_path: Path) -> None:
        session = AppServerRuntimeSession(repo_root=tmp_path)
        stub = _StubClientForTurnStart()
        session._client = stub  # type: ignore[assignment]
        session.run_advisory_turn(
            thread_id="thr-1",
            prompt_text="test",
            output_schema={},
            effort="high",
        )
        assert stub.last_params is not None
        assert stub.last_params["effort"] == "high"

    def test_effort_absent_when_none(self, tmp_path: Path) -> None:
        session = AppServerRuntimeSession(repo_root=tmp_path)
        stub = _StubClientForTurnStart()
        session._client = stub  # type: ignore[assignment]
        session.run_advisory_turn(
            thread_id="thr-1",
            prompt_text="test",
            output_schema={},
        )
        assert stub.last_params is not None
        assert "effort" not in stub.last_params


def test_build_workspace_write_sandbox_policy_restricts_reads_and_writes(
    tmp_path: Path,
) -> None:
    worktree_path = tmp_path / "worktree"
    policy = build_workspace_write_sandbox_policy(worktree_path)
    home = Path.home()
    assert policy == {
        "type": "workspaceWrite",
        "writableRoots": [str(worktree_path.resolve())],
        "readOnlyAccess": {
            "type": "restricted",
            "readableRoots": [
                str(worktree_path.resolve()),
                str(home / ".codex" / "memories"),
                str(home / ".codex" / "plugins" / "cache"),
                str(home / ".agents" / "skills"),
                str(home / ".agents" / "plugins"),
            ],
            "includePlatformDefaults": True,
        },
        "networkAccess": False,
        "excludeSlashTmp": True,
        "excludeTmpdirEnvVar": True,
    }


def test_run_turn_uses_custom_sandbox_policy_when_provided(tmp_path: Path) -> None:
    session = AppServerRuntimeSession(repo_root=tmp_path)
    stub = _StubClientForTurnStart()
    session._client = stub  # type: ignore[assignment]

    worktree_path = tmp_path / "worktree"
    sandbox_policy = build_workspace_write_sandbox_policy(worktree_path)
    session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
        sandbox_policy=sandbox_policy,
    )

    assert stub.last_params is not None
    assert stub.last_params["sandboxPolicy"] == sandbox_policy


def test_run_advisory_turn_uses_read_only_policy(tmp_path: Path) -> None:
    session = AppServerRuntimeSession(repo_root=tmp_path)
    stub = _StubClientForTurnStart()
    session._client = stub  # type: ignore[assignment]

    session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert stub.last_params is not None
    assert stub.last_params["sandboxPolicy"] == {"type": "readOnly"}


# ---------------------------------------------------------------------------
# FakeServerProcess — configurable fake for status-widening tests
# ---------------------------------------------------------------------------


class FakeServerProcess:
    """Fake JSON-RPC client that queues specific responses and notifications."""

    def __init__(self) -> None:
        self._responses: dict[str, dict] = {}
        self._errors: dict[str, Exception] = {}
        self._notifications: list[dict] = []
        self._notification_index = 0
        self.requests: list[tuple[str, dict]] = []
        self.client = _FakeJsonRpcClient(self)

    def queue_response(self, method: str, result: dict) -> None:
        self._responses[method] = result

    def queue_error(self, method: str, error: Exception) -> None:
        self._errors[method] = error

    def queue_notification(self, method: str, params: dict) -> None:
        self._notifications.append({"method": method, "params": params})


class _FakeJsonRpcClient:
    """Companion client for FakeServerProcess."""

    def __init__(self, server: FakeServerProcess) -> None:
        self._server = server

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict) -> dict:
        self._server.requests.append((method, params))
        if method in self._server._errors:
            raise self._server._errors[method]
        return self._server._responses.get(method, {})

    def next_notification(self, timeout: float = 60.0) -> dict:
        if self._server._notification_index < len(self._server._notifications):
            n = self._server._notifications[self._server._notification_index]
            self._server._notification_index += 1
            return n
        raise TimeoutError("No more notifications")

    def respond(self, request_id: str | int, result: dict) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.fixture
def fake_server_process() -> FakeServerProcess:
    return FakeServerProcess()


def test_run_turn_accepts_interrupted_status_when_allowed(
    fake_server_process: FakeServerProcess,
) -> None:
    """Execution turns accept interrupted as a valid terminal status."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turn": {"id": "t1", "status": "interrupted", "items": []},
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client  # type: ignore[assignment]

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.status == "interrupted"
    assert result.turn_id == "t1"


def test_run_turn_accepts_failed_status_when_allowed(
    fake_server_process: FakeServerProcess,
) -> None:
    """Execution turns accept failed as a valid terminal status."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turn": {
                "id": "t1",
                "status": "failed",
                "items": [],
                "error": {"message": "boom"},
            },
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client  # type: ignore[assignment]

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.status == "failed"


# ---------------------------------------------------------------------------
# Tests #4-#9: thread/read fallback for empty agent_message
# ---------------------------------------------------------------------------

import json

FALLBACK_AGENT_TEXT = json.dumps(
    {
        "position": "recovered via fallback",
        "evidence": [
            {"claim": "test claim", "citation": "test.py:1-5"},
        ],
        "uncertainties": ["none"],
        "follow_up_branches": ["branch-a"],
    }
)


def _setup_advisory_session_no_item_completed(
    fake_server_process: FakeServerProcess,
) -> AppServerRuntimeSession:
    """Common setup: advisory turn completes without item/completed notification."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turnId": "t1",
            "turn": {"id": "t1", "status": "completed", "items": []},
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client  # type: ignore[assignment]
    return session


def test_advisory_turn_fallback_populates_agent_message(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #4: fallback via thread/read populates agent_message when
    item/completed did not fire."""
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": FALLBACK_AGENT_TEXT,
                    },
                ],
            },
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.agent_message == FALLBACK_AGENT_TEXT
    assert result.turn_id == "t1"
    assert result.status == "completed"
    thread_read_calls = [
        (m, p) for m, p in fake_server_process.requests if m == "thread/read"
    ]
    assert len(thread_read_calls) == 1
    assert thread_read_calls[0][1] == {"threadId": "thr-1", "includeTurns": True}


def test_advisory_turn_fallback_uses_turn_id_lookup(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #4 supplement: fallback selects the correct turn by ID, not position."""
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "earlier-turn",
                        "status": "completed",
                        "agentMessage": "wrong turn",
                    },
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": FALLBACK_AGENT_TEXT,
                    },
                ],
            },
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.agent_message == FALLBACK_AGENT_TEXT


def test_fallback_output_parses_as_consult_response(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #5: fallback-produced agent_message passes through
    parse_consult_response without error."""
    from server.prompt_builder import parse_consult_response

    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "agentMessage": FALLBACK_AGENT_TEXT,
                    },
                ],
            },
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    position, evidence, uncertainties, follow_up_branches = parse_consult_response(
        result.agent_message
    )
    assert position == "recovered via fallback"
    assert len(evidence) == 1
    assert uncertainties == ("none",)
    assert follow_up_branches == ("branch-a",)


def test_fallback_read_thread_raises(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #6: read_thread raises — fall through with agent_message == ""."""
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_error(
        "thread/read", RuntimeError("connection lost")
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.agent_message == ""
    assert result.status == "completed"


def test_fallback_no_matching_turn_id(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #7: thread/read returns turns but none match turn_id."""
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "other-turn",
                        "status": "completed",
                        "agentMessage": "wrong turn",
                    },
                ],
            },
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.agent_message == ""
    assert result.status == "completed"


def test_fallback_matching_turn_no_extractable_message(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #8: matching turn exists but extract_agent_message returns ""."""
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {"id": "t1", "status": "completed"},
                ],
            },
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.agent_message == ""
    assert result.status == "completed"


def test_execution_turn_does_not_trigger_fallback(
    fake_server_process: FakeServerProcess,
) -> None:
    """Test #9: run_execution_turn with empty agent_message on interrupted
    status does NOT call thread/read."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turn": {"id": "t1", "status": "interrupted", "items": []},
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client  # type: ignore[assignment]

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.agent_message == ""
    assert result.status == "interrupted"
    thread_read_calls = [
        (m, p) for m, p in fake_server_process.requests if m == "thread/read"
    ]
    assert len(thread_read_calls) == 0


# ---------------------------------------------------------------------------
# Option E: gitdir resolution
# ---------------------------------------------------------------------------

_STATIC_READABLE_ROOT_COUNT = 5  # worktree + 4 carve-outs


def _make_worktree_gitdir(
    tmp_path: Path,
    worktree_name: str = "worktree",
    gitdir_name: str = "wk1",
) -> tuple[Path, Path]:
    """Create a realistic worktree + gitdir pair with bidirectional pointers."""
    worktree = tmp_path / worktree_name
    worktree.mkdir()
    gitdir = tmp_path / "repo" / ".git" / "worktrees" / gitdir_name
    gitdir.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n")
    (gitdir / "gitdir").write_text(f"{worktree / '.git'}\n")
    return worktree, gitdir


def test_resolve_worktree_gitdir_absolute_pointer(tmp_path: Path) -> None:
    worktree, gitdir = _make_worktree_gitdir(tmp_path)

    result = _resolve_worktree_gitdir(worktree)

    assert result == str(gitdir.resolve())


def test_resolve_worktree_gitdir_relative_pointer(tmp_path: Path) -> None:
    worktree, gitdir = _make_worktree_gitdir(tmp_path)
    rel = os.path.relpath(gitdir, worktree)
    (worktree / ".git").write_text(f"gitdir: {rel}\n")

    result = _resolve_worktree_gitdir(worktree)

    assert result == str(gitdir.resolve())


def test_resolve_worktree_gitdir_none_when_outside_git_worktrees(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: /home/user/.config/secrets\n")

    assert _resolve_worktree_gitdir(worktree) is None


def test_resolve_worktree_gitdir_none_when_git_but_not_worktrees(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: /some/repo/.git/refs/heads\n")

    assert _resolve_worktree_gitdir(worktree) is None


def test_resolve_worktree_gitdir_none_when_worktrees_dir_itself(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(
        f"gitdir: {tmp_path}/repo/.git/worktrees\n"
    )

    assert _resolve_worktree_gitdir(worktree) is None


def test_resolve_worktree_gitdir_none_when_sibling_worktree(
    tmp_path: Path,
) -> None:
    worktree_a, _ = _make_worktree_gitdir(
        tmp_path, worktree_name="wt-a", gitdir_name="wk-a"
    )
    _, gitdir_b = _make_worktree_gitdir(
        tmp_path, worktree_name="wt-b", gitdir_name="wk-b"
    )
    # Rewrite wt-a's .git to point at wt-b's gitdir (attack scenario)
    (worktree_a / ".git").write_text(f"gitdir: {gitdir_b}\n")

    assert _resolve_worktree_gitdir(worktree_a) is None


def test_resolve_worktree_gitdir_none_when_back_pointer_missing(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    gitdir = tmp_path / "repo" / ".git" / "worktrees" / "wk1"
    gitdir.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n")
    # No back-pointer file created

    assert _resolve_worktree_gitdir(worktree) is None


def test_resolve_worktree_gitdir_none_when_git_is_directory(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").mkdir()

    assert _resolve_worktree_gitdir(worktree) is None


def test_resolve_worktree_gitdir_none_when_malformed(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("not a gitdir pointer\n")

    assert _resolve_worktree_gitdir(worktree) is None


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="permission removal ineffective as root",
)
def test_resolve_worktree_gitdir_none_when_unreadable(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    git_file = worktree / ".git"
    git_file.write_text("gitdir: /some/path\n")
    git_file.chmod(0o000)
    try:
        assert _resolve_worktree_gitdir(worktree) is None
    finally:
        git_file.chmod(0o644)


def test_resolve_worktree_gitdir_none_when_missing(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()

    assert _resolve_worktree_gitdir(worktree) is None


def test_policy_includes_gitdir_when_valid_git_pointer_present(
    tmp_path: Path,
) -> None:
    worktree, gitdir = _make_worktree_gitdir(tmp_path)

    policy = build_workspace_write_sandbox_policy(worktree)
    readable_roots = policy["readOnlyAccess"]["readableRoots"]

    assert len(readable_roots) == _STATIC_READABLE_ROOT_COUNT + 1
    assert readable_roots[-1] == str(gitdir.resolve())


def test_policy_excludes_gitdir_when_pointer_outside_git_worktrees(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: /home/user/.config/secrets\n")

    policy = build_workspace_write_sandbox_policy(worktree)
    readable_roots = policy["readOnlyAccess"]["readableRoots"]

    assert len(readable_roots) == _STATIC_READABLE_ROOT_COUNT


def test_policy_excludes_gitdir_when_sibling_worktree_pointer(
    tmp_path: Path,
) -> None:
    worktree_a, _ = _make_worktree_gitdir(
        tmp_path, worktree_name="wt-a", gitdir_name="wk-a"
    )
    _, gitdir_b = _make_worktree_gitdir(
        tmp_path, worktree_name="wt-b", gitdir_name="wk-b"
    )
    (worktree_a / ".git").write_text(f"gitdir: {gitdir_b}\n")

    policy = build_workspace_write_sandbox_policy(worktree_a)
    readable_roots = policy["readOnlyAccess"]["readableRoots"]

    assert len(readable_roots) == _STATIC_READABLE_ROOT_COUNT


def test_policy_excludes_gitdir_when_no_git_pointer(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()

    policy = build_workspace_write_sandbox_policy(worktree)
    readable_roots = policy["readOnlyAccess"]["readableRoots"]

    assert len(readable_roots) == _STATIC_READABLE_ROOT_COUNT
