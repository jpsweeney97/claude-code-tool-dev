# Conflict Resolution Reference

When lens suggestions conflict, use this priority hierarchy to resolve.

## Priority Hierarchy

Lenses are prioritized by impact of getting them wrong:

| Priority | Lens | Rationale |
|----------|------|-----------|
| **1** | Resilience | Broken behavior is worse than inefficiency |
| **2** | Trigger Fidelity | A skill that doesn't fire is useless |
| **3** | Degrees of Freedom | Wrong rigidity causes failures or missed opportunities |
| **4** | Plugin Coherence | Confusion undermines all other improvements |
| **5** | Structural Clarity | Claude must find information to use it |
| **6** | Token Economy | Efficiency matters only after correctness |

**Rule:** When lenses conflict, higher priority wins unless user explicitly overrides.

---

## Common Conflicts

### Token Economy vs Resilience

**Conflict:**
- Token Economy: "Remove verbose error handling—too long"
- Resilience: "Add more error coverage—gaps exist"

**Resolution:** Resilience wins (Priority 1 > Priority 6)

**Mitigation:** Use progressive disclosure
- Brief error summary in SKILL.md
- Full examples in references/error-patterns.md
- Both lenses satisfied

---

### Trigger Fidelity vs Plugin Coherence

**Conflict:**
- Trigger Fidelity: "Add specific trigger 'debug flaky tests'"
- Plugin Coherence: "Use consistent vocabulary—'test' not 'tests'"

**Resolution:** Trigger Fidelity wins (Priority 2 > Priority 4)

**Mitigation:** Document naming convention
- Accept the specific trigger for invocation
- Add naming guide to README for consistency elsewhere

---

### Structural Clarity vs Token Economy

**Conflict:**
- Structural Clarity: "Add table of contents for navigation"
- Token Economy: "TOC adds 20 lines—cut it"

**Resolution:** Structural Clarity wins (Priority 5 > Priority 6)

**Mitigation:** Minimal TOC
- Include TOC only for files >150 lines
- Use brief section names

---

### Degrees of Freedom vs Structural Clarity

**Conflict:**
- Degrees of Freedom: "Add decision trees for edge cases"
- Structural Clarity: "Keep linear flow—decision trees complicate"

**Resolution:** Degrees of Freedom wins (Priority 3 > Priority 5)

**Mitigation:** Collapsible sections
- Main flow stays linear
- Decision trees in `<details>` blocks
- Complexity available but not in the way

---

## Resolution Protocol

### Step 1: Identify Conflict

During analysis, flag when suggestions contradict:

```markdown
**CONFLICT DETECTED**
- Lens A suggests: [suggestion]
- Lens B suggests: [opposite suggestion]
```

### Step 2: Apply Priority

1. Check priority of each lens
2. Higher priority lens wins by default
3. State the winner and rationale

### Step 3: Seek Mitigation

Ask: "Can we satisfy both lenses partially?"

Common mitigations:
- **Progressive disclosure:** Move detail to references
- **Collapsible sections:** Complexity available but hidden
- **Documentation:** Accept one, document why
- **Compromise:** Partial implementation of each

### Step 4: Document Resolution

```markdown
## Conflict Resolution: [Lens A] vs [Lens B]

**Conflict:** [What contradicts]
**Winner:** [Lens] (Priority N > Priority M)
**Mitigation:** [How losing lens is partially addressed]
**Rationale:** [Why this trade-off is acceptable]
```

---

## Resolution in Design Document

The design document should include:

```markdown
## Resolved Conflicts

| Conflict | Lenses | Resolution | Mitigation |
|----------|--------|------------|------------|
| Verbosity vs Coverage | Token↔Resilience | Resilience wins | Progressive disclosure |
| Specificity vs Naming | Trigger↔Coherence | Trigger wins | Naming guide in README |
```

---

## User Override

If user disagrees with priority-based resolution:

1. Present the default resolution
2. Explain priority rationale
3. Ask: "Would you like to override this?"
4. If yes, document user's reasoning
5. Proceed with user's choice

**Note:** User override is valid—they know their context better. Document it for future reference.

---

## Conflict Detection Checklist

During synthesis, verify:

- [ ] All suggestion pairs checked for conflicts
- [ ] Conflicts flagged with both perspectives
- [ ] Priority-based resolution applied
- [ ] Mitigations identified where possible
- [ ] Resolutions documented in design
