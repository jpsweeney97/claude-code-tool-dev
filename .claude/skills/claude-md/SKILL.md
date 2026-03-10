---
name: claude-md
description: Create, audit, and update CLAUDE.md files with codebase-grounded accuracy. Orchestrates an agent team to explore the project from five perspectives — toolchain, architecture, conventions, gotchas, and existing documentation — then produces CLAUDE.md content verified against reality. Trigger on "create a CLAUDE.md", "write a CLAUDE.md", "audit CLAUDE.md", "check CLAUDE.md", "improve CLAUDE.md", "update CLAUDE.md", "this project needs a CLAUDE.md", "write project instructions for Claude", "set up Claude for this project" (when about project instruction files, not hooks/MCP/settings), or any request about CLAUDE.md quality, accuracy, or completeness. Distinct from README (introducing the project), handbook (operating the system), and changelog (tracking changes). For quick session-scoped updates, use /revise-claude-md.
---

# CLAUDE.md

Create, audit, or update CLAUDE.md files — the project instruction files that tell Claude how to work effectively in a codebase. CLAUDE.md is to Claude what onboarding docs are to a new team member: the fastest path from "I've never seen this repo" to "I know how things work here."

Unlike README (introducing the project to humans) or handbook (operating the system), CLAUDE.md captures operational knowledge that prevents wasted context: which commands to run, where things live, what conventions to follow, and what will silently break if you don't know about it.

## Prerequisite

This skill requires agent teams. Before proceeding, verify the feature is enabled:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

If not enabled, tell the user: "This skill uses agent teams for deep parallel codebase exploration. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json env block, then restart the session." Do not fall back to a shallow approach — the quality difference between solo exploration and parallel multi-perspective investigation is the entire point.

## Modes

| Mode | When | What happens |
|------|------|-------------|
| **Create** | No CLAUDE.md exists, or user says "create a CLAUDE.md" | Full exploration → section selection → write |
| **Audit** | CLAUDE.md exists, user says "audit", "check", "is this accurate" | Full exploration → compare claims vs reality → report |
| **Update** | CLAUDE.md exists, user says "update", "improve", "fix" | Full exploration → compare → rewrite sections that drifted |

Detect the mode from the user's request. If ambiguous, ask: "Do you want me to create a new CLAUDE.md, audit the existing one for accuracy, or update it?"

## Scope Check

Before starting, confirm the request is about CLAUDE.md:

**Redirect signals** — the request focuses on:

| Request | Redirect |
|---------|----------|
| "Write a README" / document for users | README skill |
| "Create operational docs" / write runbooks | Handbook skill |
| "Document what changed" / release notes | Changelog skill |
| "Remember this for next time" / session note | /revise-claude-md |

**CLAUDE.md signals** — the request focuses on:
- Project instructions for Claude / AI assistants
- Setting up Claude to work in a codebase
- Commands, conventions, or gotchas that Claude should know
- Quality, accuracy, or completeness of existing CLAUDE.md files

Proceed with this skill when CLAUDE.md signals are present.

## Step 1: Determine Scope

1. **Project root**: Locate the codebase root (`.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`)
2. **Existing CLAUDE.md files**: Check `.claude/CLAUDE.md`, root `CLAUDE.md`, and nested CLAUDE.md files
3. **Project type**: Classify — library, CLI, web app, API, monorepo, plugin, or other
4. **Sub-packages**: For monorepos, identify packages that might benefit from their own CLAUDE.md

**Scope boundary:** This skill creates project-level CLAUDE.md files (checked into the repo, shared by the team). Global user-level files (`~/.claude/CLAUDE.md`) are personal preferences — out of scope.

For audit/update modes, read the existing CLAUDE.md file(s) before launching the exploration team so teammates know what claims to verify.

## Step 2: Launch Exploration Team

Create an agent team with 5 teammates. Agent teams are coordinated via natural language — describe the team structure, teammates, and tasks to the lead. The lead handles spawning, task assignment, and coordination internally. Each teammate has a distinct exploration mandate and reports findings to dedicated files in the workspace.

**Critical: known failure modes to guard against:**
- **Do not substitute the Agent tool for agent teams.** If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` and use it. The Agent tool with `run_in_background` looks similar but lacks teammate-to-teammate messaging, coordinated completion detection, and shared task state — leading to polling races and lost coordination. Agent teams and the Agent tool are not interchangeable.
- The lead may start doing exploration work itself instead of waiting for teammates. If you catch yourself exploring the codebase before teammates finish, stop. Your job is to coordinate, then synthesize.
- The lead may declare the team finished before all teammates complete. Wait for all 5 idle notifications before proceeding to synthesis.
- Task status can lag — a teammate may finish work without marking the task complete. Check the workspace for output files as a secondary completion signal.

Tell the lead to create these teammates with these prompts:

### Teammate 1: Toolchain Scout

> Explore the project's toolchain and development workflow. Write findings to `.claude-md-workspace/exploration/toolchain.md`.
>
> Tasks:
> 1. **Package manager** — npm, yarn, pnpm, uv, pip, cargo, go modules, etc.
> 2. **Build commands** — run them if possible to verify they work
> 3. **Test commands** — test runner, coverage tools, test patterns
> 4. **Lint/format tools** — what's configured (eslint, prettier, ruff, rustfmt, etc.)
> 5. **CI/CD configuration** — what pipelines exist, what they run
> 6. **Environment variables** — required vars, .env patterns, setup steps
> 7. **Install/setup steps** — what a new developer needs to do first
> 8. **Scripts** — custom scripts in package.json, Makefile, scripts/, etc.
>
> For each command, verify it exists (check package.json scripts, Makefile targets, pyproject.toml scripts). Mark unverifiable commands as [UNVERIFIED].
>
> When you discover build constraints or quirky setup requirements, message the Gotcha Hunter — these are often gotchas worth documenting. When you find environment variables that affect runtime behavior, message the Convention Miner in case they imply coding patterns.
>
> Format:
> ```
> ## Commands
> | Command | Purpose | Verified |
> ...
> ## Environment
> ...
> ## Setup Steps
> ...
> ```

### Teammate 2: Codebase Cartographer

> Map the project's architecture and structure. Write findings to `.claude-md-workspace/exploration/architecture.md`.
>
> Tasks:
> 1. **Directory tree** — top-level layout (depth 2-3, excluding node_modules, .git, __pycache__) with annotations on what each directory contains
> 2. **Key files** — entry points, main config files, important modules
> 3. **Module relationships** — what depends on what
> 4. **Project type classification** — library, CLI, web app, API, monorepo, plugin. Evidence your classification with specific files (package.json bin field, setup.py entry_points, plugin manifest, workspace config)
> 5. **Package inventory** — for monorepos: all sub-packages with paths and purposes
> 6. **Framework(s) and language(s)** — what's used and their roles
>
> Focus on what Claude needs to navigate the codebase — not exhaustive inventory.
>
> When you discover unconventional directory layouts or generated code, message the Gotcha Hunter. When you find config files that imply coding patterns (tsconfig strictness, eslint rules), message the Convention Miner.
>
> Format:
> ```
> ## Project Type
> ...
> ## Directory Structure
> <tree>
> ## Key Files
> ...
> ## Module Relationships
> ...
> ```

### Teammate 3: Convention Miner

> Extract the coding conventions actually used in this project. Write findings to `.claude-md-workspace/exploration/conventions.md`.
>
> Tasks:
> 1. **Naming** — snake_case, camelCase, PascalCase for files, variables, functions, classes
> 2. **Import patterns** — absolute vs relative, grouping order, barrel files
> 3. **Error handling** — exceptions, Result types, error codes, logging patterns
> 4. **Test patterns** — file naming (*.test.ts, test_*.py), structure, fixtures, mocks
> 5. **Type usage** — strict types, any/unknown, type annotations, generics
> 6. **Comment style** — JSDoc, docstrings, inline — when used vs not
> 7. **Module structure** — one-class-per-file, barrel exports, feature folders
> 8. **Framework-specific patterns** — component structure, hook patterns, middleware
>
> Read 5-8 representative source files across different parts of the codebase. Extract ACTUAL patterns from code — don't guess from config files alone. When patterns conflict across the codebase, note both and which is more common.
>
> When you find conventions that contradict existing CLAUDE.md claims (in audit/update modes), message the Documentation Auditor with the specific contradiction and evidence. When you find patterns that would surprise a newcomer, message the Gotcha Hunter.
>
> Format:
> ```
> ## Naming
> ...
> ## Code Organization
> ...
> ## Error Handling
> ...
> ## Testing Patterns
> ...
> ## Framework Conventions
> ...
> ```

### Teammate 4: Gotcha Hunter

> Find non-obvious patterns, quirks, and potential pitfalls. Write findings to `.claude-md-workspace/exploration/gotchas.md`.
>
> Tasks:
> 1. **Configuration quirks** — settings that must be specific, non-obvious defaults
> 2. **Ordering dependencies** — things that must happen before other things
> 3. **Environment-specific issues** — dev vs prod vs CI differences
> 4. **Common mistakes** — search for FIXME, HACK, WORKAROUND, XXX comments
> 5. **Implicit dependencies** — services that must be running, databases that need seeding
> 6. **File path gotchas** — case sensitivity, symlinks, generated files not to edit
> 7. **Build/test gotchas** — sequential tests, version-specific builds
> 8. **Recent bug patterns** — search recent commit messages and PR descriptions
>
> Also check:
> - README warnings or "important" sections
> - Contributing guides
> - Any docs that mention caveats
>
> Each gotcha: what it is, why it matters, what to do about it.
>
> When you find gotchas related to specific commands, message the Toolchain Scout to verify them. When you find gotchas related to the project structure, message the Codebase Cartographer.
>
> Format as flat list:
> ```
> - **<title>**: <explanation>
> ```

### Teammate 5: Documentation Auditor

The auditor's prompt depends on the mode.

**Create mode:**

> Scan existing documentation for CLAUDE.md-worthy information. Write findings to `.claude-md-workspace/exploration/existing-docs.md`.
>
> Tasks:
> 1. **Documentation inventory** — README.md (and nested READMEs), CONTRIBUTING.md, docs/ directory, .github/ templates and workflows, existing CLAUDE.md files (at any level), config files (.editorconfig, .prettierrc, .eslintrc, tsconfig.json, pyproject.toml)
> 2. **CLAUDE.md-worthy extraction** — information that belongs in a CLAUDE.md but currently lives elsewhere: build/test instructions buried in README, coding standards in CONTRIBUTING.md, architecture notes in docs/, workflow patterns in CI configs
> 3. **Source attribution** — note where each piece was found so we can decide whether to consolidate or cross-reference
>
> Don't duplicate — reference the source.
>
> When you find documented conventions, message the Convention Miner so they can verify against actual code. When you find documented gotchas, message the Gotcha Hunter so they can verify they're still current.

**Audit/Update mode:**

> Evaluate existing CLAUDE.md files for accuracy and completeness. Write findings to `.claude-md-workspace/exploration/audit.md`.
>
> For each CLAUDE.md file found:
> 1. **Verify every command** — does it exist in package.json/Makefile/pyproject.toml?
> 2. **Verify every file path** — does it still exist?
> 3. **Verify architecture claims** — does the directory structure match?
> 4. **Check for staleness** — removed dependencies, old tool versions, deprecated patterns. Cross-reference doc file ages against source file ages
> 5. **Check for gaps** — important project knowledge not captured
> 6. **Check for redundancy** — same info repeated across multiple CLAUDE.md files
> 7. **Check language quality** — concise, specific, actionable?
>
> Share your claims checklist with specific teammates for verification. Message the Toolchain Scout about command claims, the Codebase Cartographer about file path and architecture claims, the Convention Miner about code style claims, and the Gotcha Hunter about gotcha claims. Use targeted messages, not broadcast.
>
> Format:
> ```
> ## <file path>
> ### Accurate
> - <verified content>
> ### Inaccurate
> - <what's wrong, what it should say>
> ### Missing
> - <what should be added>
> ### Stale
> - <what's outdated>
> ### Improvement Opportunities (update mode)
> - <sections that could be clearer, better structured, or more concise>
> ```

### Workspace Setup

Before spawning the team, create the workspace directory:

```
<project-root>/.claude-md-workspace/exploration/
```

Tell each teammate to write their findings to this directory. Cleanup is handled automatically after completion (see Cleanup section).

**Small projects:** If the Cartographer reports fewer than 20 source files and no tests, the lead should consolidate remaining work rather than waiting for all teammates to produce near-empty reports. Dismiss teammates whose domain has no content and proceed to synthesis with whatever reports exist.

### Task Structure

Instruct the lead to create tasks with these dependencies:

1. All 5 exploration tasks (independent, no dependencies between them)
2. "Synthesize exploration findings" (depends on all 5 completing)
3. "Select CLAUDE.md sections" (depends on synthesis)
4. "Write CLAUDE.md" (depends on section selection)

**Important:** Explicitly tell the lead: "Wait for all teammates to complete their exploration tasks before starting synthesis. Do not begin synthesis, section selection, or writing until all 5 exploration reports exist in the workspace."

## Step 3: Reconcile Findings

Teammates do not inherit the lead's conversation history — they start fresh with only their spawn prompt and the project's CLAUDE.md/skills. This is why each teammate prompt above is self-contained with explicit deliverables and output paths. Do not assume teammates know the user's original request or the CLAUDE.md mode.

After all teammates complete, read all exploration files and synthesize:

1. **Confirm project type** — does the Cartographer's classification match what the Toolchain Scout and Convention Miner found?
2. **Cross-reference commands** — do the Toolchain Scout's commands align with what the Cartographer found in build system config?
3. **Resolve conflicts** — when teammates disagree (e.g., different naming conventions observed), investigate which is authoritative
4. **Verify gotchas** — do the Gotcha Hunter's findings hold up against other teammates' evidence?
5. **(Audit/Update) Build claims verdict** — go through the Documentation Auditor's claims checklist. Mark each claim as confirmed, outdated, or wrong based on other teammates' findings
6. **Reject unsupported claims** — every path, command, and convention in the final CLAUDE.md must trace to teammate evidence
7. **Identify coverage gaps** — topics that no teammate found information on but that the section templates expect. These become omissions (if optional) or "Unknown" markers (if important for safety), never fabricated content

**When sources conflict:** Evidence sources may disagree — a config file specifies one convention but actual code follows another. Resolution hierarchy:
- **Actual code is ground truth** for what conventions are in practice
- **Config files are authoritative** for what conventions are intended (linter rules, tsconfig settings)
- **Documentation is secondary** — verify against code before trusting
- **Comments are weakest** — may be stale; corroborate before citing

If actual practice conflicts with config (e.g., code uses camelCase but linter enforces snake_case), note both in the CLAUDE.md — the intended convention and the current drift.

## Step 4: Select Sections

Based on exploration findings, decide which sections to include. Read `references/section-templates.md` for the section catalog with selection criteria.

Determine which optional sections to include based on whether the exploration team found substantive content. An empty "Code Style" section is worse than no "Code Style" section.

**Gate:** Present the proposed section list to the user before writing. Example:

> Based on exploration, I recommend these sections for your CLAUDE.md:
> - Project Overview (always)
> - Commands (found 8 build/test/lint commands)
> - Architecture (monorepo with 4 packages)
> - Code Style (strong conventions: snake_case, absolute imports, pytest fixtures)
> - Gotchas (found 3 non-obvious patterns)
>
> Skipping: Environment (no env vars needed), Key Files (entry points are conventional)
>
> Does this look right?

Wait for confirmation before proceeding.

## Step 5: Write

### Create Mode

Write the CLAUDE.md following the section templates from `references/section-templates.md`. Every claim must trace to exploration evidence.

**Placement:** Write to `.claude/CLAUDE.md` (the standard project-level location). For monorepos where packages need their own CLAUDE.md, write those too — but only if the package has conventions or commands that differ from the root (see Nested CLAUDE.md Files section).

**Voice:** CLAUDE.md speaks to Claude. Use imperative mood ("Run tests with...", "Use snake_case for..."). Be direct and dense. Every line must earn its context window cost.

**Ground every claim in exploration findings.** Do not invent commands, conventions, or configuration options that the exploration team didn't discover. If a section in the template has no corresponding exploration data, either:
- Omit the section (if optional)
- Write "Unknown — exploration did not find evidence for this" (if important for safety)

**No placeholders:** Never write TODO stubs. If a section can't be filled with real data, omit it entirely.

**Conciseness check:** After drafting, reread the full file. Delete any line where removing it would not cause Claude to make a mistake. Prefer tables over prose. Prefer one line over three.

### Audit Mode

Produce a structured audit report, not a rewritten CLAUDE.md:

```markdown
# CLAUDE.md Audit: <project name>

## Summary
<1-2 sentence overall assessment>

## Findings

### Accurate
- <verified content, grouped by section> — confirmed by <evidence>

### Inaccurate
- <wrong content> — actually <reality per evidence>

### Stale
- <outdated content> — current state: <what's true now>

### Missing
- <important knowledge not captured> — discovered by <teammate>

### Redundant
- <duplicated across files, with locations>

## Recommendations
<prioritized list of specific changes, ordered by impact>
```

After delivering the report, offer to make the changes. Wait for confirmation before applying edits.

### Update Mode

**For targeted updates**, you may not need all 5 teammates. Launch only those whose domain overlaps with the change (e.g., new build tool → Toolchain Scout + Documentation Auditor).

Preserve the existing CLAUDE.md's structure and voice where it's accurate. Apply improvements to sections that drifted:
- Fix inaccuracies (replace wrong commands, update paths)
- Remove stale content
- Add missing sections using section templates
- Consolidate redundant content
- Tighten language — apply the project's writing principles if a `docs/references/writing-principles.md` or similar exists

**Structural mismatch detection:** If the CLAUDE.md emphasizes the wrong aspects for the project type (e.g., heavy architecture documentation for a simple CLI where commands are what matters most), flag this to the user: "The existing CLAUDE.md is structured for a [X]-style project but this is actually a [Y]. Want me to restructure it, or just update the content within the current structure?"

Show a diff summary of what changed and why before delivering.

## Step 6: Verify

Before presenting the final result:

1. **Commands**: Every documented command must be verifiable — check it exists in the build system
2. **Paths**: Every file path referenced must exist (use Glob to verify)
3. **Conventions**: Style claims must match actual code (spot-check 2-3 files)
4. **Completeness**: Cross-reference against the section selection from Step 4
5. **Conciseness**: Is every line earning its keep? Remove filler, obvious info, and generic advice
6. **No fabricated content**: Every claim traces back to an exploration finding. When uncertain, say so rather than guess
7. **Internal consistency**: Key facts (commands, paths, conventions, gotchas) must not contradict across sections. Spot-check: does the Commands section match what Gotchas warns about?

If any check fails, fix the content before presenting. Do not present a CLAUDE.md with known inaccuracies — correct first, then deliver.

## Nested CLAUDE.md Files

When working on a nested CLAUDE.md (a package within a monorepo, a module within a larger project):

1. **Scope the team** to that directory and its immediate dependencies
2. **Select sections** for the nested project's type — a plugin within a monorepo gets plugin-appropriate sections, not monorepo-level sections
3. **Reference the root CLAUDE.md** for shared context: "See the [root CLAUDE.md](../../.claude/CLAUDE.md) for workspace-level setup and cross-cutting conventions"
4. **Don't duplicate** — shared commands, environment setup, or conventions that belong in the root CLAUDE.md shouldn't be repeated in nested files

## Cleanup

After the CLAUDE.md is complete and delivered, clean up automatically — do not ask:

1. Shut down all teammates via `SendMessage` with `type: "shutdown_request"`
2. Remove the workspace directory (`.claude-md-workspace/`)
3. Remove team files (`~/.claude/teams/<team-name>/`)
4. Remove task files (`~/.claude/tasks/<team-name>/`)

These are transient working artifacts, not deliverables.
