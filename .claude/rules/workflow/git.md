# Branch Protection

This project enforces branch protection via a `PreToolUse` hook that blocks edits on protected branches. Work happens on feature branches; merge to `main` when done.

## Protected Branches

| Branch | Purpose | Edits Allowed |
|--------|---------|---------------|
| `main` / `master` | Production | No — create a working branch |

## Working Branches

All working branches are based on `main`:

| Branch Pattern | Purpose |
|----------------|---------|
| `feature/*` | New functionality |
| `feat/*` | New functionality (alias) |
| `fix/*` | Bug fixes |
| `hotfix/*` | Emergency production fixes |
| `chore/*` | Maintenance, cleanup |

Additional recognized patterns: `docs/*`, `style/*`, `refactor/*`, `perf/*`, `test/*`, `build/*`, `ci/*`, `release/*`, `spike/*`, `experiment/*`, `poc/*`

## Workflow

```bash
git checkout main
git checkout -b feature/<name>
# ... work ...
# merge to main when done
```

## Hook Behavior

The hook checks git state before `Edit` or `Write` operations:

| State | Behavior |
|-------|----------|
| Protected branch | Block with guidance |
| Valid working branch | Allow |
| Non-standard branch | Warn (suggest rename) |
| Rebase in progress | Block (edits dangerous) |
| Bisect in progress | Block (edits lost) |
| Merge conflict | Warn (edits expected) |
| Cherry-pick conflict | Warn (edits expected) |
| Detached HEAD | Warn (commits may be orphaned) |

## Configuration

Set via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROTECTED_BRANCHES` | `main,master` | Comma-separated protected branches |
| `GITFLOW_STRICT` | (unset) | Set to `1` to block non-standard branch names |
| `GITFLOW_BYPASS` | (unset) | Set to `1` to bypass all checks (emergency) |
| `GITFLOW_ALLOW_FILES` | (unset) | Glob patterns for files allowed on protected branches |

To add `develop` as a protected branch (for repos using GitFlow):
```bash
PROTECTED_BRANCHES=main,master,develop claude
```

## When Blocked

If blocked on a protected branch:

1. **Don't bypass** — create the right branch
2. Check which branch you're on: `git branch --show-current`
3. Create appropriate working branch (see patterns above)
4. Continue work on the new branch

## Parallel Development with Worktrees

For working on multiple features simultaneously without stashing:

```bash
# Create worktree for a feature (from any branch)
git worktree add ../project-feature-x feature/x

# Or create worktree with new branch
git worktree add -b feature/new-thing ../project-new-thing main
```

Each worktree has its own working directory and checked-out branch. The hook enforces branch rules in all worktrees.

**When worktrees help:**
- Running tests on `main` while developing on a feature branch
- Reviewing a PR without disrupting current work
- Comparing behavior between branches side-by-side

**Managing worktrees:**
```bash
git worktree list              # Show all worktrees
git worktree remove <path>     # Remove a worktree (branch remains)
git worktree prune             # Clean up stale worktree references
```

**Note:** Each worktree uses disk space for a full copy of tracked files. The `.git` data is shared.

## Emergency Bypass

For genuine emergencies only:

```bash
GITFLOW_BYPASS=1 claude
```

This disables all protection for the session. Document why in commit message.
