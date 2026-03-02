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
| `ticket_engine.py` | Script | Called by skills/agent | Canonical decision engine: `classify\|plan\|execute` subcommands |

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
│   ├── ticket_engine.py             # Canonical decision engine (classify|plan|execute)
│   ├── ticket_id.py                 # ID allocation (deterministic, collision-resistant)
│   ├── ticket_render.py             # Markdown rendering (template-based)
│   └── ticket_parse.py             # YAML frontmatter parsing (multi-format)
├── references/
│   └── ticket-contract.md           # Single source of truth: schemas, policies, fields
└── tests/
    ├── test_engine.py
    ├── test_id.py
    ├── test_render.py
    └── test_parse.py
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
| `update` | Update existing ticket | classify → execute |
| `close` | Close/resolve ticket | classify → execute |
| `query` | Search tickets by criteria | Direct file read + filter |
| `list` | Dashboard summary | Direct file read + summarize |
| (empty) | Dashboard | Same as `list` |

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
| `policy_blocked` | Show rendered preview, ask user to confirm creation |
| `escalate` | Explain why engine couldn't handle, suggest manual action |

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

### Three-Stage Pipeline

```
ticket_engine.py classify <json>   → intent + confidence
ticket_engine.py plan <json>       → action plan + validation
ticket_engine.py execute <json>    → result + machine state
```

All decision logic lives here. Skills and agent call the engine and map its machine states to appropriate UX.

### Dedup (hard gate in execute)

- Fingerprint: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`
- Window: scan tickets created within 24 hours
- Match: exact fingerprint → `duplicate_candidate` hard block
- Override: `force: true` in execute input (user explicitly confirmed)

### Autonomy Enforcement (in execute)

```
if action == "create" and source == "auto":
    mode = read_autonomy_mode()
    if mode == "suggest":     → return policy_blocked with preview
    if mode == "auto_audit":  → create ticket, log audit, return ok_create
    if mode == "auto_silent": → create ticket, log audit, return ok_create
```

Default: `suggest` (fail-closed). Configuration: `.claude/ticket.local.md`.

## Ticket Contract

The full contract lives in `references/ticket-contract.md` within the plugin. It is the single source of truth for:

1. **Storage** — file locations, naming conventions, directory bootstrap
2. **ID Allocation** — deterministic algorithm, collision prevention, format invariants
3. **Schema** — YAML fields (required/optional), validation rules, section ordering
4. **Engine Interface** — stdin/stdout/stderr contracts for all three subcommands
5. **Autonomy Model** — mode definitions, configuration, override rules, audit trail
6. **Dedup Policy** — fingerprint algorithm, window, resolution rules
7. **Status Transitions** — allowed transitions with preconditions, archive-on-close
8. **Migration** — old format read support, conversion rules, status mapping
9. **Integration** — how external consumers (handoff /triage) read ticket files
10. **Versioning** — contract version in ticket-meta footer, compatibility checks

All three components (ticket-ops, ticket-triage, ticket-autocreate) reference this contract. Changes to the contract are the mechanism for evolving the system.

## Relationship to Handoff Plugin

**Clean break with format-as-contract:**
- Ticket plugin owns all ticket infrastructure (creation, management, triage)
- Handoff plugin removes `/defer` skill and `defer.py` script
- Handoff plugin removes `/triage` skill (migrated to ticket plugin)
- Handoff's `/save` can reference the ticket-autocreate agent for unfinished work
- Handoff reads ticket files (plain markdown in `docs/tickets/`) for any remaining integration

**Migration path:**
- Existing tickets in `docs/tickets/` keep their format (engine reads legacy formats)
- New tickets always use v1.0 format
- Updating a legacy ticket converts it (with user confirmation)

## Codex Dialogue Provenance

Architecture E emerged from a 12-turn collaborative Codex dialogue (thread `019cad28-6567-7f12-9bbd-1f9a96d46b33`). Key convergence points:

- **T2:** Codex conceded description-based skill selection can't disambiguate 5 similar operations → invocation contract pattern
- **T4:** Engine-centric adapter pattern emerged — both sides agreed business logic belongs in code, not markdown
- **T5:** Reduced from 5 skills to 2 — first-token routing in ticket-ops handles create/update/close/query without separate skills
- **T6:** Three-tier autonomy model with fail-closed default
- **T7:** Dedup as mandatory hard gate via deterministic fingerprinting

All 7 key outcomes RESOLVED with high confidence. 3 items EMERGED (Architecture E itself, invocation contract pattern, `skills:` injection limitation).
