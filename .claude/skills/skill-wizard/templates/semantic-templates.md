# Semantic Templates (T1-T7)

Copy/paste-ready templates from the semantic quality addendum.

## T1: Semantic Contract Block (When to Use)

```markdown
## When to Use

**Primary goal:** [1-2 sentence description of what this skill accomplishes]

**Triggers:**
- User says "[exact phrases that activate this skill]"
- User needs to [specific action] for [specific context]
- Before/after [specific event in workflow]
```

## T2: Scope Fence (Inputs or Procedure)

```markdown
**Scope fence:**
- MAY touch: [paths/modules/systems explicitly in scope]
- MUST NOT touch: [paths/modules/systems explicitly out of scope]
- Crossing the fence requires: STOP and ask user for explicit approval
```

## T3: Assumptions Ledger (Inputs or Outputs)

```markdown
**Assumptions:**
| Assumption | Verified | Evidence |
|------------|----------|----------|
| [assumption 1] | Verified/Inferred/Assumed | [file:line or "not checked"] |
| [assumption 2] | Verified/Inferred/Assumed | [file:line or "not checked"] |
```

## T4: Decision Point with Observable Trigger

```markdown
**If** `<file>` exists (check: `test -f <file>`)
**then** [action A]
**otherwise** [action B]
```

## T5: Verification Ladder (Medium/High Risk)

```markdown
**Verification ladder:**

1. **Quick check** (seconds): [primary signal]
   - Run: `<command>`
   - Expected: [pattern]

2. **Narrow check** (minutes): [neighbors/related]
   - Run: `<command>`
   - Expected: [pattern]

3. **Broad check** (longer): [system confidence]
   - Run: `<command>`
   - Expected: [pattern]

Each rung must pass before proceeding to the next.
```

## T6: Failure Interpretation Table (Troubleshooting)

```markdown
| Symptom | Likely Cause | Next Steps |
|---------|--------------|------------|
| [exact error/behavior] | [specific cause] | [specific commands/actions] |
| [exact error/behavior] | [specific cause] | [specific commands/actions] |
```

## T7: Calibration Wording (Procedure, Outputs, Verification)

```markdown
**Calibration:**
Label conclusions as:
- **Verified**: supported by direct evidence (paths/commands/observations)
- **Inferred**: derived from verified facts; call out inference explicitly
- **Assumed**: not verified; STOP/ask if assumption is material

If a verification step was not run, report:
`Not run (reason): <reason>. Run: <command>. Expected: <pattern>.`
```

## Template Suggestions by Section

| Section | Templates to Offer |
|---------|-------------------|
| When to use | T1 (semantic contract) |
| Inputs | T2 (scope fence), T3 (assumptions ledger) |
| Outputs | T3 (for audit skills producing reports) |
| Decision Points | T4 (observable trigger phrasing) |
| Verification | T5 (verification ladder for Medium/High), T7 (calibration) |
| Troubleshooting | T6 (failure interpretation table) |
