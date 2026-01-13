---
name: design-reviewer
description: Reviews design documents produced by brainstorming skill for quality, completeness, and implementation readiness. Use after brainstorming completes, before writing-plans.
allowed-tools: Read, Glob, Grep, Write
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

- **STOP** if no design document exists yet — run brainstorming first to create one
- **STOP** if the document is an implementation plan (from writing-plans), not a design doc — this skill reviews designs, not plans
- **STOP** if user wants to edit/improve the design — this skill produces a report, it doesn't modify the original

**Non-goals:**

- Does not fix issues in the design (reports them for author to address)
- Does not validate implementation plans — those have different structure and criteria
- Does not replace human judgment on business/product decisions
- Does not review standalone code files or PRs — use code-review skills for that (code snippets within design docs are fair game)

## Inputs

**Required:**

- **Design document path** — Path to design doc (typically `docs/plans/YYYY-MM-DD-<topic>-design.md`)

**Optional:**

- **Focus areas** — Specific aspects to emphasize (e.g., "security", "error handling", "scalability")
- **Context** — Additional background not in the design doc (constraints, history, concerns)

**Constraints:**

- Design document must exist at the specified path
- `docs/plans/` directory must exist (created if missing)
- Write permission required for output directory
- Assumes design follows brainstorming skill output format (if not, reviewer adapts but may miss structure-specific checks)

## Outputs

**Artifacts:**

- **Review report** — Written to `docs/plans/YYYY-MM-DD-<topic>-design-review.md` (same directory as design doc, with `-review` suffix)

**Report structure:**

```markdown
# Design Review: <topic>

**Design doc:** <path>
**Reviewed:** <date>
**Verdict:** PASS | PASS WITH CONCERNS | NEEDS REVISION

## Summary
<2-3 sentence overall assessment>

## Findings

### Critical (must fix before implementation)
- <finding with rationale>

### Important (should address)
- <finding with rationale>

### Minor (consider for future)
- <finding with rationale>

## Recommendations
<Prioritized next steps>
```

**Definition of Done:**

- [ ] Review report file exists at expected path
- [ ] Report contains verdict (PASS, PASS WITH CONCERNS, or NEEDS REVISION)
- [ ] All critical findings include rationale explaining the concern
- [ ] Recommendations section present (even if empty with "None — ready for implementation")

## Procedure

1. **Announce:** "Using design-reviewer to audit the design document."

2. **Locate design document:**
   - If path provided, use it
   - If not provided, search `docs/plans/*-design.md` for most recent
   - **STOP** if no design document found. Ask user to specify path or run brainstorming first.

3. **Read and parse the design document**

4. **Incorporate user-provided context** (if any) — use constraints, history, or concerns to inform evaluation priorities

5. **Evaluate against review criteria:**

   | Criterion | Questions to Answer |
   |-----------|---------------------|
   | **Completeness** | Does it cover purpose, architecture, components, data flow, error handling? |
   | **Clarity** | Could an engineer with no context understand and implement this? |
   | **Feasibility** | Are there technical blockers, missing dependencies, or unrealistic assumptions? |
   | **Architecture** | Is the approach sound? Are there simpler alternatives? |
   | **Edge cases** | Are failure modes, error handling, and boundary conditions addressed? |
   | **Security** | Are there authentication, authorization, or data exposure concerns? |
   | **Testability** | Is the testing strategy clear? Can this be verified? |

6. **Categorize findings by severity:**
   - **Critical** — Must fix before implementation (blockers, security issues, fundamental flaws)
   - **Important** — Should address (gaps, unclear areas, missing considerations)
   - **Minor** — Consider for future (nice-to-haves, polish)

7. **Determine verdict:**
   - **PASS** — No critical findings, ≤2 important findings
   - **PASS WITH CONCERNS** — No critical findings, but >2 important findings
   - **NEEDS REVISION** — Any critical findings present

8. **Write review report** to `docs/plans/YYYY-MM-DD-<topic>-design-review.md`
   - If write fails, check that `docs/plans/` exists. Create with `mkdir -p docs/plans` if needed and retry.
   - If still failing, STOP and report the permission error to user.

9. **Present summary to user** with verdict and critical/important findings

10. **Run verification check** (see Verification section)

## Decision Points

- **If no design document found at path or in `docs/plans/`:**
  STOP and ask user for path. Do not proceed without a document to review.

- **If document appears to be an implementation plan (contains "Task N:" headers, step-by-step implementation):**
  STOP and inform user this skill reviews design docs, not implementation plans. Suggest they wanted to run this before writing-plans, not after.

- **If design document is very short (<200 words):**
  Ask user if this is a complete design or a stub. If stub, suggest running brainstorming to flesh it out first.

- **If review finds critical issues:**
  Verdict is NEEDS REVISION. Recommend addressing critical findings before proceeding to implementation.

- **If user provided focus areas:**
  Weight those criteria higher in the review, but still evaluate all criteria.

## Verification

**Quick check:**

Use the actual report path from step 8 (e.g., `docs/plans/2024-01-13-auth-design-review.md`):

```bash
test -f "$REPORT_PATH" && grep -q "^## Summary" "$REPORT_PATH"
```

Expected: Exit 0 (file exists and contains Summary section)

Note: Replace `$REPORT_PATH` with the literal path written in step 8. Do not use glob patterns.

**Deep check:**

1. Report file exists at expected path
2. Report contains all required sections:
   - `grep -q "Verdict:" <report>` — has verdict
   - `grep -q "## Summary" <report>` — has summary
   - `grep -q "## Findings" <report>` — has findings
   - `grep -q "## Recommendations" <report>` — has recommendations
3. Verdict is one of: PASS, PASS WITH CONCERNS, NEEDS REVISION
4. Critical findings have rationale:
   - Each bullet under "### Critical" must explain *why* it's a concern, not just *what*
   - Verify: `awk '/### Critical/,/### Important/' "$REPORT_PATH" | grep -c "^-"` should match count of findings
   - If any critical finding lacks rationale (just states the issue without explaining impact), revise before finalizing report

**If quick check fails:**

- If file missing: Write failed. Check path permissions. Verify `docs/plans/` exists.
- If Summary missing: Report incomplete. Re-run procedure from step 8.

## Troubleshooting

**Symptom:** Review report has no findings (all sections empty)
**Cause:** Design document may be too abstract or high-level for concrete review
**Next steps:** Ask user if they want a higher-level review (architecture only) or if the design should be fleshed out more with brainstorming

---

**Symptom:** Cannot determine if document is design vs implementation plan
**Cause:** Document has mixed structure (some design narrative, some implementation steps)
**Next steps:** Ask user which aspect they want reviewed. Offer to review as design (ignoring implementation details) or suggest splitting into two documents.

---

**Symptom:** Report file not created despite procedure completing
**Cause:** Write permission issue or `docs/plans/` directory doesn't exist
**Next steps:**
1. Check if directory exists: `ls -la docs/plans/`
2. If missing, create it: `mkdir -p docs/plans`
3. Retry writing the report
