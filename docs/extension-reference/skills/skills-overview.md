---
id: skills-overview
topic: Skills Overview
category: skills
tags: [skills, workflow, verification, procedures]
related_to: [skills-frontmatter, skills-invocation, commands-overview]
official_docs: https://code.claude.com/en/skills
---

# Skills Overview

Skills are structured workflows with verification steps. Unlike commands (simple prompt templates), skills guide Claude through complex procedures with decision points, quality gates, and explicit success criteria.

## Purpose

- Complex multi-step workflows
- Conditional "if X then Y" logic
- Quality gates and verification
- Reusable procedures across projects

## Location

```
.claude/skills/<skill-name>/
└── SKILL.md           # Required: Main skill definition
└── references/        # Optional: Deep documentation
└── scripts/           # Optional: Automation (stdlib only)
└── templates/         # Optional: Output templates
└── assets/            # Optional: Images, prompts
```

User location: `~/.claude/skills/<skill-name>/SKILL.md`

## When to Use

Use skills when:
- Multi-step procedures with decision points
- "If X then Y otherwise Z" logic needed
- Verification and quality gates required
- Reusable across multiple projects

Use commands instead when:
- Simple prompt injection
- No conditional logic
- One-shot execution

## Key Points

- Skills are markdown files with YAML frontmatter
- User scope overrides project scope for same-named skills
- `SKILL.md` filename is required (not `<skill-name>.md`)
- Skills can define component-scoped hooks
