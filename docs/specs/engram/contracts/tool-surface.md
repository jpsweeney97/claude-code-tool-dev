---
module: tool-surface
legacy_sections: ["4"]
authority: contracts
normative: true
status: active
---

## MCP Tool Surface (13 tools)

| # | Tool | Subsystem | Envelope | Key Parameters |
|---|------|-----------|----------|----------------|
| 1 | `session_start` | Context | Entity | session_id (required), goal, branch, context_summary, tags, continued_from_session_ids, external_refs |
| 2 | `session_snapshot` | Context | Entity | content, kind (checkpoint), external_refs |
| 3 | `session_end` | Context | Entity | summary, final_content (optional — creates kind='final' snapshot) |
| 4 | `session_get` | Context | Entity | session_id (returns session + loadable_snapshot) |
| 5 | `session_list` | Context | Collection | state (all\|open\|closed; default: all), limit, cursor (returns activity_at, last_snapshot_at per session; ordered by activity_at DESC) |
| 6 | `task_create` | Work | Entity | title, description, priority, tags, blocked_by[], sources, external_refs, derived_from_lesson_ids |
| 7 | `task_update` | Work | Entity | task_id, action (patch/close/reopen), terminal_status, fields, reason, add_blocked_by[], remove_blocked_by[], add_sources, add_external_refs, add_derived_from_lesson_ids |
| 8 | `task_query` | Work | Collection | text (FTS), task_ids[], status[], priority[], tags[], session_id, blocked_by[], blocks[], is_blocked, has_dependents, limit, cursor |
| 9 | `lesson_capture` | Knowledge | Entity | insight, context, tags, sources, external_refs, derived_from_task_ids |
| 10 | `lesson_query` | Knowledge | Collection | text (FTS), lesson_ids[], tags[], status, promoted, sort_by (created_at_desc\|updated_at_desc\|reinforcement_count_desc; default: created_at_desc), session_id, limit, cursor |
| 11 | `lesson_update` | Knowledge | Entity | lesson_id, action (patch/retract/reinforce), fields (context, tags), add_sources, add_external_refs, add_derived_from_task_ids; retract additionally accepts reason_code ('incorrect'/'obsolete') and reason |
| 12 | `lesson_promote` | Knowledge | Entity | lesson_id, target |
| 13 | `query` | Cross-cutting | Collection | text (required), entity_types[], tags[], updated_after, updated_before, limit, cursor |

### Response Envelopes

- **Entity envelope** (mutations): `{outcome, reason_code, entity, details, warnings}`
- **Collection envelope** (queries): `{results, total, cursor, warnings}`
- **Error taxonomy:** 5 reason codes: `invalid_transition`, `dependency_blocked`, `duplicate`, `policy_blocked`, `conflict`

### Ref Object

Structured provenance reference used by `sources`, `external_refs`, and `lesson_promote` `target`:

```json
{ "type": "github_pr", "ref": "https://github.com/org/repo/pull/42", "label": "PR #42" }
```

- `type` (required): `url`, `file`, `github_issue`, `github_pr`, or domain-specific types
- `ref` (required): URI or path
- `label` (optional): human-readable display name

Parameter name determines `provenance_links.relation_type` (`sources` → `'source'`, `external_refs` → `'external_ref'`). Ref fields map to provenance columns: `type` → `target_type`, `ref` → `target_ref`, `label` → `target_label`.

### Session Bootstrap

`session_start` is the only session creation path — no auto-open on first MCP call. All mutation tools **except `session_start`** require an active session. Enforcement is distributed across three layers:

| Layer | Role | Mechanism |
|-------|------|-----------|
| **Skills** | Identity carrier | SKILL.md contains `${CLAUDE_SESSION_ID}` (substituted at load time); skill passes the UUID as `session_id` to MCP tools |
| **PreToolUse hook** | Stateless identity validation | Cross-checks `tool_input.session_id` against top-level `session_id` (hook common input field); blocks on mismatch (exit 2). `session_start` is exempt |
| **MCP server** | Existence and lifecycle enforcement | Rejects mutations when session does not exist, is closed, or violates constraints. Returns `reason_code` in entity envelope |

`session_start` is exempt from hook identity validation because it is the tool that creates sessions — requiring a session to exist before creating one is circular.

`session_start` must be idempotent on `session_id`. Calling it on an existing session applies **field-specific patch semantics**:

| Field Category | Omitted | Explicit Null | Present (non-null) | Rationale |
|----------------|---------|---------------|-------------------|-----------|
| Scalars (`goal`, `branch`, `context_summary`) | Preserve existing | Clear to NULL | Replace | Descriptive metadata — latest value wins |
| `tags` | Preserve existing | Clear to NULL | Replace with provided set (deduplicated); `[]` clears to NULL | Descriptive metadata — replace, not accumulate |
| `continued_from_session_ids` | Preserve existing | Rejected (`policy_blocked`) | Append (deduplicated); `[]` is no-op | Relationship log — additive, never clearable |
| `external_refs` | Preserve existing | Rejected (`policy_blocked`) | Append (deduplicated on `(relation_type, target_type, target_ref)`); `[]` is no-op | Provenance is append-only, never clearable |

**Empty string rule:** `""` is invalid for all scalar fields — server rejects with `reason_code='policy_blocked'`. Use explicit null to clear.

**Transport requirement:** Three-state semantics require the transport to distinguish missing keys from explicit null values. Standard JSON (`{}` vs `{"goal": null}`) supports this natively. MCP tool input uses JSON.

**Update guards:**
- The entity envelope response includes `details.created` (boolean) so callers can detect whether the call created a new session or enriched an existing one
- Self-links are rejected (`continued_from_session_ids` must not contain the current session's ID)
- Updates to closed sessions are rejected unless the call is a semantic no-op after normalization (zero persisted value changes AND zero new rows in relationship tables)
- First continuation link becomes `is_primary=true`; subsequent distinct links are secondary

**Session_id availability:** Skills obtain the current session UUID via `${CLAUDE_SESSION_ID}`, a skill content substitution that Claude Code replaces with the session UUID when SKILL.md is loaded (available since Claude Code v2.1.9). Skills pass `session_id` explicitly to all MCP mutation tools. Read tools do not require `session_id` — skills pass it explicitly when session-scoped filtering is needed.

### Action Semantics

**`task_update` actions:**
- `patch` — non-terminal edits: title, description, priority, tags, status transitions between `open` ↔ `in_progress`. Rejects `reason` and `terminal_status` (`policy_blocked`)
- `close` — terminal: requires `terminal_status` (`done`|`cancelled`). `cancelled` requires non-empty `reason`; `done` forbids `reason` (server rejects if present). Sets `closed_at`.
- `reopen` — sets status to `open`, clears `closed_at` and `reason`. Only valid from terminal states (`done`, `cancelled`) — server returns `invalid_transition` for non-terminal tasks

**`lesson_update` actions:**
- `patch` — update `context` and/or `tags`, and/or append provenance (`add_sources`, `add_external_refs`, `add_derived_from_task_ids`). At least one field or provenance parameter required. Rejects `reason_code` and `reason` (`policy_blocked`)
- `retract` — set status to `retracted` (lesson found to be wrong). Accepts `reason_code` (enum: `incorrect`, `obsolete`) and `reason` (freeform string). Server stores both alongside the retraction and sets `retracted_at`. Rejects `fields` and all `add_*` provenance params (`policy_blocked`)
- `reinforce` — increment `reinforcement_count` (explicit reinforcement path when caller knows `lesson_id`, separate from `lesson_capture` dedup which is implicit via `anchor_hash`). Optionally accepts `add_sources`, `add_external_refs`, `add_derived_from_task_ids`. Does not accept context/tags — use `patch` for field updates. Rejects retracted lessons (`invalid_transition`) — if the insight is re-encountered, use `lesson_capture` which creates a new active lesson

### Architectural Rules

- `task_update` and `lesson_update` use explicit `action` field to separate non-terminal edits from lifecycle transitions
- Dependencies use `blocked_by[]` on creation/update; `blocks[]`, `is_blocked`, `has_dependents` are derived on read from `task_dependencies`
- No archive/active table distinction — use `closed_at` + query-time filtering
- Flat resource-prefixed tool naming (`session_start`, not `context.session_start`)
- Provenance uses structured Ref objects — mutation tools accept `sources` and `external_refs` as Ref arrays, server writes `provenance_links` rows
- **Provenance parameter naming convention:** Create tools use plain names (`sources`, `external_refs`) for initial provenance sets. Update tools use `add_` prefix (`add_sources`, `add_external_refs`) for append-only provenance. Mutable relationships use both `add_` and `remove_` prefixes (`add_blocked_by`, `remove_blocked_by`). This asymmetry signals the append-only invariant — there is no `remove_sources`
- `anchor_hash` is server-computed from normalized `insight` text — not a tool parameter. On `lesson_capture` with anchor_hash match: merge path returns `outcome='reinforced'`, increments `reinforcement_count`, applies field-specific merge semantics (tags replaced if provided, context preserved with `details.context_conflict=true` when different — see [behavioral-semantics.md](behavioral-semantics.md#anchor-hash-merge)). No match: `outcome='created'`
- `session_get` returns session metadata plus `loadable_snapshot` (`Snapshot|null`): final snapshot if present, else latest checkpoint, else null (no snapshots). This is the primary load API for the Context subsystem.
- `session_end` atomically writes a `kind='final'` snapshot (if `final_content` provided) and closes the session
- `session_id` is an externally-provided UUID (the Claude Code session ID, passed by skills via `${CLAUDE_SESSION_ID}`). `task_id` and `lesson_id` are server-generated UUIDs. `entity_pk` is internal only.
- **Atomic rejection invariant:** When a mutation tool returns a determinate failure (`reason_code` in the entity envelope), the server guarantees no durable state was changed. All mutations are transactional — either fully applied or fully rejected.

### Public Result Types

The public API contract is defined by this document and `contracts/`. [Schema documents](../schema/ddl.md) describe storage implementation and must not change public behavior.

| Type | Used By | Key Fields |
|------|---------|------------|
| `SessionSummary` | `session_list.results[]` | session_id, goal, branch, tags, started_at, closed_at, activity_at (computed), last_snapshot_at (computed), snapshot_count (computed) |
| `SessionDetail` | `session_get.entity` | SessionSummary fields + context_summary, summary, loadable_snapshot (`Snapshot|null` — final if present, else latest checkpoint, else null) |
| `TaskSummary` | `task_query.results[]` | task_id, title, description, status, priority, tags, reason, created_at, updated_at, closed_at, is_blocked (derived), blocked_by[] (derived task_ids), blocks[] (derived task_ids), has_dependents (derived) |
| `LessonSummary` | `lesson_query.results[]` | lesson_id, insight, context, tags, status, promoted, reinforcement_count, created_at, updated_at |
| `SearchHit` | `query.results[]` | entity_type, entity_id, title, snippet (FTS-highlighted excerpt), tags, relevance_score, created_at |

**`SearchHit.relevance_score`:** Opaque higher-is-better float. Valid for within-query ordering only — not normalized across queries, not comparable between different query strings. Backed by FTS5 rank value (or monotonic transformation).

**`lesson_query.sort_by`:** Descending-only enum in v1: `created_at_desc` (default), `updated_at_desc`, `reinforcement_count_desc`. Default applies when `sort_by` is omitted.

**Internal-only fields (not in public types):** `entity_pk`, `session_pk`, `sessions.updated_at`. The `updated_at` column tracks operational freshness for internal queries; public freshness signals are `activity_at` (primary ordering for `session_list`), `last_snapshot_at`, and `closed_at`.

Shared fragments:
- **Timestamps:** ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SS.fffZ`)
- **Tags:** JSON arrays of strings, always deduplicated
- **Ref objects:** `{type, ref, label}` — see Ref Object section above

### Public IDs

**Public IDs:** `session_id` is externally provided by Claude Code (via `${CLAUDE_SESSION_ID}` skill substitution). `task_id` and `lesson_id` are server-generated UUIDs. `entity_pk` is internal only — never exposed through the tool surface.
