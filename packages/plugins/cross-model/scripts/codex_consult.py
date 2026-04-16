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
    from scripts.consultation_safety import check_tool_input, START_POLICY, SafetyVerdict
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from consultation_safety import check_tool_input, START_POLICY, SafetyVerdict  # type: ignore[import-not-found,no-redef]
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
_SUBPROCESS_TIMEOUT = 900
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

    reasoning_effort = data.get("reasoning_effort", "high")
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


def _check_codex_version() -> None:
    """Verify codex CLI >= 0.111.0."""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise ConsultationError("codex not found on PATH")
    except subprocess.TimeoutExpired:
        raise ConsultationError("codex --version timed out")

    if result.returncode != 0:
        raise ConsultationError("codex --version failed")

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)
    if not match:
        raise ConsultationError("codex --version: cannot parse version")

    version = tuple(int(g) for g in match.groups())
    if version < _MIN_VERSION:
        raise ConsultationError(
            f"requires codex >= {'.'.join(str(v) for v in _MIN_VERSION)}, "
            f"found {'.'.join(str(v) for v in version)}"
        )


def _build_command(
    prompt: str,
    thread_id: str | None,
    sandbox: str,
    model: str | None,
    reasoning_effort: str,
) -> list[str]:
    """Build codex exec command. Supports new and resume conversations."""
    if thread_id:
        cmd = ["codex", "exec", "resume", thread_id, "--json"]
    else:
        cmd = ["codex", "exec", "--json"]
        cmd.extend(["-s", sandbox])

    cmd.append("--skip-git-repo-check")

    if model:
        cmd.extend(["-m", model])

    cmd.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])

    cmd.append("--")
    cmd.append(prompt)
    return cmd


_KNOWN_EVENT_TYPES = {
    "thread.started", "turn.started", "turn.completed", "turn.failed",
    "item.started", "item.completed", "error",
}


def _parse_jsonl(stdout: str) -> dict:
    """Parse JSONL events from codex exec stdout.

    Opaque continuation tokens: uses LAST thread_id from thread.started
    (not first-wins like codex_delegate.py). exec resume may emit a new
    thread.started with a different ID.
    """
    continuation_id: str | None = None
    response_parts: list[str] = []
    token_usage: dict | None = None
    runtime_failures: list[str] = []
    usable_count = 0

    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print("codex-consult: skipped malformed JSONL line", file=sys.stderr)
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        if event_type not in _KNOWN_EVENT_TYPES:
            continue
        usable_count += 1

        if event_type == "thread.started":
            tid = event.get("thread_id")
            if isinstance(tid, str):
                continuation_id = tid

        elif event_type == "item.completed":
            item = event.get("item", {})
            if not isinstance(item, dict):
                continue
            if item.get("type") == "agent_message":
                text_val = item.get("text")
                if isinstance(text_val, str):
                    response_parts.append(text_val)

        elif event_type == "turn.completed":
            usage = event.get("usage", {})
            if isinstance(usage, dict) and usage:
                token_usage = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

        elif event_type == "turn.failed":
            runtime_failures.append(str(event.get("error", "unknown error")))

        elif event_type == "error":
            runtime_failures.append(str(event.get("message", event.get("error", "unknown error"))))

    if usable_count == 0:
        raise ConsultationError("parse failed: no usable JSONL events from codex exec")

    if continuation_id is None:
        print("codex-consult: no thread.started event, continuation_id will be null", file=sys.stderr)

    return {
        "continuation_id": continuation_id,
        "response_text": "\n\n".join(response_parts) if response_parts else None,
        "token_usage": token_usage,
        "runtime_failures": runtime_failures,
    }


def _read_stdout(stdout_sink) -> str:
    """Read and decode stdout from the sink file, enforcing size cap."""
    stdout_sink.seek(0, os.SEEK_END)
    stdout_size = stdout_sink.tell()
    stdout_sink.seek(0)
    stdout_bytes = stdout_sink.read(_STDOUT_MAX_BYTES + 1)
    if stdout_size > _STDOUT_MAX_BYTES:
        print("codex-consult: stdout truncated (exceeded 50MB cap)", file=sys.stderr)
    return stdout_bytes[:_STDOUT_MAX_BYTES].decode("utf-8", errors="replace")


def _run_subprocess(cmd: list[str]) -> tuple[str, int]:
    """Execute codex exec and return (stdout_text, returncode).

    Propagates CODEX_SANDBOX=seatbelt to prevent macOS startup panics.
    On timeout: reads partial stdout and raises SubprocessTimeout.
    """
    env = os.environ.copy()
    env["CODEX_SANDBOX"] = "seatbelt"

    try:
        with TemporaryFile() as stdout_sink, TemporaryFile() as stderr_sink:
            proc = subprocess.Popen(
                cmd,
                stdout=stdout_sink,
                stderr=stderr_sink,
                env=env,
                text=False,
            )
            try:
                proc.wait(timeout=_SUBPROCESS_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait()
                except subprocess.TimeoutExpired:
                    pass
                partial = _read_stdout(stdout_sink)
                raise SubprocessTimeout(partial)

            return _read_stdout(stdout_sink), proc.returncode
    except FileNotFoundError:
        raise ConsultationError("exec failed: codex not found")


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

_OUTPUT_REQUIRED = {
    "status", "dispatched", "continuation_id", "response_text",
    "token_usage", "runtime_failures", "error", "dispatch_state",
}


def _result(status: str, **kwargs: object) -> dict:
    """Build result dict with field validation."""
    result: dict = {"status": status}
    result.update(kwargs)
    missing = _OUTPUT_REQUIRED - set(result.keys())
    assert not missing, f"_result missing fields: {missing}"
    return result


def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON string. Validates all required fields."""
    return json.dumps(_result(status, **kwargs))


# ---------------------------------------------------------------------------
# Programmatic API
# ---------------------------------------------------------------------------


def consult(
    prompt: str,
    thread_id: str | None = None,
    model: str | None = None,
    reasoning_effort: str = "high",
) -> dict:
    """Run the consultation pipeline programmatically.

    Returns a dict with all required output fields. Never raises.
    Status is one of: ok, blocked, timeout_uncertain, error.
    """
    dispatch = DispatchState.NO_DISPATCH

    try:
        if reasoning_effort not in _VALID_EFFORTS:
            raise ConsultationError(
                f"invalid reasoning_effort: must be one of {sorted(_VALID_EFFORTS)}"
            )

        verdict = check_tool_input({"prompt": prompt}, START_POLICY)
        if verdict.action == "block":
            raise CredentialBlockError(verdict.reason or "credential detected")

        _check_codex_version()

        cmd = _build_command(
            prompt=prompt,
            thread_id=thread_id,
            sandbox="read-only",
            model=model,
            reasoning_effort=reasoning_effort,
        )

        dispatch = DispatchState.DISPATCHED_NO_TOKEN
        stdout_text, returncode = _run_subprocess(cmd)

        parsed = _parse_jsonl(stdout_text)

        if parsed["continuation_id"]:
            dispatch = DispatchState.COMPLETE

        return _result(
            "ok", dispatched=True,
            continuation_id=parsed["continuation_id"],
            response_text=parsed["response_text"],
            token_usage=parsed["token_usage"],
            runtime_failures=parsed["runtime_failures"],
            error=None, dispatch_state=dispatch.value,
        )

    except CredentialBlockError as exc:
        return _result(
            "blocked", dispatched=False, error=str(exc),
            continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=DispatchState.NO_DISPATCH.value,
        )

    except SubprocessTimeout as exc:
        partial_token = None
        try:
            partial = _parse_jsonl(exc.partial_stdout)
            partial_token = partial.get("continuation_id")
        except ConsultationError:
            pass

        if partial_token:
            dispatch = DispatchState.DISPATCHED_WITH_TOKEN_UNCERTAIN

        return _result(
            "timeout_uncertain", dispatched=True, error=str(exc),
            continuation_id=partial_token, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )

    except ConsultationError as exc:
        return _result(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=str(exc), continuation_id=None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )

    except Exception as exc:
        return _result(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=f"internal error: {exc}", continuation_id=None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run(input_path: Path) -> int:
    """Execute the consultation pipeline from file. Returns exit code."""
    try:
        phase_a = _parse_input(input_path)
    except ConsultationError as exc:
        print(_output(
            "error", dispatched=False, error=str(exc),
            continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=DispatchState.NO_DISPATCH.value,
        ))
        return 1

    result = consult(
        prompt=phase_a["prompt"],
        thread_id=phase_a["thread_id"],
        model=phase_a["model"],
        reasoning_effort=phase_a["reasoning_effort"],
    )
    print(json.dumps(result))
    return 0 if result["status"] in ("ok", "blocked") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(_output(
            "error", error="usage: codex_consult.py <input_file.json>",
            dispatched=False, continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[], dispatch_state="no_dispatch",
        ))
        return 1
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
