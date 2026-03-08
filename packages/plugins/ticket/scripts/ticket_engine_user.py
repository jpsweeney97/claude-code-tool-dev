#!/usr/bin/env python3
"""User entrypoint for the ticket engine.

Hardcodes request_origin="user". Called by ticket-ops skill.
Usage: python3 ticket_engine_user.py <subcommand> <payload_file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_core import (
    AutonomyConfig,
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)
from scripts.ticket_paths import resolve_tickets_dir

REQUEST_ORIGIN = "user"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_user.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "user" regardless of what caller passed.
    payload["request_origin"] = REQUEST_ORIGIN

    # Check for hook-injected origin mismatch (all stages).
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != REQUEST_ORIGIN:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={REQUEST_ORIGIN}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        sys.exit(1)

    # Execute requires the full trust triple.
    if subcommand == "execute":
        hook_injected = payload.get("hook_injected", False)
        session_id = payload.get("session_id", "")
        trust_errors: list[str] = []
        if not hook_injected:
            trust_errors.append("hook_injected=False")
        if hook_origin is None:
            trust_errors.append("hook_request_origin missing")
        if not session_id:
            trust_errors.append("session_id empty")
        if trust_errors:
            resp = EngineResponse(
                state="policy_blocked",
                message=f"Execute requires verified hook provenance: {', '.join(trust_errors)}",
                error_code="policy_blocked",
            )
            print(resp.to_json())
            sys.exit(1)

    tickets_dir_raw = payload.get("tickets_dir", "docs/tickets")
    tickets_dir, path_error = resolve_tickets_dir(tickets_dir_raw, project_root=Path.cwd())
    if path_error is not None or tickets_dir is None:
        resp = EngineResponse(
            state="policy_blocked",
            message=path_error or "tickets_dir validation failed",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        sys.exit(1)

    resp = _dispatch(subcommand, payload, tickets_dir)
    print(resp.to_json())
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        sys.exit(0)
    elif resp.error_code == "need_fields":
        sys.exit(2)
    else:
        sys.exit(1)


def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    elif subcommand == "plan":
        return engine_plan(
            intent=payload.get("intent", payload.get("action", "")),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            tickets_dir=tickets_dir,
        )
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            fields=payload.get("fields"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            hook_injected=payload.get("hook_injected", False),
            tickets_dir=tickets_dir,
        )
    elif subcommand == "execute":
        config_data = payload.get("autonomy_config")
        autonomy_config = AutonomyConfig.from_dict(config_data) if isinstance(config_data, dict) else None
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
            target_fingerprint=payload.get("target_fingerprint"),
            autonomy_config=autonomy_config,
            hook_injected=payload.get("hook_injected", False),
            hook_request_origin=payload.get("hook_request_origin"),
            classify_intent=payload.get("classify_intent"),
            classify_confidence=payload.get("classify_confidence"),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
        )
    else:
        return EngineResponse(state="escalate", message=f"Unknown subcommand: {subcommand!r}", error_code="intent_mismatch")


if __name__ == "__main__":
    main()
