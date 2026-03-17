---
job: Critically analyze the Engram design document and surface specific weaknesses, gaps, risks, and improvement opportunities with actionable recommendations
created: 2026-03-16
---

Read the file at `docs/superpowers/specs/2026-03-16-engram-design.md` in full before producing any output.

Analyze the Engram design across five dimensions. For each dimension, examine how decisions in different sections interact — do not walk the document linearly.

## Dimensions

### 1. Invariant integrity
Examine every stated invariant, contract, and "hard rule" in the document. For each: is there a mechanism that enforces it, or is it aspirational? Identify invariants that could be violated by the design's own features.

### 2. Interface seams
Where subsystems, engines, readers, and skills connect: are the contracts complete? Look for implicit assumptions about ordering, availability, format, or state that aren't captured in types or protocols.

### 3. Migration risk
Evaluate the build sequence (Steps 0–5). What ordering dependencies exist that aren't stated? What happens if a step partially succeeds? Where does the rollback strategy rely on assumptions about git state?

### 4. Absence analysis
What does the design need to address that it currently doesn't? Focus on operational scenarios: what happens during concurrent worktree sessions, plugin upgrades mid-session, partial filesystem failures, or first-time setup?

### 5. Internal contradictions
Find places where the document says one thing in one section and contradicts or undermines it in another. Include cases where a deferred decision conflicts with a current design choice.

## Output format

For each finding, use this structure:

```
### [D#] Finding title
**Dimension:** (which of the 5)
**Location:** (specific section numbers and/or line references)
**Problem:** What is wrong or missing, and what evidence in the document supports this diagnosis.
**Impact:** What goes wrong if this isn't addressed — be specific about the failure scenario.
**Recommendation:** What to change, add, or clarify. If multiple options exist, state trade-offs.
```

Number findings sequentially (D1, D2, D3...). Do not group by dimension — interleave freely based on severity.

After all findings, add:

```
## Summary
- Total findings: N
- By dimension: (count per dimension)
- Top 3 by impact: (finding numbers)
```

## Ground rules

- Do not change the fundamental goal of the design.
- Do not praise the design. Every item in your output must identify a specific problem.
- Every finding must cite a specific section, decision, type, flow, or mechanism from the document. If a finding could apply to "any design doc," cut it.
- State the problem before recommending a solution. If you aren't sure what the right fix is, say what additional information would resolve it.
- Do not invent requirements the document didn't set for itself. Evaluate against its own stated goals, invariants, and success criteria.
- If a concern is already addressed by the document's own "Risks" or "Deferred decisions" sections, do not re-raise it unless the mitigation is insufficient. State why the mitigation falls short.
- Aim for 8–15 findings. Fewer than 8 suggests you skipped a dimension. More than 15 suggests you're padding with low-impact observations.
