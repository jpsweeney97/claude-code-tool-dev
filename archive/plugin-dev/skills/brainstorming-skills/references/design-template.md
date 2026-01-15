# Skill Design: [Name]

**Date:** YYYY-MM-DD
**Author:** [Name]
**Status:** Draft | Ready for Implementation

## Purpose

[One sentence: what this skill does and why it matters]

## Triggers

- [natural phrase 1]
- [natural phrase 2]
- [natural phrase 3]
- [natural phrase 4 - optional]
- [natural phrase 5 - optional]

**Trigger quality check:** Would Claude find this skill when a user says these phrases?

## Scope

### In Scope

- [what this skill handles - be specific]
- [another thing it handles]
- [another thing it handles]

### Out of Scope

- [what this skill does NOT handle]
- [another exclusion]
- [another exclusion]

### Adjacent Skills

| Skill | Relationship |
|-------|--------------|
| [skill-name] | [how they relate] |

## Structure

| Component | Content |
|-----------|---------|
| SKILL.md | [outline of main sections] |
| references/ | [list files needed, or "none"] |
| scripts/ | [list scripts needed, or "none"] |
| examples/ | [list examples needed, or "none"] |

### SKILL.md Outline

```
# [Skill Name]

## Quick Start
[Brief overview]

## The Process
### Step 1: [Name]
### Step 2: [Name]
...

## Anti-Patterns
[Table of what to avoid]

## Verification
[How to know it's done correctly]
```

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| [pattern] | [reason] | [alternative] |

## Success Criteria

How to know the skill is working correctly:
- [ ] [criterion 1]
- [ ] [criterion 2]
- [ ] [criterion 3]

## Open Questions

- [Any unresolved design questions]
- [Decisions deferred to implementation]

## Next Steps

After this design is approved:
1. Run `/implementing-skills docs/plans/[this-file].md`
2. Follow TDD process (RED-GREEN-REFACTOR)
3. Test with pressure scenarios
