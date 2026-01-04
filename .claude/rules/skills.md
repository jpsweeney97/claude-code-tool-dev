---
paths: .claude/skills/**
---

# Skill Development

## Structure

Skills are directories containing `SKILL.md`:
```
.claude/skills/<name>/
├── SKILL.md          # Main skill file (required)
└── ...               # Supporting files (optional)
```

## SKILL.md Format

```markdown
---
name: skill-name
description: One-line description for skill list
allowed-tools: ["Tool1", "Tool2"]  # Optional: auto-approve these tools
---

# Skill Name

Skill content here...
```

## Workflow

1. Create `.claude/skills/<name>/SKILL.md`
2. Test with `/<name>` in this project
3. Promote: `uv run scripts/promote skill <name>`

## Precedence

Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

To test changes to an existing skill:
1. Use a dev name: `.claude/skills/<name>-dev/`
2. Test with `/<name>-dev`
3. When ready, promote overwrites production
