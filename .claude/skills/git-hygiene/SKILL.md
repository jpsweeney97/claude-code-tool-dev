---
name: git-hygiene
description: Use when git status shows clutter (untracked files, mixed changes, stale branches), when you want to organize uncommitted work into coherent commits, or when user says "clean up git", "git hygiene", or "tidy this repo".
---

## Overview

Git repos accumulate mess: untracked files that should be ignored or deleted, changes spanning multiple concerns staged together, stale local branches, and orphaned remote-tracking branches. Manual cleanup is tedious and error-prone.

This skill analyzes the repo state, proposes a cleanup plan (grouping changes into coherent commits, identifying files to ignore or delete, listing branches to prune), and executes the approved plan on an isolated cleanup branch.

**Key behaviors:**

- Preview-first — always shows the full plan before executing
- Semi-autonomous — safe operations proceed automatically; destructive operations (file deletion) require explicit approval
- Isolated — all work happens on a timestamped `cleanup/*` branch
- Reversible — detailed output includes undo commands for every action

**Non-goals:**

- Resolving merge conflicts or complex git states (skill aborts cleanly if detected)
- Modifying submodules (reports status only)
- Pushing to remotes or creating PRs

## When to Use

- Git status shows untracked files that have accumulated
- Working tree has mixed changes spanning multiple concerns
- Local branches are stale (merged or abandoned)
- Remote-tracking branches reference deleted remotes
- Before starting fresh work on a cluttered repo
- User says: "clean up git", "git hygiene", "tidy the repo", "organize my commits"

**Do NOT use when:**

- Rebase, merge, cherry-pick, or bisect is in progress (skill will abort)
- You need to resolve conflicts (resolve first, then run hygiene)
- The repo is a shallow clone (limited git history may cause issues)

## Process

### Phase 1: Preflight

1. **Check repo state** — Verify no complex operations in progress
   - If rebase, merge, cherry-pick, or bisect detected → STOP with message: "Cannot run hygiene during [operation]. Complete or abort it first."
   - If shallow clone detected → WARN and ask whether to proceed with limited analysis

2. **Check scope** — Count untracked files, changed files, local branches
   - If totals exceed thresholds (>100 files or >50 branches) → Ask before proceeding: "Large repo detected. Continue with full analysis?"

3. **Create cleanup branch** — `cleanup/YYYY-MM-DD-HHMMSS` from current HEAD
   - All subsequent work happens on this branch

### Phase 2: Analysis

4. **Catalog untracked files** — Classify each file:
   - **Auto-ignore**: Matches known artifact patterns (build outputs, editor files, OS files)
   - **Auto-track**: Matches project source patterns
   - **Ask**: Unknown — will prompt user
   - **Protected**: Matches sensitive patterns (`.env*`, `*.key`, `*.pem`, `credentials.*`) — never auto-delete

5. **Analyze changes** — Read staged and unstaged changes, group by semantic concern
   - Use file paths, change content, and commit history to infer groupings
   - Each group becomes a proposed commit with Conventional Commits message

6. **Identify stale branches**:
   - Local branches fully merged into default branch
   - Remote-tracking branches with no upstream (`gone`)

7. **Check submodules** — Report status only (dirty/clean), do not modify

8. **Load project config** — If `.git-hygiene.json` exists, apply learned patterns

### Phase 3: Preview

9. **Present full plan** — Show everything that will happen:
   ```
   .gitignore additions:
     + *.pyc
     + __pycache__/
     + .DS_Store

   Files to delete (requires approval):
     - tmp/debug.log
     - scratch.txt

   Unknown files (decision needed):
     ? notes.md — track, ignore, or delete?

   Proposed commits:
     1. chore: update .gitignore with Python artifacts
     2. feat(auth): add login validation
     3. fix(api): handle timeout errors
     4. chore: remove unused imports

   Branches to delete:
     - feature/old-experiment (merged)
     - fix/typo (merged)

   Remote tracking to prune:
     - origin/feature/deleted-upstream

   Submodules:
     - vendor/lib: 3 uncommitted changes (not modified by this skill)
   ```

10. **Collect decisions** — For unknown files and proposed groupings:
    - User can approve as-is, adjust groupings (split/merge/reassign), or cancel
    - Protected file deletion requires explicit per-file confirmation

### Phase 4: Execute

11. **Update .gitignore** — Add approved patterns, commit: `chore: update .gitignore with [patterns]`

12. **Delete approved files** — Only files explicitly approved for deletion

13. **Create commits** — For each approved group:
    - Stage the files
    - Commit with the approved message
    - Use Conventional Commits format

14. **Delete branches** — Local branches approved for deletion

15. **Prune remote tracking** — Run `git remote prune origin` for approved remotes

16. **Update project config** — Save learned patterns to `.git-hygiene.json`

### Phase 5: Report

17. **Show detailed results**:
    ```
    Cleanup complete on branch: cleanup/2024-01-21-143052

    .gitignore: 3 patterns added
    Files deleted: 2
    Commits created: 4
      abc1234 chore: update .gitignore with Python artifacts
      def5678 feat(auth): add login validation
      ghi9012 fix(api): handle timeout errors
      jkl3456 chore: remove unused imports
    Branches deleted: 2
    Remote tracking pruned: 1

    To undo:
      git checkout <original-branch>
      git branch -D cleanup/2024-01-21-143052

    To merge:
      git checkout <target-branch>
      git merge cleanup/2024-01-21-143052
    ```

**On failure:** If any operation fails, STOP immediately. Report what succeeded, what failed, and why. Do not attempt to continue or rollback — let the user assess.

## Decision Points

**Complex state detected:**

- If rebase/merge/cherry-pick/bisect in progress → Abort cleanly. Do not attempt partial cleanup.
- Rationale: These states require human judgment about intent. Interfering could lose work.

**Large repo:**

- If >100 files or >50 branches → Ask before proceeding
- User may want to narrow scope or proceed with awareness of analysis time

**Grouping disagreement:**

- If user rejects proposed groupings → Present adjustment interface
- User can: split a group, merge groups, reassign files between groups, rename commit messages
- After adjustment, re-present the modified plan for final approval

**Unknown files:**

- If file doesn't match known patterns → Ask per file: track, ignore, or delete?
- Never auto-delete unknowns. Never auto-ignore source-looking files.

**Protected file deletion requested:**

- If user wants to delete a protected-pattern file → Require explicit confirmation separate from batch approval
- Message: "This file matches a protected pattern (`.env*`). Are you SURE you want to delete it? This may contain secrets that cannot be recovered."

**Pressure to skip preview:**

- If user says "just do it" or "skip the preview" → Acknowledge, but still show preview
- Response: "I hear you — here's a quick summary. Please confirm before I execute: [condensed plan]. Proceed?"
- The preview exists to prevent mistakes. Skipping it risks wrong deletions or bad commits.

**Nothing to clean:**

- If analysis finds no untracked files, no mixed changes, no stale branches → Report "Repository is already clean" and exit
- Do not create empty cleanup branch

**Mid-execution failure:**

- If a commit fails (e.g., pre-commit hook) → STOP immediately
- Report: what succeeded (with commit hashes), what failed (with error), what was not attempted
- Do not rollback successful operations. Let user assess and decide.

**Cleanup branch already exists:**

- If `cleanup/YYYY-MM-DD-HHMMSS` already exists (unlikely but possible) → Append random suffix or increment seconds
- Do not overwrite or reuse existing cleanup branches

## Examples

### Scenario: Developer returns to a repo after a week away

The repo has accumulated: 15 untracked files (mix of build artifacts, editor backups, and a new config file), uncommitted changes spanning authentication fixes AND unrelated formatting cleanup, and 3 local branches that were merged via PR.

### BAD: Without the skill

Claude runs `git add .` and creates one commit: "WIP: various fixes and cleanup"

**Why it's bad:**

- Build artifacts (`.pyc`, `node_modules/`) are now tracked
- Auth fixes and formatting changes are in one incoherent commit
- Git history is polluted — can't cherry-pick the auth fix later
- Stale branches remain, cluttering `git branch` output
- The new config file is buried in a "WIP" commit instead of being properly introduced

### GOOD: With the skill

1. **Preflight**: Confirms no complex operations in progress
2. **Creates branch**: `cleanup/2024-01-21-143052`
3. **Analyzes and presents preview**:
   ```
   .gitignore additions:
     + *.pyc
     + __pycache__/
     + .vscode/

   Unknown files (decision needed):
     ? config/new-feature.yaml — track, ignore, or delete?

   Proposed commits:
     1. chore: update .gitignore with Python and editor artifacts
     2. feat(config): add new-feature configuration
     3. fix(auth): validate token expiration before refresh
     4. style: apply consistent formatting to api module

   Branches to delete:
     - feature/user-profiles (merged)
     - fix/login-redirect (merged)
     - experiment/caching (merged)
   ```
4. **User approves** (chooses to track the new config file)
5. **Executes**: Creates 4 atomic commits, deletes 3 branches
6. **Reports**: Full summary with commit hashes and undo commands

**Why it's good:**

- Build artifacts properly ignored, not tracked
- Each commit has a single purpose — auth fix can be cherry-picked independently
- New config file introduced with its own descriptive commit
- Stale branches cleaned up
- All changes on isolated branch — easy to review or discard

---

### Scenario: User says "just clean it up quickly"

### BAD: Without the skill

Claude interprets "quickly" as permission to skip analysis. Runs `git clean -fd` to remove untracked files, deletes what looks like junk. One of the deleted files was `credentials.local.json` containing API keys.

**Why it's bad:**

- Irreversible data loss
- No preview, no confirmation
- "Quickly" was interpreted as "skip safety checks"

### GOOD: With the skill

Claude acknowledges the time pressure but still runs the preview:

"I understand you want this done quickly. Here's what I found — please confirm before I proceed:

```
Files to delete (requires approval):
  - tmp/debug.log
  - test-output.json

PROTECTED (requires explicit confirmation):
  credentials.local.json — matches sensitive pattern
```

Would you like me to proceed? The protected file will NOT be deleted without separate confirmation."

**Why it's good:**

- Protected file pattern caught the credentials file
- User still sees what will happen before it happens
- "Quickly" doesn't bypass safety — it just keeps the preview concise

## Anti-Patterns

**Pattern:** Skipping preview because "it's a small repo"
**Why it fails:** Small repos can still have protected files, mixed concerns, or files the user forgot about. Size doesn't determine risk.
**Fix:** Always show preview. If truly small, the preview is fast and short anyway.

---

**Pattern:** Auto-deleting files that "look like" artifacts
**Why it fails:** Pattern matching isn't perfect. A file named `build.log` might be intentionally tracked documentation. `tmp/` might contain work-in-progress the user needs.
**Fix:** Known artifact patterns go to .gitignore (reversible). Unknown files get asked about. Deletion requires explicit approval.

---

**Pattern:** Grouping all changes into one "cleanup" commit
**Why it fails:** Defeats the purpose of coherent commits. Can't bisect, can't cherry-pick, can't understand history.
**Fix:** Analyze changes semantically. Even if user says "just commit everything," propose groupings first. They can reject the groupings if they truly want one commit.

---

**Pattern:** Treating user impatience as permission to skip steps
**Why it fails:** "Just do it" expressed frustration, not informed consent to skip safety checks. When something goes wrong, "but you said just do it" isn't a defense.
**Fix:** Acknowledge the pressure, keep the preview concise, but still show it. Fast execution comes from efficient analysis, not skipped steps.

---

**Pattern:** Deleting branches without checking worktree status
**Why it fails:** A branch checked out in another worktree can't be deleted — git will error. Worse, on older git versions, force-delete might succeed and corrupt the worktree.
**Fix:** Check worktree status before proposing branch deletions. If worktree check fails, refuse to delete rather than guess.

---

**Pattern:** Committing .gitignore changes mixed with code changes
**Why it fails:** Muddies the history. The .gitignore update is infrastructure; the code changes are feature work. Mixing them makes both harder to review and revert.
**Fix:** .gitignore changes are always their own commit, created first, so subsequent commits benefit from the updated ignore rules.

---

**Pattern:** Running on a repo in complex state "just to see what happens"
**Why it fails:** Interacting with a repo during rebase/merge can create confusing states. Even read-only analysis might give misleading results if the index is in a transitional state.
**Fix:** Detect complex states in preflight and abort cleanly. The user can resume hygiene after resolving the complex state.

---

**Pattern:** Deferring to "the user knows what they staged"
**Why it fails:** Users often stage incrementally without reviewing the whole picture. Mixed concerns get staged together accidentally. The skill exists to catch what users miss.
**Fix:** Always analyze staged changes for semantic coherence. Propose groupings even if user seems confident.

## Red Flags — STOP and Reconsider

If you catch yourself thinking any of these, you're rationalizing around the skill:

- "This is over-clarifying"
- "The user already knows"
- "It's just a tiny/small/simple cleanup"
- "I can reasonably infer what they want"
- "Full ceremony is overkill here"

**All of these mean:** Show the preview anyway. The preview exists to catch mistakes. Size and apparent simplicity don't reduce risk — they just make the preview faster.

## Troubleshooting

**Symptom:** Skill aborts with "complex state detected"
**Cause:** Rebase, merge, cherry-pick, or bisect is in progress
**Next steps:** Complete or abort the in-progress operation first:
- Rebase: `git rebase --continue` or `git rebase --abort`
- Merge: resolve conflicts and `git commit`, or `git merge --abort`
- Cherry-pick: `git cherry-pick --continue` or `git cherry-pick --abort`
- Bisect: `git bisect reset`

Then re-run the skill.

---

**Symptom:** Grouping proposal doesn't make sense (unrelated changes grouped together)
**Cause:** Semantic analysis inferred wrong relationships, possibly due to similar file paths or commit history
**Next steps:** Use the adjustment interface to split the group. The skill will re-present the modified plan. Consider adding notes to `.git-hygiene.json` about project-specific grouping patterns.

---

**Symptom:** A commit fails with pre-commit hook error
**Cause:** The staged changes don't pass the project's pre-commit checks (linting, formatting, tests)
**Next steps:** The skill has stopped and reported which commit failed. Fix the issues that the hook identified, then either:
- Re-run the skill (it will re-analyze)
- Manually complete the remaining commits

---

**Symptom:** Branch deletion fails with "checked out in another worktree"
**Cause:** The branch is currently active in a different worktree
**Next steps:** Either finish work in that worktree and switch branches, or remove that branch from the deletion list. The skill will continue with other operations.

---

**Symptom:** Protected file appears in "files to delete" despite protection
**Cause:** The file matches a deletion pattern more specifically than the protection pattern, or protection patterns aren't loaded
**Next steps:** This shouldn't happen — file a bug. In the meantime, simply don't approve that file for deletion. Protected files always require explicit per-file confirmation anyway.

---

**Symptom:** Skill creates too many small commits
**Cause:** Semantic analysis over-split the changes, possibly treating each file as its own concern
**Next steps:** Use the adjustment interface to merge groups before execution. Consider whether the changes actually are distinct concerns — many small commits might be correct if the work truly spans multiple purposes.

---

**Symptom:** `.git-hygiene.json` isn't being respected
**Cause:** File might be malformed JSON, in wrong location, or skill is running in a subdirectory
**Next steps:** Verify the file is valid JSON (`cat .git-hygiene.json | jq .`). Ensure it's in the repo root. Run skill from repo root.

---

**Symptom:** User wants to undo the cleanup after it completed
**Cause:** Changed their mind, or realized something was wrong after the fact
**Next steps:** The cleanup branch is isolated. To undo everything:
```bash
git checkout <original-branch>
git branch -D cleanup/YYYY-MM-DD-HHMMSS
```
If the branch was already merged, use `git revert` on the merge commit or individual commits (hashes are in the report output).

## Verification

**Quick check:** After skill completes, run `git status` on the cleanup branch.

**Expected result:**
```
On branch cleanup/2024-01-21-143052
nothing to commit, working tree clean
```

**If not clean:**

- Untracked files remain → Skill didn't complete, or files were left intentionally (user chose "leave in working tree" for WIP)
- Uncommitted changes remain → Skill stopped mid-execution; check the report for what failed

**Additional checks:**

| Check | Command | Expected |
|-------|---------|----------|
| Commits created | `git log --oneline <original>..HEAD` | Lists the cleanup commits |
| Branches pruned | `git branch` | Stale branches no longer listed |
| Remote tracking pruned | `git branch -r` | Gone branches no longer listed |
| .gitignore updated | `git diff <original> -- .gitignore` | Shows added patterns |

## Extension Points

**Project configuration (`.git-hygiene.json`):**

```json
{
  "ignorePatterns": ["*.log", "tmp/", ".cache/"],
  "protectedPatterns": [".env*", "*.key", "secrets/"],
  "groupingHints": {
    "src/auth/": "auth",
    "src/api/": "api",
    "tests/": "test"
  },
  "branchProtection": ["main", "develop", "release/*"],
  "defaultCommitPrefix": "chore"
}
```

**Fields:**

- `ignorePatterns`: Always add these to .gitignore (learned from past runs)
- `protectedPatterns`: Never auto-delete; extend the built-in list
- `groupingHints`: Map paths to concern names for better semantic grouping
- `branchProtection`: Never delete these branches (extends git's default branch protection)
- `defaultCommitPrefix`: Conventional Commits type for ambiguous changes

**Integration with other skills:**

- After cleanup completes, user may want to run `/commit` to create a merge commit message
- Before starting new feature work, run `/git-hygiene` to ensure clean slate
- Pairs well with branch management skills that create feature branches

**Customization hooks:**

The skill respects standard git configuration:

- `core.excludesFile`: Global gitignore patterns
- `init.defaultBranch`: Determines which branch is "default" for merge detection
- Pre-commit hooks: Skill stops if commits fail hooks, letting user fix and retry
