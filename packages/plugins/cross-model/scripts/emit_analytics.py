"""Deterministic analytics emitter for cross-model plugin.

Reads an input JSON file describing a dialogue or consultation outcome,
parses synthesis text (for dialogue outcomes), validates all fields,
and appends a single-line JSON event to the shared event log.

Usage:
    python3 emit_analytics.py <input_file.json>

Input JSON must contain:
- "event_type": "dialogue_outcome" or "consultation_outcome"
- "pipeline": dict of pipeline state fields
- "synthesis_text": full agent output (dialogue_outcome only)
- "scope_breach": bool (dialogue_outcome only)

Exit codes:
    0 — success (event appended)
    1 — error (bad input, validation failure, missing file)
    2 — degraded (validation ok, write failed)
"""

from __future__ import annotations

import json
import re
import sys
from typing import TypeGuard
import traceback
import uuid
from pathlib import Path

if __package__:
    from scripts.event_log import (
        ts as _ts,
        append_log as _append_log,
        session_id as _session_id,
    )
    from scripts.event_schema import (
        SCHEMA_VERSION as _SCHEMA_VERSION,
        resolve_schema_version as _resolve_schema_version,
        is_non_negative_int,
        valid_termination_reasons as _valid_termination_reasons,
        VALID_POSTURES as _VALID_POSTURES,
        VALID_SEED_CONFIDENCE as _VALID_SEED_CONFIDENCE,
        VALID_SHAPE_CONFIDENCE as _VALID_SHAPE_CONFIDENCE,
        VALID_CONVERGENCE_CODES as _VALID_CONVERGENCE_CODES,
        VALID_MODES as _VALID_MODES,
        VALID_MODE_SOURCES as _VALID_MODE_SOURCES,
        VALID_LOW_SEED_CONFIDENCE_REASONS as _VALID_LOW_SEED_CONFIDENCE_REASONS,
        VALID_TERMINATION_REASONS as _VALID_TERMINATION_REASONS,
        COUNT_FIELDS as _COUNT_FIELDS,
        REQUIRED_FIELDS_BY_EVENT,
    )
else:
    from event_log import ts as _ts, append_log as _append_log, session_id as _session_id  # type: ignore[import-not-found,no-redef]
    from event_schema import (  # type: ignore[import-not-found,no-redef]
        SCHEMA_VERSION as _SCHEMA_VERSION,
        resolve_schema_version as _resolve_schema_version,
        is_non_negative_int,
        valid_termination_reasons as _valid_termination_reasons,
        VALID_POSTURES as _VALID_POSTURES,
        VALID_SEED_CONFIDENCE as _VALID_SEED_CONFIDENCE,
        VALID_SHAPE_CONFIDENCE as _VALID_SHAPE_CONFIDENCE,
        VALID_CONVERGENCE_CODES as _VALID_CONVERGENCE_CODES,
        VALID_MODES as _VALID_MODES,
        VALID_MODE_SOURCES as _VALID_MODE_SOURCES,
        VALID_LOW_SEED_CONFIDENCE_REASONS as _VALID_LOW_SEED_CONFIDENCE_REASONS,
        VALID_TERMINATION_REASONS as _VALID_TERMINATION_REASONS,
        COUNT_FIELDS as _COUNT_FIELDS,
        REQUIRED_FIELDS_BY_EVENT,
    )

_DIALOGUE_REQUIRED = REQUIRED_FIELDS_BY_EVENT["dialogue_outcome"]
_CONSULTATION_REQUIRED = REQUIRED_FIELDS_BY_EVENT["consultation_outcome"]
_DELEGATION_REQUIRED = REQUIRED_FIELDS_BY_EVENT["delegation_outcome"]
_REQUIRED_MAP: dict[str, frozenset[str]] = {
    "dialogue_outcome": _DIALOGUE_REQUIRED,
    "consultation_outcome": _CONSULTATION_REQUIRED,
    "delegation_outcome": _DELEGATION_REQUIRED,
}


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------


def _strip_fenced_blocks(text: str) -> tuple[str, bool]:
    """Remove fenced code blocks to prevent parsing headers inside them.

    Returns (cleaned_text, truncated). truncated is True when an unclosed
    fence was detected and content after it was discarded.
    """
    # First pass: matched pairs
    text = re.sub(r"^```.*?^```", "", text, flags=re.MULTILINE | re.DOTALL)
    # Second pass: unclosed fence (opening ``` with no matching close) — strip to EOF.
    # This intentionally discards all content after the unclosed fence because
    # leaving it would create spurious section headers in _split_sections.
    before = text
    text = re.sub(r"^```.*", "", text, flags=re.MULTILINE | re.DOTALL)
    truncated = text != before
    if truncated:
        print(
            "_strip_fenced_blocks: unclosed fence detected, content after fence discarded",
            file=sys.stderr,
        )
    return text, truncated


def _split_sections(text: str) -> tuple[dict[str, str], bool]:
    """Split synthesis text into named sections using ## or ### headers.

    Returns (sections, truncated). sections maps lowercase section name
    to section content. truncated is True when an unclosed fence caused
    content loss during pre-processing.
    """
    cleaned, truncated = _strip_fenced_blocks(text)
    sections: dict[str, str] = {}
    pattern = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(cleaned))

    for i, match in enumerate(matches):
        name = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        sections[name] = cleaned[start:end]

    return sections, truncated


# ---------------------------------------------------------------------------
# Synthesis parser
# ---------------------------------------------------------------------------


def _parse_epilogue(synthesis_text: str) -> tuple[dict | None, list[str]]:
    """Parse the pipeline-data JSON epilogue from synthesis text.

    Accepts either of these layouts:
    1. Sentinel before the fenced JSON block
    2. Sentinel as the first line inside the fenced JSON block
    """
    sentinel = r"<!--\s*pipeline-data\s*-->"
    patterns = (
        re.compile(
            rf"```json[^\n]*\n\s*{sentinel}\s*(?P<body>.*?)```",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            rf"{sentinel}\s*```json[^\n]*\n\s*(?P<body>.*?)```",
            re.IGNORECASE | re.DOTALL,
        ),
    )

    for pattern in patterns:
        match = pattern.search(synthesis_text)
        if match is None:
            continue
        body = match.group("body").strip()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            return (None, [f"pipeline-data epilogue malformed: {exc.msg}"])
        if not isinstance(payload, dict):
            return (
                None,
                ["pipeline-data epilogue malformed: top-level JSON must be an object"],
            )
        return (payload, [])

    return (None, ["pipeline-data epilogue missing"])


def _has_usable_epilogue_data(payload: dict | None) -> TypeGuard[dict]:
    """Report whether parsed epilogue contains any usable machine fields."""
    if payload is None:
        return False

    keys_with_nullable_values = {"thread_id", "convergence_reason_code"}
    keys_with_non_null_values = {
        "turn_count",
        "converged",
        "scout_count",
        "resolved_count",
        "unresolved_count",
        "emerged_count",
        "mode",
        "scope_breach_count",
        "termination_reason",
    }

    if any(payload.get(key) is not None for key in keys_with_nullable_values):
        return True
    return any(key in payload for key in keys_with_non_null_values)


def _parse_markdown_synthesis(text: str) -> tuple[dict, bool]:
    """Extract legacy markdown heading fields from synthesis text."""
    sections, truncated = _split_sections(text)

    summary = sections.get("conversation summary", "")
    continuation = sections.get("continuation", "")

    # --- Counts from original text (not section-scoped) ---
    # Checkpoint content lives inside fenced code blocks in the agent
    # output, so searching the original text is correct here.
    resolved_matches = re.findall(r"^RESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    unresolved_matches = re.findall(r"^UNRESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    emerged_matches = re.findall(r"^EMERGED:", text, re.MULTILINE | re.IGNORECASE)
    resolved_count = len(resolved_matches)
    unresolved_count = len(unresolved_matches)
    emerged_count = len(emerged_matches)

    # --- Converged from Summary (tolerant) ---
    converged = False
    converged_match = re.search(r"\*\*Converged:\*\*\s*(.+)", summary, re.IGNORECASE)
    if converged_match:
        converged = converged_match.group(1).strip().lower().startswith("yes")

    # --- Turn count from Summary (handles "X of Y" and "X/Y") ---
    turn_count = 0
    turn_match = re.search(r"\*\*Turns:\*\*\s*(\d+)", summary, re.IGNORECASE)
    if turn_match:
        turn_count = int(turn_match.group(1))

    # --- Thread ID from Continuation (strips backticks) ---
    thread_id = None
    thread_match = re.search(r"\*\*Thread ID:\*\*\s*(.+)", continuation, re.IGNORECASE)
    if thread_match:
        value = thread_match.group(1).strip().strip("`")
        if value.lower() != "none":
            thread_id = value

    # --- Scout count from Summary Evidence (NOT Continuation) ---
    # Summary format: "**Evidence:** X scouts / Y turns, ..."
    # Continuation uses "**Evidence trajectory:**" — different field
    scout_count = 0
    scout_match = re.search(
        r"\*\*Evidence:\*\*\s*(\d+)\s+scouts?", summary, re.IGNORECASE
    )
    if scout_match:
        scout_count = int(scout_match.group(1))

    usable = any(
        (
            bool(resolved_matches),
            bool(unresolved_matches),
            bool(emerged_matches),
            converged_match is not None,
            turn_match is not None,
            thread_match is not None,
            scout_match is not None,
        )
    )

    return (
        {
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "emerged_count": emerged_count,
            "converged": converged,
            "turn_count": turn_count,
            "thread_id": thread_id,
            "scout_count": scout_count,
            "mode": None,
            "convergence_reason_code": None,
            "scope_breach_count": 0,
            "termination_reason": None,
            "parse_truncated": truncated,
        },
        usable,
    )


def parse_synthesis(text: str) -> dict:
    """Extract structured fields from codex-dialogue agent output.

    Splits text into sections for Summary/Continuation fields.
    Checkpoint prefixes (RESOLVED/UNRESOLVED/EMERGED) are searched in
    the original text since they appear inside fenced code blocks that
    get stripped during section splitting.

    Returns dict with keys: resolved_count, unresolved_count,
    emerged_count, converged, turn_count, thread_id, scout_count.
    Defaults on parse failure:
    - counts: 0
    - strings: None
    - booleans: False
    """
    payload, warnings = _parse_epilogue(text)
    markdown_data, markdown_usable = _parse_markdown_synthesis(text)

    if _has_usable_epilogue_data(payload):
        return {
            "resolved_count": payload.get("resolved_count", 0),
            "unresolved_count": payload.get("unresolved_count", 0),
            "emerged_count": payload.get("emerged_count", 0),
            "converged": payload.get("converged", False),
            "turn_count": payload.get("turn_count", 0),
            "thread_id": payload.get("thread_id"),
            "scout_count": payload.get("scout_count", 0),
            "mode": payload.get("mode"),
            "convergence_reason_code": payload.get("convergence_reason_code"),
            "scope_breach_count": payload.get("scope_breach_count", 0),
            "termination_reason": payload.get("termination_reason"),
            "parse_truncated": markdown_data["parse_truncated"],
            "parse_failed": False,
        }

    if warnings:
        print(
            "epilogue missing or malformed, falling back to markdown parsing",
            file=sys.stderr,
        )

    markdown_data["parse_failed"] = not markdown_usable
    return markdown_data


# ---------------------------------------------------------------------------
# Convergence mapper
# ---------------------------------------------------------------------------


def map_convergence(
    converged: bool,
    unresolved_count: int,
    turn_count: int,
    turn_budget: int,
    scope_breach: bool = False,
) -> tuple[str, str]:
    """Map dialogue state to (convergence_reason_code, termination_reason).

    Priority order: scope_breach > all_resolved > natural > budget > error.

    The error fallback covers any state where ``converged=False`` and
    ``turn_count < turn_budget``. This includes the contradictory case
    (zero unresolved items but not converged) and the unexpected case
    (unresolved items remain but budget was not exhausted). Either
    indicates a pipeline or state tracking bug.
    """
    if scope_breach:
        return ("scope_breach", "scope_breach")
    if converged and unresolved_count == 0:
        return ("all_resolved", "convergence")
    if converged and unresolved_count > 0:
        return ("natural_convergence", "convergence")
    if not converged and turn_count >= turn_budget:
        return ("budget_exhausted", "budget")
    print(
        f"map_convergence reached error fallback: converged={converged}, "
        f"unresolved_count={unresolved_count}, turn_count={turn_count}, "
        f"turn_budget={turn_budget}",
        file=sys.stderr,
    )
    return ("error", "error")


# ---------------------------------------------------------------------------
# Event builders
# ---------------------------------------------------------------------------


def build_dialogue_outcome(input_data: dict) -> dict:
    """Build a dialogue_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})
    synthesis_text = input_data.get("synthesis_text", "")
    scope_breach = input_data.get("scope_breach", False)

    parsed = parse_synthesis(synthesis_text)
    parse_degraded = parsed.get("parse_failed", False)
    if parse_degraded:
        print(
            "synthesis parse failed: epilogue and markdown parsing yielded no usable data; "
            "emitting degraded event with defaults",
            file=sys.stderr,
        )

    turn_budget = pipeline.get("turn_budget", 1)
    scope_breach = scope_breach or parsed.get("scope_breach_count", 0) > 0
    scope_breach = scope_breach or parsed.get("termination_reason") == "scope_breach"
    scope_breach = scope_breach or parsed.get("convergence_reason_code") == "scope_breach"

    if parse_degraded:
        code, reason = ("error", "error")
    else:
        code, reason = map_convergence(
            converged=parsed["converged"],
            unresolved_count=parsed["unresolved_count"],
            turn_count=parsed["turn_count"],
            turn_budget=turn_budget,
            scope_breach=scope_breach,
        )

    # Validate epilogue enum values — invalid values fall through to computed defaults.
    # The agent template may produce values from the wrong enum (e.g. "convergence"
    # is valid for termination_reason but not convergence_reason_code).
    epilogue_code = parsed.get("convergence_reason_code")
    if epilogue_code is not None and epilogue_code not in _VALID_CONVERGENCE_CODES:
        print(
            f"invalid epilogue convergence_reason_code {epilogue_code!r}, "
            f"using computed value {code!r}",
            file=sys.stderr,
        )
        epilogue_code = None

    epilogue_reason = parsed.get("termination_reason")
    if epilogue_reason is not None and epilogue_reason not in _VALID_TERMINATION_REASONS:
        print(
            f"invalid epilogue termination_reason {epilogue_reason!r}, "
            f"using computed value {reason!r}",
            file=sys.stderr,
        )
        epilogue_reason = None

    event = {
        # Core
        "schema_version": _SCHEMA_VERSION,
        "consultation_id": str(uuid.uuid4()),
        "thread_id": parsed["thread_id"],
        "session_id": _session_id(),
        "event": "dialogue_outcome",
        "ts": _ts(),
        # Dialogue parameters
        "posture": pipeline.get("posture"),
        "turn_count": parsed["turn_count"],
        "turn_budget": turn_budget,
        "profile_name": pipeline.get("profile_name"),
        "mode": parsed.get("mode") or pipeline.get("mode", "server_assisted"),
        "mode_source": pipeline.get("mode_source"),
        # Outcome
        "converged": parsed["converged"],
        "convergence_reason_code": epilogue_code or code,
        "termination_reason": epilogue_reason or reason,
        "resolved_count": parsed["resolved_count"],
        "unresolved_count": parsed["unresolved_count"],
        "emerged_count": parsed["emerged_count"],
        "parse_degraded": parse_degraded,
        # Context quality
        "seed_confidence": pipeline.get("seed_confidence", "normal"),
        "low_seed_confidence_reasons": pipeline.get("low_seed_confidence_reasons", []),
        "assumption_count": pipeline.get("assumption_count", 0),
        "no_assumptions_fallback": pipeline.get("no_assumptions_fallback", False),
        # Gatherer metrics
        "gatherer_a_lines": pipeline.get("gatherer_a_lines", 0),
        "gatherer_b_lines": pipeline.get("gatherer_b_lines", 0),
        "gatherer_a_retry": pipeline.get("gatherer_a_retry", False),
        "gatherer_b_retry": pipeline.get("gatherer_b_retry", False),
        "citations_total": pipeline.get("citations_total", 0),
        "unique_files_total": pipeline.get("unique_files_total", 0),
        "gatherer_a_unique_paths": pipeline.get("gatherer_a_unique_paths", 0),
        "gatherer_b_unique_paths": pipeline.get("gatherer_b_unique_paths", 0),
        "shared_citation_paths": pipeline.get("shared_citation_paths", 0),
        "counter_count": pipeline.get("counter_count", 0),
        "confirm_count": pipeline.get("confirm_count", 0),
        "open_count": pipeline.get("open_count", 0),
        "claim_count": pipeline.get("claim_count", 0),
        # Scouting
        "scout_count": parsed["scout_count"],
        # Scope envelope
        "source_classes": pipeline.get("source_classes", []),
        "scope_root_count": pipeline.get("scope_root_count", 0),
        "scope_roots_fingerprint": pipeline.get("scope_roots_fingerprint"),
        # Planning (nullable — populated when --plan is used)
        "question_shaped": pipeline.get("question_shaped"),
        "shape_confidence": pipeline.get("shape_confidence"),
        "assumptions_generated_count": pipeline.get("assumptions_generated_count"),
        "ambiguity_count": pipeline.get("ambiguity_count"),
        # Provenance (nullable)
        "provenance_unknown_count": pipeline.get("provenance_unknown_count"),
        # Episode linkage: reserved nullable. Not populated at emit time.
        # E-LEARNING will use append-only episode_link events for post-hoc
        # linkage via consultation_id. Do not add to _DIALOGUE_REQUIRED.
        "episode_id": None,
        # Parse diagnostics: True when unclosed fence caused content loss
        "parse_truncated": parsed["parse_truncated"],
    }

    # Schema version auto-bump (§4.4): unified resolver
    event["schema_version"] = _resolve_schema_version(event)

    return event


def build_consultation_outcome(input_data: dict) -> dict:
    """Build a consultation_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})

    event = {
        "schema_version": _SCHEMA_VERSION,  # placeholder; resolved below
        "consultation_id": str(uuid.uuid4()),
        "thread_id": pipeline.get("thread_id"),
        "session_id": _session_id(),
        "event": "consultation_outcome",
        "ts": _ts(),
        "posture": pipeline.get("posture"),
        "turn_count": pipeline.get("turn_count", 1),
        "turn_budget": pipeline.get("turn_budget", 1),
        "profile_name": pipeline.get("profile_name"),
        "mode": pipeline.get("mode", "server_assisted"),
        "converged": None,
        "termination_reason": pipeline.get("termination_reason", "complete"),
        "consultation_source": pipeline.get("consultation_source", "codex"),
        # Nullable feature-flag fields (propagated from pipeline when present)
        "provenance_unknown_count": pipeline.get("provenance_unknown_count"),
        "question_shaped": pipeline.get("question_shaped"),
        "shape_confidence": pipeline.get("shape_confidence"),
        "assumptions_generated_count": pipeline.get("assumptions_generated_count"),
        "ambiguity_count": pipeline.get("ambiguity_count"),
    }

    # Schema version auto-bump: unified resolver (same as build_dialogue_outcome)
    event["schema_version"] = _resolve_schema_version(event)

    return event


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(event: dict, event_type: str) -> None:
    """Validate event fields. Raises ValueError on failure."""
    required = _REQUIRED_MAP.get(event_type)
    if required is None:
        raise ValueError(f"unknown event_type: {event_type!r}")

    # Required fields
    missing = required - set(event.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")

    # Event type
    if event.get("event") != event_type:
        raise ValueError(
            f"event field mismatch: expected {event_type!r}, got {event.get('event')!r}"
        )

    # Termination reason — per-event-type dispatch
    valid_reasons = _valid_termination_reasons(event_type)
    reason = event.get("termination_reason")
    if reason is None:
        raise ValueError("termination_reason is required")
    if not isinstance(reason, str) or reason not in valid_reasons:
        raise ValueError(f"invalid termination_reason: {reason!r}")

    # Count fields >= 0
    for field in _COUNT_FIELDS:
        value = event.get(field)
        if value is not None and not is_non_negative_int(value):
            raise ValueError(f"{field} must be non-negative int, got {value!r}")

    # Cross-field: schema_version must match feature-flag state
    expected_version = _resolve_schema_version(event)
    actual_version = event.get("schema_version")
    if actual_version != expected_version:
        raise ValueError(
            f"schema_version mismatch: expected {expected_version!r} "
            f"(from feature flags), got {actual_version!r}"
        )

    # --- Dialogue/consultation-specific validation (not applicable to delegation) ---
    if event_type != "delegation_outcome":
        # Enum checks — each uses isinstance(str) guard before set membership
        # to prevent TypeError on non-hashable values (dicts, lists from JSON).
        posture = event.get("posture")
        if posture is None:
            raise ValueError("posture is required")
        if not isinstance(posture, str) or posture not in _VALID_POSTURES:
            raise ValueError(f"invalid posture: {posture!r}")

        code = event.get("convergence_reason_code")
        if event_type == "dialogue_outcome" and code is None:
            raise ValueError("convergence_reason_code required for dialogue_outcome")
        if code is not None and (
            not isinstance(code, str) or code not in _VALID_CONVERGENCE_CODES
        ):
            raise ValueError(f"invalid convergence_reason_code: {code!r}")

        seed = event.get("seed_confidence")
        if event_type == "dialogue_outcome" and seed is None:
            raise ValueError("seed_confidence required for dialogue_outcome")
        if seed is not None and (
            not isinstance(seed, str) or seed not in _VALID_SEED_CONFIDENCE
        ):
            raise ValueError(f"invalid seed_confidence: {seed!r}")

        mode = event.get("mode")
        if mode is None:
            raise ValueError("mode is required")
        if not isinstance(mode, str) or mode not in _VALID_MODES:
            raise ValueError(f"invalid mode: {mode!r}")

        # mode_source enum (dialogue_outcome only, nullable; rejected on other event types)
        ms = event.get("mode_source")
        if event_type == "dialogue_outcome":
            if ms is not None:
                if not isinstance(ms, str) or ms not in _VALID_MODE_SOURCES:
                    raise ValueError(f"invalid mode_source: {ms!r}")
        elif "mode_source" in event:
            raise ValueError(f"mode_source must not be present on {event_type}, got {ms!r}")

        # Tri-state planning invariant: question_shaped drives field requirements
        qs = event.get("question_shaped")
        if qs is not None:
            if not isinstance(qs, bool):
                raise ValueError(
                    f"question_shaped must be bool or None, got {type(qs).__name__}"
                )
            # Forward: when question_shaped is set (true or false), remaining planning
            # fields must be non-None (failure telemetry is preserved even on false)
            for pf in (
                "shape_confidence",
                "assumptions_generated_count",
                "ambiguity_count",
            ):
                if event.get(pf) is None:
                    raise ValueError(
                        f"{pf} is required when question_shaped is set (got None)"
                    )
        else:
            # Reverse: when question_shaped is None (--plan not used or debug gate
            # skip), all companion fields must also be None
            for pf in (
                "shape_confidence",
                "assumptions_generated_count",
                "ambiguity_count",
            ):
                if event.get(pf) is not None:
                    raise ValueError(
                        f"{pf} must be None when question_shaped is None "
                        f"(got {event.get(pf)!r})"
                    )

        # Validate shape_confidence enum values when non-null
        sc = event.get("shape_confidence")
        if sc is not None and (
            not isinstance(sc, str) or sc not in _VALID_SHAPE_CONFIDENCE
        ):
            raise ValueError(f"invalid shape_confidence: {sc!r}")

        # Cross-field invariants
        turn_budget = event.get("turn_budget")
        if (
            turn_budget is None
            or isinstance(turn_budget, bool)
            or not isinstance(turn_budget, int)
        ):
            raise ValueError(f"turn_budget must be a positive int, got {turn_budget!r}")
        if turn_budget < 1:
            raise ValueError(f"turn_budget must be >= 1, got {turn_budget}")

        turn_count = event.get("turn_count", 0)
        if (
            event_type == "dialogue_outcome"
            and event.get("termination_reason") != "error"
            and turn_count > turn_budget
        ):
            raise ValueError(f"turn_count ({turn_count}) > turn_budget ({turn_budget})")

        # Type checks
        converged = event.get("converged")
        if converged is not None and not isinstance(converged, bool):
            raise ValueError(
                f"converged must be bool or None, got {type(converged).__name__}"
            )

        source_classes = event.get("source_classes")
        if source_classes is not None:
            if not isinstance(source_classes, list):
                raise ValueError("source_classes must be a list")
            if not all(isinstance(s, str) for s in source_classes):
                raise ValueError("source_classes must contain only strings")

        low_reasons = event.get("low_seed_confidence_reasons")
        if low_reasons is not None:
            if not isinstance(low_reasons, list):
                raise ValueError("low_seed_confidence_reasons must be a list")
            if not all(isinstance(s, str) for s in low_reasons):
                raise ValueError("low_seed_confidence_reasons must contain only strings")
            invalid = set(low_reasons) - _VALID_LOW_SEED_CONFIDENCE_REASONS
            if invalid:
                raise ValueError(
                    f"invalid low_seed_confidence_reasons values: {sorted(invalid)}"
                )

    # --- Delegation-specific cross-field invariants ---
    if event_type == "delegation_outcome":
        dispatched = event.get("dispatched")
        tr = event.get("termination_reason")
        exit_code = event.get("exit_code")
        cmd_count = event.get("commands_run_count", 0)
        block_flags = (
            event.get("credential_blocked"),
            event.get("dirty_tree_blocked"),
            event.get("readable_secret_file_blocked"),
        )

        if tr == "complete" and dispatched is not True:
            raise ValueError("complete requires dispatched=True")
        if tr == "blocked" and dispatched is not False:
            raise ValueError("blocked requires dispatched=False")
        if tr == "blocked" and not any(block_flags):
            raise ValueError("blocked requires at least one block flag set")
        if isinstance(cmd_count, int) and cmd_count > 0 and dispatched is not True:
            raise ValueError("commands_run_count > 0 requires dispatched=True")
        if exit_code is not None and dispatched is not True:
            raise ValueError("exit_code requires dispatched=True")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _result(status: str, reason: str | None = None) -> str:
    """Format a status result as JSON."""
    d: dict = {"status": status}
    if reason is not None:
        d["reason"] = reason
    return json.dumps(d)


def _process(input_path: Path) -> int:
    """Process input file and emit event. Returns exit code."""
    try:
        input_data = json.loads(input_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(_result("error", f"input read failed: {exc}"))
        return 1

    event_type = input_data.get("event_type")

    # Build phase — KeyError/TypeError likely indicate bugs or bad input structure
    try:
        if event_type == "dialogue_outcome":
            event = build_dialogue_outcome(input_data)
        elif event_type == "consultation_outcome":
            event = build_consultation_outcome(input_data)
        else:
            print(_result("error", f"unknown event_type: {event_type!r}"))
            return 1
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        print(traceback.format_exc(), file=sys.stderr)
        print(_result("error", f"build failed: {exc}"))
        return 1

    # Validation phase — ValueError is expected for invalid field values
    try:
        validate(event, event_type)
    except ValueError as exc:
        print(_result("error", str(exc)))
        return 1

    # Append to log (best-effort)
    logged = _append_log(event)

    if not logged:
        print(_result("degraded", "event valid but log write failed"))
        return 2

    print(_result("ok"))
    return 0


def main() -> int:
    """Entry point. Returns exit code."""
    if len(sys.argv) < 2:
        print(_result("error", "usage: emit_analytics.py <input_file.json>"))
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(_result("error", f"input file not found: {input_path}"))
        return 1

    try:
        return _process(input_path)
    finally:
        try:
            input_path.unlink()
        except OSError as exc:
            print(f"input cleanup failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
