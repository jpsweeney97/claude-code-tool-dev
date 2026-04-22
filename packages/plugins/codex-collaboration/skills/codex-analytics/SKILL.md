---
name: codex-analytics
description: Compute analytics views from codex-collaboration outcome and audit streams. Use when user asks for collaboration statistics, delegation metrics, review analytics, consultation history, usage data, or codex stats beyond live runtime status.
user-invocable: true
allowed-tools: Bash, Read, mcp__plugin_codex-collaboration_codex-collaboration__codex.status
---

# Codex Analytics

Compute analytics from the codex-collaboration data streams.

## Data Location

Call `codex.status` with the current `repo_root` to get `plugin_data_path`. The two data files:

- `{plugin_data_path}/analytics/outcomes.jsonl` — advisory and delegation terminal outcomes
- `{plugin_data_path}/audit/events.jsonl` — trust boundary, lifecycle, and security events

Both are append-only JSONL. Use the analytics script (see below) for aggregation, or `Read` for ad-hoc inspection of small files.

## Outcome Record Shapes

Records in `outcomes.jsonl` dispatch on `outcome_type`:

### Advisory outcome (`outcome_type` = `"consult"` or `"dialogue_turn"`)

| Field | Type | Description |
|-------|------|-------------|
| `outcome_id` | string | Unique ID |
| `timestamp` | string | ISO 8601 UTC |
| `outcome_type` | `"consult"` or `"dialogue_turn"` | Discriminator |
| `collaboration_id` | string | Collaboration identity |
| `runtime_id` | string | Advisory runtime that served the turn |
| `context_size` | int or null | Assembled context size in chars |
| `turn_id` | string | Codex turn ID |
| `turn_sequence` | int or null | 1-based sequence (dialogue only) |
| `policy_fingerprint` | string or null | Advisory policy hash |
| `repo_root` | string or null | Repository root path |
| `workflow` | `"consult"` or `"review"` | Workflow discriminator |

**Missing `workflow` field:** treat as `"consult"` (pre-migration rows).

**`outcome_type="dialogue_turn"` rows** always have `workflow="consult"`. Do NOT count dialogue turns in the review breakdown — only `outcome_type="consult"` rows participate in workflow discrimination.

### Delegation terminal outcome (`outcome_type` = `"delegation_terminal"`)

| Field | Type | Description |
|-------|------|-------------|
| `outcome_id` | string | Unique ID |
| `timestamp` | string | ISO 8601 UTC |
| `outcome_type` | `"delegation_terminal"` | Discriminator |
| `collaboration_id` | string | Collaboration identity |
| `runtime_id` | string | Execution runtime that ran the job |
| `job_id` | string | Delegation job ID |
| `terminal_status` | `"completed"`, `"failed"`, or `"unknown"` | Execution terminal state |
| `base_commit` | string | Base commit the delegation branched from |
| `repo_root` | string or null | Primary repository root |

### Unknown outcome types

Skip gracefully. Count and report as metadata:

```
Skipped N records with unknown outcome_type: {type1: count1, type2: count2}
```

Do NOT silently discard. The count is part of the analytics output.

## Audit Event Shape

Records in `events.jsonl`:

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique ID |
| `timestamp` | string | ISO 8601 UTC |
| `actor` | `"claude"`, `"codex"`, `"user"`, `"system"` | Who initiated |
| `action` | string | One of 7 actions (see below) |
| `collaboration_id` | string | Correlation ID |
| `runtime_id` | string | Runtime that served the action |
| `job_id` | string or null | Delegation job (delegation actions only) |
| `request_id` | string or null | Server request (escalation/approval only) |
| `decision` | string or null | `"approve"` or `"deny"` (approval actions only) |

### Audit Actions

| Action | Meaning | Decision field |
|--------|---------|----------------|
| `consult` | Advisory consultation | — |
| `dialogue_turn` | Dialogue turn | — |
| `delegate_start` | Delegation job created | — |
| `escalate` | Execution needs user decision | — |
| `approve` | User resolved escalation | `decision` = `"approve"` or `"deny"` |
| `promote` | User promoted delegate work | `decision` = `"approve"` |
| `discard` | User discarded delegate work | — |

**IMPORTANT:** The `approve` action carries BOTH approve and deny decisions in its `decision` field. There is no `action="deny"`. To count approvals vs denials, filter `action="approve"` and group by `decision`.

## Analytics Script

Run the aggregation script via Bash with the two data file paths as positional arguments:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analytics.py <outcomes.jsonl> <events.jsonl>
```

## Known Limitations

Two Reliability/security metrics are not yet available:

- **Credential blocks/shadows:** Credential interception logs to the operation journal for recovery, not to the audit stream. Requires new audit emission points to become reportable.
- **Promotion rejections:** Promotion precondition failures return rejection responses but do not emit audit records. Requires new audit emission at rejection sites.

The recipe outputs these as `unavailable (not emitted to audit stream)` rather than silently omitting them.

## Output Format

Present each view as a markdown table. Group views under `##` headers. Include the data file paths and total record counts at the top for transparency.
