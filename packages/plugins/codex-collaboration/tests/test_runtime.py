from __future__ import annotations

from pathlib import Path

import pytest

from server.runtime import AppServerRuntimeSession


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


def test_resume_thread_returns_new_thread_id() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(
        responses={
            "thread/resume": {
                "thread": {"id": "thr-resumed"},
            },
        }
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    new_thread_id = session.resume_thread("thr-1")
    assert new_thread_id == "thr-resumed"
    assert client.requests[0] == ("thread/resume", {"threadId": "thr-1"})


def test_resume_thread_raises_on_malformed_response() -> None:
    from server.runtime import AppServerRuntimeSession

    client = _StubClientForThreadOps(responses={"thread/resume": {"error": "bad"}})
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = client
    with pytest.raises(RuntimeError, match="Thread resume failed"):
        session.resume_thread("thr-1")
