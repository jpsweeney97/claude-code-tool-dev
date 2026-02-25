# Design: Handoff Checkpoint Tier

```yaml
date: 2026-02-24
status: planning
ticket: docs/tickets/handoff-checkpoints.md
plugin: packages/plugins/handoff/
revision: 2 (post-Codex adversarial review, 7 turns)
```

## Problem

The handoff plugin treats every save-state operation as a full handoff: load synthesis guide (~520 lines), answer all prompts, produce 300+ line document. At 7.4 handoffs/day (peak 25), many are context-pressure saves — not comprehensive knowledge captures. 30% of handoffs are under 100 lines, indicating the full flow was triggered when a lighter-weight operation was needed.

**Key insight from Codex review:** The 74 under-100-line handoffs prove users *already do fast saves* — they just lack a sanctioned path that produces adequate (not maximal) quality. The checkpoint should legitimize and structure what's already happening, not create a "mini-handoff."

## Solution

Add a `/checkpoint` command backed by a separate skill that produces fast, lightweight state captures optimized for context-pressure session cycling. All three handoff skills (create, checkpoint, resume) share a thin contract reference for frontmatter schema, chain protocol, and storage rules.

## Design Decisions

### Trigger: Context pressure
The primary checkpoint trigger is running low on context window. Speed and low context cost matter above all. Checkpoints capture the minimum needed to resume without re-exploration: current state, active files, next action, and what failed.

### Architecture: Separate skill + shared contract

New `skills/checkpointing/SKILL.md` (~100-120 lines) with abbreviated prompts inline. All three skills (creating-handoffs, checkpointing, resuming-handoffs) load a shared `references/handoff-contract.md` (~50-80 lines) that defines the cross-skill contract: frontmatter schema, chain protocol (state file read/write/cleanup), storage conventions, and `${CLAUDE_SESSION_ID}` injection.

**Why shared contract:** The Codex review identified that full self-containment creates distributed complexity — three skills must independently agree on chain protocol, frontmatter schema, and storage conventions. A thin shared reference prevents drift while keeping skills behaviorally isolated.

**Why not full self-containment (original Approach A):** Conformance to chain protocol and frontmatter schema would depend solely on inline prompts matching an external spec (format-reference.md) that the skill never loads. This is a documentation drift risk with no mitigation.

**Rejected alternatives:**
- **Mode within creating-handoffs:** Conditional logic in instruction documents is fragile. Claude Code skills have no native parameter mechanism. Would make the already-large skill more complex.
- **Shared core module (full extraction):** Over-engineered — would require refactoring existing skills. The shared contract is a lighter version of this idea.

### Invocation: `/checkpoint`
Dedicated top-level command — fastest to type, clearly distinct from `/handoff`.

```
/checkpoint           # save state quickly
/checkpoint <title>   # save with custom title
/handoff              # full handoff (unchanged)
```

Note: `/handoff checkpoint` (subcommand form) is not supported. If a user types it, the creating-handoffs skill will treat "checkpoint" as the title argument.

### Resume: Same treatment
`/resume` loads the most recent file regardless of type. A checkpoint and a handoff are both "the last thing saved." Display shows the type for clarity.

### Chain: Same chain, labeled
Checkpoints participate in the same `resumed_from` chain as full handoffs. The `type` field in frontmatter distinguishes them. Future chain visualization (#4) can filter or annotate checkpoint vs handoff links.

### Cumulative decay guardrail
After N consecutive checkpoints without a full `/handoff`, the checkpoint skill prompts: "You've created N checkpoints in a row. Consider a full `/handoff` to capture decisions, codebase knowledge, and session narrative before they decay." Suggested N: 3.

This prevents chains of thin checkpoints from accumulating knowledge loss across sessions.

## Content Model

### Sections

| Section | Required? | Depth Target | Purpose |
|---------|-----------|-------------|---------|
| **Current Task** | Yes | 3-5 lines | What we're working on and why |
| **In Progress** | Yes | 5-15 lines | Active state: approach, working/broken, immediate next action |
| **Active Files** | Yes | 2-10 lines | Files modified or read this session with purpose |
| **Next Action** | Yes | 2-5 lines | The literal next thing to do on resume |
| **Verification Snapshot** | Yes | 1-3 lines | Last command/test run and its result — prevents debugging re-discovery |
| **Don't Retry** | If applicable | 1-3 lines/item | Failed approaches: "Tried X, failed because Y" — prevents retry waste |
| **Key Finding** | If applicable | 2-5 lines | Important codebase discovery worth preserving |
| **Decisions** | If applicable | 3-5 lines/decision | Lightweight: choice + driver only |

**Required sections sum:** 13-38 lines at depth targets. With conditional sections: 22-55 lines body.

### Excluded vs full handoffs

No session narrative, conversation highlights, user preferences, full codebase knowledge dumps, mental model, or full evidence requirements. Those belong in the full `/handoff` at natural stopping points.

**Why "Don't Retry" is included:** The Codex review identified rejected approaches as the most dangerous knowledge to lose during context-pressure saves. Failed approaches discovered mid-session are exactly what gets re-attempted after a context cycle. A "Gotchas" section is too vague to reliably prevent retries.

**Why "Verification Snapshot" is required:** Debugging-heavy sessions are the most common context-pressure trigger. Without the last command's output and result, the resumed session wastes a cycle rediscovering the exact failing state.

### Abbreviated synthesis

Four inline prompts (not a separate file):

1. What am I in the middle of right now? → Current Task + In Progress
2. What should I do first on resume? → Next Action + Verification Snapshot
3. What failed or surprised me? → Don't Retry + Key Finding (if applicable)
4. Were any decisions made? → Decisions (if applicable)

### Output target

22-55 lines body content (required sections: 13-38 lines, conditional sections: up to ~15 more). Frontmatter adds ~15 lines. Total file: 37-70 lines.

**No upper-bound enforcement.** If a checkpoint exceeds ~80 lines body, it's drifting toward handoff territory. The skill should note: "This checkpoint is getting long. Consider `/handoff` for a full capture."

## Frontmatter Schema

```yaml
---
date: YYYY-MM-DD
time: "HH:MM"
created_at: "YYYY-MM-DDTHH:MM:SSZ"
session_id: <UUID>
resumed_from: <path>                # optional
project: <project-name>
branch: <branch-name>              # optional
commit: <short-hash>               # optional
title: "Checkpoint: <descriptive-title>"
type: checkpoint                    # NEW — distinguishes from full handoffs
files:
  - <key files touched>
---
```

**Backwards compatibility:** Existing handoffs without `type` field are treated as `handoff`. The creating-handoffs skill will be updated to explicitly set `type: handoff`.

**Title convention:** Checkpoint titles use `"Checkpoint: "` prefix for scannability.

**Session ID injection:** The checkpoint skill uses `${CLAUDE_SESSION_ID}` at the top of the skill file, same mechanism as creating-handoffs (substituted by Claude Code at skill load time). Documented in `handoff-contract.md`.

## Procedure

The checkpoint skill follows this procedure (chain protocol details in `handoff-contract.md`):

1. **Check prerequisites:** If session is trivially light (no work done), ask: "Nothing to checkpoint — create one anyway?"
2. **Note session ID** from `${CLAUDE_SESSION_ID}` substitution at skill load time
3. **Gather context** using the 4 abbreviated synthesis prompts
4. **Check state file** at `~/.claude/.session-state/handoff-<session_id>` — if exists, set `resumed_from` field
5. **Check consecutive checkpoint count** — if ≥3 consecutive checkpoints (no full handoff in between), prompt for full `/handoff`
6. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
7. **Clean up state file** — `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists
8. **Verify** — confirm file exists and frontmatter is valid

Steps 4 and 7 implement the chain protocol (read state → write handoff → cleanup state). This matches creating-handoffs steps 7 and 9.

## File Plan

### New files

| File | Purpose | Est. Lines |
|------|---------|------------|
| `skills/checkpointing/SKILL.md` | Checkpoint skill | ~100-120 |
| `commands/checkpoint.md` | Thin command wrapper | ~7 |
| `references/handoff-contract.md` | Shared cross-skill contract | ~50-80 |

### Modified files

| File | Change |
|------|--------|
| `references/format-reference.md` | Add "Checkpoint Format" section (~30 lines) |
| `skills/resuming-handoffs/SKILL.md` | Show `type` column in `/list-handoffs`; display type on resume; load `handoff-contract.md` |
| `skills/creating-handoffs/SKILL.md` | Add `type: handoff` to frontmatter template; load `handoff-contract.md`; remove inline chain protocol (now in contract) |
| `scripts/cleanup.py` | Replace `Path.unlink()` with `trash` command (bug fix) |
| `.claude-plugin/plugin.json` | Version bump to 1.1.0 |

### Unchanged

| File | Why |
|------|-----|
| `skills/creating-handoffs/synthesis-guide.md` | Not loaded by checkpoints, not modified |
| `hooks/hooks.json` | No new hooks for checkpoints (quality hook is Enhancement #3) |

## Context Budget

| Operation | Context Loaded | Change |
|-----------|---------------|--------|
| `/handoff` (full) | ~570 lines + ~60 contract | +contract, net ~630 |
| `/checkpoint` | ~100-120 lines + ~60 contract | **New** — ~170 total, 70% less than `/handoff` |
| `/resume` | ~220 lines + ~60 contract | +contract, net ~280 |

The contract adds ~60 lines to each operation but eliminates drift risk. Net context for `/checkpoint` is ~170 lines — 70% less than `/handoff`.

## Resume & List Integration

**`/resume` behavior:** Unchanged logic. Loads most recent `.md` file regardless of type. Displays type: "Resuming from **checkpoint**: ..." or "Resuming from **handoff**: ...". Archive and state file behavior identical.

**`/list-handoffs` output:**

```
| Date       | Title                                          | Type       | Branch              |
|------------|------------------------------------------------|------------|---------------------|
| 2026-02-24 | Checkpoint: implementing Redis sync layer      | checkpoint | feature/rate-limit  |
| 2026-02-24 | Rate limiting — architecture and initial impl  | handoff    | feature/rate-limit  |
```

**Chain semantics:** Checkpoints are links in the chain. Chain visualization (Enhancement #4) will label them distinctly (e.g., `○` checkpoint vs `●` handoff).

## Quality Calibration

| Type | Target Lines | Minimum Sections |
|------|-------------|-----------------|
| Checkpoint | 22-55 (body) | 5 (Current Task, In Progress, Active Files, Next Action, Verification Snapshot) |
| Full handoff | 300-700+ | 6-8 |

Enhancement #3 (quality hook) will use the `type` field to select thresholds:
- Checkpoint under 20 lines → warn (likely missing required sections)
- Checkpoint over 80 lines → warn (drifting toward handoff territory, suggest `/handoff`)
- Full handoff under 300 lines → warn (under-capturing)

## Known Pre-Existing Issues

These issues exist in the current handoff system and are inherited by checkpoints. Not addressed in this design — tracked for future work:

1. **Resume-consume recovery:** `/resume` archives the handoff immediately. If the resumed session crashes before writing a new save, the latest state is in the archive and undiscoverable by plain `/resume`.
2. **Archive failure chain poisoning:** Warn-and-continue on archive creation still writes the state file for `resumed_from`, potentially producing invalid links.
3. **State-file TTL race:** 24h pruning can break `resumed_from` if user pauses more than 24h between resume and next save.

## Codex Review Summary

Adversarial review (7 turns, converged). Key changes from original design:

| Finding | Severity | Change Made |
|---------|----------|-------------|
| Goal drift: 150-300 target ≠ "fast save" | High | Revised content model to 22-55 lines |
| Chain integrity gaps (state file, SESSION_ID, cross-skill contract) | High | Added procedure section with chain protocol; added shared contract |
| Quality-hook dependency broken by spec drift | High | Reconciled thresholds (22-55 checkpoint, 300+ handoff) |
| Full self-containment creates drift risk | High | Added shared `handoff-contract.md` |
| Missing "Don't Retry" section | High | Added as conditional section |
| Verification Snapshot should be required | Medium | Added as required section |
| No cumulative decay guardrail | Medium | Added consecutive checkpoint prompt at N=3 |

## Verification

After implementation:

- [ ] `/checkpoint` produces a file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-*.md`
- [ ] Frontmatter includes `type: checkpoint` and all required fields
- [ ] Skill loads ≤120 lines + ~60 line contract (~180 total)
- [ ] Output is 22-55 lines body (37-70 total with frontmatter)
- [ ] All 5 required sections present (Current Task, In Progress, Active Files, Next Action, Verification Snapshot)
- [ ] Chain protocol works: state file read → checkpoint write → state file cleanup
- [ ] `/resume` loads checkpoints identically to full handoffs
- [ ] `/list-handoffs` shows type column
- [ ] Existing `/handoff` flow unchanged (now includes `type: handoff`, loads contract)
- [ ] Chain: checkpoint → checkpoint → full handoff preserves `resumed_from` throughout
- [ ] Consecutive checkpoint guardrail triggers at N=3
- [ ] `cleanup.py` uses `trash` instead of `unlink()`
