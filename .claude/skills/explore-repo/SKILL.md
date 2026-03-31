---
name: explore-repo
description: Deeply explore any GitHub repository or local codebase to build comprehensive, question-ready understanding using a parallel agent team. Orchestrates 6 specialized teammates — Cartographer, Architect, Interface Mapper, Toolchain Scout, Domain Analyst, and Historian — to investigate every dimension of a repository simultaneously, then synthesizes findings so you can answer any question about the repo. Use whenever you need to understand an unfamiliar codebase, explore a GitHub repo, onboard to a new project, prepare for code review of an unfamiliar repo, or dive deep into how something works. Trigger on "explore this repo", "understand this codebase", "deep dive into this project", "what does this repo do", "learn about this project", or any request for comprehensive codebase knowledge. Also trigger when a user pastes a GitHub URL and wants to understand the project, or when preparing to work in an unfamiliar codebase. Works with both remote GitHub repositories (cloned automatically) and local codebases.
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
argument-hint: "[target — GitHub URL, owner/repo, local path, or 'this repo']"
---

# Explore Repo

Deeply explore any repository — remote or local — to build comprehensive, question-ready understanding. Uses a 6-teammate agent team to investigate structure, architecture, interfaces, toolchain, domain logic, and project history in parallel, then synthesizes findings so you can answer any question about the repo with grounded evidence.

Unlike documentation skills (README, handbook, CLAUDE.md) that produce a specific artifact, this skill produces **understanding** — explored knowledge lives in your context, ready for whatever questions come next.

**Announce at start:** "I'm using the explore-repo skill to deeply explore this [repository/codebase]."

## When to Use

- Understanding an unfamiliar codebase before working in it
- Onboarding to a new project or exploring a GitHub URL
- Preparing for code review of an unfamiliar repo
- Deep-diving into how a system works
- Building comprehensive knowledge to answer follow-up questions

## When NOT to Use

- Writing a README → use `readme`
- Creating operational documentation → use `handbook`
- Auditing or creating CLAUDE.md → use `claude-md`
- Quick search for a specific file or function → use Grep/Glob directly
- Architecture review producing a findings report → use `design-review-team` or `system-design-review`

## Prerequisites

**Agent teams required.** Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams for deep parallel exploration. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential exploration — parallel multi-perspective investigation is what makes the understanding comprehensive rather than shallow.

## Constraints

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams required | Hard prerequisite. Do NOT fall back to sequential or Agent-tool-only alternatives. |
| 2 | Sonnet for teammates | Spawn all teammates with `model: "sonnet"`. Lead uses the session's default model. |
| 3 | Teammates lack conversation history | Each teammate starts fresh with only its spawn prompt plus the project's CLAUDE.md/skills. Include everything teammates need in their spawn prompts. |
| 4 | One team per session | No nested teams. Clean up before starting a new one. |
| 5 | 6 teammates | Cartographer, Architect, Interface Mapper, Toolchain Scout, Domain Analyst, Historian. |
| 6 | Lead does not explore | The lead frames, coordinates, and synthesizes. Teammates investigate. |

See `references/agent-teams.md` for the full agent teams API reference.

## Procedure

`Resolve → Setup → Explore → Synthesize → Present → Cleanup`

### Phase 1: Resolve Target

Determine whether the target is remote or local.

| Signal | Mode | Action |
|--------|------|--------|
| GitHub URL (`https://github.com/...`) | Remote | Clone to `/tmp/explore-repo/<repo-name>` (full clone — Historian needs git history) |
| Shorthand (`owner/repo`) | Remote | Expand to `https://github.com/owner/repo`, then clone |
| Local path or "this repo" / "this codebase" | Local | Use current working directory or specified path |
| Ambiguous | — | Ask: "Should I clone a remote repo, or explore the local codebase?" |

**Scope check** after resolving:
1. Confirm the repo has source code (not empty, not docs-only)
2. Estimate project size (file count). For large repos (>5000 source files), ask: "This is a large codebase. Want me to focus on specific areas, or do a broad sweep?"
3. Note primary language(s) — helps teammates calibrate exploration

### Phase 2: Setup Workspace

1. Create workspace: `{repo-root}/.explore-workspace/exploration/`
2. Verify `.explore-workspace/` is in `.gitignore`. If absent, add it.

### Phase 3: Launch Exploration Team

#### 3a: Create Team and Tasks

If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.

1. **Create the team** via `TeamCreate` with `team_name: "repo-exploration"`.
2. **Create one task per teammate** via `TaskCreate`. Do NOT set `blockedBy` — all 6 run in parallel.

| Task | Teammate ID | Output file |
|------|-------------|-------------|
| Map project structure | `cartographer` | `exploration/structure.md` |
| Analyze architecture | `architect` | `exploration/architecture.md` |
| Map interfaces and capabilities | `interface-mapper` | `exploration/interfaces.md` |
| Investigate toolchain and workflow | `toolchain-scout` | `exploration/toolchain.md` |
| Analyze domain and purpose | `domain-analyst` | `exploration/domain.md` |
| Mine history and context | `historian` | `exploration/history.md` |

#### 3b: Spawn Teammates

Spawn all 6 using the `Agent` tool with `team_name: "repo-exploration"`. The `team_name` parameter is what makes a spawned agent a teammate with messaging, shared tasks, and idle notifications — without it, the agent is an isolated subagent with none of those capabilities.

**Design principle:** All teammates access all project files — scoped by perspective, not directory. Do NOT partition directories among teammates. Directory-partitioned exploration creates gaps at boundaries where cross-cutting concerns live.

For each teammate, call `Agent` with:
- `team_name`: `"repo-exploration"` (must match TeamCreate)
- `name`: teammate ID from table above
- `model`: `"sonnet"`
- `prompt`: spawn prompt below

Spawn all 6 in the same message to maximize parallelism. Do NOT start your own exploration before all teammates are spawned.

##### Cartographer

> Map the complete physical structure of the repository at `{repo-path}`. Write findings to `{workspace}/exploration/structure.md`.
>
> Tasks:
> 1. **Directory tree** — full layout (depth 3-4) with annotations. For large repos (>500 files), limit depth and sample representative files per directory
> 2. **File inventory** — count and categorize: source by language, config, test, docs, scripts, assets, generated
> 3. **Project classification** — library, CLI tool, web app, API service, framework, plugin/extension, monorepo, or hybrid. Evidence with specific files (package.json bin field, setup.py entry_points, Dockerfile, workspace config)
> 4. **Package/module structure** — for monorepos: sub-packages with paths and purposes. For single packages: module organization
> 5. **Entry points** — main files, handler registrations, initialization sequences, exported modules
> 6. **Notable patterns** — unconventional structure, generated code, vendored deps, symlinks
>
> Cross-teammate messaging: Message `architect` when you find entry points or module boundaries. Message `interface-mapper` when you find config files or CLI directories. Message `toolchain-scout` when you find build/test/CI config.

##### Architect

> Analyze internal architecture and design of the codebase at `{repo-path}`. Write findings to `{workspace}/exploration/architecture.md`.
>
> Tasks:
> 1. **Module dependency graph** — internal imports/requires. Core modules vs leaf modules
> 2. **Data flow** — entry points → processing → output. Trace 2-3 representative flows end-to-end
> 3. **Key abstractions** — central types, classes, interfaces the architecture is built around
> 4. **Design patterns** — MVC, middleware pipeline, event bus, repository pattern, etc. Name and cite examples
> 5. **State management** — databases, caches, in-memory stores, files, external services
> 6. **Concurrency model** — threading, event loops, workers, queues (if applicable)
> 7. **External dependencies** — key libraries/frameworks and roles. Flag heavy, unusual, or security-sensitive
> 8. **Code conventions** — naming, imports, error handling, comments, test patterns. Read 8-12 representative files
>
> Focus on runtime behavior: "Module X calls Y when Z happens" over "X imports Y."
>
> Cross-teammate messaging: Message `interface-mapper` about public APIs or extension points. Message `domain-analyst` about non-obvious error handling or failure modes. Message `toolchain-scout` about conventions that would surprise a newcomer.

##### Interface Mapper

> Map everything this project exposes to users and the outside world at `{repo-path}`. Write findings to `{workspace}/exploration/interfaces.md`.
>
> Tasks:
> 1. **Public API surface** — exported functions, classes, types, constants with signatures. For large APIs (>30 exports), group by module and highlight key items
> 2. **CLI interface** — commands, subcommands, flags, arguments with types and defaults
> 3. **HTTP/API endpoints** — routes, methods, request/response schemas, auth requirements
> 4. **Configuration schema** — env vars, config files, constructor options: name, type, default, purpose
> 5. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems, callbacks
> 6. **Output formats** — files, logs, API responses, side effects
> 7. **Integration points** — databases, message queues, external APIs, cloud services
>
> Be exhaustive on public surface. Note internal-only interfaces briefly.
>
> Cross-teammate messaging: Message `toolchain-scout` about config affecting runtime. Message `architect` about extension points with architectural implications. Message `domain-analyst` about domain-specific interfaces.

##### Toolchain Scout

> Investigate how to work with the project at `{repo-path}`. Write findings to `{workspace}/exploration/toolchain.md`.
>
> Tasks:
> 1. **Language and runtime** — primary language(s), required versions, language-specific tooling
> 2. **Package manager** — npm/yarn/pnpm/uv/pip/cargo/go modules. Lock file present?
> 3. **Build system** — commands, tools, output locations, build modes (dev/prod/release)
> 4. **Test infrastructure** — framework, how to run, organization, coverage, fixtures
> 5. **Lint and format** — configured tools, how to run
> 6. **CI/CD** — pipelines (.github/workflows, .gitlab-ci.yml, etc.), required checks
> 7. **Scripts and automation** — package.json scripts, Makefile, justfile, etc.
> 8. **Setup steps** — prerequisites → clone → install → configure → run
> 9. **Development workflow** — dev server, watch mode, hot reload, debugging
> 10. **Docker/containers** — Dockerfiles, docker-compose, container-based dev
>
> Verify each command exists in build config. Mark unverifiable as [UNVERIFIED].
>
> Cross-teammate messaging: Message `domain-analyst` about build constraints or setup quirks. Message `architect` about CI pipelines testing specific areas.

##### Domain Analyst

> Understand what this project actually does — its purpose, domain, and core logic at `{repo-path}`. Write findings to `{workspace}/exploration/domain.md`.
>
> Tasks:
> 1. **Project purpose** — what problem does this solve? Who is it for? Read README and overview files
> 2. **Core domain concepts** — key nouns and verbs, mental model needed to understand the project
> 3. **Data models** — key types, schemas, database models, entity relationships
> 4. **Business rules and invariants** — validation logic, state machines, access control
> 5. **Key algorithms and logic** — core non-trivial logic, main code paths traced
> 6. **Existing documentation** — README, design docs, ADRs, explanatory comments
> 7. **Project maturity** — version, release history, test coverage, contributor activity
> 8. **Non-obvious gotchas** — FIXME/HACK/WORKAROUND comments, ordering dependencies, confusing naming
>
> Read deeply — understand actual code, not just file categories.
>
> Cross-teammate messaging: Message `interface-mapper` about domain concepts shaping the API. Message `architect` about business rules enforced through error handling. Message `toolchain-scout` about gotchas related to setup.

##### Historian

> Mine the project's history, evolution, community, and security posture at `{repo-path}`. Write findings to `{workspace}/exploration/history.md`.
>
> Tasks:
> 1. **Recent git history** — last 50-100 commits: active areas, frequency, development phases. Use `git log --oneline -100` and `git log --since="6 months ago" --format="%h %ad %s" --date=short`
> 2. **Pull request analysis** — recent merged PRs (20-30): change types, priorities. Use `gh pr list --state merged --limit 30 --json number,title,mergedAt,body,labels` if available
> 3. **Issue landscape** — open and recent issues: reports, requests. Use `gh issue list --limit 30 --json number,title,labels,body,state` if available
> 4. **Release history** — versioning, cadence, changelog. Use `gh release list` and `git tag --sort=-creatordate | head -20`
> 5. **Contributor patterns** — solo/team/community? Activity? Use `git shortlog -sn --no-merges | head -20`
> 6. **Decision trail** — ADRs, CHANGELOG, design docs, RFCs
> 7. **Community signals** — LICENSE, CONTRIBUTING.md, code of conduct, issue/PR templates
> 8. **Security posture** — SECURITY.md, advisories, dependency audit tools, auth/crypto patterns
>
> Before using `gh`, verify availability and authentication. If unavailable, rely on git and filesystem — note the gap.
>
> Cross-teammate messaging: Message `architect` about historical decisions explaining current architecture. Message `domain-analyst` about issues reporting bugs or gotchas. Message `toolchain-scout` about contributor workflow expectations.

#### 3c: Monitor Completion

**Primary signal:** Idle notifications from the team system. When a teammate finishes, the lead receives a notification automatically. Peer DM summaries appear in idle notifications — use as synthesis input.

**Completion rule:** Wait for all 6 idle notifications before proceeding to synthesis. Do NOT start synthesis early — partial data produces incomplete understanding.

**Verification:** After all idle notifications, verify each expected output file exists in the workspace via `Glob` or `Read`.

**Timeout:** If no idle notifications or task status changes (via `TaskGet`) for 5 minutes, proceed with available findings. "Activity" means: idle notification received, or a task moving to `completed`.

**Partial completion:** Always proceed with available findings rather than blocking. Note which teammates failed and why in synthesis — partial understanding with known gaps beats blocking indefinitely.

**Small projects:** If the Cartographer reports fewer than 20 source files, consider dismissing remaining teammates early and proceeding with available reports.

### Phase 4: Synthesize Findings

Read all exploration reports from the workspace. Synthesize in order:

1. **Confirm project identity** — reconcile Cartographer's classification with Domain Analyst's purpose and Interface Mapper's capabilities. Build a clear "what this project is and does" statement
2. **Map architecture to structure** — combine physical layout with logical design. Where do key abstractions live? How do modules map to capabilities?
3. **Connect interfaces to implementation** — Interface Mapper found what's exposed; Architect found how it's built. Connect entry points to internal flows
4. **Add historical context** — Historian's findings explain *why* architecture and interfaces look the way they do. Note trajectory: what's actively changing, stable, deprecated
5. **Assess project health** — combine contributor patterns and release cadence with CI/CD and test infrastructure
6. **Resolve contradictions** — when teammates disagree, investigate. Note genuine ambiguity rather than guessing
7. **Build operational picture** — combine Toolchain Scout's findings with Domain Analyst's gotchas
8. **Identify knowledge gaps** — topics no teammate found information on. Honest unknowns, not silent omissions

**Source hierarchy when conflicting:**
- **Code** is ground truth for what the project does
- **Config files** are authoritative for what's intended
- **Documentation** may be stale — verify against code
- **Comments** are weakest — corroborate before citing

### Phase 5: Verify & Present

Before presenting, verify the synthesis against teammate findings:

1. **Cross-check project classification** — does the Cartographer's evidence (specific files) support the identity statement?
2. **Verify key claims** — spot-check 3-5 specific claims (commands, file paths, API endpoints) against the relevant exploration report
3. **Confirm no fabrication** — every capability, pattern, or convention cited in the synthesis should trace to a teammate's finding. If it doesn't, remove it or re-read the report
4. **Flag unresolved gaps** — if synthesis contains hedged language ("likely", "appears to"), either confirm from reports or mark explicitly as uncertain

Present a structured summary — dense and informative:

```
## {Project Name}

**What it is:** [1-2 sentences: type, purpose, audience]
**Built with:** [key technologies and frameworks]
**Size:** [file count, language breakdown, package count if monorepo]
**Maturity:** [active/stable/maintenance-mode, contributor count, release cadence]

### Architecture
[3-5 sentences: how pieces connect, key abstractions, data flow]

### Key Capabilities
[Bulleted: APIs, CLI commands, features, what it can do]

### How to Work With It
[Setup, build, test — essential commands]

### Project Health & History
[Development activity, recent focus, key design decisions, security posture]

### Notable
[2-3 things that would surprise or interest someone new]
```

Then: "I've completed the exploration. Ask me anything about this codebase — I have detailed findings on structure, architecture, interfaces, toolchain, domain logic, and project history."

**Keep workspace files available** during Q&A. If a detailed question exceeds the synthesis, re-read the relevant exploration report.

### Phase 6: Cleanup

When the user signals they're done (moves to another task, says "thanks", starts unrelated work), clean up. Do not ask before cleaning — these are transient working artifacts.

Follow the cleanup resilience protocol from `references/agent-teams.md`:

1. **Shutdown loop** — for each teammate, send up to 3 shutdown requests with escalating context:
   - Attempt 1: `{type: "shutdown_request", reason: "Exploration complete"}`
   - Attempt 2 (if no idle after 60s): "All exploration is complete, findings have been saved. Please shut down."
   - Attempt 3 (if no idle after 60s): "Session ending. Cleanup requires all teammates to shut down. This is the final request."
   - If no idle after 30s: classify as **orphaned** with reason.
2. **TeamDelete** — call `TeamDelete`. If it fails (orphaned teammates still active), report degraded state:
   "Team cleanup partially failed: [N] teammate(s) did not shut down ([names]). Team resources may remain at `~/.claude/teams/repo-exploration/`. These will be cleaned up when a new team is created, or remove manually."
3. **Workspace** — remove `.explore-workspace/`. Workspace cleanup is independent of team cleanup — always attempt regardless of TeamDelete outcome.
4. **Temp clone** — if a remote repo was cloned to `/tmp/explore-repo/`, remove it.

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop — do not fall back |
| TeamCreate fails | Phase 3a step 1 | Hard stop — cannot proceed without team |
| Teammate spawn fails | Phase 3b | Log, continue with remaining. All fail = hard stop |
| Teammate timeout | No activity for 5 min | Treat as failed, proceed with available findings |
| Missing output file | Phase 3c verification | Log as coverage gap in synthesis |
| Clone fails (remote mode) | Phase 1 | Check URL, auth, network. Retry once, then ask user |
| Stale workspace | Phase 2 setup | Warn user, offer: archive / remove / abort |
| TeamDelete fails | Phase 6 cleanup | Report degraded state, proceed with workspace cleanup |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Lead exploring before teammates finish | Duplicates work, biases synthesis | Lead frames and synthesizes; teammates investigate |
| Declaring done before all teammates complete | Incomplete understanding with silent gaps | Wait for all 6 idle notifications |
| Using Agent tool without team_name | No messaging, shared tasks, or idle notifications | Always set team_name to match TeamCreate |
| Partitioning directories among teammates | Gaps at cross-directory boundaries | All teammates access all files, scoped by perspective |
| Starting synthesis on partial findings | Missing cross-references between perspectives | Wait for completion or timeout, then note gaps explicitly |

## References

| File | When to read |
|------|-------------|
| [`references/agent-teams.md`](references/agent-teams.md) | Phase 3: team lifecycle, messaging, completion detection, cleanup protocol |
