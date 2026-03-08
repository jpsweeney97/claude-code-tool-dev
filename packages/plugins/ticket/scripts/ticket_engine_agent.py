#!/usr/bin/env python3
"""Agent entrypoint for the ticket engine.

Hardcodes request_origin="agent". Called by ticket-autocreate agent.
Usage: python3 ticket_engine_agent.py <subcommand> <payload_file>
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
from scripts.ticket_paths import discover_project_root, resolve_tickets_dir
from scripts.ticket_stage_models import (
    ClassifyInput,
    ExecuteInput,
    PayloadError,
    PlanInput,
    PreflightInput,
)
from scripts.ticket_trust import collect_trust_triple_errors

REQUEST_ORIGIN = "agent"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_agent.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "agent" regardless of what caller passed.
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
        trust_errors = collect_trust_triple_errors(
            payload.get("hook_injected", False),
            hook_origin,
            payload.get("session_id", ""),
        )
        if trust_errors:
            resp = EngineResponse(
                state="policy_blocked",
                message=f"Execute requires verified hook provenance: {', '.join(trust_errors)}",
                error_code="policy_blocked",
            )
            print(resp.to_json())
            sys.exit(1)

    project_root = discover_project_root(Path.cwd())
    if project_root is None:
        resp = EngineResponse(
            state="policy_blocked",
            message="Cannot determine project root: no .claude/ or .git/ marker found in ancestors of cwd",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        sys.exit(1)

    tickets_dir_raw = payload.get("tickets_dir", "docs/tickets")
    tickets_dir, path_error = resolve_tickets_dir(tickets_dir_raw, project_root=project_root)
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
    try:
        if subcommand == "classify":
            inp = ClassifyInput.from_payload(payload)
            return engine_classify(
                action=inp.action,
                args=inp.args,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
            )
        elif subcommand == "plan":
            inp = PlanInput.from_payload(payload)
            return engine_plan(
                intent=inp.intent,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "preflight":
            inp = PreflightInput.from_payload(payload)
            return engine_preflight(
                ticket_id=inp.ticket_id,
                action=inp.action,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                classify_confidence=inp.classify_confidence,
                classify_intent=inp.classify_intent,
                dedup_fingerprint=inp.dedup_fingerprint,
                target_fingerprint=inp.target_fingerprint,
                fields=inp.fields,
                duplicate_of=inp.duplicate_of,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                hook_injected=inp.hook_injected,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "execute":
            inp = ExecuteInput.from_payload(payload)
            autonomy_config = (
                AutonomyConfig.from_dict(inp.autonomy_config_data)
                if isinstance(inp.autonomy_config_data, dict)
                else None
            )
            return engine_execute(
                action=inp.action,
                ticket_id=inp.ticket_id,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                tickets_dir=tickets_dir,
                target_fingerprint=inp.target_fingerprint,
                autonomy_config=autonomy_config,
                hook_injected=inp.hook_injected,
                hook_request_origin=inp.hook_request_origin,
                classify_intent=inp.classify_intent,
                classify_confidence=inp.classify_confidence,
                dedup_fingerprint=inp.dedup_fingerprint,
            )
        else:
            return EngineResponse(
                state="escalate",
                message=f"Unknown subcommand: {subcommand!r}",
                error_code="intent_mismatch",
            )
    except PayloadError as exc:
        return EngineResponse(
            state=exc.state,
            message=f"{subcommand} payload validation failed: {exc}",
            error_code=exc.code,
        )


if __name__ == "__main__":
    main()
