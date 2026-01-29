# Task Skill Template

For skills that provide step-by-step instructions: deployments, commits, code generation, specific actions.

```yaml
---
name: <skill-name>
description: <trigger conditions — when to invoke this task>
disable-model-invocation: true  # Set if user-invoked only (e.g., /deploy)
---
```

## When to Use

<!-- When should this task be invoked? What context triggers it? -->

## Steps

<!-- Numbered steps for the task. Keep steps atomic and verifiable. -->

1. [First step]
2. [Second step]
3. ...

## Verification

<!-- How to confirm the task succeeded. What should the user see/check? -->

**Quick check:** [Concrete verification with expected result]

<!--
TEMPLATE GUIDANCE:
- Task skills are PROCEDURES with clear start and end
- Steps should be atomic — one action per step
- Include verification so users know the task succeeded
- If steps require judgment calls, add a Decision Points section
- If task commonly fails, add Troubleshooting

OPTIONAL SECTIONS (add if needed):
- Decision Points: If steps require judgment or branching
- Troubleshooting: If task commonly fails in predictable ways
- Inputs: If task requires user to provide parameters

DO NOT ADD these sections (they indicate wrong template choice):
- Examples (BAD/GOOD comparisons) — steps are self-evident
- Anti-Patterns — unless task is commonly misused
- Rationalizations — not discipline-enforcing
-->

---

## Validation Checklist

Before finalizing, verify:

- [ ] Steps are atomic and verifiable
- [ ] Verification section tells user how to confirm success
- [ ] Description contains trigger conditions only
- [ ] No discipline-enforcement language (if present, use template-methodology.md)

**Remove this section before finalizing the skill.**
