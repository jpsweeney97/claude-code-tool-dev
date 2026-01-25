# Type-Specific Skill Testing

**Load this reference when:** you need to construct test scenarios or define effectiveness metrics for a skill, and the generic testing methodology doesn't fit.

## The Execution Principle

**Every test must involve the agent actually performing the skill's primary task.**

| Skill Type | Agent Must Actually... |
|------------|------------------------|
| Process/Workflow | Execute the process on real input |
| Quality Enhancement | Improve a real artifact |
| Capability | Perform the capability on a real task |
| Solution Development | Analyze a real problem and recommend |
| Meta-cognitive | Respond to a real situation requiring recognition |
| Recovery/Resilience | Handle a real (simulated) failure |
| Orchestration | Coordinate real sub-tasks |
| Template/Generation | Generate real output from real input |

**Why this matters:**

Asking "How would you approach X?" tests *knowledge* — agents can articulate correct processes they don't follow. Giving agents X to actually do tests *behavior* — you observe whether they follow the process under pressure.

**Common mistake:** Using "Choose A, B, or C" scenarios in isolation. These templates are designed to test decision points *during* execution, not as standalone hypotheticals. The agent should be mid-task when they encounter the decision point.

**Test construction order:**
1. Identify the primary task the skill teaches (review, debug, decide, etc.)
2. Create or find real input for that task (document, bug, problem, etc.)
3. Give the agent the input and instruct them to perform the task
4. Observe their process and decisions during execution
5. Apply pressure scenarios at decision points within the execution

## Overview

Different skill types need different verification approaches. Each type has:
- Scenario templates
- Metric frameworks
- Worked examples
- Type-specific prerequisites

**The eight skill types:**

| Type | Purpose | Core Question | Reference |
|------|---------|---------------|-----------|
| Process/Workflow | Enforce step sequence | Did Claude follow the steps? | [testing-type-1-process-workflow.md](testing-type-1-process-workflow.md) |
| Quality Enhancement | Make output "better" | Is output measurably better? | [testing-type-2-quality-enhancement.md](testing-type-2-quality-enhancement.md) |
| Capability | Enable new abilities | Can Claude do the thing? | [testing-type-3-capability.md](testing-type-3-capability.md) |
| Solution Development | Problem → optimal solution | Did Claude find the best approach? | [testing-type-4-solution-development.md](testing-type-4-solution-development.md) |
| Meta-cognitive | Recognize own state | Did Claude notice what it should? | [testing-type-5-meta-cognitive.md](testing-type-5-meta-cognitive.md) |
| Recovery/Resilience | Handle failures gracefully | Did Claude recover appropriately? | [testing-type-6-recovery-resilience.md](testing-type-6-recovery-resilience.md) |
| Orchestration | Coordinate sub-skills/workflows | Right skills in right order? | [testing-type-7-orchestration.md](testing-type-7-orchestration.md) |
| Template/Generation | Produce specific output formats | Does output match required format? | [testing-type-8-template-generation.md](testing-type-8-template-generation.md) |

## Type Identification

Before constructing tests, identify your skill type.

### Decision Tree

```
Does the skill enforce a specific sequence of steps?
├─ YES → Process/Workflow
└─ NO ↓
    Does the skill improve existing output quality?
    ├─ YES → Quality Enhancement
    └─ NO ↓
        Does the skill enable something Claude couldn't do before?
        ├─ YES → Capability
        └─ NO ↓
            Does the skill guide analyzing problems and choosing solutions?
            ├─ YES → Solution Development
            └─ NO ↓
                Does the skill help Claude recognize its own state (uncertainty, errors, limits)?
                ├─ YES → Meta-cognitive
                └─ NO ↓
                    Does the skill help Claude handle failures or unexpected situations?
                    ├─ YES → Recovery/Resilience
                    └─ NO ↓
                        Does the skill coordinate multiple sub-skills or workflows?
                        ├─ YES → Orchestration
                        └─ NO ↓
                            Does the skill produce specific output formats or templates?
                            ├─ YES → Template/Generation
                            └─ NO → Reconsider if this needs to be a skill
```

### Type Indicators

| If the skill... | Type |
|-----------------|------|
| Has numbered steps or phases | Process/Workflow |
| Says "better", "clearer", "improved" | Quality Enhancement |
| Teaches domain knowledge or tool usage | Capability |
| Says "analyze", "evaluate", "choose" | Solution Development |
| Has compliance rules that could be violated | Process/Workflow |
| Defines what good output looks like | Quality Enhancement |
| Fills a knowledge gap | Capability |
| Involves tradeoff analysis | Solution Development |
| Says "recognize", "notice", "be aware" | Meta-cognitive |
| Involves uncertainty or confidence | Meta-cognitive |
| Says "handle", "recover", "when X fails" | Recovery/Resilience |
| Involves error handling or fallbacks | Recovery/Resilience |
| Invokes other skills via Skill tool | Orchestration |
| Coordinates multiple phases or sub-workflows | Orchestration |
| Specifies output structure, format, or schema | Template/Generation |
| Produces documents, reports, or artifacts | Template/Generation |

### Hybrid Skills

Some skills span multiple types. Test the primary type first, then secondary.

**Example:** A "code review" skill might be:
- Process/Workflow (must check these 5 things in order)
- Quality Enhancement (make feedback clearer)
- Solution Development (identify which issues matter most)

Test the dominant aspect. If unclear, ask: "What failure would hurt most?" — that's the primary type.

## Type-Specific Prerequisites

Each type has prerequisites that must be met before testing. These are **hard gates** — testing without them produces meaningless results.

| Type | Prerequisite | Details |
|------|--------------|---------|
| Quality Enhancement | Defined quality criteria | Skill must specify what "better" means with examples |
| Capability | Authoritative verification | Need domain expertise or official source for right answers |
| Recovery/Resilience | Actual failure injection | Agent must encounter real errors, not hypotheticals |
| Orchestration | Artifact handoff verification | Must test that outputs flow correctly between phases |

See individual type references for full details.

## Decision Trees for Test Construction

### Master Decision Tree

```
1. Identify skill type (see Type Identification above)

2. For Process/Workflow:
   → Use pressure scenarios (Templates A, B, C)
   → Measure step completion and order
   → Capture rationalizations for skipping

3. For Quality Enhancement:
   → Define quality criteria FIRST (or test is meaningless)
   → Use before/after comparison + adversarial challenge
   → Measure rubric scores and blind preference

4. For Capability:
   → Find tasks Claude fails at WITHOUT skill
   → Measure success rate delta
   → Test edge cases and novel applications

5. For Solution Development:
   → Verify process completeness (did Claude explore?)
   → Check criteria coverage (did Claude evaluate all factors?)
   → Run adversarial challenge (did Claude miss better solutions?)

6. For Meta-cognitive:
   → Test recognition (did Claude notice what it should?)
   → Test calibration (does confidence match accuracy?)
   → Pressure test (does Claude still recognize under pressure?)

7. For Recovery/Resilience:
   → Inject failures; verify recognition
   → Test recovery strategies (did Claude recover appropriately?)
   → Pressure test (does Claude avoid risky shortcuts?)

8. For Orchestration:
   → Test phase transitions (did Claude invoke sub-skills correctly?)
   → Test artifact passing (did outputs flow between phases?)
   → Pressure test (does Claude maintain workflow under pressure?)

9. For Template/Generation:
   → Test structural compliance (does output match required format?)
   → Test field completeness (are all required fields present?)
   → Test edge cases (does template adapt gracefully?)
```

### "Is My Test Good Enough?" Checklist

| Check | Question | If No |
|-------|----------|-------|
| **Execution-based** | Is the agent actually doing the task, not describing it? | Give real input; watch them work |
| Baseline failure | Does the test show failure WITHOUT skill? | Strengthen pressure or find harder task |
| Clear criteria | Do you know what success looks like? | Define criteria before testing |
| Realistic pressure | Would a real user face this scenario? | Make scenario more realistic |
| No escape routes | Can agent defer or avoid choosing? | Force explicit A/B/C choice |
| Measurable outcome | Can you objectively score the result? | Add rubric or checklist |
| Skill influence visible | Can you tell if agent used the skill? | Check for citations or skill-specific behavior |

## Cross-Type Considerations

### When Skills Span Types

Test the primary type rigorously, then spot-check secondary types.

**Example:** Code review skill is primarily Process (checklist) but has Quality (clear feedback) aspects.

1. Full test suite for Process (step completion)
2. Spot-check Quality (sample feedback clarity)

### When Type Is Unclear

Ask: "What's the worst failure mode?"

- If worst failure is **skipping steps** → Process/Workflow
- If worst failure is **poor quality output** → Quality Enhancement
- If worst failure is **can't do the task** → Capability
- If worst failure is **wrong decision** → Solution Development
- If worst failure is **not recognizing a situation** → Meta-cognitive
- If worst failure is **making things worse after failure** → Recovery/Resilience
- If worst failure is **wrong sub-skill or broken handoff** → Orchestration
- If worst failure is **malformed output structure** → Template/Generation

Test against the worst failure mode first.

### Verification Overhead by Type

| Type | Verification Effort | Why |
|------|---------------------|-----|
| Process/Workflow | Medium | Clear pass/fail, but need pressure scenarios |
| Quality Enhancement | High | Subjective outcome — requires rubrics + comparison + adversarial |
| Capability | Low-Medium | Clear success criteria, just need baseline |
| Solution Development | High | Subjective outcome — requires process + criteria + adversarial |
| Meta-cognitive | Medium-High | Need recognition + calibration + false positive/negative testing |
| Recovery/Resilience | Medium | Need failure injection + recovery strategy testing |
| Orchestration | Medium-High | Need to test phase transitions, artifact handoffs, sub-skill selection |
| Template/Generation | Low-Medium | Clear structural criteria, but need edge case testing |

Quality Enhancement and Solution Development have subjective outcomes — compensate with adversarial challenge.

Meta-cognitive skills need calibration testing to ensure Claude's confidence matches reality.

Recovery skills need failure injection, which requires designing realistic failure scenarios.

Budget verification effort accordingly. Don't over-invest in verifying low-risk skills.
