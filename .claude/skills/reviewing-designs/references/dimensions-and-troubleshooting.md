# Dimensions & Troubleshooting Reference

Supporting reference for the [reviewing-designs](../SKILL.md) skill.

## How to Use This File

- **During DISCOVER:** Consult the Dimension Catalog to identify what to check
- **When something goes wrong:** Consult Anti-Patterns and Troubleshooting
- **Core process lives in SKILL.md** — this file is lookup reference only

---

## Dimension Catalog

### Source Coverage

- **D1: Structural coverage** — Are all source sections accounted for?
- **D2: Semantic fidelity** — Does meaning match, not just presence?
- **D3: Procedural completeness** — Are steps fully specified?

### Behavioral Completeness

- **D4: Decision rules** — What happens at decision points when uncertain?
- **D5: Exit criteria** — When is each phase considered "done"?
- **D6: Safety defaults** — What happens when things go wrong?

### Implementation Readiness

- **D7: Clarity** — Could someone implement without clarifying questions?
- **D8: Completeness** — Purpose, components, data flow, error handling, testing?
- **D9: Feasibility** — Do referenced dependencies exist? Are claims justified?
- **D10: Edge cases** — Empty inputs, boundaries, concurrency, failure modes?
- **D11: Testability** — Testing approach, verifiable success criteria?

### Consistency

- **D12: Cross-validation** — Do inputs/outputs/terminology agree throughout?

### Document Quality

- **D13: Implicit concepts** — Are all terms defined? (catches undefined jargon, assumed knowledge)
- **D14: Precision** — Is language precise? (catches vague wording, loopholes, wiggle room)
- **D15: Examples** — Is abstract guidance illustrated? (catches theory without concrete application)
- **D16: Internal consistency** — Do parts agree? (catches contradictions between sections)
- **D17: Redundancy** — Is anything said twice differently? (catches duplication that may drift)
- **D18: Verifiability** — Can compliance be verified? (catches unverifiable requirements)
- **D19: Actionability** — Is it clear what to do? (catches ambiguous instructions)

**Check order for Document Quality:** D13-D15 (surface issues in single sections) → D16-D17 (cross-section comparison) → D18-D19 (holistic assessment)

---

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

**Pattern:** Early gate as checkbox
**Why it fails:** Producing formulaic hypotheses ("what if it doesn't scale?") that technically satisfy hard-fail rules but lack genuine adversarial intent. Same theater problem as "adversarial pass as checkbox."
**Fix:** Q3 must name specific mechanisms, not categories. Q5 must state what breaks. Generic answers fail hard-fail rules. If hypotheses feel formulaic, re-engage with genuine adversarial intent.

---

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

---

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
