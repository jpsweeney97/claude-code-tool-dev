"""Canonical serialization and entity key functions.

Two serialization policies:
- canonical_json_bytes(): HMAC payload — exclude None, sorted keys, compact
- wire_dump(): Protocol output — include null, for JSON serialization

Never call model_dump() ad hoc. Use these functions.

Contract reference: HMAC Token Specification section.
"""

import json
from typing import Any

from pydantic import BaseModel

from context_injection.types import ProtocolModel, ReadSpec, GrepSpec


class ScoutTokenPayload(ProtocolModel):
    """HMAC signing payload. Binds turn identity to execution spec.

    Not sent over the wire — used only for canonical_json_bytes() → HMAC signing.
    """

    v: int
    conversation_id: str
    turn_number: int
    scout_option_id: str
    spec: ReadSpec | GrepSpec


def canonical_json_bytes(payload: ScoutTokenPayload) -> bytes:
    """Serialize payload to canonical JSON bytes for HMAC signing.

    Rules (from contract):
    - json.dumps(separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    - Encode as UTF-8
    - No None values (exclude_none=True)
    - No floats (ints only)
    - NFC-normalized Unicode (enforced before model construction, not here)
    """
    data = payload.model_dump(exclude_none=True)
    return json.dumps(
        data,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")


def wire_dump(model: BaseModel) -> dict[str, Any]:
    """Serialize a protocol model for wire output.

    Includes None as null (exclude_none=False, the Pydantic default).
    Used for TurnPacket and ScoutResult JSON responses.
    """
    return model.model_dump()


def make_entity_key(entity_type: str, canonical_form: str) -> str:
    """Build deterministic entity key: '{entity_type}:{canonical_form}'.

    Used for dedupe and evidence_history cross-turn identification.
    """
    return f"{entity_type}:{canonical_form}"


def parse_entity_key(key: str) -> tuple[str, str]:
    """Parse entity key back to (entity_type, canonical_form).

    Handles values containing colons (e.g., file_loc:config.py:42).
    """
    entity_type, _, canonical_form = key.partition(":")
    return entity_type, canonical_form
