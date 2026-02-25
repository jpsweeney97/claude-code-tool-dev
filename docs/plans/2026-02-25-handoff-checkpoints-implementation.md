# Handoff Checkpoint Tier — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/checkpoint` command to the handoff plugin for fast, lightweight state saves during context-pressure session cycling.

**Architecture:** Separate `checkpointing` skill (~100-120 lines) + shared `handoff-contract.md` (~50-80 lines) loaded by all three handoff skills. Contract defines frontmatter schema, chain protocol, and storage conventions. Checkpoint output targets 22-55 lines body.

**Tech Stack:** Markdown skills, Python (cleanup.py fix), Claude Code plugin system

**Design doc:** `docs/plans/2026-02-24-handoff-checkpoints-design.md` (revision 2, post-Codex adversarial review)

**Plugin root:** `packages/plugins/handoff/`

---

### Task 1: Create shared handoff contract

The contract is the foundation — all subsequent tasks reference it.

**Files:**
- Create: `packages/plugins/handoff/references/handoff-contract.md`

**Step 1: Write the contract**

This document defines the cross-skill contract loaded by creating-handoffs, checkpointing, and resuming-handoffs. It covers three things: frontmatter schema, chain protocol, and storage conventions.

```markdown
# Handoff Contract

Shared contract for all handoff plugin skills. Loaded by creating-handoffs, checkpointing, and resuming-handoffs.

## Session ID

The session ID is injected by Claude Code at skill load time via `${CLAUDE_SESSION_ID}`. Each skill includes this line near the top:

**Session ID:** ${CLAUDE_SESSION_ID}

This substitution happens once when the skill loads. The resulting UUID is used for state file naming and frontmatter.

## Frontmatter Schema

All handoff files (checkpoints and full handoffs) use this frontmatter:

```yaml
---
date: YYYY-MM-DD                    # Required
time: "HH:MM"                       # Required (quoted for YAML)
created_at: "YYYY-MM-DDTHH:MM:SSZ"  # Required: ISO 8601 UTC
session_id: <UUID>                   # Required: from ${CLAUDE_SESSION_ID}
resumed_from: <path>                 # Optional: archive path if resumed
project: <project-name>             # Required: git root or directory name
branch: <branch-name>               # Optional: current git branch
commit: <short-hash>                # Optional: short commit hash
title: <descriptive-title>          # Required
type: <handoff|checkpoint>          # Required: distinguishes file type
files:
  - <key files touched>             # List of relevant files
---
```

**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints. Existing files without a `type` field are treated as `handoff` for backwards compatibility.

**Title convention:** Checkpoint titles use `"Checkpoint: <title>"` prefix. Full handoff titles have no prefix.

## Chain Protocol

The chain protocol enables `resumed_from` tracking across sessions. Three skills participate:

**Resume (resuming-handoffs) — writes state:**
1. Archive the handoff to `~/.claude/handoffs/<project>/.archive/<filename>`
2. Write archive path to `~/.claude/.session-state/handoff-<session_id>`

**Create/Checkpoint (creating-handoffs, checkpointing) — reads and cleans state:**
1. **Read:** Check `~/.claude/.session-state/handoff-<session_id>` — if exists, include path as `resumed_from` in frontmatter
2. **Write:** Write the new handoff/checkpoint file
3. **Cleanup:** Use `trash` to remove state file at `~/.claude/.session-state/handoff-<session_id>` (if exists)

**Invariant:** State files are created by resume and consumed by the next create/checkpoint. A state file that persists beyond 24 hours is stale (cleanup.py prunes these).

## Storage

| Location | Format | Retention |
|----------|--------|-----------|
| `~/.claude/handoffs/<project>/` | `YYYY-MM-DD_HH-MM_<slug>.md` | 30 days |
| `~/.claude/handoffs/<project>/.archive/` | Same | 90 days |
| `~/.claude/.session-state/handoff-<UUID>` | Plain text (path) | 24 hours |

**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.

## Project Name

Determined by:
1. Git root directory name (if in a git repo)
2. Current directory name (fallback)
3. Ask user (if ambiguous)

## Git Detection

If `.git/` exists in current or parent directories, include `branch` and `commit` in frontmatter. Otherwise omit them entirely (no placeholders).

## Write Permission

If `~/.claude/handoffs/<project>/` is not writable (or cannot be created), **STOP** and ask: "Can't write to ~/.claude/handoffs/. Where should I save this?"
```

**Step 2: Verify the contract**

Read the file back and verify:
- Frontmatter schema matches design doc
- Chain protocol has all 3 steps for create/checkpoint (read, write, cleanup)
- Session ID injection mechanism documented
- Storage conventions match existing behavior

**Step 3: Commit**

```bash
git add packages/plugins/handoff/references/handoff-contract.md
git commit -m "feat(handoff): add shared handoff contract for cross-skill consistency"
```

---

### Task 2: Create checkpoint skill

**Files:**
- Create: `packages/plugins/handoff/skills/checkpointing/SKILL.md`

**Step 1: Write the checkpoint skill**

```markdown
---
name: checkpointing
description: Used when user runs /checkpoint to save session state quickly under context pressure. Fast, lightweight alternative to /handoff. Use when user says "checkpoint", "save state", "quick save", or is running low on context.
---

**Session ID:** ${CLAUDE_SESSION_ID}

# Checkpointing

Fast state capture for context-pressure session cycling. Produces 22-55 line documents — the minimum needed to resume without re-exploration.

**Read [handoff-contract.md](../../references/handoff-contract.md) for:** frontmatter schema, chain protocol (state file read/write/cleanup), storage conventions. Follow the contract exactly.

## When to Use

- User runs `/checkpoint` or `/checkpoint <title>`
- User says "save state", "quick save", or "checkpoint"
- Session is under context pressure and needs to cycle

## When NOT to Use

- **Full knowledge capture needed** — use `/handoff` instead
- **Natural stopping point** (PR merged, plan written) — use `/handoff` instead
- **Session was trivial** — skip

## Procedure

1. **Check prerequisites:**
   - If session has no work done (no files read, no changes, no progress), ask: "Nothing to checkpoint — create one anyway?"
   - If user declines, **STOP**.

2. **Note session ID** from the "Session ID:" line above (substituted at load time)

3. **Answer the 4 synthesis prompts (INTERNAL — do not output):**
   - What am I in the middle of right now? → Current Task + In Progress
   - What should I do first on resume? → Next Action + Verification Snapshot
   - What failed or surprised me? → Don't Retry + Key Finding (if applicable)
   - Were any decisions made? → Decisions (if applicable)

4. **Check state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
   - Read `~/.claude/.session-state/handoff-<session_id>`
   - If exists, set `resumed_from` to its content

5. **Check consecutive checkpoint count:**
   - Use Glob to list recent files in `~/.claude/handoffs/<project>/`
   - Count consecutive checkpoints (files with `type: checkpoint` in frontmatter, most recent first, stopping at first `type: handoff` or missing type)
   - If count ≥ 3: prompt "You've created 3 checkpoints in a row without a full /handoff. Consider /handoff to capture decisions, codebase knowledge, and session narrative before they decay. Continue with checkpoint anyway?"
   - If user wants full handoff, **STOP** and suggest they run `/handoff`.

6. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
   - Use frontmatter from [handoff-contract.md](../../references/handoff-contract.md) with `type: checkpoint`
   - Title: `"Checkpoint: <descriptive-title>"`
   - Include only non-empty sections

7. **Cleanup state file** per chain protocol:
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists

8. **Verify:** Confirm file exists. Report: "Checkpoint saved: `<path>`"
   - Do NOT reproduce content in chat. The file is the deliverable.

## Sections

| Section | Required? | Depth | Purpose |
|---------|-----------|-------|---------|
| **Current Task** | Yes | 3-5 lines | What we're working on and why |
| **In Progress** | Yes | 5-15 lines | Approach, working/broken, immediate next action |
| **Active Files** | Yes | 2-10 lines | Files modified or key files read, with purpose |
| **Next Action** | Yes | 2-5 lines | The literal next thing to do on resume |
| **Verification Snapshot** | Yes | 1-3 lines | Last command/test and result |
| **Don't Retry** | If applicable | 1-3 lines/item | "Tried X, failed because Y" |
| **Key Finding** | If applicable | 2-5 lines | Codebase discovery worth preserving |
| **Decisions** | If applicable | 3-5 lines/decision | Choice + driver only |

**Output target:** 22-55 lines body. If exceeding ~80 lines, note: "This checkpoint is getting long. Consider `/handoff` for a full capture."

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Writing session narrative | Too expensive under context pressure | Capture state, not story |
| Full decision analysis (8 elements) | That's /handoff's job | Choice + driver only |
| Codebase knowledge dumps | Checkpoint isn't a knowledge base | Key findings only |
| Reproducing content in chat | File is the deliverable | Brief confirmation only |
```

**Step 2: Verify skill structure**

Check:
- Frontmatter has `name` (kebab-case) and `description` (what + when + triggers)
- References `handoff-contract.md` via relative link
- Skill is under 120 lines
- Procedure matches design doc (8 steps)
- All 5 required sections present in table
- Chain protocol steps match contract (read state → write → cleanup)

**Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/checkpointing/SKILL.md
git commit -m "feat(handoff): add checkpointing skill for fast state saves"
```

---

### Task 3: Create checkpoint command

**Files:**
- Create: `packages/plugins/handoff/commands/checkpoint.md`

**Step 1: Write the command wrapper**

Follow the exact pattern from `commands/handoff.md` and `commands/resume.md`:

```markdown
---
description: Save session state quickly (lightweight alternative to /handoff)
disable-model-invocation: true
---

Invoke the handoff:checkpointing skill and follow it exactly as presented to you
```

**Step 2: Verify command**

- `disable-model-invocation: true` present (manual invocation only)
- References `handoff:checkpointing` skill correctly
- Description is concise

**Step 3: Commit**

```bash
git add packages/plugins/handoff/commands/checkpoint.md
git commit -m "feat(handoff): add /checkpoint command wrapper"
```

---

### Task 4: Update creating-handoffs skill

**Files:**
- Modify: `packages/plugins/handoff/skills/creating-handoffs/SKILL.md`

Three changes: (a) add `type: handoff` to frontmatter template, (b) add contract reference, (c) note that chain protocol details are in the contract.

**Step 1: Add contract reference after the Session ID line**

At line 6 of SKILL.md (after `**Session ID:** ${CLAUDE_SESSION_ID}`), add:

```markdown
**Read [handoff-contract.md](../../references/handoff-contract.md) for:** frontmatter schema, chain protocol, storage conventions.
```

**Step 2: Add `type: handoff` to the frontmatter schema**

In the Outputs section (around line 59 in the frontmatter example within format-reference), the creating-handoffs skill references `format-reference.md` for the schema. The contract now also has the schema with the `type` field. No inline schema change needed in SKILL.md itself — the contract and format-reference define it.

But we need to ensure step 7 of the procedure explicitly includes `type: handoff`:

At the procedure step 7 (line 143), change:
```
7. **Generate markdown** with frontmatter per [format-reference.md](../../references/format-reference.md):
   - Include `session_id:` with the UUID from step 2
```

To:
```
7. **Generate markdown** with frontmatter per [format-reference.md](../../references/format-reference.md) and [handoff-contract.md](../../references/handoff-contract.md):
   - Include `session_id:` with the UUID from step 2
   - Include `type: handoff` in frontmatter
```

**Step 3: Verify changes**

- Contract reference appears near top of skill
- `type: handoff` explicitly mentioned in procedure step 7
- No other behavioral changes to creating-handoffs

**Step 4: Commit**

```bash
git add packages/plugins/handoff/skills/creating-handoffs/SKILL.md
git commit -m "feat(handoff): add type field and contract reference to creating-handoffs"
```

---

### Task 5: Update resuming-handoffs skill

**Files:**
- Modify: `packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`

Three changes: (a) add contract reference, (b) display type on resume, (c) add type column to `/list-handoffs`.

**Step 1: Add contract reference after Session ID line**

At line 7 (after `**Session ID:** ${CLAUDE_SESSION_ID}`), add:

```markdown
**Read [handoff-contract.md](../../references/handoff-contract.md) for:** frontmatter schema, chain protocol, storage conventions.
```

**Step 2: Update resume display (step 5 of procedure)**

At line 116-119, change:
```
5. **Display and summarize:**
   - Show full handoff content
   - Summarize key points: goal, decisions, next steps
   - Offer: "Continue with [first next step]?"
```

To:
```
5. **Display and summarize:**
   - Show full handoff/checkpoint content
   - Note the type: "Resuming from **checkpoint**: ..." or "Resuming from **handoff**: ..."
   - Summarize key points: goal/current task, decisions, next steps/next action
   - Offer: "Continue with [first next step/action]?"
```

**Step 3: Update `/list-handoffs` format (line 135)**

Change:
```
3. Format as table: date, title, branch
```

To:
```
3. Format as table: date, title, type, branch
   - `type` comes from frontmatter `type` field. If missing, display as `handoff` (backwards compatibility).
```

**Step 4: Verify changes**

- Contract reference present
- Resume displays type label
- List-handoffs shows type column with backwards compatibility

**Step 5: Commit**

```bash
git add packages/plugins/handoff/skills/resuming-handoffs/SKILL.md
git commit -m "feat(handoff): add type display to resume and list-handoffs"
```

---

### Task 6: Add checkpoint format to format-reference

**Files:**
- Modify: `packages/plugins/handoff/references/format-reference.md`

**Step 1: Add checkpoint format section**

After the "Quality Calibration" section (end of file, around line 705), add:

```markdown
## Checkpoint Format

Checkpoints are lightweight state captures for context-pressure session cycling. They use the same frontmatter schema as full handoffs (see above) with `type: checkpoint`.

### Checkpoint Sections

| Section | Required? | Depth | Purpose |
|---------|-----------|-------|---------|
| **Current Task** | Yes | 3-5 lines | What we're working on and why |
| **In Progress** | Yes | 5-15 lines | Approach, working/broken, immediate next action |
| **Active Files** | Yes | 2-10 lines | Files modified or key files read, with purpose |
| **Next Action** | Yes | 2-5 lines | The literal next thing to do on resume |
| **Verification Snapshot** | Yes | 1-3 lines | Last command/test and result |
| **Don't Retry** | If applicable | 1-3 lines/item | "Tried X, failed because Y" |
| **Key Finding** | If applicable | 2-5 lines | Codebase discovery worth preserving |
| **Decisions** | If applicable | 3-5 lines/decision | Choice + driver only |

### Checkpoint Quality Calibration

| Metric | Target |
|--------|--------|
| Body lines | 22-55 |
| Required sections | 5 (Current Task, In Progress, Active Files, Next Action, Verification Snapshot) |
| Warning: under | 20 lines (likely missing sections) |
| Warning: over | 80 lines (drifting toward handoff) |

### Filename Convention

Checkpoint filenames use `checkpoint-` prefix in slug: `YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
```

**Step 2: Verify**

- Section added after existing content
- Table matches design doc content model
- Quality thresholds match design doc

**Step 3: Commit**

```bash
git add packages/plugins/handoff/references/format-reference.md
git commit -m "docs(handoff): add checkpoint format section to format-reference"
```

---

### Task 7: Fix cleanup.py (unlink → trash)

**Files:**
- Modify: `packages/plugins/handoff/scripts/cleanup.py`

**Step 1: Replace `unlink()` with `trash` subprocess call**

In `prune_old_handoffs` (line 58), change:
```python
                handoff.unlink(missing_ok=True)
```
To:
```python
                subprocess.run(["trash", str(handoff)], capture_output=True, timeout=5)
```

In `prune_old_state_files` (line 78), change:
```python
                state_file.unlink(missing_ok=True)
```
To:
```python
                subprocess.run(["trash", str(state_file)], capture_output=True, timeout=5)
```

**Step 2: Verify `trash` is available**

Run: `which trash`

Expected: `/opt/homebrew/bin/trash` or similar path (macOS `trash` CLI)

**Step 3: Test cleanup script runs without error**

Run: `python3 packages/plugins/handoff/scripts/cleanup.py`

Expected: Exit code 0, no output (silent cleanup)

**Step 4: Commit**

```bash
git add packages/plugins/handoff/scripts/cleanup.py
git commit -m "fix(handoff): use trash instead of unlink in cleanup.py"
```

---

### Task 8: Bump plugin version

**Files:**
- Modify: `packages/plugins/handoff/.claude-plugin/plugin.json`

**Step 1: Update version**

Change `"version": "1.0.0"` to `"version": "1.1.0"`.

**Step 2: Commit**

```bash
git add packages/plugins/handoff/.claude-plugin/plugin.json
git commit -m "chore(handoff): bump plugin version to 1.1.0"
```

---

### Task 9: Integration verification

**No files changed** — this is a verification task.

**Step 1: Verify file structure**

Run: `find packages/plugins/handoff -name '*.md' -o -name '*.py' -o -name '*.json' | sort`

Expected tree should include:
```
packages/plugins/handoff/.claude-plugin/marketplace.json
packages/plugins/handoff/.claude-plugin/plugin.json
packages/plugins/handoff/commands/checkpoint.md
packages/plugins/handoff/commands/handoff.md
packages/plugins/handoff/commands/resume.md
packages/plugins/handoff/hooks/hooks.json
packages/plugins/handoff/references/format-reference.md
packages/plugins/handoff/references/handoff-contract.md
packages/plugins/handoff/scripts/cleanup.py
packages/plugins/handoff/skills/checkpointing/SKILL.md
packages/plugins/handoff/skills/creating-handoffs/SKILL.md
packages/plugins/handoff/skills/creating-handoffs/synthesis-guide.md
packages/plugins/handoff/skills/resuming-handoffs/SKILL.md
```

**Step 2: Verify context budgets**

Count lines in each skill + contract:
```bash
wc -l packages/plugins/handoff/skills/checkpointing/SKILL.md
wc -l packages/plugins/handoff/references/handoff-contract.md
```

Expected:
- `checkpointing/SKILL.md`: ≤120 lines
- `handoff-contract.md`: ≤80 lines
- Total checkpoint context: ≤180 lines

**Step 3: Verify contract references**

```bash
grep -l "handoff-contract.md" packages/plugins/handoff/skills/*/SKILL.md
```

Expected: All three skills reference the contract:
- `skills/checkpointing/SKILL.md`
- `skills/creating-handoffs/SKILL.md`
- `skills/resuming-handoffs/SKILL.md`

**Step 4: Verify type field**

```bash
grep "type:" packages/plugins/handoff/skills/checkpointing/SKILL.md
grep "type:" packages/plugins/handoff/skills/creating-handoffs/SKILL.md
```

Expected:
- Checkpointing mentions `type: checkpoint`
- Creating-handoffs mentions `type: handoff`

**Step 5: Verify cleanup.py uses trash**

```bash
grep -n "unlink" packages/plugins/handoff/scripts/cleanup.py
grep -n "trash" packages/plugins/handoff/scripts/cleanup.py
```

Expected: No `unlink` calls, `trash` subprocess calls present.

**Step 6: Manual smoke test**

Reinstall the plugin and test:
```bash
claude plugin marketplace update handoff-dev
claude plugin install handoff@handoff-dev
```

Then in a new session:
1. Run `/checkpoint` — should produce a file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-*.md`
2. Run `/list-handoffs` — should show type column
3. Run `/resume` — should load the checkpoint with "Resuming from **checkpoint**:" label
4. Run `/handoff` — should include `type: handoff` in frontmatter

---

## Summary

| Task | What | Files | Est. |
|------|------|-------|------|
| 1 | Shared contract | Create `references/handoff-contract.md` | ~70 lines |
| 2 | Checkpoint skill | Create `skills/checkpointing/SKILL.md` | ~115 lines |
| 3 | Command wrapper | Create `commands/checkpoint.md` | ~7 lines |
| 4 | Update creating-handoffs | Add type + contract ref | ~3 line changes |
| 5 | Update resuming-handoffs | Type display + contract ref | ~8 line changes |
| 6 | Checkpoint format spec | Add to `format-reference.md` | ~30 lines |
| 7 | Fix cleanup.py | `unlink` → `trash` | 2 line changes |
| 8 | Version bump | `plugin.json` | 1 line change |
| 9 | Integration verification | Smoke test | No changes |
