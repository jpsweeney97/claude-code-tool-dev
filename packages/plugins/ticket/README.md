# Ticket

Repo-local ticket management for Claude Code. Tracks work as markdown files with YAML frontmatter, enforces a 4-stage mutation pipeline, and gates agent writes with configurable autonomy policy.

## Installation

Install via the turbo-mode marketplace:

```bash
claude plugin marketplace update turbo-mode
claude plugin install ticket@turbo-mode
```

**Requirements:** Python 3.11+, Claude Code with plugin support.

**Runtime dependency:** `pyyaml` (>=6.0) — installed automatically.

## What It Does

- **Creates and manages tickets** as markdown files in `docs/tickets/` within any git-tracked project
- **Enforces a 4-stage pipeline** (classify, plan, preflight, execute) for every mutation — no direct file writes
- **Gates agent autonomy** — user mutations always allowed; agent mutations require explicit opt-in via `autonomy_mode: auto_audit`
- **Deduplicates** — SHA-256 fingerprint of problem text + key files, checked within a 24-hour window
- **Prevents race conditions** — TOCTOU protection via content+mtime fingerprints between preflight and execute
- **Audits every mutation** — append-only JSONL logs in `.audit/`, fail-closed for agent writes
- **Validates trust** — a PreToolUse hook injects and verifies a trust triple (session ID, hook confirmation, request origin) before any write
- **Reads legacy tickets** — parses Gen 1-4 ticket formats with backward-compatible field defaults

## Quick Start

After installation, use the `/ticket` skill in any Claude Code session within a project that has a `.git/` or `.claude/` directory:

```
/ticket create "Fix login timeout on slow connections"
```

Claude will gather details (priority, tags, key files), show you the proposed ticket, and ask for confirmation before writing. The ticket lands at `docs/tickets/YYYY-MM-DD-fix-login-timeout-on.md`.

To check project health:

```
/ticket-triage
```

This shows active ticket counts, stale items, blocked dependency chains, and recent audit activity.

## Components

### Skills

| Skill | Purpose | Triggers |
|-------|---------|----------|
| `/ticket` | Lifecycle operations: create, update, close, reopen, list, query, audit repair | "create a ticket", "update ticket T-...", "close T-...", "list tickets", "show open tickets" |
| `/ticket-triage` | Read-only health dashboard: stale detection, blocked chains, audit summary | "triage tickets", "what's in the backlog", "any stale tickets", "what should I work on next" |

### Hook

**`ticket_engine_guard.py`** — a `PreToolUse` hook on Bash commands that:

- Validates ticket engine invocations against a canonical allowlist
- Injects trust fields (`session_id`, `hook_injected`, `request_origin`) into the payload atomically
- Blocks shell metacharacters (`|`, `;`, `` ` ``, `$`, `&`, `()`, `<>`, newlines) to prevent injection
- Validates that the tickets directory resolves inside the project root

### Scripts

15 Python modules in `scripts/`, organized in tiers:

| Tier | Modules | Role |
|------|---------|------|
| Entrypoints | `ticket_engine_user.py`, `ticket_engine_agent.py` | Thin wrappers setting `request_origin` |
| Runner + Core | `ticket_engine_runner.py`, `ticket_engine_core.py` | CLI dispatch, 4-stage pipeline orchestration |
| Models + Validation | `ticket_stage_models.py`, `ticket_validate.py`, `ticket_parse.py` | Frozen dataclasses, schema checks, markdown parsing |
| File Operations | `ticket_paths.py`, `ticket_render.py`, `ticket_read.py`, `ticket_id.py` | Path discovery, markdown rendering, queries, ID allocation |
| Integrity | `ticket_dedup.py`, `ticket_audit.py`, `ticket_triage.py` | Fingerprinting, JSONL repair, health dashboard |
| Trust | `ticket_trust.py` | Trust triple validation at execute boundary |

The hook lives separately at `hooks/ticket_engine_guard.py`.

## Configuration

### Autonomy Policy

Create `.claude/ticket.local.md` at your project root:

```yaml
---
autonomy_mode: suggest
max_creates_per_session: 5
---
```

| Key | Type | Default | Options | Purpose |
|-----|------|---------|---------|---------|
| `autonomy_mode` | string | `suggest` | `suggest`, `auto_audit` | `suggest`: only user mutations allowed. `auto_audit`: agent mutations allowed with full audit trail. |
| `max_creates_per_session` | int | `5` | `0` (disabled) or positive int | Per-session cap on agent-initiated creates |

The config is re-read at both preflight and execute stages — changes take effect immediately without restarting.

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_PLUGIN_ROOT` | Auto-set by Claude Code | Absolute path to plugin installation. Skills resolve this at invocation. |

### Tickets Directory

- **Location:** `<project_root>/docs/tickets/`
- **Project root:** nearest ancestor containing `.claude/` or `.git/`
- **Closed tickets:** archived to `docs/tickets/closed-tickets/`
- **Audit logs:** `docs/tickets/.audit/YYYY-MM-DD/*.jsonl`

## Ticket Format

### Filename

`YYYY-MM-DD-<slug>.md` — slug is the first 6 words of the title, kebab-case, `[a-z0-9-]` only, max 60 characters. Collisions get a `-2`, `-3` suffix.

### YAML Frontmatter

```yaml
id: T-20260305-01
date: 2026-03-05
status: open
priority: high
effort: M
tags: [auth, timeout]
blocked_by: []
blocks: []
source:
  type: user
  ref: ""
  session: "abc123def456"
contract_version: "1.0"
```

| Field | Required | Type | Valid Values |
|-------|----------|------|-------------|
| `id` | yes | string | `T-YYYYMMDD-NN` |
| `date` | yes | string | `YYYY-MM-DD` |
| `status` | yes | string | `open`, `in_progress`, `blocked`, `done`, `wontfix` |
| `priority` | yes | string | `critical`, `high`, `medium`, `low` |
| `effort` | no | string | `XS`, `S`, `M`, `L`, `XL` or free text |
| `tags` | no | list | any strings |
| `blocked_by` | no | list | ticket IDs |
| `blocks` | no | list | ticket IDs |
| `source` | yes | object | `{type, ref, session}` |
| `contract_version` | yes | string | `"1.0"` |

### Markdown Sections

Tickets follow a standard section order: Problem, Context, Prior Investigation, Approach, Decisions Made, Acceptance Criteria, Verification, Key Files, Related, Reopen History. Only Problem is required (used for dedup fingerprinting).

### Status Transitions

| From | To | Precondition |
|------|----|-------------|
| `open` | `in_progress` | none |
| `open` | `blocked` | `blocked_by` non-empty |
| `in_progress` | `done` | acceptance criteria recommended |
| `in_progress` | `blocked` | `blocked_by` non-empty |
| `blocked` | `open` or `in_progress` | all blockers resolved |
| any | `wontfix` | none (terminal) |
| `done` or `wontfix` | `open` | `reopen_reason` required, user-only |

## Architecture

### Pipeline

Every mutation flows through four stages:

```
Classify → Plan → Preflight → Execute
```

1. **Classify** — resolves intent (create/update/close/reopen) and validates the trust triple
2. **Plan** — validates fields, generates dedup fingerprint, checks autonomy policy
3. **Preflight** — takes TOCTOU snapshot, validates dependencies, checks dedup window
4. **Execute** — re-reads config, re-checks TOCTOU fingerprint, performs atomic file write, writes audit log

Each stage accepts and returns frozen dataclasses. Stages are independently testable. Read operations (list, query, triage) bypass the pipeline entirely.

### Trust Model

Mutations carry a trust triple injected by the hook:

| Field | Source | Validates |
|-------|--------|-----------|
| `session_id` | Claude Code session | Request identity |
| `hook_injected` | Guard hook | Request passed validation |
| `request_origin` | Guard hook (from `agent_id` presence) | User vs. agent — must match entrypoint |

Mismatches are hard rejections. The trust triple is checked at both runner dispatch and execute stage.

### Module Dependency Graph

```
Entrypoints (user/agent)
  → Runner (dispatch + trust check)
    → Core Engine (pipeline stages)
      → Stage Models (frozen boundary types)
      → Validate (field schema)
      → Parse (markdown → structured)
      → Render (structured → markdown)
      → Read (queries)
      → ID (allocation)
      → Dedup (fingerprinting)
      → Paths (project root discovery)
      → Audit (JSONL logging)
      → Trust (triple validation)
```

Acyclic DAG — no circular imports. Policy is single-sourced in `ticket_engine_core.py`.

## Usage Patterns

### Create a ticket

```
/ticket create "Refactor auth module to use token rotation"
```

The skill gathers priority, tags, key files, then shows the proposed ticket for confirmation.

### Update fields

```
/ticket update T-20260305-01 --priority critical --tags security,auth
```

Only YAML frontmatter fields are updated — markdown body sections are preserved.

### Close with resolution

```
/ticket close T-20260305-01
```

Ticket moves to `done` status and archives to `closed-tickets/`.

### Query by ID prefix

```
/ticket query T-202603
```

Returns all tickets matching the prefix (useful for date-range queries).

### Enable agent autonomy

Add to `.claude/ticket.local.md`:

```yaml
---
autonomy_mode: auto_audit
max_creates_per_session: 3
---
```

Agents can now create tickets autonomously (up to 3 per session), with every mutation logged to the audit trail.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `trust_triple_invalid` | Guard hook not running | Verify hook is registered in plugin settings |
| `Shell metacharacters detected` | Using `$CLAUDE_PLUGIN_ROOT` directly | Resolve the variable to a string first, then use the resolved path |
| `autonomy_blocked` | `autonomy_mode: suggest` blocks agent writes | Set `autonomy_mode: auto_audit` in `.claude/ticket.local.md` |
| `dedup_collision` | Same problem+files created within 24 hours | Review existing tickets with `/ticket list`; update the duplicate instead |
| `toctou_conflict` | Ticket file changed between preflight and execute | Re-run the mutation — it will pick up the current state |
| `path_outside_cwd` | Tickets directory resolves outside project root | Ensure project has `.git/` or `.claude/` at the expected location |
| `session_cap_exceeded` | Agent create cap hit for this session | Raise `max_creates_per_session` or start a new session |

## Extension Points

- **Tags and filters** — `/ticket list` supports `--status`, `--priority`, and `--tag` flags for custom filtering
- **Audit analytics** — read `.audit/YYYY-MM-DD/*.jsonl` directly for custom session activity, per-action metrics, or result distributions
- **External consumption** — tickets are plain markdown + YAML frontmatter, parseable by any tool. Use the `T-YYYYMMDD-NN` ID format for cross-system linking
- **Dependency graphs** — `blocked_by` and `blocks` fields enable external tools to build and traverse dependency chains

Custom YAML fields are **not** supported in v1.0 — payload validation rejects unknown keys.

## Development

```bash
cd packages/plugins/ticket
uv sync
uv run pytest tests/
```

596 tests across 25 test files. Fixtures in `conftest.py` provide `tmp_tickets` and `tmp_audit` temporary directories.

**Run a single test:**

```bash
uv run pytest tests/test_parse.py::TestClassName::test_method -vv
```

**Project structure:**

```
scripts/     15 Python modules (core engine)
hooks/       PreToolUse guard hook
skills/      /ticket and /ticket-triage skill definitions
tests/       596 tests (unit + integration)
references/  ticket-contract.md (canonical schema)
```

## Known Limitations

1. **Concurrent agent creates** are not fully serialized under parallel subagent execution
2. **`auto_silent` mode** is defined in the contract but not yet implemented — do not use
3. **24-hour dedup window** is calendar-day scoped; tickets created late one day and early the next may not be caught
4. **Dependency cycle detection** handles linear chains only, not cycles
5. **Gen 1-2 legacy tickets** may parse with reduced field completeness

## Related Documentation

| Document | Purpose |
|----------|---------|
| [HANDBOOK.md](HANDBOOK.md) | Operational guide: bring-up, internals, failure recovery, verification smoke tests |
| [CHANGELOG.md](CHANGELOG.md) | Version history (v1.0.0 through v1.4.0) |
| [ticket-contract.md](references/ticket-contract.md) | Canonical schema, pipeline contract, dedup algorithm, status transitions |
| [pipeline-guide.md](skills/ticket/references/pipeline-guide.md) | Payload schemas, state propagation, response states, field disambiguation |

## License

MIT
