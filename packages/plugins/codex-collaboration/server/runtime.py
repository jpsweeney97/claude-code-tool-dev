"""Live App Server runtime session.

Advisory and execution callers share the same JSON-RPC transport wrapper, but
capability-specific turn entrypoints remain separate so the public API does not
silently blur the runtime boundary.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from .jsonrpc_client import JsonRpcClient
from .models import AccountState, RuntimeHandshake, TurnExecutionResult
from .turn_extraction import extract_agent_message

log = logging.getLogger(__name__)


def _build_read_only_sandbox_policy() -> dict[str, Any]:
    """Return the advisory runtime sandbox policy."""

    return {"type": "readOnly"}


def build_workspace_write_sandbox_policy(worktree_path: Path) -> dict[str, Any]:
    """Return the v1 execution sandbox policy for an isolated worktree.

    Enforcement note (post-Candidate-A closure, 2026-04-29):

    The Codex App Server enforces this policy by interrupting the shell
    process mid-execution at the first boundary-violating operation,
    uniformly across operation classes (network, sensitive-host-path
    read, sibling-worktree read). Enforcement does NOT surface as a
    permission error returned to userspace — the shell is killed before
    any syscall result returns, so chain patterns like ``cmd || handler``
    cannot catch sandbox denials.

    ``includePlatformDefaults: True`` grants curated platform-default
    reads (e.g., shell binaries such as ``/bin/zsh``, ``/usr/bin/env``,
    system shared libraries) needed for command execution. Empirical
    basis for both sufficiency (canonical smoke artifact succeeded) and
    safety (3 security probes — Network, Sensitive-path, Sibling-worktree —
    all returned BLOCKED): T-01 Candidate A diagnostic closure record at
    ``docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md``.
    """

    resolved = worktree_path.resolve()
    return {
        "type": "workspaceWrite",
        "writableRoots": [str(resolved)],
        "readOnlyAccess": {
            "type": "restricted",
            "readableRoots": [str(resolved)],
            "includePlatformDefaults": True,
        },
        "networkAccess": False,
        "excludeSlashTmp": True,
        "excludeTmpdirEnvVar": True,
    }


class AppServerRuntimeSession:
    """Thin high-level wrapper over the Codex App Server JSON-RPC transport."""

    def __init__(
        self,
        *,
        repo_root: Path,
        command: list[str] | None = None,
        request_timeout: float = 1200.0,
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
                account_type=str(account_type)
                if isinstance(account_type, str)
                else None,
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

    def run_advisory_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        output_schema: dict[str, Any],
        effort: str | None = None,
    ) -> TurnExecutionResult:
        """Start an advisory turn in the read-only runtime."""

        return self._run_turn(
            thread_id=thread_id,
            prompt_text=prompt_text,
            output_schema=output_schema,
            effort=effort,
            sandbox_policy=_build_read_only_sandbox_policy(),
            approval_policy="never",
            allowed_terminal_statuses=("completed",),
            fallback_on_empty_message=True,
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
        """Start an execution turn with an explicit execution sandbox."""

        return self._run_turn(
            thread_id=thread_id,
            prompt_text=prompt_text,
            output_schema=output_schema,
            effort=effort,
            sandbox_policy=sandbox_policy,
            approval_policy=approval_policy,
            allowed_terminal_statuses=("completed", "interrupted", "failed"),
            server_request_handler=server_request_handler,
        )

    def interrupt_turn(
        self, *, thread_id: str, turn_id: str | None
    ) -> None:
        """Request cancellation of an in-flight turn via turn/interrupt."""
        params: dict[str, Any] = {"threadId": thread_id}
        if turn_id is not None:
            params["turnId"] = turn_id
        self._client.request("turn/interrupt", params)

    def _run_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        output_schema: dict[str, Any] | None,
        effort: str | None,
        sandbox_policy: dict[str, Any],
        approval_policy: str = "never",
        allowed_terminal_statuses: tuple[str, ...] = ("completed",),
        server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None]
        | None = None,
        fallback_on_empty_message: bool = False,
    ) -> TurnExecutionResult:
        """Start a turn and collect notifications until completion."""

        params: dict[str, Any] = {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt_text}],
            "cwd": str(self._repo_root),
            "approvalPolicy": approval_policy,
            "sandboxPolicy": sandbox_policy,
            "summary": "concise",
            "personality": "pragmatic",
        }
        if output_schema is not None:
            params["outputSchema"] = output_schema
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
            notification = self._client.next_notification(timeout=1200.0)
            if notification.get("method") is None:
                continue
            notifications.append(notification)
            method = str(notification["method"])
            params_n = notification.get("params", {})
            if not isinstance(params_n, dict):
                continue
            if params_n.get("turnId") not in (None, turn_id):
                continue
            # Server-request handling: messages with both 'id' and 'method'
            # are server-initiated requests, not passive notifications.
            if "id" in notification and server_request_handler is not None:
                response_payload = server_request_handler(notification)
                if response_payload is not None:
                    self._client.respond(notification["id"], response_payload)
            if method == "item/completed":
                item = params_n.get("item")
                if isinstance(item, dict) and item.get("type") == "agentMessage":
                    text = item.get("text")
                    if isinstance(text, str):
                        agent_message = text
            if method == "turn/completed":
                turn_payload = params_n.get("turn")
                if not isinstance(turn_payload, dict):
                    raise RuntimeError(
                        "Turn completion failed: missing turn payload. "
                        f"Got: {params_n!r:.100}"
                    )
                status = turn_payload.get("status")
                if status not in allowed_terminal_statuses:
                    raise RuntimeError(
                        "Turn completion failed: turn status not in allowed set. "
                        f"Got: {status!r:.100}, allowed: {allowed_terminal_statuses!r}"
                    )
                if (
                    fallback_on_empty_message
                    and not agent_message
                    and status == "completed"
                ):
                    agent_message = self._fallback_extract_agent_message(
                        thread_id, turn_id
                    )
                return TurnExecutionResult(
                    turn_id=turn_id,
                    status=str(status),
                    agent_message=agent_message,
                    notifications=tuple(notifications),
                )

    def _fallback_extract_agent_message(
        self, thread_id: str, turn_id: str
    ) -> str:
        """Best-effort agent message recovery via thread/read.

        Called when the live notification stream did not deliver an
        item/completed notification for the agent message. Falls through
        to "" on any failure — must never raise.
        """
        try:
            thread_data = self.read_thread(thread_id)
        except Exception:
            log.debug(
                "thread/read fallback failed for thread=%s turn=%s",
                thread_id,
                turn_id,
                exc_info=True,
            )
            return ""

        thread = thread_data.get("thread")
        if not isinstance(thread, dict):
            return ""
        turns = thread.get("turns")
        if not isinstance(turns, list):
            return ""

        for raw_turn in turns:
            if not isinstance(raw_turn, dict):
                continue
            if raw_turn.get("id") == turn_id:
                return extract_agent_message(raw_turn)
        return ""

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

    def respond(self, request_id: str | int, result: dict[str, Any]) -> None:
        """Send a JSON-RPC 2.0 response to a server-initiated request.

        Called by the worker to forward operator decisions and timeout signals
        back to the Codex App Server subprocess.
        """
        self._client.respond(request_id, result)

    def close(self) -> None:
        self._client.close()
