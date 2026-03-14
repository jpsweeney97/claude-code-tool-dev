---
module: internal-architecture
legacy_sections: ["5"]
authority: root
normative: true
status: active
---

## Internal Architecture

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
