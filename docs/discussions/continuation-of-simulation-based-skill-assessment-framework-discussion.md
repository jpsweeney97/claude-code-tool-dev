---
title: Simulation-Based Skill Assessment Framework Review
date: 2026-02-04
model: Opus 4.5
version: Claude Code v2.1.31
---

# Simulation-Based Skill Assessment Framework Review

## Table of Contents

- [Turn 1: User](#turn-1-user)
- [Turn 2: Claude](#turn-2-Claude)
- [Turn 3: User](#turn-3-user)
- [Turn 4: Claude](#turn-4-Claude)
- [Turn 5: User](#turn-5-user)
- [Turn 6: Claude](#turn-6-Claude)
- [Turn 7: User](#turn-7-user)
- [Turn 8: Claude](#turn-8-Claude)
- [Turn 9: User](#turn-9-user)
- [Turn 10: Claude](#turn-10-Claude)

## Turn 1: User

Read this and share your interpretation:

`docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`

[Tool #1: Read docs/frameworks/simulation-based-skill-assessment_v0.1.0.md]

## Turn 2: Claude

I've read the simulation-based skill assessment framework. Here's my interpretation:

### What It Is

A specification for rebuilding the improving-skills skill. The current skill fails because it assesses structural compliance (does this follow skills-guide.md?) rather than functional effectiveness (does this actually work when Claude uses it?).

### The Core Problem

**Structural compliance ≠ functional effectiveness**

A skill can score perfectly on every structural checklist—trigger phrases present, under 500 lines, blocking language used—and still completely fail at its stated purpose. The existing skill assessed the former while claiming to measure the latter.

Why this happens: Structural checks are binary and verifiable. Functional effectiveness requires actually running the skill and observing behavior. Systems default to measuring what's easy to measure.

### The Solution: Empirical Testing with Subagents

Instead of reasoning about what should happen, observe what actually happens:

1. Baseline subagent - runs a task WITHOUT the skill
2. Test subagent - runs the SAME task WITH the skill injected
3. Delta evaluation - compare behaviors and measure improvement

This treats skill improvement as empirical science, not code review.

### The 8-Step Scenario Generation Framework

The document's primary contribution is a detailed procedure for generating 5-7 test scenarios:

| Step                               | Purpose                                                          |
| ---------------------------------- | ---------------------------------------------------------------- |
| 1. Purpose Determination           | What is the skill actually trying to achieve?                    |
| 2. Skill Type Classification       | Discipline/Technique/Pattern/Reference                           |
| 3. Use Case Extraction             | Gather scenario seeds from documentation or generate them        |
| 4. Trigger Condition Analysis      | When should/shouldn't the skill activate?                        |
| 5. Instruction → Behavior Mapping  | Transform vague instructions into observable, testable behaviors |
| 6. Expected Behavior Derivation    | What behaviors does this skill type predict?                     |
| 7. Adversarial Scenario Generation | Edge cases, boundary conditions, shortcut temptations            |
| 8. Scenario Assembly               | Prioritize (P0/P1/P2) and select final suite                     |

Step 5 is the most complex—it includes procedures for operationalizing subjective terms like "quality" or "thorough" into observable proxies.

### Key Design Insights

**Dual-path design:** Each step has extraction (when skill provides material) and generation (when it doesn't) paths. The difficulty of generation is diagnostic—if the framework struggles because the skill is unclear, Claude will struggle too.

**Quality over quantity:** 5-7 well-chosen scenarios covering happy paths, edge cases, and boundaries matter more than volume.

**Variance is signal:** If 4 scenarios pass and 1 fails, that outlier reveals where the skill behaves differently. Investigate it.

**Holdout scenarios:** Reserve 1-2 scenarios for final validation only to detect overfitting.

### Acknowledged Limitations

| Limitation            | Why It Matters                                                             |
| --------------------- | -------------------------------------------------------------------------- |
| Multi-session effects | Subagents are isolated—can't observe accumulation                          |
| Skill interactions    | Testing in isolation may miss conflicts                                    |
| The Oracle Problem    | To judge correctness, you need to know what correct looks like             |
| Irreducible judgment  | Proxy selection, goal inference, purpose centrality require human judgment |

The framework structures judgment rather than eliminating it. Judgment points are explicit and traceable.

### Current Status

| Phase                        | Status                     |
| ---------------------------- | -------------------------- |
| 1. Framework specification   | ✓ Complete (this document) |
| 2. Skill architecture design | Not started                |
| 3. Subagent orchestration    | Not started                |
| 4. Worked example            | Not started                |
| 5. Skill implementation      | Not started                |
| 6. Validation                | Not started                |

### My Take

**Insight:** This framework addresses a genuine epistemological problem. The original skill conflated checking that something looks right with verifying it works. The solution—empirical measurement via controlled A/B testing with subagents—is sound. The document is unusually self-aware about its limitations. It explicitly acknowledges the oracle problem, irreducible judgment, and that it "pushes the problem up a level rather than solving it completely." The real test will be Phase 4. A worked example applying this to an actual skill will reveal whether the 8-step process produces useful scenarios or gets mired in the complexity of operationalizing vague instructions.

What would you like to do with this? The document is ready to be used for manual skill assessment, or we could work on one of the open items (skill architecture, subagent orchestration, worked example).

## Turn 3: User

Do you see any significant gaps in the framework document `simulation-based-skill-assessment_v0.1.0.md`, or is it sound?

## Turn 4: Claude

Let me examine this critically. I'll distinguish between gaps that could block implementation and gaps that are acknowledged limitations.

### Significant Gaps

#### 1. Subagent Skill Injection Is Mechanically Undefined

The document assumes you can inject a skill into a subagent's system prompt, but skills in Claude Code aren't just text:

- Skills have frontmatter with trigger conditions
- Skills are loaded via the Skill tool, not raw prompt injection
- The subagent spawned via Task has its own isolated context—how does skill invocation work there?

The document says "the skill will handle how to spawn and capture" but this isn't a minor implementation detail. The mechanics constrain what's testable. For example:

- Can you inject a skill without the user invoking it?
- Does the subagent have access to Skill tool?
- How do you ensure the skill activates for the scenario?

This could block implementation.

#### 2. The Oracle Problem Has No Mitigation Strategy

The document acknowledges "Claude-as-evaluator" has the same biases as the subagent being tested, then says this "mitigates but doesn't fully solve" the problem—but offers no actual mitigation.

Possible mitigations not explored:

- Planted issues: Create scenarios with known failures to calibrate evaluator
- Multiple evaluator personas: Have evaluator argue against itself
- Ground truth scenarios: Skills where correct behavior is unambiguous
- Human spot-checks: Sample verification to catch systematic evaluator errors

Without mitigation, you could have systematically biased assessments that look rigorous.

#### 3. Scenario Execution Mechanics Are Missing

Section 4 describes what to observe but not how:

| Question                                   | Not Answered                                     |
| ------------------------------------------ | ------------------------------------------------ |
| What's the token/time budget per scenario? | Unbounded = expensive; too short = incomplete    |
| How do you capture reasoning traces?       | Task tool returns summary, not raw output        |
| What if subagent hangs or loops?           | No timeout/termination guidance                  |
| How do you ensure identical conditions?    | "Same task" but what about stochastic variation? |

#### 4. Delta Evaluation Assumes Comparable Behaviors

The framework compares "did baseline do X" vs "did test do X"—but what if:

- They took completely different approaches (both valid)?
- The skill caused unexpected-but-good behavior?
- The skill caused the subagent to ask clarifying questions (changing the task)?

The evaluation schema has no category for "skill changed the approach in ways not anticipated by the scenario."

#### 5. No Scenario Generation Failure Protocol

What happens when:

- You can't generate 5 scenarios? (Proceed with fewer? Block?)
- All scenarios are P2? (No critical path to test)
- Step 5 fails to operationalize key instructions? (Skip them? Flag the skill?)

The document has "purpose-incoherent" as a terminal state but doesn't handle partial failures.

### Moderate Gaps

#### 6. Holdout Set Is Too Small for Statistical Confidence

1-2 holdout scenarios from 5-7 total means a single pass/fail could be noise. The document treats this as a strong generalization signal, but with n=1 or n=2, you can't distinguish skill improvement from variance.

#### 7. Reference Skills Are Underspecified

For reference skills, testing "does it surface correct information" requires ground truth. But:

- Where does ground truth come from?
- What if the reference content is stale?
- How do you test "query guidance" without actual search results?

This skill type gets the least attention despite being arguably hardest to test.

#### 8. Cost Model Doesn't Enable Decisions

The document estimates "~31 subagent/analysis operations" but doesn't translate to tokens, time, or money. Without this, you can't answer "is this skill worth the assessment cost?" The principle "expensive-but-works beats cheap-but-broken" isn't actionable guidance.

### Acknowledged but Under-Addressed

#### 9. The Fundamental Tension

The document says:

> If purposes are unclear, the framework tests whether skills match their documentation—which is a sophisticated form of structural compliance, not functional assessment.

This is the same failure mode as the original skill, just at a higher level. The document acknowledges it then moves on. This deserves more attention—perhaps a procedure for detecting when you've fallen into this trap.

#### 10. No Calibration Procedure

How do you know your scenarios are at the right difficulty? If baseline always fails → no signal. If baseline always passes → skill adds no value. There's no procedure for calibrating scenario difficulty before running full assessment.

### Verdict

The framework is conceptually sound but has implementation-blocking gaps in:

1. Subagent skill injection mechanics
2. Scenario execution mechanics
3. Failure protocols

These aren't things you can handwave during Phase 3—they constrain what the framework can actually test.

**Insight:** The document is a specification, not a design. It says what should happen at each step but often not how it can happen given Claude Code's actual mechanics. Phase 2 (skill architecture) and Phase 3 (subagent orchestration) will need to resolve whether the specification is implementable—and may require revising the specification when constraints surface. The oracle problem is the largest conceptual gap. Every other gap is mechanical; this one is epistemological. If Claude evaluates Claude, what confidence can we have in the verdicts?

Would you like me to draft additions addressing any of these gaps?

## Turn 5: User

What is the dependency order? Do these gaps need to be resolved before design, or does design need to be completed to address these gaps?

## Turn 6: Claude

Good question. Let me map the dependencies.

### Dependency Graph

```
PHASE 0: FEASIBILITY SPIKE
├── Can skills be injected into subagents at all?
│   ├── If NO → Framework is unimplementable as specified
│   └── If YES → Reveals constraints that shape everything else
└── Gaps resolved: #1 (Subagent Injection), #3 (Execution Mechanics)
            │
            ▼
SPECIFICATION REVISION (can happen in parallel with spike)
├── These are spec gaps, not design gaps:
│   • #4 Delta Evaluation - add categories for divergent approaches
│   • #5 Failure Protocol - define behavior when steps fail
│   • #7 Reference Skills - specify ground truth requirements
│   • #9 Fundamental Tension - add detection procedure
└── These don't depend on implementation details.
            │
            ▼
PHASE 2-3: DESIGN (Skill Architecture + Subagent Orchestration)
├── Now informed by:
│   • What subagent mechanics actually allow
│   • Revised specification
└── Design will resolve:
    • #8 Cost Model (actual token/time costs become measurable)
    • #10 Calibration (what's measurable determines calibration approach)
            │
            ▼
PARALLEL: ORACLE MITIGATION
├── #2 can be addressed at any point, but benefits from knowing:
│   • What observations are capturable (from spike)
│   • What the cost budget allows (from design)
└── Could prototype mitigation strategies during Phase 4 (Worked Example)
            │
            ▼
PHASE 4: WORKED EXAMPLE
└── Reveals whether all the above actually works in practice.
    #6 (Holdout sizing) can be calibrated here based on observed variance.
```

### The Critical Path

Gap #1 (Subagent Skill Injection) blocks everything. Until you know whether skills can be injected into subagents—and under what constraints—you can't design the orchestration layer.

This suggests a Phase 0: Feasibility Spike before proceeding:

| Question                                                       | Test                                       |
| -------------------------------------------------------------- | ------------------------------------------ |
| Can you inject arbitrary text into a subagent's system prompt? | Spawn Task with custom prompt content      |
| Can you inject a skill specifically?                           | Try injecting skill content as prompt text |
| Does the subagent have access to Skill tool?                   | Check tool availability in subagent        |
| Can you capture the subagent's full response (not summary)?    | Examine Task tool output                   |
| What are the token/time limits?                                | Push boundaries, observe failures          |

If the spike reveals that skills cannot be injected as the framework assumes, you have three options:

1. Revise the framework to work with available mechanics
2. Build custom tooling (MCP server?) to enable injection
3. Abandon the approach

### Summary Table

| Gap                    | When to Address                         | Blocking? |
| ---------------------- | --------------------------------------- | --------- |
| #1 Subagent Injection  | Before design (feasibility spike)       | Yes       |
| #3 Execution Mechanics | Before design (feasibility spike)       | Yes       |
| #4 Delta Evaluation    | Before or during design (spec revision) | No        |
| #5 Failure Protocol    | Before or during design (spec revision) | No        |
| #7 Reference Skills    | Before or during design (spec revision) | No        |
| #9 Fundamental Tension | Before or during design (spec revision) | No        |
| #2 Oracle Mitigation   | During or after design                  | No        |
| #8 Cost Model          | After design (needs measurements)       | No        |
| #10 Calibration        | After design (needs measurements)       | No        |
| #6 Holdout Sizing      | During worked example                   | No        |

**Insight:** The document's roadmap is slightly out of order. It lists: 1. Framework specification ✓, 2. Skill architecture design, 3. Subagent orchestration. But subagent orchestration constraints should be discovered before designing the skill architecture, because the skill's design depends on what the orchestration layer can actually do. A feasibility spike should precede both.

Recommendation: Run the feasibility spike first. It's cheap (a few experiments with Task tool), and it will either validate the approach or surface constraints that reshape everything downstream.

Want me to draft the feasibility spike experiments?

## Turn 7: User

methodically draft the feasibility spike experiments

## Turn 8: Claude

I'll draft a structured feasibility spike with clear hypotheses, procedures, and decision criteria.

### Feasibility Spike: Subagent-Based Skill Assessment

#### Purpose

Determine whether the simulation-based skill assessment framework is implementable given Claude Code's actual mechanics. The spike answers blocking questions before investing in full design.

#### Success Criteria

The framework is feasible if ALL of the following are true:

1. Skill content can be injected into subagent context (baseline vs test differentiation possible)
2. Subagent outputs can be captured with sufficient detail for evaluation
3. Controlled conditions can be maintained between baseline and test runs
4. Cost is bounded and predictable

If any criterion fails, document the constraint and identify workarounds before proceeding.

---

### Experiment 1: Prompt Injection Baseline

**Question:** Can arbitrary instructional content be injected into a subagent's context via the Task tool prompt?

**Hypothesis:** The Task tool's prompt parameter accepts arbitrary text that becomes part of the subagent's operating context.

**Procedure:**

1. Create a simple behavioral instruction: "When asked any question, always begin your response with 'INJECTED: '"

2. Spawn a subagent with this instruction in the prompt:

   ```
   Task(
     subagent_type: "general-purpose",
     prompt: "[instruction above] + Now answer: What is 2+2?"
   )
   ```

3. Observe whether the subagent's response begins with "INJECTED: "

4. Repeat with variations:
   - a. Instruction at start of prompt
   - b. Instruction at end of prompt
   - c. Instruction in middle of prompt
   - d. Conflicting instruction (e.g., "Never say INJECTED")

**Success Criteria:**

- Subagent follows injected instruction in at least one position
- Position sensitivity documented (does placement matter?)
- Conflict resolution behavior documented

**Failure Implications:**

If prompt injection doesn't influence behavior:

- Subagents may have fixed system prompts that override user content
- May need alternative injection mechanism (MCP server, custom agent type)

---

### Experiment 2: Skill Content Injection

**Question:** Can actual skill content (multi-section markdown with instructions) be injected and followed?

**Hypothesis:** Skill content injected via prompt will be treated as operating instructions by the subagent.

**Procedure:**

1. Select a simple, testable skill with clear behavioral markers. Candidate: A skill that requires specific output format or process steps.

2. Extract the skill's SKILL.md content (without frontmatter).

3. Create two subagents:

   **BASELINE:**

   ```
   Task(
     subagent_type: "general-purpose",
     prompt: "Complete this task: [task that skill addresses]"
   )
   ```

   **TEST:**

   ```
   Task(
     subagent_type: "general-purpose",
     prompt: "
       You have the following skill loaded:
       ---
       [skill content]
       ---

       Complete this task: [same task]
     "
   )
   ```

4. Compare outputs:
   - Does TEST show skill-specific behaviors absent from BASELINE?
   - Does TEST follow skill instructions?
   - Does TEST acknowledge the skill?

**Test Skills (in order of complexity):**

| Skill              | Observable Marker                 | Why This Skill                 |
| ------------------ | --------------------------------- | ------------------------------ |
| A formatting skill | Output structure matches template | Binary pass/fail               |
| A process skill    | Specific steps executed in order  | Sequence observable            |
| A discipline skill | Gates enforced, shortcuts avoided | Hardest case—tests enforcement |

**Success Criteria:**

- Observable behavioral difference between BASELINE and TEST
- TEST follows at least core skill instructions
- Skill complexity level where injection stops working is identified

**Failure Implications:**

If skill content doesn't transfer:

- May need structured injection format
- May need to prime subagent with skill acknowledgment
- May need skill-aware agent type

---

### Experiment 3: Output Capture Fidelity

**Question:** What level of detail can be captured from subagent execution?

**Hypothesis:** Task tool returns sufficient information to evaluate skill compliance.

**Procedure:**

1. Spawn a subagent with a multi-step task requiring tool use:

   ```
   Task(
     subagent_type: "general-purpose",
     prompt: "
       Read the file at [path].
       Summarize its contents.
       Then create a new file at [path2] with the summary.
     "
   )
   ```

2. Examine the returned output for:
   - a. Final response text
   - b. Tool calls made (which tools, what parameters)
   - c. Tool call sequence/order
   - d. Intermediate reasoning
   - e. Errors encountered

3. Document what IS and IS NOT captured.

4. Test with `run_in_background=true`:
   - Read output file
   - Compare captured detail to synchronous execution

**Capture Matrix:**

| Information            | Needed for Assessment | Captured? |
| ---------------------- | --------------------- | --------- |
| Final output text      | Yes (outcome)         | ?         |
| Tool calls made        | Yes (process)         | ?         |
| Tool call parameters   | Yes (behavior detail) | ?         |
| Tool call sequence     | Yes (process order)   | ?         |
| Intermediate reasoning | Helpful (intent)      | ?         |
| Token count            | Helpful (cost)        | ?         |
| Elapsed time           | Helpful (cost)        | ?         |
| Errors/exceptions      | Yes (failure modes)   | ?         |

**Success Criteria:**

- Final output captured
- Tool calls captured (at minimum: which tools)
- Sufficient detail to determine "did subagent do X"

**Failure Implications:**

If output capture is summary-only:

- May need background execution + output file parsing
- May need custom observation wrapper
- Evaluation may be limited to outcome-only (not process)

---

### Experiment 4: Controlled Conditions

**Question:** Can baseline and test runs be made identical except for skill presence?

**Hypothesis:** Same prompt structure, same tools, same context produces comparable runs.

**Procedure:**

1. Define a deterministic task with predictable baseline behavior: "List the files in [directory] and count them."

2. Run BASELINE twice with identical prompts:
   - Compare outputs for variance
   - Document any differences

3. Run TEST twice with identical prompts (skill injected):
   - Compare outputs for variance
   - Document any differences

4. Compare BASELINE vs TEST:
   - Identify differences attributable to skill vs. noise

5. Test tool availability control:
   - Can you restrict tools available to subagent?
   - Do both conditions have identical tool access?

**Variance Assessment:**

| Source                    | Acceptable?  | Mitigation                   |
| ------------------------- | ------------ | ---------------------------- |
| Stochastic model output   | Yes if small | Multiple runs, majority vote |
| Different tools available | No           | Must control                 |
| Different context/files   | No           | Must control                 |
| Prompt position effects   | Maybe        | Standardize position         |

**Success Criteria:**

- Same-condition runs produce similar outputs (low variance)
- Skill presence is the primary variable between conditions
- Tool availability is identical or controllable

**Failure Implications:**

If conditions can't be controlled:

- Comparisons are confounded
- May need stricter prompt templating
- May need multiple runs with statistical comparison

---

### Experiment 5: Cost Boundaries

**Question:** What are the token/time/cost bounds for subagent execution?

**Hypothesis:** Subagent costs are predictable and bounded.

**Procedure:**

1. Measure baseline costs:
   - Simple task (one tool call): tokens, time
   - Medium task (3-5 tool calls): tokens, time
   - Complex task (10+ tool calls): tokens, time

2. Test limits:
   - What happens at max_turns limit?
   - What happens with unbounded task?
   - Is there a token ceiling?

3. Calculate assessment cost:
   - Per scenario: 1 baseline + 1 test = 2 subagent runs
   - Per iteration: 5 scenarios × 2 runs = 10 runs
   - Full assessment: 3 iterations × 10 runs = 30 runs
   - Estimate total tokens/time for typical assessment

**Cost Model Template:**

| Component                      | Tokens (est.) | Time (est.) | Notes |
| ------------------------------ | ------------- | ----------- | ----- |
| Simple scenario (baseline)     | ?             | ?           |       |
| Simple scenario (test)         | ?             | ?           |       |
| Medium scenario (baseline)     | ?             | ?           |       |
| Medium scenario (test)         | ?             | ?           |       |
| Scenario evaluation            | ?             | ?           |       |
| Per iteration (5 scenarios)    | ?             | ?           |       |
| Full assessment (3 iterations) | ?             | ?           |       |

**Success Criteria:**

- Costs are measurable
- Costs are bounded (won't run away)
- Full assessment cost is acceptable for skill importance

**Failure Implications:**

If costs are unbounded or excessive:

- May need scenario complexity limits
- May need sampling instead of full runs
- May need to tier assessment depth by skill importance

---

### Experiment 6: Skill Activation Simulation

**Question:** Can injected skill content trigger the same behaviors as natively-loaded skills?

**Hypothesis:** Skill behavioral effect comes from the instructions, not the loading mechanism.

**Procedure:**

1. Select a skill you have natively loaded.

2. In current session (skill active), execute a task the skill addresses. Record the behavior.

3. Spawn a subagent WITHOUT the skill natively loaded, but WITH skill content injected via prompt. Execute the same task. Record the behavior.

4. Compare:
   - Same behavioral markers?
   - Same process followed?
   - Same output quality?

5. Test edge cases:
   - Does injected skill reference other skills? (dependency)
   - Does injected skill use Skill tool? (meta-reference)
   - Does injected skill have TodoWrite requirements? (tool dependency)

**Comparison Matrix:**

| Behavioral Marker          | Native Skill | Injected Skill | Match? |
| -------------------------- | ------------ | -------------- | ------ |
| Process steps followed     | ?            | ?              | ?      |
| Output format              | ?            | ?              | ?      |
| Tool usage pattern         | ?            | ?              | ?      |
| Error handling             | ?            | ?              | ?      |
| Blocking language enforced | ?            | ?              | ?      |

**Success Criteria:**

- Core behaviors match between native and injected
- Differences are documented and explainable
- Critical skill features work when injected

**Failure Implications:**

If injected skills behave differently:

- Framework may only assess "skill content as instructions" not "skill as loaded"
- May need to document which skill features don't transfer
- May need skill-specific injection adaptations

---

### Execution Order

| #   | Experiment                  | Blocks | Estimated Effort |
| --- | --------------------------- | ------ | ---------------- |
| 1   | Prompt Injection Baseline   | 2, 6   | 15 min           |
| 2   | Skill Content Injection     | 6      | 30 min           |
| 3   | Output Capture Fidelity     | 4      | 20 min           |
| 4   | Controlled Conditions       | —      | 20 min           |
| 5   | Cost Boundaries             | —      | 20 min           |
| 6   | Skill Activation Simulation | —      | 30 min           |

Total estimated time: ~2.5 hours

Run experiments 1-3 first (blocking). If any fail critically, stop and reassess before continuing.

---

### Decision Matrix

| Outcome                      | Decision                                                                |
| ---------------------------- | ----------------------------------------------------------------------- |
| All experiments pass         | Proceed to Phase 2 (Skill Architecture Design)                          |
| Experiments 1-2 fail         | Framework unimplementable as specified; redesign injection approach     |
| Experiment 3 fails           | Framework limited to outcome-only evaluation; revise spec               |
| Experiment 4 fails           | Comparisons unreliable; add statistical methods or abandon A/B approach |
| Experiment 5 fails           | Cost prohibitive; tier assessment or find efficiency gains              |
| Experiment 6 fails (partial) | Document limitations; some skills may not be assessable                 |

---

### Output Artifact

Document results in: `docs/spikes/simulation-feasibility-spike_YYYY-MM-DD.md`

Include:

1. Each experiment's results (pass/fail/partial)
2. Constraints discovered
3. Workarounds identified
4. Go/no-go decision with rationale
5. Recommended spec revisions (if any)

---

**Insight:** The spike is designed to fail fast. Experiments 1-2 are the critical path—if skill content can't be injected and followed, everything downstream is moot. The ordering ensures you discover showstoppers before investing in lower-priority experiments. The spike also produces design inputs. Even successful experiments will reveal constraints (position sensitivity, capture limitations, cost bounds) that shape the architecture design.

Want me to execute these experiments now, or refine the spike design first?

## Turn 9: User

Proceed to execution of each of these experiments

## Turn 10: Claude

I'll execute each experiment systematically, documenting results as I go.

---

### Experiment 1: Prompt Injection Baseline

Testing whether arbitrary instructional content influences subagent behavior.

**Test 1a: Instruction at start of prompt**

[Tool #2: Task — Test prompt injection at start]

Result: API Error 500 - Internal server error
