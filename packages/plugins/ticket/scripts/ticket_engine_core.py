"""Ticket engine core — classify | plan | preflight | execute pipeline.

All mutation and policy-enforcement logic lives here. Entrypoints
(ticket_engine_user.py, ticket_engine_agent.py) set request_origin
and delegate to this module.

Subcommand contract: each function returns an EngineResponse with
{state, ticket_id, message, data}.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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


# Sentinel for audit read failures.
AUDIT_UNAVAILABLE = object()


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


# --- plan ---

# Required fields for create.
_CREATE_REQUIRED = ("title", "problem", "priority")

# Dedup window.
_DEDUP_WINDOW_HOURS = 24


def engine_plan(
    *,
    intent: str,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage: validate fields and check for duplicates (create only).

    For create: validates required fields, computes dedup fingerprint,
    scans for duplicates within 24h window.
    For other intents: passes through (plan is create-specific).
    """
    if intent == "create":
        return _plan_create(fields, session_id, request_origin, tickets_dir)

    # Non-create: plan is a pass-through.
    return EngineResponse(
        state="ok",
        message=f"Plan pass-through for {intent}",
        data={
            "dedup_fingerprint": None,
            "target_fingerprint": None,
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": intent},
        },
    )


def _plan_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage for create: field validation + dedup."""
    from scripts.ticket_dedup import dedup_fingerprint
    from scripts.ticket_read import list_tickets

    # Check required fields.
    missing = [f for f in _CREATE_REQUIRED if not fields.get(f)]
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields: {', '.join(missing)}",
            error_code="need_fields",
            data={"missing_fields": missing},
        )

    # Compute dedup fingerprint.
    problem_text = fields["problem"]
    key_file_paths = fields.get("key_file_paths", [])
    fp = dedup_fingerprint(problem_text, key_file_paths)

    # Scan for duplicates within 24h window.
    duplicate_of = None
    dup_target_fp = None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=_DEDUP_WINDOW_HOURS)

    existing = list_tickets(tickets_dir)
    for ticket in existing:
        # Check if ticket is within dedup window.
        try:
            ticket_date = datetime.strptime(ticket.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if ticket_date < cutoff:
            continue

        # Compute fingerprint for this ticket's problem text.
        ticket_problem = ticket.sections.get("Problem", "")
        ticket_key_file_paths: list[str] = []
        # Extract file paths from Key Files section if present.
        key_files_section = ticket.sections.get("Key Files", "")
        if key_files_section:
            for match in re.finditer(r"^\| ([^|]+) \|", key_files_section, re.MULTILINE):
                cell = match.group(1).strip()
                if cell and cell != "File" and not cell.startswith("-"):
                    ticket_key_file_paths.append(cell)

        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_file_paths)
        if existing_fp == fp:
            from scripts.ticket_dedup import target_fingerprint

            duplicate_of = ticket.id
            dup_target_fp = target_fingerprint(Path(ticket.path))
            break

    if duplicate_of:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Potential duplicate of {duplicate_of}",
            ticket_id=duplicate_of,
            error_code="duplicate_candidate",
            data={
                "dedup_fingerprint": fp,
                "target_fingerprint": dup_target_fp,
                "duplicate_of": duplicate_of,
                "missing_fields": [],
                "action_plan": {"intent": "create", "duplicate_candidate": True},
            },
        )

    return EngineResponse(
        state="ok",
        message="Plan complete, no duplicates found",
        data={
            "dedup_fingerprint": fp,
            "target_fingerprint": None,
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": "create"},
        },
    )


# --- preflight ---

# Confidence thresholds (provisional — calibrate pre-GA).
_T_BASE = 0.5
_ORIGIN_MODIFIER: dict[str, float] = {"user": 0.0, "agent": 0.15}

# Terminal statuses for dependency resolution.
_TERMINAL_STATUSES = frozenset({"done", "wontfix"})


def _read_autonomy_mode(tickets_dir: Path) -> str:
    """Read autonomy mode from .claude/ticket.local.md.

    Returns 'suggest' as default if file missing or malformed.
    """
    # Walk up from tickets_dir to find project root.
    project_root = tickets_dir
    while project_root != project_root.parent:
        if (project_root / ".claude").is_dir():
            break
        project_root = project_root.parent

    config_path = project_root / ".claude" / "ticket.local.md"
    if not config_path.is_file():
        return "suggest"

    try:
        import yaml

        text = config_path.read_text(encoding="utf-8")
        # Parse YAML frontmatter (--- delimited).
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1])
                if isinstance(data, dict):
                    mode = data.get("autonomy_mode", "suggest")
                    if mode in ("suggest", "auto_audit", "auto_silent"):
                        return mode
    except Exception:
        pass

    return "suggest"


def engine_preflight(
    *,
    ticket_id: str | None,
    action: str,
    session_id: str,
    request_origin: str,
    classify_confidence: float,
    classify_intent: str,
    dedup_fingerprint: str | None,
    target_fingerprint: str | None,
    duplicate_of: str | None = None,
    dedup_override: bool = False,
    dependency_override: bool = False,
    tickets_dir: Path,
) -> EngineResponse:
    """Preflight: single enforcement point for all mutating operations.

    Checks in order: origin, action, agent policy, confidence, intent match,
    dedup, ticket existence, dependency integrity, TOCTOU fingerprint.
    """
    checks_passed: list[str] = []
    checks_failed: list[dict[str, str]] = []

    # --- Origin check ---
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
            error_code="origin_mismatch",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "origin", "reason": "unknown origin"}],
            },
        )
    checks_passed.append("origin")

    # --- Action validation (Codex finding 3: defense-in-depth) ---
    if action not in VALID_ACTIONS:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
            error_code="intent_mismatch",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "action", "reason": "unknown action"}],
            },
        )
    checks_passed.append("action")

    # --- Agent policy: Phase 1 strict fail-closed (Codex finding 5: before confidence) ---
    # Moved before confidence gate so all agent requests get policy_blocked,
    # not a misleading preflight_failed for coincidental confidence issues.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Agent mutations are hard-blocked in Phase 1. "
            "The PreToolUse hook (Phase 2) is required for legitimate agent invocations.",
            error_code="policy_blocked",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "agent_phase1_block", "reason": "Phase 1 fail-closed policy"}],
            },
        )
    checks_passed.append("autonomy_policy")

    # --- Confidence gate ---
    modifier = _ORIGIN_MODIFIER.get(request_origin, 0.0)
    threshold = _T_BASE + modifier
    if classify_confidence < threshold:
        return EngineResponse(
            state="preflight_failed",
            message=f"Low confidence classification: {classify_confidence:.2f} "
            f"(threshold: {threshold:.2f}). Rephrase or specify the operation.",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "confidence", "reason": f"below threshold {threshold}"}],
            },
        )
    checks_passed.append("confidence")

    # --- Intent match ---
    if classify_intent != action:
        return EngineResponse(
            state="escalate",
            message=f"Intent_mismatch: classify returned {classify_intent!r} but action is {action!r}",
            error_code="intent_mismatch",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "intent_match", "reason": "mismatch"}],
            },
        )
    checks_passed.append("intent_match")

    # --- Dedup enforcement (create action) ---
    if action == "create" and duplicate_of and not dedup_override:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Duplicate of {duplicate_of} detected in plan stage. "
            "Pass dedup_override=True to proceed.",
            error_code="duplicate_candidate",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "dedup", "reason": f"duplicate_of={duplicate_of}"}],
            },
        )
    if action == "create":
        checks_passed.append("dedup")

    # --- Ticket ID required for non-create ---
    if action != "create" and not ticket_id:
        return EngineResponse(
            state="need_fields",
            message=f"ticket_id required for {action}",
            error_code="need_fields",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "ticket_id", "reason": "missing for non-create"}],
            },
        )

    # --- Ticket existence check (non-create) ---
    if action != "create" and ticket_id:
        from scripts.ticket_read import find_ticket_by_id

        ticket = find_ticket_by_id(tickets_dir, ticket_id)
        if ticket is None:
            return EngineResponse(
                state="not_found",
                message=f"No ticket found matching {ticket_id}",
                ticket_id=ticket_id,
                error_code="not_found",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [{"check": "ticket_exists", "reason": "not found"}],
                },
            )
        checks_passed.append("ticket_exists")

        # --- Dependency check (close action) ---
        if action == "close" and ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                if dependency_override:
                    checks_passed.append("dependencies_overridden")
                else:
                    return EngineResponse(
                        state="dependency_blocked",
                        message=f"Ticket has open blockers: {unresolved}. "
                        "Resolve or pass dependency_override: true.",
                        ticket_id=ticket_id,
                        error_code="dependency_blocked",
                        data={
                            "checks_passed": checks_passed,
                            "checks_failed": [{"check": "dependencies", "reason": f"unresolved: {unresolved}"}],
                        },
                    )
            else:
                checks_passed.append("dependencies")

        # --- TOCTOU fingerprint check ---
        if target_fingerprint is not None:
            from scripts.ticket_dedup import target_fingerprint as compute_fp

            current_fp = compute_fp(Path(ticket.path))
            if current_fp != target_fingerprint:
                return EngineResponse(
                    state="preflight_failed",
                    message="Stale fingerprint — ticket was modified since read. "
                    "Re-run to get a fresh plan.",
                    ticket_id=ticket_id,
                    error_code="stale_plan",
                    data={
                        "checks_passed": checks_passed,
                        "checks_failed": [{"check": "target_fingerprint", "reason": "stale"}],
                    },
                )
            checks_passed.append("target_fingerprint")

    return EngineResponse(
        state="ok",
        message="All preflight checks passed",
        data={"checks_passed": checks_passed, "checks_failed": checks_failed},
    )


# --- execute ---

from datetime import date as Date

from scripts.ticket_id import allocate_id, build_filename
from scripts.ticket_parse import (
    ParsedTicket,
    extract_fenced_yaml,
    parse_yaml_block,
    parse_ticket as _parse_ticket,
)
from scripts.ticket_render import render_ticket

# Canonical field order for YAML frontmatter rendering.
_CANONICAL_FIELD_ORDER = [
    "id", "date", "status", "priority", "effort",
    "source", "tags", "blocked_by", "blocks",
    "contract_version",
]

# Valid status transitions for update action (from -> set of valid to statuses).
# done/wontfix are terminal — only reopen (separate action) can transition out.
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "blocked", "wontfix"},
    "in_progress": {"open", "blocked", "done", "wontfix"},
    "blocked": {"open", "in_progress", "wontfix"},
    "done": set(),       # Terminal — reopen action required.
    "wontfix": set(),    # Terminal — reopen action required.
}

# Transitions that require preconditions.
_TRANSITION_PRECONDITIONS: dict[tuple[str, str], str] = {
    ("open", "blocked"): "blocked_by_required",
    ("in_progress", "blocked"): "blocked_by_required",
    ("in_progress", "done"): "acceptance_criteria_required",
    ("blocked", "open"): "blockers_resolved_required",
    ("blocked", "in_progress"): "blockers_resolved_required",
}


_YAML_SPECIAL_CHARS = frozenset(",[]{}:#&*?|>!%@`\"'")


def _yaml_quote_flow_item(item: Any) -> str:
    """Quote a YAML flow sequence item if it contains special characters."""
    s = str(item)
    if any(c in s for c in _YAML_SPECIAL_CHARS) or not s:
        return f'"{s}"'
    return s


def _render_canonical_frontmatter(data: dict[str, Any]) -> str:
    """Render YAML frontmatter with controlled field order and quoting.

    Unlike yaml.dump(), this function:
    - Preserves field order (canonical, not alphabetical)
    - Always quotes date strings (prevents PyYAML date coercion)
    - Uses consistent list formatting (flow style for simple lists)
    """
    lines: list[str] = []
    for key in _CANONICAL_FIELD_ORDER:
        if key not in data:
            continue
        value = data[key]
        if value is None:
            continue
        if key == "date":
            lines.append(f'{key}: "{value}"')
        elif key == "source" and isinstance(value, dict):
            lines.append("source:")
            for sk, sv in value.items():
                lines.append(f'  {sk}: "{sv}"' if isinstance(sv, str) else f"  {sk}: {sv}")
        elif key == "contract_version":
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, list):
            items = ", ".join(_yaml_quote_flow_item(item) for item in value)
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    # Preserve unknown keys (forward-compat).
    known_keys = set(_CANONICAL_FIELD_ORDER) | {"defer"}
    for key in data:
        if key not in known_keys:
            value = data[key]
            if value is not None:
                lines.append(f"{key}: {value}")
    # Include defer if present.
    if "defer" in data and data["defer"] is not None:
        defer = data["defer"]
        lines.append("defer:")
        for dk, dv in defer.items():
            if isinstance(dv, bool):
                lines.append(f"  {dk}: {'true' if dv else 'false'}")
            else:
                lines.append(f'  {dk}: "{dv}"' if isinstance(dv, str) else f"  {dk}: {dv}")
    return "\n".join(lines) + "\n"


def _is_valid_transition(current: str, target: str, action: str) -> bool:
    """Check if a status transition is valid per the contract."""
    if action == "close":
        if current in _TERMINAL_STATUSES:
            return False
        return target in ("done", "wontfix")
    if action == "reopen":
        return current in ("done", "wontfix") and target == "open"
    # Update: follow transition table.
    valid = _VALID_TRANSITIONS.get(current, set())
    return target in valid


def _check_transition_preconditions(
    current: str, target: str, ticket: Any, tickets_dir: Path,
    fields: dict[str, Any] | None = None,
) -> str | None:
    """Check transition preconditions. Returns error message or None if OK.

    Uses merged state: fields (pending update) take precedence over ticket
    (pre-update) for fields that are being changed in this operation.
    """
    key = (current, target)
    precondition = _TRANSITION_PRECONDITIONS.get(key)
    if precondition is None:
        return None

    _fields = fields or {}

    if precondition == "blocked_by_required":
        blocked_by = _fields.get("blocked_by", ticket.blocked_by)
        if not blocked_by:
            return "Transition to 'blocked' requires non-empty blocked_by"
        return None

    if precondition == "acceptance_criteria_required":
        ac = ticket.sections.get("Acceptance Criteria", "")
        if not ac.strip():
            return "Transition to 'done' requires acceptance criteria section"
        return None

    if precondition == "blockers_resolved_required":
        if ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                return f"Blockers still open: {unresolved}. Resolve or use dependency_override."
        return None

    return None


def _audit_append(session_id: str, tickets_dir: Path, entry: dict[str, Any]) -> bool:
    """Append a JSONL audit entry for the given session.

    Location: <tickets_dir>/.audit/YYYY-MM-DD/<session_id>.jsonl
    Returns True on success, False on failure.
    """
    try:
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = tickets_dir / ".audit" / date_dir
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_file = audit_dir / f"{session_id}.jsonl"
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception:
        return False


def engine_count_session_creates(session_id: str, tickets_dir: Path) -> int | object:
    """Count successful create actions in a session's audit file.

    Reads <tickets_dir>/.audit/YYYY-MM-DD/<session_id>.jsonl for today's
    date and counts entries where action == "create" and result starts
    with "ok_".

    Returns:
        int: count of successful creates (0 if file doesn't exist)
        AUDIT_UNAVAILABLE: on permission error reading the audit file
    """
    date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_file = tickets_dir / ".audit" / date_dir / f"{session_id}.jsonl"

    if not audit_file.exists():
        return 0

    try:
        text = audit_file.read_text(encoding="utf-8")
    except OSError:
        return AUDIT_UNAVAILABLE

    count = 0
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("action") == "create" and isinstance(entry.get("result"), str) and entry["result"].startswith("ok_"):
            count += 1
    return count


def engine_execute(
    *,
    action: str,
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    dedup_override: bool,
    dependency_override: bool,
    tickets_dir: Path,
    autonomy_mode: str = "suggest",
    hook_injected: bool = False,
) -> EngineResponse:
    """Execute the mutation: create, update, close, or reopen.

    Assumes preflight has already passed. Writes ticket files.
    Wraps dispatch with JSONL audit trail.
    """
    # Phase 1: hard-block all agent mutations (defense-in-depth, mirrors preflight).
    # M8: Remove this block. The transport-layer validation below becomes the primary gate.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Phase 1: agent mutations are hard-blocked",
            error_code="policy_blocked",
        )

    # --- Transport-layer validation ---
    # Agent mutations without hook_injected are rejected (defense-in-depth).
    # The Phase 1 hard-block above catches this first, but when M8 removes
    # the hard-block, this validation becomes the primary gate.
    if request_origin == "agent" and not hook_injected:
        return EngineResponse(
            state="policy_blocked",
            message="Agent mutations require hook_injected=True (missing trust field)",
            error_code="policy_blocked",
        )
    # User without hook_injected: proceed (warn only — unverified in audit).

    # Audit: attempt_started
    base_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": "attempt_started",
        "ticket_id": ticket_id,
        "session_id": session_id,
        "request_origin": request_origin,
        "autonomy_mode": autonomy_mode,
        "result": None,
        "changes": None,
    }
    _audit_append(session_id, tickets_dir, base_entry)

    # Dispatch
    try:
        if action == "create":
            resp = _execute_create(fields, session_id, request_origin, tickets_dir)
        elif action == "update":
            resp = _execute_update(ticket_id, fields, session_id, request_origin, tickets_dir)
        elif action == "close":
            resp = _execute_close(ticket_id, fields, session_id, request_origin, tickets_dir)
        elif action == "reopen":
            resp = _execute_reopen(ticket_id, fields, session_id, request_origin, tickets_dir)
        else:
            resp = EngineResponse(
                state="escalate",
                message=f"Unknown action: {action!r}",
                error_code="intent_mismatch",
            )
    except Exception as exc:
        # Audit: error entry
        error_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "ticket_id": ticket_id,
            "session_id": session_id,
            "request_origin": request_origin,
            "autonomy_mode": autonomy_mode,
            "result": f"error:{type(exc).__name__}",
            "changes": None,
        }
        _audit_append(session_id, tickets_dir, error_entry)
        raise

    # Audit: attempt_result
    result_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "ticket_id": resp.ticket_id if resp.ticket_id else ticket_id,
        "session_id": session_id,
        "request_origin": request_origin,
        "autonomy_mode": autonomy_mode,
        "result": resp.state,
        "changes": resp.data.get("changes") if resp.data else None,
    }
    _audit_append(session_id, tickets_dir, result_entry)

    return resp


# --- Execute sub-functions (stubs replaced in subsequent slices) ---


def _execute_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Create a new ticket file with all required contract fields."""
    missing = []
    if not fields.get("title"):
        missing.append("title")
    if not fields.get("problem"):
        missing.append("problem")
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields for create: {missing}",
            error_code="need_fields",
        )

    tickets_dir.mkdir(parents=True, exist_ok=True)

    today = Date.today()
    ticket_id = allocate_id(tickets_dir, today)
    title = fields.get("title", "Untitled")
    filename = build_filename(ticket_id, title)

    source = fields.get("source", {"type": "ad-hoc", "ref": "", "session": session_id})
    if "session" not in source:
        source["session"] = session_id

    content = render_ticket(
        id=ticket_id,
        title=title,
        date=today.isoformat(),
        status="open",
        priority=fields.get("priority", "medium"),
        effort=fields.get("effort", ""),
        source=source,
        tags=fields.get("tags", []),
        problem=fields.get("problem", ""),
        approach=fields.get("approach", ""),
        acceptance_criteria=fields.get("acceptance_criteria"),
        verification=fields.get("verification", ""),
        key_files=fields.get("key_files"),
        context=fields.get("context", ""),
        prior_investigation=fields.get("prior_investigation", ""),
        decisions_made=fields.get("decisions_made", ""),
        related=fields.get("related", ""),
    )

    ticket_path = tickets_dir / filename
    ticket_path.write_text(content, encoding="utf-8")

    return EngineResponse(
        state="ok_create",
        message=f"Created {ticket_id} at {ticket_path}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": None},
    )


def _execute_update(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Update an existing ticket's frontmatter fields."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for update", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")

    # Check status transition validity.
    new_status = fields.get("status")
    if new_status and new_status != ticket.status:
        if not _is_valid_transition(ticket.status, new_status, "update"):
            return EngineResponse(
                state="invalid_transition",
                message=f"Cannot transition from {ticket.status} to {new_status} via update"
                + (" (use reopen action)" if ticket.status in _TERMINAL_STATUSES else ""),
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )
        precondition_error = _check_transition_preconditions(
            ticket.status, new_status, ticket, tickets_dir, fields=fields,
        )
        if precondition_error:
            return EngineResponse(
                state="invalid_transition",
                message=precondition_error,
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )

    # Update frontmatter fields.
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    changes: dict[str, Any] = {"frontmatter": {}, "sections_changed": []}
    for key, value in fields.items():
        if key in data and data[key] != value:
            changes["frontmatter"][key] = [data[key], value]
        data[key] = value

    # Re-render using canonical frontmatter renderer (not yaml.dump).
    new_yaml = _render_canonical_frontmatter(data)
    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_update",
        message=f"Updated {ticket_id}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )


def _execute_close(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Close a ticket (set status to done or wontfix, optionally archive).

    Validates transitions with action='close', which allows done/wontfix
    from any non-terminal status.
    """
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for close", error_code="need_fields")

    resolution = fields.get("resolution", "done")
    archive = fields.get("archive", False)

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    # Validate transition with action="close" (not "update").
    if not _is_valid_transition(ticket.status, resolution, "close"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot close with resolution {resolution!r} (must be 'done' or 'wontfix')"
            + (f" from terminal status {ticket.status!r}" if ticket.status in _TERMINAL_STATUSES else ""),
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Check transition preconditions (e.g., acceptance criteria for -> done).
    precondition_error = _check_transition_preconditions(
        ticket.status, resolution, ticket, tickets_dir, fields=fields,
    )
    if precondition_error:
        return EngineResponse(
            state="invalid_transition",
            message=precondition_error,
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change using canonical frontmatter renderer.
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = resolution
    new_yaml = _render_canonical_frontmatter(data)
    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    changes = {"frontmatter": {"status": [old_status, resolution]}}

    # Archive if requested.
    if archive:
        closed_dir = tickets_dir / "closed-tickets"
        closed_dir.mkdir(exist_ok=True)
        dst = closed_dir / ticket_path.name
        ticket_path.rename(dst)
        return EngineResponse(
            state="ok_close_archived",
            message=f"Closed and archived {ticket_id} to closed-tickets/",
            ticket_id=ticket_id,
            data={"ticket_path": str(dst), "changes": changes},
        )

    return EngineResponse(
        state="ok_close",
        message=f"Closed {ticket_id} (status: {resolution})",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )


def _execute_reopen(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Reopen a done/wontfix ticket."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for reopen", error_code="need_fields")

    reopen_reason = fields.get("reopen_reason", "")
    if not reopen_reason:
        return EngineResponse(state="need_fields", message="reopen_reason required for reopen", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    if not _is_valid_transition(ticket.status, "open", "reopen"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot reopen ticket with status {ticket.status} (must be done or wontfix)",
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change.
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = "open"
    new_yaml = _render_canonical_frontmatter(data)
    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Append to Reopen History section (newest-last).
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    reopen_entry = f"\n\n## Reopen History\n- **{now}**: {reopen_reason} (by {request_origin})"

    if "## Reopen History" in new_text:
        rh_match = re.search(r"## Reopen History\n", new_text)
        if rh_match:
            next_heading = re.search(r"\n## ", new_text[rh_match.end():])
            if next_heading:
                insert_pos = rh_match.end() + next_heading.start()
            else:
                insert_pos = len(new_text)
            entry = f"- **{now}**: {reopen_reason} (by {request_origin})\n"
            new_text = new_text[:insert_pos].rstrip() + "\n" + entry + new_text[insert_pos:]
    else:
        new_text += reopen_entry

    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_reopen",
        message=f"Reopened {ticket_id}. Reason: {reopen_reason}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": {"status": [old_status, "open"]}},
    )
