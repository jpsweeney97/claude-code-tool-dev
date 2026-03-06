---
name: readme-gen
description: Generate comprehensive, high-quality README documents for any software project. Enforces a 5-phase pipeline - Explore (subagent inventory) → Classify (project type) → Audit (coverage gaps) → Write (fill gaps) → Verify (checklist). Use when user says "write a README", "create README", "document this project", "audit the README", "improve the README", "check README quality", or when creating documentation for a new project.
---

# README Generation

README quality is won or lost in the exploration phase, not the writing phase. Claude already knows how to write — the failure mode is writing from incomplete knowledge, then producing a README that sounds comprehensive but silently misses coverage areas.

This skill enforces a 5-phase pipeline that prevents that failure:

1. **Explore** — Launch a subagent to inventory the entire codebase. Non-negotiable.
2. **Classify** — Determine project type from exploration results.
3. **Audit** — Compare existing README (if any) against the project type's section checklist. Identify gaps.
4. **Write** — Fill gaps. Enhance where coverage exists but lacks depth.
5. **Verify** — Self-audit the result against the checklist. Report coverage.

Each phase has a gate. You cannot proceed without evidence from the previous phase.

**Scope:** This skill covers README files only. It does not cover changelogs, contributing guides, API documentation, or any other documentation artifact.

## Phase 1: Explore

Launch an Explore subagent with the following prompt template. Replace `{path}` with the project root.

> Thoroughly explore the project at {path}. Return a complete inventory:
>
> 1. Read the manifest/package file (package.json, pyproject.toml, Cargo.toml, go.mod, etc.)
> 2. Read ALL configuration files
> 3. List ALL source files with their purposes
> 4. List ALL test files and what they test
> 5. Identify: entry points, CLI interface, public API, hooks, plugins, scripts, agents, skills
> 6. Note dependencies (runtime vs dev)
> 7. Note any existing documentation files
> 8. Run the test suite and report the count (e.g., `uv run pytest --co -q | tail -1`)
>
> Final response under 8000 characters. Structured inventory format.

**Gate:** Do not proceed until the subagent returns. Read the full inventory before continuing.

## Phase 2: Classify

Determine the project type from the exploration results. Select exactly one:

| Type | Signals |
|------|---------|
| Library | Published package, public API, imported by others, no CLI entry point |
| CLI Tool | Argument parser, subcommands, entry point script, `--help` output |
| API / Service | HTTP server, routes/endpoints, request handlers, middleware |
| Plugin / Extension | Manifest file (`plugin.json`, `package.json` with `engines`), hooks, skills, agents |
| MCP Server | MCP protocol implementation, tools/resources, stdio/SSE transport |
| Framework | Scaffolding, project templates, conventions for user code |

If the project matches multiple types (e.g., a library with a CLI), choose the **primary** type — the one that best describes what a user would look up the README for.

**Default for unlisted types:** If the project doesn't match any type above (e.g., data pipeline, game, documentation site, monorepo), use the **Universal sections only** from the checklist. Add type-specific sections based on what the exploration found — there is no checklist to fall back on, so derive sections from the inventory.

**Gate:** State the classified type and your reasoning in one sentence before proceeding.

## Phase 3: Audit

Read the project type's section checklist from [section-checklists.md](references/section-checklists.md).

**If a README exists:** Read it. For each checklist item, score:
- **Covered** — Section exists with adequate depth
- **Shallow** — Section exists but lacks architectural depth or practical detail
- **Missing** — Section does not exist

Present the audit as a table. Example:

| Section | Status | Notes |
|---------|--------|-------|
| Problem statement | Missing | No motivation section |
| Installation | Covered | |
| Architecture | Shallow | Lists components but doesn't explain data flow |
| CLI interface | Missing | Commands exist but aren't documented |
| Tests | Shallow | Has run command but no file-level breakdown |

**If no README exists:** Skip the audit table. The entire checklist is the plan.

**Gate:** Present the audit results to the user. Get confirmation before writing.

## Phase 4: Write

Fill gaps and enhance shallow sections. Follow these rules:

- **Enhance, don't rewrite** — If existing content is good, keep it. Add around it.
- **Tables for reference data** — Field lists, CLI flags, test files, configuration options.
- **Prose for concepts** — Architecture, design decisions, problem statements.
- **Examples for formats** — Show a concrete instance of the file format, config file, or API call.
- **Verify claims against exploration** — Every file path, field name, test count, and CLI flag must come from the exploration results. Do not hallucinate specifics.

For each section, ask: "Does this explain both HOW it works and HOW TO USE it?"

Architecture sections should answer: What are the components? How do they connect? What are the design properties (fail-open/closed, security, immutability)?

Practical sections should answer: What command do I run? What does the output look like? What configuration options exist?

## Phase 5: Verify

After writing, self-audit against the checklist:

1. Re-read the section checklist for this project type
2. Confirm every item is now Covered (not Shallow, not Missing)
3. Spot-check 3 specific claims against the exploration results (file paths, test counts, field names)
4. Report: "Checklist: X/Y sections covered. Spot-checked: [claim 1], [claim 2], [claim 3] — all verified."

**Gate:** Do not claim the README is complete until verification passes.

## Red Flags

These thoughts mean STOP — you're about to compromise quality:

| Thought | Reality |
|---------|---------|
| "I already know this codebase" | Launch the explorer anyway. You miss things. |
| "The existing README is pretty good" | Run the audit. "Pretty good" hides gaps. |
| "I'll just read a few key files" | Partial exploration produces partial READMEs. Use the subagent. |
| "This project is simple enough to skip classification" | Classification selects the checklist. Skip it, miss sections. |
| "I can write and verify at the same time" | Write first, verify separately. Concurrent verification is theater. |
| "The user seems impatient, I'll skip the audit" | Presenting the audit takes 30 seconds. Rewriting a bad README takes 30 minutes. |

## Failure Modes

| If you skip... | You get... |
|----------------|------------|
| Exploration | README based on assumptions. Hallucinated file paths, wrong test counts, missing components. |
| Classification | Wrong section checklist. Plugin README without hooks section. Library README without API reference. |
| Audit | No gap awareness. You rewrite good sections and miss bad ones. |
| Verification | False confidence. "Looks complete" without evidence. |
