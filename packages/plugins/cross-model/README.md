# Cross-Model Plugin

A Claude Code plugin that gives Claude structured ways to consult, delegate to, and collaborate with OpenAI Codex. Claude remains the primary agent; Codex provides independent second opinions, multi-turn dialogues, and autonomous task execution — all behind credential scanning, sandbox containment, and scope enforcement.

**License:** MIT | **Host:** Claude Code

### Document Authority

| Document | Role | Edits go here when... |
|----------|------|-----------------------|
| `references/*.md` | Normative protocol specs | ...changing how consultation, safety, or context injection work |
| `skills/`, `agents/` | Executable instructions conforming to contracts | ...changing entrypoint behavior or orchestration |
| `README.md` (this file) | Overview, setup, architecture | ...changing what the plugin is or how to install/use it |
| `HANDBOOK.md` | Operations, troubleshooting, failure recovery | ...changing how to operate or debug the plugin |

Protocol details live in the contracts. This file and the handbook link to them rather than restating them.

## Installation

### Prerequisites

| Requirement | Purpose | Check |
|-------------|---------|-------|
| **Claude Code** | Plugin host | `claude --version` |
| **Codex CLI** | Consultation transport | `codex --version` (v0.111.0+) |
| **Python 3.11+** | Plugin scripts and MCP server | `python3 --version` |
| **uv** | Python package management | `uv --version` |
| **git** | Evidence gathering, delegation gates | `git --version` |

**Authentication:** Run `codex login` or set `OPENAI_API_KEY` in your environment.

### Install

```bash
claude plugin marketplace update turbo-mode
claude plugin install cross-model@turbo-mode
```

The plugin auto-registers two MCP servers, three hooks, four skills, and four agents. No manual post-install configuration is needed.

### Verify

After installation, confirm the plugin loaded correctly:

1. `/codex ping` — should get a Codex response
2. `/consultation-stats` — should report event counts (or "No consultation data found" on first run)

## What It Does

The plugin adds four capabilities to Claude Code:

| Capability | Skill | When to Use |
|------------|-------|-------------|
| **Consult** | `/codex` | Quick second opinion on architecture, debugging, code review |
| **Dialogue** | `/dialogue` | Deep multi-turn discussion with codebase evidence gathering |
| **Delegate** | `/delegate` | Hand off a coding task for Codex to execute autonomously |
| **Analytics** | `/consultation-stats` | Review consultation history, convergence rates, security events |

Each capability has its own trust model:

| Skill | Trust Level | Safety Controls |
|-------|-------------|-----------------|
| `/codex` | Advisory | Credential scan (fail-closed) |
| `/dialogue` | Multi-turn with evidence | Credential scan + scope envelope + context-injection redaction |
| `/delegate` | Lowest (autonomous execution) | Credential scan + clean-tree gate + secret-file gate + sandbox + mandatory review |
| `/consultation-stats` | Read-only | Event log access only |

## Components

### Skills (Slash Commands)

#### `/codex` — Direct Consultation

```
/codex [-m <model>] [-s <sandbox>] [-a <approval>] [-t <effort>] PROMPT
```

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `-m` | model name | Codex default | Model override |
| `-s` | `read-only`, `workspace-write`, `danger-full-access` | `read-only` | Sandbox mode |
| `-a` | `untrusted`, `on-failure`, `on-request`, `never` | Coupled to sandbox | Approval policy |
| `-t` | `minimal`, `low`, `medium`, `high`, `xhigh` | `xhigh` | Reasoning effort |

Single-turn: sends a briefing to Codex, relays the response as a three-part structure (Codex Position, Claude Assessment, Decision).

#### `/dialogue` — Orchestrated Multi-Turn Consultation

```
/dialogue "question" [-p <posture>] [-n <turns>] [--profile <name>] [--plan]
```

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `-p` | `adversarial`, `collaborative`, `exploratory`, `evaluative`, `comparative` | `collaborative` | Conversation style |
| `-n` | 1-15 | 8 | Maximum turns |
| `--profile` | Named preset (see [Profiles](#consultation-profiles)) | none | Use a consultation profile |
| `--plan` | boolean | false | Enable question decomposition before dialogue |

Multi-turn: launches two parallel context gatherers to explore the codebase, assembles an evidence-backed briefing, then delegates to the `codex-dialogue` agent for a structured conversation with running ledger, convergence detection, and confidence-annotated synthesis.

#### `/delegate` — Autonomous Codex Execution

```
/delegate [-m <model>] [-s <sandbox>] [-t <effort>] [--full-auto] PROMPT
```

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `-m` | model name | Codex default | Model override |
| `-s` | `read-only`, `workspace-write` | `workspace-write` | Sandbox mode (`danger-full-access` not supported) |
| `-t` | `minimal`, `low`, `medium`, `high`, `xhigh` | `high` | Reasoning effort |
| `--full-auto` | boolean | false | Skip interactive steps (mutually exclusive with `-s read-only`) |

Hands a coding task to Codex CLI for autonomous execution. Requires a clean git working tree. Claude reviews all changes afterward — no auto-commit.

#### `/consultation-stats` — Analytics Dashboard

```
/consultation-stats [--period <days>] [--type <filter>]
```

| Parameter | Values | Default | Purpose |
|-----------|--------|---------|---------|
| `--period` | 7, 30, 0 (all time) | 30 | Time window |
| `--type` | `all`, `consultation`, `dialogue`, `delegation`, `security` | `all` | Event type filter |

Reads `~/.claude/.codex-events.jsonl` and computes convergence rates, posture effectiveness, context quality, and security metrics.

### Agents

| Agent | Spawned By | Purpose | Model |
|-------|-----------|---------|-------|
| `codex-dialogue` | `/dialogue` | Multi-turn conversation manager with 7-step per-turn loop, ledger tracking, and convergence detection | Opus |
| `codex-reviewer` | Direct invocation | Cross-model code review from git diffs (size limits: full <=500 lines, summarize 501-1500, reject >1500) | Opus |
| `context-gatherer-code` | `/dialogue` (parallel) | Pre-dialogue codebase explorer; emits `CLAIM`/`OPEN` tagged lines with citations | Sonnet |
| `context-gatherer-falsifier` | `/dialogue` (parallel) | Pre-dialogue assumption tester; searches for counterevidence | Sonnet |

### Hooks

| Event | Matcher | Script | Behavior |
|-------|---------|--------|----------|
| `PreToolUse` | `mcp__plugin_cross-model_codex__codex\|codex-reply` | `codex_guard.py` | Credential scan; exit 2 blocks dispatch (fail-closed) |
| `PostToolUse` | `mcp__plugin_cross-model_codex__codex\|codex-reply` | `codex_guard.py` | Appends event to JSONL log (fail-soft) |
| `PostToolUseFailure` | `Bash` | `nudge_codex.py` | Suggests `/codex` after repeated failures (requires `CROSS_MODEL_NUDGE=1`) |

### MCP Servers

**Codex** — a local FastMCP shim (`codex_shim.py`) that translates MCP tool calls to `codex exec` CLI invocations via the `codex_consult.py` adapter. Replaces the upstream `codex mcp-server` binary for stability against CLI updates.

| Tool | Purpose |
|------|---------|
| `mcp__plugin_cross-model_codex__codex` | Start a new Codex conversation |
| `mcp__plugin_cross-model_codex__codex-reply` | Continue an existing conversation (via `threadId`) |

**Context Injection** — a Python MCP server (v0.2.0) bundled at `context-injection/` that provides mid-conversation evidence gathering for the `codex-dialogue` agent.

| Tool | Purpose |
|------|---------|
| `mcp__plugin_cross-model_context-injection__process_turn` | Analyze a conversation turn: extract entities, rank scout templates, produce scout options with HMAC tokens |
| `mcp__plugin_cross-model_context-injection__execute_scout` | Execute a selected scout: gather evidence from the codebase, redact credentials, return results |

The context-injection server is stateful per-process. It uses HMAC tokens (generated in Call 1, validated in Call 2) to ensure scout integrity. All file access is gated by git-tracked status and path denylists.

### Shared Modules

Python scripts in `scripts/` provide the shared infrastructure:

| Module | Purpose | Used By |
|--------|---------|---------|
| `credential_scan.py` | Tiered credential detection (strict/contextual/broad) | `codex_guard.py`, `codex_delegate.py` |
| `secret_taxonomy.py` | Credential pattern families with per-family redact/egress controls | `credential_scan.py` |
| `event_log.py` | Atomic POSIX append to `~/.claude/.codex-events.jsonl` | `codex_guard.py`, `emit_analytics.py` |
| `emit_analytics.py` | Deterministic event emission with schema validation | `/codex`, `/dialogue`, `/delegate` |
| `read_events.py` | JSONL event reader with per-type field validation | `compute_stats.py` |
| `compute_stats.py` | Analytics computation (usage, quality, context, security) | `/consultation-stats` |
| `stats_common.py` | Shared aggregation and formatting utilities | `compute_stats.py` |
| `codex_guard.py` | PreToolUse/PostToolUse enforcement hook | Hook system |
| `codex_delegate.py` | 14-step delegation pipeline adapter | `/delegate` |
| `nudge_codex.py` | PostToolUseFailure optional nudge | Hook system |
| `codex_consult.py` | Consultation adapter — wraps `codex exec` with programmatic `consult()` API | `codex_shim.py` |
| `codex_shim.py` | FastMCP MCP shim translating tool calls to adapter | MCP server (`.mcp.json`) |
| `consultation_safety.py` | Shared safety utilities (ToolScanPolicy, SafetyVerdict, check_tool_input) | `codex_guard.py`, `codex_consult.py` |
| `retrieve_learnings.py` | Keyword-scored learning retrieval from `docs/learnings/learnings.md` | `/codex`, `/dialogue` |
| `event_schema.py` | Event field definitions and schema version resolution | `codex_delegate.py`, `emit_analytics.py` |
| `validate_graduation.py` | Learning graduation report validator | Scripts, tests |
| `validate_profiles.py` | Consultation profile YAML validator (contract §14 invariants) | Scripts, tests |

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | unset | Codex CLI authentication (alternative to `codex login`) |
| `CODEX_SANDBOX` | `seatbelt` | Prevents Codex CLI startup panic on macOS (set in `.mcp.json`) |
| `REPO_ROOT` | `${PWD}` | Repository root for context-injection server (set in `.mcp.json`) |
| `CROSS_MODEL_NUDGE` | unset | Set to `1` to enable Bash failure nudges |
| `CLAUDE_SESSION_ID` | set by host | Session identifier appended to analytics events (read from env, nullable) |

### Consultation Profiles

Named presets in `references/consultation-profiles.yaml` configure posture, turn budget, and reasoning effort:

| Profile | Turns | Posture | Effort | Use Case |
|---------|-------|---------|--------|----------|
| `quick-check` | 1 | collaborative | medium | Fast sanity check |
| `collaborative-ideation` | 6 | collaborative | high | Brainstorming |
| `exploratory` | 6 | exploratory | high | Open-ended research |
| `deep-review` | 8 | evaluative | xhigh | Thorough multi-turn review |
| `code-review` | 4 | evaluative | high | Focused code/document review |
| `adversarial-challenge` | 6 | adversarial | xhigh | Stress-test assumptions |
| `planning` | 8 | comparative | xhigh | Architectural design review |
| `decision-making` | 6 | comparative | xhigh | Choose between N options |
| `debugging` | 7 | exploratory/evaluative/collaborative | high | Multi-phase debugging (profile-only) |

**Resolution order:** explicit CLI flags > named profile > contract defaults.

Override or add profiles by creating `references/consultation-profiles.local.yaml`:

```yaml
profiles:
  my-profile:
    description: "Custom profile"
    sandbox: read-only
    approval_policy: never
    reasoning_effort: high
    posture: collaborative
    turn_budget: 4
```

### Normative Contracts

Two primary contracts are the authoritative source of truth for protocol behavior. Code must conform to them. Three supporting reference documents provide format specs and agent-optimized extracts.

| Contract | Location | Scope |
|----------|----------|-------|
| Consultation Contract | `references/consultation-contract.md` | Briefing assembly, safety pipeline, transport, relay format |
| Context Injection Contract | `references/context-injection-contract.md` | Two-call protocol, TurnRequest/TurnPacket shapes, scout validation |
| Composition Contract | `references/composition-contract.md` | Multi-skill composition: sentinel detection, capsule exchange, lineage |
| Dialogue Synthesis Format | `references/dialogue-synthesis-format.md` | Output format and pipeline data epilogue for dialogue synthesis |
| Contract Agent Extract | `references/contract-agent-extract.md` | Agent-readable extract of consultation contract (§4-5, §7-10, §15) |

## Usage Patterns

### Quick Second Opinion

```
/codex Is this retry logic correct? I'm worried about the exponential backoff cap.
```

### Deep Architecture Review

```
/dialogue "Is our caching strategy over-engineered for the current scale?" -p adversarial -n 5
```

### Evidence-Backed Planning

```
/dialogue "Design the new auth flow" --profile planning --plan
```

### Autonomous Bug Fix

```
/delegate fix the flaky test in tests/auth_test.py
```

### Codebase Analysis (Read-Only)

```
/delegate -s read-only analyze the codebase for dead code and unused exports
```

### Review Consultation History

```
/consultation-stats --period 7 --type dialogue
```

## Architecture

The plugin is organized in five layers, each with a distinct responsibility:

```
Layer 1: Skills           User-facing entrypoints (/codex, /dialogue, /delegate, /consultation-stats)
Layer 2: Agents           Orchestration (codex-dialogue, codex-reviewer, context-gatherers)
Layer 3: Scripts + Hooks  Enforcement (credential scanning) and analytics (event logging)
Layer 4: Contracts        Normative specifications (5 reference documents in references/)
Layer 5: MCP Servers      Codex shim (codex_shim.py) + context-injection (context_injection/server.py)
```

### Execution Flows

**`/codex`** — Skill builds briefing, calls Codex MCP tool (credential-scanned by hook), relays three-part response.

**`/dialogue`** — Skill spawns two parallel context gatherers, assembles enriched briefing, delegates to `codex-dialogue` agent. Agent runs a multi-turn scouting loop: Call 1 (process_turn) produces scout options, Call 2 (execute_scout) gathers evidence, then Codex responds — repeating until convergence or budget exhaustion.

**`/delegate`** — Skill validates input, calls `codex_delegate.py` adapter (14-step pipeline: credential scan, version check, clean-tree gate, secret-file gate, `codex exec` subprocess), then Claude reviews all changes.

**`/consultation-stats`** — Skill calls `compute_stats.py` which reads the JSONL event log, filters by time/type, and returns aggregated metrics.

### Safety Model

Credential scanning runs on every outbound Codex payload (PreToolUse hook) and on delegation prompts. The context-injection server independently redacts credentials from gathered evidence. Over-redaction is always preferred over under-redaction.

Tier definitions, pattern families, and blocking behavior are specified in [consultation-contract.md §7](references/consultation-contract.md).

### Nested Package: Context Injection

The `context-injection/` directory is a standalone Python MCP server (v0.2.0) with its own `pyproject.toml`, dependency set (`mcp>=1.9.0`), and test suite (~1000 tests). It ships inside the plugin because it's tightly coupled to the `codex-dialogue` agent's scouting loop.

It can be developed and tested independently:

```bash
cd context-injection
uv run pytest
```

See `context-injection/README.md` for package-specific documentation.

## Extension Points

### Custom Profiles

Create `references/consultation-profiles.local.yaml` to add or override consultation profiles. Local profiles merge with defaults; explicit CLI flags override all profiles.

### Scope Envelopes

Control which directories the context-injection server can access during dialogue:

```json
{
  "allowed_roots": ["src/", "docs/", "tests/"],
  "source_classes": ["repo_code", "repo_doc"]
}
```

Paths outside `allowed_roots` are rejected. Mid-conversation scope expansion triggers re-consent.

### Custom Redaction Formats

Add format handlers in `context-injection/context_injection/redact_formats.py`. Built-in formats: YAML, JSON, TOML, INI, ENV, raw text. New formats must fail-closed on parse errors.

### Analytics Events

All skills emit events to `~/.claude/.codex-events.jsonl` via `emit_analytics.py`. Structured event types: `consultation_outcome`, `dialogue_outcome`, `delegation_outcome`. The `codex_guard.py` hook also logs `block`, `shadow`, and `consultation` events. The `/consultation-stats` skill reads and aggregates these events.

## Development

### Testing

```bash
# Plugin scripts (from plugin root)
cd packages/plugins/cross-model
uv run pytest

# Context-injection server (~1000 tests)
cd packages/plugins/cross-model/context-injection
uv run pytest

# Or from the monorepo root
uv run --package cross-model-plugin pytest tests
```

### Project Structure

```
cross-model/
├── .claude-plugin/plugin.json     Plugin manifest (v3.1.3)
├── .mcp.json                      MCP server registration
├── skills/                        4 user-facing skills
│   ├── codex/SKILL.md
│   ├── dialogue/SKILL.md
│   ├── delegate/SKILL.md
│   └── consultation-stats/SKILL.md
├── agents/                        4 subagents
│   ├── codex-dialogue.md
│   ├── codex-reviewer.md
│   ├── context-gatherer-code.md
│   └── context-gatherer-falsifier.md
├── hooks/hooks.json               Hook configuration
├── scripts/                       Shared Python modules (17 files)
├── references/                    Normative contracts + profiles
├── context-injection/             Bundled MCP server (canonical)
├── tests/                         Plugin-level tests
├── testdata/                      Ground-truth test corpus (credential parity)
├── CHANGELOG.md                   Version history
└── HANDBOOK.md                    Operational runbook
```

### Key References

| Document | Purpose |
|----------|---------|
| [HANDBOOK.md](HANDBOOK.md) | Operational runbook: bring-up, health checks, failure recovery, internals |
| [CHANGELOG.md](CHANGELOG.md) | Version history from v0.1.0 through current |
| [consultation-contract.md](references/consultation-contract.md) | Normative: briefing structure, safety pipeline, relay format |
| [context-injection-contract.md](references/context-injection-contract.md) | Normative: two-call protocol, scout validation, redaction rules |
| [consultation-profiles.yaml](references/consultation-profiles.yaml) | Named profile presets |

## Troubleshooting

### Codex MCP server fails to start

**Symptom:** `/codex` returns an MCP connection error.

**Causes:** `uv` not installed or not on PATH, `mcp>=1.9.0` dependency resolution failure, `${CLAUDE_PLUGIN_ROOT}` expansion issue, or Python < 3.11. The shim requires the same Python environment as the context-injection server.

### Context injection server fails to start

**Symptom:** `/dialogue` falls back to `manual_legacy` mode (no mid-conversation evidence).

**Causes:** Python < 3.11, uv not installed, git not available, or non-POSIX host. The server runs startup gates that fail-closed on any missing prerequisite.

### Credential scan blocks a legitimate prompt

**Symptom:** `/codex` or `/delegate` returns "blocked by credential scan."

**Cause:** The prompt contains text matching a strict or contextual credential pattern. Placeholder words (e.g., "example", "format", "dummy") within 100 characters suppress contextual matches but not strict matches.

**Fix:** Rephrase the prompt to avoid including real credentials or patterns that resemble them. This is fail-closed by design — over-blocking is preferred.

### `/delegate` reports dirty working tree

**Symptom:** `/delegate` fails with "clean git working tree required."

**Cause:** The delegation pipeline requires `git status` to be clean (no staged, unstaged, or untracked changes).

**Fix:** Commit or stash your changes before delegating.
