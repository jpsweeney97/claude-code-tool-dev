---
name: Skill Development
description: This skill provides structural reference for building skills in Claude Code plugins. Use for "skill file structure", "SKILL.md format", "progressive disclosure patterns", "organizing skill directories", or "skill anatomy". This is the WHERE and WHAT of skills. For HOW to test, see implementing-skills. For rigorous creation, see skillforge.
---

# Skill Development for Claude Code Plugins

Structural reference for building skills in Claude Code plugins.

## Related

For the **creation process** (TDD, testing, validation workflow), see the `implementing-skills` skill.

For **rigorous skill creation** with analysis, evolution scoring, and synthesis panel, use the `skillforge` skill or `/plugin-dev:create-skill` command.

## About Skills

Skills are modular packages extending Claude's capabilities with specialized knowledge and tools. They transform Claude from general-purpose to specialized by providing procedural knowledge no model fully possesses.

### What Skills Provide

| Type | Purpose | Example |
|------|---------|---------|
| Workflows | Multi-step procedures | Hook creation flow |
| Integrations | File format / API guidance | MCP configuration |
| Domain expertise | Company-specific knowledge | Business rules, schemas |
| Bundled resources | Scripts, references, assets | Validation utilities |

## Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown body
└── Bundled Resources (optional)
    ├── scripts/      - Executable code (deterministic tasks)
    ├── references/   - Documentation loaded as needed
    ├── examples/     - Working code to copy/adapt
    └── assets/       - Files for output (templates, icons)
```

### SKILL.md (Required)

| Component | Purpose |
|-----------|---------|
| `name` | Letters, numbers, hyphens only |
| `description` | When to use (not what it does) |
| Body | Core workflow, quick reference |

### scripts/

Executable code for deterministic or frequently-repeated tasks.

- **When to include:** Same code rewritten repeatedly, deterministic reliability needed
- **Example:** `scripts/validate-hook-schema.sh`
- **Benefits:** Token efficient, may execute without loading into context

### references/

Documentation loaded into context as needed.

- **When to include:** Detailed info Claude should reference while working
- **Examples:** API docs, schemas, patterns, advanced techniques
- **Best practice:** If >10k words, include grep search patterns in SKILL.md

**Avoid duplication:** Content lives in SKILL.md OR references, not both. Prefer references for detail—keeps SKILL.md lean.

### examples/

Working code users copy and adapt.

- **When to include:** Common patterns worth demonstrating
- **Examples:** Complete hook scripts, config files, templates

### assets/

Files for output, not context loading.

- **When to include:** Files used in final output (not documentation)
- **Examples:** Templates, images, fonts, boilerplate

## Progressive Disclosure

Skills use three-level loading to manage context efficiently:

| Level | When Loaded | Size Target |
|-------|-------------|-------------|
| Metadata (name + description) | Always | ~100 words |
| SKILL.md body | When triggered | 1,500-2,000 words |
| Bundled resources | As needed | Unlimited |

**Key principle:** SKILL.md must be self-sufficient for executing the skill. References provide depth on concepts mentioned in the skill—they answer "tell me more about X," not "what's the next step."

## SKILL.md Structure

```markdown
---
name: Skill-Name
description: Use when [specific triggering conditions]
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Bullet list with symptoms and use cases.
When NOT to use.

## Core Pattern
Before/after comparison or quick reference table.

## [Workflow Sections]
Step-by-step procedures as needed.

## Common Mistakes
What goes wrong + fixes.

## Resources
Pointers to references/, examples/, scripts/
```

## Description Quality

Descriptions determine when Claude loads the skill. Include:

- Specific trigger phrases in quotes
- Concrete scenarios (symptoms, contexts)
- Related skills for cross-reference

**Format:** Start with "Use when" or "Use for"

```yaml
# Good
description: Use for "skill file structure", "SKILL.md format", "progressive disclosure" patterns, or organizing skill directories.

# Bad
description: Provides guidance for working with skills.
```

## Directory Structure Patterns

### Minimal Skill
```
skill-name/
└── SKILL.md
```
For: Simple knowledge, no complex resources

### Standard Skill
```
skill-name/
├── SKILL.md
├── references/
│   └── detailed-guide.md
└── examples/
    └── working-example.sh
```
For: Most plugin skills

### Complete Skill
```
skill-name/
├── SKILL.md
├── references/
│   ├── patterns.md
│   └── advanced.md
├── examples/
│   ├── example1.sh
│   └── example2.json
└── scripts/
    └── validate.sh
```
For: Complex domains with utilities

## Plugin-Specific Notes

### Location

```
my-plugin/
├── .claude-plugin/plugin.json
└── skills/
    └── my-skill/
        └── SKILL.md
```

### Auto-Discovery

Claude Code automatically:
1. Scans `skills/` directory
2. Finds subdirectories with SKILL.md
3. Loads metadata always, body when triggered

### Testing

```bash
cc --plugin-dir /path/to/plugin
# Ask questions that should trigger the skill
```

## Study These Examples

Plugin-dev's skills demonstrate best practices:

| Skill | Look For |
|-------|----------|
| `hook-development` | Progressive disclosure with 3 validation scripts |
| `agent-development` | AI-assisted generation prompts in references |
| `mcp-integration` | Comprehensive reference files for complex topic |
| `plugin-settings` | Real-world examples from production plugins |
