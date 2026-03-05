# Pipeline Guide

Reference for `/ticket` skill. Covers payload schemas, pipeline state propagation, response states, and loop procedures.

---

## Pipeline State Propagation

**The engine CLI is stateless.** Each invocation reads the payload file, calls one engine function, prints the response JSON to stdout, and exits. It does NOT write stage outputs back to the payload file.

The skill must carry state between stages manually:

1. Run the stage command
2. Parse stdout as JSON — the response is `{state, ticket_id, message, data}`
3. Merge `response.data` fields into the current payload dict
4. Write the updated payload back to `.claude/ticket-tmp/payload.json` using the Write tool
5. Only then run the next stage

| Stage | Reads from payload | Fields to write into payload after this stage |
|-------|--------------------|-----------------------------------------------|
| `classify` | `action`, `args`, `session_id`, `request_origin` | `intent` = data.intent, **`classify_intent`** = data.intent, **`classify_confidence`** = data.confidence, `resolved_ticket_id` = data.resolved_ticket_id |
| `plan` | `intent`, `fields`, `session_id`, `request_origin` | `dedup_fingerprint`, `target_fingerprint`, `duplicate_of`, `missing_fields`, `action_plan` (all from data directly) |
| `preflight` | All classify+plan fields, `action`, `fields`, `dedup_override`, `dependency_override`, `hook_injected` | `autonomy_config` = data.autonomy_config (if present) |
| `execute` | `action`, `ticket_id`, `fields`, `session_id`, `request_origin`, `dedup_override`, `dependency_override` | (no merge — execute writes the ticket file to disk) |

**Critical:** `classify` returns `confidence` and `intent` in `response.data`, but `preflight` reads `classify_confidence` and `classify_intent` from the payload. These are different key names. When writing the payload after classify, you MUST set both `intent` (for plan) AND `classify_intent` + `classify_confidence` (for preflight). A simple `data` merge without renaming will leave `classify_confidence=0.0` and cause preflight to fail.

After `need_fields`, re-run from `plan` (not `classify`) — `intent`, `classify_intent`, and `classify_confidence` are already in the payload.

---

## Payload Schemas

### create

```json
{
  "action": "create",
  "args": "<natural-language description from user>",
  "session_id": "<hook-injected — leave empty string>",
  "request_origin": "user",
  "fields": {
    "title": "Fix auth token race condition",
    "problem": "Tokens expire mid-request under high load...",
    "priority": "high",
    "tags": ["auth", "race-condition"],
    "key_file_paths": ["src/auth/token.py", "src/middleware/session.py"],
    "key_files": [
      {"file": "src/auth/token.py", "role": "token refresh logic", "look_for": "expiry check"},
      {"file": "src/middleware/session.py", "role": "session middleware", "look_for": "concurrent access"}
    ],
    "effort": "M"
  }
}
```

### update

```json
{
  "action": "update",
  "args": "",
  "session_id": "",
  "request_origin": "user",
  "fields": {
    "ticket_id": "T-20260302-01",
    "priority": "critical",
    "status": "in_progress"
  }
}
```

Only include fields being changed. All fields are optional except `ticket_id`.

### close

```json
{
  "action": "close",
  "args": "",
  "session_id": "",
  "request_origin": "user",
  "fields": {
    "ticket_id": "T-20260302-01",
    "resolution": "wontfix"
  }
}
```

`resolution` is optional. Valid values: `wontfix`, `duplicate`, `fixed`, or omit for default close.

### reopen

```json
{
  "action": "reopen",
  "args": "",
  "session_id": "",
  "request_origin": "user",
  "fields": {
    "ticket_id": "T-20260302-01",
    "reopen_reason": "Regression found in v2.1 — issue recurred under new load pattern"
  }
}
```

`reopen_reason` is required by the engine for audit trail purposes.

---

## Field Disambiguation

Two fields look similar but serve different purposes:

| Field | Type | Stage | Purpose |
|-------|------|-------|---------|
| `key_file_paths` | `list[str]` | plan (input) | File paths for dedup fingerprinting. Include whenever files are relevant. |
| `key_files` | `list[dict]` | execute (input) | Structured table rows `{file, role, look_for}` for rendering into the ticket body. |

Include both in `create` payloads when you have file context. If only paths are known (no descriptions), populate `key_file_paths` and omit `key_files` — the engine will render paths-only.

---

## `need_fields` Loop

When `plan` returns `state: "need_fields"`:

1. Read `data.missing_fields` — list of field names the engine requires.
2. Ask the user for each missing field. Example: "To create this ticket I need: priority (critical/high/medium/low). What priority?"
3. Update `.claude/ticket-tmp/payload.json` — write the user's answers into `fields`.
4. Re-run from `plan` (not from `classify` — `intent` is already in the payload):
   ```bash
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py plan .claude/ticket-tmp/payload.json
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py preflight .claude/ticket-tmp/payload.json
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py execute .claude/ticket-tmp/payload.json
   ```
5. If `plan` returns `duplicate_candidate` during this loop, enter the `duplicate_candidate` loop below before proceeding. If `plan` returns any other non-`need_fields` state, handle it per the Step 5 response state table in SKILL.md.

---

## `duplicate_candidate` Loop

When `plan` returns `state: "duplicate_candidate"`:

1. Read `data.duplicate_of` — the ID of the existing ticket that matches.
2. Read the existing ticket: `python3 <PLUGIN_ROOT>/scripts/ticket_read.py query <TICKETS_DIR> <duplicate_of>`
3. Present the match to the user:
   ```
   Found a similar ticket: T-20260302-01 — "Fix auth token race condition" (open, high priority)

   Create a new ticket anyway? [y/n]
   ```
4. If `n` → stop and point the user to the existing ticket.
5. If `y` → add `dedup_override: true` and `ticket_id: "<duplicate_of>"` to the payload at the top level (not inside `fields`). The `ticket_id` here is the duplicate's ID from `data.duplicate_of` — this tells the engine which existing ticket you are overriding. Then re-run:
   ```bash
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py plan .claude/ticket-tmp/payload.json
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py preflight .claude/ticket-tmp/payload.json
   python3 <PLUGIN_ROOT>/scripts/ticket_engine_user.py execute .claude/ticket-tmp/payload.json
   ```

---

## Response State → UX Mapping

All 15 machine states from the ticket contract:

| State | When emitted | User-facing action |
|-------|-------------|-------------------|
| `ok` | Generic success (non-specific) | Report success |
| `ok_create` | Ticket created | "Created ticket T-YYYYMMDD-NN at docs/tickets/<slug>.md" |
| `ok_update` | Ticket updated | "Updated T-... — changed: <list fields>" |
| `ok_close` | Ticket closed (in-place) | "Closed ticket T-..." |
| `ok_close_archived` | Ticket closed and moved | "Closed ticket T-... (archived to docs/tickets/closed-tickets/)" |
| `ok_reopen` | Ticket reopened | "Reopened T-... — status is now open" |
| `need_fields` | Required fields missing | Run `need_fields` loop (above) |
| `duplicate_candidate` | Fingerprint matches existing ticket | Run `duplicate_candidate` loop (above) |
| `preflight_failed` | Policy or state check failed | Report `data.checks_failed` list; stop |
| `policy_blocked` | Operation blocked by policy | Report policy message from `top-level `message``; stop |
| `invalid_transition` | Status change not allowed | Report current status and valid transitions; stop |
| `dependency_blocked` | Blocked-by tickets not resolved | Report `data.blocking_ids` list; stop |
| `not_found` | Ticket ID does not exist | "Ticket T-... not found in docs/tickets/"; stop |
| `escalate` | Engine hit unrecoverable state | Report `top-level `message``; stop; do not retry automatically |
| `merge_into_existing` | Reserved — not emitted in v1.0 | N/A |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — response JSON on stdout |
| 1 | Engine error — details on stderr |
| 2 | Validation failure — malformed payload or missing required field |

On exit code 2: check the payload against schemas above. The `session_id` field can be an empty string — the guard hook injects the real value.
