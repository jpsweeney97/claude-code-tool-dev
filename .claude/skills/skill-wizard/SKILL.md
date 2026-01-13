---
name: skill-wizard
description: >
  Guided skill creation with spec compliance validation. Use when creating
  a new Claude Code skill from scratch, when you want interactive authoring
  with inline validation, or when you need help meeting the skills-as-prompts
  spec requirements. Walks through all 8 required sections, generates draft
  content, validates against structural and semantic quality criteria, and
  produces a compliant SKILL.md.
license: MIT
metadata:
  version: "1.0.0"
  category: meta-skills
  risk_tier: low
  spec_version: "skills-as-prompts-strict-v1"
  timelessness_score: 8
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# Skill Wizard

## When to Use

- User wants to create a new Claude Code skill from scratch
- User has an idea but doesn't know the spec requirements
- User wants guided, interactive skill authoring with validation
- User says "create a skill", "new skill", "skill wizard", "/skill-wizard"

**Primary goal:** Guide authors from skill idea to spec-compliant SKILL.md through structured dialogue, draft generation, and inline validation.

## When NOT to Use

**STOP conditions:**

- **STOP** if user has an existing complete draft they want validated, not created.
  Route to: `skill-reviewer` agent or manual review against compliance checklist.

- **STOP** if user wants quick scaffolding without compliance validation.
  Route to: `skillforge --quick` or manual creation from `skill-skeleton.md`.

- **STOP** if user wants to audit multiple existing skills in batch.
  Route to: dedicated audit workflow or `skill-reviewer` in batch mode.

- **STOP** if the task is creating a simple command, not a full skill.
  Route to: `.claude/commands/` directory (commands don't need 8 sections).

- **STOP** if user cannot articulate what the skill should do after 2 clarifying questions.
  The wizard requires a clear purpose to generate meaningful drafts.

**Non-goals:**

- Does not review or grade existing skills (that's assessment, not creation)
- Does not generate skills autonomously without user input at each section
- Does not modify skills after initial creation (use Edit tool directly)
- Does not create skill directories or file structure (only writes SKILL.md)
- Does not install dependencies or configure the environment

## Inputs

**Required:**

- **Skill purpose**: What the skill does (gathered during discovery)
- **Output path**: Where to write the final SKILL.md

**Optional:**

- Category hint: If user knows the category upfront
- Risk tier override: If user wants to force a specific tier
- Exception flags: Known exceptions to flag upfront

**Constraints:**

- Write access to target directory
- No external dependencies (wizard is self-contained)
- If target path has existing SKILL.md, wizard warns before overwrite

**Fallback:** If write fails, wizard presents skill content in conversation for manual copy.

## Outputs

**Artifacts:**

- `SKILL.md` at user-specified path (complete skill with all 8 sections)
- Compliance summary in conversation

**Definition of Done:**

1. **File created:** `test -f <path>/SKILL.md` returns 0
2. **All 8 sections present:** `grep -c "^## " <path>/SKILL.md` returns >=8
3. **Zero MUST violations:** Compliance summary shows all MUST requirements passed
4. **Cross-section consistency:** Final check found no reference errors
5. **Frontmatter valid:** Name is kebab-case <=64 chars, description <=1024 chars
6. **Wizard metadata removed:** No `metadata.wizard` block in final file
