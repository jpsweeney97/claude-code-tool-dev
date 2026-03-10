# T-20260302-03: ticket audit repair command

```yaml
id: T-20260302-03
date: "2026-03-02"
status: done
priority: medium
effort: "S (1-2 sessions)"
tags: [ticket-plugin, audit, reliability]
blocked_by: []
blocks: []
related: [T-20260302-01]
ticket_id: T-20260302-03
closed_at: "2026-03-10"
closed_by: "PR #69"
notes: "Dry-run default + --fix flag + 5 new tests. All acceptance criteria met."
```

## Problem

The per-session audit trail (`docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`) is the authoritative source for session-cap counting. If an audit file becomes corrupted (non-JSON lines, permission errors, truncated writes beyond trailing partial lines), autonomous creates are blocked with `policy_blocked` (fail-closed). There is no recovery path — the user must manually fix or delete the corrupted file.

## Context

The deeper review Codex dialogue (thread `019caf7f`) specified corruption handling:
- Trailing partial line (incomplete write): tolerated — skip and count preceding complete lines
- Other corruption (non-JSON, permission errors): fail closed for autonomous, proceed with warning for user
- "Explicit repair path: `ticket audit repair` (implementation ticket)" — this ticket

The fail-closed behavior is correct for safety, but without a repair command, a single corrupted audit file can permanently block autonomous ticket creation for that session (or any session if the corruption is in the directory structure).

## Prior Investigation

- Audit trail format: one JSONL file per session per day, append-only
- Corruption sources: interrupted writes (process kill), disk full, permission changes, concurrent write races
- Current handling: trailing partial line tolerated, all other corruption blocks autonomous creates

## Approach

Implement `ticket audit repair` as a subcommand of the engine (called via ticket-ops skill):

1. **Scan:** Read all audit files, identify corrupted entries
2. **Report:** Show summary of corruption found (which files, which lines, what type)
3. **Fix options:**
   - `--dry-run` (default): report only, no changes
   - `--fix`: remove corrupted lines, preserve valid entries, write backup of original
4. **Backup:** Before any modification, copy corrupted file to `<filename>.bak`

### Decisions Made
- Repair is explicit user action, never automatic — fail-closed is the correct default
- Backup before modification — audit trail is evidence, not disposable

## Acceptance Criteria
- [x] `ticket audit repair` scans all audit files and reports corruption
- [x] `--dry-run` mode shows what would be fixed without modifying files
- [x] `--fix` mode removes corrupted lines and creates `.bak` backup
- [x] After repair, session-cap counting works correctly for affected sessions
- [x] Tests cover: trailing partial line (tolerated), non-JSON line (removed), empty file (valid), permission error (reported)

## Key Files
| File | Role | Look For |
|------|------|----------|
| `docs/plans/2026-03-02-ticket-plugin-design.md:460` | Audit trail spec | Per-session file layout, corruption handling |
| (future) `ticket/scripts/ticket_engine_core.py` | Engine logic | `engine_count_session_creates()` function |
| (future) `ticket/scripts/ticket_triage.py` | Audit reporting | Audit trail scan for triage dashboard |
