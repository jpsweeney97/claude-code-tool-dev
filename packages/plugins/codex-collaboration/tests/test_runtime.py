from __future__ import annotations

from pathlib import Path

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
