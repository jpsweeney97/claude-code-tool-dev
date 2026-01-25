# Testing Template/Generation Skills

Skills that produce specific output formats, documents, or structured artifacts.

**Examples:** Report generators, document templates, code scaffolding, structured output formats

## The Format Challenge

Template skills must verify:
1. **Structural compliance** — Does output match required structure?
2. **Field completeness** — Are all required fields present?
3. **Content quality** — Is content appropriate (not just structurally correct)?
4. **Adaptability** — Does the template work across different inputs?

## Scenario Templates

**Template A: Structure Validation**

```markdown
Using [TEMPLATE SKILL], generate output for:

[INPUT DATA]

The output must include:
- [REQUIRED SECTION 1]
- [REQUIRED SECTION 2]
- [REQUIRED SECTION 3]

Generate the output.
```

Check: Does output contain all required sections in correct structure?

**Template B: Edge Case Input**

```markdown
Using [TEMPLATE SKILL], generate output for this edge case:

[MINIMAL/UNUSUAL/EDGE CASE INPUT]

Generate the output, adapting the template as needed.
```

Check: Does output handle edge case gracefully without breaking structure?

**Template C: Content vs Structure**

```markdown
Using [TEMPLATE SKILL], generate output for:

[INPUT THAT COULD PRODUCE STRUCTURALLY CORRECT BUT LOW-QUALITY CONTENT]

Generate the output.
```

Check: Is content meaningful, or just placeholder text in correct structure?

**Template D: Format Under Pressure**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are using [TEMPLATE SKILL]. The user says:
"I need this report ASAP. Don't worry about [REQUIRED SECTION], just give me the main points."

Options:
A) Omit the section as requested
B) Include a minimal version of the section
C) Explain why the section is required and include it fully

Choose A, B, or C.
```

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Structural compliance | Required sections present / Total required | 100% | <100% |
| Field completeness | Required fields populated / Total required | 100% | Missing fields |
| Schema validation | Passes format validation | Pass | Fail |
| Content quality | Meaningful content / Total sections | High | Placeholder text |
| Edge case handling | Valid output on edge cases / Total edge cases | >90% | <70% |
| Adaptability | Works across input variations | Flexible | Rigid/breaks |

## Worked Example: Handoff Document Skill

**Skill summary:** Generates structured handoff documents for session continuity

**Template structure:**
```yaml
---
date: YYYY-MM-DD
project: <project-name>
branch: <current-branch>
---
# Handoff: <title>
## Goal
## Decisions
## Changes
## Next Steps
## References
```

**Baseline scenario (RED) — WITHOUT skill:**

```markdown
Create a handoff document for continuing this session later.
```

**Expected baseline failure:** Agent might:
- Miss required frontmatter fields
- Use inconsistent section ordering
- Omit critical sections (Next Steps, References)
- Include narrative instead of actionable items

**Verification scenario (GREEN) — WITH skill:**

Same request. Agent should:
1. Include all frontmatter fields
2. Follow exact section ordering
3. Populate all required sections
4. Use actionable format (not narrative)

**Edge case scenario:**

```markdown
Create a handoff document, but there were no code changes this session — only research.
```

Check: Does output adapt gracefully (e.g., "## Changes: None — research session only")?
