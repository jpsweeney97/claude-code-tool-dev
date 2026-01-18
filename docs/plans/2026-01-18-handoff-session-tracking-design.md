# Handoff Session Tracking Design

Upgrade the handoff skill to leverage `${CLAUDE_SESSION_ID}` for traceability and lineage tracking.

## Goals

1. **Traceability** — Know which session created each handoff
2. **Lineage tracking** — Chain sessions together via `resumed_from` links

## Non-Goals

- Filename collision prevention (timestamp-based remains)
- Duplicate handoff prevention per session
- Bidirectional links (updating original handoff when resumed)

## Frontmatter Changes

Two new optional fields:

```yaml
---
date: 2026-01-18
time: "14:30"
created_at: "2026-01-18T14:30:00Z"
project: my-app
branch: feat/auth-middleware
commit: 8709e5d
title: Auth middleware implementation
session_id: 470bbb1a-7a5c-4465-81f5-8d5ba468aea7    # NEW: always present
resumed_from: ~/.claude/handoffs/my-app/.archive/2026-01-17_16-45_auth-design.md  # NEW: if resumed
files:
  - src/auth/middleware.py
---
```

| Field | Presence | Description |
|-------|----------|-------------|
| `session_id` | Always | Session that created this handoff. Uses `${CLAUDE_SESSION_ID}` substitution. |
| `resumed_from` | Conditional | Archive path of handoff loaded via `/resume` earlier in session. Omitted if session didn't resume from a handoff. |

Existing handoffs without these fields remain valid.

## State Tracking

### State File

| Attribute | Value |
|-----------|-------|
| Path | `~/.claude/.session-state/handoff-<session-id>` |
| Format | Plain text, single line |
| Contents | Absolute path to the archived handoff |
| Encoding | UTF-8 |
| Permissions | User read/write (0600) |

Example contents:
```
/Users/jp/.claude/handoffs/my-app/.archive/2026-01-17_16-45_auth-design.md
```

### Workflow

**When `/resume` runs:**

1. Read and display the handoff content
2. Create `~/.claude/handoffs/<project>/.archive/` if needed
3. Move handoff to `.archive/<filename>`
4. Create `~/.claude/.session-state/` if needed
5. Write archive path to `~/.claude/.session-state/handoff-<session-id>`

**When `/handoff` runs:**

1. Check for state file at `~/.claude/.session-state/handoff-<session-id>`
2. If exists, read the archive path
3. Include as `resumed_from` in frontmatter
4. Write handoff file
5. Delete state file after successful write

## Archive Behavior

| Aspect | Behavior |
|--------|----------|
| Location | `~/.claude/handoffs/<project>/.archive/` |
| `/list-handoffs` | Excludes archive (shows active only) |
| `/resume` (no args) | Finds latest in active directory only |
| `/resume <path>` | Can explicitly load from archive |
| Retention | 90 days (vs 30 days for active) |

## Retention Policy

| Location | Retention |
|----------|-----------|
| Active handoffs (`~/.claude/handoffs/<project>/`) | 30 days |
| Archived handoffs (`~/.claude/handoffs/<project>/.archive/`) | 90 days |
| State files (`~/.claude/.session-state/`) | 24 hours |

SessionStart hook handles all pruning silently.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Multiple resumes in one session | State file overwritten; most recent path used |
| Resume from archive | File stays in archive; that path written to state |
| No follow-up handoff | State file orphaned; cleaned after 24 hours |
| Session compaction | State file survives (external); `${CLAUDE_SESSION_ID}` substituted at load time |
| Cross-project resume | `resumed_from` points to other project's archive; new handoff goes in current project |
| Missing archive directory | `/resume` creates it before moving file |

## Lineage Traversal

Example chain:

```
Session C's handoff:
  session_id: ccc-111
  resumed_from: ~/.claude/handoffs/app/.archive/B.md

B.md (in archive):
  session_id: bbb-222
  resumed_from: ~/.claude/handoffs/app/.archive/A.md

A.md (in archive):
  session_id: aaa-333
  (no resumed_from — origin)
```

Follow `resumed_from` links to traverse history backward.

## Changes Summary

| Component | Change |
|-----------|--------|
| Frontmatter | Add `session_id` (always), `resumed_from` (conditional) |
| `/resume` | Move to `.archive/` instead of trash; write state file |
| `/handoff` | Read state file if exists; include `resumed_from`; delete state file |
| `/list-handoffs` | Exclude `.archive/` from listing |
| SessionStart hook | Add archive pruning (90d) and state file pruning (24h) |

## What Doesn't Change

- Filename format (timestamp-based)
- Section checklist
- Signal phrase detection
- `/handoff <title>` argument handling
- Basic verification steps
