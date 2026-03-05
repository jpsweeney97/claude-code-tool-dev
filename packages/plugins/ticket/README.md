# Ticket Plugin

> **v1.0.0** · MIT · Python ≥3.11 · Requires: `pyyaml>=6.0`

An issue tracker that lives inside your codebase, managed entirely by Claude Code. Instead of using an external tool like Jira or GitHub Issues, tickets are stored as markdown files in your repository at `docs/tickets/`. Claude creates, updates, closes, and triages these tickets through a structured engine — and critically, the plugin controls *how much autonomy* Claude has to do this on its own versus requiring human approval.

## What Problem Does This Solve?

During AI-assisted development sessions, work items surface constantly: bugs found while implementing features, deferred decisions, things to investigate later. Without structure, these get lost — buried in conversation history or scattered across sticky notes. The ticket plugin gives Claude a structured, auditable way to capture and manage these work items *within the codebase itself*, so they travel with the code and are visible to both humans and AI.

## Quick Start

Install via the Claude Code plugin marketplace:

```bash
claude plugin install ticket@turbo-mode
```

By default, Claude can only manage tickets when *you* ask it to (`suggest` mode). To let Claude create tickets autonomously, add a config file at `.claude/ticket.local.md`:

```yaml
---
autonomy_mode: auto_audit
max_creates_per_session: 5
---
```

| Field | Default | Options |
|-------|---------|---------|
| `autonomy_mode` | `suggest` | `suggest` (human-only), `auto_audit` (agent + audit trail) |
| `max_creates_per_session` | `5` | Agent create cap per session (0 = disable) |

## How It Works

### Directory Layout

```
docs/tickets/
├── 2026-03-04-fix-auth-bug.md      # Active tickets
├── closed-tickets/                  # Archived (done/wontfix)
└── .audit/
    └── 2026-03-04/
        └── <session_id>.jsonl       # Per-session mutation log
```

File naming: `YYYY-MM-DD-<slug>.md` where slug is the first 6 words of the title in kebab-case (`[a-z0-9-]`, max 60 chars). Collisions get a `-2` suffix.

### The Ticket Format

Each ticket is a markdown file with a fenced YAML block (not frontmatter):

~~~~markdown
# Fix auth token refresh race condition

```yaml
id: T-20260304-01
date: 2026-03-04
status: open
priority: high
source: {type: session, ref: "", session: abc-123}
contract_version: "1.0"
effort: S
tags: [auth, race-condition]
blocked_by: []
blocks: [T-20260304-02]
```

## Problem
Token refresh requests can overlap, causing 401 cascades...

## Approach
Add a mutex around the refresh call...

## Acceptance Criteria
- [ ] No duplicate refresh requests under concurrent load

## Verification
`uv run pytest tests/test_auth.py -k refresh`

## Key Files
| File | Role | Look For |
|------|------|----------|
| src/auth.py | Token refresh logic | `refresh_token()` |
~~~~

#### Required YAML Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `T-YYYYMMDD-NN` (date + 2-digit daily sequence) |
| `date` | string | Creation date (`YYYY-MM-DD`) |
| `status` | string | `open`, `in_progress`, `blocked`, `done`, `wontfix` |
| `priority` | string | `critical`, `high`, `medium`, `low` |
| `source` | object | `{type, ref, session}` — origin metadata |
| `contract_version` | string | `"1.0"` |

#### Optional YAML Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `effort` | string | `""` | Estimate: XS, S, M, L, XL |
| `tags` | list | `[]` | Categorization tags |
| `blocked_by` | list | `[]` | IDs of blocking tickets |
| `blocks` | list | `[]` | IDs this ticket blocks |
| `defer` | object | `null` | `{active, reason, deferred_at}` |

#### Section Guidance (v1.0 Runtime)

Section ordering is canonicalized as:
Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related

Runtime note: v1.0 does not hard-fail create/update when sections are missing. These sections are strongly recommended and enforced by process/tests rather than strict runtime schema rejection.
Runtime note: v1.0 `update` only mutates YAML frontmatter. Section-backed fields such as Problem and Approach are not writable through the `update` action.

### Status Transitions

| From | To | Preconditions |
|------|----|---------------|
| open | in_progress | — |
| open | blocked | `blocked_by` non-empty |
| in_progress | open | — |
| in_progress | blocked | `blocked_by` non-empty |
| in_progress | done | Acceptance criteria present |
| blocked | open | All `blocked_by` resolved |
| blocked | in_progress | All `blocked_by` resolved |
| * | wontfix | — |
| done | open | `reopen_reason` required, user-only |
| wontfix | open | `reopen_reason` required, user-only |

Terminal states (`done`, `wontfix`) allow non-status field edits without reopening.
Missing blocker references are invalid and are not treated as resolved.

### The Engine Pipeline

Every ticket mutation flows through a 4-stage pipeline:

1. **Classify** — Validates the requested action (create/update/close/reopen) and determines intent with a confidence score.
2. **Plan** — For creates: validates required fields (title, problem, priority) and checks for duplicates within a 24-hour window using content fingerprinting (SHA-256 of normalized problem text + key file paths). For other actions: pass-through.
3. **Preflight** — The enforcement checkpoint. Checks (in order): caller identity, action validity, autonomy policy, confidence threshold, intent consistency, dedup enforcement, ticket existence, dependency integrity (resolution-aware for close), and TOCTOU (time-of-check-time-of-use) fingerprint to catch concurrent modifications.
4. **Execute** — Performs the mutation (writes the file). Has defense-in-depth: independently re-checks dedup, optional stale fingerprint checks, and for agent-origin requests re-reads live autonomy policy from `.claude/ticket.local.md` before allowing the write. If policy changed since preflight, execute blocks and requires a rerun. Execute is intentionally more lenient than plan for optional fields (e.g., `priority` defaults to `"medium"` if absent) — the goal is to always produce a valid ticket rather than fail at the last stage.

### Two Entrypoints, One Engine

The engine has two entrypoints that are identical in structure but differ in one critical field — `request_origin`:

- **`ticket_engine_user.py`** — Called when a human initiates a ticket operation. Sets `request_origin="user"`. Users are trusted and face fewer restrictions.
- **`ticket_engine_agent.py`** — Called when Claude (or a sub-agent) initiates a ticket operation autonomously. Sets `request_origin="agent"`. Agents face strict policy enforcement.

Both entrypoints call the same core engine functions. The origin field determines which policy rules apply.

### The Hook Guard (Security Layer)

A PreToolUse hook (`ticket_engine_guard.py`) intercepts every Bash command Claude runs. When it detects a ticket engine invocation, it:

1. Validates the command matches an exact allowlist pattern (blocks shell injection via metacharacters like `|`, `;`, `` ` ``)
2. Validates payload path containment: payload files must resolve inside the current workspace root (`event.cwd`)
3. Injects trust fields into the payload file (`session_id`, `hook_injected=true`, `hook_request_origin`) using atomic file writes (temp file -> fsync -> rename)
4. Returns allow/deny to Claude Code's permission system

This prevents Claude from forging trust fields or bypassing the entrypoint separation. If an agent tries to call the user entrypoint, the hook injects `hook_request_origin="agent"`, and the entrypoint detects the mismatch and rejects the request.

**Assumption:** The hook matches commands containing `ticket_engine` in the command string. If an entrypoint is renamed, wrapped, or invoked via a path that drops this substring, the hook silently passes through (no payload injection, no origin enforcement). This is proportionate for the accidental-autonomy threat model — it is not designed to resist adversarial circumvention.

### Autonomy Enforcement

The owner configures how much autonomy Claude gets in `.claude/ticket.local.md`:

| Mode | Behavior |
|------|----------|
| `suggest` (default) | Agents are **blocked** from all mutations. Only humans can create/update/close tickets. |
| `auto_audit` | Agents **can** mutate tickets, subject to a per-session create cap (default 5). Every mutation is logged to a JSONL audit trail. |
| `auto_silent` | Reserved for v1.1 — currently blocked. |

The session create cap prevents runaway agents from flooding the ticket directory. The audit trail at `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl` records every mutation with timestamps for traceability.

Key security properties:

- **Fail-closed audit**: If the audit trail can't be written (disk full, permissions), agent mutations are blocked. User mutations proceed (advisory only).
- **Path traversal protection**: Session IDs from untrusted payloads are sanitized (stripping `/`, `\`, `\0`) before being used in filesystem paths.
- **Workspace boundary enforcement**: hook payload paths and entrypoint `tickets_dir` must resolve inside project/workspace root.
- **Live policy reread for agent execute**: `AutonomyConfig` is still a frozen, self-healing type, but agent `execute` treats the on-disk config as authoritative and blocks if it diverges from the preflight snapshot.

## Module Reference

| Module | Purpose |
|--------|---------|
| `ticket_engine_core.py` | 4-stage pipeline (classify/plan/preflight/execute), `AutonomyConfig`, audit trail |
| `ticket_engine_user.py` | User entrypoint — hardcodes `request_origin="user"` |
| `ticket_engine_agent.py` | Agent entrypoint — hardcodes `request_origin="agent"` |
| `ticket_engine_guard.py` | PreToolUse hook — command allowlist + payload injection |
| `ticket_parse.py` | Parses markdown files with fenced YAML. Supports 4 legacy ticket formats with automatic field defaults and section renames. |
| `ticket_read.py` | Read-only queries: list tickets, find by ID, filter by status/priority/tag, fuzzy match. |
| `ticket_render.py` | Template-based rendering: generates markdown file content with proper YAML and section ordering. |
| `ticket_id.py` | ID allocation: scans existing tickets for the next available `T-YYYYMMDD-NN` sequence number. |
| `ticket_dedup.py` | Content fingerprinting: 5-step text normalization + SHA-256 hashing for duplicate detection. |
| `ticket_triage.py` | Read-only health analysis: dashboard, stale ticket detection, blocked dependency chains, audit reporting, orphan detection. |

### CLI Interface

Both entrypoints use the same subcommand pattern:

```bash
python3 scripts/ticket_engine_user.py <subcommand> <payload.json>
python3 scripts/ticket_engine_agent.py <subcommand> <payload.json>
```

Subcommands: `classify`, `plan`, `preflight`, `execute`. Each reads a JSON payload file and writes a JSON response envelope to stdout:

```json
{"state": "ok_create", "ticket_id": "T-20260304-01", "message": "...", "data": {...}}
```

Exit codes: `0` (success), `1` (engine error), `2` (validation failure).

Path constraints:
- Hook payload path must resolve under the current workspace root (`event.cwd`) or the command is denied.
- `tickets_dir` must resolve under the entrypoint process root (`Path.cwd()`). The default remains `docs/tickets`.

## Skills

| Skill | Trigger Phrases | Allowed Tools |
|-------|----------------|---------------|
| `/ticket` | "create a ticket", "update ticket T-...", "close/reopen ticket", "list tickets", "track this bug/feature/task" — or any request to persistently capture a work item, even without the word "ticket" | Bash, Write, Read |
| `/ticket-triage` | "triage tickets", "ticket dashboard", "any stale tickets", "what should I work on next", "catch me up on the project" — or any health check or project orientation request | Bash, Read |

## Hooks

| Event | Matcher | Script | Timeout | Behavior |
|-------|---------|--------|---------|----------|
| `PreToolUse` | `Bash` | `hooks/ticket_engine_guard.py` | 10s | Command allowlist + trust-field injection; denies shell metacharacters and payload paths outside workspace root |

See [The Hook Guard](#the-hook-guard-security-layer) for full architectural detail.

## Reference Files

| File | Authority |
|------|-----------|
| `references/ticket-contract.md` | Single source of truth for ticket schema, engine interface, autonomy model, dedup policy, status transitions, and migration rules. All engine components reference this. |

## Tests

363 tests across 15 test files:

| Test File | Coverage Area |
|-----------|--------------|
| `test_engine.py` | Core pipeline stages |
| `test_autonomy.py` | Policy enforcement unit tests |
| `test_autonomy_integration.py` | End-to-end autonomy scenarios |
| `test_audit.py` | Audit trail writes, fail-closed behavior |
| `test_hook.py` | Guard allowlist, payload injection |
| `test_hook_integration.py` | End-to-end hook scenarios |
| `test_triage.py` | Dashboard, stale detection, orphans |
| `test_entrypoints.py` | User/agent entrypoint routing |
| `test_id.py` | ID allocation, sequence gaps |
| `test_parse.py` | YAML parsing, legacy format support |
| `test_read.py` | Queries, filtering, fuzzy match |
| `test_render.py` | Template rendering, section ordering |
| `test_dedup.py` | Fingerprinting, normalization |
| `test_integration.py` | Full create/update/close flows |
| `test_migration.py` | Legacy format conversion |

```bash
cd packages/plugins/ticket && uv run pytest
```

## What's Not Built Yet

The `agents/` directory is reserved but empty. Two production skills (`/ticket` and `/ticket-triage`) are deployed. What's missing:

- **Agent workflows** — autonomous sub-processes for tasks like auto-creating tickets from code review findings or session summaries. Planned for a future milestone.
