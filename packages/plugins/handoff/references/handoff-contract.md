# Handoff Contract

Shared contract for all handoff plugin skills. Loaded by save, quicksave, and load.

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

**Resume (load) — writes state:**
1. Archive the handoff to `<project_root>/.claude/handoffs/.archive/<filename>`
2. Write archive path to `~/.claude/.session-state/handoff-<session_id>`

**Save/Quicksave (save, quicksave) — reads and cleans state:**
1. **Read:** Check `~/.claude/.session-state/handoff-<session_id>` — if exists, include path as `resumed_from` in frontmatter
2. **Write:** Write the new handoff/checkpoint file
3. **Cleanup:** Use `trash` to remove state file at `~/.claude/.session-state/handoff-<session_id>` (if exists). If `trash` fails, warn the user that the state file persists but do not block handoff/checkpoint creation — the 24-hour TTL will clean it up.

**Invariant:** State files are created by load; the next save/quicksave reads them to populate `resumed_from`, then attempts cleanup via `trash`. If cleanup fails, the file may persist until TTL pruning (24 hours). A state file that persists beyond 24 hours is stale.

## Storage

| Location | Format | Retention |
|----------|--------|-----------|
| `<project_root>/.claude/handoffs/` | `YYYY-MM-DD_HH-MM_<slug>.md` | 30 days |
| `<project_root>/.claude/handoffs/.archive/` | Same | 90 days |
| `~/.claude/.session-state/handoff-<UUID>` | Plain text (path) | 24 hours |

**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.

## Project Root

The project root determines where handoff files are stored. Resolved by:
1. `git rev-parse --show-toplevel` (if in a git repo)
2. Current working directory (fallback)

The full project root path is used for storage resolution — handoff files live at `<project_root>/.claude/handoffs/`.

## Git Detection

If `.git/` exists in current or parent directories, include `branch` and `commit` in frontmatter. Otherwise omit them entirely (no placeholders).

## Write Permission

If `<project_root>/.claude/handoffs/` is not writable (or cannot be created), **STOP** and ask: "Can't write to <project_root>/.claude/handoffs/. Where should I save this?"

## Precedence

This contract is canonical for cross-skill invariants: frontmatter field definitions, type semantics, chain protocol, and storage/retention. `format-reference.md` is canonical for section content guidance, depth targets, quality calibration, and examples. If `format-reference.md` conflicts with this contract, **this contract wins**.

**Schema drift note:** Skills may contain partial field lists in Definition of Done tables and Verification checklists. These are non-canonical summaries — this contract governs. If a skill's field list diverges from this schema, update the skill to match the contract.

## Known Limitations

Three inherited issues from the current chain protocol design. These are pre-existing — not introduced by the checkpoint tier.

1. **Resume-crash recovery:** If a session resumes a handoff but crashes before creating a new one, the state file persists but no successor handoff references the archived file. The chain has a gap. No automated recovery — the archived file is intact and can be manually re-loaded. The orphaned state file is pruned by the 24-hour TTL.

2. **Archive-failure chain poisoning:** If archive creation fails but the state file is written, the `resumed_from` path in the next handoff/checkpoint points to a non-existent file. Skills should not fail on a missing `resumed_from` target — treat as informational metadata.

3. **State-file TTL race:** State files are pruned after 24 hours by cleanup.py. If a session spans >24 hours (rare), the state file may be pruned before the next save/quicksave reads it. Result: missing `resumed_from` in the next file. Not data loss — the chain link is skipped.
