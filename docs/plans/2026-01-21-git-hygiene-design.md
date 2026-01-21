## Design Context: git-hygiene

**Type:** Process/Workflow
**Risk:** Medium (creates commits, deletes branches — reversible via cleanup branch isolation)

### Problem Statement

Git repos accumulate mess over time: untracked files that should be ignored or deleted, changes spanning multiple concerns staged together, stale local branches from merged PRs, and orphaned remote-tracking branches. Manual cleanup is tedious, error-prone, and often skipped — leading to cluttered git status, incoherent commit history, and branch list noise.

### Success Criteria

- Zero untracked files (everything tracked, ignored, or deleted with approval)
- Coherent commits (changes grouped by semantic concern, Conventional Commits format)
- Minimal working tree (only intentional WIP remains)
- Clean branch list (no merged/stale local branches, no orphaned remote-tracking)

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Autonomy level | Semi-autonomous | Safe ops (staging, .gitignore) auto; destructive ops (delete) require approval |
| Change grouping | Hybrid (semantic + approval) | Pure auto-grouping makes mistakes; pure manual defeats purpose |
| Commits | Full (analyze, group, message, commit) | User wanted complete automation through to committed changes |
| Preview | Default mode (always preview first) | Matches semi-autonomous model; prevents mistakes |
| Cleanup isolation | Always on timestamped branch | Safety — easy to review, discard, or merge |
| Failure handling | Stop and report | Don't attempt partial recovery; let user assess |
| Branch naming | `cleanup/YYYY-MM-DD-HHMMSS` | Guaranteed unique, chronological, no conflicts |
| Config location | Project root (tracked) | Shared team conventions, survives fresh clones |

### Compliance Risks

Things that could cause Claude to rationalize around this skill:

1. **"This is a simple case"** — temptation to skip preview for small repos
2. **"User said just clean it"** — pressure to bypass grouping approval
3. **"Patterns match, no need to ask"** — over-relying on pattern detection for ambiguous files
4. **"Already previewed the plan"** — treating approval of one part as blanket approval for all
5. **"Time pressure"** — interpreting "quickly" as permission to skip safety checks

Mitigations built into the skill:
- Explicit Decision Point for "pressure to skip preview"
- Protected patterns require per-file confirmation regardless of batch approval
- Anti-pattern documentation for "treating impatience as permission"

### Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Aggressive autonomy (auto-delete artifacts) | Too risky; pattern matching isn't perfect |
| Stash WIP automatically | Stashes get forgotten; explicit ask-per-case is safer |
| Recurse into submodules | Submodules have their own lifecycle; report-only is appropriate |
| Try to resolve complex states | Rebase/merge states need human judgment; abort cleanly instead |
| Rollback on failure | Git operations aren't easily undone; stop-and-report is cleaner |
| Path-based grouping | Often wrong; semantic analysis + approval is more accurate |

### Edge Cases Handled

- Large repos (>100 files / >50 branches): Ask before proceeding
- Complex git states (rebase, merge, etc.): Abort cleanly with guidance
- Protected files (`.env*`, `*.key`): Never auto-delete; explicit confirmation required
- Unknown files: Always ask (track/ignore/delete)
- Pre-commit hook failures: Stop, report, let user fix
- Worktree conflicts: Detect and refuse to delete affected branches
- Nothing to clean: Quick confirmation and exit (no empty cleanup branch)

### Prior Art

An archived plan document (`docs/plans/archived/2026-01-07-git-hygiene-pr-fixes.md`) shows prior implementation work that was not merged. This design is fresh but informed by the existence of that prior attempt — the archived plan focused on fixing safety issues in Python scripts, suggesting the prior implementation had matured enough to need bug fixes.

### Testing Strategy

1. Create repo with intentionally messy state:
   - Untracked files (mix of artifacts, unknowns, protected patterns)
   - Mixed staged/unstaged changes spanning multiple concerns
   - Stale local and remote-tracking branches

2. Run skill, verify:
   - Preview shows all categories correctly
   - Grouping proposal is sensible
   - Protected files flagged appropriately
   - Execution creates expected commits
   - Branch cleanup works
   - Report is complete and accurate

3. Pressure test: Run with "just clean it up quickly" and verify preview still shown

4. Failure test: Create pre-commit hook that fails, verify skill stops and reports correctly
