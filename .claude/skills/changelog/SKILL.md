---
name: changelog
description: >-
  Create, audit, update, and refine CHANGELOGs with verified accuracy. Trigger on: adding
  PRs/commits to a changelog, creating a changelog from scratch, checking changelog accuracy
  against git history, finding what changed between versions or since a date, preparing release
  documentation, or figuring out which version a feature shipped in. Applies to any request that
  touches CHANGELOG.md files, version history, or release notes — whether creating, editing, or
  verifying them. Cross-references git log, GitHub PRs, and handoff archives for accuracy.
---

# Changelog

Create and maintain CHANGELOGs with verified accuracy by cross-referencing three evidence sources.

## Operations

Detect which operation the user needs from context:

| Operation | Trigger | What Happens |
|-----------|---------|--------------|
| **Create** | No CHANGELOG exists, or user asks to create one | Build from scratch using full history |
| **Update** | CHANGELOG exists, user asks to add recent changes | Add entries since last documented version |
| **Audit** | User asks to check, verify, or audit the changelog | Cross-reference existing entries against sources |
| **Refine** | User asks to improve wording, recategorize, fix formatting | Edit existing entries without gathering new evidence |

If ambiguous, ask: "I see an existing CHANGELOG. Do you want me to **update** it with recent changes, or **audit** it for accuracy?"

## Sources of Evidence

Every changelog entry must trace back to at least one evidence source:

| Source | What It Provides | How to Access |
|--------|-----------------|---------------|
| **Git history** | Commits, tags, diffs, merge commits | `git log`, `git diff`, `git tag` |
| **GitHub PRs** | Titles, descriptions, labels, linked issues | `gh pr list`, `gh pr view` |
| **Handoff archive** | Session context, decisions, rationale, deferred work | Files in handoff archive directory |

The handoff archive lives at `~/.claude/handoffs/<project-name>/.archive/` where `<project-name>` is derived from the project's root directory name. If the archive directory doesn't exist, skip this source and note it.

### Why three sources matter

- **Git commits** are complete but noisy — merge commits, WIP, fixups all appear
- **GitHub PRs** are curated summaries but may bundle multiple logical changes
- **Handoff files** capture intent and decisions that neither commits nor PRs preserve

No single source is sufficient. Cross-referencing catches omissions and improves entry quality.

## Format: Keep a Changelog

All CHANGELOGs follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

### Deprecated
- Features that will be removed

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Vulnerability fixes
```

**Rules:**
- Versions in reverse chronological order (newest first)
- Each version gets a date in ISO format
- Empty categories are omitted (don't include `### Removed` if nothing was removed)
- Entries are concise but specific — name the component, feature, or file affected
- Reference PR numbers where applicable: `(#42)`
- Group related entries under a single bullet when they're part of the same logical change

## Workflow

### Step 1: Identify Scope

Determine what the CHANGELOG covers:

1. **Which component?** A specific package, plugin, or the whole repo?
2. **What version range?** Everything, or since a specific version/tag/date?
3. **Where does the CHANGELOG live?** Find existing file or determine where to create it.

For package-level CHANGELOGs, scope git history to the package directory:
```bash
git log --oneline -- packages/plugins/<name>/
```

### Step 2: Gather Evidence

Collect evidence from all three sources. Use subagents for parallel gathering when context is over ~50k tokens, otherwise gather inline.

#### 2a. Git History

```bash
# All commits (or since a tag/date for updates)
git log --oneline --since="YYYY-MM-DD" -- <scope-path>

# Tags for version boundaries
git tag --list | sort -V

# Diff between versions for detailed changes
git diff <old-tag>..<new-tag> -- <scope-path>

# Merge commits (often correspond to PRs)
git log --merges --oneline -- <scope-path>
```

#### 2b. GitHub PRs

```bash
# Merged PRs (adjust date range as needed)
gh pr list --state merged --limit 100 --json number,title,mergedAt,body,labels

# Detailed view of a specific PR
gh pr view <number> --json title,body,files,commits
```

Filter to PRs that touch the scope path. PR descriptions often contain the best summary of what changed and why.

#### 2c. Handoff Archive (mandatory)

Handoff files are structured session records with consistent sections. They capture intent, decisions, and context that git and PRs don't preserve. Skipping this source produces mechanically accurate but shallow entries — the difference between "Add comparative posture" and "Add comparative posture for structured trade-off analysis in multi-phase dialogues."

**Locating the archive:**

```bash
# Derive project name from repo root directory
PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel)")
ARCHIVE_DIR=~/.claude/handoffs/$PROJECT_NAME/.archive

# List handoff files, filter by date range
ls "$ARCHIVE_DIR" | grep "^2026-03"  # adjust date prefix to match scope
```

If the archive directory doesn't exist, note this gap explicitly and proceed with git + PRs only.

**Filtering relevant handoffs:**

Handoff filenames follow `YYYY-MM-DD_HH-MM_<title-slug>.md`. Use two filters:

1. **Date range** — match the version range you're documenting
2. **Title keywords** — scan for component names, feature names, or PR numbers in the filename

For large archives (50+ files in range), grep the YAML frontmatter `files:` field to find handoffs that touched files in your scope:

```bash
grep -l "packages/plugins/<name>" "$ARCHIVE_DIR"/2026-03-*.md
```

**Extracting CHANGELOG-relevant content:**

Handoff files have a fixed section structure. These 5 sections have the highest CHANGELOG value:

| Section | CHANGELOG Value | What to Extract |
|---------|----------------|-----------------|
| **## Changes** | Direct implementation record — per-file changes with purpose, commit hashes, patterns followed | Raw material for entries. Each subsection typically maps to one CHANGELOG bullet. |
| **## Decisions** | The "why" behind changes — alternatives rejected, trade-offs accepted, confidence levels | Transforms mechanical entries into meaningful ones. Use to write entries that explain impact, not just mechanics. |
| **## Goal** | Session scope and stakes — what the session set out to accomplish, success criteria | Groups changes into logical features. The "Connection to project arc" subfield shows how the session fits into a larger effort. |
| **## In Progress** | Completion status — "clean stopping point" vs "work in flight" | Tells you whether changes are done or partial. Partial work should go under `[Unreleased]`, not a version. |
| **## Next Steps** | Deferred work — what comes after this session | Work listed here should NOT appear in the changelog yet. Use as a negative filter. |

Ignore: Learnings, Risks, Gotchas, Codebase Knowledge, Context, User Preferences, References — these are session-continuation context, not CHANGELOG material.

**Reading strategy:** Don't read entire handoff files. Extract targeted sections:

```bash
# Extract the Changes section from a handoff
awk '/^## Changes/{flag=1;next}/^## /{flag=0}flag' "$ARCHIVE_DIR/<filename>.md"
```

For each relevant handoff, read **Changes** first (always), then **Decisions** and **Goal** if the changes are non-trivial (new features, architectural shifts, complex bug fixes).

### Step 3: Reconcile and Categorize

Cross-reference the three sources to build a complete picture:

1. **Start with PRs** as the primary structure — each merged PR typically represents one logical change
2. **Fill gaps from commits** — changes that were pushed directly without a PR
3. **Enrich from handoffs** — for every entry describing a new feature, architectural change, or non-trivial fix, check whether a handoff exists for the session that implemented it. If a handoff's **Decisions** section explains why an approach was chosen, that context should inform the entry's wording. If a handoff's **Goal** section describes a multi-session arc, group related entries as a single logical feature rather than listing fragments.

**Handoff enrichment gate:** Before moving to Step 4, confirm that you have consulted the handoff archive. If handoffs exist for the scope and date range but you haven't read any, stop and go back to Step 2c. The only valid reason to skip handoffs is that the archive directory doesn't exist or contains no files matching the scope.

For each change, determine the Keep a Changelog category:

| Category | Use When |
|----------|----------|
| Added | Entirely new feature, capability, file, or component |
| Changed | Modification to existing behavior or interface |
| Deprecated | Feature marked for future removal |
| Removed | Feature, file, or capability deleted |
| Fixed | Bug fix, error correction, regression fix |
| Security | Vulnerability patch, credential handling change |

**When categorization is ambiguous:** A PR titled "refactor auth module" that also fixes a bug is both Changed and Fixed. Create separate entries under each category rather than forcing one.

### Step 4: Draft Entries

Write changelog entries following these principles:

- **Lead with what changed**, not how: "Add JWT token refresh" not "Modify auth.py to call refresh endpoint"
- **Be specific**: "Fix race condition in ticket ID allocation" not "Fix bug"
- **Name the component**: "Add `/dialogue` skill for multi-turn consultation" not "Add new skill"
- **Reference PRs**: Append `(#N)` when a PR exists for the change
- **One logical change per bullet**: If a PR contains multiple distinct changes, split into multiple entries

**Using handoff context to improve entries:**

Handoff-enriched entries describe impact and intent, not just mechanics. Compare:

| Without handoff context | With handoff context |
|------------------------|---------------------|
| Add comparative posture | Add `comparative` posture for structured trade-off analysis in multi-phase dialogues |
| Fix payload collision bug | Fix payload collision where guard hook's atomic inject overwrites new payloads with stale data between stages |
| Add phase tracking fields | Add phase-local convergence — track posture phases in `ConversationState` so each dialogue phase has independent convergence detection |

The handoff's **Decisions** section explains *why* (trade-offs, alternatives rejected). The **Goal** section explains *what for* (stakes, connection to project arc). Use both to write entries that a reader can understand without reading the code.

### Step 5: Verify Accuracy

This is the critical gate. Before presenting the CHANGELOG to the user, verify every entry:

**Completeness check:**
- [ ] Every merged PR in the version range has a corresponding entry (or explicit justification for omission)
- [ ] Direct-push commits that represent meaningful changes are captured
- [ ] Multi-session features from handoffs are represented as complete features, not fragments
- [ ] Handoff archive was consulted (or documented as absent) — note how many handoffs were read and which sections were extracted

**Accuracy check:**
- [ ] Each entry accurately describes what changed (verify against actual diffs, not just commit messages)
- [ ] PR numbers are correct
- [ ] Version numbers and dates are correct
- [ ] Categories match the nature of the change

**Omission check — what NOT to include:**
- Version bumps, dependency updates (unless user-facing)
- Merge commits, CI-only changes
- Internal refactoring with no behavior change (unless significant architectural shift)
- WIP commits that were superseded by later work

If any check fails, go back to Step 2 and gather the missing evidence. Do not present an unverified CHANGELOG.

### Step 6: Present and Iterate

Present the draft to the user. Explicitly note:
- Any entries you're uncertain about (flag with context)
- Any PRs/changes you intentionally omitted, and why
- Any version boundaries you inferred (if no tags exist)

## Operation-Specific Notes

### Create Mode

When building from scratch:
- Determine version boundaries from git tags, or ask the user
- If no tags exist, consider the full history as `[0.1.0]` or ask the user for versioning
- Start from the earliest relevant commit and work forward
- For large histories (100+ commits), use subagents to gather evidence in parallel by time period

### Update Mode

When adding to an existing CHANGELOG:
- Read the existing CHANGELOG first to understand the style, granularity, and conventions used
- Identify where the last entry ends (latest version date, or `[Unreleased]` section)
- Gather evidence only for changes since that point
- Match the existing style — if entries are terse, keep new ones terse; if detailed, match that

### Audit Mode

When verifying an existing CHANGELOG:
- Read the full CHANGELOG
- For each version section, gather the evidence that should correspond to it
- Report: missing entries, inaccurate descriptions, miscategorized items, wrong PR references
- Present findings as a structured report before making changes
- Only modify the CHANGELOG after user approves the audit findings

### Refine Mode

When improving existing entries:
- Do NOT gather new evidence — work only with what's in the CHANGELOG
- Focus on: clarity, consistency, categorization, formatting
- Preserve PR references and version structure
- Show a diff of proposed changes before applying

## Red Flags — Stop and Verify

If you notice any of these, pause and investigate before proceeding:

| Red Flag | What To Do |
|----------|------------|
| PR exists but no corresponding changelog entry | Verify it's a meaningful change, then add an entry |
| Changelog entry has no matching PR or commit | Verify it's real — may be from a squashed merge or direct push |
| Handoff mentions a feature but CHANGELOG doesn't | Check if it was actually merged or is still in progress |
| Version date doesn't match any tag or PR merge | Investigate — may be a typo or incorrect version boundary |
| Entry describes behavior that contradicts the diff | The entry is wrong — rewrite from the diff |
