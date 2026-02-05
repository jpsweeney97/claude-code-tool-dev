# Simulation-Based Skill Assessment: Feasibility Spike

**Date:** 2026-02-04
**Status:** Complete
**Decision:** Proceed to Phase 2 (Skill Architecture Design)

---

## Executive Summary

This spike validates whether the simulation-based skill assessment framework is implementable given Claude Code's actual mechanics. All six experiments pass, confirming the approach is feasible with specific architectural constraints.

**Key Findings:**

1. **Skill injection works** — Skill content can be injected into subagents and produces expected behavioral changes
2. **Task framing required** — Injected content must be framed as task requirements, not system rules
3. **Background execution required** — Full observability (tool calls, parameters, results) requires background execution with output file parsing
4. **Skills hot-reload, subagents don't** — Skills created mid-session are immediately available; subagents require session restart
5. **`context: fork` is the recommended architecture** — Create dynamic skills with `context: fork` pointing to a static assessment subagent

**Recommended Architecture:**
- **Static subagent** (`assessment-runner`) — Defines tools, permissions, model; checked into repo
- **Dynamic skills** — Created per-scenario with `context: fork` + `agent: assessment-runner`
- **Skill tool** — Invokes dynamic skills (hot-reload ensures immediate availability)

---

## Experiment Results

### Experiment 1: Prompt Injection Baseline

**Question:** Can arbitrary instructional content influence subagent behavior?

| Test | Framing | Result |
|------|---------|--------|
| 1a | Instruction at start of prompt | ❌ Ignored |
| 1b | Instruction at end of prompt | ❌ Ignored |
| 1c | System rules framing ("You must...") | ❌ Ignored |
| 1d | Output format requirement | ✅ Followed |
| 1e | Conflicting instructions | Prohibition wins over format |

**Finding:** Subagents treat Task prompts as task descriptions, not system prompts. Instructions framed as "you must always X" are ignored; instructions framed as "output format: X" are followed.

**Implication:** Skill content must be reframed as task requirements, not behavioral rules.

---

### Experiment 2: Skill Content Injection

**Question:** Can multi-section skill content be injected and followed?

**Test:** Injected a "Code Quality Skill" with phase gates, completion markers, and process requirements.

| Skill Requirement | Baseline | With Skill Injected |
|-------------------|----------|---------------------|
| Phase 1: Design with edge cases | ❌ No design phase | ✅ Edge cases listed |
| "DESIGN COMPLETE" marker | ❌ Absent | ✅ Present |
| Phase 2: Docstring with examples | ❌ Minimal docstring | ✅ Full docstring |
| Phase 3: 3 test categories | ❌ One test block | ✅ Happy/edge/error |
| "VERIFICATION COMPLETE" marker | ❌ Absent | ✅ Present |

**Finding:** Skill content produces comprehensive behavioral changes when framed as "follow this process exactly."

---

### Experiment 3: Output Capture Fidelity

**Question:** What detail can be captured from subagent execution?

| Information | Synchronous Task | Background + File Parse |
|-------------|------------------|------------------------|
| Final output text | ✅ Summary only | ✅ Full |
| Tool calls count | ✅ | ✅ |
| Tool names | ❌ | ✅ |
| Tool parameters | ❌ | ✅ |
| Tool results | ❌ | ✅ |
| Token counts | ✅ Total only | ✅ Per-message |
| Timestamps | ❌ | ✅ |
| Message sequence | ❌ | ✅ UUID chain |

**Finding:** Synchronous Task returns summaries. Background execution writes JSONL with full detail to output file.

**Implication:** Use `run_in_background=true` and parse output file for process evaluation.

---

### Experiment 4: Controlled Conditions

**Question:** Can baseline and test runs be made identical except for skill presence?

| Comparison | Result |
|------------|--------|
| Baseline run 1 vs Baseline run 2 | Same substance, minor format variance |
| Test run 1 vs Test run 2 | Identical output |
| Baseline vs Test | Clear behavioral difference |
| Tool calls | Consistent across conditions |
| Token count | Consistent (~18,900) |

**Finding:** Same-condition runs are reproducible. Skill presence is a clean independent variable.

---

### Experiment 5: Cost Boundaries

**Question:** What are the token/time bounds for assessment?

| Task Complexity | Tokens | Tool Uses | Duration |
|-----------------|--------|-----------|----------|
| Simple (2+2) | 18,500 | 0 | ~2s |
| Medium (4-step analysis) | 25,961 | 3 | ~41s |

**Projected Assessment Cost:**

| Component | Tokens | Duration |
|-----------|--------|----------|
| Per scenario (baseline + test) | ~45K | ~1.5 min |
| Per iteration (5 scenarios) | ~225K | ~7.5 min |
| Full assessment (3 iterations) | ~675K | ~22 min |

**Finding:** Costs are bounded and predictable. Full assessment is affordable.

---

### Experiment 6: Skill Activation Simulation

**Question:** Does injected skill content produce expected structured behaviors?

**Test:** Injected writing-principles skill and compared to baseline review.

| Behavioral Marker | Baseline | With Skill Injected |
|-------------------|----------|---------------------|
| Structured workflow | ❌ Freeform list | ✅ Calibrate → Report → Wait |
| Risk calibration | ❌ Absent | ✅ "Assessment: Medium" |
| Violations table format | ❌ Numbered list | ✅ `\| Principle # \| Quote \| Issue \|` |
| Principle references | ❌ No numbers | ✅ "1 - Be Specific" |
| Gate compliance | ❌ No gates | ✅ "Awaiting direction" |

**Finding:** Injected skills produce expected structured behavior matching skill specifications.

---

## Constraints Discovered

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Task prompts are task-framed | Skills framed as "you must X" are ignored | Reframe as "follow this process" |
| Synchronous Task returns summaries | Can't see tool call details | Use background execution |
| Prohibitions override format requirements | Conflict resolution favors negatives | Avoid conflicting instructions |
| `skills` field requires literal names | Can't parameterize at runtime | Inject skill content into dynamic skill files |
| Subagents don't hot-reload | Dynamic subagent creation requires session restart | Use skills with `context: fork` instead |
| `/agents` reload ineffective | New agents not available after `/agents` | Use skills (which do hot-reload) |
| **Skills DO hot-reload** | ✅ Enabler, not constraint | Use dynamic skill files with `context: fork` |

---

## Architecture Insights

### Skills and Subagents Relationship

Claude Code provides two mechanisms for skill injection:

| Approach | How It Works | When to Use |
|----------|--------------|-------------|
| **Skill with `context: fork`** | SKILL.md content becomes task; agent type provides system prompt | Skill drives the subagent |
| **Subagent with `skills` field** | Subagent body is system prompt; skills preloaded into context | Static skill sets |
| **Manual prompt injection** | Skill content embedded in Task prompt | Dynamic skill selection |

### Recommended Architecture for Assessment

**Hybrid approach:** Use custom subagents for consistent configuration + manual injection for skill content.

```yaml
# .claude/agents/assessment-runner.md
---
name: assessment-runner
description: Execute assessment scenarios with consistent configuration
tools: Read, Grep, Glob, Bash, Write, Edit
permissionMode: acceptEdits
model: inherit
---
Execute the provided scenario task. Report your complete process including:
- Tools used and why
- Decisions made
- Final output

Follow any skill instructions provided in the task.
```

**Baseline invocation:**
```
Task(
  subagent_type: "assessment-runner",
  prompt: "Scenario: [task description]",
  run_in_background: true
)
```

**Test invocation (with skill):**
```
Task(
  subagent_type: "assessment-runner",
  prompt: """
    You have this skill loaded. Follow its instructions:
    ---
    [skill content]
    ---

    Scenario: [task description]
  """,
  run_in_background: true
)
```

### Architecture Evolution

The spike tested three approaches in sequence:

| Approach | Result | Details |
|----------|--------|---------|
| 1. Task tool + manual prompt injection | ✅ Works | Validated in Experiments 1-6 |
| 2. Dynamic subagent + `skills` field | ❌ Fails | Subagents don't hot-reload; see [Addendum 1](#addendum-dynamic-subagent-generation-test) |
| 3. Dynamic skill + `context: fork` | ✅ Works | Skills hot-reload; see [Addendum 2](#addendum-2-skills-with-context-fork--the-correct-architecture) |

**Final recommendation:** Use approach #3 (dynamic skills with `context: fork`) as the primary architecture, with approach #1 (Task tool injection) as a fallback.

| Factor | Task Tool Injection | Skill + `context: fork` |
|--------|--------------------|-----------------------|
| Official mechanism | ⚠️ Workaround | ✅ Designed for this |
| Separation of concerns | ❌ Mixed in prompt | ✅ Skill = task, Subagent = env |
| Subagent configuration | Limited | ✅ Full control |
| File management | None needed | Temp files to clean up |
| Hot-reload | N/A | ✅ Immediate |

---

## Output Parsing

Background execution produces JSONL at:
```
/private/tmp/claude-501/{project-path}/tasks/{agentId}.output
```

Each line is a JSON object containing:

```json
{
  "type": "assistant",
  "message": {
    "content": [
      {"type": "tool_use", "name": "Glob", "input": {"pattern": "**/*.md"}}
    ]
  },
  "timestamp": "2026-02-04T21:04:53.615Z"
}
```

**Parsing strategy:**
1. Read output file line by line
2. Parse each JSON object
3. Extract tool calls from `message.content` where `type: "tool_use"`
4. Extract tool results from `message.content` where `type: "tool_result"`
5. Reconstruct execution sequence from timestamps/UUIDs

---

## Decision

**All experiments pass. The framework is implementable.**

### Go Criteria Met

| Criterion | Status |
|-----------|--------|
| Skill content can be injected | ✅ Pass |
| Behavioral changes are observable | ✅ Pass |
| Controlled conditions achievable | ✅ Pass |
| Costs are bounded | ✅ Pass |
| Output capture sufficient for evaluation | ✅ Pass |
| Mid-session dynamic creation | ✅ Pass (via skills with `context: fork`) |

### Recommended Architecture

**Primary approach:** Dynamic skills with `context: fork`
- Static `assessment-runner` subagent defines execution environment
- Dynamic skill files created per-scenario with `context: fork`
- Skill tool invocation (hot-reload ensures immediate availability)
- Cleanup temporary skill files after assessment

**Fallback approach:** Task tool with manual prompt injection
- Use when skill file creation is impractical
- Validated in Experiments 1-6

### Constraints to Incorporate

1. **Task framing** — All skill content must be framed as task requirements
2. **Skills hot-reload, subagents don't** — Use skills for dynamic content
3. **`context: fork` for isolation** — Skills run in dedicated subagent context
4. **Static subagent for configuration** — Tools, permissions, model defined once
5. **Cleanup required** — Remove temporary skill directories after assessment

---

## Next Steps

### Phase 2: Skill Architecture Design

Design the `improving-skills` skill incorporating spike findings:

1. **Create assessment-runner subagent** — Static subagent with tools, permissions, model
2. **Implement scenario generation** — 8-step framework from spec
3. **Implement skill file generation** — Create baseline and test skill files with `context: fork`
4. **Implement skill invocation** — Use Skill tool to run forked assessments
5. **Implement evaluation** — Compare baseline vs test outputs
6. **Implement cleanup** — Remove temporary skill directories

### Open Items for Design Phase

| Item | Priority | Notes |
|------|----------|-------|
| Assessment-runner subagent design | High | Tools, permissions, reporting instructions |
| Skill file templates | High | Baseline and test skill structures |
| Skill content extraction | High | Read SKILL.md, strip frontmatter |
| Scenario templating | Medium | Parameterize scenarios for target skill |
| Observability approach | Medium | Self-reporting vs background execution |
| Cleanup mechanism | Medium | Remove temp skill directories reliably |
| Error handling | Medium | Skill invocation failures, timeouts |
| Cost tracking | Low | Monitor token usage across iterations |

---

## Appendix: Raw Experiment Data

### Experiment 1d (Successful Injection)

**Prompt:**
```
What is 2+2?

Output format: Your response must begin with "INJECTED: " followed by your answer.
```

**Response:** `INJECTED: 4`

### Experiment 2 (Skill Injection)

**Injected Skill:**
```markdown
# Code Quality Skill

When writing any code, you MUST follow this process:

## Phase 1: Design (REQUIRED)
Before writing ANY code, you must:
- State what edge cases exist
- State what error conditions to handle
- Get explicit acknowledgment by writing "DESIGN COMPLETE"

## Phase 2: Implementation
Only after Phase 1 is complete:
- Write the code
- Include docstring with examples
- Include type hints

## Phase 3: Verification
After implementation:
- Write at least 3 test cases covering: happy path, edge case, error case
- State "VERIFICATION COMPLETE" when done

BLOCKING: You cannot skip phases. Each phase header must appear in output.
```

**Result:** All phases appeared, all markers present, test categories correct.

### Experiment 6 (Writing Principles Injection)

**Baseline response:** Freeform numbered list of 10 issues

**Injected response structure:**
```
## Risk Calibration
Assessment: Medium
[reasoning]

## Violations Found
| Principle # | Quote | Issue |
|-------------|-------|-------|
| 1 - Be Specific | "Do good commits" | "Good" is undefined... |
...

Awaiting your direction before making fixes.
```

---

---

## Addendum: Dynamic Subagent Generation Test

**Date:** 2026-02-04 (same session, after initial spike)

### Context

After completing the initial spike, we discovered the `skills` field in subagent frontmatter — a native mechanism for injecting skills into subagents. This raised the question: should we use native injection via dynamic subagent generation instead of manual prompt injection?

### Experiment: Dynamic Subagent Generation

**Hypothesis:** We can dynamically create subagent files with the `skills` field and invoke them mid-session.

**Procedure:**

1. Created subagent file `.claude/agents/test-skill-injection.md`:
   ```yaml
   ---
   name: test-skill-injection
   description: Test subagent with writing-principles skill loaded
   skills:
     - writing-principles
   tools: Read, Grep, Glob
   model: haiku
   ---
   You are a document reviewer...
   ```

2. Attempted to invoke immediately via Task tool — **Failed** (agent not found)

3. User ran `/agents` command to reload — **Agent still not found**

4. Created simpler test without `skills` field (`test-simple.md`) — **Also not found after `/agents`**

5. Compared with working agents (`skill-explorer.md`, `claude-code-docs-researcher.md`) — File structure identical

### Results

| Test | Result |
|------|--------|
| Invoke immediately after file creation | ❌ Agent not found |
| Invoke after `/agents` reload | ❌ Agent not found |
| Simpler agent without `skills` field | ❌ Agent not found |
| Existing project agents (created before session) | ✅ Available |

### Findings

1. **`/agents` does not reload agents from disk mid-session** — Despite documentation stating it should, newly created agent files were not available after running `/agents`

2. **Session restart likely required** — The documentation states "restart your session or use `/agents`" but only session restart appears to work reliably

3. **Dynamic generation is not viable for single-session workflows** — Creating subagent files mid-session and expecting to use them immediately does not work

### Implications for Architecture

| Approach | Viability |
|----------|-----------|
| Manual prompt injection | ✅ Works mid-session, validated in spike |
| Dynamic file + `/agents` reload | ❌ Does not work (reload ineffective) |
| Dynamic file + session restart | ⚠️ Would work but breaks workflow |
| Pre-session setup | ✅ Would work but requires planning |

### Revised Recommendation

**Use manual prompt injection** for the improving-skills skill. It is:
- The only approach that works within a single session
- Validated in Experiments 1-2 and 6
- More flexible (no file system changes needed)

The `skills` field remains useful for:
- Static subagent configurations (checked into repo)
- Workflows where the skill set is known before session start

### Files Created During Test

```
.claude/agents/test-skill-injection.md  # With skills field
.claude/agents/test-simple.md           # Without skills field
```

These can be deleted or kept for future testing with session restart.

---

## Addendum 2: Skills with `context: fork` — The Correct Architecture

**Date:** 2026-02-04 (same session, after dynamic subagent test)

### The Key Insight

After the dynamic subagent generation test failed, we discovered a critical difference between skills and subagents:

| Component | Hot-Reload? | Mid-Session Creation | Official Mechanism |
|-----------|-------------|---------------------|-------------------|
| **Skills** | ✅ Yes | ✅ Immediately available | `context: fork` runs in subagent |
| **Subagents** | ❌ No | ❌ Requires session restart | `skills` field preloads skills |

**Skills hot-reload. Subagents don't.** This changes everything.

### The `context: fork` Mechanism

Skills can run in forked subagent contexts using frontmatter configuration:

```yaml
---
name: my-skill
context: fork          # Run in isolated subagent context
agent: general-purpose # Which subagent to use (built-in or custom)
---
[skill content becomes the task for the subagent]
```

When a skill with `context: fork` is invoked:
1. A new isolated context is created
2. The subagent receives the skill content as its task prompt
3. The `agent` field determines execution environment (model, tools, permissions)
4. Results are returned to the main conversation

### Experiment: Skill Hot-Reload with `context: fork`

**Hypothesis:** We can create skills mid-session that immediately run in forked subagent contexts.

**Procedure:**

1. Created skill file mid-session:
   ```yaml
   # .claude/skills/temp-fork-test/SKILL.md
   ---
   name: temp-fork-test
   description: Test skill hot-reload with context fork
   context: fork
   agent: general-purpose
   ---
   Answer this question: What is 2+2?

   Your response MUST begin with "FORKED-SKILL-RESPONSE: " followed by your answer.
   ```

2. Immediately invoked via Skill tool (no reload, no restart)

3. Observed result

**Result:** ✅ Complete success

```
Skill "temp-fork-test" completed (forked execution).

Result:
FORKED-SKILL-RESPONSE: 4
```

**Observations:**
- Skill was immediately available after file creation
- `context: fork` executed correctly in isolated context
- Format instruction was followed (demonstrating the skill content became the task)
- No `/skills` command or session restart required

### Why This Is Better Than Task Tool Injection

| Factor | Task Tool Injection | Skill with `context: fork` |
|--------|--------------------|-----------------------------|
| Official mechanism | ⚠️ Validated workaround | ✅ Designed for this |
| Hot-reload | N/A (no files) | ✅ Immediate |
| Separation of concerns | ❌ Task + skill mixed in prompt | ✅ Skill = task, Subagent = environment |
| Subagent configuration | ⚠️ Limited to subagent_type | ✅ Full control via custom subagent |
| Observability | ✅ Background + file parse | ✅ Same (when using background) |
| Cleanup | ❌ None needed | ⚠️ Temp skill files to clean |

### Revised Architecture

#### Component 1: Static Assessment Subagent

Create once, check into repository:

```yaml
# .claude/agents/assessment-runner.md
---
name: assessment-runner
description: Executes assessment scenarios with full tool access
tools: Read, Grep, Glob, Bash, Write, Edit
model: inherit
permissionMode: acceptEdits
---
You are an assessment executor. Execute the task provided in full.

Report your complete process including:
- Each tool you used and why
- Decisions you made
- Your reasoning at each step
- Final output

Do not summarize or abbreviate. The full process trace is needed for evaluation.
```

This subagent:
- Has all tools needed for realistic scenario execution
- Uses `acceptEdits` to avoid permission prompts during assessment
- Inherits model from parent (consistent evaluation)
- Instructs for full process reporting (needed for evaluation)

#### Component 2: Dynamic Baseline Skill

Created by improving-skills for each scenario:

```yaml
# .claude/skills/assessment-baseline-{scenario-id}/SKILL.md
---
name: assessment-baseline-{scenario-id}
description: Baseline assessment for scenario {id}
context: fork
agent: assessment-runner
---
## Scenario

{scenario setup and context}

## Task

{scenario trigger / user message}

## Instructions

Execute this task using your standard capabilities. Do not use any special skills or guidelines beyond your base training.

Report your complete process and final output.
```

#### Component 3: Dynamic Test Skill (With Target Skill Injected)

Created by improving-skills for each scenario:

```yaml
# .claude/skills/assessment-test-{scenario-id}/SKILL.md
---
name: assessment-test-{scenario-id}
description: Test assessment for scenario {id} with target skill
context: fork
agent: assessment-runner
---
## Loaded Skill

You have the following skill loaded. Follow its instructions throughout this task:

---
{target skill content - full SKILL.md minus frontmatter}
---

## Scenario

{scenario setup and context}

## Task

{scenario trigger / user message}

## Instructions

Execute this task while following the loaded skill above.

Report your complete process and final output.
```

#### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. SCENARIO GENERATION (8-step framework)                      │
│     Input: Target skill                                         │
│     Output: 5-7 prioritized scenarios                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. FOR EACH SCENARIO:                                          │
│                                                                 │
│     a. Create baseline skill file                               │
│        - context: fork                                          │
│        - agent: assessment-runner                               │
│        - Scenario task (no target skill)                        │
│                                                                 │
│     b. Invoke baseline skill                                    │
│        Skill(skill: "assessment-baseline-{id}")                 │
│                                                                 │
│     c. Create test skill file                                   │
│        - context: fork                                          │
│        - agent: assessment-runner                               │
│        - Target skill content + scenario task                   │
│                                                                 │
│     d. Invoke test skill                                        │
│        Skill(skill: "assessment-test-{id}")                     │
│                                                                 │
│     e. Evaluate delta between baseline and test                 │
│                                                                 │
│     f. Clean up temporary skill files                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. GAP ANALYSIS                                                │
│     Compare baseline vs test across all scenarios               │
│     Identify where skill helped / failed / hurt                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. ITERATION                                                   │
│     Fix identified gaps, re-run scenarios                       │
│     Repeat until threshold met                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Observability with Forked Skills

The Skill tool with `context: fork` returns the subagent's response. For full process observability (tool calls, parameters), we may need to:

1. **Check if Skill tool supports background execution** — If yes, parse output file as with Task tool
2. **Rely on subagent's self-reporting** — The assessment-runner prompt instructs full process reporting
3. **Use hooks** — Subagent hooks can capture tool usage during execution

The self-reporting approach is likely sufficient since:
- The assessment-runner explicitly requests full process traces
- We're evaluating whether skill instructions were followed, which is visible in the output
- Tool call sequences can be inferred from the narrative

### Comparison: All Approaches Tested

| Approach | Mid-Session | Works? | Recommended |
|----------|-------------|--------|-------------|
| Task tool + manual prompt injection | ✅ | ✅ | ⚠️ Fallback |
| Dynamic subagent + `/agents` reload | ✅ | ❌ | ❌ |
| Dynamic subagent + session restart | ❌ | ✅ (assumed) | ❌ |
| Pre-existing subagent with `skills` field | ❌ | ✅ | ⚠️ Static only |
| **Dynamic skill + `context: fork`** | ✅ | ✅ | ✅ **Recommended** |

### Updated Recommendations

#### Primary Approach: Skills with `context: fork`

For the improving-skills skill, use:

1. **Static assessment-runner subagent** — Defines execution environment (tools, permissions, model)
2. **Dynamic skill files** — Created per-scenario with `context: fork` and `agent: assessment-runner`
3. **Skill tool invocation** — Hot-reload ensures immediate availability
4. **Cleanup** — Remove temporary skill directories after assessment

#### Fallback Approach: Task Tool Injection

If skill creation fails or is impractical:

1. Use Task tool with `subagent_type: "general-purpose"` (or custom subagent if available)
2. Inject skill content directly into prompt using task-framing
3. Use `run_in_background: true` for full observability

### Files Created During Test

```
.claude/skills/temp-fork-test/SKILL.md  # context: fork test skill
```

This skill demonstrated:
- Immediate availability after creation (hot-reload works)
- Correct forked execution
- Instruction following in forked context

### Summary

The discovery of skill hot-reload with `context: fork` resolves the key architectural question:

| Question | Answer |
|----------|--------|
| How do we inject skills into subagents dynamically? | Create skill files with `context: fork` |
| How do we avoid session restart? | Skills hot-reload; use skills instead of subagents for dynamic content |
| How do we maintain clean separation? | Skill = task, Subagent = execution environment |
| What's the recommended architecture? | Static subagent + dynamic skills with `context: fork` |

This is a cleaner, more maintainable architecture than Task tool injection, using official mechanisms as designed.

---

## References

- Framework specification: `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`
- Discussion consolidation: `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md`
- Skills/subagents relationship: `docs/discussions/skills-subagents-relationship.md`
- Claude Code subagents documentation: https://code.claude.com/docs/en/sub-agents
