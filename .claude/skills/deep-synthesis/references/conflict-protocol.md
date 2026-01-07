# Conflict Resolution Protocol

Detailed protocol for Phase 4: Synthesis. Guides resolution of conflicts between repos.

---

## Conflict Types

| Type | Definition | Resolution Basis |
|------|------------|------------------|
| **Direct** | Same trigger, file, or config key | Empirical (which works better) |
| **Philosophical** | Different approaches to same goal | Preference (target philosophy) |
| **Incompatible** | A requires X, B breaks X | Choose one (document exclusion) |
| **Complementary** | A handles X, B handles Y | Verify compatibility, combine |

---

## Resolution Process

### Step 1: Classify Conflict Type

```markdown
**Conflict:** [brief description]
**Type:** [Direct / Philosophical / Incompatible / Complementary]
**Repos:** [A], [B]
**Items:** [item from A] vs [item from B]
```

---

### Step 2: Gather Evidence

**For Empirical conflicts** (Direct, some Incompatible):

| Evidence Type | How to Gather | Weight |
|---------------|---------------|--------|
| **Primary** | Run both, measure, compare | Highest |
| **Secondary** | Inspect source, read docs | Medium |
| **Tertiary** | Check stars, community sentiment | Lowest |

**For Preference conflicts** (Philosophical):

| Input | Source |
|-------|--------|
| Target philosophy | Section 1: Target Analysis |
| User stated preferences | Pre-flight or episodic memory |
| Skill defaults | Minimal > Maximal unless stated |

See [evidence-hierarchy.md](evidence-hierarchy.md) for detailed guidance.

---

### Step 3: Document Comparison

```markdown
| Aspect | Repo A | Repo B |
|--------|--------|--------|
| Approach | [description] | [description] |
| Evidence level | [Primary/Secondary/Tertiary] | [Primary/Secondary/Tertiary] |
| [metric if applicable] | [value] | [value] |
| Alignment with target | [assessment] | [assessment] |
```

---

### Step 4: Make Decision

| Decision | When to Use | Requires |
|----------|-------------|----------|
| **Choose A** | A clearly better | Evidence citation |
| **Choose B** | B clearly better | Evidence citation |
| **Hybrid** | Best of both possible | Specification of what from each |
| **Neither** | Both problematic | Justification for excluding both |

---

### Step 5: Label Decision Type

| Type | Definition | Documentation Required |
|------|------------|------------------------|
| **EMPIRICAL** | Based on measurable evidence | Primary or strong Secondary evidence cited |
| **PREFERENCE** | Based on philosophy/values | Reference to target philosophy |

**Rule:** Be honest about decision type. Preference decisions are valid but should not be disguised as empirical.

---

### Step 6: Assign Confidence

**Evidence ceiling applies:** Your confidence CANNOT exceed the maximum allowed by your evidence basis.

| Evidence Basis | Maximum Confidence |
|----------------|-------------------|
| Primary + cross-reference | Certain |
| Primary alone | Probable |
| Secondary only | Probable |
| Tertiary only | Possible |

See [evidence-hierarchy.md](evidence-hierarchy.md) for definitions.

**Process:**
1. Identify your strongest evidence for this resolution
2. Classify it as Primary/Secondary/Tertiary
3. Look up the maximum confidence allowed
4. Assign confidence AT OR BELOW that ceiling

**If you believe higher confidence is warranted:** Gather stronger evidence first. Do not override the ceiling—it exists to prevent false precision.

| Confidence | Meaning |
|------------|---------|
| **Certain** | Primary evidence with cross-reference, clear winner, no reasonable alternative |
| **Probable** | Primary or strong secondary evidence, reasonable confidence |
| **Possible** | Tertiary evidence or close call, notable uncertainty |

---

### Step 7: Document Resolution

```markdown
## Conflict C[N]: [descriptive name]

**Type:** [Empirical / Preference]
**Repos:** [A], [B]

### Comparison

| Aspect | [A] | [B] |
|--------|-----|-----|
| Approach | [description] | [description] |
| Evidence | [level] | [level] |
| [metric] | [value] | [value] |

### Resolution

**Choice:** [A / B / Hybrid / Neither]
**Rationale:** [2-3 sentences explaining WHY]
**Decision type:** [EMPIRICAL / PREFERENCE]
**Confidence:** [Certain / Probable / Possible]
```

---

## Special Cases

### Philosophical Conflicts Without Target Philosophy

If target philosophy is not explicitly stated:

1. Check episodic memory for past decisions
2. Infer from existing target patterns
3. Default: prefer minimal over maximal
4. Document as: "PREFERENCE (inferred: minimal)"

### Three-Way+ Conflicts

When 3+ repos conflict on the same item:

1. Don't treat as multiple pairwise conflicts
2. Evaluate all approaches together
3. Find overall best, not tournament-style winner
4. Document: "Compared A vs B vs C; selected B because [reason]"

### Complementary Items That Fail Compatibility

If compatibility-checklist.md reveals hidden conflicts:

1. Reclassify as appropriate conflict type (Direct/Incompatible)
2. Follow this protocol for resolution
3. Document the reclassification

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Resolving without evidence | Unreliable decisions | Always cite evidence or philosophy |
| Disguising preference as empirical | Undermines trust | Be honest about decision type |
| Choosing based on familiarity | Bias, not merit | Evaluate on criteria |
| Skipping documentation | Not reproducible | Document every resolution |
| Defaulting to "Neither" | Loses value | Only if both truly problematic |
