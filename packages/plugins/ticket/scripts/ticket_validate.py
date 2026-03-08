"""Shared schema validation for writable ticket fields.

Validates field types and enum membership before render_ticket() or
YAML replacement. Rejects invalid inputs; omitted fields are not errors
(defaults are applied by the engine, not the validator).
"""
from __future__ import annotations

from typing import Any

VALID_PRIORITIES = frozenset({"critical", "high", "medium", "low"})
VALID_STATUSES = frozenset({"open", "in_progress", "blocked", "done", "wontfix"})
VALID_RESOLUTIONS = frozenset({"done", "wontfix"})


def validate_fields(fields: dict[str, Any]) -> list[str]:
    """Validate writable ticket fields. Returns list of error messages (empty = valid)."""
    errors: list[str] = []

    # --- Enum fields ---
    if "priority" in fields:
        v = fields["priority"]
        if not isinstance(v, str) or v not in VALID_PRIORITIES:
            errors.append(
                f"priority must be one of {sorted(VALID_PRIORITIES)}, got {v!r}"
            )

    if "status" in fields:
        v = fields["status"]
        if not isinstance(v, str) or v not in VALID_STATUSES:
            errors.append(
                f"status must be one of {sorted(VALID_STATUSES)}, got {v!r}"
            )

    if "resolution" in fields:
        v = fields["resolution"]
        if not isinstance(v, str) or v not in VALID_RESOLUTIONS:
            errors.append(
                f"resolution must be one of {sorted(VALID_RESOLUTIONS)}, got {v!r}"
            )

    # --- List-of-string fields ---
    for key in ("tags", "blocked_by", "blocks"):
        if key in fields:
            v = fields[key]
            if not isinstance(v, list):
                errors.append(f"{key} must be a list, got {type(v).__name__}")
            elif not all(isinstance(item, str) for item in v):
                errors.append(f"{key} must contain only strings")

    # --- Dict fields ---
    if "source" in fields:
        v = fields["source"]
        if not isinstance(v, dict):
            errors.append(f"source must be a dict, got {type(v).__name__}")
        elif not all(isinstance(val, str) for val in v.values()):
            errors.append("source values must all be strings")

    if "defer" in fields:
        v = fields["defer"]
        if not isinstance(v, dict):
            errors.append(f"defer must be a dict, got {type(v).__name__}")

    # --- Structured list fields ---
    if "key_files" in fields:
        v = fields["key_files"]
        if not isinstance(v, list):
            errors.append(f"key_files must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, dict) for item in v):
            errors.append("key_files must contain only dicts")

    return errors
