---
name: exploring-codebases
description: Use when asked to "explore this codebase thoroughly", "understand this codebase", or when needing comprehensive architectural understanding of an unfamiliar codebase.
---

# Exploring Codebases

Systematic, thorough exploration of unfamiliar codebases using the Framework for Thoroughness.

## Overview

This skill applies `thoroughness.framework@1.0.0` to codebase exploration, producing:

- Comprehensive architectural understanding
- Actionable orientation for contribution
- Documented findings in Thoroughness Report format

**The loop:** DISCOVER (what to look for) → EXPLORE (cover each dimension) → VERIFY (check findings) → REFINE (loop or exit based on Yield%)

**Default thoroughness:** Rigorous (Yield <10%, E2 evidence for P0 dimensions)

**Protocol:** [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md)

## Triggers

- "Explore this codebase thoroughly"
- "Thoroughly explore this codebase"
- "Help me understand this codebase"
- "Give me an architectural overview"

## When to Use

**Use when:**

- Starting work on an unfamiliar codebase
- Onboarding to a new project or inherited code
- Need comprehensive understanding before contributing
- Want documented findings to reference later or share

**Don't use when:**

- Quick answer to a specific question → use targeted search instead

## Outputs

**Artifacts:**

- **Documented findings:** Thoroughness Report at `docs/exploration-findings/YYYY-MM-DD-<codebase-name>-exploration.md`

**Report follows framework template:**

- Context (protocol, scope, constraints)
- Entry Gate (assumptions, thoroughness level, stopping criteria, seed dimensions)
- Coverage Tracker (items with Cell Schema: ID, Status, Priority, Evidence, Confidence)
- Iteration Log (table with New/Total/Yield%/Decision per pass)
- Findings (with Evidence + Confidence levels)
- Disconfirmation Attempts
- Decidable vs Undecidable
- Exit Gate verification

**The report serves as:**

- Reference for future work in the codebase
- Shareable onboarding document for others
- Audit trail of exploration methodology

**Definition of Done:**

- Entry Gate completed (assumptions surfaced, thoroughness level set)
- All P0/P1 dimensions explored with required evidence level
- Yield% below threshold for chosen thoroughness level
- Exit Gate criteria satisfied
- Report written and committed

## Process

The skill follows `thoroughness.framework@1.0.0`. This section summarizes; see [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md) for full protocol.

### Entry Gate

Before exploring, establish:

| Aspect             | Question                                          | Default                                                |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------ |
| Assumptions        | What am I taking for granted about this codebase? | List explicitly                                        |
| Thoroughness       | How thorough?                                     | Rigorous                                               |
| Stopping criteria  | When is "enough"?                                 | Discovery-based (two loops with no new P0/P1 findings) |
| Seed dimensions    | What aspects to explore?                          | See Seed Dimensions below                              |
| Coverage structure | How to track?                                     | Hybrid (skill decides based on codebase)               |

### Seed Dimensions

Start with these; DISCOVER phase will expand:

| Dimension        | What to Look For                                  | Priority |
| ---------------- | ------------------------------------------------- | -------- |
| Structure        | Directory layout, module boundaries, entry points | P0       |
| Data flow        | How data moves through the system                 | P0       |
| Dependencies     | External libraries, internal coupling             | P0       |
| Patterns         | Design patterns, conventions, idioms              | P1       |
| Error handling   | How failures are managed                          | P1       |
| Configuration    | How behavior is customized                        | P1       |
| Extension points | Where/how the system is meant to be extended      | P1       |
| Testing          | Test organization, patterns, coverage approach    | P1       |

### The Loop

```
DISCOVER → EXPLORE → VERIFY → REFINE → (loop or exit)
```

**DISCOVER:** Apply ≥3 techniques to find dimensions beyond the seed list:

- Pre-mortem: "This exploration would be worthless if..."
- Perspective multiplication: What would a security reviewer notice? A performance engineer?
- Boundary perturbation: What happens at 10x scale? With zero data?

**EXPLORE:** For each dimension, gather evidence:

- E1: Single method (read file)
- E2: Two independent methods (read + grep confirmed)
- E3: Triangulated + disconfirmation attempted

**VERIFY:** Cross-reference findings, attempt disconfirmation, check assumptions.

**REFINE:** Compute Yield%. If below threshold and no new dimensions, exit. Otherwise loop.

### Iteration Log Format

Each pass MUST include an explicit Iteration Log entry showing the Yield% calculation:

```
## Iteration Log

| Pass | New Findings | Total Findings | Yield% | Decision |
|------|--------------|----------------|--------|----------|
| 1    | 12           | 12             | 100%   | Continue |
| 2    | 4            | 16             | 25%    | Continue |
| 3    | 1            | 17             | 5.9%   | Exit (< 10%) |
```

**Required columns:**

- **New Findings:** Count of genuinely new items discovered this pass
- **Total Findings:** Cumulative count
- **Yield%:** `New / Total × 100` (show the math)
- **Decision:** Continue or Exit with reason

**Anti-pattern:** Reporting only final Yield% without iteration history. The log proves convergence wasn't faked.

### Exit Gate

Cannot claim "done" until:

- [ ] Coverage complete (no `[ ]` or `[?]` items)
- [ ] Connections mapped (dependencies, failure propagation)
- [ ] Disconfirmation attempted for P0 findings
- [ ] Assumptions resolved (verified, invalidated, or flagged)
- [ ] Convergence reached (Iteration Log shows Yield% below threshold)
- [ ] Stopping criteria satisfied

## Decision Points

**Choosing coverage structure:**

- Tree → codebase has clear hierarchical modules (monolith, layered architecture)
- Graph → heavy interdependencies, microservices, event-driven
- Matrix → cross-cutting concerns matter (security × each module, performance × each endpoint)
- Backlog → structure unclear at start; discover as you go

**During DISCOVER — when to stop adding dimensions:**

- Applied ≥3 discovery techniques
- New dimensions are P2 (nice-to-have, not critical)
- Diminishing returns on additional perspectives

**During EXPLORE — depth calibration:**

- P0 dimensions: Deep exploration, E2+ evidence required
- P1 dimensions: Moderate depth, E1 acceptable
- P2 dimensions: Surface only, or defer entirely

**When Yield% is high but time is limited:**

- Do NOT exit early — document the incomplete state
- Lower thoroughness level if appropriate (Rigorous → Adequate)
- Flag which dimensions remain unexplored

**When findings contradict each other:**

- STOP exploration on other dimensions
- Investigate contradiction with additional methods
- Document resolution or flag as unresolved

**When to escalate to user:**

- Codebase requires credentials or access you don't have
- Key files are binary, minified, or unreadable
- Architecture is so unusual that seed dimensions don't fit

## Examples

**Scenario:** User asks "Explore this codebase thoroughly" on an unfamiliar Node.js web framework.

### ❌ BAD: Ad-hoc exploration without structure

Claude reads `README.md`, scans a few source files, and reports:

> "This is a web framework. The main entry point is `src/index.ts`. It uses Express-like routing in `src/router/`. There are middleware in `src/middleware/`. Tests are in `tests/`."

**Why it's bad:**

- No systematic coverage — missed entire subsystems
- No evidence levels — "it uses Express-like routing" is E0 (assertion)
- No convergence — stopped when it felt like enough
- No documented methodology — can't verify completeness or reproduce
- Missed non-obvious patterns (plugin system, lifecycle hooks, error propagation)

### ✅ GOOD: Framework-driven thorough exploration

Claude runs Entry Gate, identifies dimensions, loops until convergence:

**Entry Gate output:**

- Assumptions: Node.js project, can read all source files, English documentation
- Thoroughness: Rigorous
- Stopping: Discovery-based (two loops, no new P0/P1)
- Structure: Tree (clear module hierarchy)

**Iteration Log:**

| Pass | New Findings | Total Findings | Yield% | Decision     |
| ---- | ------------ | -------------- | ------ | ------------ |
| 1    | 8            | 8              | 100%   | Continue     |
| 2    | 3            | 11             | 27%    | Continue     |
| 3    | 1            | 12             | 8%     | Exit (< 10%) |

**Pass 1 findings:**

- Structure: 4 top-level modules identified (core, router, middleware, plugins)
- Data flow: Request → middleware chain → handler → response
- Dependencies: 3 external (http, path, events), tight internal coupling in core

**Pass 2 findings:**

- NEW: Plugin system discovered (missed in Pass 1) — P0, escalated
- REVISED: Middleware isn't linear — supports branching via conditions
- Testing: Unit tests mock core, integration tests use real server

**Pass 3 findings:**

- No new dimensions
- Refined understanding of plugin lifecycle hooks
- Disconfirmation: Tried to find global state mutation — none found

**Exit:** Iteration Log shows Yield% < 10%, discovery-based criteria met.

**Why it's good:**

- Systematic coverage with tracked dimensions
- Evidence levels assigned (E2 for P0 findings)
- Iteration Log shows convergence with explicit math — proves rigor wasn't faked
- Documented methodology — reproducible, auditable
- Discovered non-obvious patterns through iteration

## Anti-Patterns

**Pattern:** One-pass theater
**Why it fails:** Running the loop once and claiming "it converged" defeats the purpose. Real exploration discovers new dimensions that require re-exploration.
**Fix:** Yield% must actually drop below threshold over multiple passes. First pass is always 100%.

**Pattern:** Summary-only Yield%
**Why it fails:** Reporting "final Yield% was 8%" without showing the iteration log hides whether convergence was real or fabricated.
**Fix:** Include the full Iteration Log table showing New/Total/Yield%/Decision for each pass. The math must be visible.

**Pattern:** Skipping Entry Gate
**Why it fails:** Without assumptions surfaced, you don't know what you're taking for granted. Without thoroughness level set, you have no stopping criteria.
**Fix:** Entry Gate is mandatory. Document assumptions even if they seem obvious.

**Pattern:** E0 evidence for P0 dimensions
**Why it fails:** "I believe the data flows through X" is assertion, not evidence. P0 dimensions require E2 (two independent methods).
**Fix:** For every P0 finding, cite: what file(s), what command(s), what confirmed it.

**Pattern:** Exploring breadth without depth
**Why it fails:** Knowing "there's a plugin system" without understanding how plugins are loaded, registered, and invoked leaves critical gaps.
**Fix:** P0 dimensions require deep exploration. Trace data flow, read implementation, verify with tests.

**Pattern:** Ignoring DISCOVER phase
**Why it fails:** Seed dimensions are a starting point, not the complete list. Skipping DISCOVER means missing dimensions you didn't think to include.
**Fix:** Apply ≥3 discovery techniques. Pre-mortem alone often surfaces 2-3 missed dimensions.

**Pattern:** Stopping when "it feels complete"
**Why it fails:** Human intuition about completeness is unreliable. "Feels done" is not a stopping criterion.
**Fix:** Use Yield% and stopping criteria templates. Exit Gate must pass.

## Troubleshooting

**Symptom:** Yield% stays high (>30%) after multiple passes
**Cause:** Either the codebase is genuinely complex, or dimensions are too broad
**Next steps:**

- Break large dimensions into sub-dimensions (e.g., "Data flow" → "Request flow", "Event flow", "State updates")
- Check if new discoveries are truly P0/P1 or could be P2
- Consider switching to Exhaustive thoroughness if stakes warrant it

**Symptom:** DISCOVER phase produces no new dimensions
**Cause:** Techniques applied superficially, or seed list was already comprehensive
**Next steps:**

- Apply techniques with genuine adversarial intent — "what would break this exploration?"
- Try different perspectives: attacker, maintainer, new hire, performance engineer
- If genuinely no new dimensions, document this and proceed

**Symptom:** Can't achieve E2 evidence for a dimension
**Cause:** Dimension may not be verifiable through static exploration (requires runtime)
**Next steps:**

- Document as E1 with note: "Requires runtime verification"
- Flag in report as lower-confidence finding
- Suggest verification method for user to run

**Symptom:** Coverage structure doesn't fit the codebase
**Cause:** Initial choice (tree/graph/matrix) was wrong for this architecture
**Next steps:**

- Switch structures mid-exploration — this is allowed
- Document why the switch was needed (useful insight about the codebase)
- Migrate tracked items to new structure

**Symptom:** Exploration takes too long
**Cause:** Thoroughness level too high for the need, or codebase is very large
**Next steps:**

- Consider scoping to a subsystem rather than entire codebase
- Lower thoroughness level (Rigorous → Adequate) if stakes allow
- Do NOT abandon rigor — incomplete exploration should be documented as incomplete

## Verification

**Quick check:** Exit Gate passes and Iteration Log shows Yield% below threshold.

**Deeper validation:**

- Compare findings against actual documentation (if available)

## References

**Required protocol:**

- [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md) — Full framework specification (Entry/Exit Gates, loop phases, Yield%, evidence levels, report template)

**The framework reference contains:**

- Normative requirements (MUST/SHOULD/MAY)
- Coverage structure options (matrix/tree/graph/backlog)
- Cell Schema for tracking items
- Thoroughness Report Template
- Stopping criteria templates
