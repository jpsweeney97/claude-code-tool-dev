# Testing Quality Enhancement Skills

Skills that make output "better" along some dimension.

**Examples:** Better explanations, clearer code review feedback, more thorough documentation

## PREREQUISITE: Defined Quality Criteria

**You cannot test quality without defined criteria. This is a hard gate.**

Before any testing, verify the skill specifies:
- [ ] Concrete quality dimensions (clarity, completeness, accuracy, etc.)
- [ ] What "good" looks like for each dimension (with examples)
- [ ] What "bad" looks like for each dimension (with examples)

| Skill says... | Testable? | Action |
|---------------|-----------|--------|
| "Make explanations clearer" | No | Fix skill: define what "clear" means |
| "Improve with better structure, examples, and plain language" | Partial | Fix skill: add examples of good/bad for each |
| "Structure: use headers. Examples: concrete not abstract. Language: no jargon without definition" | Yes | Proceed to testing |

**If the skill just says "make it better" without criteria, fix the skill first. Testing undefined quality is theater.**

## Scenario Templates

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

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Dimension coverage | Criteria addressed / Total criteria | 100% | <100% |
| Rubric score improvement | After score - Before score | Positive on all | Negative on any |
| Blind preference | Evaluator prefers improved version | >80% | <60% |
| Specific improvement count | Concrete changes made | Matches criteria count | Generic changes |
| Regression rate | Dimensions that got worse | 0 | >0 |
| Adversarial survival | No clearly better version found | Survives | Better version found |

## Verification Protocol for Quality Enhancement

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

## Worked Example: Clearer Explanations Skill

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
