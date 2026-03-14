# Engram: Design Specification

**Status:** In progress (brainstorming phase)
**Date:** 2026-03-12

---

## 1. System Overview

**Engram** is a persistence and observability layer for Claude Code, packaged as a single plugin. It maintains state across sessions via three subsystems — Context, Work, and Knowledge — backed by a project-local SQLite database and exposed through a single MCP server.

### What Engram Replaces

The handoff plugin, ticket plugin, and learning pipeline (`/learn`, `/distill`, `/promote`) are fully superseded. This is a complete redesign — no backwards compatibility.

### Architecture: "A outside, B inside"

- **External:** One plugin, one MCP server (FastMCP, stdio transport), one database (`.engram/engram.db`)
- **Internal:** `kernel/` package owns shared infrastructure; three subsystem modules (`context/`, `work/`, `knowledge/`) own domain logic; subsystem modules never import each other

### Layering

| Layer | Role | Examples |
|-------|------|---------|
| **Skills** | Orchestration + higher-order judgment | `/save`, `/load`, `/triage`, `/promote` |
| **Hooks** | Identity validation + mutation enforcement | `PreToolUse` → validate session identity; lifecycle hooks TBD (Section 8) |
| **MCP tools** | Atomic operations with server-side validation | `session_start`, `task_create`, `lesson_capture`, `query` |
| **SQLite** | Persistent storage | `.engram/engram.db` with WAL mode |

### Three Subsystems

**Context** — Captures and restores session state. The unit is a *snapshot*: structured session state that any future session can load. Sessions are first-class entities (opened explicitly via `session_start`, closed via `session_end`).

**Work** — Tracks tasks through a defined lifecycle. A work graph that Claude Code can read and write. Knows what's planned, in-progress, done, and cancelled. Dependency blocking is derived from the task graph, not stored as status.

**Knowledge** — Captures durable insights as *lessons*: structured knowledge with `insight` (one-liner), `context` (freeform), and `tags`. Retrievable via FTS5. Lessons that prove durable can be promoted (a derived database projection, not a separate workflow).

---

## 2. Skills, MCP Tools, and the Judgment Split

### The Design Tension

Skills are prompt-based playbooks — they instruct Claude on what to do. But Claude Code doesn't architecturally enforce skill mediation of MCP tools. Claude can see MCP tool descriptions and call them directly.

### Resolution: Smart Tools + Hook Enforcement + Skills as UX

**"Smart tools make bypass safe; hooks make bypass rarer; skills make the system usable."**

Judgment is distributed across three layers:

| Layer | Owns | Examples |
|-------|------|---------|
| **Server (MCP tool)** | Minimum bar — integrity invariants | Dedupe check, schema validation, idempotency, evidence-present check |
| **Skill** | Higher-order judgment — workflow orchestration | When to capture, what to present to user, batching, timing |
| **Hook** | Coarse-gating — audit and policy | Block unauthenticated mutations, log all writes |

This means skills are the *intended* entry point, but the system is safe even without them.

### Tool Access Model

| Tool Category | Direct Call? | Skill Required? | Hook Enforced? |
|--------------|-------------|-----------------|----------------|
| **Read tools** (session_get, session_list, task_query, lesson_query, query) | Yes | No — safe for direct lookup | No |
| **Mutation tools** (session_start, session_snapshot, session_end, task_create, task_update, lesson_capture, lesson_update, lesson_promote) | Possible but discouraged | Yes — skills provide orchestration | Yes — PreToolUse hook gates mutations |

### Tool Descriptions

Clear and specific — not vague. Server instructions state the policy: "Mutation tools are normally invoked via Engram skills that perform relevance, dedupe, and workflow checks." Vague descriptions fight tool search and aren't a real control mechanism.

---

## 3. Design Decisions

These decisions were made during the brainstorming phase:

| Decision | Choice | Source |
|----------|--------|--------|
| MCP interface model | Thick MCP — domain-specific tools | Brainstorming Q1, Codex dialogue #22 |
| Storage backend | SQLite (pure, no file export) | Brainstorming Q2 |
| Scope | Project-local (`.engram/engram.db`) | Brainstorming Q3 |
| Session identity | First-class entities (sessions table) | Brainstorming Q4 |
| Lesson structure | Minimal structured: `insight` + `context` + `tags` + metadata + optional facets | Codex consultation #1 |
| Retrieval model | FTS5 (tag + text search), promotion as derived DB projection | Codex consultation #1 |
| MCP tool surface | 13 tools (5 session + 3 task + 4 lesson + 1 cross-cutting query) | Codex dialogue #1, deep review #6 |
| Cross-cutting query | Dedicated FTS projection, not fan-out to domain tools | Codex dialogue #1 |
| Coupling approach | "A outside, B inside" — single server/DB, internally modular | Codex dialogue #2 |
| Skill/MCP relationship | Smart tools + hook enforcement + skills as UX | Codex consultation #2-3 |
| Skill surface model | Separate skills per workflow (not one skill per subsystem) | Brainstorming Q8 |
| Lifecycle events | Hooks for enforcement, skills for lifecycle and judgment | Brainstorming Q9 |

### MCP vs CLI — Re-evaluated Rationale

*The CLI alternative was not evaluated during brainstorming Q1. Codex dialogue #22 (thread `019cea73`, exploratory, 6 turns) performed a head-to-head evaluation. MCP was confirmed, but for different reasons than originally assumed.*

**Original rationale (weak):** Connection persistence — keeping the SQLite connection open across calls. In practice, SQLite opens are cheap and WAL mode works correctly from short-lived processes.

**Actual deciding factors:**

1. **API fidelity.** Engram requires three-state patch semantics (omitted/null/present), typed Ref objects, structured action enums, and FTS5 query parameters. These are native JSON/MCP constructs. CLI argv cannot distinguish "field omitted" from "field set to null." The ticket plugin's payload-by-file workaround (write JSON to temp file, pass path as argv) demonstrates that CLI with complex structured data becomes ad hoc RPC over Bash.

2. **Hook enforcement.** MCP gives PreToolUse hooks structured `tool_input` for stateless identity validation — match a tool name, read `session_id` directly. CLI hooks must match on `Bash` and parse command strings. The ticket plugin's guard hook requires 218 lines of shlex parsing, env expansion, and metacharacter blocking for one CLI tool. Engram has 8 mutation tools requiring identity validation.

3. **Complexity quarantine.** CLI distributes transport complexity across skills (command construction), hooks (Bash parsing), and temp-file conventions. MCP quarantines it in `server.py`. The design discipline: `server.py` should be the thinnest file in the system — domain logic stays in plain Python modules (`kernel/`, `context/`, `work/`, `knowledge/`).

**Deferred:** Admin CLI for inspection and debugging (v2, only if operational pain appears). Raw `sqlite3 .engram/engram.db` covers most admin operations. Invariant-aware operations (`migrate`, `doctor`, `rebuild-search`) are the candidates for a purpose-built CLI.

**Open risks:** (1) 13 tool descriptions cost an estimated 3k–8k tokens in context (~1.5–4% of 200k); Claude Code's Tool Search mitigates but the estimate is unverified. (2) MCP server crash recovery is undocumented — if Claude Code does not auto-restart crashed servers, all Engram operations silently fail until next session.

---

## 4. MCP Tool Surface (13 tools)

*Revised based on Codex deep review #6 (thread `019ce54a`). Key changes: session_start requires session_id, session_end is atomic with optional final_content, anchor_hash removed from lesson_capture, lesson_update added, task dependencies writable, Ref objects for provenance, action semantics specified. Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — three-layer enforcement model, `${CLAUDE_SESSION_ID}` identity transport, plugin naming resolved; three-state patch semantics, semantic no-op guard, `loadable_snapshot` nullability, `sessions.updated_at` (internal-only). Bundle 3 — `terminal_status` close parameter, `depends_on[]` → `blocked_by[]` query parameter rename. Bundle 4 — `anchor_hash` merge with `context_conflict`, provenance `target_label` + uniqueness, `sort_by` enum, `relevance_score` semantics. Codex dialogue #19 — `session_list` state filter + `activity_at` ordering, provenance naming convention, `lesson_update` provenance params.*

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
- `anchor_hash` is server-computed from normalized `insight` text — not a tool parameter. On `lesson_capture` with anchor_hash match: merge path returns `outcome='reinforced'`, increments `reinforcement_count`, applies field-specific merge semantics (tags replaced if provided, context preserved with `details.context_conflict=true` when different — see S6.6). No match: `outcome='created'`
- `session_get` returns session metadata plus `loadable_snapshot` (`Snapshot|null`): final snapshot if present, else latest checkpoint, else null (no snapshots). This is the primary load API for the Context subsystem.
- `session_end` atomically writes a `kind='final'` snapshot (if `final_content` provided) and closes the session
- `session_id` is an externally-provided UUID (the Claude Code session ID, passed by skills via `${CLAUDE_SESSION_ID}`). `task_id` and `lesson_id` are server-generated UUIDs. `entity_pk` is internal only.
- **Atomic rejection invariant:** When a mutation tool returns a determinate failure (`reason_code` in the entity envelope), the server guarantees no durable state was changed. All mutations are transactional — either fully applied or fully rejected.

### Public Result Types

Section 6 is storage schema; Section 4 is the API contract. Read-tool results use named public types that may diverge from raw table columns (computed fields, joins, omitted internals). DDL changes do not alter the API unless this section changes.

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

---

## 5. Internal Architecture

### Directory Layout (v1)

```
engram/
├── kernel/
│   ├── db.py           # Connection, WAL mode, migrations runner
│   ├── migrations.py   # Schema versioning
│   ├── entities.py     # Shared entities table, entity_pk allocation
│   ├── search.py       # FTS search_documents projection
│   └── types.py        # Shared enums, response envelopes
├── context/            # Sessions, snapshots, session_links
├── work/               # Tasks, task_dependencies
├── knowledge/          # Lessons, lesson promotion
└── server.py           # FastMCP tool registration, wiring
```

### Key Architectural Rules

- **Subsystem modules must not import each other** — cross-subsystem operations go through the kernel or `server.py` wiring layer. Exception: `tasks.session_pk` and `lessons.session_pk` create schema-level coupling to the context subsystem. This is intentional attribution — `server.py` resolves `session_pk` before passing to subsystem modules, so work/ and knowledge/ never query context/ directly.
- **Search projection is transactionally coupled** — `kernel/search.py` is the sole writer to `search_projection`. Subsystem modules provide data; kernel owns the write. This is honest coupling in v1 (single-user SQLite, same-transaction writes). A `rebuild_search()` function provides repair if the projection drifts.
- **Three-tier test architecture:** subsystem tests (bulk), integration tests (cross-subsystem), server tests (wiring only)
- **Kernel-owned `entities` table** with `entity_pk` FKs provides cross-subsystem referential integrity
- **Single architecture test** enforces no cross-subsystem imports (formal lint deferred)
- **Relationship taxonomy:** typed FKs for canonical relationships (session_links, task_dependencies), `entity_derivations` for internal cross-entity lineage (intentionally generic — source kind recoverable from `entities.kind` JOIN), `provenance_links` for external references
- **Session bootstrap:** `session_start` is the only creation path. Skills carry session identity via `${CLAUDE_SESSION_ID}`; `PreToolUse` hook validates identity (stateless cross-check); server enforces session existence and lifecycle. Mutation skills call `session_start` lazily before their first mutation if no session exists (Section 7.3). No auto-open.
- **Sessions are non-deletable in v1** — no delete tool. `ON DELETE RESTRICT` on tasks/lessons enforces referential integrity. Orphan sessions accumulate (acceptable for local dev tool).
- **`session_links` directionality:** `from_session_pk` = prior session, `to_session_pk` = new session. Chronological: edges flow forward in time. When session B calls `session_start(continued_from_session_ids=[A])`, server writes `from_session_pk=A, to_session_pk=B`.

### Deferred for v1

- DAG cycle detection in task dependencies
- Formal import lint (single architecture test instead)
- Generic provenance querying
- Deep kernel sub-layering (bootstrap vs projections)
- Session deletion
- `lesson status = 'superseded'` (requires explicit supersession links)

---

## 6. Database Schema

*Revised based on Codex dialogue #5 (thread `019ce52a`) and deep review #6 (thread `019ce54a`). Dialogue #5: dual-table search projection, three-class relationship taxonomy, lessons trimmed, unicode61 tokenizer, JSON CHECKs, ON DELETE policy, bidirectional status/closed_at constraint. Deep review #6: removed blocked from task status, added task_id/lesson_id/description columns, added task_dependencies and search_projection indexes, session_links directionality defined.*

### Connection Pragmas

Set at connection time, not in schema DDL:

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
```

### 6.1 Kernel

```sql
-- Central entity registry — every domain object gets an entity_pk
CREATE TABLE entities (
    entity_pk   INTEGER PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('session', 'snapshot', 'task', 'lesson')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Migration tracking — forward-only numbered migrations
CREATE TABLE schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Search projection — ordinary table owned by kernel, source of truth for search
-- Application writes this in the same transaction as domain table mutations
CREATE TABLE search_projection (
    entity_pk        INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    entity_type      TEXT NOT NULL,  -- 'session', 'task', 'lesson' (not 'snapshot')
    title            TEXT NOT NULL,
    body             TEXT,
    tags_json        TEXT,           -- JSON array for exact filtering via json_each
    tags_text        TEXT,           -- space-separated for FTS
    created_at       TEXT NOT NULL,
    last_modified_at TEXT NOT NULL
);

-- FTS5 index — external content mode over search_projection
CREATE VIRTUAL TABLE search_documents USING fts5(
    title,
    body,
    tags_text,
    content='search_projection',
    content_rowid='entity_pk',
    tokenize='unicode61'
);

-- FTS5 sync triggers — maintain index when projection changes
CREATE TRIGGER search_ai AFTER INSERT ON search_projection BEGIN
    INSERT INTO search_documents(rowid, title, body, tags_text)
    VALUES (new.entity_pk, new.title, new.body, new.tags_text);
END;

CREATE TRIGGER search_ad AFTER DELETE ON search_projection BEGIN
    INSERT INTO search_documents(search_documents, rowid, title, body, tags_text)
    VALUES ('delete', old.entity_pk, old.title, old.body, old.tags_text);
END;

CREATE TRIGGER search_au AFTER UPDATE ON search_projection BEGIN
    INSERT INTO search_documents(search_documents, rowid, title, body, tags_text)
    VALUES ('delete', old.entity_pk, old.title, old.body, old.tags_text);
    INSERT INTO search_documents(rowid, title, body, tags_text)
    VALUES (new.entity_pk, new.title, new.body, new.tags_text);
END;
```

### 6.2 Context Subsystem

```sql
CREATE TABLE sessions (
    entity_pk       INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    session_id      TEXT NOT NULL UNIQUE,  -- Claude Code session UUID
    goal            TEXT,
    branch          TEXT,
    context_summary TEXT,
    tags            TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    started_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    closed_at       TEXT,
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    summary         TEXT
);

CREATE TABLE snapshots (
    entity_pk   INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    session_pk  INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    content     TEXT NOT NULL,  -- JSON: structured session state
    kind        TEXT NOT NULL DEFAULT 'checkpoint' CHECK (kind IN ('checkpoint', 'final')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE session_links (
    from_session_pk INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    to_session_pk   INTEGER NOT NULL REFERENCES sessions(entity_pk) ON DELETE CASCADE,
    is_primary      INTEGER NOT NULL DEFAULT 0,  -- boolean: primary continuation chain
    PRIMARY KEY (from_session_pk, to_session_pk)
);

CREATE INDEX idx_sessions_branch ON sessions(branch);
CREATE INDEX idx_sessions_closed ON sessions(closed_at);
CREATE INDEX idx_snapshots_session ON snapshots(session_pk);
CREATE UNIQUE INDEX idx_snapshots_final ON snapshots(session_pk) WHERE kind = 'final';
CREATE INDEX idx_search_entity_type ON search_projection(entity_type);
```

### 6.3 Work Subsystem

```sql
CREATE TABLE tasks (
    entity_pk   INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    task_id     TEXT NOT NULL UNIQUE,  -- server-generated UUID
    title       TEXT NOT NULL,
    description TEXT,                   -- optional task body; maps to search_projection.body
    status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
    priority    TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    tags        TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    reason      TEXT,  -- close reason; required for 'cancelled', forbidden for 'done' (server-side validation)
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    closed_at   TEXT,
    session_pk  INTEGER REFERENCES sessions(entity_pk) ON DELETE RESTRICT,
    -- Bidirectional invariant: closed_at set iff terminal status
    CHECK ((closed_at IS NULL) = (status NOT IN ('done', 'cancelled')))
);

CREATE TABLE task_dependencies (
    task_pk         INTEGER NOT NULL REFERENCES tasks(entity_pk) ON DELETE CASCADE,
    depends_on_pk   INTEGER NOT NULL REFERENCES tasks(entity_pk) ON DELETE CASCADE,
    PRIMARY KEY (task_pk, depends_on_pk),
    CHECK (task_pk != depends_on_pk)
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_session ON tasks(session_pk);
CREATE INDEX idx_deps_depends_on ON task_dependencies(depends_on_pk);
```

### 6.4 Knowledge Subsystem

```sql
CREATE TABLE lessons (
    entity_pk           INTEGER PRIMARY KEY REFERENCES entities(entity_pk) ON DELETE CASCADE,
    lesson_id           TEXT NOT NULL UNIQUE,  -- server-generated UUID
    insight             TEXT NOT NULL,  -- one-liner
    context             TEXT,           -- freeform body
    tags                TEXT CHECK (tags IS NULL OR json_valid(tags)),  -- JSON array
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'retracted')),
    promoted            INTEGER NOT NULL DEFAULT 0,  -- denormalized cache; truth is provenance_links
    reinforcement_count INTEGER NOT NULL DEFAULT 0,  -- historical: preserved on retraction, not decremented
    anchor_hash         TEXT NOT NULL,  -- server-computed normalized hash of insight; dedup key
    retracted_at        TEXT,           -- set when status transitions to 'retracted'
    retraction_code     TEXT CHECK (retraction_code IS NULL OR retraction_code IN ('incorrect', 'obsolete')),
    retraction_reason   TEXT,           -- freeform explanation for retraction
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    session_pk          INTEGER REFERENCES sessions(entity_pk) ON DELETE RESTRICT
);

CREATE INDEX idx_lessons_promoted ON lessons(promoted);
CREATE INDEX idx_lessons_status ON lessons(status);
CREATE INDEX idx_lessons_anchor ON lessons(anchor_hash);
CREATE INDEX idx_lessons_session ON lessons(session_pk);
```

### 6.5 Cross-cutting

```sql
-- Internal entity-to-entity lineage (derived_from_task_ids, derived_from_lesson_ids)
CREATE TABLE entity_derivations (
    entity_pk        INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    source_entity_pk INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (entity_pk, source_entity_pk)
);

-- External provenance + promotion targets (sources, external_refs, promoted_to)
-- Append-only: rows are never deleted (except by CASCADE from entities); only update is NULL label backfill
CREATE TABLE provenance_links (
    id              INTEGER PRIMARY KEY,
    entity_pk       INTEGER NOT NULL REFERENCES entities(entity_pk) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,  -- 'source', 'external_ref', 'promoted_to'
    target_type     TEXT NOT NULL,  -- 'url', 'file', 'github_issue', 'github_pr', etc.
    target_ref      TEXT NOT NULL,  -- URI or path
    target_label    TEXT,           -- human-readable display name (from Ref.label); excluded from uniqueness
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (entity_pk, relation_type, target_type, target_ref)
);

CREATE INDEX idx_derivations_source ON entity_derivations(source_entity_pk);
CREATE INDEX idx_provenance_entity ON provenance_links(entity_pk);
CREATE INDEX idx_provenance_target ON provenance_links(target_type, target_ref);
```

### 6.6 Design Notes

*Revised based on Codex deep review #6 (thread `019ce54a`). Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — `sessions.updated_at`, final snapshot uniqueness index, `session_get` null handling. Bundle 3 — `terminal_status` close semantics, `reason` binding (server-side validation). Bundle 4 — `anchor_hash` merge semantics, provenance `target_label` + uniqueness, `sort_by`/`relevance_score` mapping. Codex dialogue #19 — `session_list` state filter + `activity_at`, `lesson_update` provenance paths, collection-tool validation.*

**Table count:** 11 tables (3 kernel + 3 context + 2 work + 1 knowledge + 2 cross-cutting) + 1 FTS5 virtual table + 3 triggers.

**ON DELETE policy:**
- **CASCADE** (ownership): entities → all domain tables, sessions → snapshots/session_links, tasks → task_dependencies, entities → entity_derivations/provenance_links/search_projection
- **RESTRICT** (attribution): sessions ← tasks.session_pk, sessions ← lessons.session_pk — creation-session attribution is historical provenance that must not silently disappear

**Kind-check enforcement (v1):** Server-side invariant — kernel creates entity row in same transaction as domain row. Startup verifier query confirms no orphaned entities or kind mismatches. Integration test validates. Promote to DB triggers if write paths multiply.

**FTS5 sync model:** `kernel/search.py` is the sole writer to `search_projection`. Subsystem modules provide data; kernel owns the write in the same transaction as domain mutations. Triggers on `search_projection` maintain FTS5 index. Snapshots are not indexed — search covers sessions, tasks, and lessons only. A `rebuild_search()` function provides repair if the projection drifts.

**`search_projection.body` mapping:**
- **Tasks:** `description` column (nullable — tasks without descriptions have NULL body in projection)
- **Sessions:** synthesized from `goal` + `context_summary` + `summary` (server-side, not stored)
- **Lessons:** `context` column

**`lesson_query.sort_by` mapping:** Translates to SQL `ORDER BY` on the lessons table. Three values (descending-only in v1): `created_at_desc` (default) → `ORDER BY created_at DESC`, `updated_at_desc` → `ORDER BY updated_at DESC`, `reinforcement_count_desc` → `ORDER BY reinforcement_count DESC`. Default applies when `sort_by` is omitted. Invalid enum values are rejected; error transport for collection tools is implementation-defined in v1.

**`query` relevance_score:** The cross-cutting `query` tool returns `relevance_score` in each `SearchHit`. Raw FTS5 rank value (or monotonic transformation) — opaque higher-is-better float. Valid for within-query ordering only; not normalized across queries or comparable between different query strings.

**`anchor_hash` dedup and merge:** Server computes normalized hash of `insight` text — not a tool parameter. On `lesson_capture`, checks for existing active lesson with same `anchor_hash`. No match → create new lesson (`outcome='created'`). Match → merge (`outcome='reinforced'`): increment `reinforcement_count`, then apply field-specific merge semantics:

- **`context`:** Omitted or null → preserve existing. Present and identical → preserve, no conflict. Present and different → preserve existing, return `details.context_conflict=true`. The skill (not server) decides whether to follow up with `lesson_update(action='patch')`.
- **`tags`:** Omitted or null → preserve existing. Present → replace existing (deduplicated). Tags are categorical metadata — replacement during merge is safe, unlike freeform context.
- **`sources`, `external_refs`, `derived_from_task_ids`:** Follow standard append path during merge. Server writes provenance_links/entity_derivations rows; UNIQUE constraints deduplicate. New unique refs are appended to the existing lesson's provenance.

This preserves append-only knowledge semantics: the server never silently overwrites context. Retracted lessons are skipped during anchor_hash lookup — a new active lesson is created if the only match is retracted. NOT NULL enforced at schema level.

**`lesson_capture` dual-path:** Single tool handles both new lesson creation (no `anchor_hash` match) and reinforcement (match found → increment `reinforcement_count`, optionally update context/tags, `details.context_conflict` when provided context differs).

**Promotion model:** `lesson_promote` writes a `provenance_links` row with `relation_type='promoted_to'`, `target` Ref holding the destination, and sets `lessons.promoted = 1` as denormalized cache. Source of truth is the provenance_links row.

**Public IDs:** `session_id` is externally provided by Claude Code (via `${CLAUDE_SESSION_ID}` skill substitution). `task_id` and `lesson_id` are server-generated UUIDs. `entity_pk` is internal only — never exposed through the tool surface.

**Three-class relationship taxonomy:**
- **Canonical typed:** `session_links` (session continuation), `task_dependencies` (task DAG) — domain-specific semantics, real FKs
- **Internal lineage:** `entity_derivations` — cross-subsystem derivation (lesson from task, task from lesson) with real FKs + CASCADE. Intentionally generic: source kind recoverable from `entities.kind` JOIN; no `relation_type` column needed.
- **External provenance:** `provenance_links` — structured Ref objects (type, ref, label) as external references + promotion targets, append-only

**Provenance uniqueness:** `UNIQUE(entity_pk, relation_type, target_type, target_ref)` — `target_label` is excluded from uniqueness (presentation metadata, not identity). First-write-wins: duplicate inserts on the dedup key are silently ignored. Exception: existing rows with NULL `target_label` can be backfilled to non-NULL on subsequent writes (the one exception to first-write-wins — backfill from NULL only). Label on first write cannot be corrected without server-side migration (accepted for v1).

**`session_links` directionality:** `from_session_pk` = prior session, `to_session_pk` = new session. Chronological — edges flow forward in time. `is_primary` marks the main continuation chain.

**`session_end` atomicity:** When `final_content` is provided, server writes a `kind='final'` snapshot and sets `sessions.closed_at` and `sessions.updated_at` in one transaction. The partial unique index `idx_snapshots_final` enforces at most one final snapshot per session — if a final already exists, server rejects with `reason_code='conflict'` before hitting the constraint. When `final_content` is omitted, server sets `sessions.closed_at` and `sessions.updated_at` without creating a final snapshot.

**`session_get` as load API:** Returns session metadata plus `loadable_snapshot` (`Snapshot|null`): the `kind='final'` snapshot if present, else the latest `kind='checkpoint'` snapshot, else null (no snapshots). This is the primary entry point for the Context subsystem's restore-session use case.

**Cross-subsystem FK coupling:** `tasks.session_pk` and `lessons.session_pk` reference `sessions(entity_pk)` directly — work→context and knowledge→context coupling at the schema level. This is intentional attribution. `server.py` resolves `session_pk` before calling subsystem modules, so work/ and knowledge/ never query context/ directly. The Python import rule ("subsystems must not import each other") is preserved.

**Task dependency write paths:** `task_create` accepts `blocked_by[]` (initial dependencies). `task_update` accepts `add_blocked_by[]` and `remove_blocked_by[]`. Server writes/deletes `task_dependencies` rows. `blocks[]`, `is_blocked`, and `has_dependents` are derived at query time from reverse joins on `task_dependencies`. `idx_deps_depends_on` supports reverse lookups.

**`task_update(close)` terminal status:** `action='close'` requires `terminal_status` (`done`|`cancelled`) — server rejects close without it. `reason` binding is server-side validation (not CHECK constraint): `cancelled` requires non-empty `reason`; `done` rejects `reason` if present (prevents semantic overloading — "done with a reason" is indistinguishable from "cancelled"). `reopen` clears both `closed_at` and `reason`. Server-side validation preferred over multi-column CHECK for v1 — the bidirectional `closed_at`/status CHECK (Section 6.3) handles the state invariant; `reason` binding is an input policy, not a schema constraint. Validation failures use `reason_code='policy_blocked'`: close without `terminal_status`, `done` with `reason` present, `cancelled` without `reason`, `patch` with `reason` or `terminal_status`. `reopen` on a non-terminal task returns `invalid_transition`.

**Tool parameter → table mapping:**
- `sources`, `external_refs`, `add_sources`, `add_external_refs` → `provenance_links` rows (Ref objects → relation_type, target_type, target_ref, target_label)
- `derived_from_task_ids`, `derived_from_lesson_ids`, `add_derived_from_task_ids`, `add_derived_from_lesson_ids` → `entity_derivations` rows
- `continued_from_session_ids` → `session_links` rows
- `blocked_by[]` → `task_dependencies` rows

**Deferred for v1:** `durability`, `evidence`, `conditions`, `supersedes`, `contradicts` columns on lessons (no v1 tool writes or reads them). DAG cycle detection in `task_dependencies`. `lesson status = 'superseded'` (requires explicit supersession links). Session deletion. Structured retraction evidence (counter-evidence via distinct `relation_type` in `provenance_links`) — `relation_type` is open TEXT to enable future extension.

**`sessions.updated_at`:** Internal-only column — server sets on every session mutation (field patches via `session_start`, `session_end`). `session_snapshot` also updates `sessions.updated_at` as a cross-table side-effect (UPDATE on sessions row in the same transaction as the snapshots INSERT). Not exposed in S4 public types (SessionSummary, SessionDetail). Public freshness signals are `activity_at`, `last_snapshot_at`, and `closed_at`. Used for internal query filtering, time-range queries, and operational diagnostics.

**`session_list` ordering and `activity_at`:** `activity_at` is a computed field representing the most recent user-visible event on a session: the latest of `started_at`, `last_snapshot_at`, or `closed_at`. Computed at query time via grouped snapshot aggregate CTE — no schema change needed. `started_at` (NOT NULL) is the guaranteed floor: a session with no snapshots and not closed has `activity_at = started_at`. `session_list` orders by `(activity_at DESC, started_at DESC, session_id DESC)` — this deterministic sort tuple ensures cursor stability for pagination. The `state` filter (`all`|`open`|`closed`) applies server-side before `limit` — without server-side filtering, `limit=10` could return only closed sessions, pushing open ones off the first page. Note: `activity_at` tracks user-visible events only (start, snapshot, close); `sessions.updated_at` tracks all mutations including metadata patches. A `session_start` call that only updates `goal` bumps `updated_at` but not `activity_at`.

**Final snapshot uniqueness:** `idx_snapshots_final` is a partial unique index enforcing at most one `kind='final'` snapshot per session at the schema level. Defense-in-depth — server validates before INSERT.

**Migration strategy:** Forward-only numbered SQL files. Pre-migration backup of `.engram/engram.db` once holding real data. `schema_version` table tracks applied versions.

---

## 7. Skill Surface (6 skills)

*Designed via Codex dialogue #7 (exploratory, thread `019ce590`) and #8 (collaborative, thread `019ce5a8`). Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — lazy session bootstrap, `${CLAUDE_SESSION_ID}` identity transport, `mcp__plugin_engram_core__` prefix, mutation confirmation narrowed. Bundle 3 — `terminal_status` close parameter in `/task` workflow. Bundle 4 — `anchor_hash` merge with `context_conflict` in `/remember` workflow. Codex dialogue #19 — `/load` open-first session listing, `/remember` maintain routing rule.*

### 7.1 Skill Roster

| # | Skill | Subsystem Focus | MCP Tools Used | Mutation? |
|---|-------|----------------|----------------|-----------|
| 1 | `/save` | Context | `session_start`, `session_snapshot`, `session_end`, `session_get` | Yes |
| 2 | `/load` | Context + cross-subsystem | `session_list`, `session_get`, `session_start`, `task_query`, `lesson_query` | Yes |
| 3 | `/triage` | Cross-cutting | `task_query`, `session_list`, `lesson_query`, `query` | No (read-only) |
| 4 | `/task` | Work | `session_start`, `task_create`, `task_update`, `task_query` | Yes |
| 5 | `/remember` | Knowledge | `session_start`, `lesson_capture`, `lesson_update`, `lesson_query` | Yes |
| 6 | `/promote` | Knowledge + filesystem | `session_start`, `lesson_query`, `lesson_promote` + Read, Edit | Yes |

### 7.2 Visibility Model

All 6 skills are visible — descriptions are loaded into context at session start. No skill uses `disable-model-invocation`. Claude can auto-invoke any skill based on conversation context.

**Safety for mutation skills:** The two-stage guard (Section 7.3) prevents proactive mutation. All mutation skills require explicit user confirmation before user-directed MCP mutation calls. Infrastructure mutations (lazy session bootstrap via `session_start` — Section 7.3) are exempt from confirmation — they are transparent lifecycle operations, not user-visible state changes. This makes auto-visibility safe despite side effects — the confirmation gate is the control mechanism, not description hiding.

**Description constraints:** Narrow trigger phrases to Engram-scoped phrasing. Avoid generic phrases that over-match (e.g., "save" alone matches too broadly — use "save session state" or "wrap up this session"). Total description budget: 6 skills × ~200 chars = ~1,200 chars, well within the 2% context budget (~20k chars on 1M model).

**Natural-language triggers by skill:**
- `/save` — "wrap this up", "save session", "checkpoint", "end session"
- `/load` — "pick up where I left off", "continue from last session", "load session"
- `/triage` — "what's outstanding", "catch me up", "project status", "triage"
- `/task` — "create a task", "track this", "defer this for later"
- `/remember` — "remember this", "capture this insight", "this is worth noting"
- `/promote` — "promote this to CLAUDE.md", "graduate this lesson"

### 7.3 Cross-Cutting Patterns

#### Two-Stage Guard Architecture

All skills that call mutation tools use a two-stage guard to prevent proactive mutation:

**Stage 1 — Relevance gate** (skill-specific): A 3-way classifier in the skill body determines whether to execute, clarify, or ignore. This is per-skill judgment — each skill defines its own relevance criteria.

| Classification | Action | Example |
|---------------|--------|---------|
| Execute | Proceed to Stage 2 | User explicitly says "save my session" |
| Clarify | Ask one question | Ambiguous intent — "I'm done" could mean done with task or done with session |
| Ignore | Do nothing, respond normally | Conversation mentions "saving" in an unrelated context |

**Stage 2 — Confirmation** (shared): Uses the `mutation-confirmation.md` contract. The skill presents what will happen and asks for confirmation before any MCP mutation call.

#### Confirmation Severity Model

Three severity levels determine confirmation UX weight:

| Severity | Gate | Applied To |
|----------|------|-----------|
| **Advisory** | Inline confirmation, proceed by default | Checkpoints (`session_snapshot`) |
| **Durable** | Explicit yes/no before proceeding | Task creation/update, lesson capture |
| **Terminal** | Explicit yes/no with consequences stated | Session close (`session_end`), lesson retraction |

Per-skill severity bindings are specified in each skill's design below.

#### Snapshot Content Schema

The `snapshot-schema.md` contract defines what `/save` produces and `/load` consumes. Content follows the pointer-vs-substance principle:

| Data Type | Treatment | Rationale |
|-----------|-----------|-----------|
| Entities in Engram (tasks, lessons) | Store pointer (entity ID) | Canonical data lives in the database — snapshots reference, not duplicate |
| Working-memory data (conversation insights, unstructured context) | Store substance | Only exists in the session — snapshots preserve it |

Checkpoint and final snapshots use the same schema. They differ in `capture_type` and `focus.state` fields, not structure.

#### Cross-Skill Contracts

Three shared reference documents in the plugin's `references/` directory:

| Contract | Purpose | Producer | Consumer |
|----------|---------|----------|----------|
| `mutation-confirmation.md` | Shared confirmation UX template (advisory/durable/terminal) | All mutation skills | — |
| `snapshot-schema.md` | Snapshot content structure | `/save` | `/load` |
| `ref-normalization.md` | Ref object construction rules (type inference, path normalization, label generation) | All skills that write provenance | — |

**`mutation-confirmation.md` normative content:**
- Three severity levels: advisory (inline, proceed by default), durable (explicit yes/no), terminal (yes/no with consequences stated)
- Each confirmation presents: what will change, which MCP tool will be called, severity level
- User can override downward (skip advisory confirmations) but not upward
- After confirmation, execute the mutation immediately — do not re-confirm
- **Exemption:** Lazy session bootstrap (`session_start` calls per Section 7.3) is an infrastructure operation exempt from confirmation — it runs between confirmation and domain mutation without user interaction
- On failure, follow the single-mutation failure pattern (Section 7.3)

**`snapshot-schema.md` normative content:**
- Required fields: `capture_type` (enum: `checkpoint`, `final`), `captured_at` (ISO 8601), `session_id`
- Content block: `focus` object with `goal`, `state` (what the user was doing), `next_steps` (what remains)
- Entity references: `task_ids[]`, `lesson_ids[]` — pointers to Engram entities (not inline substance)
- Working-memory block: `conversation_insights` (freeform), `decisions` (freeform) — substance that only exists in the session
- Checkpoint and final snapshots use the same schema; they differ in `capture_type` and `focus.state` scope

**`ref-normalization.md` normative content:**
- `type` inference: local paths → `file`, URLs → `url`, GitHub patterns → `github_issue`/`github_pr`
- Path normalization: resolve relative paths to absolute, strip trailing slashes, collapse `//`
- Label generation: if not provided, derive from ref (filename for files, `#N` for issues/PRs, domain for URLs)
- Dedup key: `(relation_type, target_type, target_ref)` — normalized before comparison
- Skills constructing Ref objects apply these rules before passing to MCP tools

Skills interoperate through the MCP server (entity IDs, Ref objects), not through direct skill-to-skill protocols.

#### Single-Mutation Failure Pattern

When a confirmed single mutation fails, all mutation skills follow this shared pattern:

**Determinate failure** (server returns `reason_code` in entity envelope):
- Surface the `reason_code` and a natural-language interpretation
- State that the mutation was not applied (guaranteed by the atomic rejection invariant — Section 4)
- Do not silently retry
- Offer the user: retry, revise parameters, or abandon

**Indeterminate failure** (timeout, transport error, no server response):
- State that completion is unknown — the mutation may or may not have been applied
- Verify state via a read tool (e.g., `session_get`, `task_query`, `lesson_query`) before any retry
- Present verified state to the user before proceeding

Multi-step non-atomic workflows (`/promote` local-file promotion, `/task` "create task that blocks X") have additional per-skill recovery procedures specified in their designs below.

#### Lazy Session Bootstrap

*Added based on collaborative resolution #17 (thread `019ce851`). Resolves session identity transport and bootstrap ownership.*

Mutation skills (except `/load`) ensure a session exists before their first MCP mutation call. This is an infrastructure operation — no user confirmation required.

**Mechanism:**
1. Each mutation skill's SKILL.md contains a session identity declaration: `**Session identity:** ${CLAUDE_SESSION_ID}`. Claude Code substitutes the session UUID at load time.
2. After user confirms the domain mutation (Stage 2 of the two-stage guard) but before the first MCP mutation call, the skill calls `session_start(session_id=<session_id>)`.
3. `session_start` is idempotent (Section 4): if the session already exists, the call is a no-op or enrichment (field-specific patch semantics apply); if not, it creates the session row with minimal metadata (goal inferred from conversation context).
4. The `details.created` field in the entity envelope response indicates whether a new session was created or an existing one was enriched.
5. If `session_start` fails (e.g., session is closed), surface the error and stop — do not proceed to the domain mutation.

**Key properties:**
- **No user confirmation** — session bootstrap is infrastructure, not a user-directed mutation. The two-stage guard applies to the subsequent domain mutation.
- **Idempotent** — multiple skills bootstrapping in the same session converge to the same session row.
- **Skills carry identity** — `${CLAUDE_SESSION_ID}` provides the session UUID without hook injection. The `PreToolUse` hook validates that the skill-provided `session_id` matches the Claude Code session (stateless cross-check).

**Exception — `/load`:** `/load`'s `session_start` call serves dual purpose: bootstrap (creating the session row if needed) AND continuation (setting `continued_from_session_ids`). The user's session selection is the implicit confirmation. `/load` does not use the generic lazy bootstrap pattern — its `session_start` call is part of the domain workflow, not a separate infrastructure step.

### 7.4 Per-Skill Designs

#### `/save` — Session Persistence

**Frontmatter:**
```yaml
name: save
description: >
  Save session state to Engram. Use when the user says "wrap up",
  "save session", "checkpoint", "end session", or indicates they are
  finishing work and want to preserve context for a future session.
allowed-tools: mcp__plugin_engram_core__session_start, mcp__plugin_engram_core__session_snapshot, mcp__plugin_engram_core__session_end, mcp__plugin_engram_core__session_get
```

**Workflow:** Branches internally between two MCP tools based on user intent:

| Branch | MCP Tool | Confirmation | When |
|--------|----------|-------------|------|
| Checkpoint | `session_snapshot(content, kind='checkpoint')` | Advisory | Mid-session save, context pressure, quick state capture |
| Close | `session_end(summary, final_content)` | Terminal | End of session, user is done, "wrap this up" |

**Steps (close branch):**
1. Relevance gate: classify intent as execute/clarify/ignore
2. Determine branch: checkpoint or close (ask if ambiguous)
3. Synthesize session state using pointer-vs-substance principle (per `snapshot-schema.md`)
4. Present summary of what will be saved + confirmation (terminal severity)
5. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `session_end(summary=..., final_content=...)` — atomic final snapshot + close
7. Report outcome from entity envelope

**Steps (checkpoint branch):**
1-3. Same as close branch
4. Present summary + confirmation (advisory severity)
5. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `session_snapshot(content=..., kind='checkpoint')` — session stays open
7. Report outcome

**Design notes:**
- The hard confirmation gate prevents Claude from proactively calling session_end even though the skill is auto-visible
- `session_get` in allowed-tools enables reading current session state during synthesis (returns empty if session has not yet been bootstrapped — synthesis proceeds from conversation context)
- `/save` calls `session_start` only for lazy bootstrap (Section 7.3) — never for continuation or enrichment

#### `/load` — Session Resumption

**Frontmatter:**
```yaml
name: load
description: >
  Resume from a previous Engram session. Use when the user says "continue
  from last session", "pick up where I left off", "load session", or at
  the start of a session when prior context would help.
allowed-tools: mcp__plugin_engram_core__session_list, mcp__plugin_engram_core__session_get, mcp__plugin_engram_core__session_start, mcp__plugin_engram_core__task_query, mcp__plugin_engram_core__lesson_query
```

**Workflow:**
1. Relevance gate: classify intent as execute/clarify/ignore
2. Call `session_list(state='open', limit=10)` — present recent open sessions. If no suitable candidates (or user explicitly requests older/closed sessions), fall back to `session_list(state='all', limit=10)`
3. User selects a session (or skill suggests most recent)
4. Call `session_get(session_id=...)` — retrieve session metadata + `loadable_snapshot` (`Snapshot|null`)
5. Rehydrate linked entities: call `task_query(session_id=..., status=['open','in_progress'])` and `lesson_query(session_id=...)` to fetch open tasks and recent lessons from the selected session
6. Present session context using one of two profiles:
   - **Resume:** Pick up where you left off — show snapshot content, open tasks, recent lessons. Requires non-null `loadable_snapshot`.
   - **Catch-up:** Orientation on prior work — show goal, summary, key decisions. Used when `loadable_snapshot` is null or user intent is orientation.
7. Call `session_start(session_id=<session_id>, continued_from_session_ids=[selected_session_id], ...)` — bootstraps session (if needed) and sets continuation metadata
8. Report: session linked, context loaded

**Design notes:**
- `/load` does NOT archive or consume old sessions — prior sessions are database records, not queue items
- Step 5 uses session-scoped queries (`session_id` filter) for rehydration — not broad cross-subsystem search. `/load` is "resume one session", not "orient on the whole project" (that's `/triage`)
- Step 7 calls `session_start` for both bootstrap and continuation — `session_start` is idempotent on `session_id` (Section 4), so it creates the session row if needed and sets `continued_from_session_ids` in the same call. The user's session selection is the implicit confirmation (Section 7.3, lazy bootstrap exception).
- `session_start` field-specific patch semantics (Section 4) ensure enriching an existing session appends continuation links and preserves existing metadata
- `loadable_snapshot` is `Snapshot|null`: null when session has no snapshots (e.g., session was started but never saved). When null, `/load` falls back to catch-up profile only — there is no snapshot content to resume from
- Presentation profile (resume vs catch-up) is inferred from `loadable_snapshot` presence and user phrasing

#### `/triage` — Project Orientation

**Frontmatter:**
```yaml
name: triage
description: >
  Review project status across tasks, sessions, and lessons. Use when the
  user says "what's outstanding", "catch me up", "project status", "triage",
  or at the start of a session when the user wants project orientation.
allowed-tools: mcp__plugin_engram_core__task_query, mcp__plugin_engram_core__session_list, mcp__plugin_engram_core__lesson_query, mcp__plugin_engram_core__query
```

**Workflow:** Three mode-dependent query orderings based on user intent:

| Mode | Primary Query | Secondary | Supplement | Trigger Phrases |
|------|--------------|-----------|------------|-----------------|
| **Action** | `task_query(status=['open','in_progress'])` | `session_list(state='all', limit=5)` | `lesson_query` | "what should I work on", "what's outstanding", "triage" |
| **Catch-up** | `session_list(state='all', limit=10)` | `task_query(status=['open'])` | `query(text=...)` | "catch me up", "what happened", "project status" |
| **Knowledge** | `lesson_query(tags=[...])` or `query(text=...)` | `task_query` | `session_list` | "what do we know about X", "any lessons on" |

**Steps:**
1. Relevance gate: classify intent as execute/clarify/ignore
2. Determine mode from user phrasing (default: action)
3. Execute primary query
4. Execute secondary query for cross-subsystem context
5. Present unified view: tasks grouped by status/priority, recent sessions with goals, relevant lessons
6. Recommend next actions — may suggest `/task` for task management, but never creates tasks itself

**Design notes:**
- `/triage` is read-only — it calls only read tools. Safe for auto-invocation per the skills guide
- Text search switches to cross-cutting `query` as candidate generator, with native tools (`task_query`, `lesson_query`) for enrichment
- Description scoped to project-oriented phrasing to prevent over-matching on generic "what" questions

#### `/task` — Task Management

**Frontmatter:**
```yaml
name: task
description: >
  Create and manage Engram tasks. Use when the user says "create a task",
  "track this", "defer this for later", "update task status", or wants
  to manage work items and dependencies.
allowed-tools: mcp__plugin_engram_core__session_start, mcp__plugin_engram_core__task_create, mcp__plugin_engram_core__task_update, mcp__plugin_engram_core__task_query
```

**Workflow (create):**
1. Gather task details: title, description, priority, tags
2. Check for blockers: if user mentions dependencies, resolve task IDs via `task_query`
3. Present task details + confirmation (durable severity)
4. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
5. Call `task_create(title, description, priority, tags, blocked_by=[...])` — single mutation
6. Report outcome with task_id

**Workflow (update):**
1. Resolve target task via `task_query` or user-provided task_id
2. Determine action: patch (edit fields, status transitions) / close (requires `terminal_status`: `done`|`cancelled`) / reopen
3. For close: pass `terminal_status` to `task_update`. If `cancelled`, require `reason` from user; if `done`, omit `reason` (server rejects if present)
4. Present change + confirmation (durable for patch, terminal for close)
5. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `task_update(task_id, action, ...)` — single mutation
7. Report outcome

**Dependency workflows:**
- **"Create task blocked by X":** Single mutation — resolve X via `task_query`, pass `blocked_by=[x_task_id]` to `task_create`
- **"Create task that blocks X":** Two-step — lazy bootstrap (Section 7.3) precedes step (1); (1) `task_create` the new task, (2) `task_update(x_task_id, action='patch', add_blocked_by=[new_task_id])`. Confirmation mentions non-atomicity. **Recovery if step 2 fails:** report the orphaned task (step 1 succeeded), present the task_id, and offer: retry step 2, manually add the dependency later, or delete the orphaned task.

**Design notes:**
- Subsumes the old `/defer` workflow — deferring work is just task creation with appropriate tags/context
- Read-before-write for all dependency changes: always query current state before mutation
- Direction disambiguation: "A blocks B" vs "A is blocked by B" — skill must clarify before writing

#### `/remember` — Lesson Capture

**Frontmatter:**
```yaml
name: remember
description: >
  Capture or maintain lessons in Engram. Use when the user says "remember
  this", "capture this insight", "this is worth noting", or wants to
  update, reinforce, or retract an existing lesson.
allowed-tools: mcp__plugin_engram_core__session_start, mcp__plugin_engram_core__lesson_capture, mcp__plugin_engram_core__lesson_update, mcp__plugin_engram_core__lesson_query
```

**Workflow (capture):**
1. Extract candidate insight from conversation or user input
2. Apply quality bar — 4 durability tests (examples-based, not scoring thresholds):
   - **Stability:** Will this still be true next week?
     - Pass: "FTS5 external content mode requires explicit sync triggers" (structural fact)
     - Fail: "The deploy pipeline is slow today" (transient observation)
   - **Reusability:** Does this apply beyond the current task?
     - Pass: "Preserving `reinforcement_count` on retraction provides useful signal for lesson quality analysis" (cross-task principle)
     - Fail: "We should use a 5-second timeout for this specific API call" (task-specific tuning)
   - **Decision value:** Would knowing this change a future decision?
     - Pass: "Session-scoped queries need a `session_id` filter parameter — without it, skills over-fetch" (informs API design)
     - Fail: "Python 3.12 is the latest version" (easily discoverable, doesn't change decisions)
   - **Self-contained:** Is the insight understandable without conversation context?
     - Pass: "Append-only semantics for `continued_from_session_ids` preserves session lineage history"
     - Fail: "That approach was better" (requires conversation context to interpret)
3. If quality bar not met, classify and redirect:
   - Sounds like a task → suggest `/task` instead
   - Sounds like session state → suggest `/save` instead
   - User override: proceed with explicit tradeoff communication ("This may not be durable enough to retrieve usefully later — capture anyway?")
4. Present insight + context + tags + confirmation (durable severity)
5. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `lesson_capture(insight, context, tags, ...)` — server handles dedup via `anchor_hash`
7. Report outcome — note if reinforced (existing lesson) vs created (new). If `details.context_conflict=true`, inform user that the existing lesson's context differs and offer to update via `lesson_update(action='patch')`

**Workflow (maintain — patch/reinforce/retract):**
1. Identify target lesson via `lesson_query` or user reference
2. Determine action using routing rule:
   - **reinforce** — "encountered this insight again in a new context" (optionally with new provenance via `add_sources`)
   - **patch** — "edit or enrich an existing lesson" (update context/tags and/or add provenance without implying re-encounter)
   - **retract** — "this lesson is wrong" (incorrect or obsolete)
3. For retraction: classify as `incorrect` or `obsolete`, gather reason from user/context
4. Present consequences + confirmation (terminal severity for retraction, durable for patch)
5. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `lesson_update(lesson_id, action='retract', reason_code=..., reason=...)` — single mutation. `reinforcement_count` is preserved as historical (not decremented).
7. Report outcome

**Design notes:**
- Redirect-not-refuse pattern: suggests the right tool rather than blocking
- `lesson_capture` dual-path is transparent to the user — server reports whether the lesson was created or reinforced
- Retraction and capture have different epistemic postures (additive vs adversarial-to-prior) — the confirmation severity difference (durable vs terminal) reflects this

#### `/promote` — Lesson Promotion

**Frontmatter:**
```yaml
name: promote
description: >
  Promote Engram lessons to permanent project documentation. Use when the
  user says "promote this to CLAUDE.md", "graduate this lesson", or wants
  to surface high-value lessons for promotion to documentation.
allowed-tools: mcp__plugin_engram_core__session_start, mcp__plugin_engram_core__lesson_query, mcp__plugin_engram_core__lesson_promote, Read, Edit
```

**Workflow:**
1. Surface promotion candidates: `lesson_query(status='active', promoted=0, sort_by='reinforcement_count_desc')`
2. Present candidates with insight, reinforcement count, and context
3. User selects lesson(s) to promote
4. For each selected lesson, determine target and route by capability:

| Target Type | Capability | Workflow |
|-------------|-----------|----------|
| Local editable file (e.g., `.claude/CLAUDE.md`) | Read + Edit | Read file → apply edit → verify edit → call `lesson_promote(lesson_id, target={type:'file', ref:path})` |
| External target (e.g., GitHub wiki, Notion) | Generate payload only | Generate content payload → present to user → user attests to manual application → call `lesson_promote(lesson_id, target={type:target_type, ref:target_ref})` |
| Unsupported target | None | Report unsupported, ask user to specify a different target |

5. Confirmation: durable severity for each promotion
6. Lazy bootstrap (Section 7.3): call `session_start(session_id=<session_id>)` to ensure active session
7. Report outcome — provenance recorded, destination updated (or attested)

**Design notes:**
- `lesson_promote` fires only **after** the destination is verifiably updated (local files) or user-attested (external targets). Provenance records truth, not intent.
- Routes by target capability, not by flag — removed the `--record-only` concept from the prior dialogue
- Needs `Read` and `Edit` in `allowed-tools` because local-file promotion requires reading and editing the destination
- Editorial judgment (e.g., where in CLAUDE.md to place the promoted content, how to phrase it) remains skill-level judgment — the MCP tool only records provenance

**Recovery for partial failure (local-file promotion):**
The local-file workflow is non-atomic: the first operation edits the destination, the second calls `lesson_promote` to record provenance. If `lesson_promote` fails after the edit succeeds, the destination has the content but Engram has no provenance record. Recovery:
1. Report: "Content was applied to {destination} but provenance recording failed"
2. Present the lesson_id and destination path
3. Offer: retry `lesson_promote` (idempotent — safe to retry), or accept the edit without provenance (lesson remains marked `promoted=0`, may appear as a candidate again)

### 7.5 Skill Directory Layout

```
engram/
├── skills/
│   ├── save/
│   │   └── SKILL.md
│   ├── load/
│   │   └── SKILL.md
│   ├── triage/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── triage-modes.md          # Detailed mode trigger rules
│   ├── task/
│   │   └── SKILL.md
│   ├── remember/
│   │   └── SKILL.md
│   └── promote/
│       ├── SKILL.md
│       └── references/
│           └── target-profiles.md       # Target-type routing rules
└── references/
    ├── mutation-confirmation.md          # Shared confirmation UX contract
    ├── snapshot-schema.md               # Snapshot content schema (save→load)
    └── ref-normalization.md             # Ref object construction rules
```

**Layout rules:**
- Cross-skill contracts go in shared `references/` at plugin level
- Skill-specific reference material goes in skill-local `references/`
- `/task` and `/remember` are single-file skills in v1 (no supporting references)
- `/triage` and `/promote` have skill-local references for mode and target routing rules

### 7.6 `allowed-tools` and MCP Tool Naming

*Resolved: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`). Plugin name: `engram`, server name: `core`.*

All `allowed-tools` entries use the prefix `mcp__plugin_engram_core__`. This follows the Claude Code plugin naming convention: `mcp__plugin_<plugin-name>_<server-name>__<tool>`. Plugin name is `engram`; server name is `core` (single MCP server).

`allowed-tools` grants auto-approval, not exclusivity. If the prefix is wrong, Claude will still see the tools but will prompt for permission on each call. Getting the prefix right matters for UX, not for access control.

### 7.7 Open Questions (from dialogue)

1. ~~**`task_get` or `task_query(ids=[])`**~~ — **REOPENED (holistic review).** Added `task_ids[]` to `task_query` and `lesson_ids[]` to `lesson_query` for direct ID lookups. FTS alone cannot resolve task_ids for dependency workflows — UUIDs are not indexed in title/body/tags. `task_ids[]` enables programmatic lookups (skill has task_id from prior query) and the `/task` dependency resolution path. Cross-cutting `query` still not needed in `/task`'s `allowed-tools`.

2. ~~**`lesson_update(retract)` reason field**~~ — **CLOSED (adversarial review #9).** Added `reason_code` (enum: `incorrect`, `obsolete`) and `reason` (freeform) to `lesson_update(retract)` in Section 4. Added `retracted_at`, `retraction_code`, `retraction_reason` columns to Section 6. `reinforcement_count` preserved as historical on retraction.

3. **Lesson tag convention for `/triage`** — Should there be a formalized tag convention (e.g., `domain:*`, `type:*`) to improve `/triage` recommendation quality? Defer to implementation.

4. **`/promote` target profiles for non-CLAUDE.md files** — The local-file promotion workflow is designed for CLAUDE.md. Other documentation files (README, handbook) may need different editorial rules. Specify in `target-profiles.md` during implementation.

5. **`query` output field richness** — Whether the cross-cutting `query` tool's `SearchHit` type (Section 4) returns enough detail for all confirmation screens. If not, skills may need to follow up with native subsystem queries for enrichment.

---

## 8. Remaining Design Work

The following sections still need to be designed and approved:

- [x] Database schema (Codex dialogue #5 + deep review #6, 25 resolved items)
- [x] Skill surface (Codex dialogue #7 + #8, 6 skills; adversarial review #9, 13 findings applied; evaluative review #16 + collaborative resolution #17, identity/bootstrap amendments)
- [ ] Hook specifications — PreToolUse identity guard, SessionStart/Stop lifecycle telemetry
- [ ] Server-side validation rules — what each mutation tool validates
- [x] Tool naming — `mcp__plugin_engram_core__<tool>` (evaluative review #16, collaborative resolution #17)
- [ ] Plugin packaging — plugin.json, .mcp.json, directory structure
- [ ] Migration strategy — how to deprecate old plugins
- [ ] Testing strategy — what to test at each tier
