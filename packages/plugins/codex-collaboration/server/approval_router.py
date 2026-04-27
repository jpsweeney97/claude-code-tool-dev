"""Execution approval-routing primitives for T-05.

This module intentionally stops at parsing and preserving raw request-relevant
payloads. Decision routing, resolution dispatch, and job-state transitions land
 in later execution slices.
"""

from __future__ import annotations

from typing import Any

from .models import PendingRequestKind, PendingServerRequest

_REQUEST_CONTEXT_KEYS = frozenset({"itemId", "threadId", "turnId", "availableDecisions"})
_METHOD_TO_KIND: dict[str, PendingRequestKind] = {
    "item/commandExecution/requestApproval": "command_approval",
    "item/fileChange/requestApproval": "file_change",
    "item/tool/requestUserInput": "request_user_input",
}
_AVAILABLE_DECISIONS: dict[PendingRequestKind, tuple[str, ...]] = {
    "command_approval": (
        "accept",
        "acceptForSession",
        "acceptWithExecpolicyAmendment",
        "applyNetworkPolicyAmendment",
        "decline",
        "cancel",
    ),
    # File-change and user-input decision sets are routed later when the
    # execution-domain decide surface is implemented.
    "file_change": (),
    "request_user_input": (),
    "unknown": (),
}


def parse_pending_server_request(
    message: dict[str, Any],
    *,
    runtime_id: str,
    collaboration_id: str,
) -> PendingServerRequest:
    """Project a raw App Server request into a plugin-owned request record."""

    raw_request_id = _extract_wire_request_id(message, "id")
    request_id = str(raw_request_id)
    method = _require_string(message, "method")
    params = message.get("params")
    if not isinstance(params, dict):
        raise RuntimeError(
            "Server request parse failed: params is not an object. "
            f"Got: {params!r:.100}"
        )
    item_id = _require_string(params, "itemId")
    thread_id = _require_string(params, "threadId")
    turn_id = _require_string(params, "turnId")
    kind = _METHOD_TO_KIND.get(method, "unknown")
    requested_scope = {
        key: value for key, value in params.items() if key not in _REQUEST_CONTEXT_KEYS
    }
    available_decisions = _resolve_available_decisions(params, kind)
    return PendingServerRequest(
        request_id=request_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        codex_thread_id=thread_id,
        codex_turn_id=turn_id,
        item_id=item_id,
        kind=kind,
        requested_scope=requested_scope,
        available_decisions=available_decisions,
        raw_request_id=raw_request_id,
    )


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise RuntimeError(
            f"Server request parse failed: missing {key}. Got: {value!r:.100}"
        )
    return value


def _extract_wire_request_id(payload: dict[str, Any], key: str) -> int | str:
    """Extract a JSON-RPC request ID preserving its wire type.

    The wire ``RequestId`` is ``anyOf [string, integer]`` per the App
    Server schema (``ServerRequest.json:1475``). The caller stores the
    str form in ``PendingServerRequest.request_id`` for store/MCP
    correlation and D6 diagnostics, and stores this raw value in
    ``raw_request_id`` for transport so ``session.respond()`` can echo
    the original wire type — required for the App Server's id equality.
    """
    value = payload.get(key)
    if not isinstance(value, (str, int)):
        raise RuntimeError(
            f"Server request parse failed: missing {key}. Got: {value!r:.100}"
        )
    return value


def _resolve_available_decisions(
    params: dict[str, Any], kind: PendingRequestKind
) -> tuple[str, ...]:
    wire_value = params.get("availableDecisions")
    if isinstance(wire_value, list) and all(
        isinstance(decision, str) for decision in wire_value
    ):
        return tuple(wire_value)
    return _AVAILABLE_DECISIONS[kind]
