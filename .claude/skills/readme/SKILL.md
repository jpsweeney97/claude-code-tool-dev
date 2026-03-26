---
name: readme
description: Create, audit, and improve README files for any codebase, plugin, or repo. Orchestrates an agent team to deeply explore the project before writing, so every README is grounded in what actually exists — not what the author remembers. Use this skill whenever a user asks to "write a README", "create documentation for this project", "audit this README", "update the README", "this repo needs a README", "document this codebase", or mentions README quality, accuracy, or completeness. Also trigger when a user asks to "document this project" and the request is about introducing the project to users or contributors (not about operational runbooks — redirect to the handbook skill for those). Covers root READMEs, nested package READMEs, and monorepo documentation hierarchies.
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

# README Skill

Create, audit, and improve READMEs grounded in comprehensive codebase exploration. Targets two audiences: humans who skim for quick starts, and agents who parse for structure, entry points, and contracts.

**Announce at start:** "I'm using the readme skill to [create/audit/update] this README."

## Prerequisite

This skill requires agent teams. Verify the feature is enabled before any other work:

Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams for deep parallel exploration. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential exploration — parallel multi-perspective exploration is the skill's value proposition.

## Constraints

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams required | Hard prerequisite. Do NOT fall back to sequential or Agent-tool-only alternatives. |
| 2 | Sonnet for teammates | Spawn all teammates with `model: "sonnet"`. Lead uses the session's default model. |
| 3 | Teammates lack conversation history | Each teammate starts fresh with only its spawn prompt plus the project's CLAUDE.md/skills. The lead's conversation does NOT carry over — include everything teammates need in their spawn prompts. |
| 4 | One team per session | No nested teams. Clean up before starting a new one. |
| 5 | 5 teammates | Cartographer, Interface Analyst, DevEx Analyst, Archaeologist, Architect. |

See `references/agent-teams.md` for the full agent teams API reference.

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

For audit/update modes, read the existing README(s) before exploration so you know what claims to verify.

## Step 2: Explore the Project

Explore the project from 5 perspectives in parallel using an agent team. Each teammate investigates one dimension and writes structured findings to the workspace.

### Phase 1: Setup

1. Create the workspace directory: `<project-root>/.readme-workspace/exploration/`
2. Verify `.readme-workspace/` is in `.gitignore`. If absent, add it.

### Phase 2: Create Team and Tasks

If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.

1. **Create the team** via `TeamCreate` with `team_name: "readme-exploration"` and a description of the README task.
2. **Create one task per teammate** via `TaskCreate`. Each task describes the teammate's exploration mandate and output path. Do NOT set `blockedBy` dependencies — all 5 tasks run in parallel.

| Task | Teammate ID | Output file |
|------|-------------|-------------|
| Map project structure | `cartographer` | `exploration/cartographer.md` |
| Catalog public interfaces | `interface-analyst` | `exploration/interface.md` |
| Map developer experience | `devex-analyst` | `exploration/devex.md` |
| Audit existing documentation | `archaeologist` | `exploration/archaeologist.md` |
| Map internal architecture | `architect` | `exploration/architect.md` |

### Phase 3: Spawn Teammates

Spawn all 5 teammates using the `Agent` tool. The `team_name` parameter is what makes a spawned agent a teammate with messaging, shared tasks, and idle notifications. Without `team_name`, the agent is an isolated subagent with none of those capabilities.

**Design principle:** All teammates access all project files — they are scoped by perspective, not by directory. Do NOT partition directories among teammates. Directory-partitioned exploration creates gaps at boundaries where cross-cutting concerns live.

For each teammate, call `Agent` with:
- `team_name`: `"readme-exploration"` (must match TeamCreate)
- `name`: the teammate ID from the table above — this is the addressing key for all communication
- `model`: `"sonnet"`
- `prompt`: the spawn prompt below

Spawn all 5 in the same message to maximize parallelism. Do NOT start your own exploration or analysis before all teammates are spawned — your job is to coordinate and then synthesize.

#### Cartographer

```
Map the complete structure of the project at {project-root}. Write findings to {workspace}/exploration/cartographer.md.

Tasks:
1. **Directory tree** — full layout with annotations for top-level and second-level directories. For projects over 500 files, limit to 3 levels deep and sample 3-5 representative files per directory
2. **File inventory** — count and categorize: source files, config files, test files, documentation, scripts, assets
3. **Project type classification** — library, CLI tool, plugin/extension, monorepo, or hybrid. Evidence with specific files (package.json bin field, setup.py entry_points, plugin manifest, workspace config)
4. **Nested package detection** — all sub-packages, their own READMEs (or lack thereof), and relationship to root
5. **Notable patterns** — anything unusual about project structure that a README should explain

When you discover something relevant to another teammate, message them directly via SendMessage. For example, if you find a bin/ directory, message interface-analyst about potential CLI commands.
```

#### Interface Analyst

```
Map everything this project exposes to its users at {project-root}. Write findings to {workspace}/exploration/interface.md.

Tasks:
1. **Public API surface** — all exported functions, classes, types, constants with signatures. For large APIs (>20 exports), group by module and note the top 10
2. **CLI commands** — every command and subcommand with flags, arguments, and defaults
3. **Configuration schema** — all config options: config files, environment variables, constructor options with types and defaults
4. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems

Focus on what's public and documented. Flag things that appear public but lack documentation.

Structure output as: ## Public API, ## CLI Commands, ## Configuration, ## Extension Points
```

#### DevEx Analyst

```
Map the complete developer experience at {project-root}. Write findings to {workspace}/exploration/devex.md.

Tasks:
1. **Installation** — all supported methods: package registries, Docker, platform-specific installers, build-from-source
2. **Build system** — tools, commands, prerequisites, platform requirements
3. **Test infrastructure** — framework, how to run tests, organization, coverage tools
4. **Development workflow** — dev server, watch mode, hot reload, linting, formatting, pre-commit hooks
5. **CI/CD** — what CI runs, required checks, deployment pipeline if visible
6. **Contributing prerequisites** — language/runtime versions, system dependencies, required accounts

Try each installation/build step mentally — if the README says "run npm install" but there's no package.json, that's a finding.
```

#### Archaeologist

```
Excavate existing documentation at {project-root}. Write findings to {workspace}/exploration/archaeologist.md.

Tasks:
1. **Existing README analysis** — if a README exists, extract every factual claim (file paths, command examples, feature descriptions) into a claims checklist
2. **Documentation inventory** — all docs/ files, inline doc comments, wiki references, external doc links with coverage assessment
3. **Staleness signals** — references to deleted files, old API signatures, deprecated features, stale version numbers
4. **Undocumented directories** — directories with significant code but no doc coverage, ranked by user-facing impact
5. **Example quality** — existing examples in docs/, README, or tests: are they runnable and using current APIs?

Share your claims checklist with the specific teammates whose domains overlap. Message interface-analyst about API/config claims, devex-analyst about install/build claims, architect about architecture claims, cartographer about file path claims. Use targeted messages, not broadcast — broadcast costs scale with team size.
```

#### Architect

```
Map how the project's internals connect at {project-root}. Write findings to {workspace}/exploration/architect.md.

Tasks:
1. **Dependency graph** — external dependencies and purpose of each. Flag heavy, unusual, or security-sensitive ones
2. **Internal architecture** — how modules/components connect: data flow, control flow, key abstractions
3. **Design patterns** — recurring patterns (repository, middleware pipeline, event bus, etc.)
4. **Entry points** — where execution starts: main files, handler registrations, initialization sequences
5. **Cross-cutting concerns** — error handling, logging, configuration loading, auth patterns

When you discover something relevant to another teammate, message them directly. If you find config loaded via singleton, message interface-analyst. If you find complex init sequences, message devex-analyst.
```

### Phase 4: Monitor Completion

**Primary signal:** idle notifications from the team system. When a teammate finishes and goes idle, the lead receives a notification. Peer DM summaries appear in idle notifications — use these as synthesis input.

**Completion rule:** Wait for all 5 idle notifications before proceeding to synthesis. Do NOT start synthesis early — partial exploration data produces incomplete READMEs.

**Verification:** After all idle notifications, verify each expected output file exists in the workspace via `Glob` or `Read`.

**Timeout:** If no idle notifications or task status changes (confirmed via `TaskGet`) arrive for 5 minutes, proceed with available findings. "Activity" means: idle notification received, or a task moving to `completed`.

**Partial completion:** Always proceed with available findings rather than blocking. Note which teammates failed and why in your synthesis — a README with known coverage gaps is better than no README.

**Small projects:** If the Cartographer reports fewer than 20 source files and no tests, dismiss remaining teammates and proceed to synthesis with whatever reports exist.

## Step 3: Synthesize Findings

After all teammates complete, read all reports from the workspace. Synthesize into a unified understanding:

1. **Confirm project type** — Cartographer's classification, corroborated by Interface Analyst's findings (API surface → library, CLI commands → CLI tool, plugin manifest → plugin, workspace config → monorepo)
2. **Resolve contradictions** — if teammates found conflicting information, investigate. Note genuine ambiguity in the README rather than guessing
3. **Build claims verdict** — for audit/update modes, go through the Archaeologist's claims checklist and mark each as confirmed, outdated, or wrong based on other teammates' findings
4. **Identify coverage gaps** — topics no teammate found information on but the structural pattern expects. These become "Unknown" or "TODO" markers rather than fabricated content

## Step 4: Select Structural Pattern

Read `references/structural-patterns.md` and select the pattern matching the confirmed project type.

For hybrid projects (e.g., a library that also has a CLI), use the dominant type's pattern and incorporate relevant sections from the secondary type.

Include optional sections only when the exploration team found substantive content. An empty "Architecture" section is worse than no "Architecture" section.

## Step 5: Write the README

### Create Mode

Write the full README following the selected structural pattern.

**Ground every claim in exploration findings.** Do not invent features, commands, or configuration the exploration team didn't discover. If a section has no corresponding data, either:
- Omit the section (if optional)
- Write "TODO: [what's needed]" with a note explaining what's missing (if required)

**Dual-audience writing:**
- Lead each section with the human-readable narrative
- Follow with precise, parseable details (tables for options, code blocks for commands, explicit file paths)
- State types, defaults, and constraints explicitly — agents need these; humans benefit from them
- Name files and paths precisely ("configure in `config/settings.yaml`", not "the config file")

### Audit Mode

Produce an audit report, not a rewritten README:

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

Rewrite only sections identified as outdated, incorrect, or missing. Preserve the existing README's structure and voice where accurate. If the README uses a fundamentally wrong structural pattern (e.g., Library pattern for what's actually a CLI tool), flag this: "The existing README is structured as a [X] but the project is actually a [Y]. Want me to restructure it, or just update the content within the current structure?" Show a diff summary of what changed and why.

## Quality Checks

Before presenting the final README, verify:

1. **Every command example is real** — cross-reference with DevEx Analyst's findings
2. **Every file path exists** — cross-reference with Cartographer's inventory
3. **Every config option is current** — cross-reference with Interface Analyst's schema
4. **Quick start is copy-paste-runnable** — commands work on a fresh clone
5. **No fabricated content** — every claim traces to an exploration finding

If any check fails, fix before presenting. Do not deliver a README with known inaccuracies.

## Nested READMEs

When working on a nested README (a package within a monorepo, a plugin within a collection):

1. Scope the exploration team to that directory and its immediate dependencies
2. Select the structural pattern for the nested project's type (the plugin gets the Plugin pattern, not the Monorepo pattern)
3. Reference the root README for shared setup ("See the [root README](../README.md) for workspace setup")
4. Don't duplicate information that belongs in the root README

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop — do not fall back |
| TeamCreate fails | Phase 2 step 1 | Hard stop — cannot proceed without team |
| Teammate spawn fails | Phase 3 | Log, continue with remaining. All fail = hard stop |
| Teammate timeout | No activity for 5 min | Treat as failed, proceed with available findings |
| Missing output file | Phase 4 verification | Log as coverage gap in synthesis |
| Stale workspace | Phase 1 setup | Warn user, offer: archive / remove / abort |
| TeamDelete fails | Cleanup step 2 | Orphaned teammates still active — report degraded state, proceed with workspace cleanup |

## Cleanup

After the README is complete and delivered, follow the cleanup resilience protocol from `references/agent-teams.md`. These are transient working artifacts — do not ask the user about cleanup.

1. **Shutdown loop** — for each teammate, send up to 3 shutdown requests with escalating context:
   - Attempt 1: `{type: "shutdown_request", reason: "README complete"}`
   - Attempt 2 (if no idle after 60s): "All exploration is complete, findings have been saved. Please shut down."
   - Attempt 3 (if no idle after 60s): "Session ending. Cleanup requires all teammates to shut down. This is the final request."
   - If no idle after 30s: classify as **orphaned** with reason.
2. **TeamDelete** — call `TeamDelete`. If it fails (orphaned teammates still active), report degraded state to user:
   "Team cleanup partially failed: [N] teammate(s) did not shut down ([names]). Team resources may remain at `~/.claude/teams/readme-exploration/`. These will be cleaned up when a new team is created, or remove manually."
3. **Workspace** — remove `.readme-workspace/`. Workspace cleanup is independent of team cleanup — always attempt it regardless of TeamDelete outcome.
