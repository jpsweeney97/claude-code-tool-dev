# Ticket Plugin

> **Plugin v1.2.0** · Ticket contract v1.0 · MIT · Python ≥3.11 · Requires: `pyyaml>=6.0`

This README tracks the installed Claude Code plugin release. Ticket files written by the engine still use `contract_version: "1.0"`, so version references below call out the contract/runtime version only where that distinction matters.

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

#### Section Guidance (Contract v1.0 Runtime)

Section ordering is canonicalized as:
Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History

`Reopen History` is only present after a terminal ticket has been reopened.

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

Both entrypoints call the same core engine functions. The split is a routing convenience and explicit entrypoint choice, not the trust boundary by itself.

### The Hook Guard (Security Layer)

A PreToolUse hook (`ticket_engine_guard.py`) intercepts every Bash command Claude runs. When it detects a ticket engine invocation, it:

1. Validates the command matches an exact allowlist pattern (blocks shell injection via metacharacters like `|`, `;`, `` ` ``)
2. Validates payload path containment: payload files must resolve inside the current workspace root (`event.cwd`)
3. Injects trust fields into the payload file (`session_id`, `hook_injected=true`, `hook_request_origin`) using atomic file writes (temp file -> fsync -> rename)
4. Returns allow/deny to Claude Code's permission system

Trust origin comes from hook metadata, not from whichever entrypoint path appears in the Bash command. If `agent_id` is present in the `PreToolUse` event, the hook injects `hook_request_origin="agent"`; otherwise it injects `"user"`. The entrypoints still reject mismatches, so using the wrong entrypoint now fails explicitly.

**Assumption:** The hook matches commands containing `ticket_engine` in the command string. If an entrypoint is renamed, wrapped, or invoked via a path that drops this substring, the hook silently passes through (no payload injection, no origin enforcement). This is proportionate for the accidental-autonomy threat model — it is not designed to resist adversarial circumvention.

### Autonomy Enforcement

The owner configures how much autonomy Claude gets in `.claude/ticket.local.md`:

| Mode | Behavior |
|------|----------|
| `suggest` (default) | Agents are **blocked** from all mutations. Only humans can create/update/close tickets. |
| `auto_audit` | Agents **can** mutate tickets, subject to a per-session create cap (default 5). Every mutation is logged to a JSONL audit trail. |
| `auto_silent` | Reserved for a future release — currently blocked. |

The session create cap prevents runaway agents from flooding the ticket directory. The audit trail at `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl` records every mutation with timestamps for traceability.

Key security properties:

- **Fail-closed audit**: If the audit trail can't be written (disk full, permissions), agent mutations are blocked. User mutations proceed (advisory only).
- **Path traversal protection**: Session IDs from untrusted payloads are sanitized (stripping `/`, `\`, `\0`) before being used in filesystem paths.
- **Workspace boundary enforcement**: hook payload paths and all ticket CLI `tickets_dir` arguments must resolve inside project/workspace root.
- **Live policy reread for agent execute**: `AutonomyConfig` is still a frozen, self-healing type, but agent `execute` treats the on-disk config as authoritative and blocks if it diverges from the preflight snapshot.

Known limitation (current implementation): create now uses exclusive file creation with bounded retry to prevent same-path silent overwrite, but concurrent autonomous creates are still not fully serialized. Session create cap enforcement and ID allocation are not lock-based, so parallel subagent execution can still overrun caps or allocate colliding IDs.

## Module Reference

| Module | Purpose |
|--------|---------|
| `ticket_engine_core.py` | 4-stage pipeline (classify/plan/preflight/execute), `AutonomyConfig`, audit trail |
| `ticket_engine_user.py` | User entrypoint — hardcodes `request_origin="user"` |
| `ticket_engine_agent.py` | Agent entrypoint — hardcodes `request_origin="agent"` |
| `ticket_engine_guard.py` | PreToolUse hook — command allowlist + payload injection |
| `ticket_parse.py` | Parses markdown files with fenced YAML and H1 titles. Supports 4 legacy ticket formats with automatic field defaults and section renames. |
| `ticket_read.py` | Read-only queries: list tickets, find by ID, filter by status/priority/tag, fuzzy match, and return structured titles. |
| `ticket_render.py` | Template-based rendering: generates markdown file content with proper YAML and section ordering. |
| `ticket_audit.py` | Standalone audit maintenance utility: scans `docs/tickets/.audit/` JSONL files, reports corruption, and repairs them with backups when requested. |
| `ticket_id.py` | ID allocation: scans existing tickets for the next available `T-YYYYMMDD-NN` sequence number. |
| `ticket_dedup.py` | Content fingerprinting: 5-step text normalization + SHA-256 hashing for duplicate detection. |
| `ticket_triage.py` | Read-only health analysis: dashboard, stale ticket detection, blocked dependency chains, audit reporting, orphan detection. |
| `ticket_paths.py` | Shared path validation helpers: resolves `tickets_dir` and rejects paths that escape the workspace root. |

### CLI Interface

The package exposes five script entrypoint families:

| Script | Subcommands | Use Case |
|--------|-------------|----------|
| `ticket_engine_user.py` | `classify`, `plan`, `preflight`, `execute` | Mutating 4-stage pipeline for user-initiated operations |
| `ticket_engine_agent.py` | `classify`, `plan`, `preflight`, `execute` | Same pipeline, but with agent-origin autonomy enforcement |
| `ticket_read.py` | `list`, `query` | Read-only ticket lookup and metadata filtering |
| `ticket_triage.py` | `dashboard`, `audit` | Read-only health summaries and recent audit aggregation |
| `ticket_audit.py` | `repair` | Audit-log repair with optional dry-run mode |

#### Engine entrypoints

Both mutation entrypoints use the same subcommand pattern:

```bash
python3 scripts/ticket_engine_user.py <subcommand> <payload.json>
python3 scripts/ticket_engine_agent.py <subcommand> <payload.json>
```

Subcommands: `classify`, `plan`, `preflight`, `execute`. Each reads a JSON payload file and writes a JSON response envelope to stdout:

```json
{"state": "ok_create", "ticket_id": "T-20260304-01", "message": "...", "data": {...}}
```

Exit codes: `0` (success), `1` (engine error), `2` (validation failure).

#### Read-only utilities

`ticket_read.py` exposes the operator-facing query surface:

```bash
python3 scripts/ticket_read.py list <tickets_dir> [--status <status>] [--priority <priority>] [--tag <tag>] [--include-closed]
python3 scripts/ticket_read.py query <tickets_dir> <id_prefix>
```

- `list` returns parsed ticket metadata and supports status, priority, tag, and archived-ticket filtering.
- `query` performs ID-prefix lookup and returns structured ticket summaries.

`ticket_triage.py` exposes read-only health checks:

```bash
python3 scripts/ticket_triage.py dashboard <tickets_dir>
python3 scripts/ticket_triage.py audit <tickets_dir> [--days <n>]
```

- `dashboard` reports open/in-progress/blocked counts, stale tickets, blocked chains, and document-size warnings.
- `audit` summarizes recent JSONL audit activity, grouped by action and result, over a configurable day window.

Both scripts emit JSON to stdout. On successful runs they exit `0`; path/runtime errors exit `1`; CLI argument errors come from `argparse` and exit `2`.

#### Audit remediation

Audit repair stays outside the mutation pipeline:

```bash
python3 scripts/ticket_audit.py repair <tickets_dir> [--dry-run]
```

Use `--dry-run` to report corrupt audit files without writing. Repair mode creates `*.jsonl.bak-<YYYYMMDDTHHMMSSZ>` backups and rewrites the original JSONL file with only valid JSON-object lines.
`ticket_audit.py` exits `0` on success and `1` on invalid arguments or repair failures.

Path constraints:
- Hook payload path must resolve under the current workspace root (`event.cwd`) or the command is denied.
- `tickets_dir` must resolve under the calling process root (`Path.cwd()`) for entrypoint, read, triage, and audit scripts. The default remains `docs/tickets`.

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

## Environment Variables

| Variable | Default / Source | Purpose |
|----------|------------------|---------|
| `CLAUDE_PLUGIN_ROOT` | No explicit default in `hooks/hooks.json`; inside `ticket_engine_guard.py`, the guard falls back to its own parent directory when resolving its internal root | Used to register the hook command path and to anchor the guard's engine/read allowlist patterns |

## Reference Files

| File | Authority |
|------|-----------|
| `references/ticket-contract.md` | Single source of truth for ticket schema, engine interface, autonomy model, dedup policy, status transitions, and migration rules. All engine components reference this. |
| `skills/ticket/references/pipeline-guide.md` | Skill implementation reference: payload schemas, pipeline state propagation, response states, and loop procedures for the `/ticket` skill. |

## Tests

Plugin test coverage includes:

Current suite: 596 tests across 25 files (`cd packages/plugins/ticket && uv run pytest --co -q`).

| Test File | Coverage Area |
|-----------|--------------|
| `test_classify.py` | Classify stage: action intent resolution |
| `test_plan.py` | Plan stage: field validation, dedup fingerprinting |
| `test_preflight.py` | Preflight stage: policy enforcement, transition validation |
| `test_execute.py` | Execute stage: dispatch, create, update, close, reopen, trust |
| `test_autonomy.py` | Policy enforcement unit tests |
| `test_autonomy_integration.py` | End-to-end autonomy scenarios |
| `test_audit.py` | Audit trail writes, fail-closed behavior |
| `test_hook.py` | Guard allowlist, payload injection |
| `test_hook_integration.py` | End-to-end hook scenarios |
| `test_triage.py` | Dashboard, stale detection, orphans |
| `test_entrypoints.py` | User/agent entrypoint routing |
| `test_runner.py` | Engine runner: CLI arg parsing, JSON I/O boundary |
| `test_id.py` | ID allocation, sequence gaps |
| `test_parse.py` | YAML parsing, legacy format support |
| `test_read.py` | Queries, filtering, fuzzy match |
| `test_render.py` | Template rendering, section ordering |
| `test_dedup.py` | Fingerprinting, normalization |
| `test_trust.py` | Trust validation helpers (hook_injected, request_origin, session_id) |
| `test_validate.py` | Ticket field schema validation |
| `test_stage_models.py` | Stage boundary input model dataclasses |
| `test_response_models.py` | EngineResponse output envelope invariants |
| `test_paths.py` | Project-root resolution, tickets_dir path containment |
| `test_integration.py` | Full create/update/close flows |
| `test_migration.py` | Legacy format conversion |
| `test_review_findings.py` | Regression tests for 2026-03-08 architectural review findings |

```bash
cd packages/plugins/ticket && uv run pytest
```

## What's Not Built Yet

The `agents/` directory is reserved but empty. Two production skills (`/ticket` and `/ticket-triage`) are deployed. What's missing:

- **Agent workflows** — autonomous sub-processes for tasks like auto-creating tickets from code review findings or session summaries. Planned for a future milestone.
