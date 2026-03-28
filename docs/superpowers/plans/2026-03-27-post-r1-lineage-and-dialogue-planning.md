# Post-R1 Lineage & Dialogue Milestone Planning

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan produces **spec artifacts and decision records**, not runtime code.

**Goal:** Land the normative lineage-store spec section, triage R1 debt into durable backlog artifacts, and freeze the next implementation milestone boundary for the codex-collaboration plugin.

**Architecture:** Four tasks produce committed artifacts: a fork-scope decision record, a normative lineage-store spec section in `contracts.md`, a consolidated debt ticket, and a dialogue milestone scope section in `delivery.md`. The critical path is T1 → T2 → T4. T3 runs in parallel with T1.

**Branch:** `chore/post-r1-planning` (from `main` at `f04978f6`)

**Prerequisite:** `main` pushed to `origin` (completed).

---

## Preamble: Review Surface

T2 amends `contracts.md` (adding a Lineage Store section and dialogue typed response shapes) and `recovery-and-journal.md` (adding a cross-reference). Per `spec.yaml:88-92`, changes to the `contracts` authority trigger mandatory review from three authorities:

| Authority | File | Review Reason |
|---|---|---|
| `promotion-contract` | `promotion-protocol.md` | Handle identity could affect promotion preconditions |
| `advisory-policy` | `advisory-runtime-policy.md` | Rotation depends on handle-to-runtime remapping |
| `recovery-contract` | `recovery-and-journal.md` | Crash recovery rebuilds handle mappings from lineage store |

There is **no boundary rule** that fires FROM `recovery-contract` changes (`spec.yaml` only lists it as a reviewer for other authorities). The `recovery-and-journal.md` amendment in T2 is a cross-reference addition, not a behavioral change — but this plan notes it explicitly for transparency.

**What this means in practice:** After T2 is committed, the implementer should verify that:
1. The lineage store's `update_runtime` operation is consistent with `advisory-runtime-policy.md:97` (rotation step 4)
2. The crash recovery contract references are consistent with `recovery-and-journal.md:107` (step 2)
3. No promotion precondition in `promotion-protocol.md` depends on handle state in a way the lineage store doesn't support

These checks are steps within T2, not separate tasks.

## Preamble: Persistence Boundary

The lineage store must survive crashes to satisfy `recovery-and-journal.md:107` ("Rebuild handle mappings from the lineage store"). But the spec does **not** say whether it survives Claude session restarts. This choice drives storage design and security posture:

| Option | Crash Survival | Session Restart Survival | Storage | Complexity |
|---|---|---|---|---|
| **A: Session-bounded** | Yes (fsync) | No | `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/` | Low — cleanup on session end |
| **B: Cross-session** | Yes (fsync) | Yes | Persistent directory outside session scope | Higher — retention policy, orphan cleanup, session-id reconciliation |

**Evidence favoring Option A:**
- The operation journal is explicitly session-bounded (`recovery-and-journal.md:54-56`)
- `CollaborationHandle.claude_session_id` already provides session scoping (`contracts.md:47`)
- Cross-session dialogue resumption is not in v1 scope (`delivery.md:176`)
- Crash recovery describes within-session recovery: "Allow Claude to continue from the last completed turn" (`recovery-and-journal.md:111`)

**Evidence favoring Option B:**
- None in the current spec. Cross-session persistence would only matter for "resume a dialogue from a previous session," which is not a v1 goal.

**This plan recommends Option A (session-bounded).** If the implementer chooses Option B, the lineage store spec section in T2 must additionally define: retention policy, orphan handle cleanup, session-id reconciliation on reload, and storage location outside `${CLAUDE_PLUGIN_DATA}`.

T2 Step 1 resolves this decision before writing the spec section.

---

## File Structure

| Task | Action | File |
|---|---|---|
| T1 | Modify | `docs/superpowers/specs/codex-collaboration/decisions.md` (add resolved question) |
| T2 | Modify | `docs/superpowers/specs/codex-collaboration/contracts.md` (add Lineage Store section after line 85; add dialogue response shapes after line 165) |
| T2 | Modify | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` (cross-reference at line 107) |
| T2 | Modify | `docs/superpowers/specs/codex-collaboration/spec.yaml` (update contracts description) |
| T3 | Create | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` |
| T4 | Modify | `docs/superpowers/specs/codex-collaboration/delivery.md` (add R2 section after line 189) |

---

## Task 1: Fork Scope Decision

**Depends on:** Nothing — can start immediately.
**Parallel with:** T3.

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/decisions.md` (append to Open Questions section)

**Evidence summary:**

| Source | Citation | What it says |
|---|---|---|
| `delivery.md:158` | Step 4 scope | `.start` + `.reply` + `.read` — fork is **not listed** |
| `contracts.md:22` | MCP tool surface | `.fork` is a first-class tool |
| `foundations.md:173-174` | Dialogue flow | Fork maps to `thread/fork`, plugin records parent-child lineage |
| `runtime.py:95` | Implementation | `fork_thread()` already works for consultation branching |

`delivery.md` is the delivery authority. It explicitly scopes step 4 without fork. The recommendation is: **defer fork from the first dialogue milestone, but design the lineage store schema to include `parent_collaboration_id` and `fork_reason` from creation, so no migration is needed later.**

- [ ] **Step 1: Write fork scope decision in `decisions.md`**

Append the following after the `### Advisory Domain Stale Context After Promotion` section (after line 79) in `docs/superpowers/specs/codex-collaboration/decisions.md`:

```markdown
### Dialogue Fork Scope

**Resolved.** `codex.dialogue.fork` is deferred from the first post-R1 dialogue milestone. The milestone implements `.start`, `.reply`, and `.read` only, matching [delivery.md step 4](delivery.md).

**Rationale:** [delivery.md:158](delivery.md) explicitly scopes step 4 without fork. Deferring fork allows the [lineage store](contracts.md#lineage-store) to start as flat handle tracking without tree-traversal operations. The [CollaborationHandle](contracts.md#collaborationhandle) schema already includes `parent_collaboration_id` and `fork_reason` — no schema migration will be needed when fork enters scope.

**Forward compatibility:** `thread/fork` is already implemented in `runtime.py` for consultation branching. Adding `codex.dialogue.fork` is additive, not architectural.

**Change trigger:** When a use case for branched dialogue is identified. Fork is not blocked — it is deferred for scope reasons, not design reasons.
```

- [ ] **Step 2: Verify no conflicts**

Confirm that:
1. `delivery.md:158` still scopes step 4 as `.start` + `.reply` + `.read`
2. No other spec section requires fork for the next milestone
3. `contracts.md:45-46` still defines `parent_collaboration_id` and `fork_reason` in CollaborationHandle

Run: `grep -n "dialogue.fork\|thread/fork" docs/superpowers/specs/codex-collaboration/*.md`
Expected: References exist (contracts, foundations, advisory-runtime-policy) but none mandate fork in the next milestone.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/decisions.md
git commit -m "docs(codex-collaboration): resolve fork scope — defer from first dialogue milestone"
```

---

## Task 2: Lineage Store Spec Section

**Depends on:** T1 (fork scope determines whether lineage store needs tree operations).
**Critical path:** T1 → **T2** → T4.

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/contracts.md:85` (insert Lineage Store section)
- Modify: `docs/superpowers/specs/codex-collaboration/contracts.md:165` (append dialogue typed response shapes)
- Modify: `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:107` (add cross-reference)
- Modify: `docs/superpowers/specs/codex-collaboration/spec.yaml:14` (update contracts description)

- [ ] **Step 1: Resolve persistence boundary**

Record the persistence boundary decision. If following the recommended Option A (session-bounded):

Confirm that these three conditions hold:
1. Operation journal is session-bounded: check `recovery-and-journal.md:54-56`
2. `CollaborationHandle.claude_session_id` exists: check `contracts.md:47`
3. Cross-session dialogue is not in v1 scope: check `delivery.md:176`

If all three hold, proceed with Option A. If any fail, reassess and adjust the spec section in Step 2.

- [ ] **Step 2: Write lineage store section in `contracts.md`**

Insert the following between the `### PendingServerRequest` section (after line 85, after the `kind: unknown` note) and the `## Audit Event Schema` heading (currently line 87) in `docs/superpowers/specs/codex-collaboration/contracts.md`:

```markdown
## Lineage Store

The lineage store persists [CollaborationHandle](#collaborationhandle) records for the control plane. It is the plugin's identity and routing layer — all handle-to-runtime mappings, lifecycle state, and parent-child relationships are maintained here independently of raw Codex thread IDs.

### Persistence Scope

**v1: Session-bounded with crash survival.**

The lineage store is scoped to the Claude session that creates the handles. It survives process crashes within a running session but does not survive Claude session restarts. On session end, all handle records for that session are eligible for cleanup.

| Property | Value | Rationale |
|---|---|---|
| Crash survival | Yes | Required by [recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash) step 2 |
| Session restart survival | No | Cross-session dialogue resumption is not in v1 scope; operation journal is also session-bounded ([§Session Scope](recovery-and-journal.md#session-scope)) |
| Write discipline | Write-through (fsync before return) | Crash survival requires durable writes, not in-memory caching |
| Session scoping key | `claude_session_id` on [CollaborationHandle](#collaborationhandle) | Already defined in the data model |

### Storage

**Location:** `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/`

The session-id subdirectory isolates each session's handles. `${CLAUDE_PLUGIN_DATA}` is durable plugin state ([foundations.md §Chosen Defaults](foundations.md#chosen-defaults)), not inherently session-scoped — the session partition is enforced by the directory structure.

**Format:** Append-only JSONL. All mutations (create, update_status, update_runtime) append a new record. On read, the store replays the log — the last record for each `collaboration_id` wins. Incomplete trailing records (from crash mid-write) are discarded on load.

**Atomicity:** Individual appends are crash-safe: write the record, then `fsync`. A crash mid-append produces at most one incomplete trailing line, which the reader discards. No temp-file-rename needed because the store never rewrites existing data.

**Compaction:** Optional. When the log exceeds a size threshold (e.g., 100 records), the store may compact by writing a fresh file via temp-file-then-rename with `fsync`. Compaction is a performance optimization, not a correctness requirement — the append-only log is always readable without it.

**Cleanup:** On session end, the control plane removes its `<claude_session_id>/` subdirectory. Stale session directories (from crashes that prevented cleanup) are pruned on next plugin startup by scanning for directories whose session is no longer active.

**Security posture:** The lineage store contains opaque identifiers (collaboration_ids, Codex thread_ids), not secrets or conversation content. Thread IDs are routing handles into Codex thread history — they should be treated as internal state, not exposed outside the plugin data directory. No additional access controls beyond `${CLAUDE_PLUGIN_DATA}` defaults.

### Operations

| Operation | Purpose | Used by |
|---|---|---|
| `create` | Persist a new handle | `codex.dialogue.start` |
| `get` | Retrieve handle by `collaboration_id` | `codex.dialogue.reply`, `codex.dialogue.read`, control plane routing |
| `list` | Query handles by session, repo root, and optional status filter | `codex.dialogue.read` (listing dialogues) |
| `update_status` | Transition handle lifecycle status | Handle completion, crash recovery |
| `update_runtime` | Remap handle to a new runtime | Advisory runtime rotation ([advisory-runtime-policy.md §Rotate](advisory-runtime-policy.md#rotate) step 4) |

Fork-specific operations (`get_children`, `get_parent`, tree reconstruction) are deferred until `codex.dialogue.fork` enters scope. See [decisions.md §Dialogue Fork Scope](decisions.md#dialogue-fork-scope).

### Handle Lifecycle

| Status | Meaning | Transitions to |
|---|---|---|
| `active` | Handle is open for turns | `completed`, `crashed`, `unknown` |
| `completed` | Dialogue or consultation finished normally | Terminal |
| `crashed` | Runtime crash detected | `active` (after recovery) |
| `unknown` | Session crash, state uncertain | `active` (after recovery), `completed` (after inspection) |

### Crash Recovery Contract

When an advisory runtime crashes ([recovery-and-journal.md §Advisory Runtime Crash](recovery-and-journal.md#advisory-runtime-crash)):

1. The control plane restarts the advisory runtime.
2. The control plane reads all handles with `status: active` from the lineage store for the current session and repo root.
3. For each active handle, the control plane uses Codex `thread/read` on the handle's `codex_thread_id` to recover the latest completed state.
4. The control plane calls `update_runtime` on each recovered handle to point to the new runtime instance.
5. Pending server requests associated with crashed handles are marked canceled.
6. Claude may continue from the last completed turn. Forking from the interrupted snapshot requires `codex.dialogue.fork` to be in scope.

The lineage store does not participate in crash detection or runtime restart — those are control plane responsibilities. The store's role is providing the handle data needed for step 2.

### Relationship to Other Stores

| Store | Scope | Write Discipline | Purpose |
|---|---|---|---|
| Lineage store | Session-bounded | Write-through (fsync) | Handle identity and routing |
| [Operation journal](recovery-and-journal.md#operation-journal) | Session-bounded | fsync before dispatch | Idempotent replay |
| [Audit log](recovery-and-journal.md#audit-log) | Cross-session (30-day TTL) | Best-effort append | Human reconstruction |

The lineage store and operation journal are both session-bounded but serve different purposes. The journal records in-flight operations for replay; the lineage store records handle identity for routing and recovery. They share `${CLAUDE_PLUGIN_DATA}` but use separate subdirectories.
```

- [ ] **Step 3: Add typed response shapes for dialogue tools**

Append the following to the `## Typed Response Shapes` section (after the `### Runtime Health` subsection, currently ending at line 165) in `docs/superpowers/specs/codex-collaboration/contracts.md`:

```markdown
### Dialogue Start

Returned by `codex.dialogue.start`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Plugin-assigned unique handle for this dialogue |
| `runtime_id` | string | Advisory runtime instance serving this dialogue |
| `status` | enum | Initial handle lifecycle status (always `active`) |
| `created_at` | ISO 8601 | Handle creation time |

### Dialogue Reply

Returned by `codex.dialogue.reply`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Handle for this dialogue |
| `runtime_id` | string | Advisory runtime that served this turn |
| `position` | string | Codex's response on this turn |
| `evidence` | list\[object\] | Supporting evidence: each has `claim` (string) and `citation` (string) |
| `uncertainties` | list\[string\] | Noted uncertainties |
| `follow_up_branches` | list\[string\] | Suggested follow-up directions |
| `turn_sequence` | integer | Turn number within this dialogue |
| `context_size` | integer | UTF-8 byte length of assembled packet |

### Dialogue Read

Returned by `codex.dialogue.read`.

| Field | Type | Description |
|---|---|---|
| `collaboration_id` | string | Handle for this dialogue |
| `status` | enum | Current handle lifecycle status |
| `turn_count` | integer | Number of completed turns |
| `created_at` | ISO 8601 | Handle creation time |
| `turns` | list\[object\] | Each has: `turn_sequence` (integer), `position` (string summary), `context_size` (integer), `timestamp` (ISO 8601) |
```

- [ ] **Step 4: Add lineage store reference to CollaborationHandle**

In `docs/superpowers/specs/codex-collaboration/contracts.md`, modify the `### CollaborationHandle` intro paragraph (line 37) from:

```markdown
A logical identifier for a Codex interaction (consultation, dialogue turn, or delegation job).
```

to:

```markdown
A logical identifier for a Codex interaction (consultation, dialogue turn, or delegation job). Handle records are persisted by the [lineage store](#lineage-store) for routing, crash recovery, and lifecycle management.
```

- [ ] **Step 5: Update crash recovery cross-reference in `recovery-and-journal.md`**

In `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md`, modify line 107 from:

```markdown
2. Rebuild handle mappings from the lineage store.
```

to:

```markdown
2. Rebuild handle mappings from the [lineage store](contracts.md#lineage-store).
```

- [ ] **Step 6: Update `spec.yaml` contracts authority description**

In `docs/superpowers/specs/codex-collaboration/spec.yaml`, modify the contracts description (lines 14-17) from:

```yaml
  contracts:
    description: >-
      MCP tool surface, logical data model types (CollaborationHandle,
      DelegationJob, PendingServerRequest), audit event schema, typed
      rejection and response shapes, and protocol message formats.
```

to:

```yaml
  contracts:
    description: >-
      MCP tool surface, logical data model types (CollaborationHandle,
      DelegationJob, PendingServerRequest), lineage store persistence
      contract, audit event schema, typed rejection and response shapes,
      and protocol message formats.
```

- [ ] **Step 7: Verify boundary rules are satisfied**

Check each authority that must review changes to `contracts`:

1. **`promotion-contract` (`promotion-protocol.md`):** Does the lineage store affect promotion preconditions?
   - Check: `grep -n "collaboration_id\|handle\|lineage" docs/superpowers/specs/codex-collaboration/promotion-protocol.md`
   - Expected: Promotion operates on `DelegationJob`, not `CollaborationHandle`. No conflict.

2. **`advisory-policy` (`advisory-runtime-policy.md`):** Is `update_runtime` consistent with rotation step 4?
   - Check: Verify `advisory-runtime-policy.md:97` says "Update the control plane's handle mappings to point to the new runtime"
   - Expected: The lineage store's `update_runtime` operation directly implements this requirement.

3. **`recovery-contract` (`recovery-and-journal.md`):** Is the crash recovery contract consistent?
   - Check: Verify `recovery-and-journal.md:107` (now cross-referenced) aligns with the lineage store's crash recovery section
   - Expected: The lineage store section's 6-step crash recovery path matches `recovery-and-journal.md:104-111`.

If any check reveals a conflict, resolve it before committing. Document the resolution in the commit message.

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/contracts.md
git add docs/superpowers/specs/codex-collaboration/recovery-and-journal.md
git add docs/superpowers/specs/codex-collaboration/spec.yaml
git commit -m "docs(codex-collaboration): add lineage store and dialogue response shapes

Adds Lineage Store section to contracts.md: session-partitioned storage
at CLAUDE_PLUGIN_DATA/lineage/<session_id>/, append-only JSONL with
crash-safe semantics, explicit cleanup rules.

Adds typed response shapes for codex.dialogue.start, .reply, .read.

Cross-references recovery-and-journal.md crash recovery path.
Updates spec.yaml contracts description to include lineage store.

Review surface: promotion-contract, advisory-policy, recovery-contract
(per spec.yaml boundary rule for contracts changes)."
```

---

## Task 3: R1 Debt Triage

**Depends on:** Nothing — can start immediately.
**Parallel with:** T1.

**Files:**
- Create: `docs/tickets/2026-03-27-r1-carry-forward-debt.md`

- [ ] **Step 1: Create the consolidated debt ticket**

Write the following to `docs/tickets/2026-03-27-r1-carry-forward-debt.md`:

```markdown
# T-20260327-01: R1 carry-forward debt triage

```yaml
id: T-20260327-01
date: 2026-03-27
status: open
priority: medium
tags: [codex-collaboration, r1, hardening]
blocked_by: []
blocks: []
effort: medium
```

## Context

R1 runtime milestone merged to main at `3490718a` (2026-03-27). The following items were identified during spec-grounded R1 code review and explicitly deferred. This ticket converts them from handoff-only notes into durable backlog artifacts.

Source: R1 handoff document, review findings #1-10, downstream risks A-E.

## Items

| # | Item | Code Location | Severity | Classification | Rationale |
|---|---|---|---|---|---|
| 1 | Bootstrap-required method assertions | `runtime.py:29-33,52`; `control_plane.py:243,260` — calls `initialize`/`account/read` without asserting in `REQUIRED_METHODS` | Medium | Parked | Dialogue doesn't change the bootstrap path. These methods are called before any capability-specific code. |
| 2 | Process orphan cleanup | `jsonrpc_client.py` — no `__del__`, no `__enter__`/`__exit__`, no `atexit.register()`. Relies on explicit `close()`. | Low | Parked | Invalidation-on-failure from R1 reduces practical orphan damage. Same risk profile for dialogue. |
| 3 | Concurrent consult safety | `control_plane.py:65` — `_advisory_runtimes` dict has no `threading.Lock`. Multiple `.get()`, `[]`, `.pop()` without synchronization. | Low | Parked | R2 MCP server uses serialized dispatch (one tool call at a time). Concurrent safety is not needed while serialization invariant holds. Revisit only if serialization is relaxed. |
| 4 | `AuditEvent` schema expansion | `models.py:149-151` — missing `job_id`, `request_id`, `artifact_hash`, `decision`, `causal_parent`. Currently uses `extra: dict[str, Any]`. | Deferred | Parked | Dialogue events only need existing fields (`collaboration_id`, `runtime_id`, `turn_id`). Add delegation-specific fields before delegation events land. |
| 5 | Policy fingerprint parameterization | `control_plane.py:346-357` — `build_policy_fingerprint()` uses hardcoded material dict (`transport_mode`, `sandbox_level`, etc.). | Deferred | Parked | Blocks advisory widening, not dialogue. No change needed for R2. |
| 6 | Redaction pattern coverage | `context_assembly.py:40-45` — 4 patterns (OpenAI `sk-*`, Bearer, PEM, `password=`). Missing: AWS `AKIA*`, GitHub `ghp_`/`gho_`/`github_pat_`, base64 credentials. | Medium | Existing gap | Same assembly path for dialogue and consultation. Not dialogue-specific, but a token in context assembly leaks regardless of capability. |
| 7 | Non-UTF-8 file read hardening | `context_assembly.py:345` — `read_text(encoding="utf-8")` without `try/except UnicodeDecodeError`. Binary file reference crashes the entire assembly pipeline. | Medium | Existing gap | Same assembly path for dialogue and consultation. A user referencing a binary file (image, compiled asset) crashes assembly for any capability. |

## Classification Key

| Classification | Meaning | Action |
|---|---|---|
| **Parked** | Not a pre-dialogue blocker. Revisit when the relevant capability enters scope or the risk profile changes. | No action before R2. |
| **Existing gap** | Affects all context assembly equally (dialogue and consultation). Not dialogue-specific, but the risk exists today. | Fix opportunistically or add to R2 scope at T4 decision gate. |

## Decision Gate (T4 input)

Before freezing R2 scope in T4, review items classified as **existing gap** (items 6 and 7):

- If the team judges that either gap undermines trustworthy context assembly enough to warrant pre-dialogue fixing, promote it to R2 scope.
- If neither is promoted, they remain here as open backlog items with no milestone assignment.

## Acceptance Criteria

- [ ] All 7 items have a classification (parked or existing gap)
- [ ] Any items promoted to pre-dialogue blockers are noted for T4 scope inclusion
- [ ] This ticket replaces handoff-only tracking — the handoff is archived
```

- [ ] **Step 2: Review classification and adjust if needed**

Read each item's code location to verify the classification is still accurate:

```bash
# Item 1: Bootstrap assertions
grep -n "initialize\|account/read" packages/plugins/codex-collaboration/server/runtime.py
grep -n "REQUIRED_METHODS" packages/plugins/codex-collaboration/server/codex_compat.py

# Item 6: Redaction patterns
grep -n "_SECRET_PATTERNS" packages/plugins/codex-collaboration/server/context_assembly.py

# Item 7: UTF-8 hardening
grep -n "read_text" packages/plugins/codex-collaboration/server/context_assembly.py
```

If any item's code location has changed since R1, update the ticket. If the team decides to promote items 6 or 7 to pre-dialogue blockers, update their classification column.

- [ ] **Step 3: Commit**

```bash
git add docs/tickets/2026-03-27-r1-carry-forward-debt.md
git commit -m "docs(codex-collaboration): triage R1 carry-forward debt into durable ticket

7 deferred items from R1 review: 5 parked (bootstrap assertions,
process orphans, concurrent safety, audit schema, policy fingerprint),
2 classified as existing context-assembly gaps (redaction coverage,
UTF-8 hardening). Decision gate feeds into T4 scope freeze."
```

---

## Task 4: Dialogue Milestone Scope Freeze

**Depends on:** T2 (lineage spec landed) and T3 (debt triage complete).
**Critical path terminal node.**

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/delivery.md` (insert after line 189, before "Not in First Slice")

- [ ] **Step 1: Check T3 decision gate output**

Before writing the scope section, check the T3 ticket:
- Were items 6 (redaction) or 7 (UTF-8) promoted to pre-dialogue blockers?
- If yes, add them to the R2 "In scope" list below.
- If no, proceed with the scope section as written.

- [ ] **Step 2: Write Runtime Milestone R2 section in `delivery.md`**

Insert the following after the R1 acceptance gates (after line 189, before `### Not in First Slice`) in `docs/superpowers/specs/codex-collaboration/delivery.md`:

```markdown
### Runtime Milestone R2 (Dialogue Foundation)

R2 implements the lineage store (delivery step 3) and the minimum dialogue surface (delivery step 4, minus fork). It also introduces MCP server scaffolding for tool exposure and dialogue operation journaling.

**In scope**

- Lineage store implementation per [contracts.md §Lineage Store](contracts.md#lineage-store): session-partitioned append-only JSONL at `${CLAUDE_PLUGIN_DATA}/lineage/<claude_session_id>/`, crash-safe semantics, lifecycle management, and advisory runtime rotation mapping
- MCP server scaffolding (`mcp_server.py`): tool registration and serialized request dispatch for all R2 tools plus existing R1 capabilities (`codex.status`, `codex.consult`). **Serialization invariant:** the control plane processes one tool call at a time; concurrent MCP requests are queued, not processed in parallel
- `codex.dialogue.start`: create a durable dialogue thread in the advisory runtime, persist handle in lineage store, return [Dialogue Start](contracts.md#dialogue-start) response shape
- `codex.dialogue.reply`: continue a dialogue turn on an existing handle, dispatch via advisory runtime using the same context assembly pipeline as consultation, return [Dialogue Reply](contracts.md#dialogue-reply) response shape
- `codex.dialogue.read`: read dialogue state for a given `collaboration_id` from lineage store data plus Codex `thread/read`, return [Dialogue Read](contracts.md#dialogue-read) response shape
- Operation journal entries for dialogue turns: journal-before-dispatch per [recovery-and-journal.md §Write Ordering](recovery-and-journal.md#write-ordering), with idempotency keys per [§Idempotency Keys](recovery-and-journal.md#idempotency-keys) (`runtime_id` + `thread_id` + `turn_sequence`). Trim on turn completion.
- Audit events for `dialogue_turn` with required fields per [recovery-and-journal.md §Write Triggers](recovery-and-journal.md#write-triggers): `collaboration_id`, `runtime_id`, `turn_id`
- Context assembly reuse: dialogue turns use the same advisory profile, assembler, redactor, trimmer, and budget caps as consultation

**Deferred**

- `codex.dialogue.fork` and tree reconstruction in `codex.dialogue.read` — see [decisions.md §Dialogue Fork Scope](decisions.md#dialogue-fork-scope)
- Hook guard integration for dialogue tool calls
- Delegation runtime, worktree orchestration, and promotion
- `turn/steer`-based coherence

**Acceptance gates**

- Lineage store persists handles to disk (append-only JSONL) and recovers them after a simulated process crash within a session, including discarding incomplete trailing records
- `codex.dialogue.start` creates a fresh advisory thread and returns a valid [Dialogue Start](contracts.md#dialogue-start) response backed by a persisted handle
- `codex.dialogue.reply` dispatches a turn on an existing handle and returns a valid [Dialogue Reply](contracts.md#dialogue-reply) response
- `codex.dialogue.read` returns the current state of a dialogue matching the [Dialogue Read](contracts.md#dialogue-read) shape, from lineage store data plus Codex thread history
- MCP server exposes all R2 tools (`codex.dialogue.start`, `.reply`, `.read`) plus R1 tools (`codex.status`, `codex.consult`) with serialized dispatch
- Dialogue turns are journaled before dispatch and replayed idempotently after simulated crash
- Audit events are emitted for dialogue turns with required fields
- No R2 path depends on fork, delegation, promotion, or hook guard enforcement
```

If T3 promoted items 6 or 7 to pre-dialogue blockers, add them to the "In scope" list:

For item 6 (if promoted): `- Context assembly redaction hardening: add AWS, GitHub, and base64 credential patterns to _SECRET_PATTERNS`

For item 7 (if promoted): `- Context assembly UTF-8 hardening: catch UnicodeDecodeError in _read_file_excerpt, skip binary files gracefully`

- [ ] **Step 3: Verify scope boundary is complete**

Confirm that:
1. Every R2 acceptance gate is testable (no ambiguous success criteria)
2. The deferred list explicitly names everything NOT in R2 that someone might expect
3. MCP server exposure boundary is addressed (tools listed, scaffolding in scope)
4. Context assembly reuse is noted (no new assembly pipeline for dialogue)
5. The lineage store section in `contracts.md` supports every R2 capability (create, get, list, update_status, update_runtime)

Run: `grep -c "codex.dialogue" docs/superpowers/specs/codex-collaboration/delivery.md`
Expected: References exist in both R2 scope and the step 4 row.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/delivery.md
git commit -m "docs(codex-collaboration): freeze Runtime Milestone R2 scope — dialogue foundation

R2 covers: lineage store (session-partitioned, append-only JSONL),
MCP server scaffolding (serialized dispatch), codex.dialogue.start/
.reply/.read with typed response shapes, dialogue operation journaling
with idempotency keys. Fork deferred per decisions.md."
```

---

## Decision Gates (Cross-Task)

These gates are evaluated between phases, not within tasks:

| Gate | Timing | Condition | If True | If False |
|---|---|---|---|---|
| **Fork complexity** | After T1, before T2 | T1 decides fork is in scope | T2 must add `get_children`, `get_parent`, and tree reconstruction operations to the lineage store section. Lineage becomes a tree, not flat handles. | T2 proceeds with flat-handle lineage store (recommended path). |
| **Debt promotion** | After T3, before T4 | T3 promotes item 6 or 7 to pre-dialogue blocker | T4 adds the promoted item(s) to R2 "In scope" and acceptance gates. | T4 proceeds with R2 scope as written. |
| **Authority conflict** | After T2 Step 6 | Boundary rule check reveals a conflict with promotion-contract, advisory-policy, or recovery-contract | Resolve the conflict before committing T2. Document the resolution in the commit message. | T2 commits cleanly. |

---

## Verification

After all four tasks are committed, verify the plan produced its promised artifacts:

```bash
# T1: Fork scope decision exists
grep -l "Dialogue Fork Scope" docs/superpowers/specs/codex-collaboration/decisions.md

# T2: Lineage store section exists and is cross-referenced
grep -l "## Lineage Store" docs/superpowers/specs/codex-collaboration/contracts.md
grep "lineage store" docs/superpowers/specs/codex-collaboration/recovery-and-journal.md
grep "lineage store" docs/superpowers/specs/codex-collaboration/spec.yaml

# T3: Debt ticket exists
test -f docs/tickets/2026-03-27-r1-carry-forward-debt.md && echo "exists"

# T4: R2 scope section exists
grep -l "Runtime Milestone R2" docs/superpowers/specs/codex-collaboration/delivery.md
```

All four checks should succeed. If any fails, the corresponding task was not completed.
