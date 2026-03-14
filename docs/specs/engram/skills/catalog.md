---
module: skills-catalog
legacy_sections: ["7.4"]
authority: skills
normative: true
status: active
---

## Per-Skill Designs

*Skills that exceed ~100 lines or are independently amended should be extracted to their own file.*

#### `/save` — Session Persistence {#skill-save}

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
5. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `session_end(summary=..., final_content=...)` — atomic final snapshot + close
7. Report outcome from entity envelope

**Steps (checkpoint branch):**
1-3. Same as close branch
4. Present summary + confirmation (advisory severity)
5. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `session_snapshot(content=..., kind='checkpoint')` — session stays open
7. Report outcome

**Design notes:**
- The hard confirmation gate prevents Claude from proactively calling session_end even though the skill is auto-visible
- `session_get` in allowed-tools enables reading current session state during synthesis (returns empty if session has not yet been bootstrapped — synthesis proceeds from conversation context)
- `/save` calls `session_start` only for lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)) — never for continuation or enrichment

#### `/load` — Session Resumption {#skill-load}

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
- Step 7 calls `session_start` for both bootstrap and continuation — `session_start` is idempotent on `session_id` ([tool-surface.md](../contracts/tool-surface.md#action-semantics)), so it creates the session row if needed and sets `continued_from_session_ids` in the same call. The user's session selection is the implicit confirmation ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap), lazy bootstrap exception).
- `session_start` field-specific patch semantics ([tool-surface.md](../contracts/tool-surface.md#action-semantics)) ensure enriching an existing session appends continuation links and preserves existing metadata
- `loadable_snapshot` is `Snapshot|null`: null when session has no snapshots (e.g., session was started but never saved). When null, `/load` falls back to catch-up profile only — there is no snapshot content to resume from
- Presentation profile (resume vs catch-up) is inferred from `loadable_snapshot` presence and user phrasing

#### `/triage` — Project Orientation {#skill-triage}

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

**Mode arbitration:** Modes control query priority, not exclusive scope — all modes run secondary and supplemental queries from other subsystems. Default to Action when intent is ambiguous. Mixed-intent prompts ("catch me up and tell me what to work on next") do not require mode composition: Action mode already includes `session_list` as secondary, providing catch-up context. Use the relevance gate's "clarify" classification only when the user's intent is genuinely unclear (not when it spans modes).

**Steps:**
1. Relevance gate: classify intent as execute/clarify/ignore
2. Determine mode from user phrasing (default: action; see mode arbitration above)
3. Execute primary query
4. Execute secondary query for cross-subsystem context
5. Present unified view: tasks grouped by status/priority, recent sessions with goals, relevant lessons
6. Recommend next actions — may suggest `/task` for task management, but never creates tasks itself

**Design notes:**
- `/triage` is read-only — it calls only read tools. Safe for auto-invocation per the skills guide
- Read tool selection follows the policy in [foundations.md](../foundations.md#read-tool-selection-policy) — `query` is the cross-cutting fallback when entity type is unknown, not a substitute for domain-specific tools
- Description scoped to project-oriented phrasing to prevent over-matching on generic "what" questions

#### `/task` — Task Management {#skill-task}

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
4. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
5. Call `task_create(title, description, priority, tags, blocked_by=[...])` — single mutation
6. Report outcome with task_id

**Workflow (update):**
1. Resolve target task via `task_query` or user-provided task_id
2. Determine action: patch (edit fields, status transitions) / close (requires `terminal_status`: `done`|`cancelled`) / reopen
3. For close: pass `terminal_status` to `task_update`. If `cancelled`, require `reason` from user; if `done`, omit `reason` (server rejects if present)
4. Present change + confirmation (durable for patch, terminal for close)
5. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `task_update(task_id, action, ...)` — single mutation
7. Report outcome

**Dependency workflows:**
- **"Create task blocked by X":** Single mutation — resolve X via `task_query`, pass `blocked_by=[x_task_id]` to `task_create`
- **"Create task that blocks X":** Two-step — lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)) precedes step (1); (1) `task_create` the new task, (2) `task_update(x_task_id, action='patch', add_blocked_by=[new_task_id])`. Confirmation mentions non-atomicity. **Recovery if step 2 fails:** report the orphaned task (step 1 succeeded), present the task_id, and offer: retry step 2, manually add the dependency later, or delete the orphaned task.

**Design notes:**
- Subsumes the old `/defer` workflow — deferring work is just task creation with appropriate tags/context
- Read-before-write for all dependency changes: always query current state before mutation
- Direction disambiguation: "A blocks B" vs "A is blocked by B" — skill must clarify before writing

#### `/remember` — Lesson Capture {#skill-remember}

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
5. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
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
5. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
6. Call `lesson_update(lesson_id, action='retract', reason_code=..., reason=...)` — single mutation. `reinforcement_count` is preserved as historical (not decremented).
7. Report outcome

**Design notes:**
- Redirect-not-refuse pattern: suggests the right tool rather than blocking
- `lesson_capture` dual-path is transparent to the user — server reports whether the lesson was created or reinforced
- Retraction and capture have different epistemic postures (additive vs adversarial-to-prior) — the confirmation severity difference (durable vs terminal) reflects this

#### `/promote` — Lesson Promotion {#skill-promote}

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
6. Lazy bootstrap ([skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)): call `session_start(session_id=<session_id>)` to ensure active session
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
