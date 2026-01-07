---
name: git-hygiene
description: Smart repository maintenance with analysis and guided cleanup
---

# Git Hygiene

Repository maintenance: analyze stale branches, old stashes, untracked files. Safe by default.

## Triggers

- `/git-hygiene`, `git hygiene`, `clean up git`
- `stale branches`, `branch cleanup`
- `git maintenance`, `repo health`

## Execution Protocol

### Phase 1: Preflight

Run safety check:
```bash
python3 scripts/preflight.py --json
```

| Exit | Meaning | Action |
|------|---------|--------|
| 0 | Safe | Continue |
| 2 | Blocked | Show resolution, STOP |

If `warnings` in JSON, note them but continue.

### Phase 2: Analysis

```bash
python3 scripts/analyze.py --json [--days N] [--merged-days N]
```

Parse JSON output categories:
- `branches.gone` - remote deleted, safe to delete
- `branches.merged_stale` - merged, safe to delete
- `branches.unmerged_stale` - WARN, needs review
- `stashes` where `stale: true` - suggest deletion

### Phase 3: Review

Present findings:

```
## Branch Analysis
| Branch | Status | Age | Risk |
|--------|--------|-----|------|
| feature/old | [gone] | - | Low |
| fix/typo | merged | 14d | Low |
| experiment/x | unmerged | 45d | Medium |

## Stash Analysis
| Index | Age | Message | Risk |
|-------|-----|---------|------|
| 0 | 67d | WIP: old | Low |
```

Use AskUserQuestion:
- "Delete [gone] branches?"
- "Delete merged stale branches?"
- "Review unmerged branches individually?"
- "Drop old stashes?"

### Phase 4: Execute

Confirm selections, then run:
```bash
python3 scripts/cleanup.py --json --branches "b1,b2" --stashes "0,1"
```

Report each operation with undo command.

### Phase 5: Report

```
## Summary
| Metric | Before | After |
|--------|--------|-------|
| Branches | 12 | 9 |
| Stashes | 5 | 3 |

## Undo Commands
git branch feature/old abc1234
git branch fix/typo def5678
```

## Decision Tree

```
Branch found
├── [gone]? → Delete (low risk)
├── Merged + stale? → Delete (low risk)
├── Unmerged + stale? → WARN, require --force
├── In worktree? → BLOCK
└── Active? → Skip
```

## Commands

| Command | Action |
|---------|--------|
| `/git-hygiene` | Full analysis (dry-run) |
| `/git-hygiene --execute` | With confirmation |
| `/git-hygiene --status` | Quick summary |
| `/git-hygiene branches` | Branch analysis only |
| `/git-hygiene --days N` | Set staleness threshold |
| `/git-hygiene --force` | Allow unmerged deletion |

## Scripts

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `preflight.py` | Safety check | 0=safe, 1=error, 2=blocked |
| `analyze.py` | Scan repo | 0=success, 1=error |
| `cleanup.py` | Execute ops | 0=success, 2=partial, 10=blocked |

## Blocking Behavior

| Context | During Merge | During Rebase |
|---------|--------------|---------------|
| File edits (hook) | ALLOW | BLOCK |
| Git hygiene | BLOCK | BLOCK |

Hygiene blocks during merge to protect merge state.
