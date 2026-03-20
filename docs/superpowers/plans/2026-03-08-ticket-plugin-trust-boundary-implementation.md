# Ticket Plugin Trust Boundary & Data Integrity — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Harden the ticket plugin's trust boundary and data integrity, implementing the remediation plan at `docs/plans/2026-03-08-ticket-plugin-trust-boundary-and-data-Integrity.md`.

**Architecture:** Two patches. Patch 1 (Tasks 1–6) hardens the trust boundary: shlex-based hook prefilter, explicit agent_id origin helper, guarded execute at both entrypoint and engine layers, and structural stage prerequisites. Patch 2 (Tasks 7–9) adds schema validation, marker-based project-root resolution, and contract/doc/test alignment. Each task is TDD: write failing tests first, then implement.

**Tech Stack:** Python 3.12+, pytest, shlex, hashlib, pathlib. Run tests: `cd packages/plugins/ticket && uv run pytest tests/ -q`

**Working branch:** `fix/ticket-plugin-trust-boundary`

**Baseline:** 398 tests, all passing.

---

## Patch 1: Trust Boundary Hardening

### Task 1: Replace `_is_ticket_invocation()` with shlex-based candidate detection

The current regex-based `_is_ticket_invocation()` in `hooks/ticket_engine_guard.py:63–82` has a leading-space bypass: `" python3 ...ticket_engine_user.py..."` fails the `^` anchor, falls through to branch 4 (pass-through), and runs unhooked. Replace with `shlex.split()`-based parsing that detects ticket script basenames in the script-operand position of a Python-like launcher.

**Files:**
- Modify: `hooks/ticket_engine_guard.py:63–82` (replace `_is_ticket_invocation`)
- Modify: `hooks/ticket_engine_guard.py:196–208` (add `lstrip()` + reorder `2>&1` stripping before candidate detection)
- Test: `tests/test_hook.py`

**Step 1: Write failing tests for the new prefilter**

Add these tests to `tests/test_hook.py`. They exercise the new detection logic. The leading-space and env-launcher tests should currently pass through (no deny) because `_is_ticket_invocation()` misses them.

```python
# --- In test_hook.py, new class after existing tests ---

class TestCandidateDetection:
    """Tests for shlex-based ticket command candidate detection."""

    # --- Leading-space bypass (F-001) ---
    def test_leading_space_denied(self, tmp_path):
        """Leading space must not bypass hook — detected as candidate, denied as non-canonical."""
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f" python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_leading_tabs_denied(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"\tpython3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    # --- env launcher variants (detected as candidate → denied as non-canonical) ---
    def test_env_python3_denied(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"/usr/bin/env python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_env_with_var_denied(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"env PYTHONPATH=. python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    # --- Versioned python (detected as candidate → denied as non-canonical) ---
    def test_versioned_python_denied(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3.12 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_absolute_python_denied(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"/usr/bin/python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    # --- Non-ticket commands pass through ---
    def test_non_ticket_python_passes_through(self, tmp_path):
        """Python invocations that don't target ticket scripts pass through."""
        result = run_hook(make_hook_input("python3 setup.py install", cwd=str(tmp_path)))
        assert result == {} or result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_grep_for_ticket_script_name_passes_through(self, tmp_path):
        """Non-python commands mentioning ticket script basenames pass through."""
        result = run_hook(make_hook_input("rg ticket_engine_user.py README.md", cwd=str(tmp_path)))
        assert result == {} or result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    # --- Malformed quoting with ticket basename → deny ---
    def test_malformed_quoting_with_ticket_basename_denied(self, tmp_path):
        """shlex.split failure + ticket basename in raw string → deny."""
        plugin_root = str(Path(__file__).parent.parent)
        cmd = f"python3 '{plugin_root}/scripts/ticket_engine_user.py classify"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    # --- Malformed quoting without ticket basename → pass through ---
    def test_malformed_quoting_without_ticket_basename_passes(self, tmp_path):
        cmd = "python3 'some_other_script.py"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result == {} or result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    # --- Canonical form still allowed ---
    def test_canonical_user_still_allowed(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"

    def test_canonical_agent_still_allowed(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_agent.py classify {payload}"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"

    def test_canonical_with_2>&1_still_allowed(self, tmp_path):
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py execute {payload} 2>&1"
        result = run_hook(make_hook_input(cmd, cwd=str(tmp_path)))
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_hook.py::TestCandidateDetection -v
```

Expected: `test_leading_space_denied`, `test_leading_tabs_denied`, `test_env_python3_denied`, `test_env_with_var_denied`, `test_versioned_python_denied`, `test_absolute_python_denied`, and `test_malformed_quoting_with_ticket_basename_denied` FAIL (currently pass through as non-ticket commands).

**Step 3: Implement shlex-based candidate detection**

Replace `_is_ticket_invocation()` (lines 63–82) with:

```python
import shlex

# Known ticket script basenames for candidate detection.
_TICKET_SCRIPT_BASENAMES = frozenset({
    "ticket_engine_user.py",
    "ticket_engine_agent.py",
    "ticket_read.py",
    "ticket_triage.py",
    "ticket_audit.py",
})

# Python-like launcher basenames.
_PYTHON_LAUNCHER_RE = re.compile(r"^python[\d.]*$")


def _is_ticket_candidate(command: str) -> bool:
    """Detect if command is a Python invocation targeting a known ticket script.

    Uses shlex.split() for token-based parsing. Identifies the script operand
    to a Python-like launcher and checks if its basename is a known ticket script.

    Supports:
    - Direct: python3 script.py
    - Versioned: python3.12 script.py
    - Absolute: /usr/bin/python3 script.py
    - env: env python3 script.py
    - env with vars: env KEY=VAL python3 script.py
    - Leading env assignments: KEY=VAL python3 script.py

    Returns True if detected as a ticket script candidate (routes to exact
    allowlist validation in branches 1-3). False means pass-through (branch 4).
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        # shlex.split() failed (unclosed quote, etc.).
        # If the raw command mentions a known ticket script basename, deny
        # as malformed; otherwise pass through.
        return any(basename in command for basename in _TICKET_SCRIPT_BASENAMES)

    if not tokens:
        return False

    # Find the Python launcher token, skipping:
    # - "env" or absolute-path env (e.g., /usr/bin/env)
    # - Environment variable assignments (KEY=VALUE)
    i = 0

    # Skip env launcher if present.
    if tokens[i] == "env" or (tokens[i].endswith("/env") and "/" in tokens[i]):
        i += 1

    # Skip environment variable assignments (KEY=VALUE before Python token).
    while i < len(tokens) and re.match(r"^[A-Z_][A-Z0-9_]*=", tokens[i]):
        i += 1

    if i >= len(tokens):
        return False

    # Check if current token is a Python launcher.
    launcher = tokens[i]
    launcher_basename = launcher.rsplit("/", 1)[-1] if "/" in launcher else launcher
    if not _PYTHON_LAUNCHER_RE.match(launcher_basename):
        return False

    # Next token after launcher is the script argument.
    script_idx = i + 1
    if script_idx >= len(tokens):
        return False

    script_path = tokens[script_idx]
    script_basename = script_path.rsplit("/", 1)[-1] if "/" in script_path else script_path
    return script_basename in _TICKET_SCRIPT_BASENAMES
```

Then update `main()` to normalize before candidate detection. Replace lines 196–208 with:

```python
    # Normalize: strip leading whitespace and trailing 2>&1 before candidate detection.
    command_normalized = command.lstrip()
    command_clean = re.sub(r"\s+2>&1\s*$", "", command_normalized)

    # Branch 4: Non-ticket-script invocations pass through.
    plugin_root = _plugin_root()
    if not _is_ticket_candidate(command_clean):
        print("{}")
        return

    # --- From here, command is a candidate ticket script invocation. ---

    # Block shell metacharacters.
    if SHELL_METACHAR_RE.search(command_clean):
        # ...existing code...
```

Note: the existing allowlist patterns (branches 1, 2, 2b) match against `command_clean`, which is now normalized. This is correct because `lstrip()` + `2>&1` stripping produce the same canonical form the patterns expect.

**Step 4: Run all hook tests**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_hook.py tests/test_hook_integration.py -v
```

Expected: ALL pass (new + existing).

**Step 5: Commit**

```bash
git add hooks/ticket_engine_guard.py tests/test_hook.py
git commit -m "fix(ticket): replace regex prefilter with shlex-based candidate detection

Closes the leading-space bypass (F-001): _is_ticket_invocation() used
a ^ anchor that missed whitespace-prefixed commands. The new
_is_ticket_candidate() uses shlex.split() to find the script operand
by position, detecting python/env launcher variants and routing them
to exact allowlist validation (branch 3 deny).

Also normalizes with lstrip() before candidate detection and reorders
2>&1 stripping to happen before detection rather than after."
```

---

### Task 2: Shared origin helper for explicit `agent_id` handling

The hook currently uses truthiness-based `event.get("agent_id")` at two locations: engine trust injection (line 250) and audit user-only gate (line 276). `agent_id=""` or `agent_id=0` would incorrectly classify as "user". Replace with a shared helper that distinguishes missing (user), non-empty string (agent), and present-but-invalid (deny).

**Files:**
- Modify: `hooks/ticket_engine_guard.py:250` (engine branch)
- Modify: `hooks/ticket_engine_guard.py:276` (audit branch)
- Test: `tests/test_hook.py`

**Step 1: Write failing tests**

```python
class TestAgentIdOriginHelper:
    """Tests for explicit agent_id handling in all hook branches."""

    # --- Engine branch: empty string agent_id should deny ---
    def test_engine_empty_agent_id_denied(self, tmp_path):
        """Present-but-empty agent_id on engine command → deny as malformed."""
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = ""  # Present but empty.
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_engine_non_string_agent_id_denied(self, tmp_path):
        """Non-string agent_id (e.g., int) on engine command → deny."""
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = 42
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_engine_missing_agent_id_is_user(self, tmp_path):
        """Missing agent_id key → user origin, allowed."""
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py classify {payload}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        assert "agent_id" not in hook_input  # Confirm missing.
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"
        # Verify injected origin is "user".
        injected = json.loads(Path(payload).read_text(encoding="utf-8"))
        assert injected["hook_request_origin"] == "user"

    def test_engine_valid_agent_id_is_agent(self, tmp_path):
        """Non-empty string agent_id → agent origin."""
        plugin_root = str(Path(__file__).parent.parent)
        payload = make_payload_file(tmp_path)
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_agent.py classify {payload}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = "agent-123"
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"
        injected = json.loads(Path(payload).read_text(encoding="utf-8"))
        assert injected["hook_request_origin"] == "agent"

    # --- Audit branch: empty/non-string agent_id should deny ---
    def test_audit_empty_agent_id_denied(self, tmp_path):
        """Present-but-empty agent_id on audit command → deny."""
        plugin_root = str(Path(__file__).parent.parent)
        cmd = f"python3 {plugin_root}/scripts/ticket_audit.py list /tmp/payload.json"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = ""
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_audit_non_string_agent_id_denied(self, tmp_path):
        """Non-string agent_id on audit command → deny."""
        plugin_root = str(Path(__file__).parent.parent)
        cmd = f"python3 {plugin_root}/scripts/ticket_audit.py list /tmp/payload.json"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = 0
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_audit_valid_agent_id_denied(self, tmp_path):
        """Valid agent_id on audit command → deny (audit is user-only)."""
        plugin_root = str(Path(__file__).parent.parent)
        cmd = f"python3 {plugin_root}/scripts/ticket_audit.py list /tmp/payload.json"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["agent_id"] = "agent-456"
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_audit_missing_agent_id_allowed(self, tmp_path):
        """Missing agent_id on audit command → user → allowed."""
        plugin_root = str(Path(__file__).parent.parent)
        cmd = f"python3 {plugin_root}/scripts/ticket_audit.py list /tmp/payload.json"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        assert "agent_id" not in hook_input
        result = run_hook(hook_input)
        assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "allow"
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_hook.py::TestAgentIdOriginHelper -v
```

Expected: `test_engine_empty_agent_id_denied`, `test_engine_non_string_agent_id_denied`, `test_audit_empty_agent_id_denied`, `test_audit_non_string_agent_id_denied` FAIL (currently treated as falsy → user → allowed).

**Step 3: Implement shared origin helper**

Add to `hooks/ticket_engine_guard.py`, before `main()`:

```python
def _resolve_origin(
    event: dict, *, is_ticket_candidate: bool
) -> tuple[str | None, str | None]:
    """Determine request origin from agent_id field.

    Returns (origin, error):
    - ("user", None): agent_id key missing → user origin
    - ("agent", None): agent_id is a non-empty string → agent origin
    - (None, reason): present-but-empty or non-string agent_id on a ticket
      candidate command → deny with reason
    """
    if "agent_id" not in event:
        return "user", None

    agent_id = event["agent_id"]
    if isinstance(agent_id, str) and agent_id:
        return "agent", None

    if is_ticket_candidate:
        return None, (
            f"Malformed agent_id: expected non-empty string or absent, "
            f"got {type(agent_id).__name__}={agent_id!r:.50}"
        )

    # Non-ticket commands with weird agent_id: pass through (not our concern).
    return "user", None
```

Replace line 250 (`effective_origin = "agent" if event.get("agent_id") else "user"`) with:

```python
        effective_origin, origin_error = _resolve_origin(event, is_ticket_candidate=True)
        if origin_error is not None:
            print(json.dumps(_make_deny(origin_error)))
            return
```

Replace lines 275–280 (audit branch agent check) with:

```python
    if audit_match:
        origin, origin_error = _resolve_origin(event, is_ticket_candidate=True)
        if origin_error is not None:
            print(json.dumps(_make_deny(origin_error)))
            return
        if origin == "agent":
            print(json.dumps(_make_deny(
                "Ticket audit is user-only — agents cannot invoke audit repair"
            )))
            return
```

**Step 4: Run all hook tests**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_hook.py tests/test_hook_integration.py -v
```

Expected: ALL pass.

**Step 5: Commit**

```bash
git add hooks/ticket_engine_guard.py tests/test_hook.py
git commit -m "fix(ticket): replace truthiness agent_id checks with explicit origin helper

Introduces _resolve_origin() that distinguishes missing agent_id (user),
non-empty string (agent), and present-but-invalid (deny). Applied to
both engine trust injection (line 250) and audit user-only gate (line 276).

Closes the gap where agent_id='' or agent_id=0 silently classified as
user origin, bypassing agent restrictions."
```

---

### Task 3: Guard `execute` at entrypoint layer

Both entrypoints (`ticket_engine_user.py:47–48`, `ticket_engine_agent.py:47–48`) currently have `if hook_origin is not None and hook_origin != REQUEST_ORIGIN` — the `is not None` guard allows unhooked invocations through for execute. Remove this escape hatch for execute only; keep non-execute stages directly runnable.

**Files:**
- Modify: `scripts/ticket_engine_user.py:46–55` (execute guard)
- Modify: `scripts/ticket_engine_agent.py:46–55` (execute guard)
- Test: `tests/test_entrypoints.py`

**Step 1: Write failing tests**

```python
class TestExecuteTrustTriple:
    """Execute requires the full trust triple at the entrypoint layer."""

    def test_user_execute_without_hook_rejected(self, tmp_path):
        """User execute without hook_injected is rejected."""
        payload = {
            "action": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
        }
        result = run_entrypoint("ticket_engine_user.py", "execute", payload, tmp_path)
        assert result.get("error_code") == "policy_blocked" or result.get("state") == "policy_blocked"

    def test_user_execute_without_session_id_rejected(self, tmp_path):
        """User execute with hook_injected but empty session_id is rejected."""
        payload = {
            "action": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
            "hook_injected": True,
            "hook_request_origin": "user",
            "session_id": "",
        }
        result = run_entrypoint("ticket_engine_user.py", "execute", payload, tmp_path)
        assert result.get("error_code") == "policy_blocked" or result.get("state") == "policy_blocked"

    def test_user_execute_without_hook_request_origin_rejected(self, tmp_path):
        """User execute with hook_injected but missing hook_request_origin is rejected."""
        payload = {
            "action": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
            "hook_injected": True,
            "session_id": "test-session",
            # hook_request_origin missing
        }
        result = run_entrypoint("ticket_engine_user.py", "execute", payload, tmp_path)
        assert result.get("error_code") in ("policy_blocked", "origin_mismatch") or result.get("state") == "policy_blocked"

    def test_agent_execute_without_hook_rejected(self, tmp_path):
        """Agent execute without hook_injected is rejected."""
        payload = {
            "action": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
        }
        result = run_entrypoint("ticket_engine_agent.py", "execute", payload, tmp_path)
        assert result.get("error_code") == "policy_blocked" or result.get("state") == "policy_blocked"

    def test_user_classify_without_hook_allowed(self, tmp_path):
        """Non-execute stages remain directly runnable without hook metadata."""
        payload = {"action": "create", "args": {}}
        result = run_entrypoint("ticket_engine_user.py", "classify", payload, tmp_path)
        assert result.get("state") == "ok"

    def test_user_plan_without_hook_allowed(self, tmp_path):
        """Plan stage works without hook metadata."""
        payload = {
            "action": "create",
            "intent": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
        }
        result = run_entrypoint("ticket_engine_user.py", "plan", payload, tmp_path)
        assert result.get("state") in ("ok", "duplicate_candidate")

    def test_user_execute_with_full_trust_triple_allowed(self, tmp_path):
        """User execute with complete trust triple succeeds."""
        payload = {
            "action": "create",
            "fields": {"title": "Test", "problem": "Problem", "priority": "medium"},
            "hook_injected": True,
            "hook_request_origin": "user",
            "session_id": "test-session",
        }
        result = run_entrypoint("ticket_engine_user.py", "execute", payload, tmp_path)
        assert result.get("state") == "ok_create"
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py::TestExecuteTrustTriple -v
```

Expected: `test_user_execute_without_hook_rejected`, `test_user_execute_without_session_id_rejected`, `test_user_execute_without_hook_request_origin_rejected` FAIL (currently allowed through for users).

**Step 3: Implement entrypoint execute guard**

In `scripts/ticket_engine_user.py`, replace lines 46–55 with:

```python
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
```

Apply the identical change to `scripts/ticket_engine_agent.py`.

**Step 4: Run all entrypoint tests**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v
```

Expected: ALL pass. Some existing tests may need `hook_injected=True`, `hook_request_origin`, and `session_id` added to their payloads — update those tests to include the trust triple for execute calls.

**Step 5: Commit**

```bash
git add scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/test_entrypoints.py
git commit -m "fix(ticket): guard execute at entrypoint layer with full trust triple

Execute now requires hook_injected=True, hook_request_origin matching
REQUEST_ORIGIN, and non-empty session_id at both user and agent entrypoints.
Non-execute stages (classify, plan, preflight) remain directly runnable
without hook metadata.

Removes the 'hook_origin is not None' escape hatch that allowed unhooked
execute invocations to bypass trust validation."
```

---

### Task 4: Guard `execute` at engine layer (defense-in-depth)

`engine_execute()` in `ticket_engine_core.py:983` currently only checks `hook_injected` for agents (line 1021). Extend to require the full trust triple for all origins, add `hook_request_origin` parameter, and remove the agent-only restriction.

**Files:**
- Modify: `scripts/ticket_engine_core.py:983–1027` (engine_execute signature + trust validation)
- Modify: `scripts/ticket_engine_user.py` (pass `hook_request_origin` in dispatch)
- Modify: `scripts/ticket_engine_agent.py` (pass `hook_request_origin` in dispatch)
- Test: `tests/test_engine.py`, `tests/test_autonomy.py`

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
class TestExecuteTrustTripleEngine:
    """engine_execute() requires full trust triple for all origins."""

    def test_user_execute_without_hook_injected_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="test-session", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=False,
            hook_request_origin="user",
        )
        assert resp.state == "policy_blocked"

    def test_user_execute_without_hook_request_origin_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="test-session", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            # hook_request_origin not passed (defaults to None)
        )
        assert resp.state == "policy_blocked"

    def test_user_execute_with_mismatched_hook_origin_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="test-session", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            hook_request_origin="agent",
        )
        assert resp.error_code == "origin_mismatch"

    def test_user_execute_with_full_triple_succeeds(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="test-session", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            hook_request_origin="user",
        )
        assert resp.state == "ok_create"
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestExecuteTrustTripleEngine -v
```

Expected: `test_user_execute_without_hook_injected_rejected` and `test_user_execute_without_hook_request_origin_rejected` FAIL (currently allowed for users). `test_user_execute_with_mismatched_hook_origin_rejected` FAIL (`hook_request_origin` not a parameter yet).

**Step 3: Implement engine-layer trust triple**

Modify `engine_execute()` signature at line 983 — add `hook_request_origin` parameter:

```python
def engine_execute(
    *,
    action: str,
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    dedup_override: bool,
    dependency_override: bool,
    tickets_dir: Path,
    target_fingerprint: str | None = None,
    autonomy_config: AutonomyConfig | None = None,
    hook_injected: bool = False,
    hook_request_origin: str | None = None,
) -> EngineResponse:
```

Replace lines 1019–1027 (the agent-only hook_injected check and user comment) with:

```python
    # --- Transport-layer trust triple (defense-in-depth for all origins) ---
    trust_errors: list[str] = []
    if not hook_injected:
        trust_errors.append("hook_injected=False")
    if hook_request_origin is None:
        trust_errors.append("hook_request_origin missing")
    elif hook_request_origin != request_origin:
        return EngineResponse(
            state="escalate",
            message=f"origin_mismatch: request_origin={request_origin!r}, hook_request_origin={hook_request_origin!r}",
            error_code="origin_mismatch",
        )
    if not session_id:
        trust_errors.append("session_id empty")
    if trust_errors:
        return EngineResponse(
            state="policy_blocked",
            message=f"Execute requires verified hook provenance: {', '.join(trust_errors)}",
            error_code="policy_blocked",
        )
```

Update both entrypoint `_dispatch()` functions to pass `hook_request_origin`:

```python
    # In _dispatch, execute branch:
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
    )
```

**Step 4: Update existing tests**

All existing `engine_execute()` calls with `request_origin="user"` that currently omit `hook_injected` (or set it to False) need updating. There are ~65 calls in `test_engine.py` and a few in `test_autonomy_integration.py`.

For every `engine_execute()` call in existing tests:
- Add `hook_injected=True`
- Add `hook_request_origin=<matching request_origin>`

Example — `test_engine.py` line 841 currently:
```python
resp = engine_execute(
    action="create", ticket_id=None,
    fields={"title": "Test ticket", "problem": "A test problem."},
    session_id="test-session", request_origin="user",
    dedup_override=False, dependency_override=False,
    tickets_dir=tmp_tickets,
)
```

Update to:
```python
resp = engine_execute(
    action="create", ticket_id=None,
    fields={"title": "Test ticket", "problem": "A test problem."},
    session_id="test-session", request_origin="user",
    dedup_override=False, dependency_override=False,
    tickets_dir=tmp_tickets,
    hook_injected=True, hook_request_origin="user",
)
```

For agent calls in `test_autonomy.py`, add `hook_request_origin="agent"` alongside existing `hook_injected=True`.

Also update `test_autonomy.py:445` (`test_agent_execute_allows_when_live_config_auto_audit_and_no_snapshot`) — this test now requires `autonomy_config` (see Task 5), but for now just add `hook_request_origin="agent"`.

**Step 5: Run full test suite**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Expected: ALL pass.

**Step 6: Commit**

```bash
git add scripts/ticket_engine_core.py scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/test_engine.py tests/test_autonomy.py tests/test_autonomy_integration.py
git commit -m "fix(ticket): enforce trust triple in engine_execute for all origins

engine_execute() now requires hook_injected=True, hook_request_origin
matching request_origin, and non-empty session_id for both user and agent
execute calls. This is defense-in-depth: entrypoints check first, engine
rechecks.

Removes the agent-only restriction on hook_injected. User mutations
without verified hook provenance are now rejected, not silently allowed."
```

---

### Task 5: Structural stage prerequisites in `execute`

`engine_execute()` currently does not require prior-stage artifacts. Add mandatory parameters: `classify_intent`, `classify_confidence`, `dedup_fingerprint` (create only). Make `autonomy_config` required for agents. Make `target_fingerprint` mandatory for non-create.

**Files:**
- Modify: `scripts/ticket_engine_core.py:983` (engine_execute signature + validation)
- Modify: `scripts/ticket_engine_user.py` (extract new fields from payload)
- Modify: `scripts/ticket_engine_agent.py` (extract new fields from payload)
- Test: `tests/test_engine.py`

**Step 1: Write failing tests**

```python
class TestExecuteStructuralPrerequisites:
    """engine_execute() requires prior-stage artifacts."""

    def test_missing_classify_intent_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            # classify_intent missing
        )
        assert resp.state == "policy_blocked"

    def test_mismatched_classify_intent_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="update",  # Doesn't match action="create"
            classify_confidence=0.95,
        )
        assert resp.error_code == "intent_mismatch"

    def test_missing_classify_confidence_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create",
            # classify_confidence missing (defaults to None)
        )
        assert resp.state == "policy_blocked"

    def test_low_confidence_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.3,  # Below 0.5 threshold
        )
        assert resp.state == "preflight_failed"

    def test_agent_low_confidence_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket
        write_autonomy_config(
            tmp_tickets,
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 5\n---\n",
        )
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="agent",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="agent",
            classify_intent="create",
            classify_confidence=0.60,  # Below 0.65 (0.5 + 0.15) agent threshold
            autonomy_config=AutonomyConfig(mode="auto_audit", max_creates=5),
        )
        assert resp.state == "preflight_failed"

    def test_missing_dedup_fingerprint_for_create_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            # dedup_fingerprint missing
        )
        assert resp.state == "policy_blocked"

    def test_mismatched_dedup_fingerprint_rejected(self, tmp_tickets):
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint="wrong-fingerprint",
        )
        assert resp.error_code == "stale_plan"

    def test_correct_dedup_fingerprint_accepted(self, tmp_tickets):
        from scripts.ticket_dedup import dedup_fingerprint
        fp = dedup_fingerprint("P", [])
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint=fp,
        )
        assert resp.state == "ok_create"

    def test_missing_target_fingerprint_for_update_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket
        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update", ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="update",
            classify_confidence=0.95,
            # target_fingerprint missing (None)
        )
        assert resp.state == "policy_blocked"

    def test_agent_missing_autonomy_config_rejected(self, tmp_tickets):
        write_autonomy_config(
            tmp_tickets,
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 5\n---\n",
        )
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "P"},
            session_id="sess", request_origin="agent",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="agent",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint="anything",
            # autonomy_config=None (missing snapshot)
        )
        assert resp.state == "policy_blocked"
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestExecuteStructuralPrerequisites -v
```

Expected: ALL fail (these parameters don't exist on `engine_execute` yet, or aren't checked).

**Step 3: Implement structural prerequisites**

Add new parameters to `engine_execute()`:

```python
def engine_execute(
    *,
    action: str,
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    dedup_override: bool,
    dependency_override: bool,
    tickets_dir: Path,
    target_fingerprint: str | None = None,
    autonomy_config: AutonomyConfig | None = None,
    hook_injected: bool = False,
    hook_request_origin: str | None = None,
    classify_intent: str | None = None,
    classify_confidence: float | None = None,
    dedup_fingerprint: str | None = None,
) -> EngineResponse:
```

After the trust triple check (added in Task 4), before the autonomy checks, add:

```python
    # --- Structural stage prerequisites ---
    # classify_intent: must match action.
    if classify_intent is None:
        return EngineResponse(
            state="policy_blocked",
            message="Execute requires classify_intent (run classify stage first)",
            error_code="policy_blocked",
        )
    if classify_intent != action:
        return EngineResponse(
            state="escalate",
            message=f"intent_mismatch: classify_intent={classify_intent!r} but action={action!r}",
            error_code="intent_mismatch",
        )

    # classify_confidence: must be present and above threshold.
    if classify_confidence is None:
        return EngineResponse(
            state="policy_blocked",
            message="Execute requires classify_confidence (run classify stage first)",
            error_code="policy_blocked",
        )
    modifier = _ORIGIN_MODIFIER.get(request_origin, 0.0)
    threshold = _T_BASE + modifier
    if classify_confidence < threshold:
        return EngineResponse(
            state="preflight_failed",
            message=f"Low confidence: {classify_confidence:.2f} (threshold: {threshold:.2f})",
            error_code="preflight_failed",
        )

    # dedup_fingerprint: required for create, must match recomputed value.
    if action == "create":
        if dedup_fingerprint is None:
            return EngineResponse(
                state="policy_blocked",
                message="Create execute requires dedup_fingerprint (run plan stage first)",
                error_code="policy_blocked",
            )
        from scripts.ticket_dedup import dedup_fingerprint as compute_dedup_fp
        expected_fp = compute_dedup_fp(
            fields.get("problem", ""),
            fields.get("key_file_paths", []),
        )
        if dedup_fingerprint != expected_fp:
            return EngineResponse(
                state="preflight_failed",
                message="dedup_fingerprint mismatch — create fields changed since plan",
                error_code="stale_plan",
            )

    # target_fingerprint: required for non-create actions.
    if action != "create" and target_fingerprint is None:
        return EngineResponse(
            state="policy_blocked",
            message=f"{action} execute requires target_fingerprint (run plan stage first)",
            error_code="policy_blocked",
        )

    # autonomy_config: required for agent-origin (snapshot from preflight).
    if request_origin == "agent" and autonomy_config is None:
        return EngineResponse(
            state="policy_blocked",
            message="Agent execute requires autonomy_config snapshot (rerun from preflight)",
            error_code="policy_blocked",
        )
```

Update both entrypoint `_dispatch()` functions to extract and pass the new fields:

```python
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
```

**Step 4: Update ALL existing engine_execute calls in tests**

Every existing `engine_execute()` call in tests now needs the new parameters. Apply systematically:

For **create** actions, add:
```python
classify_intent="create",
classify_confidence=0.95,
dedup_fingerprint=dedup_fingerprint(fields["problem"], fields.get("key_file_paths", [])),
```

For **update/close/reopen** actions, add:
```python
classify_intent="<action>",
classify_confidence=0.95,
target_fingerprint=target_fingerprint(ticket_path),
```

Import at top of test files:
```python
from scripts.ticket_dedup import dedup_fingerprint, target_fingerprint
```

For agent calls, ensure `autonomy_config=AutonomyConfig(mode="auto_audit", max_creates=5)` is passed.

**Important:** The test `test_agent_execute_allows_when_live_config_auto_audit_and_no_snapshot` (test_autonomy.py:445) must be updated to **expect rejection** — change `assert resp.state == "ok_create"` to `assert resp.state == "policy_blocked"`. Then add a new test that passes the snapshot and succeeds.

**Step 5: Run full test suite**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Expected: ALL pass.

**Step 6: Commit**

```bash
git add scripts/ticket_engine_core.py scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/
git commit -m "fix(ticket): add structural stage prerequisites to engine_execute

execute now requires: classify_intent (must match action), classify_confidence
(must meet origin-specific threshold), dedup_fingerprint (create only, must
match recomputed value), target_fingerprint (non-create, mandatory), and
autonomy_config (agent-origin, snapshot from preflight).

These are mandatory payload-consistency checks proving that classify and plan
stages ran with the current fields. The existing live duplicate scan in execute
is unchanged — it remains the store-state check for duplicates appearing
between plan and execute."
```

---

### Task 6: Patch 1 integration test + full suite verification

Add an integration test that exercises the real hook → entrypoint → engine path with staged payloads, verifying all Patch 1 changes work together end-to-end.

**Files:**
- Test: `tests/test_hook_integration.py` (add integration test)

**Step 1: Write integration test**

```python
class TestPatch1Integration:
    """End-to-end: hook → entrypoint → engine with full staged payload."""

    def test_canonical_create_flow_with_staged_payload(self, tmp_path):
        """Full trust path: hook injects trust fields, entrypoint validates,
        engine checks structural prerequisites."""
        plugin_root = str(Path(__file__).parent.parent)
        from scripts.ticket_dedup import dedup_fingerprint

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)

        fp = dedup_fingerprint("Integration test problem", [])
        payload_data = {
            "action": "create",
            "fields": {
                "title": "Integration Test",
                "problem": "Integration test problem",
                "priority": "medium",
            },
            "classify_intent": "create",
            "classify_confidence": 0.95,
            "dedup_fingerprint": fp,
            "tickets_dir": str(tickets_dir),
        }
        payload_file = make_payload_file(tmp_path, payload_data)

        # Hook injection
        cmd = f"python3 {plugin_root}/scripts/ticket_engine_user.py execute {payload_file}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        hook_input["session_id"] = "integration-session"
        hook_result = run_hook(hook_input)
        assert hook_result["hookSpecificOutput"]["permissionDecision"] == "allow"

        # Verify payload was injected
        injected = json.loads(Path(payload_file).read_text(encoding="utf-8"))
        assert injected["hook_injected"] is True
        assert injected["hook_request_origin"] == "user"
        assert injected["session_id"] == "integration-session"

    def test_bypass_attempt_blocked_end_to_end(self, tmp_path):
        """Leading-space bypass attempt is caught by prefilter."""
        plugin_root = str(Path(__file__).parent.parent)
        payload_file = make_payload_file(tmp_path)
        cmd = f" python3 {plugin_root}/scripts/ticket_engine_user.py execute {payload_file}"
        hook_input = make_hook_input(cmd, cwd=str(tmp_path))
        result = run_hook(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
```

**Step 2: Run integration + full suite**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Expected: ALL pass.

**Step 3: Commit**

```bash
git add tests/test_hook_integration.py
git commit -m "test(ticket): add Patch 1 integration test for trust boundary

Exercises the full hook → entrypoint → engine path with staged payloads,
verifying shlex prefilter, origin helper, trust triple, and structural
prerequisites work together end-to-end."
```

---

## Patch 2: Data Integrity & Interface Cleanup

### Task 7: Schema/type validation before writes

No schema validation currently exists for `priority`, `resolution`, `tags`, `blocked_by`, `blocks`, `source`, `key_files`, or `defer`. Invalid types or values are silently accepted and written to files. Add shared validation that rejects invalid inputs before `render_ticket()` or YAML replacement runs.

**Files:**
- Create: `scripts/ticket_validate.py` (shared validation module)
- Modify: `scripts/ticket_engine_core.py` (call validation before writes in `_execute_create`, `_execute_update`, `_execute_close`)
- Test: `tests/test_validate.py` (new)

**Step 1: Write failing tests**

Create `tests/test_validate.py`:

```python
"""Tests for ticket field schema validation."""
from __future__ import annotations

import pytest

from scripts.ticket_validate import validate_fields


class TestValidateFields:
    """Shared validation for writable ticket fields."""

    # --- priority ---
    def test_valid_priorities(self):
        for p in ("critical", "high", "medium", "low"):
            errors = validate_fields({"priority": p})
            assert not errors, f"priority={p} should be valid"

    def test_invalid_priority_rejected(self):
        errors = validate_fields({"priority": "urgent"})
        assert any("priority" in e for e in errors)

    def test_priority_wrong_type_rejected(self):
        errors = validate_fields({"priority": 1})
        assert any("priority" in e for e in errors)

    # --- status ---
    def test_valid_statuses(self):
        for s in ("open", "in_progress", "blocked", "done", "wontfix"):
            errors = validate_fields({"status": s})
            assert not errors, f"status={s} should be valid"

    def test_invalid_status_rejected(self):
        errors = validate_fields({"status": "pending"})
        assert any("status" in e for e in errors)

    # --- resolution ---
    def test_valid_resolutions(self):
        for r in ("done", "wontfix"):
            errors = validate_fields({"resolution": r})
            assert not errors, f"resolution={r} should be valid"

    def test_invalid_resolution_rejected(self):
        errors = validate_fields({"resolution": "cancelled"})
        assert any("resolution" in e for e in errors)

    # --- tags ---
    def test_valid_tags(self):
        errors = validate_fields({"tags": ["bug", "urgent"]})
        assert not errors

    def test_tags_scalar_rejected(self):
        errors = validate_fields({"tags": "bug"})
        assert any("tags" in e for e in errors)

    def test_tags_non_string_elements_rejected(self):
        errors = validate_fields({"tags": ["bug", 42]})
        assert any("tags" in e for e in errors)

    # --- blocked_by ---
    def test_valid_blocked_by(self):
        errors = validate_fields({"blocked_by": ["T-20260302-01"]})
        assert not errors

    def test_blocked_by_scalar_rejected(self):
        errors = validate_fields({"blocked_by": "T-20260302-01"})
        assert any("blocked_by" in e for e in errors)

    # --- blocks ---
    def test_valid_blocks(self):
        errors = validate_fields({"blocks": ["T-20260302-02"]})
        assert not errors

    def test_blocks_scalar_rejected(self):
        errors = validate_fields({"blocks": "T-20260302-02"})
        assert any("blocks" in e for e in errors)

    # --- source ---
    def test_valid_source(self):
        errors = validate_fields({"source": {"type": "ad-hoc", "ref": "", "session": "s"}})
        assert not errors

    def test_source_non_dict_rejected(self):
        errors = validate_fields({"source": "ad-hoc"})
        assert any("source" in e for e in errors)

    def test_source_non_string_values_rejected(self):
        errors = validate_fields({"source": {"type": 123, "ref": "", "session": "s"}})
        assert any("source" in e for e in errors)

    # --- defer ---
    def test_valid_defer(self):
        errors = validate_fields({"defer": {"active": True, "reason": "blocked on X"}})
        assert not errors

    def test_defer_non_dict_rejected(self):
        errors = validate_fields({"defer": "yes"})
        assert any("defer" in e for e in errors)

    # --- key_files ---
    def test_valid_key_files(self):
        errors = validate_fields({"key_files": [{"path": "src/main.py", "reason": "entry point"}]})
        assert not errors

    def test_key_files_non_list_rejected(self):
        errors = validate_fields({"key_files": "src/main.py"})
        assert any("key_files" in e for e in errors)

    def test_key_files_non_dict_elements_rejected(self):
        errors = validate_fields({"key_files": ["src/main.py"]})
        assert any("key_files" in e for e in errors)

    # --- omitted fields are fine ---
    def test_empty_fields_valid(self):
        errors = validate_fields({})
        assert not errors

    def test_unknown_fields_ignored(self):
        errors = validate_fields({"title": "Test", "problem": "Problem"})
        assert not errors
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_validate.py -v
```

Expected: ALL fail (module doesn't exist yet).

**Step 3: Implement validation module**

Create `scripts/ticket_validate.py`:

```python
"""Shared schema validation for writable ticket fields.

Validates field types and enum membership before render_ticket() or
YAML replacement. Rejects invalid inputs; omitted fields are not errors
(defaults are applied by the engine, not the validator).
"""
from __future__ import annotations

from typing import Any

VALID_PRIORITIES = frozenset({"critical", "high", "medium", "low"})
VALID_STATUSES = frozenset({"open", "in_progress", "blocked", "done", "wontfix"})
VALID_RESOLUTIONS = frozenset({"done", "wontfix"})


def validate_fields(fields: dict[str, Any]) -> list[str]:
    """Validate writable ticket fields. Returns list of error messages (empty = valid)."""
    errors: list[str] = []

    # --- Enum fields ---
    if "priority" in fields:
        v = fields["priority"]
        if not isinstance(v, str) or v not in VALID_PRIORITIES:
            errors.append(
                f"priority must be one of {sorted(VALID_PRIORITIES)}, got {v!r}"
            )

    if "status" in fields:
        v = fields["status"]
        if not isinstance(v, str) or v not in VALID_STATUSES:
            errors.append(
                f"status must be one of {sorted(VALID_STATUSES)}, got {v!r}"
            )

    if "resolution" in fields:
        v = fields["resolution"]
        if not isinstance(v, str) or v not in VALID_RESOLUTIONS:
            errors.append(
                f"resolution must be one of {sorted(VALID_RESOLUTIONS)}, got {v!r}"
            )

    # --- List-of-string fields ---
    for key in ("tags", "blocked_by", "blocks"):
        if key in fields:
            v = fields[key]
            if not isinstance(v, list):
                errors.append(f"{key} must be a list, got {type(v).__name__}")
            elif not all(isinstance(item, str) for item in v):
                errors.append(f"{key} must contain only strings")

    # --- Dict fields ---
    if "source" in fields:
        v = fields["source"]
        if not isinstance(v, dict):
            errors.append(f"source must be a dict, got {type(v).__name__}")
        elif not all(isinstance(val, str) for val in v.values()):
            errors.append("source values must all be strings")

    if "defer" in fields:
        v = fields["defer"]
        if not isinstance(v, dict):
            errors.append(f"defer must be a dict, got {type(v).__name__}")

    # --- Structured list fields ---
    if "key_files" in fields:
        v = fields["key_files"]
        if not isinstance(v, list):
            errors.append(f"key_files must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, dict) for item in v):
            errors.append("key_files must contain only dicts")

    return errors
```

**Step 4: Run validation tests**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_validate.py -v
```

Expected: ALL pass.

**Step 5: Wire validation into engine**

In `ticket_engine_core.py`, import and call validation before writes:

```python
from scripts.ticket_validate import validate_fields
```

In `_execute_create()` (after missing-field check, before `tickets_dir.mkdir`):
```python
    validation_errors = validate_fields(fields)
    if validation_errors:
        return EngineResponse(
            state="need_fields",
            message=f"Field validation failed: {'; '.join(validation_errors)}",
            error_code="need_fields",
            data={"validation_errors": validation_errors},
        )
```

In `_execute_update()` (after ticket lookup, before YAML extraction):
```python
    validation_errors = validate_fields(fields)
    if validation_errors:
        return EngineResponse(
            state="need_fields",
            message=f"Field validation failed: {'; '.join(validation_errors)}",
            error_code="need_fields",
            ticket_id=ticket_id,
            data={"validation_errors": validation_errors},
        )
```

In `_execute_close()` (after ticket lookup, before transition check):
```python
    close_fields = dict(fields)
    close_fields["resolution"] = resolution  # Validate the resolution too.
    validation_errors = validate_fields(close_fields)
    if validation_errors:
        return EngineResponse(
            state="need_fields",
            message=f"Field validation failed: {'; '.join(validation_errors)}",
            error_code="need_fields",
            ticket_id=ticket_id,
            data={"validation_errors": validation_errors},
        )
```

**Step 6: Add engine-level validation tests**

Add to `tests/test_engine.py`:

```python
class TestExecuteFieldValidation:
    """engine_execute rejects invalid field types/values before writing."""

    def test_create_invalid_priority_rejected(self, tmp_tickets):
        from scripts.ticket_dedup import dedup_fingerprint
        fp = dedup_fingerprint("Problem", [])
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "Problem", "priority": "urgent"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create", classify_confidence=0.95,
            dedup_fingerprint=fp,
        )
        assert resp.error_code == "need_fields"
        assert "priority" in resp.message

    def test_create_scalar_tags_rejected(self, tmp_tickets):
        from scripts.ticket_dedup import dedup_fingerprint
        fp = dedup_fingerprint("Problem", [])
        resp = engine_execute(
            action="create", ticket_id=None,
            fields={"title": "T", "problem": "Problem", "tags": "bug"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="create", classify_confidence=0.95,
            dedup_fingerprint=fp,
        )
        assert resp.error_code == "need_fields"
        assert "tags" in resp.message

    def test_update_scalar_blocked_by_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket
        from scripts.ticket_dedup import target_fingerprint
        tp = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        tfp = target_fingerprint(tp)
        resp = engine_execute(
            action="update", ticket_id="T-20260302-01",
            fields={"blocked_by": "T-20260302-02"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="update", classify_confidence=0.95,
            target_fingerprint=tfp,
        )
        assert resp.error_code == "need_fields"
        assert "blocked_by" in resp.message

    def test_close_invalid_resolution_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket
        from scripts.ticket_dedup import target_fingerprint
        tp = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        tfp = target_fingerprint(tp)
        resp = engine_execute(
            action="close", ticket_id="T-20260302-01",
            fields={"resolution": "cancelled"},
            session_id="sess", request_origin="user",
            dedup_override=False, dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True, hook_request_origin="user",
            classify_intent="close", classify_confidence=0.95,
            target_fingerprint=tfp,
        )
        assert resp.error_code == "need_fields"
        assert "resolution" in resp.message
```

**Step 7: Run full test suite**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Expected: ALL pass.

**Step 8: Commit**

```bash
git add scripts/ticket_validate.py tests/test_validate.py scripts/ticket_engine_core.py tests/test_engine.py
git commit -m "fix(ticket): add schema validation before writes

New ticket_validate.py module enforces contract enums (priority, status,
resolution), list-of-string types (tags, blocked_by, blocks), dict shapes
(source, defer), and structured list shape (key_files). Invalid inputs are
rejected with need_fields; omitted optional fields are not errors.

Called in _execute_create, _execute_update, and _execute_close before any
file mutation occurs."
```

---

### Task 8: Marker-based project-root resolution

Both entrypoints resolve `tickets_dir` against `Path.cwd()` (line 58). In nested working directories, this writes tickets to the wrong location. Replace with marker-based project-root discovery that walks ancestors for `.claude/`, `.git/`, or `.git` file.

**Files:**
- Modify: `scripts/ticket_paths.py` (add `discover_project_root()`)
- Modify: `scripts/ticket_engine_user.py:57–58` (use discovered root)
- Modify: `scripts/ticket_engine_agent.py:57–58` (use discovered root)
- Test: `tests/test_paths.py` (new, or add to existing path tests)

**Step 1: Write failing tests**

Create or extend tests. If `tests/test_paths.py` doesn't exist, check for path tests in `test_engine.py`:

```python
"""Tests for marker-based project-root resolution."""
from __future__ import annotations

import pytest
from pathlib import Path

from scripts.ticket_paths import discover_project_root


class TestDiscoverProjectRoot:
    """Marker-based project root discovery."""

    def test_finds_git_directory(self, tmp_path):
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "src" / "pkg"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_finds_claude_directory(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        nested = tmp_path / "src" / "deep" / "pkg"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_finds_git_file_worktree(self, tmp_path):
        """A .git file (worktree) is also a valid marker."""
        (tmp_path / ".git").write_text("gitdir: /some/other/.git/worktrees/x")
        nested = tmp_path / "src"
        nested.mkdir()
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_prefers_nearest_ancestor(self, tmp_path):
        """If multiple ancestors have markers, choose nearest."""
        (tmp_path / ".git").mkdir()
        inner = tmp_path / "subproject"
        inner.mkdir()
        (inner / ".claude").mkdir()
        deep = inner / "src"
        deep.mkdir()
        root = discover_project_root(deep)
        assert root == inner

    def test_returns_none_without_markers(self, tmp_path):
        nested = tmp_path / "no" / "markers" / "here"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root is None

    def test_cwd_itself_is_root(self, tmp_path):
        (tmp_path / ".git").mkdir()
        root = discover_project_root(tmp_path)
        assert root == tmp_path
```

**Step 2: Run tests to verify failures**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_paths.py::TestDiscoverProjectRoot -v
```

Expected: ALL fail (`discover_project_root` doesn't exist).

**Step 3: Implement project-root discovery**

Add to `scripts/ticket_paths.py`:

```python
_PROJECT_ROOT_MARKERS = (".claude", ".git")


def discover_project_root(start: Path) -> Path | None:
    """Walk ancestors from start to find nearest project root.

    A project root is the nearest ancestor (including start itself) that
    contains a .claude/ directory, a .git/ directory, or a .git file
    (git worktree marker).

    Returns None if no marker is found (caller should reject, not fallback).
    """
    current = start.resolve()
    while True:
        for marker in _PROJECT_ROOT_MARKERS:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            return None
        current = parent
```

**Step 4: Run discovery tests**

```bash
cd packages/plugins/ticket && uv run pytest tests/test_paths.py::TestDiscoverProjectRoot -v
```

Expected: ALL pass.

**Step 5: Wire into entrypoints**

In both `ticket_engine_user.py` and `ticket_engine_agent.py`, replace lines 57–66 with:

```python
    from scripts.ticket_paths import discover_project_root

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
```

**Step 6: Add entrypoint-level tests**

```python
class TestProjectRootResolution:
    """Entrypoints use marker-based project root, not raw cwd."""

    def test_nested_cwd_resolves_to_project_root(self, tmp_path):
        """Running from a nested dir finds the project root."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        (project / "docs" / "tickets").mkdir(parents=True)
        nested = project / "src" / "deep"
        nested.mkdir(parents=True)

        payload = {
            "action": "create",
            "fields": {"title": "T", "problem": "P", "priority": "medium"},
            "hook_injected": True,
            "hook_request_origin": "user",
            "session_id": "test-session",
            "classify_intent": "create",
            "classify_confidence": 0.95,
            "dedup_fingerprint": dedup_fingerprint("P", []),
        }
        # Run from nested dir
        result = run_entrypoint(
            "ticket_engine_user.py", "execute", payload, tmp_path, cwd=nested
        )
        assert result.get("state") == "ok_create"

    def test_no_markers_rejects(self, tmp_path):
        """No project root markers → policy_blocked."""
        bare = tmp_path / "no_markers"
        bare.mkdir()
        payload = {"action": "create", "args": {}}
        result = run_entrypoint(
            "ticket_engine_user.py", "classify", payload, tmp_path, cwd=bare
        )
        assert result.get("error_code") == "policy_blocked"
```

Note: `run_entrypoint()` may need a `cwd` parameter added. If it uses `subprocess.run()`, add `cwd=cwd` to the call. Check the existing fixture and extend if needed.

**Step 7: Run full test suite**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Expected: ALL pass. Some existing entrypoint tests may need `.git` or `.claude` markers added to their `tmp_path` fixtures — check and fix any failures.

**Step 8: Commit**

```bash
git add scripts/ticket_paths.py scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/
git commit -m "fix(ticket): replace cwd fallback with marker-based project-root resolution

discover_project_root() walks ancestors from cwd for .claude/ or .git/
markers. Both entrypoints use the discovered root instead of Path.cwd()
for tickets_dir resolution.

When no project root is found, rejects with policy_blocked instead of
silently writing to <cwd>/docs/tickets. This prevents nested-cwd
invocations from creating tickets outside the project."
```

---

### Task 9: Contract, docs, and test alignment

Update the contract and pipeline docs to state the new invariants. Remove or invert tests that bless unsafe shortcuts.

**Files:**
- Modify: `references/ticket-contract.md`
- Test: verify no tests assert the old unsafe shortcuts

**Step 1: Update contract**

In `references/ticket-contract.md`, update the relevant sections:

1. Replace "Execute leniency" paragraph (around line 101) with:
   ```
   Execute provenance: execute requires verified hook provenance (hook_injected=True,
   hook_request_origin matching entrypoint origin, non-empty session_id) for all
   mutations, both user and agent. Non-execute stages (classify, plan, preflight)
   remain directly runnable without hook metadata.
   ```

2. Add after the execute section:
   ```
   Execute prerequisites: execute requires prior-stage artifacts:
   - classify_intent (must match action)
   - classify_confidence (must meet origin-specific threshold: 0.5 for user, 0.65 for agent)
   - dedup_fingerprint (create only, must match recomputed value from current fields)
   - target_fingerprint (non-create, mandatory — validates ticket unchanged since read)
   - autonomy_config (agent only, snapshot from preflight)
   ```

3. Update the field validation section to state:
   ```
   Field validation: priority, status, and resolution are validated against contract
   enums before writes. tags, blocked_by, and blocks must be lists of strings. source
   must be a dict with string values. key_files must be a list of dicts. defer must
   be a dict. Invalid inputs are rejected (need_fields), not silently coerced.
   ```

4. Update tickets_dir section:
   ```
   tickets_dir resolution: CLI entrypoints resolve tickets_dir against a marker-based
   project root (nearest ancestor containing .claude/ or .git/), not against cwd.
   Explicit tickets_dir must resolve inside the project root. If no project root is
   found, the operation is rejected (policy_blocked).
   ```

**Step 2: Verify no tests assert old shortcuts**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -q
```

Grep for any tests that might still assert the old behavior:

```bash
grep -rn "hook_injected=False.*ok_create\|without.*hook.*ok\|no_snapshot.*ok_create" tests/
```

If any found, update them to expect rejection.

**Step 3: Run full test suite one final time**

```bash
cd packages/plugins/ticket && uv run pytest tests/ -v
```

Expected: ALL pass.

**Step 4: Commit**

```bash
git add references/ticket-contract.md tests/
git commit -m "docs(ticket): update contract for trust boundary and validation changes

Contract now states: execute requires verified hook provenance for all
origins, execute requires prior-stage artifacts, field validation rejects
invalid types/values, and tickets_dir uses marker-based root resolution."
```

---

## Post-Implementation Checklist

After all tasks complete:

1. Run full test suite: `cd packages/plugins/ticket && uv run pytest tests/ -v`
2. Verify test count increased (baseline: 398)
3. Verify no tests assert old unsafe shortcuts (user execute without hook, agent execute without snapshot)
4. Review git log for clean commit history with atomic changes
5. Verify contract doc matches implementation

---

## File Reference

| File | Purpose | Tasks |
|------|---------|-------|
| `hooks/ticket_engine_guard.py` | PreToolUse hook | 1, 2 |
| `scripts/ticket_engine_user.py` | User entrypoint | 3, 4, 5, 8 |
| `scripts/ticket_engine_agent.py` | Agent entrypoint | 3, 4, 5, 8 |
| `scripts/ticket_engine_core.py` | Engine core | 4, 5, 7 |
| `scripts/ticket_paths.py` | Path resolution | 8 |
| `scripts/ticket_validate.py` | Field validation (new) | 7 |
| `references/ticket-contract.md` | Contract docs | 9 |
| `tests/test_hook.py` | Hook tests | 1, 2 |
| `tests/test_hook_integration.py` | Integration tests | 6 |
| `tests/test_entrypoints.py` | Entrypoint tests | 3, 8 |
| `tests/test_engine.py` | Engine tests | 4, 5, 7 |
| `tests/test_autonomy.py` | Autonomy tests | 4, 5 |
| `tests/test_autonomy_integration.py` | Autonomy integration | 4 |
| `tests/test_validate.py` | Validation tests (new) | 7 |
| `tests/test_paths.py` | Path resolution tests | 8 |
