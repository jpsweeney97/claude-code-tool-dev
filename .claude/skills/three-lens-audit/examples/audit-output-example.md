# Worked Example: Auditing writing-for-claude v1.0.0

This example shows actual output from a three-lens audit of `skills/writing-for-claude/SKILL.md`.

---

## Target

The `writing-for-claude` skill (~150 lines) that defines:
- 18 evidence-based principles for writing Claude-facing artifacts
- When to use vs. when not to use
- Priority order when principles conflict
- Framework connection (Framework for Improvement)

---

## Agent Outputs

### Adversarial Auditor

| Vulnerability | Evidence | Attack Scenario | Severity |
|--------------|----------|-----------------|----------|
| Principles can justify contradictory edits | P2 "use tables" vs P7 "provide motivation" — priority order exists but is subjective | Reviewer claims any edit is "clearer" without objective measure; no way to validate compliance | Major |
| Token counts are vague | "~8,000 tokens" for references/principles.md | User assumes this fits in context; actual may vary by model/encoding; could exceed limit | Minor |
| External sources may change | Links to Anthropic docs (lines 151-155) | Documentation updates could invalidate principles; skill becomes stale without notice | Minor |
| "Claude 4.x" hardcoded | "Claude 4.x follows precise instructions" (line 58) | Future Claude versions may behave differently; advice becomes outdated | Minor |

**Meta-Critique:** The skill is more advisory than prescriptive. There's no enforcement mechanism — a user can claim they applied the principles without actually doing so. The "When Principles Conflict" section acknowledges this but doesn't resolve it.

---

### Pragmatic Practitioner

**What Works:**
- Quick Reference table is genuinely useful — I can glance at 18 principles in 30 seconds
- "When to Use" and "When NOT to Use" sections are clear and mutually exclusive
- Conflict priority order gives concrete guidance when stuck
- Links to sources let me verify if I'm skeptical

**What's Missing:**
- No before/after examples in SKILL.md itself (must read principles.md for those)
- No checklist format for validating edits ("did I apply P1-18?")
- No guidance on which principles matter most — are some 80/20?
- Limited Context Strategy is vague ("dispatch a subagent") — what prompt?

**Friction Points:**
- principles.md is 8K tokens — too big to read unless actively editing
- Principles numbered 1-18 but grouped by category — hard to find "principle 7" by scanning
- Artifact Types table doesn't say what "Both" means — both what?

**Verdict:** I'd use the Quick Reference as a checklist and skip the full principles.md unless debugging a specific issue. The skill is useful but top-heavy — most value is in the tables, most tokens are in the prose.

---

### Cost/Benefit Analyst

| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Quick Reference tables | Low | High | Worth it — scannable, actionable |
| 18 principles in references/principles.md | High (8K tokens) | Medium | Over-documented — same info in less space |
| "When to Use" section | Low | High | Worth it — prevents misapplication |
| Framework Connection section | Medium | Low | Academic — users won't read |
| External source links | Low | Medium | Worth it — builds trust |
| Conflict priority order | Low | High | Worth it — resolves real ambiguity |

**High-ROI Elements:**
- Quick Reference (lines 44-88) — maximum information density
- When to Use / When NOT to Use — prevents wrong-tool-for-job
- Priority order (lines 93-103) — actionable when stuck

**Low-ROI Elements:**
- Framework Connection — meta-documentation that users skip
- Limited Context Strategy — too vague to be useful
- Artifact Types table — obvious once you read When to Use

**Recommendations:**
1. Move best examples from principles.md into SKILL.md — reduce need to load 8K tokens
2. Cut Framework Connection or move to references/ — it's for skill authors, not users
3. Add concrete prompt for "Limited Context Strategy" — currently hand-wavy

---

## Synthesis

### Convergent Findings (All 3 Lenses)

| Finding | Adversarial | Pragmatic | Cost/Benefit |
|---------|-------------|-----------|--------------|
| principles.md is too heavy | Token count vague, may exceed context | 8K tokens too big unless actively editing | Over-documented, same info in less space |
| Limited Context Strategy is vague | No enforcement of "dispatch subagent" | "What prompt?" — not actionable | Too vague to be useful |

**Assessment:** The skill's reference document is its biggest liability — too long to load casually, but the skill depends on it for examples. This is the critical path for v1.1.0.

### Convergent Findings (2 Lenses)

| Finding | Lenses | Evidence |
|---------|--------|----------|
| No before/after examples in SKILL.md | Pragmatic, Cost/Benefit | "Must read principles.md for those" + "Move best examples into SKILL.md" |
| Framework Connection is low-value | Pragmatic (implicit), Cost/Benefit | "Academic — users won't read" |

### Lens-Specific Insights

**Adversarial Only:**
- External doc links may become stale — not caught by other lenses because it's a future risk, not current friction
- "Claude 4.x" hardcoding — version-specific advice ages poorly

**Pragmatic Only:**
- Artifact Types table says "Both" without explaining — minor UX issue
- Principles numbered 1-18 but grouped by category — finding-by-number is hard

**Cost/Benefit Only:**
- Framework Connection section is explicit low-ROI — other lenses implied this but didn't quantify

### Prioritized Recommendations

| Priority | Issue | Fix | Effort | Convergence |
|----------|-------|-----|--------|-------------|
| 1 | principles.md too heavy | Add 3-5 best examples directly to SKILL.md | Medium | All 3 |
| 2 | Limited Context Strategy vague | Add actual subagent prompt template | Low | All 3 |
| 3 | No checklist for validation | Add "Validation Checklist" section | Low | 2 lenses |
| 4 | "Both" unexplained in table | Add footnote or parenthetical | Low | 1 lens |
| 5 | External links may stale | Add "last verified" date | Low | 1 lens |

### Summary

**Overall assessment:** The skill is well-structured and genuinely useful, but front-loads too much into references/principles.md while leaving SKILL.md too abstract.

**Critical path:** Add inline examples and a concrete subagent prompt to make the skill self-sufficient without loading 8K tokens.

**Optional improvements:** Validation checklist, table footnotes, link freshness dates.

---

## Key Observations

1. **Convergent findings surface real issues** — All three lenses flagged principles.md size and Limited Context vagueness
2. **Each lens found unique value** — Adversarial caught version-specific advice; Pragmatic caught UX friction; Cost/Benefit quantified Framework Connection as low-ROI
3. **Severity ≠ Priority** — The "Claude 4.x hardcoding" is technically a risk but low priority because it's easy to update later
4. **Synthesis reveals actionable path** — Individual findings become "add examples + add prompt template" as concrete next steps
