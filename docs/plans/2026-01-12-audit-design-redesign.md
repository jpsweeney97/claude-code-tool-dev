# Audit Design Skill Redesign

**Date:** 2026-01-12
**Status:** Approved
**Replaces:** `.claude/skills/auditing-tool-designs/`

## Problem

The current `auditing-tool-designs` skill is slow and produces shallow findings:
- 5-6 subagent invocations (claude-code-guide + 4 lenses + Arbiter)
- 3 calibration questions before analysis starts
- Each lens works in isolation with minimal context
- Coordination overhead exceeds value

## Design Decisions

| Decision | Choice |
|----------|--------|
| Focus | Feasibility + Risk only (drop spec compliance, scope minimalism) |
| Workflow | Light confirmation (artifact type only), then autonomous |
| Output | Markdown report to `docs/audits/` |
| Architecture | Single-pass, no subagents |
| Calibration | Sensible defaults, no questions |

## New Skill: audit-design

### Invocation

```
/audit-design path/to/design.md
```

### Flow

1. Read target file
2. Detect artifact type (skill/hook/command/plugin/agent)
3. If ambiguous → ask user to confirm (single question with options)
4. Apply feasibility + risk analysis in one pass
5. Write report to `docs/audits/audit-<filename>-<date>.md`
6. Show summary in conversation

### Artifact Type Detection

| Signal | Type |
|--------|------|
| `SKILL.md` or `skills/` path | skill |
| `hooks` in frontmatter or `settings.json` | hook |
| `.claude/commands/` path | command |
| `plugin.json` | plugin |
| `.claude/agents/` path or Task tool config | agent |

## Analysis Perspectives

### Feasibility — "Will Claude actually do this?"

- State assumptions: Does it expect persistence, cross-session memory?
- Reasoning complexity: Multi-step instructions that may fail intermittently?
- Tool behavior: Assumes capabilities tools don't have?
- Proactivity: Expects Claude to act without explicit triggers?
- Model fit: Task complexity vs what the model can reliably do?

### Risk — "What breaks this?"

- Error handling: What happens when steps fail? Silent failures?
- Edge cases: Inputs or scenarios not covered?
- Recovery: How does user know something failed? How to recover?
- Integration: Handoffs between components that could fail?
- Underspecification: Guidance too vague to implement consistently?

## Output Format

### Finding Structure

```markdown
### [Title]
- **What:** [The issue]
- **Why it matters:** [Impact if not addressed]
- **Evidence:** [Quote from design]
- **Severity:** Critical / Major / Minor
- **Suggestion:** [How to fix]
```

### Report Template

```markdown
# Audit: <design-name>

**Date:** YYYY-MM-DD
**Artifact:** <type>
**File:** <path>

## Summary

<2-3 sentence assessment>

**Verdict:** Ready / Needs Work / Major Issues

## Findings

### 1. [Title]
...

## What's Working

<Brief list of strengths>
```

### Severity Definitions

- **Critical:** Will definitely fail. Design assumes something impossible.
- **Major:** Likely to cause problems. Missing handling for common cases.
- **Minor:** Could be better. Edge cases, minor gaps.

### Verdict Logic

- Any Critical → "Major Issues"
- 2+ Major → "Needs Work"
- Otherwise → "Ready"

## Removed From Current Skill

| Removed | Reason |
|---------|--------|
| 4 lens subdirectory structure | Single-pass doesn't need it |
| Arbiter synthesis | No separate outputs to merge |
| Context assessment (3 questions) | Sensible defaults instead |
| claude-code-guide lookup | Bake in needed knowledge |
| fallback-specs.md | Not doing spec compliance |
| Lens verification handshake | No lenses to verify |
| JSON implementation spec | Unnecessary artifact |
| Quick/Full modes | One mode that's already fast |
| Hierarchical audit (>50K) | YAGNI |
| Element taxonomy | Simpler finding format |
| Classification labels | Overkill |

## Definition of Done

1. Report file exists at `docs/audits/audit-<name>-<date>.md`
2. Report contains Summary, Verdict, and Findings sections
3. Each finding has What/Why/Evidence/Severity/Suggestion fields

## Implementation Notes

- New skill name: `audit-design` (shorter than `auditing-tool-designs`)
- Single SKILL.md file, ~150-200 lines
- No subdirectories
- Delete old skill after new one is validated
