# Design Context: reviewing-skills

**Type:** Quality Enhancement
**Risk:** Medium (writes files, bounded and reversible)

## Problem Statement

Skills fail silently due to document quality issues:
- **Vague triggers** cause misfires or missed activations
- **Weak compliance language** gets rationalized around by agents
- **Missing sections** leave gaps that testing catches too late
- **Quality drift** in production skills accumulates over time
- **Author blindness** means self-reviews miss obvious issues

These issues are cheaper to fix during document review than during behavioral testing or production use.

## Success Criteria

1. Systematic review of SKILL.md files against defined quality dimensions
2. Review of references/ directory (existence, quality, coherence with SKILL.md)
3. Cross-check against external sources when skill claims to implement a spec
4. Iterative passes until Yield% converges (Framework for Thoroughness)
5. Adversarial pass to challenge the skill itself
6. Fixes applied in place (not just reported)
7. Audit report generated at `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
8. Brief summary in chat (not full report)

## Compliance Risks

Rationalizations that would cause agents to skip or shortcut this skill:

| Risk | Counter |
|------|---------|
| "The skill is simple enough" | Simple skills still have quality gaps. Explicit "no exceptions" language. |
| "I just wrote it, I know what it says" | Author blindness is real. Require noting self-review in Entry Gate. |
| "Testing will catch any issues" | Testing validates behavior, not document quality. Make distinction explicit. |
| "This is just a quick fix" | Quick fixes accumulate. Review the change, not just the original. |
| "No time for full review" | Compress output, not process. Minimum requirements per stakes level. |

## Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Single-pass checklist | Insufficient — reviewing-documents shows iteration catches what single-pass misses |
| Report-only (no fixes) | Less valuable — user wants fixes applied, not just findings reported |
| Automatic handoff to testing-skills | Too prescriptive — user should decide when to test |
| Domain accuracy validation | Out of scope — skill can check consistency with sources, not whether sources are correct |
| Rewriting fundamentally broken skills | Wrong tool — should recommend brainstorming-skills instead |

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Use Framework for Thoroughness** | User requested; reviewing-documents shows it works well for document review |
| **Default to Rigorous** | User requested; skills guide agent behavior, moderate stakes |
| **12 dimensions + 1 conditional** | Comprehensive coverage without overwhelming; conditional D13 for orchestration skills only |
| **Include references/ review** | User requested; skills are SKILL.md + references/ as a unit |
| **Cross-check external sources** | User requested; adds value when skill claims to implement a spec |
| **Rationalization table** | Skill enforces discipline; needs its own compliance defenses |
| **Dimension reference file** | Catalog in SKILL.md says *what*, reference file says *how to check* |
| **Same output pattern as reviewing-documents** | Consistency; proven pattern works well |

## Skill Pipeline Position

```
brainstorming-skills → reviewing-skills → testing-skills
        ↑                                      │
        └──────────── (if fundamental issues) ─┘
```

- **Upstream:** brainstorming-skills produces draft SKILL.md
- **This skill:** reviews document quality, applies fixes
- **Downstream:** testing-skills validates behavioral effectiveness
- **Escalation:** If skill is fundamentally flawed, recommend returning to brainstorming-skills

Also works standalone for auditing existing production skills.

## Files Created

| File | Purpose |
|------|---------|
| `.claude/skills/reviewing-skills/SKILL.md` | Main skill definition |
| `.claude/skills/reviewing-skills/references/dimension-definitions.md` | Detailed checking guidance per dimension |
| `.claude/skills/reviewing-skills/references/framework-for-thoroughness.md` | Protocol reference (copied from reviewing-documents) |
| `docs/plans/2026-01-26-reviewing-skills-design.md` | This design context document |

## Next Steps

1. **Test the skill** — Use testing-skills to validate behavioral effectiveness
2. **Promote to production** — After testing, run `uv run scripts/promote skill reviewing-skills`
