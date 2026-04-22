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

Both are append-only JSONL. Read with `Bash` using `cat` + `python -c` for aggregation, or `Read` for small files.

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

## Analytics Recipe

Use this Python aggregation via Bash. Replace `{outcomes}` and `{audit}` with the actual file paths.

````bash
python3 -c "
import json, sys
from collections import Counter
from pathlib import Path

outcomes_path = Path('{outcomes}')
audit_path = Path('{audit}')

# --- Parse outcomes ---
by_type = Counter()
workflow_counts = Counter()
context_sizes = []
fingerprints = Counter()
delegation_terminals = []
unknown_types = Counter()
total_outcome_records = 0
for line in (outcomes_path.read_text().strip().split('\n') if outcomes_path.exists() else []):
    if not line.strip(): continue
    r = json.loads(line)
    total_outcome_records += 1
    ot = r.get('outcome_type', '')
    if ot in ('consult', 'dialogue_turn'):
        by_type[ot] += 1
        cs = r.get('context_size')
        if cs is not None: context_sizes.append(cs)
        fp = r.get('policy_fingerprint')
        if fp is not None: fingerprints[fp] += 1
        if ot == 'consult':
            wf = r.get('workflow', 'consult')
            workflow_counts[wf] += 1
    elif ot == 'delegation_terminal':
        by_type[ot] += 1
        delegation_terminals.append(r)
    else:
        unknown_types[ot] += 1

# --- Parse audit ---
audit_actions = Counter()
decisions = Counter()
promote_count = 0
discard_count = 0
delegate_starts = {}
total_audit_records = 0
for line in (audit_path.read_text().strip().split('\n') if audit_path.exists() else []):
    if not line.strip(): continue
    r = json.loads(line)
    total_audit_records += 1
    action = r.get('action', '')
    audit_actions[action] += 1
    if action == 'approve':
        decisions[r.get('decision', 'unknown')] += 1
    elif action == 'promote':
        promote_count += 1
    elif action == 'discard':
        discard_count += 1
    elif action == 'delegate_start':
        jid = r.get('job_id')
        if jid: delegate_starts[jid] = r.get('timestamp', '')

# --- Output ---
print('## Data Sources')
print(f'- Outcomes: \`{outcomes_path}\` ({total_outcome_records} records)')
print(f'- Audit: \`{audit_path}\` ({total_audit_records} records)')

print('\n## Usage')
print('| Metric | Count |')
print('|--------|-------|')
for t in ('consult', 'dialogue_turn', 'delegation_terminal'):
    print(f'| {t} | {by_type[t]} |')
delegate_start_count = audit_actions['delegate_start']
print(f'| delegate_start | {delegate_start_count} |')
review_count = workflow_counts['review']
print(f'| reviews | {review_count} |')

if unknown_types:
    unk_total = sum(unknown_types.values())
    unk_detail = dict(unknown_types)
    print(f'\n**Skipped {unk_total} records with unknown outcome_type:** {unk_detail}')

print('\n## Reliability and Security')
total_del = len(delegation_terminals)
completed = sum(1 for d in delegation_terminals if d.get('terminal_status') == 'completed')
failed = sum(1 for d in delegation_terminals if d.get('terminal_status') == 'failed')
unknown = sum(1 for d in delegation_terminals if d.get('terminal_status') == 'unknown')
rate = f'{completed}/{total_del} ({completed*100//total_del}%)' if total_del else 'n/a'
esc_count = audit_actions['escalate']
esc_approve = decisions['approve']
esc_deny = decisions['deny']
print('| Metric | Value |')
print('|--------|-------|')
print(f'| Delegation success rate | {rate} |')
print(f'| Failed | {failed} |')
print(f'| Unknown | {unknown} |')
print(f'| Escalations | {esc_count} |')
print(f'| Escalation approvals | {esc_approve} |')
print(f'| Escalation denials | {esc_deny} |')
print(f'| Credential blocks/shadows | unavailable (not emitted to audit stream) |')
print(f'| Promotion rejections | unavailable (not emitted to audit stream) |')

print('\n## Context and Runtime')
if context_sizes:
    s = sorted(context_sizes)
    print('| Metric | Value |')
    print('|--------|-------|')
    print(f'| Min context | {s[0]} |')
    print(f'| Max context | {s[-1]} |')
    print(f'| Mean context | {sum(s)//len(s)} |')
    print(f'| p50 context | {s[len(s)//2]} |')
else:
    print('No context size data.')

if fingerprints:
    print('\n### Policy Fingerprints')
    print('| Fingerprint | Count |')
    print('|-------------|-------|')
    for fp, count in fingerprints.most_common():
        print(f'| `{fp}` | {count} |')
else:
    print('\nNo policy fingerprint data.')

print('\n## Delegation Lifecycle')
print('| Status | Count |')
print('|--------|-------|')
print(f'| started | {len(delegate_starts)} |')
print(f'| completed | {completed} |')
print(f'| failed | {failed} |')
print(f'| unknown | {unknown} |')
print(f'| promoted | {promote_count} |')
print(f'| discarded | {discard_count} |')
print(f'| escalations | {esc_count} |')

print('\n## Review')
consult_count = workflow_counts['consult']
ratio = str(review_count) + ':' + str(consult_count) if consult_count else 'n/a'
print('| Metric | Value |')
print('|--------|-------|')
print(f'| Review consultations | {review_count} |')
print(f'| workflow=consult | {consult_count} |')
print(f'| workflow=review | {review_count} |')
print(f'| Review:consult ratio | {ratio} |')
"
```
````

## Known Limitations

Two Reliability/security metrics are not yet available:

- **Credential blocks/shadows:** Credential interception logs to the operation journal for recovery, not to the audit stream. Requires new audit emission points to become reportable.
- **Promotion rejections:** Promotion precondition failures return rejection responses but do not emit audit records. Requires new audit emission at rejection sites.

The recipe outputs these as `unavailable (not emitted to audit stream)` rather than silently omitting them.

## Output Format

Present each view as a markdown table. Group views under `##` headers. Include the data file paths and total record counts at the top for transparency.
