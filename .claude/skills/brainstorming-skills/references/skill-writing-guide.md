# Skill Writing Guide

Essential principles for writing effective skills. **Read this before drafting any SKILL.md.**

---

## Philosophy

**The context window is a public good.** Your skill competes with conversation history, other skills, and user requests. Challenge every line: "Does Claude need this? Can I assume Claude knows this? Does this justify its token cost?"

**Claude is already smart.** Only add context Claude doesn't have. Skip explanations of common concepts.

**Match specificity to fragility:**

| Freedom | When to Use | Example |
|---------|-------------|---------|
| High | Multiple valid approaches; context-dependent | Code review guidelines |
| Medium | Preferred pattern exists; some variation OK | Report templates with customization |
| Low | Fragile operations; consistency critical | Database migrations, exact scripts |

*Narrow bridge = low freedom (one safe path). Open field = high freedom (many paths work).*

**One default, not menus.** Don't offer "use X or Y or Z." Provide one recommended approach with escape hatches for exceptions.

---

## Requirements

**Name:**
- Kebab-case, ≤64 characters
- Gerund form preferred: `processing-pdfs`, `analyzing-data`, `writing-tests`
- Avoid: vague names (`helper`, `utils`), reserved words (`claude-*`, `anthropic-*`)

**Description:**
- Trigger conditions ONLY — never summarize workflow or outcomes
- Third person (injected into system prompt)
- ≤1024 characters
- Include key terms for discoverability

```
❌ BAD: "Guides comments toward explaining intent" (describes outcome)
❌ BAD: "Helps write better error messages" (describes what skill does)
❌ BAD: "Enforces TDD by requiring tests first" (summarizes workflow)

✅ GOOD: "Use when adding comments to code"
✅ GOOD: "Use when writing code that raises exceptions"
✅ GOOD: "Use when implementing features, before writing code"
```

**Why this matters:** Claude may follow the description instead of reading the skill body. Outcome descriptions become shortcuts that bypass the actual guidance.

**Body:**
- Under 500 lines
- Split to reference files if approaching limit

---

## Structure

**Progressive disclosure:** SKILL.md is a table of contents. Point to detailed files; Claude loads them as needed.

**One level deep.** All references link directly from SKILL.md. Nested references get partially read.

**TOC for long files.** Reference files >100 lines need a table of contents so Claude sees full scope even when previewing.

**Consistent terminology.** Pick one term and use it throughout. "API endpoint" everywhere, not mixed with "URL", "route", "path".

---

## Compliance Techniques

LLMs respond to persuasion. Use these deliberately for discipline-enforcing skills.

**Authority:** Imperative language eliminates rationalization.
- "YOU MUST", "Never", "No exceptions"
- Removes "is this an exception?" decisions

**Commitment:** Force explicit choices and tracking.
- "Announce: 'I'm using [Skill Name]'"
- Use TodoWrite for checklists
- Public declaration → consistency pressure

**Scarcity:** Time-bound requirements prevent "I'll do it later."
- "IMMEDIATELY after X"
- "Before proceeding"
- Sequential dependencies

**Social Proof:** Establish norms via universal patterns.
- "Every time", "Always"
- "X without Y = failure"

**By skill type:**

| Type | Use | Avoid |
|------|-----|-------|
| Discipline-enforcing | Authority + Commitment + Social Proof | Liking |
| Guidance/technique | Moderate Authority + Unity | Heavy authority |
| Collaborative | Unity + Commitment | Authority |
| Reference | Clarity only | All persuasion |

**Key insight:** Bright-line rules reduce rationalization. "When X, do Y" is more effective than "generally do Y."

---

## Quality Dimensions

Apply these to reduce ambiguity and prevent drift.

**A. Intent fidelity**
- State primary goal explicitly
- List non-goals to prevent scope creep
- Distinguish must-haves from nice-to-haves

**B. Constraint completeness**
- "Allowed: ..." / "Forbidden: ..."
- "If constraint blocks progress, STOP and ask for: ..."

**C. Terminology clarity**
- "In this skill, 'X' means: ..."
- Define overloaded terms once, reuse consistently

**D. Evidence anchoring**
- "Confirm `<file>` exists before acting"
- "Do not assume `<tool>`; check `<cmd> --version`"

**E. Decision sufficiency**
- Every decision point: condition → action → alternative
- "If two interpretations exist, STOP and ask"

**F. Verification validity**
- Quick check measures primary success property
- Include failure interpretation: likely causes + next step

**G. Artifact usefulness**
- Specify output format, required fields, ordering
- Tailor to consumer (reviewer, operator, user)

**H. Minimality**
- "Prefer smallest correct change"
- "If you need dependency/scope change, STOP and justify"

**I. Calibration**
- Label claims: Verified / Inferred / Assumed
- "Not run (reason): ... Run `<cmd>` to verify"

---

## Patterns

### Feedback Loops

**Run → fix → repeat.** This pattern dramatically improves quality.

```markdown
1. Draft content following STYLE_GUIDE.md
2. Review against checklist
3. If issues found:
   - Note each issue with specific reference
   - Revise
   - Review again
4. Only proceed when all requirements met
```

For code: `validate.py` → fix errors → validate again → only then proceed.

### Checklists for Multi-Step Workflows

Provide checklists Claude can track. Use TodoWrite for enforcement. Clear steps prevent skipping critical validation.

### Verifiable Intermediate Outputs

For complex tasks: **plan → validate → execute**

1. Claude creates plan file (e.g., `changes.json`)
2. Script validates plan before execution
3. Catches errors early, enables iteration without touching originals

Use for: batch operations, destructive changes, high-stakes operations.

### Template Pattern

**Strict** (API responses, data formats): "ALWAYS use this exact structure"
**Flexible** (reports, analysis): "Sensible default; adapt as needed"

### Examples Pattern

Two formats, different purposes:

**BAD/GOOD comparisons** — Use in SKILL.md Examples section to show skill impact:
- BAD: What Claude does/produces without the skill
- GOOD: What Claude does/produces with the skill
- Include "Why it's bad/good" explanations

**Input/output pairs** — Use when demonstrating transformations within the skill:

```markdown
**Example 1:**
Input: Added user authentication
Output: feat(auth): implement JWT-based authentication
```

Use BAD/GOOD for skill verification (does the skill change behavior?). Use input/output for teaching format/style.

### Solve, Don't Punt

Scripts should handle errors, not defer to Claude. Verbose error messages help Claude fix issues: "Field 'X' not found. Available: A, B, C."

---

## Checklist

Before finalizing any skill:

**Core:**
- [ ] Description contains trigger conditions only (no workflow)
- [ ] Description is third person
- [ ] Body under 500 lines
- [ ] Consistent terminology throughout
- [ ] References one level deep from SKILL.md
- [ ] Examples are concrete, not abstract

**Quality:**
- [ ] Primary goal stated; non-goals listed
- [ ] Decision points have condition → action → alternative
- [ ] Verification checks measure actual success property
- [ ] Feedback loops for quality-critical tasks

**Compliance (discipline skills):**
- [ ] Authority language for critical requirements
- [ ] Explicit choices or TodoWrite tracking
- [ ] Bright-line rules, not "use judgment"

**Code/Scripts:**
- [ ] Scripts handle errors (don't punt)
- [ ] Validation steps for critical operations
- [ ] Plan-validate-execute for complex tasks
