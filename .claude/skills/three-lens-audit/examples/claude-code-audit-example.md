# Worked Example: Auditing a Claude Code Skill Design

This example shows actual output from a `--claude-code` audit of a proposed "smart-refactor" skill.

---

## Target

A draft skill design document proposing an automated refactoring assistant:

```markdown
# Smart Refactor Skill (Draft)

## Overview
Automatically identify and apply refactoring opportunities across a codebase.

## Workflow
1. User invokes `/smart-refactor <directory>`
2. Claude scans all files for patterns (duplication, long functions, unused imports)
3. Claude presents a ranked list of refactoring opportunities
4. User approves selections
5. Claude applies all approved refactorings in parallel
6. Claude runs tests to verify no breakage
7. Claude commits changes with descriptive message

## Features
- Pattern detection across multiple files
- Parallel refactoring application
- Automatic test verification
- Git integration for safe rollback

## Triggers
- `/smart-refactor`
- `refactor this codebase`
```

---

## Agent Outputs

### Implementation Realist

**Artifact Type:** Skill (SKILL.md with multi-phase workflow)

### Works Today

| Element | Tool Required | Confidence | Notes |
|---------|---------------|------------|-------|
| Scan directory for files | Glob, Read | High | Standard file operations |
| Identify pattern (single file) | Read | Medium | Claude can reason about code |
| Present list to user | Output | High | Text generation |
| Apply single edit | Edit | High | With prior Read |
| Run tests | Bash | High | If test command known |
| Git commit | Bash | High | Standard git operations |

### Capability Gaps

| Assumption | Reality | Evidence | Severity |
|------------|---------|----------|----------|
| "Scan all files" is feasible | Context limits (~200K tokens) prevent loading large codebases | Session context documented in capabilities reference | Critical |
| Cross-file pattern detection | Requires holding multiple files in context simultaneously | Limited working memory per reasoning step | Major |
| "Apply all in parallel" | Parallel Edit calls may conflict on overlapping regions | Edit tool requires unique old_string | Major |
| Test verification always possible | Test command varies by project; may timeout for slow suites | Bash timeout defaults to 2 min | Minor |

### Artifact Checklist Failures

| Item | Status | Issue |
|------|--------|-------|
| Description includes when/why to use | Partial | Description is generic; doesn't explain specific contexts |
| SKILL.md body under 500 lines | Pass | Draft is concise |
| YAML uses only documented properties | Unknown | Draft doesn't show frontmatter |

**Note:** Skills are matched semantically via description; there is no separate "trigger phrases" field (per official docs).

### Behavioral Risks

**Cross-file reasoning:** Claude can analyze individual files well, but maintaining consistent understanding across 20+ files while identifying duplicated patterns requires holding too much context. The skill assumes Claude can "see" the whole codebase at once.

**Parallel application:** The workflow says "applies all approved refactorings in parallel" but Edit operations on the same file will conflict. If refactoring A changes lines 10-15 and refactoring B changes lines 12-18, parallel execution fails.

**User approval ambiguity:** "User approves selections" is vague. Does Claude wait? Present a numbered list? How does the user specify which items?

### State Assumptions

| Assumption | Reality |
|------------|---------|
| Remember analysis across workflow phases | Within-session only; if session ends, analysis lost |
| Track which refactorings applied | No native state; requires file-based tracking |
| Rollback on test failure | Git provides this, but skill must handle the git reset logic |

### Economic Viability

**Token cost:** Scanning 50 files × ~500 tokens avg = 25K input tokens just for initial scan. Pattern analysis would require multiple passes. Estimated 100K+ tokens for medium codebase.

**Latency:** Multiple Opus reasoning steps for pattern detection. User waits 2-5 minutes for analysis before seeing any results.

**Comparison:** Manual inspection of hot spots (identified via test coverage or git churn) would be faster for most real use cases.

### Verdict

**Implementability: Low-Medium**

The core idea is sound but the implementation assumes capabilities that don't exist at scale:

1. **Scale limitation:** Works for <10 files; breaks for real codebases
2. **Parallelism issue:** Must serialize edits or detect conflicts
3. **State gap:** Needs explicit state management for multi-phase workflow

**What would need to change:**
- Scope to single-directory or explicit file list (not "codebase")
- Serialize edit applications with conflict detection
- Add TodoWrite for state tracking across phases
- Define explicit approval UX (numbered list + user response)

---

### Adversarial Auditor

| Vulnerability | Evidence | Attack Scenario | Severity |
|--------------|----------|-----------------|----------|
| No scope boundaries | "Scan all files" with no exclusions | Refactors node_modules/, .git/, or generated files | Major |
| Auto-commit without review | Step 7 commits "with descriptive message" | Commits incorrect refactoring before user notices | Major |
| Test false positive | "Run tests to verify no breakage" | Tests pass but runtime behavior changes (e.g., performance regression) | Minor |
| Parallel edit races | "Applies all approved refactorings in parallel" | Two edits overlap → one fails silently or corrupts file | Critical |
| No rollback UX | "Git integration for safe rollback" but no user trigger | User doesn't know how to undo; rollback mechanism exists but isn't exposed | Minor |

**Meta-Critique:** The skill optimizes for the happy path. Every step assumes success. What happens when:
- Pattern detection is wrong? (No confidence scoring)
- Test command isn't known? (Skill halts with no guidance)
- Refactoring introduces bug not caught by tests? (No escape hatch)

---

### Cost/Benefit Analyst

| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Pattern scanning | High (tokens, latency) | Medium | Over-invested — most patterns obvious to developers |
| Ranked presentation | Low | High | Worth it — helps prioritization |
| Parallel application | High (conflict handling) | Low | Cut — serial is simpler and safer |
| Test verification | Medium | High | Worth it — catches breakage |
| Auto-commit | Low | Low | Cut — too risky for marginal convenience |

**High-ROI Elements:**
- Single-file refactoring suggestions with confidence scores
- Test verification before any commit
- Explicit user approval with clear UX

**Low-ROI Elements:**
- Cross-codebase pattern detection (too expensive, too error-prone)
- Parallel application (complexity exceeds benefit)
- Auto-commit (risk exceeds convenience)

**Recommendations:**
1. Scope to single file or explicit file list — removes scalability issues
2. Drop parallel application — serial with conflict check is safer
3. Make commit opt-in — user runs `/commit` separately
4. Add confidence scores — let user filter low-confidence suggestions

---

## Synthesis

### Convergent Findings (All 3 Lenses)

| Finding | Implementation | Adversarial | Cost/Benefit |
|---------|---------------|-------------|--------------|
| Parallel edit is problematic | "Parallel Edit calls may conflict" | "Two edits overlap → one fails silently" | "Complexity exceeds benefit" |
| Scale assumptions unrealistic | "Context limits prevent loading large codebases" | "Scan all files with no exclusions" | "Cross-codebase detection too expensive" |
| Auto-commit is risky | (implied in state assumptions) | "Commits incorrect refactoring before user notices" | "Risk exceeds convenience" |

**Assessment:** All three lenses independently flagged parallel editing and auto-commit as problems. Scale limitations appeared in all perspectives. This is the critical path — the skill cannot ship without addressing these.

### Convergent Findings (2 Lenses)

| Finding | Lenses | Evidence |
|---------|--------|----------|
| Missing rollback UX | Adversarial, Cost/Benefit | "User doesn't know how to undo" + "Make commit opt-in" |
| No confidence scoring | Adversarial, Cost/Benefit | "No confidence scoring" + "Add confidence scores" |

### Lens-Specific Insights

**Implementation Only:**
- Trigger phrases insufficient (only 2 defined)
- TodoWrite needed for multi-phase state tracking
- Bash timeout may block long test suites

**Adversarial Only:**
- Tests may pass but behavior changes (performance regressions)
- No exclusion patterns for node_modules, generated files

**Cost/Benefit Only:**
- Most patterns obvious to developers anyway
- Single-file scope delivers 80% of value

### Prioritized Recommendations

| Priority | Issue | Fix | Effort | Convergence |
|----------|-------|-----|--------|-------------|
| 1 | Parallel edit conflicts | Serialize edits with conflict detection | Medium | All 3 |
| 2 | Scale assumptions | Scope to explicit file list (max 10 files) | Low | All 3 |
| 3 | Auto-commit risk | Remove auto-commit; user runs `/commit` | Low | All 3 |
| 4 | No rollback UX | Add "undo last refactoring" command | Low | 2 lenses |
| 5 | No confidence scores | Add High/Medium/Low confidence to suggestions | Medium | 2 lenses |
| 6 | Insufficient triggers | Add 3 more varied trigger phrases | Low | 1 lens |

### Summary

**Overall assessment:** The skill concept is valuable but over-scoped. It tries to solve "refactor a codebase" when Claude Code can reliably solve "refactor these specific files."

**Critical path:**
1. Reduce scope from "codebase" to "file list"
2. Remove parallel editing
3. Remove auto-commit

**After fixes:** A focused "suggest refactorings for <files>, let user approve, apply serially, verify tests" skill is implementable and useful.

---

## Key Observations

1. **Implementation lens caught capability gaps** — The artifact-specific checklist identified missing triggers; the behavioral analysis identified the core scalability issue
2. **Adversarial lens found the critical bug** — Parallel edit races would cause silent file corruption
3. **Cost/Benefit quantified the over-engineering** — Cross-codebase analysis is expensive for marginal value
4. **Convergence reveals the redesign** — All three lenses point to a simpler, scoped-down skill as the right solution

This example demonstrates how `--claude-code` audits surface implementation reality that abstract design review would miss.
