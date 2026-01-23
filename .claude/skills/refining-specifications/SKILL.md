---
name: refining-specifications
description: Use when reviewing or improving specification documents (frameworks, API specs, rules, process definitions). Use proactively after authoring or significantly modifying a spec. Use when asked to "review," "refine," or "improve" a spec.
---

# Refining Specifications

## Overview

Specification documents often ship unclear: first drafts lack precision, implicit knowledge stays in the author's head, and reviews become "LGTM" theater. This skill applies seven refinement lenses systematically until no new issues emerge.

**Core insight:** Different lenses catch different problems. A single read-through favors high-salience issues (undefined terms) and misses low-salience ones (distant inconsistencies). Sequential passes with dedicated focus surface what parallel scanning misses.

**Outputs:**
- Issues report organized by lens
- Refined document with fixes applied
- Summary of changes made

## When to Use

- After authoring a specification, framework, or process document
- After significant modifications to an existing spec
- When asked to "review," "refine," or "improve" a spec document
- Before publishing or promoting a spec to production use
- When a spec feels unclear but you can't pinpoint why

## When NOT to Use

- **Code** — this is for prose specifications, not source code
- **External documents** — specs you can't edit (third-party standards, vendor docs)
- **Ephemeral content** — chat messages, temporary notes, one-off explanations
- **Gap analysis situations** — when comparing a spec against source materials (use gap-analysis skill)
- **Pre-implementation validation** — when checking if a design is ready to build (use validating-designs skill)

## The Seven Lenses

Each lens targets a specific clarity dimension. Apply sequentially, one pass per lens.

| # | Lens | Question | Catches |
|---|------|----------|---------|
| 1 | **Implicit concepts** | Are all terms defined? | Undefined jargon, assumed knowledge |
| 2 | **Weak spots** | Is language precise? | Vague wording, loopholes, wiggle room |
| 3 | **Missing examples** | Is abstract guidance illustrated? | Theory without concrete application |
| 4 | **Internal consistency** | Do parts agree? | Contradictions between sections |
| 5 | **Overlap/redundancy** | Is anything said twice differently? | Duplication that may drift |
| 6 | **Testability** | Can compliance be verified? | Unverifiable requirements |
| 7 | **Actionability** | Is it clear what to do? | Ambiguous instructions |

**Why this order:** Lenses 1-3 are "surface" issues (visible in a single section). Lenses 4-5 require cross-document comparison. Lenses 6-7 require stepping back to assess the whole.

## Process

### 1. Announce and Scope

Before starting:
- Identify the document to refine
- Confirm it's a specification (not code, not external, not ephemeral)
- State: "Refining [document name] using the 7-lens protocol"

### 2. Execute Lens Passes

For each lens (1 through 7):

1. **State the lens:** "Pass N: [Lens name] — [Question]"
2. **Read the document** with that lens active
3. **Record issues** found (with line references where possible)
4. **Note if clean:** "No issues found for this lens"

Keep a running tally:
```
Pass 1 (Implicit concepts): 2 issues
Pass 2 (Weak spots): 3 issues
Pass 3 (Missing examples): 1 issue
...
```

### 3. Report Findings

After all 7 passes, present findings organized by lens:

```markdown
## Refinement Report: [Document]

### Issues Found

**Lens 1 — Implicit concepts (2 issues):**
- Line 45: "pass" used but not defined
- Line 112: "convergence" assumes reader knows the term

**Lens 2 — Weak spots (3 issues):**
- Line 78: "should generally" is vague — when specifically?
...

### Summary
- Total issues: N
- By severity: X critical, Y moderate, Z minor
```

### 4. Apply Fixes

For each issue:
1. Make the edit
2. Note what changed

### 5. Check Convergence

After fixing, run another 7-lens pass. Convergence is reached when:
- A pass surfaces only issues already found (repetition), OR
- Two consecutive passes find nothing new (stability)

If new issues emerge, return to step 4.

## Anti-Patterns

| Pattern | Why It Fails | Fix |
|---------|--------------|-----|
| **"Document is already good"** | Rationalizes skipping refinement entirely | Every document benefits from systematic review. Run the lenses. |
| **"Just a minor update"** | Exempts small changes that compound | Minor changes can introduce inconsistencies. At minimum, run lenses 4-5 (consistency, overlap). |
| **Surface-level passes** | Checkbox compliance without genuine examination | Each pass must produce either issues or an explicit "No issues found" with evidence of examination. |
| **Conflating with other skills** | Using gap-analysis or validating-designs when refinement is needed | Gap-analysis compares documents; validating-designs checks implementation-readiness. Refinement improves a single document's clarity. |
| **Stopping after one clean pass** | One pass might miss issues; doesn't confirm stability | Convergence requires repetition signal OR two consecutive clean passes. |
| **Fixing without reporting** | Jumps to edits, skips the diagnostic phase | Report first, then fix. The report creates accountability and teaches the pattern. |

## Examples

### BAD: Ad-hoc review

```
User: Review the verification framework

Claude: I've read through the framework. It looks comprehensive and well-structured.
The four stages (DEFINE/DESIGN/EXECUTE/EVALUATE) are clear, and the failure modes
section is helpful. A few minor suggestions:
- Consider adding more examples
- The probabilistic section could be expanded

Overall it's ready to use.
```

**Why it's bad:**
- No systematic lens application
- Vague findings ("looks comprehensive")
- No evidence of thorough examination
- "Consider adding" without specifics
- Declared done without convergence check

### GOOD: Lens-based refinement

```
User: Review the verification framework

Claude: Refining verification.framework using the 7-lens protocol.

**Pass 1 — Implicit concepts:**
- Line 147: "pass" used in iteration cap but not defined
- Line 181: Oracle Types vs Methods distinction unclear

**Pass 2 — Weak spots:**
- Line 43: "Timestamp verdicts" is SHOULD, but staleness is a failure mode
- Line 354: Dimension mixing exception allows downgrades (loophole)

**Pass 3 — Missing examples:**
- Line 49: DEFINE+DESIGN collapse mentioned but no example given
- Line 211: Time-shift verification unexplained

**Pass 4 — Internal consistency:**
- Line 43 vs Line 388: Timestamp recommendation contradicts staleness countermeasure

**Pass 5 — Overlap/redundancy:**
- Oracle Types (line 169) and Methods (line 193) have overlapping entries

**Pass 6 — Testability:**
- No issues found

**Pass 7 — Actionability:**
- No issues found

## Summary
- 7 issues across 5 lenses
- 2 lenses clean

Proceeding to fixes...

[Makes targeted edits]

Running convergence check... Pass 2 surfaces no new issues. Refinement complete.
```

**Why it's good:**
- Systematic lens application with explicit passes
- Specific issues with line references
- Clean lenses explicitly noted
- Fixes applied after diagnosis
- Convergence verified

## Decision Points

**Document type unclear:**
- If it defines expected behavior (process, contract, interface, rules) → use this skill
- If it's narrative prose (blog post, explanation, tutorial) → use writing-clearly-and-concisely
- If comparing against sources → use gap-analysis

**Many issues found:**
- More than 10 issues suggests structural problems, not just clarity issues
- Consider: Is this spec ready for refinement, or does it need rewriting?
- If rewriting needed → stop refinement, flag to user

**Lens finds nothing:**
- Explicit "No issues found" is valid — document that lens was applied
- If multiple consecutive lenses find nothing, continue anyway (later lenses may catch issues)

**Disagreement on whether something is an issue:**
- If genuinely ambiguous → note it as "Potential issue (ambiguous)" and let user decide
- Don't silently skip uncertain findings

**Time pressure:**
- If user needs quick feedback → run lenses 1-3 only (surface issues), note that lenses 4-7 were skipped
- Never skip the report phase — compressed is fine, absent is not

## Troubleshooting

**Symptom:** Refinement feels endless (many passes, still finding issues)
**Cause:** Document has fundamental clarity problems, not surface issues
**Fix:** Stop after 3 full cycles. Report: "Document may need restructuring rather than refinement. Found [N] issues across [M] passes. Recommend addressing root causes."

**Symptom:** All lenses return "no issues" on first pass
**Cause:** Either document is genuinely clean, or passes were too shallow
**Fix:** For the first occurrence, trust the result but run a second full pass to confirm stability. If second pass also clean → done. If doubt remains, apply lens 2 (weak spots) more aggressively.

**Symptom:** User pushes back on reported issues
**Cause:** Issue may be intentional, or context was missing
**Fix:** Don't defend — explore. "Is this intentional? If so, I'll mark it as accepted." Update report to distinguish issues from accepted deviations.

**Symptom:** Fixes introduce new issues
**Cause:** Edits created new inconsistencies or unclear language
**Fix:** This is why convergence requires a post-fix pass. The loop is working correctly. Continue until stable.
