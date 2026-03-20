# Ticket Plugin Phase 2 Design

**Goal:** Build the UX and trust infrastructure layer on top of Phase 1's engine: ticket-ops skill, PreToolUse hook, audit trail, autonomy enforcement, and triage script.

**Architecture:** Same hybrid adapter pattern (Architecture E). Phase 2 adds the skill (thin UX transport) and hook (trust enforcement) that Phase 1's engine was designed to receive.

**Design Doc:** `docs/plans/2026-03-02-ticket-plugin-design.md` (912 lines, canonical spec)

**Phase 1 State:** 157 tests, 9 files, 15 public symbols + 2 entrypoints, all on `main` at `18cce86`.

**Phase 2 Scope Policy:**
- `ticket-triage` **skill** (proactive SKILL.md) is Phase 3 — Phase 2 builds only the `ticket_triage.py` script it will wrap.
- `ticket-autocreate` **agent** is Phase 3 — behind feature flag per E-lite phasing.
- `auto_silent` autonomy mode returns `policy_blocked` in v1.0 — gated on v1.1 MCP migration.
- `merge_into_existing` state remains reserved — `escalate` fallback in v1.0.

**Pre-Phase 2 Decision (resolved):**
- `key_files` type split → separate field names: `key_file_paths: list[str]` for dedup, `key_files: list[dict]` for rendering.

---

## Module Breakdown

| Module | Components | Depends On | Estimated Tasks |
|--------|-----------|------------|-----------------|
| **M6: Pre-Phase 2 Fixes** | key_files rename, YAML injection fix, seq overflow fix | — | 3 |
| **M7: Hook + Audit Trail** | PreToolUse hook, audit wrapper in engine_execute, hook_injected validation | M6 | 5 (4→5a/5b) |
| **M8: Autonomy + Triage Script** | ticket.local.md parsing, autonomy enforcement (snapshot pattern), triage script (3 sub-tasks) | M7 | 6 (4→8/9/10a/10b/10c/11) |
| **M9: ticket-ops Skill** | SKILL.md, reference.md, e2e integration, version bump | M7, M8 | 4 |

Total: 18 tasks across 4 modules.

### Task-Level Dependency DAG

```
M6: T1 → T2 → T3 (sequential, shared test suite)

M7: T4 (hook) ─┬─→ T5a (audit wrapper) → T5b (session counting) → T6 (hook_injected validation) → T7 (integration)
               └─→ T6 can start after T4 (hook_injected requires hook to exist)

M8: T8 (config parsing) → T9 (autonomy enforcement, consumes config snapshot + session count) → T10a (core triage) → T10b (audit reader) → T10c (orphan detection) → T11 (integration)

M9: T12 (SKILL.md) → T13 (reference.md) → T14 (e2e test) → T15 (cleanup + gate)
```

Sub-gates: M7a (after T4), M7b (after T5b), M8a (after T9), M8b (after T10c).

---

## M6: Pre-Phase 2 Fixes

**Goal:** Resolve three known defects before building new Phase 2 components.

### Task 1: key_files field rename

**Files modified:** `ticket_engine_core.py`, `ticket_dedup.py`, `ticket-contract.md`
**Tests modified:** `test_engine.py`, `test_dedup.py`, `test_integration.py`

Rename `key_files` to `key_file_paths` in the dedup/plan pipeline:
- `engine_plan` input/output: `key_file_paths: list[str]` (file paths for fingerprinting)
- `dedup_fingerprint()`: accepts `key_file_paths` parameter (already correct in `ticket_dedup.py:41`)
- `ticket_engine_core.py:172`: change `fields.get("key_files", [])` → `fields.get("key_file_paths", [])`
- `render_ticket`: keeps `key_files: list[dict]` (structured table rows with file/role/look_for)
- `engine_execute`: receives `key_file_paths` for dedup verification, `key_files` for rendering (separate fields)
- Contract: document both fields with types in the `plan` subcommand I/O table (currently treats `fields` as opaque)
- **Compatibility rule:** If both `key_files` and `key_file_paths` are present in input, `key_file_paths` wins for dedup. `key_files` is always used for rendering regardless.

### Task 2: YAML injection in render_ticket

**Files modified:** `ticket_render.py`
**Tests modified:** `test_render.py` (add adversarial test)

Replace string interpolation for the source block with `yaml.safe_dump`. Codex M3 finding 1, confirmed by M4 gate probe — adversarial `source.ref` with nested double quotes breaks YAML round-trip.

### Task 3: Seq overflow at 99

**Files modified:** `ticket_id.py`
**Tests modified:** `test_id.py` (add boundary test)

Extend `_DATE_ID_RE` to support variable-width sequences (3+ digits). Update `allocate_id` to handle IDs beyond `T-YYYYMMDD-99`. Add test for `T-YYYYMMDD-100`.

### Gate

All 157+ existing tests pass after modifications. No new test files — only updates to existing test files.

---

## M7: Hook + Audit Trail

**Goal:** Build the PreToolUse hook and audit trail — the trust infrastructure that all Phase 2 components depend on.

### Task 4: PreToolUse hook implementation

**Files created:** `hooks/ticket_engine_guard.py`, update `hooks/hooks.json`
**Tests created:** `test_hook.py`

**Allowlist matching:** Permits only exact engine invocation shapes:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_{user|agent}.py <subcommand> <path-to-input-file>
```
Blocks all other Bash commands mentioning `ticket_engine`. Non-ticket Bash commands pass through (hook returns `allow` without modification).

**Payload injection (atomic):**
1. Read payload file path from command arguments
2. Inject `session_id` (from hook input JSON), `hook_injected: true`, `hook_request_origin` (derived from entrypoint basename: `ticket_engine_user.py` → `"user"`, `ticket_engine_agent.py` → `"agent"`)
3. Write temp file → fsync → rename (atomic replacement)
4. If injection fails → block (see output format below)

**Hook output format (prompt-based hooks API):** Returns JSON with `hookSpecificOutput.permissionDecision`:
- `"allow"` — command matches allowlist, payload injection succeeded
- `"deny"` — command mentions `ticket_engine` but doesn't match allowlist, or injection failed
- Non-ticket Bash commands: no `hookSpecificOutput` (hook passes through silently)

**Field naming convention:** The hook injects `hook_request_origin` (not `request_origin`). The entrypoint script sets `request_origin` in-process from its hardcoded constant. Mismatch between `hook_request_origin` and `request_origin` → `origin_mismatch` → `escalate`. This matches the existing entrypoint implementation at `ticket_engine_user.py:45`.

**Tests:** Allowlist matching (exact shapes allowed, variations blocked), payload injection verification, deny on injection failure, non-ticket commands pass through, **hook crash/exception → fail-open behavior documented** (accepted v1.0 limitation per canonical spec non-coverage statement).

### Task 5a: Centralized audit wrapper in engine_execute

**Files modified:** `ticket_engine_core.py`
**Tests created:** `test_audit.py`

**Architecture:** Centralize audit writes in `engine_execute` itself (not in `_execute_*` sub-functions). `engine_execute` wraps the dispatch in `try/except/finally` to enforce canonical write ordering even under exceptions:

```python
def engine_execute(...):
    # 1. Write attempt_started (action="attempt_started", result=null)
    _audit_append(session_id, {"action": "attempt_started", ...})
    try:
        # 2. Dispatch to _execute_create/_execute_update/etc.
        result = _dispatch_execute(action, ...)
        # 3. Write attempt_result with actual action and result
        _audit_append(session_id, {"action": action, "result": result.state, "changes": result.data.get("changes")})
    except Exception as exc:
        # 3b. Write attempt_result with error
        _audit_append(session_id, {"action": action, "result": f"error:{type(exc).__name__}", "changes": None})
        raise
```

- **Location:** `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
- **Entry schema:** `{ts, action, ticket_id, session_id, request_origin, autonomy_mode, result, changes}`
- `attempt_started` entries: `action: "attempt_started"`, `result: null`
- `attempt_result` entries: `action: <original_action>`, `result: <ok_*|error:code>`
- **Failure entries:** same schema with `result: "error:<code>"`, `changes: null`
- **`audit_unavailable` error code:** When audit directory cannot be created or JSONL append fails: agent callers → `policy_blocked` (error: `audit_unavailable`). User callers → proceed with warning + `unaudited: true` marker in ticket YAML frontmatter (excluded from autonomy-derived counters per canonical spec guardrail 5).
- **`autonomy_mode` source:** `engine_execute` receives `autonomy_mode` as a parameter from the caller (preflight passes it through). The audit writer does NOT independently read `ticket.local.md` — see P0-3 fix in M8.

**Tests:** Write ordering verified (attempt_started before attempt_result), exception safety (attempt_result written even on crash), `audit_unavailable` handling (agent blocked, user proceeds with marker), corruption handling (partial line tolerated), directory creation.

### Task 5b: Session counting

**Files modified:** `ticket_engine_core.py`
**Tests:** `test_audit.py` additions

Add `engine_count_session_creates(session_id)`:
- Reads session's audit file, counts entries where `action == "create"` and `result` starts with `"ok_"`
- Returns `int` on success, `AUDIT_UNAVAILABLE` sentinel on read failure
- **Consumer contract (defined by M8):** Called from `engine_preflight` for `auto_silent` session cap. Must handle: missing file (0 creates), partial/corrupt last line (skip, count preceding), permission error (`AUDIT_UNAVAILABLE`).
- **Cross-day behavior:** Counts only the current session file — session caps are per-session, not per-day.

**Tests:** Count accuracy, missing file returns 0, corrupt line handling, AUDIT_UNAVAILABLE on permission error.

### Task 6: hook_injected + session_id validation

**Files modified:** `ticket_engine_core.py`
**Tests modified:** `test_engine.py` updates

Add transport-layer field validation before subcommand dispatch:
- Agent mutations: require `hook_injected: true` + non-empty `session_id` → reject otherwise
- User mutations: warn on missing `hook_injected`/`session_id`, proceed
- Origin mismatch detection: compare `hook_request_origin` (injected by hook) vs `request_origin` (set by entrypoint). Mismatch → `origin_mismatch` → `escalate`

### Task 7: Integration — hook → engine → audit

**Tests created:** `test_hook_integration.py`

Full flow test: hook injects fields → engine validates transport layer → engine executes → audit trail written. Uses subprocess to simulate the hook input JSON that Claude Code provides.

### Gate

All prior tests pass + new hook/audit tests. PreToolUse hook tested via subprocess simulation.

---

## M8: Autonomy + Triage Script

**Goal:** Replace Phase 1's agent hard-block with the full autonomy enforcement model, add configuration parsing, and build the triage analysis script.

### Task 8: ticket.local.md parsing

**Files modified:** `ticket_engine_core.py` — extend existing `_read_autonomy_mode()` to `read_autonomy_config()`
**Tests created:** `test_autonomy.py`

Extend the existing `_read_autonomy_mode()` (line 248) to return a config object instead of just a mode string:

```python
@dataclass
class AutonomyConfig:
    mode: str          # "suggest" | "auto_audit" | "auto_silent"
    max_creates: int   # default 5
    warnings: list[str]  # any warnings from parsing
```

Parse `.claude/ticket.local.md` YAML frontmatter:
- Fields: `autonomy_mode` (suggest|auto_audit|auto_silent), `max_creates_per_session` (int, default 5)
- Defaults: `suggest`, `5`
- Fail-closed: missing file → `suggest`, malformed YAML → `suggest` + **warning** (fix existing silent `except: pass`), unknown mode → `suggest` + warning
- Engine owns all defaulting logic — callers do not parse this file
- **Note:** Replaces existing `_read_autonomy_mode()` which silently swallows all exceptions with no warning. The new function must emit warnings to stderr for malformed/unknown values.

### Task 9: Autonomy enforcement (replace hard-block)

**Files modified:** `ticket_engine_core.py` — replace hard-block in `engine_preflight` and `engine_execute`
**Tests:** `test_autonomy.py` additions

**Snapshot pattern (P0-3 fix):** `engine_preflight` reads autonomy config ONCE via `read_autonomy_config()` and includes the `AutonomyConfig` snapshot in its response. `engine_execute` receives the snapshot as a parameter — it does NOT re-read `ticket.local.md`. This prevents TOCTOU where the config file is mutated between preflight and execute (agent's `Bash` tool can write files even though `Write` is excluded from its tools list).

Replace Phase 1 agent hard-block with full policy from design doc pseudo-code:
- **Ordering (preserve Phase 1 correction):** Check `request_origin` FIRST, then confidence threshold. Phase 1 established origin-before-confidence ordering per Codex M4 finding 5 — do NOT revert to the canonical spec's original ordering.
- Confidence threshold gate: `T_base + origin_modifier` with provisional defaults (calibration required pre-GA)
- `request_origin == "unknown"` → `escalate`
- Agent + `suggest` → `policy_blocked` with rendered preview
- Agent + `auto_audit` → proceed, audit trail write, notification template
- Agent + `auto_silent` → `policy_blocked` in v1.0 (feature-gated)
- Agent action exclusions: `reopen` is user-only in v1.0
- Agent override rejection: `dedup_override` and `dependency_override` rejected for agents
- User → proceed (user explicitly invoked the operation)
- **`engine_execute` defense-in-depth:** Keep the agent block in `engine_execute` as a fallback, but it now reads from the `AutonomyConfig` snapshot (not re-reading config). The execute-level check is belt-and-suspenders — if preflight is bypassed, execute still blocks.

Phase 1 agent hard-block tests updated to test specific autonomy modes.

### Task 10a: Core triage script

**Files created:** `scripts/ticket_triage.py`
**Tests created:** `test_triage.py`

Read-only analysis script — core features:
- **Dashboard:** open/in-progress/blocked/stale ticket counts with summaries
- **Stale detection:** tickets in `open` or `in_progress` for >7 days without activity
- **Blocked chain analysis:** follow `blocked_by` references to find root blockers
- **Doc size warnings:** 16KB warn, 32KB strong warn (advisory, per design doc)

### Task 10b: Audit trail reader

**Files modified:** `scripts/ticket_triage.py`
**Tests:** `test_triage.py` additions

Add audit report capability to the triage script:
- **Audit report:** summarize recent autonomous actions from `.audit/` JSONL files
- Read per-session files, aggregate by action type and result
- Report: total creates, failures, blocked attempts, session cap hits

### Task 10c: Orphan detection

**Files modified:** `scripts/ticket_triage.py`
**Tests:** `test_triage.py` additions

Port orphan detection from handoff's `triage.py` — uses three matching strategies (NOT text-similarity):
1. **Provenance/session-ID matching:** match handoff `source.session` to ticket `source.session`
2. **Ticket-ID cross-referencing:** match ticket IDs referenced in handoff deferred items
3. **Manual review fallback:** items that don't match any ticket are flagged for review

**Note:** The canonical spec says "text-similarity" but the actual handoff `triage.py` implementation uses `uid_match` + `id_ref` + `manual_review`. Port the actual implementation, not the spec's description. The spec's "text-similarity" claim is a documentation inconsistency — file a separate fix against the canonical spec.

### Task 11: Autonomy integration

**Tests created:** `test_autonomy_integration.py`

Full flow: config → preflight → execute → audit trail with session counting. Tests `suggest` mode blocking, `auto_audit` mode proceeding + audit write + notification, session cap enforcement.

### Gate

All prior tests pass + autonomy and triage tests. Phase 1 agent hard-block behavior replaced by autonomy modes.

---

## M9: ticket-ops Skill

**Goal:** Build the user-facing skill — the primary interface for ticket operations.

### Task 12: ticket-ops SKILL.md

**Files created:** `skills/ticket-ops/SKILL.md`

~200 lines following writing-principles rules:
1. First-token routing table (create|update|close|reopen|query|list)
2. Per-operation flow: gather fields → write payload to temp file → call engine via Bash → map machine state to UX
3. Machine state → UX mapping table (14 states from design doc)
4. Payload-by-file pattern: write JSON to temp file, pass path as argument (not inline JSON)
5. Reference to `../../references/ticket-contract.md` for schemas
6. Reference to `reference.md` for detailed per-operation guides

### Task 13: reference.md (progressive disclosure)

**Files created:** `skills/ticket-ops/reference.md`

Detailed per-operation guides:
- `create`: field gathering (required vs optional), dedup flow, duplicate confirmation UX
- `update`: ticket selection (ID or fuzzy match), field diff preview, confirmation
- `close`: resolution type (`done`/`wontfix`), `--archive` option, dependency check + override
- `reopen`: reason requirement, reopen history append, user-only enforcement
- `query/list`: filter syntax, dashboard format, stale indicators

### Task 14: End-to-end integration test

**Tests created:** `test_e2e.py`

Subprocess test: user entrypoint with hook-injected fields → engine → audit → verify ticket on disk. Exercises the full Phase 2 stack without requiring a live Claude Code session.

### Task 15: Final cleanup + gate

- Version bump: `plugin.json` 1.0.0 → 1.1.0
- Contract update if needed
- Full test suite pass
- Manual verification: `/ticket list` and `/ticket create` in a live session

### Gate

All tests pass. Manual verification of skill UX in Claude Code.

---

## Dependency Graph

```
M6 (Pre-Phase 2 Fixes)
 └── M7 (Hook + Audit Trail)
      │  Sub-gates: M7a (after T4 hook), M7b (after T5b session counting)
      ├── M8 (Autonomy + Triage Script)
      │    │  Sub-gates: M8a (after T9 enforcement), M8b (after T10c orphan detection)
      │    └── M9 (ticket-ops Skill)
      └── M9 (ticket-ops Skill)
```

M6 → M7 → M8 → M9 is the critical path. M9 depends on both M7 and M8 (needs hook for payload-by-file pattern, needs autonomy for preflight behavior).

**Cross-module interface:** `engine_count_session_creates()` is implemented in M7 (Task 5b) but consumed by M8 (Task 9). The consumer contract is defined in Task 5b based on M8's needs — consumer-contract-first to avoid designing the interface before knowing its caller.

## Codex Review Strategy

Same as Phase 1: Codex review after each module completion, before gate card. Focus areas per module:

| Module | Codex Focus |
|--------|-------------|
| M6 | Rename completeness — any remaining `key_files` references in dedup path? |
| M7 | Hook security — allowlist bypass vectors, injection atomicity, failure modes |
| M8 | Autonomy policy — mode escalation paths, session counting race conditions |
| M9 | Skill UX — state mapping completeness, payload construction correctness |

## Codex Adversarial Review

4-turn adversarial Codex dialogue (thread `019cb59c-dfb4-7231-80c8-dba91163cf52`). 10 RESOLVED, 3 UNRESOLVED, 3 EMERGED.

### Findings Applied

| # | Severity | Finding | Fix Applied |
|---|----------|---------|-------------|
| P0-1 | P0 | Hook transport contract uses deprecated `decision`/`reason` fields; `request_origin` vs `hook_request_origin` field name mismatch | Updated Task 4: `hookSpecificOutput.permissionDecision` with allow/deny, explicit `hook_request_origin` field naming convention |
| P0-2 | P0 | Audit wrapper architecture unspecified — `_execute_*` sub-functions have no audit logic | Split Task 5 into 5a (centralized try/except/finally wrapper) and 5b (session counting). Added `audit_unavailable` error code and `unaudited: true` marker |
| P0-3 | P0 | Autonomy TOCTOU — reading `ticket.local.md` twice allows mode drift between preflight and execute | Added snapshot pattern: preflight reads config once, passes `AutonomyConfig` to execute |
| P1-1 | P1 | Tasks 4/5/9/10 too coarse — Task 10 bundles 6 features | Split Task 10 into 10a (core triage), 10b (audit reader), 10c (orphan detection). Total: 15→18 tasks |
| P1-2 | P1 | Task 10 claims "text-similarity" matching but handoff's `triage.py` uses `uid_match` + `id_ref` + `manual_review` | Corrected Task 10c to port actual implementation, not spec's description |
| P1-3 | P1 | Module dependency graph needs task-level DAG with sub-gates | Added task-level DAG and sub-gates (M7a/M7b, M8a/M8b) |
| P1-4 | P1 | `engine_count_session_creates` interface designed before consumer exists | Task 5b defines consumer contract based on M8's needs (consumer-contract-first) |

### Emerged

- **Audit concurrency gap:** No file-locking or multi-process consistency contract for `.audit` JSONL. Concurrent sessions could produce corruption/miscounts. Accepted for v1.0 single-user sessions; design note added.
- **Preflight ordering preservation:** Phase 1 checks origin BEFORE confidence (Codex M4 finding 5). Task 9 must preserve this ordering. Added explicit note.
- **`unaudited: true` marker:** Canonical spec guardrail 5 requires this for user callers on audit write failure. Added to Task 5a.

### Unresolved (deferred)

- Task 14 e2e test strategy: real hook infrastructure vs simulated payload (overlaps Task 7)
- Orphan detection text-similarity scope: port exact handoff logic vs new algorithm (resolved: port exact)
- Audit trail concurrency model for multi-process consistency (accepted for v1.0)

## Open Items Carried Forward

- `key_files` type split: **RESOLVED** (separate field names)
- YAML injection: **RESOLVED in M6**
- Seq overflow: **RESOLVED in M6**
- Hook transport contract: **RESOLVED** (P0-1 fix)
- Audit wrapper architecture: **RESOLVED** (P0-2 fix, Task 5a/5b)
- Autonomy TOCTOU: **RESOLVED** (P0-3 fix, snapshot pattern)
- Override flags type confusion (P2): deferred — callers are engine entrypoints that parse to bool
- `auto_silent` guardrails: v1.1 (feature-gated in v1.0)
- `merge_into_existing`: v1.1 (reserved state, escalate fallback)
- Audit concurrency: accepted for v1.0 (single-user sessions)
- Canonical spec "text-similarity" claim: needs separate fix (documentation inconsistency)
