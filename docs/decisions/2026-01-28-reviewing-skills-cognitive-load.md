# Decision: Improving Reference Guidance in reviewing-skills

**Date:** 2026-01-28
**Status:** Recommended (Final)
**Stakes:** Rigorous
**Protocol:** decision-making.framework@1.0.0

## Context

The reviewing-skills skill was initially identified as having "cognitive load" issues. Through iterative analysis, this framing was refined multiple times:

### Framing Evolution

| Iteration | Framing | Why It Was Wrong |
|-----------|---------|------------------|
| 1 | "16 dimensions create parallel cognitive load" | Dimensions are checked sequentially, not in parallel |
| 2 | "Entry Gate ceremony and upfront TaskCreates are overhead" | These are structure, not burden; TaskCreate externalizes tracking (reduces load) |
| 3 | "Reference jumping to 1180-line file is overhead" | Agents read ~60 lines per dimension, not 1180; file has TOC |
| **Final** | **"Supporting file references lack clear guidance"** | **Correct problem identified** |

### The Actual Problem

The skill has 6 supporting files, but SKILL.md doesn't clearly guide agents on:

1. **What** to consult — which file for which purpose
2. **When** to consult — at what point in the process
3. **How** to consult — what to look for, how to apply it

| File | Current Reference in SKILL.md | Gap |
|------|-------------------------------|-----|
| dimension-definitions.md | "For detailed checking guidance, see..." | When to use full guidance vs. trusting own judgment? How to apply it? |
| skill-type-adaptation.md | Mentioned in DISCOVER for "priority adjustments" | How to identify skill type first? When exactly in DISCOVER? |
| framework-for-thoroughness.md | Listed as "Protocol" in Overview | When would you need to consult this vs. trust SKILL.md's summary? |
| examples.md | "See Examples for worked examples" | When to consult? Before starting? When stuck? |
| troubleshooting.md | "For common issues..." | Only when something goes wrong? Proactively? |
| verification-checklist.md | "For detailed verification checklist..." | How does this relate to Exit Gate section already in SKILL.md? |

### What Is NOT a Problem

The following were initially considered problems but are actually well-designed:

| Aspect | Why It's Fine |
|--------|---------------|
| 7-step Entry Gate | Steps are sequential and necessary; each serves a purpose |
| 16 upfront TaskCreates | Externalizes tracking, *reduces* cognitive load |
| Sequential dimension checking | One thing at a time is manageable |
| Yield% calculation | Precise convergence signal; complexity is justified |
| 16 dimensions | They catch real issues; quantity is appropriate |

## Decision Statement

How should SKILL.md better guide agents on when and how to consult its supporting files?

## Constraints

1. Must not duplicate content from supporting files (single source of truth)
2. Must be concise enough to actually read
3. Must integrate naturally with the existing process structure
4. Must not require restructuring supporting files

## Criteria

| Criterion | Weight |
|-----------|--------|
| Clarity of guidance | 5 |
| Integration with process | 4 |
| Conciseness | 4 |
| Maintainability | 3 |
| Implementation effort | 2 |

## Options Considered

### Option A: Reference Files Section

Add a dedicated "Reference Files" section near the top of SKILL.md with a table mapping each file to when/how to use it.

**Pros:** Single location for all reference guidance; easy to find
**Cons:** Separated from point of use; agents must remember to check it

### Option B: Enhanced Inline References

Improve each inline reference throughout SKILL.md to include when/how guidance at point of use.

**Pros:** Guidance appears exactly when needed
**Cons:** Scattered throughout; harder to get overview; repetitive if same file referenced multiple times

### Option C: Both (Reference Section + Enhanced Inline)

Add Reference Files section for overview, AND improve inline references for point-of-use guidance.

**Pros:** Overview available; guidance at point of use
**Cons:** Some redundancy; maintenance of two locations

### Option D: Null

Accept current reference style.

## Evaluation

| Option | Clarity (5) | Integration (4) | Concise (4) | Maintain (3) | Impl (2) | Total |
|--------|-------------|-----------------|-------------|--------------|----------|-------|
| A: Reference Section | 4 | 3 | 5 | 5 | 5 | 76 |
| B: Enhanced Inline | 4 | 5 | 3 | 3 | 3 | 68 |
| **C: Both** | 5 | 5 | 4 | 4 | 3 | **80** |
| D: Null | 2 | 3 | 5 | 5 | 5 | 62 |

**Frontrunner:** Option C (Both)

## Adversarial Analysis

**Kill it:** Two locations (section + inline) creates maintenance burden and potential inconsistency.
**Response:** Reference section is overview ("what exists"); inline is contextual ("use it now for X"). Different purposes, minimal overlap. If they diverge, inline takes precedence.

**Pre-mortem:** "Agents skip the Reference Files section because it's at the top and they jump to Process."
**Response:** Reference section is for orientation, not mandatory reading. Inline references catch agents at point of need.

**Steelman Option A alone:** Simpler, single location, easy to maintain.
**Response:** Reference section alone doesn't help agents mid-process. They'd need to scroll up, find the table, then scroll back. Inline guidance is essential for flow.

## Recommendation

**Add Reference Files Section + Enhance Key Inline References**

### Implementation

**1. Add Reference Files section after Overview, before When to Use:**

```markdown
## Reference Files

This skill uses supporting files for detailed guidance. Consult them as indicated:

| File | Consult When | How to Use |
|------|--------------|------------|
| [dimension-definitions.md](dimension-definitions.md) | During EXPLORE, when checking each dimension | Read the full section for the dimension: "What it catches" (context), "How to check" (process), "Red flags" and "Good patterns" (calibration), "Pass criteria" (completion), "Example findings" (formatting your own). |
| [skill-type-adaptation.md](skill-type-adaptation.md) | During DISCOVER, after listing initial dimensions | Use "Identifying Skill Type" table to classify the skill, then apply "Elevate Priority" and "Additional Checks" for that type. |
| [framework-for-thoroughness.md](framework-for-thoroughness.md) | Rarely — only if Yield% calculation or evidence levels are unclear | SKILL.md contains what you need. Consult this only for edge cases or deeper understanding of the protocol. |
| [examples.md](examples.md) | Before your first review; when unsure if your approach is correct | Compare your process to GOOD example. Check if you're falling into BAD patterns. |
| [troubleshooting.md](troubleshooting.md) | When you hit a specific problem during review | Find your symptom in the list, apply recommended next steps. |
| [verification-checklist.md](verification-checklist.md) | At Exit Gate, before claiming done | Walk through each checkbox. More detailed than Exit Gate section. |
```

**2. Enhance key inline references:**

In DISCOVER section, change:
```markdown
Different skill types have different priority emphases — see [Skill Type Adaptation](skill-type-adaptation.md) for type-specific guidance.
```
To:
```markdown
Different skill types have different priority emphases. After listing initial dimensions, consult [Skill Type Adaptation](skill-type-adaptation.md): first identify the skill type using the Signals table, then apply the priority elevations and additional checks for that type.
```

In EXPLORE section, change:
```markdown
Check the dimension using guidance from [Dimension Definitions](dimension-definitions.md)
```
To:
```markdown
Check the dimension using [Dimension Definitions](dimension-definitions.md) — read the full section for that dimension, follow "How to check" as your process, use "Red flags" and "Good patterns" to calibrate, and confirm against "Pass criteria".
```

Similar enhancements for other key inline references.

## Trade-offs Accepted

1. **Some redundancy:** Reference section overview + inline details cover similar ground. Accepted for usability — overview for orientation, inline for action.

2. **Maintenance of two locations:** If guidance changes, both section and inline references may need updates. Mitigated by keeping section high-level (what/when) and inline contextual (how, in this specific context).

## What Would Change This

- If agents consistently skip the Reference Files section, consider removing it and relying solely on inline references
- If inline references become too verbose, trim them back to pointers and rely on the Reference Files section
- If supporting file structure changes significantly, revisit the "How to Use" guidance

## Iteration Log

| Pass | Framing | Frontrunner |
|------|---------|-------------|
| 1 | "Parallel dimension handling creates load" | Stakes-Aligned Phases |
| 2 | "Entry Gate ceremony is overhead" | Streamlined Entry + Lazy Tasks + Inline Checks |
| 3 | "Reference jumping is overhead" | Streamlined Entry + Lazy Tasks (dropped Inline Checks) |
| 4 | "Entry Gate and TaskCreates are structure, not burden" | Re-evaluated: these aren't problems |
| **5** | **"Supporting file references lack guidance"** | **Reference Section + Enhanced Inline** |

## Confidence

**High**

Based on:
- Problem correctly identified after multiple reframings
- Solution directly addresses the stated gap (what/when/how for each file)
- Implementation is straightforward (add section, enhance references)
- No risk to existing skill effectiveness

Uncertainty:
- Whether agents will actually read the Reference Files section (mitigated by inline references)
- Optimal verbosity of inline enhancements (can tune based on feedback)
