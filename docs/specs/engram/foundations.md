---
module: foundations
legacy_sections: ["1", "2"]
authority: root
normative: true
status: active
---

## System Overview

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
| **Hooks** | Identity validation + mutation enforcement | `PreToolUse` → validate session identity; lifecycle hooks TBD ([implementation/](implementation/)) |
| **MCP tools** | Atomic operations with server-side validation | `session_start`, `task_create`, `lesson_capture`, `query` |
| **SQLite** | Persistent storage | `.engram/engram.db` with WAL mode |

### Three Subsystems

**Context** — Captures and restores session state. The unit is a *snapshot*: structured session state that any future session can load. Sessions are first-class entities (opened explicitly via `session_start`, closed via `session_end`).

**Work** — Tracks tasks through a defined lifecycle. A work graph that Claude Code can read and write. Knows what's planned, in-progress, done, and cancelled. Dependency blocking is derived from the task graph, not stored as status.

**Knowledge** — Captures durable insights as *lessons*: structured knowledge with `insight` (one-liner), `context` (freeform), and `tags`. Retrievable via FTS5. Lessons that prove durable can be promoted (a derived database projection, not a separate workflow).

---

## Skills, MCP Tools, and the Judgment Split

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

### Read Tool Selection Policy {#read-tool-selection-policy}

The 4 read tools encode different retrieval contracts. Use the narrowest tool that fully expresses the request:

| Signal | Tool | Why |
|--------|------|-----|
| Entity type is tasks (explicit or inferable) | `task_query` | Supports `status[]`, `priority[]`, `blocked_by[]`, `is_blocked`, `has_dependents` — filters `query` cannot express |
| Entity type is lessons (explicit or inferable) | `lesson_query` | Supports `promoted`, `sort_by` (`reinforcement_count_desc`), lesson `status` — filters `query` cannot express |
| Session browsing or lifecycle filtering | `session_list` | Lifecycle `state` filter (`open`/`closed`/`all`), deterministic `activity_at` ordering — structurally different from text search |
| Entity type unknown, multiple types wanted, or time-bounded recall | `query` | Cross-cutting FTS with `entity_types[]` filter and `updated_after`/`updated_before` temporal range |

**Enrichment rule:** When `query` returns results that will materially inform a response about tasks or lessons, follow with the matching native tool (`task_query` or `lesson_query`) using `task_ids[]`/`lesson_ids[]` for batch lookup. `SearchHit` fields (`entity_type`, `entity_id`, `title`, `snippet`, `tags`, `relevance_score`) are intentionally thin — native result types carry status, priority, dependencies, reinforcement counts, and promotion state.

**Non-goal:** `query` does not subsume `task_query`, `lesson_query`, or `session_list`. These tools have domain-specific filter parameters, return types, and ordering semantics that a single unified tool would push into parameter accretion. The unified search experience is provided by skills (especially `/triage`), not by tool surface unification. Skills orchestrate multiple read tools internally and present a unified interface to the user.

Tool descriptions must carry selection guidance so that direct callers (outside skill workflows) choose the right tool. Each read tool's description should state its domain and when to prefer it over `query`.
