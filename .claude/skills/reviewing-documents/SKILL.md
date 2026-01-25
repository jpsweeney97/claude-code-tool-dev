---
name: reviewing-documents
description: Use when reviewing or improving specification documents, designs, or frameworks. Use after authoring or significantly modifying a spec. Use before implementing from a design. Use when past designs have led to implementation surprises. Use when asked to "review," "refine," or "improve" a document.
---

# Reviewing Documents

## Overview

Specification documents often ship unclear: first drafts lack precision, implicit knowledge stays in the author's head, and reviews become "LGTM" theater. Design reviews catch issues before implementation, when they're cheap to fix.

This skill addresses three concerns:

1. **Document quality** — Are terms defined? Is language precise? Are instructions actionable?
2. **Source coverage** — Does the document capture everything from source materials? (when sources exist)
3. **Implementation readiness** — Can someone build from this without asking clarifying questions? (when document will be implemented)

A single pass checking "is X mentioned?" misses decision rules, exit criteria, and safety defaults — single sentences with outsized impact. Different lenses catch different problems: a single read-through favors high-salience issues (undefined terms) and misses low-salience ones (distant inconsistencies). Sequential passes with dedicated focus surface what parallel scanning misses.

This skill uses the Framework for Thoroughness to iterate until findings converge, then applies fixes.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness.md)
**Default thoroughness:** Rigorous

**Outputs:**
- Refined document with fixes applied
- Review report at `docs/audits/YYYY-MM-DD-<document-name>-review.md`
- Brief summary in chat

## When to Use

- After authoring a specification, framework, or process document
- After creating a design document from multiple sources
- After significant modifications to an existing spec
- When verifying a specification captures all requirements
- Before implementing from a design (verify completeness and clarity)
- When past designs have led to implementation surprises, missing pieces, or ambiguous specs
- After brainstorming completes and a design document exists
- When merging methodologies or patterns from different sources
- When asked to "review," "refine," or "improve" a spec document
- Before publishing or promoting a spec to production use
- When a spec feels unclear but you can't pinpoint why

## When NOT to Use

- **No document exists yet** — use brainstorming first
- **Code** — this is for prose specifications, not source code
- **Code reviews** — use code-review skills
- **External documents you can't edit** — third-party standards, vendor docs
- **Ephemeral content** — chat messages, temporary notes, one-off explanations
- **Implementation already complete** — this is pre-implementation review
- **Quick prototype/spike where rigor isn't needed** — skill adds overhead

## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifacts:**

| Artifact | Location |
|----------|----------|
| Refined document | Original location (edits applied in place) |
| Review report | `docs/audits/YYYY-MM-DD-<document-name>-review.md` |

**Review report includes:**

- Entry Gate (assumptions, stakes, stopping criteria)
- Coverage Tracker (dimensions with Cell Schema: ID, Status, Priority, Evidence, Confidence)
- Iteration Log (pass-by-pass Yield%)
- Findings grouped by dimension type:
  - Document Quality Issues
  - Source Coverage Gaps (if sources exist)
  - Implementation Readiness Issues (if document will be implemented)
  - Adversarial Findings
- Fixes Applied (what changed, where)
- Disconfirmation Attempts
- Exit Gate verification

**Summary table (top of report and in chat):**

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | N     | Issues that break correctness or execution |
| P1       | N     | Issues that degrade quality                |
| P2       | N     | Polish items                               |

**Chat summary (brief — not the full report):**

```
**Review complete:** [document name]
**Findings:** P0: N | P1: N | P2: N (N fixed)
**Key changes:** [1-2 most significant fixes]
**Full report:** `docs/audits/YYYY-MM-DD-<name>-review.md`
```

**Do NOT include in chat:** Full findings list, iteration log, coverage tracker, disconfirmation details, complete list of fixes.

**Definition of Done:**

- [ ] Entry Gate completed and recorded
- [ ] All dimensions explored with Evidence/Confidence ratings
- [ ] Yield% below threshold for thoroughness level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed
- [ ] Fixes applied to document
- [ ] Exit Gate criteria satisfied
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify inputs:**

- Target document (the document being reviewed)
- Source documents (materials the document should capture), if applicable
- User-specified concerns, if any

If inputs are unclear, ask. Accept paths, conventions (e.g., `docs/plans/`), or descriptions.

**2. Determine review scope:**

Based on inputs, determine which dimension categories apply:

| Category | When to include |
|----------|-----------------|
| Document Quality (D13-D19) | Always — cannot skip |
| Cross-validation (D12) | Always — cannot skip |
| Source Coverage (D1-D3) | When source documents exist |
| Behavioral Completeness (D4-D6) | When document will be implemented |
| Implementation Readiness (D7-D11) | When document will be implemented |

**3. Surface assumptions:**

List what you're taking for granted:

- Source documents are complete and authoritative (if applicable)
- Target document is the current version
- [Any context-specific assumptions]

**4. Calibrate stakes:**

| Factor        | Adequate     | Rigorous       | Exhaustive        |
| ------------- | ------------ | -------------- | ----------------- |
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius  | Localized    | Moderate       | Wide/systemic     |
| Cost of error | Low          | Medium         | High              |
| Uncertainty   | Low          | Moderate       | High              |
| Time pressure | High         | Moderate       | Low/none          |

**Default: Rigorous.** Override if user specifies or factors clearly indicate otherwise.

**5. Select stopping criteria:**

- **Primary:** Yield-based (Yield% below threshold)
- **Thresholds:** Adequate <20%, Rigorous <10%, Exhaustive <5%

**6. Record Entry Gate:**

Document assumptions, stakes level, scope, and stopping criteria before proceeding.

### The Review Loop

```
    ┌─────────────────────────────────────────────┐
    │                                             │
    ▼                                             │
DISCOVER ──► EXPLORE ──► VERIFY ──► FIX ──► REFINE?
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
| Behavioral Completeness | D4-D6 | When document will be implemented |
| Implementation Readiness | D7-D11 | When document will be implemented |
| Consistency | D12 | Always |
| Document Quality | D13-D19 | Always |

**Document Quality dimensions (the 7 lenses):**

| Dimension | Lens | Question | Catches |
|-----------|------|----------|---------|
| D13 | Implicit concepts | Are all terms defined? | Undefined jargon, assumed knowledge |
| D14 | Precision | Is language precise? | Vague wording, loopholes, wiggle room |
| D15 | Examples | Is abstract guidance illustrated? | Theory without concrete application |
| D16 | Internal consistency | Do parts agree? | Contradictions between sections |
| D17 | Redundancy | Is anything said twice differently? | Duplication that may drift |
| D18 | Verifiability | Can compliance be verified? | Unverifiable requirements |
| D19 | Actionability | Is it clear what to do? | Ambiguous instructions |

**Check order for Document Quality:** D13-D15 (surface issues in single sections) → D16-D17 (cross-section comparison) → D18-D19 (holistic assessment)

**Dimension applicability rules:**

**Always mandatory (cannot skip):**

- Document Quality (D13-D19)
- Cross-validation (D12)

**Conditional (require justification to skip):**

- Source Coverage (D1-D3) — skip only if no source documents exist
- Behavioral Completeness (D4-D6) — skip only if document won't be implemented
- Implementation Readiness (D7-D11) — skip only if document is documentation-only

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
- Historical pattern mining (what caused problems in similar documents?)

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
| Notes      | If applicable | What's missing, proposed fix                                               |

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

**For each finding:**

- Link to dimension(s) it relates to
- Assign priority based on impact (P0/P1/P2)
- Rate evidence and confidence
- Note artifacts (quotes, line:column references)
- Draft proposed fix

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

**Output:** Verified findings with confidence levels and proposed fixes

#### FIX: Apply corrections

For each verified finding:

1. Apply the fix to the document
2. Note what changed (original → revised)
3. Mark finding as fixed in the coverage tracker

**Fix order:** P0 issues first, then P1, then P2.

**Conflict detection:** If fixing one issue would contradict or undo another fix:

1. Note the conflict
2. Determine which fix takes priority (usually the higher-priority finding)
3. Document the trade-off in the review report

**Do not fix:**

- Issues marked as "accepted deviation" by user
- Issues outside the document's scope (flag for separate work)
- Issues that require user decision (flag and ask)

#### REFINE: Loop or exit?

**Calculate Yield%:**

Yield% measures how much new/revisionary information emerged this pass.

An entity _yields_ if it is:

- New (didn't exist last pass)
- Reopened (resolved → unresolved)
- Revised (conclusion changed)
- Escalated (priority increased)

`Yield% = (yielding entities / total P0+P1 entities) × 100`

**Worked example:**

| Pass | Action | P0+P1 Entities | Yielding | Yield% |
|------|--------|----------------|----------|--------|
| 1 | Found 3 P0 gaps, 5 P1 issues | 8 | 8 (all new) | 100% |
| 2 | Found 2 more P0s, revised 1 P1 | 10 | 3 (2 new + 1 revised) | 30% |
| 3 | Found 1 P1, no revisions | 11 | 1 (new) | 9% |

Pass 3 Yield% (9%) is below Rigorous threshold (10%) → exit to Adversarial Pass.

**Continue iterating if:**

- New dimensions discovered
- Findings significantly revised
- Coverage has unresolved `[ ]` or `[?]` items
- Assumptions invalidated that affect completed items
- Fixes introduced new issues
- Yield% above threshold for stakes level

**Exit to Adversarial Pass when:**

- No new dimensions in last pass
- No significant revisions
- All items resolved (`[x]`, `[-]`, or `[~]` with documented gaps)
- Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

**Iteration cap (failsafe):** If convergence not reached after 5 passes (Adequate), 7 passes (Rigorous), or 10 passes (Exhaustive), exit with finding: "Document may need fundamental revision — review did not converge after N passes." This prevents infinite loops on genuinely problematic documents.

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if the review loop found nothing.

This pass challenges the _document itself_, not just individual findings. Apply each lens with genuine adversarial intent — objections must cause discomfort if true.

| Lens                       | Question                                                                                                       |
| -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Assumption Hunting**     | What assumptions does the document make (explicit and implicit)? What if they're wrong?                        |
| **Scale Stress**           | What breaks at 10x? 100x? Where are the bottlenecks?                                                           |
| **Competing Perspectives** | Security: attack vectors? Performance: slow spots? Maintainability: hard to change? Operations: hard to debug? |
| **Kill the Document**      | What's the strongest argument against this? If it fails in production, what's the cause?                       |
| **Pre-mortem**             | It's 6 months later, this failed catastrophically. What went wrong? What warnings were ignored?                |
| **Steelman Alternatives**  | What approaches were rejected? What would make them better than this approach?                                 |
| **Challenge the Framing**  | Is this the right problem to solve? Are we addressing a symptom instead of root cause?                         |
| **Hidden Complexity**      | Where is complexity underestimated? What looks simple but isn't?                                               |
| **Motivated Reasoning**    | Where might the document rationalize a preferred approach? Is there anchoring to an early idea?                |

**Minimum depth by stakes:**

- Adequate: Apply 4 lenses; document key objections; fix issues found
- Rigorous: Apply all 9 lenses; document objections and responses; fix issues found
- Exhaustive: Apply all 9 lenses; document objections, responses, and residual risks; fix issues found

**Output:** Adversarial findings added to report, categorized separately from systematic findings. Fixes applied to document.

### Exit Gate

**Cannot claim "done" until ALL criteria pass:**

| Criterion                 | Check                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| Coverage complete         | No `[ ]` or `[?]`. All items are `[x]`, `[-]` (with rationale), or `[~]` (with documented gaps) |
| Evidence requirements met | P0 dimensions have required evidence level for stakes                                           |
| Disconfirmation attempted | Techniques applied to P0s; documented what was tried and found                                  |
| Assumptions resolved      | Each verified, invalidated, or flagged as unverified                                            |
| Convergence reached       | Yield% below threshold for stakes level                                                         |
| Adversarial pass complete | All required lenses applied; objections documented                                              |
| Fixes applied             | All P0 and P1 findings fixed (or explicitly accepted by user)                                   |

**"No issues found" requires extra verification:**

- [ ] Convergence reached (Yield% below threshold)
- [ ] Disconfirmation genuinely attempted (not just claimed)
- [ ] Self-check: "Did I actually look, or did I assume the document was fine?"

**Produce output:**

1. Write full report to `docs/audits/YYYY-MM-DD-<document-name>-review.md`
2. Present brief summary in chat (P0/P1/P2 counts, fixes applied, key changes only)

## Decision Points

**Inputs unclear:**

- If target document not specified → Ask: "Which document should I review?"
- If sources not specified but source comparison might be relevant → Ask: "Are there source documents this should capture?"
- If user says "just review it" → Proceed with Document Quality and Cross-validation dimensions only; note Source Coverage and Implementation Readiness dimensions skipped

**Stakes disagreement:**

- If factors split across columns → Choose the higher level
- If user specifies a level → User's choice wins; document rationale in Entry Gate

**Dimension not applicable:**

- Mark as `[-]` with brief rationale (e.g., "D1-D3: N/A — no source documents specified")
- Do not force-fit dimensions that don't apply
- Document Quality (D13-D19) and Cross-validation (D12) cannot be marked N/A

**P0 issue found during EXPLORE:**

- Draft the fix immediately
- Continue review (don't stop to apply fixes mid-pass)
- Ensure finding is prominently captured
- Complete remaining dimensions before applying fixes

**Yield% ambiguous:**

- If unsure whether a change "counts" as revision → When in doubt, count it (bias toward more iteration)
- If Yield% hovers near threshold → Run one more pass to confirm convergence

**Fixes conflict with each other:**

- Note the conflict in findings
- Determine which fix takes priority (higher-priority finding wins)
- Document the trade-off
- If iteration cap reached with oscillating fixes → Exit with finding: "Document may need structural revision — fixes are conflicting"

**Adversarial pass finds fundamental flaw:**

- Add as P0 finding
- Apply fix if possible
- If flaw is too fundamental to fix in place → Note in summary: "Document may need fundamental rethinking"

**Many issues found (>10):**

- Check P0/P1/P2 distribution
- If mostly P0 → Document needs significant work; say so clearly
- If mostly P1/P2 → Focus summary on P0s; note "N additional lower-priority findings in full report"
- Consider: Is this document ready for refinement, or does it need rewriting?

**User pushes back on reported issues:**

- Don't defend — explore: "Is this intentional? If so, I'll mark it as accepted."
- Update report to distinguish issues from accepted deviations
- Continue with remaining issues

**User pressure to skip steps:**

- Acknowledge the pressure
- "Skipping [Entry Gate/Adversarial Pass/etc.] risks missing issues that surface during implementation."
- Complete minimum requirements for stakes level
- Compress output, not process

**"No issues" feels wrong:**

- Trust the feeling — run disconfirmation more aggressively
- Self-check: "What would I expect to find if there WERE issues? Did I look there?"
- If still nothing after genuine effort → Accept the finding; document what was checked

**Time pressure:**

- If user needs quick feedback → Run Document Quality dimensions only (D13-D19), note that other dimensions were skipped
- Never skip the report phase — compressed is fine, absent is not
- Note: quick reviews may miss issues that full reviews would catch

## Examples

**Scenario:** Team created a specification for a new authentication system, derived from security requirements docs and API specifications.

### BAD: Single-pass "looks good" review

Claude scans the document once, notes "has all the sections," checks that auth flows are mentioned, and reports: "Spec looks comprehensive. Ready for implementation."

**Why it's bad:**

- No Entry Gate — stakes not assessed, no stopping criteria
- Single pass — no iteration, no Yield% tracking
- Checked presence, not completeness — "auth flows mentioned" ≠ "auth flows fully specified"
- Skipped Behavioral Completeness — no check for decision rules, exit criteria, safety defaults
- No adversarial pass — didn't try to break the design
- No disconfirmation — accepted "looks good" without testing that conclusion
- No fixes applied — just declared it ready
- Missed: Token refresh edge case undefined, error responses inconsistent with API spec, no rollback procedure for failed auth upgrades

### GOOD: Iterative review with fixes applied

**Entry Gate:**

- Target: `docs/specs/auth-system.md`
- Sources: `docs/requirements/security.md`, `docs/specs/api-v2.md`
- Stakes: Rigorous (implementation follows; moderate undo cost)
- Stopping: Yield% <10%

**Pass 1:** DISCOVER dimensions, assign priorities

- D1-D3 (Source Coverage): P0 — must capture all security requirements
- D4-D6 (Behavioral Completeness): P0 — auth failures need clear handling
- D7-D11 (Implementation Readiness): P1
- D12-D19 (Consistency + Document Quality): P1

**Pass 1 EXPLORE:** Found 3 P0 gaps, 5 P1 issues.

- D13: "session" used but not defined
- D14: "should generally validate" is vague — when specifically?
- D4: Token refresh behavior undefined

Yield% = 8/8 = 100% (first pass)

**Pass 1 FIX:** Applied 8 fixes to document.

**Pass 2 EXPLORE:** Deeper check on D4-D6, found 2 more P0 gaps (token refresh race condition, no rollback procedure), revised 1 P1 severity. Yield% = 3/10 = 30%

**Pass 2 FIX:** Applied 3 fixes.

**Pass 3 EXPLORE:** Checked remaining dimensions. Found 1 P1 issue (vague language in error handling). No new P0s, no revisions. Yield% = 1/11 = 9%

**Pass 3 FIX:** Applied 1 fix.

**Adversarial Pass:**

- Pre-mortem: "Auth system fails in production because token refresh race condition wasn't specified" — already found and fixed
- Scale stress: "At 100x users, token validation becomes bottleneck" — added as P1 concern, added note about caching strategy
- Kill the document: "Rollback procedure is still underspecified" — strengthened the rollback section

**Exit Gate:** Yield% <10%, all dimensions checked, disconfirmation attempted, 12 fixes applied.

**Output:**

```
**Review complete:** auth-system.md
**Findings:** P0: 5 | P1: 7 | P2: 2 (14 fixed)
**Key changes:** Added token refresh race condition handling; defined rollback procedure; clarified session terminology
**Full report:** `docs/audits/2024-01-15-auth-system-review.md`
```

**Why it's good:**

- Entry Gate established scope and stakes
- Iterative passes with Yield% tracking
- Checked completeness, not just presence
- All dimension categories covered with appropriate priority
- Fixes applied after each pass
- Adversarial pass found additional issue and strengthened existing fix
- Clear output with fix count and key changes highlighted

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

## Verification

After completing a review, verify:

**Entry Gate:**

- [ ] Inputs identified (target document, source documents if applicable)
- [ ] Scope determined (which dimension categories apply)
- [ ] Assumptions listed
- [ ] Stakes level assessed and recorded
- [ ] Stopping criteria selected (Yield% threshold)

**DISCOVER:**

- [ ] Dimensions identified with priorities (P0/P1/P2)
- [ ] ≥3 DISCOVER techniques applied to expand beyond seed dimensions
- [ ] Document Quality (D13-D19) and Cross-validation (D12) not skipped
- [ ] Any N/A dimensions have skeptical-reviewer-level justification

**EXPLORE:**

- [ ] Each checked dimension has Cell Schema fields (Status, Evidence, Confidence)
- [ ] Evidence requirements met for stakes level (Rigorous: E2 for P0, E1 for P1)
- [ ] Findings linked to dimensions with priority assigned
- [ ] Proposed fixes drafted for each finding

**VERIFY:**

- [ ] Disconfirmation attempted for P0 dimensions (techniques documented)
- [ ] Assumptions resolved (verified, invalidated, or flagged unverified)

**FIX:**

- [ ] Fixes applied in priority order (P0 first)
- [ ] Each fix documented (original → revised)
- [ ] Conflicts noted and resolved

**REFINE:**

- [ ] Yield% calculated for each pass
- [ ] Iteration log shows pass-by-pass changes
- [ ] Convergence reached (Yield% below threshold) or iteration cap hit

**Adversarial Pass:**

- [ ] Required lenses applied for stakes level (Rigorous: all 9)
- [ ] Objections documented with responses or accepted risks
- [ ] Pre-mortem produced specific, plausible failure story
- [ ] Issues found were fixed

**Exit Gate:**

- [ ] All criteria passed
- [ ] Full report written to artifact location
- [ ] Chat summary contains P0/P1/P2 counts, fix count, and key changes only
- [ ] Chat does NOT contain full findings, iteration log, or coverage tracker

**Quick self-test:**

- If a P0 issue existed, would the user definitely see it in the summary?
- If the document had hidden flaws, did I genuinely try to find them?
- Are the fixes actually applied to the document, not just reported?

## Extension Points

**Domain-specific dimensions:**

- Security reviews: Add threat modeling dimensions (attack vectors, trust boundaries)
- API designs: Add consistency dimensions (naming conventions, error formats)
- Performance-critical: Add scale dimensions (bottlenecks, resource bounds)

**Framework handoffs:**

- If review finds document is fundamentally flawed → Recommend returning to brainstorming
- If review passes → Document ready for implementation or further refinement
- These are informational notes, not automated handoffs (workflow decisions are user's domain)

**Custom artifact locations:**

- Default: `docs/audits/YYYY-MM-DD-<document-name>-review.md`
- Projects can override via CLAUDE.md if different convention exists

**Stakes presets:**

- Projects can define default stakes in CLAUDE.md (e.g., "all document reviews are Rigorous minimum")
- User can still override per-review

**Integration with other skills:**

- **writing-clearly-and-concisely:** For narrative prose (blog posts, explanations, tutorials) — different skill, different purpose
- **making-recommendations:** May be invoked if review surfaces decision points requiring structured analysis
- **brainstorming:** If document needs fundamental rethinking, hand off to brainstorming rather than continuing to refine

## References

- [Dimension Catalog & Troubleshooting](references/dimensions-and-troubleshooting.md) — Full dimension definitions, additional anti-patterns, troubleshooting details
- [Framework for Thoroughness](references/framework-for-thoroughness.md) — Protocol specification for Yield%, stakes calibration, evidence levels
