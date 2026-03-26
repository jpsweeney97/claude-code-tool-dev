---
name: changelog
description: Create, audit, update, and refine CHANGELOGs with verified accuracy. Orchestrates an agent team to gather evidence from git history, GitHub PRs, and handoff archives in parallel, then cross-references all three sources to produce grounded entries. Trigger on: adding PRs/commits to a changelog, creating a changelog from scratch, checking changelog accuracy against git history, finding what changed between versions or since a date, preparing release documentation, or figuring out which version a feature shipped in. Applies to any request that touches CHANGELOG.md files, version history, or release notes — whether creating, editing, or verifying them.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - ToolSearch
  - TeamCreate
  - TeamDelete
  - SendMessage
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
---

# Changelog Skill

Create and maintain CHANGELOGs with verified accuracy by cross-referencing three evidence sources in parallel. Uses an agent team to deeply mine git history, GitHub PRs, and handoff archives simultaneously — producing entries grounded in evidence, not memory.

**Announce at start:** "I'm using the changelog skill to [create/update/audit] this CHANGELOG."

## Prerequisite

This skill requires agent teams. Verify the feature is enabled before any other work:

Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams for parallel evidence gathering. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential evidence gathering — parallel cross-referencing is the skill's value proposition.

## Constraints

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams required | Hard prerequisite. Do NOT fall back to sequential or Agent-tool-only alternatives. |
| 2 | Sonnet for teammates | Spawn all teammates with `model: "sonnet"`. Lead uses the session's default model. |
| 3 | Teammates lack conversation history | Each teammate starts fresh with only its spawn prompt plus the project's CLAUDE.md/skills. The lead's conversation does NOT carry over — include everything teammates need in their spawn prompts. |
| 4 | One team per session | No nested teams. Clean up before starting a new one. |
| 5 | 3-4 teammates | Git Historian, PR Analyst, Handoff Archivist (always). Changelog Analyst (audit/update only). |

See `references/agent-teams.md` for the full agent teams API reference.

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

## Step 2: Gather Evidence

Gather evidence from git history, GitHub PRs, and handoff archives in parallel using an agent team. Each teammate specializes in one evidence source and writes structured findings to the workspace.

### Phase 1: Setup

1. Create the workspace directory: `{project-root}/.changelog-workspace/evidence/`
2. Verify `.changelog-workspace/` is in `.gitignore`. If absent, add it.

### Phase 2: Create Team and Tasks

If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.

1. **Create the team** via `TeamCreate` with `team_name: "changelog-evidence"` and a description of the changelog task.
2. **Create one task per teammate** via `TaskCreate`. Each task describes the teammate's evidence-gathering mandate and output path. Do NOT set `blockedBy` dependencies — all tasks run in parallel.

| Task | Teammate ID | Output file | Modes |
|------|-------------|-------------|-------|
| Mine git history | `git-historian` | `evidence/git-history.md` | All |
| Mine GitHub PRs | `pr-analyst` | `evidence/pr-analysis.md` | All |
| Mine handoff archive | `handoff-archivist` | `evidence/handoff-context.md` | All |
| Analyze existing CHANGELOG | `changelog-analyst` | `evidence/changelog-analysis.md` | Audit, Update |

### Phase 3: Spawn Teammates

Spawn teammates using the `Agent` tool. The `team_name` parameter is what makes a spawned agent a teammate with messaging, shared tasks, and idle notifications. Without `team_name`, the agent is an isolated subagent with none of those capabilities.

**Design principle:** All teammates access all project files — they are scoped by evidence source, not by directory. Do NOT partition the repository among teammates.

For each teammate, call `Agent` with:
- `team_name`: `"changelog-evidence"` (must match TeamCreate)
- `name`: the teammate ID from the table above — this is the addressing key for all communication
- `model`: `"sonnet"`
- `prompt`: the spawn prompt below

Spawn all teammates in the same message to maximize parallelism. In create mode, spawn 3 (skip `changelog-analyst`). In audit/update mode, spawn all 4. Do NOT start your own evidence gathering before all teammates are spawned — your job is to coordinate and then reconcile.

#### Git Historian

```
Mine the complete git history for this project. Write findings to {workspace}/evidence/git-history.md.

Scope: {scope-path} — version range: {version-range}

Tasks:
1. **Version boundaries** — identify all git tags in scope. Map each to date and commit. Classify: version tags (v1.2.3, 1.0.0, release-1.2) are boundaries; deployment tags (deploy/prod, staging-2024-01) are not. If no version-like tags exist, note this
2. **Commit timeline** — all commits in range, scoped to path. Capture: hash, date, message, author. For merge commits, also capture branch name. Over 500 commits: group by file/directory and summarize patterns. Over 2000: message the lead to narrow scope
3. **Diff analysis** — for each version boundary (or logical grouping if no tags), summarize: files added/modified/deleted with nature of changes
4. **Direct pushes** — commits pushed directly (not via PR merge). These won't appear in PR data
5. **Superseded work** — WIP or fixup commits later replaced. Flag to prevent duplicate entries

When you find direct-push commits with no merge commit, message pr-analyst. When you find commits referencing session work, message handoff-archivist with the date range.

Structure output as: ## Version Boundaries, ## Changes by Version, ## Direct Pushes (no PR), ## Superseded Work
```

#### PR Analyst

```
Mine all GitHub pull requests for this project. Write findings to {workspace}/evidence/pr-analysis.md.

Scope: {scope-path} — date range: {date-range}

Before mining PRs, verify `gh` is available and authenticated. If `gh` fails (no GitHub remote, not authenticated, or API error), write a note explaining the failure and stop — the Git Historian's data will serve as primary structure instead.

Tasks:
1. **Merged PRs** — all merged PRs in date range. Capture: number, title, merge date, description summary, labels, files changed. Use `gh pr list --state merged --json number,title,mergedAt,body,labels,files` and `gh pr view <n> --json title,body,files,commits`
2. **Logical grouping** — PRs that are part of the same feature (multi-PR features, PR with follow-up fixes)
3. **Multi-change PRs** — PRs with multiple distinct changes bundled. Each should become a separate entry
4. **PR quality assessment** — rate how well title/description summarizes actual change. For squash-merged PRs, the PR body and diff are primary evidence, not the commit list
5. **Linked issues** — capture issues providing context about user-facing impact

Filter to PRs touching files in scope path. If no merged PRs found, note this as a valid finding (all changes were direct pushes).

When you find PRs with vague titles or no description, message handoff-archivist — handoffs often contain the intent behind these changes.

Structure output as: ## PRs by Date (newest first), ## Logical Groups, ## Missing Context
```

#### Handoff Archivist

```
Mine the handoff archive for session context, decisions, and intent behind changes. Write findings to {workspace}/evidence/handoff-context.md.

Scope: Project {project-name} — date range: {date-range}

The handoff archive lives at ~/.claude/handoffs/{project-name}/.archive/. Filenames follow YYYY-MM-DD_HH-MM_<title-slug>.md.

If the archive directory doesn't exist, write a note explaining the gap and stop — there's no handoff data to mine.

Tasks:
1. **Locate relevant handoffs** — filter by date range and scope. For large archives (50+), grep YAML frontmatter `files:` field
2. **Extract high-value sections** — priority order: Changes (always), Decisions (non-trivial changes), Goal (non-trivial changes), In Progress (partial work → [Unreleased]). Ignore: Learnings, Risks, Gotchas, Codebase Knowledge, Context, User Preferences, References
3. **Build enrichment map** — for each handoff: what was done, why, user-facing impact. Map to corresponding PR(s)/commit(s)
4. **Flag multi-session arcs** — handoffs forming a larger feature. These should be one entry, not fragments

When you find sessions referencing specific PRs or commits, message git-historian and pr-analyst. When you find multi-session arcs, message both.

Structure output as: ## Handoffs Found, ## Enrichment Map, ## Multi-Session Arcs, ## Deferred Work (exclude from changelog)
```

#### Changelog Analyst (audit/update modes only)

```
Analyze the existing CHANGELOG and extract every factual claim for verification. Write findings to {workspace}/evidence/changelog-analysis.md.

File: {changelog-path}

Tasks:
1. **Extract claims** — for every entry: what changed, when, in which version, with which PR reference
2. **Create verification checklist** — for each claim, note what evidence would confirm or deny it
3. **Style analysis** — entry length, verb tense, specificity level, component naming, PR references. The lead will match this style
4. **Coverage map** — version ranges and date ranges already documented
5. **Gap detection** — for update mode: where new entries should be inserted

Share your claims checklist with specific teammates. Message git-historian about commit/tag claims, pr-analyst about PR number claims, handoff-archivist about feature/decision claims. Use targeted messages, not broadcast — broadcast costs scale with team size.

Structure output as: ## Claims by Version, ## Style Profile, ## Coverage Map, ## Insertion Points (update mode)
```

### Phase 4: Monitor Completion

**Primary signal:** idle notifications from the team system. When a teammate finishes and goes idle, the lead receives a notification. Peer DM summaries appear in idle notifications — use these as reconciliation input.

**Completion rule:** Wait for all idle notifications (3 in create mode, 4 in audit/update mode) before proceeding to reconciliation. Do NOT start reconciliation early — partial evidence produces unreliable entries.

**Verification:** After all idle notifications, verify each expected output file exists in the workspace via `Glob` or `Read`.

**Timeout:** If no idle notifications or task status changes (confirmed via `TaskGet`) arrive for 5 minutes, proceed with available findings. "Activity" means: idle notification received, or a task moving to `completed`.

**Partial completion:** Always proceed with available findings rather than blocking. Note which teammates failed and why in your reconciliation — a changelog with known evidence gaps is better than no changelog.

**PR Analyst failure:** If `gh` was unavailable and the PR Analyst produced only a failure note, this is expected — use Git Historian's data as primary structure instead.

## Step 3: Reconcile Evidence

After all teammates complete, read all evidence reports. Cross-reference into a unified change list:

1. **Start with PRs as primary structure** — each merged PR typically represents one logical change with a clean summary. If no PRs exist (the PR Analyst reported none or `gh` was unavailable), use git history as primary structure instead — group commits by logical change
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

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop — do not fall back |
| TeamCreate fails | Phase 2 step 1 | Hard stop — cannot proceed without team |
| Teammate spawn fails | Phase 3 | Log, continue with remaining. All fail = hard stop |
| Teammate timeout | No activity for 5 min | Treat as failed, proceed with available findings |
| Missing output file | Phase 4 verification | Log as evidence gap in reconciliation |
| `gh` unavailable | PR Analyst reports failure | Expected — use Git Historian as primary structure |
| No handoff archive | Handoff Archivist reports absence | Expected — proceed without handoff enrichment |
| Stale workspace | Phase 1 setup | Warn user, offer: archive / remove / abort |
| TeamDelete fails | Cleanup step 2 | Orphaned teammates still active — report degraded state, proceed with workspace cleanup |

## Cleanup

After the CHANGELOG is complete and delivered, follow the cleanup resilience protocol from `references/agent-teams.md`. These are transient working artifacts — do not ask the user about cleanup.

1. **Shutdown loop** — for each teammate, send up to 3 shutdown requests with escalating context:
   - Attempt 1: `{type: "shutdown_request", reason: "CHANGELOG complete"}`
   - Attempt 2 (if no idle after 60s): "All evidence gathering is complete, findings have been saved. Please shut down."
   - Attempt 3 (if no idle after 60s): "Session ending. Cleanup requires all teammates to shut down. This is the final request."
   - If no idle after 30s: classify as **orphaned** with reason.
2. **TeamDelete** — call `TeamDelete`. If it fails (orphaned teammates still active), report degraded state to user:
   "Team cleanup partially failed: [N] teammate(s) did not shut down ([names]). Team resources may remain at `~/.claude/teams/changelog-evidence/`. These will be cleaned up when a new team is created, or remove manually."
3. **Workspace** — remove `.changelog-workspace/`. Workspace cleanup is independent of team cleanup — always attempt it regardless of TeamDelete outcome.
