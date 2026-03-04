# Ticket Plugin

An issue tracker that lives inside your codebase, managed entirely by Claude Code. Instead of using an external tool like Jira or GitHub Issues, tickets are stored as markdown files in your repository at `docs/tickets/`. Claude creates, updates, closes, and triages these tickets through a structured engine — and critically, the plugin controls *how much autonomy* Claude has to do this on its own versus requiring human approval.

## What Problem Does This Solve?

During AI-assisted development sessions, work items surface constantly: bugs found while implementing features, deferred decisions, things to investigate later. Without structure, these get lost — buried in conversation history or scattered across sticky notes. The ticket plugin gives Claude a structured, auditable way to capture and manage these work items *within the codebase itself*, so they travel with the code and are visible to both humans and AI.

## How It Works

### The Ticket Format

Each ticket is a markdown file with embedded YAML metadata:

```
docs/tickets/2026-03-04-fix-auth-bug.md
```

The YAML block contains structured fields (ID, status, priority, tags, dependencies) and the markdown body contains sections: Problem, Approach, Acceptance Criteria, Key Files, etc. Tickets use IDs like `T-20260304-01` (date + daily sequence number). They follow a state machine: `open -> in_progress -> blocked -> done/wontfix`, with defined transitions and preconditions (e.g., you can't close a ticket without acceptance criteria, can't mark as blocked without specifying what blocks it).

### The Engine Pipeline

Every ticket mutation flows through a 4-stage pipeline:

1. **Classify** — Validates the requested action (create/update/close/reopen) and determines intent with a confidence score.
2. **Plan** — For creates: validates required fields (title, problem, priority) and checks for duplicates within a 24-hour window using content fingerprinting (SHA-256 of normalized problem text + key file paths). For other actions: pass-through.
3. **Preflight** — The enforcement checkpoint. Checks (in order): caller identity, action validity, autonomy policy, confidence threshold, intent consistency, dedup enforcement, ticket existence, dependency integrity, and TOCTOU (time-of-check-time-of-use) fingerprint to catch concurrent modifications.
4. **Execute** — Performs the mutation (writes the file). Has defense-in-depth: independently re-checks all autonomy policies even if preflight passed, because preflight could theoretically be bypassed.

### Two Entrypoints, One Engine

The engine has two entrypoints that are identical in structure but differ in one critical field — `request_origin`:

- **`ticket_engine_user.py`** — Called when a human initiates a ticket operation. Sets `request_origin="user"`. Users are trusted and face fewer restrictions.
- **`ticket_engine_agent.py`** — Called when Claude (or a sub-agent) initiates a ticket operation autonomously. Sets `request_origin="agent"`. Agents face strict policy enforcement.

Both entrypoints call the same core engine functions. The origin field determines which policy rules apply.

### The Hook Guard (Security Layer)

A PreToolUse hook (`ticket_engine_guard.py`) intercepts every Bash command Claude runs. When it detects a ticket engine invocation, it:

1. Validates the command matches an exact allowlist pattern (blocks shell injection via metacharacters like `|`, `;`, `` ` ``)
2. Injects trust fields into the payload file (`session_id`, `hook_injected=true`, `hook_request_origin`) using atomic file writes (temp file -> fsync -> rename)
3. Returns allow/deny to Claude Code's permission system

This prevents Claude from forging trust fields or bypassing the entrypoint separation. If an agent tries to call the user entrypoint, the hook injects `hook_request_origin="agent"`, and the entrypoint detects the mismatch and rejects the request.

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
- **Immutable config snapshots**: The `AutonomyConfig` type is a frozen dataclass that self-heals invalid values to safe defaults. Once constructed, it can't be mutated between preflight and execute.

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

## Contract

`references/ticket-contract.md` is the single source of truth for the ticket schema, engine interface, autonomy model, dedup policy, status transitions, and migration rules. All components reference this contract.

## Tests

287 tests across 15 test files. Run from the package directory:

```bash
cd packages/plugins/ticket && uv run pytest
```

## What's Not Built Yet

The `skills/` and `agents/` directories are empty. The engine is fully functional as a Python library with CLI entrypoints, but it doesn't yet have:

- A **skill** — instructions telling Claude *when and how* to invoke the engine in natural conversation
- An **agent** — an autonomous sub-process for tasks like auto-creating tickets from code review findings

These are the next milestone (M9), connecting the engine to Claude Code's skill system so that "create a ticket for this bug" gets routed through the pipeline automatically.
