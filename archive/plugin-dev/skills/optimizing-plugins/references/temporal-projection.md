# Temporal Projection Reference

Evaluate suggestions across time horizons. Ensure optimizations age well.

## Time Horizons

| Horizon | Key Question | Focus |
|---------|--------------|-------|
| **Now** | Does this solve the immediate problem? | Current utility |
| **1 week** | Will first users succeed? | Initial experience |
| **1 month** | What feedback will we receive? | Early adoption |
| **6 months** | How will usage patterns evolve? | Maturation |
| **1 year** | What ecosystem changes are likely? | External pressure |
| **2 years** | Is the core approach still valid? | Fundamental soundness |

---

## Temporal Analysis Template

For significant suggestions, complete:

```markdown
## Temporal Projection: [Suggestion]

| Horizon | Expected State | Risk | Mitigation |
|---------|---------------|------|------------|
| 6 months | [How it evolves] | [What could break] | [Prevention] |
| 1 year | [How it evolves] | [What could break] | [Prevention] |
| 2 years | [How it evolves] | [What could break] | [Prevention] |

**Timelessness Score:** X/10
**Proceed:** Yes / Revise / Reject
```

---

## Timelessness Scoring

| Score | Description | Verdict |
|-------|-------------|---------|
| 1-3 | Tied to current tools/versions | Reject or abstract |
| 4-6 | Moderate longevity, some dependencies | Revise to reduce coupling |
| **7-8** | **Principle-based, extensible** | **Approve** |
| 9-10 | Timeless, addresses fundamental need | Exemplary |

**Threshold:** Suggestions should score ≥7 or include documented mitigation.

---

## Anti-Obsolescence Patterns

### Do

| Pattern | Example |
|---------|---------|
| **Principle over implementation** | "Validates quality" not "Runs ESLint 8.x" |
| **Version-agnostic** | "Uses configured linter" not "Uses ruff 0.1.5" |
| **Extension points** | "Add patterns to patterns/" not closed list |
| **Loose coupling** | Abstract volatile dependencies |
| **Document WHY** | Decisions include rationale for future maintainers |

### Don't

| Anti-Pattern | Risk |
|--------------|------|
| Hardcoded tool versions | Breaks on updates |
| Platform-specific assumptions | Limits portability |
| Point-in-time references | "Since Claude now supports X..." |
| Closed feature lists | Can't extend without rewrite |
| Missing rationale | Can't adapt when context changes |

---

## Risk Categories

### Low Risk (Score 8-10)
- Addresses fundamental, unchanging need
- Uses stable, principle-based patterns
- Has clear extension points
- No volatile dependencies

### Medium Risk (Score 5-7)
- Depends on current tooling conventions
- Some hardcoded elements
- Limited extension points
- May need revision in 1-2 years

### High Risk (Score 1-4)
- Tied to specific versions
- Hardcoded external dependencies
- No extension mechanism
- Will likely break within 6 months

---

## Application Protocol

### During Synthesis

1. **Select Significant Suggestions:** Those affecting architecture or workflow
2. **Project Forward:** Apply temporal analysis template
3. **Score Timelessness:** 1-10 based on criteria
4. **Flag Risks:** Mark suggestions with score <7
5. **Document Mitigations:** How to reduce temporal risk

### Output Format

```markdown
## Temporal Analysis

| Suggestion | Score | Risk Level | Key Risk | Mitigation |
|------------|-------|------------|----------|------------|
| Add scoring | 9/10 | Low | None | — |
| Pin ruff 0.1.5 | 3/10 | High | Version breaks | Use "configured linter" |
| Add hook validation | 6/10 | Medium | API changes | Abstract to pattern |
```

---

## Integration with Design Document

The design document should include:

```markdown
## Temporal Analysis

### Overall Timelessness: X/10

### Risk Summary
| Risk Level | Count | Examples |
|------------|-------|----------|
| Low | 5 | Scoring, structure changes |
| Medium | 2 | Hook validation, trigger phrases |
| High | 0 | — |

### Mitigations Applied
1. [Suggestion X]: Abstracted to pattern to reduce version coupling
2. [Suggestion Y]: Added extension point for future changes

### Extension Points
1. [Where the design can grow]
2. [How to adapt when context changes]
```

---

## Warning Signs

Flag suggestions that exhibit:

- [ ] Hardcoded version numbers
- [ ] Specific tool names without abstraction
- [ ] "Currently" or "now" language
- [ ] No extension mechanism
- [ ] Tight coupling to external systems
- [ ] Missing rationale for decisions

---

## Temporal Projection Pitfalls

| Avoid | Why | Instead |
|-------|-----|---------|
| Rejecting all due to uncertainty | Paralysis; no improvement | Accept with documented risk |
| Ignoring temporal dimension | Technical debt accumulates | Brief analysis on significant changes |
| Over-engineering for hypotheticals | Wasted effort | Address known evolution paths |
| Assuming stability | Blindsided by change | Document assumptions explicitly |
