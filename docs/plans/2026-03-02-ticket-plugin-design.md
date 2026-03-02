# Ticket Plugin Design

A standalone Claude Code plugin for repo-local ticket management. Provides full lifecycle operations (create, update, close, query, triage) with smart routing, autonomous ticket creation, and plug-and-play ticket quality.

## Architecture: Hybrid Adapter Pattern (Architecture E)

Emerged from a 12-turn collaborative Codex dialogue. Neither the initial monolith recommendation nor the multi-skill router survived — the dialogue synthesized a hybrid that combines routing precision with modular tool scoping via an engine-centric adapter pattern.

**Core principle:** All mutation and policy-enforcement logic lives in Python (engine scripts). Read-only operations (query, list) use a shared read module (`ticket_read.py`). Skills and agent are thin transport layers that map user intent to engine/read calls and states back to UX.

### Components

| Component | Type | Triggering | Purpose |
|-----------|------|-----------|---------|
| `ticket-ops` | Skill | Explicit only (`disable-model-invocation:true`) | First-token dispatch for `/ticket create\|update\|close\|query\|list` |
| `ticket-triage` | Skill | Proactive (read-only) | NL gateway — handles ambiguous input, suggests explicit commands, dashboard |
| `ticket-autocreate` | Agent | Proactive (`"use proactively"`) | Autonomous ticket creation during work, foreground-only |
| `ticket-contract.md` | Reference | Loaded by all components | Shared schemas, policies, field definitions |
| `ticket_engine_*.py` | Scripts | Called by skills/agent | Split entrypoints (`_user.py`, `_agent.py`) + shared core (`_core.py`): `classify\|plan\|preflight\|execute` |
| `ticket_read.py` | Script | Called by skills | Shared read module for `query` and `list` operations |

### Why This Architecture

| Property | How Architecture E achieves it |
|----------|-------------------------------|
| No rule drift | Single engine owns all logic; skills are pure state-to-UX mappers |
| Precise routing | `ticket-ops` uses deterministic first-token dispatch, not NLP |
| Safe proactivity | `ticket-triage` is the sole proactive NL gateway; mutations are explicit-only |
| Autonomous creation | `ticket-autocreate` agent calls engine directly; autonomy mode enforced |
| Composability | 2 skills + 1 agent compose cleanly; each has scoped `allowed-tools` |

### Rejected Alternatives

| Approach | Why Rejected |
|----------|-------------|
| A: Monolith + light agent | 500-line SKILL.md limit exceeded; all operations load every time |
| B: Pure monolith | Same as A, plus autonomous behavior mixed into skill instructions |
| C: 5-skill multi-skill | 12+ files must stay in sync; coordination cost exceeds benefit |
| D: Skill + full agent | Two places maintaining creation logic; drift between paths |

## Plugin Structure

```
ticket/                              # packages/plugins/ticket/
├── .claude-plugin/
│   └── plugin.json                  # name: "ticket", v1.0.0
├── skills/
│   ├── ticket-ops/
│   │   ├── SKILL.md                 # Explicit-only, first-token dispatch (~200 lines)
│   │   └── reference.md             # Per-operation detailed guides (progressive disclosure)
│   └── ticket-triage/
│       └── SKILL.md                 # Proactive, read-only NL gateway (~250 lines)
├── agents/
│   └── ticket-autocreate.md         # Proactive autonomous creation (~150 lines)
├── scripts/
│   ├── ticket_engine_core.py        # Shared engine logic (classify|plan|preflight|execute)
│   ├── ticket_engine_user.py        # User entrypoint (sets request_origin=user)
│   ├── ticket_engine_agent.py       # Agent entrypoint (sets request_origin=agent)
│   ├── ticket_read.py               # Shared read module (query, list, parse, filter)
│   ├── ticket_id.py                 # ID allocation (deterministic, collision-resistant)
│   ├── ticket_render.py             # Markdown rendering (template-based)
│   ├── ticket_parse.py              # Fenced-YAML parsing (multi-format, based on handoff's ticket_parsing.py)
│   └── ticket_triage.py             # Orphan detection + audit trail reporting
├── references/
│   └── ticket-contract.md           # Single source of truth: schemas, policies, fields
└── tests/
    ├── test_engine.py
    ├── test_read.py
    ├── test_id.py
    ├── test_render.py
    ├── test_parse.py
    └── test_triage.py
```

## Ticket Format

### Example Ticket

```markdown
# T-20260302-01: Fix authentication timeout on large payloads

\`\`\`yaml
id: T-20260302-01
date: "2026-03-02"
status: open
priority: high
effort: S
source:
  type: ad-hoc
  ref: ""
  session: "abc-123"
tags: [auth, api]
blocked_by: []
blocks: []
\`\`\`

## Problem
Authentication handler times out for payloads >10MB. The serialization step
takes 28s, exceeding the 30s hardcoded timeout. Users see 504 errors on large
file uploads.

## Context
The timeout was set to 30s in the initial implementation (commit abc123) and
has never been configurable. Related to the API config refactor (T-20260301-03).

## Prior Investigation
- Checked `handler.py:45` — timeout is hardcoded to 30s, not configurable
- Ruled out: connection pooling issue (pool size adequate per load test at 200 concurrent)
- Found: serialization step takes 28s for payloads >10MB (profiled with cProfile)
- Checked Redis cache — not involved in this path

## Approach
Make timeout configurable per route via the existing route config system.

### Decisions Made
- **Configurable timeout** over fixed increase — allows per-route tuning without code changes
- Rejected: async processing — would require API contract change (breaking for clients)
- Rejected: streaming upload — good long-term but scope too large for this fix

## Acceptance Criteria
- [ ] Timeout configurable per route via `routes.yaml`
- [ ] Default timeout remains 30s (backwards compatible)
- [ ] Payloads up to 50MB complete within configured timeout
- [ ] Existing tests pass unchanged

## Verification
\`\`\`bash
uv run pytest tests/test_auth.py -k timeout        # All pass
uv run pytest tests/test_routes.py -k config        # New config tests pass
curl -X POST localhost:8000/api/upload -d @50mb.json # Returns 200, not 504
\`\`\`

## Key Files
| File | Role | Look For |
|------|------|----------|
| `src/auth/handler.py:45` | Timeout logic | Hardcoded `timeout=30` in `handle_request()` |
| `src/config/routes.yaml` | Route config | Add `timeout` field to route schema |
| `src/config/routes.py` | Config loader | Parse new `timeout` field |
| `tests/test_auth.py` | Test coverage | Add parameterized timeout tests |

## Related
- Pattern to follow: `src/config/routes.yaml` existing per-route config pattern
- Related ticket: T-20260301-03 (API config refactor)
- API docs: `docs/api/configuration.md`

```

### Quality Attributes

| Attribute | How the Format Achieves It |
|-----------|---------------------------|
| **Rich context** | Problem (evidence-anchored), Context, Prior Investigation, Decisions Made |
| **Actionable structure** | Acceptance criteria (checkboxes), effort estimate, priority, Key Files with roles |
| **Traceability** | Source (type + ref + session) in frontmatter, `contract_version` in frontmatter, Related links |
| **Plug-and-play** | Prior Investigation eliminates re-walking paths; Decisions Made prevents re-debating; Verification provides exact commands; Key Files has "Look For" column |

### Plug-and-Play Design Principle

A fresh session picking up a ticket should start *doing*, not *re-investigating*. Each section eliminates a specific waste source:

| Section | Waste Eliminated |
|---------|-----------------|
| Prior Investigation | Re-exploring paths already walked, re-ruling-out dead ends |
| Decisions Made | Re-debating settled questions, flip-flopping on approach |
| Verification | Guessing how to confirm done-ness |
| Key Files (with "Look For") | Re-discovering file roles, reading wrong files first |
| Related | Missing patterns to follow, not knowing about related work |

## Skill Designs

### ticket-ops (explicit-only, first-token dispatch)

```yaml
---
name: ticket-ops
description: >-
  Create, update, close, reopen, and query repo-local tickets in docs/tickets/.
  Use when user says "/ticket create", "/ticket update", "/ticket close",
  "/ticket reopen", "/ticket query", or "/ticket list". Do NOT use for
  ambiguous natural-language ticket requests (use ticket-triage instead).
disable-model-invocation: true
argument-hint: create|update|close|reopen|query|list [args]
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
```

**Skill type:** Technique (structured method for ticket operations) + Discipline (engine enforcement)

**First-token routing table:**

| First Token | Action | Engine Pipeline |
|-------------|--------|----------------|
| `create` | Create new ticket | classify → plan → execute |
| `update` | Update existing ticket | classify → preflight → execute |
| `close` | Close/resolve ticket | classify → preflight → execute |
| `reopen` | Reopen done/wontfix ticket | classify → preflight → execute |
| `query` | Search tickets by criteria | `ticket_read.py` (shared read module) |
| `list` | Dashboard summary | `ticket_read.py` (shared read module) |
| (empty) | Dashboard | Same as `list` |

All mutating operations (`create`, `update`, `close`, `reopen`) pass through a validation gate before `execute`. For `create`, the `plan` stage handles dedup and field validation. For `update`, `close`, and `reopen`, the `preflight` stage handles precondition checks (ticket exists, status transition is valid, autonomy policy allows the mutation, dependency integrity). Read-only operations (`query`, `list`) use the shared `ticket_read.py` module directly — they do not pass through the engine pipeline.

**Body structure (~200 lines):**
1. Routing table and dispatch rules
2. Per-operation flow: gather fields → call engine → map machine state to UX
3. Machine state → UX mapping table
4. Reference to `../../references/ticket-contract.md` for schemas
5. Reference to `reference.md` for detailed operation guides

**Machine state → UX mapping:**

| Engine State | User-Facing Response |
|-------------|---------------------|
| `ok_create` | "Created T-YYYYMMDD-NN at docs/tickets/..." + show ticket |
| `ok_update` | Show field diff + confirm |
| `ok_close` | "Closed T-... (moved to archive)" |
| `ok_reopen` | "Reopened T-... (status: open). Reason: {reason}" + show Reopen History |
| `need_fields` | List missing fields, ask user to provide |
| `duplicate_candidate` | Show both tickets side by side, offer: (a) create anyway, (b) abort |
| `merge_into_existing` | **Reserved — not emitted in v1.0.** Merge algorithm and field conflict resolution deferred. If conditions would produce this state, engine returns `escalate` instead. |
| `policy_blocked` | "Autonomy policy blocks this action. Suggested: [rendered preview]" |
| `invalid_transition` | "Cannot transition from {current} to {target}: {reason}" |
| `dependency_blocked` | "Ticket has open blockers: {list}. Resolve or force-close?" |
| `not_found` | "No ticket found matching {id}. Did you mean: {fuzzy_matches}?" |
| `escalate` | Explain why engine couldn't handle, suggest manual action |

`policy_blocked` is exclusively for autonomy enforcement (autonomous caller blocked by policy). User-initiated operations that need confirmation use `duplicate_candidate` (dedup) or `dependency_blocked` (close with open blockers) — each semantically distinct confirmation reason has its own state.

### ticket-triage (proactive, read-only)

```yaml
---
name: ticket-triage
description: >-
  Triage and review repo-local tickets. Reads docs/tickets/ to report status,
  identify blocked/stale tickets, and suggest actions. Use proactively when
  conversation involves ticket review, project status, sprint planning, or when
  user mentions "triage", "backlog", "what's open", "ticket status", or
  "review tickets". Do NOT use for ticket creation or mutation (use ticket-ops).
allowed-tools: Read, Grep, Glob, Bash
---
```

**Skill type:** Technique (triage methodology) + Reference (ticket status lookup)

**Capabilities:**
- Dashboard: open/in-progress/blocked/stale ticket counts with summaries
- Stale detection: tickets in `open` or `in-progress` for >7 days without activity
- Blocked chain analysis: follow `blocked_by` references to find root blockers
- Ambiguous NL routing: interpret natural language and suggest explicit `/ticket` commands
- Orphan detection: scan recent handoffs for deferred items not yet tracked as tickets
- Audit report: summarize recent autonomous ticket actions from `docs/tickets/.audit/`

**Orphan detection implementation:** Port matching logic from handoff's `triage.py` (lines 132-180) which implements three matching strategies: provenance/session-ID matching, ticket-ID cross-referencing, and text-similarity matching against handoff deferred items. The ticket plugin needs its own `ticket_triage.py` script (added to plugin structure) to implement this — the handoff plugin's `triage.py` cannot be imported cross-plugin.

**Ambiguous NL handling:**
When user says something like "close the auth bug", triage:
1. Searches tickets matching "auth" in title/tags/problem
2. If single match → suggests: "Run `/ticket close T-20260302-01` to close it"
3. If multiple matches → presents disambiguation list
4. Never mutates — always routes to explicit commands

### ticket-autocreate (proactive agent)

```yaml
---
name: ticket-autocreate
description: >-
  Use proactively when Claude encounters a problem, bug, or improvement
  opportunity during active work that should be tracked but is out of scope
  for the current task. Creates repo-local tickets autonomously based on
  the three-tier autonomy model.
tools: Read, Grep, Glob, Bash
model: sonnet
---
```

**Trigger conditions** (agent fires when):
- Claude identifies a bug or issue while working on something else
- A TODO/FIXME is found that should be tracked
- A code review finding is worth preserving
- A Codex consultation identifies action items
- During `/save` handoff, unfinished work items are identified

**Agent behavior:**
1. Gather context from working files, recent git changes, conversation
2. Call `ticket_engine_agent.py classify` to confirm intent
3. Call `ticket_engine_agent.py plan` to check for duplicates
4. Engine reads autonomy mode from `.claude/ticket.local.md` (agent does not read this file directly — it lacks Write access to prevent self-escalation)
5. If `suggest`: return rendered preview for user confirmation (does NOT create)
6. If `auto_audit`: call `execute`, log to audit trail, notify user with template (see Autonomy section)
7. If `auto_silent`: call `execute`, log to audit trail, reduced notification (see guardrails in Autonomy section)

**Note:** The agent's `tools` list excludes `Write`. All file writes (ticket creation, audit trail) are performed by the engine script, not by the agent directly. This prevents the agent from writing to `.claude/ticket.local.md` to escalate its own autonomy mode.

## Engine Design

### Pipeline

```
ticket_engine_{user|agent}.py classify <json>    → intent + confidence
ticket_engine_{user|agent}.py plan <json>        → action plan + dedup + field validation (create only)
ticket_engine_{user|agent}.py preflight <json>   → precondition checks (update/close/reopen)
ticket_engine_{user|agent}.py execute <json>     → result + machine state
```

Skills call `ticket_engine_user.py`; the agent calls `ticket_engine_agent.py`. Both are thin wrappers that set `request_origin` and delegate to `ticket_engine_core.py`. All mutation and policy-enforcement logic lives in the core module.

**Mutation preflight** (`preflight` subcommand): All mutating operations pass through a validation gate before `execute`. The `preflight` stage checks:
- Ticket exists and is parseable
- Status transition is valid (per status transition rules in the contract)
- Autonomy policy allows the mutation (not just creation — see Trust Model below)
- Dependency integrity (`blocked_by` tickets are not still open, for `close`)
- No concurrent modification (file mtime check + plan fingerprint — see TOCTOU below)

For `create`, the existing `plan` subcommand handles dedup and field validation, which are create-specific concerns. `preflight` handles mutation-specific concerns.

**TOCTOU mitigation:** The `plan` stage returns a fingerprint (`sha256(ticket_content + mtime)`) with its action plan. The `execute` stage verifies the fingerprint before applying the mutation. If the ticket was modified between `plan` and `execute` (e.g., concurrent session), `execute` returns `stale_plan` error instead of proceeding. Risk level: Medium in single-user (concurrent Claude Code sessions are uncommon but possible). The fingerprint does not replace file-level locking — it detects the race, not prevent it.

### Dedup (hard gate in plan)

- Fingerprint: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`
- Window: scan tickets created within 24 hours
- Match: exact fingerprint → `duplicate_candidate` hard block
- Override: `force: true` in execute input (user explicitly confirmed via skill UX)

**`normalize()` specification** (canonical ordered steps):
1. Strip leading/trailing whitespace
2. Collapse all internal whitespace sequences to single space
3. Lowercase
4. Remove punctuation except hyphens and underscores
5. NFC Unicode normalization

This function is deterministic — two implementations given the same input must produce the same output. The contract must include test vectors (input → expected normalized output) to verify cross-implementation consistency.

**`force` propagation:** When the user confirms a duplicate, `ticket-ops` re-calls `execute` with `force: true`. The `plan` stage is not re-run — the user's confirmation overrides the dedup gate. The skill stores the `duplicate_candidate` response from `plan` and passes its `ticket_id` in the `force` payload so `execute` can verify the override is for the same candidate.

### Trust Model

**Security posture:** `request_origin` is a **policy selector in a trusted runtime**, not authentication. Within a single Claude Code session, all callers execute as the same OS user via Bash — there is no cryptographic caller identity. The split-entrypoint mechanism (below) provides defense-in-depth against model misbehavior, not a hard security boundary against a determined adversary. This is an accepted limitation of the plugin runtime.

Two distinct concepts that the engine must keep separate:

| Concept | Field | Set By | Purpose |
|---------|-------|--------|---------|
| **Request origin** | `request_origin` | Entrypoint script (hardcoded) | Policy selection: which autonomy rules apply |
| **Ticket provenance** | `source` (in ticket YAML) | Caller (metadata) | Traceability: where this ticket came from |

**Derivation mechanism (split entrypoints):**
- `ticket_engine_user.py` — hardcodes `request_origin = "user"`. Called by `ticket-ops` skill.
- `ticket_engine_agent.py` — hardcodes `request_origin = "agent"`. Called by `ticket-autocreate` agent.
- Both delegate to `ticket_engine_core.py` which receives `request_origin` as an internal parameter.
- `unknown` — fallback if core is called directly without an entrypoint → fail closed (reject mutation).

**Defense-in-depth layers (v1.0):**
1. Split entrypoints (cosmetic — equivalent to a CLI flag without further enforcement)
2. PreToolUse hook with **allowlist-first policy**: permits only exact engine invocation shapes (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_{user|agent}.py <subcommand> <path-to-input-file>`). Blocks all other Bash commands mentioning `ticket_engine`. **Payload-by-file:** engine input is written to a temp file and passed as a path argument rather than inline JSON, reducing the shell metacharacter attack surface.
3. Agent `tools` list excludes `Write` (prevents direct file manipulation)
4. **Detective controls:** `ticket-triage` audit report scans for engine invocations that bypassed the preventive hook (e.g., direct `_core.py` calls in audit trail). Post-exec detection complements preventive blocking.

**PreToolUse hook non-coverage statement (v1.0):**
The hook **cannot** reliably catch: shell obfuscation (`eval`, backtick expansion, `$()` substitution wrapping the engine path), calls to `_core.py` bypassing the entrypoints (detectable post-exec but not preventable), or fail-open scenarios from hook runtime errors (PreToolUse hooks are mechanically fail-open — unhandled exceptions allow the tool call to proceed). These gaps are **accepted** for v1.0; the v1.1 MCP migration eliminates all three.

**v1.1 path:** Replace Bash-based engine calls with MCP tools for a real security boundary (MCP tool names are not spoofable by the model).

The `source` field in ticket YAML (`source.type`, `source.ref`, `source.session`) is provenance metadata stored in the ticket for traceability. It has no authorization role.

### Autonomy Enforcement (in preflight and execute)

Autonomy policy gates **all mutating actions** from autonomous callers, not just `create`:

```
if request_origin == "unknown":
    → return escalate ("cannot determine caller identity")

if request_origin == "agent":
    mode = read_autonomy_mode()
    if mode == "suggest":     → return policy_blocked with preview
    if mode == "auto_audit":  → proceed, log to audit trail, notify user
    if mode == "auto_silent":
        if action != "create": → return policy_blocked ("auto_silent limited to create in v1.0")
        session_create_count = engine_count_session_creates(session_id)  # authoritative from audit trail
        if session_create_count >= max_creates_per_session: → return policy_blocked ("session cap reached")
        if session_create_count == AUDIT_UNAVAILABLE: → return policy_blocked ("audit trail unavailable, fail closed")
        → proceed, log to audit trail, reduced notification

if request_origin == "user":
    → proceed (user explicitly invoked the operation)

# force:true override is rejected when request_origin == "agent"
# (autonomous callers cannot bypass dedup)
```

Default: `suggest` (fail-closed). Configuration: `.claude/ticket.local.md`.

**`auto_silent` guardrails** (6 hard constraints):
1. Default remains `suggest` — `auto_silent` requires explicit opt-in
2. Opt-in in `.claude/ticket.local.md` must include risk acknowledgment comment
3. `max_creates_per_session` hard cap (default: 5), engine-enforced via authoritative audit trail count — cap reached → `policy_blocked`
4. **Mandatory durable summary** of all auto-created tickets written to audit trail (even in silent mode). **Best-effort user-visible digest** emitted by `ticket-triage` skill on next user-visible turn (e.g., `/ticket list` or proactive triage). Note: SessionEnd hooks output goes to debug-only — they cannot surface content to the user. The durable summary (audit trail) is guaranteed; the visible digest is best-effort.
5. If cap reached, audit trail unavailable, or audit write fails → fallback to `policy_blocked` (fail-closed for autonomous creates; proceed with warning for user creates)
6. `auto_silent` limited to `create` only in v1.0 — update/close/reopen require `auto_audit` or higher

**`auto_audit` notification template:**
```
[auto] Created T-YYYYMMDD-NN: <title summary>
  Path: docs/tickets/YYYY-MM-DD-<slug>.md
  Review: /ticket query T-YYYYMMDD-NN
```

### Autonomy Configuration (`ticket.local.md`)

Location: `.claude/ticket.local.md` (per-project, gitignored).

```yaml
---
autonomy_mode: suggest    # suggest | auto_audit | auto_silent
max_creates_per_session: 5  # hard cap for auto_audit and auto_silent
# Uncomment to enable auto_silent (risk: tickets created without notification):
# autonomy_mode: auto_silent
---
```

Uses YAML frontmatter in markdown (consistent with handoff plugin's `.local.md` pattern). Parsing contract:
- If file doesn't exist → default to `suggest`
- If file exists but frontmatter is missing or malformed → default to `suggest` + emit warning
- If `autonomy_mode` has unknown value → default to `suggest` + emit warning
- Engine owns the defaulting logic; agent and skill do not independently parse this file

### Audit Trail

Location: `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl` (per-session file within daily directory, append-only).

**Why per-session files:** (1) Session-cap counting reads one small file instead of filtering a global log. (2) Corruption in one session's file cannot affect other sessions' counts. (3) Natural partitioning for concurrent sessions.

**`session_id` delivery:** The engine receives `session_id` as a required parameter from the calling skill/agent. Claude Code provides `session_id` via hook input JSON (all hook events); the skill passes it through to the engine's stdin. If `session_id` is missing or empty, the engine fails closed (returns `escalate` for agent callers, proceeds with warning for user callers).

Each entry:

```json
{"ts": "ISO8601", "action": "create|update|close|reopen", "ticket_id": "T-...", "session_id": "abc-123", "request_origin": "agent", "autonomy_mode": "auto_audit", "result": "ok_create|ok_update|ok_close|ok_reopen", "changes": null}
```

The `changes` field is required for `update`, `close`, and `reopen` actions (null for `create`):

```json
{"changes": {"frontmatter": {"status": ["open", "in_progress"]}, "sections_changed": ["Approach", "Acceptance Criteria"]}}
```

**Engine-authoritative session counting:** `engine_count_session_creates(session_id)` reads the session's audit file and counts `action: "create"` entries. This is the sole authority for `session_create_count` — callers may pass an advisory `observed_count` for debugging but the engine ignores it for policy decisions.

**Corruption handling:** Trailing partial line (incomplete write) is tolerated — skip and count preceding complete lines. Other corruption (non-JSON lines, permission errors) → fail closed for autonomous creates (`policy_blocked`), proceed with warning for user creates. Explicit repair path: `ticket audit repair` (implementation ticket).

Read-back: `ticket-triage` can report autonomous actions by scanning the audit trail. No separate read-back mechanism needed.

### Scalability

**Current corpus:** 17 tickets. The engine performs O(n) directory scans with YAML parsing for dedup (plan stage, 24-hour window), ID allocation (execute stage, same-day scan), and triage (full scan).

**Scan budget per create:** 3 full directory scans (classify reads ticket if referenced, plan scans for dedup, execute scans for ID allocation). Each scan globs `docs/tickets/*.md` and parses YAML frontmatter.

**Acceptable at current scale:** <100 tickets. Filesystem I/O with YAML parsing is O(n) with low constant factors. At 17 tickets, the total scan time is negligible.

**Indexing plan for >500 tickets:** If the corpus grows beyond 500 tickets, the engine should build and maintain a lightweight index file (`docs/tickets/.index/tickets.jsonl`) containing `{id, date, status, priority, fingerprint, path, mtime}` per ticket. Scans read the index instead of parsing all files. Index is rebuilt on mtime mismatch. This is a v1.1 optimization — not blocking v1.0.

## Ticket Contract

The full contract lives in `references/ticket-contract.md` within the plugin. It is the single source of truth for all 10 domains below. The contract file does not exist yet — it must be created during implementation Phase 1 (engine + contract).

**Elaborated in this design doc:** Engine Interface (pipeline section), Autonomy Model (trust model + enforcement section), Dedup Policy (dedup section), Migration (migration section).

**Must be specified in the contract** (not yet elaborated):

1. **Storage** — `docs/tickets/` for active, `docs/tickets/closed-tickets/` for archived (matches existing directory). Engine reads from both locations. Directory bootstrap: engine creates directories on first write. Naming: `YYYY-MM-DD-<slug>.md` for new tickets. Slug derivation: first 6 words of title, kebab-case, `[a-z0-9-]` only, max 60 chars, sequence suffix on collision.
2. **ID Allocation** — Format: `T-YYYYMMDD-NN` (date + daily sequence). Collision prevention: scan existing tickets for same-day IDs, allocate next available NN. Legacy IDs (`T-NNN`, `T-[A-F]`, `handoff-*`) are preserved permanently — never converted.
3. **Schema** — Required YAML fields: `id`, `date`, `status`, `priority`, `source`, `contract_version`. Optional: `effort`, `tags`, `blocked_by`, `blocks`, `defer` (see below). Required sections: Problem, Approach, Acceptance Criteria, Verification, Key Files. Optional sections: Context, Prior Investigation, Decisions Made, Related, Reopen History. Section ordering rationale: Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History. Ordering follows the cognitive flow of a fresh session: understand the problem, absorb context, learn what was already tried, then see the plan and verification steps. Reopen History is last because it's audit-style append-only data, not working context.

   **Orthogonal defer field:** Deferral is not a status (the canonical 5-state set `{open, in_progress, blocked, done, wontfix}` is preserved). Instead, `defer` is an orthogonal field:
   ```yaml
   defer:
     active: true
     reason: "Waiting for upstream API v2 release"
     deferred_at: "2026-03-02"
   ```
   When `defer.active: true`, the ticket remains in its current canonical status (`open`, `in_progress`, etc.) but triage reports it in a separate "deferred" group. This preserves triage semantics — stale detection skips deferred tickets, and re-activating a deferred ticket is a metadata change (`defer.active: false`), not a status transition.

   **Doc size soft guardrails:** Tickets with growing sections (Prior Investigation, Decisions Made, Reopen History) can expand unboundedly. Guardrails:
   - 16KB: `ticket-triage` emits warning: "Ticket approaching size threshold — consider splitting or archiving sections"
   - 32KB: `ticket-triage` emits strong warning: "Ticket exceeds recommended size — split recommended"
   - No hard enforcement in v1.0 — the engine does not reject large tickets. Guardrails are advisory via triage reporting.
4. **Engine Interface** — stdin/stdout/stderr contracts for `classify`, `plan`, `preflight`, and `execute` subcommands. Exit codes: 0 (success), 1 (engine error), 2 (validation failure).

   **Minimum schema shape contract** (field names, types, enumerations — full JSON schemas are implementation-level):

   **Common response envelope** (all subcommands):
   ```
   {state: string, ticket_id: string|null, message: string, data: object}
   ```
   `state` is one of the 12 machine states. `data` is subcommand-specific.

   **Per-subcommand I/O shapes:**

   | Subcommand | Input Fields | Output `data` Fields |
   |-----------|-------------|---------------------|
   | `classify` | `action: string`, `args: object`, `session_id: string`, `request_origin: string` | `intent: string`, `confidence: float`, `resolved_ticket_id: string\|null` |
   | `plan` | `intent: string`, `fields: object`, `session_id: string`, `request_origin: string` | `fingerprint: string`, `duplicate_of: string\|null`, `missing_fields: list[string]`, `action_plan: object` |
   | `preflight` | `ticket_id: string`, `action: string`, `session_id: string`, `request_origin: string`, `plan_fingerprint: string` | `checks_passed: list[string]`, `checks_failed: list[{check: string, reason: string}]` |
   | `execute` | `action: string`, `ticket_id: string\|null`, `fields: object`, `session_id: string`, `request_origin: string`, `plan_fingerprint: string\|null`, `force: bool` | `ticket_path: string`, `changes: object\|null` |

   **Deterministic error codes:** `missing_field`, `invalid_transition`, `policy_blocked`, `stale_plan`, `duplicate_detected`, `audit_unavailable`, `parse_error`, `not_found`. Each maps to exactly one machine state.

   **Behavior rules:** Unknown fields in input are **ignored** (forward-compatible — new callers can add fields that old engines skip). Missing required fields → exit code 2 + `need_fields` state.
5. **Autonomy Model** — mode definitions, `ticket.local.md` parsing, `request_origin` derivation, audit trail format. See Trust Model section above.
6. **Dedup Policy** — `normalize()` algorithm with test vectors, fingerprint construction, 24-hour window, `force` override protocol. See Dedup section above.
7. **Status Transitions** — allowed transitions with preconditions:
   - `open` → `in_progress` (no preconditions)
   - `open` → `blocked` (requires `blocked_by` non-empty)
   - `in_progress` → `open` (no preconditions — re-queue)
   - `in_progress` → `blocked` (requires `blocked_by` non-empty)
   - `in_progress` → `done` (requires acceptance criteria present)
   - `blocked` → `open` (all `blocked_by` resolved)
   - `blocked` → `in_progress` (all `blocked_by` resolved — resume directly)
   - `*` → `wontfix` (no preconditions)
   - `done` → `open` (requires `reopen_reason`, user-only in v1.0, appends to ## Reopen History)
   - `wontfix` → `open` (requires `reopen_reason`, user-only in v1.0, appends to ## Reopen History)
   - `done`/`wontfix` → archive (explicit `/ticket close --archive`, move to `closed-tickets/` directory)
   - **Status normalization** (dual-status model, port from handoff's `triage.py`): raw statuses from legacy tickets are normalized to canonical statuses. Transitions are evaluated in canonical space only. Unknown raw statuses → fail closed during mutation (block the operation).

   | Raw Status | Canonical Status |
   |-----------|-----------------|
   | `planning` | `open` |
   | `implementing` | `in_progress` |
   | `complete` | `done` |
   | `closed` | `done` |
   | `deferred` | `open` (with `defer.active: true`, `defer.reason` from context if available) |
8. **Migration** — see Migration section below. **Golden test requirement:** The contract must include at least one golden test file per legacy generation (Gen 1-4) with expected parsed output, covering field mapping, section renaming, and status normalization. These are regression tests for the read path.
9. **Integration** — external consumers read `docs/tickets/*.md` as plain markdown with fenced YAML blocks. No API or import mechanism. Handoff's `/save` can reference ticket IDs in its output. Format uses fenced YAML (`` ```yaml ```) not YAML frontmatter (`---`), consistent with existing tickets and `ticket_parsing.py`.
10. **Versioning** — `contract_version` in YAML frontmatter (top-level field). Current: `"1.0"`. Compatibility: engine reads all versions; writes latest only. Legacy `ticket-meta` comment footers are readable for migration (Gen 1-3 may have them) but never written by the ticket plugin. If both frontmatter and footer contain `contract_version`, frontmatter wins — emit warning for the discrepancy.

All three components (ticket-ops, ticket-triage, ticket-autocreate) reference this contract. Changes to the contract are the mechanism for evolving the system.

## Relationship to Handoff Plugin

**Clean break with format-as-contract:**
- Ticket plugin owns all ticket infrastructure (creation, management, triage)
- Handoff plugin removes `/defer` skill and `defer.py` script
- Handoff plugin removes `/triage` skill (migrated to ticket plugin)
- Handoff reads ticket files (plain markdown in `docs/tickets/`) for any remaining integration

**Provider switch via DeferredWorkEnvelope:**
- Handoff's `/save` emits a neutral `DeferredWorkEnvelope` (JSON) for each unfinished work item, containing: `title`, `problem`, `context`, `source` metadata, and `suggested_priority`
- Ticket plugin supports explicit ingestion: `/ticket create --from-envelope <path>` reads the envelope and creates a ticket
- Optional autonomous ingestion: `ticket-autocreate` agent can process envelopes when configured with `auto_audit` or higher autonomy
- Transition sequence: (1) Ticket plugin ships with envelope support. (2) Handoff's `/save` emits envelopes instead of calling `defer.py`. (3) After telemetry confirms stability, deprecate `/defer`. (4) Remove `defer.py` and `/defer` skill.
- Envelope format is an implementation detail — handoff and ticket plugins agree on a shared schema in their respective contracts

**Migration path:**
- New tickets always use v1.0 format
- Legacy IDs are preserved permanently — never converted to `T-YYYYMMDD-NN`
- Engine reads all 4 legacy generations (read-only, no write-back on read)
- Updating a legacy ticket converts it to v1.0 format (with user confirmation + diff preview)

**Legacy format read support:**

| Generation | ID Pattern | Key Field Differences | Read Strategy |
|-----------|------------|----------------------|---------------|
| Gen 1 (hand-authored) | Slug (`handoff-chain-viz`) | `plugin`, `related` (flat list), no `source`/`tags`/`effort` | Map `related` → informational only (not directional `blocks`/`blocked_by`). Ignore `plugin`. Missing fields default to empty. |
| Gen 2 (letter IDs) | `T-[A-F]` | `branch`, `effort: "S (1-2 sessions)"` (free text), sections: Summary/Rationale/Design/Risks | Parse `effort` as free text (no validation). Map Summary → Problem. Other sections preserved as-is. |
| Gen 3 (numeric IDs) | `T-NNN` | `branch`, sections: Summary/Prerequisites/Findings/Verification/References (plus varied per-ticket sections) | Map Summary → Problem, Findings → Prior Investigation. Unrecognized sections preserved verbatim. |
| Gen 4 (defer output) | `T-YYYYMMDD-NN` | `source_type`, `source_ref`, `provenance` dict, `status: deferred`, sections: Problem/Source/Proposed Approach/Acceptance Criteria | Map `provenance` → `source` (`source_type` → `source.type`, `source_ref` → `source.ref`). Map `status: deferred` → `open`. Map Proposed Approach → Approach. Read-time defaults: `priority: medium`, `source.type: defer`. |

**Section renaming strategy** (3-tier deterministic, applied during conversion):

| Tier | Rule | Examples |
|------|------|---------|
| Exact rename | Known section name → v1.0 equivalent | Summary → Problem, Findings → Prior Investigation, Proposed Approach → Approach, Files Affected → Key Files, Files to Create/Modify → Key Files |
| Near-equivalent | Semantically close → v1.0 section | Scope → Context, Risks → Context |
| Preserve verbatim | Unrecognized section name | Design Space, Cross-Cutting Issues, P1/P2/P3, Deferred Findings, Execution Plan, Open Questions, Positive Security Assessment — kept as-is with original heading |

**Field defaults for legacy tickets** (applied on read, not written back):

| Missing Field | Default Value | Rationale |
|--------------|--------------|-----------|
| `priority` | `medium` | Safe middle ground |
| `source` | `{type: "legacy", ref: "", session: ""}` | Distinguishes from new tickets |
| `effort` | (empty) | Cannot be inferred |
| `tags` | `[]` | Cannot be inferred |
| `blocked_by` / `blocks` | `[]` | Unless already present (Gen 2/3 have these) |

**Ignored legacy fields:** `plugin` (Gen 1), `branch` (Gen 2/3) — ephemeral metadata, not migrated to v1.0. `branch` info is preserved in git history.

**Conversion on update:** When a user runs `/ticket update` on a legacy ticket:
1. Engine reads the legacy ticket and maps fields per the table above
2. Renders a v1.0 preview with diff showing what changed
3. User confirms the conversion
4. Engine writes v1.0 format, preserving the original ID
5. No rollback mechanism — the original content is visible in git history

**What is NOT converted:** Legacy IDs stay as-is. `related` fields in Gen 1 become a `## Related` section (not `blocked_by`/`blocks` — the semantic distinction between undirected relation and directional dependency cannot be inferred automatically).

## Codex Dialogue Provenance

Architecture E emerged from a 12-turn collaborative Codex dialogue (thread `019cad28-6567-7f12-9bbd-1f9a96d46b33`). Key convergence points:

- **T2:** Codex conceded description-based skill selection can't disambiguate 5 similar operations → invocation contract pattern
- **T4:** Engine-centric adapter pattern emerged — both sides agreed business logic belongs in code, not markdown
- **T5:** Reduced from 5 skills to 2 — first-token routing in ticket-ops handles create/update/close/query without separate skills
- **T6:** Three-tier autonomy model with fail-closed default
- **T7:** Dedup as mandatory hard gate via deterministic fingerprinting

All 7 key outcomes RESOLVED with high confidence. 3 items EMERGED (Architecture E itself, invocation contract pattern, `skills:` injection limitation).

### Adversarial Review

6-turn adversarial Codex dialogue (thread `019caf2e-9901-7a41-be8b-9a3c862c273f`). 10 RESOLVED, 5 UNRESOLVED, 3 EMERGED.

**Critical findings (applied to this design doc):**

| # | Finding | Fix Applied |
|---|---------|-------------|
| 1 | `update`/`close` skip `plan`, bypassing validation + autonomy | Added `preflight` subcommand; all mutations pass through validation gate |
| 2 | `source` field is confused deputy — caller can claim `source: "user"` | Separated `request_origin` (runtime, trusted) from `source` (provenance, metadata) |
| 3 | Migration "read legacy, convert on update" had no spec | Added field mapping table for 3 legacy generations + conversion rules |
| 4 | Contract claimed SSOT but 6/10 domains were empty | Elaborated all 10 domains with requirements |
| 5 | Orphan detection capability silently dropped from handoff migration | Added `ticket_triage.py` script + implementation path |
| 6 | `ticket.local.md` had no format spec | Added parsing contract with fail-closed defaults |
| 7 | `normalize()` in dedup fingerprint was unspecified | Added 5-step canonical normalization + test vector requirement |

**Emerged insights:**
- Privilege-escalation path from interaction of pipeline bypass + autonomy gap (neither alone is critical)
- `request_origin` vs `ticket_source` trust model decomposition
- "Decomposition is sound, control flow is not" — the architecture is correct; the pipeline and migration needed fixing

**Unresolved (deferred to implementation):**
- ~~Whether `triage.py`'s dual-status model should be adopted~~ → **Resolved:** adopted. See Status Transitions section.
- `ticket-autocreate` foreground-only constraint has no enforcement mechanism (agents lack native foreground/background distinction)
- ~~YAML frontmatter vs fenced yaml blocks~~ → **Resolved:** fenced blocks (consistent with existing tickets)

### 5-Agent Team Review + Collaborative Codex Dialogue

5-agent team review (architecture, security, migration, UX, enhancement) produced 57 findings: 1 Critical, 10 High, 18 Medium, 11 Low, 17 Enhancement. Followed by a 6-turn collaborative Codex dialogue (thread `019caf51-7725-78f1-9a91-ad1b20e047bd`). 10 RESOLVED, 3 UNRESOLVED, 3 EMERGED.

**Findings applied to this design doc:**

| # | Source | Severity | Finding | Fix Applied |
|---|--------|----------|---------|-------------|
| 1 | UX | Critical | `done`/`wontfix` are terminal — no reopen path | Added reopen transitions with `reopen_reason` requirement, user-only in v1.0 |
| 2 | Security | High | Agent can write `ticket.local.md` to escalate autonomy | Removed `Write` from agent `tools` list |
| 3 | Arch+Sec | High | `request_origin` derivation mechanism unspecified | Added split entrypoints + honest defense-in-depth framing |
| 4 | Arch | High | `query`/`list` bypass engine, contradicting core principle | Added `ticket_read.py` shared read module; restated engine principle (mutations only) |
| 5 | UX | High | `auto_silent` creates files user doesn't know about | Added 6 hard guardrails (cap, summary, opt-in, create-only, fail-closed) |
| 6 | UX | High | `duplicate_candidate` abort is dead end | Added `merge_into_existing` outcome to machine state table |
| 7 | Migration | High | Section mapping too narrow — real tickets have unmapped sections | Added 3-tier section renaming, field defaults, Gen 4 support, status normalization |

**Emerged from dialogue:**
- `ticket_read.py` as shared read module prevents duplication between ticket-ops and ticket-triage
- Audit trail `changes` field (`frontmatter` diff + `sections_changed`) required for update/close/reopen
- 4th legacy generation (defer.py output) with distinct field requirements and read-time defaults

**Previously unresolved (now resolved by deeper review):**
- ~~Provider switch mechanism for `/save` → ticket routing~~ → **Resolved:** DeferredWorkEnvelope bridge. See Relationship to Handoff Plugin section.
- ~~Who writes the session-end summary for `auto_silent`~~ → **Resolved:** Guardrail 4 rewritten. Durable summary in audit trail (guaranteed) + skill-owned visible digest on next turn (best-effort). SessionEnd hooks are debug-only.
- ~~PreToolUse hook reliability~~ → **Resolved:** Allowlist-first policy with documented non-coverage statement. See Trust Model section.

**Implementation tickets (not design-level):**
- `auto_audit` notification UX flows (confirmation handling, undo path)
- `merge_into_existing` UX flows deferred to v1.1 (state reserved in v1.0, escalate fallback)
- `ticket audit repair` command for corrupted audit files
- DeferredWorkEnvelope schema definition (shared between handoff and ticket plugins)

### Deeper Review (Evaluative Codex Dialogue)

6-turn evaluative Codex dialogue (thread `019caf7f-6c81-7453-9ecf-c4f5a3980acf`). 12 RESOLVED, 3 UNRESOLVED, 5 EMERGED.

**Findings applied to this design doc:**

| # | Finding | Fix Applied |
|---|---------|-------------|
| 1 | Engine Interface has no schema shapes — implementer can't code I/O | Added minimum schema shape contract: common envelope, per-subcommand field tables, error codes, unknown-field policy |
| 2 | `session_create_count` caller-tracked — trust boundary violation | Engine-authoritative via per-session audit trail; caller count advisory only |
| 3 | `ticket-meta` footer duplicates YAML frontmatter provenance | Eliminated footer; `contract_version` moved to frontmatter; legacy footers readable for migration |
| 4 | Summary writer guardrail 4 unimplementable (SessionEnd is debug-only) | Split: durable audit summary (guaranteed) + skill-owned visible digest (best-effort) |
| 5 | Provider switch mechanism unspecified | DeferredWorkEnvelope bridge with explicit `/ticket create --from-envelope` path |
| 6 | `merge_into_existing` has no engine logic | Reserved in v1.0; `escalate` fallback; removed from `duplicate_candidate` options |
| 7 | `deferred` mapped to `open` loses triage semantics | Orthogonal `defer` field (`defer.active`, `defer.reason`, `defer.deferred_at`) |
| 8 | PreToolUse hook fragile for arbitrary shell patterns | Allowlist-first + payload-by-file + documented non-coverage + detective controls |
| 9 | Session counting needs fail-closed + corruption handling | Fail closed for autonomous; per-session audit files; explicit repair path |
| 10 | Doc size threshold unaddressed | Soft guardrails: 16KB warn, 32KB strong warn, no hard enforcement v1.0 |
| 11 | 3-scan-per-create scalability concern | Acceptable at <100; indexing plan documented for >500 |
| 12 | TOCTOU risk in plan→execute gap | Plan fingerprint (`sha256(content+mtime)`) verified by execute; `stale_plan` error on mismatch |

**Additional items from areas of agreement:**
- `Reopen History` added to schema optional sections list
- `test_read.py` added to test plan for `ticket_read.py` shared module
- Migration golden tests required (1 per legacy generation)
- Status normalization for `deferred` now sets `defer.active: true`

**Emerged from dialogue:**
- Build-blocker vs integration-blocker severity distinction for review findings
- Payload-by-file pattern reduces shell metacharacter attack surface
- Per-session audit files (`YYYY-MM-DD/<session_id>.jsonl`) solve counting + blast radius
- Detective controls (post-exec audit check) complement preventive PreToolUse hook
- DeferredWorkEnvelope as decoupled bridge between plugins

**Unresolved (deferred to implementation):**
- Full error code enumeration for engine I/O (8 codes specified; full set during implementation)
- Per-session audit file race conditions vs daily file approach (implied concern, not probed)

**Review history (complete):**

| Round | Posture | Thread | Turns | Outcome |
|-------|---------|--------|-------|---------|
| 1. Collaborative Codex | collaborative | `019cad28-6567-7f12-9bbd-1f9a96d46b33` | 12 | Architecture E emerged (7 RESOLVED, 3 EMERGED) |
| 2. Adversarial Codex | adversarial | `019caf2e-9901-7a41-be8b-9a3c862c273f` | 6 | 7 control-plane flaws fixed (10 RESOLVED, 5 UNRESOLVED, 3 EMERGED) |
| 3. 5-agent team review | multi-lens | — | — | 57 findings (1C, 10H, 18M, 11L, 17E) |
| 4. Collaborative Codex | collaborative | `019caf51-7725-78f1-9a91-ad1b20e047bd` | 6 | Triage + prioritization (10 RESOLVED, 3 UNRESOLVED, 3 EMERGED) |
| 5. Deeper review Codex | evaluative | `019caf7f-6c81-7453-9ecf-c4f5a3980acf` | 6 | Testability, contracts, integration, scale (12 RESOLVED, 3 UNRESOLVED, 5 EMERGED) |
