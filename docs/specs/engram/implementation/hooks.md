---
module: hooks
legacy_sections: ["8"]
authority: implementation
normative: false
status: active
---

# Hook Specifications

## Overview

Engram uses Claude Code plugin hooks for two purposes:

1. **Identity enforcement** — PreToolUse hook validates that mutation tool calls carry the correct session identity
2. **Telemetry** — PostToolUse and PostToolUseFailure hooks log all MCP tool calls for observability

A single Python script (`scripts/engram_guard.py`) handles all hook events, dispatching on `hook_event_name` at runtime. This follows the established pattern from the cross-model plugin's `codex_guard.py`.

**Design constraint:** PreToolUse hooks are fail-open in Claude Code — unhandled exceptions produce a non-zero exit code that is NOT exit code 2, so the tool call proceeds. For the identity guard (critical enforcement), the script must catch all exceptions in the PreToolUse path and exit 2 on failure. PostToolUse/PostToolUseFailure errors are always silent (exit 0).

### Hook Events Used

| Event | Purpose | Blockable | Matcher |
|-------|---------|-----------|---------|
| `PreToolUse` | Identity validation on mutations | Yes (exit 2) | `mcp__plugin_engram_core__.*` |
| `PostToolUse` | Telemetry logging (success) | No | `mcp__plugin_engram_core__.*` |
| `PostToolUseFailure` | Telemetry logging (failure) | No | `mcp__plugin_engram_core__.*` |
| `SessionStart` | Environment bootstrap | No | (all sources) |

### Relationship to Other Enforcement Layers

The hooks are one layer in a three-layer enforcement stack ([tool-surface.md](../contracts/tool-surface.md)):

| Layer | Role | What It Checks |
|-------|------|----------------|
| **Skills** | Identity carrier | SKILL.md contains `${CLAUDE_SESSION_ID}`; skill passes UUID as `session_id` to MCP tools |
| **PreToolUse hook** | Stateless identity validation | `tool_input.session_id` matches Claude Code's `session_id` (common input field) |
| **MCP server** | Existence and lifecycle enforcement | Session exists, is open, constraints satisfied; returns `reason_code` on failure |

The hook validates identity but not session state (open/closed, existence). That is the server's job. The hook is stateless — it reads two values from the hook input and compares them. No database access, no network calls, no file reads beyond the hook input itself.

---

## Hook Registrations

### hooks.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__plugin_engram_core__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/engram_guard.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__plugin_engram_core__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/engram_guard.py"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "mcp__plugin_engram_core__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/engram_guard.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/engram_guard.py"
          }
        ]
      }
    ]
  }
}
```

**Matcher pattern:** `mcp__plugin_engram_core__.*` matches all 13 Engram MCP tools. `engram` is the plugin name; `core` is the MCP server name (single server). This follows the Claude Code naming convention: `mcp__plugin_<plugin>_<server>__<tool>`. The server name `core` is established in [appendix.md](../skills/appendix.md) and used by all skill `allowed-tools` entries.

**SessionStart has no matcher** — it fires on all session sources (startup, resume, clear, compact). The hook uses `hook_event_name` to dispatch, not the matcher.

**Single script registration:** All four events use the same script. The script reads `hook_event_name` from stdin JSON and dispatches to the appropriate handler.

**Matcher symmetry invariant:** All three tool-event registrations (PreToolUse, PostToolUse, PostToolUseFailure) must use the same matcher pattern. If the matcher is updated for one, update all three. A mismatch would cause identity enforcement and telemetry to cover different tool sets.

### plugin.json Reference

```json
{
  "hooks": "./hooks/hooks.json"
}
```

---

## PreToolUse: Identity Guard {#identity-guard}

### Tool Classification

The hook classifies each tool call into one of three categories:

| Category | Tools | Identity Check | Rationale |
|----------|-------|---------------|-----------|
| **Mutation** | `session_start`, `session_snapshot`, `session_end`, `task_create`, `task_update`, `lesson_capture`, `lesson_update`, `lesson_promote` | Required | Must validate that the caller's `session_id` matches the Claude Code session |
| **Read** | `session_get`, `session_list`, `task_query`, `lesson_query`, `query` | Skip | Read tools are ungated by design ([foundations.md](../foundations.md)) — safe for direct lookup |

**`session_start` is identity-checked, not exempt.** The original spec exempted `session_start` with a "circular dependency" rationale — but that rationale confuses the server's session-existence check (which `session_start` is indeed exempt from, since it creates sessions) with the hook's identity check (which just compares two available UUIDs). The hook's `session_id` common input field is always present, and skills always pass `session_id` in `tool_input`. Identity-checking `session_start` prevents calls with mismatched UUIDs from creating or enriching session rows under the wrong identity.

> **Contracts alignment:** [tool-surface.md](../contracts/tool-surface.md) Session Bootstrap section updated to reflect that the hook validates identity (UUID match) while the server exempts `session_start` from session-existence requirements. *(Codex dialogue #26, finding #1)*

Tool names arrive as full MCP names (e.g., `mcp__plugin_engram_core__task_create`). The hook extracts the suffix after the last `__` for classification. The matcher (`mcp__plugin_engram_core__.*`) is the authoritative tool-name filter — the suffix classification only categorizes tools that already passed the matcher.

```python
_READ = {"session_get", "session_list", "task_query", "lesson_query", "query"}
_MUTATION = {
    "session_start", "session_snapshot", "session_end",
    "task_create", "task_update",
    "lesson_capture", "lesson_update", "lesson_promote",
}
```

**Unknown tool suffix:** If the extracted suffix is not in either set, the hook blocks (exit 2). This is a defensive measure — an unrecognized tool should not bypass identity enforcement. If new tools are added to the MCP server, the hook's classification sets must be updated. A CI parity check (`_READ | _MUTATION` equals the server's registered tool set, sets are disjoint) is recommended to detect drift at build time rather than at runtime.

### Identity Validation Logic

For mutation tools, the hook performs a stateless cross-check:

```
hook_session_id  = data["session_id"]          # Claude Code session UUID (common input field)
tool_session_id  = data["tool_input"]["session_id"]  # What the caller passed to the MCP tool
```

| Condition | Result | Exit | Reason |
|-----------|--------|------|--------|
| `tool_session_id` == `hook_session_id` | Allow | 0 | Identity match — caller is the current session |
| `tool_session_id` != `hook_session_id` | Block | 2 | Identity mismatch — possible cross-session contamination |
| `tool_session_id` is missing | Block | 2 | Mutation requires `session_id` — direct call without identity |
| `hook_session_id` is missing | Block | 2 | Claude Code did not provide session context — should not happen |

**Why `session_id` missing triggers a block:** Skills pass `session_id` explicitly via `${CLAUDE_SESSION_ID}`. If a mutation tool is called without `session_id`, the caller bypassed the skill path. The server would also reject (session not found), but the hook catches it earlier with a clearer error message.

**Why `hook_session_id` missing triggers a block:** The `session_id` common input field is provided by Claude Code on every hook invocation. Its absence indicates a malformed hook payload, which should fail-closed.

### Response Format

The identity guard uses **exit code 2** for blocks (following the `codex_guard.py` pattern):

**Allow (exit 0):** No stdout output needed. The tool call proceeds.

**Block (exit 2):** stderr message displayed to Claude:

```
engram-guard: identity mismatch — tool_input.session_id ({tool_session_id:.8}...) does not match session ({hook_session_id:.8}...)
```

```
engram-guard: mutation requires session_id — {tool_suffix} called without session_id in tool_input
```

```
engram-guard: unrecognized tool — {tool_suffix} not in known tool classification
```

**Truncated UUIDs in messages:** Session IDs are truncated to 8 characters in error messages to avoid leaking full UUIDs while still being useful for debugging.

### Failure Semantics

**Fail-closed for PreToolUse:** The outer try/except catches all exceptions and exits 2. This compensates for Claude Code's fail-open default. An internal error in the identity guard should block the mutation rather than silently allow it.

```python
def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(f"engram-guard: stdin parse failed ({e})", file=sys.stderr)
        return 2  # fail-closed

    event = data.get("hook_event_name", "PreToolUse")

    try:
        if event == "PreToolUse":
            return handle_pre(data)
        elif event == "PostToolUse":
            return handle_post(data)
        elif event == "PostToolUseFailure":
            return handle_post_failure(data)
        elif event == "SessionStart":
            return handle_session_start(data)
        else:
            return 0  # unknown event — allow
    except Exception as e:
        if event == "PreToolUse":
            print(f"engram-guard: internal error (fail-closed): {e}", file=sys.stderr)
            return 2
        return 0  # non-PreToolUse errors are silent
```

**Fail-silent for PostToolUse/PostToolUseFailure/SessionStart:** These events are observe-only. Errors in telemetry logging must not disrupt the session.

### Lazy Bootstrap Interaction {#lazy-bootstrap-interaction}

The lazy session bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)) calls `session_start` after user confirmation but before the first domain mutation. The hook call sequence is:

```
1. User confirms mutation (Stage 2 of two-stage guard)
2. Skill calls session_start(session_id=<UUID>)     → PreToolUse fires → MUTATION → identity check → Allow (UUID matches)
3. Skill calls domain mutation (e.g., task_create)   → PreToolUse fires → MUTATION → identity check → Allow (same UUID)
```

The identity guard does not interfere with lazy bootstrap because both `session_start` and the subsequent domain mutation carry the same `session_id` (from `${CLAUDE_SESSION_ID}`), which matches the Claude Code session UUID in the common input field.

**Edge case — bootstrap failure:** If `session_start` fails (server rejects), the skill stops per the lazy bootstrap contract. The identity guard for the subsequent mutation never fires because the skill never makes the call.

---

## PostToolUse: Success Telemetry {#success-telemetry}

### Purpose

Log all successful Engram MCP tool calls. This is best-effort local telemetry — log writes may silently fail, and the log is not a guaranteed audit trail. It provides:
- Best-effort record of mutations (tool, session, outcome, timestamp)
- Usage patterns for capacity planning and tool surface optimization
- Foundation for analytics (tool frequency, session activity, error rates)

### Handler

The PostToolUse handler always exits 0 — it cannot block (the tool already executed). All errors in the handler are silently swallowed.

### Input Fields Used

| Field | Source | Purpose |
|-------|--------|---------|
| `tool_name` | Common input | Tool identification |
| `session_id` | Common input | Session attribution |
| `tool_input` | Event-specific (same parameters as PreToolUse) | Parameters logged for telemetry |
| `tool_response` | PostToolUse-specific | Outcome logged for audit |

### Event Schema

```json
{
  "ts": "2026-03-14T16:00:00.000Z",
  "event": "success",
  "tool": "mcp__plugin_engram_core__task_create",
  "tool_suffix": "task_create",
  "session_id": "a1b2c3d4-...",
  "category": "mutation",
  "outcome": "created",
  "entity_id": "e5f6g7h8-...",
  "input_keys": ["title", "description", "session_id"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ts` | ISO 8601 UTC | Timestamp of the hook execution |
| `event` | `"success"` | Discriminator |
| `tool` | string | Full MCP tool name |
| `tool_suffix` | string | Short name (after last `__`) |
| `session_id` | string | Claude Code session UUID |
| `category` | `"mutation"` \| `"read"` \| `"exempt"` | Tool classification |
| `outcome` | string \| null | `tool_response.outcome` for entity envelope responses (mutations); null for collections |
| `entity_id` | string \| null | `tool_response.entity.{task_id,lesson_id,session_id}` for entity responses; null for collections |
| `input_keys` | string[] | Top-level keys of `tool_input` (for audit without logging sensitive content) |

**Content redaction:** The event logs `input_keys` (parameter names) but not parameter values. Snapshot content, lesson insights, and task descriptions may contain sensitive information. Full audit is available via the MCP server's own response data and the database.

**`tool_response` parsing:** The handler attempts to extract `outcome` and entity ID from the response. If the response is not a dict or does not follow the entity envelope format, these fields are null. Parsing failures are silent.

---

## PostToolUseFailure: Failure Telemetry {#failure-telemetry}

### Purpose

Log all failed Engram MCP tool calls. This provides:
- Failure rate tracking per tool
- Input for the Server Unavailable Escalation heuristic ([skill-orchestration.md](../contracts/skill-orchestration.md#server-unavailable)) — skills use observed failure patterns, but telemetry provides offline analysis
- Debugging support for transport errors and server crashes

### Handler

Always exits 0 — PostToolUseFailure is not blockable.

### Input Fields Used

| Field | Source | Purpose |
|-------|--------|---------|
| `tool_name` | Common input | Tool identification |
| `session_id` | Common input | Session attribution |
| `tool_input` | Event-specific (same parameters as PreToolUse) | Parameters logged for debugging |
| `error` | PostToolUseFailure-specific | Error message from the failed tool |
| `is_interrupt` | PostToolUseFailure-specific | Whether the user interrupted the tool |

### Event Schema

```json
{
  "ts": "2026-03-14T16:00:00.000Z",
  "event": "failure",
  "tool": "mcp__plugin_engram_core__task_create",
  "tool_suffix": "task_create",
  "session_id": "a1b2c3d4-...",
  "category": "mutation",
  "error": "Connection closed",
  "error_class": "transport",
  "is_interrupt": false,
  "input_keys": ["title", "description", "session_id"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ts` | ISO 8601 UTC | Timestamp |
| `event` | `"failure"` | Discriminator |
| `tool` / `tool_suffix` | string | Tool identification |
| `session_id` | string | Claude Code session UUID |
| `category` | string | Tool classification |
| `error` | string | Error message from Claude Code |
| `error_class` | `"transport"` \| `"server"` \| `"unknown"` | Heuristic classification (see below) |
| `is_interrupt` | bool | User interrupted the tool |
| `input_keys` | string[] | Top-level keys of `tool_input` |

### Error Classification Heuristic {#error-classification}

The hook heuristically classifies errors to support offline analysis of server unavailability patterns:

| Class | Heuristic | Typical Causes |
|-------|-----------|---------------|
| `transport` | Error contains "ECONNREFUSED", "EPIPE", "timeout", "closed", "unavailable" | MCP server crashed, stdio pipe broken, network timeout |
| `server` | Error contains "reason_code", "policy_blocked", "conflict", "invalid_transition" | Server-side rejection (the server is alive but rejected the request) |
| `unknown` | Neither pattern matches, OR both patterns match | Unrecognized or ambiguous error format |

**Overlap tie-break:** If an error message matches tokens from both `transport` and `server` classes, classify as `unknown`. This prevents ambiguous messages (e.g., "invalid connection state") from being silently bucketed into a single class.

**Token specificity:** Tokens are chosen to minimize overlap. `"invalid_transition"` (specific Engram reason_code) replaces the bare `"invalid"` token. `"connection"` was removed (too broad — appears in both server rejection messages and transport errors). *(Codex dialogue #26, finding #5)*

This classification is best-effort — it does not drive runtime behavior. Skills use their own detection logic for the Server Unavailable Escalation ([skill-orchestration.md](../contracts/skill-orchestration.md#server-unavailable)). The telemetry classification supports post-hoc analysis only.

---

## SessionStart: Environment Bootstrap {#session-start-hook}

### Purpose

Write the Engram database path to `CLAUDE_ENV_FILE` so that hook scripts and utility scripts in subsequent Bash tool calls can locate the database without path discovery.

### Handler

```python
import shlex

def handle_session_start(data: dict) -> int:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return 0  # not available — skip silently

    cwd = data.get("cwd", "")
    if not cwd:
        return 0

    db_path = os.path.join(cwd, ".engram", "engram.db")

    try:
        with open(env_file, "a") as f:
            f.write(f"export ENGRAM_DB_PATH={shlex.quote(db_path)}\n")
    except OSError as e:
        print(f"engram-guard: env-file write failed ({e})", file=sys.stderr)

    return 0  # always allow — SessionStart is observe-only
```

**Shell-safe quoting:** `shlex.quote()` prevents shell injection from directory names containing special characters (backticks, `$()`, semicolons). While the `cwd` value comes from Claude Code (not user input), defense-in-depth is cheap here. *(Codex dialogue #26, finding #2)*

**Explicit error handling:** Write errors are caught and reported to stderr (visible in verbose mode) rather than being silently swallowed by the outer dispatcher. This preserves the bootstrap reliability story — if the env file write fails, the user at least sees a warning. *(Codex dialogue #26, finding #3)*

**`CLAUDE_ENV_FILE` availability:** Only available to SessionStart hooks. The hook appends (not overwrites) to avoid clobbering other plugins' variables.

**`cwd` as project root:** The working directory at session start is typically the project root. If it is not, `ENGRAM_DB_PATH` points to a non-existent path, which is harmless — the MCP server discovers its own database path independently. This env var is a convenience for scripts, not a critical path.

**No MCP probing:** SessionStart hooks are command-only shell scripts — they cannot invoke MCP tool calls. Server liveness checks are handled by skills at first use, not by hooks at session start. See [decisions.md](../decisions.md) (open risk #2 closure).

---

## Telemetry Log {#telemetry-log}

### Log Path

```
.engram/hooks.jsonl
```

Project-local, alongside the database (`.engram/engram.db`). The hook determines the log path from `cwd` in the hook input data.

**Path discovery:** The hook uses `data["cwd"]` to construct the log path: `os.path.join(data["cwd"], ".engram", "hooks.jsonl")`. If `.engram/` does not exist, the hook creates it. If the path is unwritable, the hook logs a warning to stderr (visible in verbose mode only) and continues — telemetry failure must not block tool calls.

### Log Format

One JSON object per line (JSONL). Each object has an `event` discriminator field:

| `event` value | Source | Description |
|---------------|--------|-------------|
| `"success"` | PostToolUse | Successful tool call |
| `"failure"` | PostToolUseFailure | Failed tool call |
| `"block"` | PreToolUse | Identity guard blocked a call |
| `"session_init"` | SessionStart | Session environment bootstrapped |

**Block events** are logged by the PreToolUse handler before exiting 2:

```json
{
  "ts": "2026-03-14T16:00:00.000Z",
  "event": "block",
  "tool": "mcp__plugin_engram_core__task_create",
  "tool_suffix": "task_create",
  "session_id": "a1b2c3d4-...",
  "reason": "identity_mismatch",
  "hook_session_id_prefix": "a1b2c3d4",
  "tool_session_id_prefix": "x9y8z7w6"
}
```

**Session init events** are logged by the SessionStart handler:

```json
{
  "ts": "2026-03-14T16:00:00.000Z",
  "event": "session_init",
  "session_id": "a1b2c3d4-...",
  "source": "startup",
  "cwd": "/path/to/project",
  "engram_db_path": "/path/to/project/.engram/engram.db"
}
```

### Retention

The log file grows unboundedly in v1. Rotation and cleanup are deferred — `.engram/hooks.jsonl` is expected to remain small for single-user development use (estimated <1MB per month of active use at ~500 bytes per event, ~60 events per session, ~50 sessions per month).

---

## Implementation: engram_guard.py {#implementation}

### Script Structure

```
scripts/engram_guard.py
├── main()                    # Entry point: parse stdin, dispatch on hook_event_name
├── handle_pre(data)          # PreToolUse: identity guard
├── handle_post(data)         # PostToolUse: success telemetry
├── handle_post_failure(data) # PostToolUseFailure: failure telemetry
├── handle_session_start(data)# SessionStart: environment bootstrap
├── _classify_tool(name)      # Extract suffix, return category
├── _classify_error(error)    # Heuristic error classification
├── _append_log(entry, cwd)   # JSONL append to .engram/hooks.jsonl
└── _ts()                     # UTC ISO 8601 timestamp
```

### Dependencies

**None.** The script uses only Python standard library (`json`, `sys`, `os`, `datetime`, `shlex`). No third-party imports, no project imports. This is intentional — hook scripts must start fast (they run on every tool call) and must not fail due to missing dependencies.

### Performance Budget

The hook runs synchronously before (PreToolUse) or after (PostToolUse/PostToolUseFailure) every Engram MCP tool call. Target latency: **<10ms** for PreToolUse (identity check is two string comparisons), **<20ms** for telemetry handlers (one JSONL append).

The script imports only standard library modules. No subprocess calls, no network I/O, no database access. The only file I/O is the JSONL append (PostToolUse/PostToolUseFailure/block events) and the `CLAUDE_ENV_FILE` append (SessionStart).

---

## Guard Response Summary {#response-summary}

| Scenario | Hook Event | Exit | Output | Logged As |
|----------|-----------|------|--------|-----------|
| Read tool call | PreToolUse | 0 | (none) | (not logged by PreToolUse) |
| Mutation (incl. `session_start`) — identity match | PreToolUse | 0 | (none) | (not logged by PreToolUse) |
| Mutation — identity mismatch | PreToolUse | 2 | stderr: reason | `block` event |
| Mutation — missing session_id | PreToolUse | 2 | stderr: reason | `block` event |
| Unrecognized tool | PreToolUse | 2 | stderr: reason | `block` event |
| Internal error (PreToolUse) | PreToolUse | 2 | stderr: error | `block` event (if logging succeeds) |
| Successful tool call | PostToolUse | 0 | (none) | `success` event |
| Failed tool call | PostToolUseFailure | 0 | (none) | `failure` event |
| Session start | SessionStart | 0 | (none) | `session_init` event |
| Internal error (non-PreToolUse) | any | 0 | (none) | (not logged — error swallowed) |

---

## Cross-References

| Topic | Location |
|-------|----------|
| Three-layer session bootstrap | [tool-surface.md](../contracts/tool-surface.md) — Session Bootstrap section |
| `session_start` idempotency | [tool-surface.md](../contracts/tool-surface.md) — Session Bootstrap section |
| Lazy session bootstrap (hook call sequence) | [skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap) |
| Server Unavailable Escalation | [skill-orchestration.md](../contracts/skill-orchestration.md#server-unavailable) |
| Single-mutation failure pattern | [skill-orchestration.md](../contracts/skill-orchestration.md#single-mutation-failure) |
| Tool Access Model (read ungated, mutation gated) | [foundations.md](../foundations.md) |
| MCP vs CLI decision (hook enforcement as deciding factor) | [decisions.md](../decisions.md) — MCP vs CLI section |
| MCP tool naming (server name `core`) | [appendix.md](../skills/appendix.md) |
| `codex_guard.py` reference implementation | `packages/plugins/cross-model/scripts/codex_guard.py` |
| Hook system documentation | Claude Code docs: `hooks`, `hooks-guide` |
| Codex adversarial review | Dialogue #26, thread `019ced3e-f858-7020-88ec-b697a0ec53c0` |

### Contracts Alignment (Completed)

[tool-surface.md](../contracts/tool-surface.md) Session Bootstrap section updated to separate hook identity validation (applies to `session_start`) from server session-existence enforcement (exempts `session_start`). See Codex dialogue #26, finding #1.
