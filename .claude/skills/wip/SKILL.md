---
name: wip
description: Persistent project-level work-in-progress tracking across sessions
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# WIP Skill

Track active work streams that persist across Claude Code sessions.

## Triggers

- `/wip` - Show current WIP items
- `/wip add <description>` - Add new item
- `/wip <id>` - Show item detail
- `/wip done <id>` - Mark completed
- `/wip block <id> <reason>` - Set blocker
- `/wip unblock <id>` - Clear blocker
- `/wip pause <id>` - Pause item
- `/wip resume <id>` - Resume paused item
- `/wip archive` - Move completed to archive

## Quick Reference

| Command | Action |
|---------|--------|
| `/wip` | Show active and blocked items |
| `/wip add Feature X` | Create new active item |
| `/wip W001` | Show full detail for W001 |
| `/wip done W001` | Mark W001 completed |
| `/wip block W001 Waiting for API` | Block W001 |
| `/wip unblock W001` | Clear blocker |
| `/wip pause W001` | Move to paused |
| `/wip resume W001` | Resume from paused |
| `/wip archive` | Archive completed items |

## How It Works

**Storage:** `.claude/wip/WIP.md` - single markdown file, version controlled.

**Auto-init:** WIP.md is created automatically on first `/wip add` if it doesn't exist.

**Sections:** Items organized by status (Active/Paused/Completed). Items move between sections on status change.

**IDs:** Sequential `W001`, `W002`, etc. Format supports unlimited digits (W001 through W99999+). Never reused.

**Archive:** Completed items stay in WIP.md until `/wip archive` moves them to `WIP-archive.md`.

## Item Structure

```markdown
### [W001] Implement authentication middleware
**Added:** 2026-01-05 | **Files:** src/auth/jwt.py, src/auth/middleware.py

JWT-based auth for API endpoints. Using RS256 for verification.

**Blocker:** None
**Next:** Write integration tests
```

## Scripts

Run scripts directly - do not read into context:

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `scripts/init.py` | Create WIP.md | 0=success, 1=exists, 2=error |
| `scripts/read.py` | Display items | 0=success, 1=not found |
| `scripts/update.py` | Modify items | 0=success, 1=input error, 2=write error |

### Usage Examples

**Initialize WIP:**
```bash
python3 ~/.claude/skills/wip/scripts/init.py
```

**Add item:**
```bash
python3 ~/.claude/skills/wip/scripts/update.py add \
  --desc "Implement feature X" \
  --files "src/x.py,src/y.py" \
  --next "Write failing tests"
```

**Mark completed:**
```bash
python3 ~/.claude/skills/wip/scripts/update.py move W001 --status completed
```

**Compact view (for hooks):**
```bash
python3 ~/.claude/skills/wip/scripts/read.py --compact
```

## SessionStart Hook

Add to settings to auto-inject WIP summary:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/wip/scripts/read.py --compact 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

## Workflows

### Starting Work

1. User starts session
2. Hook injects WIP summary (active items, blockers)
3. Claude acknowledges current work state
4. User continues from context

### Adding New Work

1. User: `/wip add Implement caching layer`
2. Claude runs `update.py add --desc "..."`
3. Claude confirms: "Added W003: Implement caching layer"
4. Claude asks: "What files will this involve? Any next steps?"

### Completing Work

1. User: `/wip done W001`
2. Claude runs `update.py move W001 --status completed`
3. Claude confirms and asks if ready to archive

### Blocking/Unblocking

1. User: `/wip block W002 Waiting for design review`
2. Claude runs `update.py block W002 --reason "..."`
3. Item shows as blocked in next session's injection

## Relationship to Other Tools

| Tool | Use For |
|------|---------|
| **WIP** | Active work streams across sessions |
| **TodoWrite** | Subtask breakdown within sessions |
| **Handoff** | Detailed context transfer at session end |

**Pattern:** WIP tracks what; handoff captures why and how.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| >10 active items | Too much parallel work | Pause or complete some |
| Items with no next action | Unclear what to do | Always set next step |
| Never archiving | File grows unbounded | Archive weekly |
| Duplicate with TodoWrite | Confusion about source of truth | WIP = persistent, Todo = session |

## Verification

After operations, verify:
- [ ] WIP.md exists at `.claude/wip/WIP.md`
- [ ] Item IDs are unique and sequential
- [ ] Sections are properly formatted
- [ ] Hook injection is <100 tokens
