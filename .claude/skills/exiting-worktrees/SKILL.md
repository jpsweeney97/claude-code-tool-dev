---
name: exiting-worktrees
description: "Safe worktree exit with pre-flight checks and cleanup. Use proactively whenever a worktree's work is complete — after merging a PR, landing changes on main, or when the user says 'clean up the worktree', 'exit worktree', 'done with this worktree', 'land changes and clean up', or similar. Also trigger when you detect a PR merge or branch merge that implies the worktree is no longer needed. Covers the full exit sequence: verify changes landed, sync local main, confirm with user, call ExitWorktree. Never use manual git worktree remove — it breaks in predictable, hard-to-recover-from ways."
---

# Exiting Worktrees

Safe worktree exit with verification. Prevents data loss from manual cleanup.

## The ExitWorktree Tool

`ExitWorktree` is a Claude Code built-in tool (deferred — fetch its schema via `ToolSearch` before first use). It safely removes worktrees by handling CWD restoration, directory cleanup, and git metadata in a single atomic operation.

**Parameters:**
- `action` (required): `"remove"` (delete worktree + branch) or `"keep"` (leave both intact)
- `discard_changes` (optional, default false): When `true` with `action: "remove"`, forces removal even with uncommitted files or unmerged commits. The tool refuses without this flag if the worktree has unsaved state.

**Key behavior:** On completion, `ExitWorktree` returns the session to the original working directory (the directory before `EnterWorktree` was called). This means after exiting, you're back in the main repo — not stranded in a deleted path.

**Scope:** Always try `ExitWorktree` first, regardless of how the worktree was created. It may work on worktrees from previous sessions or those created via `claude --worktree`. If it reports "no worktree session is active" (a true no-op), fall back to manual cleanup from the **main repo directory** (not from inside the worktree):

```bash
# 1. Run from main repo to avoid CWD breakage
git -C <main-repo-path> worktree remove <worktree-path>
# 2. Delete the branch
git -C <main-repo-path> branch -d <branch-name>
```

The `-C` flag runs git from the main repo without changing your shell CWD, avoiding the "Path does not exist" failure. This is the ONLY acceptable fallback — never `cd` into the worktree and then try to remove it.

**Why not `git worktree remove` from inside the worktree:** Running it from inside the worktree breaks the shell CWD — every subsequent Bash command fails with "Path does not exist." `ExitWorktree` avoids this entirely by restoring CWD before removing the directory. The `-C` fallback above also avoids it by never entering the worktree.

**Branch cleanup after `ExitWorktree`:** `ExitWorktree` may not always delete the branch — particularly when using `discard_changes: true`. After exit, verify the branch was removed: `git branch --list '<branch-pattern>'`. If it survives, delete it manually with `git branch -d <branch-name>`.

## Why This Skill Exists

`ExitWorktree` handles the mechanical removal, but it doesn't know whether your work is safe to delete. This skill ensures you've verified everything landed before calling it — uncommitted changes checked, PR confirmed merged, local main synced.

## Pre-Exit Checklist

Run these checks in order. Stop and resolve any that fail.

### 1. Confirm you're in a worktree

```bash
git worktree list
```

If only one entry (the main repo), you're not in a worktree — nothing to exit.

### 2. Check for uncommitted changes

```bash
git status --short
```

If uncommitted changes exist, ask the user:
> "There are uncommitted changes in the worktree. Commit them before exiting, or discard?"

Do NOT proceed until the user decides. Commit if requested, or note they'll be discarded.

### 3. Check for unpushed commits

```bash
git log @{upstream}.. --oneline 2>/dev/null
```

If unpushed commits exist:
- **If a PR was squash-merged:** Unpushed commits are expected — the squash commit on main contains the work. Confirm with the user: "The PR was squash-merged, so these local commits are already represented on main. OK to proceed?"
- **If no PR:** Ask whether to push first.

### 4. Verify the branch's work is merged

This check depends on how the work was integrated:

**If a PR exists:**
```bash
gh pr list --head <branch-name> --state merged --json number,title --jq '.[0]'
```
A merged PR means the work is on main (via squash or merge commit). The branch itself won't appear in `git branch --merged main` after a squash merge — that's expected and not a problem.

**If merged locally (no PR):**
```bash
git log main --oneline -5
```
Verify the merge commit or the branch's commits appear on main.

**If work needs to be merged now (no PR, not yet on main):**

You cannot `git checkout main` from inside a worktree — main is already checked out in the main worktree. Git prevents two worktrees from having the same branch checked out. Use `git -C` to merge from the main repo:

```bash
# Merge the worktree branch into main from the main repo
git -C <main-repo-path> merge <branch-name>
# Verify
git -C <main-repo-path> log --oneline -3
```

After this merge succeeds, `ExitWorktree(action: "remove", discard_changes: true)` is safe — the "discarded" commit is already on main. The tool reports discarding because the worktree branch's commit is no longer exclusive to it, not because work is lost.

If the merge fails (e.g., conflicts), resolve from the main repo (`git -C <main-repo-path> merge --abort` to cancel, or resolve conflicts there). Do NOT attempt to resolve merge conflicts from inside the worktree — you cannot checkout main there.

**If neither merged nor mergeable:** Warn the user that exiting will lose work unless they choose to keep the worktree.

### 5. Ensure local main has the changes

```bash
# Check if local main matches origin/main
git fetch origin
git log main..origin/main --oneline
git log origin/main..main --oneline
```

Three cases:
- **Local main behind origin:** Pull needed. Run from the main repo (not the worktree): `git -C <main-repo-path> pull origin main`
- **Local main ahead of origin:** Local commits exist that aren't pushed. This is fine — just note it.
- **Diverged:** Local main has commits not on origin AND origin has commits not on local. Use `git -C <main-repo-path> pull --rebase origin main` to replay local commits on top of origin.

After syncing, verify:
```bash
git -C <main-repo-path> log --oneline -3
```

## Exit Procedure

After all checks pass:

**1. Confirm with the user:**

> "All changes are on local main. Ready to remove worktree `<name>` and delete the branch. Proceed?"

Wait for explicit confirmation.

**2. Call ExitWorktree:**

```
ExitWorktree(action: "remove")
```

If it reports uncommitted files or unmerged commits, go back to the checklist — do NOT retry with `discard_changes: true` unless:
- The user explicitly says to discard, OR
- The worktree directory is already gone (broken state from a prior cleanup attempt)

**3. Verify and clean up:**

```bash
git worktree list
git log --oneline -3
git branch --list '<branch-pattern>'
```

Confirm the worktree is gone and main shows the expected history. If the branch survived (common with `discard_changes: true`), delete it: `git branch -d <branch-name>`.

## Prohibited Actions

| Action | Why | Use Instead |
|--------|-----|-------------|
| `git worktree remove` | Breaks when run from inside worktree; CWD becomes invalid | `ExitWorktree` tool |
| `git branch -D` (force delete) without merge proof | Silently deletes unmerged work | `git branch -d` first; `-D` only after confirmed squash merge (see below) |
| `rm -rf` on worktree directory | Leaves orphaned git metadata | `ExitWorktree` tool |
| `discard_changes: true` as first attempt | Masks unresolved issues | Run checklist first, resolve issues |
| Proceeding without user confirmation | Risk of data loss | Always confirm before removing |

### Branch Deletion After Squash Merge

`ExitWorktree` handles branch deletion automatically. But if branch cleanup falls through (e.g., `ExitWorktree` was a no-op for a manually-created worktree, or `action: "keep"` was used), you may need to delete the branch manually.

After a squash merge, `git branch -d` fails because git doesn't recognize the squash commit as merging the branch (the SHAs differ). This is the one case where `-D` is acceptable:

1. First, confirm the PR was merged: `gh pr list --head <branch> --state merged`
2. Try safe delete: `git branch -d <branch>`
3. If `-d` fails with "not fully merged" AND step 1 confirmed the PR is merged: `git branch -D <branch>` is safe — the PR merge serves as proof the work landed.

Do NOT use `-D` without first confirming the merge via `gh pr list`. The PR confirmation is what makes `-D` safe, not the failure of `-d`.

## Edge Cases

| Situation | Action |
|-----------|--------|
| PR squash-merged, branch shows "unmerged" | Expected. Verify via `gh pr list --state merged`, then proceed. |
| Local main diverged from origin | `git pull --rebase origin main` in main repo before exiting. |
| Worktree directory already gone (broken state) | `ExitWorktree(action: "remove", discard_changes: true)` — handles orphaned metadata. |
| Multiple worktrees exist | Only exit the one being discussed. Don't touch others. |
| User wants to keep the worktree | `ExitWorktree(action: "keep")` — directory and branch remain. |
| Remote branch already deleted by PR merge | Normal — GitHub deletes the remote branch on merge. Local branch cleanup still needed. |
| Worktree created in a previous session or manually | Try `ExitWorktree` first — it may still work. If it reports "no worktree session is active," use `git -C <main-repo> worktree remove` fallback (see tool section). |
| Work needs merging but main is checked out elsewhere | Cannot `git checkout main` from inside the worktree. Use `git -C <main-repo-path> merge <branch>` to merge from the main repo, then `ExitWorktree(action: "remove", discard_changes: true)`. |
| Branch survives after `ExitWorktree` | Common with `discard_changes: true`. Verify with `git branch --list`, then `git branch -d <branch>`. |

## Integration

**Complements:**
- `using-git-worktrees` — creates worktrees; this skill exits them
- `finishing-a-development-branch` — decides merge/PR/keep/discard; this skill supersedes its Step 5 (worktree cleanup) which uses raw `git worktree remove`

**Typical sequence:**
1. `finishing-a-development-branch` → user picks "Create PR" (Option 2)
2. PR review cycle happens
3. PR merged on GitHub
4. **This skill activates** → sync main, confirm, ExitWorktree, verify
