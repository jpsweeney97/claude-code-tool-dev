---
name: handoff
description: Session continuity - capture context when stopping, auto-restore when resuming. One action to save, zero actions to resume.
metadata:
  version: 2.0.0
  model: claude-opus-4-5-20251101
---

# Handoff Skill

Capture session context at stopping points. Resume seamlessly next session.

**Core Promise:** One action to save, zero actions to resume (when recent).

## Commands

| Command | Action |
|---------|--------|
| `/handoff` | Create handoff (Claude generates title) |
| `/handoff <title>` | Create handoff with specified title |
| `/resume` | Manually load latest handoff |
| `/resume <path>` | Load specific handoff |
| `/list-handoffs` | List available handoffs for project |

## Signal Phrases

When user says these, offer to create a handoff:
- "wrap this up"
- "handoff"
- "new session"

**Response:** "Create a handoff before ending?"

**STOP Condition:** If user declines, do not re-prompt or proceed.

## Creating a Handoff

When user runs `/handoff [title]` or confirms a signal phrase offer:

1. **Gather context** from the session
2. **Select relevant sections** using the checklist below (omit empty sections)
3. **Generate markdown** with frontmatter
4. **Write directly** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
5. **Confirm:** "Handoff saved: <title> (N decisions, N changes, N next steps)"

### Frontmatter Format

```yaml
---
date: 2026-01-08
time: "14:30"
session_id: <from CLAUDE_SESSION_ID env var>
project: <git root name or directory name>
branch: <current branch if git>
commit: <short commit hash if git>
title: <descriptive title>
files:
  - <key files touched>
---
```

### Section Checklist

Include only sections relevant to the session. Empty sections are omitted.

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

## Resuming from Handoff

### Automatic (SessionStart Hook)

The `read.py` script runs automatically at session start:

1. Finds latest handoff for current project in `~/.claude/handoffs/<project>/`
2. Prunes handoffs older than 30 days
3. Outputs based on recency:
   - **<24h:** Auto-inject content with `[Resuming: <title>]`
   - **>24h:** Prompt `[Found handoff from <date>: <title>. Resume from this?]`
   - **None:** Silent (no output)

### Manual (`/resume`)

When user runs `/resume [path]`:

1. If path provided: read that specific handoff
2. If no path: use Glob to find latest in `~/.claude/handoffs/<project>/`
3. Read the handoff content
4. Summarize key points and offer: "Continue with [next step]?"

### Listing (`/list-handoffs`)

When user runs `/list-handoffs`:

1. Glob `~/.claude/handoffs/<project>/*.md`
2. Read frontmatter from each file
3. Format as table: date, title, branch

## Storage

**Location:** `~/.claude/handoffs/<project>/`

**Filename:** `YYYY-MM-DD_HH-MM_<title-slug>.md`

**Retention:** Files older than 30 days are pruned automatically.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Handoff for trivial sessions | Noise accumulation | Skip if no meaningful decisions/progress |
| Including every file touched | Information overload | Focus on key artifacts with purpose |
| Missing decisions/rationale | Just listing changes isn't useful | Always capture at least one "why" |
| Re-prompting after user declines | Annoying, ignores user intent | Respect "no" and move on |

## Verification

After creating handoff:
- [ ] File exists at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- [ ] Frontmatter parses as valid YAML
- [ ] Required fields present: date, time, session_id, project, title
- [ ] At least one section has content

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `note` | Complementary: note for journaling, handoff for session transfer |
| `episodic-memory` | Complementary: memory for search, handoff for structured resume |
