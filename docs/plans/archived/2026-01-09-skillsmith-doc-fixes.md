# Skillsmith Documentation Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix identified issues in skillsmith design and migration documents to ensure accuracy and consistency.

**Architecture:** Direct edits to two markdown files with verification after each fix.

**Tech Stack:** Markdown editing, no code changes

---

## Issues Summary

| ID | Doc | Issue | Fix |
|----|-----|-------|-----|
| C-1 | Design | File count "~30" is inaccurate | Update to "~33" with corrected breakdown |
| C-4 | Migration | Phase 3 header misleading | Rename to reflect both create and update |
| C-6 | Migration | Phase 5.1 verbose vs 5.2-5.4 brief | Remove template from 5.1, add design doc reference |

**Note:** C-2 and C-3 are deferred as low-impact (C-2 requires skillforge verification, C-3 values are acceptable).

---

### Task 1: Fix Design Doc File Count (C-1)

**Files:**
- Modify: `docs/plans/2026-01-09-skillsmith-design.md:169-179`

**Step 1: Verify actual file count**

Count from Section 2 tree structure:
- `.claude-plugin/plugin.json`: 1
- `agents/`: 4 files
- `skills/skillsmith/SKILL.md`: 1
- `references/spec/`: 4 files
- `references/workflow/`: 3 files
- `references/analysis/`: 3 files
- `references/review/`: 1 file
- `references/scripts/`: 2 files
- `references/spec-index.md`: 1 file
- `templates/`: 3 files
- `scripts/`: 2 + 2 test files = 4
- `commands/`: 3 files
- `README.md, LICENSE, CHANGELOG.md`: 3 files

Total: 1+4+1+4+3+3+1+2+1+3+4+3+3 = **33 files**

**Step 2: Update file count text**

Replace lines 169-179:

```markdown
**File counts:**

- Plugin config: 1 file (plugin.json)
- Reference docs: 14 files
- Templates: 3 files
- Agents: 4 files
- Scripts: 2 + 2 test files
- Commands: 3 files
- Skill: 1 file (SKILL.md)
- Other: 3 files (README, LICENSE, CHANGELOG)

**Total: 33 files**
```

**Step 3: Verify edit**

Run: `grep -n "Total:" docs/plans/2026-01-09-skillsmith-design.md`
Expected: Line shows "Total: 33 files"

**Step 4: Commit**

```bash
git add docs/plans/2026-01-09-skillsmith-design.md
git commit -m "fix(docs): correct skillsmith file count from ~30 to 33"
```

---

### Task 2: Clarify Migration Phase 3 Header (C-4)

**Files:**
- Modify: `docs/plans/2026-01-09-skillsmith-migration.md:157-165`

**Step 1: Review current header**

Current text (lines 157-165):
```markdown
## Phase 3: Create New Reference Files

**Goal:** Create new files that don't exist in either source.
```

Issue: Steps 3.2-3.4 UPDATE files copied in Phase 2, not create new.

**Step 2: Update header and goal**

Replace with:

```markdown
## Phase 3: Create and Update Reference Files

**Goal:** Create new files and update copied files to match skillsmith spec.
```

**Step 3: Verify edit**

Run: `grep -A2 "## Phase 3" docs/plans/2026-01-09-skillsmith-migration.md`
Expected: Shows "Create and Update Reference Files"

**Step 4: Commit**

```bash
git add docs/plans/2026-01-09-skillsmith-migration.md
git commit -m "fix(docs): clarify Phase 3 includes both create and update"
```

---

### Task 3: Normalize Migration Phase 5 Steps (C-6)

**Files:**
- Modify: `docs/plans/2026-01-09-skillsmith-migration.md:271-299`

**Step 1: Review current step 5.1**

Current step 5.1 (lines 272-277) has inline template:
```markdown
- [ ] 5.1 Create `agents/design-agent.md`:
  - Focus: Structure, patterns, technical correctness
  - Dimensions: Constraint completeness, Decision sufficiency, Minimality
  - Include spec consultation triggers
  - Follow agent review format from design doc Section 9
```

Steps 5.2-5.4 are brief, with only bullet points for focus/dimensions.

**Step 2: Normalize 5.1 to match 5.2-5.4 brevity**

Replace lines 272-277 with:

```markdown
- [ ] 5.1 Create `agents/design-agent.md`:
  - Focus: Structure, patterns, technical correctness
  - Dimensions: Constraint completeness, Decision sufficiency, Minimality
  - Reference: Design doc Section 9 (Agent Review Format)
```

**Step 3: Add consistent reference line to 5.2-5.4**

Update 5.2 (lines 279-282):
```markdown
- [ ] 5.2 Create `agents/audience-agent.md`:
  - Focus: Clarity, triggers, discoverability
  - Dimensions: Intent fidelity, Terminology clarity, Artifact usefulness
  - Reference: Design doc Section 9 (Agent Review Format)
```

Update 5.3 (lines 284-289):
```markdown
- [ ] 5.3 Create `agents/evolution-agent.md`:
  - Focus: Timelessness scoring, extension points, ecosystem fit
  - Threshold: Score ≥7 required
  - Reference: Design doc Section 9 (Agent Review Format), Section 11b (Timelessness)
```

Update 5.4 (lines 291-294):
```markdown
- [ ] 5.4 Create `agents/script-agent.md`:
  - Focus: Script quality (conditional—only if scripts/ exists)
  - Checks: Pattern compliance, self-verification, documentation
  - Reference: Design doc Section 9 (Agent Review Format)
```

**Step 4: Verify edit**

Run: `grep -A4 "5\.[1-4] Create" docs/plans/2026-01-09-skillsmith-migration.md`
Expected: All four steps show consistent structure with "Reference:" line

**Step 5: Commit**

```bash
git add docs/plans/2026-01-09-skillsmith-migration.md
git commit -m "fix(docs): normalize Phase 5 agent steps for consistency"
```

---

### Task 4: Final Verification

**Step 1: Run diff to confirm all changes**

```bash
git diff HEAD~3..HEAD --stat
```

Expected: 2 files changed

**Step 2: Review changes are complete**

```bash
git log --oneline -3
```

Expected:
```
fix(docs): normalize Phase 5 agent steps for consistency
fix(docs): clarify Phase 3 includes both create and update
fix(docs): correct skillsmith file count from ~30 to 33
```

---

## Deferred Issues

| ID | Reason |
|----|--------|
| C-2 | Requires verification of skillforge source structure—low impact if path is correct |
| C-3 | "Effort" column values (Low/Medium/High) are complexity ratings, not time estimates—acceptable |

---

## Success Criteria

| Criterion | Verification |
|-----------|--------------|
| File count accurate | Design doc shows "33 files" |
| Phase 3 header clear | Migration doc says "Create and Update" |
| Phase 5 normalized | All agent steps have consistent structure |
| No regressions | Both docs remain valid markdown |
