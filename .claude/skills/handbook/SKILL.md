---
name: handbook
description: Create, audit, and update operational handbooks — technical reference documents covering bring-up, runbooks, failure recovery, internals, and verification for any software system. Orchestrates an agent team to explore the system from five operational perspectives in parallel, then synthesizes findings into grounded documentation. Distinct from READMEs (what it is) and CHANGELOGs (what changed). Use this skill whenever the user wants to document how to **operate** a system. Trigger on: "write a handbook", "create an operational runbook", "document how this system works", "audit this handbook", "update the handbook", "write a technical reference", "write runbooks for X", "document the bring-up procedure", or when the user says "document it" about a system with multiple entrypoints, safety controls, or operational complexity and a README isn't clearly what they need. Default to this skill over README generation when the subject is an existing running system rather than a new project being introduced to users.
---

# Handbook Skill

Create and maintain operational handbooks grounded in comprehensive, parallel system exploration. Uses an agent team to investigate architecture, interfaces, operations, failure modes, and existing documentation simultaneously — producing handbooks that reflect what the system actually does, not what someone remembers it doing.

An **operational handbook** is the "how to operate and understand this system" layer. It is not:
- A README (which introduces the system to users)
- A CHANGELOG (which tracks history)
- API docs (which describe individual functions)

A handbook is for operators: people who need to bring up, run, debug, maintain, or extend the system.

## Prerequisite

This skill requires agent teams. Before proceeding, verify the feature is enabled:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

If not enabled, tell the user: "This skill uses agent teams for deep parallel system exploration. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json env block, then restart the session." Do not fall back to a single-subagent approach — the depth difference is what makes handbooks operationally useful rather than superficially structural.

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

## Step 2: Launch Exploration Team

Create an agent team with 5 teammates. Each investigates the system from a different operational perspective, writing findings to the workspace.

**Critical: known failure modes to guard against:**
- **Do not substitute the Agent tool for agent teams.** If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` and use it. The Agent tool with `run_in_background` looks similar but lacks teammate-to-teammate messaging, coordinated completion detection, and shared task state — leading to polling races and lost coordination. Agent teams and the Agent tool are not interchangeable.
- The lead may start exploring the system itself instead of waiting for teammates. If you catch yourself reading source files before teammates finish, stop. Your job is to coordinate, then synthesize.
- The lead may declare the team finished before all teammates complete. Wait for all 5 idle notifications before proceeding to synthesis.
- Task status can lag — check the workspace for output files as a secondary completion signal.

Tell the lead to create these teammates with these prompts:

### Teammate 1: Architecture Scout

> Map the internal architecture of the system at `{system-path}`. Your deliverable helps operators understand how the pieces connect.
>
> Tasks:
> 1. **Module inventory** — every source file with a one-line responsibility. Group by logical subsystem
> 2. **Dependency graph** — external dependencies: what each is used for, which are critical at runtime vs build-time only. Flag unusual or security-sensitive dependencies
> 3. **Internal data flow** — how data moves through the system. Entry points → processing → output. Key abstractions and where they live
> 4. **Design patterns** — recurring patterns (middleware pipeline, event bus, repository pattern, etc.). Name them so the handbook can reference them
> 5. **Contracts and specs** — normative reference documents (specs, protocols, schemas). Summarize each in 2-3 sentences
>
> Focus on runtime behavior, not just static structure. "Module X calls module Y when Z happens" is more useful than "module X imports module Y."
>
> When you discover something relevant to another teammate's mandate, message them directly. For example, if you find a complex error handling pattern, message the Safety & Failure Analyst. If you discover undocumented entry points, message the Interface Cataloger.
>
> Write your findings to `{workspace}/exploration/architecture.md`.

### Teammate 2: Interface Cataloger

> Catalog everything this system exposes to operators and users at `{system-path}`. Your deliverable is the complete surface area.
>
> Tasks:
> 1. **Entry points** — every way to invoke the system: CLI commands, API endpoints, scripts, hooks, MCP tools, skills, agents. For each: name, purpose, inputs with types and defaults, outputs, execution model
> 2. **Configuration** — all configuration surfaces: env vars, config files, settings, flags. For each: name, type, default, purpose, where it's read
> 3. **Extension points** — hooks, plugin APIs, middleware interfaces, event systems — anything that lets operators or users extend behavior
> 4. **Output formats** — what the system produces: files, logs, API responses, side effects. Where they go and what they look like
>
> Be exhaustive — a handbook that misses an entry point is a handbook that will surprise an operator.
>
> When you discover configuration that affects runtime behavior, message the Operations Analyst. When you find extension points with safety implications, message the Safety & Failure Analyst.
>
> Write your findings to `{workspace}/exploration/interfaces.md`.

### Teammate 3: Operations Analyst

> Investigate the operational requirements and runtime behavior of `{system-path}`. Your deliverable helps operators bring up, run, and maintain the system.
>
> Tasks:
> 1. **Prerequisites** — everything needed before the system can run: runtimes, system dependencies, accounts, credentials, services. Include version requirements
> 2. **Bring-up procedure** — step-by-step: install → configure → verify → first run. Note non-obvious ordering dependencies
> 3. **Runtime behavior** — what happens at startup, steady state, and shutdown. Background processes, scheduled tasks, file watchers, connection pools
> 4. **Environment assumptions** — what the system expects: directory structure, file permissions, network access, OS features
> 5. **Development workflow** — how to run in development mode, run tests, format/lint, iterate. Watch modes or hot reload support
> 6. **Observability** — where do logs go? What format and log levels exist? Are there metrics, health check endpoints, or monitoring hooks? How does an operator read logs during an incident?
>
> Try to mentally execute the bring-up procedure. If a step depends on something not set up earlier, note the gap.
>
> If the system is a pure library with no runtime process, focus on install, test invocation, and development workflow. Skip runtime behavior, startup/shutdown, and environment assumptions — these don't apply to libraries.
>
> When you discover runtime failure scenarios, message the Safety & Failure Analyst. When you find prerequisite tools or dependencies, message the Architecture Scout to confirm they're in the dependency graph.
>
> Write your findings to `{workspace}/exploration/operations.md`.

### Teammate 4: Safety & Failure Analyst

> Analyze the failure modes, safety controls, and error handling of `{system-path}`. Your deliverable helps operators know what can go wrong and how to recover.
>
> Tasks:
> 1. **Error handling patterns** — how does the system handle errors? Retry, fail fast, fall back, silently swallow? Map patterns by subsystem
> 2. **Validation and guards** — input validation, auth checks, permission gates, rate limits, sanitization. What gets blocked and what gets through
> 3. **Known failure modes** — from error handling code, test assertions, and existing docs: what specific things can go wrong? For each: symptom, likely cause, diagnosis steps, recovery
> 4. **Safety controls** — sandboxing, credential handling, dangerous-operation guards, audit logging. What prevents bad outcomes
> 5. **Edge cases from tests** — test files encode known edge cases and failure scenarios. What do the tests reveal about what the system's authors worry about? If no test suite exists, note this explicitly as a coverage gap — the absence of tests is itself a finding.
> 6. **Data sensitivity** — what data flows through the system? What's sensitive (credentials, PII, tokens)? What gets logged vs redacted? Are there retention policies or cleanup procedures?
>
> Pay special attention to silent failures — catch blocks that swallow exceptions, fallbacks that mask errors, retries without limits.
>
> When you find failure modes tied to specific entry points, message the Interface Cataloger so they can note it in their surface area inventory. When you find safety controls that affect the bring-up procedure, message the Operations Analyst.
>
> Write your findings to `{workspace}/exploration/safety-failures.md`.

### Teammate 5: Documentation Auditor

> Audit all existing documentation for the system at `{system-path}`. Your deliverable maps what's documented, what's stale, and what's missing.
>
> Tasks:
> 1. **Documentation inventory** — all docs: README, HANDBOOK, inline comments, doc comments, docs/ directory, wiki references, external links. For each: path, scope, freshness estimate
> 2. **Claims extraction** — if an existing handbook or README exists, extract every factual claim (file paths, commands, behaviors, config options). Create a claims checklist for other teammates to verify
> 3. **Test suite implications** — what does the test suite tell you about intended behavior? Tests encode invariants that documentation should reflect. If no test suite exists, note this as a significant coverage gap and flag it for the handbook's Known Limitations section.
> 4. **Staleness signals** — references to deleted files, old APIs, deprecated features, stale versions. Cross-reference doc file ages against source file ages
> 5. **Coverage gaps** — directories or components with significant code but no documentation. Rank by operational importance
>
> Share your claims checklist with specific teammates. Message the Architecture Scout about internal design claims, the Interface Cataloger about entry point and config claims, the Operations Analyst about setup and runtime claims, and the Safety Analyst about failure mode claims. Use targeted messages, not broadcast.
>
> Write your findings to `{workspace}/exploration/documentation.md`.

### Workspace Setup

Before spawning the team, create the workspace directory:

```
{system-root}/.handbook-workspace/exploration/
```

Tell each teammate to write their findings to this directory. Cleanup is handled automatically after completion (see Cleanup section).

### Task Structure

Instruct the lead to create tasks with these dependencies:

1. All 5 exploration tasks (independent, no dependencies between them)
2. "Synthesize exploration findings" (depends on all 5 completing)
3. "Select handbook sections" (depends on synthesis)
4. "Write handbook" (depends on section selection)

**Important:** Explicitly tell the lead: "Wait for all teammates to complete their exploration tasks before starting synthesis. Do not begin synthesis, section selection, or writing until all 5 exploration reports exist in the workspace."

## Step 3: Synthesize Findings

Teammates do not inherit the lead's conversation history — they start fresh with only their spawn prompt and the project's CLAUDE.md/skills. This is why each teammate prompt above is self-contained with explicit deliverables and output paths. Do not assume teammates know the user's original request or the handbook mode.

After all teammates complete, read all 5 reports. Synthesize into a unified operational understanding:

1. **Confirm system type** — determine whether this is a service, library, CLI tool, plugin, or hybrid. Corroborate using Architecture Scout's module inventory and Interface Cataloger's entry points. This classification informs section selection in Step 4
2. **Cross-reference architecture and interfaces** — the Architecture Scout maps internal structure; the Interface Cataloger maps external surface. Together they reveal which internals are user-facing and which are implementation detail
3. **Resolve contradictions** — if teammates found conflicting information, investigate. Note genuine ambiguity in the handbook rather than guessing
3. **Build the failure picture** — combine the Safety Analyst's failure modes with the Operations Analyst's runtime behavior. Every operational step should have its failure modes paired
4. **(Audit/Update) Build claims verdict** — go through the Documentation Auditor's claims checklist. Mark each claim as confirmed, outdated, or wrong based on other teammates' findings
5. **Identify coverage gaps** — topics no teammate found data on. These become known unknowns in the handbook, not silent omissions

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
6. **Bring-up sequence is copy-paste-runnable** — every command in Configuration and Bring-Up must execute as written from a fresh checkout, not just be conceptually correct
7. **No fabricated content** — every claim traces back to an exploration finding
8. **Internal consistency** — key facts (version requirements, dependencies, file paths, config defaults) must not contradict across sections. Spot-check: does the Overview's stated requirements match the Bring-Up section's prerequisites?

If any check fails, fix it before delivering.

### Output Placement

Unless the user specifies otherwise, place the handbook at `HANDBOOK.md` in the system's root directory.

## Scoped Handbooks

When documenting a single service or package within a larger system:

1. **Scope the team** to that directory and its immediate dependencies
2. **Select sections** for the scoped system's type — a plugin within a monorepo gets plugin-appropriate sections, not monorepo-level sections
3. **Reference the root handbook** for shared operational context: "See the [root handbook](../../HANDBOOK.md) for workspace-level setup and cross-cutting operations"
4. **Don't duplicate** — shared infrastructure, CI/CD, or environment setup that belongs in the root handbook shouldn't be repeated

## Cleanup

After the handbook is complete and delivered, clean up automatically — do not ask:

1. Shut down all teammates via `SendMessage` with `type: "shutdown_request"`
2. Remove the workspace directory (`.handbook-workspace/`)
3. Remove team files (`~/.claude/teams/<team-name>/`)
4. Remove task files (`~/.claude/tasks/<team-name>/`)

These are transient working artifacts, not deliverables.
