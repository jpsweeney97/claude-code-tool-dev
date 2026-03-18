"""Single source of truth for cross-model event field definitions.

All event-producing scripts (emit_analytics.py) and event-consuming
scripts (read_events.py, compute_stats.py) import field definitions
from this module.

This module owns:
- Required field sets per event type
- Valid enum values for constrained fields
- Schema version resolution logic
- Count field definitions

This module does NOT own:
- Log I/O (see event_log.py)
- Event construction or validation logic (stays in each producer/consumer)
- Validation depth (read_events validates presence only; emit_analytics
  validates enums and cross-field invariants)
"""

from __future__ import annotations

import types

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

SCHEMA_VERSION: str = "0.1.0"
"""Base schema version. Feature-flag fields bump this automatically."""


def is_non_negative_int(value: object) -> bool:
    """Check value is a non-negative int, excluding bool."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def resolve_schema_version(event: dict) -> str:
    """Determine schema version from feature-flag fields.

    Precedence: planning (0.3.0) > provenance (0.2.0) > base (0.1.0).
    """
    if event.get("question_shaped") is not None:
        return "0.3.0"
    if is_non_negative_int(event.get("provenance_unknown_count")):
        return "0.2.0"
    return SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Required fields per event type
# ---------------------------------------------------------------------------

REQUIRED_FIELDS_BY_EVENT: types.MappingProxyType[str, frozenset[str]] = types.MappingProxyType({
    "dialogue_outcome": frozenset({
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "converged",
        "convergence_reason_code",
        "termination_reason",
        "resolved_count",
        "unresolved_count",
        "emerged_count",
        "seed_confidence",
        "mode",
    }),
    "consultation_outcome": frozenset({
        "schema_version",
        "consultation_id",
        "thread_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "termination_reason",
        "mode",
    }),
    "delegation_outcome": frozenset({
        "schema_version",
        "event",
        "ts",
        "consultation_id",
        "session_id",
        "thread_id",
        "dispatched",
        "sandbox",
        "full_auto",
        "credential_blocked",
        "dirty_tree_blocked",
        "readable_secret_file_blocked",
        "commands_run_count",
        "exit_code",
        "termination_reason",
        "model",
        "reasoning_effort",
    }),
})

STRUCTURED_EVENT_TYPES: frozenset[str] = frozenset(REQUIRED_FIELDS_BY_EVENT)
"""Event types that have required-field schemas. Derived from REQUIRED_FIELDS_BY_EVENT."""

KNOWN_UNSTRUCTURED_TYPES: frozenset[str] = frozenset({
    "block", "shadow", "consultation",
})
"""Event types that are valid but have no required-field schema."""

assert STRUCTURED_EVENT_TYPES.isdisjoint(KNOWN_UNSTRUCTURED_TYPES), \
    "structured and unstructured event types must not overlap"


def required_fields(event_type: str) -> frozenset[str]:
    """Return required fields for an event type, or empty frozenset if unknown."""
    return REQUIRED_FIELDS_BY_EVENT.get(event_type, frozenset())


# ---------------------------------------------------------------------------
# Enum value sets
# ---------------------------------------------------------------------------

VALID_POSTURES: frozenset[str] = frozenset({
    "adversarial", "collaborative", "exploratory", "evaluative", "comparative",
})

VALID_SEED_CONFIDENCE: frozenset[str] = frozenset({"normal", "low"})

VALID_SHAPE_CONFIDENCE: frozenset[str] = frozenset({"high", "medium", "low"})

VALID_CONVERGENCE_CODES: frozenset[str] = frozenset({
    "all_resolved", "natural_convergence", "budget_exhausted", "error", "scope_breach",
})

VALID_MODES: frozenset[str] = frozenset({"server_assisted", "manual_legacy"})

VALID_MODE_SOURCES: frozenset[str] = frozenset({"epilogue", "fallback"})

VALID_LOW_SEED_CONFIDENCE_REASONS: frozenset[str] = frozenset({
    "thin_citations", "few_files", "zero_output", "provenance_violations",
})

VALID_TERMINATION_REASONS: frozenset[str] = frozenset({
    "convergence", "budget", "error", "scope_breach", "complete",
})

VALID_CONSULTATION_SOURCES: frozenset[str] = frozenset({
    "codex",
    "dialogue",
    "reviewer",
})
"""Discriminator for consultation_outcome origin. Optional field — not
in required set to preserve backward compatibility with historical events."""

# ---------------------------------------------------------------------------
# Count fields (non-negative int validation)
# ---------------------------------------------------------------------------

COUNT_FIELDS: frozenset[str] = frozenset({
    "turn_count",
    "turn_budget",
    "resolved_count",
    "unresolved_count",
    "emerged_count",
    "assumption_count",
    "gatherer_a_lines",
    "gatherer_b_lines",
    "citations_total",
    "unique_files_total",
    "gatherer_a_unique_paths",
    "gatherer_b_unique_paths",
    "shared_citation_paths",
    "counter_count",
    "confirm_count",
    "open_count",
    "claim_count",
    "scout_count",
    "scope_root_count",
    "provenance_unknown_count",
    "assumptions_generated_count",
    "ambiguity_count",
})
