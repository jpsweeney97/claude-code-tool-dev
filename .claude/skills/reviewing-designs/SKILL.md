---
name: reviewing-designs
description: Iterative design review using the Framework for Thoroughness. Use when verifying a design captures all requirements from sources. Use after creating specs from multiple documents. Use before implementing from a design. Use when past designs have led to implementation surprises.
---

# Reviewing Designs

## Overview

Design review catches issues before implementation, when they're cheap to fix. This skill unifies two concerns:

1. **Source coverage** — Does the design capture everything from source materials?
2. **Implementation readiness** — Can someone build from this without asking clarifying questions?

A single pass checking "is X mentioned?" misses decision rules, exit criteria, and safety defaults — single sentences with outsized impact. This skill uses the Framework for Thoroughness to iterate until findings converge.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness_v1.0.0.md)
**Default thoroughness:** Rigorous

**Core insight:** The items most often missed are single sentences that define behavior at decision points.

## When to Use

- After creating a design document from multiple sources
- When verifying a specification captures all requirements
- Before implementing from a design (verify completeness and clarity)
- When past designs have led to implementation surprises, missing pieces, or ambiguous specs
- After brainstorming completes and a design document exists
- When merging methodologies or patterns from different sources

## When NOT to Use

- No design document exists yet (use brainstorming first)
- Simple document reviews that don't involve source comparison or implementation readiness
- Code reviews (use code-review skills)
- Implementation is already complete (this is pre-implementation review)
- Quick prototype/spike where rigor isn't needed

## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifact:** `docs/audits/YYYY-MM-DD-<design-name>-review.md`

Uses Thoroughness Report template with:

- Entry Gate (assumptions, stakes, stopping criteria)
- Coverage Tracker (dimensions with Cell Schema: ID, Status, Priority, Evidence, Confidence)
- Iteration Log (pass-by-pass Yield%)
- Findings grouped by dimension type:
  - Source Coverage Gaps
  - Implementability Issues
  - Adversarial Findings
- Disconfirmation Attempts
- Exit Gate verification

**Summary table (top of artifact and in chat):**

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | N     | Issues that break correctness or execution |
| P1       | N     | Issues that degrade quality                |
| P2       | N     | Polish items                               |

**Chat summary (brief — not the full report):**

```
**Review complete:** [design name]
**Findings:** P0: N | P1: N | P2: N
**Key issues:** [1-2 most critical if any]
**Full report:** `docs/audits/YYYY-MM-DD-<name>-review.md`
```

**Do NOT include in chat:** Full findings list, iteration log, coverage tracker, disconfirmation details.

**Definition of Done:**

- [ ] Entry Gate completed and recorded
- [ ] All dimensions explored with Evidence/Confidence ratings
- [ ] Yield% below threshold for thoroughness level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed
- [ ] Exit Gate criteria satisfied
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify inputs:**

- Target document (the design being reviewed)
- Source documents (materials the design should capture), if applicable
- User-specified concerns, if any

If inputs are unclear, ask. Accept paths, conventions (e.g., `docs/plans/`), or descriptions.

**2. Surface assumptions:**
List what you're taking for granted:

- Source documents are complete and authoritative
- Target document is the current version
- [Any context-specific assumptions]

**3. Calibrate stakes:**

| Factor        | Adequate     | Rigorous       | Exhaustive        |
| ------------- | ------------ | -------------- | ----------------- |
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius  | Localized    | Moderate       | Wide/systemic     |
| Cost of error | Low          | Medium         | High              |
| Uncertainty   | Low          | Moderate       | High              |
| Time pressure | High         | Moderate       | Low/none          |

**Default: Rigorous.** Override if user specifies or factors clearly indicate otherwise.

**4. Select stopping criteria:**

- **Primary:** Yield-based (Yield% below threshold)
- **Thresholds:** Adequate <20%, Rigorous <10%, Exhaustive <5%

**5. Record Entry Gate:**
Document assumptions, stakes level, and stopping criteria before proceeding.

### The Review Loop

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
DISCOVER ──► EXPLORE ──► VERIFY ──► REFINE?
                                          │
                                    (Yield% above
                                     threshold?)
                                          │
                                     EXIT if below
```

#### DISCOVER: What dimensions should I check?

**Seed dimensions:** See [Dimension Catalog](references/dimensions-and-troubleshooting.md#dimension-catalog) for full definitions.

| Category | Dimensions | When to Check |
|----------|------------|---------------|
| Source Coverage | D1-D3 | When source documents exist |
| Behavioral Completeness | D4-D6 | When design will be implemented |
| Implementation Readiness | D7-D11 | When design will be implemented |
| Consistency | D12 | Always |
| Document Quality | D13-D19 | Always |

**Dimension applicability rules:**

**Always mandatory (cannot skip):**

- Document Quality (D13-D19)
- Cross-validation (D12)

**Conditional (require justification to skip):**

- Source Coverage (D1-D3) — skip only if no source documents exist
- Behavioral Completeness (D4-D6) — skip only if design won't be implemented
- Implementation Readiness (D7-D11) — skip only if design is documentation-only

**Before marking any dimension N/A:**

1. State specific reason (not "doesn't apply" but WHY it doesn't apply)
2. Test: "Would a skeptical reviewer accept this justification?"
3. Self-check: "If this dimension revealed issues, would I be surprised?"

If the answer to #2 is "maybe not" or #3 is "no" → check the dimension anyway.

**Assign priorities:**

- **P0:** Missing this breaks correctness or execution
- **P1:** Missing this degrades quality
- **P2:** Polish

**Expand dimensions:** Apply ≥3 DISCOVER techniques from the framework:

- External taxonomy check (find established frameworks for this domain)
- Perspective multiplication (what would different stakeholders notice?)
- Pre-mortem inversion ("This review would be worthless if...")
- Historical pattern mining (what caused problems in similar designs?)

**Output:** Dimension list with priorities (P0/P1/P2)

#### EXPLORE: Check each dimension

For each dimension, record using Cell Schema:

| Field      | Required      | Values                                                                     |
| ---------- | ------------- | -------------------------------------------------------------------------- |
| ID         | Yes           | D1, D2, ... F1, F2, ...                                                    |
| Status     | Yes           | `[x]` done, `[~]` partial, `[-]` N/A, `[ ]` not started, `[?]` unknown     |
| Priority   | Yes           | P0 / P1 / P2                                                               |
| Evidence   | Yes           | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes           | High / Medium / Low                                                        |
| Artifacts  | If applicable | File paths, quotes, line numbers                                           |
| Notes      | If applicable | What's missing, next action                                                |

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

**For each finding:**

- Link to dimension(s) it relates to
- Assign priority based on impact (P0/P1/P2)
- Rate evidence and confidence
- Note artifacts (quotes, file:line references)

**STOP-CHECK before proceeding:**
1. Did you check COMPLETENESS, not just PRESENCE? "Design mentions X" ≠ "X is fully specified." For each dimension, the question is "Is this COMPLETE?" not "Is this MENTIONED?"
2. Did any dimension get `[-]` N/A? Verify each N/A passes the skeptical-reviewer test from DISCOVER. If justification is weak, re-check the dimension.

#### VERIFY: Check findings

**Cross-reference:** Do findings from different dimensions agree or contradict?

**Disconfirmation:** For each P0 dimension/finding, attempt to disprove it:

| Technique              | Method                                         |
| ---------------------- | ---------------------------------------------- |
| Counterexample search  | Find a case that breaks the current claim      |
| Alternative hypothesis | What's another explanation? Test it.           |
| Adversarial read       | Could this evidence be misleading?             |
| Negative test          | What check would fail if the finding is wrong? |
| Cross-check            | Verify via an independent method               |

**Minimum disconfirmation by stakes:**

- Adequate: 1 technique per P0
- Rigorous: 2+ techniques per P0
- Exhaustive: 3+ techniques per P0

**Assumption check:** Which Entry Gate assumptions were validated? Invalidated?

**Gap scan:** Any `[ ]` or `[?]` items remaining?

**Output:** Verified findings with confidence levels

**STOP-CHECK before proceeding:** Was disconfirmation genuine? "I tried to disprove it" requires stating what technique you used AND what you found. If you cannot name the technique and result, go back and actually attempt disconfirmation.

#### REFINE: Loop or exit?

**Calculate Yield%:**

Yield% measures how much new/revisionary information emerged this pass.

An entity _yields_ if it is:

- New (didn't exist last pass)
- Reopened (resolved → unresolved)
- Revised (conclusion changed)
- Escalated (priority increased)

`Yield% = ( |Y| / max(1, |U|) ) × 100`

Where:
- `E_prev` = in-scope P0+P1 entities at end of previous pass
- `E_cur` = in-scope P0+P1 entities at end of current pass
- `U = E_prev ∪ E_cur` (union — prevents denominator shrinkage when items are reclassified or removed)
- `Y` = subset of `U` that yielded this pass

Pass 1 special case: Yield% = 100% (no prior snapshot).

**Priority downgrade rule:** Downgrades (P0→P1, P1→P2) require: (a) new evidence supporting lower severity, (b) documented justification that decision-impact is unchanged. Downgrades without evidence retain original priority. Track all downgrades in the iteration log — they are auditable.

**Worked example:**

| Pass | U (union) | Y (yielding) | Yield% |
|------|-----------|--------------|--------|
| 1 | — | — | 100% (special case) |
| 2 | 10 | 3 (2 new + 1 revised) | 30% |
| 3 | 11 | 1 (1 new) | 9% |

Pass 3 Yield% (9%) is below Rigorous threshold (10%) → exit to Adversarial Pass.

**Continue iterating if:**

- New dimensions discovered
- Findings significantly revised
- Coverage has unresolved `[ ]` or `[?]` items
- Assumptions invalidated that affect completed items
- Yield% above threshold for stakes level

**Exit to Adversarial Pass when:**

- No new dimensions in last pass
- No significant revisions
- All items resolved (`[x]`, `[-]`, or `[~]` with documented gaps)
- Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

**Iteration cap (failsafe):** If convergence not reached after 5 passes (Adequate), 7 passes (Rigorous), or 10 passes (Exhaustive), exit with finding: "Design may need fundamental revision — review did not converge after N passes." This prevents infinite loops on genuinely problematic designs.

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if VERIFY found nothing.

This pass challenges the _design itself_, not just individual findings. Apply each lens with genuine adversarial intent — objections must cause discomfort if true.

| ID | Lens                       | Question                                                                                                       |
| -- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A1 | **Assumption Hunting**     | What assumptions does the design make (explicit and implicit)? What if they're wrong?                          |
| A2 | **Scale Stress**           | What breaks at 10x? 100x? Where are the bottlenecks?                                                           |
| A3 | **Competing Perspectives** | Security: attack vectors? Performance: slow spots? Maintainability: hard to change? Operations: hard to debug? |
| A4 | **Kill the Design**        | What's the strongest argument against this? If it fails in production, what's the cause?                       |
| A5 | **Pre-mortem**             | It's 6 months later, this failed catastrophically. What went wrong? What warnings were ignored?                |
| A6 | **Steelman Alternatives**  | What approaches were rejected? What would make them better than this design?                                   |
| A7 | **Challenge the Framing**  | Is this the right problem to solve? Are we addressing a symptom instead of root cause?                         |
| A8 | **Hidden Complexity**      | Where is complexity underestimated? What looks simple but isn't?                                               |
| A9 | **Motivated Reasoning**    | Where might the design rationalize a preferred approach? Is there anchoring to an early idea?                  |

**Completion schema:** For each applied lens, record: lens ID, objection raised, response/mitigation, and residual risk (if any). Verify the count of lenses with non-empty objections matches the stakes requirement below.

**Minimum depth by stakes:**

- Adequate: Apply 4+ lenses (by ID); document key objections
- Rigorous: Apply all 9 lenses (A1-A9); document objections and responses
- Exhaustive: Apply all 9 lenses (A1-A9); document objections, responses, and residual risks

**Output:** Adversarial findings added to report, categorized separately from systematic findings (reference by lens ID)

### Exit Gate

**Cannot claim "done" until ALL criteria pass:**

| Criterion                 | Check                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| Coverage complete         | No `[ ]` or `[?]`. All items are `[x]`, `[-]` (with rationale), or `[~]` (with documented gaps) |
| Evidence requirements met | P0 dimensions have required evidence level for stakes                                           |
| Disconfirmation attempted | Techniques applied to P0s; documented what was tried and found                                  |
| Assumptions resolved      | Each verified, invalidated, or flagged as unverified                                            |
| Convergence reached       | Yield% below threshold for stakes level                                                         |
| Adversarial pass complete | All required lenses applied (with IDs); objections documented with responses or accepted risks  |

**Post-completion self-check (verify before producing output):**

- [ ] Entry Gate: inputs, assumptions, stakes, stopping criteria all recorded
- [ ] DISCOVER: ≥3 techniques applied; D12-D19 not skipped; N/A dimensions have skeptical-reviewer justification
- [ ] EXPLORE: each dimension has Cell Schema fields (Status, Evidence, Confidence); findings linked to dimensions
- [ ] VERIFY: disconfirmation techniques documented (what was tried AND what was found)
- [ ] REFINE: Yield% calculated per pass; iteration log shows pass-by-pass changes
- [ ] Adversarial: required lens count met for stakes; pre-mortem produced specific, plausible failure story
- [ ] If a P0 exists, would the user definitely see it in the summary?
- [ ] If the design had hidden flaws, did I genuinely try to find them?

**"No issues found" requires extra scrutiny:** Was disconfirmation genuinely attempted? Self-check: "Did I actually look, or did I assume the design was fine?"

**Produce output:**

1. Write full report to `docs/audits/YYYY-MM-DD-<design-name>-review.md`
2. Present brief summary in chat (P0/P1/P2 counts + key issues only)
3. Chat must NOT contain full findings, iteration log, or coverage tracker

## Decision Points

**Inputs unclear:**

- If target document not specified → Ask: "Which design document should I review?"
- If sources not specified but source comparison is relevant → Ask: "Are there source documents this design should capture?"
- If user says "just review it" → Proceed with D4-D19 (Behavioral Completeness through Document Quality); mark D1-D3 as `[-]` with rationale: no source documents specified

**Stakes disagreement:**

- If factors split across columns → Choose the higher level
- If user specifies a level → User's choice wins; document rationale in Entry Gate

**Dimension not applicable:**

- Mark as `[-]` with brief rationale (e.g., "D1-D3: N/A — no source documents specified")
- Do not force-fit dimensions that don't apply

**P0 issue found during EXPLORE:**

- Continue review (don't stop to fix)
- Ensure finding is prominently captured
- Complete remaining dimensions before exiting

**Yield% ambiguous:**

- If unsure whether a change "counts" as revision → When in doubt, count it (bias toward more iteration)
- If Yield% hovers near threshold → Run one more pass to confirm convergence

**Adversarial pass finds fundamental flaw:**

- Add as P0 finding
- Do not attempt to fix within this skill (remediation is outside scope)
- Note in summary: "Design may need fundamental rethinking"

**User pressure to skip steps:**

- Acknowledge the pressure
- "Skipping [Entry Gate/Adversarial Pass/etc.] risks missing issues that surface during implementation."
- Complete minimum requirements for stakes level
- Compress output, not process

**"No issues" feels wrong:**

- Trust the feeling — run disconfirmation more aggressively
- Self-check: "What would I expect to find if there WERE issues? Did I look there?"
- If still nothing after genuine effort → Accept the finding; document what was checked

## Examples

See [Review Examples](references/examples.md) for BAD vs. GOOD comparison showing single-pass checkbox review (what to avoid) vs. iterative framework-based review (what to do).

## Anti-Patterns

Common failure modes and fixes: [Anti-Patterns Reference](references/dimensions-and-troubleshooting.md#anti-patterns)

**Most critical (memorize these):**

- **Single-pass "looks good" review** → Iterate until Yield% below threshold. Pass 1 is always 100% yield — you can't exit after one pass.
- **Checking presence instead of completeness** → Ask "Is this COMPLETE?" not "Is this MENTIONED?"
- **Skipping Document Quality dimensions** → D13-D19 are mandatory. Cannot be skipped.

## Troubleshooting

If the review process isn't working as expected, see [Troubleshooting Reference](references/dimensions-and-troubleshooting.md#troubleshooting).

**Quick checks:**

- **Review completed in one pass?** → Pass 1 is always 100% yield; cannot exit after one pass
- **Most dimensions marked N/A?** → Document Quality (D13-D19) and Cross-validation (D12) cannot be N/A
- **"No issues found"?** → Verify disconfirmation was genuinely attempted

## Extension Points

**Domain-specific dimensions:**

- Security reviews: Add threat modeling dimensions (attack vectors, trust boundaries)
- API designs: Add consistency dimensions (naming conventions, error formats)
- Performance-critical: Add scale dimensions (bottlenecks, resource bounds)

**Framework handoffs:**

- If review finds design is fundamentally flawed → Recommend returning to brainstorming
- If review passes → Design ready for writing-plans or implementation
- These are informational notes, not automated handoffs (workflow decisions are user's domain)

**Custom artifact locations:**

- Default: `docs/audits/YYYY-MM-DD-<design-name>-review.md`
- Projects can override via CLAUDE.md if different convention exists

**Stakes presets:**

- Projects can define default stakes in CLAUDE.md (e.g., "all design reviews are Rigorous minimum")
- User can still override per-review
- **Conflict resolution:** If CLAUDE.md specifies a minimum and user requests lower: state the concrete risk delta (which evidence requirements drop, which disconfirmation techniques are removed, how confidence ceiling changes), record accepted risk in Entry Gate, proceed with user's choice
