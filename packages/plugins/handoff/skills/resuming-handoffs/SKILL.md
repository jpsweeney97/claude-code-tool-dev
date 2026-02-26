---
name: resuming-handoffs
description: Used when continuing from a previous session; when user runs `/resume` to load the most recent handoff, or `/resume <path>` for a specific handoff.
---

**Session ID:** ${CLAUDE_SESSION_ID}
**Read [handoff-contract.md](../../references/handoff-contract.md) for:** frontmatter schema, chain protocol, storage conventions.

# Resuming Handoffs

Continue work from a previous handoff.

**Core Promise:** One action to resume (`/resume`).

## When to Use

- User explicitly runs `/resume` or `/resume <path>`
- User says "continue from where we left off" or "pick up where I stopped"
- Starting a new session that should continue previous work

## When NOT to Use

- **Creating a new handoff** — use the `creating-handoffs` skill instead
- Session has no prior handoffs for this project
- User wants to start fresh without prior context

**Non-goals (this skill does NOT):**
- Create handoffs (that's the `creating-handoffs` skill)
- Auto-inject handoffs at session start (explicit resume only)
- Suggest handoffs (user must request)
- Load the synthesis guide (not needed for resume)

## Inputs

**Required:**
- Project context (determined from git root or current directory)

**Optional:**
- `path` argument for `/resume <path>` — specific handoff to load

**Constraints/Assumptions:**

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Project name determinable | Yes | Ask user to specify |
| Handoff exists for project | No | Report "No handoffs found" |

## Outputs

**Artifacts:**
- Archived handoff at `~/.claude/handoffs/<project>/.archive/<filename>`
- State file at `~/.claude/.session-state/handoff-<session_id>`

**Side Effects:**
- Original handoff moved to archive
- Context loaded into conversation

**Definition of Done:**

| Check | Expected |
|-------|----------|
| Handoff content displayed | User sees full handoff context |
| Original archived | File moved to `.archive/` |
| State file created | Path recorded for next handoff's `resumed_from` |
| Next step offered | "Continue with [next step]?" |

## Commands

| Command | Action |
|---------|--------|
| `/resume` | Load most recent handoff for this project |
| `/resume <path>` | Load specific handoff by path |
| `/list-handoffs` | List available handoffs for project |

## Decision Points

1. **Path argument provided:**
   - If path provided: validate file exists, then use that specific handoff.
   - If path doesn't exist: report "Handoff not found at <path>" and **STOP**.
   - If no path: search for most recent handoff in project directory.

2. **Handoff availability:**
   - If handoffs found for project: select most recent by filename timestamp.
   - If no handoffs found: report "No handoffs found for this project" and **STOP**.

3. **Project detection:**
   - If in git repository: use git root directory name as project.
   - If not in git: use current directory name.
   - If project name ambiguous or undeterminable: ask user to specify.

4. **Archive directory:**
   - If `.archive/` exists: move handoff there.
   - If `.archive/` doesn't exist: create it, then move handoff.
   - If cannot create `.archive/`: warn user but continue (handoff still readable).

5. **State file creation:**
   - If `~/.claude/.session-state/` writable: write state file with archive path.
   - If not writable: warn user (next handoff won't have `resumed_from` field).

## Procedure

### Resume (`/resume [path]`)

When user runs `/resume [path]`:

1. **Note the session ID** from the "Session ID:" line at the top of this skill (substituted by Claude Code at load time)

2. **Locate handoff:**
   - If path provided: validate it exists, use that handoff
   - If no path:
     1. Use Bash: `ls $HOME/.claude/handoffs/<project>/*.md 2>/dev/null` (shell glob is non-recursive — unlike the Glob tool, it won't descend into `.archive/`)
     2. If no output, report "No handoffs found for this project" and **STOP**
     3. Select most recent by filename (format: `YYYY-MM-DD_HH-MM_*.md`)

3. **Read handoff content**

4. **Display and summarize:**
   - Show full handoff/checkpoint content
   - Note the type: "Resuming from **checkpoint**: ..." or "Resuming from **handoff**: ..."
   - Summarize key points: goal/current task, decisions, next steps/next action
   - Offer: "Continue with [first next step/action]?"

5. **Archive the handoff:**
   - Create `~/.claude/handoffs/<project>/.archive/` if needed
   - Move handoff to `.archive/<filename>`

6. **Write state file:**
   - Create `~/.claude/.session-state/` if needed
   - Write archive path to `~/.claude/.session-state/handoff-<session_id>` (using UUID from step 1)

### List (`/list-handoffs`)

When user runs `/list-handoffs`:

1. Use Bash: `ls $HOME/.claude/handoffs/<project>/*.md 2>/dev/null` (shell glob is non-recursive — unlike the Glob tool, it won't descend into `.archive/`)
2. If no output, report "No handoffs found for this project" and **STOP**
3. Read frontmatter from each file
4. Format as table: date, title, type, branch
   - `type` comes from frontmatter `type` field. If missing, display as `handoff` (backwards compatibility).

## Storage

See [format-reference.md](../../references/format-reference.md) for:
- Storage location (`~/.claude/handoffs/<project>/`)
- Filename format (`YYYY-MM-DD_HH-MM_<slug>.md`)
- Archive location (`~/.claude/handoffs/<project>/.archive/`)
- Retention policies (30 days active, 90 days archive)

See also [handoff-contract.md](../../references/handoff-contract.md) for storage conventions, retention policies, and filename format.

## Background Cleanup (SessionStart Hook)

The plugin's SessionStart hook runs silently at session start:

1. Prunes handoffs older than 30 days
2. Prunes archived handoffs older than 90 days
3. Prunes state files older than 24 hours
4. Produces no output (no auto-inject, no prompts)

This is automatic — no user action required.

## Verification

After resuming, verify:

- [ ] Handoff content displayed to user
- [ ] Original file moved to `.archive/`
- [ ] State file exists at `~/.claude/.session-state/handoff-<session_id>`
- [ ] Type displayed on resume ("Resuming from **checkpoint**:" or "Resuming from **handoff**:")
- [ ] User offered continuation prompt

**Quick check:** `ls ~/.claude/handoffs/<project>/.archive/` shows the archived file.

## Troubleshooting

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

### Archive directory not created

**Symptoms:** Resume fails when trying to archive

**Likely causes:**
- Permission denied on handoffs directory
- Disk full

**Next steps:**
1. Check write permissions on `~/.claude/handoffs/<project>/`
2. Create `.archive/` manually if needed: `mkdir ~/.claude/handoffs/<project>/.archive`

### State file not created

**Symptoms:** Next handoff missing `resumed_from` field

**Likely causes:**
- Permission denied on `~/.claude/.session-state/`
- Session ended before state file written

**Next steps:**
1. Check if `~/.claude/.session-state/` exists
2. Create manually if needed: `mkdir -p ~/.claude/.session-state`

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Auto-injecting handoffs | Stale handoffs clutter unrelated sessions | Explicit `/resume` only |
| Suggesting old handoffs | Context may be irrelevant | User decides when to resume |
| Loading synthesis guide | Not needed for resume, wastes context | Resume skill is lightweight |
| Modifying handoff content | Handoffs are immutable snapshots | Create new handoff if needed |

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `creating-handoffs` | Complementary: creating-handoffs creates, resuming-handoffs loads |
