"""Consultation adapter for codex exec.

Pipeline: parse input → credential scan → version check → build command →
run subprocess → parse JSONL → structured output.

Read-only consultation — no clean-tree gate, no secret-file gate, no output
file. Sandbox is always read-only. Supports resume via codex exec resume.

Design decisions:
- Opaque continuation tokens: last-wins for thread_id (exec resume may
  emit new thread.started). Callers persist newest continuation_id.
- 4-state dispatch model: no_dispatch, dispatched_no_token,
  dispatched_with_token_uncertain, complete.
- No analytics emission: skills own event production. Adapter is transport.
- CODEX_SANDBOX=seatbelt: propagated to subprocess environment.

Usage:
    python3 codex_consult.py <input_file.json>

Exit codes:
    0 — success or blocked (check status field)
    1 — adapter error
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from tempfile import TemporaryFile

if __package__:
    from scripts.consultation_safety import check_tool_input, START_POLICY
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from consultation_safety import check_tool_input, START_POLICY  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError as exc:
        print(f"codex-consult: fatal: cannot import sibling modules: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class ConsultationError(Exception):
    """Adapter-level error (exit 1)."""

class CredentialBlockError(Exception):
    """Credential detected in prompt (exit 0, status=blocked)."""

class SubprocessTimeout(ConsultationError):
    """Timeout with partial stdout available for token extraction."""
    def __init__(self, partial_stdout: str):
        super().__init__("exec failed: process timeout")
        self.partial_stdout = partial_stdout


# ---------------------------------------------------------------------------
# Dispatch state
# ---------------------------------------------------------------------------

class DispatchState(Enum):
    NO_DISPATCH = "no_dispatch"
    DISPATCHED_NO_TOKEN = "dispatched_no_token"
    DISPATCHED_WITH_TOKEN_UNCERTAIN = "dispatched_with_token_uncertain"
    COMPLETE = "complete"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
_MIN_VERSION = (0, 111, 0)
_STDOUT_MAX_BYTES = 50 * 1024 * 1024
_SUBPROCESS_TIMEOUT = 300
_KNOWN_FIELDS = {"prompt", "thread_id", "model", "reasoning_effort"}


# ---------------------------------------------------------------------------
# Pipeline functions
# ---------------------------------------------------------------------------


def _parse_input(input_path: Path) -> dict:
    """Phase A: structural parse of input JSON.

    Returns dict with defaults applied. Does not echo user content in errors.
    """
    try:
        raw = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConsultationError(f"input read failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConsultationError(f"invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ConsultationError("expected JSON object at top level")

    prompt = data.get("prompt")
    if prompt is None:
        raise ConsultationError("prompt is required")
    if not isinstance(prompt, str):
        raise ConsultationError("prompt must be string")

    reasoning_effort = data.get("reasoning_effort", "xhigh")
    if reasoning_effort not in _VALID_EFFORTS:
        raise ConsultationError(
            f"invalid reasoning_effort: must be one of {sorted(_VALID_EFFORTS)}"
        )

    model = data.get("model") or None
    if model is not None and not isinstance(model, str):
        raise ConsultationError("model must be string")

    thread_id = data.get("thread_id") or None
    if thread_id is not None and not isinstance(thread_id, str):
        raise ConsultationError("thread_id must be string")

    return {
        "prompt": prompt,
        "thread_id": thread_id,
        "sandbox": "read-only",
        "model": model,
        "reasoning_effort": reasoning_effort,
    }
