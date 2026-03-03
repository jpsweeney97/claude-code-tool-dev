"""Ticket engine core — classify | plan | preflight | execute pipeline.

All mutation and policy-enforcement logic lives here. Entrypoints
(ticket_engine_user.py, ticket_engine_agent.py) set request_origin
and delegate to this module.

Subcommand contract: each function returns an EngineResponse with
{state, ticket_id, message, data}.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# --- Response envelope ---


@dataclass
class EngineResponse:
    """Common response envelope for all engine subcommands.

    state: machine state (one of 14 defined states, or "ok" for classify/plan success)
    error_code: machine-readable error code (one of 11 defined codes, or None on success)
    ticket_id: affected ticket ID or None
    message: human-readable description
    data: subcommand-specific output
    """

    state: str
    message: str
    error_code: str | None = None
    ticket_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "state": self.state,
            "ticket_id": self.ticket_id,
            "message": self.message,
            "data": self.data,
        }
        if self.error_code is not None:
            d["error_code"] = self.error_code
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# --- Valid actions and origins ---

VALID_ACTIONS = frozenset({"create", "update", "close", "reopen"})
VALID_ORIGINS = frozenset({"user", "agent"})


# --- classify ---


def engine_classify(
    *,
    action: str,
    args: dict[str, Any],
    session_id: str,
    request_origin: str,
) -> EngineResponse:
    """Classify the caller's intent and validate the action.

    Input action (from first-token routing) is authoritative. Classify validates
    but does not remap. If classify's intent disagrees -> intent_mismatch -> escalate.

    Returns EngineResponse with state="ok" on success, or error state on failure.
    """
    # Fail closed on unknown origin.
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
        )

    # Validate action.
    if action not in VALID_ACTIONS:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
        )

    # Resolve ticket ID from args (for non-create actions).
    resolved_ticket_id = args.get("ticket_id") if action != "create" else None

    # Confidence: high for explicit invocations (first-token routing provides strong signal).
    # This is a provisional default — calibration on labeled corpus required pre-GA.
    confidence = 0.95

    return EngineResponse(
        state="ok",
        message=f"Classified as {action}",
        data={
            "intent": action,
            "confidence": confidence,
            "resolved_ticket_id": resolved_ticket_id,
        },
    )
