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
SHELL_METACHAR_RE = re.compile(r"[|;&`$><]")


def _plugin_root() -> str:
    """Return plugin root directory, preferring CLAUDE_PLUGIN_ROOT env var."""
    return os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))


def _build_allowlist_pattern(plugin_root: str) -> re.Pattern[str]:
    """Build the allowlist regex anchored to the plugin root."""
    escaped = re.escape(plugin_root)
    return re.compile(
        rf"^python3\s+{escaped}/scripts/ticket_engine_(user|agent)\.py\s+(\w+)\s+(.+)$"
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
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return f"Payload write failed: {exc}"

    return None


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

    # Non-ticket commands pass through.
    if "ticket_engine" not in command:
        print("{}")
        return

    # --- From here, the command mentions ticket_engine. Apply strict checks. ---

    # Block shell metacharacters.
    if SHELL_METACHAR_RE.search(command):
        print(json.dumps(_make_deny(
            f"Shell metacharacters detected in ticket engine command. Got: {command!r:.100}"
        )))
        return

    # Match against allowlist.
    plugin_root = _plugin_root()
    pattern = _build_allowlist_pattern(plugin_root)
    match = pattern.match(command)

    if not match:
        print(json.dumps(_make_deny(
            f"Command does not match ticket engine allowlist. Got: {command!r:.100}"
        )))
        return

    entrypoint_type = match.group(1)  # "user" or "agent"
    subcommand = match.group(2)
    payload_path = match.group(3)

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

    # Inject trust fields into payload.
    session_id = event.get("session_id", "")
    error = _inject_payload(payload_path, session_id, entrypoint_type)
    if error is not None:
        print(json.dumps(_make_deny(f"Payload injection failed: {error}")))
        return

    print(json.dumps(_make_allow(
        f"Ticket engine {entrypoint_type}/{subcommand} validated and payload injected"
    )))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail open on unhandled exceptions — exit 0 with empty JSON.
        print("{}")
        sys.exit(0)
