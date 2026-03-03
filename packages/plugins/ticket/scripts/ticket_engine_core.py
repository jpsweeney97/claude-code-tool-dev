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
    key_files = fields.get("key_files", [])
    fp = dedup_fingerprint(problem_text, key_files)

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
        ticket_key_files: list[str] = []
        # Extract file paths from Key Files section if present.
        key_files_section = ticket.sections.get("Key Files", "")
        if key_files_section:
            for match in re.finditer(r"^\| ([^|]+) \|", key_files_section, re.MULTILINE):
                cell = match.group(1).strip()
                if cell and cell != "File" and not cell.startswith("-"):
                    ticket_key_files.append(cell)

        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_files)
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

    Checks in order: origin, confidence, intent match, agent policy,
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

    # --- Agent policy: Phase 1 strict fail-closed ---
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
