"""Execution-turn prompt construction.

Execution turns dispatch real work in an isolated worktree. The prompt conveys
the objective and scope. Unlike advisory turns, execution turns do NOT use a
structured output schema — the "result" is the worktree state plus any server
requests captured during the turn.
"""

from __future__ import annotations

import json

from .artifact_store import TEST_RESULTS_RECORD_RELATIVE_PATH
from .models import PendingServerRequest


def build_execution_turn_text(
    *,
    objective: str,
    worktree_path: str,
) -> str:
    """Build the text input for an execution turn's ``turn/start``.

    The prompt instructs the execution agent to work within the isolated
    worktree boundary. No structured output schema is enforced — the agent
    operates freely within the sandbox constraints.
    """
    return (
        "You are working in an isolated worktree. Your workspace is:\n"
        f"  {worktree_path}\n\n"
        "Objective:\n"
        f"  {objective}\n\n"
        "When you run verification, persist a deterministic test-results record at:\n"
        f"  {TEST_RESULTS_RECORD_RELATIVE_PATH}\n"
        "Write JSON with keys: schema_version, status, commands, summary.\n"
        "Work within the worktree boundary. Commands that require approval "
        "will be escalated to the caller for review."
    )


def build_execution_resume_turn_text(
    *,
    pending_request: PendingServerRequest,
    answers: dict[str, tuple[str, ...]] | None,
) -> str:
    """Build the follow-up prompt used after Claude approves an escalation."""

    requested_scope = json.dumps(
        pending_request.requested_scope,
        indent=2,
        sort_keys=True,
    )
    lines = [
        "Continue the existing isolated delegation thread.",
        "The earlier server request has already been resolved at the wire layer.",
        "Do not re-ask for the same approval; treat the caller decision below as authoritative.",
        f"Persist verification output (status, commands, summary) at {TEST_RESULTS_RECORD_RELATIVE_PATH} when you run tests.",
        "",
        f"Escalation kind: {pending_request.kind}",
        f"Request id: {pending_request.request_id}",
        "Captured request scope:",
        requested_scope,
    ]
    if answers:
        answer_payload = json.dumps(
            {key: {"answers": list(value)} for key, value in answers.items()},
            indent=2,
            sort_keys=True,
        )
        lines.extend(
            [
                "",
                "Caller-supplied answers:",
                answer_payload,
            ]
        )
    return "\n".join(lines)
