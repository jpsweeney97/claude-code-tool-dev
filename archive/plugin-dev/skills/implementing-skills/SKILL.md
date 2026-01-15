---
name: implementing-skills
description: Use when building a skill from a design, "implement this skill",
  "write the skill", "TDD for skills", "pressure testing skills", or
  "validating skill effectiveness". For structure reference, see skill-development.
  For deep creation methodology, see skillforge.
---

# Implementing Skills

Build skills using test-driven development: write failing tests first, then write the skill to pass them.

## Pipeline Context

This skill is **Stage 3: Implement** in the plugin development pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Build skill from design using TDD |
| Previous | `/brainstorming-skills` (design document) |
| Next | `/optimizing-plugins` or personal use |

**Full pipeline:** See `references/pipeline-overview.md` in brainstorming-plugins.

## Prerequisites Check

Before proceeding, verify:

1. **Design document exists?**
   - If yes: "I see the design at `[path]`. Proceeding with implementation."
   - If no: "I don't see a design document. Should we start with `/brainstorming-skills`?"

2. **Design has required sections?**
   - Purpose statement
   - Trigger phrases (3-5)
   - Scope boundaries (in/out)

If any section is missing, ask: "The design is missing [sections]. Should we complete it first?"

**No formal design?** You can proceed with a clear mental model, but document what you're building first.

## Related Skills

For **file structure** (directories, SKILL.md format, progressive disclosure), see the `skill-development` skill.

For **full autonomous creation** with 11 thinking lenses, evolution scoring, and synthesis panel, use the `skillforge` skill.

## Overview

Write test cases (pressure scenarios with subagents), watch them fail (baseline behavior), write the skill, watch tests pass (agents comply), refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**Skill Architecture Principle:**
- SKILL.md = Complete workflow, self-sufficient for using the skill
- References = Deep knowledge on elemental concepts mentioned in the skill
- If Claude must read a reference to execute the skill, that content belongs in SKILL.md

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in CLAUDE.md)
- Mechanical constraints enforceable with validation

### Skill Types

| Type | What It Is | Test Approach |
|------|------------|---------------|
| **Technique** | Concrete method with steps | Application scenarios |
| **Pattern** | Way of thinking about problems | Recognition + counter-examples |
| **Reference** | API docs, syntax guides | Retrieval + gap testing |
| **Discipline** | Rules/requirements to follow | Pressure scenarios |

## The TDD Process

### The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS to existing skills. Write skill before testing? Delete it. Start over.

**No exceptions:** Not for "simple additions," "just adding a section," or "documentation updates."

### RED: Write Failing Test (Baseline)

Run pressure scenario with subagent WITHOUT the skill. Document:
- What choices did they make?
- What rationalizations did they use (verbatim)?
- Which pressures triggered violations?

This is "watch the test fail"—see what agents naturally do before writing the skill.

### GREEN: Write Minimal Skill

Write skill addressing those specific rationalizations. Don't add content for hypothetical cases.

Run same scenarios WITH skill. Agent should now comply.

### REFACTOR: Close Loopholes

Agent found new rationalization? Add explicit counter. Re-test until bulletproof.

**Testing methodology:** See `references/testing-skills-with-subagents.md` for pressure scenarios, pressure types, and systematic hole-plugging.

## Writing the Skill

### Claude Search Optimization (CSO)

**Critical:** Future Claude needs to FIND your skill.

#### Description Field

| Aspect | Guidance |
|--------|----------|
| Format | Start with "Use when..." |
| Content | Triggering conditions only |
| Avoid | Summarizing workflow (Claude will follow description instead of reading skill) |
| Person | Third person (injected into system prompt) |

```yaml
# Bad - summarizes workflow
description: Use when executing plans - dispatches subagent per task with code review

# Good - just triggers
description: Use when executing implementation plans with independent tasks
```

#### Keywords

Use words Claude would search for:
- Error messages: "Hook timed out", "race condition"
- Symptoms: "flaky", "hanging", "pollution"
- Synonyms: "timeout/hang/freeze", "cleanup/teardown"
- Tools: Actual commands, library names

#### Naming

- Active voice, verb-first: `creating-skills` not `skill-creation`
- Gerunds work well: `debugging-with-logs`, `testing-skills`
- Name by what you DO: `condition-based-waiting` not `async-helpers`

### Skill Content Guidelines

**One excellent example beats many mediocre ones.** Choose most relevant language:
- Testing → TypeScript/JavaScript
- System debugging → Shell/Python
- Data processing → Python

**Cross-referencing other skills:**
- Use: `**REQUIRED SUB-SKILL:** Use superpowers:test-driven-development`
- Avoid: `@skills/path/SKILL.md` (force-loads, burns context)

**Flowcharts:** Use ONLY for non-obvious decision points or "when to use A vs B" decisions. Never for reference material, code examples, or linear instructions.

## Testing by Skill Type

### Discipline Skills (rules/requirements)

Test with pressure scenarios combining multiple pressures:
- Time pressure
- Sunk cost
- Authority signals
- Exhaustion cues

**Success:** Agent follows rule under maximum pressure.

### Technique Skills (how-to guides)

Test with application scenarios:
- Can they apply correctly?
- Do they handle edge cases?
- Are instructions complete?

**Success:** Agent successfully applies technique to new scenario.

### Pattern/Reference Skills

Test with recognition and retrieval:
- Do they recognize when pattern applies?
- Can they find the right information?
- Are common use cases covered?

## Bulletproofing Against Rationalization

Skills enforcing discipline need to resist rationalization under pressure.

### Close Every Loophole Explicitly

```markdown
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Delete means delete
```

### Build Rationalization Table

Capture rationalizations from baseline testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |

### Create Red Flags List

```markdown
## Red Flags - STOP and Start Over

- Code before test
- "I already manually tested it"
- "This is different because..."

**All of these mean: Delete. Start over.**
```

## Checklist

**Use TodoWrite to create todos for each item.**

**RED Phase:**
- [ ] Create pressure scenarios (3+ combined pressures for discipline skills)
- [ ] Run WITHOUT skill - document baseline verbatim
- [ ] Identify rationalization patterns

**GREEN Phase:**
- [ ] Name uses only letters, numbers, hyphens
- [ ] Description starts "Use when..." with specific triggers
- [ ] Description in third person
- [ ] Address specific baseline failures
- [ ] Run WITH skill - verify compliance

**REFACTOR Phase:**
- [ ] Identify NEW rationalizations
- [ ] Add explicit counters
- [ ] Build rationalization table
- [ ] Re-test until bulletproof

**Quality:**
- [ ] Quick reference table included
- [ ] Common mistakes section
- [ ] No narrative storytelling
- [ ] Supporting files only for tools or heavy reference

**Deployment:**
- [ ] Commit to git
- [ ] STOP after each skill - don't batch without testing

## The Bottom Line

**Creating skills IS TDD for process documentation.**

Same Iron Law: No skill without failing test first.
Same cycle: RED (baseline) → GREEN (write skill) → REFACTOR (close loopholes).
Same benefits: Better quality, fewer surprises, bulletproof results.

## Output

Working skill in correct location:
- Plugin skill: `plugin-name/skills/skill-name/SKILL.md`
- Personal skill: `~/.claude/skills/skill-name/SKILL.md`

Plus any references/, scripts/, examples/ as designed.

## Next Step

Choose one and run:

| Situation | Command |
|-----------|---------|
| More components to build | `/brainstorming-{component}` for next component |
| Plugin complete, want polish | `/optimizing-plugins` |
| Personal use only | Done — skill is active |

## References

- `references/testing-skills-with-subagents.md` - Full TDD methodology for skills
- `references/pressure-scenario-design.md` - Designing effective pressure scenarios
- `references/bulletproofing-rationalization.md` - Countering agent rationalizations
- `references/persuasion-principles.md` - Psychology of rationalization resistance
- `references/anthropic-best-practices.md` - Official Anthropic guidance
- brainstorming-skills — Design phase (if design needed)
- brainstorming-plugins/references/pipeline-overview.md — Full pipeline
