---
name: merge-branch
description: Commit, merge the current feature branch into its base branch, and delete the feature branch — the local fast-path for landing completed work without a PR. Use when the user says "merge to main", "merge and clean up", "land this branch", "done with this branch", "merge it", "commit and merge", "yes merge it", or any variation of finishing work on a feature branch and integrating it locally. Also trigger when the user confirms a merge after being asked. Do not use when the user wants to create a PR or push to remote — those are different workflows.
---

# Merge Branch

Commit all pending changes, merge the current branch into its base, and delete the feature branch. This is the local fast-path for landing completed work — no PR, no push.

## When to Use

- Work is complete on a feature branch and should be merged locally
- No PR review is needed (solo work, trivial changes, or already reviewed)

## When NOT to Use

- User wants a PR — use the commit-push-pr workflow instead
- User wants to push to remote without merging — just push
- Already on the base branch — nothing to merge

## Procedure

### 1. Assess State

Before anything else, determine the current situation:

```bash
git branch --show-current
git status
git diff --stat
git log --oneline -5
```

**Stop conditions:**
- Already on a protected branch (main/master) → "You're on `main` — no feature branch to merge."
- Rebase, bisect, or merge in progress → "Resolve the in-progress operation first."

### 2. Commit (if needed)

If there are staged or unstaged changes:

1. Stage the relevant files (prefer specific files over `git add -A`)
2. Draft a commit message from the diff — don't ask the user to write one from scratch
3. Follow the repository's commit conventions: message style, HEREDOC format, `Co-Authored-By` trailer
4. Commit

If there are no uncommitted changes, skip to Step 3.

If the last commit is already the user's work and nothing else is pending, also skip to Step 3.

### 3. Merge

```bash
git checkout main && git merge <branch-name>
```

Identify the base branch — usually `main`, but check if the branch was created from a different base. Fast-forward merges are ideal and typical for single-contributor feature branches.

**If there are merge conflicts:** stop and tell the user. Do not attempt automatic conflict resolution.

### 4. Clean Up

```bash
git branch -d <branch-name>
```

Use `-d` (safe delete), not `-D`. If git reports the branch isn't fully merged, something went wrong in Step 3 — investigate rather than force-deleting.

### 5. Confirm

Show the result briefly:

```bash
git log --oneline -3
```

One line of confirmation: "Merged `<branch>` to `main` and deleted the branch."
