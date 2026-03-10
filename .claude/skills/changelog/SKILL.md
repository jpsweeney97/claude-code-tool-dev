---
name: changelog
description: >-
  Create, audit, update, and refine CHANGELOGs with verified accuracy. Orchestrates an agent team
  to gather evidence from git history, GitHub PRs, and handoff archives in parallel, then
  cross-references all three sources to produce grounded entries. Trigger on: adding PRs/commits
  to a changelog, creating a changelog from scratch, checking changelog accuracy against git history,
  finding what changed between versions or since a date, preparing release documentation, or figuring
  out which version a feature shipped in. Applies to any request that touches CHANGELOG.md files,
  version history, or release notes — whether creating, editing, or verifying them.
---

# Changelog Skill

Create and maintain CHANGELOGs with verified accuracy by cross-referencing three evidence sources in parallel. Uses an agent team to deeply mine git history, GitHub PRs, and handoff archives simultaneously — producing entries grounded in evidence, not memory.

## Prerequisite

This skill requires agent teams. Before proceeding, verify the feature is enabled:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

If not enabled, tell the user: "This skill uses agent teams to gather evidence from git, GitHub, and handoff archives in parallel. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json env block, then restart the session." Do not fall back to a sequential approach — parallel evidence gathering with cross-referencing is the core value proposition.

## Modes

| Mode | When | What happens |
|------|------|-------------|
| **Create** | No CHANGELOG exists, or user asks to create one | Full evidence gathering → reconcile → write |
| **Update** | CHANGELOG exists, user asks to add recent changes | Scoped evidence gathering → reconcile with existing → write new entries |
| **Audit** | User asks to check, verify, or audit the changelog | Full evidence gathering → compare claims vs evidence → report |
| **Refine** | User asks to improve wording, recategorize, fix formatting | Edit existing entries directly — no team needed |

Detect the mode from context. If ambiguous between Update and Audit, ask: "I see an existing CHANGELOG. Do you want me to **update** it with recent changes, or **audit** it for accuracy?"

**Refine mode** skips the agent team entirely — it works only with existing CHANGELOG content. Proceed directly to editing.

## Scope Check

Before starting, check whether the user actually needs a changelog or something adjacent.

**Redirect signals** — the request is about:
- Release notes for users (different audience and format than a changelog)
- A raw commit log dump ("give me all the commits")
- Deployment documentation or runbooks (handbook territory)

**Redirect action:** "This sounds like [release notes / a commit log / operational documentation] rather than a changelog. Want me to proceed differently?"

**Changelog signals** — the request focuses on tracking what changed across versions, maintaining a CHANGELOG.md, or auditing existing entries against evidence.

**Format conformance:** If an existing CHANGELOG uses a non-Keep-a-Changelog format (Angular-style, GNU-style, or a custom format), match the existing format rather than converting. The Keep a Changelog format in Step 4 is the default for new changelogs only.

## Step 1: Determine Scope

Before launching the team, establish:

1. **Which component?** The whole repo, a specific package, or a plugin? This determines the git path filter.
2. **What version range?** Everything (for create), or since a specific version/tag/date (for update)?
3. **Where does the CHANGELOG live?** Find the existing file or determine where to create it.

For package-level CHANGELOGs, scope evidence gathering to that package's directory.

For audit/update modes, read the existing CHANGELOG before launching the team so you can communicate the current state to the Changelog Analyst.

## Step 2: Launch Evidence Team

Create an agent team to gather evidence from all three sources simultaneously. Each teammate specializes in one evidence source and writes structured findings to the workspace.

**Critical: known failure modes to guard against:**
- **Do not substitute the Agent tool for agent teams.** If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` and use it. The Agent tool with `run_in_background` looks similar but lacks teammate-to-teammate messaging, coordinated completion detection, and shared task state — leading to polling races and lost coordination. Agent teams and the Agent tool are not interchangeable.
- The lead may start gathering evidence itself instead of waiting for teammates. If you catch yourself running git log or gh commands before teammates finish, stop. Your job is to coordinate, then reconcile.
- The lead may declare the team finished before all teammates complete. Wait for all idle notifications (3 in create mode, 4 in audit/update mode) before proceeding to reconciliation.
- Task status can lag — check the workspace for output files as a secondary completion signal.

Tell the lead to create these teammates with these prompts:

### Teammate 1: Git Historian

> Mine the complete git history for this project. Your deliverable is a structured change timeline.
>
> **Scope:** `{scope-path}` — version range: `{version-range}`
>
> Tasks:
> 1. **Version boundaries** — identify all git tags in the scope. Map each tag to a date and commit. Classify each tag: version tags (v1.2.3, 1.0.0, release-1.2) are version boundaries; deployment tags (deploy/prod, staging-2024-01) and arbitrary labels should be noted but not used as version boundaries. If no version-like tags exist, note this so the lead can ask the user about versioning
> 2. **Commit timeline** — all commits in the version range, scoped to the path. Capture: hash, date, message, author. For merge commits, also capture the branch name. For repos with over 500 commits in the version range, switch strategies: group commits by file or directory rather than listing individually, and summarize patterns (e.g., "47 commits touching auth/ — primarily refactoring and test additions"). If over 2000 commits, ask the lead to narrow the scope before proceeding
> 3. **Diff analysis** — for each version boundary (or logical grouping if no tags), summarize what changed: files added/modified/deleted, with brief descriptions of the nature of changes
> 4. **Direct pushes** — identify commits that were pushed directly (not via PR merge). These often represent small fixes or config changes that PRs miss
> 5. **Superseded work** — identify WIP or fixup commits that were superseded by later work in the same range. Flag these so they don't become duplicate entries
>
> When you find direct-push commits that have no corresponding merge commit, message the PR Analyst — these changes won't appear in their PR data. When you find commits referencing session work or handoff context, message the Handoff Archivist with the date range.
>
> Write your findings to `{workspace}/evidence/git-history.md` in this structure:
> ```
> ## Version Boundaries
> [tags with dates and commits]
>
> ## Changes by Version
> ### [version or date range]
> - [commit hash] [date] [message] — [brief description of what changed]
>
> ## Direct Pushes (no PR)
> [commits not associated with merge commits]
>
> ## Superseded Work
> [WIP/fixup commits that were later replaced]
> ```

### Teammate 2: PR Analyst

> Mine all GitHub pull requests for this project. Your deliverable is a curated summary of logical changes.
>
> **Scope:** `{scope-path}` — date range: `{date-range}`
>
> Tasks:
> 1. **Merged PRs** — list all merged PRs in the date range. Capture: number, title, merge date, description summary, labels, files changed
> 2. **Logical grouping** — identify PRs that are part of the same feature (multiple PRs for one feature, or a PR with follow-up fixes). Group them
> 3. **Multi-change PRs** — flag PRs whose description or diff reveals multiple distinct changes bundled together. Each distinct change should become a separate changelog entry
> 4. **PR quality assessment** — for each PR, rate how well the title/description summarizes the actual change. Note cases where the title is misleading or too vague
> 5. **Linked issues** — capture any linked issues that provide additional context about user-facing impact
>
> Filter to PRs that touch files in the scope path. Use `gh pr list --state merged --json number,title,mergedAt,body,labels,files` and `gh pr view <n> --json title,body,files,commits` for details. For squash-merged PRs (where `commits` returns a single commit), the PR body and diff are the primary evidence — not the commit list. Read the full PR body and diff to reconstruct individual changes. If the PR body is empty and the title is vague, flag it in the "Missing Context" section. Before mining PRs, verify `gh` is available and authenticated. If `gh` fails (no GitHub remote, not authenticated, or API error), write a note explaining the specific failure and stop — the Git Historian's data will serve as primary structure instead. If `gh` works but returns no merged PRs for the scope, note this as a valid finding (all changes were direct pushes) and stop.
>
> When you find PRs with vague titles or no description (the "Missing Context" category), message the Handoff Archivist — handoff files often contain the intent behind these changes.
>
> Write your findings to `{workspace}/evidence/pr-analysis.md` in this structure:
> ```
> ## PRs by Date (newest first)
> ### PR #N: [title] — [merge date]
> Summary: [what actually changed, from the diff, not just the title]
> Files: [key files changed]
> Labels: [if any]
> Multi-change: [yes/no — if yes, list the distinct changes]
>
> ## Logical Groups
> [PRs that belong together]
>
> ## Missing Context
> [PRs with vague titles or no description — flag for handoff enrichment]
> ```

### Teammate 3: Handoff Archivist

> Mine the handoff archive for session context, decisions, and intent behind changes. Your deliverable enriches mechanical git/PR data with the "why."
>
> **Scope:** Project `{project-name}` — date range: `{date-range}`
>
> The handoff archive lives at `~/.claude/handoffs/{project-name}/.archive/`. Filenames follow `YYYY-MM-DD_HH-MM_<title-slug>.md`.
>
> If the archive directory doesn't exist, write a note to your output file explaining the gap and stop — there's no handoff data to mine.
>
> Tasks:
> 1. **Locate relevant handoffs** — filter by date range and scope. For large archives (50+ files), grep the YAML frontmatter `files:` field to find handoffs touching the scope path
> 2. **Extract high-value sections** — for each relevant handoff, read these sections in priority order:
>    - **Changes** (always read) — per-file implementation record with commit hashes. Direct material for entries. Each subsection typically maps to one changelog bullet
>    - **Decisions** (read for non-trivial changes) — the "why": alternatives rejected, trade-offs accepted. Transforms mechanical entries into meaningful ones
>    - **Goal** (read for non-trivial changes) — session scope, stakes, connection to project arc. Groups changes into logical features
>    - **In Progress** — completion status. Partial work → `[Unreleased]`, not a version
>    - **Next Steps** — deferred work. Exclude from changelog
>    - Ignore: Learnings, Risks, Gotchas, Codebase Knowledge, Context, User Preferences, References (session-continuation context, not changelog material)
> 3. **Build enrichment map** — for each handoff: what was done, why, and user-facing impact. Map to corresponding PR(s) or commit(s) where visible
> 4. **Flag multi-session arcs** — handoffs that are part of a larger feature spanning multiple sessions. These should be one logical feature in the changelog, not fragmented entries
>
> When you find handoff sessions that reference specific PRs or commits, message the Git Historian and PR Analyst so they can cross-reference. When you find multi-session arcs, message both so they can look for the corresponding commit/PR patterns.
>
> Write your findings to `{workspace}/evidence/handoff-context.md` in this structure:
> ```
> ## Handoffs Found
> [count and date range]
>
> ## Enrichment Map
> ### [handoff filename]
> What: [what was done]
> Why: [key decisions and rationale]
> Impact: [user-facing significance]
> Related PRs/commits: [if identifiable]
>
> ## Multi-Session Arcs
> [groups of handoffs forming a single feature]
>
> ## Deferred Work (exclude from changelog)
> [items from Next Steps sections]
> ```

### Teammate 4: Changelog Analyst (Audit and Update modes only)

> Analyze the existing CHANGELOG and extract every factual claim for verification.
>
> **File:** `{changelog-path}`
>
> Tasks:
> 1. **Extract claims** — for every entry, extract the factual claim: what changed, when, in which version, with which PR reference
> 2. **Create verification checklist** — for each claim, note what evidence would confirm or deny it (specific commit, PR, file change)
> 3. **Style analysis** — document the existing style: entry length, verb tense, specificity level, whether components are named, whether PR numbers are included. The lead will match this style for new entries
> 4. **Coverage map** — identify the version ranges and date ranges already documented
> 5. **Gap detection** — for update mode: identify where new entries should be inserted (after which version, in which section)
>
> Share your claims checklist with the other teammates. Message the Git Historian about commit/tag claims, the PR Analyst about PR number claims, and the Handoff Archivist about feature/decision claims. Use targeted messages, not broadcast.
>
> Write your findings to `{workspace}/evidence/changelog-analysis.md` in this structure:
> ```
> ## Claims by Version
> ### [version]
> - Claim: [what the entry says]
>   Verify: [what evidence would confirm — commit hash, PR number, file change]
>   Status: [pending — to be filled by lead during reconciliation]
>
> ## Style Profile
> Entry length: [terse/moderate/detailed]
> Verb tense: [past/present/imperative]
> Components named: [yes/no]
> PR references: [yes/no]
>
> ## Coverage Map
> [version ranges and date ranges documented]
>
> ## Insertion Points (update mode)
> [where new entries should go]
> ```

### Workspace Setup

Before spawning the team, create the workspace directory:

```
{project-root}/.changelog-workspace/evidence/
```

Tell each teammate to write their findings to this directory. After the CHANGELOG is complete, offer to clean up the workspace.

### Task Structure

Instruct the lead to create tasks with these dependencies:

1. Evidence gathering tasks (independent, no dependencies between them):
   - "Gather git history evidence" (Git Historian)
   - "Gather PR evidence" (PR Analyst)
   - "Gather handoff context" (Handoff Archivist)
   - "Analyze existing CHANGELOG" (Changelog Analyst — audit/update only)
2. "Reconcile evidence from all sources" (depends on all evidence tasks)
3. "Draft changelog entries" (depends on reconciliation)
4. "Verify accuracy" (depends on draft)

**Important:** Explicitly tell the lead: "Wait for all teammates to complete their evidence gathering before starting reconciliation. Do not begin reconciling, drafting, or writing until all evidence reports exist in the workspace."

## Step 3: Reconcile Evidence

Teammates do not inherit the lead's conversation history — they start fresh with only their spawn prompt and the project's CLAUDE.md/skills. This is why each teammate prompt above is self-contained with explicit deliverables and output paths. Do not assume teammates know the user's original request or the CHANGELOG mode.

After all teammates complete, read all evidence reports. Cross-reference into a unified change list:

1. **Start with PRs as primary structure** — each merged PR typically represents one logical change with a clean summary. If no PRs exist (the PR Analyst reported none), use git history as primary structure instead — group commits by logical change
2. **Fill gaps from git history** — direct-push commits and changes not associated with PRs
3. **Enrich from handoffs** — for every non-trivial entry (new features, architectural changes, complex fixes), check the Handoff Archivist's enrichment map for the "why" behind the change
4. **Filter superseded work** — the Git Historian flagged WIP and fixup commits. Remove duplicates
5. **(Audit/Update) Cross-reference claims** — the Changelog Analyst's checklist tells you what the existing CHANGELOG says. Verify each claim against the other three sources

**When sources conflict:** Evidence sources may disagree — a PR title says "refactor," the diff shows a behavior change, and the handoff calls it a security fix. Resolution hierarchy:
- **Diffs are ground truth** for what actually changed (files, lines, behavior)
- **Handoffs are authoritative** for why it changed (intent, decisions, trade-offs)
- **PR titles are summaries** that may be inaccurate — verify against diffs before trusting
- If conflict affects a user-facing claim, note the discrepancy in the entry

**Handoff enrichment gate:** Before proceeding to drafting, confirm you consulted the handoff evidence. If handoffs exist but you haven't incorporated their context, stop and re-read the Handoff Archivist's report. The only valid reason to skip is that the archive directory doesn't exist.

## Step 4: Categorize and Draft

Assign each change to a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) category:

| Category | Use When |
|----------|----------|
| Added | Entirely new feature, capability, file, or component |
| Changed | Modification to existing behavior or interface |
| Deprecated | Feature marked for future removal |
| Removed | Feature, file, or capability deleted |
| Fixed | Bug fix, error correction, regression fix |
| Security | Vulnerability patch, credential handling change |

When ambiguous (a PR that refactors and fixes a bug), create separate entries under each relevant category.

Write entries following these principles:

- **Lead with what changed**, not how: "Add JWT token refresh" not "Modify auth.py to call refresh endpoint"
- **Be specific**: "Fix race condition in ticket ID allocation" not "Fix bug"
- **Name the component**: "Add `/dialogue` skill for multi-turn consultation" not "Add new skill"
- **Reference PRs**: Append `(#N)` when a PR exists
- **One logical change per bullet**: Split multi-change PRs into multiple entries
- **Deprecation entries must include**: what's being deprecated, what replaces it (or "no replacement"), and when removal is planned (version or timeframe). A bare "Deprecate X" without context is unusable

For examples of how handoff context transforms entry quality, read `references/entry-writing.md`.

**Format:** All CHANGELOGs follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):

```markdown
# Changelog

All notable changes to [component name] are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [X.Y.Z] — YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality
```

Versions in reverse chronological order. Empty categories omitted. Dates in ISO format.

## Step 5: Verify Accuracy

Before presenting the CHANGELOG, verify every entry:

**Completeness** (cross-reference with PR Analyst and Git Historian reports):
- [ ] Every merged PR in the version range has a corresponding entry (or explicit justification for omission)
- [ ] Direct-push commits representing meaningful changes are captured (check Git Historian's "Direct Pushes" section)
- [ ] Multi-session features from handoffs are represented as complete features, not fragments (check Handoff Archivist's "Multi-Session Arcs")
- [ ] Handoff archive was consulted (or documented as absent)

**Accuracy** (cross-reference with Git Historian diffs and PR Analyst summaries):
- [ ] Each entry accurately describes what changed (verify against Git Historian's diff analysis, not just commit messages)
- [ ] PR numbers are correct (verify against PR Analyst's report)
- [ ] Version numbers and dates are correct (verify against Git Historian's version boundaries)
- [ ] Categories match the nature of the change
- [ ] Version numbers follow semantic versioning relative to change categories: breaking changes (Removed, Changed with API breaks) warrant a major bump; new features (Added) warrant a minor bump; bug fixes (Fixed) warrant a patch bump. Flag mismatches to the user

**Edit placement (when modifying an existing CHANGELOG):**
- [ ] After any Edit, run `grep -n "^## \|^### "` to confirm the change landed in the intended version block — duplicate section headers across version blocks can silently redirect edits

**Omissions (what NOT to include):**
- Version bumps, dependency updates (unless user-facing)
- Merge commits, CI-only changes
- Internal refactoring with no behavior change (unless significant architectural shift)
- WIP commits superseded by later work

If any check fails, return to the evidence and fix it. Do not present an unverified CHANGELOG.

## Scoped CHANGELOGs

When working on a package-level CHANGELOG within a monorepo:

1. **Scope the team** to that package's directory — git history, PRs, and handoffs should all be filtered to the package path
2. **Select the right granularity** — package changelogs track package-level releases, not repo-level commits. A repo-wide refactor that doesn't change the package's behavior shouldn't appear here
3. **Reference the root CHANGELOG** for repo-wide changes: "See the [root CHANGELOG](../../CHANGELOG.md) for cross-cutting changes"
4. **Don't duplicate** — changes that appear in the root CHANGELOG shouldn't also appear in the package changelog unless they have package-specific impact

## Step 6: Present and Iterate

Present the draft. Explicitly note:
- Entries you're uncertain about (flag with context)
- PRs/changes you intentionally omitted, and why
- Version boundaries you inferred (if no tags exist)
- How many handoffs were consulted and what they contributed

### Audit Mode Output

For audit mode, produce a report instead of a CHANGELOG:

```markdown
# CHANGELOG Audit: [Component Name]

## Summary
[N accuracy issues, N coverage gaps, N missing entries]

## Verified Entries
- [entry] — confirmed by [evidence source]

## Inaccurate Entries
- [entry] — actually [reality per evidence]. Source: [which teammate found it]

## Missing Entries
- [change discovered by team but absent from CHANGELOG]

## Recommended Changes
[Prioritized list of specific edits]
```

After delivering the report, offer to make the changes. Wait for confirmation.

### Refine Mode

Refine mode works only with existing CHANGELOG content — no evidence gathering:
- Focus on: clarity, consistency, categorization, formatting
- Preserve PR references and version structure
- Show proposed changes before applying

## Cleanup

After the CHANGELOG is complete and the user is satisfied:

1. Ask: "Want me to clean up the evidence workspace (`.changelog-workspace/`)?"
2. If yes, remove the workspace directory
3. The agent team cleans up automatically when the lead shuts it down
