---
module: decisions
legacy_sections: ["3"]
authority: root
normative: true
status: active
---

## Design Decisions

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

**Open risks:** (1) 13 tool descriptions cost an estimated 3k–8k tokens in context (~1.5–4% of 200k); Claude Code's Tool Search mitigates but the estimate is unverified. (2) ~~MCP server crash recovery is undocumented — if Claude Code does not auto-restart crashed servers, all Engram operations silently fail until next session.~~ **CLOSED (Codex consultation #25).** Skill-level behavior is covered by the Server Unavailable Escalation rule ([skill-orchestration.md](contracts/skill-orchestration.md#server-unavailable)): skills detect total unavailability via "primary call + verification read both fail," surface an explicit message, and stop. Automatic server restart is platform-dependent — Claude Code documents SSE auto-reconnection but not stdio auto-restart. SessionStart hook liveness checks were evaluated and rejected (hooks are command-only, cannot probe MCP tools).

### Rejected v1 Alternatives — Read Tool Surface

*Evaluated in Codex dialogue #24 (thread `019cecff`, collaborative, 6 turns). All rejected with reopen criteria.*

| Alternative | Proposed | Rejected Because | Reopen If |
|-------------|----------|-----------------|-----------|
| **Unified query tool** (fold `task_query`, `lesson_query`, `session_list` into `query`) | Dialogue #24 — motivated by "Engram is a unified system, multiple query tools fragment the experience" | Parameter accretion (~20 params, most irrelevant per call); polymorphic return types are a tax in FastMCP; `session_list` is lifecycle browsing with deterministic ordering, not text search; skills already provide unified UX via orchestration | Empirical evidence that Claude cannot reliably select between 4 read tools despite tool description guidance and foundations.md routing policy |
| **`include_summary` flag on `query`** | Dialogue #24, T2 — middle-ground: `query` optionally returns full entity summaries inline | Single-type-only has limited value; mixed-type requires server-side fan-out contradicting "dedicated FTS projection" decision (row above); enrichment round-trip is acceptable (3 calls for one skill/one mode, batchable via `*_ids[]`) | Enrichment latency becomes a measurable UX problem in practice |
| **Polymorphic return types** (`SearchHit \| TaskSummary \| LessonSummary`) | Dialogue #24, T1 — `query` returns domain-specific types based on `entity_types[]` filter | FastMCP tool response schema favors uniform types; polymorphic returns push type dispatch to the client; breaks the contract that `query` returns `SearchHit` | FastMCP gains native discriminated union support in tool response schemas |
