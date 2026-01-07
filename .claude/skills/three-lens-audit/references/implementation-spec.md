# Implementation Spec Output Format

Use `--impl-spec` to generate an actionable implementation spec instead of a synthesis report. This format is optimized for Claude Code to execute fixes systematically.

## When to Use

| Situation | Output Format |
|-----------|---------------|
| Understanding findings | Default synthesis report |
| Executing fixes | `--impl-spec` |
| Tracking progress | `--impl-spec` |

## Spec Structure

```markdown
# Implementation Spec: {target}

## Summary
| Priority | Count | Convergence | Detail Level |
|----------|-------|-------------|--------------|
| P1       | N     | All 3 lenses | Detailed |
| P2       | N     | 2 lenses | High-level |
| P3       | N     | Single lens | Brief |

## P1 Tasks (Detailed)
### Task 1.1: {finding description}
**File:** `{target}`
**Convergence:** All 3 lenses (confidence: X%)

**Rationale:**
- Adversarial: "..."
- Pragmatic: "..."
- Cost/Benefit: "..."

**Implementation:**
1. Locate the relevant section
2. Address the issue
3. Verify the fix

**Done Criteria:**
- [ ] Issue no longer flagged
- [ ] Usability improved
- [ ] Cost/benefit justified

## P2 Tasks (High-Level)
### Task 2.1: {finding}
**Action:** {what to do}
**Done Criteria:** {single statement}

## P3 Tasks (Optional)
### Task 3.1: {finding}
**Lens:** {which lens}
**Action:** {brief description}
```

## Priority Mapping

| Convergence | Priority | Detail Level |
|-------------|----------|--------------|
| All 3 lenses | P1 | Detailed implementation steps |
| 2 lenses | P2 | High-level action + done criteria |
| Single lens | P3 | Brief description (optional) |

## Example Workflow

```bash
# Run audit
python scripts/run_audit.py finalize adv.md prag.md cb.md --target "SKILL.md"

# Generate implementation spec
python scripts/run_audit.py finalize adv.md prag.md cb.md --target "SKILL.md" --impl-spec > impl-spec.md

# Execute with Claude Code
# Claude reads impl-spec.md, creates TodoWrite entries, executes P1 first
```

_Full example: [../examples/implementation-spec-example.md](../examples/implementation-spec-example.md)_
