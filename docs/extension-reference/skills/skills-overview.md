---
id: skills-overview
topic: Skills Overview
category: skills
tags: [skills, workflow, verification, procedures]
related_to: [skills-frontmatter, skills-invocation, commands-overview, skills-troubleshooting, skills-getting-started, skills-validation]
official_docs: https://code.claude.com/en/skills
---

# Skills Overview

Skills are structured workflows with verification steps. Unlike commands (simple prompt templates), skills guide Claude through complex procedures with decision points, quality gates, and explicit success criteria.

## Purpose

- Complex multi-step workflows
- Conditional "if X then Y" logic
- Quality gates and verification
- Reusable procedures across projects

## Location and Precedence

| Scope | Path | Applies to |
|-------|------|------------|
| Enterprise | [Managed settings](/en/iam#managed-settings) | All users in organization |
| Personal | `~/.claude/skills/<name>/SKILL.md` | You, across all projects |
| Project | `.claude/skills/<name>/SKILL.md` | Anyone in this repository |
| Plugin | `skills/<name>/SKILL.md` in plugin | Anyone with plugin installed |

**Precedence**: If two skills have the same name, higher scope wins: Enterprise > Personal > Project > Plugin.

### Directory Structure

```
.claude/skills/<skill-name>/
└── SKILL.md           # Required: Main skill definition
└── references/        # Optional: Deep documentation
└── scripts/           # Optional: Automation (stdlib only)
└── templates/         # Optional: Output templates
└── assets/            # Optional: Images, prompts
```

## Skills vs Other Extensions

| Extension | Purpose | When it runs |
|-----------|---------|--------------|
| **Skills** | Specialized knowledge and procedures | Claude chooses when relevant |
| **Slash commands** | Reusable prompts | User types `/command` |
| **CLAUDE.md** | Project-wide instructions | Loaded every conversation |
| **Subagents** | Delegate tasks to separate context | Claude delegates or user invokes |
| **Hooks** | Run scripts on events | Fires on tool events |
| **MCP servers** | Connect to external tools/data | Claude calls MCP tools |

**Skills vs Subagents**: Skills add knowledge to current conversation. Subagents run in separate context with own tools. Use skills for guidance; subagents for isolation.

**Skills vs MCP**: Skills tell Claude _how_ to use tools. MCP _provides_ the tools. Example: MCP connects to your database; a skill teaches your data model and query patterns.

**Further reading**: [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Anthropic engineering deep-dive on skill architecture.

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

## Distribution

- **Project**: Commit `.claude/skills/` to version control. Anyone cloning gets the skills.
- **Plugins**: Create `skills/` directory in your [plugin](/en/plugins), distribute via [plugin marketplace](/en/plugin-marketplaces).
- **Managed**: Administrators deploy organization-wide through managed settings.

## Update and Delete

- **Update**: Edit `SKILL.md` directly. Changes take effect immediately.
- **Delete**: Remove the skill directory. No restart required.

## Specifications

For detailed normative requirements beyond this reference:

| Document | Purpose |
|----------|---------|
| [skills-as-prompts-strict-spec.md](../../../skill-documentation/skills-as-prompts-strict-spec.md) | Structural requirements, reviewer checklist, fail codes |
| [skills-semantic-quality-addendum.md](../../../skill-documentation/skills-semantic-quality-addendum.md) | Semantic quality requirements, templates |
| [skills-categories-guide.md](../../../skill-documentation/skills-categories-guide.md) | Category definitions, DoD patterns, decision point libraries |

These specifications are authoritative for skill compliance validation.

## Key Points

- Skills are markdown files with YAML frontmatter
- Higher scope overrides lower scope for same-named skills
- `SKILL.md` filename is required (not `<skill-name>.md`)
- Skills can define component-scoped hooks
