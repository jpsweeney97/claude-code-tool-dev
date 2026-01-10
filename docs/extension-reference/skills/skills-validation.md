---
id: skills-validation
topic: Skill Validation and Quality
category: skills
tags: [validation, quality, checklist, compliance]
requires: [skills-overview, skills-content-sections]
related_to: [skills-examples]
official_docs: https://code.claude.com/en/skills
---

# Skill Validation and Quality

Quality standards and validation checklist for skills.

## Workflow

Create → Test → Validate → Promote flow:

1. Create `.claude/skills/<name>/SKILL.md`
2. Test with `/<name>` in project
3. Validate against compliance checklist (below)
4. Promote to production

## Compliance Checklist

Before promoting a skill, verify:

- [ ] All 8 required content areas exist and are findable quickly
- [ ] Outputs include artifacts + ≥1 objective DoD check
- [ ] Procedure is numbered and includes ≥1 STOP/ask step
- [ ] ≥2 explicit decision points with observable triggers (or justified exception)
- [ ] Verification includes concrete quick check with expected result
- [ ] Troubleshooting includes ≥1 failure mode (symptoms/causes/next steps)
- [ ] Assumptions declared (tools/network/permissions/repo) with fallback
- [ ] Default procedure is safe (ask-first for breaking/destructive actions)
- [ ] Primary goal stated; ≥3 non-goals listed
- [ ] Commands specify expected results and fallbacks

## Semantic Quality

Beyond structure, skills need semantic precision.

### Intent Fidelity

- Primary goal stated in 1-2 sentences
- ≥3 non-goals (explicit out-of-scope items)
- No proxy goals ("improve quality") without measurable acceptance signal

### Constraint Completeness

- Declare constraints likely to be guessed wrong (no new deps, no breaking changes, no secrets)
- If constraints are unknown, STOP to ask

### Calibration

- Label claims as: Verified (evidence) / Inferred (derived) / Assumed (not verified)
- Report skipped checks as: `Not run (reason): ... Run: <command> to verify`

## Command Mention Rule

Any command in a skill MUST specify:

1. **Expected result shape** — exit code and/or output pattern
2. **Preconditions** — tools, env vars, working directory, permissions
3. **Fallback** — what to do when command cannot run (missing tool, no network, restricted permissions)

## Output Contract Details

### What Counts as Objective DoD

- Artifact existence/shape (file exists, contains required keys)
- Deterministic query/invariant (grep finds/doesn't find X)
- Executable check with expected output (command exits 0, output contains pattern)
- Deterministic logical condition (all X remain unchanged except Y)

### What Does NOT Count

- "Verify it works"
- "Ensure quality"
- "Make sure tests pass" (without specifying which tests)
- "Check for errors" (without specifying where/how)

## STOP/Ask Behavior

### STOP Patterns (Missing Inputs/Ambiguity)

```
STOP. Ask the user for: <missing required input>. Do not proceed until provided.
STOP. The request is ambiguous. Ask: <clarifying question>. Proceed only after user confirms.
```

### Ask-First Patterns (Risky/Breaking Actions)

```
Ask first: This step may be breaking/destructive (<risk>). Do not proceed without explicit user approval.
If the user does not explicitly approve <action>, skip it and provide a safe alternative.
```

## Key Points

- Validate all skills against the compliance checklist before promotion
- Semantic quality ensures skills are precise and unambiguous
- Commands must specify expected results and fallbacks
- STOP/Ask patterns prevent undefined behavior
