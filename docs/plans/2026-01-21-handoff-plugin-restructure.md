## Design Note: Restructure Handoff as Plugin

**Status:** Planned (after synthesis guide merges)
**Depends on:** `feature/handoff-synthesis-guide` branch

### Problem

The current handoff skill bundles three distinct functions:
- `/handoff` — Create handoffs (with synthesis guide)
- `/resume` — Load and continue from handoffs
- `/list-handoffs` — List available handoffs

When running `/resume`, Claude loads ~400 lines including the synthesis guide and handoff creation procedure — none of which is needed for resuming.

### Proposed Solution

Create a plugin that separates these into focused skills with shared references.

### Plugin Structure

```
packages/plugins/handoff/
├── plugin.json
├── skills/
│   ├── handoff/
│   │   ├── SKILL.md           # Creating handoffs only
│   │   ├── synthesis-guide.md # Synthesis process (from current branch)
│   │   └── format-reference.md
│   └── resuming-handoffs/
│       ├── SKILL.md           # Resuming from handoffs
│       └── format-reference.md
└── hooks/
    └── hooks.json             # SessionStart cleanup (migrate from read.py)
```

### Skill Responsibilities

**handoff skill:**
- Trigger: `/handoff`, signal phrases ("wrap this up", "new session")
- Requires synthesis guide
- Creates handoff files
- References format-reference.md for schema

**resuming-handoffs skill:**
- Trigger: `/resume`, `/list-handoffs`
- Reads and displays handoffs
- Archives on resume
- Manages state files
- References format-reference.md for schema

### Shared Reference Content

`format-reference.md` should contain:
- Frontmatter schema (date, time, created_at, session_id, etc.)
- Storage location: `~/.claude/handoffs/<project>/`
- Filename format: `YYYY-MM-DD_HH-MM_<slug>.md`
- Archive location: `~/.claude/handoffs/<project>/.archive/`
- Retention policies (30 days active, 90 days archive, 24 hours state)
- Section checklist (shared so resume understands handoff structure)

### Open Questions

- Should the plugin be named `handoff` or `session-handoff` or `context-handoff`?
- Should `/list-handoffs` be its own skill or be dropped?
- Any other hooks needed? (e.g., offer handoff on session end?)

### Benefits

- Single responsibility per skill
- Shared references without duplication
- Install/uninstall as a unit
- Publishable to marketplace
- Cleaner context loading (resume doesn't load synthesis guide)
