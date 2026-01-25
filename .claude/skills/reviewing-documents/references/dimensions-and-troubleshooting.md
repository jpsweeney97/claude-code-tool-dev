# Dimensions & Troubleshooting Reference

Supporting reference for the [reviewing-documents](../SKILL.md) skill.

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
**Why it fails:** "The spec mentions error handling" ≠ "Error handling is fully specified." Presence checks miss the gaps that cause implementation surprises.
**Fix:** For each dimension, ask "Is this COMPLETE?" not "Is this MENTIONED?"

**Pattern:** "Document is already good"
**Why it fails:** Rationalizes skipping review entirely. Every document benefits from systematic review.
**Fix:** Run the process. Even clean documents benefit from adversarial thinking.

**Pattern:** "Just a minor update"
**Why it fails:** Exempts small changes that compound. Minor changes can introduce inconsistencies.
**Fix:** At minimum, run Document Quality dimensions (D13-D19) and Cross-validation (D12).

**Pattern:** Skipping Document Quality dimensions
**Why it fails:** A document can have all the right content but be unclear, inconsistent, or unactionable. Implementation fails when developers can't understand what to build.
**Fix:** Document Quality (D13-D19) is mandatory. Cannot be skipped.

**Pattern:** Marking dimensions N/A without genuine justification
**Why it fails:** "D4-D6 N/A: seems straightforward" is rationalization. Behavioral Completeness issues are the most common source of implementation surprises.
**Fix:** Before any N/A, pass the skeptical reviewer test and self-check. If in doubt, check the dimension.

**Pattern:** Adversarial pass as checkbox
**Why it fails:** "Applied all 9 lenses, found nothing" without genuine adversarial intent is theater. The pass exists to find weaknesses, not to check a box.
**Fix:** Pre-mortem must produce a plausible failure story. If it doesn't feel uncomfortable, dig harder.

**Pattern:** Surface-level passes
**Why it fails:** Checkbox compliance without genuine examination.
**Fix:** Each pass must produce either issues or an explicit "No issues found" with evidence of examination.

**Pattern:** Stopping because "taking too long"
**Why it fails:** Feeling like enough time passed isn't convergence. Issues don't care about your schedule.
**Fix:** Yield% is calculated, not felt. Continue until below threshold for stakes level.

**Pattern:** Fixing without diagnosing
**Why it fails:** Jumps to edits, skips the diagnostic phase. Risks fixing symptoms instead of causes.
**Fix:** Complete EXPLORE and VERIFY for each pass before applying fixes. The diagnosis creates accountability and catches root causes.

**Pattern:** Stopping after one clean pass
**Why it fails:** One pass might miss issues; doesn't confirm stability.
**Fix:** Convergence requires Yield% below threshold. One clean pass after multiple finding passes is expected.

**Pattern:** Burying P0 findings in long report
**Why it fails:** User skims report, misses critical issue, implements with P0 gap.
**Fix:** Summary table with P0 count goes at top of report AND in chat summary. P0s must be unmissable.

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

**Symptom:** All lenses return "no issues" on first pass
**Cause:** Either document is genuinely clean, or passes were too shallow
**Next steps:** For the first occurrence, trust the result but run a second full pass to confirm stability. If second pass also clean → proceed to adversarial pass. If doubt remains, apply D14 (Precision) more aggressively.

**Symptom:** Yield% never drops below threshold
**Cause:** Scope too large; dimensions too broad; or genuinely complex document with many issues
**Next steps:** Check if scope is bounded appropriately. If document genuinely has many issues, that's a valid finding — report it. Consider: "Document may need fundamental revision before detailed review is valuable."

**Symptom:** Adversarial pass finds nothing
**Cause:** Either document is solid, or adversarial pass wasn't genuinely adversarial
**Next steps:** Try harder to kill the document. Apply pre-mortem seriously — write a specific failure story. If still nothing after genuine effort, accept the finding but document what was tried.

**Symptom:** User wants to skip Entry Gate or Adversarial Pass
**Cause:** Time pressure; perceived overhead
**Next steps:** Acknowledge the pressure. Explain: "Skipping Entry Gate means no stopping criteria — review could be endless or premature. Skipping Adversarial Pass misses design-level flaws." Complete minimum requirements for stakes level.

**Symptom:** Review produces 50+ findings, feels overwhelming
**Cause:** Document may have fundamental issues; or findings not prioritized effectively
**Next steps:** Check P0/P1/P2 distribution. If mostly P0, document needs significant work — say so clearly. If mostly P1/P2, focus report on P0s and note "N additional lower-priority findings in full report."

**Symptom:** Refinement feels endless (many passes, still finding issues)
**Cause:** Document has fundamental clarity problems, not surface issues
**Next steps:** Stop after iteration cap (5/7/10 passes by stakes). Report: "Document may need restructuring rather than refinement. Found [N] issues across [M] passes. Recommend addressing root causes."

**Symptom:** Same issues found on re-review after user claimed to fix them
**Cause:** Fixes were incomplete or introduced new issues
**Next steps:** This is valuable signal — note which issues recurred. Consider: Are fix instructions unclear? Is the document fundamentally hard to get right? Report pattern, not just recurrence.

**Symptom:** Fixes introduce new issues
**Cause:** Edits created new inconsistencies or unclear language
**Next steps:** This is why convergence requires post-fix passes. The loop is working correctly. Continue until stable or iteration cap reached.

**Symptom:** User pushes back on reported issues
**Cause:** Issue may be intentional, or context was missing
**Next steps:** Don't defend — explore. "Is this intentional? If so, I'll mark it as accepted." Update report to distinguish issues from accepted deviations.
