# Handoff Enhancement #3: Quality Enforcement Hook

```yaml
id: handoff-quality-hook
date: 2026-02-24
status: implementing
priority: medium
blocked_by: [handoff-checkpoints]
blocks: []
related: []
plugin: packages/plugins/handoff/
```

## Problem

The creating-handoffs skill specifies a 300-line minimum, required frontmatter fields, and section depth targets. But 30% of handoffs (74/244) are under 100 lines. The quality instruction is aspirational — there's no programmatic enforcement.

**Evidence:**
- 74/244 handoffs (30%) under 100 lines
- Quality distribution is bimodal: short handoffs cluster at 34-90 lines, good ones at 300-573
- Synthesis guide improved quality dramatically (early avg 75 lines → recent avg 370 lines) but can't enforce programmatically
- No validation runs after the handoff file is written

**Cost:**
- Short handoffs represent sessions where context was lost
- Future sessions that resume from thin handoffs start with inadequate context
- Quality regression risk if synthesis guide is loaded but not followed

**Dependency on #5 (Checkpoints):** Must use different thresholds for checkpoints (50-150 lines expected) vs full handoffs (300+ lines expected). Needs the `type` frontmatter field from #5.

## Scope

**In scope:**
- PostToolUse hook on Write operations targeting handoff directory
- Validate: line count, required frontmatter, section count
- Non-blocking warning via `additionalContext` (warn, don't block)
- Checkpoint-aware thresholds

**Out of scope:**
- Blocking writes (PostToolUse can't block; PreToolUse could but is wrong tool)
- Content quality assessment (that's what the synthesis guide does)
- Modifying handoff content automatically

## Design Space

*To be filled during brainstorming. Key questions:*

1. **Hook type**: PostToolUse command hook with Python script?
2. **File detection**: How to identify handoff files? Path pattern matching?
3. **Thresholds**: What line counts, section counts, and fields to check?
4. **Warning format**: What `additionalContext` message guides Claude to fix the issue?
5. **Checkpoint awareness**: Check `type` field in frontmatter to select thresholds?
6. **Performance**: Must complete quickly — what's the timeout budget?

## Files Affected

| File | Change |
|------|--------|
| `hooks/hooks.json` | Add PostToolUse hook |
| `scripts/quality-check.py` | **New** — validation script |
| `.claude-plugin/plugin.json` | Version bump |

## Acceptance Criteria

- [ ] PostToolUse hook fires on Write to `~/.claude/handoffs/`
- [ ] Warns when full handoff is under 400 lines
- [ ] Warns when checkpoint is under 20 lines
- [ ] Warns when checkpoint exceeds 80 lines
- [ ] Warns when any of 7 required frontmatter fields are missing
- [ ] Warns when any of 13 required sections missing (handoff) or 5 sections (checkpoint)
- [ ] Warns when sections have no content (empty heading)
- [ ] Uses `type` field to select threshold set (checkpoint: 20-80, handoff: 400+)
- [ ] Validates checkpoint title starts with "Checkpoint:"
- [ ] Warning appears as `additionalContext` system reminder
- [ ] Type validated against {handoff, checkpoint} allowlist before branching
- [ ] Code fence-aware section parsing (## inside ``` not counted)
- [ ] Hollow-handoff guardrail: >=1 non-empty from {Decisions, Changes, Learnings}
- [ ] Body line count (after frontmatter), not total line count
- [ ] Conditional tail message (errors -> "fix and rewrite", warnings -> "review")
- [ ] Hook completes in under 2 seconds
- [ ] Hook never blocks session or tool execution (exit 0 always)
- [ ] SKILL.md updated: 13 required sections, 400-line minimum
- [ ] format-reference.md updated to match new quality definition
