---
name: handbook
description: Create, audit, and update operational handbooks — technical reference documents covering bring-up, runbooks, failure recovery, internals, and verification for any software system. Distinct from READMEs (what it is) and CHANGELOGs (what changed). Use this skill whenever the user wants to document how to **operate** a system. Trigger on: "write a handbook", "create an operational runbook", "document how this system works", "audit this handbook", "update the handbook", "write a technical reference", "write runbooks for X", "document the bring-up procedure", or when the user says "document it" about a system with multiple entrypoints, safety controls, or operational complexity and a README isn't clearly what they need. Default to this skill over README generation when the subject is an existing running system rather than a new project being introduced to users.
---

# Handbook

An **operational handbook** is the "how to operate and understand this system" layer of documentation. It is not:

- A README (which introduces the system and explains installation)
- A CHANGELOG (which tracks history)
- API docs (which describe individual functions or methods)

A handbook is for operators: people who need to bring up, run, debug, maintain, or extend the system. It covers runtime behavior, failure recovery, and internal mechanics that are not obvious from reading the source.

## Mode Detection

Determine the mode from context before doing anything else:

| Mode | Signals |
|------|---------|
| **create** | No existing handbook; source directory or repo provided; "write a handbook for X" |
| **audit** | Existing handbook present; "audit", "check", "review this handbook", "is this up to date?" |
| **update** | Specific system changes described; "update the handbook for X", "add a section for Y" |

If mode is unclear, ask once: "Do you want to create a new handbook, audit an existing one, or update specific sections?"

---

## Mode: Create

Handbook quality is won or lost in the exploration phase. Writing from incomplete knowledge produces documentation that sounds comprehensive but silently misses coverage areas. Don't skip exploration.

### Phase 1 — Explore (non-negotiable)

Launch a subagent to inventory the system before writing anything. Use this prompt template, replacing `{path}` with the system root:

> Inventory the system at `{path}`. Return a structured map:
>
> 1. **Entry points**: CLI commands, API surface, slash commands, skills, agents, MCP tools, scripts — for each: name, purpose, inputs, outputs, execution model
> 2. **Core modules**: main source files — for each: file path, one-line responsibility, what it depends on
> 3. **Configuration**: env vars, config files, settings, defaults — for each: name, default, purpose
> 4. **Dependencies**: external tools, services, APIs, runtimes required at runtime
> 5. **Safety controls**: validation, auth, sandboxing, rate limits, hooks, gates
> 6. **Contracts**: any normative reference documents (specs, protocols, contracts, schemas) — summarize each
> 7. **Tests**: what the test suite verifies, and what that implies about intended behavior
> 8. **Existing docs**: README, HANDBOOK, references — summarize each in 1-2 sentences
>
> Final response under 10000 characters. Structured inventory format, not prose.

**Gate:** Do not write any handbook content until the subagent returns. Read the full inventory before proceeding.

### Phase 2 — Structure Selection

From the inventory, select which canonical sections to include. Skip sections with nothing to put in them — a sparse section is worse than no section.

| Section | Include when |
|---------|--------------|
| Overview | Always |
| At a Glance | System has 3+ components or 2+ entrypoints worth summarizing in tables |
| Core Components | System has named modules, subsystems, or files worth inventorying |
| Configuration and Bring-Up | System requires installation steps, env vars, or a non-trivial startup procedure |
| Operating Model | System has non-obvious runtime behavior, trust models, or shared contracts |
| Component Runbooks | System has 2+ independently invocable entrypoints or separately operable components |
| Internals | System has complex internal flows (sequences, state machines) not obvious from the source |
| Failure and Recovery Matrix | System has documented or discoverable failure modes |
| Known Limitations | System has guardrails, footguns, or known issues operators should know |
| Verification | System can be verified as working via a concrete, runnable check procedure |

**Gate:** State which sections you're including and one-line reasoning for each before writing.

### Phase 3 — Draft

Write each section with these rules:

**Structure**
- Tables over prose for structured comparisons: components, config vars, failure modes, entrypoints
- Concrete file paths and links — not just names; link to actual paths
- Behavioral specification, not structural description: "blocks outbound calls when credentials are detected" not "contains a credential scanner"
- Document failure modes in every runbook section, not only the happy path

**Operator audience**
Assume the reader can read code. They don't need line-by-line explanation of what the code does. They need: how to bring it up, what runtime assumptions it makes, what can go wrong, how to recover, and what the non-obvious invariants are.

**Section templates**

For **Overview**, write: purpose in one sentence, scope in 1-2 sentences, what the system does NOT cover.

For **At a Glance**, use tables — one table per structural dimension worth summarizing (e.g., entrypoints, components, hooks). Each row: name, purpose, key property.

For **Core Components**, use H3 subheadings grouped by type (e.g., Skills, Agents, Scripts), with a table or bulleted list of file paths and one-line responsibilities.

For **Component Runbooks**, use this template per component:

```
### When to use
[2-3 sentences: what problem this solves, when to choose it over alternatives]

### Inputs and defaults
| Parameter | Default | Purpose |
|-----------|---------|---------|

### Flow
1. [Concrete step]
2. [Concrete step]

### Failure modes
| Symptom | Cause | Recovery |
|---------|-------|---------|
```

For **Failure and Recovery Matrix**, use:

```
| Symptom | Likely Cause | Diagnosis | Recovery |
|---------|-------------|-----------|---------|
```

For **Verification**, write a numbered procedure that can be executed from a fresh checkout. Include: prerequisite checks, a minimal smoke test per entrypoint, and one end-to-end check.

### Phase 4 — Verify

Before delivering:
- Confirm every cited file path exists on disk
- Confirm every env var, CLI flag, and config key is accurate against the source
- Check that each runbook section has at least one failure mode
- Confirm the verification procedure actually runs on the described system (trace through it mentally)

If any check fails, fix it before delivering. Don't deliver a handbook with known inaccuracies.

### Output placement

Unless the user specifies otherwise, place the handbook at `HANDBOOK.md` in the system's root directory (the same level as its README).

---

## Mode: Audit

Read the existing handbook, then read the source files it describes. Do not fix anything before delivering the report.

### Audit categories

**Accuracy** — claims that are factually wrong or outdated:
- Incorrect file paths or module names
- Behaviors described that no longer match the code
- Changed defaults, env vars, or config keys
- Removed or renamed components, entrypoints, flags

**Coverage** — missing content that operators need:
- Entrypoints or components in the source with no handbook entry
- Runbook sections with no failure modes
- No bring-up procedure or prerequisites section
- No verification procedure

**Currency** — content that may be stale:
- "Planned" or "upcoming" work that may have already shipped
- References to files that no longer exist
- Version numbers or dependency specs that may be outdated

**Structure** — organizational problems:
- Sections that belong in a different location
- Missing canonical sections for the system type
- Inconsistent depth across similar components (e.g., three runbooks with failure modes, one without)

### Audit output format

```
## Handbook Audit: [Document Name]

### Summary
[N accuracy issues, N coverage gaps, N currency concerns, N structural issues]

### Accuracy Issues
- [Section/claim]: [what's wrong → what the correct value is, with evidence]

### Coverage Gaps
- Missing: [what's absent → why operators need it]

### Currency Concerns
- [Section]: [what may be stale → what to verify against source]

### Structural Issues
- [Issue → recommendation]

### Recommended Priority
1. [Most critical fix and why]
2. ...
```

**After delivering the report:** Offer to make the changes. Wait for user confirmation before editing anything.

---

## Mode: Update

Use when the system changed and the handbook needs to reflect that change.

### Process

1. **Understand the change** — what changed in the system? (new feature, behavior change, new entrypoint, renamed component, changed default)
2. **Locate affected sections** — find every handbook section that references the changed component or behavior; don't assume it's just one section
3. **Read current content and source** — read the section and the updated source before editing
4. **Update precisely** — change only what's affected; don't rewrite adjacent sections or restructure unrelated content
5. **Verify** — confirm the updated section accurately reflects current behavior

When scope is unclear, ask: "Does this change affect [section X] as well?"

Don't volunteer to restructure or improve sections you're not updating. If you notice other issues, flag them separately after completing the update.

---

## Writing Rules

Apply in all three modes:

- **Link to files** — use paths that navigate to actual files, not just names
- **Operational voice** — "Run `uv run pytest`" not "tests can be run"
- **No placeholders** — if a section can't be written accurately, omit it; never write TODO stubs or "see source"
- **Tables for structure** — configuration, components, failure modes, and comparisons belong in tables, not prose
- **Concrete procedures** — numbered steps, not vague descriptions like "configure the environment"
- **Operator, not learner** — assume the reader knows the domain; don't explain general concepts, explain this system's behavior
