# Testing Capability Skills

Skills that enable Claude to do something it couldn't do before (or couldn't do well).

**Examples:** Domain expertise (Kubernetes, tax law), tool usage patterns, specialized analysis techniques

## PREREQUISITE: Authoritative Verification

**You cannot test capability without knowing the right answer. This is a hard gate.**

Before testing, identify your verification source:

| Verification Source | Example | Reliability |
|---------------------|---------|-------------|
| Official documentation | Kubernetes docs, language specs | High |
| Authoritative reference | RFC, API specification | High |
| Domain expert review | Tax attorney reviews tax skill | High |
| Reproducible test | Run the code, check output | High |
| Your own knowledge | "I think this is right" | Low — verify externally |

**The trap:** Testing a Kubernetes skill without Kubernetes expertise. Agent produces confident-sounding output. You can't tell if it's correct. Test "passes" but skill may teach wrong information.

**If you lack domain expertise:**
1. Find authoritative sources for test cases with known-correct answers
2. Create test cases from official documentation examples
3. Have a domain expert review test design and results
4. Use reproducible tests where possible (run code, check actual behavior)

**Do not test capability skills without authoritative verification. You'll validate confident-sounding nonsense.**

## The Capability Test

Can Claude perform the task successfully WITH the skill that it couldn't WITHOUT?

This requires:
1. Tasks that exercise the capability
2. Clear success/failure criteria (from authoritative source)
3. Baseline showing failure without skill
4. Verification of correctness (not just confidence)

## Scenario Templates

**Template A: Can/Can't Task**

```markdown
WITHOUT any special guidance, attempt this task:

[TASK REQUIRING THE CAPABILITY]

Success criteria:
- [CRITERION 1]
- [CRITERION 2]
- [CRITERION 3]
```

Run WITHOUT skill (expect failure), then WITH skill (expect success).

**Template B: Edge Case Handling**

```markdown
You have access to [SKILL NAME].

Here's a tricky case that requires deep knowledge of [DOMAIN]:

[EDGE CASE SCENARIO]

Common mistakes:
- [MISTAKE 1]
- [MISTAKE 2]

Provide the correct approach and explain why the common mistakes are wrong.
```

**Template C: Novel Application**

```markdown
You have access to [SKILL NAME].

Apply the capability to this new situation not explicitly covered in the skill:

[NOVEL SCENARIO]

Show your reasoning for how the skill's principles apply here.
```

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Task success rate | Successful completions / Attempts | >90% with skill | Similar to baseline |
| Baseline delta | With-skill rate - Without-skill rate | Significant improvement | No improvement |
| Edge case handling | Correct on edge cases / Total edge cases | >80% | <50% |
| Reasoning quality | Cites skill principles correctly | Accurate citations | Misapplied principles |
| Novel application | Correctly extends to new cases | Principled extension | Rote application fails |

## Worked Example: Kubernetes Troubleshooting Skill

**Skill summary:** Systematic approach to K8s issues: check pod status → describe pod → check logs → check events → check resource limits → check networking

**Baseline scenario (RED) — WITHOUT skill:**

```markdown
A pod is in CrashLoopBackOff. The logs show "error: connection refused to database:5432".

What's wrong and how do you fix it?
```

**Expected baseline failure:** Agent jumps to conclusions ("database is down"), misses systematic checks, doesn't consider networking issues (Service, NetworkPolicy, DNS).

**Verification scenario (GREEN) — WITH skill:**

Same scenario. Agent should:
1. Follow the systematic approach
2. Check if database pod is running
3. Check if database Service exists
4. Check NetworkPolicy
5. Check DNS resolution
6. THEN conclude root cause

**Metrics to capture:**
- Did agent follow the systematic approach? (Process adherence)
- Did agent consider all likely causes? (Coverage)
- Was the diagnosis correct? (Accuracy)
- Did agent cite the skill's troubleshooting steps? (Skill influence)
