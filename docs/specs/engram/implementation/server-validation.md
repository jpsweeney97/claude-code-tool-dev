---
module: server-validation
legacy_sections: ["8"]
authority: implementation
normative: false
status: active
---

# Server Validation

> **Authority:** Implementation. This document describes *how* the MCP server enforces rules defined in [tool-surface.md](../contracts/tool-surface.md) and [behavioral-semantics.md](../contracts/behavioral-semantics.md). It must not change public behavior — all observable semantics are normative in contracts.

## Scope and Boundary {#scope}

Server validation is the second layer of the three-layer enforcement stack ([tool-surface.md](../contracts/tool-surface.md) — Session Bootstrap):

| Layer | What it checks | Stateful? |
|-------|---------------|-----------|
| PreToolUse hook | Identity: `tool_input.session_id` == Claude Code session UUID | No |
| **MCP server** | **Session existence, lifecycle state, constraint satisfaction** | **Yes — reads/writes SQLite** |
| Skills | Intent: should this mutation happen? | No — prompt-based judgment |

This document covers:

- **Validation pipeline** — the ordered phases every mutation traverses
- **Common normalizers** — shared algorithms (anchor_hash, tags, semantic dedup, three-state resolution)
- **Per-tool validation** — what each tool checks at each pipeline phase
- **Enforcement ownership** — which enforcement layer owns each rule, and where schema provides a backstop
- **Error transport** — how determinate rejections, lookup failures, and internal errors reach the caller

This document does NOT cover:

- Tool parameters, envelopes, or action semantics — see [tool-surface.md](../contracts/tool-surface.md)
- Merge semantics, atomicity guarantees, or ordering contracts — see [behavioral-semantics.md](../contracts/behavioral-semantics.md)
- Schema design or column rationale — see [ddl.md](../schema/ddl.md) and [rationale.md](../schema/rationale.md)
- Hook enforcement — see [hooks.md](hooks.md)

---

## Terminology {#terminology}

| Term | Definition |
|------|-----------|
| **Write-plan** | The computed mutation delta — what the server will change if validation passes. Comparing the write-plan against persisted state enables semantic no-op detection, closed-session guards, and atomic rejection guarantees |
| **Semantic no-op** | A mutation whose write-plan produces zero persisted value changes AND zero new rows in relationship tables ([tool-surface.md](../contracts/tool-surface.md)). Label backfills count as persisted value changes. Allowed on closed sessions; the response reflects persisted state unchanged |
| **Lookup failure** | An entity ID that does not resolve to a row. Outside the 5-code reason taxonomy — surfaced as non-envelope RPC errors (see [Error Transport](#error-transport)) |
| **DB backstop** | A schema constraint (CHECK, UNIQUE, partial index) that enforces an invariant already validated by server logic. Defense-in-depth — the constraint catches bugs in server code, not expected user errors |
| **Three-state** | A field value that can be *omitted* (preserve existing), *explicit null* (clear to NULL), or *present* (replace/append). Requires raw transport inspection — Python default parameters collapse omitted and null |
| **Persistence normalization** | Transforming a value before storage (e.g., tag dedup, whitespace collapse). Changes what is persisted |
| **Comparison normalization** | Transforming a value for equality testing without changing what is stored (e.g., anchor_hash computation). The original value is preserved |

---

## Enforcement Ownership Crosswalk {#crosswalk}

Every validation rule below is authored in a normative contracts or schema document. This crosswalk maps each rule to its primary runtime enforcer and the role of the database schema.

| Rule | Authored In | Primary Runtime Enforcer | DB Role | Notes |
|------|------------|-------------------------|---------|-------|
| Identity match (session_id) | tool-surface.md | PreToolUse hook | None | Stateless — hook compares two UUIDs |
| Session existence (mutations) | tool-surface.md | Server (phase 3) | FK + UNIQUE on `sessions.session_id` | Server rejects before FK would |
| Session open (mutations) | tool-surface.md | Server (phase 4) | None | Checks `closed_at IS NULL`. Reason code varies: `session_end` → `invalid_transition`; `session_start` → deferred no-op check; all others → `policy_blocked` |
| Closed-session no-op exception | tool-surface.md | Server write-plan (phase 5) | None | Zero-delta write-plan = allowed |
| Empty string rejection | tool-surface.md | Server (phase 2) | None | `""` → `policy_blocked` on all scalars |
| Self-link rejection | tool-surface.md | Server (phase 3) | None | `continued_from` must not contain own session_id |
| `session_start` idempotency | tool-surface.md | Server write-plan (phase 5) | None | Field-specific patch semantics |
| Final snapshot uniqueness | behavioral-semantics.md | Server (phase 4) | Partial UNIQUE backstop (`idx_snapshots_final`) | Server checks before INSERT |
| `anchor_hash` dedup/merge | behavioral-semantics.md | Server (phase 5) | Index only (`idx_lessons_anchor`) | Server queries index, decides create vs merge |
| Provenance uniqueness | behavioral-semantics.md | Server (phase 5, two-stage dedup) | UNIQUE backstop | Server decides insert/noop/label-backfill; `INSERT OR IGNORE` is defense-in-depth |
| `closed_at`/status invariant | ddl.md | Server write logic, satisfied by construction | CHECK backstop | Server always sets both atomically |
| Task `reason`/`terminal_status` binding | behavioral-semantics.md | Server (phase 4) | None | `cancelled` requires reason; `done` forbids it |
| Task self-dependency | ddl.md | CHECK constraint | CHECK enforcer | `CHECK (task_pk != depends_on_pk)` |
| `session_end` atomicity | behavioral-semantics.md | Server (phase 6, transaction) | Partial UNIQUE backstop | Final snapshot + close in one transaction |
| Entity kind integrity | rationale.md | Server (same-transaction write) | None (startup verifier) | Kernel creates entity + domain row atomically |
| Search projection coupling | rationale.md | Server (phase 6, same transaction) | FTS5 triggers | Projection update in mutation transaction |
| `dependency_blocked` | tool-surface.md | Reserved — not emitted in v1 | None | Taxonomy placeholder |

---

## Shared Validation Pipeline {#pipeline}

Every mutation tool traverses a 7-phase pipeline. Phases are ordered — later phases consume earlier phase outputs, never re-read raw input. Rejection is deterministic: the earliest failing phase produces the error; later phases are not evaluated.

| Phase | Name | Produces | Can Reject? |
|-------|------|----------|-------------|
| 1 | Transport parse | `typed_input`, `raw_keys` (set of present key names) | Yes — malformed input |
| 2 | Common policy | `validated_input` | Yes — `policy_blocked` |
| 3 | Session/target resolution | `session_pk`, target entity PKs, lifecycle state | Yes — lookup failure, `policy_blocked` |
| 4 | Lifecycle/state checks | `lifecycle_ok`, applicable action path | Yes — `invalid_transition`, `conflict`, `policy_blocked` |
| 5 | Semantic dedup / write-plan | `write_plan` (delta), `is_noop` | Yes — `policy_blocked` (empty patch) |
| 6 | Transactional write | Committed entities, timestamps | No — internal errors abort |
| 7 | Response assembly | Entity envelope | No |

### Phase 1: Transport Parse

Parse raw MCP input into typed Python objects. Resolve three-state semantics for patch-capable tools.

**Three-state resolution:** Standard FastMCP typed parameters collapse omitted and null. To distinguish them, the server reads `ctx.request_context.request.params.arguments` for raw key presence:

```python
raw_args = ctx.request_context.request.params.arguments or {}
raw_keys = set(raw_args.keys())

# Three-state resolution for a field:
# - key not in raw_keys → OMITTED (preserve existing)
# - key in raw_keys and value is None → EXPLICIT NULL (clear to NULL)
# - key in raw_keys and value is not None → PRESENT (replace/append)
```

Three-state input discrimination is needed for: `session_start` (goal, branch, context_summary, tags, continued_from_session_ids, external_refs) and `task_update(action='patch')` (title, description, priority, tags, status). Other tools use standard two-state semantics (present or absent).

For `session_start` append-only relations (`continued_from_session_ids`, `external_refs`), three-state input discrimination detects explicit null (which phase 2 rejects with `policy_blocked`) vs omitted (which preserves existing). The `resolve_three_state()` function in the normalizers section applies only to scalar and tags fields — append-only relations use a different code path that routes explicit null to phase 2 rejection rather than clearing.

### Phase 2: Common Policy

Apply universal validation rules that are independent of entity state:

1. **Empty string rejection:** For every scalar string field in `typed_input`, reject `""` with `reason_code='policy_blocked'`. Use explicit null to clear. ([tool-surface.md](../contracts/tool-surface.md), empty string rule)
2. **Enum validation:** Reject unknown values for `action`, `status`, `priority`, `terminal_status`, `kind`, `reason_code` (retraction), `sort_by`. Use `policy_blocked`.
3. **Required field check:** Reject missing required fields (e.g., `task_create.title`, `lesson_capture.insight`, `task_update.action`). Use `policy_blocked`.
4. **Mutual exclusion:** Reject fields that are invalid for the given action (e.g., `task_update(action='patch')` with `reason` or `terminal_status`). Use `policy_blocked`. Per-tool tables specify which fields each action accepts and rejects.

### Phase 3: Session/Target Resolution

Resolve public IDs to internal PKs. All lookups use indexed columns.

**Session resolution** (all mutation tools):

```
session_pk = lookup(sessions, session_id=typed_input.session_id)
```

- `session_start` when session does not exist: create path (no resolution needed, session_pk allocated in phase 6)
- `session_start` when session exists: enrich path (session_pk resolved)
- All other mutations: session must exist. Lookup failure → non-envelope RPC error (see [Error Transport](#error-transport))

**Target resolution** (update tools):

```
task_pk    = lookup(tasks, task_id=typed_input.task_id)        # task_update
lesson_pk  = lookup(lessons, lesson_id=typed_input.lesson_id)  # lesson_update, lesson_promote
```

Lookup failure → non-envelope RPC error.

**Relationship resolution** (create/update tools with references):

```
blocked_by_pks       = [lookup(tasks, task_id=id) for id in typed_input.blocked_by]
derived_from_pks     = [lookup(entities, ...) for id in typed_input.derived_from_*_ids]
continued_from_pks   = [lookup(sessions, session_id=id) for id in typed_input.continued_from_session_ids]
```

Unknown relationship target → non-envelope RPC error. `server.py` resolves all PKs before passing to subsystem modules — subsystem modules never query other subsystems directly ([internal-architecture.md](../internal-architecture.md)).

**Self-link check:** After resolving `continued_from_session_ids`, reject if any resolved PK equals the current session's PK. Use `policy_blocked`.

### Phase 4: Lifecycle/State Checks

Verify that the entity's current state permits the requested mutation.

**Session lifecycle** (all mutations except `session_start` create path):

| Current State | Mutation | Result |
|--------------|----------|--------|
| Open (`closed_at IS NULL`) | Any mutation | Proceed to phase 5 |
| Closed (`closed_at IS NOT NULL`) | `session_start` (enrich) | Proceed to phase 5 (write-plan will determine if no-op) |
| Closed | `session_end` | Reject: `invalid_transition` |
| Closed | All other mutations | Reject: `policy_blocked` |

**Closed-session no-op exception** (session_start enrich on closed session): Phase 5 computes the write-plan. If the write-plan is a semantic no-op (zero persisted value changes AND zero new rows in relationship tables), the mutation is allowed and returns the existing session unchanged. If the write-plan has any delta, reject with `policy_blocked`. ([tool-surface.md](../contracts/tool-surface.md), update guards)

**Task lifecycle:**

| Current Status | Action | Result |
|---------------|--------|--------|
| `open` / `in_progress` | `patch` | Allowed — status transitions within {open, in_progress} only |
| `open` / `in_progress` | `close` | Allowed — sets terminal status |
| `open` / `in_progress` | `reopen` | Reject: `invalid_transition` (already non-terminal) |
| `done` / `cancelled` | `patch` | Reject: `policy_blocked` (task is closed) |
| `done` / `cancelled` | `close` | Reject: `invalid_transition` (already terminal) |
| `done` / `cancelled` | `reopen` | Allowed — sets status to `open` |

**Task close validation** ([behavioral-semantics.md](../contracts/behavioral-semantics.md#task-update-close-terminal-status)):

| `terminal_status` | `reason` | Result |
|-------------------|----------|--------|
| `done` | absent | Allowed |
| `done` | present | Reject: `policy_blocked` |
| `cancelled` | present and non-empty | Allowed |
| `cancelled` | absent or empty | Reject: `policy_blocked` |

**Lesson lifecycle:**

| Current Status | Action | Result |
|---------------|--------|--------|
| `active` | `patch` / `retract` / `reinforce` | Allowed |
| `retracted` | `reinforce` | Reject: `invalid_transition` — use `lesson_capture` to create new active lesson |
| `retracted` | `patch` | Reject: `policy_blocked` |
| `retracted` | `retract` | Reject: `invalid_transition` (already retracted) |

**Promoting retracted lessons:** Whether `lesson_promote` should accept retracted lessons is an open contracts question — [tool-surface.md](../contracts/tool-surface.md) does not specify behavior for this case. This document cannot assign observable behavior; a contracts amendment is needed. Until then, implementors should choose a consistent behavior and document it as implementation-specific. See [Open Questions](#open-questions) item 2.

**Final snapshot guard:**

- `session_snapshot` with `kind='final'`: reject with `policy_blocked`. Final snapshots are created exclusively via `session_end` with `final_content` ([behavioral-semantics.md](../contracts/behavioral-semantics.md#session-end-atomicity))
- `session_end` with `final_content` when a final snapshot already exists: reject with `conflict`

### Phase 5: Semantic Dedup / Write-Plan {#write-plan}

Compute the mutation delta before applying. The write-plan is the central abstraction — it determines what rows to insert/update, enables semantic no-op detection, and feeds the transactional write.

**Syntactic vs semantic empty patch:** A *syntactic* empty patch is a request with no patchable fields or provenance params supplied — rejected at phase 2 (e.g., `lesson_update(action='patch')` with no fields) or phase 5 (e.g., `task_update(action='patch')` after three-state resolution). A *semantic* no-op is a request where parameters were supplied but the write-plan produces zero delta against persisted state (e.g., setting `goal` to its current value). Semantic no-ops are success, not errors — the response reflects persisted state unchanged.

**Tags normalization** (persistence normalization):
1. If input is a JSON array of strings: deduplicate (preserve first occurrence order), strip whitespace from each tag
2. If result is empty array after dedup: store as NULL (empty tags = no tags)
3. Serialize as JSON array for storage in the `tags` column

**Tags in anchor_hash context:** Tags are *not* included in anchor_hash computation. Tags are categorical metadata that can change between reinforcements. The hash captures semantic identity (insight text), not metadata.

**Two-stage semantic dedup** (for all append-only relations):

Stage 1 — Normalize within input:
```
input_refs = deduplicate(typed_input.sources, key=(relation_type, target_type, target_ref))
```

Stage 2 — Filter against persisted state:
```
existing = query(provenance_links, entity_pk=target_pk, relation_type=rel_type)
new_refs = [r for r in input_refs if (r.target_type, r.target_ref) not in existing_keys]
```

The write-plan includes only `new_refs`. This applies to: `sources`, `external_refs`, `add_sources`, `add_external_refs`, `continued_from_session_ids`, `blocked_by` (task_create), `add_blocked_by` (task_update), `derived_from_*_ids`, `add_derived_from_*_ids`.

**NULL-label backfill exception:** An existing row with NULL `target_label` and a new input with non-NULL `label` for the same dedup key is NOT a no-op. The write-plan includes a label UPDATE for that row. This is the one exception to first-write-wins for provenance ([behavioral-semantics.md](../contracts/behavioral-semantics.md#provenance-uniqueness)).

**Write-plan composition:** After normalization and dedup, the write-plan is a structured delta:

```python
@dataclass
class WritePlan:
    scalar_updates: dict[str, Any]     # column → new value (only changed fields)
    new_rows: list[RowInsert]          # relationship/provenance rows to INSERT
    label_backfills: list[LabelUpdate] # provenance label updates (NULL → non-NULL)
    is_noop: bool                      # True if all three lists are empty
```

**Semantic no-op detection:** `write_plan.is_noop` is True when all three components are empty — zero persisted value changes (including label backfills) AND zero new relationship rows. This matches the two-condition definition in [tool-surface.md](../contracts/tool-surface.md): "zero persisted value changes AND zero new rows in relationship tables." Label backfills are persisted value changes, not a third independent condition. Used by:
- Closed-session `session_start` guard (phase 4 deferred check)
- Provenance re-submission (idempotent success, not `duplicate`)

### Phase 6: Transactional Write

Apply the write-plan within a single SQLite transaction. All writes in this phase are atomic — if any step fails, the entire transaction rolls back and an internal error is returned.

**Write order within transaction:**
1. Entity row creation (if new entity): `INSERT INTO entities (kind)` → `entity_pk`
2. Domain table write: INSERT or UPDATE on `sessions`/`tasks`/`lessons`/`snapshots`
3. Relationship tables: `session_links`, `task_dependencies`, `entity_derivations`
4. Provenance: `INSERT OR IGNORE INTO provenance_links` (UNIQUE constraint handles dedup), label backfills
5. Search projection: `kernel/search.py` writes/updates `search_projection` row with data from domain table
6. Timestamp updates: `updated_at` on the target entity's domain row; `sessions.updated_at` for cross-table side-effects (e.g., `session_snapshot` updates the session row)

**Search projection coupling:** The search projection update is in the same transaction as the domain write. This is honest coupling for v1 — single-user SQLite with same-transaction writes. `rebuild_search()` provides repair if the projection drifts ([rationale.md](../schema/rationale.md)).

**`anchor_hash` active duplicate invariant:** If the server finds more than one active lesson with the same `anchor_hash`, this is an invariant breach — it should never happen under correct server logic. The server aborts with a JSON-RPC internal error (`-32603`), not a reason_code. This is a bug signal, not a user-facing rejection.

### Phase 7: Response Assembly

Build the entity envelope from committed state.

```json
{
  "outcome": "created|updated|reinforced|retracted|reopened|promoted|closed",
  "reason_code": null,
  "entity": { ... },
  "details": { ... },
  "warnings": []
}
```

For semantic no-ops (write-plan with zero delta on existing entities): `outcome` reflects the existing state, `reason_code` is null, `entity` reflects persisted state. The response is success — no-ops are not errors.

---

## Common Normalizers {#normalizers}

### `anchor_hash` Computation {#anchor-hash}

Server-computed comparison normalization for `lesson_capture` dedup. The hash captures semantic identity of the `insight` text — two insights that differ only in formatting should merge.

**Algorithm:**

```
1. NFKC normalize (Unicode canonical decomposition + compatibility composition)
2. Normalize line endings: CRLF → LF, CR → LF
3. Trim leading and trailing whitespace
4. Strip one leading presentation prefix: /^[-*>]\s+/ or /^\d+\.\s+/
5. Unwrap one whole-string formatting pair: **…**, *…*, `…`, _…_
6. Collapse internal whitespace: runs of spaces/tabs → single space
7. SHA-256 hash → hex digest
8. Prefix: "v1:" + hex digest
```

**Case-preserving:** No casefold. Case carries semantic meaning for identifiers, environment variables, and filenames (`API_KEY` ≠ `api_key`). False-positive merges (incorrectly combining distinct insights) are worse than false-negative duplicates (failing to merge identical insights).

**Versioned prefix:** The `v1:` prefix enables future algorithm changes without invalidating existing hashes. A migration can recompute hashes with a `v2:` prefix while preserving `v1:` hashes for comparison during transition.

**What is NOT normalized:** Punctuation (semantic in code), case (semantic for identifiers), stemming (changes meaning), markdown structure beyond presentation prefix/formatting pairs (intentional formatting).

### Three-State Field Resolution {#three-state}

Used by `session_start` and `task_update(action='patch')` for patch-capable fields.

```python
def resolve_three_state(field_name: str, raw_keys: set[str], typed_value: Any, existing_value: Any) -> Any:
    """Returns the value to persist.

    - field_name not in raw_keys → preserve existing (OMITTED)
    - field_name in raw_keys and typed_value is None → NULL (EXPLICIT NULL)
    - field_name in raw_keys and typed_value is not None → typed_value (PRESENT)
    """
    if field_name not in raw_keys:
        return existing_value  # OMITTED — no change
    if typed_value is None:
        return None            # EXPLICIT NULL — clear
    return typed_value         # PRESENT — replace
```

The `resolve_three_state()` function above applies to scalar and tags fields only — it returns the value to persist (existing, NULL, or new). Append-only relations (`continued_from_session_ids`, `external_refs`) require three-state *input discrimination* (to detect explicit null for phase 2 rejection) but use a different write path: omitted = no-op, explicit null = reject (`policy_blocked`), present = append via two-stage semantic dedup. Standard `add_*` params on update tools use two-state: absent = no-op, present = append.

### Semantic Dedup {#semantic-dedup}

Two-stage dedup for all append-only relations. See [Phase 5](#write-plan) for the algorithm.

Applies to these parameter → table mappings:

| Parameter | Table | Dedup Key |
|-----------|-------|-----------|
| `sources`, `add_sources` | `provenance_links` | `(entity_pk, 'source', target_type, target_ref)` |
| `external_refs`, `add_external_refs` | `provenance_links` | `(entity_pk, 'external_ref', target_type, target_ref)` |
| `continued_from_session_ids` | `session_links` | `(from_session_pk, to_session_pk)` |
| `blocked_by`, `add_blocked_by` | `task_dependencies` | `(task_pk, depends_on_pk)` |
| `derived_from_task_ids`, `add_derived_from_task_ids` | `entity_derivations` | `(entity_pk, source_entity_pk)` |
| `derived_from_lesson_ids`, `add_derived_from_lesson_ids` | `entity_derivations` | `(entity_pk, source_entity_pk)` |
| `lesson_promote` `target` | `provenance_links` | `(entity_pk, 'promoted_to', target_type, target_ref)` |

---

## Mutation Tools {#mutations}

Per-tool validation tables. Columns describe what happens at each pipeline phase. Simple tools have a single table; branching tools (action-dispatched or server-determined codepath) have a parent table plus sub-tables.

### `session_start` {#session-start-validation}

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 1 | Three-state resolution for: goal, branch, context_summary, tags, continued_from_session_ids, external_refs | — | `session_id` is always required (two-state) |
| 2 | Empty string rejection on scalar fields (goal, branch, context_summary). Explicit null on `continued_from_session_ids` or `external_refs` → `policy_blocked` | `policy_blocked` | Append-only relations cannot be cleared |
| 3 | Lookup `session_id` → `session_pk`. Not found = create path. Self-link check on `continued_from_session_ids` | `policy_blocked` (self-link) | Create path skips phases 4-5 session checks |
| 4 | If session exists and closed → defer to phase 5 no-op check. If session exists and open → proceed | `policy_blocked` (closed + non-noop) | |
| 5 | Compute write-plan with field-specific patch semantics ([tool-surface.md](../contracts/tool-surface.md)). Two-stage dedup on continued_from and external_refs. First distinct continuation link gets `is_primary=true` | — | |
| 6 | Create or update session + entities + session_links + provenance_links + search_projection | — | |
| 7 | Entity envelope with `details.created` (boolean) | — | `outcome`: `created` (new) or `updated` (enriched) |

### `session_snapshot` {#session-snapshot-validation}

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 1 | `content` required. `kind` defaults to `checkpoint`. `external_refs` optional | — | |
| 2 | `kind='final'` → reject. Finals are created exclusively via `session_end` | `policy_blocked` | |
| 3 | Resolve `session_pk` | lookup failure | |
| 4 | Session must be open | `policy_blocked` | |
| 5 | Two-stage dedup on external_refs. Write-plan: snapshot row + provenance | — | |
| 6 | Create entities + snapshot row + provenance_links. Update `sessions.updated_at` (cross-table side-effect) | — | |
| 7 | Entity envelope. `outcome`: `created` | — | |

### `session_end` {#session-end-validation}

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 1 | `summary` optional. `final_content` optional | — | |
| 2 | Empty string rejection on `summary` (scalar). `final_content` is not subject to empty-string rejection (content, not metadata) | `policy_blocked` | Universal empty-string rule applies |
| 3 | Resolve `session_pk` | lookup failure | |
| 4 | Session must be open. If closed → `invalid_transition`. If `final_content` provided, check `idx_snapshots_final` — existing final → `conflict` | `invalid_transition`, `conflict` | |
| 5 | Write-plan: set `closed_at`, `updated_at`, optional `summary`. If `final_content`: create final snapshot | — | |
| 6 | Atomic transaction: create final snapshot (if `final_content`) + close session. `session_end` atomicity guarantee ([behavioral-semantics.md](../contracts/behavioral-semantics.md#session-end-atomicity)) | — | |
| 7 | Entity envelope. `outcome`: `closed` | — | |

### `task_create` {#task-create-validation}

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 1 | `title` required. `priority` defaults to `medium`. `status` defaults to `open` | — | |
| 2 | Empty string rejection on `title`, `description`. Enum validation: `priority`. Note: `status` is not a documented `task_create` parameter in [tool-surface.md](../contracts/tool-surface.md) — if accepted, only `open` is valid (implementation inference; consider contracts amendment) | `policy_blocked` | |
| 3 | Resolve `session_pk`. Resolve `blocked_by[]` → task PKs. Resolve `derived_from_lesson_ids` → entity PKs | lookup failure | v1 allows dependencies on terminal tasks |
| 4 | Session must be open | `policy_blocked` | |
| 5 | Normalize tags. Two-stage dedup on sources, external_refs, blocked_by, derived_from_lesson_ids | — | |
| 6 | Create entities + task + task_dependencies + provenance_links + entity_derivations + search_projection | — | Server generates `task_id` (UUID) |
| 7 | Entity envelope. `outcome`: `created` | — | |

### `task_update` {#task-update-validation}

**Parent validation** (all actions):

| Phase | Validation | Reason Code |
|-------|-----------|-------------|
| 1 | `task_id` required. `action` required: `patch` \| `close` \| `reopen` | — |
| 2 | Unknown `action` value → reject | `policy_blocked` |
| 3 | Resolve `session_pk` from `session_id`. Resolve `task_pk` from `task_id` | lookup failure |
| 4 | Caller's session must be open | `policy_blocked` |

**Sub-table: `patch`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 2 | Rejects `reason`, `terminal_status`. Empty string rejection on `title`, `description`. `status` enum: `open` \| `in_progress` only | `policy_blocked` | Terminal transitions require `close` |
| 4 | Task must be non-terminal (`open` or `in_progress`) | `policy_blocked` | |
| 5 | Three-state resolution for patchable fields. Two-stage dedup on `add_blocked_by`, `add_sources`, `add_external_refs`, `add_derived_from_lesson_ids`. Process `remove_blocked_by` (delete task_dependencies rows) | `policy_blocked` (empty patch — no fields or provenance) | |
| 6 | Update task row + relationships + provenance + search_projection | — | |
| 7 | Entity envelope. `outcome`: `updated` | — | |

**Sub-table: `close`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 2 | `terminal_status` required: `done` \| `cancelled`. `done` + `reason` present → reject. `cancelled` + `reason` absent/empty → reject | `policy_blocked` | [behavioral-semantics.md](../contracts/behavioral-semantics.md#task-update-close-terminal-status) |
| 4 | Task must be non-terminal | `invalid_transition` | |
| 5 | Write-plan: set `status`, `closed_at`, optional `reason` | — | |
| 6 | Update task row + search_projection. `closed_at`/status CHECK satisfied by construction | — | |
| 7 | Entity envelope. `outcome`: `closed` | — | |

**Sub-table: `reopen`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 4 | Task must be terminal (`done` or `cancelled`). Non-terminal → reject | `invalid_transition` | |
| 5 | Write-plan: set `status='open'`, clear `closed_at`, clear `reason` | — | |
| 6 | Update task row + search_projection | — | |
| 7 | Entity envelope. `outcome`: `reopened` | — | |

### `lesson_capture` {#lesson-capture-validation}

**Parent validation:**

| Phase | Validation | Reason Code |
|-------|-----------|-------------|
| 1 | `insight` required. `context`, `tags`, `sources`, `external_refs`, `derived_from_task_ids` optional | — |
| 2 | Empty string rejection on `insight`, `context` | `policy_blocked` |
| 3 | Resolve `session_pk`. Resolve `derived_from_task_ids` → entity PKs | lookup failure |
| 4 | Session must be open | `policy_blocked` |
| 5 | Compute `anchor_hash` from `insight` ([anchor_hash algorithm](#anchor-hash)). Query `lessons` for active lesson with matching hash (retracted lessons skipped) | — |

**Sub-table: create** (no `anchor_hash` match — server-determined codepath)

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 5 | No active match found. Normalize tags. Two-stage dedup on sources, external_refs, derived_from | — | |
| 6 | Create entities + lesson + provenance_links + entity_derivations + search_projection. Server generates `lesson_id` (UUID) | — | |
| 7 | Entity envelope. `outcome`: `created` | — | |

**Sub-table: merge** (active `anchor_hash` match found — server-determined codepath)

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 5 | Active match found. If >1 active match → invariant breach (abort with internal RPC error). Apply merge semantics ([behavioral-semantics.md](../contracts/behavioral-semantics.md#anchor-hash-merge)): increment `reinforcement_count`. **Context:** omitted/null → preserve existing; present and identical → preserve, no conflict; present and different → preserve existing, set `details.context_conflict=true`. **Tags:** omitted/null → preserve existing; present → replace existing (deduplicated). **Provenance:** append via two-stage dedup | — | |
| 6 | Update existing lesson row + append provenance + update search_projection | — | |
| 7 | Entity envelope. `outcome`: `reinforced`. `details.context_conflict`: boolean | — | |

### `lesson_update` {#lesson-update-validation}

**Parent validation** (all actions):

| Phase | Validation | Reason Code |
|-------|-----------|-------------|
| 1 | `lesson_id` required. `action` required: `patch` \| `retract` \| `reinforce` | — |
| 2 | Unknown `action` value → reject | `policy_blocked` |
| 3 | Resolve `session_pk` from `session_id`. Resolve `lesson_pk` from `lesson_id` | lookup failure |
| 4 | Caller's session must be open | `policy_blocked` |

**Sub-table: `patch`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 2 | At least one field (`context`, `tags`) or provenance param (`add_sources`, `add_external_refs`, `add_derived_from_task_ids`) required. Rejects `reason_code`, `reason` | `policy_blocked` | Empty patch is an error |
| 4 | Lesson must be active | `policy_blocked` | |
| 5 | Normalize tags. Two-stage dedup on provenance params. Compute write-plan | — | |
| 6 | Update lesson row + provenance + search_projection | — | |
| 7 | Entity envelope. `outcome`: `updated` | — | |

**Sub-table: `retract`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 2 | Rejects `context`, `tags`, and all `add_*` provenance params (`add_sources`, `add_external_refs`, `add_derived_from_task_ids`). Accepts `reason_code` (`incorrect` \| `obsolete`) and `reason` | `policy_blocked` | |
| 4 | Lesson must be active. Already retracted → reject | `invalid_transition` | |
| 5 | Write-plan: set `status='retracted'`, `retracted_at`, `retraction_code`, `retraction_reason` | — | |
| 6 | Update lesson row + search_projection | — | `reinforcement_count` preserved, not decremented |
| 7 | Entity envelope. `outcome`: `retracted` | — | |

**Sub-table: `reinforce`**

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 2 | Optionally accepts `add_sources`, `add_external_refs`, `add_derived_from_task_ids`. Rejects `context`, `tags` (use `patch` for field updates). All provenance params absent is valid — reinforce with no provenance increments `reinforcement_count` only | `policy_blocked` | |
| 4 | Lesson must be active. Retracted → reject — use `lesson_capture` for re-encountered retracted insights | `invalid_transition` | [tool-surface.md](../contracts/tool-surface.md) |
| 5 | Two-stage dedup on provenance params. Write-plan: increment `reinforcement_count` | — | |
| 6 | Update lesson row + provenance | — | |
| 7 | Entity envelope. `outcome`: `reinforced` | — | |

### `lesson_promote` {#lesson-promote-validation}

| Phase | Validation | Reason Code | Notes |
|-------|-----------|-------------|-------|
| 1 | `lesson_id` required. `target` required (Ref object: type, ref, label) | — | |
| 2 | Validate Ref structure: `type` and `ref` required, non-empty | `policy_blocked` | |
| 3 | Resolve `session_pk` from `session_id`. Resolve `lesson_pk` from `lesson_id` | lookup failure | |
| 4 | Caller's session must be open. Lesson must be active. Retracted → behavior unspecified in contracts (see [Open Questions](#open-questions) item 2) | `policy_blocked` (session), unspecified (retracted) | |
| 5 | Semantic dedup: check `provenance_links` for existing `promoted_to` row with same `(target_type, target_ref)`. If exists → idempotent success (no-op). NULL-label backfill exception applies | — | Re-promotion is idempotent, not `duplicate` |
| 6 | `INSERT OR IGNORE INTO provenance_links` with `relation_type='promoted_to'`. Set `lessons.promoted = 1` (denormalized cache). Update `lessons.updated_at`. Update search_projection | — | |
| 7 | Entity envelope. `outcome`: `promoted` | — | |

---

## Read Tools {#reads}

Read tools have minimal server validation — no session lifecycle checks, no identity enforcement, no mutation invariants. Coverage is limited to parameter validation, cursor handling, and lookup behavior.

### `session_get`

| Validation | Details |
|-----------|---------|
| `session_id` required | Lookup failure → non-envelope RPC error |
| Response | SessionDetail + `loadable_snapshot`: final if present, else latest checkpoint, else null |

### `session_list`

| Validation | Details |
|-----------|---------|
| `state` enum | `all` (default), `open`, `closed`. Invalid → `-32602` |
| `limit` | Positive integer. Invalid → `-32602` |
| `cursor` | Opaque string from prior response. Invalid/expired → `-32602` |
| Server-side filter | `state` filter applied before `limit` |
| Ordering | `(activity_at DESC, started_at DESC, session_id DESC)` — deterministic for cursor stability |

### `task_query`

| Validation | Details |
|-----------|---------|
| `status[]` enum | Each must be in {open, in_progress, done, cancelled}. Invalid → `-32602` |
| `priority[]` enum | Each must be in {low, medium, high, critical}. Invalid → `-32602` |
| `session_id` | If provided, resolves to `session_pk`. Lookup failure → empty results (not error) |
| Boolean filters | `is_blocked`, `has_dependents` — derived from `task_dependencies` joins |
| `limit`, `cursor` | Same as `session_list` |

### `lesson_query`

| Validation | Details |
|-----------|---------|
| `sort_by` enum | `created_at_desc` (default), `updated_at_desc`, `reinforcement_count_desc`. Invalid → `-32602` |
| `status` enum | `active`, `retracted`. Invalid → `-32602` |
| `session_id` | If provided, resolves to `session_pk`. Lookup failure → empty results |
| `limit`, `cursor` | Same as `session_list` |

### `query`

| Validation | Details |
|-----------|---------|
| `text` required | Non-empty string for FTS5 search. Empty → `-32602` |
| `entity_types[]` | Each must be in {session, task, lesson}. Invalid → `-32602` |
| `updated_after`, `updated_before` | ISO 8601 UTC strings. Invalid format → `-32602` |
| `limit`, `cursor` | Same as `session_list` |

---

## Error Transport and Rejection Precedence {#error-transport}

### Determinate Rejections

Mutations that fail validation return an entity envelope with `reason_code` set and no durable state changed (atomic rejection invariant — [tool-surface.md](../contracts/tool-surface.md)):

```json
{
  "outcome": null,
  "reason_code": "policy_blocked",
  "entity": null,
  "details": { "message": "cancelled requires non-empty reason" },
  "warnings": []
}
```

**Reason code distinction principle:** `invalid_transition` is reserved for lifecycle state machine violations — a requested state change that cannot occur from the entity's current state (e.g., reopen a non-terminal task, retract an already-retracted lesson, close an already-closed session). `policy_blocked` covers input policy violations — edits disallowed by immutability rules, mutual exclusion, or constraint policies (e.g., patching a terminal task, clearing append-only relations, empty strings).

The 5 reason codes and their usage:

| Code | Meaning | Typical Triggers |
|------|---------|-----------------|
| `invalid_transition` | Lifecycle state machine violation | `reopen` on non-terminal task, `reinforce` on retracted lesson, `session_end` on closed session |
| `policy_blocked` | Input policy violation | Empty string, mutual exclusion, closed-session mutation (non-noop), empty patch, clearing append-only relations |
| `conflict` | Concurrent or duplicate state | `session_end` with `final_content` when final already exists |
| `duplicate` | Not currently emitted | Reserved for future use |
| `dependency_blocked` | Not currently emitted | Reserved — likely assignment: task close when open dependents exist (requires contracts amendment) |

### Lookup Failures

Entity ID resolution failures (`session_id`, `task_id`, `lesson_id` not found) are outside the 5-code reason taxonomy. The current taxonomy describes *what went wrong with a valid request*, not *why the request couldn't be routed*.

Provisional behavior: non-envelope JSON-RPC error with code `-32602` (invalid params) and structured data:

```json
{
  "code": -32602,
  "message": "task not found",
  "data": { "field": "task_id", "value": "abc-123" }
}
```

A `not_found` reason code may be added to the taxonomy in a future contracts amendment. Until then, lookup failures use RPC-level errors.

### Collection Tool Errors

Collection tools (`session_list`, `task_query`, `lesson_query`, `query`) use the collection envelope for success responses. Validation errors (invalid enum, bad cursor, malformed params) use JSON-RPC error codes:

| Code | Meaning | Triggers |
|------|---------|----------|
| `-32602` | Invalid params | Bad enum value, invalid cursor, malformed filter |
| `-32603` | Internal error | FTS5 failure, database error |

Collection envelopes are success-only — they never carry `reason_code`.

### Internal Errors

Invariant breaches (e.g., `anchor_hash` active duplicate, entity/domain kind mismatch) are internal errors that signal server bugs:

```json
{
  "code": -32603,
  "message": "internal error: multiple active lessons with same anchor_hash",
  "data": null
}
```

Internal errors abort the current operation. They are not retriable without server-side investigation.

### Rejection Precedence

When multiple phases would reject a request, the earliest failing phase wins. Later phases are not evaluated for error selection.

Example: A `task_update(action='close')` request with missing `terminal_status` (phase 2 failure) targeting a closed task (phase 4 failure) returns `policy_blocked` for the missing `terminal_status`, not `invalid_transition` for the closed task.

This deterministic ordering simplifies client error handling — the first error is always the most actionable.

---

## Cross-References

| Topic | Location |
|-------|----------|
| Tool surface (parameters, envelopes, action semantics) | [tool-surface.md](../contracts/tool-surface.md) |
| Behavioral semantics (merge rules, atomicity, ordering) | [behavioral-semantics.md](../contracts/behavioral-semantics.md) |
| Database schema (DDL, constraints, indexes) | [ddl.md](../schema/ddl.md) |
| Schema rationale (design decisions, deferred items) | [rationale.md](../schema/rationale.md) |
| Hook enforcement (identity guard, telemetry) | [hooks.md](hooks.md) |
| Internal architecture (subsystem boundaries, server.py wiring) | [internal-architecture.md](../internal-architecture.md) |
| Three-layer enforcement stack | [tool-surface.md](../contracts/tool-surface.md) — Session Bootstrap |
| Lazy session bootstrap | [skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap) |
| Tool Access Model (read ungated, mutation gated) | [foundations.md](../foundations.md) |
| Codex collaborative design review | Dialogue #27, thread `019ced65-055c-7c41-9474-447383a55fe6` |
| Codex adversarial review | Dialogue #28, thread `019ced84-9ce3-7ef1-9acb-1d3b90bfae0d` |

### Open Questions (Contracts-Level)

These questions cannot be resolved in this implementation document — they require amendments to normative contracts:

1. **`not_found` reason code:** Should the 5-code taxonomy gain a `not_found` code for entity ID resolution failures? Currently handled via non-envelope RPC errors. ([tool-surface.md](../contracts/tool-surface.md))
2. **Promoting retracted lessons:** Should `lesson_promote` accept retracted lessons? No behavior specified in contracts. ([tool-surface.md](../contracts/tool-surface.md))
3. **`anchor_hash` partial UNIQUE index:** Should `idx_lessons_anchor` become a partial unique index `WHERE status='active'` for schema-level active-duplicate prevention? Currently index-only with server-maintained invariant. ([ddl.md](../schema/ddl.md))
4. **`dependency_blocked` assignment:** Should `dependency_blocked` be emitted when closing a task with open dependents? Currently reserved. ([tool-surface.md](../contracts/tool-surface.md))
5. **Cursor format and validation:** What encoding, expiration, and error handling rules apply to pagination cursors? ([tool-surface.md](../contracts/tool-surface.md))
6. **`task_create` `status` parameter:** `tool-surface.md` does not list `status` as a `task_create` parameter. Should it be documented with its default (`open`), or should the validation be removed? ([tool-surface.md](../contracts/tool-surface.md))
7. **`"fields"` container vs individual params:** `tool-surface.md` uses `fields (context, tags)` in the `lesson_update` row — is `fields` a container parameter or shorthand for individual top-level parameters? Affects phase 1 parse shape. ([tool-surface.md](../contracts/tool-surface.md))
