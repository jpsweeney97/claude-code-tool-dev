# Ticket Contract v1.0

Single source of truth for the ticket plugin. All components (skills, agents, engine) reference this contract.

## 1. Storage

- Active tickets: `docs/tickets/`
- Archived tickets: `docs/tickets/closed-tickets/`
- Audit trail: `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
- Naming: `YYYY-MM-DD-<slug>.md`
- Slug: first 6 words of title, kebab-case, `[a-z0-9-]` only, max 60 chars, sequence suffix on collision
- Bootstrap: missing `docs/tickets/` → empty result for reads; create on first write

## 2. ID Allocation

- Format: `T-YYYYMMDD-NN` (date + 2-digit daily sequence, zero-padded)
- Collision prevention: scan existing tickets for same-day IDs, allocate next NN
- Legacy IDs preserved permanently: `T-NNN` (Gen 3), `T-[A-F]` (Gen 2), slugs (Gen 1)

## 3. Schema

### Required YAML Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Ticket ID (T-YYYYMMDD-NN or legacy) |
| `date` | string | Creation date (YYYY-MM-DD) |
| `status` | string | One of: open, in_progress, blocked, done, wontfix |
| `priority` | string | One of: critical, high, medium, low |
| `source` | object | `{type: string, ref: string, session: string}` |
| `contract_version` | string | "1.0" |

### Optional YAML Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `effort` | string | "" | Estimate (XS, S, M, L, XL or free text) |
| `tags` | list[string] | [] | Categorization tags |
| `blocked_by` | list[string] | [] | IDs of blocking tickets |
| `blocks` | list[string] | [] | IDs of tickets this blocks |
| `defer` | object | null | `{active: bool, reason: string, deferred_at: string}` |

### Required Sections

Problem, Approach, Acceptance Criteria, Verification, Key Files

### Optional Sections

Context, Prior Investigation, Decisions Made, Related, Reopen History

### Section Ordering

Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History

## 4. Engine Interface

Common response envelope: `{state: string, ticket_id: string|null, message: string, data: object}`

Exit codes: 0 (success), 1 (engine error), 2 (validation failure)

### Subcommands

| Subcommand | Input | Output `data` |
|-----------|-------|---------------|
| classify | action, args, session_id, request_origin | intent, confidence, resolved_ticket_id |
| plan | intent, fields, session_id, request_origin | dedup_fingerprint, target_fingerprint, duplicate_of, missing_fields, action_plan |
| preflight | ticket_id, action, session_id, request_origin, classify_confidence, classify_intent, dedup_fingerprint, target_fingerprint | checks_passed, checks_failed |
| execute | action, ticket_id, fields, session_id, request_origin, dedup_override, dependency_override | ticket_path, changes |

### Machine States (14 total: 13 emittable, 1 reserved)

ok_create, ok_update, ok_close, ok_close_archived, ok_reopen, need_fields, duplicate_candidate, preflight_failed, policy_blocked, invalid_transition, dependency_blocked, not_found, escalate, merge_into_existing (reserved)

### Error Codes (11)

need_fields, invalid_transition, policy_blocked, stale_plan, audit_unavailable, duplicate_candidate, parse_error, not_found, dependency_blocked, intent_mismatch, origin_mismatch

## 5. Autonomy Model

Modes: suggest (default), auto_audit, auto_silent (v1.1 only)

Config: `.claude/ticket.local.md` YAML frontmatter

`request_origin`: "user" (ticket_engine_user.py), "agent" (ticket_engine_agent.py), "unknown" (fail closed)

## 6. Dedup Policy

Fingerprint: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`

`normalize()` steps: (1) strip, (2) collapse whitespace, (3) lowercase, (4) remove punctuation except hyphens/underscores, (5) NFC Unicode normalization

Window: 24 hours. Override: `dedup_override: true` with matching `ticket_id`.

### Test Vectors

| Input | Expected Normalized |
|-------|-------------------|
| `"  Hello,  World!  "` | `"hello world"` |
| `"Fix: the AUTH bug..."` | `"fix the auth bug"` |
| `"résumé"` | `"résumé"` (NFC) |
| `"  multiple   spaces  \n  newlines  "` | `"multiple spaces newlines"` |
| `"keep-hyphens and_underscores"` | `"keep-hyphens and_underscores"` |

## 7. Status Transitions

| From | To | Preconditions |
|------|----|---------------|
| open | in_progress | none |
| open | blocked | blocked_by non-empty |
| in_progress | open | none |
| in_progress | blocked | blocked_by non-empty |
| in_progress | done | acceptance criteria present |
| blocked | open | all blocked_by resolved (done or wontfix) |
| blocked | in_progress | all blocked_by resolved |
| * | wontfix | none |
| done | open | reopen_reason required, user-only v1.0 |
| wontfix | open | reopen_reason required, user-only v1.0 |

Non-status edits on terminal tickets (done/wontfix) are allowed without reopening.

### Status Normalization (Legacy)

| Raw | Canonical |
|-----|-----------|
| planning | open |
| implementing | in_progress |
| complete | done |
| closed | done |
| deferred | open (with defer.active: true) |

## 8. Migration

Read-only for legacy formats. Conversion on update (with user confirmation).

### Legacy Generations

| Gen | ID Pattern | Section Renames |
|-----|-----------|----------------|
| 1 | slug | Summary→Problem |
| 2 | T-[A-F] | Summary→Problem |
| 3 | T-NNN | Summary→Problem, Findings→Prior Investigation |
| 4 | T-YYYYMMDD-NN | Proposed Approach→Approach, provenance→source |

### Field Defaults (applied on read)

| Missing Field | Default |
|--------------|---------|
| priority | medium |
| source | {type: "legacy", ref: "", session: ""} |
| effort | "" |
| tags | [] |
| blocked_by/blocks | [] |

## 9. Integration

External consumers read `docs/tickets/*.md` as plain markdown with fenced YAML.
Format uses fenced YAML (```yaml), not YAML frontmatter (---).

## 10. Versioning

`contract_version` in YAML frontmatter. Current: "1.0".
Engine reads all versions; writes latest only.
