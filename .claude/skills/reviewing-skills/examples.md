# Examples

Worked examples demonstrating the reviewing-skills process.

## Example 1: Reviewing a draft skill

**Scenario:** Review a draft skill for handling API rate limits.

### BAD: Single-pass "looks fine" review

Claude scans the skill once, notes "has Overview, Process, Examples," and reports: "Skill looks complete. Ready for testing."

**Why it's bad:**

- No Entry Gate — stakes not assessed, no stopping criteria
- Single pass — no iteration, no Yield% tracking
- Checked presence, not quality — "has Process" ≠ "Process is complete and actionable"
- Skipped compliance strength — didn't check for rationalization counters
- No adversarial pass — didn't try to find ways an agent could ignore the skill
- No disconfirmation — accepted "looks fine" without testing that conclusion
- Missed: Description summarizes workflow (triggers bypass), decision points undefined for edge cases, no "When NOT to Use" section

### GOOD: Iterative review with fixes applied

**Entry Gate:**

- Target: `.claude/skills/handling-rate-limits/SKILL.md`
- Supporting files: `retry-strategies.md` (linked from SKILL.md)
- Stakes: Rigorous (skill will guide production behavior)
- Stopping: Yield% <10%

**Pass 1:** DISCOVER dimensions, assign priorities

Findings (format: `Dimension: finding priority — description`):

- D1 (Trigger clarity): P0 — description says "manages rate limit responses" (summarizes workflow)
- D3 (Structural conformance): P0 — missing "When NOT to Use" section
- D4 (Compliance strength): P1 — no rationalization table

Yield% = 100% (first pass)

**Pass 1 FIX:** Rewrote description to trigger-only, added When NOT to Use section.

**Pass 2:** Deeper check on remaining dimensions

- D2 (Process completeness): P1 — retry logic defined but backoff ceiling undefined
- D5 (Precision): P1 — "wait appropriate amount" is vague
- D9 (Reference validity): P2 — link to retry-strategies.md works but file has stale example

Yield% = 3 new P0/P1 findings / 5 total P0/P1 entities = 60%

**Pass 2 FIX:** Defined backoff ceiling, replaced "appropriate amount" with specific formula, updated stale example.

**Pass 3:** Final dimension sweep

- D4 (Compliance strength): P1 — revised: added stronger "YOU MUST" for backoff
- D10 (Edge cases): P2 — what if rate limit is permanent (banned)?
- Added edge case handling

Yield% = 1 revised P1 finding / 6 total P0/P1 entities = 17%

**Pass 4:** Convergence check

- No new issues, no revisions
- Yield% = 0%

**Adversarial Pass:**

- Compliance Prediction: "Under time pressure, agent might skip backoff" → Added explicit: "YOU MUST wait the full backoff period. No shortcuts."
- Trigger Ambiguity: "Could fire for non-rate-limit errors" → Tightened description to specify HTTP 429 only
- Author Blindness: "Assumes reader knows exponential backoff" → Added brief explanation

**Exit Gate:** Yield% <10%, all dimensions checked, 8 fixes applied.

**Output:**

```
**Review complete:** handling-rate-limits
**Findings:** P0: 2 | P1: 4 | P2: 2 (8 fixed)
**Key changes:** Rewrote description to trigger-only; added backoff ceiling and compliance language
**Full report:** `docs/audits/2024-01-15-handling-rate-limits-review.md`
```

**Why it's good:**

- Entry Gate established scope and stakes
- Iterative passes with Yield% tracking
- Checked quality, not just presence
- All dimensions covered with appropriate priority
- Fixes applied after each pass
- Adversarial pass strengthened compliance language
- Clear output with fix count and key changes

## Example 2: Auditing an existing production skill

**Scenario:** The `writing-tests` skill exists but agents frequently skip the "run tests before claiming done" step.

**Entry Gate:**

- Target: `~/.claude/skills/writing-tests/SKILL.md`
- Context: Behavioral compliance issue reported
- Stakes: Rigorous

**Key findings:**

| Dimension | Finding | Priority |
|-----------|---------|----------|
| D4 (Compliance strength) | "Run tests" instruction uses weak language ("should run") | P0 |
| D4 (Compliance strength) | No rationalization table for "tests take too long" excuse | P1 |
| D1 (Trigger clarity) | Description overlaps with `debugging-code` skill | P1 |

**Fixes applied:**

- Changed "should run tests" → "YOU MUST run tests and see them pass"
- Added rationalization table entry: "Tests take too long" → "Skipped tests waste more time debugging. Run them."
- Tightened description to distinguish from debugging-code

**Output:**

```
**Review complete:** writing-tests
**Findings:** P0: 1 | P1: 2 | P2: 0 (3 fixed)
**Key changes:** Strengthened compliance language; added rationalization counter
**Full report:** `docs/audits/2024-02-01-writing-tests-review.md`
```

**Why this matters:** The behavioral issue (agents skipping tests) traced back to weak compliance language — a document quality issue that review catches and testing wouldn't.
