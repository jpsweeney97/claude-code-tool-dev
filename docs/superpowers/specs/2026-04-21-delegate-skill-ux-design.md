# Delegate Skill UX Design

## Overview

A stateless state-router skill for the codex-collaboration delegation lifecycle. Routes through the 5 `codex.delegate.*` MCP tools plus `codex.status`. Each invocation discovers current job state from the server, renders it, and exits with next-step guidance.

Lives in `packages/plugins/codex-collaboration/skills/delegate/SKILL.md`.

**Ticket:** T-20260330-06 (remaining AC: delegate skill UX).

**Prerequisites:** Server enrichment (Slice 0) must land before the skill can function.

## Architecture

### Design Model

The skill is a **stateless state router**. Each invocation:

1. Determines user intent (start new job, resume active job, or explicit verb).
2. Discovers current job state via `codex.status` -> `active_delegation`.
3. Routes to the appropriate MCP tool(s).
4. Renders the result and exits with next-step guidance.

No skill-owned state files. The server is the single source of truth for job lifecycle.

### Server Prerequisite (Slice 0)

`codex.status` must populate `active_delegation`. This field means **the current delegation requiring user attention** -- not merely a runtime-active job. The distinction matters: a completed job awaiting review is not runtime-active but absolutely requires user attention.

Integration mechanism: MCP-side enrichment. `McpServer` enriches the `codex.status` result with delegation state after calling `ControlPlane.codex_status()`. The delegation controller owns the relevant state via `DelegationJobStore`. The existing `list_active()` method covers only runtime-active states (`queued`, `running`, `needs_escalation`) for the busy gate. A new `list_user_attention_required()` method is needed for the UX query. See [Slice 0](#slice-0-server-enrichment) for full integration details and error handling.

### active_delegation Shape

```json
{
  "job_id": "...",
  "status": "...",
  "promotion_state": "...",
  "base_commit": "...",
  "artifact_hash": "...",
  "artifact_paths": ["..."],
  "attention_job_count": 1
}
```

Null when no job requires user attention. `attention_job_count` is normally 1 (guaranteed by the singleton invariant for new sessions). Values > 1 indicate a pre-migration anomaly from sessions started before the widened busy gate -- the skill should warn but still operate on the returned job (last created by store replay order).

### Singleton Invariant

`active_delegation` is singular (one job or null). The server guarantees at most one user-attention job via a widened start gate: `codex.delegate.start` rejects with `busy` when any attention-active job exists, not just runtime-active ones. A user must promote, discard, or otherwise terminalize the current job before starting a new delegation.

This invariant is established in Slice 0 by widening the delegation controller's busy gate from `list_active()` (runtime-active only) to `list_user_attention_required()` (attention-active). The `busy` response includes the attention-active job's `job_id` and `status` so the skill can route the user to resolve it.

Failed and unknown jobs with `promotion_state is None` are made discardable (Slice 0) to ensure every non-terminal job has a path to terminalization. Without this, a failed job would permanently block new delegations. Failed/unknown jobs with post-mutation promotion states (`applied`, `rollback_needed`) are NOT discardable -- those require recovery/rollback handling, not abandonment.

### User-Attention-Required Definition

**Included:**

| Status | promotion_state | Why |
|--------|-----------------|-----|
| `queued`, `running` | null | In progress |
| `needs_escalation` | null | Waiting for decision |
| `completed` | `pending` | Waiting for review -> promote/discard |
| `completed` | `prechecks_failed` | User must resolve blocker or discard |
| `failed`, `unknown` | non-terminal | Needs inspection/decision |
| any | `prechecks_passed`, `applied`, `rollback_needed` | Partial/recovery states requiring attention |

**Excluded (terminal -- no action needed):**

| promotion_state | Why |
|-----------------|-----|
| `verified` | Promotion succeeded |
| `discarded` | User discarded |
| `rolled_back` | Rollback completed |

## Invocation Grammar

### Commands

```
/delegate                          -> resume active job
/delegate <objective>              -> start new job
/delegate start <objective>        -> explicit start (escape hatch)
/delegate -- <objective>           -> explicit start (escape hatch)

/delegate poll [job_id]            -> explicit poll
/delegate approve                  -> approve active escalation
/delegate deny                     -> deny active escalation
/delegate promote [job_id]         -> promote reviewed job
/delegate discard [job_id]         -> discard unpromoted job
```

### Parse Order

Deterministic, evaluated in this order:

1. Empty args -> **resume** (call `codex.status`, route from `active_delegation`).
2. `-- ` prefix -> strip `--`, remainder is **objective** -> start.
3. `start ` prefix -> strip `start`, remainder is **objective** -> start.
4. First token in `{poll, approve, deny, promote, discard}` -> **control subcommand**.
5. Anything else -> **objective** -> start.

### Disambiguation

If a reserved subcommand has unexpected trailing text beyond an optional `job_id` (for `poll`, `promote`, and `discard`), or any trailing text at all (for `approve` and `deny`), **reject with escape guidance**:

> `promote` is a control command. To delegate an objective starting with "promote", use `/delegate start promote better error handling`.

Do not silently reinterpret ambiguous input. `approve` and `deny` must never be context-sensitive. A single token after `poll`, `promote`, or `discard` is a valid `job_id` argument, not unexpected text.

### Optional job_id on Verbs

When `poll`, `promote`, or `discard` have no `job_id` argument, the skill uses `active_delegation.job_id` from `codex.status`. If no active delegation exists: error "No active delegation found."

`/delegate promote` always uses `active_delegation.job_id`. An explicit job_id on promote (e.g., `/delegate promote <job_id>`) is treated as a read-only inspection if it doesn't match `active_delegation` -- see [Gate 1](#gate-1-review-before-promote).

`/delegate poll <job_id>` is the only verb that allows inspecting arbitrary jobs outside the active delegation. This is read-only and safe.

## State Router

### Procedure

1. Determine repo root: `git rev-parse --show-toplevel`. If not in a git repository, stop.
2. Call `codex.status(repo_root)`.
   - If `auth_status` is not `authenticated`: report auth remediation steps and stop.
   - If `errors` is non-empty: report errors and stop.
   - If `delegation_status_error` is present: report the delegation diagnostic and stop. Do NOT treat null `active_delegation` as "no active delegation" when this field is set — the null is caused by a recovery/query failure, not by absence of jobs.
3. Extract `active_delegation` (or use explicit `job_id` from verb argument).
4. Call `poll(job_id)`.
5. Route on poll result using tiered precedence.

### Router Precedence

Evaluate promotion state first when non-null, then fall through to job runtime status. Exception: `pending` with `status != "completed"` (legacy/corrupt records where `promotion_state` defaults to `"pending"`) falls through to Tier 4 (runtime status) instead of being handled in Tier 3. This avoids unexpected behavior when status and promotion state combine in recovery or legacy shapes.

**Tier 1 -- Terminal promotion states.**

Terminal states are excluded from `active_delegation`. These are only reachable via the result of an explicit `promote`, `discard`, or direct `poll` with a `job_id` argument.

| `promotion_state` | Action |
|---|---|
| `verified` | "Promotion succeeded. {changed_files_count} files applied." |
| `discarded` | "Job discarded. No workspace changes." |
| `rolled_back` | "Promotion rolled back. Workspace restored to pre-promotion state." |

**Tier 2 -- Recovery/partial promotion states.**

| `promotion_state` | Action |
|---|---|
| `rollback_needed` | "Post-apply verification failed. Rollback needed." Render verification failure details from `poll.detail`. |
| `applied` | "Diff applied but not yet verified. Partial promotion state -- may indicate crash recovery." |
| `prechecks_passed` | "Prechecks passed but apply not yet completed. May normalize to `pending` after recovery." |

**Tier 3 -- User-decision promotion states.**

| `promotion_state` | Action |
|---|---|
| `pending` | If `status == "completed"`: **Review rendering** (see [Completed Job Review](#completed-job-review)). Exit with `/delegate promote` and `/delegate discard` choices. If `status != "completed"` (legacy/corrupt — `promotion_state` defaults to `"pending"` in legacy records): fall through to Tier 4 (route by runtime status). Do not render review ceremony for non-completed jobs. |
| `prechecks_failed` | "Previous promotion prechecks failed. Resolve the blocking condition, then retry `/delegate promote`, or `/delegate discard`." Do not render a specific rejection reason -- it was returned by `promote` at failure time and is not persisted on the job model. |

**Tier 4 -- Job runtime status (promotion_state is null).**

| `status` | Action |
|---|---|
| `queued` / `running` | Render job id, status, base_commit. "Run `/delegate` to check progress." |
| `needs_escalation` | **Escalation rendering** (see [Escalation Display](#escalation-display)). |
| `failed` / `unknown` | Render `poll.detail` and inspection snapshot if available. If `promotion_state is None`: "Inspect artifacts. `/delegate discard` to clear, then start a new delegation if needed." If `promotion_state` is a post-mutation state (`applied`, `rollback_needed`): "Recovery required. Workspace may have been mutated." Do not offer discard for post-mutation states. If `promotion_state` is terminal: excluded from `active_delegation`, only reachable via explicit `poll`. |
| `completed` with null `promotion_state` | Inconsistent state (should not occur — `update_status_and_promotion` sets both atomically). Report: "Job completed but promotion state is missing. This is a legacy or corrupted state that cannot be promoted or discarded. Inspect artifacts manually via `/delegate poll {job_id}`. To clear, the job store entry must be resolved outside the skill." Do NOT render promote/discard choices. |

### Start Routing

`codex.delegate.start` can return different result types:

| Result | Routing |
|---|---|
| Normal start (job running) | Render `job.job_id` prominently, status, base_commit. "Run `/delegate` to check progress." |
| `escalated: true` | Enter escalation rendering. |
| `busy: true` | Adopt `active_job_id` from the busy response. Call `poll`. Route via state router. The widened busy gate means this can be a runtime-active job (running/queued/needs_escalation) or an attention-active job (completed awaiting review, failed needing discard). The state router handles all cases. |

Always render `job.job_id` prominently on start for debugging and explicit verb use.

## Review Rendering

### Completed Job Review

When the state router reaches a completed job with `promotion_state = pending`, render in this order:

**1. Job metadata:**

```
Job: {job_id}
Status: completed | Promotion: pending
Base commit: {base_commit}
Artifact hash: {artifact_hash}
Reviewed at: {inspection.reviewed_at}
```

**2. Changed files** from `inspection.changed_files` (a path list; modification type is not included in the inspection snapshot -- derive from `full.diff` if needed):

```
Changed files ({count}):
  src/auth/handler.py
  src/auth/middleware.py
  tests/test_auth.py
```

**3. Test results** -- read `test-results.json` from `artifact_paths`:

- If tests recorded: summarize status (pass/fail), command, and key results.
- If `not_recorded` stub: "Test results: not recorded by execution agent."

**4. Diff** -- read `full.diff` from `artifact_paths`:

- If about 200 lines or fewer: include full diff.
- If larger: summarize per file (additions/deletions counts), show representative hunks for the most significant changes, and note the artifact path for manual inspection.

The 200-line threshold is a soft heuristic: summarize when the diff would crowd out review judgment. Not a hard protocol rule.

**5. Claude's assessment:** independent evaluation of correctness, risks, suspicious patterns, and missing test coverage. When the full diff is shown, the assessment may evaluate whether promotion is reasonable. When the diff is summarized (large diffs), the assessment must state that it is based on a partial view and cannot fully evaluate promotion safety -- do not produce strong "promotion is reasonable" conclusions from summarized diffs.

**6. Choices:**

```
Next steps:
  /delegate promote  -- apply these changes to primary workspace
  /delegate discard  -- discard without applying
  Read specific artifact: {artifact_path}
```

### Canonical Artifact Set

The review set is fixed at three files: `full.diff`, `changed-files.json`, and `test-results.json`. The promotion protocol ties review integrity to this set via artifact hash. The skill reads all three during review rendering.

## Escalation Rendering

### Escalation Display

When `pending_escalation` is encountered (from start, resume, or decide re-escalation):

**1. Header:** kind, request_id.

**2. Requested scope** -- render per kind:

| Kind | Rendering |
|------|-----------|
| `command_approval` | Show the command being requested. |
| `file_change` | Show the file path and change type. |
| `request_user_input` | Show what the agent is asking. |
| `unknown` | Render raw `requested_scope` JSON with a note that this is an unrecognized escalation type. |

**3. Agent context** -- if `agent_context` is non-null, show what the agent was doing when the escalation triggered.

**4. Decision prompt:**

```
Available decisions: approve, deny
  /delegate approve  -- approve this escalation
  /delegate deny     -- deny this escalation
```

### request_user_input Handling

For `request_user_input` kind, bare `/delegate approve` is insufficient. The server rejects approve without answers for this escalation type.

Procedure:

1. Render what the agent is asking, including question identifiers from `requested_scope`.
2. Tell the user: "Please provide your answer, then run `/delegate approve`."
3. When the user provides their answer (in the conversation) and invokes `/delegate approve`:
   a. The skill detects the escalation kind is `request_user_input`.
   b. The skill instructions require Claude to construct the `answers` parameter from the question identifiers (rendered in step 1) and the user's response in the conversation context.
   c. Call `codex.delegate.decide(job_id, request_id, "approve", answers={...})`.
   d. If the conversation does not contain a clear answer to the rendered questions, ask the user to clarify before calling `decide`.
4. Bare `/delegate deny` works without answers for all escalation kinds.

The skill does not parse answer syntax from the command line. Claude mediates between the user's natural language response and the decide tool's structured `answers` parameter. The explicit `/delegate approve` invocation is the trigger -- the user's answer is sourced from conversation context, not from command arguments.

**Why `/delegate approve` and not a natural-language trigger:** A plain user response (without `/delegate approve`) does not activate the skill. The skill must be explicitly invoked to call `decide`. This is intentional: the approve/deny verbs are the only paths to `decide`, maintaining the explicit-intent principle.

### Escalation Continuation (A-Style)

After each `decide`, if the result contains a new `pending_escalation`:

- Render it and ask for the next decision.
- Continue only when the user gives another clear approve/deny or answer.

This is user-mediated. The skill never automatically chains approvals or denials. Each escalation requires explicit user input before the next `decide` call.

If `decide` returns `resumed: true` with no `pending_escalation`, the job is running autonomously. Render status and exit with "Run `/delegate` to check progress."

## Ceremony Gates

### Gate 1: Review-Before-Promote

When `/delegate promote` is invoked:

1. Call `codex.status` -> read `active_delegation.artifact_hash` (this is the pre-poll state).
2. Call `poll(job_id)` to refresh state.
3. **If pre-poll `artifact_hash` was null:**
   - Poll triggered materialization.
   - Render full review.
   - Exit with: "Review complete. Run `/delegate promote` again to apply."
   - **Do not promote.** This invocation materialized the artifact -- the user has not reviewed it.
4. **If pre-poll `artifact_hash` was non-null:**
   - Render brief confirmation: "Promoting job `{job_id}`: {changed_files_count} files, artifact hash `{hash_prefix}...`"
   - Call `promote(job_id)`.
   - Render result.

**Promote only routes through active_delegation.** The singleton invariant guarantees that if a job is promotable, it IS the `active_delegation`. `/delegate promote <job_id>` where `job_id` does not match `active_delegation.job_id` (or `active_delegation` is null) is treated as a read-only inspection: poll the job, render review if applicable, but **do not call `promote`**. Report: "This job is not the active delegation. Use bare `/delegate promote` to promote the active job."

This restriction exists because the skill is stateless and cannot confirm the user reviewed an arbitrary job in a prior flow. The singleton invariant makes the restriction cost-free: there is exactly one promotable job at a time, and it is always the active delegation.

### Gate 2: Approve/Deny Requires Pending Escalation

1. Call `codex.status` -> get `active_delegation`.
2. If no active delegation -> error: "No active delegation."
3. Call `poll(active_delegation.job_id)`.
4. If no `pending_escalation` in poll result -> error: "No pending escalation to approve/deny."
5. Use `pending_escalation.request_id` for the `decide` call. Never expose or require internal request fields.

### Gate 3: Never Auto-Promote from Resume

Generic `/delegate` (no args) routes through the state router up to rendering the review and choices. It never calls `promote`. Promotion requires explicit `/delegate promote`.

## Failure Handling

| Condition | Behavior |
|---|---|
| MCP tools unavailable | "codex-collaboration plugin may not be installed. Check `/mcp`." Stop. |
| `codex.status` fails | Report error. Stop. |
| Not in git repository | "Not in a git repository." Stop. |
| No active delegation on resume | "No active delegation. Start one with `/delegate <objective>`." Stop. |
| `poll` returns `job_not_found` | "Job not found. It may have been cleaned up." Stop. |
| `start` returns `busy` | Adopt `active_job_id`. Call `poll`. Route via state router. With the widened busy gate, this may be a runtime-active or attention-active job. |
| `codex.status` reports `auth_status` not `authenticated` | Report auth remediation steps. Stop. |
| `codex.status` reports non-empty `errors` | Report errors. Stop. |
| `codex.status` reports `delegation_status_error` | Report delegation diagnostic. Stop. Do not treat null `active_delegation` as "no active delegation" — the null is from a recovery/query failure. |
| Artifact file unreadable (`Read` fails on path from `artifact_paths`) | Warn that artifacts exist but could not be read. Show available metadata. Do not block review -- partial information is better than none. |
| `promote` returns typed rejection | Render rejection (reason, detail, expected/actual). Guide user to resolve. |
| `decide` returns typed rejection | Render rejection reason. Guide based on reason code. |
| `discard` returns typed rejection | Render rejection. If `job_not_discardable`, explain the allowed states. |
| Reserved subcommand with unexpected args | Error with `start`/`--` escape guidance. |

## Skill Frontmatter

```yaml
---
name: delegate
description: >-
  Delegate coding tasks to Codex for autonomous execution in an isolated worktree,
  then review and promote results. Use when the user wants Codex to DO something
  autonomously. Supports start, poll, approve/deny escalations, promote, and discard.
  Resume with bare /delegate. Trigger on "delegate to codex", "have codex implement",
  "send this to codex", "let codex handle this", or any request for autonomous execution.
argument-hint: '"objective" | start | poll | approve | deny | promote | discard'
user-invocable: true
allowed-tools: Bash, Read, mcp__plugin_codex-collaboration_codex-collaboration__codex.status, mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.start, mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll, mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide, mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.promote, mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.discard
---
```

`Bash` for `git rev-parse --show-toplevel`. `Read` for reading artifact files (`full.diff`, `test-results.json`, `changed-files.json`) from `artifact_paths`.

## Implementation Slices

### Slice 0: Server Enrichment

**Scope:**

1. **New `list_user_attention_required()` method on `DelegationJobStore`.**
   Returns jobs matching the user-attention-required definition. Distinct from `list_active()` which serves the runtime busy gate.

2. **Widened `discard` eligibility.**
   `discard()` currently accepts `promotion_state in (pending, prechecks_failed)`. Widen to also accept `failed` and `unknown` jobs with `promotion_state is None`. This ensures every non-terminal pre-mutation job has a path to terminalization, preventing resume poisoning. Do NOT allow discard when `promotion_state` is `prechecks_passed`, `applied`, or `rollback_needed` -- those are post-mutation or mid-promotion states that require recovery handling, not abandonment.

3. **Widened start busy gate.**
   `codex.delegate.start` currently rejects when `list_active()` returns a runtime-active job. Widen to reject when `list_user_attention_required()` returns any attention-active job. The `busy` response must include the attention-active job's `job_id` and `status` so the skill can route the user to resolve it. This establishes the singleton invariant.

4. **`active_delegation` populated in `codex.status` via MCP-side enrichment.**
   Integration mechanism: the MCP tool dispatch path calls `control_plane.codex_status(repo_root)` as today, then enriches the result with delegation state via a recovery-capable helper:
   - The helper calls `_ensure_delegation_controller()` (which initializes/recovers the controller from durable job state if needed), then queries `list_user_attention_required()`.
   - If the query returns a job: populate `active_delegation` with the job summary.
   - If the query returns no job: `active_delegation` remains null.
   - If `_ensure_delegation_controller()` or the query raises an error: suppress the error, leave `active_delegation` null, set `delegation_status_error` to a diagnostic string. Do NOT append to global `errors` -- existing status consumers (consult, dialogue) treat non-empty `errors` as blocking. Status must never fail because delegation recovery failed.

   Recovery-capability is required because after a server restart within the same Claude session, the delegation controller may not be initialized even though durable job state exists on disk. Status is the skill's resume source -- if status cannot recover/load delegation state, bare `/delegate` would incorrectly report "no active delegation" after a restart.

5. **Normative contract updates.**
   - `contracts.md`: update `active_delegation` description from "Active delegation job summary" to "Current delegation requiring user attention" with the user-attention-required definition.
   - `promotion-protocol.md`: update discard eligibility predicate. Discard is allowed when `promotion_state in {pending, prechecks_failed}`, or when `status in {failed, unknown}` and `promotion_state is None`. It remains rejected for `prechecks_passed`, `applied`, `rollback_needed`, `verified`, `rolled_back`, and `discarded`.
   - `recovery-and-journal.md`: update concurrency text to reflect that the busy gate covers attention-active jobs, not just runtime-active jobs.

6. **Tests** for the new store method, widened discard, widened busy gate, and status enrichment (including error suppression and recovery paths).

### Slice 1: Skill

**Scope:**

- `packages/plugins/codex-collaboration/skills/delegate/SKILL.md` with full grammar, state router, rendering, ceremony gates, failure handling.

**Depends on:** Slice 0.

## Design Decisions

### D1: Stateless skill, server-owned truth

The skill holds no state files. `codex.status.active_delegation` is the resume source. The `/dialogue` skill owns state because it manages containment seeds and subagent orchestration. The delegate skill does not -- the server owns the full job lifecycle.

### D2: Resume-first with explicit verb escape hatches (Option D)

`/delegate` (no args) resumes. Explicit verbs (`poll`, `approve`, `deny`, `promote`, `discard`) are available for precision. `start` and `--` are escape hatches for objectives that collide with reserved words.

### D3: Promotion as explicit ceremony

`/delegate promote` is the only path to primary-workspace mutation. Generic resume never auto-promotes. The review-before-promote gate prevents promoting in the same invocation that materializes the artifact.

### D4: active_delegation means user-attention-active, not runtime-active

The field includes completed jobs awaiting review, failed jobs needing inspection, and partial promotion states needing recovery. This is distinct from `list_active()` which serves the busy gate for runtime-active jobs only.

### D5: Failed/unknown jobs are discardable when pre-mutation

v1 `discard()` is widened (Slice 0) to accept failed/unknown jobs with `promotion_state is None`. This is the pre-mutation case: the job failed before any promotion attempt, so no primary-workspace mutation has occurred. Without this path, a failed job would permanently block new delegations via the widened busy gate. Failed/unknown jobs with post-mutation promotion states (`applied`, `rollback_needed`) require recovery handling and are NOT discardable -- the primary workspace may already be mutated.

### D6: Verb disambiguation rejects ambiguity loudly

Reserved subcommands with unexpected trailing text error with escape guidance. The skill never silently reinterprets ambiguous input. This prevents the most dangerous verbs (`promote`, `approve`) from being context-sensitive.

## References

| Document | Location | Role |
|----------|----------|------|
| T-06 ticket | `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md` | Ticket scope and ACs |
| Contracts | `docs/superpowers/specs/codex-collaboration/contracts.md` | MCP tool surface and response shapes |
| Promotion protocol | `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` | Promotion state machine, preconditions, rollback |
| Recovery and journal | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` | Concurrency limits, journal phases |
| Cross-model delegate skill | `packages/plugins/cross-model/skills/delegate/SKILL.md` | UX precedent (different architecture) |
| Consult skill | `packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md` | Pattern reference for thin skill |
| Dialogue skill | `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` | Pattern reference for heavy skill |
