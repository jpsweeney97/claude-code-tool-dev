---
id: skills-anti-patterns
topic: Skill Anti-Patterns
category: skills
tags: [anti-patterns, mistakes, quality, validation]
requires: [skills-overview, skills-content-sections]
related_to: [skills-validation, skills-examples]
official_docs: https://code.claude.com/en/skills
---

# Skill Anti-Patterns

Common mistakes when writing skills and how to prevent them.

## Activation Problems

| Anti-pattern | Problem | Prevention |
|--------------|---------|------------|
| Over-broad activation | Skill triggers for unintended requests due to vague "When to use" or missing "When NOT to use" | Add explicit "When NOT to use" bullets; include STOP/ask for ambiguous requests |
| Implicit assumptions | Skill relies on unstated environment (tools, network, repo layout) or user intent | Declare constraints in Inputs section; provide fallback when assumptions aren't met |

```yaml
# Bad: vague activation
## When to Use
- When working with code

# Good: specific boundaries
## When to Use
- Fixing narrow bugs with existing test coverage

## When NOT to Use
- Dependency upgrades, schema migrations, security changes
- STOP if user cannot state expected behavior or provide failing test
```

## Procedure Problems

| Anti-pattern | Problem | Prevention |
|--------------|---------|------------|
| Premature solutioning | Edits files before gathering evidence (repro, logs, success criteria) | Add inspect/evidence step before writes; STOP when evidence missing |
| Scope creep | Expands beyond request (refactors, upgrades, unrelated cleanup) | Explicit non-goals; ask-first for breaking/risky actions |
| Unsafe default | Default behavior performs destructive/irreversible actions without approval | Add ask-first gate before dangerous operations; conservative defaults |

```markdown
# Bad: jumps to editing
## Procedure
1. Open the file
2. Fix the bug

# Good: evidence first
## Procedure
1. **Do not edit files yet.** Reproduce the issue and capture expected vs actual behavior.
2. State root cause hypothesis with supporting evidence.
3. Implement the smallest correct change.
```

## Verification Problems

| Anti-pattern | Problem | Prevention |
|--------------|---------|------------|
| Verification theater | Checks are non-executable, non-specific, or disconnected from outcome | At least one concrete quick check with expected result shape tied to DoD |
| Decision-point omission | Says "use judgment" instead of encoding branches | At least 2 explicit "If ... then ... otherwise" decision points |
| Proxy-only verification | Checks compile/lint when behavior correctness is the goal | Quick check must measure primary success property |
| Silent skipping | Verification skipped without reporting reason | Always report skipped checks: "Not run (reason): ... Run: `<cmd>`" |

```markdown
# Bad: vague verification
## Verification
- Make sure it works
- Check for errors

# Good: concrete checks
## Verification
Quick check: Run `pytest tests/test_auth.py -k login`. Expected: all tests pass.
If quick check fails, do not continue—go to Troubleshooting.
```

## Recovery Problems

| Anti-pattern | Problem | Prevention |
|--------------|---------|------------|
| Unrecoverable procedure | No path forward when steps fail | At least one troubleshooting entry with symptoms/causes/next steps |
| Non-portable instructions | Depends on host-specific behavior without alternatives | Declare assumptions; provide offline/restricted fallbacks |
| Evidence-free outputs | Reports/recommendations omit rationale, making review impossible | Each finding must include evidence trail (path, query, observation) |

```markdown
# Bad: no recovery path
## Troubleshooting
(empty or missing)

# Good: actionable recovery
## Troubleshooting
**Symptom:** Test still fails after patch
**Causes:** Wrong code path; missing edge case; test not exercising intended path
**Next steps:** Re-check repro assumptions, add logging, narrow failing input, update hypothesis
```

## Key Points

- Over-broad activation → explicit "When NOT to use" + STOP/ask
- Implicit assumptions → declare constraints + fallback
- Premature solutioning → evidence before edits
- Scope creep → non-goals + ask-first
- Verification theater → concrete quick check with expected result
- Decision-point omission → ≥2 explicit If/then/otherwise branches
- Unsafe default → ask-first gate for destructive actions
- Unrecoverable procedure → troubleshooting with symptoms/causes/next
- Non-portable instructions → assumptions + offline fallbacks
- Proxy-only verification → quick check measures primary property
- Silent skipping → report "Not run (reason)" with manual command
- Evidence-free outputs → include evidence trail per finding
