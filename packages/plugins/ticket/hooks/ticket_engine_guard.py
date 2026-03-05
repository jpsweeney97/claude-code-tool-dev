#!/usr/bin/env python3
"""PreToolUse hook: validates ticket engine invocations and injects trust fields.

Allowlist matching:
- Permits only exact engine invocation shapes matching the pattern:
    python3 <PLUGIN_ROOT>/scripts/ticket_engine_(user|agent).py <subcommand> <path>
- Valid subcommands: classify, plan, preflight, execute.
- Blocks commands with shell metacharacters, extra arguments, or unknown subcommands.
- Non-ticket Bash commands pass through silently (empty JSON).

Payload injection (atomic):
- Injects session_id, hook_injected, hook_request_origin into the payload file.
- Resolves payload path relative to hook cwd and denies paths outside workspace root.
- Uses temp file + fsync + os.replace for atomic writes.
- Denies on any injection failure (unreadable file, invalid JSON, write error).

Exit code always 0 (fail-open on crash — accepted v1.0 limitation).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

VALID_SUBCOMMANDS = frozenset({"classify", "plan", "preflight", "execute"})

# Shell metacharacters that indicate command chaining or redirection.
SHELL_METACHAR_RE = re.compile(r"[|;&`$><\n\r]")


def _plugin_root() -> str:
    """Return plugin root directory, preferring CLAUDE_PLUGIN_ROOT env var."""
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def _build_allowlist_pattern(plugin_root: str) -> re.Pattern[str]:
    """Build the allowlist regex anchored to the plugin root."""
    escaped = re.escape(plugin_root)
    return re.compile(
        rf"^python3\s+{escaped}/scripts/ticket_engine_(user|agent)\.py\s+(\w+)\s+(.+)$"
    )


def _build_readonly_pattern(plugin_root: str) -> re.Pattern[str]:
    """Build pattern for read-only ticket scripts (no payload injection)."""
    escaped = re.escape(plugin_root)
    return re.compile(
        rf"^python3\s+{escaped}/scripts/ticket_(read|triage)\.py\s+(\w+)\s+(.+)$"
    )


def _is_ticket_invocation(command: str) -> bool:
    """Check if command is a Python invocation that might target ticket scripts.

    Intentionally broad — catches non-canonical Python launcher forms:
    python, python3, python3.11, /usr/bin/python3, /usr/local/bin/python3.11,
    env python3, env PYTHONPATH=. python3, PYTHONPATH=. python3,
    as well as relative paths and path traversal in the script argument.
    Exact validation happens in branches 1-3; branch 3 denies anything that
    doesn't match the explicit allowlists.

    Non-python commands (cat, rg, wc) pass through — they don't match the
    Python launcher prefix so this returns False (branch 4).
    """
    return bool(
        re.match(
            r"^(?:env\s+)?(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:/\S+/)?python[\d.]*\s+",
            command,
        )
        and re.search(r"\bscripts/ticket_\w+\.py\b", command)
    )


def _make_allow(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }


def _make_deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _inject_payload(
    payload_path: str,
    session_id: str,
    request_origin: str,
) -> str | None:
    """Inject trust fields into the payload file atomically.

    Returns None on success, or an error message string on failure.
    """
    path = Path(payload_path)

    # Read existing payload.
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Payload unreadable: {exc}"

    # Parse JSON.
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return f"Payload invalid JSON: {exc}"

    if not isinstance(payload, dict):
        return f"Payload is not a JSON object, got {type(payload).__name__}"

    # Inject trust fields.
    payload["session_id"] = session_id
    payload["hook_injected"] = True
    payload["hook_request_origin"] = request_origin

    # Atomic write: temp file in same directory -> fsync -> os.replace.
    parent = path.parent
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix=".tmp")
        try:
            data = json.dumps(payload, indent=2).encode("utf-8")
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, str(path))
    except OSError as exc:
        # Clean up temp file on failure.
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return f"Payload write failed: {exc}"

    return None


def _resolve_payload_path(payload_path: str, workspace_root: str) -> tuple[Path | None, str | None]:
    """Resolve payload path and enforce workspace-root containment."""
    if not isinstance(workspace_root, str) or not workspace_root:
        return None, f"Invalid workspace root. Got: {workspace_root!r:.100}"
    try:
        root = Path(workspace_root).resolve()
        candidate = Path(payload_path)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    except OSError as exc:
        return None, f"Payload path resolution failed: {exc}. Got: {payload_path!r:.100}"
    try:
        resolved.relative_to(root)
    except ValueError:
        return (
            None,
            f"Payload path outside workspace root {str(root)!r}. Got: {payload_path!r:.100}",
        )
    return resolved, None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed input — fail open.
        print("{}")
        return

    # Non-Bash tools pass through.
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        print("{}")
        return

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")

    # Branch 4: Non-ticket-script invocations pass through (cat, rg, wc, etc.).
    # Only python3 invocations of ticket_*.py scripts enter strict checks.
    plugin_root = _plugin_root()
    if not _is_ticket_invocation(command):
        print("{}")
        return

    # --- From here, command is a python3 invocation of a ticket script. ---

    # Block shell metacharacters.
    if SHELL_METACHAR_RE.search(command):
        print(json.dumps(_make_deny(
            f"Shell metacharacters detected in ticket engine command. Got: {command!r:.100}"
        )))
        return

    # Branch 1: Engine exact allowlist → validate subcommand/payload + inject.
    engine_pattern = _build_allowlist_pattern(plugin_root)
    engine_match = engine_pattern.match(command)

    if engine_match:
        entrypoint_type = engine_match.group(1)  # "user" or "agent"
        subcommand = engine_match.group(2)
        payload_path = engine_match.group(3)

        # Validate subcommand.
        if subcommand not in VALID_SUBCOMMANDS:
            print(json.dumps(_make_deny(
                f"Unknown subcommand '{subcommand}'. Valid: {sorted(VALID_SUBCOMMANDS)}"
            )))
            return

        # Check for extra arguments (payload_path should not contain whitespace).
        if re.search(r"\s", payload_path):
            print(json.dumps(_make_deny(
                f"Extra arguments after payload path. Got: {command!r:.100}"
            )))
            return

        workspace_root = event.get("cwd", "")
        resolved_path, path_error = _resolve_payload_path(payload_path, workspace_root)
        if path_error is not None or resolved_path is None:
            print(json.dumps(_make_deny(
                f"Payload path validation failed: {path_error or 'unknown error'}"
            )))
            return

        # Inject trust fields into payload.
        session_id = event.get("session_id", "")
        error = _inject_payload(str(resolved_path), session_id, entrypoint_type)
        if error is not None:
            print(json.dumps(_make_deny(f"Payload injection failed: {error}")))
            return

        print(json.dumps(_make_allow(
            f"Ticket engine {entrypoint_type}/{subcommand} validated and payload injected"
        )))
        return

    # Branch 2: Read-only scripts (ticket_read.py, ticket_triage.py) → allow, no injection.
    readonly_pattern = _build_readonly_pattern(plugin_root)
    readonly_match = readonly_pattern.match(command)
    if readonly_match:
        script_name = readonly_match.group(1)  # "read" or "triage"
        subcommand = readonly_match.group(2)
        print(json.dumps(_make_allow(
            f"Ticket {script_name}/{subcommand} validated (read-only)"
        )))
        return

    # Branch 3: Unrecognized ticket script invocation → deny.
    print(json.dumps(_make_deny(
        f"Command invokes unrecognized ticket script. Got: {command!r:.100}"
    )))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail open on unhandled exceptions — exit 0 with empty JSON.
        print("{}")
        sys.exit(0)
