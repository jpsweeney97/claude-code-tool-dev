# Ticket Plugin Design

A standalone Claude Code plugin for repo-local ticket management. Provides full lifecycle operations (create, update, close, query, triage) with smart routing, autonomous ticket creation, and plug-and-play ticket quality.

## Architecture: Hybrid Adapter Pattern (Architecture E)

Emerged from a 12-turn collaborative Codex dialogue. Neither the initial monolith recommendation nor the multi-skill router survived — the dialogue synthesized a hybrid that combines routing precision with modular tool scoping via an engine-centric adapter pattern.

**Core principle:** All decision logic lives in Python (`ticket_engine.py`). Skills and agent are thin transport layers that map user intent to engine calls and engine states back to UX.

### Components

| Component | Type | Triggering | Purpose |
|-----------|------|-----------|---------|
| `ticket-ops` | Skill | Explicit only (`disable-model-invocation:true`) | First-token dispatch for `/ticket create\|update\|close\|query\|list` |
| `ticket-triage` | Skill | Proactive (read-only) | NL gateway — handles ambiguous input, suggests explicit commands, dashboard |
| `ticket-autocreate` | Agent | Proactive (`"use proactively"`) | Autonomous ticket creation during work, foreground-only |
| `ticket-contract.md` | Reference | Loaded by all components | Shared schemas, policies, field definitions |
| `ticket_engine.py` | Script | Called by skills/agent | Canonical decision engine: `classify\|plan\|preflight\|execute` subcommands |

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
│   ├── ticket_engine.py             # Canonical decision engine (classify|plan|preflight|execute)
│   ├── ticket_id.py                 # ID allocation (deterministic, collision-resistant)
│   ├── ticket_render.py             # Markdown rendering (template-based)
│   ├── ticket_parse.py              # Fenced-YAML parsing (multi-format, based on handoff's ticket_parsing.py)
│   └── ticket_triage.py             # Orphan detection + audit trail reporting
├── references/
│   └── ticket-contract.md           # Single source of truth: schemas, policies, fields
└── tests/
    ├── test_engine.py
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

<!-- ticket-meta {"source_session": "abc-123", "source_type": "ad-hoc", "created_by": "ticket-ops", "contract_version": "1.0", "v": 1} -->
```

### Quality Attributes

| Attribute | How the Format Achieves It |
|-----------|---------------------------|
| **Rich context** | Problem (evidence-anchored), Context, Prior Investigation, Decisions Made |
| **Actionable structure** | Acceptance criteria (checkboxes), effort estimate, priority, Key Files with roles |
| **Traceability** | Source (type + ref + session), ticket-meta footer, Related links |
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
  Create, update, close, and query repo-local tickets in docs/tickets/.
  Use when user says "/ticket create", "/ticket update", "/ticket close",
  "/ticket query", or "/ticket list". Do NOT use for ambiguous natural-language
  ticket requests (use ticket-triage instead).
disable-model-invocation: true
argument-hint: create|update|close|query|list [args]
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
| `query` | Search tickets by criteria | Direct file read + filter |
| `list` | Dashboard summary | Direct file read + summarize |
| (empty) | Dashboard | Same as `list` |

All mutating operations (`create`, `update`, `close`) pass through a validation gate before `execute`. For `create`, the `plan` stage handles dedup and field validation. For `update` and `close`, the `preflight` stage handles precondition checks (ticket exists, status transition is valid, autonomy policy allows the mutation, dependency integrity).

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
| `need_fields` | List missing fields, ask user to provide |
| `duplicate_candidate` | Show both tickets side by side, ask user to confirm or abort |
| `policy_blocked` | "Autonomy policy blocks this action. Suggested: [rendered preview]" |
| `invalid_transition` | "Cannot transition from {current} to {target}: {reason}" |
| `dependency_blocked` | "Ticket has open blockers: {list}. Resolve or force-close?" |
| `not_found` | "No ticket found matching {id}" |
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
tools: Read, Grep, Glob, Bash, Write
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
2. Call `ticket_engine.py classify` to confirm intent
3. Call `ticket_engine.py plan` to check for duplicates
4. Read autonomy mode from `.claude/ticket.local.md`
5. If `suggest`: return rendered preview for user confirmation (does NOT create)
6. If `auto_audit`: call `execute`, log to audit trail, notify user
7. If `auto_silent`: call `execute`, log to audit trail, no notification

## Engine Design

### Pipeline

```
ticket_engine.py classify <json>    → intent + confidence
ticket_engine.py plan <json>        → action plan + dedup + field validation (create only)
ticket_engine.py preflight <json>   → precondition checks (update/close)
ticket_engine.py execute <json>     → result + machine state
```

All decision logic lives here. Skills and agent call the engine and map its machine states to appropriate UX.

**Mutation preflight** (`preflight` subcommand): All mutating operations pass through a validation gate before `execute`. The `preflight` stage checks:
- Ticket exists and is parseable
- Status transition is valid (per status transition rules in the contract)
- Autonomy policy allows the mutation (not just creation — see Trust Model below)
- Dependency integrity (`blocked_by` tickets are not still open, for `close`)
- No concurrent modification (file mtime check)

For `create`, the existing `plan` subcommand handles dedup and field validation, which are create-specific concerns. `preflight` handles mutation-specific concerns.

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

Two distinct concepts that the engine must keep separate:

| Concept | Field | Set By | Purpose |
|---------|-------|--------|---------|
| **Request origin** | `request_origin` | Engine (runtime-derived) | Authorization: who is calling the engine |
| **Ticket provenance** | `source` (in ticket YAML) | Caller (metadata) | Traceability: where this ticket came from |

`request_origin` is determined by the engine from runtime context — never from caller payload. Values:
- `user` — called from `ticket-ops` skill (user explicitly invoked `/ticket`)
- `agent` — called from `ticket-autocreate` agent
- `unknown` — origin cannot be determined → fail closed (reject mutation)

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
    if mode == "auto_silent": → proceed, log to audit trail, no notification

if request_origin == "user":
    → proceed (user explicitly invoked the operation)
```

Default: `suggest` (fail-closed). Configuration: `.claude/ticket.local.md`.

### Autonomy Configuration (`ticket.local.md`)

Location: `.claude/ticket.local.md` (per-project, gitignored).

```yaml
---
autonomy_mode: suggest    # suggest | auto_audit | auto_silent
---
```

Uses YAML frontmatter in markdown (consistent with handoff plugin's `.local.md` pattern). Parsing contract:
- If file doesn't exist → default to `suggest`
- If file exists but frontmatter is missing or malformed → default to `suggest` + emit warning
- If `autonomy_mode` has unknown value → default to `suggest` + emit warning
- Engine owns the defaulting logic; agent and skill do not independently parse this file

### Audit Trail

Location: `docs/tickets/.audit/YYYY-MM-DD.jsonl` (one file per day, append-only).

Each entry:

```json
{"ts": "ISO8601", "action": "create|update|close", "ticket_id": "T-...", "request_origin": "agent", "autonomy_mode": "auto_audit", "result": "ok_create|ok_update|ok_close"}
```

Read-back: `ticket-triage` can report autonomous actions by scanning the audit trail. No separate read-back mechanism needed.

## Ticket Contract

The full contract lives in `references/ticket-contract.md` within the plugin. It is the single source of truth for all 10 domains below. The contract file does not exist yet — it must be created during implementation Phase 1 (engine + contract).

**Elaborated in this design doc:** Engine Interface (pipeline section), Autonomy Model (trust model + enforcement section), Dedup Policy (dedup section), Migration (migration section).

**Must be specified in the contract** (not yet elaborated):

1. **Storage** — `docs/tickets/` for active, `docs/tickets/closed/` for archived. Directory bootstrap: engine creates directories on first write. Naming: `YYYY-MM-DD-<slug>.md` for new tickets.
2. **ID Allocation** — Format: `T-YYYYMMDD-NN` (date + daily sequence). Collision prevention: scan existing tickets for same-day IDs, allocate next available NN. Legacy IDs (`T-NNN`, `T-[A-F]`, `handoff-*`) are preserved permanently — never converted.
3. **Schema** — Required YAML fields: `id`, `date`, `status`, `priority`, `source`. Optional: `effort`, `tags`, `blocked_by`, `blocks`. Required sections: Problem, Approach, Acceptance Criteria, Verification, Key Files. Optional sections: Context, Prior Investigation, Decisions Made, Related. Section ordering rationale: Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related. Ordering follows the cognitive flow of a fresh session: understand the problem, absorb context, learn what was already tried, then see the plan and verification steps.
4. **Engine Interface** — stdin/stdout/stderr contracts for `classify`, `plan`, `preflight`, and `execute` subcommands. JSON input/output schemas. Exit codes: 0 (success), 1 (engine error), 2 (validation failure).
5. **Autonomy Model** — mode definitions, `ticket.local.md` parsing, `request_origin` derivation, audit trail format. See Trust Model section above.
6. **Dedup Policy** — `normalize()` algorithm with test vectors, fingerprint construction, 24-hour window, `force` override protocol. See Dedup section above.
7. **Status Transitions** — allowed transitions with preconditions:
   - `open` → `in_progress` (no preconditions)
   - `open` → `blocked` (requires `blocked_by` non-empty)
   - `in_progress` → `blocked` (requires `blocked_by` non-empty)
   - `in_progress` → `done` (requires acceptance criteria present)
   - `blocked` → `open` (all `blocked_by` resolved)
   - `*` → `wontfix` (no preconditions)
   - `done`/`wontfix` → archive (move to `closed/` directory)
   - Legacy status `deferred` maps to `open` on read (no write-back unless ticket is updated).
8. **Migration** — see Migration section below.
9. **Integration** — external consumers read `docs/tickets/*.md` as plain markdown with fenced YAML blocks. No API or import mechanism. Handoff's `/save` can reference ticket IDs in its output. Format uses fenced YAML (`` ```yaml ```) not YAML frontmatter (`---`), consistent with existing tickets and `ticket_parsing.py`.
10. **Versioning** — `contract_version` in `ticket-meta` footer. Current: `"1.0"`. Compatibility: engine reads all versions; writes latest only.

All three components (ticket-ops, ticket-triage, ticket-autocreate) reference this contract. Changes to the contract are the mechanism for evolving the system.

## Relationship to Handoff Plugin

**Clean break with format-as-contract:**
- Ticket plugin owns all ticket infrastructure (creation, management, triage)
- Handoff plugin removes `/defer` skill and `defer.py` script
- Handoff plugin removes `/triage` skill (migrated to ticket plugin)
- Handoff's `/save` can reference the ticket-autocreate agent for unfinished work
- Handoff reads ticket files (plain markdown in `docs/tickets/`) for any remaining integration

**Migration path:**
- New tickets always use v1.0 format
- Legacy IDs are preserved permanently — never converted to `T-YYYYMMDD-NN`
- Engine reads all 3 legacy generations (read-only, no write-back on read)
- Updating a legacy ticket converts it to v1.0 format (with user confirmation + diff preview)

**Legacy format read support:**

| Generation | ID Pattern | Key Field Differences | Read Strategy |
|-----------|------------|----------------------|---------------|
| Gen 1 (hand-authored) | Slug (`handoff-chain-viz`) | `plugin`, `related` (flat list), no `source`/`tags`/`effort` | Map `related` → informational only (not directional `blocks`/`blocked_by`). Ignore `plugin`. Missing fields default to empty. |
| Gen 2 (letter IDs) | `T-[A-F]` | `branch`, `effort: "S (1-2 sessions)"` (free text), sections: Summary/Rationale/Design/Risks | Parse `effort` as free text (no validation). Map Summary → Problem. Other sections preserved as-is. |
| Gen 3 (numeric IDs) | `T-NNN` | `branch`, sections: Summary/Prerequisites/Findings/Verification/References | Map Summary → Problem, Findings → Prior Investigation. Other sections preserved as-is. |

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
- Whether `triage.py`'s dual-status model (`raw_status` + `canonical_status`) should be adopted
- `ticket-autocreate` foreground-only constraint has no enforcement mechanism (agents lack native foreground/background distinction)
- YAML frontmatter vs fenced yaml blocks — resolved in favor of fenced blocks (consistent with existing tickets)
