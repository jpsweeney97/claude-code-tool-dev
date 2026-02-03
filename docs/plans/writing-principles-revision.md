# Implementation Plan: Writing Principles Document Revision

## Summary

Revise `docs/references/writing-principles.md` to:
1. Fix internal consistency violations (structural fixes)
2. Add two new principles (#13 Declare Preconditions, #14 Define Authority)
3. Update all dependent sections (Quick Reference, Priority table, Self-Check, Grading Scale)

**Target file:** `docs/references/writing-principles.md`

---

## Phase 1: Structural Fixes

Quick wins that improve internal consistency without touching the principle structure.

### 1.1 Add Applicability Statement to Preamble

**Location:** After line 3 (after "...correct interpretation.")

**Add:**
```markdown
This guide applies to Claude Code authoring instruction documents. It does not apply to user-facing documentation, conversational responses, code comments, or creative writing (see Limitations).
```

**Rationale:** States Boundaries (#9) — scope was only stated at end in Limitations section.

### 1.2 Define "Progressive Disclosure"

**Location:** Line 459

**Change from:**
```markdown
Progressive disclosure: SKILL.md under 500 lines; reference material in supporting files.
```

**Change to:**
```markdown
Progressive disclosure (main content first, reference material last or in separate files): SKILL.md under 500 lines.
```

**Rationale:** Define Terms (#3) — "progressive disclosure" is UX jargon.

### 1.3 Close Self-Check Iteration Loop

**Location:** After line 546 (end of Pass 10)

**Add new section:**
```markdown
### Iteration

If violations found:
1. Fix highest-priority violations first (Priority 1 before Priority 2, etc.)
2. Re-run Self-Check from Pass 1
3. If a violation cannot be fixed without creating higher-priority violations, document the trade-off and mark for review

Stopping condition: No Priority 1-3 violations remain, or all remaining violations are documented trade-offs.
```

**Rationale:** Specify Failure Modes (#11) — original didn't specify iteration path.

### 1.4 Add Limitations Reference to Preamble

**Location:** Already handled in 1.1 — "(see Limitations)" provides the forward reference.

**Alternative consideration:** Move Limitations section earlier?

**Decision:** Keep Limitations at end. The preamble reference is sufficient per Front-Load (#6) — the existence of limitations is flagged early; details can remain at end.

---

## Phase 2: Merge Conflict Sections

**Current state:** Two sections handle principle conflicts:
- Lines 36-48: "When Principles Conflict" (priority table + rule of thumb)
- Lines 55-77: "When Principles Conflict Irreconcilably" (edge cases)

**Target state:** Single section with subsections.

### 2.1 Merged Structure

```markdown
## When Principles Conflict

### Priority Hierarchy

| Priority | Principles | Rationale |
|----------|------------|-----------|
| 1 | Be Specific (#2), Define Terms (#3), Show Examples (#4), Verify Interpretation (#12) | Ambiguity and misinterpretation cause wrong behavior |
| 2 | State Boundaries (#9), Specify Failure Modes (#11), Declare Preconditions (#13), Define Authority (#14) | Improvisation in ambiguous execution context is worse than verbosity |
| 3 | Close Loopholes (#5) | Misinterpretation harder to detect than fix |
| 4 | Front-Load (#6), Group Related (#7), Keep Parallel (#8) | Parsing errors cascade |
| 5 | Specify Outcomes (#10) | Verification gaps are recoverable |
| 6 | Economy (#1) | Trim only after all else assured |

When in doubt: if cutting a word creates ambiguity or removes important context, keep the word.

### Irreconcilable Conflicts

If you cannot satisfy a principle without violating another of equal or higher priority:

1. State the conflict explicitly in your output
2. Choose the option that preserves more information (ambiguity is worse than verbosity)
3. Mark the compromise for human review

### Missing Context

If you lack context to satisfy a principle (e.g., cannot be specific because information is missing):

1. Flag the gap: "Specificity requires [X]; not available"
2. Proceed with best available approximation
3. Mark as incomplete

### Conflicting Instructions in Target Document

If the target document contains instructions that genuinely conflict:

1. Flag for human resolution—this is an intent problem, not a writing problem
2. Do not resolve by choosing one instruction over another

Default behavior: Flag and continue. Never silently improvise. Never spin indefinitely.
```

**Changes:**
- Combined into single section with clear subsections
- Updated Priority 2 to include #13 and #14
- Removed "Completion Criterion" as standalone section — its content is now in Self-Check Iteration

---

## Phase 3: Add New Principles

### 3.1 Principle #13: Declare Preconditions

**Location:** After #12 (Verify Interpretation), before Grading Scale

```markdown
---

### 13. Declare Preconditions

State what must be true before execution begins. Include a verification step.

Unstated preconditions force Claude to discover requirements at execution time—after partial work may have occurred. Explicit preconditions enable upstream checking.

| Before | After | Precondition Surfaced |
|--------|-------|----------------------|
| "Run `npm test`" | "Requires: in repo root (`package.json` exists). Check: `test -f package.json`. Run `npm test`." | Working directory |
| "Deploy to staging" | "Requires: user has approved deploy. Check: confirm with user that deploy is approved. Deploy to staging." | Human approval |
| "Merge feature branch" | "Requires: no merge conflicts. Check: `git merge --no-commit feature && git merge --abort` exits 0. Merge feature branch." | Git state |

**Pattern:** "Requires: [state]. Check: [verification]. [instruction]."

| Check Type | Form | Example |
|------------|------|---------|
| Programmatic | Command that exits 0 / returns expected output | `Check: test -f .env` |
| Confirmation | Explicit user confirmation | `Check: confirm with user that [X]` |
| Reference | Prior verification still valid | `Check: CI shows green for HEAD` |

**If you cannot specify a check:** The precondition is likely underspecified. Make it concrete enough to verify, or flag it as requiring human review.

**Common violations:**

_Unstated preconditions:_
- Assumed working directory: "Run `pytest tests/`" — which directory?
- Assumed tool availability: "Format with `black .`" — is black installed?
- Assumed prior completion: "Deploy the build" — was build successful?
- Assumed environment state: "Source the env file" — which file? Does it exist?
- Assumed permissions: "Write results to `/var/log/`" — write access?

_Unverifiable preconditions:_
- Precondition without check: "Requires: clean git state" — how to verify?
- Vague check: "Check: ensure environment is ready" — not executable
- Subjective check: "Check: code is well-tested" — no objective verification

_Incomplete preconditions:_
- Check without failure path: stated precondition but no "if not met" guidance
- Compound precondition, single check: "Requires: Node 18+ and npm 9+" with one version check
- Transitive precondition unstated: "Requires: tests pass" — but tests require dependencies...
```

### 3.2 Principle #14: Define Authority

**Location:** After #13, before Grading Scale

```markdown
---

### 14. Define Authority

State how this document relates to other instruction sources. Declare what it overrides, what it defers to, and its scope of applicability.

Future sessions interpreting multiple instruction documents cannot infer authorial intent about precedence. Explicit authority declarations prevent conflicts from being resolved by loading order or implicit conventions.

| Before | After | Authority Clarified |
|--------|-------|---------------------|
| "Use 4-space indentation" | "Use 4-space indentation. Overrides: project CLAUDE.md style section for files in `src/legacy/`." | Scope + override |
| "Run tests before committing" | "Run tests before committing. Defers to: CI workflow skill if present." | Conditional deference |
| "Format with Prettier" | "Format with Prettier. This skill's formatting rules override CLAUDE.md formatting guidance." | Skill vs CLAUDE.md |

**Pattern:** After instructions that might conflict with other sources, state:
- "Overrides: [source] for [scope]" — this document wins
- "Defers to: [source] for [scope]" — other source wins
- "Scoped to: [context]" — this document applies only in [context]

**When authority is unstated:** Future sessions resolve conflicts using default precedence (loading order, specificity heuristics). This may not match authorial intent.

**Common violations:**

_Implicit precedence:_
- Conflicting guidance, no precedence: CLAUDE.md says "use Prettier," Skill says "use Black" — which wins?
- Override without declaration: Skill file changes commit format — override or supplement?
- Assumed deference: "Follow project conventions" — which document defines them?
- Specificity assumed: Subdirectory CLAUDE.md differs from root — which is authoritative?

_Unstated scope:_
- Unbounded guidance: "Use 4-space indentation" in Skill file — all files or just skill-touched files?
- Context-dependent without context: "These rules apply during refactoring" — what counts as refactoring?
- Implicit file type scope: "Format with gofmt" — stated or assumed to apply only to .go files?

_Missing conflict resolution:_
- No fallback specified: Two skills could both apply — which governs?
- Partial override: Skill overrides "formatting" but CLAUDE.md has formatting and linting together — does override include linting?
- Temporal ambiguity: "Use new style going forward" — override or coexist?
```

---

## Phase 4: Update Dependent Sections

### 4.1 Quick Reference Table

**Location:** Lines 19-32

**Add two rows before the closing `---`:**

```markdown
| 13 | Declare Preconditions | State requirements and verification before execution | Assumed working directory, tools, or state |
| 14 | Define Authority | Declare precedence relationships with other instruction sources | Conflicting guidance without stated precedence |
```

### 4.2 Grading Scale

**Location:** Lines 422-430

**Change:**
- Line 426: "All 12 principles" → "All 14 principles"
- Line 430: "8+ principles" → "10+ principles"

**Updated table:**
```markdown
| Grade | Criteria |
|-------|----------|
| A | All 14 principles followed consistently |
| B | Minor violations in 1-2 principles |
| C | Noticeable issues in 3-4 principles |
| D | Significant issues in 5-8 principles |
| F | Pervasive violations (9+ principles) |
```

### 4.3 Self-Check Procedure

**Rename and extend Pass 8 and Pass 9:**

**Pass 8: Preconditions and Failure Modes** (was "Failure Modes")

```markdown
### Pass 8: Preconditions and Failure Modes
28. Flag instructions with preconditions but no failure handling
29. Verify "if X fails, then Y" patterns for critical operations
30. Check that error handling is specific, not "handle appropriately"
31. Flag instructions that reference files, commands, or state without directory/environment context
32. Flag instructions that depend on prior steps—verify those steps have success criteria
33. For each "Requires:" statement, verify a "Check:" is specified
34. Verify each check is executable (command, confirmation prompt, or reference)
35. Verify compound preconditions have individual checks for each component
```

**Pass 9: Verification and Authority** (was "Verification Checkpoints")

```markdown
### Pass 9: Verification and Authority
36. Identify instructions with high-risk factors (irreversible, ambiguous scope, domain-specific)
37. Verify each has an interpretation checkpoint or explicit confirmation step
38. Check that checkpoints specify observable state, not just "confirm understanding"
39. Flag instructions that could plausibly appear in multiple document types
40. For overlapping instructions, verify authority relationship is stated (overrides, defers to, scoped to)
41. Flag skill files—verify they state relationship to CLAUDE.md for overlapping concerns
42. Flag CLAUDE.md files—verify they state deference patterns for skills and subagents
43. Verify scope limitations are explicit, not assumed from document location
```

**Pass 10: Coherence** (renumber items)

```markdown
### Pass 10: Coherence
44. Read the document end-to-end: do sections contradict each other?
45. Would a fresh Claude session understand and follow these instructions without clarification?
46. Are there any loopholes you'd exploit if asked to comply minimally?
```

---

## Execution Order

1. **Structural fixes** (Phase 1) — independent, can be done in any order
   - 1.1 Applicability statement
   - 1.2 Progressive disclosure definition
   - 1.3 Self-check iteration loop

2. **Merge conflict sections** (Phase 2) — depends on knowing #13/#14 for Priority table

3. **Add new principles** (Phase 3)
   - 3.1 Add #13 after #12
   - 3.2 Add #14 after #13

4. **Update dependent sections** (Phase 4)
   - 4.1 Quick Reference table
   - 4.2 Grading Scale
   - 4.3 Self-Check Procedure (rename passes, add items, renumber)

---

## Verification

After all edits:

1. **Structural check:** Confirm document has consistent heading hierarchy
2. **Numbering check:** Verify Self-Check items are numbered 1-46 consecutively
3. **Cross-reference check:** Verify all principle numbers in Priority table and prose match actual principles
4. **Self-consistency check:** Run the document's own Self-Check Procedure against itself — should pass with no Priority 1-3 violations
