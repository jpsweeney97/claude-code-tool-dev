---
module: behavioral-semantics
legacy_sections: ["6.6"]
authority: contracts
normative: true
status: active
---

## Behavioral Semantics

**`anchor_hash` dedup and merge:** {#anchor-hash-merge} Server computes normalized hash of `insight` text — not a tool parameter. On `lesson_capture`, checks for existing active lesson with same `anchor_hash`. No match → create new lesson (`outcome='created'`). Match → merge (`outcome='reinforced'`): increment `reinforcement_count`, then apply field-specific merge semantics:

- **`context`:** Omitted or null → preserve existing. Present and identical → preserve, no conflict. Present and different → preserve existing, return `details.context_conflict=true`. The skill (not server) decides whether to follow up with `lesson_update(action='patch')`.
- **`tags`:** Omitted or null → preserve existing. Present → replace existing (deduplicated). Tags are categorical metadata — replacement during merge is safe, unlike freeform context.
- **`sources`, `external_refs`, `derived_from_task_ids`:** Follow standard append path during merge. Server writes provenance_links/entity_derivations rows; UNIQUE constraints deduplicate. New unique refs are appended to the existing lesson's provenance.

This preserves append-only knowledge semantics: the server never silently overwrites context. Retracted lessons are skipped during anchor_hash lookup — a new active lesson is created if the only match is retracted. NOT NULL enforced at schema level.

**`lesson_capture` dual-path:** {#lesson-capture-dual-path} Single tool handles both new lesson creation (no `anchor_hash` match) and reinforcement (match found → increment `reinforcement_count`, optionally update context/tags, `details.context_conflict` when provided context differs).

**`query` relevance_score:** {#query-relevance-score} The cross-cutting `query` tool returns `relevance_score` in each `SearchHit`. Raw FTS5 rank value (or monotonic transformation) — opaque higher-is-better float. Valid for within-query ordering only; not normalized across queries or comparable between different query strings.

**Provenance uniqueness:** {#provenance-uniqueness} `UNIQUE(entity_pk, relation_type, target_type, target_ref)` — `target_label` is excluded from uniqueness (presentation metadata, not identity). First-write-wins: duplicate inserts on the dedup key are silently ignored. Exception: existing rows with NULL `target_label` can be backfilled to non-NULL on subsequent writes (the one exception to first-write-wins — backfill from NULL only). Label on first write cannot be corrected without server-side migration (accepted for v1).

**`session_end` atomicity:** {#session-end-atomicity} When `final_content` is provided, server writes a `kind='final'` snapshot and sets `sessions.closed_at` and `sessions.updated_at` in one transaction. The partial unique index `idx_snapshots_final` enforces at most one final snapshot per session — if a final already exists, server rejects with `reason_code='conflict'` before hitting the constraint. When `final_content` is omitted, server sets `sessions.closed_at` and `sessions.updated_at` without creating a final snapshot.

**`session_get` as load API:** {#session-get-load-api} Returns session metadata plus `loadable_snapshot` (`Snapshot|null`): the `kind='final'` snapshot if present, else the latest `kind='checkpoint'` snapshot, else null (no snapshots). This is the primary entry point for the Context subsystem's restore-session use case.

**`task_update(close)` terminal status:** {#task-update-close-terminal-status} `action='close'` requires `terminal_status` (`done`|`cancelled`) — server rejects close without it. `reason` binding is server-side validation (not CHECK constraint): `cancelled` requires non-empty `reason`; `done` rejects `reason` if present (prevents semantic overloading — "done with a reason" is indistinguishable from "cancelled"). `reopen` clears both `closed_at` and `reason`. Server-side validation preferred over multi-column CHECK for v1 — the bidirectional `closed_at`/status CHECK (Section 6.3) handles the state invariant; `reason` binding is an input policy, not a schema constraint. Validation failures use `reason_code='policy_blocked'`: close without `terminal_status`, `done` with `reason` present, `cancelled` without `reason`, `patch` with `reason` or `terminal_status`. `reopen` on a non-terminal task returns `invalid_transition`.

**`session_list` ordering and `activity_at`:** {#session-list-ordering} `activity_at` is a computed field representing the most recent user-visible event on a session: the latest of `started_at`, `last_snapshot_at`, or `closed_at`. Computed at query time via grouped snapshot aggregate CTE — no schema change needed. `started_at` (NOT NULL) is the guaranteed floor: a session with no snapshots and not closed has `activity_at = started_at`. `session_list` orders by `(activity_at DESC, started_at DESC, session_id DESC)` — this deterministic sort tuple ensures cursor stability for pagination. The `state` filter (`all`|`open`|`closed`) applies server-side before `limit` — without server-side filtering, `limit=10` could return only closed sessions, pushing open ones off the first page. Note: `activity_at` tracks user-visible events only (start, snapshot, close); `sessions.updated_at` tracks all mutations including metadata patches. A `session_start` call that only updates `goal` bumps `updated_at` but not `activity_at`.
