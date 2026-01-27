---
name: reviewing-code
description: Use when performing thorough code review. Use when asked to "review this code", "check code quality", or "audit this module". Use before merging significant changes. Use when code quality concerns exist but aren't pinpointed. Use when past reviews missed issues that surfaced later.
---

# Reviewing Code

## Overview

Code reviews often fail silently: one-pass "looks good" verdicts, fragmented tooling that misses gaps, context-blind analysis that doesn't understand the system, and shallow checks that miss technical debt, over-engineering, and architectural drift.

This skill addresses these failures through:

1. **Comprehensive coverage** — 41 dimensions across 9 categories (correctness, robustness, security, performance, maintainability, code health, architecture, testing, type design)
2. **Context-first approach** — Dedicated exploration phase understands codebase patterns and conventions before reviewing
3. **Iterative convergence** — Multiple passes with Yield% tracking; cannot exit after one pass
4. **Fixes applied** — Issues are fixed in place, not just reported
5. **Stratified fix safety** — Cosmetic fixes applied directly; behavior-changing fixes require test verification or user approval

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness.md)
**Default thoroughness:** Rigorous

**Outputs:**
- Refined code with fixes applied
- Review report at `docs/audits/YYYY-MM-DD-<target>-code-review.md`
- Brief summary in chat

**Definition of Done:**
- [ ] Context phase completed
- [ ] All applicable dimensions explored with Evidence/Confidence ratings
- [ ] Yield% below threshold for thoroughness level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed
- [ ] Fixes applied (stratified by risk)
- [ ] Exit Gate criteria satisfied
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only

## When to Use

- When asked to "review this code", "check code quality", or "audit this module"
- Before merging significant changes (alternative to quick PR review when thoroughness needed)
- When code quality concerns exist but aren't pinpointed
- When past reviews missed issues that surfaced later
- After major refactoring to verify nothing was lost
- When onboarding to unfamiliar code that will be modified
- When technical debt feels high but isn't catalogued
- When preparing code for production deployment
- When security, performance, or architecture concerns are suspected

## When NOT to Use

- **Quick targeted checks** — Use pr-review-toolkit agents for fast, focused review
- **PR diffs only** — Use `/review-pr` for standard pre-merge review
- **No code exists** — Can't review what isn't written
- **Generated code** — Auto-generated code follows different quality standards
- **Throwaway prototypes** — Rigor adds overhead where quality doesn't matter
- **Code you can't modify** — Third-party libraries, vendor code (can audit, but can't apply fixes)

## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifacts:**

| Artifact | Location |
|----------|----------|
| Refined code | Original locations (fixes applied in place) |
| Review report | `docs/audits/YYYY-MM-DD-<target>-code-review.md` |

**Review report includes:**

- Entry Gate (assumptions, stakes, stopping criteria, target scope)
- Context Summary (patterns discovered, conventions identified)
- Coverage Tracker (dimensions with Cell Schema)
- Iteration Log (pass-by-pass Yield%)
- Findings grouped by category (C1-C5, R1-R4, S1-S5, PF1-PF4, M1-M6, H1-H5, A1-A4, T1-T4, TD1-TD4)
- Fixes Applied (what changed, where, risk level)
- Fixes Deferred (user approval required)
- Disconfirmation Attempts
- Adversarial Findings
- Exit Gate verification

**Chat summary (brief — not the full report):**

```
**Review complete:** [target]
**Findings:** P0: N | P1: N | P2: N
**Fixes applied:** N (cosmetic: X, simplification: Y, behavior: Z)
**Fixes deferred:** N (awaiting approval)
**Key changes:** [1-2 most significant fixes]
**Full report:** `docs/audits/YYYY-MM-DD-<target>-code-review.md`
```

**Do NOT include in chat:** Full findings list, iteration log, coverage tracker, context summary, disconfirmation details, complete fix list, adversarial findings.

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify target:**
- What code is being reviewed? (files, module, directory, feature)
- If unclear, ask: "Which code should I review?"

**2. Determine review scope:**

| Category | Dimensions | When to Check |
|----------|------------|---------------|
| Correctness | C1-C5 | Always |
| Robustness | R1-R4 | Always |
| Maintainability | M1-M6 | Always |
| Code Health | H1-H5 | Always |
| Security | S1-S5 | When code handles user input, auth, or sensitive data |
| Performance | PF1-PF4 | When code is on critical path or handles scale |
| Architecture | A1-A4 | When reviewing module/feature (not single file) |
| Testing | T1-T4 | When tests exist or should exist |
| Type Design | TD1-TD4 | When code defines types/classes/interfaces |

**3. Surface assumptions** and **4. Calibrate stakes** (default: Rigorous)

**5. Select stopping criteria:** Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

### Context Phase

**YOU MUST** complete the Context Phase before reviewing. Do not skip even for "familiar" code.

**1. Read project configuration:** CLAUDE.md, package manifests, configs
**2. Explore codebase structure:** Directory organization, module boundaries, entry points
**3. Identify patterns and conventions:** Naming, error handling, testing, architecture
**4. Map target context:** Imports, exports, callers, dependencies, role in system
**5. Record Context Summary**

**Exploration strategy:**
- **1-3 files:** Direct exploration sufficient
- **Module/feature:** Use Explore agent
- **Large scope:** Deploy multiple Explore agents in parallel (e.g., one for architecture, one for patterns, one for dependencies) then synthesize findings

**Multi-file synthesis:** When reviewing multiple files, look for:
- Inconsistent patterns between files (different error handling styles, naming conventions)
- Assumptions in one file that aren't validated in another (caller assumes non-null but callee can return null)
- Circular dependencies or layer violations across file boundaries

### The Review Loop

```
DISCOVER ──► EXPLORE ──► VERIFY ──► FIX ──► REFINE? ──► (loop until Yield% below threshold)
```

**DISCOVER:** Identify dimensions, assign priorities (P0/P1/P2), apply ≥3 expansion techniques.

**EXPLORE:** Check each dimension using Cell Schema (ID, Status, Priority, Evidence, Confidence). Classify findings by fix type.

**VERIFY:** Cross-reference findings, attempt disconfirmation for P0s, check assumptions.

**FIX:** Apply corrections stratified by risk:

| Fix Type | Definition | Strategy |
|----------|------------|----------|
| Cosmetic | Formatting, naming, comments, type annotations (no runtime change) | Apply → Run tests → Verify green |
| Simplification | Refactoring that preserves exact behavior (extract function, reduce nesting) | Apply → Run tests → Verify green |
| Behavior-changing | Any fix that could change runtime behavior (logic, error handling, validation) | Write failing test → Apply → Verify passes |
| Behavior-changing (no coverage) | Behavior-changing fix where no tests exercise the affected code | **Defer for user approval** |

**REFINE:** Calculate Yield%. Continue if above threshold; exit to Adversarial Pass when below.

See [Dimension Catalog](references/dimension-catalog.md) for full dimension definitions.

### Adversarial Pass

**YOU MUST** complete before Exit Gate. Apply these lenses with genuine adversarial intent:

| Lens | Question |
|------|----------|
| Assumption Hunting | What assumptions does this code make? What if wrong? |
| Scale Stress | What breaks at 10x? 100x? |
| Security Mindset | How would an attacker abuse this? |
| Failure Modes | How does this fail? Silently? Gracefully? |
| Maintenance Burden | What will be painful to change in 6 months? |
| Kill the Code | Strongest argument for rewriting? |
| Pre-mortem | 6 months later, this caused an outage. What went wrong? |
| Hidden Complexity | Where is complexity hiding? |
| Over-engineering | What here is unnecessary? |

**Minimum depth by stakes:**

| Level | Required Lenses | Must Include |
|-------|-----------------|--------------|
| Adequate | 4 | Assumption Hunting, Failure Modes, + 2 others |
| Rigorous | 6 | All of Adequate + Security Mindset, Pre-mortem |
| Exhaustive | All 9 | Complete coverage |

**Pre-mortem requirement:** At every level, the Pre-mortem lens must produce a specific, plausible failure story — not just "could fail." If no plausible story emerges, document why (e.g., "code is pure function with no side effects").

### Exit Gate

Cannot claim "done" until ALL criteria pass:

- [ ] Context Phase complete (patterns, conventions, dependencies documented)
- [ ] Coverage complete (no `[ ]` or `[?]` items remaining)
- [ ] Evidence requirements met (E2 for P0 at Rigorous; E3 for P0 at Exhaustive)
- [ ] Disconfirmation attempted (1+ technique per P0 at Adequate; 2+ at Rigorous; 3+ at Exhaustive)
- [ ] Convergence reached (Yield% below threshold: <20% Adequate, <10% Rigorous, <5% Exhaustive)
- [ ] Adversarial pass complete (minimum lenses applied, Pre-mortem produced story)
- [ ] Fixes applied (stratified by risk; behavior-changing with tests verified)
- [ ] Tests pass (all tests green after fixes)

## Decision Points

- **Target unclear:** Ask which code to review
- **Behavior-changing fix, no tests:** Defer for user approval — do NOT apply
- **Tests fail after fix:** Revert immediately, document, investigate
- **Adversarial pass finds fundamental flaw:** Note "Code may need significant redesign"
- **User pushes back:** Don't defend — explore if intentional, mark as accepted deviation

## Examples

See [Examples section in full documentation](references/examples.md) for detailed BAD/GOOD comparison showing one-pass failure vs iterative review with context and stratified fixes.

## Anti-Patterns

- **One-pass "looks good"** → Iterate until Yield% below threshold
- **Skipping Context Phase** → Mandatory even for familiar code
- **Checking presence not correctness** → Ask "Is this CORRECT?" not "Does this EXIST?"
- **Applying behavior-changing fixes without tests** → Defer to user
- **Adversarial pass as checkbox** → Pre-mortem must produce plausible failure story

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "I know this code well" | Familiarity breeds blindness. Context Phase is mandatory. |
| "It's just a small change" | Small changes can have large blast radius. Check scope. |
| "Tests are passing" | Passing tests ≠ correct code. Tests may not cover the issue. |
| "The fix is obvious" | Obvious fixes can introduce subtle bugs. Verify with tests. |
| "No time for full review" | Partial review finds partial issues. Compress output, not process. |
| "This dimension doesn't apply" | Correctness, Robustness, Maintainability, Code Health always apply. |
| "I'll just do a quick check" | Pass 1 is always 100% yield — one pass is never enough. |

**All of these mean: Complete the review. No exceptions.**

## Troubleshooting

- **Review completes in one pass:** Pass 1 is always 100% yield — cannot exit after one pass
- **Many dimensions N/A:** Correctness, Robustness, Maintainability, Code Health cannot be N/A
- **All fixes deferred:** Review fix classifications — cosmetic should be applied
- **Yield% never drops:** Code may need significant refactoring before detailed review

## Verification

- [ ] Entry Gate complete (target, scope, stakes, stopping criteria)
- [ ] Context Phase complete (patterns, conventions, dependencies)
- [ ] DISCOVER complete (dimensions prioritized, ≥3 techniques applied)
- [ ] EXPLORE complete (Cell Schema for each dimension)
- [ ] VERIFY complete (disconfirmation for P0s)
- [ ] FIX complete (stratified safety, tests run)
- [ ] REFINE complete (Yield% converged)
- [ ] Adversarial Pass complete (all lenses, pre-mortem produced failure story)
- [ ] Exit Gate passed
- [ ] Report written to artifact location
- [ ] Chat contains brief summary only

## Extension Points

**Domain-specific dimensions:** Add OWASP for web, REST conventions for APIs, etc.

**Stakes presets:** Projects can set defaults in CLAUDE.md.

**Integration:** Hand off to testing-skills if coverage insufficient, systematic-debugging for root cause analysis.

## References

- [Dimension Catalog](references/dimension-catalog.md) — Full definitions for all 41 dimensions
- [Framework for Thoroughness](references/framework-for-thoroughness.md) — Protocol specification
