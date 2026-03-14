---
name: explore-repo
description: Deeply explore any GitHub repository to build comprehensive, question-ready understanding using a parallel agent team. Orchestrates 6 specialized teammates — Structural Cartographer, Architecture Analyst, Interface Mapper, Toolchain Scout, Domain Analyst, and History & Context Analyst — to investigate every dimension of a repository simultaneously, then synthesizes findings into your context so you can answer any question about the repo. Use whenever you need to understand an unfamiliar codebase, explore a GitHub repo, onboard to a new project, prepare for a code review of an unfamiliar repo, or dive deep into how something works. Trigger on "explore this repo", "understand this codebase", "deep dive into this project", "what does this repo do", "learn about this project", "I need to understand X before working on it", or any request for comprehensive codebase knowledge. Also use when a user pastes a GitHub URL and wants to understand the project, or when preparing to work in an unfamiliar codebase.
---

# Explore Repo

Deeply explore any GitHub repository to build comprehensive, question-ready understanding. Uses an agent team to investigate structure, architecture, interfaces, toolchain, domain logic, and project history in parallel — then synthesizes findings so you can answer any question about the repo with grounded evidence.

Unlike documentation skills (README, handbook, CLAUDE.md) that produce a specific artifact, this skill produces **understanding** — the explored knowledge lives in your context, ready for whatever questions come next.

## Prerequisite

This skill requires agent teams. Before proceeding, verify the feature is enabled:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

If not enabled, tell the user: "This skill uses agent teams for deep parallel codebase exploration. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json env block, then restart the session." Do not fall back to serial exploration — parallel multi-perspective investigation is what makes the understanding comprehensive rather than shallow.

## Step 1: Clone the Repository

This skill targets remote GitHub repositories. The user provides a GitHub URL — clone it locally for the team to explore.

```bash
git clone <url> /tmp/explore-repo/<repo-name>
```

A full clone (not shallow) is needed because the History & Context Analyst requires git history. Note the clone path for teammate prompts.

If the user provides a shorthand like `owner/repo`, expand to `https://github.com/owner/repo`.

**Scope check** after cloning:
1. Confirm the repo has source code (not empty, not docs-only)
2. Estimate project size (file count). For large repos (>5000 source files), ask the user: "This is a large codebase. Want me to focus on specific areas, or do a broad sweep?"
3. Note primary language(s) — helps teammates calibrate their exploration

## Step 2: Launch Exploration Team

Create an agent team with 6 teammates. Each investigates the codebase from a different dimension, writing findings to the workspace.

**Critical: known failure modes to guard against:**
- **Do not substitute the Agent tool for agent teams.** If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` and use it. The Agent tool with `run_in_background` looks similar but lacks teammate-to-teammate messaging, coordinated completion detection, and shared task state — leading to polling races and lost coordination. Agent teams and the Agent tool are not interchangeable.
- The lead may start exploring the codebase itself instead of waiting for teammates. If you catch yourself reading source files before teammates finish, stop. Your job is to coordinate, then synthesize.
- The lead may declare the team finished before all teammates complete. Wait for all 6 idle notifications before proceeding to synthesis.
- Task status can lag — check the workspace for output files as a secondary completion signal.

Tell the lead to create these teammates with these prompts:

### Teammate 1: Structural Cartographer

> Map the complete physical structure of the repository at `{repo-path}`. Your deliverable answers "where is everything?"
>
> Tasks:
> 1. **Directory tree** — full layout (depth 3-4) with annotations on what each directory contains. For large repos (>500 files), limit depth and sample representative files per directory
> 2. **File inventory** — count and categorize: source files by language, config files, test files, documentation, scripts, assets, generated files
> 3. **Project classification** — what type of project is this? Library, CLI tool, web app, API service, framework, plugin/extension, monorepo, or hybrid. Evidence your classification with specific files (package.json bin field, setup.py entry_points, Dockerfile, workspace config, etc.)
> 4. **Package/module structure** — for monorepos: all sub-packages with paths and purposes. For single packages: module organization and grouping strategy
> 5. **Entry points** — where does execution start? Main files, handler registrations, initialization sequences, exported modules
> 6. **Notable structural patterns** — anything unusual: unconventional directory names, generated code directories, vendored dependencies, symlinks, significant gitignore patterns
>
> When you discover entry points or module boundaries, message the Architecture Analyst. When you find config files or CLI-related directories, message the Interface Mapper. When you find build/test/CI configuration, message the Toolchain Scout.
>
> Write your findings to `{workspace}/exploration/structure.md`.

### Teammate 2: Architecture Analyst

> Analyze the internal architecture and design of the codebase at `{repo-path}`. Your deliverable answers "how does everything connect?"
>
> Tasks:
> 1. **Module dependency graph** — what depends on what internally. Import/require analysis across main source directories. Identify core modules everything depends on vs leaf modules
> 2. **Data flow** — how data moves through the system. Entry points → processing → output. Trace 2-3 representative flows end-to-end
> 3. **Key abstractions** — the central types, classes, interfaces, or concepts the architecture is built around. What are the "load-bearing" abstractions?
> 4. **Design patterns** — recurring architectural patterns (MVC, middleware pipeline, event bus, repository pattern, actor model, etc.). Name them and cite examples
> 5. **State management** — where is state held? Databases, caches, in-memory stores, files, external services. How is state accessed and modified?
> 6. **Concurrency model** — if applicable: threading, event loops, workers, queues. How does the system handle parallel work?
> 7. **External dependencies** — key libraries/frameworks and their roles. Flag heavy, unusual, or security-sensitive dependencies
> 8. **Code conventions** — naming patterns, import style, error handling patterns, comment style, test patterns. Read 8-12 representative source files across the codebase
>
> Focus on runtime behavior, not just static structure. "Module X calls Y when Z happens" is more useful than "X imports Y."
>
> When you discover public APIs or extension points, message the Interface Mapper. When you find non-obvious error handling or failure modes, message the Domain Analyst. When you find conventions that would surprise a newcomer, message the Toolchain Scout.
>
> Write your findings to `{workspace}/exploration/architecture.md`.

### Teammate 3: Interface & Capability Mapper

> Map everything this project exposes to its users and the outside world at `{repo-path}`. Your deliverable answers "what can this project do?"
>
> Tasks:
> 1. **Public API surface** — all exported functions, classes, types, constants. Include signatures and brief descriptions. For large APIs (>30 exports), group by module and highlight the most important
> 2. **CLI interface** — if this is a CLI tool: every command, subcommand, flag, and argument with types and defaults
> 3. **HTTP/API endpoints** — if this is a service: all routes, methods, request/response schemas, authentication requirements
> 4. **Configuration schema** — all configuration surfaces: env vars, config files, constructor options, settings. For each: name, type, default, purpose
> 5. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems, callback registrations — anything that lets users extend behavior
> 6. **Output formats** — what the project produces: files, logs, API responses, side effects. Where outputs go and what they look like
> 7. **Integration points** — how this project connects to other systems: databases, message queues, external APIs, file systems, cloud services
>
> Be exhaustive on the public surface — this is what users interact with. For internal-only interfaces, note briefly but don't catalog in depth.
>
> When you find configuration that affects runtime behavior, message the Toolchain Scout. When you find extension points with architectural implications, message the Architecture Analyst. When you find domain-specific interfaces, message the Domain Analyst.
>
> Write your findings to `{workspace}/exploration/interfaces.md`.

### Teammate 4: Toolchain & Workflow Scout

> Investigate how to work with the project at `{repo-path}`. Your deliverable answers "how do I build, test, run, and develop on this?"
>
> Tasks:
> 1. **Language and runtime** — primary language(s), required runtime versions, language-specific tooling
> 2. **Package manager** — npm, yarn, pnpm, uv, pip, cargo, go modules, etc. Lock file present?
> 3. **Build system** — how to build: commands, tools, output locations. Build modes (dev, prod, release)
> 4. **Test infrastructure** — test framework, how to run tests, test organization, coverage tools, fixtures, test utilities
> 5. **Lint and format** — configured tools (eslint, prettier, ruff, rustfmt, etc.), how to run them
> 6. **CI/CD** — what pipelines exist (.github/workflows, .gitlab-ci.yml, Jenkinsfile), what they run, required checks
> 7. **Scripts and automation** — custom scripts in package.json, Makefile, scripts/, justfile, etc. What each does
> 8. **Setup steps** — what a new developer needs: install prerequisites, clone, install deps, configure, first run
> 9. **Development workflow** — dev server, watch mode, hot reload, debugging setup
> 10. **Docker/containers** — Dockerfiles, docker-compose, container-based dev environments
>
> For each command, verify it exists in the build system config. Mark unverifiable commands as [UNVERIFIED].
>
> When you discover build constraints or setup quirks, message the Domain Analyst. When you find CI pipelines that test specific things, message the Architecture Analyst.
>
> Write your findings to `{workspace}/exploration/toolchain.md`.

### Teammate 5: Domain & Purpose Analyst

> Understand what this project actually does — its purpose, domain, and core logic at `{repo-path}`. Your deliverable answers "what is this project and why does it exist?"
>
> Tasks:
> 1. **Project purpose** — what problem does this solve? Who is it for? Read README, docs, and any overview files
> 2. **Core domain concepts** — what are the key nouns and verbs in this project's domain? What mental model is needed to understand it? (e.g., for a task runner: tasks, dependencies, execution graph, runners)
> 3. **Data models** — key types, schemas, database models, or data structures that represent the domain. What are the entities and their relationships?
> 4. **Business rules and invariants** — rules enforced by the code that reflect domain constraints. Validation logic, state machines, access control rules
> 5. **Key algorithms and logic** — the core "interesting" logic. What does the project do that's non-trivial? Trace through the main code paths
> 6. **Existing documentation** — README content, design docs, architectural decision records, inline comments explaining "why"
> 7. **Project maturity** — version, release history, test coverage, contributor activity. Is this alpha, beta, stable, or maintenance-mode?
> 8. **Non-obvious gotchas** — things that would surprise someone new. Search for FIXME, HACK, WORKAROUND, XXX comments. Check for non-obvious ordering dependencies, implicit requirements, confusing naming
>
> Read deeply — you need to understand the actual code, not just categorize files. Read the core business logic files, not just configs and manifests.
>
> When you find domain concepts that shape the API, message the Interface Mapper. When you find business rules enforced through error handling, message the Architecture Analyst. When you find gotchas related to setup or development, message the Toolchain Scout.
>
> Write your findings to `{workspace}/exploration/domain.md`.

### Teammate 6: History & Context Analyst

> Mine the project's history, evolution, community, and security posture at `{repo-path}`. Your deliverable answers "how did this get here, who's behind it, and what should I be careful about?"
>
> Tasks:
> 1. **Recent git history** — last 50-100 commits: what areas are actively changing? Commit frequency and patterns? Clear development phases or focus areas? Use `git log --oneline -100` and `git log --since="6 months ago" --format="%h %ad %s" --date=short`
> 2. **Pull request analysis** — recent merged PRs (last 20-30): what kinds of changes are being made? What do PR descriptions reveal about priorities and decision-making? Use `gh pr list --state merged --limit 30 --json number,title,mergedAt,body,labels` if `gh` is available
> 3. **Issue landscape** — open and recent closed issues: what are users reporting? What's requested? What's broken? Use `gh issue list --limit 30 --json number,title,labels,body,state` if `gh` is available
> 4. **Release history** — versioning scheme, release cadence, what changes between versions. Use `gh release list` and release notes if available. Check git tags with `git tag --sort=-creatordate | head -20`
> 5. **Contributor patterns** — who contributes? Solo project, small team, or open community? How active? Use `git shortlog -sn --no-merges | head -20`
> 6. **Decision trail** — ADRs, CHANGELOG, design docs, RFCs — anything capturing the "why" behind architectural choices
> 7. **Community signals** — LICENSE type, CONTRIBUTING.md, code of conduct, issue templates, PR templates. What does the project expect from contributors?
> 8. **Security posture** — SECURITY.md, security advisories, dependency audit tooling (dependabot, renovate), security-sensitive code patterns (auth, crypto, input validation, secrets handling)
>
> Before using `gh` commands, verify `gh` is available and authenticated for the repo. If `gh` is not available, rely on `git log`, `git tag`, and filesystem analysis — note the gap in your findings.
>
> When you find historical decisions that explain current architecture, message the Architecture Analyst. When you find issues reporting bugs or gotchas, message the Domain Analyst. When you find security-related patterns, message the Architecture Analyst. When you find contributor workflow expectations, message the Toolchain Scout.
>
> Write your findings to `{workspace}/exploration/history.md`.

### Workspace Setup

Before spawning the team, create the workspace directory:

```
{repo-root}/.explore-workspace/exploration/
```

Tell each teammate to write their findings to this directory.

### Task Structure

Instruct the lead to create tasks with these dependencies:

1. All 6 exploration tasks (independent, no dependencies between them)
2. "Synthesize exploration findings" (depends on all 6 completing)

**Important:** Explicitly tell the lead: "Wait for all teammates to complete their exploration tasks before starting synthesis. Do not begin synthesis until all 6 exploration reports exist in the workspace."

## Step 3: Synthesize Findings

Teammates do not inherit the lead's conversation history — they start fresh with only their spawn prompt and the project's CLAUDE.md/skills. This is why each teammate prompt above is self-contained with explicit deliverables and output paths. Do not assume teammates know the user's original request.

After all teammates complete, read all 6 exploration reports. Synthesize into a comprehensive understanding:

1. **Confirm project identity** — reconcile the Cartographer's classification with the Domain Analyst's purpose and the Interface Mapper's capabilities. Build a clear "what this project is and does" statement
2. **Map architecture to structure** — combine the Cartographer's physical layout with the Architecture Analyst's logical design. Where do key abstractions live? How do modules map to capabilities?
3. **Connect interfaces to implementation** — the Interface Mapper found what's exposed; the Architecture Analyst found how it's built. Connect them: which entry point leads to which internal flow
4. **Add historical context** — the History Analyst's findings explain *why* the architecture and interfaces look the way they do. Connect design decisions to their rationale. Note the project's trajectory: what's actively changing, what's stable, what's being deprecated
5. **Assess project health** — combine the History Analyst's contributor patterns and release cadence with the Toolchain Scout's CI/CD and test infrastructure. Is this project actively maintained? Well-tested? Secure?
6. **Resolve contradictions** — when teammates disagree, investigate. Note genuine ambiguity rather than guessing
7. **Build the operational picture** — combine Toolchain Scout's findings with the Domain Analyst's gotchas
8. **Identify knowledge gaps** — topics no teammate found information on. These are honest unknowns, not silent omissions

**When sources conflict:**
- **Actual code is ground truth** for what the project does
- **Config files** are authoritative for what's intended
- **Documentation** may be stale — verify against code before trusting
- **Comments** are weakest — may be outdated; corroborate before citing

## Step 4: Present Summary & Engage

Present a structured summary to the user — dense and informative:

```
## {Project Name}

**What it is:** [1-2 sentences: type, purpose, audience]
**Built with:** [key technologies and frameworks]
**Size:** [file count, language breakdown, package count if monorepo]
**Maturity:** [active/stable/maintenance-mode, contributor count, release cadence]

### Architecture
[3-5 sentences: how the pieces connect, key abstractions, data flow]

### Key Capabilities
[Bulleted list: APIs, CLI commands, features, what it can do]

### How to Work With It
[Setup, build, test — the essential commands]

### Project Health & History
[Development activity, recent focus areas, key design decisions, security posture]

### Notable
[2-3 things that would surprise or interest someone new to this codebase]
```

Then: "I've completed the exploration. Ask me anything about this codebase — I have detailed findings on structure, architecture, interfaces, toolchain, domain logic, and project history."

**Keep workspace files available** during the Q&A phase. If the user asks a detailed question the synthesis didn't fully capture, re-read the relevant exploration report for specifics.

## Ending an Exploration Session

When the user signals they're done (moves to another task, says "thanks", starts unrelated work), clean up:

1. Shut down all teammates via `SendMessage` with `type: "shutdown_request"`
2. Remove the workspace directory (`.explore-workspace/`)
3. Remove team files (`~/.claude/teams/<team-name>/`)
4. Remove task files (`~/.claude/tasks/<team-name>/`)
5. If a temp clone was created (`/tmp/explore-repo/`), remove it

Do not ask before cleaning up — these are transient working artifacts.

## Extension Points

This skill is designed for in-context understanding. Future extensions could add:

- **Persistent knowledge files** — write synthesis to `{repo}/.explore-knowledge/` so future sessions can load it instead of re-exploring
- **Focused re-exploration** — deep-dive a specific area with targeted teammates (e.g., "explore just the auth module in more detail")
- **Comparison mode** — explore two repos and compare architecture, patterns, or approaches
- **Incremental updates** — re-explore only what changed since last exploration
