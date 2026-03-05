---
name: ticket
description: "Manage codebase tickets: create, update, close, reopen, list, and query. Use when the user says \"create a ticket\", \"update ticket T-...\", \"close ticket\", \"reopen ticket\", \"list tickets\", \"show open tickets\", \"find ticket about...\", or asks to track a bug, feature, or task as a ticket."
disable-model-invocation: true
argument-hint: "[create|update|close|reopen|list|query] [ticket-id or details]"
allowed-tools:
  - Bash
  - Write
  - Read
---

# /ticket

Manages codebase tickets via the 4-stage engine pipeline (classify → plan → preflight → execute) for mutations, and `ticket_read.py` directly for reads.

**Reference:** See [references/pipeline-guide.md](references/pipeline-guide.md) for payload schemas, pipeline state propagation, and all 15 machine states.

---

## Setup (run once per skill invocation)

Resolve the plugin root and locate the tickets directory before any Bash commands. These two values are used throughout.

**Step 1 — Resolve plugin root:**
```bash
echo $CLAUDE_PLUGIN_ROOT
```
Store the output as `PLUGIN_ROOT`. Use this absolute path (not the env var) in all subsequent commands. Reason: `$CLAUDE_PLUGIN_ROOT` contains `$` which is blocked by the guard hook's metachar check.

If output is empty, stop and report: "CLAUDE_PLUGIN_ROOT is not set — the ticket plugin may not be installed. Check `claude plugin list`."

**Step 2 — Resolve tickets directory:**
```bash
git rev-parse --show-toplevel
```
Append `/docs/tickets`. Store as `TICKETS_DIR`.

**Step 3 — Ensure payload directory exists (mutations only):**
```bash
mkdir -p .claude/ticket-tmp
```

---

## Routing

Dispatch on the first token of the text typed after `/ticket` (e.g., `/ticket create Fix auth bug` → operation is `create`) or the user's intent. If no operation is clear, ask: "What would you like to do? (create / update / close / reopen / list / query)"

| Operation | Trigger phrases | Execution path |
|-----------|----------------|----------------|
| `create` | "create a ticket", "track this bug/feature" | Engine pipeline |
| `update` | "update ticket T-...", "change priority/status of T-..." | Engine pipeline |
| `close` | "close ticket T-...", "mark T-... done" | Engine pipeline |
| `reopen` | "reopen T-...", "T-... needs more work" | Engine pipeline |
| `list` | "list tickets", "show open tickets", "what's in-progress" | `ticket_read.py list` (direct) |
| `query` | "find ticket about...", "do we have a ticket for..." | `ticket_read.py query` (direct) |

---

## Read Operations

Read operations call `ticket_read.py` directly — no engine pipeline, no payload file.

**List:**
```bash
python3 <PLUGIN_ROOT>/scripts/ticket_read.py list <TICKETS_DIR> [--status open|blocked|in_progress] [--priority high|critical] [--tag <tag>]
```

**Query (fuzzy ID or text search):**
```bash
python3 <PLUGIN_ROOT>/scripts/ticket_read.py query <TICKETS_DIR> <search_term>
```

Both return `{"state": "ok", "data": {"tickets": [...]}}` where each ticket has: `id`, `date`, `status`, `priority`, `tags`, `blocked_by`, `blocks`, `path`. Present as a table with ID, status, priority, and tags (if non-empty).

---

## Mutation Operations

All mutations (create, update, close, reopen) follow this flow:

### Step 1: Extract fields from context

From the conversation history, extract:
- **create**: title (required), problem statement, priority (default: medium), key files, tags
- **update**: ticket ID (required), fields to change (status, priority, problem, approach, tags)
- **close**: ticket ID (required), resolution (optional)
- **reopen**: ticket ID (required), reopen reason (required by engine)

### Step 2: Confirmation gate

**For update/close/reopen:** First read the existing ticket file to show current state:
```bash
python3 <PLUGIN_ROOT>/scripts/ticket_read.py query <TICKETS_DIR> <ticket-id>
```

Present the proposed operation before writing any files:

```
I'll create a ticket with:
  Title: <title>
  Priority: <priority>
  Problem: <extracted problem statement>
  Key files: <extracted files if any>

Continue? [y / edit / n]
```

For update/close/reopen: show current ticket state (from the read above) alongside proposed changes.

- `y` → proceed to pipeline
- `edit` → ask which fields to change, update, re-confirm
- `n` → stop

**NEVER call execute without user confirmation.**

### Step 3: Write initial payload

Write to `.claude/ticket-tmp/payload.json` using the Write tool. See [references/pipeline-guide.md](references/pipeline-guide.md) for per-operation field schemas.

The payload file is the pipeline's running state — each stage enriches it. Construct the initial payload with all known fields; the engine fills in the rest.

### Step 4: Run the 4-stage pipeline

Run each command and inspect the response before proceeding to the next stage.

```bash
python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py classify .claude/ticket-tmp/payload.json
python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py plan .claude/ticket-tmp/payload.json
python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py preflight .claude/ticket-tmp/payload.json
python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py execute .claude/ticket-tmp/payload.json
```

After each stage, check the `state` field. States handled by the Step 5 table (need_fields, duplicate_candidate, etc.) require action — do not call the next stage until resolved. Stop immediately on any `state` not listed in the Step 5 table.

### Step 5: Handle the response state

Read `state` from the JSON response (`{"state": ..., "data": {...}}`):

| State | Action |
|-------|--------|
| `ok` | Report success and stop (generic — rare in pipeline context) |
| `ok_create` | Report success: "Created ticket T-YYYYMMDD-NN at docs/tickets/<slug>.md" |
| `ok_update` | Report: "Updated ticket T-..." with list of changed fields |
| `ok_close` / `ok_close_archived` | Report: "Closed ticket T-... (archived to closed-tickets/)" |
| `ok_reopen` | Report: "Reopened ticket T-... (status: open)" |
| `need_fields` | Ask user for missing fields (see [pipeline-guide](references/pipeline-guide.md#need_fields-loop)) |
| `duplicate_candidate` | Show duplicate match, ask for override (see [pipeline-guide](references/pipeline-guide.md#duplicate_candidate-loop)) |
| `preflight_failed` | Report failed checks from `data.checks_failed`, stop |
| `policy_blocked` | Report the policy message, stop |
| `invalid_transition` | Report current status and valid transitions, stop |
| `dependency_blocked` | Report blocking ticket IDs, stop |
| `not_found` | Report "Ticket T-... not found", stop |
| `escalate` | Report the escalation message, stop |

---

## Troubleshooting

**Exit code 1:** Engine error. Read stderr for details.

**Exit code 2:** Validation failure. Check payload structure against [pipeline-guide.md](references/pipeline-guide.md).

**"Shell metacharacters detected":** A `$` appeared in the Bash command. Ensure you are using the resolved `PLUGIN_ROOT` string (from Step 1 above), not the env var `$CLAUDE_PLUGIN_ROOT`.

**"Payload path outside workspace root":** The payload path must be inside the project root. Use `.claude/ticket-tmp/payload.json` (relative), not `/tmp/...`.

**Guard hook blocks command:** Verify the invocation uses `python3` (not `python3.11` or `/usr/bin/python3`) and the full absolute `PLUGIN_ROOT` path (not a relative path).
