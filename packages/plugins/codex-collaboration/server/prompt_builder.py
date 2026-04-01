"""Prompt and result helpers for advisory consultation."""

from __future__ import annotations

import json

from .models import ConsultEvidence


CONSULT_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "position": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "citation": {"type": "string"},
                },
                "required": ["claim", "citation"],
                "additionalProperties": False,
            },
        },
        "uncertainties": {
            "type": "array",
            "items": {"type": "string"},
        },
        "follow_up_branches": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["position", "evidence", "uncertainties", "follow_up_branches"],
    "additionalProperties": False,
}


def build_consult_turn_text(packet_payload: str, *, posture: str | None = None) -> str:
    """Build the single text input item for `turn/start`."""
    posture_instruction = ""
    if posture is not None:
        posture_instruction = f" Adopt a {posture} posture for this advisory turn."

    return (
        "Use the following structured task packet as the only authority for this advisory turn. "
        f"Stay within read-only advisory scope and return valid JSON matching the requested output schema.{posture_instruction}\n\n"
        f"{packet_payload}"
    )


def parse_consult_response(
    message: str,
) -> tuple[str, tuple[ConsultEvidence, ...], tuple[str, ...], tuple[str, ...]]:
    """Parse the final agent message into the structured consult projection."""

    try:
        payload = json.loads(message)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Consult result parse failed: expected JSON object. Got: {message!r:.100}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Consult result parse failed: expected object payload. Got: {payload!r:.100}"
        )
    position = payload.get("position")
    evidence_items = payload.get("evidence")
    uncertainties = payload.get("uncertainties")
    follow_up_branches = payload.get("follow_up_branches")
    if not isinstance(position, str):
        raise ValueError(
            f"Consult result parse failed: missing string position. Got: {position!r:.100}"
        )
    if not isinstance(evidence_items, list):
        raise ValueError(
            "Consult result parse failed: evidence must be an array. "
            f"Got: {evidence_items!r:.100}"
        )
    if not isinstance(uncertainties, list) or not all(
        isinstance(item, str) for item in uncertainties
    ):
        raise ValueError(
            "Consult result parse failed: uncertainties must be a string array. "
            f"Got: {uncertainties!r:.100}"
        )
    if not isinstance(follow_up_branches, list) or not all(
        isinstance(item, str) for item in follow_up_branches
    ):
        raise ValueError(
            "Consult result parse failed: follow_up_branches must be a string array. "
            f"Got: {follow_up_branches!r:.100}"
        )
    evidence: list[ConsultEvidence] = []
    for raw_item in evidence_items:
        if not isinstance(raw_item, dict):
            raise ValueError(
                "Consult result parse failed: evidence entries must be objects. "
                f"Got: {raw_item!r:.100}"
            )
        claim = raw_item.get("claim")
        citation = raw_item.get("citation")
        if not isinstance(claim, str) or not isinstance(citation, str):
            raise ValueError(
                "Consult result parse failed: evidence entry missing claim/citation strings. "
                f"Got: {raw_item!r:.100}"
            )
        evidence.append(ConsultEvidence(claim=claim, citation=citation))
    return (
        position,
        tuple(evidence),
        tuple(uncertainties),
        tuple(follow_up_branches),
    )
