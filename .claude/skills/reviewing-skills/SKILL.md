---
name: reviewing-skills
description: Use after brainstorming-skills produces a draft. Use when auditing existing skills for quality drift. Use when agents don't follow a skill reliably. Use when asked to "review," "audit," or "improve" a skill.
---

# Reviewing Skills

## Overview

Skills fail silently: vague triggers cause misfires, weak compliance language gets rationalized around, missing sections leave gaps that testing catches too late. Document quality issues compound — a slightly unclear instruction becomes agent confusion becomes user frustration.

This skill reviews SKILL.md files and their supporting files for structural quality, clarity, and compliance strength. It catches issues before behavioral testing (testing-skills), when fixes are cheap.

**What this skill can do:**
- Assess document quality (clarity, precision, completeness)
- Predict compliance strength (rationalization resistance, not actual behavior)
- Validate internal references (linked files exist, links work, content aligns with SKILL.md)
- Cross-check external sources (if skill claims to implement a spec or follow official docs, verify alignment)
- Escalate when issues are too fundamental to fix in place

**What this skill cannot do:**
- Verify agents actually follow the skill (that's testing-skills)
- Validate domain expertise (can check consistency with sources, not whether sources are correct)
- Rewrite fundamentally broken skills (recommend brainstorming-skills instead)

**Protocol:** [thoroughness.framework@1.0.0](framework-for-thoroughness.md)
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
| Refined supporting files | Original locations (edits applied in place) |
| Review report | `docs/audits/YYYY-MM-DD-<skill-name>-review.md` (create directory if needed) |

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
**Findings:** P0: N | P1: N | P2: N (N fixed, M accepted)
**Key changes:** [1-2 most significant fixes]
**Full report:** `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
```

**Do NOT include in chat:** Full findings list, iteration log, coverage tracker, disconfirmation details, complete list of fixes.

**Definition of Done:**

- [ ] Entry Gate completed and recorded
- [ ] All dimensions explored with Evidence/Confidence ratings meeting stakes requirements (Adequate: E1 for P0; Rigorous: E2 for P0, E1 for P1; Exhaustive: E2 for all, E3 for P0)
- [ ] Yield% below threshold for thoroughness level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed
- [ ] Fixes applied to skill and supporting files
- [ ] Exit Gate criteria satisfied
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify inputs:**

- Target skill (SKILL.md path)
- Supporting files (any files linked from SKILL.md — may be in skill root or subdirectories)
- External sources (official docs, specs the skill claims to implement), if applicable
- User-specified concerns, if any

If inputs are unclear, ask. Accept paths or skill names.

**2. Inventory the skill:**

- Read the entire SKILL.md — not just headers, but full content. You need to understand the skill's purpose and flow before checking individual dimensions.
- Identify all linked supporting files (look for markdown links like `[text](file.md)` — files may be in skill root or subdirectories like `reference/`, `examples/`, `scripts/`)
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

**7. Initialize dimension tracking:**

Use TaskCreate to create one task per dimension (D1-D16). This externalizes your checklist so you don't need to hold all dimensions in memory.

- Subject: "D1: Trigger clarity" (use dimension name)
- Description: Include priority (P0/P1/P2) and the "What it catches" summary from [Dimension Definitions](dimension-definitions.md)
- activeForm: "Checking trigger clarity" (shown in spinner while task is in_progress)
- Do not start checking until all dimension tasks are created

This step is critical for cognitive manageability — the review process involves tracking 16 dimensions across multiple passes. Task tracking externalizes this burden and survives context compaction.

### Dimension Catalog

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D1 | Trigger clarity | P0 | Vague or overlapping descriptions that cause misfires or missed activations |
| D2 | Process completeness | P0 | Missing steps, undefined decision points, unclear exit criteria |
| D3 | Structural conformance | P0 | Missing required sections, wrong frontmatter, exceeds size limits |
| D4 | Compliance strength | P1 | Weak language, missing rationalization counters, no red flags |
| D5 | Precision | P1 | Vague wording that allows multiple interpretations (language quality) |
| D6 | Actionability | P1 | Instructions lack execution details — tools, paths, methods unspecified (execution readiness) |
| D7 | Internal consistency | P1 | Contradictions between sections, terminology drift |
| D8 | Scope boundaries | P1 | Missing "When NOT to Use", unclear exclusions |
| D9 | Reference validity | P2 | Broken links, outdated references, missing assets |
| D10 | Edge cases | P2 | Boundary situations undefined |
| D11 | Feasibility | P2 | Requirements that can't be achieved |
| D12 | Testability | P2 | Requirements that can't be verified |
| D14 | Example quality | P1 | Unrealistic, non-diverse, or non-graduated examples that don't transfer |
| D15 | Cognitive manageability | P2 | Skill overwhelms working memory or requires tracking too much simultaneously |
| D16 | Methodological soundness | P1 | Wrong, outdated, or poorly-justified approach — skill teaches bad methodology |

**Conditional dimension:**

| ID | Dimension | Priority | When to check |
|----|-----------|----------|---------------|
| D13 | Integration clarity | P1 | Orchestration-type skills only — unclear handoffs to/from other skills |

**Dimension applicability:**

- **D1-D8:** Always check (cannot skip)
- **D9-D12:** Always check, but lower priority
- **D13:** Only for orchestration skills (mark N/A otherwise)
- **D14-D15:** Always check, but lower priority (P1/P2)
- **D16:** Always check; priority varies by skill type (P0 for Process/Quality/Solution, P1 for others)

**Before marking any dimension N/A:**

1. State specific reason (not "doesn't apply" but WHY)
2. Test: "Would a skeptical reviewer accept this justification?"
3. Self-check: "If this dimension revealed issues, would I be surprised?"

If #2 is "maybe not" or #3 is "no" → check the dimension anyway.

**For detailed checking guidance per dimension, see [Dimension Definitions](dimension-definitions.md).**

### The Review Loop

**Note:** This skill adds a FIX stage to the standard thoroughness framework loop (DISCOVER → EXPLORE → VERIFY → REFINE). The FIX stage is where corrections are applied to the skill being reviewed, between verification and convergence checking.

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

**Seed dimensions:** Start with D1-D16 from the catalog. D13 applies only to orchestration skills (mark N/A otherwise).

**Assign priorities:** Use catalog defaults, adjust if context warrants. Different skill types have different priority emphases — see [Skill Type Adaptation](skill-type-adaptation.md) for type-specific guidance on which dimensions to elevate.

**Expand dimensions:** Apply ≥3 DISCOVER techniques:

- **Skill-specific patterns:** What quality issues are common for this skill type?
- **Reference scan:** Do references introduce dimensions not in the catalog?
- **Pre-mortem:** "This review would be worthless if I missed..."
- **Historical patterns:** What caused problems in similar skills?

**Output:** Dimension list with priorities (P0/P1/P2)

#### EXPLORE: Check each dimension

**Before checking any dimension:** Verify all dimension tasks exist (created in Entry Gate step 7). Use TaskList to confirm.

**If resuming after context compaction:** Use TaskGet to retrieve full details for any task you need to continue. TaskList shows summaries; TaskGet returns the complete description and metadata.

**For each dimension:**

1. TaskUpdate to mark `in_progress` (the activeForm you set during creation will show in the spinner)
2. Re-read the relevant section of the skill being reviewed (don't rely on memory from Entry Gate)
3. Check the dimension using guidance from [Dimension Definitions](dimension-definitions.md)
4. TaskUpdate to mark `completed` with Cell Schema fields in metadata

**Cell Schema fields** (record in task metadata):

| Field | Required | Values |
|-------|----------|--------|
| ID | Yes | D1, D2, ... |
| Status | Yes | `[x]` done, `[~]` partial, `[-]` N/A, `[ ]` not started, `[?]` unknown |
| Priority | Yes | P0 / P1 / P2 |
| Evidence | Yes | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes | High / Medium / Low |
| Artifacts | If applicable | File paths, quotes, line numbers |
| Notes | If applicable | What's missing, proposed fix |

**For dimensions with no issues:** Mark as `[x]` with Evidence level reflecting how thoroughly you checked. Example: `| D8 | [x] | P1 | E1 | High | Notes: "When NOT to Use" section present and specific |`

**For dimensions with findings:** Create separate finding entries (F1, F2, etc.) linked to the dimension. The dimension status reflects overall check completion, not whether issues were found.

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Independent methods for document review:**
- Reading the section directly (E1)
- Cross-referencing with examples or other sections (E1 → E2 when combined)
- Tracing a concept through the full document (E1 → E2 when combined)
- Checking against project CLAUDE.md or external standards (independent source)
- Testing a claim by applying the skill mentally to a hypothetical case

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

**For each finding, use TaskCreate:**

Create a finding task (F1, F2, etc.) with:
- Subject: "F1: [brief description of issue]"
- Description: Include linked dimension(s), priority, evidence, confidence, artifacts (quotes, line refs), and proposed fix
- activeForm: "Investigating [brief description]" (shown in spinner during FIX stage)

Example proposed fix: "Add 'YOU MUST' before the instruction" or "Replace vague 'appropriate' with specific criteria"

These finding tasks will be processed in the FIX stage.

**For subsequent passes (Pass 2+):**

Dimension tasks track *cumulative state* (status, evidence, confidence). Pass tasks track *activity* (what you're examining this iteration). Use both:

1. **Create a pass task** at the start of each subsequent pass:
   - Subject: "Execute Pass N: [focus]" (e.g., "Execute Pass 2: Deep compliance check")
   - Description: List which dimensions you'll re-examine and why
   - activeForm: "Executing Pass N"

2. **When re-checking a dimension**, update its task metadata (not status — dimension remains `completed`):
   - Add to Notes: "Pass 2: re-checked, no changes" or "Pass 2: found issue, see F6"
   - Update Evidence/Confidence fields if the re-check changes your assessment

3. **Mark the pass task complete** when done, recording Yield% in metadata

This maintains dimension → finding linkage while making pass progression visible and surviving context compaction.

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

**Use TaskList to see all finding tasks.** Process in priority order (P0 first, then P1, then P2).

For each finding task:

1. TaskUpdate to mark `in_progress` with activeForm: "Fixing [brief description]"
2. Apply the fix directly to the skill or reference file using the Edit tool
3. TaskUpdate to mark `completed` with metadata noting what changed (original text → revised text, with file and line reference)

**Apply fixes at the end of each pass**, not during EXPLORE/VERIFY. This prevents fixes from interfering with dimension checking.

**Fix order:** P0 issues first, then P1, then P2.

**Conflict detection:** If fixing one issue contradicts another fix:

1. Note the conflict
2. Determine priority (higher-priority finding wins)
3. Document the trade-off in the review report

**Do not fix:**

- Issues marked as "accepted deviation" by user
- Issues outside skill's scope (flag for separate work)
- Issues requiring user decision (flag and ask)

**For controversial fixes** (where reasonable people might disagree — e.g., word choice, organizational structure, level of detail): Flag for user review before applying. If uncertain whether a fix is controversial, ask.

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

**Proceed to Adversarial Pass when ALL of these are true:**

- No new dimensions in last pass
- No significant revisions
- All items resolved
- Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

**YOU MUST** complete the Adversarial Pass before claiming done. Do not skip it even if the loop found no issues.

**Iteration cap (failsafe):** If convergence not reached after 5 passes (Adequate), 7 passes (Rigorous), or 10 passes (Exhaustive), exit with finding: "Skill may need fundamental revision — review did not converge."

### Reviewing Supporting Files

Supporting files can live anywhere in the skill directory: in the root (e.g., `examples.md`, `template.md`) or in subdirectories (e.g., `reference/`, `scripts/`, `examples/`). The key requirement is that they're linked from SKILL.md and kept one level deep (never deeply nested).

**If no supporting files exist:** Skip this section. Note "No supporting files" in the review report and proceed to Adversarial Pass.

**Discovery:**

1. Scan SKILL.md for markdown links: `[text](path)`
2. List the skill directory contents to find any files not linked
3. Scripts in `scripts/` subdirectories are executed, not loaded — check they exist but don't apply document quality dimensions

**For each linked supporting file:**

**Existence and linkage:**
- [ ] File exists at the linked path
- [ ] Link syntax is correct (relative path from SKILL.md)
- [ ] No orphaned files (files that exist but aren't linked from SKILL.md)
- [ ] Files are one level deep from SKILL.md (not nested like `reference/sub/file.md`)

**Quality (apply relevant dimensions):**
- D5 (Precision): Is language precise?
- D6 (Actionability): Are instructions clear?
- D7 (Internal consistency): Does it use same terminology as SKILL.md?

**Coherence with SKILL.md:**
- [ ] Supporting file supports claims made in SKILL.md
- [ ] No contradictions between SKILL.md and supporting file
- [ ] Supporting file doesn't introduce requirements not mentioned in SKILL.md
- [ ] Terminology matches (no drift)

**File-specific checks:**
- TOC present if >100 lines?
- Examples concrete, not abstract?
- Outdated information (dates, versions, deprecated features)?

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if the review loop found nothing.

**Before starting:** Use TaskCreate to create one task per lens you'll apply (7 for Rigorous/Exhaustive, 4 for Adequate). Include activeForm for each (e.g., "Applying compliance prediction lens"). This ensures no lens is skipped.

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

- Adequate: Apply 4 lenses (must include Compliance Prediction and Trigger Ambiguity; choose 2 others); document key objections; fix issues found
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

**After review completes:** If no P0 issues remain, the skill is ready for testing-skills to validate behavioral effectiveness. Pass the reviewed SKILL.md path.

## Decision Points

**Inputs unclear:**

- If skill path not specified → Ask: "Which skill should I review?"
- If supporting files exist but not inventoried → Inventory them automatically by scanning links in SKILL.md
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

See [Examples](examples.md) for worked examples demonstrating:

- **Example 1:** Reviewing a draft skill — shows BAD (single-pass "looks fine") vs GOOD (iterative with fixes)
- **Example 2:** Auditing a production skill — traces behavioral issue to document quality

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
| "I'll just do a quick check" | Pass 1 is always 100% yield — one pass is never enough. The loop exists for a reason. |
| "I already reviewed this recently" | Skills drift. Context changes. Re-review catches what shifted since last time. |

**All of these mean: Complete the review. No exceptions.**

## Troubleshooting

For common issues and solutions, see [Troubleshooting](troubleshooting.md).

## Verification

After completing a review, verify all items in the Definition of Done (Outputs section) are satisfied.

For the detailed verification checklist, see [Verification Checklist](verification-checklist.md).

## References

- [Dimension Definitions](dimension-definitions.md) — Detailed checking guidance for each D1-D16 dimension
- [Skill Type Adaptation](skill-type-adaptation.md) — Type-specific priority adjustments, extension points, and additional checks
- [Framework for Thoroughness](framework-for-thoroughness.md) — Protocol specification for Yield%, stakes calibration, evidence levels
- [Examples](examples.md) — Worked examples showing BAD vs GOOD review approaches
- [Troubleshooting](troubleshooting.md) — Common issues and solutions
- [Verification Checklist](verification-checklist.md) — Detailed checklist for review completion
