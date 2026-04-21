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

# /delegate

Stateless state router for the codex-collaboration delegation lifecycle. Each invocation: determine intent, discover state from the server, route to the appropriate MCP tool, render the result, exit with next-step guidance.

**No skill-owned state files.** The server is the single source of truth for job lifecycle. `codex.status` -> `active_delegation` is the resume source.

## Scope

**In scope:** Start delegation, poll progress, approve/deny escalations, review completed work, promote to primary workspace, discard unwanted results.

**Out of scope:** Briefing enrichment, context assembly, dialogue orchestration. Those belong to the server and other skills. Do NOT port cross-model delegation features into this skill.

## Procedure

### 1. Determine repo root

Run via Bash:

```bash
git rev-parse --show-toplevel
```

If the command fails (exit code non-zero): report "Not in a git repository." and **stop**. Do NOT fall back to the current directory.

Use the output as `repo_root` for all subsequent calls.

### 2. Parse arguments

Parse `$ARGUMENTS` using this grammar, evaluated in this exact order:

| Priority | Pattern | Intent | Action |
|----------|---------|--------|--------|
| 1 | Empty / no args | **Resume** | Go to step 3 (status preflight), then step 5 (resume routing) |
| 2 | `-- ` prefix | **Start** | Strip `-- `, remainder is `objective`. Go to step 4 (start routing) |
| 3 | `start ` prefix | **Start** | Strip `start `, remainder is `objective`. Go to step 4 (start routing) |
| 4 | First token is `poll` | **Poll** | Optional second token is `job_id`. Go to step 7 (poll verb) |
| 5 | First token is `approve` | **Approve** | Go to step 8 (approve verb) |
| 6 | First token is `deny` | **Deny** | Go to step 9 (deny verb) |
| 7 | First token is `promote` | **Promote** | Go to step 10 (promote verb) |
| 8 | First token is `discard` | **Discard** | Optional second token is `job_id`. Go to step 11 (discard verb) |
| 9 | Anything else | **Start** | Entire input is `objective`. Go to step 4 (start routing) |

**Disambiguation rule:** If a reserved subcommand (`poll`, `approve`, `deny`, `promote`, `discard`) has unexpected trailing text beyond an optional `job_id` (for `poll` and `discard`), **reject** with escape guidance:

> "`{word}` is a control command. To delegate an objective starting with "{word}", use `/delegate start {word} {rest}` or `/delegate -- {word} {rest}`."

Do NOT silently reinterpret ambiguous input. `promote` and `approve` must never be context-sensitive.

### 3. Status preflight

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.status` with `repo_root`.

Check in this order:

1. **`auth_status`** -- if not `"authenticated"`: report auth remediation steps and **stop**.
2. **`errors`** -- if non-empty: report errors and **stop**.
3. **`delegation_status_error`** -- if present: report the delegation diagnostic and **stop**. Do NOT treat null `active_delegation` as "no active delegation" when `delegation_status_error` is set -- the null is caused by a recovery/query failure, not by absence of jobs.

### 4. Start routing

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.start` with `repo_root` and `objective`.

Handle the result based on its shape:

**Normal start** (job running):
- Render `job_id` prominently, status, `base_commit`.
- Exit with: "Run `/delegate` to check progress."

**`escalated: true`** (immediate escalation):
- Enter escalation rendering (step 6c).

**`busy: true`** (attention-active job exists):
- Adopt `active_job_id` from the busy response.
- Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll` with `active_job_id`.
- Route via the state router (step 6).

Always render `job_id` prominently on start for debugging and explicit verb use.

### 5. Resume routing

Extract `active_delegation` from the status result (step 3).

- If `active_delegation` is null: "No active delegation. Start one with `/delegate <objective>`." **Stop.**
- If `attention_job_count` > 1: warn "Multiple jobs require attention ({count}). Operating on the most recent." Continue with the returned job.
- Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll` with `active_delegation.job_id`.
- Route via the state router (step 6).

### 6. State router

Evaluate `promotion_state` first when non-null. Fall through to job `status` only when `promotion_state` is null.

#### 6a. Tier 1 -- Terminal promotion states

Terminal states are excluded from `active_delegation`. Reachable only via explicit `promote`, `discard`, or direct `poll` with a `job_id` argument.

| `promotion_state` | Rendering |
|---|---|
| `verified` | "Promotion succeeded. {changed_files_count} files applied to primary workspace." |
| `discarded` | "Job discarded. No workspace changes." |
| `rolled_back` | "Promotion rolled back. Workspace restored to pre-promotion state." |

#### 6b. Tier 2 -- Recovery/partial promotion states

| `promotion_state` | Rendering |
|---|---|
| `rollback_needed` | "Post-apply verification failed. Rollback needed." Render verification failure details from `poll.detail`. |
| `applied` | "Diff applied but not yet verified. Partial promotion state -- may indicate crash recovery." |
| `prechecks_passed` | "Prechecks passed but apply not yet completed. May normalize to `pending` after recovery." |

#### 6c. Tier 3 -- User-decision promotion states

| `promotion_state` | Rendering |
|---|---|
| `pending` | Render full review (step 6e). Exit with `/delegate promote` and `/delegate discard` choices. Do NOT call promote. |
| `prechecks_failed` | "Previous promotion prechecks failed. Resolve the blocking condition, then retry `/delegate promote`, or `/delegate discard`." Do NOT render a specific rejection reason -- it was returned at failure time and is not persisted on the job model. |

#### 6d. Tier 4 -- Job runtime status (promotion_state is null)

| `status` | Rendering |
|---|---|
| `queued` / `running` | Render job_id, status, base_commit. "Run `/delegate` to check progress." |
| `needs_escalation` | Render escalation (step 6f). |
| `failed` / `unknown` | Render `poll.detail` and inspection snapshot if available. "Inspect artifacts. `/delegate discard` to clear, then start a new delegation if needed." |
| `completed` with null `promotion_state` | **Inconsistent state.** Report: "Job completed but promotion state is missing. This is a legacy or corrupted state that cannot be promoted or discarded. Inspect artifacts manually via `/delegate poll {job_id}`. To clear, the job store entry must be resolved outside the skill." Do NOT render promote/discard choices. |

**`failed`/`unknown` with post-mutation `promotion_state`** (`applied`, `rollback_needed`): "Recovery required. Workspace may have been mutated." Do NOT offer discard for post-mutation states.

#### 6e. Review rendering (completed + pending)

Render in this order:

**1. Job metadata:**

```
Job: {job_id}
Status: completed | Promotion: pending
Base commit: {base_commit}
Artifact hash: {artifact_hash}
Reviewed at: {inspection.reviewed_at}
```

**2. Changed files** from `inspection.changed_files`:

```
Changed files ({count}):
  src/auth/handler.py
  src/auth/middleware.py
  tests/test_auth.py
```

**3. Test results** -- read `test-results.json` from `artifact_paths` via the Read tool:

- If tests recorded: summarize status (pass/fail), command, key results.
- If `not_recorded` stub: "Test results: not recorded by execution agent."

**4. Diff** -- read `full.diff` from `artifact_paths` via the Read tool:

- ~200 lines or fewer: include full diff.
- Larger: summarize per file (additions/deletions counts), show representative hunks for the most significant changes, note the artifact path for manual inspection.

The 200-line threshold is a soft heuristic for when the diff would crowd out review judgment.

**5. Claude's assessment:** Independent evaluation of correctness, risks, suspicious patterns, and missing test coverage. When the full diff is shown, evaluate whether promotion is reasonable. When the diff is summarized (large diffs), state that the assessment is based on a partial view and cannot fully evaluate promotion safety. Do NOT produce strong "promotion is reasonable" conclusions from summarized diffs.

**6. Choices:**

```
Next steps:
  /delegate promote  -- apply these changes to primary workspace
  /delegate discard  -- discard without applying
  Read specific artifact: {artifact_path}
```

#### 6f. Escalation rendering

**1. Header:** escalation kind, request_id.

**2. Requested scope** -- render per kind:

| Kind | Rendering |
|------|-----------|
| `command_approval` | Show the command being requested. |
| `file_change` | Show the file path and change type. |
| `request_user_input` | Show what the agent is asking. Include question identifiers from `requested_scope`. |
| unknown kind | Render raw `requested_scope` JSON with a note that this is an unrecognized escalation type. |

**3. Agent context** -- if `agent_context` is non-null, show what the agent was doing when the escalation triggered.

**4. Decision prompt:**

```
Available decisions: approve, deny
  /delegate approve  -- approve this escalation
  /delegate deny     -- deny this escalation
```

**`request_user_input` handling:** For this kind, bare `/delegate approve` is insufficient -- the server rejects approve without answers.

1. Render what the agent is asking, including question identifiers from `requested_scope`.
2. Tell the user: "Please provide your answer, then run `/delegate approve`."
3. When the user provides their answer (in conversation) and invokes `/delegate approve`: construct the `answers` parameter from the question identifiers and the user's response in conversation context. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide` with `answers`.
4. If the conversation does not contain a clear answer to the rendered questions, ask the user to clarify before calling `decide`.
5. Bare `/delegate deny` works without answers for all escalation kinds.

The skill does NOT parse answer syntax from the command line. Claude mediates between the user's natural language response and the `decide` tool's structured `answers` parameter. The explicit `/delegate approve` invocation is the trigger -- the user's answer is sourced from conversation context, not from command arguments.

**Escalation continuation:** After each `decide` call, if the result contains a new `pending_escalation`: render it and ask for the next decision. Never auto-chain approvals or denials. Each escalation requires explicit user input before the next `decide` call.

If `decide` returns `resumed: true` with no `pending_escalation`: the job is running autonomously. Render status and exit with "Run `/delegate` to check progress."

## Ceremony Gates

### Gate 1: Review-before-promote

When `/delegate promote` is invoked:

1. Run status preflight (step 3). Read `active_delegation.artifact_hash` (this is the **pre-poll** state).
2. If `active_delegation` is null or `active_delegation.job_id` does not match the target: "This job is not the active delegation. Use bare `/delegate promote` to promote the active job." Render read-only poll if a job_id was provided. Do NOT call promote.
3. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll` with the job_id.
4. **If pre-poll `artifact_hash` was null:** Poll triggered materialization. Render full review (step 6e). Exit with: "Review complete. Run `/delegate promote` again to apply." Do NOT promote.
5. **If pre-poll `artifact_hash` was non-null:** Render brief confirmation: "Promoting job `{job_id}`: {changed_files_count} files, artifact hash `{hash_prefix}...`". Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.promote` with `job_id`. Render result via state router (step 6).

Promote only routes through `active_delegation`. The singleton invariant guarantees that if a job is promotable, it IS the `active_delegation`.

### Gate 2: Approve/deny requires pending escalation

1. Run status preflight (step 3). Extract `active_delegation`.
2. If no active delegation: "No active delegation." **Stop.**
3. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll` with `active_delegation.job_id`.
4. If no `pending_escalation` in poll result: "No pending escalation to approve/deny." **Stop.**
5. Use `pending_escalation.request_id` for the `decide` call. Never expose or require internal request fields from the user.

### Gate 3: Never auto-promote from resume

Generic `/delegate` (no args) routes through the state router up to rendering the review and choices. It never calls `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.promote`. Promotion requires explicit `/delegate promote`.

## Verb-Specific Procedures

### Poll (`/delegate poll [job_id]`)

1. Run status preflight (step 3).
2. If `job_id` provided: use it directly. If not: extract `active_delegation.job_id` from status. If no active delegation: "No active delegation. Start one with `/delegate <objective>`." **Stop.**
3. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll` with `job_id`.
4. Route via state router (step 6).

Poll is the only verb that allows inspecting arbitrary jobs outside the active delegation. This is read-only and safe.

### Approve (`/delegate approve`)

1. Execute Gate 2 (approve/deny requires pending escalation).
2. Determine escalation kind from `pending_escalation`.
3. If kind is `request_user_input`: construct `answers` from conversation context and question identifiers. If no clear answer in conversation: ask user to clarify. **Stop.**
4. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide` with `job_id`, `request_id`, `"approve"`, and `answers` (if applicable).
5. Handle escalation continuation (step 6f).

### Deny (`/delegate deny`)

1. Execute Gate 2 (approve/deny requires pending escalation).
2. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.decide` with `job_id`, `request_id`, `"deny"`.
3. Handle escalation continuation (step 6f).

### Promote (`/delegate promote`)

Execute Gate 1 (review-before-promote). The gate handles all routing.

### Discard (`/delegate discard [job_id]`)

1. Run status preflight (step 3).
2. If `job_id` provided: use it. If not: extract `active_delegation.job_id` from status. If no active delegation: "No active delegation." **Stop.**
3. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.discard` with `job_id`.
4. If success: render terminal state via state router (step 6a).
5. If typed rejection (`job_not_discardable`): render rejection. Explain allowed states: discard accepts `promotion_state` in `{pending, prechecks_failed}`, or `status` in `{failed, unknown}` with null `promotion_state`. Post-mutation states (`applied`, `rollback_needed`) require recovery, not discard.

## Failure Handling

| Condition | Behavior |
|---|---|
| MCP tools unavailable | "codex-collaboration plugin may not be installed. Check `/mcp`." **Stop.** |
| `codex.status` fails | Report error. **Stop.** |
| Not in git repository | "Not in a git repository." **Stop.** |
| `auth_status` not `authenticated` | Report auth remediation steps. **Stop.** |
| Non-empty `errors` | Report errors. **Stop.** |
| `delegation_status_error` present | Report delegation diagnostic. **Stop.** Do NOT treat null `active_delegation` as "no active delegation." |
| No active delegation on resume | "No active delegation. Start one with `/delegate <objective>`." **Stop.** |
| `poll` returns `job_not_found` | "Job not found. It may have been cleaned up." **Stop.** |
| `start` returns `busy` | Adopt `active_job_id`. Call poll. Route via state router. |
| Artifact file unreadable (Read fails on path from `artifact_paths`) | Warn that artifacts exist but could not be read. Show available metadata. Do NOT block review -- partial information is better than none. |
| `promote` returns typed rejection | Render rejection (reason, detail, expected/actual). Guide user to resolve. |
| `decide` returns typed rejection | Render rejection reason. Guide based on reason code. |
| `discard` returns typed rejection | Render rejection. If `job_not_discardable`, explain allowed states. |
| Reserved subcommand with unexpected args | Reject with `start`/`--` escape guidance. |
