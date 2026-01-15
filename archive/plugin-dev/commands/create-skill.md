---
description: Create a new skill using SkillForge's rigorous 5-phase methodology with triage, analysis, specification, generation, and multi-agent review
argument-hint: "<goal> [--quick|--plan-only]"
allowed-tools: [Task, Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Skill, AskUserQuestion]
model: claude-opus-4-5-20251101
---

# Create Skill

Create a production-ready Claude Code skill using SkillForge methodology.

## Usage

```
/plugin-dev:create-skill <goal>
/plugin-dev:create-skill --quick <goal>
/plugin-dev:create-skill --plan-only <goal>
```

## Options

| Option | Effect |
|--------|--------|
| (none) | Full 5-phase methodology with synthesis panel |
| `--quick` | Streamlined creation (skip multi-lens deep dives) |
| `--plan-only` | Generate specification only, no generation |

## Process

This command invokes the `skillforge` skill which executes:

0. **Phase 0: Triage** - Routes to USE_EXISTING / IMPROVE_EXISTING / CREATE_NEW / COMPOSE / CLARIFY
1. **Phase 1: Deep Analysis** - 11 thinking lenses, regression questioning
2. **Phase 2: Specification** - XML spec with evolution scoring (≥7 required)
3. **Phase 3: Generation** - SKILL.md, references/, assets/
4. **Phase 4: Synthesis Panel** - 3 Opus agents must unanimously approve

## Execution

Load and follow the skillforge skill:

**REQUIRED:** Use the `skillforge` skill to create the requested skill.

Parse the user's goal from the command arguments. If `--quick` is specified, inform the skill to use reduced analysis depth. If `--plan-only` is specified, stop after Phase 2.

After completion, run validation:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/skillforge/scripts/quick_validate.py <skill-path>
```

## Related

- `skill-development` - Structural reference for skill anatomy
- `implementing-skills` - TDD testing methodology
- `skill-reviewer` agent - Post-creation quality review
