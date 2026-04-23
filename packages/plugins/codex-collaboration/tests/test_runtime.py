from __future__ import annotations

from pathlib import Path

import pytest

from server.runtime import (
    AppServerRuntimeSession,
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
        self.last_method = method
        self.last_params = dict(params)
        return {"turn": {"id": "turn-1"}}

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
    assert policy == {
        "type": "workspaceWrite",
        "writableRoots": [str(worktree_path.resolve())],
        "readOnlyAccess": {
            "type": "restricted",
            "readableRoots": [str(worktree_path.resolve())],
            "includePlatformDefaults": True,
        },
        "networkAccess": False,
        "excludeSlashTmp": True,
        "excludeTmpdirEnvVar": True,
    }


def test_build_workspace_write_sandbox_policy_adds_codex_support_roots(
    tmp_path: Path,
) -> None:
    worktree_path = tmp_path / "worktree"
    codex_home = tmp_path / ".codex"
    (codex_home / "skills").mkdir(parents=True)
    (codex_home / "plugins" / "cache").mkdir(parents=True)
    (codex_home / "memories").mkdir(parents=True)
    (codex_home / "references").mkdir(parents=True)

    policy = build_workspace_write_sandbox_policy(worktree_path, codex_home=codex_home)

    readable = policy["readOnlyAccess"]["readableRoots"]
    assert readable[0] == str(worktree_path.resolve())
    assert str((codex_home / "skills").resolve()) in readable
    assert str((codex_home / "plugins" / "cache").resolve()) in readable
    assert str((codex_home / "memories").resolve()) in readable
    assert str((codex_home / "references").resolve()) in readable
    assert str(codex_home.resolve()) not in readable
    assert policy["writableRoots"] == [str(worktree_path.resolve())]


def test_build_workspace_write_sandbox_policy_skips_missing_support_roots(
    tmp_path: Path,
) -> None:
    worktree_path = tmp_path / "worktree"
    codex_home = tmp_path / ".codex"
    (codex_home / "skills").mkdir(parents=True)

    policy = build_workspace_write_sandbox_policy(worktree_path, codex_home=codex_home)

    readable = policy["readOnlyAccess"]["readableRoots"]
    assert len(readable) == 2
    assert readable[0] == str(worktree_path.resolve())
    assert readable[1] == str((codex_home / "skills").resolve())


def test_build_workspace_write_sandbox_policy_rejects_support_root_symlink_escape(
    tmp_path: Path,
) -> None:
    worktree_path = tmp_path / "worktree"
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    escape_target = tmp_path / "secret"
    escape_target.mkdir()
    (codex_home / "memories").symlink_to(escape_target)

    policy = build_workspace_write_sandbox_policy(worktree_path, codex_home=codex_home)

    readable = policy["readOnlyAccess"]["readableRoots"]
    assert str(escape_target.resolve()) not in readable
    assert len(readable) == 1


def test_initialize_retains_codex_home(tmp_path: Path) -> None:
    class _StubInitClient:
        def request(self, method: str, params: dict) -> dict:
            assert method == "initialize"
            return {
                "codexHome": str(tmp_path / ".codex"),
                "platformFamily": "darwin",
                "platformOs": "macOS",
                "userAgent": "test/1.0",
            }

    session = AppServerRuntimeSession(repo_root=tmp_path)
    session._client = _StubInitClient()  # type: ignore[assignment]

    assert session.codex_home is None
    session.initialize()
    assert session.codex_home == tmp_path / ".codex"


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
        self._notifications: list[dict] = []
        self._notification_index = 0
        self.requests: list[tuple[str, dict]] = []
        self.client = _FakeJsonRpcClient(self)

    def queue_response(self, method: str, result: dict) -> None:
        self._responses[method] = result

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
