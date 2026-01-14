---
name: handoff
description: Use when user says "wrap this up", "new session", or "handoff"; when stopping work with context to preserve; or when resuming from a previous session.
metadata:
  version: 4.0.0
  model: claude-opus-4-5-20251101
---

# Handoff Skill

Capture session context at stopping points. Resume explicitly with `/resume`.

**Core Promise:** One action to save (`/handoff`), one action to resume (`/resume`).

## When to Use

- User explicitly runs `/handoff` or `/handoff <title>`
- User says signal phrases: "wrap this up", "new session", "handoff"
- Session contains at least one of: decision made, file changed, gotcha discovered, next step identified
- User is stopping work and wants to resume later with context

## When NOT to Use

- Session was trivial (quick Q&A with no decisions, changes, or learnings)
- User explicitly declines handoff offer
- Context is already captured elsewhere (PR description, committed docs, issue tracker)
- Session is exploratory research with no actionable next steps

**Non-goals (this skill does NOT):**
- Replace proper documentation (handoffs are ephemeral, docs are permanent)
- Capture every detail (focus on decisions and next steps, not transcript)
- Work across different machines (handoffs are local to `~/.claude/`)
- Version control handoffs (they're working documents, not artifacts)

**STOP:** If unclear whether session has meaningful content, ask: "Should I create a handoff? This session seems light on decisions/changes."

## Inputs

**Required:**
- Session context (gathered from conversation history)

**Optional:**
- `title` argument for `/handoff <title>` — if omitted, Claude generates a descriptive title

**Constraints/Assumptions:**

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Git repository | No | Omit `branch` and `commit` fields from frontmatter |
| Write access to `~/.claude/handoffs/` | Yes | **STOP** and ask for alternative path |
| Project name determinable | No | Use parent directory name; if ambiguous, ask user |

**STOP:** If `~/.claude/handoffs/` doesn't exist and cannot be created, ask: "I can't write to ~/.claude/handoffs/. Where should I save handoffs?"

## Outputs

**Artifacts:**
- Markdown file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- Frontmatter with session metadata (date, time, created_at, project, title, files)
- Body with relevant sections from checklist (only non-empty sections included)

**Definition of Done:**

| Check | Expected |
|-------|----------|
| File exists at expected path | `ls ~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_*.md` returns file |
| Frontmatter parses as valid YAML | No YAML syntax errors |
| Required fields present | `date`, `time`, `created_at`, `project`, `title` all have values |
| At least one body section | File contains at least one H2 section with content |
| Content is resumable | Reading the handoff provides enough context to continue work |

**Quick check:** After writing, verify file exists and contains the title. If missing, check write permissions and path.

## Commands

| Command | Action |
|---------|--------|
| `/handoff` | Create handoff (Claude generates title) |
| `/handoff <title>` | Create handoff with specified title |
| `/resume` | Manually load latest handoff |
| `/resume <path>` | Load specific handoff |
| `/list-handoffs` | List available handoffs for project |

## Decision Points

1. **Signal phrase detected:**
   - If user says "wrap this up", "new session", or "handoff", then offer: "Create a handoff before ending?"
   - If user declines, **STOP**. Do not re-prompt or proceed.

2. **Session content assessment:**
   - If session contains at least one of: decision made, file changed, gotcha discovered, next step identified, then proceed with handoff.
   - Otherwise, ask: "This session seems light — create a handoff anyway, or skip?"

3. **Git repository detection:**
   - If `.git/` directory exists in current or parent directories, then include `branch` and `commit` in frontmatter.
   - Otherwise, omit `branch` and `commit` fields entirely (don't use placeholders).

4. **Timestamp generation:**
   - Generate `created_at` as ISO 8601 UTC timestamp (e.g., `2026-01-12T14:30:00Z`)
   - Use the current time when the handoff is created

5. **Write permission check:**
   - If `~/.claude/handoffs/<project>/` is writable (or can be created), write handoff there.
   - Otherwise, **STOP** and ask: "Can't write to ~/.claude/handoffs/. Where should I save this handoff?"

## Procedure

When user runs `/handoff [title]` or confirms a signal phrase offer:

1. **Check prerequisites:**
   - If session appears trivial (no decisions, changes, or learnings), ask: "This session seems light — create a handoff anyway?"
   - If user declines, **STOP**. Do not proceed.

2. **Gather context** from the session

3. **Select relevant sections** using the checklist below
   - If no sections have content, **STOP** and ask: "I don't see anything to hand off. What should I capture?"
   - Omit empty sections from output
   - **Calibration:** Distinguish verified facts (explicitly discussed) from inferred conclusions (reasonable next steps) from assumed context (background not verified this session)

4. **Determine output path:**
   - If `~/.claude/handoffs/<project>/` is not writable, **STOP** and ask for alternative path
   - If project name is ambiguous (not in git, generic directory name), ask user to specify

5. **Generate markdown** with frontmatter
   - Use fallbacks for optional fields (see Inputs → Constraints/Assumptions)

6. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`

7. **Verify and confirm:**
   - Check file exists and frontmatter is valid
   - Confirm: "Handoff saved: <title> (N decisions, N changes, N next steps)"

### Frontmatter Format

```yaml
---
date: 2026-01-08
time: "14:30"
created_at: "<ISO 8601 UTC timestamp, e.g., 2026-01-08T14:30:00Z>"
project: <git root name or directory name>
branch: <current branch if git, omit if not git>
commit: <short commit hash if git, omit if not git>
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
created_at: "2026-01-08T14:30:00Z"
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

Handoffs require **explicit resume** — they are not auto-injected or suggested at session start. This prevents stale handoffs from cluttering unrelated sessions.

### Background Cleanup (SessionStart Hook)

The `read.py` script runs silently at session start:

1. Prunes handoffs older than 30 days
2. Produces no output (no auto-inject, no prompts)

### Manual (`/resume`)

When user runs `/resume [path]`:

1. If path provided: read that specific handoff
2. If no path: use Glob to find latest in `~/.claude/handoffs/<project>/`
3. Read and display the handoff content
4. Summarize key points and offer: "Continue with [next step]?"
5. **Trash the handoff file** after displaying (handoffs are single-use)

### Listing (`/list-handoffs`)

When user runs `/list-handoffs`:

1. Glob `~/.claude/handoffs/<project>/*.md`
2. Read frontmatter from each file
3. Format as table: date, title, branch

## Storage

**Location:** `~/.claude/handoffs/<project>/`

**Filename:** `YYYY-MM-DD_HH-MM_<title-slug>.md`

**Retention:** Files older than 30 days are pruned automatically.

## Verification

After creating handoff, verify:

- [ ] File exists at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- [ ] Frontmatter parses as valid YAML
- [ ] Required fields present: date, time, created_at, project, title
- [ ] At least one section has content

**Quick check:** Run `ls ~/.claude/handoffs/<project>/` and confirm new file appears. If not, check write permissions.

**If verification fails:** Do not report success. Check Troubleshooting section and resolve before confirming.

## Troubleshooting

### Handoff file not created

**Symptoms:** `/handoff` completes but no file appears at `~/.claude/handoffs/<project>/`

**Likely causes:**
- Permission denied on `~/.claude/` directory
- Project name couldn't be determined (not in git, ambiguous directory)
- Disk full or path too long

**Next steps:**
1. Check if `~/.claude/handoffs/` exists: `ls -la ~/.claude/handoffs/`
2. Check write permissions: `touch ~/.claude/handoffs/test && rm ~/.claude/handoffs/test`
3. If permissions issue, ask user for alternative path
4. If project undetermined, ask user to specify project name

---

### Resume not finding handoff

**Symptoms:** `/resume` says "No handoffs found" or finds wrong handoff

**Likely causes:**
- Handoff older than 30 days (auto-pruned by retention policy)
- Running from different project directory than where handoff was created
- Handoff saved with different project name

**Next steps:**
1. Run `/list-handoffs` to see available handoffs for current project
2. Check `~/.claude/handoffs/` directly: `ls ~/.claude/handoffs/`
3. If found in different project, use `/resume <full-path>`

---

### Handoff content missing key decisions

**Symptoms:** Resumed handoff lacks important context from original session

**Likely causes:**
- Handoff created too early (before key decisions made)
- Section checklist didn't capture all relevant categories
- Session had implicit decisions not stated explicitly

**Next steps:**
1. Review session history for decisions made after handoff
2. Create new handoff with more complete context
3. Consider adding to existing handoff manually if file still accessible

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Handoff for trivial sessions | Noise accumulation | Skip if no meaningful decisions/progress |
| Including every file touched | Information overload | Focus on key artifacts with purpose |
| Missing decisions/rationale | Just listing changes isn't useful | Always capture at least one "why" |
| Re-prompting after user declines | Annoying, ignores user intent | Respect "no" and move on |
| Guessing when uncertain | May create useless handoff | Ask user if handoff is needed |

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `note` | Complementary: note for journaling, handoff for session transfer |

