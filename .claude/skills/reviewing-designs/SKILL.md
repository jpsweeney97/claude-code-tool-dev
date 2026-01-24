---
name: reviewing-designs
description: Use when verifying a design captures all requirements from sources. Use after creating specs from multiple documents. Use before implementing from a design. Use when past designs have led to implementation surprises.
---

# Reviewing Designs

## Overview

Design review catches issues before implementation, when they're cheap to fix. This skill unifies two concerns:

1. **Source coverage** — Does the design capture everything from source materials?
2. **Implementation readiness** — Can someone build from this without asking clarifying questions?

A single pass checking "is X mentioned?" misses decision rules, exit criteria, and safety defaults — single sentences with outsized impact. This skill uses the Framework for Thoroughness to iterate until findings converge.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness.md)
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

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | N | Issues that break correctness or execution |
| P1 | N | Issues that degrade quality |
| P2 | N | Polish items |

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

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High | Moderate | Low/none |

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

**Seed dimensions** (check all that apply to the target document):

**Source Coverage:**
- D1: Structural coverage — Are all source sections accounted for?
- D2: Semantic fidelity — Does meaning match, not just presence?
- D3: Procedural completeness — Are steps fully specified?

**Behavioral Completeness:**
- D4: Decision rules — What happens at decision points when uncertain?
- D5: Exit criteria — When is each phase considered "done"?
- D6: Safety defaults — What happens when things go wrong?

**Implementation Readiness:**
- D7: Clarity — Could someone implement without clarifying questions?
- D8: Completeness — Purpose, components, data flow, error handling, testing?
- D9: Feasibility — Do referenced dependencies exist? Are claims justified?
- D10: Edge cases — Empty inputs, boundaries, concurrency, failure modes?
- D11: Testability — Testing approach, verifiable success criteria?

**Consistency:**
- D12: Cross-validation — Do inputs/outputs/terminology agree throughout?

**Document Quality:**
- D13: Implicit concepts — Are all terms defined? (catches undefined jargon, assumed knowledge)
- D14: Precision — Is language precise? (catches vague wording, loopholes, wiggle room)
- D15: Examples — Is abstract guidance illustrated? (catches theory without concrete application)
- D16: Internal consistency — Do parts agree? (catches contradictions between sections)
- D17: Redundancy — Is anything said twice differently? (catches duplication that may drift)
- D18: Verifiability — Can compliance be verified? (catches unverifiable requirements)
- D19: Actionability — Is it clear what to do? (catches ambiguous instructions)

*Document Quality check order: D13-D15 (surface issues in single sections) → D16-D17 (cross-section comparison) → D18-D19 (holistic assessment)*

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
- Pre-mortem inversion ("This review would be worthless if ___")
- Historical pattern mining (what caused problems in similar designs?)

**Output:** Dimension list with priorities (P0/P1/P2)

#### EXPLORE: Check each dimension

For each dimension, record using Cell Schema:

| Field | Required | Values |
|-------|----------|--------|
| ID | Yes | D1, D2, ... F1, F2, ... |
| Status | Yes | `[x]` done, `[~]` partial, `[-]` N/A, `[ ]` not started, `[?]` unknown |
| Priority | Yes | P0 / P1 / P2 |
| Evidence | Yes | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes | High / Medium / Low |
| Artifacts | If applicable | File paths, quotes, line numbers |
| Notes | If applicable | What's missing, next action |

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

#### VERIFY: Check findings

**Cross-reference:** Do findings from different dimensions agree or contradict?

**Disconfirmation:** For each P0 dimension/finding, attempt to disprove it:

| Technique | Method |
|-----------|--------|
| Counterexample search | Find a case that breaks the current claim |
| Alternative hypothesis | What's another explanation? Test it. |
| Adversarial read | Could this evidence be misleading? |
| Negative test | What check would fail if the finding is wrong? |
| Cross-check | Verify via an independent method |

**Minimum disconfirmation by stakes:**
- Adequate: 1 technique per P0
- Rigorous: 2+ techniques per P0
- Exhaustive: 3+ techniques per P0

**Assumption check:** Which Entry Gate assumptions were validated? Invalidated?

**Gap scan:** Any `[ ]` or `[?]` items remaining?

**Output:** Verified findings with confidence levels

#### REFINE: Loop or exit?

**Calculate Yield%:**

Yield% measures how much new/revisionary information emerged this pass.

An entity *yields* if it is:
- New (didn't exist last pass)
- Reopened (resolved → unresolved)
- Revised (conclusion changed)
- Escalated (priority increased)

`Yield% = (yielding entities / total P0+P1 entities) × 100`

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

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if VERIFY found nothing.

This pass challenges the *design itself*, not just individual findings. Apply each lens with genuine adversarial intent — objections must cause discomfort if true.

| Lens | Question |
|------|----------|
| **Assumption Hunting** | What assumptions does the design make (explicit and implicit)? What if they're wrong? |
| **Scale Stress** | What breaks at 10x? 100x? Where are the bottlenecks? |
| **Competing Perspectives** | Security: attack vectors? Performance: slow spots? Maintainability: hard to change? Operations: hard to debug? |
| **Kill the Design** | What's the strongest argument against this? If it fails in production, what's the cause? |
| **Pre-mortem** | It's 6 months later, this failed catastrophically. What went wrong? What warnings were ignored? |
| **Steelman Alternatives** | What approaches were rejected? What would make them better than this design? |
| **Challenge the Framing** | Is this the right problem to solve? Are we addressing a symptom instead of root cause? |
| **Hidden Complexity** | Where is complexity underestimated? What looks simple but isn't? |
| **Motivated Reasoning** | Where might the design rationalize a preferred approach? Is there anchoring to an early idea? |

**Minimum depth by stakes:**
- Adequate: Apply 4 lenses; document key objections
- Rigorous: Apply all 9 lenses; document objections and responses
- Exhaustive: Apply all 9 lenses; document objections, responses, and residual risks

**Output:** Adversarial findings added to report, categorized separately from systematic findings

### Exit Gate

**Cannot claim "done" until ALL criteria pass:**

| Criterion | Check |
|-----------|-------|
| Coverage complete | No `[ ]` or `[?]`. All items are `[x]`, `[-]` (with rationale), or `[~]` (with documented gaps) |
| Evidence requirements met | P0 dimensions have required evidence level for stakes |
| Disconfirmation attempted | Techniques applied to P0s; documented what was tried and found |
| Assumptions resolved | Each verified, invalidated, or flagged as unverified |
| Convergence reached | Yield% below threshold for stakes level |
| Adversarial pass complete | All required lenses applied; objections documented |

**"No issues found" requires extra verification:**
- [ ] Convergence reached (Yield% below threshold)
- [ ] Disconfirmation genuinely attempted (not just claimed)
- [ ] Self-check: "Did I actually look, or did I assume the design was fine?"

**Produce output:**
1. Write full report to `docs/audits/YYYY-MM-DD-<design-name>-review.md`
2. Present brief summary in chat (P0/P1/P2 counts + key issues only)

## Decision Points

**Inputs unclear:**
- If target document not specified → Ask: "Which design document should I review?"
- If sources not specified but source comparison is relevant → Ask: "Are there source documents this design should capture?"
- If user says "just review it" → Proceed with Implementation Readiness and Document Quality dimensions only; note Source Coverage dimensions skipped

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

**Scenario:** Team created a design document for a new authentication system, derived from security requirements docs and API specifications.

### BAD: Single-pass checkbox review

Claude scans the document once, notes "has all the sections," checks that auth flows are mentioned, and reports: "Design looks complete. Ready for implementation."

**Why it's bad:**
- No Entry Gate — stakes not assessed, no stopping criteria
- Single pass — no iteration, no Yield% tracking
- Checked presence, not completeness — "auth flows mentioned" ≠ "auth flows fully specified"
- Skipped Behavioral Completeness — no check for decision rules, exit criteria, safety defaults
- No adversarial pass — didn't try to break the design
- No disconfirmation — accepted "looks good" without testing that conclusion
- Missed: Token refresh edge case undefined, error responses inconsistent with API spec, no rollback procedure for failed auth upgrades

### GOOD: Iterative review with framework

**Entry Gate:**
- Target: `docs/designs/auth-system.md`
- Sources: `docs/requirements/security.md`, `docs/specs/api-v2.md`
- Stakes: Rigorous (implementation follows; moderate undo cost)
- Stopping: Yield% <10%

**Pass 1:** DISCOVER dimensions, assign priorities
- D1-D3 (Source Coverage): P0 — must capture all security requirements
- D4-D6 (Behavioral Completeness): P0 — auth failures need clear handling
- D7-D11 (Implementation Readiness): P1
- D12-D19 (Consistency + Document Quality): P1

**Pass 1 EXPLORE:** Found 3 P0 gaps, 5 P1 issues. Yield% = 100% (first pass)

**Pass 2 EXPLORE:** Deeper check on D4-D6, found 2 more P0 gaps (token refresh undefined, no rollback procedure). Yield% = 25%

**Pass 3 EXPLORE:** Checked D13-D19 (Document Quality). Found 1 P1 issue (vague language in error handling). No new P0s. Yield% = 8%

**Adversarial Pass:**
- Pre-mortem: "Auth system fails in production because token refresh race condition wasn't specified" — added to findings
- Scale stress: "At 100x users, token validation becomes bottleneck" — noted as P1 concern

**Exit Gate:** Yield% <10%, all dimensions checked, disconfirmation attempted.

**Output:**
```
**Review complete:** auth-system.md
**Findings:** P0: 5 | P1: 7 | P2: 2
**Key issues:** Token refresh edge case undefined; no rollback for failed upgrades
**Full report:** `docs/audits/2024-01-15-auth-system-review.md`
```

**Why it's good:**
- Entry Gate established scope and stakes
- Iterative passes with Yield% tracking
- Checked completeness, not just presence
- All dimension categories covered with appropriate priority
- Adversarial pass found additional issue
- Clear output with P0 count prominent

## Anti-Patterns

**Pattern:** Single-pass "looks good" review
**Why it fails:** One pass catches obvious issues but misses behavioral gaps, edge cases, and document quality issues. "Looks good" without iteration is confirmation bias.
**Fix:** Iterate until Yield% below threshold. Pass 1 is always 100% yield — you can't exit after one pass.

**Pattern:** Checking presence instead of completeness
**Why it fails:** "The design mentions error handling" ≠ "Error handling is fully specified." Presence checks miss the gaps that cause implementation surprises.
**Fix:** For each dimension, ask "Is this COMPLETE?" not "Is this MENTIONED?"

**Pattern:** Skipping Document Quality dimensions
**Why it fails:** A design can have all the right content but be unclear, inconsistent, or unactionable. Implementation fails when developers can't understand what to build.
**Fix:** Document Quality (D13-D19) is mandatory. Cannot be skipped.

**Pattern:** Marking dimensions N/A without genuine justification
**Why it fails:** "D4-D6 N/A: seems straightforward" is rationalization. Behavioral Completeness issues are the most common source of implementation surprises.
**Fix:** Before any N/A, pass the skeptical reviewer test and self-check. If in doubt, check the dimension.

**Pattern:** Adversarial pass as checkbox
**Why it fails:** "Applied all 9 lenses, found nothing" without genuine adversarial intent is theater. The pass exists to find weaknesses, not to check a box.
**Fix:** Pre-mortem must produce a plausible failure story. If it doesn't feel uncomfortable, dig harder.

**Pattern:** Stopping because "taking too long"
**Why it fails:** Feeling like enough time passed isn't convergence. Issues don't care about your schedule.
**Fix:** Yield% is calculated, not felt. Continue until below threshold for stakes level.

**Pattern:** Fixing issues during review
**Why it fails:** Mixing review and remediation leads to incomplete review (stopped to fix) and incomplete fixes (didn't finish reviewing first).
**Fix:** Review finds and reports. Fixing is outside this skill's scope. Complete the review, then fix, then re-run if needed.

**Pattern:** Burying P0 findings in long report
**Why it fails:** User skims report, misses critical issue, implements with P0 gap.
**Fix:** Summary table with P0 count goes at top of report AND in chat summary. P0s must be unmissable.

## Troubleshooting

**Symptom:** Claude completes review in one pass, claims "no significant findings"
**Cause:** Skipped iteration; checked presence not completeness; confirmation bias
**Next steps:** Return to Entry Gate. Pass 1 is always 100% yield — cannot exit after one pass. Explicitly track Yield% and require it below threshold.

**Symptom:** Review finds nothing but implementation later reveals gaps
**Cause:** Dimensions skipped or checked superficially; disconfirmation not attempted
**Next steps:** Check which dimensions were marked N/A — were justifications valid? Was disconfirmation genuinely attempted for P0 dimensions? Learn from the gap and adjust dimension priorities for future reviews.

**Symptom:** Claude marked most dimensions as N/A
**Cause:** Rationalization to reduce effort; unclear about what dimensions mean
**Next steps:** Document Quality (D13-D19) and Cross-validation (D12) cannot be N/A. For others, verify justifications pass the skeptical reviewer test. If justifications are weak, re-check those dimensions.

**Symptom:** Yield% never drops below threshold
**Cause:** Scope too large; dimensions too broad; or genuinely complex design with many issues
**Next steps:** Check if scope is bounded appropriately. If design genuinely has many issues, that's a valid finding — report it. Consider: "Design may need fundamental revision before detailed review is valuable."

**Symptom:** Adversarial pass finds nothing
**Cause:** Either design is solid, or adversarial pass wasn't genuinely adversarial
**Next steps:** Try harder to kill the design. Apply pre-mortem seriously — write a specific failure story. If still nothing after genuine effort, accept the finding but document what was tried.

**Symptom:** User wants to skip Entry Gate or Adversarial Pass
**Cause:** Time pressure; perceived overhead
**Next steps:** Acknowledge the pressure. Explain: "Skipping Entry Gate means no stopping criteria — review could be endless or premature. Skipping Adversarial Pass misses design-level flaws." Complete minimum requirements for stakes level.

**Symptom:** Review produces 50+ findings, feels overwhelming
**Cause:** Design may have fundamental issues; or findings not prioritized effectively
**Next steps:** Check P0/P1/P2 distribution. If mostly P0, design needs significant work — say so clearly. If mostly P1/P2, focus report on P0s and note "N additional lower-priority findings in full report."

**Symptom:** Same issues found on re-review after user claimed to fix them
**Cause:** Fixes were incomplete or introduced new issues
**Next steps:** This is valuable signal — note which issues recurred. Consider: Are fix instructions unclear? Is the design fundamentally hard to get right? Report pattern, not just recurrence.

## Verification

After completing a review, verify:

**Entry Gate:**
- [ ] Inputs identified (target document, source documents if applicable)
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

**VERIFY:**
- [ ] Disconfirmation attempted for P0 dimensions (techniques documented)
- [ ] Assumptions resolved (verified, invalidated, or flagged unverified)

**REFINE:**
- [ ] Yield% calculated for each pass
- [ ] Iteration log shows pass-by-pass changes
- [ ] Convergence reached (Yield% below threshold)

**Adversarial Pass:**
- [ ] Required lenses applied for stakes level (Rigorous: all 9)
- [ ] Objections documented with responses or accepted risks
- [ ] Pre-mortem produced specific, plausible failure story

**Exit Gate:**
- [ ] All criteria passed
- [ ] Full report written to artifact location
- [ ] Chat summary contains P0/P1/P2 counts and key issues only
- [ ] Chat does NOT contain full findings, iteration log, or coverage tracker

**Quick self-test:**
- If a P0 issue exists, would the user definitely see it in the summary?
- If the design had hidden flaws, did I genuinely try to find them?

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
