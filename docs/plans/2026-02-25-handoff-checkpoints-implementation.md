# Handoff Checkpoint Tier — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/checkpoint` command to the handoff plugin for fast, lightweight state saves during context-pressure session cycling.

**Architecture:** Separate `checkpointing` skill (~130-150 lines) + shared `handoff-contract.md` (~80-100 lines) loaded by all three handoff skills. Contract defines frontmatter schema, chain protocol, storage conventions, precedence rules, and known limitations. Checkpoint output targets 22-55 lines body.

**Tech Stack:** Markdown skills, Python (cleanup.py fix), Claude Code plugin system

**Design doc:** `docs/plans/2026-02-24-handoff-checkpoints-design.md` (revision 2, post-Codex adversarial review)

**Plugin root:** `packages/plugins/handoff/`

**Codex review (adversarial-challenge, 5 turns):** Plan revised to incorporate 12 findings. Key changes: chain-walk replaces Glob scan for N≥3 guardrail (critical correctness fix), inline chain protocol removed from creating-handoffs (design doc compliance), triple-authority schema resolved with precedence rules, cleanup.py error handling added, smoke test expanded to 12-item design verification checklist. See commit history for pre-review version.

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

## Precedence

This contract is canonical for cross-skill invariants: frontmatter field definitions, type semantics, chain protocol, and storage/retention. `format-reference.md` is canonical for section content guidance, depth targets, quality calibration, and examples. If `format-reference.md` conflicts with this contract, **this contract wins**.

## Known Limitations

Three inherited issues from the current chain protocol design. These are pre-existing — not introduced by the checkpoint tier.

1. **Resume-consume recovery:** If a session resumes a handoff but crashes before creating a new one, the state file is consumed but no successor exists. The chain has a gap. No automated recovery — the archived file is intact and can be manually re-resumed.

2. **Archive-failure chain poisoning:** If archive creation fails but the state file is written, the `resumed_from` path in the next handoff/checkpoint points to a non-existent file. Skills should not fail on a missing `resumed_from` target — treat as informational metadata.

3. **State-file TTL race:** State files are pruned after 24 hours by cleanup.py. If a session spans >24 hours (rare), the state file may be pruned before the next create/checkpoint reads it. Result: missing `resumed_from` in the next file. Not data loss — the chain link is skipped.
```

**Step 2: Verify the contract**

Read the file back and verify:
- Frontmatter schema matches design doc
- Chain protocol has all 3 steps for create/checkpoint (read, write, cleanup)
- Session ID injection mechanism documented
- Storage conventions match existing behavior
- Known Limitations section acknowledges 3 inherited chain protocol issues
- Precedence section declares contract canonical for cross-skill invariants

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
   - Determine project name per [handoff-contract.md](../../references/handoff-contract.md) (git root name or cwd name).
   - Verify `~/.claude/handoffs/<project>/` is writable. If not writable and cannot be created, **STOP** per contract Write Permission section.
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

5. **Check consecutive checkpoint count via chain walk:**
   - If `resumed_from` was set in step 4, read the archived file it points to
   - Check its `type:` frontmatter field. If `checkpoint`, increment count and follow its `resumed_from` (if present)
   - Stop at first `type: handoff`, missing `type`, missing file, or count ≥ 3
   - This is bounded to 3-4 file reads maximum — faster than Glob and correct across the resume/archive lifecycle (Glob scan of active directory fails because `/resume` archives files to `.archive/`)
   - If `resumed_from` was NOT set (no state file — e.g., TTL race, first checkpoint of session): skip the guardrail. Emit no warning — lack of state file is not evidence of checkpoint streaking.
   - If count ≥ 3: prompt "You've created 3 checkpoints in a row without a full /handoff. Consider /handoff to capture decisions, codebase knowledge, and session narrative before they decay. Continue with checkpoint anyway?"
   - If user wants full handoff, **STOP** and suggest they run `/handoff`.

6. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
   - Use frontmatter from [handoff-contract.md](../../references/handoff-contract.md) with `type: checkpoint`
   - Title: `"Checkpoint: <descriptive-title>"`
   - Required sections (5) are always included — use placeholder content for thin sessions (e.g., "No commands run yet" for Verification Snapshot). Conditional sections (3) are omitted when not applicable.

7. **Cleanup state file** per chain protocol:
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists

8. **Verify:** Confirm file exists and frontmatter is valid (required fields present per contract). Report: "Checkpoint saved: `<path>`"
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

## Troubleshooting

### File not created

**Symptoms:** Checkpoint command completes but no file appears

**Likely causes:**
- Project name detection failed (not in a git repo, ambiguous directory)
- Write permission denied on `~/.claude/handoffs/<project>/`

**Next steps:**
1. Check project detection: `git rev-parse --show-toplevel 2>/dev/null || pwd`
2. Check permissions: `ls -la ~/.claude/handoffs/`
3. Create directory manually if needed: `mkdir -p ~/.claude/handoffs/<project>`

### Missing resumed_from

**Symptoms:** Checkpoint has no `resumed_from` field after resuming

**Likely causes:**
- State file expired (>24 hours, pruned by cleanup.py)
- Previous session crashed before writing state file

**Next steps:**
- This is informational — the chain link is skipped. No data loss. See contract Known Limitations §3.
```

**Step 2: Verify skill structure**

Check:
- Frontmatter has `name` (kebab-case) and `description` (what + when + triggers)
- References `handoff-contract.md` via relative link
- Skill is under 150 lines (expanded from 120 to accommodate troubleshooting + project detection)
- Procedure matches design doc (8 steps) with chain-walk guardrail at step 5
- All 5 required sections present in table
- Chain protocol steps match contract (read state → write → cleanup)
- Troubleshooting section covers file-not-created and missing-resumed_from
- Project detection and writeability check in step 1

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

Six changes: (a) add contract reference, (b) add `type: handoff` to procedure step 7, (c) replace inline chain protocol in steps 7-9 with contract references, (d) update Definition of Done to include `type` and `session_id`, (e) update Verification checklist to include `type`, (f) fix `rm` → `trash` in Troubleshooting section.

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

**Step 3: Replace inline chain protocol with contract references**

The design doc requires removing inline chain protocol from creating-handoffs (now defined in the contract). The current SKILL.md implements chain protocol inline at procedure steps 7 and 9. Replace the inline mechanics with contract references:

In procedure step 7 (currently "Check for state file"), replace the inline implementation:
```
7. **Check for state file** at `~/.claude/.session-state/handoff-<session_id>`:
   - If found, read the archive path and use it as `resumed_from` in frontmatter
```

With:
```
7. **Check state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
   - Read `~/.claude/.session-state/handoff-<session_id>`
   - If exists, set `resumed_from` to its content
```

In procedure step 9 (currently "trash the state file"), replace:
```
9. `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` (if it exists)
```

With:
```
9. **Cleanup state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists
```

**Step 4: Update Definition of Done**

In the Definition of Done table (around line 68), add `session_id` and `type` to the "Required fields present" row:

Change:
```
| Required fields present | date, time, created_at, project, title |
```

To:
```
| Required fields present | date, time, created_at, session_id, project, title, type |
```

**Step 5: Update Verification checklist**

In the Verification section (around line 162), add a `type` check:

Add to the checklist:
```
- [ ] `type: handoff` present in generated frontmatter
- [ ] `session_id` present in generated frontmatter
```

**Step 6: Fix `rm` in Troubleshooting**

In the Troubleshooting section (around line 185), change:
```
touch ~/.claude/handoffs/test && rm ~/.claude/handoffs/test
```

To:
```
touch ~/.claude/handoffs/test && trash ~/.claude/handoffs/test
```

**Step 7: Verify changes**

- Contract reference appears near top of skill
- `type: handoff` explicitly mentioned in procedure step 8 (generate markdown)
- Inline chain protocol replaced with contract references at steps 7 and 9
- Definition of Done includes `session_id` and `type`
- Verification checklist includes `type: handoff` and `session_id`
- Troubleshooting uses `trash` not `rm`

**Step 8: Commit**

```bash
git add packages/plugins/handoff/skills/creating-handoffs/SKILL.md
git commit -m "feat(handoff): add type field, contract reference, remove inline chain protocol"
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

**Step 4: Update Verification checklist**

In the Verification section (around line 157), add a type display check:

Add to the checklist:
```
- [ ] Type displayed on resume ("Resuming from **checkpoint**:" or "Resuming from **handoff**:")
```

Also ensure the `/resume <path>` code path (not just the "most recent" path) also reads and displays the type from frontmatter. Both branches should display the type label.

**Step 5: Verify changes**

- Contract reference present
- Resume displays type label (both "most recent" and "path provided" branches)
- List-handoffs shows type column with backwards compatibility (missing type → `handoff`)
- Verification checklist includes type display check

**Step 6: Commit**

```bash
git add packages/plugins/handoff/skills/resuming-handoffs/SKILL.md
git commit -m "feat(handoff): add type display to resume and list-handoffs"
```

---

### Task 6: Add checkpoint format to format-reference

**Files:**
- Modify: `packages/plugins/handoff/references/format-reference.md`

**Step 1: Add `type` field to canonical frontmatter schema**

In the frontmatter schema block at the top of format-reference.md (around lines 9-22), add the `type` field:

```yaml
type: <handoff|checkpoint>          # Required: distinguishes file type
```

Add it after the `title:` line. Also add backwards-compatibility note after the schema block:
```markdown
**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints. Files without a `type` field are treated as `handoff` for backwards compatibility.
```

**Step 2: Update example frontmatter blocks**

There are two example frontmatter blocks in format-reference.md (around lines 71-86 and 497-512). Add `type: handoff` to both example blocks.

**Step 3: Add precedence text**

After the frontmatter schema section, add:
```markdown
**Precedence:** If this file conflicts with [handoff-contract.md](handoff-contract.md), the contract wins. This file is canonical for section content guidance, depth targets, and quality calibration.
```

**Step 4: Add checkpoint format section**

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

**Step 5: Verify**

- `type` field added to canonical frontmatter schema block
- Both example frontmatter blocks include `type: handoff`
- Precedence text references handoff-contract.md
- Checkpoint format section added after existing content
- Table matches design doc content model
- Quality thresholds match design doc

**Step 6: Commit**

```bash
git add packages/plugins/handoff/references/format-reference.md
git commit -m "docs(handoff): add type field to schema, checkpoint format section, precedence text"
```

---

### Task 7: Fix cleanup.py (unlink → trash)

**Files:**
- Modify: `packages/plugins/handoff/scripts/cleanup.py`

**Step 1: Replace `unlink()` with `trash` subprocess call (with error handling)**

In `prune_old_handoffs` (line 58), change:
```python
                handoff.unlink(missing_ok=True)
```
To:
```python
                try:
                    subprocess.run(["trash", str(handoff)], capture_output=True, timeout=5, check=True)
                except FileNotFoundError:
                    pass  # trash binary not installed — skip deletion, don't fall back to unlink
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass  # trash failed or timed out — skip, don't block session start
```

In `prune_old_state_files` (line 78), change:
```python
                state_file.unlink(missing_ok=True)
```
To:
```python
                try:
                    subprocess.run(["trash", str(state_file)], capture_output=True, timeout=5, check=True)
                except FileNotFoundError:
                    pass  # trash binary not installed — skip deletion
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass  # trash failed or timed out — skip
```

**Note:** `check=True` raises `CalledProcessError` on non-zero exit, preventing silent failure. `FileNotFoundError` catches missing `trash` binary. Both exception paths skip deletion rather than falling back to `unlink()` — falling back would defeat the purpose of using `trash`. The script already imports `subprocess` (line 18).

**Step 2: Verify `trash` is available**

Run: `which trash`

Expected: `/opt/homebrew/bin/trash` or similar path (macOS `trash` CLI). If absent, cleanup will silently skip deletions — this is acceptable (files expire naturally).

**Step 3: Test cleanup script runs without error**

Run: `python3 packages/plugins/handoff/scripts/cleanup.py`

Expected: Exit code 0, no output (silent cleanup). Note: this confirms the script runs without crashing, but does not exercise the `trash` path unless expired handoffs exist.

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
- `checkpointing/SKILL.md`: ≤150 lines
- `handoff-contract.md`: ≤100 lines
- Total checkpoint context: ≤230 lines

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

Then in a new session, run through the full design verification checklist:

**Basic checkpoint creation:**
1. Run `/checkpoint` — should produce a file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-*.md`
2. Verify generated file frontmatter contains: `type: checkpoint`, `session_id`, `date`, `time`, `created_at`, `project`, `title` (with "Checkpoint:" prefix)
3. Verify body has all 5 required sections (Current Task, In Progress, Active Files, Next Action, Verification Snapshot)
4. Verify body is 22-55 lines (target range)
5. Run `/checkpoint my-title` — verify title argument is used

**Type display and listing:**
6. Run `/list-handoffs` — should show type column with `checkpoint` for new files and `handoff` for legacy files
7. Run `/resume` — should load the checkpoint with "Resuming from **checkpoint**:" label

**Chain protocol:**
8. After `/resume`, run `/checkpoint` again — verify `resumed_from` points to the archived checkpoint path
9. Run `/handoff` — should include `type: handoff` in frontmatter and `resumed_from` pointing to the archived checkpoint

**Multi-hop chain (design doc verification):**
10. Create a chain: `/checkpoint` → `/resume` → `/checkpoint` → `/resume` → `/checkpoint` — verify each has `resumed_from` linking to the previous archived file
11. Verify the N≥3 guardrail triggers on the 3rd consecutive checkpoint (chain-walk should detect 2 prior checkpoints via `resumed_from`)

**Contract references:**
12. Verify all three skills reference handoff-contract.md: `grep -l "handoff-contract.md" packages/plugins/handoff/skills/*/SKILL.md`

---

## Summary

| Task | What | Files | Est. |
|------|------|-------|------|
| 1 | Shared contract | Create `references/handoff-contract.md` | ~90 lines |
| 2 | Checkpoint skill | Create `skills/checkpointing/SKILL.md` | ~140 lines |
| 3 | Command wrapper | Create `commands/checkpoint.md` | ~7 lines |
| 4 | Update creating-handoffs | Type + contract ref + remove inline protocol + DoD + rm fix | ~20 line changes |
| 5 | Update resuming-handoffs | Type display + contract ref + verification update | ~12 line changes |
| 6 | Update format-reference | Schema + examples + precedence + checkpoint section | ~45 lines |
| 7 | Fix cleanup.py | `unlink` → `trash` with error handling | ~12 line changes |
| 8 | Version bump | `plugin.json` | 1 line change |
| 9 | Integration verification | Full design checklist smoke test (12 checks) | No changes |
