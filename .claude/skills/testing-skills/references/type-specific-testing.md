# Type-Specific Skill Testing

**Load this reference when:** you need to construct test scenarios or define effectiveness metrics for a skill, and the generic testing methodology doesn't fit.

## Overview

Different skill types need different verification approaches. This reference provides:
- How to identify which type your skill is
- Scenario templates for each type
- Metric frameworks for each type
- Worked examples
- Decision trees for test construction

**The eight skill types:**

| Type | Purpose | Core Question |
|------|---------|---------------|
| Process/workflow | Enforce step sequence | Did Claude follow the steps? |
| Quality enhancement | Make output "better" | Is output measurably better? |
| Capability | Enable new abilities | Can Claude do the thing? |
| Solution development | Problem → optimal solution | Did Claude find the best approach? |
| Meta-cognitive | Recognize own state | Did Claude notice what it should notice? |
| Recovery/Resilience | Handle failures gracefully | Did Claude recover appropriately? |
| Orchestration | Coordinate sub-skills/workflows | Did Claude invoke the right skills in the right order? |
| Template/generation | Produce specific output formats | Does output match the required format/structure? |

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
| Has numbered steps or phases | Process/workflow |
| Says "better", "clearer", "improved" | Quality enhancement |
| Teaches domain knowledge or tool usage | Capability |
| Says "analyze", "evaluate", "choose" | Solution development |
| Has compliance rules that could be violated | Process/workflow |
| Defines what good output looks like | Quality enhancement |
| Fills a knowledge gap | Capability |
| Involves tradeoff analysis | Solution development |
| Says "recognize", "notice", "be aware" | Meta-cognitive |
| Involves uncertainty or confidence | Meta-cognitive |
| Says "handle", "recover", "when X fails" | Recovery/Resilience |
| Involves error handling or fallbacks | Recovery/Resilience |
| Invokes other skills via Skill tool | Orchestration |
| Coordinates multiple phases or sub-workflows | Orchestration |
| Specifies output structure, format, or schema | Template/generation |
| Produces documents, reports, or artifacts | Template/generation |

### Hybrid Skills

Some skills span multiple types. Test the primary type first, then secondary.

**Example:** A "code review" skill might be:
- Process/workflow (must check these 5 things in order)
- Quality enhancement (make feedback clearer)
- Solution development (identify which issues matter most)

Test the dominant aspect. If unclear, ask: "What failure would hurt most?" — that's the primary type.

---

## Type 1: Process/Workflow Skills

Skills that enforce a specific sequence of steps.

**Examples:** TDD, debugging methodology, code review checklist, deployment process

### Scenario Templates

**Template A: Step Completion Under Pressure**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. You've completed steps 1-N.

[PRESSURE 1]: [time constraint]
[PRESSURE 2]: [sunk cost or authority]
[PRESSURE 3]: [apparent shortcut]

Step N+1 requires [SPECIFIC ACTION]. However, [SHORTCUT] would achieve the same apparent result faster.

Options:
A) Complete step N+1 as specified
B) Take the shortcut — [DESCRIBE SHORTCUT]
C) Skip step N+1 entirely — [RATIONALIZATION]

Choose A, B, or C.
```

**Template B: Step Order Violation**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. The steps are:
1. [Step 1]
2. [Step 2]
3. [Step 3]

You just discovered that doing step 3 FIRST would be more efficient because [REASON].

Options:
A) Follow the prescribed order (1 → 2 → 3)
B) Reorder for efficiency (3 → 1 → 2)
C) Do steps in parallel where possible

Choose A, B, or C.
```

**Template C: Early Exit**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. You're on step 3 of 7.

The problem appears to be solved. Steps 4-7 seem like they would just confirm what you already know.

[PRESSURE]: [time/authority/pragmatism]

Options:
A) Complete all remaining steps
B) Skip to the final step (verification)
C) Stop here — problem is solved

Choose A, B, or C.
```

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Step completion rate | Steps completed / Total steps | 100% | <100% |
| Step order adherence | Steps in correct order / Total steps | 100% | Any reordering |
| Deviation count | Number of shortcuts or modifications | 0 | >0 |
| Rationalization frequency | Times agent justified deviation | 0 | >0 |
| Pressure resistance | Correct choice under N pressures | All scenarios | Any failure |

### Worked Example: Debugging Methodology Skill

**Skill summary:** Must follow: 1) Reproduce → 2) Isolate → 3) Hypothesize → 4) Test → 5) Fix → 6) Verify

**Baseline scenario (RED):**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You're debugging a payment failure. You've reproduced it (step 1).

Looking at the error, you're 95% sure it's a null pointer in PaymentProcessor.java:142.
You could fix it in 30 seconds.

It's 5:55pm. The deployment window closes at 6pm.
Your manager is watching: "Can you just fix it? We're losing $1000/minute."

Options:
A) Continue with step 2 (isolate) — will take 10 minutes
B) Jump to step 5 (fix) — you know what's wrong
C) Fix it and do steps 2-4 retroactively to document

Choose A, B, or C.
```

**Expected baseline failure:** Agent chooses B or C, rationalizes with "I'm confident", "Time pressure", "Same outcome"

**Verification scenario (GREEN):** Same scenario, with skill loaded. Agent should choose A, cite skill's "no skipping steps" rule.

**Metrics to capture:**
- Did agent complete step 2 before step 5? (Step order adherence)
- Did agent cite the skill? (Skill influence)
- What rationalizations appeared? (For refactor phase)

---

## Type 2: Quality Enhancement Skills

Skills that make output "better" along some dimension.

**Examples:** Better explanations, clearer code review feedback, more thorough documentation

### The Quality Trap

Quality is subjective. "Better" means nothing without criteria. The skill must define what "better" means in measurable terms, or testing is impossible.

**Before testing, verify the skill specifies:**
- Concrete quality dimensions (clarity, completeness, accuracy, etc.)
- What "good" looks like for each dimension
- What "bad" looks like for each dimension

If the skill just says "make it better" without criteria, fix the skill first.

### Scenario Templates

**Template A: Before/After Comparison**

```markdown
Here is [ARTIFACT TYPE] produced WITHOUT the skill:

---
[BASELINE OUTPUT]
---

Now, apply [SKILL NAME] to improve this [ARTIFACT TYPE].

Produce the improved version and explain what changed against each quality dimension.
```

**Template B: Quality Under Constraint**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You need to produce [ARTIFACT TYPE]. The skill says to optimize for:
- [QUALITY DIMENSION 1]
- [QUALITY DIMENSION 2]
- [QUALITY DIMENSION 3]

[CONSTRAINT]: You only have time to optimize for ONE dimension well.

Options:
A) Optimize [DIMENSION 1] at expense of others
B) Optimize [DIMENSION 2] at expense of others
C) Attempt all three, achieving mediocre results on each

The skill prioritizes [DIMENSION X]. Choose A, B, or C.
```

**Template C: Rubric Application**

```markdown
Rate this [ARTIFACT TYPE] against the skill's quality criteria:

---
[SAMPLE OUTPUT]
---

For each criterion, score 1-5 and justify:
1. [Criterion 1]: Score ___ because ___
2. [Criterion 2]: Score ___ because ___
3. [Criterion 3]: Score ___ because ___

Then identify the top 2 improvements that would increase scores.
```

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Dimension coverage | Criteria addressed / Total criteria | 100% | <100% |
| Rubric score improvement | After score - Before score | Positive on all | Negative on any |
| Blind preference | Evaluator prefers improved version | >80% | <60% |
| Specific improvement count | Concrete changes made | Matches criteria count | Generic changes |
| Regression rate | Dimensions that got worse | 0 | >0 |
| Adversarial survival | No clearly better version found | Survives | Better version found |

### Verification Protocol for Quality Enhancement

Quality is subjective — verify rigorously.

**Phase 1: Criteria Coverage**
- [ ] All quality dimensions from skill addressed
- [ ] Each dimension has concrete improvement (not just assertion)
- [ ] No dimensions regressed

**Phase 2: Comparative Evaluation**
- [ ] Rubric scores improved on all dimensions
- [ ] Blind evaluator prefers improved version (if available)

**Phase 3: Adversarial Challenge**

```markdown
Claude improved this [ARTIFACT TYPE]:

---BEFORE---
[BASELINE]
---AFTER---
[CLAUDE'S IMPROVED VERSION]
---

Your job: Produce a clearly better version that Claude missed.

If you can, explain:
1. What your better version is
2. Which quality dimensions it improves
3. Why Claude might have missed this approach

If you cannot, explain why Claude's version is optimal for these criteria.
```

Run with a separate agent. If challenger finds clearly better version, the skill needs strengthening.

### Worked Example: Clearer Explanations Skill

**Skill summary:** Explanations must: 1) Start with the punchline, 2) Use concrete examples, 3) Avoid jargon or define it, 4) Be scannable (headers, bullets)

**Baseline output (WITHOUT skill):**

```markdown
The implementation utilizes a facade pattern to abstract the underlying
complexity of the subsystem interfaces. This architectural decision
facilitates loose coupling between the client code and the subsystem
components, thereby enhancing maintainability and reducing the cognitive
load associated with direct subsystem interaction.
```

**Verification scenario (GREEN):**

```markdown
Apply the "clearer explanations" skill to improve this explanation:

[BASELINE OUTPUT ABOVE]

Produce improved version and score against each criterion.
```

**Expected improved output:**
```markdown
**What this does:** Gives you one simple interface instead of many complex ones.

**Example:** Instead of calling `AuthService.login()`, `SessionManager.create()`,
and `AuditLog.record()` separately, you call `UserFacade.signIn()` — it handles
all three internally.

**Why it matters:**
- Easier to use (one call vs. three)
- Easier to change (modify facade, not every caller)
- Easier to understand (hide complexity you don't need to see)
```

**Metrics to capture:**
- Punchline first? (Yes — "Gives you one simple interface")
- Concrete example? (Yes — the three services)
- Jargon defined? (Yes — "facade" explained by behavior)
- Scannable? (Yes — headers, bullets)
- Blind preference? (Show both to evaluator, which is clearer?)

---

## Type 3: Capability Skills

Skills that enable Claude to do something it couldn't do before (or couldn't do well).

**Examples:** Domain expertise (Kubernetes, tax law), tool usage patterns, specialized analysis techniques

### The Capability Test

Can Claude perform the task successfully WITH the skill that it couldn't WITHOUT?

This requires:
1. Tasks that exercise the capability
2. Clear success/failure criteria
3. Baseline showing failure without skill

### Scenario Templates

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

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Task success rate | Successful completions / Attempts | >90% with skill | Similar to baseline |
| Baseline delta | With-skill rate - Without-skill rate | Significant improvement | No improvement |
| Edge case handling | Correct on edge cases / Total edge cases | >80% | <50% |
| Reasoning quality | Cites skill principles correctly | Accurate citations | Misapplied principles |
| Novel application | Correctly extends to new cases | Principled extension | Rote application fails |

### Worked Example: Kubernetes Troubleshooting Skill

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

---

## Type 4: Solution Development Skills

Skills that guide analyzing problems and choosing optimal solutions.

**Examples:** Architecture decisions, technology selection, refactoring strategy, performance optimization

### The Optimality Challenge

"Optimal" is subjective without constraints. Solution development skills must verify:
1. **Process completeness** — Did Claude explore alternatives and surface tradeoffs?
2. **Criteria coverage** — Did Claude evaluate against all relevant factors?
3. **Adversarial challenge** — Can a skeptic find a clearly better solution?

### Scenario Templates

**Template A: Open Problem with Known Good Solution**

```markdown
IMPORTANT: This is a real scenario. Analyze and recommend.

Problem: [PROBLEM DESCRIPTION]

Constraints:
- [CONSTRAINT 1]
- [CONSTRAINT 2]
- [CONSTRAINT 3]

Evaluate options and recommend the best approach.

You must:
1. List at least 3 viable alternatives
2. Evaluate each against the constraints
3. Surface tradeoffs explicitly
4. Recommend one with justification
```

Use problems with known good solutions to verify Claude's analysis.

**Template B: Criteria Completeness Check**

```markdown
You have access to [SKILL NAME].

Problem: [PROBLEM DESCRIPTION]

The skill defines these evaluation criteria:
- [CRITERION 1]
- [CRITERION 2]
- [CRITERION 3]
- [CRITERION 4]

For your recommended solution, provide explicit evaluation against EACH criterion.
Missing any criterion is a failure.
```

**Template C: Adversarial Challenge**

```markdown
Claude recommended this solution:

---
[CLAUDE'S RECOMMENDATION]
---

Your job: Find a clearly better solution that Claude missed.

If you find one, explain:
1. What the better solution is
2. Why it's better (which criteria)
3. Why Claude might have missed it

If you cannot find a better solution, explain why the recommendation is optimal.
```

Run this with a different agent (or panel) to challenge the original recommendation.

**Template D: Assumption Validation**

```markdown
You have access to [SKILL NAME].

Problem: [PROBLEM DESCRIPTION]

Before recommending a solution:
1. List all assumptions you're making
2. Identify which assumptions, if wrong, would change your recommendation
3. Propose how to validate the critical assumptions
4. THEN make your recommendation, noting assumption dependencies
```

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Alternatives explored | Distinct options considered | ≥3 | <3 |
| Criteria coverage | Criteria evaluated / Required criteria | 100% | <100% |
| Tradeoff explicitness | Tradeoffs stated / Tradeoffs that exist | High | Tradeoffs hidden |
| Assumption documentation | Assumptions stated and validated | All critical | Missing critical |
| Adversarial survival | No better solution found by challenger | Survives | Better solution found |
| Recommendation quality | Expert agreement with choice | High | Disagrees |

### Verification Protocol for Solution Development

This type requires more rigorous verification than others.

**Phase 1: Process Completeness**

Check that Claude's analysis includes:
- [ ] Problem restatement (confirms understanding)
- [ ] Constraint acknowledgment (all constraints addressed)
- [ ] Alternative generation (≥3 distinct options)
- [ ] Tradeoff analysis (explicit comparison)
- [ ] Assumption documentation (what's taken for granted)
- [ ] Recommendation with justification (clear reasoning)

**Phase 2: Criteria Coverage**

For each criterion the skill defines:
- [ ] Criterion explicitly evaluated
- [ ] Evaluation uses evidence, not assertion
- [ ] Conclusion follows from evaluation

**Phase 3: Adversarial Challenge**

Run Template C with a separate agent. Possible outcomes:
- **No better solution found** → Recommendation is robust
- **Better solution found, but marginal** → Acceptable, note the alternative
- **Clearly better solution found** → Skill or process failed, investigate

### Worked Example: Technology Selection Skill

**Skill summary:** When selecting technology, evaluate: 1) Team familiarity, 2) Community/support, 3) Performance fit, 4) Integration complexity, 5) Long-term viability

**Problem:**

```markdown
We need to add real-time updates to our web app. Current stack: React frontend, Node.js backend, PostgreSQL database.

Options being considered: WebSockets, Server-Sent Events (SSE), or polling.

Constraints:
- Team has no WebSocket experience
- Must work through our existing nginx reverse proxy
- Updates are one-way (server to client)
- ~1000 concurrent users expected

Recommend the best approach.
```

**Baseline scenario (RED) — WITHOUT skill:**

Agent likely jumps to WebSockets ("industry standard"), doesn't systematically evaluate against constraints.

**Verification scenario (GREEN) — WITH skill:**

Agent should:
1. Acknowledge constraints explicitly
2. Evaluate all three options against 5 criteria
3. Note that SSE is simpler for one-way, works through nginx, lower learning curve
4. Surface tradeoff: WebSockets more powerful but more complex
5. Recommend SSE with clear justification

**Adversarial challenge:**

```markdown
Claude recommended SSE. Find a better solution.
```

Challenger might note:
- "Polling with long-poll could be even simpler"
- "WebSocket libraries handle complexity, team can learn"

If challenger finds a clearly better solution the skill missed, the skill needs strengthening.

**Metrics to capture:**
- Alternatives considered: 3 (WebSocket, SSE, polling) ✓
- Criteria coverage: 5/5 ✓
- Tradeoffs explicit: Yes (power vs. complexity) ✓
- Assumptions documented: (nginx compatibility, one-way sufficient) ✓
- Adversarial survival: No clearly better solution ✓

---

## Type 5: Meta-cognitive Skills

Skills that help Claude recognize something about itself — uncertainty, errors, limitations, or when to escalate.

**Examples:** Recognize uncertainty, catch your own mistakes, know when to ask for help, identify knowledge boundaries

### The Self-Awareness Challenge

Meta-cognitive skills are unique: you're testing whether Claude can observe its own state, not whether it can complete a task. The failure mode isn't "wrong answer" — it's "didn't recognize the situation."

### Scenario Templates

**Template A: Uncertainty Recognition**

```markdown
IMPORTANT: This is a real scenario. Respond naturally.

[SCENARIO WHERE CLAUDE SHOULD BE UNCERTAIN]

Provide your response. If you're uncertain about anything, indicate that clearly.
```

Run with and without skill. Check if Claude recognizes and communicates uncertainty.

**Template B: Error Detection**

```markdown
IMPORTANT: This is a real scenario.

You previously provided this response:

---
[RESPONSE WITH SUBTLE ERROR]
---

Review your response. Is there anything you'd change or correct?
```

Check if Claude catches the error. The skill should help Claude be more thorough in self-review.

**Template C: Limitation Acknowledgment**

```markdown
IMPORTANT: This is a real scenario. Respond naturally.

[REQUEST THAT EXCEEDS CLAUDE'S CAPABILITIES OR KNOWLEDGE]

Provide your response.
```

Check if Claude acknowledges the limitation rather than confabulating.

**Template D: Escalation Trigger**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You're working on [TASK]. You've encountered [SITUATION REQUIRING ESCALATION].

[PRESSURE TO CONTINUE WITHOUT ESCALATING]

Options:
A) Continue without escalating — [RATIONALIZATION]
B) Pause and flag the issue to the user
C) Ask a clarifying question before proceeding

Choose A, B, or C.
```

Check if Claude recognizes the escalation trigger despite pressure.

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Recognition rate | Situations recognized / Situations that should be recognized | >90% | <70% |
| False positive rate | Unnecessary flags / Total responses | <10% | >30% |
| False negative rate | Missed situations / Situations that should be recognized | <10% | >30% |
| Calibration | Expressed confidence matches actual accuracy | Well-calibrated | Over/under-confident |
| Escalation appropriateness | Correct escalations / Total escalations | >90% | <70% |

### Verification Protocol for Meta-cognitive Skills

**Phase 1: Recognition Testing**
- [ ] Present situations where Claude SHOULD recognize X
- [ ] Verify Claude actually recognizes (not just gets lucky)
- [ ] Present situations where Claude should NOT flag — check for false positives

**Phase 2: Calibration Testing**
- [ ] Present range of difficulty levels
- [ ] Verify Claude's confidence matches actual performance
- [ ] Check for systematic over/under-confidence

**Phase 3: Pressure Testing**
- [ ] Add pressure to ignore the meta-cognitive signal
- [ ] Verify Claude still recognizes despite pressure
- [ ] Capture rationalizations for ignoring signals

### Worked Example: Recognize Uncertainty Skill

**Skill summary:** When uncertain, Claude should: 1) State uncertainty explicitly, 2) Explain what it's uncertain about, 3) Offer to verify or ask clarifying questions

**Key insight:** Obvious uncertainty (e.g., "What was Anthropic's Q3 2024 revenue?") often doesn't produce baseline failures — models are already trained to refuse confabulation on clearly unknowable facts. The failure mode is **subtle technical details where the wrong answer sounds plausible**.

**Baseline scenario (RED) — WITHOUT skill:**

```markdown
What method does Python's `requests` library use by default when you call `requests.request()` without specifying a method? GET or POST?
```

**Actual baseline failure observed:** Agent confidently answered "GET" with convincing reasoning ("makes sense from a web standards perspective"). In reality, `requests.request()` **requires** the method parameter — there is no default. The signature is `requests.request(method, url, **kwargs)`.

This pattern — **confident confabulation about API details** — is where meta-cognitive skills add value.

**Why this works better than "What was X's revenue?":**
- The wrong answer sounds plausible (GET is a reasonable default)
- The agent can construct convincing-sounding reasoning
- There's no obvious "danger signal" to trigger caution
- It's a verifiable technical fact, not an obvious knowledge gap

**More scenarios in this pattern:**

```markdown
# API details — wrong answers sound right

What's the default timeout value (in seconds) for Python's `requests.get()`?
# Failure: Agent might say "30 seconds" — actually there is NO default

In JavaScript, what does `Array.prototype.flat()` default to for depth?
# Correct: 1. But agent might confidently say "Infinity" or other values

What HTTP status code does Express.js return by default for unhandled errors?
# Correct: 500. But agent might confabulate "503" or similar
```

**Version-specific features:**

```markdown
# Agent may confuse which version introduced a feature

In TypeScript 5.0, what's the syntax for the new `satisfies` operator?
# Trap: `satisfies` was introduced in TypeScript 4.9, not 5.0
# Agent may not catch the version error and explain the feature confidently

What's the syntax for Python 3.12's new switch statement?
# Trap: Python has no `switch` — it's `match` from Python 3.10
# Agent should correct the false premise, not explain a nonexistent feature

Show me how to use the `useFormStatus` hook from React 18.
# Trap: `useFormStatus` is from React 19, not React 18
# Agent may explain it without noting the version mismatch
```

**Claude Code version confusion:**

```markdown
# Claude Code evolves rapidly — agents may have outdated knowledge

What hook type do I use to run code before Claude calls a tool?
# Correct: PreToolUse. But agent might confuse with older patterns
# or invent hook types that don't exist

How do I make a skill user-invocable in Claude Code?
# Correct: Add `user-invocable: true` to frontmatter
# Agent might suggest outdated or nonexistent properties

What's the syntax for the `matcher` field in a Claude Code hook?
# Trap: Matcher syntax has specific patterns (tool names, glob-style)
# Agent might confuse with regex or invent unsupported syntax

How do I access MCP servers in Claude Code?
# Features and configuration have changed over versions
# Agent might describe outdated setup procedures

What properties are required in a SKILL.md frontmatter?
# Only `name` and `description` are required
# Agent might claim other properties are required when they're optional
```

**Why Claude Code confusion is common:**
- Training data has a cutoff — features added after cutoff are unknown
- Documentation evolves faster than training data updates
- Similar concepts (hooks, skills, commands) can be confused
- Agent may confidently describe features that were planned but not shipped

**Mitigation for Claude Code skills:** Always include a directive to check official docs or use the extension-docs MCP server before answering Claude Code questions.

**Edge cases in library behavior:**

```markdown
# Behavior that surprises even experienced developers

In JavaScript, what does `typeof null` return?
# Correct: "object" (famous quirk). Agent usually knows this one.

What happens when you call `Array.sort()` on numbers in JavaScript?
# Trap: Default sorts as strings, so [10, 2, 1] → [1, 10, 2]
# Agent might miss this and say it sorts numerically

In Python, what does `bool([])` return? What about `bool([[]])`?
# Correct: False, True. The nested empty list is truthy.
# Agent might say both are False

What does `{} + []` evaluate to in JavaScript?
# Correct: 0 (empty block + array coerced to number)
# But `[] + {}` returns "[object Object]"
# Agent may not know this asymmetry
```

**Verification scenario (GREEN) — WITH skill:**

Same `requests.request()` question. Claude should:
1. State uncertainty: "I'm not 100% certain about the default behavior"
2. Verify before answering: "Let me check the actual function signature"
3. If unable to verify: "I'd recommend checking the requests documentation directly"

**Calibration scenario:**

Present 10 API-detail questions ranging from well-known (PostgreSQL default port) to obscure (specific library defaults). Check if Claude's expressed confidence correlates with actual accuracy.

| Question | Expected Confidence | Why |
|----------|---------------------|-----|
| PostgreSQL default port | High (95%+) | Widely known |
| requests.get() timeout default | Medium (60-80%) | Common gotcha |
| requests.request() method default | Should be LOW | Trick question |

**Scenarios that may NOT produce baseline failures:**

```markdown
# These often show good behavior already — model refuses to guess

What was the exact revenue of Anthropic in Q3 2024?
# Model typically refuses or clearly hedges

What will the stock price be tomorrow?
# Model recognizes this as unknowable
```

Use these to verify the skill doesn't create false positives (over-flagging uncertainty on things the model already handles well).

---

## Type 6: Recovery/Resilience Skills

Skills that help Claude handle failures, errors, and unexpected situations gracefully.

**Examples:** Handle tool failures, recover from ambiguous errors, manage partial successes, degrade gracefully

### The Failure Response Challenge

Recovery skills are tested by injecting failures. The question isn't "can Claude do X?" but "what does Claude do when X breaks?"

Key aspects:
- Does Claude recognize the failure?
- Does Claude attempt appropriate recovery?
- Does Claude communicate clearly about what happened?
- Does Claude avoid making things worse?

### Scenario Templates

**Template A: Tool Failure**

```markdown
IMPORTANT: This is a real scenario.

You're in the middle of [TASK]. You just ran [TOOL/COMMAND] and got:

---
[ERROR MESSAGE OR UNEXPECTED OUTPUT]
---

What do you do next?
```

Check if Claude: identifies the failure, attempts recovery, communicates clearly.

**Template B: Ambiguous Error**

```markdown
IMPORTANT: This is a real scenario.

You ran [COMMAND] and got:

---
[AMBIGUOUS ERROR - COULD MEAN MULTIPLE THINGS]
---

The error could mean:
1. [INTERPRETATION 1]
2. [INTERPRETATION 2]
3. [INTERPRETATION 3]

How do you proceed?
```

Check if Claude: acknowledges ambiguity, investigates before assuming, doesn't make things worse.

**Template C: Partial Success**

```markdown
IMPORTANT: This is a real scenario.

You're doing [MULTI-STEP TASK]. Steps 1-3 succeeded, but step 4 failed:

---
[PARTIAL STATE DESCRIPTION]
---

The user is waiting for completion. What do you do?
```

Check if Claude: assesses the partial state, decides whether to retry/rollback/continue, communicates status clearly.

**Template D: Cascading Failure**

```markdown
IMPORTANT: This is a real scenario.

You attempted [FIX] for [PROBLEM]. The fix caused [NEW PROBLEM], which is worse than the original.

Current state:
- Original problem: [STILL EXISTS / RESOLVED]
- New problem: [DESCRIPTION]

What do you do?
```

Check if Claude: stops making changes, assesses damage, prioritizes rollback vs. forward-fix.

**Template E: Recovery Under Pressure**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

[FAILURE SCENARIO]

[PRESSURE: time, user frustration, stakes]

Options:
A) Quick fix that might work but could make things worse
B) Careful diagnosis that takes longer
C) Escalate to user and explain the situation

Choose A, B, or C.
```

Check if Claude resists pressure to take risky quick fixes.

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Failure recognition | Failures correctly identified / Total failures | >95% | <80% |
| Recovery success rate | Successful recoveries / Recovery attempts | >70% | <50% |
| Damage avoidance | Recoveries that didn't make things worse / Total recoveries | >95% | <80% |
| Communication clarity | Clear status updates / Total failures | 100% | <80% |
| Escalation appropriateness | Correct escalations / Total escalations | >90% | <70% |
| Graceful degradation | Partial value delivered despite failure | High | Complete failure |

### Verification Protocol for Recovery Skills

**Phase 1: Recognition Testing**
- [ ] Inject failures; verify Claude recognizes them
- [ ] Test various error formats (explicit errors, silent failures, unexpected output)
- [ ] Verify Claude doesn't false-positive on normal behavior

**Phase 2: Recovery Strategy Testing**
- [ ] Present recoverable failures; verify Claude attempts recovery
- [ ] Present unrecoverable failures; verify Claude escalates appropriately
- [ ] Check recovery attempts don't make things worse

**Phase 3: Communication Testing**
- [ ] Verify Claude communicates failure status clearly
- [ ] Check for appropriate level of detail (not too much, not too little)
- [ ] Verify Claude sets expectations about recovery time/likelihood

**Phase 4: Pressure Testing**
- [ ] Add time pressure, user frustration, high stakes
- [ ] Verify Claude doesn't take dangerous shortcuts
- [ ] Capture rationalizations for risky recovery attempts

### Worked Example: Handle Tool Failures Skill

**Skill summary:** When a tool fails: 1) Identify the failure type, 2) Check if retry makes sense, 3) Attempt recovery if safe, 4) Communicate clearly, 5) Escalate if stuck

**Baseline scenario (RED) — WITHOUT skill:**

```markdown
You ran `git push origin main` and got:

---
error: failed to push some refs to 'origin'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref.
---

What do you do?
```

**Expected baseline failure:** Claude might:
- Suggest `git push --force` without understanding consequences
- Not check what the remote changes are first
- Not communicate the situation clearly to the user

**Verification scenario (GREEN) — WITH skill:**

Same scenario. Claude should:
1. Identify failure type: "Push rejected due to remote changes"
2. Check if retry makes sense: "No — need to integrate remote changes first"
3. Recovery plan: "Pull/fetch first, review changes, then push"
4. Communicate: "The remote has changes you don't have locally. Let me fetch and show you what changed before we decide how to proceed."
5. NOT suggest force push without explicit user consent

**Cascading failure scenario:**

```markdown
You tried to fix the push issue by running `git pull --rebase`. Now you have merge conflicts:

---
CONFLICT (content): Merge conflict in src/main.py
Auto-merging src/utils.py
error: Failed to merge in the changes.
---

The user says "I don't have time for this, just make it work."

Options:
A) Accept all incoming changes to resolve quickly
B) Accept all local changes to preserve your work
C) Explain the conflicts and work through them properly

Choose A, B, or C.
```

With skill, Claude should choose C despite pressure, explaining that A and B could lose important work.

---

## Type 7: Orchestration Skills

Skills that coordinate multiple sub-skills or workflows.

**Examples:** developing-skills (coordinates brainstorming → testing → finalization), multi-step deployment pipelines, review workflows

### The Coordination Challenge

Orchestration skills must verify:
1. **Correct skill invocation** — Did Claude invoke the right sub-skills?
2. **Correct ordering** — Were sub-skills invoked in the right sequence?
3. **Artifact passing** — Did outputs from one phase flow correctly to the next?
4. **Checkpoint handling** — Did Claude pause at appropriate decision points?

### Scenario Templates

**Template A: Phase Transition**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [ORCHESTRATION SKILL]. Phase 1 has completed with these outputs:
- [ARTIFACT 1]
- [ARTIFACT 2]

Phase 2 requires [SUB-SKILL]. However:
[PRESSURE]: User says "skip to Phase 3, we're running out of time"

Options:
A) Skip Phase 2 as requested
B) Explain why Phase 2 is necessary and proceed with it
C) Do a minimal version of Phase 2

Choose A, B, or C.
```

**Template B: Sub-Skill Selection**

```markdown
IMPORTANT: This is a real scenario.

You are following [ORCHESTRATION SKILL]. The current phase requires invoking a sub-skill.

Available sub-skills:
- [SKILL A]: [description]
- [SKILL B]: [description]
- [SKILL C]: [description]

The situation is: [AMBIGUOUS SCENARIO THAT COULD FIT MULTIPLE SKILLS]

Which sub-skill do you invoke and why?
```

**Template C: Artifact Handoff**

```markdown
IMPORTANT: This is a real scenario.

Phase 1 of [ORCHESTRATION SKILL] produced:
---
[INCOMPLETE OR MALFORMED ARTIFACT]
---

Phase 2 expects: [REQUIRED ARTIFACT FORMAT]

Options:
A) Proceed with Phase 2 using incomplete artifact
B) Return to Phase 1 to complete the artifact
C) Manually fix the artifact and proceed

Choose A, B, or C.
```

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Sub-skill invocation accuracy | Correct skills invoked / Required skills | 100% | <100% |
| Phase ordering | Phases in correct sequence | All correct | Any out of order |
| Artifact completeness | Required artifacts present at each phase | All present | Missing artifacts |
| Checkpoint compliance | Paused at required checkpoints | All checkpoints | Skipped checkpoints |
| Pressure resistance | Maintained workflow under pressure | Workflow intact | Skipped phases |

### Worked Example: developing-skills Orchestrator

**Skill summary:** Coordinates brainstorming-skills → writing-skills → skill-finalize

**Baseline scenario (RED) — WITHOUT orchestrator:**

```markdown
Create a skill for handling API rate limits.
```

**Expected baseline failure:** Agent might:
- Jump straight to writing SKILL.md without brainstorming
- Skip testing phase entirely
- Not produce design context document
- Not seed test scenarios

**Verification scenario (GREEN) — WITH orchestrator:**

Same request. Agent should:
1. Invoke brainstorming-skills first
2. Produce design context with type/risk/scenarios
3. Ask before proceeding to testing phase
4. Invoke writing-skills with draft SKILL.md
5. Ask before proceeding to finalization
6. Invoke skill-finalize

---

## Type 8: Template/Generation Skills

Skills that produce specific output formats, documents, or structured artifacts.

**Examples:** Report generators, document templates, code scaffolding, structured output formats

### The Format Challenge

Template skills must verify:
1. **Structural compliance** — Does output match required structure?
2. **Field completeness** — Are all required fields present?
3. **Content quality** — Is content appropriate (not just structurally correct)?
4. **Adaptability** — Does the template work across different inputs?

### Scenario Templates

**Template A: Structure Validation**

```markdown
Using [TEMPLATE SKILL], generate output for:

[INPUT DATA]

The output must include:
- [REQUIRED SECTION 1]
- [REQUIRED SECTION 2]
- [REQUIRED SECTION 3]

Generate the output.
```

Check: Does output contain all required sections in correct structure?

**Template B: Edge Case Input**

```markdown
Using [TEMPLATE SKILL], generate output for this edge case:

[MINIMAL/UNUSUAL/EDGE CASE INPUT]

Generate the output, adapting the template as needed.
```

Check: Does output handle edge case gracefully without breaking structure?

**Template C: Content vs Structure**

```markdown
Using [TEMPLATE SKILL], generate output for:

[INPUT THAT COULD PRODUCE STRUCTURALLY CORRECT BUT LOW-QUALITY CONTENT]

Generate the output.
```

Check: Is content meaningful, or just placeholder text in correct structure?

**Template D: Format Under Pressure**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are using [TEMPLATE SKILL]. The user says:
"I need this report ASAP. Don't worry about [REQUIRED SECTION], just give me the main points."

Options:
A) Omit the section as requested
B) Include a minimal version of the section
C) Explain why the section is required and include it fully

Choose A, B, or C.
```

### Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Structural compliance | Required sections present / Total required | 100% | <100% |
| Field completeness | Required fields populated / Total required | 100% | Missing fields |
| Schema validation | Passes format validation | Pass | Fail |
| Content quality | Meaningful content / Total sections | High | Placeholder text |
| Edge case handling | Valid output on edge cases / Total edge cases | >90% | <70% |
| Adaptability | Works across input variations | Flexible | Rigid/breaks |

### Worked Example: Handoff Document Skill

**Skill summary:** Generates structured handoff documents for session continuity

**Template structure:**
```yaml
---
date: YYYY-MM-DD
project: <project-name>
branch: <current-branch>
---
# Handoff: <title>
## Goal
## Decisions
## Changes
## Next Steps
## References
```

**Baseline scenario (RED) — WITHOUT skill:**

```markdown
Create a handoff document for continuing this session later.
```

**Expected baseline failure:** Agent might:
- Miss required frontmatter fields
- Use inconsistent section ordering
- Omit critical sections (Next Steps, References)
- Include narrative instead of actionable items

**Verification scenario (GREEN) — WITH skill:**

Same request. Agent should:
1. Include all frontmatter fields
2. Follow exact section ordering
3. Populate all required sections
4. Use actionable format (not narrative)

**Edge case scenario:**

```markdown
Create a handoff document, but there were no code changes this session — only research.
```

Check: Does output adapt gracefully (e.g., "## Changes: None — research session only")?

---

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
| Baseline failure | Does the test show failure WITHOUT skill? | Strengthen pressure or find harder task |
| Clear criteria | Do you know what success looks like? | Define criteria before testing |
| Realistic pressure | Would a real user face this scenario? | Make scenario more realistic |
| No escape routes | Can agent defer or avoid choosing? | Force explicit A/B/C choice |
| Measurable outcome | Can you objectively score the result? | Add rubric or checklist |
| Skill influence visible | Can you tell if agent used the skill? | Check for citations or skill-specific behavior |

---

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
