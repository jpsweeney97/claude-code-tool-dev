---
date: 2026-04-07
time: "00:47"
created_at: "2026-04-07T04:47:59Z"
session_id: 3b1327d6-f414-416a-8e5a-d62c51672fc1
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-06_23-39_t6-governance-closed-and-pr95-merged.md
project: claude-code-tool-dev
branch: main
commit: e26d070c
title: Git hygiene — preservation-first branch cleanup
type: handoff
files:
  - docs/handoffs/archive/2026-04-05_04-50_t6-review-correction-merged-pr91-and-f6-f7-f11-branch-initialized.md
  - docs/handoffs/archive/2026-04-06_15-07_f6-concession-lifecycle-resolved-and-pr93-merged.md
  - docs/handoffs/archive/2026-04-06_22-51_f7-f11-resolved-and-pr94-opened.md
  - docs/handoffs/archive/2026-04-06_23-39_t6-governance-closed-and-pr95-merged.md
  - .claude/skills/scrutinize/SKILL.md
---

# Handoff: Git hygiene — preservation-first branch cleanup

## Goal

Clean up local branch clutter and sync local `main` with `origin/main`
after the T6 governance arc completed (PRs #93-#95 merged). The repo
had accumulated 4 local branches, a 4-ahead/4-behind `main` divergence,
and multiple stale remote tracking refs.

**Trigger:** Prior session (T6 governance close, PR #95) identified
branch cleanup and local main sync as deferred items. User invoked
`/git-hygiene` to start a dedicated cleanup pass.

**Stakes:** Growing `main` divergence — each session that archived
handoffs on local `main` added commits not on `origin/main`. The
4-ahead/4-behind state would worsen. Additionally, stale branches from
completed PRs cluttered `git branch -a` and could confuse future
sessions.

**Success criteria:**
- Local `main` matches `origin/main` exactly (0 ahead, 0 behind)
- All branches from completed PRs deleted (local and remote)
- Handoff archive files from doomed branches preserved on `origin/main`
- No unique work lost in the process

**Connection to project arc:** T6 governance close (PR #95, previous
session) -> git-hygiene pass (this session) -> T7 executable slice
unblocked (next major design work).

## Session Narrative

### Phase 1: Handoff load and git-hygiene invocation

Session opened with `/load`, archiving the T6 governance handoff. User
then invoked `/git-hygiene` with specific guidance: "starting by
classifying the two local merged branches and the new `ahead 2` state
on `chore/t6-governance-cleanup`."

### Phase 2: Git-hygiene audit

Ran full preflight: clean working tree, 0 untracked files, no complex
git state, 4 local branches, 7 remote branches. Single worktree.

Gathered detailed branch state in parallel: tracking info, merge status,
divergence analysis, commit inspection for each branch. Key findings:

1. **`chore/t6-governance-cleanup`** (current branch): PR #95 merged.
   2 local-only handoff commits (save + archive) not on origin/main.
2. **`fix/f7-f11-provenance-wire-format-blockers`**: Remote gone, PR #94
   merged. 2 local-only handoff commits beyond the PR.
3. **`feature/codex-collaboration-r2-dialogue`**: Remote gone, 39 unique
   commits, tagged `r2-dialogue-branch-tip`. Never PR'd.
4. **`main`**: 4 ahead (3 handoff lifecycle + 1 skill update), 4 behind
   (PR #94/#95 merges).

Discovered that `git branch --merged origin/main` listed NONE of the
local branches as merged — even though PRs #94 and #95 were merged.
This was because each branch had local-only handoff commits beyond the
PR merge point.

Presented audit organized by the git-hygiene skill's lane structure:
`untracked-and-ignore` (empty), `commit-shaping` (empty),
`branch-pruning` (main event), `config-learning` (deferred).

### Phase 3: First recommendation and scrutiny

Presented a structured recommendation (via `/making-recommendations`)
for the cleanup path. Proposed "Rebase + file recovery" as the top
option: sync main via rebase, recover handoff files from branches via
`git checkout <branch> -- <file>`, one preservation commit, delete
branches. Labeled "verifiably best."

User scrutinized the recommendation (copied to clipboard, analyzed
externally). Scrutiny returned **Major revision** with 4 findings:

1. **High — option set dodges the `main` disposition decision.** The
   plan assumed main's 4 local-only commits should stay. That's the
   unresolved question.
2. **High — branch deletion is mechanically incomplete.** File recovery
   doesn't create ancestry. `git branch -d` will refuse. Plan actually
   requires `git branch -D` (force-delete) — not stated.
3. **Medium — scope and stakes inconsistent.** Plan says "low-stakes
   local-only" but step 7 expands into remote pruning (shared-state
   mutation).
4. **Medium — "verifiably best" overstated.** Option space incomplete
   (omits `main == origin/main` end-state).

All 4 findings accepted. The scrutiny exposed a framing error:
optimizing for *how* to sync (rebase vs merge) before deciding *what
main should be after cleanup*.

### Phase 4: Main end-state policy decision

Presented the prerequisite decision: what should `main` look like after
cleanup? Four options:

1. **Exact mirror** — `main == origin/main`, relocate local-only commits
2. **Intentionally ahead** — rebase, keep local commits on top
3. **Selective split** — reset main, relocate skill update to branch
4. **Null** — leave as-is

Key information gap: whether the scrutinize skill update (`3e24c225`)
had already been promoted to `~/.claude/`. Verified via `diff`: the
production file at `~/.claude/skills/scrutinize/SKILL.md` was IDENTICAL
to the commit. This resolved the gap — all 4 local-only commits were
either already-promoted (skill) or operational (handoff lifecycle).

Recommended **Exact mirror**. User accepted, with a critical
constraint: "main == origin/main is only acceptable after the preserved
handoff files have themselves been merged into origin/main."

### Phase 5: Preservation-first plan revision

User's constraint inverted the execution order. Original plan: sync
main first, then recover files. Revised plan: preserve files on
`origin/main` first (via dedicated branch and PR), then reset main.

Also identified that `main` had 2 additional handoff archive files not
on `origin/main` — total of 4 files needing preservation across 3
source branches.

User scrutinized the revised plan (Minor revision). Two findings:

1. **Step 11 underspecified:** `git branch -d` for the preservation
   branch only works if PR merged with ancestry preserved (merge
   commit). If squash-merged, `-d` refuses. Also, GitHub auto-delete
   affects the remote, not the local branch.
2. **Step 3 too broad:** `git add docs/handoffs/archive/` should be
   tightened to stage the 4 specific files.

Both accepted and incorporated.

### Phase 6: Execution

**Phase 1 — Preservation branch:**
1. Created `chore/preserve-handoff-archives` from `origin/main`
2. File-recovered all 4 handoff archive files from 3 source branches
3. Staged the 4 specific files (not the whole directory)
4. Committed at `59c39a1f`
5. Pushed and opened PR #96

**Phase 2 — Merge and verify:**
6. User validated PR #96 (1 commit, 4 files, no spillover)
7. User chose merge commit (not squash) to preserve ancestry for
   `git branch -d` on the preservation branch
8. Merged PR #96 at `91966af0`
9. Fetched origin, verified 4 files on `origin/main`, archive count 50

**Phase 3 — Reset and delete:**
10. Switched to main
11. `git reset --hard origin/main` — main now matches origin exactly
12. `git branch -D chore/t6-governance-cleanup` — force-delete (no
    ancestry, as predicted by scrutiny)
13. `git branch -D fix/f7-f11-provenance-wire-format-blockers` — force-
    delete (no ancestry)
14. `git branch -d chore/preserve-handoff-archives` — safe delete
    succeeded (merge commit preserved ancestry, confirming user's merge
    strategy choice)

**Remote cleanup:**
15. Deleted 3 merged remote branches: `origin/chore/t6-governance-
    cleanup`, `origin/worktree-engram-remediation`, `origin/chore/
    preserve-handoff-archives`
16. Pruned stale tracking refs

**Skill sync:**
17. User replaced scrutinize skill repo copy with the promoted version
    from `~/.claude/`
18. Committed at `e26d070c`

## Decisions

### Decision 1: Main end-state policy — exact mirror

**Choice:** After cleanup, local `main` must match `origin/main`
exactly (0 ahead, 0 behind).

**Driver:** The 4 local-only commits on main were all either
already-promoted (scrutinize skill update, verified identical to
`~/.claude/skills/scrutinize/SKILL.md`) or operational (handoff
lifecycle commits). None carried unique work. Keeping main intentionally
ahead formalizes the drift pattern that created the divergence.

**Alternatives considered:**
- **Intentionally ahead** (rebase, keep local commits): Does not solve
  the drift problem — formalizes it. Main would be 4+ commits ahead
  after this cleanup, 6+ after next session's handoff lifecycle.
  Rejected because the pattern compounds.
- **Selective split** (reset main, relocate skill update to branch):
  Same end state as exact mirror but with unnecessary ceremony for an
  already-promoted skill update. Rejected as redundant.
- **Null** (leave as-is): 4-ahead/4-behind grows with each session.
  Rejected because the user invoked `/git-hygiene` specifically to
  resolve this.

**Trade-offs accepted:** Resetting main means the repo copy of
`.claude/skills/scrutinize/SKILL.md` reverts to the origin/main
version. Production copy at `~/.claude/` stays current. User addressed
this by manually copying the promoted version back after reset.

**Confidence:** High (E2) — verified skill promotion status via `diff`,
verified all 4 commits are either promoted or operational, verified
local main was never pushed with these commits.

**Reversibility:** Medium — `git reset --hard` is destructive to local
main. Recoverable via reflog for ~90 days.

**What would change this decision:** If handoff lifecycle commits needed
to be on `main` for some operational reason (they don't — handoffs are
searchable from any branch via `/search`).

### Decision 2: Preservation-first execution order

**Choice:** Preserve handoff archive files on `origin/main` via
dedicated PR BEFORE resetting local main to match it.

**Driver:** User stated: "main == origin/main is only acceptable after
the preserved handoff files have themselves been merged into
origin/main. Until then, branch cleanup has to be preservation-first,
not sync-first."

**Alternatives considered:**
- **Sync-first, recover later** (original plan): Rebase main first,
  then cherry-pick or file-recover. Rejected by user scrutiny — the
  reset would destroy the source branches' handoff files before they're
  preserved. Ordering violation.
- **Accept archive loss** (delete branches, no preservation): Handoff
  content already consumed, but the detailed session records (decisions,
  learnings, cross-references) lose their primary durable record and
  become unsearchable via `/search`. User chose to preserve.

**Trade-offs accepted:** Requires a PR to land the preservation commit
on `origin/main` before local cleanup can proceed. Adds one PR cycle
to the cleanup. Acceptable because the PR is trivial (4 files, no
code changes).

**Confidence:** High (E2) — the ordering constraint is mechanical: you
cannot recover files from branches you've already deleted, and you
cannot reset main to match origin/main until origin/main has the files.

**Reversibility:** N/A — this is a sequencing decision, not a state
change.

**What would change this decision:** If handoff archives were stored
outside git (e.g., a separate database), the ordering wouldn't matter.
They're git-tracked, so preservation must precede deletion.

### Decision 3: Merge commit over squash for PR #96

**Choice:** Merge PR #96 with a regular merge commit, not squash.

**Driver:** User stated: "My call is to merge it, and to use a regular
merge commit rather than squash. That preserves ancestry for
`chore/preserve-handoff-archives`, which makes the later local cleanup
cleaner and may allow `git branch -d` after `main` is reset."

**Alternatives considered:**
- **Squash merge:** Creates a single new commit on origin/main with no
  parent relationship to the preservation branch tip (`59c39a1f`).
  After resetting main to origin/main, `git branch -d` would refuse
  because the branch tip is not an ancestor. Would require `-D`
  (force-delete). Rejected to avoid unnecessary force-deletion.

**Trade-offs accepted:** Merge commit adds one "Merge pull request #96"
entry to `git log`. Negligible noise for the benefit of clean ancestry.

**Confidence:** High (E2) — the `-d` vs `-D` behavior is a mechanical
consequence of merge strategy. Verified: `-d` succeeded after merge
commit, confirming the prediction.

**Reversibility:** Low — merge strategy is fixed once PR is merged.

**What would change this decision:** If the repo had a squash-only
policy (it doesn't).

### Decision 4: Force-delete for non-ancestor branches

**Choice:** Use `git branch -D` (force-delete) for
`chore/t6-governance-cleanup` and
`fix/f7-f11-provenance-wire-format-blockers`.

**Driver:** File recovery via `git checkout <branch> -- <file>` does
not create merge ancestry. The branch tips (`7aff8ad6`, `b5be5d9e`)
are not ancestors of `main` even after the preservation commit lands.
`git branch -d` (safe delete) checks ancestry and will refuse.

**Alternatives considered:**
- **Cherry-pick instead of file recovery:** Would create ancestry by
  replaying commits on main. Rejected because cherry-picking the
  save+archive commit pairs imports intermediate state (file created
  then moved) and adds 4 commits to main instead of 1 clean
  preservation commit.
- **Merge the branches into main:** Would create ancestry via merge
  commit. Rejected because the branches contain product commits already
  on main via PR merge — would duplicate those commits in the merge.

**Trade-offs accepted:** Force-delete bypasses the safety gate that
prevents deleting unmerged work. Safe here because all preserved
content is verified on `origin/main` before deletion.

**Confidence:** High (E2) — verified `7aff8ad6` and `b5be5d9e` are not
ancestors of `main` or `origin/main`. Verified all 4 preserved files
exist on `origin/main` at commit `91966af0`. Deletion is the correct
mechanism.

**Reversibility:** Medium — branch tips recoverable via `git reflog`
for ~90 days. Specific SHAs: `chore/t6-governance-cleanup` was
`7aff8ad6`, `fix/f7-f11-provenance-wire-format-blockers` was
`b5be5d9e`.

**What would change this decision:** Nothing — this is the mechanically
correct deletion method given the preservation strategy chosen.

### Decision 5: Remote prune as separate phase

**Choice:** Prune merged remote branches after local cleanup, as a
separate phase rather than interleaved.

**Driver:** User's scrutiny finding #3 — remote deletion is shared-
state mutation, not local-only cleanup. Treating it as part of the
same plan blurs risk boundaries.

**Alternatives considered:**
- **Interleave with local cleanup** (original plan): Delete remote
  branches during the same execution pass as local cleanup. Rejected
  because shared-state mutation warrants separate risk evaluation.

**Trade-offs accepted:** Two phases instead of one. Minor coordination
cost.

**Confidence:** High (E2) — straightforward scope separation.

**Reversibility:** High — remote branches can be re-pushed if needed.

**What would change this decision:** Nothing — scope separation is a
process decision, not a technical one.

## Changes

### PR #96: `docs/handoffs/archive/` (4 new files, 3888 insertions)

**Purpose:** Preserve handoff archive files from local branches being
deleted. Prerequisite for resetting local `main` to `origin/main`.

**State before session:** 46 archived handoffs on `origin/main`. 4
additional handoff archives existed only on local branches
(`chore/t6-governance-cleanup`, `fix/f7-f11-provenance-wire-format-
blockers`, local `main`) and would be lost on branch deletion / main
reset.

**State after session:** 50 archived handoffs on `origin/main`. All 4
files recovered via `git checkout <branch> -- <file>` onto a dedicated
preservation branch, committed at `59c39a1f`, merged via PR #96 at
`91966af0`.

**Files preserved:**
| File | Source | Lines |
|------|--------|-------|
| `2026-04-05_04-50_t6-review-correction-merged-pr91-and-f6-f7-f11-branch-initialized.md` | local `main` | 1142 |
| `2026-04-06_15-07_f6-concession-lifecycle-resolved-and-pr93-merged.md` | local `main` | 1102 |
| `2026-04-06_22-51_f7-f11-resolved-and-pr94-opened.md` | `fix/f7-f11-...` | 852 |
| `2026-04-06_23-39_t6-governance-closed-and-pr95-merged.md` | `chore/t6-...` | 792 |

### `.claude/skills/scrutinize/SKILL.md` (115 insertions, 57 deletions)

**Purpose:** Sync repo copy with the promoted production version at
`~/.claude/skills/scrutinize/SKILL.md`. The repo copy fell behind
after `main` was reset to `origin/main` (which had an older version).

**Committed at:** `e26d070c` on `main`.

**Design choice:** User performed the copy manually rather than
cherry-picking the original commit (`3e24c225`). The production copy is
the authority after promotion — copying it back is the correct approach.

## Codebase Knowledge

### Branch state (post-session)

| Branch | Location | State | Action |
|--------|----------|-------|--------|
| `main` | local + remote | Exact mirror (`e26d070c`, 1 ahead for skill sync) | Cleaned |
| `feature/codex-collaboration-r2-dialogue` | local only | 39 commits, upstream gone, tagged `r2-dialogue-branch-tip` | Deferred |

### Remote branches (post-session)

| Remote branch | Status | Notes |
|---|---|---|
| `origin/main` | Default branch | At `91966af0` (PR #96 merge) |
| `origin/chore/post-r1-planning` | Unmerged, 9 commits | R2 dialogue planning, last activity 2026-03-28 |
| `origin/feature/codex-compat-baseline` | Unmerged, 11 commits | T1 compat baseline, last activity 2026-03-27 |
| `origin/worktree-engram-review` | Unmerged, 11 commits | Engram spec review amendments, last activity 2026-03-19 |

### Deleted branches (this session)

| Branch | Type | Mechanism | Reason |
|--------|------|-----------|--------|
| `chore/t6-governance-cleanup` | local | `git branch -D` | PR #95 merged, handoff commits non-ancestor |
| `fix/f7-f11-provenance-wire-format-blockers` | local | `git branch -D` | PR #94 merged, handoff commits non-ancestor |
| `chore/preserve-handoff-archives` | local | `git branch -d` | PR #96 merged with merge commit, ancestry preserved |
| `origin/chore/t6-governance-cleanup` | remote | `git push --delete` | Merged into origin/main |
| `origin/worktree-engram-remediation` | remote | `git push --delete` | Merged into origin/main |
| `origin/chore/preserve-handoff-archives` | remote | `git push --delete` | Merged into origin/main, GitHub didn't auto-delete |

### Git mechanics learned this session

**File recovery vs cherry-pick:** `git checkout <branch> -- <file>`
grabs the final state of a file from another branch into the current
working tree. Unlike cherry-pick, it doesn't import the commit history
or create ancestry. This means:
- Cleaner preservation (one commit with final-state files, not
  intermediate save+archive pairs)
- But: the source branch tips remain non-ancestors of main, so
  `git branch -d` (safe delete) will refuse — must use `-D`

**Merge commit vs squash for `-d` compatibility:** `git branch -d`
checks whether the branch tip is an ancestor of HEAD. A merge commit
makes the branch tip an ancestor (it's a parent of the merge). A squash
commit creates a new commit with no parent relationship to the branch
tip. For branches you want to safe-delete after PR merge, choose merge
commit over squash.

**`git branch --merged` vs "PR merged":** These are different concepts.
`git branch --merged origin/main` checks git ancestry — whether the
branch tip is reachable from origin/main. "PR merged" means the PR's
product commits reached main via a GitHub merge/squash. A branch can
have its PR merged while still failing `--merged` if it has local-only
commits beyond the PR (e.g., handoff lifecycle commits).

### Handoff lifecycle commit pattern

Handoff save/archive operations commit to whatever branch is checked
out at the time. When working on feature branches, these commits end up
on the feature branch. After the feature PR merges, the handoff commits
are orphaned — they exist only on the local branch, with no path to
origin/main. This creates a structural problem: branch deletion loses
the handoff archives.

The preservation-first pattern resolves this: before deleting branches,
file-recover the handoff archives onto a dedicated branch, PR them to
origin/main, then delete.

## Context

### Mental model for this session

**Framing:** This was a repository governance problem, not a git
mechanics problem. The core question wasn't "rebase vs merge" — it was
"what is main allowed to be?" The sync method is downstream of the
policy. My initial recommendation optimized for the wrong variable
(mechanics before policy), and the user's scrutiny correctly identified
the framing error.

**Core insight:** Preservation must precede deletion. If content needs
to survive on `origin/main`, it must reach `origin/main` before the
source branches are destroyed. This seems obvious in retrospect, but
the natural cleanup impulse (sync first, clean up after) inverts the
safe ordering.

**Secondary insight:** `git branch -d` vs `-D` is not a preference —
it's a mechanical consequence of how content reached main. File recovery
preserves content but not ancestry. Merge commits preserve ancestry.
Squash merges don't. The deletion mechanism is determined by the
preservation strategy, not chosen independently.

### Project state (post-session)

- **main:** Clean, matches `origin/main` (1 commit ahead for skill
  sync at `e26d070c`). No divergence.
- **T7:** Unblocked. Done-when at `plan.md:42-43`. All prerequisites
  met per T6 administrative close.
- **Handoff archives:** 50 files on origin/main. All governance arc
  handoffs preserved.
- **Branches:** 2 local (main + codex-collaboration), 4 remote
  (main + 3 unmerged). Clean.

### Environment

- Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `main`
- Commit: `e26d070c`
- PR: #96 (merged at `91966af0`)
- Local main: 1 ahead of origin/main (skill sync commit)

## Learnings

### Optimize for the right variable: policy before mechanics

**Mechanism:** When cleaning up git state, the first question is "what
should the end state be?" (policy), not "how do we get there?"
(mechanics). I initially recommended "Rebase + file recovery" — which
is a mechanics answer to a policy question. The user's scrutiny found
that the option set dodged the actual decision: whether main should
match origin/main exactly or stay intentionally ahead.

**Evidence:** Scrutiny finding #1 (High): "The option set dodges the
`main` disposition decision. [...] The real choice — preserve vs
relocate vs drop those local-only commits — is still unresolved."

**Implication:** For future branch cleanup sessions, always define the
target end state first, then select the mechanics to reach it. The
end state constrains which mechanics are valid.

**Watch for:** "Rebase vs merge" debates that are actually "what belongs
on main" debates in disguise.

### File recovery doesn't create ancestry

**Mechanism:** `git checkout <branch> -- <file>` copies a file into the
working tree from another branch. It does not create any commit
relationship between the branches. The branch tips remain non-ancestors
of HEAD. This means `git branch -d` (which checks ancestry) will
refuse, even though the file content has been preserved.

**Evidence:** Both `chore/t6-governance-cleanup` (`7aff8ad6`) and
`fix/f7-f11-provenance-wire-format-blockers` (`b5be5d9e`) required
`git branch -D` after file recovery. `chore/preserve-handoff-archives`
(`59c39a1f`) allowed `git branch -d` because the merge commit preserved
ancestry.

**Implication:** When choosing a preservation strategy, consider the
downstream deletion mechanism. File recovery requires force-delete.
Cherry-pick or merge preserves ancestry for safe-delete. The trade-off:
file recovery is cleaner (one commit) but requires `-D`.

**Watch for:** Plans that use file recovery but specify `-d` for
deletion — they will fail silently (git refuses, doesn't error loudly).

### Preservation must precede deletion

**Mechanism:** If content on branch X needs to survive on
`origin/main`, it must reach `origin/main` BEFORE branch X is deleted
or main is reset. The natural cleanup impulse (sync/clean first, then
preserve) inverts the safe ordering.

**Evidence:** User's critical constraint: "main == origin/main is only
acceptable after the preserved handoff files have themselves been merged
into origin/main."

**Implication:** For any future cleanup where branch-only content needs
preservation, the execution order is: (1) create preservation branch
from origin/main, (2) file-recover content, (3) PR and merge to
origin/main, (4) THEN reset main and delete source branches.

**Watch for:** Cleanup plans that say "sync first, recover later" —
the sync (reset) destroys the source before preservation is complete.

### Merge commit vs squash determines post-merge `-d` behavior

**Mechanism:** `git branch -d` checks whether the branch tip is an
ancestor of HEAD. A merge commit makes the branch tip a parent (ancestor
of HEAD). A squash commit creates a new commit with the branch's changes
but no parent relationship to the branch tip.

**Evidence:** PR #96 merged with merge commit. After resetting main to
`91966af0`, `git branch -d chore/preserve-handoff-archives` succeeded
because `59c39a1f` (branch tip) is a parent of the merge commit.

**Implication:** When creating branches that you want to safe-delete
after PR merge, prefer merge commit over squash. When this is not
possible (squash-only repos), accept that `-D` is the required
mechanism after verifying content is on main.

**Watch for:** Repos with squash-only policies where `-d` cleanup
after PR merge will always fail — use `-D` with explicit verification
that the branch content reached main.

## Next Steps

### 1. Unmerged remote branch triage

**Dependencies:** None — can be done any time.

**What to do:** Investigate the 3 unmerged remote branches:
1. `origin/chore/post-r1-planning` — 9 commits, last activity
   2026-03-28. Codex-collaboration R2 dialogue planning.
2. `origin/feature/codex-compat-baseline` — 11 commits, last activity
   2026-03-27. T1 compatibility baseline with real feature code.
3. `origin/worktree-engram-review` — 11 commits, last activity
   2026-03-19. Engram spec review amendments.

**What to read first:** `git log --oneline -10` for each remote branch.
Check if any have associated PRs or issues. Check if the work was
superseded by later changes on main.

**Acceptance criteria:** Each branch classified as: delete (superseded),
keep (active/needed), or PR (work worth merging).

### 2. `feature/codex-collaboration-r2-dialogue` disposition

**Dependencies:** None — separate decision.

**What to do:** Decide long-term disposition for this local branch.
39 unique commits of significant product work (dialogue dispatch,
lineage recovery, turn contracts). Protected by tag
`r2-dialogue-branch-tip`. Upstream gone.

**Key question:** Is this work still relevant? Was it superseded by
later cross-model development? The tag preserves all commits even if
the branch is deleted, but the branch name provides discoverability.

**What to read first:** `git log --oneline feature/codex-collaboration-
r2-dialogue | head -20` to understand the work scope.

### 3. Push skill sync commit to origin

**Dependencies:** None — trivial.

**What to do:** Main is 1 commit ahead of origin/main (`e26d070c` —
scrutinize skill sync). This can be pushed directly to main or bundled
with other work.

**Acceptance criteria:** `git log main..origin/main` and
`git log origin/main..main` both empty.

### 4. T7 executable slice work

**Dependencies:** T6 closed (done). Blocker table clear (done). All
prerequisites met per `plan.md:42-43`.

**What to do:** Define the minimal executable slice required for a real
dry-run. Done-when: "there is an agreed smallest buildable slice that
can execute one dialogue and expose the fields the dry-run must inspect."

**What to read first:**
- `plan.md:42-43` (T7 done-when)
- `benchmark-readiness.md:167-231` (T4-BR-07: execution prerequisites)
- `benchmark-readiness.md:233-255` (T4-BR-08: non-scoring run)
- `composition-review.md:192-196` (deferred-to-T7 items)

## In Progress

**Clean stopping point.** All planned cleanup complete. PR #96 merged.
Main matches origin/main (1 ahead for skill sync). No work in flight.

Main is 1 commit ahead of origin/main with the scrutinize skill sync
at `e26d070c`. This is the only remaining local-only commit — a clean,
intentional delta rather than accumulated drift.

## Open Questions

1. **What is the disposition for the 3 unmerged remote branches?**
   `origin/chore/post-r1-planning` (9 commits, R2 planning),
   `origin/feature/codex-compat-baseline` (11 commits, T1 compat),
   `origin/worktree-engram-review` (11 commits, engram spec amendments).
   All need investigation before deciding.

2. **Should `feature/codex-collaboration-r2-dialogue` be preserved
   long-term?** 39 unique commits, tagged `r2-dialogue-branch-tip`.
   Tag preserves reachability, branch provides discoverability.

3. **Should the skill sync commit be pushed immediately or bundled?**
   Main is 1 ahead — much smaller delta than the pre-cleanup 4-ahead
   state, but still non-zero.

## Risks

1. **Handoff lifecycle commits will re-accumulate on main.** Each
   session that runs `/save` or `/load` while on main creates handoff
   commits. The exact-mirror policy is a point-in-time reset, not a
   structural fix. Future sessions that work on main (rather than
   feature branches) will recreate the same divergence pattern.

2. **Unmerged remote branches may contain superseded work.** The 3
   unmerged remotes are 10-19 days stale. If the work was superseded,
   they're safe to delete. If still relevant, they need investigation
   to determine merge path. Staleness doesn't automatically mean
   obsolescence.

3. **Post-cleanup `main` is 1 ahead.** The scrutinize skill sync commit
   is a small, intentional delta. But if left unpushed, it starts the
   same accumulation pattern. Should be pushed or PRd soon.

## References

| What | Where |
|------|-------|
| PR #96 (handoff preservation, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/96 |
| PR #95 (T6 governance close, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/95 |
| PR #94 (F7/F11 resolver, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/94 |
| Preservation commit | `59c39a1f` on `chore/preserve-handoff-archives` |
| Merge commit (PR #96) | `91966af0` on `origin/main` |
| Skill sync commit | `e26d070c` on `main` |
| Deleted branch tip: chore/t6 | `7aff8ad6` (recoverable via reflog) |
| Deleted branch tip: fix/f7-f11 | `b5be5d9e` (recoverable via reflog) |
| T7 done-when | `plan.md:42-43` |
| T6 administrative close | `composition-review.md:198-238` |

## Gotchas

1. **Main is 1 ahead of origin/main.** The scrutinize skill sync commit
   (`e26d070c`) is the only local-only commit. Much cleaner than the
   pre-session 4-ahead state, but still non-zero. Push or PR to clear.

2. **`git branch --merged` is not the same as "PR merged."** Branches
   with local-only handoff commits beyond the PR merge point fail
   `--merged` even though their product work is on main. This session
   required `git branch -D` for two such branches.

3. **File recovery doesn't create ancestry.** Using
   `git checkout <branch> -- <file>` to preserve content means the
   source branch tip remains a non-ancestor of main. `git branch -d`
   will refuse. Must use `-D` or choose a preservation method that
   creates ancestry (cherry-pick, merge).

4. **Merge commit vs squash affects post-merge cleanup.** PR #96 was
   merged with a merge commit specifically so that `git branch -d`
   (safe delete) would work for the preservation branch. Squash merge
   would have required `-D`.

5. **GitHub auto-delete affects remote, not local.** Even if GitHub
   auto-deletes the remote branch after PR merge, the local tracking
   ref persists. `origin/chore/preserve-handoff-archives` survived PR
   merge and had to be explicitly deleted.

6. **Handoff lifecycle commits orphan on feature branches.** The
   structural pattern: `/save` and `/load` commit to whatever branch
   is checked out. After a feature PR merges, these commits have no
   merge path to main. Future git-hygiene passes will encounter this
   pattern until the handoff plugin is changed to commit elsewhere.

## Conversation Highlights

### Scrutiny catching the framing error

The most consequential exchange was the user's scrutiny of my first
recommendation. I optimized for "how to sync main" (rebase vs merge)
before establishing "what main should be after cleanup." The scrutiny
returned 4 findings including two High-severity issues. The core
critique: "This is not solving the right problem yet. The hard part is
not 'rebase vs merge'; it is deciding what main is allowed to be after
cleanup."

### User's preservation-first constraint

After accepting the exact-mirror recommendation, the user added a
critical execution constraint: "main == origin/main is only acceptable
after the preserved handoff files have themselves been merged into
origin/main." This inverted my proposed execution order (sync-first →
preservation-first) and was mechanically correct — you cannot reset
main to origin/main and then recover files from branches that no longer
exist in the working tree.

### Merge strategy as a downstream consequence

The user chose merge commit over squash for PR #96 with explicit
reasoning: "That preserves ancestry for `chore/preserve-handoff-
archives`, which makes the later local cleanup cleaner and may allow
`git branch -d` after `main` is reset." This prediction was verified:
`-d` succeeded for the preservation branch while `-D` was required for
the two non-ancestor branches. The merge strategy was chosen to serve
the deletion mechanism, not as a default preference.

### Two rounds of scrutiny, both accepted

The user scrutinized both the initial recommendation (Major revision, 4
findings) and the revised plan (Minor revision, 2 findings). All 6
findings were accepted and incorporated. The scrutiny quality was high
— each finding identified a specific mechanical or framing error, not a
stylistic preference.

## User Preferences

**Scrutinizes recommendations before accepting.** User copied the
recommendation to clipboard, analyzed it externally, and returned
structured scrutiny with severity ratings. This is a deliberate
review-before-execute pattern.

**Defines policy before mechanics.** User's scrutiny explicitly
identified that the mechanics (rebase vs merge) were downstream of the
policy (what main should be). Prefers explicit end-state definitions
before choosing execution methods.

**Preservation-first execution ordering.** User's constraint: content
must reach its durable location before source branches are destroyed.
"Sync first, recover later" is the wrong order because the sync
destroys the source.

**Merge strategy chosen for downstream consequences.** User chose merge
commit specifically to enable `git branch -d` (safe delete) for the
preservation branch. Merge strategy is not a default — it's chosen for
the specific post-merge cleanup needs.

**Accepts force-delete when mechanically correct.** User did not object
to `git branch -D` for the two non-ancestor branches — the scrutiny
finding was about making the mechanism explicit, not about avoiding it.
Force-delete is acceptable when preceded by verified content
preservation.

**Validates before and after.** User validated PR #96 before merge
(1 commit, 4 files, no spillover). User validated final repo state
after cleanup (main matches origin, archive count 50, correct branch
list). Evidence-based confirmation, not trust-based.
