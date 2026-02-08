# Codex Tool Dev Repo — Comprehensive Specification

## Summary

This document specifies a new repository inspired by `claude-code-tool-dev`, but targeting **Codex**. The repo supports authoring and iterating on Codex instruction assets (skills, agents, automations, commands), building tool integrations (MCP servers), validating artifacts, and promoting validated artifacts into the production Codex home directory:

- **Production target:** `/Users/jp/.codex`

The design preserves the core strengths of the source repo:

- Dev artifacts live in-repo (versioned, reviewed, tested)
- Production artifacts live in the user’s home (runtime state, ids, schedules)
- “Validate then promote” workflow
- Deterministic, explicit, testable instruction documents

## Goals

1. Provide a single monorepo for Codex extension development:
   - Skills
   - Agents/subagents
   - Automations (templates and generated TOMLs)
   - Optional commands
   - MCP servers (Node/TS packages)
2. Make extension authoring **safe by default**:
   - Clear boundaries, no implicit destructive actions
   - Explicit preconditions and verification steps
3. Make quality **measurable**:
   - Static linting for structure/policy compliance
   - Behavioral scenario testing (simulation harness)
4. Make deployment **repeatable and reversible**:
   - Promotion into `/Users/jp/.codex` with manifests and backups

## Non-goals

- Not a general app template
- Not a place to store secrets/tokens
- Not a replacement for Codex product docs
- Not a full “plugin marketplace”; publishing is optional and separate from promotion

## Primary Personas

- **Extension Author:** writes skills/agents/automation prompts.
- **Tool Integrator:** builds MCP servers that expose tools/data to Codex.
- **Operator/Power User:** promotes artifacts into `/Users/jp/.codex` and uses them daily.

## Repository Name

Recommended repo name:

- `codex-tool-dev`

Alternates:

- `codex-extension-dev`
- `codex-devkit`

## Repo Structure (Monorepo)

Canonical directory layout:

```
.codex/                         # Dev versions of Codex instruction assets
  skills/                       # Skills (SKILL.md required)
  agents/                       # Agents/subagents (markdown specs)
  commands/                     # Optional: slash command definitions (markdown)
  automations/                  # Automation templates and generators
  rules/                        # Blocking rules for editing/adding artifacts
  settings/                     # Settings templates (non-secret)
  handoffs/                     # Optional: session handoffs/notes (repo-local)

packages/
  mcp-servers/                  # MCP servers (TypeScript/Node)
  plugins/                      # Optional: plugins if your Codex environment supports them

scripts/                        # Utilities (validate, inventory, promote, sync)
docs/
  frameworks/                   # Methodology frameworks Codex should follow
  references/                   # Writing principles and patterns for instruction docs
  plans/                        # Design docs (this document lives here)
  audits/                       # Quality audits and regression reports
  codex-documentation/          # Optional: pinned excerpts/notes of official docs

README.md
CHANGELOG.md
package.json                    # Workspace tooling (Node/TS)
```

### Production Target Mapping

Promotion installs into the Codex home directory:

- `/Users/jp/.codex`

Recommended installed destinations (keep these aligned with Codex’s conventions):

- Skills: `/Users/jp/.codex/skills/<skill-name>/SKILL.md`
- Agents: `/Users/jp/.codex/agents/<agent-name>.md`
- Commands: `/Users/jp/.codex/commands/<command-name>.md` (if supported)
- Automations:
  - Templates live in repo only.
  - Generated install artifacts go to:
    - `/Users/jp/.codex/automations/<id>/automation.toml` (Codex desktop format)

Important: automation runtime state (next/last run) should not be committed to git; it belongs in Codex runtime storage.

## Artifact Types and Contracts

Each artifact type has:

- **Schema requirements** (structure)
- **Policy requirements** (safety, determinism)
- **Validation** (static + behavioral)
- **Promotion mapping** (repo → `/Users/jp/.codex`)

### 1) Skill

Path:

- `.codex/skills/<name>/SKILL.md`

Purpose:

- Reusable, machine-oriented instruction modules for Codex.

Required sections (minimum):

1. **Name**
2. **Trigger / When to use**
3. **Inputs**
4. **Outputs**
5. **Procedure** (step-by-step)
6. **Verification**
7. **Failure modes**
8. **Examples** (happy path + edge case)

Policy:

- Must specify boundaries: what is in scope vs out of scope.
- Must define “stop conditions” (when to ask for clarification).
- Must not rely on implicit environment state (cwd, tools installed).
- Must avoid destructive actions unless explicitly gated and user-approved.

Definition of Done:

- Passes lint checks (structure + policy)
- Has scenario tests (at least 1)
- Promotes cleanly into `/Users/jp/.codex`

### 2) Agent / Subagent

Path:

- `.codex/agents/<name>.md`

Purpose:

- Specialized worker behaviors for focused tasks (e.g., security scan, doc synthesis).

Required sections:

1. Scope and non-goals
2. Tool usage rules (what tools can be used and when)
3. Output format and success criteria
4. Escalation rules (when to request approval; when to stop)

Policy:

- Must be explicit about safety boundaries (no destructive actions without approval).
- Must be explicit about evidence requirements for claims.

### 3) Automation Templates

Paths (repo-local):

- `.codex/automations/templates/<name>.toml.tmpl` (preferred)
  - or `.codex/automations/<name>.yaml` → generator produces TOML

Purpose:

- Store the **intent** and the **prompt** for recurring tasks without binding runtime ids.

Template contract:

- `name`
- `prompt` (task only; do not embed schedule/workspaces in the prompt)
- `rrule` (UI-compatible constraints; avoid unsupported RRULE variants)
- `cwds` (workspace(s) to run in)
- `status` (ACTIVE/PAUSED)

Promotion behavior:

- Promotion generates `/Users/jp/.codex/automations/<id>/automation.toml`.
- `<id>` may be stable (derived from name hash) or generated once and persisted in a local mapping file under `/Users/jp/.codex` (not committed).

Policy:

- Never commit automation ids and run-state metadata.
- Prompts must be self-sufficient and specify outputs clearly.

### 4) Commands (Optional)

Path:

- `.codex/commands/<name>.md`

Purpose:

- Provide reusable, short command-like invocations if your Codex setup supports them.

Contract:

- Clearly define arguments and outputs.
- Provide examples and failure modes.

### 5) MCP Servers

Path:

- `packages/mcp-servers/<name>/`

Purpose:

- Provide external tools/data to Codex via MCP.

Contract:

- Buildable and runnable in dev
- Clear tool list and environment variables
- Tests or at least a smoke test

## Blocking Rules (`.codex/rules/`)

The repo enforces “read-before-edit” blocking rules, modeled after the source repo.

Required rule files:

- `.codex/rules/skills.md`
- `.codex/rules/agents.md`
- `.codex/rules/automations.md`
- `.codex/rules/commands.md` (if commands supported)
- `.codex/rules/mcp-servers.md`
- `.codex/rules/settings.md`
- `.codex/rules/workflow/git.md`
- `.codex/rules/methodology/frameworks.md`

Rule philosophy:

- Rules are short, enforceable, and validated by scripts where possible.
- “Advice” belongs in `docs/references/`.

## Workflow

### Authoring

- Create/edit artifacts under `.codex/` or `packages/`.
- Write scenario tests when adding new skills/agents/automation prompts.

### Validation (Pre-promotion)

Provide a standard entrypoint plus targeted validation:

- `uv run scripts/validate`
- `uv run scripts/validate skill <name>`
- `uv run scripts/validate agent <name>`
- `uv run scripts/validate automation <name>`
- `npm test` / `npm run build` for packages

Validation should include:

- Markdown structure checks
- Policy checks (forbidden patterns, missing verification, implicit assumptions)
- MCP server build checks (tsc build, minimal tests)

### Promotion (Install to `/Users/jp/.codex`)

Promotion is the only operation that writes into the production target.

- `uv run scripts/promote skill <name>`
- `uv run scripts/promote agent <name>`
- `uv run scripts/promote automation <name>`
- `uv run scripts/promote all`

Promotion requirements:

- Validate first (fail fast if validation fails)
- Write a manifest entry for installed artifacts
- Back up the previous installed version before overwriting
- Never delete production artifacts automatically

## Safety Model

Default safety constraints:

- No destructive operations without explicit confirmation.
- No “rm” usage; if deletion is required, use safe trash semantics.
- Promotion copies files and writes manifests; it does not mutate unrelated files.

Standard error format for scripts:

- `"{operation} failed: {reason}. Got: {input!r:.100}"`

## Testing Strategy

### Static lint

- Structure compliance (required headings/fields)
- Policy compliance (no forbidden commands; explicit verification present)

### Behavioral scenario tests

Add a scenario harness to validate that skills/agents:

- Follow required output formats
- Perform verification steps
- Avoid prohibited actions
- Ask for clarification when required

Storage:

- `tests/scenarios/<artifact>/<scenario-name>.yaml` (or `.json`)

Outputs:

- Human-readable report under `docs/audits/` or `tmp/`

## Tooling

Recommended toolchain (alignable with the existing repo):

- Node/TypeScript workspaces for packages
- Python `uv` for scripts and validation harness
- `pytest` for tests, `ruff` for lint/format (python scripts)

Minimum commands:

- `uv run scripts/validate`
- `uv run scripts/promote …`
- `npm run build`
- `npm test`

## Documentation Set

### `README.md`

Must include:

- Purpose and quickstart
- Directory layout
- Validate + promote workflows
- Production target notes (`/Users/jp/.codex`)
- Safety rules and how approval works

### `docs/references/writing-principles.md`

Codex-targeted writing guidance:

- Deterministic steps, explicit inputs/outputs
- Verification and failure modes
- Tight scope and stop conditions
- No hidden environment assumptions

### `docs/frameworks/`

Frameworks Codex should follow:

- Verification framework (preconditions → execute → verify → report)
- Decision framework (options + tradeoffs + recommendation)
- Debugging framework (repro → isolate → fix → regression)

## CI / Quality Gates (Optional)

If CI is added:

- Validate instruction artifacts
- Run scenario tests
- Build MCP servers
- Refuse merge if validation fails

## Decisions and Open Questions

### Automation IDs

Two viable approaches:

1. **Stable deterministic ids**: derive id from template name (hash).
   - Pros: repeatable; no mapping file
   - Cons: renaming changes id; potential collisions (mitigable)
2. **One-time generated ids**: generate on first promote and persist mapping in `/Users/jp/.codex` (not committed).
   - Pros: stable across renames; aligns with runtime expectations
   - Cons: requires local mapping management

Recommended default: **deterministic ids** for simplicity, unless Codex runtime strongly assumes opaque ids.

### Commands Support

Codex environments vary; keep commands optional and gated behind a rules file and validation.

