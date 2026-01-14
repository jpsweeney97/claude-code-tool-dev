# GitFlow Branching

This project enforces GitFlow branching via a `PreToolUse` hook that blocks edits on protected branches.

## Protected Branches

| Branch | Purpose | Edits Allowed |
|--------|---------|---------------|
| `main` / `master` | Production | No — create hotfix branch |
| `develop` | Integration | No — create feature branch |

## Working Branches

Create branches from the appropriate base:

| Branch Pattern | Base | Purpose |
|----------------|------|---------|
| `feature/*` | develop | New functionality |
| `feat/*` | develop | New functionality (alias) |
| `fix/*` | develop | Bug fixes |
| `hotfix/*` | main | Emergency production fixes |
| `release/*` | develop | Release preparation |

Additional recognized patterns: `docs/*`, `style/*`, `refactor/*`, `perf/*`, `test/*`, `build/*`, `ci/*`, `chore/*`, `spike/*`, `experiment/*`, `poc/*`

## Workflow

**New feature:**
```bash
git checkout develop
git checkout -b feature/<name>
# ... work ...
# PR to develop
```

**Production hotfix:**
```bash
git checkout main
git checkout -b hotfix/<description>
# ... fix ...
# PR to main AND develop
```

**Release:**
```bash
git checkout develop
git checkout -b release/<version>
# ... stabilize ...
# PR to main AND develop
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
| `PROTECTED_BRANCHES` | `main,master,develop` | Comma-separated protected branches |
| `GITFLOW_STRICT` | (unset) | Set to `1` to block non-standard branch names |
| `GITFLOW_BYPASS` | (unset) | Set to `1` to bypass all checks (emergency) |
| `GITFLOW_ALLOW_FILES` | (unset) | Glob patterns for files allowed on protected branches |

## When Blocked

If blocked on a protected branch:

1. **Don't bypass** — create the right branch
2. Check which branch you're on: `git branch --show-current`
3. Create appropriate working branch (see patterns above)
4. Continue work on the new branch

## Emergency Bypass

For genuine emergencies only:

```bash
GITFLOW_BYPASS=1 claude
```

This disables all protection for the session. Document why in commit message.
