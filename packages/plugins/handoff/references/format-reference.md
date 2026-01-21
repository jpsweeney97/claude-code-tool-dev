# Handoff Format Reference

Shared schema and conventions for handoff documents.

## Frontmatter Schema

```yaml
---
date: 2026-01-08                    # Date (YYYY-MM-DD)
time: "14:30"                       # Time (HH:MM, quoted for YAML)
created_at: "2026-01-08T14:30:00Z"  # ISO 8601 UTC timestamp
session_id: <UUID>                  # Claude session ID
resumed_from: <path>                # Archive path if resumed (optional)
project: <project-name>             # Git root or directory name
branch: <branch-name>               # Current git branch (optional)
commit: <short-hash>                # Short commit hash (optional)
title: <descriptive-title>          # Handoff title
files:
  - <key files touched>             # List of relevant files
---
```

## Section Checklist

Include only sections relevant to the session. Empty sections are omitted.

| Section | When to Include |
|---------|-----------------|
| Goal | Session had a clear objective |
| Decisions | Choices made with tradeoffs/reasoning |
| Changes | Files created/modified with purpose |
| In Progress | Work was ongoing when session ended |
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

## Storage

**Location:** `~/.claude/handoffs/<project>/`

**Filename:** `YYYY-MM-DD_HH-MM_<title-slug>.md`

**Archive:** `~/.claude/handoffs/<project>/.archive/`

## Retention

| Location | Retention |
|----------|-----------|
| Active handoffs (`~/.claude/handoffs/<project>/`) | 30 days |
| Archived handoffs (`~/.claude/handoffs/<project>/.archive/`) | 90 days |
| State files (`~/.claude/.session-state/handoff-*`) | 24 hours |

## Example: New Session

```markdown
---
date: 2026-01-08
time: "14:30"
created_at: "2026-01-08T14:30:00Z"
session_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
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

## Example: Resumed Session

```markdown
---
date: 2026-01-08
time: "16:45"
created_at: "2026-01-08T16:45:00Z"
session_id: f9e8d7c6-b5a4-3210-fedc-ba0987654321
resumed_from: ~/.claude/handoffs/my-app/.archive/2026-01-08_14-30_auth-middleware-implementation.md
project: my-app
branch: feat/auth-middleware
commit: c3d4e5f
title: Auth middleware - refresh endpoint complete
files:
  - src/auth/refresh.py
  - tests/test_refresh.py
---

# Handoff: Auth middleware - refresh endpoint complete

## Goal
Complete the auth middleware implementation by adding the refresh endpoint.

## Changes
- `src/auth/refresh.py` — Token refresh endpoint
- `tests/test_refresh.py` — Integration tests for refresh flow

## Next Steps
1. Add middleware to protected routes
2. Update API documentation
```
