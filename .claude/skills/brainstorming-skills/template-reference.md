# Reference Skill Template

For skills that provide knowledge Claude applies to work: conventions, patterns, style guides, domain knowledge.

```yaml
---
name: <skill-name>
description: <when this knowledge applies — trigger conditions only>
---
```

[Knowledge content goes here]

<!--
TEMPLATE GUIDANCE:
- Reference skills are KNOWLEDGE, not workflows
- Keep it concise — if you need more than ~50 lines, consider if this is really a reference skill
- No process to follow = no Process section needed
- If you find yourself adding steps, use template-task.md instead
- If you need Anti-Patterns or Troubleshooting, use template-methodology.md instead

DO NOT ADD these sections (they indicate wrong template choice):
- Process / Steps / Procedure
- Decision Points
- Examples (BAD/GOOD comparisons)
- Anti-Patterns
- Troubleshooting
- Rationalizations
-->

---

## Validation Checklist

Before finalizing, verify:

- [ ] Content is knowledge/conventions, not a workflow
- [ ] Description contains trigger conditions only (when to apply this knowledge)
- [ ] No procedural steps exist in the content
- [ ] Content is concise and scannable

**Remove this section before finalizing the skill.**
