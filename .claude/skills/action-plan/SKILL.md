---
name: action-plan
description: >
  Produce a dependency-aware, gated action plan of strategic tasks from review findings,
  audit results, brainstorming output, retrospectives, or any analysis that surfaced multiple
  issues needing coordinated action. Use this skill whenever the user wants to turn findings
  into a plan, figure out what to tackle and in what order, prioritize work after a review or
  audit, or says things like "what do we do about all this?", "plan this out", "what's the
  sequence here", "how should we tackle these findings", "action plan", "create an action plan",
  or "what's the plan of attack?". Also trigger after a review, audit, retrospective, or
  brainstorming session completes and the natural next step is deciding what to do about the
  findings. Do NOT use for implementation planning (session-sized tasks with code changes) —
  that's the Next Steps protocol. This skill produces strategic tasks where "done" means
  the approach is agreed and ready for a focused follow-up session.
---

# Action Plan

Produce a dependency-aware, gated checklist of **high-level strategic tasks** from the conversation so far. This is a jumping-off point for deeper discussion via `/cross-model:dialogue` — not an implementation plan.

Tasks live at the level of "these two skills should be combined" or "this section needs a trust boundary defined", not "here is how to combine them."

## When This Skill Applies (and When It Doesn't)

| Use action-plan | Use Next Steps protocol instead |
|---|---|
| Findings from a review, audit, or brainstorm need to become coordinated work | A design decision is made and you need session-sized implementation tasks |
| "Done" = approach agreed, ready for follow-up session | "Done" = verifiable condition (tests pass, file exists) |
| Tasks are strategic: *what* should change and *why* | Tasks are tactical: *how* to change it, step by step |
| Output feeds into Codex dialogue or focused planning sessions | Output feeds directly into coding work |

If the conversation already has a clear implementation path, use the Next Steps protocol from CLAUDE.md instead. Action plans are for when the *direction* still needs to be decided, not just the *execution*.

## Ground Rules

- **Strategic, not implementation.** Each task names *what* should change and *why it matters*, not *how* to change it.
- **"Done" = approach agreed.** Every task's completion means the approach is agreed and the task is ready for a focused follow-up session. It does not mean the work is built.
- **No padding.** If there are 3 tasks, the plan has 3 tasks.
- **Flag ambiguity.** If the right sequence is uncertain, state what information would resolve it — don't guess.
- **Unblock decisions first.** Prefer the sequence that surfaces decision points earliest, not the sequence that starts with the most comfortable task.

## Output Format

Use exactly this structure:

### 1. Current State

One paragraph: what the review/analysis found, which findings are being acted on, and which are being parked. State any constraints already known (hard dependencies, out-of-scope items).

### 2. Dependency Map

Every discrete task needed to address the findings. For each, state what it depends on (or "none — can start now"). Use short task IDs (T1, T2, ...) for cross-reference.

**Format:**

- T1: \<task\> — depends on: none
- T2: \<task\> — depends on: T1
- T3: \<task\> — depends on: none (parallel to T1)

### 3. Sequenced Plan

Group tasks into phases from the dependency map. Within each phase, tasks are parallelizable. Between phases, there's a hard dependency.

**Phase 1** (can start now):
- T1: \<task\> — done when: \<approach agreed / question resolved / ready for follow-up session\>
- T3: \<task\> — done when: \<approach agreed / question resolved / ready for follow-up session\>

**Phase 2** (after Phase 1):
- T2: \<task\> — done when: \<approach agreed / question resolved / ready for follow-up session\>

### 4. Decision Gates

Call out any point where the plan branches based on an outcome:

- After T1: if \<condition\>, then \<path A\>; otherwise \<path B\>

If there are no meaningful decision points, say "None — all tasks have a single forward path."

### 5. Critical Path

**Scheduling:** The longest dependency chain — the sequence that sets the minimum number of sessions to complete the plan. State the chain (e.g., T1 → T3 → T5).

**Highest-risk task:** The single task with the highest (likelihood x impact) of stalling the plan. State: (1) which task, (2) the likelihood it stalls, (3) the impact if it does, (4) whether it's on the critical path, and (5) why. Recommend starting here.

**Example:** "T2 (webhook reliability) — likelihood: high (silent event loss is already happening in production), impact: high (customers losing data erodes trust faster than any other issue). On the critical path. Start here because delayed action compounds the damage."

**Self-check:** Verify that the critical path chain is derivable from the Dependency Map. Every link in the chain (e.g., T1 → T4) must correspond to a "depends on" declaration above. If the chain doesn't match, fix the dependency map or the chain.

### 6. Out of Scope (Parked)

Findings from the review that are worth addressing eventually but not required for the immediate goal. 3-5 items max, one-line descriptions. These are not in the task list above.

## After Producing the Plan

Suggest the user take the highest-risk or first-phase tasks into a Codex dialogue for deeper exploration. Use the literal slash command `/cross-model:dialogue` so the user can invoke it directly.

**Example:** "Want me to start a `/cross-model:dialogue` on T1 to work through the approach?"
