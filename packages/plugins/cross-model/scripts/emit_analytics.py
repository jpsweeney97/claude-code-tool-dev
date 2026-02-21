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
import os
import re
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOG_PATH = Path.home() / ".claude" / ".codex-events.jsonl"
_SCHEMA_VERSION = "0.1.0"

_VALID_POSTURES = {"adversarial", "collaborative", "exploratory", "evaluative"}
_VALID_SEED_CONFIDENCE = {"normal", "low"}
_VALID_SHAPE_CONFIDENCE = {"high", "medium", "low"}
_VALID_CONVERGENCE_CODES = {
    "all_resolved",
    "natural_convergence",
    "budget_exhausted",
    "error",
    "scope_breach",
}
_VALID_MODES = {"server_assisted", "manual_legacy"}
_VALID_LOW_SEED_CONFIDENCE_REASONS = {
    "thin_citations",
    "few_files",
    "zero_output",
    "provenance_violations",
}
_VALID_TERMINATION_REASONS = {
    "convergence",
    "budget",
    "error",
    "scope_breach",
    "complete",
}


def _is_non_negative_int(value: object) -> bool:
    """Check value is a non-negative int, excluding bool."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _resolve_schema_version(event: dict) -> str:
    """Determine schema version from feature-flag fields.

    Precedence: planning (0.3.0) > provenance (0.2.0) > base (0.1.0).
    Used in both build (auto-set) and validate (exact equality check).
    """
    if event.get("question_shaped") is not None:
        return "0.3.0"
    if _is_non_negative_int(event.get("provenance_unknown_count")):
        return "0.2.0"
    return _SCHEMA_VERSION


_COUNT_FIELDS = {
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
}

_DIALOGUE_REQUIRED = {
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
}

_CONSULTATION_REQUIRED = {
    "schema_version",
    "consultation_id",
    "event",
    "ts",
    "posture",
    "turn_count",
    "turn_budget",
    "termination_reason",
    "mode",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _ts() -> str:
    """ISO 8601 UTC timestamp with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_log(entry: dict) -> bool:
    """Append a JSON line to the event log. Returns True on success."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except (OSError, TypeError) as exc:
        print(f"log write failed: {exc}", file=sys.stderr)
        return False


def _session_id() -> str | None:
    """Read session ID from environment. Never fabricated.

    Returns None if CLAUDE_SESSION_ID is absent, empty, or whitespace-only.
    """
    value = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    return value or None


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------


def _strip_fenced_blocks(text: str) -> str:
    """Remove fenced code blocks to prevent parsing headers inside them."""
    # First pass: matched pairs
    text = re.sub(r"^```.*?^```", "", text, flags=re.MULTILINE | re.DOTALL)
    # Second pass: unclosed fence (opening ``` with no matching close) — strip to EOF.
    # This intentionally discards all content after the unclosed fence because
    # leaving it would create spurious section headers in _split_sections.
    before = text
    text = re.sub(r"^```.*", "", text, flags=re.MULTILINE | re.DOTALL)
    if text != before:
        print("_strip_fenced_blocks: unclosed fence detected, content after fence discarded", file=sys.stderr)
    return text


def _split_sections(text: str) -> dict[str, str]:
    """Split synthesis text into named sections using ## or ### headers.

    Returns a dict mapping lowercase section name to section content.
    Strips fenced code blocks first to prevent matching headers inside them.
    """
    cleaned = _strip_fenced_blocks(text)
    sections: dict[str, str] = {}
    pattern = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(cleaned))

    for i, match in enumerate(matches):
        name = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        sections[name] = cleaned[start:end]

    return sections


# ---------------------------------------------------------------------------
# Synthesis parser
# ---------------------------------------------------------------------------


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
    sections = _split_sections(text)

    summary = sections.get("conversation summary", "")
    continuation = sections.get("continuation", "")

    # --- Counts from original text (not section-scoped) ---
    # Checkpoint content lives inside fenced code blocks in the agent
    # output, so searching the original text is correct here.
    resolved_count = len(
        re.findall(r"^RESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    )
    unresolved_count = len(
        re.findall(r"^UNRESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    )
    emerged_count = len(
        re.findall(r"^EMERGED:", text, re.MULTILINE | re.IGNORECASE)
    )

    # --- Converged from Summary (tolerant) ---
    converged = False
    m = re.search(r"\*\*Converged:\*\*\s*(.+)", summary, re.IGNORECASE)
    if m:
        converged = m.group(1).strip().lower().startswith("yes")

    # --- Turn count from Summary (handles "X of Y" and "X/Y") ---
    turn_count = 0
    m = re.search(r"\*\*Turns:\*\*\s*(\d+)", summary, re.IGNORECASE)
    if m:
        turn_count = int(m.group(1))

    # --- Thread ID from Continuation (strips backticks) ---
    thread_id = None
    m = re.search(r"\*\*Thread ID:\*\*\s*(.+)", continuation, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip("`")
        if value.lower() != "none":
            thread_id = value

    # --- Scout count from Summary Evidence (NOT Continuation) ---
    # Summary format: "**Evidence:** X scouts / Y turns, ..."
    # Continuation uses "**Evidence trajectory:**" — different field
    scout_count = 0
    m = re.search(r"\*\*Evidence:\*\*\s*(\d+)\s+scouts?", summary, re.IGNORECASE)
    if m:
        scout_count = int(m.group(1))

    return {
        "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "emerged_count": emerged_count,
        "converged": converged,
        "turn_count": turn_count,
        "thread_id": thread_id,
        "scout_count": scout_count,
    }


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

    turn_budget = pipeline.get("turn_budget", 1)
    code, reason = map_convergence(
        converged=parsed["converged"],
        unresolved_count=parsed["unresolved_count"],
        turn_count=parsed["turn_count"],
        turn_budget=turn_budget,
        scope_breach=scope_breach,
    )

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
        "mode": pipeline.get("mode", "server_assisted"),
        # Outcome
        "converged": parsed["converged"],
        "convergence_reason_code": code,
        "termination_reason": reason,
        "resolved_count": parsed["resolved_count"],
        "unresolved_count": parsed["unresolved_count"],
        "emerged_count": parsed["emerged_count"],
        # Context quality
        "seed_confidence": pipeline.get("seed_confidence", "normal"),
        "low_seed_confidence_reasons": pipeline.get(
            "low_seed_confidence_reasons", []
        ),
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
        # Linkage (nullable)
        "episode_id": None,
    }

    # Schema version auto-bump (§4.4): unified resolver
    event["schema_version"] = _resolve_schema_version(event)

    return event


def build_consultation_outcome(input_data: dict) -> dict:
    """Build a consultation_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})

    # Consultation events use base schema (0.1.0) unconditionally.
    # If provenance or planning fields are added to consultations,
    # this must call _resolve_schema_version() like build_dialogue_outcome.
    return {
        "schema_version": _SCHEMA_VERSION,
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
        "termination_reason": "complete",
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(event: dict, event_type: str) -> None:
    """Validate event fields. Raises ValueError on failure."""
    required = (
        _DIALOGUE_REQUIRED
        if event_type == "dialogue_outcome"
        else _CONSULTATION_REQUIRED
    )

    # Required fields
    missing = required - set(event.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")

    # Event type
    if event.get("event") != event_type:
        raise ValueError(
            f"event field mismatch: expected {event_type!r}, "
            f"got {event.get('event')!r}"
        )

    # Enum checks
    posture = event.get("posture")
    if posture is None:
        raise ValueError("posture is required")
    if posture not in _VALID_POSTURES:
        raise ValueError(f"invalid posture: {posture!r}")

    code = event.get("convergence_reason_code")
    if event_type == "dialogue_outcome" and code is None:
        raise ValueError("convergence_reason_code required for dialogue_outcome")
    if code is not None and code not in _VALID_CONVERGENCE_CODES:
        raise ValueError(f"invalid convergence_reason_code: {code!r}")

    reason = event.get("termination_reason")
    if reason is None:
        raise ValueError("termination_reason is required")
    if reason not in _VALID_TERMINATION_REASONS:
        raise ValueError(f"invalid termination_reason: {reason!r}")

    seed = event.get("seed_confidence")
    if event_type == "dialogue_outcome" and seed is None:
        raise ValueError("seed_confidence required for dialogue_outcome")
    if seed is not None and seed not in _VALID_SEED_CONFIDENCE:
        raise ValueError(f"invalid seed_confidence: {seed!r}")

    mode = event.get("mode")
    if mode is None:
        raise ValueError("mode is required")
    if mode not in _VALID_MODES:
        raise ValueError(f"invalid mode: {mode!r}")

    # Tri-state planning invariant: question_shaped drives field requirements
    qs = event.get("question_shaped")
    if qs is not None:
        if not isinstance(qs, bool):
            raise ValueError(
                f"question_shaped must be bool or None, got {type(qs).__name__}"
            )
        # Forward: when question_shaped is set (true or false), remaining planning
        # fields must be non-None (failure telemetry is preserved even on false)
        for pf in ("shape_confidence", "assumptions_generated_count", "ambiguity_count"):
            if event.get(pf) is None:
                raise ValueError(
                    f"{pf} is required when question_shaped is set (got None)"
                )
    else:
        # Reverse: when question_shaped is None (--plan not used or debug gate
        # skip), all companion fields must also be None
        for pf in ("shape_confidence", "assumptions_generated_count", "ambiguity_count"):
            if event.get(pf) is not None:
                raise ValueError(
                    f"{pf} must be None when question_shaped is None "
                    f"(got {event.get(pf)!r})"
                )

    # Validate shape_confidence enum values when non-null
    sc = event.get("shape_confidence")
    if sc is not None and sc not in _VALID_SHAPE_CONFIDENCE:
        raise ValueError(f"invalid shape_confidence: {sc!r}")

    # Count fields >= 0
    for field in _COUNT_FIELDS:
        value = event.get(field)
        if value is not None and not _is_non_negative_int(value):
            raise ValueError(f"{field} must be non-negative int, got {value!r}")

    # Cross-field: schema_version must match feature-flag state
    expected_version = _resolve_schema_version(event)
    actual_version = event.get("schema_version")
    if actual_version != expected_version:
        raise ValueError(
            f"schema_version mismatch: expected {expected_version!r} "
            f"(from feature flags), got {actual_version!r}"
        )

    # Cross-field invariants
    turn_budget = event.get("turn_budget")
    if turn_budget is None or isinstance(turn_budget, bool) or not isinstance(turn_budget, int):
        raise ValueError(f"turn_budget must be a positive int, got {turn_budget!r}")
    if turn_budget < 1:
        raise ValueError(f"turn_budget must be >= 1, got {turn_budget}")

    turn_count = event.get("turn_count", 0)
    if (
        event_type == "dialogue_outcome"
        and event.get("termination_reason") != "error"
        and turn_count > turn_budget
    ):
        raise ValueError(
            f"turn_count ({turn_count}) > turn_budget ({turn_budget})"
        )

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
    except (KeyError, TypeError, AttributeError) as exc:
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
