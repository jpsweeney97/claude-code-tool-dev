---
module: rationale
legacy_sections: ["6.6"]
authority: schema
normative: false
status: active
---

## Schema Rationale

*This document explains storage design choices. It is non-normative — observable behavior is defined in [contracts/behavioral-semantics.md](../contracts/behavioral-semantics.md).*

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

**Promotion model:** `lesson_promote` writes a `provenance_links` row with `relation_type='promoted_to'`, `target` Ref holding the destination, and sets `lessons.promoted = 1` as denormalized cache. Source of truth is the provenance_links row.

**Three-class relationship taxonomy:**
- **Canonical typed:** `session_links` (session continuation), `task_dependencies` (task DAG) — domain-specific semantics, real FKs
- **Internal lineage:** `entity_derivations` — cross-subsystem derivation (lesson from task, task from lesson) with real FKs + CASCADE. Intentionally generic: source kind recoverable from `entities.kind` JOIN; no `relation_type` column needed.
- **External provenance:** `provenance_links` — structured Ref objects (type, ref, label) as external references + promotion targets, append-only

**`session_links` directionality:** `from_session_pk` = prior session, `to_session_pk` = new session. Chronological — edges flow forward in time. `is_primary` marks the main continuation chain.

**Cross-subsystem FK coupling:** `tasks.session_pk` and `lessons.session_pk` reference `sessions(entity_pk)` directly — work→context and knowledge→context coupling at the schema level. This is intentional attribution. `server.py` resolves `session_pk` before calling subsystem modules, so work/ and knowledge/ never query context/ directly. The Python import rule ("subsystems must not import each other") is preserved.

**Task dependency write paths:** `task_create` accepts `blocked_by[]` (initial dependencies). `task_update` accepts `add_blocked_by[]` and `remove_blocked_by[]`. Server writes/deletes `task_dependencies` rows. `blocks[]`, `is_blocked`, and `has_dependents` are derived at query time from reverse joins on `task_dependencies`. `idx_deps_depends_on` supports reverse lookups.

**Tool parameter → table mapping:**
- `sources`, `external_refs`, `add_sources`, `add_external_refs` → `provenance_links` rows (Ref objects → relation_type, target_type, target_ref, target_label)
- `derived_from_task_ids`, `derived_from_lesson_ids`, `add_derived_from_task_ids`, `add_derived_from_lesson_ids` → `entity_derivations` rows
- `continued_from_session_ids` → `session_links` rows
- `blocked_by[]` → `task_dependencies` rows

**Deferred for v1:** `durability`, `evidence`, `conditions`, `supersedes`, `contradicts` columns on lessons (no v1 tool writes or reads them). DAG cycle detection in `task_dependencies`. `lesson status = 'superseded'` (requires explicit supersession links). Session deletion. Structured retraction evidence (counter-evidence via distinct `relation_type` in `provenance_links`) — `relation_type` is open TEXT to enable future extension.

**`sessions.updated_at`:** Internal-only column — server sets on every session mutation (field patches via `session_start`, `session_end`). `session_snapshot` also updates `sessions.updated_at` as a cross-table side-effect (UPDATE on sessions row in the same transaction as the snapshots INSERT). Not exposed in S4 public types (SessionSummary, SessionDetail). Public freshness signals are `activity_at`, `last_snapshot_at`, and `closed_at`. Used for internal query filtering, time-range queries, and operational diagnostics.

**Final snapshot uniqueness:** `idx_snapshots_final` is a partial unique index enforcing at most one `kind='final'` snapshot per session at the schema level. Defense-in-depth — server validates before INSERT.

**Migration strategy:** Forward-only numbered SQL files. Pre-migration backup of `.engram/engram.db` once holding real data. `schema_version` table tracks applied versions.
