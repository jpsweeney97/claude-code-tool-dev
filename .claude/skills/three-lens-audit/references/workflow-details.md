# Re-Audit Workflow

Verify fixes after making changes based on audit findings.

## When to Re-audit

| Situation                            | Strategy               | Why                              |
| ------------------------------------ | ---------------------- | -------------------------------- |
| Fixed Critical/Major findings        | Full re-audit          | Verify fixes; catch regressions  |
| Significant refactoring during fixes | Full re-audit          | Changes may introduce new issues |
| Fixed issues from one lens only      | Single-lens re-audit   | Targeted verification            |
| Minor wording/formatting tweaks      | Spot-check (no agents) | Low risk, not worth the cost     |
| Pre-ship final check                 | Full re-audit          | Complete confidence              |

## Re-audit Strategies

**Full Re-audit** (Recommended for significant changes)

Run the complete 3-lens audit again:

```bash
python scripts/run_audit.py prepare target.md
# Run all 3 agents, save outputs
python scripts/run_audit.py finalize *.md --target "Target v2"
```

Why full re-audit matters: A fix for one lens might create problems another lens would catch. Security fix → usability regression. Simplification → completeness gap.

**Single-Lens Re-audit** (For targeted verification)

Re-run only the lens that flagged the issues you fixed:

```
/three-lens-audit target.md --lens adversarial
```

Cheaper and faster, but won't catch cross-lens regressions.

**Spot-Check** (For trivial changes)

Review changes without running agents. Suitable for typos, formatting, minor clarifications where the fix is obviously correct.

## Comparing Before/After

1. **Save original synthesis** before making changes (e.g., `synthesis-v1.md`)
2. **Run re-audit** after fixes (produces `synthesis-v2.md`)
3. **Compare:**

| Question                    | Good Sign                        | Warning Sign              |
| --------------------------- | -------------------------------- | ------------------------- |
| Original findings resolved? | Specific issues no longer appear | Same issues reappear      |
| New findings emerged?       | None, or only Minor              | New Critical/Major issues |
| Convergent findings?        | Reduced or eliminated            | Same count or increased   |

## Exit Criteria

An artifact is ready to ship when:

- [ ] No Critical findings remaining
- [ ] No convergent findings (issues flagged by 2+ lenses)
- [ ] All Major findings either fixed or explicitly accepted as known risk
- [ ] Re-audit shows measurable improvement over original

**Acceptable risk:** Some Minor findings may remain if cost-to-fix exceeds benefit. Document these as known limitations rather than grinding to zero.

## Iteration Pattern

```
Audit v1 → Fix → Re-audit v2 → Fix → Re-audit v3 → Ship
                      │                    │
                      │                    └── New issues? Iterate
                      └── New issues? Iterate
```

**Diminishing returns:** If re-audit v3 finds only the same Minor issues as v2, you've reached diminishing returns. Ship it.

**Red flag:** If each re-audit finds _entirely different_ issues unrelated to your fixes, the artifact may need fundamental redesign, not incremental fixes. Consider stepping back to reassess the approach.

## Action Tracking Template

Copy this template after synthesis to track fixes:

```markdown
## Audit Action Plan: [Target Name] - [Date]

### Convergent Findings (Priority 1)

| Finding   | Severity       | Status              | Resolution |
| --------- | -------------- | ------------------- | ---------- |
| [finding] | Critical/Major | Open/Fixed/Deferred | [notes]    |

### Lens-Specific Findings

| Finding   | Lens                               | Status              | Resolution |
| --------- | ---------------------------------- | ------------------- | ---------- |
| [finding] | Adversarial/Pragmatic/Cost-Benefit | Open/Fixed/Deferred | [notes]    |

### Deferred Items

| Finding   | Reason         | Revisit By        |
| --------- | -------------- | ----------------- |
| [finding] | [why deferred] | [date or trigger] |
```

**Status values:**

- `Open` — Not yet addressed
- `Fixed` — Resolved, verified in re-audit
- `Deferred` — Intentionally postponed (document reason)
- `Won't Fix` — Accepted as known limitation
