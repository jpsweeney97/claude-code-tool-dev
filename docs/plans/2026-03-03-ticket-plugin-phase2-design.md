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
| **M7: Hook + Audit Trail** | PreToolUse hook, audit trail JSONL, hook_injected validation | M6 | 4 |
| **M8: Autonomy + Triage Script** | ticket.local.md parsing, autonomy enforcement, ticket_triage.py | M7 | 4 |
| **M9: ticket-ops Skill** | SKILL.md, reference.md, e2e integration, version bump | M7, M8 | 4 |

Total: 15 tasks across 4 modules.

---

## M6: Pre-Phase 2 Fixes

**Goal:** Resolve three known defects before building new Phase 2 components.

### Task 1: key_files field rename

**Files modified:** `ticket_engine_core.py`, `ticket_dedup.py`, `ticket-contract.md`
**Tests modified:** `test_engine.py`, `test_dedup.py`, `test_integration.py`

Rename `key_files` to `key_file_paths` in the dedup/plan pipeline:
- `engine_plan` input/output: `key_file_paths: list[str]` (file paths for fingerprinting)
- `dedup_fingerprint()`: accepts `key_file_paths` parameter
- `render_ticket`: keeps `key_files: list[dict]` (structured table rows with file/role/look_for)
- `engine_execute`: receives `key_file_paths` for dedup verification, `key_files` for rendering (separate fields)
- Contract: document both fields with types

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
2. Inject `session_id` (from hook input JSON), `hook_injected: true`, `request_origin` (derived from entrypoint basename: `ticket_engine_user.py` → `"user"`, `ticket_engine_agent.py` → `"agent"`)
3. Write temp file → fsync → rename (atomic replacement)
4. If injection fails → exit code 2 (block)

**Hook output:** Prompt-based hooks API — returns JSON with `decision` (allow/block) and optional `reason`.

**Tests:** Allowlist matching (exact shapes allowed, variations blocked), payload injection verification, block on injection failure, non-ticket commands pass through.

### Task 5: Audit trail writes in engine

**Files modified:** `ticket_engine_core.py`
**Tests created:** `test_audit.py`

Add audit JSONL append in `engine_execute`:
- **Location:** `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
- **Write ordering:** `attempt_started` entry first → ticket file write → `attempt_result` entry
- **Entry schema:** `{ts, action, ticket_id, session_id, request_origin, autonomy_mode, result, changes}`
- **Failure entries:** same schema with `result: "error:<code>"`, `changes: null`
- Add `engine_count_session_creates(session_id)` — reads session's audit file, counts `action: "create"` entries

**Tests:** Write ordering verified, corruption handling (partial line tolerated), session counting, failure entries, directory creation.

### Task 6: hook_injected + session_id validation

**Files modified:** `ticket_engine_core.py`
**Tests modified:** `test_engine.py` updates

Add transport-layer field validation before subcommand dispatch:
- Agent mutations: require `hook_injected: true` + non-empty `session_id` → reject otherwise
- User mutations: warn on missing `hook_injected`/`session_id`, proceed
- `request_origin` mismatch detection: hook-injected value vs entrypoint value → `origin_mismatch` → `escalate`

### Task 7: Integration — hook → engine → audit

**Tests created:** `test_hook_integration.py`

Full flow test: hook injects fields → engine validates transport layer → engine executes → audit trail written. Uses subprocess to simulate the hook input JSON that Claude Code provides.

### Gate

All prior tests pass + new hook/audit tests. PreToolUse hook tested via subprocess simulation.

---

## M8: Autonomy + Triage Script

**Goal:** Replace Phase 1's agent hard-block with the full autonomy enforcement model, add configuration parsing, and build the triage analysis script.

### Task 8: ticket.local.md parsing

**Files modified:** `ticket_engine_core.py` — add `read_autonomy_config()`
**Tests created:** `test_autonomy.py`

Parse `.claude/ticket.local.md` YAML frontmatter:
- Fields: `autonomy_mode` (suggest|auto_audit|auto_silent), `max_creates_per_session` (int, default 5)
- Defaults: `suggest`, `5`
- Fail-closed: missing file → `suggest`, malformed YAML → `suggest` + warning, unknown mode → `suggest` + warning
- Engine owns all defaulting logic — callers do not parse this file

### Task 9: Autonomy enforcement (replace hard-block)

**Files modified:** `ticket_engine_core.py` — replace hard-block in `engine_preflight` and `engine_execute`
**Tests:** `test_autonomy.py` additions

Replace Phase 1 agent hard-block with full policy from design doc pseudo-code:
- Confidence threshold gate: `T_base + origin_modifier` with provisional defaults (calibration required pre-GA)
- `request_origin == "unknown"` → `escalate`
- Agent + `suggest` → `policy_blocked` with rendered preview
- Agent + `auto_audit` → proceed, audit trail write, notification template
- Agent + `auto_silent` → `policy_blocked` in v1.0 (feature-gated)
- Agent action exclusions: `reopen` is user-only in v1.0
- Agent override rejection: `dedup_override` and `dependency_override` rejected for agents
- User → proceed (user explicitly invoked the operation)

Phase 1 agent hard-block tests updated to test specific autonomy modes.

### Task 10: ticket_triage.py script

**Files created:** `scripts/ticket_triage.py`
**Tests created:** `test_triage.py`

Read-only analysis script:
- **Dashboard:** open/in-progress/blocked/stale ticket counts with summaries
- **Stale detection:** tickets in `open` or `in_progress` for >7 days without activity
- **Blocked chain analysis:** follow `blocked_by` references to find root blockers
- **Orphan detection:** port matching logic from handoff's `triage.py` (provenance/session-ID matching, ticket-ID cross-referencing, text-similarity)
- **Audit report:** summarize recent autonomous actions from `.audit/`
- **Doc size warnings:** 16KB warn, 32KB strong warn (advisory, per design doc)

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
      ├── M8 (Autonomy + Triage Script)
      │    └── M9 (ticket-ops Skill)
      └── M9 (ticket-ops Skill)
```

M6 → M7 → M8 → M9 is the critical path. M9 depends on both M7 and M8 (needs hook for payload-by-file pattern, needs autonomy for preflight behavior).

## Codex Review Strategy

Same as Phase 1: Codex review after each module completion, before gate card. Focus areas per module:

| Module | Codex Focus |
|--------|-------------|
| M6 | Rename completeness — any remaining `key_files` references in dedup path? |
| M7 | Hook security — allowlist bypass vectors, injection atomicity, failure modes |
| M8 | Autonomy policy — mode escalation paths, session counting race conditions |
| M9 | Skill UX — state mapping completeness, payload construction correctness |

## Open Items Carried Forward

- `key_files` type split: **RESOLVED** (separate field names)
- YAML injection: **RESOLVED in M6**
- Seq overflow: **RESOLVED in M6**
- Override flags type confusion (P2): deferred — callers are engine entrypoints that parse to bool
- `auto_silent` guardrails: v1.1 (feature-gated in v1.0)
- `merge_into_existing`: v1.1 (reserved state, escalate fallback)
