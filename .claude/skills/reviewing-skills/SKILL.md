---
name: reviewing-skills
description: Use after brainstorming-skills produces a draft. Use when auditing existing skills for quality drift. Use when agents don't follow a skill reliably. Use when asked to "review," "audit," or "improve" a skill.
---

# Reviewing Skills

## Overview

Skills fail silently: vague triggers cause misfires, weak compliance language gets rationalized around, missing sections leave gaps that testing catches too late. Document quality issues compound — a slightly unclear instruction becomes agent confusion becomes user frustration.

This skill reviews SKILL.md files and their references/ directories for structural quality, clarity, and compliance strength. It catches issues before behavioral testing (testing-skills), when fixes are cheap.

**What this skill can do:**
- Assess document quality (clarity, precision, completeness)
- Predict compliance strength (rationalization resistance, not actual behavior)
- Validate internal references (references/ exists, links work, content aligns with SKILL.md)
- Cross-check external sources (if skill claims to implement a spec or follow official docs, verify alignment)
- Escalate when issues are too fundamental to fix in place

**What this skill cannot do:**
- Verify agents actually follow the skill (that's testing-skills)
- Validate domain expertise (can check consistency with sources, not whether sources are correct)
- Rewrite fundamentally broken skills (recommend brainstorming-skills instead)

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness.md)
**Default thoroughness:** Rigorous

**Outputs:**
- Refined skill with fixes applied
- Review report at `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
- Brief summary in chat

## When to Use

- After brainstorming-skills produces a draft SKILL.md
- Before testing-skills validates behavioral effectiveness
- When auditing existing production skills for quality drift
- When a skill exists but agents don't follow it reliably (suggests clarity or compliance issues)
- When asked to "review," "audit," or "improve" a skill
- When merging or refactoring multiple skills
- When skill references seem outdated or broken
- Before promoting a skill from development to production

## When NOT to Use

- **No skill exists yet** — use brainstorming-skills first
- **Behavioral validation needed** — use testing-skills (this skill checks document quality, not agent behavior)
- **Code review** — use code review skills; this is for skill documentation
- **Non-skill documents** — use reviewing-documents for specs, designs, frameworks
- **Quick typo fix** — just fix it; full review is overkill for trivial edits

## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifacts:**

| Artifact | Location |
|----------|----------|
| Refined skill | Original location (edits applied in place) |
| Refined references | Original locations in references/ (edits applied in place) |
| Review report | `docs/audits/YYYY-MM-DD-<skill-name>-review.md` |

**Review report includes:**

- Entry Gate (assumptions, stakes, stopping criteria)
- Coverage Tracker (dimensions with Cell Schema: ID, Status, Priority, Evidence, Confidence)
- Iteration Log (pass-by-pass Yield%)
- Findings grouped by dimension category
- Fixes Applied (what changed, where)
- Disconfirmation Attempts
- Exit Gate verification

**Summary table (top of report and in chat):**

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | N | Issues that break correctness or execution |
| P1 | N | Issues that degrade quality |
| P2 | N | Polish items |

**Chat summary (brief — not the full report):**

```
**Review complete:** <skill-name>
**Findings:** P0: N | P1: N | P2: N (N fixed)
**Key changes:** [1-2 most significant fixes]
**Full report:** `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
```

**Do NOT include in chat:** Full findings list, iteration log, coverage tracker, disconfirmation details, complete list of fixes.

**Definition of Done:**

- [ ] Entry Gate completed and recorded
- [ ] All dimensions explored with Evidence/Confidence ratings
- [ ] Yield% below threshold for thoroughness level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed
- [ ] Fixes applied to skill and references
- [ ] Exit Gate criteria satisfied
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify inputs:**

- Target skill (SKILL.md path)
- References directory (if exists)
- External sources (official docs, specs the skill claims to implement), if applicable
- User-specified concerns, if any

If inputs are unclear, ask. Accept paths or skill names.

**2. Inventory the skill:**

- Read SKILL.md
- List all files in references/ (if exists)
- Note any external sources referenced

**3. Surface assumptions:**

List what you're taking for granted:

- Skill is the current version
- Referenced files are complete and authoritative
- [Any context-specific assumptions]

**4. Calibrate stakes:**

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High | Moderate | Low/none |

**Default: Rigorous.** Override if user specifies or factors clearly indicate otherwise.

**5. Select stopping criteria:**

- **Primary:** Yield-based (Yield% below threshold)
- **Thresholds:** Adequate <20%, Rigorous <10%, Exhaustive <5%

**6. Record Entry Gate:**

Document assumptions, stakes level, scope, and stopping criteria before proceeding.

### Dimension Catalog

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D1 | Trigger clarity | P0 | Vague or overlapping descriptions that cause misfires or missed activations |
| D2 | Process completeness | P0 | Missing steps, undefined decision points, unclear exit criteria |
| D3 | Structural conformance | P0 | Missing required sections, wrong frontmatter, exceeds size limits |
| D4 | Compliance strength | P1 | Weak language, missing rationalization counters, no red flags |
| D5 | Precision | P1 | Vague wording, loopholes, wiggle room |
| D6 | Actionability | P1 | Instructions clear in theory but ambiguous in practice |
| D7 | Internal consistency | P1 | Contradictions between sections, terminology drift |
| D8 | Scope boundaries | P1 | Missing "When NOT to Use", unclear exclusions |
| D9 | Reference validity | P2 | Broken links, outdated references, missing assets |
| D10 | Edge cases | P2 | Boundary situations undefined |
| D11 | Feasibility | P2 | Requirements that can't be achieved |
| D12 | Testability | P2 | Requirements that can't be verified |

**Conditional dimension:**

| ID | Dimension | Priority | When to check |
|----|-----------|----------|---------------|
| D13 | Integration clarity | P1 | Orchestration-type skills only — unclear handoffs to/from other skills |

**Dimension applicability:**

- **D1-D8:** Always check (cannot skip)
- **D9-D12:** Always check, but lower priority
- **D13:** Only for orchestration skills (mark N/A otherwise)

**Before marking any dimension N/A:**

1. State specific reason (not "doesn't apply" but WHY)
2. Test: "Would a skeptical reviewer accept this justification?"
3. Self-check: "If this dimension revealed issues, would I be surprised?"

If #2 is "maybe not" or #3 is "no" → check the dimension anyway.

**For detailed checking guidance per dimension, see [Dimension Definitions](references/dimension-definitions.md).**

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

**Seed dimensions:** Start with D1-D12 from the catalog (D13 if orchestration skill).

**Assign priorities:** Use catalog defaults, adjust if context warrants.

**Expand dimensions:** Apply ≥3 DISCOVER techniques:

- **Skill-specific patterns:** What quality issues are common for this skill type?
- **Reference scan:** Do references introduce dimensions not in the catalog?
- **Pre-mortem:** "This review would be worthless if I missed..."
- **Historical patterns:** What caused problems in similar skills?

**Output:** Dimension list with priorities (P0/P1/P2)

#### EXPLORE: Check each dimension

For each dimension, record using Cell Schema:

| Field | Required | Values |
|-------|----------|--------|
| ID | Yes | D1, D2, ... |
| Status | Yes | `[x]` done, `[~]` partial, `[-]` N/A, `[ ]` not started, `[?]` unknown |
| Priority | Yes | P0 / P1 / P2 |
| Evidence | Yes | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes | High / Medium / Low |
| Artifacts | If applicable | File paths, quotes, line numbers |
| Notes | If applicable | What's missing, proposed fix |

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

**For each finding:**

- Link to dimension(s) it relates to
- Assign priority based on impact
- Rate evidence and confidence
- Note artifacts (quotes, line references)
- Draft proposed fix

#### VERIFY: Check findings

**Cross-reference:** Do findings from different dimensions agree or contradict?

**Disconfirmation:** For each P0 dimension/finding, attempt to disprove it:

| Technique | Method |
|-----------|--------|
| Counterexample search | Find a case where the "issue" isn't actually a problem |
| Alternative interpretation | Could this wording be intentional? |
| Adversarial read | Am I being too strict? |
| Context check | Does project CLAUDE.md or other context justify this? |

**Minimum disconfirmation by stakes:**

- Adequate: 1 technique per P0
- Rigorous: 2+ techniques per P0
- Exhaustive: 3+ techniques per P0

**Assumption check:** Which Entry Gate assumptions were validated? Invalidated?

**Gap scan:** Any `[ ]` or `[?]` items remaining?

**Output:** Verified findings with confidence levels and proposed fixes

#### FIX: Apply corrections

For each verified finding:

1. Apply the fix to the skill or reference file
2. Note what changed (original → revised)
3. Mark finding as fixed in the coverage tracker

**Fix order:** P0 issues first, then P1, then P2.

**Conflict detection:** If fixing one issue contradicts another fix:

1. Note the conflict
2. Determine priority (higher-priority finding wins)
3. Document the trade-off in the review report

**Do not fix:**

- Issues marked as "accepted deviation" by user
- Issues outside skill's scope (flag for separate work)
- Issues requiring user decision (flag and ask)

#### REFINE: Loop or exit?

**Calculate Yield%:**

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
- Fixes introduced new issues
- Yield% above threshold

**Exit to Adversarial Pass when:**

- No new dimensions in last pass
- No significant revisions
- All items resolved
- Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

**Iteration cap (failsafe):** If convergence not reached after 5 passes (Adequate), 7 passes (Rigorous), or 10 passes (Exhaustive), exit with finding: "Skill may need fundamental revision — review did not converge."

### Reviewing References

For each file in references/:

**Existence and linkage:**
- [ ] File exists at the linked path
- [ ] Link syntax is correct (relative path from SKILL.md)
- [ ] No orphaned files (files that exist but aren't linked)

**Quality (apply relevant dimensions):**
- D5 (Precision): Is language precise?
- D6 (Actionability): Are instructions clear?
- D7 (Internal consistency): Does it use same terminology as SKILL.md?

**Coherence with SKILL.md:**
- [ ] Reference supports claims made in SKILL.md
- [ ] No contradictions between SKILL.md and reference
- [ ] Reference doesn't introduce requirements not mentioned in SKILL.md
- [ ] Terminology matches (no drift)

**Reference-specific checks:**
- TOC present if >100 lines?
- Examples concrete, not abstract?
- Outdated information (dates, versions, deprecated features)?

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if the review loop found nothing.

This pass challenges the *skill itself*, not individual findings. Apply each lens with genuine adversarial intent.

| Lens | Question |
|------|----------|
| **Compliance Prediction** | Would an agent under pressure follow this skill? Where would they rationalize around it? |
| **Trigger Ambiguity** | Could this trigger fire when it shouldn't? Could it fail to fire when it should? What overlaps with other skills? |
| **Missing Guardrails** | What's the worst an agent could do while technically following this skill? |
| **Complexity Creep** | Is this skill trying to do too much? Would two simpler skills work better? |
| **Stale Assumptions** | What context assumptions might become false? What if dependencies change? |
| **Implementation Gap** | Could someone follow every instruction and still produce bad output? |
| **Author Blindness** | What does the author know that isn't written down? What's "obvious" to them but not to an agent? |

**Minimum depth by stakes:**

- Adequate: Apply 4 lenses; document key objections; fix issues found
- Rigorous: Apply all 7 lenses; document objections and responses; fix issues found
- Exhaustive: Apply all 7 lenses; document objections, responses, and residual risks; fix issues found

**Output:** Adversarial findings added to report, categorized separately. Fixes applied to skill.

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
| Fixes applied | All P0 and P1 findings fixed (or explicitly accepted by user) |

**"No issues found" requires extra verification:**

- [ ] Convergence reached (Yield% below threshold)
- [ ] Disconfirmation genuinely attempted (not just claimed)
- [ ] Self-check: "Did I actually look, or did I assume the skill was fine?"

**Escalation trigger:**

If P0 findings exceed 5, or if the skill has fundamental structural problems:

> "Skill needs fundamental rethinking — recommend returning to brainstorming-skills rather than continuing to patch."

**Produce output:**

1. Write full report to `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
2. Present brief summary in chat (P0/P1/P2 counts, fixes applied, key changes only)

## Decision Points

**Inputs unclear:**

- If skill path not specified → Ask: "Which skill should I review?"
- If references/ exists but not inventoried → Inventory it automatically
- If user says "just review it" → Proceed with all dimensions; note any scope assumptions

**Stakes disagreement:**

- If factors split across columns → Choose the higher level
- If user specifies a level → User's choice wins; document rationale in Entry Gate

**Dimension not applicable:**

- Mark as `[-]` with brief rationale
- D1-D8 cannot be marked N/A (core quality dimensions)
- D13 (Integration clarity) is N/A for non-orchestration skills

**P0 issue found during EXPLORE:**

- Draft the fix immediately
- Continue review (don't stop to apply fixes mid-pass)
- Complete remaining dimensions before applying fixes

**Yield% ambiguous:**

- If unsure whether a change "counts" as revision → Count it (bias toward more iteration)
- If Yield% hovers near threshold → Run one more pass to confirm

**Fixes conflict:**

- Higher-priority finding wins
- Document the trade-off
- If fixes keep oscillating → Exit with: "Skill may need structural revision"

**Adversarial pass finds fundamental flaw:**

- Add as P0 finding
- Apply fix if possible
- If too fundamental → Recommend brainstorming-skills rather than patching

**Reviewing your own work:**

- Proceed, but note in Entry Gate: "Author self-review — heightened disconfirmation recommended"
- Apply extra adversarial scrutiny (Author Blindness lens is critical)
- Consider: "What would I miss because I already know what I meant?"

**Skill references external source:**

- If source accessible → Cross-check alignment
- If source inaccessible → Note as assumption: "External source not verified"
- If skill claims to implement a spec → Verify key requirements are addressed

**Many issues found (>10):**

- Check P0/P1/P2 distribution
- If mostly P0 → Skill needs significant work; say so clearly
- If mostly P1/P2 → Focus summary on P0s; note "N additional lower-priority findings"

**User pushes back on findings:**

- Don't defend — explore: "Is this intentional? If so, I'll mark it as accepted."
- Update report to distinguish issues from accepted deviations

**User pressure to skip steps:**

- Acknowledge the pressure
- "Skipping [Entry Gate/Adversarial Pass/etc.] risks missing issues that surface during testing."
- Complete minimum requirements for stakes level
- Compress output, not process

## Examples

### Example 1: Reviewing a draft skill

**Scenario:** Review a draft skill for handling API rate limits.

#### BAD: Single-pass "looks fine" review

Claude scans the skill once, notes "has Overview, Process, Examples," and reports: "Skill looks complete. Ready for testing."

**Why it's bad:**

- No Entry Gate — stakes not assessed, no stopping criteria
- Single pass — no iteration, no Yield% tracking
- Checked presence, not quality — "has Process" ≠ "Process is complete and actionable"
- Skipped compliance strength — didn't check for rationalization counters
- No adversarial pass — didn't try to find ways an agent could ignore the skill
- No disconfirmation — accepted "looks fine" without testing that conclusion
- Missed: Description summarizes workflow (triggers bypass), decision points undefined for edge cases, no "When NOT to Use" section

#### GOOD: Iterative review with fixes applied

**Entry Gate:**

- Target: `.claude/skills/handling-rate-limits/SKILL.md`
- References: `references/retry-strategies.md` (exists)
- Stakes: Rigorous (skill will guide production behavior)
- Stopping: Yield% <10%

**Pass 1:** DISCOVER dimensions, assign priorities

- D1 (Trigger clarity): P0 — description says "manages rate limit responses" (summarizes workflow)
- D3 (Structural conformance): P0 — missing "When NOT to Use" section
- D4 (Compliance strength): P1 — no rationalization table

Yield% = 100% (first pass)

**Pass 1 FIX:** Rewrote description to trigger-only, added When NOT to Use section.

**Pass 2:** Deeper check on remaining dimensions

- D2 (Process completeness): P1 — retry logic defined but backoff ceiling undefined
- D5 (Precision): P1 — "wait appropriate amount" is vague
- D9 (Reference validity): P2 — link to retry-strategies.md works but file has stale example

Yield% = 3/5 = 60%

**Pass 2 FIX:** Defined backoff ceiling, replaced "appropriate amount" with specific formula, updated stale example.

**Pass 3:** Final dimension sweep

- No new P0/P1 issues
- D10 (Edge cases): P2 — what if rate limit is permanent (banned)?
- Added edge case handling

Yield% = 1/6 = 17%

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

### Example 2: Auditing an existing production skill

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

## Anti-Patterns

### Single-pass "looks complete" review

Scanning once, checking that sections exist, and declaring "ready for testing."

**Why it fails:** Pass 1 is always 100% yield. Presence ≠ quality. Vague wording, missing edge cases, and weak compliance language hide in plain sight.

**Fix:** Iterate until Yield% below threshold. Check quality of content, not just existence of sections.

### Checking presence instead of quality

"Process section exists" → "Process is complete"

**Why it fails:** A Process section can exist and still have undefined decision points, missing steps, or vague instructions.

**Fix:** For each section, ask: "Is this COMPLETE and ACTIONABLE?" not "Does this EXIST?"

### Skipping compliance strength for "reference" skills

"This skill just provides information, it doesn't need compliance language."

**Why it fails:** Even reference skills need agents to actually use them. Without compliance mechanisms, agents rationalize: "I already know this" or "I'll check later."

**Fix:** Every skill needs some compliance strength. Reference skills need at least: clear triggers, explicit "check this before X" instructions.

### Reviewing your own work uncritically

"I wrote it, I know what it means."

**Why it fails:** Author blindness. What's "obvious" to you isn't written down. You read what you meant, not what you wrote.

**Fix:** Note self-review in Entry Gate. Apply Author Blindness lens aggressively. Ask: "What would someone who doesn't share my context misunderstand?"

### Deferring quality to testing-skills

"Testing will catch any issues."

**Why it fails:** Testing validates behavior, not document quality. A skill can pass behavioral tests while having vague triggers, missing sections, or weak compliance that will cause problems later.

**Fix:** Review catches document issues; testing catches behavioral issues. Both are needed.

### Accepting "no issues found" without disconfirmation

First pass found nothing → "Skill is perfect."

**Why it fails:** Finding nothing might mean the skill is good, or it might mean you didn't look hard enough.

**Fix:** "No issues" requires explicit disconfirmation. What did you check? What techniques did you apply? Document the absence of findings, not just the absence of a search.

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "The skill is simple enough" | Simple skills still have quality gaps. 15 minutes reviewing saves hours debugging. |
| "I just wrote it, I know what it says" | Author blindness is real. You read what you meant, not what you wrote. |
| "Testing will catch any issues" | Testing catches behavioral issues. Review catches document quality issues. Both needed. |
| "This is just a quick fix" | Quick fixes accumulate into quality drift. Review the change, not just the original. |
| "No time for full review" | Deploying unreviewed skills wastes more time fixing them later. Compress output, not process. |

**All of these mean: Complete the review. No exceptions.**

## Troubleshooting

**Symptom:** Review completed in one pass
**Cause:** Pass 1 is always 100% yield — cannot exit after one pass
**Next steps:** Run at least one more pass. If truly no new findings, Yield% will drop below threshold naturally.

**Symptom:** Most dimensions marked N/A
**Cause:** Over-aggressive skipping. D1-D8 cannot be N/A.
**Next steps:** Revisit N/A justifications. Apply the skeptical reviewer test: "Would someone else accept this rationale?"

**Symptom:** "No issues found" but skill feels off
**Cause:** Checking presence instead of quality, or insufficient disconfirmation
**Next steps:** Re-run with explicit quality questions per dimension. Apply Adversarial Pass lenses even if loop found nothing.

**Symptom:** Fixes keep conflicting with each other
**Cause:** Skill has structural problems that can't be resolved with targeted edits
**Next steps:** Escalate: "Skill may need fundamental rethinking — recommend brainstorming-skills."

**Symptom:** Review found issues but agent still doesn't follow the skill
**Cause:** Document quality ≠ behavioral effectiveness. Review checks the document; testing checks agent behavior.
**Next steps:** After review fixes are applied, use testing-skills to validate behavioral compliance.

**Symptom:** Yield% stays high across many passes
**Cause:** Each fix introduces new issues, or scope is expanding
**Next steps:** Check if fixes are causing new problems. Consider whether skill is trying to do too much. Hit iteration cap if necessary and note "did not converge."

**Symptom:** Unsure whether finding is real issue or acceptable variation
**Cause:** Ambiguous quality criteria
**Next steps:** Apply disconfirmation. If still ambiguous, note as P2 with "possible issue" and let user decide.

**Symptom:** References directory has many files, review is taking too long
**Cause:** Review scope may be too broad for stakes level
**Next steps:** For Adequate stakes, focus on SKILL.md and spot-check references. For Rigorous+, review all references but prioritize those linked from critical sections.

## Verification

After completing a review, verify:

**Entry Gate:**

- [ ] Inputs identified (skill path, references, external sources if applicable)
- [ ] Skill and references inventoried
- [ ] Assumptions listed
- [ ] Stakes level assessed and recorded
- [ ] Stopping criteria selected

**DISCOVER:**

- [ ] All 12 dimensions considered (D13 if orchestration skill)
- [ ] ≥3 DISCOVER techniques applied
- [ ] D1-D8 not skipped
- [ ] Any N/A dimensions have skeptical-reviewer-level justification

**EXPLORE:**

- [ ] Each checked dimension has Cell Schema fields (Status, Evidence, Confidence)
- [ ] Evidence requirements met for stakes level
- [ ] Findings linked to dimensions with priority assigned
- [ ] Proposed fixes drafted for each finding

**VERIFY:**

- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Assumptions resolved (verified, invalidated, or flagged)

**FIX:**

- [ ] Fixes applied in priority order (P0 first)
- [ ] Each fix documented (original → revised)
- [ ] Conflicts noted and resolved

**REFINE:**

- [ ] Yield% calculated for each pass
- [ ] Convergence reached or iteration cap hit

**Adversarial Pass:**

- [ ] Required lenses applied for stakes level
- [ ] Objections documented with responses or accepted risks
- [ ] Compliance Prediction lens applied (critical for skills)

**Exit Gate:**

- [ ] All criteria passed
- [ ] Full report written to artifact location
- [ ] Chat summary contains P0/P1/P2 counts and key changes only

**Quick self-test:**

- If a P0 issue existed, would the user definitely see it in the summary?
- Did I check quality of content, not just presence of sections?
- Are the fixes actually applied, not just reported?

## Extension Points

**Skill-type-specific dimensions:**

- Process/Workflow skills: Add "Step ordering" dimension — are steps in logical sequence?
- Quality Enhancement skills: Add "Criteria clarity" dimension — are quality dimensions measurable?
- Meta-cognitive skills: Add "Recognition specificity" dimension — are triggers concrete enough to detect?

**Framework handoffs:**

- If review finds skill is fundamentally flawed → Recommend returning to brainstorming-skills
- If review passes → Skill ready for testing-skills validation
- These are recommendations, not automated handoffs (user decides)

**Custom artifact locations:**

- Default: `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
- Projects can override via CLAUDE.md

**Stakes presets:**

- Projects can define default stakes in CLAUDE.md (e.g., "all skill reviews are Rigorous minimum")
- User can still override per-review

**Integration with other skills:**

| Skill | Relationship |
|-------|--------------|
| brainstorming-skills | Upstream — produces draft SKILL.md that this skill reviews |
| testing-skills | Downstream — validates behavioral effectiveness after review |
| reviewing-documents | Sibling — same pattern, different target (prose specs vs skills) |

**References directory depth:**

- Default: Review all files in references/ one level deep
- For skills with nested reference structures, note which files were reviewed and which were skipped

## References

- [Dimension Definitions](references/dimension-definitions.md) — Detailed checking guidance for each D1-D12 dimension
