"""Shared entrypoint runner for the ticket engine.

Consolidates boundary logic (payload read, origin enforcement, trust triple,
project root, tickets_dir, dispatch, exit codes) that was previously
duplicated between ticket_engine_user.py and ticket_engine_agent.py.

Entrypoints import and call run() with their hardcoded request_origin.
This module is never invoked directly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

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


def run(
    request_origin: str,
    argv: list[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the ticket engine entrypoint.

    Args:
        request_origin: Authoritative origin ("user" or "agent").
        argv: Command-line arguments [subcommand, payload_file].
              Defaults to sys.argv[1:].
        prog: Script name for usage messages.

    Returns:
        Exit code: 0 (success), 1 (engine error), 2 (need_fields).
    """
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(
            json.dumps({"error": f"Usage: {prog} <subcommand> <payload_file>"}),
            file=sys.stderr,
        )
        return 1

    subcommand = args[0]
    payload_path = Path(args[1])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps({"error": f"Cannot read payload: {exc}"}),
            file=sys.stderr,
        )
        return 1

    # Normalize origin in payload. request_origin argument is authoritative.
    payload["request_origin"] = request_origin

    # Check for hook-injected origin mismatch (all stages).
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != request_origin:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={request_origin}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        return 1

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
            return 1

    project_root = discover_project_root(Path.cwd())
    if project_root is None:
        resp = EngineResponse(
            state="policy_blocked",
            message="Cannot determine project root: no .claude/ or .git/ marker found in ancestors of cwd",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        return 1

    tickets_dir_raw = payload.get("tickets_dir", "docs/tickets")
    tickets_dir, path_error = resolve_tickets_dir(
        tickets_dir_raw, project_root=project_root
    )
    if path_error is not None or tickets_dir is None:
        resp = EngineResponse(
            state="policy_blocked",
            message=path_error or "tickets_dir validation failed",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        return 1

    resp = _dispatch(subcommand, payload, tickets_dir, request_origin)
    print(resp.to_json())
    return _exit_code(resp)


def _exit_code(resp: EngineResponse) -> int:
    """Map EngineResponse to exit code. Single-sourced."""
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in (
        "ok",
        "ok_create",
        "ok_update",
        "ok_close",
        "ok_close_archived",
        "ok_reopen",
    ):
        return 0
    if resp.error_code == "need_fields":
        return 2
    return 1


def _dispatch(
    subcommand: str,
    payload: dict[str, Any],
    tickets_dir: Path,
    request_origin: str,
) -> EngineResponse:
    try:
        if subcommand == "classify":
            inp = ClassifyInput.from_payload(payload)
            return engine_classify(
                action=inp.action,
                args=inp.args,
                session_id=inp.session_id,
                request_origin=request_origin,
            )
        elif subcommand == "plan":
            inp = PlanInput.from_payload(payload)
            return engine_plan(
                intent=inp.intent,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=request_origin,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "preflight":
            inp = PreflightInput.from_payload(payload)
            return engine_preflight(
                ticket_id=inp.ticket_id,
                action=inp.action,
                session_id=inp.session_id,
                request_origin=request_origin,
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
                request_origin=request_origin,
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
