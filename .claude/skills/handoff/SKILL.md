---
name: handoff
description: Session continuity - capture context when stopping, auto-restore when resuming. One action to save, zero actions to resume.
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
---

# Handoff Skill

Capture session context at stopping points. Resume seamlessly next session.

## Triggers

- `/handoff` - Create a handoff document
- `wrapping up`, `done for today`, `stopping here` - Claude offers to create handoff
- `/resume` - Load the latest handoff (or specific path)
- `/list-handoffs` - List available handoffs
- `continue where I left off` - Resume from handoff

## Quick Reference

| Action | Command |
|--------|---------|
| Create handoff | `/handoff` |
| Create with description | `/handoff auth middleware complete` |
| **Synthesize current session** | `/handoff --synthesize` |
| **Synthesize past session** | `/handoff --synthesize --session <id>` |
| **List sessions** | `/handoff --synthesize --list` |
| Resume latest | `/resume` |
| Resume specific | `/resume path/to/handoff.md` |
| List handoffs | `/list-handoffs` |
| Prune old | `/handoff --prune` |

## Commands

### `/handoff [description]`

Create a handoff document capturing current session context.

**What gets captured:**
- Goal - What you were working on
- Task Status - Checkboxes from todo list
- Key Decisions - Choices made with rationale
- Recent Changes - Files modified (with line references)
- Learnings - Gotchas, insights, things that surprised you
- Next Steps - Prioritized list of what to do next
- Git State - Branch, commit, uncommitted files (if in git repo)

**Example:**
```
User: /handoff JWT auth middleware
Claude: Creating handoff... Done.
        Saved: .claude/handoffs/2026-01-01_14-30-00_jwt-auth-middleware.md
```

### `/handoff --synthesize [--session <id>] [--list]`

Automatically synthesize a handoff from a session transcript using Opus.

**Options:**
- No options: synthesize current session
- `--session <id>`: synthesize a specific past session (use UUID or partial match)
- `--list`: show available sessions for this project

**How it works:**
1. Claude runs `prepare.py` to load and format the session transcript
2. Claude calls Task tool with Opus to analyze and synthesize
3. Claude validates the output with `validate.py`
4. If valid, Claude saves with `save.py`

**What gets synthesized:**
- Decisions with reasoning (extracted from conversation)
- Files changed with purpose
- Gotchas and surprises discovered
- Next steps with actionable context
- Artifacts preserved verbatim

**Examples:**
```
User: /handoff --synthesize
Claude: Preparing transcript... 847 messages.
        Synthesizing with Opus...
        Validating... valid.
        Saved: .claude/handoffs/2026-01-02_14-30-00_synthesis-agent-implementation.md
```

```
User: /handoff --synthesize --list
Claude: Available sessions for .claude:
        1. fa613a83... (2026-01-02 12:30) - 1.2MB
        2. 8b2c9f41... (2026-01-01 15:45) - 890KB
        3. ...
```

```
User: /handoff --synthesize --session fa613a83
Claude: Loading session fa613a83-7477-4b28-afcd-6759e1d564c9...
        Preparing transcript... 572 messages.
        Synthesizing with Opus...
        Saved: .claude/handoffs/2026-01-02_13-46-55_handoff-skill-hardening.md
```

**When to use:**
- End of long sessions where manually listing context is tedious
- Sessions with many decisions worth capturing
- When you want reasoning extracted from the conversation
- **Past sessions**: When you forgot to create a handoff and want to capture context later

**Note:** Synthesis uses Opus, which is more expensive than manual handoffs. For quick sessions, regular `/handoff` is faster.

### `/resume [path]`

Load a handoff to restore context.

- No argument: loads latest handoff for current project
- With path: loads specific handoff file

**Note:** For same-project sessions, the latest handoff is auto-injected on session start via SessionStart hook. You don't need to run `/resume` manually.

### `/list-handoffs`

List available handoffs with metadata.

```
Handoffs for my-project:
1. 2026-01-01 14:30 - JWT auth middleware (feat/user-auth)
2. 2025-12-31 18:00 - API rate limiting (main)
3. 2025-12-30 16:45 - Database schema (feat/db-migration)
```

### `/handoff --prune`

Remove old handoffs per retention policy (keeps last 10).

## Handoff Format

```markdown
---
date: 2026-01-01T14:30:00-08:00
version: 1
git_commit: abc123f
branch: feat/user-auth
repository: my-project
tags: [auth, security]
---

# Handoff: JWT authentication middleware

## Goal
Enable stateless user authentication for the API.

## Task Status
- [x] Token generation and validation
- [x] Middleware implementation
- [ ] Refresh endpoint
- [ ] Integration tests

## Key Decisions
- **JWT over sessions:** Stateless scales horizontally without shared session store.
- **RS256 signing:** Public key verification avoids sharing secrets across services.

## Attempted but Abandoned
- **HS256 signing:** Required sharing secrets between services. Rejected.

## Recent Changes
- `src/auth/jwt.py:1-45` - Token generation with RS256
- `src/auth/middleware.py:1-32` - Request authentication decorator

## Learnings
- PyJWT requires `cryptography` for RS256. Added to dependencies.
- Token decode failures raise `InvalidTokenError`, not `DecodeError`.

## Critical References
- `docs/auth-spec.md` - Original requirements

## Artifacts
- `src/auth/jwt.py` - Created
- `src/auth/middleware.py` - Created

## User Context
- User prefers explicit error messages over generic "unauthorized"

## Next Steps
1. Create `/auth/refresh` endpoint in `routes.py`
2. Add middleware to protected routes in `api.py`
3. Write integration tests for token flow
```

## Scripts

Run these scripts directly — do not read into context:

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `scripts/write.py` | Create handoff document | 0=success, 1=input error, 2=write error |
| `scripts/read.py` | Load handoff for injection | 0=success, 1=not found |
| `scripts/list.py` | List available handoffs | 0=success |
| `scripts/prune.py` | Remove old handoffs | 0=success, 1=error |
| `scripts/prepare.py` | Prepare transcript for synthesis | 0=success, 1=not found, 2=empty |
| `scripts/validate.py` | Validate handoff structure | 0=valid, 1=invalid, 2=input error |
| `scripts/save.py` | Save synthesized handoff | 0=success, 1=invalid, 2=write error |

### Usage Examples

**Create handoff:**
```bash
python3 ~/.claude/skills/handoff/scripts/write.py \
  --title "JWT auth middleware" \
  --goal "Enable stateless user authentication" \
  --decisions '["JWT over sessions: Stateless scales horizontally"]' \
  --changes '["src/auth/jwt.py:1-45 - Token generation"]' \
  --next-steps '["Create refresh endpoint", "Add middleware to routes"]' \
  --tags 'auth,security'
```

**Note:** `--tags` accepts comma-separated values (`auth,security`) or JSON arrays (`["auth","security"]`). Other list arguments require JSON arrays.

**Read latest handoff:**
```bash
python3 ~/.claude/skills/handoff/scripts/read.py
python3 ~/.claude/skills/handoff/scripts/read.py --compact  # For injection
```

**List handoffs:**
```bash
python3 ~/.claude/skills/handoff/scripts/list.py
python3 ~/.claude/skills/handoff/scripts/list.py --json
```

**Prune old handoffs:**
```bash
python3 ~/.claude/skills/handoff/scripts/prune.py --dry-run
python3 ~/.claude/skills/handoff/scripts/prune.py --keep 5
```

## Storage

| Location | Purpose |
|----------|---------|
| `.claude/handoffs/` | Project-specific handoffs |
| `~/.claude/handoffs/` | Global collection (symlinks for cross-project search) |

**Filename format:** `YYYY-MM-DD_HH-MM-SS_<description>.md`

**Retention:** Last 10 handoffs per project. Older ones are auto-pruned.

## SessionStart Hook Integration

Add to `.claude/settings.json` to auto-inject handoffs:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/handoff/scripts/read.py --compact 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

The hook outputs a compact summary of the latest handoff, which Claude sees at session start.

## Workflows

### Creating a Handoff

1. User signals stopping (or runs `/handoff`)
2. Claude gathers context:
   - Git state (branch, commit, uncommitted)
   - Todo list state
   - Decisions made this session
   - Files changed
3. Claude generates structured markdown
4. Script writes to `.claude/handoffs/` with timestamp filename
5. Script creates symlink in `~/.claude/handoffs/`
6. Script enforces retention (prune if >10 handoffs)

### Resuming from Handoff

**Same project (automatic):**
1. SessionStart hook runs `read.py --compact`
2. Output injected into Claude's context
3. Claude acknowledges: "Resuming from handoff: [title]"

**Different project or explicit:**
1. User runs `/resume` or `/resume path`
2. Claude reads full handoff
3. Claude summarizes key points and asks: "Continue with [next step]?"

### Synthesizing a Handoff

When user runs `/handoff --synthesize [--session <id>] [--list]`:

**If `--list` flag:**
```bash
python3 ~/.claude/skills/handoff/scripts/prepare.py --list
```
- Shows available sessions for this project with IDs, dates, and sizes
- User selects a session ID, then Claude re-runs with `--session`

**Step 1: Prepare transcript**
```bash
# Current session (default)
python3 ~/.claude/skills/handoff/scripts/prepare.py

# Specific past session
python3 ~/.claude/skills/handoff/scripts/prepare.py --session <uuid>
```
- Default: Uses `CLAUDE_SESSION_ID` environment variable to find current session
- With `--session`: Loads specified session (supports partial UUID match)
- Outputs line-numbered transcript with metadata header
- Filters noise (tool results, metadata entries)

**Step 2: Synthesize with Opus**

Call the Task tool:
```
subagent_type: "general-purpose"
model: "opus"
prompt: [Contents of assets/prompts/synthesis.md]

[Transcript output from Step 1]
```

The Opus agent analyzes the transcript and produces a structured markdown handoff.

**Step 3: Validate output**
```bash
echo "[Opus output]" | python3 ~/.claude/skills/handoff/scripts/validate.py
```
- Returns JSON: `{"valid": true}` or `{"valid": false, "issues": [...]}`
- If invalid, show issues and offer to retry

**Step 4: Save handoff**
```bash
echo "[Opus output]" | python3 ~/.claude/skills/handoff/scripts/save.py --validate
```
- Extracts title from content
- Saves to `.claude/handoffs/` with timestamp
- Creates symlink in `~/.claude/handoffs/`
- Enforces retention policy

**Error handling:**
- If prepare.py fails (no session): "No session transcript found. Use regular /handoff instead."
- If validation fails: Show issues, ask if user wants to retry or save anyway
- If save fails: Report error, offer to output raw content for manual save

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Handoffs >1000 tokens | Overwhelms context on injection | Prioritize: 5 decisions, 10 changes, 3 next steps |
| Handoff for trivial session | Noise accumulation | Skip if no substantial work done |
| Listing every file touched | Information overload | Focus on key artifacts with rationale |
| Missing decisions/rationale | Just listing changes isn't useful | Every handoff needs at least one "why" |

## Verification

After creating handoff:
- [ ] File exists at `.claude/handoffs/YYYY-MM-DD_...`
- [ ] Frontmatter has valid YAML (date, version, branch if git)
- [ ] At least one section has content (Goal or Next Steps)
- [ ] Injection format <500 tokens

## Extension Points

1. **Tags:** Add filtering by tag in `list.py`
2. **Sections:** Customize handoff template for specific workflows
3. **Integration:** Reference notes from `note` skill in handoffs
4. **Chains:** Handoffs reference parent handoff for long-running work

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `note` | Complementary: note for journaling, handoff for session transfer |
| `episodic-memory` | Complementary: memory for search, handoff for structured resume |
