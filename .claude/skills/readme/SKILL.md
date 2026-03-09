---
name: readme
description: Create, audit, and improve README files for any codebase, plugin, or repo. Orchestrates an agent team to deeply explore the project before writing, so every README is grounded in what actually exists — not what the author remembers. Use this skill whenever a user asks to "write a README", "create documentation for this project", "audit this README", "update the README", "this repo needs a README", "document this codebase", or mentions README quality, accuracy, or completeness. Also trigger when a user asks to "document this project" and the request is about introducing the project to users or contributors (not about operational runbooks — redirect to the handbook skill for those). Covers root READMEs, nested package READMEs, and monorepo documentation hierarchies.
---

# README Skill

Create, audit, and improve READMEs grounded in comprehensive codebase exploration. Targets two audiences: humans who skim for quick starts, and agents who parse for structure, entry points, and contracts.

## Prerequisite

This skill requires agent teams. Before proceeding, verify the feature is enabled:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

If not enabled, tell the user: "This skill uses agent teams for deep parallel exploration. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json env block, then restart the session." Do not fall back to a shallow approach — the quality difference is the point.

## Modes

| Mode | When | What happens |
|------|------|-------------|
| **Create** | No README exists, or user says "write a README" | Full exploration → classify → write |
| **Audit** | README exists, user says "audit", "check", "is this accurate" | Full exploration → compare claims vs reality → report |
| **Update** | README exists, user says "update", "improve", "fix" | Full exploration → compare → rewrite sections that drifted |

Detect the mode from the user's request. If ambiguous, ask: "Do you want me to create a new README, audit the existing one for accuracy, or update it?"

## Handbook Redirect

Before starting, check whether the user actually needs operational documentation rather than a README.

**Redirect signals** — the request focuses on:
- How to deploy, monitor, or operate a running system
- Failure recovery, runbooks, or incident response
- Internal architecture for operators (not users or contributors)
- "Document how this system works" for an existing running service

**Redirect action:** "This sounds like operational documentation — how to run and maintain the system rather than how to use and contribute to it. The handbook skill is better suited for this. Want me to use that instead?"

**README signals** — the request focuses on:
- What the project is and why it exists
- How to install, configure, and use it
- How to contribute or extend it
- A new project being introduced to users

Proceed with this skill when README signals are present.

## Step 1: Determine Scope

Identify which README(s) to work on.

**Root README only:** Default when the user says "write a README" without qualification, or when the project is a single package.

**Specific nested README:** When the user points to a specific directory ("write a README for the auth module").

**Full hierarchy:** When the user says "document this monorepo" or "all the READMEs need updating." Work on the root README first, then proceed to nested packages.

For audit/update modes, read the existing README(s) before exploration so the team knows what claims to verify.

## Step 2: Launch Exploration Team

Create an agent team with 5 teammates. Each teammate has a distinct exploration mandate and reports findings to dedicated files in the workspace.

Agent teams are coordinated via natural language — describe the team structure, teammates, and tasks to the lead. The lead handles spawning, task assignment, and coordination internally.

**Critical: known failure modes to guard against:**
- The lead may start doing exploration work itself instead of waiting for teammates. If you catch yourself exploring the codebase before teammates finish, stop. Your job is to coordinate, then synthesize.
- The lead may declare the team finished before all teammates complete. Wait for all 5 idle notifications before proceeding to synthesis.
- Task status can lag — a teammate may finish work without marking the task complete. Check the workspace for output files as a secondary completion signal.

Tell the lead to create these teammates with these prompts:

### Teammate 1: Cartographer

> Map the complete structure of this project. Your deliverable is a comprehensive inventory.
>
> Tasks:
> 1. **Directory tree** — full layout with annotations on what each top-level and second-level directory contains
> 2. **File inventory** — count and categorize: source files, config files, test files, documentation, scripts, assets
> 3. **Project type classification** — determine if this is a library, CLI tool, plugin/extension, monorepo, or hybrid. Evidence your classification with specific files (package.json bin field, setup.py entry_points, plugin manifest, workspace config)
> 4. **Nested package detection** — identify all sub-packages, their own READMEs (or lack thereof), and their relationship to the root
> 5. **Notable patterns** — anything unusual about the project structure that a README should explain (unconventional directory names, generated code, vendored dependencies)
>
> When you discover something relevant to another teammate's mandate, message them directly. For example, if you find a `bin/` directory, message the Interface Analyst about potential CLI commands.
>
> Write your findings to `<workspace>/exploration/cartographer.md`.

### Teammate 2: Interface Analyst

> Map everything this project exposes to its users. Your deliverable is a complete surface area inventory.
>
> Tasks:
> 1. **Public API surface** — all exported functions, classes, types, and constants. Include signatures and brief descriptions. For large APIs (>20 exports), group by module and note the top 10 most important
> 2. **CLI commands** — if this is a CLI tool, every command and subcommand with flags, arguments, and defaults
> 3. **Configuration schema** — all configuration options the user can set: config files, environment variables, constructor options. Include types and defaults
> 4. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems — anything that lets users extend the project's behavior
>
> Focus on what's public and documented. Flag things that appear public but lack documentation.
>
> Write your findings to `<workspace>/exploration/interface.md`.

### Teammate 3: DevEx Analyst

> Map the complete developer experience — everything someone needs to know to install, use, and develop on this project.
>
> Tasks:
> 1. **Installation** — all supported installation methods. Check package registries, Docker, platform-specific installers, build-from-source instructions
> 2. **Build system** — how to build the project. Build tools, commands, prerequisites, platform requirements
> 3. **Test infrastructure** — test framework, how to run tests, test organization, coverage tools, fixtures
> 4. **Development workflow** — dev server, watch mode, hot reload, linting, formatting, pre-commit hooks
> 5. **CI/CD** — what CI runs, required checks, deployment pipeline if visible
> 6. **Contributing prerequisites** — language/runtime version requirements, system dependencies, required accounts or credentials
>
> Try each installation/build step mentally — if the README says "run npm install" but there's no package.json, that's a finding.
>
> Write your findings to `<workspace>/exploration/devex.md`.

### Teammate 4: Archaeologist

> Excavate the project's existing documentation and identify what's stale, missing, or misleading.
>
> Tasks:
> 1. **Existing README analysis** — if a README exists, extract every factual claim it makes (file paths, command examples, feature descriptions). Create a claims checklist for other teammates to verify
> 2. **Documentation inventory** — all docs/ files, inline doc comments, wiki references, external doc links. Assess coverage: what's documented, what isn't
> 3. **Staleness signals** — docs that reference deleted files, old API signatures, deprecated features, or stale version numbers. Check git blame for doc file ages vs source file ages
> 4. **Undocumented directories** — directories with significant code but no README or doc coverage. Prioritize by complexity and user-facing impact
> 5. **Example quality** — existing examples in docs/, README, or test files. Are they runnable? Do they use current APIs?
>
> Share your claims checklist with the specific teammates whose domains overlap with the claims. Message the Interface Analyst about API/config claims, the DevEx Analyst about install/build claims, the Architect about architecture claims, and the Cartographer about file path claims. Use targeted messages, not broadcast — broadcast costs scale with team size.
>
> Write your findings to `<workspace>/exploration/archaeologist.md`.

### Teammate 5: Architect

> Map how the project's internals connect. Your deliverable helps contributors and agents understand the system's design.
>
> Tasks:
> 1. **Dependency graph** — external dependencies and what each is used for. Flag heavy, unusual, or security-sensitive dependencies
> 2. **Internal architecture** — how the project's modules/components connect. Data flow, control flow, key abstractions
> 3. **Design patterns** — recurring patterns in the codebase (repository pattern, middleware pipeline, event bus, etc.). Name them so the README can reference them
> 4. **Entry points** — where execution starts. Main files, handler registrations, initialization sequences
> 5. **Cross-cutting concerns** — error handling strategy, logging approach, configuration loading, authentication/authorization patterns
>
> Write your findings to `<workspace>/exploration/architect.md`.

### Workspace Setup

Before spawning the team, create the workspace directory:

```
<project-root>/.readme-workspace/exploration/
```

Tell each teammate to write their findings to this directory. After the README is complete, offer to clean up the workspace.

### Task Structure

Instruct the lead to create tasks with these dependencies:

1. All 5 exploration tasks (independent, no dependencies between them)
2. "Synthesize exploration findings" (depends on all 5 completing)
3. "Classify project type and select README pattern" (depends on synthesis)
4. "Write README" (depends on classification)

The lead manages task creation, assignment, and dependency resolution. Teammates self-claim tasks when they become unblocked.

**Important:** Explicitly tell the lead: "Wait for all teammates to complete their exploration tasks before starting synthesis. Do not begin synthesis, classification, or writing until all 5 exploration reports exist in the workspace."

## Step 3: Synthesize Findings

Teammates do not inherit the lead's conversation history — they start fresh with only their spawn prompt and the project's CLAUDE.md/skills. This is why each teammate prompt above is self-contained with explicit deliverables and output paths. Do not assume teammates know the user's original request or the README mode.

After all teammates complete their exploration tasks, read all 5 reports from the workspace. Synthesize into a single unified understanding:

1. **Confirm project type** — the Cartographer's classification, corroborated by Interface Analyst's findings (API surface → library, CLI commands → CLI tool, plugin manifest → plugin, workspace config → monorepo)
2. **Resolve contradictions** — if teammates found conflicting information, investigate and resolve. Note in the README if genuine ambiguity exists
3. **Build the claims verdict** — for audit/update modes, go through the Archaeologist's claims checklist and mark each as confirmed, outdated, or wrong based on other teammates' findings
4. **Identify coverage gaps** — topics that no teammate found information on but that the structural pattern expects. These become "Unknown" or "TODO" markers in the README rather than fabricated content

## Step 4: Select Structural Pattern

Read `references/structural-patterns.md` and select the pattern matching the confirmed project type.

For hybrid projects (e.g., a library that also has a CLI), use the dominant type's pattern and incorporate relevant sections from the secondary type.

Determine which optional sections to include based on whether the exploration team found substantive content for them. An empty "Architecture" section is worse than no "Architecture" section.

## Step 5: Write the README

### Create Mode

Write the full README following the selected structural pattern.

**Ground every claim in exploration findings.** Do not invent features, commands, or configuration options that the exploration team didn't discover. If a section in the pattern has no corresponding exploration data, either:
- Omit the section (if optional)
- Write "TODO: [what's needed]" with a note explaining what information is missing (if required)

**Dual-audience writing:**
- Lead each section with the human-readable narrative
- Follow with precise, parseable details (tables for options, code blocks for commands, explicit file paths)
- State types, defaults, and constraints explicitly — agents need these; humans benefit from them
- Name files and paths precisely ("configure in `config/settings.yaml`", not "the config file")

### Audit Mode

Produce an audit report, not a rewritten README. Structure:

```markdown
# README Audit: [Project Name]

## Summary
[1-3 sentences: overall accuracy assessment]

## Accurate Claims
- [claim] — confirmed by [evidence]

## Outdated Claims
- [claim] — was true, now [current state]. Source: [exploration finding]

## Incorrect Claims
- [claim] — actually [reality]. Source: [exploration finding]

## Missing Coverage
- [topic not in README but discovered by exploration team]

## Recommended Changes
[Prioritized list of specific edits, ordered by impact]
```

### Update Mode

Rewrite only the sections that the audit identified as outdated, incorrect, or missing. Preserve the existing README's structure and voice where it's accurate. Show a diff summary of what changed and why.

## Quality Checks

Before presenting the final README, verify:

1. **Every command example is real** — cross-reference with DevEx Analyst's findings. No `npm start` if there's no start script
2. **Every file path exists** — cross-reference with Cartographer's inventory. No references to deleted or renamed files
3. **Every config option is current** — cross-reference with Interface Analyst's config schema
4. **Quick start is copy-paste-runnable** — the sequence of commands in Quick Start should work on a fresh clone
5. **No fabricated content** — every claim traces back to an exploration finding. When uncertain, say so rather than guess

## Nested READMEs

When working on a nested README (a package within a monorepo, a plugin within a collection):

1. Scope the exploration team to that directory and its immediate dependencies
2. Select the structural pattern for the nested project's type (the plugin within a monorepo gets the Plugin pattern, not the Monorepo pattern)
3. Reference the root README for shared setup ("See the [root README](../README.md) for workspace setup")
4. Don't duplicate information that belongs in the root README

## Cleanup

After the README is complete and the user is satisfied:

1. Ask: "Want me to clean up the exploration workspace (`.readme-workspace/`)?"
2. If yes, remove the workspace directory
3. The agent team cleans up automatically when the lead shuts it down
