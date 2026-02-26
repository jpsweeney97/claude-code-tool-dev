# Handoff Enhancement #5: Checkpoint Tier

```yaml
id: handoff-checkpoints
date: 2026-02-24
status: planning
priority: high
blocked_by: []
blocks: [handoff-quality-hook]
related: [handoff-search, handoff-chain-viz]
plugin: packages/plugins/handoff/
```

## Problem

The handoff plugin treats every save-state operation as a full handoff: load synthesis guide (~520 lines), answer all prompts, produce 300+ line document. At 7.4 handoffs/day (peak 25), many are lightweight "save state so I can resume" operations — not comprehensive knowledge captures.

**Evidence:**
- 30% of handoffs (74/244) are under 100 lines — they were likely intended as quick saves but triggered the full flow
- Creating-handoffs skill loads ~570 lines of context (skill + synthesis guide) every invocation
- Full synthesis is overkill when the session just needs a mid-work checkpoint

**Cost:**
- ~570 lines of context consumed per invocation regardless of intent
- Synthesis overhead for sessions that just need state preservation
- Quality floor violations (under-100-line handoffs) when full synthesis is skipped or abbreviated

## Scope

**In scope:**
- New lightweight checkpoint operation (`/handoff checkpoint` or similar)
- Reduced context load (no synthesis guide)
- Checkpoint-specific format (state, changes, next steps)
- Frontmatter field to distinguish checkpoints from full handoffs
- Resume flow handles both types transparently

**Out of scope:**
- Changing the full handoff flow (that stays as-is)
- Auto-checkpointing (no hooks that trigger checkpoints without user request)
- Checkpoint-to-handoff "upgrade" (user just creates a new full handoff)

## Design Space

*To be filled during brainstorming. Key questions:*

1. **Invocation**: `/handoff checkpoint` (subcommand of existing) vs `/checkpoint` (new command)?
2. **Skill architecture**: Separate skill vs mode within creating-handoffs vs parameterized single skill?
3. **What gets captured**: Just state + changes + next steps? Or also lightweight decisions?
4. **Format**: Same frontmatter with `type: checkpoint`? Simpler schema?
5. **Storage**: Same directory as handoffs? Subdirectory?
6. **Context budget target**: How many lines should the checkpoint skill load?
7. **Line count target**: What's the expected range for checkpoint output?
8. **Resume behavior**: Should `/resume` prefer full handoffs over checkpoints? Show type in listing?
9. **Chain semantics**: Does a checkpoint reset the chain, or is it a link in the chain like full handoffs?

## Files Affected

| File | Change |
|------|--------|
| `skills/creating-handoffs/SKILL.md` | Possibly modify, or leave unchanged if separate skill |
| `skills/checkpointing/SKILL.md` | **New** — checkpoint skill |
| `commands/checkpoint.md` | **New** — command wrapper (if separate command) |
| `references/format-reference.md` | Add checkpoint format spec |
| `skills/resuming-handoffs/SKILL.md` | Handle checkpoint type in resume/list |
| `.claude-plugin/plugin.json` | Version bump |

## Acceptance Criteria

- [ ] `/checkpoint` produces a checkpoint file
- [ ] Checkpoint loads ≤180 lines total context (skill ~100-120 + shared contract ~60)
- [ ] Checkpoint output is 22-55 lines body (37-70 total with frontmatter)
- [ ] All 5 required sections present (Current Task, In Progress, Active Files, Next Action, Verification Snapshot)
- [ ] Checkpoint frontmatter includes `type: checkpoint`
- [ ] Chain protocol works: state file read → checkpoint write → state file cleanup
- [ ] `/resume` handles checkpoints transparently (loads, archives, chains)
- [ ] `/list-handoffs` shows type column (checkpoint vs handoff)
- [ ] Existing `/handoff` flow unchanged (now loads shared contract)
- [ ] Consecutive checkpoint guardrail triggers at N=3
- [ ] `cleanup.py` uses `trash` instead of `unlink()`
