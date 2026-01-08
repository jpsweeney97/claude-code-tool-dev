# Handoff Skill v2 — Design Document

**Date:** 2026-01-08
**Status:** Design complete, ready for implementation
**Supersedes:** Current handoff skill (v1)

## Overview

Session continuity for solo developers working with Claude. Capture context when stopping, restore it when resuming — optimized for both human recall and Claude context injection.

**Core Promise:** One action to save, zero actions to resume (when recent).

**Key Changes from v1:**
- Claude writes handoffs directly (no write script) — eliminates schema drift
- Single storage location (`~/.claude/handoffs/<project>/`) — no symlinks
- Guided judgment for content — 15 possible sections, include only what's relevant
- Smart resume — auto-inject if <24h, ask if older, always signal state
- Time-based retention (30 days) — aligns with "how stale is too stale"
- Session ID in frontmatter — trace back to transcript if needed
- Spec-compliant structure — follows skills-as-prompts strict spec

---

## When to Use

- End of a work session when you want to preserve context for next time
- When Claude prompts after you say "wrap this up", "handoff", or "new session"
- When resuming work on a project after any break

## When NOT to Use

- Trivial sessions with no meaningful decisions or progress
- When context is already captured elsewhere (e.g., detailed commit messages)
- Mid-session checkpoints — handoffs are for session boundaries

**STOP Condition:** If user declines a prompted handoff or resume offer, do not re-prompt or proceed with the action.

---

## Inputs

### Required
- **Active session** — Must have session context to capture
- **Project directory** — Must be in a directory (for project identification)

### Optional
- **Title argument** — `/handoff <title>` to specify slug
- **Git repository** — Enables branch/commit in frontmatter

### Constraints/Assumptions
- Write access to `~/.claude/handoffs/`
- Python 3 available (for read.py SessionStart hook)
- No network required

---

## Outputs

### Artifacts

| Artifact | Location | Format |
|----------|----------|--------|
| Handoff document | `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md` | Markdown with YAML frontmatter |
| Resume injection | Session start | Text block with handoff content or prompt |

### Definition of Done (Objective Checks)

| Action | DoD |
|--------|-----|
| Create handoff | File exists at expected path AND frontmatter parses as valid YAML AND contains required fields (date, time, session_id, project, title) |
| Resume (recent) | Claude's first message acknowledges the handoff title |
| Resume (older) | Claude asks whether to resume before proceeding |
| Prune | `find ~/.claude/handoffs/<project> -mtime +30 -type f` returns empty |

---

## Procedure

### Creating a Handoff

1. User runs `/handoff [optional-title]` OR says "wrap this up" / "handoff" / "new session"
2. If triggered by signal phrase, Claude asks: "Create a handoff before ending?"
3. If user confirms (or used explicit command), Claude gathers session context
4. Claude selects relevant sections using guided judgment (see Section Checklist below)
5. Claude generates markdown with frontmatter
6. Claude writes to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
7. Claude confirms: "Handoff saved: <title> (N decisions, N changes, N next steps)"

### Resuming from Handoff

1. SessionStart hook runs `read.py`
2. Script finds most recent handoff for current project
3. Script prunes files older than 30 days
4. Script outputs based on recency (see Decision Point 2)
5. Claude acknowledges state and offers to continue

---

## Decision Points

### Decision Point 1: Prompted Handoff
```
If user says "wrap this up", "handoff", or "new session",
  then offer to create a handoff: "Create a handoff before ending?"
Otherwise, do not prompt — wait for explicit /handoff command.
```

### Decision Point 2: Resume Recency
```
If most recent handoff is <24 hours old,
  then auto-inject and acknowledge: "[Resuming: <title>]"
Otherwise if handoff exists but >24 hours old,
  then ask: "Found handoff from <date>: <title>. Resume from this?"
Otherwise (no handoff),
  then acknowledge: "[No recent handoff for this project]"
```

### Decision Point 3: Title Slug
```
If user provides argument with /handoff (e.g., /handoff auth middleware),
  then use that as the title slug.
Otherwise, generate a descriptive slug based on session content.
```

---

## Verification

### Quick Checks

| After | Quick Check | Expected Result |
|-------|-------------|-----------------|
| Creating handoff | File exists at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md` | File present with valid frontmatter |
| Creating handoff | Frontmatter contains required fields | `date`, `time`, `session_id`, `project`, `title` all present |
| Resuming | SessionStart hook outputs one of three states | `[Resuming: ...]` or `[Found handoff...]` or `[No recent handoff...]` |
| Pruning | No files older than 30 days in project directory | `find` returns empty |

---

## Troubleshooting

| Symptom | Likely Cause | Next Steps |
|---------|--------------|------------|
| Handoff not auto-injected on session start | SessionStart hook not configured | Add hook configuration to settings.json |
| "Permission denied" when writing | Directory permissions | Run `chmod 755 ~/.claude/handoffs` |
| Old handoff injected instead of recent | Project name collision | Check `~/.claude/handoffs/` for duplicate project names |
| Empty handoff created | Session had no meaningful content | Correct behavior — skip trivial sessions |
| Handoff missing expected sections | Guided judgment deemed them irrelevant | Re-run `/handoff` and mention the topic explicitly |

---

## Storage & File Structure

**Location:** `~/.claude/handoffs/<project>/`

Where `<project>` is the git root directory name (or current directory name if not a git repo).

**Filename format:** `YYYY-MM-DD_HH-MM_<title-slug>.md`

**Example structure:**
```
~/.claude/handoffs/
├── my-app/
│   ├── 2026-01-08_14-30_auth-middleware.md
│   ├── 2026-01-07_16-45_database-migration.md
│   └── 2026-01-05_10-00_initial-setup.md
└── other-project/
    └── 2026-01-06_09-15_api-refactor.md
```

**Retention:** Files older than 30 days are pruned automatically when read.py runs.

---

## Handoff Document Format

### Frontmatter

```yaml
---
date: 2026-01-08
time: "14:30"
session_id: fa613a83-7477-4b28-afcd-6759e1d564c9
project: my-app
branch: feat/auth-middleware
commit: 8709e5d
title: Auth middleware implementation
files:
  - src/auth/middleware.py
  - src/auth/jwt.py
---
```

### Body — Guided Judgment Sections

Claude includes only sections relevant to the session. Empty sections are omitted.

**Section Checklist (include when relevant):**

| Section | When to Include |
|---------|-----------------|
| Goal | Session had a clear objective |
| Decisions | Choices made with tradeoffs/reasoning |
| Changes | Files created/modified with purpose |
| Gotchas | Something unexpected or tricky discovered |
| Next Steps | Work is incomplete, clear follow-ups exist |
| Blockers | Stuck on something, waiting for resolution |
| Context | Background info future-you/Claude needs |
| Rejected Approaches | Things tried that didn't work |
| Open Questions | Unresolved questions that need answering |
| References | Important files, docs, URLs consulted |
| Artifacts | Reusable things created (prompts, schemas, scripts) |
| Dependencies | Waiting on external things (PR review, API access) |
| Learnings | Insights gained, things figured out |
| Risks | Known concerns or fragile areas to watch |
| User Preferences | How user likes things done (discovered this session) |

### Example Handoff

```markdown
# Handoff: Auth middleware implementation

## Goal
Implement JWT-based authentication middleware for the API.

## Decisions
- **JWT over sessions:** Stateless scales horizontally without shared session store.
- **RS256 signing:** Public key verification avoids sharing secrets across services.

## Changes
- `src/auth/middleware.py` — Request authentication decorator
- `src/auth/jwt.py` — Token generation and validation

## Gotchas
- PyJWT requires `cryptography` package for RS256. Plain PyJWT only supports HS256.

## Next Steps
1. Create `/auth/refresh` endpoint
2. Add middleware to protected routes
3. Write integration tests
```

---

## Tooling Architecture

**Principle:** Scripts only where Claude can't act (SessionStart hook). Claude handles everything else directly.

| Component | Implementation | Purpose |
|-----------|----------------|---------|
| **read.py** | Python script (~100 lines) | SessionStart hook — finds latest, checks recency, outputs injection |
| **Write** | Claude + Write tool | Claude generates markdown, writes directly |
| **List** | Claude + Glob/Read | Claude globs `*.md`, reads frontmatter, formats output |
| **Prune** | Built into read.py | Deletes files >30 days when script runs |

### read.py Logic

```
1. Determine project from CWD (git root or directory name)
2. Find all handoffs in ~/.claude/handoffs/<project>/
3. Delete any older than 30 days
4. Find most recent remaining handoff
5. If exists and <24h old:
   → Output: "[Resuming: <title>]\n<handoff content>"
6. If exists and >24h old:
   → Output: "[Found handoff from <date>: <title>. Resume from this?]"
7. If none exist:
   → Output: "[No recent handoff for this project]"
```

---

## User Interaction

### Commands

| Command | Action |
|---------|--------|
| `/handoff` | Create handoff (Claude generates title) |
| `/handoff <title>` | Create handoff with specified title |
| `/resume` | Manually load latest handoff |
| `/resume <path>` | Load specific handoff |
| `/list-handoffs` | List available handoffs for project |

### Signal Phrases (Claude offers handoff)

- "wrap this up"
- "handoff"
- "new session"

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Handoff for trivial sessions | Noise accumulation | Skip if no meaningful decisions/progress |
| Including every file touched | Information overload | Focus on key artifacts with purpose |
| Missing decisions/rationale | Just listing changes isn't useful | Always capture at least one "why" |
| Re-prompting after user declines | Annoying, ignores user intent | Respect "no" and move on |

---

## Migration from v1

1. Existing handoffs in `.claude/handoffs/` remain readable
2. New handoffs go to `~/.claude/handoffs/<project>/`
3. Global symlinks (v1) are not created; existing ones can be cleaned up manually
4. Synthesis mode (`--synthesize`) is removed — use regular `/handoff`
5. Validation script removed — Claude writes correct format directly

---

## Implementation Plan

1. Write new `read.py` script (~100 lines)
2. Write new `SKILL.md` following this design
3. Configure SessionStart hook
4. Test create/resume/list flows
5. Remove old scripts (write.py, validate.py, save.py, prepare.py, etc.)
