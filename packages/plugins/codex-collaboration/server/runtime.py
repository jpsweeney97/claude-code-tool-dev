"""Live App Server runtime session for advisory work."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonrpc_client import JsonRpcClient
from .models import AccountState, RuntimeHandshake, TurnExecutionResult


class AppServerRuntimeSession:
    """Thin high-level wrapper over the Codex App Server JSON-RPC transport."""

    def __init__(
        self,
        *,
        repo_root: Path,
        command: list[str] | None = None,
        request_timeout: float = 30.0,
    ) -> None:
        self._repo_root = repo_root
        self._client = JsonRpcClient(
            command or ["codex", "app-server"],
            cwd=repo_root,
            request_timeout=request_timeout,
        )

    def initialize(self) -> RuntimeHandshake:
        """Perform the `initialize` handshake."""

        result = self._client.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "codex_collaboration",
                    "title": "Codex Collaboration Plugin",
                    "version": "0.1.0",
                }
            },
        )
        return RuntimeHandshake(
            codex_home=str(result["codexHome"]),
            platform_family=str(result["platformFamily"]),
            platform_os=str(result["platformOs"]),
            user_agent=str(result["userAgent"]),
        )

    def read_account(self) -> AccountState:
        """Return the current auth state."""

        result = self._client.request("account/read", {"refreshToken": False})
        account = result.get("account")
        requires_openai_auth = bool(result.get("requiresOpenaiAuth", False))
        if isinstance(account, dict):
            account_type = account.get("type")
            return AccountState(
                auth_status="authenticated",
                account_type=str(account_type) if isinstance(account_type, str) else None,
                requires_openai_auth=requires_openai_auth,
            )
        if requires_openai_auth:
            return AccountState(
                auth_status="missing",
                account_type=None,
                requires_openai_auth=True,
            )
        # Local-only or otherwise non-OpenAI-backed runtimes are usable without
        # credentials, so "no auth required" maps to an available runtime.
        return AccountState(
            auth_status="authenticated",
            account_type=None,
            requires_openai_auth=False,
        )

    def start_thread(self) -> str:
        """Create a fresh advisory thread."""

        result = self._client.request(
            "thread/start",
            {
                "cwd": str(self._repo_root),
                "approvalPolicy": "never",
                "personality": "pragmatic",
                "serviceName": "codex_collaboration",
            },
        )
        thread = result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise RuntimeError(
                f"Thread start failed: malformed thread response. Got: {thread!r:.100}"
            )
        return str(thread["id"])

    def fork_thread(self, thread_id: str) -> str:
        """Fork a thread for a branched consultation."""

        result = self._client.request(
            "thread/fork",
            {"threadId": thread_id, "ephemeral": True},
        )
        thread = result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise RuntimeError(
                f"Thread fork failed: malformed thread response. Got: {thread!r:.100}"
            )
        return str(thread["id"])

    def run_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        output_schema: dict[str, Any],
        effort: str | None = None,
    ) -> TurnExecutionResult:
        """Start a turn and collect notifications until completion."""

        params: dict[str, Any] = {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt_text}],
            "cwd": str(self._repo_root),
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
            "summary": "concise",
            "personality": "pragmatic",
            "outputSchema": output_schema,
        }
        if effort is not None:
            params["effort"] = effort

        result = self._client.request("turn/start", params)
        turn = result.get("turn")
        if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
            raise RuntimeError(
                f"Turn start failed: malformed turn response. Got: {turn!r:.100}"
            )
        turn_id = str(turn["id"])
        agent_message = ""
        notifications: list[dict[str, Any]] = []
        while True:
            notification = self._client.next_notification(timeout=60.0)
            if notification.get("method") is None:
                continue
            notifications.append(notification)
            method = str(notification["method"])
            params = notification.get("params", {})
            if not isinstance(params, dict):
                continue
            if params.get("turnId") not in (None, turn_id):
                continue
            if method == "item/completed":
                item = params.get("item")
                if isinstance(item, dict) and item.get("type") == "agentMessage":
                    text = item.get("text")
                    if isinstance(text, str):
                        agent_message = text
            if method == "turn/completed":
                turn_payload = params.get("turn")
                if not isinstance(turn_payload, dict):
                    raise RuntimeError(
                        "Turn completion failed: missing turn payload. "
                        f"Got: {params!r:.100}"
                    )
                status = turn_payload.get("status")
                if status != "completed":
                    raise RuntimeError(
                        "Turn completion failed: turn did not complete successfully. "
                        f"Got: {turn_payload!r:.100}"
                    )
                return TurnExecutionResult(
                    turn_id=turn_id,
                    agent_message=agent_message,
                    notifications=tuple(notifications),
                )

    def read_thread(self, thread_id: str) -> dict[str, Any]:
        """Read thread state and turn history via thread/read."""
        return self._client.request(
            "thread/read",
            {"threadId": thread_id, "includeTurns": True},
        )

    def resume_thread(self, thread_id: str) -> str:
        """Resume a thread after crash recovery. Returns the (possibly new) thread ID."""
        result = self._client.request("thread/resume", {"threadId": thread_id})
        thread = result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise RuntimeError(
                f"Thread resume failed: malformed thread response. Got: {thread!r:.100}"
            )
        return str(thread["id"])

    def close(self) -> None:
        self._client.close()
