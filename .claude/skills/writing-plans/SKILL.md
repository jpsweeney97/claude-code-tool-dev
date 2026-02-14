---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

Write implementation plans in three phases: research, outline, write. Plans assume the implementing engineer has zero codebase context and needs exact file paths, complete code, and step-by-step instructions.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

---

## Phase 1: Research

Gather the information needed to write the plan without consuming the main context window.

**Default:** Use subagents (Explore or general-purpose) for all research. Each subagent reads source files, extracts what's relevant, and returns a focused summary — not raw file contents.

**Exception:** Skip subagent research if you already have full context from the current session (e.g., from brainstorming or a prior phase).

### How to research

1. Read the spec/requirements to understand what needs to be planned
2. Identify what you need to know — examples:
   - What types, interfaces, or API contracts exist?
   - What patterns does the existing code follow?
   - What test infrastructure and patterns are available?
   - What does the target module depend on? What depends on it?
   - What decisions or constraints were established in prior work?
3. Dispatch subagents with specific questions. Prefer "What are the fields and invariants on `ScoutOptionRecord`?" over "Summarize state.py"
4. If a summary reveals something that needs verbatim precision (e.g., an exact type signature the plan must reference), read just that narrow section directly

**Gate:** Do not proceed to Phase 2 until your research questions are answered.

---

## Phase 2: Outline

Create the plan document skeleton and save it to disk before writing detailed task steps.

### Plan header

Every plan starts with this header. Include all fields that apply:

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Reference:** [Link to spec, master plan, or design doc that's authoritative for this plan]

**Branch:** Create `feature/<name>` from `main`.

**Test command:** [Exact command to run tests]

**Dependencies between tasks:**
- Task N: independent
- Task M: depends on Task N (reason)
```

### Task list

List each task with:
- Title
- Files (create/modify/test)
- Ordering rationale (why this sequence)

No step-level detail yet — that's Phase 3.

### Save and review

1. Write the outline to `docs/plans/YYYY-MM-DD-<feature-name>.md`
2. Present the outline to the user
3. Wait for approval before proceeding to Phase 3

Saving the outline preserves progress if the session reaches its context limit.

**Gate:** User approval required before Phase 3.

---

## Phase 3: Write

Expand each task with detailed, bite-sized steps.

### Task granularity

Each step is one action (2-5 minutes):
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

### Task structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

(Add more steps as needed — verification steps, full suite runs, multi-file coordination)

**Step N: Commit**

```bash
git add <specific files>
git commit -m "feat: description of what this task delivers"
```
````

Step count varies by task complexity. Simple tasks may have 5 steps. Coordinated multi-file changes may have 8-10. Every task ends with a commit.

### Final sections

After all tasks, add:

```markdown
## Final Verification

Run: [full test suite command]
Expected: All tests pass ([count] existing + [count] new)

Run: [lint command]
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `file.py` | New | Description |
| `other.py` | Modified | Description |
```

### Save incrementally

Update the plan file as you complete each task's detailed steps. Don't hold everything in memory until the end.

---

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans

---

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
