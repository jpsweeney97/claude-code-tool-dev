#!/usr/bin/env python3
"""Delegation adapter for codex exec.

14-step pipeline: resolve repo → Phase A parse → credential scan →
Phase B validate → version check → clean-tree gate → secret-file gate →
build command → run subprocess → parse JSONL → read output → emit analytics →
cleanup (output file only — F6 creation-ownership).

Error message guidelines: Phase A (structural parse, step 3) and Phase B
(field validation, step 5) are split so error messages reference field names
and structural issues but never echo user-supplied content (prompts, secrets).
This split is intentional — do not merge the phases or include prompt content
in DelegationError messages.

Usage:
    python3 codex_delegate.py <input_file.json>

Exit codes:
    0 — success or blocked (check status field)
    1 — adapter error
"""

from __future__ import annotations

import fnmatch  # B23: Module-level import, consistent with other stdlib usage
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from tempfile import TemporaryFile

# Sibling imports (same scripts/ directory)
if __package__:
    from scripts.credential_scan import scan_text
    from scripts.emit_analytics import validate as _raw_validate
    from scripts.event_log import ts, append_log, session_id
    from scripts.event_schema import resolve_schema_version as _resolve_schema_version
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from credential_scan import scan_text  # type: ignore[import-not-found,no-redef]
        from emit_analytics import validate as _raw_validate  # type: ignore[import-not-found,no-redef]
        from event_log import ts, append_log, session_id  # type: ignore[import-not-found,no-redef]
        from event_schema import resolve_schema_version as _resolve_schema_version  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError as exc:
        print(f"codex-delegate: fatal: cannot import sibling modules: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class DelegationError(Exception):
    """Adapter-level error (exit 1)."""

class CredentialBlockError(Exception):
    """Credential detected in prompt (exit 0, status=blocked)."""

class GateBlockError(Exception):
    """Pre-dispatch gate failed (exit 0, status=blocked)."""
    def __init__(self, reason: str, gate: str, paths: list[str] | None = None):
        super().__init__(reason)
        self.gate = gate
        self.paths = paths or []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_SANDBOXES = {"read-only", "workspace-write"}
_VALID_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
_KNOWN_FIELDS = {"prompt", "model", "sandbox", "reasoning_effort", "full_auto"}
_MIN_VERSION = (0, 111, 0)
_STDOUT_MAX_BYTES = 50 * 1024 * 1024

# F5: Split into exact names and glob patterns for clarity
_SECRET_EXACT_NAMES = {".env", ".npmrc", ".netrc", "auth.json"}
_SECRET_GLOBS = {"*.pem", "*.key", "*.p12", ".env.*"}
_TEMPLATE_EXEMPTIONS = {".env.example", ".env.sample", ".env.template"}
# Known-safe public artifacts — exact path-tail match (component-based, not substring).
# Each entry is a tuple of the final N path components that unambiguously identify a
# non-secret public file. *.pem remains blocked everywhere else.
_SAFE_ARTIFACT_TAILS: frozenset[tuple[str, ...]] = frozenset({
    ("certifi", "cacert.pem"),  # Python certifi CA bundle — public root certificates only
})


# ---------------------------------------------------------------------------
# Pipeline functions (one per step)
# ---------------------------------------------------------------------------


def _resolve_repo_root() -> Path:
    """Step 1: Resolve git repo root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        raise DelegationError("repo resolution failed: git timed out")
    if result.returncode != 0:
        # B10: Raise DelegationError, not RuntimeError — ensures correct error shape
        raise DelegationError("repo resolution failed: not a git repository")
    return Path(result.stdout.strip())


def _parse_input(input_path: Path) -> dict:
    """Step 3 — Phase A: structural parse. No user content echoed.

    F1+F8: Split from the old combined parse/validate path so that run() can
    capture Phase A data before credential scan. This ensures analytics
    emits for credential blocks (spec: emit if step 3 succeeds).

    Returns raw parsed dict with defaults applied (for analytics).
    Does NOT validate field values — that's Phase B (_validate_input).
    """
    try:
        raw = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DelegationError(f"input read failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise DelegationError("input parse failed: invalid JSON")

    if not isinstance(data, dict):
        raise DelegationError("input parse failed: expected JSON object")

    # Apply defaults but preserve raw values for analytics (F13)
    # R6-B5: Normalize model="" to None — empty string passes Phase B
    # isinstance check but is silently dropped by _build_command's `if model:`,
    # causing analytics to log model="" while execution uses Codex default.
    raw_model = data.get("model")
    # R6-B5: Normalize "" to None. Use isinstance so falsy non-strings
    # (0, False, []) reach Phase B type check instead of becoming None.
    model = raw_model if not isinstance(raw_model, str) or raw_model else None
    return {
        "prompt": data.get("prompt"),
        "model": model,
        "sandbox": data.get("sandbox", "workspace-write"),
        "reasoning_effort": data.get("reasoning_effort", "high"),
        "full_auto": data.get("full_auto", False),
        "_raw_keys": set(data.keys()),  # for unknown-field check in Phase B
    }


def _validate_input(parsed: dict) -> dict:
    """Step 5 — Phase B: field validation. May reference field names,
    never echoes user content.

    Called AFTER credential scan (step 4). Validates enums, conflicts,
    unknown fields.
    """
    # Prompt presence (Phase B — semantic validation)
    prompt = parsed.get("prompt")
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise DelegationError("validation failed: prompt required")

    # Unknown fields
    unknown = parsed.get("_raw_keys", set()) - _KNOWN_FIELDS
    if unknown:
        raise DelegationError(f"validation failed: unknown field '{next(iter(unknown))}'")

    # R5-B3: isinstance checks before set membership keep non-string values
    # deterministic. Unhashable values can raise TypeError; hashable
    # non-strings silently fail membership tests and blur the true error.
    sandbox = parsed["sandbox"]
    if not isinstance(sandbox, str):
        raise DelegationError("validation failed: invalid sandbox value")
    if sandbox == "danger-full-access":
        raise DelegationError("policy: danger-full-access not supported in Step 1")
    if sandbox not in _VALID_SANDBOXES:
        raise DelegationError("validation failed: invalid sandbox value")

    effort = parsed["reasoning_effort"]
    if not isinstance(effort, str):
        raise DelegationError("validation failed: invalid reasoning_effort value")
    if effort not in _VALID_EFFORTS:
        raise DelegationError("validation failed: invalid reasoning_effort value")

    # R5-B3: model must be string if present — non-string causes non-string
    # in subprocess command list
    model = parsed.get("model")
    if model is not None and not isinstance(model, str):
        raise DelegationError("validation failed: invalid model value")

    full_auto = parsed["full_auto"]
    if not isinstance(full_auto, bool):
        raise DelegationError("validation failed: full_auto must be boolean")
    if full_auto and sandbox == "read-only":
        raise DelegationError("conflict: --full-auto and -s read-only are mutually exclusive")

    return {
        "prompt": prompt.strip(),
        "model": parsed.get("model"),
        "sandbox": sandbox,
        "reasoning_effort": effort,
        "full_auto": full_auto,
    }


def _check_codex_version() -> None:
    """Step 6: Verify codex CLI version >= 0.111.0."""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise DelegationError("version check failed: codex not found in PATH")
    except subprocess.TimeoutExpired:
        # B13: Catch timeout — falls to generic handler otherwise with wrong error shape
        raise DelegationError("version check failed: codex --version timed out")

    # B13: Check returncode — broken install may produce parseable version on stderr
    if result.returncode != 0:
        raise DelegationError("version check failed: codex --version returned non-zero")

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)
    if not match:
        raise DelegationError("version check failed: cannot parse codex --version output")

    version = tuple(int(x) for x in match.groups())
    if version < _MIN_VERSION:
        raise DelegationError(
            f"version check failed: codex {'.'.join(match.groups())} < 0.111.0"
        )


def _check_clean_tree() -> None:
    """Step 7: Clean-tree gate."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--ignore-submodules=none"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError as exc:
        raise GateBlockError(
            "clean-tree check failed: git not found",
            gate="git_error",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GateBlockError(
            "clean-tree check failed: git status timed out",
            gate="git_error",
        ) from exc
    # B7: Fail closed on git command failure — empty stdout could mask dirty tree
    # R6-B2: Use gate="git_error" — git command failure ≠ dirty tree;
    # gate="clean_tree" would set dirty_tree_blocked=True in analytics
    if result.returncode != 0:
        raise GateBlockError(
            "clean-tree check failed: git status returned non-zero",
            gate="git_error",
        )
    if result.stdout.strip():
        # B8: Parse NUL-separated entries correctly — rename/copy records
        # produce two NUL-separated path fields (old\0new). Split on NUL,
        # then extract paths from status-prefixed entries (3-char prefix).
        raw_parts = result.stdout.split("\0")
        paths: list[str] = []
        i = 0
        while i < len(raw_parts):
            entry = raw_parts[i]
            if not entry.strip():
                i += 1
                continue
            # R6-B6: porcelain=v1 status codes are 2 chars (XY format) —
            # entry[0] reads only index char; use entry[:2] for full status
            status_xy = entry[:2] if len(entry) >= 2 else ""
            path = entry[3:] if len(entry) > 3 else entry
            paths.append(path)
            # Rename/copy records have a second path field. Keep both path
            # tokens instead of depending on git's -z field order.
            if ("R" in status_xy or "C" in status_xy) and i + 1 < len(raw_parts):
                second_path = raw_parts[i + 1].strip()
                if second_path:
                    paths.append(second_path)
                i += 1
            i += 1
        if paths:
            raise GateBlockError(
                "dirty working tree", gate="clean_tree", paths=paths
            )


def _check_secret_files() -> None:
    """Step 8: Readable-secret-file gate.

    F5: Clean separation of exact names and glob patterns. No mixed
    iteration or startswith fallback. Each matching path is added once.
    This gate inspects gitignored/untracked files only; tracked secrets
    remain a repository-policy concern outside this check.
    """
    # B23: fnmatch imported at module level

    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError as exc:
        raise GateBlockError(
            "secret-file check failed: git not found",
            gate="git_error",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GateBlockError(
            "secret-file check failed: git ls-files timed out",
            gate="git_error",
        ) from exc
    # B7: Fail closed on git command failure — empty stdout could mask secret files
    # R6-B2: Use gate="git_error" — git command failure ≠ secret files found
    if result.returncode != 0:
        raise GateBlockError(
            "secret-file check failed: git ls-files returned non-zero",
            gate="git_error",
        )
    if not result.stdout.strip():
        return

    matched: list[str] = []
    for filepath in result.stdout.strip().split("\n"):
        filepath = filepath.strip()
        if not filepath:
            continue
        name = Path(filepath).name

        # Template exemptions (checked first)
        if name in _TEMPLATE_EXEMPTIONS:
            continue

        # Known-safe public artifacts — exempt by exact path tail
        parts = Path(filepath).parts
        if any(parts[-len(tail):] == tail for tail in _SAFE_ARTIFACT_TAILS):
            continue

        # Exact name match
        if name in _SECRET_EXACT_NAMES:
            matched.append(filepath)
            continue

        # Glob pattern match (*.pem, *.key, *.p12, .env.*)
        if any(fnmatch.fnmatch(name, pat) for pat in _SECRET_GLOBS):
            matched.append(filepath)
            continue

    if matched:
        raise GateBlockError(
            "readable secret files found", gate="secret_files", paths=matched
        )


def _build_command(
    prompt: str,
    sandbox: str,
    model: str | None,
    reasoning_effort: str,
    full_auto: bool,
    output_file: Path,
) -> list[str]:
    """Step 9: Build codex exec command."""
    cmd = ["codex", "exec", "--json", "-o", str(output_file), "-s", sandbox, "--skip-git-repo-check"]

    if model:
        cmd.extend(["-m", model])

    cmd.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])

    if full_auto:
        cmd.append("--full-auto")

    # B6: Prevent dash-prefixed prompts from being parsed as flags
    cmd.append("--")
    cmd.append(prompt)
    return cmd


def _parse_jsonl(stdout: str) -> dict:
    """Steps 11-12: Parse JSONL events from codex exec stdout."""
    thread_id: str | None = None
    commands_run: list[dict] = []
    token_usage: dict | None = None
    runtime_failures: list[str] = []
    last_message: str | None = None
    usable_count = 0
    # B9: Only known event types count as usable — unknown types are
    # silently skipped. Prevents false status=ok when all events are
    # unrecognized (e.g., fabricated thread ID from unknown events).
    # B9: Include "error" — design spec JSONL event families table lists it
    # R6-B7: Include "turn.started" and "item.started" — spec lists them as
    # "Ignored" but they must be in _KNOWN_EVENT_TYPES so they count as usable.
    # Without this, a Codex run that emits only turn.started before early failure
    # would hit usable_count==0 and raise a misleading "no usable events" error.
    _KNOWN_EVENT_TYPES = {
        "thread.started", "turn.started", "turn.completed", "turn.failed",
        "item.started", "item.completed", "error",
    }

    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print("codex-delegate: skipped malformed JSONL line", file=sys.stderr)
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        if event_type not in _KNOWN_EVENT_TYPES:
            continue
        usable_count += 1

        if event_type == "thread.started":
            # R5-I5+D1: Type guard + first-wins — keep first thread_id only
            tid = event.get("thread_id")
            if isinstance(tid, str) and thread_id is None:
                thread_id = tid

        elif event_type == "item.completed":
            item = event.get("item", {})
            # R6-B8: Structural type guard — non-dict item would crash on .get()
            if not isinstance(item, dict):
                continue
            if item.get("type") == "command_execution":
                # R5-I5: Type guard — non-string command would corrupt output
                cmd_val = item.get("command", "")
                commands_run.append({
                    "command": cmd_val if isinstance(cmd_val, str) else str(cmd_val),
                    "exit_code": item.get("exit_code"),
                })
            elif item.get("type") == "agent_message":
                # R5-I5: Type guard — non-string text would corrupt summary
                text_val = item.get("text")
                if isinstance(text_val, str):
                    last_message = text_val

        elif event_type == "turn.completed":
            # B21: Keeps last turn.completed usage only (intentional —
            # Codex exec typically has one turn; multi-turn accumulation
            # deferred to Step 1b resume support).
            usage = event.get("usage", {})
            # R6-B8: Structural type guard — non-dict usage would crash on .get()
            if not isinstance(usage, dict):
                continue
            if usage:
                token_usage = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

        elif event_type == "turn.failed":
            runtime_failures.append(str(event.get("error", "unknown error")))

        elif event_type == "error":
            # B9: Capture top-level error events for reporting
            runtime_failures.append(str(event.get("message", event.get("error", "unknown error"))))

    if usable_count == 0:
        raise DelegationError("parse failed: no usable JSONL events from codex exec")

    if thread_id is None:
        print("codex-delegate: no thread.started event, thread_id will be null", file=sys.stderr)

    return {
        "thread_id": thread_id,  # nullable — no fabricated UUIDs
        "commands_run": commands_run,
        "token_usage": token_usage,
        "runtime_failures": runtime_failures,
        "summary": last_message,
    }


def _validate_and_log(event: dict) -> None:
    """Validate then log. Fail-closed: invalid events are dropped, not appended.

    This ensures analytics stays clean. Invalid events produce a stderr warning
    for debugging but do not pollute the structured event log.
    """
    try:
        _raw_validate(event, "delegation_outcome")
    except ValueError as exc:
        print(f"codex-delegate: event dropped (validation failed): {exc}", file=sys.stderr)
        return
    if not append_log(event):
        print("codex-delegate: analytics emission failed", file=sys.stderr)


def _emit_analytics(
    phase_a: dict,
    parsed: dict | None,
    exit_code: int | None,
    blocked_by: str | None,
    dispatched: bool,
) -> None:
    """Step 13: Emit delegation_outcome event.

    F1+F8: Takes Phase A data (not validated dict) so analytics
    emits even for credential blocks and pre-Phase-B errors.
    Logs raw values including invalid ones (F13 handles downstream).
    """
    event = {
        "event": "delegation_outcome",
        "ts": ts(),
        "consultation_id": str(uuid.uuid4()),
        "session_id": session_id(),
        # R6-B11: Use .get() — parsed may be partially populated dict
        # missing "thread_id" (e.g., DelegationError during JSONL parse)
        "thread_id": parsed.get("thread_id") if parsed else None,
        "dispatched": dispatched,
        "sandbox": phase_a.get("sandbox", "workspace-write"),
        "model": phase_a.get("model"),
        "reasoning_effort": phase_a.get("reasoning_effort", "high"),
        "full_auto": phase_a.get("full_auto", False),
        "credential_blocked": blocked_by == "credential",
        "dirty_tree_blocked": blocked_by == "clean_tree",
        "readable_secret_file_blocked": blocked_by == "secret_files",
        # R6-B11: Use .get() — same partial-dict safety as thread_id
        "commands_run_count": len(parsed.get("commands_run", [])) if parsed else 0,
        "exit_code": exit_code,
        # R5-B5: Derive termination_reason from dispatched/blocked_by hierarchy
        # — prevents impossible state dispatched=false,exit_code=0 → "complete"
        # git_error gets "gate_error" (infrastructure failure, not security block)
        "termination_reason": (
            "gate_error" if blocked_by == "git_error"
            else "blocked" if blocked_by
            else "error" if not dispatched
            else "complete" if exit_code == 0
            else "error"
        ),
    }
    event["schema_version"] = _resolve_schema_version(event)
    _validate_and_log(event)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


_OUTPUT_REQUIRED = {
    "status", "dispatched", "thread_id", "summary", "commands_run",
    "exit_code", "token_usage", "runtime_failures", "blocked_paths", "error",
}


def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON.

    R7-8: Validates all required fields are present to prevent silent
    omissions when adding new status paths or exception handlers.
    """
    result: dict = {"status": status}
    result.update(kwargs)
    missing = _OUTPUT_REQUIRED - set(result.keys())
    assert not missing, f"_output missing fields: {missing}"
    return json.dumps(result)


def run(input_path: Path) -> int:
    """Execute the 14-step delegation pipeline. Returns exit code.

    F1+F8: Phase A data captured before credential scan so analytics
    can emit for all post-step-3 failures (including credential blocks).
    F6: Adapter cleans output file only (creation-ownership). Skill
    cleans its own input file.
    """
    output_file: Path | None = None
    phase_a: dict | None = None  # F1: Phase A data for analytics
    validated: dict | None = None
    parsed: dict | None = None
    did_dispatch: bool = False  # B8: Track whether subprocess actually ran
    original_cwd = Path.cwd()

    try:
        # Step 1: resolve repo root
        repo_root = _resolve_repo_root()
        os.chdir(repo_root)

        # Step 2: allocate output temp file only (F6: adapter owns output)
        fd, output_path = tempfile.mkstemp(prefix="codex_delegate_output_", suffix=".txt")
        os.close(fd)
        os.chmod(output_path, 0o600)
        output_file = Path(output_path)

        # Step 3 — Phase A: structural parse (captures data for analytics)
        phase_a = _parse_input(input_path)

        # Step 4: credential scan on prompt (governance rule 4: fail-closed)
        # R7-29: Validate prompt type before credential scan to prevent bypass.
        # Non-string prompt (e.g., list) would skip scan entirely, violating
        # governance rule 4 (fail-closed). Reject early with clear error.
        prompt = phase_a.get("prompt")
        if prompt is not None and not isinstance(prompt, str):
            raise DelegationError("validation failed: prompt must be string")
        if prompt and isinstance(prompt, str):
            try:
                scan_result = scan_text(prompt)
            except Exception as scan_exc:
                raise CredentialBlockError(
                    f"credential scan failed: {scan_exc}"
                ) from scan_exc
            if scan_result.action == "block":
                raise CredentialBlockError(scan_result.reason or "credential detected")

        # Step 5 — Phase B: field validation
        validated = _validate_input(phase_a)

        # Step 6: version check
        _check_codex_version()

        # Step 7: clean-tree gate
        _check_clean_tree()

        # Step 8: secret-file gate
        _check_secret_files()

        # Step 9: build command
        cmd = _build_command(
            prompt=validated["prompt"],
            sandbox=validated["sandbox"],
            model=validated["model"],
            reasoning_effort=validated["reasoning_effort"],
            full_auto=validated["full_auto"],
            output_file=output_file,
        )

        # Step 10: run subprocess
        # B11: Set did_dispatch BEFORE Popen — TimeoutExpired is raised from
        # proc.wait(), so setting it after would leave did_dispatch=False
        # even though the process actually ran (and may have modified files).
        did_dispatch = True
        try:
            # Keep stdout on disk so pathological output cannot be buffered
            # fully into memory before the size cap is enforced.
            with TemporaryFile() as stdout_sink, TemporaryFile() as stderr_sink:
                proc = subprocess.Popen(
                    cmd,
                    stdout=stdout_sink,
                    stderr=stderr_sink,
                    text=False,
                )
                try:
                    proc.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    raise DelegationError("exec failed: process timeout")

                stdout_sink.seek(0, os.SEEK_END)
                stdout_size = stdout_sink.tell()
                stdout_sink.seek(0)
                stdout_bytes = stdout_sink.read(_STDOUT_MAX_BYTES + 1)
        except FileNotFoundError:
            # R5-B4: Codex binary not found at exec time (different from version check)
            raise DelegationError("exec failed: subprocess spawn error. codex not found")

        if stdout_size > _STDOUT_MAX_BYTES:
            print("codex-delegate: stdout truncated (exceeded 50MB cap)", file=sys.stderr)
        stdout = stdout_bytes[:_STDOUT_MAX_BYTES].decode("utf-8", errors="replace")

        # R7-27: Capture returncode before _parse_jsonl so it's available in error output
        returncode = proc.returncode

        # Steps 11-12: parse JSONL + read output file
        parsed = _parse_jsonl(stdout)

        # Read -o output for summary (nullable)
        if output_file.exists():
            try:
                content = output_file.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError) as exc:
                print(f"codex-delegate: output read failed: {exc}", file=sys.stderr)
            else:
                if content:
                    parsed["summary"] = content

        # Step 13: emit analytics
        _emit_analytics(phase_a, parsed, returncode, None, dispatched=True)

        # Return structured output
        # R5-B1: Include dispatched field — enables skill to branch on error+dispatched
        # R6-B1: blocked_paths always present (empty list for non-blocked)
        print(_output(
            "ok",
            dispatched=True,
            thread_id=parsed["thread_id"],
            summary=parsed["summary"],
            commands_run=parsed["commands_run"],
            exit_code=returncode,
            token_usage=parsed["token_usage"],
            runtime_failures=parsed["runtime_failures"],
            blocked_paths=[],
            error=None,
        ))
        return 0

    except CredentialBlockError as exc:
        # F1+F8: Always emit — phase_a is set (step 3 succeeded)
        if phase_a:
            _emit_analytics(phase_a, None, None, "credential", dispatched=False)
        # R5-B1: dispatched=False for credential blocks
        # R6-B1: blocked_paths always present
        print(_output("blocked", dispatched=False, error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None, runtime_failures=[],
                       blocked_paths=[]))
        return 0

    except GateBlockError as exc:
        if phase_a:
            _emit_analytics(phase_a, None, None, exc.gate, dispatched=False)
        # R5-B1: dispatched=False for gate blocks
        print(_output("blocked", dispatched=False, error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None,
                       runtime_failures=[], blocked_paths=exc.paths))
        return 0

    except DelegationError as exc:
        # B8: Use did_dispatch to correctly report whether subprocess ran
        if phase_a:
            _emit_analytics(phase_a, parsed, None, None, dispatched=did_dispatch)
        # R5-B1: dispatched=did_dispatch — skill needs this to decide whether to review changes
        # R6-B1: blocked_paths always present
        print(_output("error", dispatched=did_dispatch, error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None, runtime_failures=[],
                       blocked_paths=[]))
        return 1

    except Exception as exc:
        # B8: Use did_dispatch — generic handler may catch post-dispatch failures
        if phase_a:
            _emit_analytics(phase_a, parsed, None, None, dispatched=did_dispatch)
        # R5-B1: dispatched=did_dispatch
        # R6-B1: blocked_paths always present
        print(_output("error", dispatched=did_dispatch, error=f"internal error: {exc}", thread_id=None,
                       summary=None, commands_run=[], exit_code=None,
                       token_usage=None, runtime_failures=[], blocked_paths=[]))
        return 1

    finally:
        # Step 14: cleanup
        if output_file:
            try:
                output_file.unlink(missing_ok=True)
            except OSError as exc:
                print(f"codex-delegate: output cleanup failed: {exc}", file=sys.stderr)
        try:
            os.chdir(original_cwd)
        except OSError as exc:
            print(f"codex-delegate: cwd restore failed: {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2:
        print(_output("error", error="usage: codex_delegate.py <input_file.json>",
                       dispatched=False, thread_id=None, summary=None, commands_run=[],
                       exit_code=None, token_usage=None, runtime_failures=[], blocked_paths=[]))
        return 1
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
