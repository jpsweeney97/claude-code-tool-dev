# Type Example: Quality Enhancement Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Quality Enhancement.

## Core Question

**Is output measurably better?**

Quality Enhancement skills make output "better" along defined dimensions. The failure mode is vague improvement claims without measurable criteria.

## Type Indicators

Your skill is Quality Enhancement if it:
- Says "better", "clearer", "improved", "more readable"
- Defines what good output looks like
- Transforms existing content rather than creating new things
- Has implicit quality criteria that could be made explicit

## The Quality Trap

**"Better" means nothing without criteria.** Before writing a Quality Enhancement skill, you must define:
- What dimensions of quality matter (clarity, completeness, accuracy, etc.)
- What "good" looks like for each dimension
- What "bad" looks like for each dimension

If you can't specify these, the skill can't be tested and might not actually improve anything.

## Section Guidance

### Process Section

**Use criteria/framework.** Instead of numbered steps, define the quality dimensions and how to apply them.

**Example (clearer explanations):**

```markdown
## Process

Apply these quality criteria to explanations:

**1. Punchline First**
- Lead with the answer, then explain
- Bad: "Due to various factors including X, Y, Z, the result is..."
- Good: "The result is [answer]. Here's why..."

**2. Concrete Examples**
- Abstract concepts need concrete illustrations
- One specific example beats three abstract restatements

**3. Jargon Handling**
- Define technical terms on first use, or avoid them
- If the audience knows the term, use it; if not, explain it

**4. Scannable Structure**
- Headers, bullets, and whitespace for navigation
- A reader should grasp the structure before reading details
```

**Anti-pattern:** Generic "make it better" without specific criteria.

### Decision Points Section

Focus on **quality tradeoffs and prioritization**:
- What if criteria conflict?
- Which dimensions matter most?
- When is "good enough" acceptable?

**Example:**

```markdown
## Decision Points

**Criteria conflict:**
- If brevity conflicts with completeness → Prioritize completeness for technical audiences, brevity for general audiences
- If clarity conflicts with precision → Lead with the clear version, add precision in a follow-up

**Diminishing returns:**
- If iteration N is marginally better than N-1 → Stop. Perfectionism delays delivery.
- If user says "that's fine" → Accept it. Don't optimize past their needs.

**Context matters:**
- For documentation → Prioritize completeness and scanability
- For chat responses → Prioritize brevity and punchline-first
- For teaching → Prioritize examples and progressive disclosure
```

### Examples Section

Show **rubric-based improvement**:
- Before: Output with identified quality gaps
- After: Output with those gaps addressed
- Explain which criteria improved

**Example:**

```markdown
## Examples

**Scenario:** Explain what a database index does.

**Before** (without skill):
"A database index is a data structure that improves the speed of data retrieval operations on a database table at the cost of additional writes and storage space to maintain the index data structure. Indexes are used to quickly locate data without having to search every row in a database table every time a database table is accessed."

Quality gaps:
- No punchline (buries the answer)
- No concrete example
- Dense paragraph (not scannable)

**After** (with skill):
"**What it does:** Lets the database find rows without scanning the whole table — like a book's index vs. reading every page.

**Example:** Finding user #12345 in a million-row table:
- Without index: Check all 1M rows (slow)
- With index: Jump directly to the row (fast)

**Tradeoff:** Indexes speed up reads but slow down writes (the index must be updated too)."

Quality improvements:
- Punchline first ✓ (opens with "what it does")
- Concrete example ✓ (book index, user lookup)
- Scannable ✓ (headers, bullets)
```

### Anti-Patterns Section

Focus on **false quality and over-optimization**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Claiming improvement without citing criteria
**Why it fails:** "I made it clearer" is not verifiable. Did punchline-first improve? Did examples get added? Without specifics, you might have made it worse.
**Fix:** Always cite which quality dimension changed and how.

**Pattern:** Optimizing dimensions the user doesn't care about
**Why it fails:** Perfect scanability doesn't help if the user needed more depth. Quality is relative to purpose.
**Fix:** Ask about context or infer from usage. Match dimensions to needs.

**Pattern:** Endless iteration seeking perfection
**Why it fails:** Version 5 might be 2% better than version 4, but took 20% more time. User wanted "good" not "perfect."
**Fix:** Set a quality threshold. When met, stop. Offer to continue only if user wants more.
```

### Troubleshooting Section

Address **quality assessment failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude says "improved" but output seems the same
**Cause:** Improvement was claimed without specific criteria application
**Next steps:** Ask Claude to identify which quality dimensions changed and show before/after for each.

**Symptom:** User says the "improved" version is worse
**Cause:** Optimized for wrong dimensions (e.g., added structure when user wanted brevity)
**Next steps:** Ask user which quality dimensions matter. Re-optimize for those.

**Symptom:** Quality improvements are inconsistent across similar tasks
**Cause:** Criteria being applied ad-hoc rather than systematically
**Next steps:** Document the criteria explicitly. Apply the same checklist each time.
```

## Testing This Type

Quality Enhancement skills need **rubric comparison** and **adversarial challenge**:

1. **Rubric test:** Score Before and After against each quality dimension
2. **Blind preference test:** Show both versions to an evaluator without labels — which do they prefer?
3. **Adversarial test:** Can a challenger produce a clearly better version Claude missed?

See `type-specific-testing.md` → Type 2: Quality Enhancement Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Criteria not defined | Can't verify improvement | List specific quality dimensions before writing skill |
| "Better" without evidence | Unverifiable claims | Always cite which criterion changed and how |
| One-size-fits-all quality | Context ignored | Add Decision Points for different contexts/audiences |
| No Before/After examples | Can't see the improvement | Show concrete text with quality gaps → same text improved |
