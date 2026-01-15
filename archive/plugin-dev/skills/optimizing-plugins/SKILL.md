---
name: optimizing-plugins
description: "Systematic plugin improvement from 'good' to 'great' using 6 scored lenses, 11 thinking models, and multi-agent validation. Use after audit passes, when plugin works but feels rough, triggers aren't firing reliably, skills overlap confusingly, or when asked to optimize plugin, improve plugin quality, refine descriptions."
license: MIT
metadata:
  version: 2.0.0
  model: claude-opus-4-5-20251101
  domains: [plugin-development, optimization, quality]
  type: process
---

# Plugin Optimizer v2.0

Systematic plugin improvement through scored analysis, thinking models, and validation.

**Announce at start:** "I'm using the optimizing-plugins skill to systematically improve this plugin."

## Overview

The optimizer examines plugins through six scored lenses, producing a prioritized design document. It guides improvement from "good" to "great" — distinct from audit, which fixes broken plugins.

| Aspect | Audit | Optimizer |
|--------|-------|-----------|
| Purpose | Find problems | Improve quality |
| Input | Potentially broken plugin | Working plugin |
| Output | Issue list + fixes | Scored design document |
| Goal | "Broken → working" | "Good → great" |

## Triggers

- `optimize plugin` - After audit passes, improve quality
- `improve plugin quality` - Refine descriptions and structure
- `plugin feels rough` - Works but needs polish
- `triggers aren't firing` - Skills not activating reliably
- `skills overlap confusingly` - Unclear boundaries between skills
- `score my plugin` - Get baseline quality measurement

## Prerequisites

| Prerequisite | Source |
|--------------|--------|
| Working plugin (all components implemented) | implementing-{component} skills |
| Plugin passes basic functionality tests | Component-level testing |
| Audit passed (recommended) | plugin-audit |

**Single component?** This skill works for single-skill plugins too.
The 6 lenses still apply.

**Skipping straight here?** If you have a working plugin but skipped
earlier stages, that's fine. Optimization identifies issues regardless
of how the plugin was built.

## Pipeline Context

This skill is **Stage 4: Optimize** in the plugin development pipeline.

See: `brainstorming-plugins` for full pipeline overview.

| Aspect | Value |
|--------|-------|
| This stage | Polish plugin from "good" to "great" |
| Prerequisite | `/implementing-{component}` (working plugin) |
| Hands off to | `/deploying-plugins` or back to implementing |

## Quick Start

```bash
# Score a plugin
python scripts/rapid_score.py /path/to/plugin

# Validate a design document
python scripts/validate_design.py docs/plans/optimization.md

# Track implementation progress
python scripts/progress_tracker.py status
```

---

## The Process

### Phase 1: Orientation

Scan the plugin and deliver scored assessment:

1. **Prerequisite check:** Was audit run recently? If not, suggest running audit first (soft warning, proceed anyway).

2. **Rapid scoring:** Run scoring script or apply rubrics manually:
   ```bash
   python scripts/rapid_score.py <plugin-path>
   ```

3. **Present score summary:**
   ```
   | Lens               | Score | Status |
   |--------------------|-------|--------|
   | Trigger Fidelity   | 5.5   | ✗ Below threshold |
   | Token Economy      | 7.2   | ✓ Passing |
   | ...                | ...   | ... |
   | **Overall**        | 6.2   | NEEDS WORK |
   ```

4. **Focus recommendation:** Based on scores, recommend where to focus:
   - All passing: "Focus on polish and edge cases"
   - 1-2 below: "Recommend Deep on [lenses]"
   - 3+ below: "Priority: [top 2 by lens priority]"

5. **One-paragraph assessment:** Overall health, strengths, opportunities.

### Phase 2: Guided Tour

Walk through 6 lenses in fixed order:

| # | Lens | Core Question | Priority |
|---|------|---------------|----------|
| 1 | Trigger Fidelity | Will Claude invoke at the right moment? | 2 |
| 2 | Token Economy | Does every token earn its keep? | 6 |
| 3 | Structural Clarity | Can Claude navigate efficiently? | 5 |
| 4 | Degrees of Freedom | Does specificity match fragility? | 3 |
| 5 | Resilience | What happens when things go wrong? | 1 |
| 6 | Plugin Coherence | Does this work as a unified whole? | 4 |

See [references/lenses.md](references/lenses.md) for scoring rubrics.

**At each lens:**

1. Present score: "Resilience: 4.5/10 (threshold: 7)"
2. If score < 7: "This lens needs attention"
3. Analyze against lens criteria
4. Apply relevant thinking models (see [references/thinking-models.md](references/thinking-models.md))
5. Present findings summary
6. User chooses depth: **Skip**, **Skim**, or **Deep**

**For passing lenses (≥7):** Auto-advance with brief acknowledgment unless user requests Deep.

### Phase 3: Synthesis

After all lenses:

1. **Conflict resolution:** Check for conflicting suggestions. Apply priority hierarchy (see [references/conflict-resolution.md](references/conflict-resolution.md)).

2. **Temporal projection:** Evaluate significant suggestions across time horizons (see [references/temporal-projection.md](references/temporal-projection.md)).

3. **Cross-cutting patterns:** Identify:
   - Interactions between suggestions
   - Opportunities to consolidate changes
   - Dependencies affecting implementation order

### Phase 3.5: Validation Panel

Before finalizing, run 3 validation agents:

| Agent | Focus | Key Question |
|-------|-------|--------------|
| Completeness | Coverage | Did we address all significant issues? |
| Coherence | Unity | Do suggestions work as a whole? |
| Timelessness | Evolution | Will this design age well? |

**Consensus required:** All 3 agents must approve.

If rejected: Return to affected phase with feedback, iterate.

### Phase 4: Document & Handoff

1. Write design document using template (see [assets/templates/design-document.md](assets/templates/design-document.md))
2. Include embedded JSON for automation
3. Validate document: `python scripts/validate_design.py <doc>`
4. Ask: "Ready to set up for implementation?"
5. If yes: Initialize tracking → worktrees → writing-plans → execute

---

## Interaction Modes

### Skip
User determines no action needed. Move to next lens.

### Skim
Present all suggestions at once:
```
1. [Quick Win] Improve trigger phrase specificity
2. [High Value] Add error recovery examples
3. [Consider] Restructure for token efficiency
```
"Questions before moving on?" Suggestions go to design as-is.

### Deep

1. Ask: "Go deep on all N suggestions, or focus on high-impact ones?"
2. For each selected suggestion:
   - Issue description with score impact
   - Before/after examples
   - Thinking model insights (see [references/thinking-models.md](references/thinking-models.md))
   - Expert perspectives (see [references/expert-perspectives.md](references/expert-perspectives.md))
   - Cross-cutting connections
3. User refines, challenges, or accepts
4. Refined suggestions go to design

---

## Priority Model

| Priority | Criteria | Action |
|----------|----------|--------|
| **Quick Win** | Low effort, any impact | Do first |
| **High Value** | High impact, any effort | Worth investment |
| **Consider** | Low impact, high effort | May not justify |

---

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `rapid_score.py` | Score plugin against 6 lenses | `python scripts/rapid_score.py <path>` |
| `validate_design.py` | Check design document | `python scripts/validate_design.py <doc>` |
| `progress_tracker.py` | Track implementation | `python scripts/progress_tracker.py <cmd>` |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Invalid arguments |
| 10 | Validation/scoring failure |

---

## Design Document Structure

Write to `docs/plans/YYYY-MM-DD-<plugin>-optimization.md`:

```markdown
# Plugin Optimization: <plugin-name>

<!-- OPTIMIZATION_DATA
{"plugin": "...", "scores": {...}, "suggestions": [...]}
-->

## Summary
## Score Summary (before/after table)
## Quick Wins
## High Value
## Consider
## Cross-Cutting Notes
## Resolved Conflicts
## Temporal Analysis
## Validation Panel Results
## Next Steps
```

---

## Handoff

"Plugin optimized. What's next?"

| Situation | Next Step |
|-----------|-----------|
| Ready to publish | → `/deploying-plugins` |
| Need to implement optimization suggestions | → `/implementing-{component}` for changes |
| Discovered design issues | → `/brainstorming-{component}` to redesign |
| Personal use, no distribution | Done |

## After Optimization

**If implementing suggestions:**
- Use `/implementing-skills`, `/implementing-hooks`, etc. for changes
- Re-run optimization after significant changes

**If publishing:**
- Use `/deploying-plugins` for marketplace packaging
- Optimization design document serves as quality evidence

**Documentation:**
- Write design to `docs/plans/YYYY-MM-DD-<plugin>-optimization.md`
- Validate: `python scripts/validate_design.py <doc>`
- Commit the design document

**Implementation tracking:**
- Initialize tracking: `python scripts/progress_tracker.py init <doc>`
- Use superpowers:using-git-worktrees for isolated workspace
- Use superpowers:writing-plans for implementation plan
- Mark complete: `python scripts/progress_tracker.py complete S1`

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Skipping orientation | Loses shared context | Always deliver scores first |
| Deep-diving every lens | User fatigue | Let user choose depth |
| Mixing analysis with implementation | Scope creep | Complete design before code |
| Ignoring validation panel | Miss blind spots | Run all 3 agents |
| Treating all suggestions equally | Wastes effort | Use priority model |
| Ignoring conflicts | Inconsistent design | Apply priority hierarchy |

---

## Verification

After optimization session:

- [ ] Orientation delivered with scores
- [ ] All 6 lenses examined (skip/skim/deep)
- [ ] Conflicts resolved with priority hierarchy
- [ ] Temporal projection on significant suggestions
- [ ] Validation panel approved (3/3)
- [ ] Design document written and validated
- [ ] Suggestions categorized by priority
- [ ] User confirmed next steps

---

## Extension Points

1. **Custom lenses:** Add domain-specific lenses
2. **Additional experts:** Extend expert-perspectives.md
3. **New thinking models:** Add to thinking-models.md
4. **Script patterns:** Extend for new automation
5. **Validation agents:** Add specialized domain agents

---

## References

**Pipeline skills:**
- deploying-plugins — Next stage (marketplace packaging)
- implementing-skills — For implementing optimization suggestions
- brainstorming-skills — If redesign needed

**Optimization methodology:**
- [Lenses & Scoring](references/lenses.md) - Detailed criteria and rubrics
- [Thinking Models](references/thinking-models.md) - 11 analytical models
- [Expert Perspectives](references/expert-perspectives.md) - Simulated expert views
- [Conflict Resolution](references/conflict-resolution.md) - Priority hierarchy
- [Temporal Projection](references/temporal-projection.md) - Future-proofing

---

## Key Principles

- **Scored analysis** — Quantifiable improvement, not just prose
- **Fixed lens order** — Predictable, learnable flow
- **User controls depth** — Skip/Skim/Deep per lens
- **Priority hierarchy** — Resolve conflicts systematically
- **Validation required** — 3 agents must approve
- **Structured output** — Machine-parseable for automation
- **Separate analysis from implementation** — Design document first
