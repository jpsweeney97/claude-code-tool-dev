---
name: design-reviewer
description: Reviews design documents for quality, completeness, and implementation readiness using weighted scoring. Use after brainstorming completes, before writing-plans.
allowed-tools: Read, Glob, Grep, Write, Bash
user-invocable: true
---

# Design Reviewer

## When to Use

- After brainstorming skill completes and saves a design document
- Before starting implementation with writing-plans skill
- When someone wants an independent assessment of design quality
- User says "review design", "check my design", or "/design-reviewer"

## When NOT to Use

**STOP conditions:**

- **STOP** if no design document exists yet — run brainstorming first
- **STOP** if the document is an implementation plan (contains "Task N:" headers) — this reviews designs, not plans
- **STOP** if user wants to edit/improve the design — this produces a report, it doesn't modify the original

**Non-goals:**

- Does not fix issues in the design (reports them for author to address)
- Does not validate implementation plans — different structure and criteria
- Does not replace human judgment on business/product decisions
- Does not review standalone code files or PRs — use code-review skills for that

## Inputs

**Required:**

- **Design document path** — Path to design doc (typically `docs/plans/YYYY-MM-DD-<topic>-design.md`)

**Optional:**

- **Focus areas** — Specific aspects to emphasize (e.g., "security", "error handling")
- **Context** — Additional background not in the design doc

**Constraints:**

- Design document must exist at the specified path
- Document must have minimal structure (see Decision Points for structural check)

## Outputs

**Artifacts:**

- **Review report** — Written to `docs/plans/YYYY-MM-DD-<topic>-design-review.md` (same directory as design doc, with `-review` suffix)
- Only written after user confirmation

**Report structure:**

```markdown
# Design Review: <topic>

**Design doc:** <path>
**Reviewed:** <date>
**Verdict:** PASS | PASS WITH CONCERNS | NEEDS REVISION
**Score:** <total> (Critical: N×10, Important: N×3, Minor: N×1)

## Summary
<2-3 sentence overall assessment>

## Findings

### Critical (10 points each — must fix)
- <finding with rationale>

### Important (3 points each — should address)
- <finding with rationale>

### Minor (1 point each — consider)
- <finding with rationale>

## Recommendations
<Prioritized next steps>
```

**Definition of Done:**

- [ ] Review report file exists at confirmed path
- [ ] Report contains verdict (PASS, PASS WITH CONCERNS, or NEEDS REVISION)
- [ ] Report contains score breakdown
- [ ] All Critical/Important findings include rationale
- [ ] User confirmed before file was written

## Evaluation Checklist

Use this checklist to identify findings. Each unchecked item is a potential finding.

### Completeness
- [ ] Has clear purpose/goal statement
- [ ] Lists components or modules involved
- [ ] Describes data flow between components
- [ ] Addresses error handling and failure modes
- [ ] Includes testing strategy or verification approach

### Clarity
- [ ] No undefined terms or acronyms without explanation
- [ ] No "TBD", "TODO", or placeholder sections
- [ ] Complex concepts have examples
- [ ] Could be implemented without asking clarifying questions

### Feasibility
- [ ] All referenced dependencies exist
- [ ] No "assume X works" without justification
- [ ] Performance/scale claims have basis (benchmarks, estimates, precedent)
- [ ] Resource requirements stated (memory, storage, external services)

### Architecture
- [ ] Simpler alternative was considered (or justified why not applicable)
- [ ] Trade-offs explicitly stated
- [ ] Consistent with existing codebase patterns (or explains deviation)
- [ ] No unnecessary abstraction layers

### Edge Cases
- [ ] Empty/null inputs handled
- [ ] Boundary conditions addressed
- [ ] Concurrent access considered (if applicable)
- [ ] Failure/retry behavior defined

### Security (if applicable)
- [ ] Authentication mechanism specified
- [ ] Authorization checks defined
- [ ] Sensitive data handling addressed
- [ ] Input validation approach stated

### Testability
- [ ] Testing approach described
- [ ] Success criteria are verifiable
- [ ] Key behaviors are observable/measurable

## Severity Calibration

**Critical (10 points) — Cannot implement without fixing:**
- Security: "Auth handled client-side only" → server must validate
- Blocker: "Requires API that doesn't exist"
- Incompleteness: "Error handling: TBD" in critical path
- Contradiction: Component A assumes X, Component B assumes not-X

**Important (3 points) — Could implement but shouldn't:**
- Missing edge case: "No handling for empty input"
- Unclear ownership: "Some service will handle this"
- Weak justification: "Chose Redis because it's popular"
- Partial coverage: "Happy path only, errors handled later"

**Minor (1 point) — Cosmetic or future concern:**
- Style: "Inconsistent naming (userId vs user_id)"
- Scale: "May need optimization past 10k users"
- Polish: "Diagram would clarify this section"
- Preference: "Could use X pattern instead of Y"

## Procedure

1. **Announce:** "Using design-reviewer to audit the design document."

2. **Locate design document:**
   - If path provided, use it
   - If not provided, use Glob to search `docs/plans/*-design.md` for most recent
   - **STOP** if no design document found — ask user to specify path or run brainstorming first

3. **Use the Read tool to read the design document**

4. **Structural check:**
   Check for presence of: purpose/goal, components/architecture, data flow, error handling
   - If ≥2 sections missing → ask user: "This design is missing [X, Y]. Run brainstorming to flesh it out, or proceed with partial review?"
   - If user wants to proceed → continue with warning that review may be limited

5. **Check document type:**
   - If document contains "Task N:" headers or step-by-step implementation instructions → **STOP**
   - Inform user: "This appears to be an implementation plan, not a design doc. This skill reviews designs. Did you mean to run this before writing-plans?"

6. **Incorporate user-provided context** (if any) — use constraints, history, or concerns to weight evaluation priorities

7. **Evaluate against checklist:**
   - Work through each section of the Evaluation Checklist
   - For each unchecked item, determine if it's a finding or not applicable
   - Categorize findings using Severity Calibration examples

8. **Calculate score:**
   - Critical findings × 10
   - Important findings × 3
   - Minor findings × 1
   - Total = sum of all

9. **Determine verdict:**
   - **NEEDS REVISION** — Any Critical finding present (regardless of score)
   - **PASS WITH CONCERNS** — No Critical, but score ≥ 10
   - **PASS** — No Critical and score < 10

10. **Present summary to user:**
    Show verdict, score breakdown, and Critical/Important findings.
    Ask: "Write review report to `docs/plans/YYYY-MM-DD-<topic>-design-review.md`?"
    - If user approves → proceed to step 11
    - If user declines → output complete report to conversation only, skip to step 13
    - If user wants different path → use their path

11. **Write review report:**
    - If directory doesn't exist, create with `mkdir -p docs/plans`
    - Write report to confirmed path

12. **Verify write succeeded** (see Verification section)

13. **Complete:** Summarize verdict and key recommendations

## Decision Points

- **If no design document found at path or in `docs/plans/`:**
  STOP and ask user for path. Do not proceed without a document to review.

- **If document appears to be an implementation plan:**
  STOP and inform user this skill reviews design docs, not implementation plans. Suggest they wanted to run this before writing-plans.

- **If design document lacks ≥2 structural sections:**
  Ask user whether to proceed with partial review or run brainstorming first to complete the design.

- **If user declines to write file:**
  Output complete report to conversation. Do not write any file.

- **If any Critical finding exists:**
  Verdict is NEEDS REVISION regardless of total score.

- **If user provided focus areas:**
  Weight those checklist sections higher, but still evaluate all sections.

- **If write fails (permission error or directory missing):**
  Attempt `mkdir -p docs/plans`. If still failing, output to conversation and report the error.

## Assumptions

**Environment:**
- Bash available (macOS/Linux standard)
- Write access to project's `docs/plans/` directory

**GitFlow users:**
- If using branch protection, add `docs/plans/*.md` to `GITFLOW_ALLOW_FILES`
- Without this exception, writes on protected branches will be blocked

**Design document format:**
- Expects design to follow brainstorming skill output structure
- If format differs, review adapts but structural check may be less accurate

**Fallbacks:**
- If Bash unavailable → use Read tool to verify file exists, Grep for section headers
- If write blocked → output complete report to conversation instead

## Verification

**Preconditions:**
- Bash available (standard on macOS/Linux)
- Report path known from step 11

**Quick check:**
```bash
test -f "<report_path>" && grep -q "^## Summary" "<report_path>"
```
Expected: Exit 0 (file exists with Summary section)

**If Bash unavailable:** Use Read tool on report path; verify "## Summary" heading exists.

**Deep check:**
1. `grep -q "Verdict:" <report>` → Exit 0
2. `grep -q "## Findings" <report>` → Exit 0
3. `grep -q "Score:" <report>` → Exit 0
4. Verdict is one of: PASS, PASS WITH CONCERNS, NEEDS REVISION

**If quick check fails:**
- File missing → Write failed. Check directory exists with `ls -la docs/plans/`
- Summary missing → Report incomplete. Regenerate from step 11.

## Troubleshooting

**Symptom:** Review report has no findings (all sections empty)
**Cause:** Design document may be too abstract or high-level
**Next steps:** Ask user if they want architecture-only review or if design should be fleshed out with brainstorming

---

**Symptom:** Cannot determine if document is design vs implementation plan
**Cause:** Document has mixed structure (design narrative + implementation steps)
**Next steps:** Ask user which aspect to review. Offer to review as design only, ignoring implementation details.

---

**Symptom:** Report file not created despite procedure completing
**Cause:** Write permission issue or directory doesn't exist
**Next steps:**
1. Check if directory exists: `ls -la docs/plans/`
2. If missing, create: `mkdir -p docs/plans`
3. Retry write. If still failing, output to conversation.

---

**Symptom:** Write blocked with "protected branch" message
**Cause:** GitFlow hook active and `docs/plans/` not in allowed files
**Next steps:** Add `docs/plans/*.md` to `GITFLOW_ALLOW_FILES` environment variable, or output to conversation only

---

**Symptom:** Severity ratings seem inconsistent
**Cause:** Calibration drift from examples
**Next steps:** Re-check each finding against Severity Calibration examples; recategorize if needed

---

**Symptom:** Review takes very long or runs out of context
**Cause:** Design document too large
**Next steps:** Ask user to split document or specify a section to focus on

---

**Symptom:** Score seems mathematically wrong
**Cause:** Miscount or miscategorization
**Next steps:** Recount findings per severity; verify each assignment against calibration examples

---

**Symptom:** Structural check flags missing sections that exist
**Cause:** Non-standard heading names (e.g., "Goals" instead of "Purpose")
**Next steps:** Ask user to confirm sections present; adapt check to document's structure
