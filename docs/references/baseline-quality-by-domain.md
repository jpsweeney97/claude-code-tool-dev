# Baseline Quality is Domain-Dependent

**Date:** 2026-02-09
**Source evidence:** Stress test results (100+ runs), skill impact measurement spec session (7 review findings), making-recommendations evaluation decision
**Key claim:** Claude's baseline competence varies by domain. Skills targeting quantitative/formal reasoning have the highest value and are easiest to validate. Skills targeting qualitative reasoning face ceiling effects.

---

## Evidence Chain

### 1. Stress Tests: "Baseline is Already Good"

Across 100+ runs (categories A1 through C3, plus Phase 1.2), the stress tests demonstrated consistent baseline competence:

- Vague terms ("several," "appropriate caveats") interpreted with near-zero variance (A1a, A1c)
- Evaluative terms ("optimize," "improve," "professional") have stable default interpretations (A1d-g)
- Compliance unaffected by domain, complexity, requirement count, instruction length, or density (B2, B3, C1-C3)
- Phase 1.2: boolean/structural proxies showed categorical shifts (scope section: 0%→100%), but count proxies like failure modes showed zero delta because baseline already produces them

Finding #27: *"Some proxies fail because baseline is already good."*

### 2. Domain Scope of the Stress Tests

Every stress test scenario was qualitative or structural:

| Category | Example Tasks |
|----------|---------------|
| A1 (vague terms) | "Explain how promises work," "Should we use MongoDB?" |
| A1d-g (evaluative) | "Make this code better," "Make this more professional" |
| A2 (conflicts) | "Explain microservices trade-offs," "What database?" |
| B (scenario variance) | "REST API error handling best practices" |
| C (skill structure) | "Explain Python GIL," "Kubernetes advantages" |
| Phase 1.2 | "Write a SKILL.md for commit-message-guide" |

These are tasks where Claude excels by default: explaining concepts, making recommendations, writing structured documents, formatting code. The "baseline is already good" conclusion was established entirely within Claude's strongest domains.

### 3. Quantitative Reasoning Gaps (Spec Session Evidence)

While writing the skill impact measurement spec, Claude produced 7 errors that survived into the initial draft:

| # | Error | Category |
|---|-------|----------|
| 1 | Mixed one-tailed/two-tailed p-values across sections | Internal consistency |
| 2 | Win rate threshold (>70%) and sign test (p<0.05) disagreed at 11/15 | Threshold misalignment |
| 3 | No handling for tied tasks in sign test | Missing edge case |
| 4 | Promised "win rate with confidence interval" but never specified CI method | Unspecified claim |
| 5 | Tier-3 had only 2 tasks making quantitative thresholds meaningless | Underpowered subsample |
| 6 | Only 1-2 tasks for sensitivity/contamination controls | Fragile controls |
| 7 | Same scorer sees which output is baseline vs treatment | Confirmation bias in design |

5 of 7 are internal consistency and completeness errors — tracking multiple numerical claims across a long document and keeping them coherent. 2 of 7 require experimental design expertise.

---

## The Reframe

The stress tests' most-repeated finding — *"baseline is already comprehensive"* — needs a scope qualifier: it holds for qualitative and structural tasks, but should not be generalized uncritically.

| Domain | Baseline Quality | Ceiling Effect Risk | Skill Value Potential |
|---|---|---|---|
| **Qualitative** (writing, explaining, recommending) | High | High — stress tests confirmed | Low — skill must find narrow gaps |
| **Structural** (formatting, section presence, compliance) | High | High — stress tests confirmed | Low to moderate |
| **Quantitative/formal** (statistics, consistency, experimental design) | Moderate — spec session demonstrated gaps | Low | High — real headroom exists |

---

## Three Consequences

### A. Discriminability is Easier for Quantitative Skills

The measurement spec's discriminability verification (§3.1) asks: "Would baseline Claude satisfy this criterion without the skill?" For qualitative criteria (well-organized, comprehensive, clear), the answer is usually "yes" — ceiling effect. For quantitative criteria (internally consistent p-values, correct CI computation, properly powered sample sizes), the answer is more often "no." Fewer wasted runs, stronger signal, less rubric gymnastics.

### B. Stress Test Results Need a Scope Qualifier

"Baseline is already comprehensive" should read: *"Baseline is already comprehensive for qualitative and structural tasks."* Without the qualifier, the finding is over-generalized and could lead to the conclusion that skills are low-value across the board.

### C. Highest-Value Skills Target Formal/Quantitative Gaps

Skills like "quantitative spec review" or "experimental design review" operate where Claude has real deficits. They are both the most *useful* (genuine headroom) and the easiest to *validate* (baseline more often fails criteria, producing stronger signal).

---

## Skill Value Priority Ordering

1. **Highest value, easiest to validate:** Skills targeting quantitative/formal reasoning (internal consistency, statistical correctness, experimental design)
2. **Moderate value, moderate validation difficulty:** Skills targeting structural compliance where baseline doesn't naturally produce required artifacts (like writing-principles' scope sections)
3. **Lowest value, hardest to validate:** Skills targeting qualitative improvement where baseline is already strong (like making better recommendations)

---

## Implications for `making-recommendations`

The `making-recommendations` skill is a process-shaping skill in the qualitative domain — exactly where baseline is strongest. Its evaluation decision (`docs/decisions/2026-02-09-evaluate-making-recommendations-skill.md`) already internalizes this:

- Chose Tier A artifact compliance + field usefulness loop, not outcome-quality measurement
- Explicitly avoids claiming "better decisions" without Tier B evidence
- Validates on structural/behavioral markers (Decision Record exists? Null option present? Iteration log non-empty?) — boolean proxies that Phase 1.2 showed produce categorical shifts

As a **first pilot** for the measurement spec, `making-recommendations` is a harder target than a quantitative skill would be. A quantitative skill provides a cleaner test of the methodology because baseline has real gaps — if the methodology shows "no effect," it's informative (methodology is broken). If it shows "clearly helps," the methodology is validated and can be applied to harder qualitative targets with confidence in the instrument.

---

## Source Documents

| Document | Role |
|----------|------|
| `docs/plans/2026-02-05-architecture-stress-test-results.md` | Empirical evidence for qualitative/structural baseline quality |
| `docs/plans/2026-02-09-skill-impact-measurement-spec.md` | Both the methodology and the evidence (7 review findings) |
| `docs/decisions/2026-02-09-evaluate-making-recommendations-skill.md` | Evaluation approach that internalizes domain-dependent baseline |
| `~/.claude/handoffs/claude-code-tool-dev/2026-02-09_20-00_skill-impact-measurement-spec.md` | Session handoff where the learning was first articulated |
