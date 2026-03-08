"""Stage-boundary input models for the ticket engine pipeline.

Frozen dataclasses with from_payload() constructors that validate shape and
presence at the dispatch boundary. Business rule validation (allowed field
values, status transitions, etc.) remains in the engine and ticket_validate.py.

Import direction: this module imports only stdlib. Entrypoints and engine
import from it. It must not import EngineResponse, AutonomyConfig, or any
ticket module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class PayloadError(Exception):
    """Raised when payload validation fails during stage-input construction.

    code: "need_fields" (missing required data) or "parse_error" (wrong type/shape)
    state: recommended EngineResponse state — "need_fields" or "escalate"
    """

    def __init__(self, message: str, *, code: str, state: str) -> None:
        super().__init__(message)
        self.code = code
        self.state = state


# --- Extraction helpers ---


def _get_str(payload: dict[str, Any], key: str, *, default: str) -> str:
    """Get a string field with a default. Raises PayloadError if present but wrong type."""
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise PayloadError(
            f"{key} must be a string, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_dict(payload: dict[str, Any], key: str, *, default: dict[str, Any] | None) -> dict[str, Any]:
    """Get a dict field with a default. Raises PayloadError if present but wrong type."""
    if key not in payload:
        if default is not None:
            return dict(default)  # Defensive copy.
        raise PayloadError(
            f"missing required field: {key}",
            code="need_fields",
            state="need_fields",
        )
    value = payload[key]
    if not isinstance(value, dict):
        raise PayloadError(
            f"{key} must be a dict, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_bool(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    """Get a bool field with a default. Raises PayloadError if present but wrong type."""
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise PayloadError(
            f"{key} must be a bool, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_float(payload: dict[str, Any], key: str, *, default: float) -> float:
    """Get a numeric field with a default. Accepts int or float."""
    value = payload.get(key, default)
    if not isinstance(value, (int, float)):
        raise PayloadError(
            f"{key} must be a number, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return float(value)


def _get_optional_str(payload: dict[str, Any], key: str) -> str | None:
    """Get an optional string field. Returns None if absent."""
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise PayloadError(
            f"{key} must be a string or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_optional_float(payload: dict[str, Any], key: str) -> float | None:
    """Get an optional numeric field. Returns None if absent."""
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise PayloadError(
            f"{key} must be a number or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return float(value)


def _get_optional_dict(payload: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Get an optional dict field. Returns None if absent."""
    value = payload.get(key)
    if value is not None and not isinstance(value, dict):
        raise PayloadError(
            f"{key} must be a dict or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


# --- Stage input models ---


@dataclass(frozen=True)
class ClassifyInput:
    """Input model for the classify stage."""

    action: str
    args: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ClassifyInput:
        return cls(
            action=_get_str(payload, "action", default=""),
            args=_get_dict(payload, "args", default={}),
            session_id=_get_str(payload, "session_id", default=""),
        )


@dataclass(frozen=True)
class PlanInput:
    """Input model for the plan stage."""

    intent: str
    fields: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> PlanInput:
        return cls(
            intent=_get_str(payload, "intent", default=_get_str(payload, "action", default="")),
            fields=_get_dict(payload, "fields", default={}),
            session_id=_get_str(payload, "session_id", default=""),
        )
