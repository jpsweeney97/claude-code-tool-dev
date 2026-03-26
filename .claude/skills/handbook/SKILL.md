---
name: handbook
description: Create, audit, and update operational handbooks — technical reference documents covering bring-up, runbooks, failure recovery, internals, and verification for any software system. Orchestrates an agent team to explore the system from five operational perspectives in parallel, then synthesizes findings into grounded documentation. Distinct from READMEs (what it is) and CHANGELOGs (what changed). Use this skill whenever the user wants to document how to **operate** a system. Trigger on: "write a handbook", "create an operational runbook", "document how this system works", "audit this handbook", "update the handbook", "write a technical reference", "write runbooks for X", "document the bring-up procedure", or when the user says "document it" about a system with multiple entrypoints, safety controls, or operational complexity and a README isn't clearly what they need. Default to this skill over README generation when the subject is an existing running system rather than a new project being introduced to users.
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

# Handbook Skill

Create and maintain operational handbooks grounded in comprehensive, parallel system exploration. Uses an agent team to investigate architecture, interfaces, operations, failure modes, and existing documentation simultaneously — producing handbooks that reflect what the system actually does, not what someone remembers it doing.

An **operational handbook** is the "how to operate and understand this system" layer. It is not:
- A README (which introduces the system to users)
- A CHANGELOG (which tracks history)
- API docs (which describe individual functions)

A handbook is for operators: people who need to bring up, run, debug, maintain, or extend the system.

**Announce at start:** "I'm using the handbook skill to [create/audit/update] this handbook."

## Prerequisite

This skill requires agent teams. Verify the feature is enabled before any other work:

Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams for deep parallel system exploration. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential exploration — parallel multi-perspective exploration is the skill's value proposition.

## Constraints

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams required | Hard prerequisite. Do NOT fall back to sequential or Agent-tool-only alternatives. |
| 2 | Sonnet for teammates | Spawn all teammates with `model: "sonnet"`. Lead uses the session's default model. |
| 3 | Teammates lack conversation history | Each teammate starts fresh with only its spawn prompt plus the project's CLAUDE.md/skills. The lead's conversation does NOT carry over — include everything teammates need in their spawn prompts. |
| 4 | One team per session | No nested teams. Clean up before starting a new one. |
| 5 | 5 teammates | Architecture Scout, Interface Cataloger, Operations Analyst, Safety & Failure Analyst, Documentation Auditor. |

See `references/agent-teams.md` for the full agent teams API reference.

## Modes

| Mode | When | What happens |
|------|------|-------------|
| **Create** | No handbook exists; "write a handbook for X" | Full exploration → section selection → write |
| **Audit** | Handbook exists; "audit", "check", "is this up to date?" | Full exploration → compare claims vs reality → report |
| **Update** | Specific changes described; "update the handbook for X" | Targeted exploration → update affected sections |

Detect the mode from context. If unclear, ask once: "Do you want to create a new handbook, audit an existing one, or update specific sections?"

## README Redirect

Before starting, check whether the user actually needs a README rather than a handbook.

**Redirect signals** — the request focuses on:
- What the project is and why it exists
- How to install and use it as a consumer
- How to contribute or extend it
- Introducing a new project to users

**Redirect action:** "This sounds like a README — introducing the project to users or contributors. The readme skill is better suited. Want me to use that instead?"

**Handbook signals** — the request focuses on:
- How to deploy, run, or monitor a system
- Failure recovery, debugging, or incident response
- Internal mechanics for operators
- "Document how this works" for an existing running service

Proceed with this skill when handbook signals are present.

## Step 1: Determine Scope

Identify the system to document:

1. **System root** — what directory contains the system? A package, a service, the whole repo?
2. **Existing handbook** — does one already exist? Read it before exploration so the team knows what claims to verify
3. **Audience** — who are the operators? (Developers on the team? SREs? End users running it locally?) This affects depth and terminology

## Step 2: Explore the System

Explore the system from 5 operational perspectives in parallel using an agent team. Each teammate investigates one dimension and writes structured findings to the workspace.

### Phase 1: Setup

1. Create the workspace directory: `{system-root}/.handbook-workspace/exploration/`
2. Verify `.handbook-workspace/` is in `.gitignore`. If absent, add it.

### Phase 2: Create Team and Tasks

If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.

1. **Create the team** via `TeamCreate` with `team_name: "handbook-exploration"` and a description of the handbook task.
2. **Create one task per teammate** via `TaskCreate`. Each task describes the teammate's exploration mandate and output path. Do NOT set `blockedBy` dependencies — all 5 tasks run in parallel.

| Task | Teammate ID | Output file |
|------|-------------|-------------|
| Map internal architecture | `architecture-scout` | `exploration/architecture.md` |
| Catalog interfaces and surface area | `interface-cataloger` | `exploration/interfaces.md` |
| Investigate operational requirements | `operations-analyst` | `exploration/operations.md` |
| Analyze failure modes and safety | `safety-analyst` | `exploration/safety-failures.md` |
| Audit existing documentation | `documentation-auditor` | `exploration/documentation.md` |

### Phase 3: Spawn Teammates

Spawn all 5 teammates using the `Agent` tool. The `team_name` parameter is what makes a spawned agent a teammate with messaging, shared tasks, and idle notifications. Without `team_name`, the agent is an isolated subagent with none of those capabilities.

**Design principle:** All teammates access all system files — they are scoped by operational perspective, not by directory. Do NOT partition the codebase among teammates.

For each teammate, call `Agent` with:
- `team_name`: `"handbook-exploration"` (must match TeamCreate)
- `name`: the teammate ID from the table above — this is the addressing key for all communication
- `model`: `"sonnet"`
- `prompt`: the spawn prompt below

Spawn all 5 in the same message to maximize parallelism. Do NOT start your own exploration or analysis before all teammates are spawned — your job is to coordinate and then synthesize.

#### Architecture Scout

```
Map the internal architecture of the system at {system-path}. Write findings to {workspace}/exploration/architecture.md.

Tasks:
1. **Module inventory** — every source file with a one-line responsibility. Group by logical subsystem
2. **Dependency graph** — external dependencies: what each is used for, which are critical at runtime vs build-time. Flag unusual or security-sensitive ones
3. **Internal data flow** — how data moves through the system. Entry points → processing → output. Key abstractions and where they live
4. **Design patterns** — recurring patterns (middleware pipeline, event bus, repository pattern, etc.)
5. **Contracts and specs** — normative reference documents (specs, protocols, schemas). Summarize each in 2-3 sentences

Focus on runtime behavior, not just static structure. "Module X calls module Y when Z happens" is more useful than "module X imports module Y."

When you discover something relevant to another teammate, message them directly. If you find complex error handling patterns, message safety-analyst. If you discover undocumented entry points, message interface-cataloger.
```

#### Interface Cataloger

```
Catalog everything this system exposes to operators and users at {system-path}. Write findings to {workspace}/exploration/interfaces.md.

Tasks:
1. **Entry points** — every way to invoke the system: CLI commands, API endpoints, scripts, hooks, MCP tools, skills, agents. For each: name, purpose, inputs with types and defaults, outputs, execution model
2. **Configuration** — all config surfaces: env vars, config files, settings, flags. For each: name, type, default, purpose, where it's read
3. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems
4. **Output formats** — what the system produces: files, logs, API responses, side effects. Where they go and what they look like

Be exhaustive — a handbook that misses an entry point is a handbook that will surprise an operator.

When you discover config that affects runtime behavior, message operations-analyst. When you find extension points with safety implications, message safety-analyst.
```

#### Operations Analyst

```
Investigate operational requirements and runtime behavior of {system-path}. Write findings to {workspace}/exploration/operations.md.

Tasks:
1. **Prerequisites** — everything needed before the system can run: runtimes, system dependencies, accounts, credentials, services with version requirements
2. **Bring-up procedure** — step-by-step: install → configure → verify → first run. Note non-obvious ordering dependencies
3. **Runtime behavior** — what happens at startup, steady state, and shutdown. Background processes, scheduled tasks, file watchers, connection pools
4. **Environment assumptions** — what the system expects: directory structure, file permissions, network access, OS features
5. **Development workflow** — how to run in dev mode, run tests, format/lint, iterate. Watch modes or hot reload
6. **Observability** — where do logs go? What format and levels? Metrics, health checks, monitoring hooks?

Try to mentally execute the bring-up procedure. If a step depends on something not set up earlier, note the gap.

If the system is a pure library with no runtime process, focus on install, test invocation, and dev workflow. Skip runtime behavior and environment assumptions.

When you discover runtime failure scenarios, message safety-analyst. When you find prerequisite tools, message architecture-scout to confirm they're in the dependency graph.
```

#### Safety & Failure Analyst

```
Analyze failure modes, safety controls, and error handling of {system-path}. Write findings to {workspace}/exploration/safety-failures.md.

Tasks:
1. **Error handling patterns** — how does the system handle errors? Retry, fail fast, fall back, silently swallow? Map patterns by subsystem
2. **Validation and guards** — input validation, auth checks, permission gates, rate limits, sanitization
3. **Known failure modes** — from error handling code, test assertions, existing docs: what can go wrong? For each: symptom, likely cause, diagnosis, recovery
4. **Safety controls** — sandboxing, credential handling, dangerous-operation guards, audit logging
5. **Edge cases from tests** — test files encode known edge cases. What do they reveal about what the authors worry about? If no test suite exists, note this explicitly
6. **Data sensitivity** — what data flows through? What's sensitive? What gets logged vs redacted?

Pay special attention to silent failures — catch blocks that swallow exceptions, fallbacks that mask errors, retries without limits.

When you find failure modes tied to specific entry points, message interface-cataloger. When you find safety controls that affect bring-up, message operations-analyst.
```

#### Documentation Auditor

```
Audit all existing documentation for the system at {system-path}. Write findings to {workspace}/exploration/documentation.md.

Tasks:
1. **Documentation inventory** — all docs: README, HANDBOOK, inline comments, doc comments, docs/ directory, wiki references, external links. Path, scope, freshness estimate for each
2. **Claims extraction** — if an existing handbook or README exists, extract every factual claim (file paths, commands, behaviors, config options) into a claims checklist
3. **Test suite implications** — what does the test suite tell you about intended behavior? If no test suite exists, note this as a significant coverage gap
4. **Staleness signals** — references to deleted files, old APIs, deprecated features, stale versions
5. **Coverage gaps** — directories or components with significant code but no documentation. Rank by operational importance

Share your claims checklist with specific teammates. Message architecture-scout about design claims, interface-cataloger about entry point/config claims, operations-analyst about setup/runtime claims, safety-analyst about failure mode claims. Use targeted messages, not broadcast — broadcast costs scale with team size.
```

### Phase 4: Monitor Completion

**Primary signal:** idle notifications from the team system. When a teammate finishes and goes idle, the lead receives a notification. Peer DM summaries appear in idle notifications — use these as synthesis input.

**Completion rule:** Wait for all 5 idle notifications before proceeding to synthesis. Do NOT start synthesis early — partial exploration data produces incomplete handbooks.

**Verification:** After all idle notifications, verify each expected output file exists in the workspace via `Glob` or `Read`.

**Timeout:** If no idle notifications or task status changes (confirmed via `TaskGet`) arrive for 5 minutes, proceed with available findings. "Activity" means: idle notification received, or a task moving to `completed`.

**Partial completion:** Always proceed with available findings rather than blocking. Note which teammates failed and why in your synthesis — a handbook with known coverage gaps is better than no handbook.

## Step 3: Synthesize Findings

After all teammates complete, read all 5 reports from the workspace. Synthesize into a unified operational understanding:

1. **Confirm system type** — service, library, CLI tool, plugin, or hybrid. Corroborate using Architecture Scout's module inventory and Interface Cataloger's entry points. This classification informs section selection in Step 4
2. **Cross-reference architecture and interfaces** — the Architecture Scout maps internal structure; the Interface Cataloger maps external surface. Together they reveal which internals are user-facing and which are implementation detail
3. **Resolve contradictions** — if teammates found conflicting information, investigate. Note genuine ambiguity in the handbook rather than guessing
4. **Build the failure picture** — combine the Safety Analyst's failure modes with the Operations Analyst's runtime behavior. Every operational step should have its failure modes paired
5. **(Audit/Update) Build claims verdict** — go through the Documentation Auditor's claims checklist. Mark each claim as confirmed, outdated, or wrong based on other teammates' findings
6. **Identify coverage gaps** — topics no teammate found data on. These become known unknowns in the handbook, not silent omissions

## Step 4: Select Sections

Based on the synthesis, decide which handbook sections to include. Read `references/section-templates.md` for the canonical section list and templates.

**Gate:** State which sections you're including and one-line reasoning for each before writing. Skip sections with nothing substantive — a sparse section is worse than no section.

## Step 5: Write the Handbook

### Create Mode

Write each section using the templates from `references/section-templates.md`. Follow these rules:

**Grounding:** Every claim must trace back to an exploration finding. Do not invent behaviors, commands, or configuration. If a section template expects content the team didn't find, either omit the section (if optional) or write "Unknown — exploration did not find evidence for this" (if required for operational safety).

**Operational voice:**
- "Run `uv run pytest`" not "tests can be run"
- Concrete file paths, not just names
- Numbered steps for procedures
- Tables for structured comparisons

**Operator audience:** Assume the reader can read code. They need: how to bring it up, what runtime assumptions it makes, what can go wrong, how to recover, and what the non-obvious invariants are. They don't need line-by-line code explanation.

**No placeholders:** If a section can't be written accurately, omit it. Never write TODO stubs.

### Audit Mode

Produce an audit report, not a rewritten handbook:

```markdown
# Handbook Audit: [System Name]

## Summary
[N accuracy issues, N coverage gaps, N currency concerns, N structural issues]

## Accuracy Issues
- [Section/claim]: [what's wrong → what's correct, with evidence]

## Coverage Gaps
- Missing: [what's absent → why operators need it]

## Currency Concerns
- [Section]: [what may be stale → what to verify against source]

## Structural Issues
- [Issue → recommendation]

## Recommended Priority
1. [Most critical fix and why]
2. ...
```

After delivering the report, offer to make the changes. Wait for confirmation.

### Update Mode

1. **Understand the change** — what changed in the system?
2. **Scope the team** — for targeted updates, you may not need all 5 teammates. Launch only those whose domain overlaps with the change (e.g., new entry point → Interface Cataloger + Operations Analyst)
3. **Locate affected sections** — find every handbook section referencing the changed component
4. **Update precisely** — change only what's affected; don't rewrite adjacent sections
5. **Verify** — confirm updated sections reflect current behavior
6. **Show diff summary** — present what changed and why before delivering

## Step 6: Verify

Before presenting the handbook:

1. **Every cited file path exists** — cross-reference with Architecture Scout's inventory
2. **Every command example runs** — cross-reference with Operations Analyst's findings
3. **Every config option is current** — cross-reference with Interface Cataloger's schema
4. **Every runbook has failure modes** — cross-reference with Safety Analyst's findings
5. **Verification procedure is executable** — mentally trace through it on the described system
6. **Bring-up sequence is copy-paste-runnable** — every command must execute as written from a fresh checkout
7. **No fabricated content** — every claim traces back to an exploration finding
8. **Internal consistency** — key facts (version requirements, dependencies, file paths, config defaults) must not contradict across sections

If any check fails, fix it before delivering.

### Output Placement

Unless the user specifies otherwise, place the handbook at `HANDBOOK.md` in the system's root directory.

## Scoped Handbooks

When documenting a single service or package within a larger system:

1. **Scope the team** to that directory and its immediate dependencies
2. **Select sections** for the scoped system's type — a plugin within a monorepo gets plugin-appropriate sections, not monorepo-level sections
3. **Reference the root handbook** for shared operational context: "See the [root handbook](../../HANDBOOK.md) for workspace-level setup and cross-cutting operations"
4. **Don't duplicate** — shared infrastructure, CI/CD, or environment setup that belongs in the root handbook shouldn't be repeated

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop — do not fall back |
| TeamCreate fails | Phase 2 step 1 | Hard stop — cannot proceed without team |
| Teammate spawn fails | Phase 3 | Log, continue with remaining. All fail = hard stop |
| Teammate timeout | No activity for 5 min | Treat as failed, proceed with available findings |
| Missing output file | Phase 4 verification | Log as coverage gap in synthesis |
| Stale workspace | Phase 1 setup | Warn user, offer: archive / remove / abort |
| TeamDelete fails | Cleanup step 3 | Teammates still active — retry shutdown, then retry |

## Cleanup

After the handbook is complete and delivered:

1. Send a shutdown request to each teammate: `SendMessage` to each by name with `{type: "shutdown_request", reason: "Handbook complete"}`. If a teammate rejects the shutdown, retry with additional context explaining that the handbook is complete.
2. Teammates finish their current tool call before shutting down — this may take a moment.
3. After all teammates go idle, call `TeamDelete` to remove shared team resources. `TeamDelete` fails if any teammate is still active — confirm all are idle first.
4. Remove the workspace directory (`.handbook-workspace/`).

These are transient working artifacts — do not ask the user about cleanup.
